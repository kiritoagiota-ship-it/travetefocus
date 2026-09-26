"""
cenas.py — TraveteFocus
Cenas com o Kirito pixel art (kirito.py) + cortes em meia-lua (espadachim.py):

  cena_titulo(tela, label, on_fim)  Kirito pendurado por uma mao num canto de
                                    cima (a outra no cabo da Elucidator, na
                                    cintura), solta, saca num iai e escreve
                                    "TRAVETE FOCUS" com o rastro dos golpes -
                                    primeiro so com a Elucidator, depois com a
                                    Dark Repulser. Fica sempre inteiro dentro
                                    do quadro e sai num teleporte de luz.
  KiritoPin(caixa)                  espia por cima da caixa do PIN, as maos na
                                    borda: olha o codigo sendo digitado, se
                                    esconde no erro e, no acerto, sobe na
                                    caixa e some num teleporte.
  kirito_fatiar(widget, on_fim)     mini Kirito fatia o item que sera apagado
                                    (depois vem a explosao de cacos).
  kirito_wipe(widgets, on_fim)      versao epica: combo cortando a lista toda.

Tudo tolerante a falha: se algo der errado, on_fim ainda e chamado (a
historia do app nunca trava por causa de uma animacao).
"""
import math
import random

from kivy.uix.widget import Widget
from kivy.uix.stencilview import StencilView
from kivy.graphics import (Color, Rectangle, Line, Mesh, PushMatrix, PopMatrix,
                           Scale, Translate, Rotate, InstructionGroup)
from kivy.graphics.texture import Texture
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp

import kirito as K
from espadachim import CorteMeiaLua

CIANO = (0.0, 0.9, 1.0)
AZUL = (0.35, 0.65, 1.0)        # rastro da Dark Repulser
POEIRA = (0.55, 0.62, 0.75)

# efeitos que as cenas tocam (pre-carregados no inicio de cada cena)
_SONS_TITULO = ['agarra', 'koiguchi', 'pulo', 'pouso', 'sacar_iai', 'corte', 'sacar',
                'corte2', 'carga', 'golpe_final', 'desliza', 'embainhar', 'titulo', 'teleporte']
_SONS_PIN = ['agarra', 'susto', 'pulo', 'pouso', 'teleporte']


def _som(nome):
    try:
        import som
        som.tocar(nome)
    except Exception:
        pass


def _precarregar_sons(nomes):
    try:
        import som
        som.precarregar(nomes)
    except Exception:
        pass


def _tremer(n):
    try:
        from efeitos import tremer_tela
        tremer_tela(n)
    except Exception:
        pass


class _Uma:
    """Chama `fn` uma unica vez (protege on_fim de cenas)."""

    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *_):
        fn, self.fn = self.fn, None
        if fn:
            try:
                fn()
            except Exception as e:
                print(f"[cenas] on_fim: {e}")


def _mover(k, de, para, dur, altura=0.0, rot=None, fantasmas=True,
           cor_fantasma=CIANO, on_fim=None, linear=False, cada=2, on_passo=None,
           ease=None, limite=None):
    """Move a ancora do Kirito em arco (parabola de `altura`), girando de
    rot[0] a rot[1], deixando afterimages (1 a cada `cada` quadros).
    ease: 'out' (desacelera), 'in' (acelera, queda) ou 'linear'.
    limite=(area, folga): o boneco (girado como estiver) nunca sai da area.
    on_passo(u) e chamado a cada quadro com o progresso 0..1."""
    t = [0.0]
    cont = [0]
    feito = [False]
    if ease is None:
        ease = 'linear' if linear else ('out' if altura >= 0 else 'in')

    def _acabar():
        if not feito[0]:
            feito[0] = True
            if on_fim:
                on_fim()

    def _p(dt):
        try:
            t[0] += dt
            u = min(1.0, t[0] / dur)
            if ease == 'linear':
                e = u
            elif ease == 'in':
                e = u * u
            else:
                e = 1 - (1 - u) ** 2
            x = de[0] + (para[0] - de[0]) * e
            y = de[1] + (para[1] - de[1]) * e + altura * 4 * u * (1 - u)
            if rot is not None:
                k.rotacao = rot[0] + (rot[1] - rot[0]) * e
            if limite is not None:
                x, y = _dentro_girado(k, x, y, limite[0], limite[1])
            k.ancorar(x, y)
            cont[0] += 1
            if fantasmas and cont[0] % cada == 0 and u < 0.97:
                k.fantasma(cor=cor_fantasma, alfa=0.30, duracao=0.22)
            if on_passo:
                on_passo(u)
            if u >= 1:
                _acabar()
                return False
        except Exception as ex:
            print(f"[cenas] mover: {ex}")
            _acabar()
            return False
    return Clock.schedule_interval(_p, 1 / 60.)


# ═══════════════════════════════════════════════════════════════════
#  ENQUADRAMENTO (o boneco, com as espadas, nunca sai do quadro)
# ═══════════════════════════════════════════════════════════════════
def _ext(k, poses):
    """Maior extensao (esq, baixo, dir, cima) das poses a partir da ancora,
    na orientacao atual do boneco (espelhado ou nao)."""
    e = [0.0, 0.0, 0.0, 0.0]
    for p in poses:
        for i, v in enumerate(k.extensao(p)):
            e[i] = max(e[i], v)
    return e


def _no_quadro(k, x, y, poses, area, m=0.0):
    """(x, y) da ancora ajustado para todas as `poses` caberem na area."""
    esq, baixo, dir_, cima = _ext(k, poses)
    x0, y0, x1, y1 = area
    lo, hi = x0 + m + esq, x1 - m - dir_
    x = (lo + hi) / 2.0 if lo > hi else min(hi, max(lo, x))
    lo, hi = y0 + m + baixo, y1 - m - cima
    y = (lo + hi) / 2.0 if lo > hi else min(hi, max(lo, y))
    return x, y


def _dentro_girado(k, x, y, area, m=0.0):
    """(x, y) da ancora ajustado para a pose atual, com o giro atual (em
    torno da ancora), caber na area."""
    esq, baixo, dir_, cima = k.extensao()
    a = math.radians(k.rotacao)
    ca, sa = math.cos(a), math.sin(a)
    xs, ys = [], []
    for dx, dy in ((-esq, -baixo), (dir_, -baixo), (-esq, cima), (dir_, cima)):
        xs.append(dx * ca - dy * sa)
        ys.append(dx * sa + dy * ca)
    x0, y0, x1, y1 = area
    lo, hi = x0 + m - min(xs), x1 - m - max(xs)
    x = (lo + hi) / 2.0 if lo > hi else min(hi, max(lo, x))
    lo, hi = y0 + m - min(ys), y1 - m - max(ys)
    y = (lo + hi) / 2.0 if lo > hi else min(hi, max(lo, y))
    return x, y


def _raio(k, poses):
    """Maior distancia da ancora ate um canto das poses (para giros)."""
    r = 0.0
    for p in poses:
        esq, baixo, dir_, cima = k.extensao(p)
        r = max(r, math.hypot(max(esq, dir_), max(baixo, cima)))
    return r


def _arco(y_de, y_para, altura, teto):
    """Altura do arco limitada para o ponto mais alto nao passar do teto."""
    return max(0.0, min(altura, teto - max(y_de, y_para)))


# ═══════════════════════════════════════════════════════════════════
#  TELEPORTE (sai de cena sem sair do quadro)
# ═══════════════════════════════════════════════════════════════════
_TEX_COLUNA = None


def _textura_coluna():
    """Coluna de luz: forte embaixo, somindo para cima e para os lados."""
    global _TEX_COLUNA
    if _TEX_COLUNA is None:
        w, h = 16, 64
        buf = bytearray(w * h * 4)
        for y in range(h):
            fy = (1 - y / (h - 1.0)) ** 1.4
            for x in range(w):
                fx = max(0.0, 1 - abs(x - (w - 1) / 2.0) / (w / 2.0)) ** 1.3
                i = (y * w + x) * 4
                buf[i] = buf[i + 1] = buf[i + 2] = 255
                buf[i + 3] = int(255 * fx * fy)
        dados = bytes(buf)
        tex = Texture.create(size=(w, h), colorfmt='rgba')
        tex.wrap = 'clamp_to_edge'
        tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
        tex.add_reload_observer(
            lambda t: t.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte'))
        _TEX_COLUNA = tex
    return _TEX_COLUNA


def _teleporte(k, camada, faiscas, on_fim=None, cor=CIANO, dur=0.55, teto=None):
    """Como o cristal de teleporte de SAO: anel de luz nos pes, o boneco fica
    branco, afina, se estica para cima e se desfaz em faiscas numa coluna de
    luz. Nao sai do lugar (fica dentro do quadro)."""
    fim = _Uma(on_fim)
    try:
        ax, ay = k.ancora()
        esq, baixo, dir_, cima = k.extensao()
        base = ay - baixo
        alt = (baixo + cima) * 1.45
        if teto is not None:
            alt = max(dp(20), min(alt, teto - base))
        larg = max(dp(14), (esq + dir_) * 0.55)
        col = Widget(size_hint=(None, None), size=(0, 0))
        try:
            tex = _textura_coluna()
        except Exception:
            tex = None
        with col.canvas:
            c_col = Color(cor[0], cor[1], cor[2], 0)
            r_col = Rectangle(pos=(ax - larg / 2.0, base), size=(larg, 0), texture=tex)
            c_nuc = Color(1, 1, 1, 0)
            r_nuc = Rectangle(pos=(ax - larg / 6.0, base), size=(larg / 3.0, 0), texture=tex)
            c_anel = Color(cor[0], cor[1], cor[2], 0)
            anel = Line(ellipse=(ax - larg, base - dp(3), larg * 2, dp(6)), width=dp(1.4))
        camada.add_widget(col)
        _som('teleporte')
        t = [0.0]
        cont = [0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur)
                cont[0] += 1
                # anel nos pes abrindo
                ra = larg * (0.6 + 1.2 * u)
                anel.ellipse = (ax - ra, base - dp(3) - u * dp(3), ra * 2, dp(6) + u * dp(6))
                c_anel.a = 0.9 * (1 - u)
                # coluna sobe, fica, afina e some
                h = alt * min(1.0, u / 0.3)
                lw = larg * (1 - 0.55 * max(0.0, (u - 0.45) / 0.55))
                r_col.size = (lw, h)
                r_col.pos = (ax - lw / 2.0, base)
                r_nuc.size = (lw / 3.0, h * 0.9)
                r_nuc.pos = (ax - lw / 6.0, base)
                c_col.a = 0.55 * min(1.0, u / 0.15) * (1 - max(0.0, (u - 0.6) / 0.4))
                c_nuc.a = 0.8 * min(1.0, u / 0.15) * (1 - max(0.0, (u - 0.5) / 0.5))
                # boneco: branco -> afina, estica e some
                k.clarao = min(1.0, u / 0.25)
                if u > 0.25:
                    v = (u - 0.25) / 0.75
                    k.escala_x = max(0.04, 1 - v)
                    k.escala_y = 1 + 0.6 * v
                    k.opacity = max(0.0, 1 - v * 1.15)
                if cont[0] % 3 == 0 and u < 0.85:
                    faiscas.estourar(ax + random.uniform(-larg * 0.4, larg * 0.4),
                                     base + random.uniform(0, (baixo + cima) * 0.9),
                                     random.choice((cor, (1, 1, 1))), n=2,
                                     forca=dp(30), tam=max(2, k.ps * 0.8), gravidade=-dp(260))
                if u >= 1:
                    k.opacity = 0
                    if col.parent:
                        col.parent.remove_widget(col)
                    fim()
                    return False
            except Exception as e:
                print(f"[cena] teleporte: {e}")
                try:
                    if col.parent:
                        col.parent.remove_widget(col)
                except Exception:
                    pass
                fim()
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[cena] teleporte ignorado: {e}")
        fim()


# ═══════════════════════════════════════════════════════════════════
#  TITULO ESCRITO PELA ESPADA
# ═══════════════════════════════════════════════════════════════════
class TituloLuz(Widget):
    """Texto revelado por trechos (cada golpe escreve um trecho): o trecho
    nasce branco-quente com um risco de luz no corte e esfria para o ciano."""

    def __init__(self, texto, font_size, cor=(0.0, 0.9, 1.0), **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self.texto = texto
        self.cor = cor
        lbl = CoreLabel(text=texto, font_name="orbitron.ttf", font_size=font_size, bold=True)
        lbl.refresh()
        self._tex = lbl.texture
        self.tw, self.th = self._tex.size
        self._larg = []
        for i in range(len(texto) + 1):
            if i == 0:
                self._larg.append(0.0)
                continue
            c = CoreLabel(text=texto[:i], font_name="orbitron.ttf", font_size=font_size, bold=True)
            c.refresh()
            self._larg.append(float(c.texture.size[0]))
        self._larg[-1] = float(self.tw)
        self._trechos = []
        with self.canvas:
            PushMatrix()
            self._sc_glow = Scale(1, 1, 1)
            self._c_glow = Color(*cor, 0)
            self._r_glow = Rectangle(texture=self._tex, size=self._tex.size)
            PopMatrix()
        self._grupo = InstructionGroup()
        self.canvas.add(self._grupo)
        with self.canvas:
            self._c_risco = Color(1, 1, 1, 0)
            self._risco = Line(points=[0, 0, 0, 0], width=dp(1.6))
        self.bind(pos=self._reposicionar, x=self._reposicionar, y=self._reposicionar,
                  size=self._reposicionar)
        self._reposicionar()

    def _origem(self):
        return (self.x + (self.width - self.tw) / 2.0,
                self.y + (self.height - self.th) / 2.0)

    def _reposicionar(self, *_):
        ox, oy = self._origem()
        self._r_glow.pos = (ox, oy)
        cx, cy = ox + self.tw / 2.0, oy + self.th / 2.0
        self._sc_glow.origin = (cx, cy)
        for tr in self._trechos:
            x0 = self._larg[tr['i0']]
            tr['rect'].pos = (ox + x0, oy)

    def x_do_trecho(self, i0, i1):
        """Centro (x) do trecho [i0, i1) em coords do pai."""
        ox, oy = self._origem()
        return ox + (self._larg[i0] + self._larg[i1]) / 2.0, oy + self.th / 2.0

    def revelar(self, i0, i1, dur=0.09, cor=None):
        cor = cor or self.cor
        ox, oy = self._origem()
        x0, x1 = self._larg[i0], self._larg[i1]
        c = Color(1, 1, 1, 1)
        r = Rectangle(pos=(ox + x0, oy), size=(0, self.th))
        self._grupo.add(c)
        self._grupo.add(r)
        tr = {'i0': i0, 'rect': r}
        self._trechos.append(tr)
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur)
                w = (x1 - x0) * u
                r.texture = self._tex.get_region(x0, 0, max(1, w), self.th)
                r.size = (max(1, w), self.th)
                ox2, oy2 = self._origem()
                ex = ox2 + x0 + w
                inc = self.th * 0.35
                self._risco.points = [ex - inc, oy2 - dp(6), ex + inc, oy2 + self.th + dp(6)]
                self._c_risco.a = 1.0 if u < 1 else 0.0
                # esfria: branco -> cor do golpe -> ciano do titulo
                k = min(1.0, max(0.0, (t[0] - dur) / 0.5))
                cc = [1 + (cor[i] - 1) * min(1.0, k * 2) for i in range(3)]
                if k > 0.5:
                    kk = (k - 0.5) * 2
                    cc = [cor[i] + (self.cor[i] - cor[i]) * kk for i in range(3)]
                c.rgba = (cc[0], cc[1], cc[2], 1)
                if k >= 1:
                    c.rgba = (*self.cor, 1)
                    return False
            except Exception as e:
                print(f"[titulo] revelar: {e}")
                return False
        Clock.schedule_interval(_p, 1 / 60.)

    def clarao_final(self):
        """Titulo inteiro pulsa branco e ganha um brilho que respira."""
        t = [0.0]
        cores = [ins for ins in self._grupo.children if isinstance(ins, Color)]

        def _p(dt):
            try:
                t[0] += dt
                u = t[0]
                k = max(0.0, 1 - u / 0.6)
                for c in cores:
                    c.rgba = (self.cor[0] + (1 - self.cor[0]) * k,
                              self.cor[1] + (1 - self.cor[1]) * k,
                              self.cor[2] + (1 - self.cor[2]) * k, 1)
                self._c_glow.a = 0.30 * min(1.0, u / 0.15) * (0.75 + 0.25 * math.sin(u * 3))
                s = 1.10 - 0.04 * min(1.0, u / 0.6)
                self._sc_glow.x = self._sc_glow.y = s
                return self.parent is not None
            except Exception as e:
                print(f"[titulo] clarao: {e}")
                return False
        Clock.schedule_interval(_p, 1 / 60.)

    def varrer(self, dur=0.14):
        """Faixa de luz atravessando o titulo da esquerda para a direita (o
        corte do golpe final passando pelas letras)."""
        try:
            from animacoes_ui import _textura_faixa_luz
            tex = _textura_faixa_luz()
        except Exception:
            tex = None
        ox, oy = self._origem()
        larg = self.th * 1.6
        with self.canvas.after:
            c = Color(1, 1, 1, 0)
            r = Rectangle(size=(larg, self.th * 1.5), texture=tex)
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = t[0] / dur
                if u <= 1:
                    x = ox - larg + (self.tw + 2 * larg) * u
                    r.pos = (x, oy - self.th * 0.25)
                    c.a = 0.95
                else:
                    c.a = max(0.0, 0.95 - (t[0] - dur) / 0.2)
                    if c.a <= 0:
                        self.canvas.after.remove(c)
                        self.canvas.after.remove(r)
                        return False
            except Exception as e:
                print(f"[titulo] varrer: {e}")
                return False
        Clock.schedule_interval(_p, 1 / 60.)

    def pulsar(self, dur=0.85):
        """So as letras ja escritas pulsam (brancas) enquanto o golpe final
        carrega. O brilho da textura inteira revelaria o trecho que falta."""
        t = [0.0]
        cores = [ins for ins in self._grupo.children if isinstance(ins, Color)]

        def _p(dt):
            try:
                t[0] += dt
                if t[0] >= dur:
                    for c in cores:
                        c.rgba = (*self.cor, 1)
                    return False
                k = (0.15 + 0.55 * t[0] / dur) * (0.5 + 0.5 * math.sin(t[0] * 26))
                for c in cores:
                    c.rgba = (self.cor[0] + (1 - self.cor[0]) * k,
                              self.cor[1] + (1 - self.cor[1]) * k,
                              self.cor[2] + (1 - self.cor[2]) * k, 1)
            except Exception:
                return False
        Clock.schedule_interval(_p, 1 / 60.)

    def completo(self):
        """Mostra o titulo inteiro de uma vez (fallback)."""
        feitos = {tr['i0'] for tr in self._trechos}
        if 0 not in feitos:
            self.revelar(0, len(self.texto), dur=0.2)


# ═══════════════════════════════════════════════════════════════════
#  CENA DO TITULO
# ═══════════════════════════════════════════════════════════════════
_TRECHOS = [(0, 3), (3, 5), (5, 8), (8, 10), (10, 13)]      # TRA|VE|TE |FO|CUS


def _ps_para(largura, altura):
    alvo = min(dp(96), largura * 0.25, altura * 0.12)       # altura do boneco
    return max(2, int(round(alvo / 26.0)))


class _Agenda:
    """schedule_once que so dispara enquanto a cena esta viva e nunca deixa
    excecao escapar (no Android uma excecao num callback fecha o app)."""

    def __init__(self):
        self.evs = []
        self.vivo = True

    def depois(self, t, fn):
        def _x(dt):
            if not self.vivo:
                return
            try:
                fn()
            except Exception as e:
                print(f"[cena] passo ignorado: {e}")
        self.evs.append(Clock.schedule_once(_x, t))

    def cada(self, t, fn):
        """Repete fn a cada t s enquanto a cena viver e fn nao devolver False."""
        def _x(dt):
            if not self.vivo:
                return False
            try:
                return fn(dt)
            except Exception as e:
                print(f"[cena] passo ignorado: {e}")
                return False
        self.evs.append(Clock.schedule_interval(_x, t))

    def parar(self):
        self.vivo = False
        for ev in self.evs:
            ev.cancel()
        self.evs = []


def _risco_luz(camada, x0, x1, y, dur, cor=CIANO, espessura=None):
    """Risco reto de luz que cresce de x0 ate x1 em `dur` (o rastro do corte
    que atravessa a frase) e depois some devagar."""
    esp = espessura or dp(3)
    w = Widget(size_hint=(None, None), size=(0, 0))
    with w.canvas:
        c_glow = Color(cor[0], cor[1], cor[2], 0.0)
        glow = Line(points=[x0, y, x0, y], width=esp * 3.2, cap='round')
        c_nuc = Color(1, 1, 1, 0.0)
        nuc = Line(points=[x0, y, x0, y], width=esp, cap='round')
    camada.add_widget(w)
    t = [0.0]

    def _p(dt):
        try:
            t[0] += dt
            u = min(1.0, t[0] / dur)
            xa = x0 + (x1 - x0) * u
            glow.points = [x0, y, xa, y]
            nuc.points = [x0, y, xa, y]
            if t[0] <= dur:
                c_glow.a, c_nuc.a = 0.45, 1.0
            else:
                k = max(0.0, 1 - (t[0] - dur) / 0.55)
                c_glow.a, c_nuc.a = 0.45 * k, k
                nuc.width = max(1.0, esp * k)
                if k <= 0:
                    if w.parent:
                        w.parent.remove_widget(w)
                    return False
        except Exception as e:
            print(f"[cena] risco: {e}")
            return False
    Clock.schedule_interval(_p, 1 / 60.)


def _pendurado_idle(base, base_b, piscar=True):
    """Pernas balancando devagar (uma dobra de vez em quando) e piscada."""
    quadros = []
    for f in range(56):
        q = dict(base_b if 22 <= f < 34 else base)
        if piscar and f in (46, 47):
            q['olhos'] = 'f'
        quadros.append(q)
    return quadros


def cena_titulo(tela, label, on_fim=None, texto="TRAVETE FOCUS"):
    """Kirito pendurado por uma mao num canto de cima, a outra no cabo da
    Elucidator: kamae, solta, iai na cintura escrevendo o 1o trecho; saca a
    Dark Repulser e segue o combo; no golpe final carrega, atravessa a frase
    num corte so, para, embainha devagar - e so no clique da guarda a frase
    explode. Sai num teleporte, sem nunca deixar o quadro."""
    fim = _Uma(on_fim)
    camada = Widget(size_hint=(None, None), size=tela.size, pos=(0, 0))
    ag = _Agenda()
    camada._agenda = ag

    def encerrar():
        ag.parar()
        fim()

    try:
        tela.add_widget(camada)
        W, H = tela.size
        area = (0.0, 0.0, float(W), float(H))
        wx, wy = label.to_window(label.x, label.y)
        lx, ly = tela.to_widget(wx, wy)
        titulo = TituloLuz(texto, label.font_size, pos=(lx, ly), size=label.size)
        camada.add_widget(titulo)
        camada._titulo = titulo
        faiscas = K.Faiscas(n_max=110)
        ps = _ps_para(W, H)
        kk = K.KiritoPixel(ps=ps)
        kk.opacity = 0
        camada.add_widget(kk)
        camada.add_widget(faiscas)
        alt = 24 * ps
        th = titulo.th
        m = max(dp(4), ps)                              # folga ate a borda do quadro
        P = K.POSE_A
        kk.precarregar([P[n] for n in P])
        _precarregar_sons(_SONS_TITULO)
        y_ataque = ly + label.height / 2.0 + alt * 0.12

        def quadro(x, y, poses):
            return _no_quadro(kk, x, y, [P[n] if isinstance(n, str) else n for n in poses], area, m)

        def corte_trecho(i, cor, sentido=1, som_corte='corte', cor2=None):
            i0, i1 = _TRECHOS[i]
            cx, cy = titulo.x_do_trecho(i0, i1)
            larg = max(titulo._larg[i1] - titulo._larg[i0], th)
            a0, a1 = (160, -150) if sentido > 0 else (20, 330)
            camada.add_widget(CorteMeiaLua(centro=(cx, cy), raio=larg * 0.95, ang_ini=a0,
                                           ang_fim=a1, espessura=th * 0.9, achat=0.42, cor=cor))
            if cor2 is not None:           # golpe duplo: segunda meia-lua cruzando
                camada.add_widget(CorteMeiaLua(centro=(cx, cy + th * 0.1), raio=larg * 0.9,
                                               ang_ini=a1 + 180, ang_fim=a0 + 180,
                                               espessura=th * 0.7, achat=0.42, cor=cor2))
                _som('corte2')
            titulo.revelar(i0, i1, cor=(1, 1, 1) if cor == CIANO else AZUL)
            faiscas.estourar(cx, cy, cor, n=18, forca=dp(170), tam=ps)
            _som(som_corte)
            _tremer(6)
            kk.empurrar(capa=16, cabelo=14)

        def poeira(x, y, n=10):
            faiscas.estourar(x, y, POEIRA, n=n, forca=dp(90), tam=max(2, ps * 0.8), gravidade=dp(300))

        # ── 1. pendurado por uma mao num canto de cima ───────────────
        lado = random.choice((-1, 1))                # -1 canto esquerdo, 1 direito
        kk.espelhar = lado > 0                       # olha para o centro
        p_pend = P['pendurado']
        kk.mostrar(p_pend)
        mx, my = kk.mao_local(2, p_pend)             # mao que segura a borda
        kk.pivo = (mx, my)
        ax_l, ay_l = kk.ancora_local()
        esq, baixo, dir_, cima = kk.extensao(p_pend)
        folga = m + 2 * ps                           # o balanco nao encosta na lateral
        if lado < 0:
            kk_x = area[0] + folga - (ax_l - esq)
        else:
            kk_x = area[2] - folga - (ax_l + dir_)
        kk.pos = (kk_x, H - (my + 1.5 * ps))         # topo da luva encostado na borda
        hx, hy = kk.x + mx, H
        # a borda que ele segura acende (fica claro que esta preso em algo)
        borda = Widget(size_hint=(None, None), size=(0, 0))
        with borda.canvas:
            c_borda = Color(CIANO[0], CIANO[1], CIANO[2], 0)
            Line(points=[hx - 7 * ps, hy - dp(1.2), hx + 7 * ps, hy - dp(1.2)], width=dp(1.1))
            c_borda2 = Color(CIANO[0], CIANO[1], CIANO[2], 0)
            Line(points=[hx - 12 * ps, hy - dp(1.2), hx + 12 * ps, hy - dp(1.2)], width=dp(3))
        camada.add_widget(borda, index=len(camada.children))
        balanco = {'ativo': True, 't': 0.0, 'borda': 0.0}

        def _balanca(dt):
            if not balanco['ativo']:
                return False
            balanco['t'] += dt
            t = balanco['t']
            amp = 3.0 * math.exp(-t * 2.2)                # so o tranco de agarrar: mao firme, nao corda
            r = amp * math.sin(2 * math.pi * 0.55 * t) * lado
            kk.rotacao = r if abs(r) > 0.35 else 0.0      # parado = pixel art sem serrilhado
            balanco['borda'] = min(1.0, balanco['borda'] + dt / 0.2)
            c_borda.a = 0.85 * balanco['borda']
            c_borda2.a = 0.18 * balanco['borda']
            return True

        def _surge():
            _som('agarra')
            faiscas.estourar(hx, hy - ps, CIANO, n=8, forca=dp(60), tam=max(2, ps * 0.8), gravidade=dp(120))
            t = [0.0]

            def _f(dt):
                t[0] += dt
                kk.opacity = min(1.0, t[0] / 0.25)
                return kk.opacity < 1 and ag.vivo
            ag.cada(1 / 60., _f)
            ag.cada(1 / 60., _balanca)
            kk.tocar(_pendurado_idle(p_pend, P['pendurado_b']), loop=True)
        ag.depois(0.05, _surge)

        def _kamae():
            # recolhe as pernas e empurra a guarda com o polegar: pronto para sacar
            seq = K.sequencia([(3, P['pendurado_b']), (1, P['pendurado_b']), (1, P['pendurado2'])])
            kk.tocar(seq)
            kk.empurrar(capa=-6, lift=4)

            def _koiguchi():
                bx, by = kk.ponto_mao(1)
                faiscas.estourar(bx + (ps if lado < 0 else -ps), by, (1, 1, 1), n=5,
                                 forca=dp(35), tam=max(2, ps * 0.7), gravidade=0)
                _som('koiguchi')
            ag.depois(0.2, _koiguchi)
        ag.depois(1.05, _kamae)

        # ── 2. solta e cai girando ate o inicio da frase ─────────────
        cx1, _ = titulo.x_do_trecho(*_TRECHOS[0])
        POSES_G1 = ['agacha', 'saca1', 'corta1', 'segue1', 'pega2', 'saca2', 'dupla']

        def _solta():
            balanco['ativo'] = False
            t = [0.0]
            r0 = kk.rotacao

            def _reto(dt):
                t[0] += dt
                u = min(1.0, t[0] / 0.1)
                kk.rotacao = r0 * (1 - u)
                if u >= 1:
                    _pula()
                    return False
                return True
            ag.cada(1 / 60., _reto)

        def _pula():
            ax, ay = kk.ancora()                 # ancora sem rotacao (rotacao ~0)
            kk.pivo = None
            kk.rotacao = 0
            kk.ancorar(ax, ay)
            kk.espelhar = False
            kk.mostrar(P['pulo'])
            _som('pulo')
            kk.empurrar(capa=-10, cabelo=-8, lift=12)
            alvo = quadro(cx1 - th * 1.3, y_ataque, POSES_G1)
            # giro para a frente (horario, olhando para a direita)
            _mover(kk, (ax, ay), alvo, 0.5, altura=0.0, rot=(0, -360), cada=3, on_fim=_golpe1,
                   limite=(area, m))

            def _apaga_borda(dt):
                c_borda.a = max(0.0, c_borda.a - dt / 0.35)
                c_borda2.a = max(0.0, c_borda2.a - dt / 0.35 * 0.2)
                return c_borda.a > 0
            ag.cada(1 / 60., _apaga_borda)
        ag.depois(1.75, _solta)

        # ── 3. golpe 1: iai na cintura (Elucidator) escreve "TRA" ─────
        def _golpe1():
            kk.rotacao = 0
            _som('pouso')
            ax, ay = kk.ancora()
            poeira(ax, ay - kk.extensao()[1])
            kk.empurrar(lift=-10, capa=-6)
            seq = K.sequencia([
                (2, P['agacha']), (4, P['saca1']),
                (1, K.smear(P['corta1'], K._BAINHA_ANG)), (1, P['corta1']),
                (6, P['segue1']), (1, P['segue1'])])

            def _q(i):
                if i == 2:
                    _som('sacar_iai')
                elif i == 6:
                    corte_trecho(0, CIANO, 1, 'corte')
            kk.tocar(seq, on_quadro=_q, on_fim=_saca2)

        # ── 4. saca a Dark Repulser (das costas) e toma guarda dupla ──
        def _saca2():
            seq = K.sequencia([(4, P['pega2']), (4, P['saca2']),
                               (5, P['dupla']), (6, P['dupla'])])

            def _q(i):
                if i == 5:
                    hx2, hy2 = kk.ponto_mao(2)
                    faiscas.estourar(hx2, hy2, AZUL, n=20, forca=dp(130), tam=ps)
                    _som('sacar')
                    kk.empurrar(cabelo=8)
            kk.tocar(seq, on_quadro=_q, on_fim=lambda: _combo(1))

        # ── 5. combo samurai: "VE" (Elucidator), "TE " (Dark Repulser
        #       subindo), "FO" (giro com as duas) ────────────────────
        GOLPES = {
            1: ('c2_arma', 'c2_corta', (120, None), CIANO, 1, 'corte', None),
            2: ('c3_arma', 'c3_corta', (None, 225), AZUL, -1, 'corte2', None),
            3: ('giro_a', 'giro_b', (60, 230), CIANO, 1, 'corte', AZUL),
        }

        def _combo(i):
            if i > 3:
                _iai()
                return
            p_arma, p_corta, (s1, s2), cor, sentido, som_c, cor2 = GOLPES[i]
            cx, _ = titulo.x_do_trecho(*_TRECHOS[i])
            kk.espelhar = False
            poses = [P[p_arma], P[p_corta], P['dupla']]
            ax, ay = kk.ancora()
            if i == 3:
                # giro no ar: o boneco gira inteiro, entao vale o raio da pose
                r = _raio(kk, poses)
                alvo = (min(area[2] - m - r, max(area[0] + m + r, cx - th * 0.5)),
                        min(area[3] - m - r, max(area[1] + m + r, y_ataque + th * 0.6)))
                h = _arco(ay, alvo[1], th * 0.9, area[3] - m - r)
            else:
                alvo = quadro(cx - th * 1.0, y_ataque, poses)
                h = _arco(ay, alvo[1], th * 0.4, area[3] - m - _ext(kk, poses)[3])

            def _ataca():
                kk.rotacao = 0
                seq = K.sequencia([(2, P[p_arma]),
                                   (1, K.smear(P[p_corta], s1, s2)),
                                   (1, P[p_corta]), (3, P[p_corta]),
                                   (1, P[p_corta])])
                kk.tocar(seq, on_quadro=lambda q: q == 2 and corte_trecho(i, cor, sentido, som_c, cor2),
                         on_fim=lambda: _combo(i + 1))
            _mover(kk, (ax, ay), alvo, 0.15, altura=h,
                   rot=(0, -360) if i == 3 else None, cor_fantasma=cor, on_fim=_ataca,
                   limite=(area, m))

        # ── 6. golpe final (iai): carga -> corte atravessando a frase ─
        def _iai():
            kk.espelhar = False
            p_ini = ['pulo', 'iai_carga']
            p_fim = ['iai_corte', 'iai_fim', 'chiburi', 'embainha_a', 'embainha_b', 'guardado']
            x_ini, y_iai = quadro(titulo.x_do_trecho(0, 1)[0] - th * 1.6, y_ataque - th * 0.15, p_ini)
            x_fim, y_fim = quadro(titulo.x_do_trecho(len(texto) - 1, len(texto))[0] + th * 1.6,
                                  y_ataque - th * 0.15, p_fim)
            ox_t, oy_t = titulo._origem()
            pe = kk.extensao(P['guardado'])[1] - ps           # ancora -> sola da bota
            x_top, y_top = quadro(min(x_fim, ox_t + titulo.tw - th * 0.8), oy_t + th * 0.82 + pe, p_fim)
            # o risco de luz atravessa a frase inteira, mesmo se o boneco
            # precisar parar antes da borda para as espadas nao sairem do quadro
            ox, oy = titulo._origem()
            xr0 = max(area[0] + m, min(x_ini, ox - th * 0.4))
            xr1 = min(area[2] - m, max(x_fim, ox + titulo.tw + th * 0.4))
            kk.mostrar(P['pulo'])
            _som('pulo')
            ax, ay = kk.ancora()
            h = _arco(ay, y_iai, th * 1.4, area[3] - m - _ext(kk, [P['pulo']])[3])

            def _carrega():
                _som('pouso')
                poeira(x_ini, y_iai - kk.extensao(P['iai_carga'])[1], n=8)
                kk.tocar(K.sequencia([(5, P['iai_carga']), (1, P['iai_carga'])]))
                _som('carga')
                titulo.pulsar(0.85)
                t = [0.0]

                def _aura(dt):
                    t[0] += dt
                    if t[0] >= 0.85:
                        return False
                    ax2, ay2 = kk.ancora()
                    faiscas.estourar(ax2 + random.uniform(-alt * 0.4, alt * 0.4),
                                     ay2 + random.uniform(-alt * 0.2, alt * 0.6),
                                     random.choice((CIANO, AZUL)), n=2,
                                     forca=dp(40), tam=ps, gravidade=-160)
                    kk.empurrar(capa=2.5, cabelo=2.5, lift=1.5)
                    return True
                ag.cada(0.07, _aura)
                ag.depois(0.85, _atravessa)
            _mover(kk, (ax, ay), (x_ini, y_iai), 0.3, altura=h, on_fim=_carrega, limite=(area, m))

            def _atravessa():
                kk.mostrar(P['iai_corte'])
                _som('golpe_final')
                _tremer(10)
                dur = 0.16
                _, cy = titulo.x_do_trecho(0, len(texto))
                _risco_luz(camada, xr0, xr1, cy, dur, CIANO, espessura=max(dp(2), th * 0.08))
                titulo.varrer(dur)
                # "CUS" aparece quando a lamina passa por ele
                i0, i1 = _TRECHOS[4]
                cx5, _ = titulo.x_do_trecho(i0, i1)
                frac = max(0.0, min(1.0, (cx5 - xr0) / max(1.0, xr1 - xr0)))
                ag.depois(dur * frac, lambda: titulo.revelar(i0, i1, dur=0.06))
                _mover(kk, kk.ancora(), (x_fim, y_fim), dur, linear=True, cada=1,
                       cor_fantasma=CIANO, on_fim=_sobe)

            def _sobe():
                ax2, ay2 = kk.ancora()
                h2 = _arco(ay2, y_top, th * 0.9, area[3] - m - _ext(kk, [P['iai_fim']])[3])
                _mover(kk, (ax2, ay2), (x_top, y_top), 0.22, altura=h2, fantasmas=False,
                       on_fim=_pousa_na_frase, limite=(area, m))

            def _pousa_na_frase():
                _som('pouso')
                ax2, ay2 = kk.ancora()
                faiscas.estourar(ax2, ay2 - pe, CIANO, n=8, forca=dp(70), tam=max(2, ps * 0.8),
                                 gravidade=dp(260))
                _para()

            def _para():
                # para de costas para a frase... e o mundo segura a respiracao
                kk.mostrar(P['iai_fim'])
                kk.empurrar(capa=-20, cabelo=-16)
                ag.depois(0.45, _chiburi)

            def _chiburi():
                # chiburi (sacode a lamina) e noto: embainha devagar ate o clique
                seq = K.sequencia([(3, P['chiburi']), (6, P['embainha_a']), (8, P['embainha_b']),
                                   (2, P['embainha_c']), (2, P['guardado']), (1, P['guardado'])])

                def _q(q):
                    if q == 1:
                        _som('pulo')
                    elif q == 5:
                        _som('desliza')
                    elif q == 17:
                        _som('embainhar')
                        bx, by = kk.ponto_mao(1)
                        faiscas.estourar(bx, by, (1, 1, 1), n=6, forca=dp(50), tam=max(2, ps * 0.7),
                                         gravidade=0)
                        ag.depois(0.14, _explode)
                kk.tocar(seq, on_quadro=_q, on_fim=lambda: kk.idle(base=P['guardado']))

        # ── 7. so depois de embainhar: a frase explode ──────────────
        def _explode():
            cx, cy = titulo.x_do_trecho(0, len(texto))
            for sent, cor in ((1, CIANO), (-1, AZUL)):
                camada.add_widget(CorteMeiaLua(
                    centro=(cx, cy), raio=titulo.tw * 0.62, ang_ini=160 if sent > 0 else 20,
                    ang_fim=-45 if sent > 0 else 225, espessura=th * 1.2,
                    achat=0.34, rotacao=12 * sent, cor=cor,
                    dur_cheio=5 / 30.0, dur_decai=9 / 30.0))
            faiscas.estourar(cx, cy, CIANO, n=45, forca=dp(340), tam=ps)
            faiscas.estourar(cx, cy, AZUL, n=25, forca=dp(260), tam=ps)
            _som('titulo')
            _tremer(26)
            titulo.clarao_final()
            ag.depois(1.4, _sai)

        def _sai():
            kk.parar()
            _teleporte(kk, camada, faiscas, on_fim=_acabou, teto=area[3] - m)

        def _acabou():
            try:
                kk.parar()
                camada.remove_widget(kk)
            except Exception:
                pass
            encerrar()

        # rede de seguranca: a cena nunca prende o app
        def _seguranca():
            titulo.completo()
            encerrar()
        ag.depois(16.0, _seguranca)
    except Exception as e:
        print(f"[cena] falhou, seguindo sem ela: {e}")
        encerrar()
    return camada


def limpar_cena(camada):
    try:
        ag = getattr(camada, '_agenda', None)
        if ag is not None:
            ag.parar()
        for w in list(camada.children):
            if isinstance(w, K.KiritoPixel):
                w.parar()
        if camada.parent:
            camada.parent.remove_widget(camada)
    except Exception as e:
        print(f"[cena] limpar: {e}")


# ═══════════════════════════════════════════════════════════════════
#  KIRITO NA TELA DO PIN (espiando por cima da caixa)
# ═══════════════════════════════════════════════════════════════════
class KiritoPin:
    """Espia por cima da caixa do PIN, perto de um dos cantos: so a cabeca e
    as duas maos apoiadas na borda aparecem (o corpo fica atras da caixa,
    recortado por um StencilView na linha da borda). Olha o codigo sendo
    digitado, da um pulinho a cada tecla, se abaixa no erro e volta a espiar
    devagar; no acerto sobe na caixa, faz que sim e some num teleporte."""

    def __init__(self, caixa=None):
        self.caixa = caixa
        self.k = None
        self.clip = None
        self.faiscas = None
        self.lado = 1
        self._desc = 0.0            # px abaixo da posicao de espiar (esconder)
        self._em_cima = False       # pulando/em pe em cima da caixa (acesso liberado)
        self._pe = None             # distancia ancora -> pes, quando em pe na caixa
        self._escondido = False     # abaixado depois de um PIN errado
        self._ocupado = False
        self._ev_desc = None
        self._evs = []

    # ── geometria ────────────────────────────────────────────────────
    def _borda(self):
        """(x0, topo, x1) da caixa em coords da janela."""
        c = self.caixa
        x0, y0 = c.to_window(c.x, c.y)
        return x0, y0 + c.height, x0 + c.width

    def _linha_local(self):
        """Altura (local do sprite) da borda: 2 linhas acima do topo do
        tronco da pose sem dy (as poses 'espia*' foram feitas para ela)."""
        pern = K._PERNAS['repouso']
        topo = K._PES + len(pern) + len(K._TRONCO) - 1
        return (topo + 2) * self.k.ps

    def _seguir(self, dt=0):
        """Acompanha a caixa (ela sobe com o teclado, anima ao abrir...)."""
        try:
            if self.k is None:
                return False
            W, H = Window.size
            x0, topo, x1 = self._borda()
            self.clip.pos = (0, topo)
            self.clip.size = (W, max(0, H - topo))
            ax_l, _ = self.k.ancora_local()
            recuo = max((x1 - x0) * 0.17, dp(42))
            cx = x0 + recuo if self.lado < 0 else x1 - recuo
            if self._em_cima:
                if self._pe is not None:        # em pe na caixa: acompanha a borda
                    ax, _ = self.k.ancora()
                    self.k.ancorar(ax, topo + self._pe)
                return True
            y = topo - self._linha_local() - self._desc
            # tela baixa (teclado aberto empurrou a caixa para cima): em vez de
            # a cabeca passar do topo da janela, ele se abaixa mais atras da caixa
            y1 = K.caixa(self.k._pose)[3]
            teto = y + (y1 + 1) * self.k.ps
            if teto > H:
                y -= teto - H
            self.k.pos = (cx - ax_l, y)
            return True
        except Exception as e:
            print(f"[kirito pin] seguir: {e}")
            return False

    def _depois(self, t, fn):
        def _x(dt):
            if self.k is None:
                return
            try:
                fn()
            except Exception as e:
                print(f"[kirito pin] passo: {e}")
        self._evs.append(Clock.schedule_once(_x, t))

    def _animar_desc(self, alvo, dur, on_fim=None, volta=0.0):
        """Anima o quanto ele esta abaixado atras da borda (volta = passa do
        ponto e volta, em px)."""
        if self._ev_desc is not None:
            self._ev_desc.cancel()
        de = self._desc
        t = [0.0]

        def _p(dt):
            try:
                if self.k is None or self._em_cima:
                    return False
                t[0] += dt
                u = min(1.0, t[0] / dur)
                e = 1 - (1 - u) ** 3
                extra = volta * math.sin(math.pi * u) if volta else 0.0
                self._desc = de + (alvo - de) * e - extra
                self._seguir()
                if u >= 1:
                    self._desc = alvo
                    self._seguir()
                    if on_fim:
                        on_fim()
                    return False
            except Exception as e:
                print(f"[kirito pin] desc: {e}")
                return False
        self._ev_desc = Clock.schedule_interval(_p, 1 / 60.)
        self._evs.append(self._ev_desc)

    # ── entrada ──────────────────────────────────────────────────────
    def aparecer(self):
        try:
            if self.k is not None or self.caixa is None:
                return
            W, H = Window.size
            x0, topo, x1 = self._borda()
            ps = _ps_para(x1 - x0, H) + 1
            espaco = H - topo
            ps = min(ps, int(espaco / 15.0))         # cabeca inteira acima da caixa
            if ps < 2:
                return                               # sem espaco (tela muito baixa)
            self.lado = random.choice((-1, 1))       # -1 canto esquerdo, 1 direito
            self.clip = StencilView(size_hint=(None, None), size=(W, 0), pos=(0, topo))
            k = K.KiritoPixel(ps=ps)
            self.k = k
            k.ao_redesenhar = self._seguir          # pose mudou: reajusta na hora (sem atraso)
            k.espelhar = self.lado > 0              # olha para o centro da caixa
            k.precarregar([K.POSE_A[n] for n in ('espia', 'espia_olha', 'espia_alto', 'espia_baixo',
                                                   'pulo', 'agacha', 'guardado')])
            _precarregar_sons(_SONS_PIN)
            k.mostrar(K.POSE_A['espia_baixo'])
            self.clip.add_widget(k)
            Window.add_widget(self.clip)
            self.faiscas = K.Faiscas(n_max=40)
            Window.add_widget(self.faiscas)
            self._desc = 3 * ps                      # maos ainda abaixo da borda
            self._seguir()
            self._evs.append(Clock.schedule_interval(self._seguir, 1 / 30.))
            self._ocupado = True
            # 1) as maos agarram a borda  2) a cabeca sobe devagar e espia
            self._animar_desc(0.0, 0.12, on_fim=self._agarrou)
        except Exception as e:
            print(f"[kirito pin] aparecer: {e}")
            self.remover()

    def _agarrou(self):
        _som('agarra')
        for qual in (1, 2):
            try:
                mx, my = self.k.ponto_mao(qual)
                self.faiscas.estourar(mx, my + self.k.ps, CIANO, n=3, forca=dp(30),
                                      tam=max(2, self.k.ps * 0.6), gravidade=0)
            except Exception:
                pass
        self._depois(0.3, lambda: self.k.tocar(
            K.sequencia([(12, K.POSE_A['espia_baixo']), (1, K.POSE_A['espia_olha'])]),
            on_fim=self._esperar))

    def _esperar(self):
        """Parado espiando: olha o campo do PIN, as vezes levanta os olhos,
        pisca e respira (a cabeca sobe 1 px)."""
        if self.k is None:
            return
        self._ocupado = False
        base = K.POSE_A['espia']
        olha = K.POSE_A['espia_olha']
        quadros = []
        for f in range(100):
            q = dict(olha if 44 <= f < 66 else base)
            if 18 <= f < 24 or 76 <= f < 82:        # respira
                q['dy'] = q['dy'] + 1
                q['m1'] = (q['m1'][0], q['m1'][1] - 1)
                q['m2'] = (q['m2'][0], q['m2'][1] - 1)
            if f in (60, 61):
                q['olhos'] = 'f'
            quadros.append(q)
        self.k.tocar(quadros, loop=True)

    # ── reacoes ──────────────────────────────────────────────────────
    def reagir_tecla(self):
        """Pulinho de atencao a cada tecla."""
        try:
            if self.k is None or self._ocupado:
                return
            seq = K.sequencia([(2, K.POSE_A['espia_alto']), (3, K.POSE_A['espia']),
                               (1, K.POSE_A['espia'])])
            self.k.tocar(seq, on_fim=self._esperar)
        except Exception as e:
            print(f"[kirito pin] tecla: {e}")

    def susto(self):
        """PIN errado: se abaixa atras da caixa e depois volta a espiar
        devagar, desconfiado."""
        try:
            if self.k is None or self._em_cima or self._escondido:
                return
            self._ocupado = True
            self._escondido = True
            _som('susto')
            ps = self.k.ps
            self.k.empurrar(cabelo=18, lift=8)
            self.k.tocar(K.sequencia([(2, K.POSE_A['espia_alto']), (1, K.POSE_A['espia_baixo'])]))

            def _de_volta():
                self._escondido = False
                self.k.tocar(K.sequencia([(14, K.POSE_A['espia_baixo']), (1, K.POSE_A['espia_olha'])]),
                             on_fim=self._esperar)

            def _volta():
                self.k.mostrar(K.POSE_A['espia_baixo'])
                self._animar_desc(0.0, 0.35, on_fim=_de_volta)
            self._animar_desc(13 * ps, 0.12, on_fim=lambda: self._depois(0.75, _volta))
        except Exception as e:
            print(f"[kirito pin] susto: {e}")

    def sumir(self):
        """Acesso liberado: sobe na caixa, faz que sim e some num teleporte
        (ele volta pendurado na cena do titulo)."""
        try:
            if self.k is None:
                return
            k = self.k
            self._ocupado = True
            W, H = Window.size
            x0, topo, x1 = self._borda()
            ps = k.ps
            if H - topo < 30 * ps:
                # sem espaco para ficar em pe na caixa: some dali mesmo
                k.tocar(K.sequencia([(3, K.POSE_A['espia_alto']), (4, K.POSE_A['espia']),
                                     (1, K.POSE_A['espia_alto'])]))
                self._depois(0.3, lambda: _teleporte(k, self.clip, self.faiscas, on_fim=self.remover))
                return
            k.tocar(K.sequencia([(3, K.POSE_A['espia_alto']), (1, K.POSE_A['espia_alto'])]))

            def _pula():
                ax, ay = k.ancora()
                self._em_cima = True
                k.mostrar(K.POSE_A['pulo'])
                _som('pulo')
                k.empurrar(capa=-8, lift=10)
                base = k.extensao(K.POSE_A['guardado'])[1]
                _, topo2, _ = self._borda()
                alvo = (ax - self.lado * dp(18), topo2 + base)
                _mover(k, (ax, ay), alvo, 0.3, altura=4 * ps, fantasmas=False,
                       on_fim=lambda: _pousa(base))

            def _pousa(base):
                self._pe = base
                _som('pouso')
                ax, ay = k.ancora()
                self.faiscas.estourar(ax, ay - base, POEIRA, n=8, forca=dp(60),
                                      tam=max(2, ps * 0.7), gravidade=dp(250))
                k.tocar(K.sequencia([(3, K.POSE_A['agacha']), (4, K.POSE_A['guardado']),
                                     (3, dict(K.POSE_A['guardado'], dy=-1)),      # faz que sim
                                     (3, K.POSE_A['guardado']), (1, K.POSE_A['guardado'])]),
                        on_fim=lambda: _teleporte(k, self.clip, self.faiscas, on_fim=self.remover))
            self._depois(0.12, _pula)
        except Exception as e:
            print(f"[kirito pin] sumir: {e}")
            self.remover()

    def remover(self, *_):
        for ev in self._evs:
            try:
                ev.cancel()
            except Exception:
                pass
        self._evs = []
        k, self.k = self.k, None
        if k is not None:
            try:
                k.parar()
            except Exception:
                pass
        for w in (self.clip, self.faiscas):
            _remover_da_janela(w)
        self.clip = self.faiscas = None


# ═══════════════════════════════════════════════════════════════════
#  MINI KIRITO FATIANDO O QUE SERA APAGADO
# ═══════════════════════════════════════════════════════════════════
def _limites():
    """(x0, y0, x1, y1) da area do app na janela: no PC em janela larga o app
    fica numa coluna central, e o Kirito deve usar as bordas dela."""
    W, H = Window.size
    try:
        from kivy.app import App
        sm = App.get_running_app().root.ids.sm
        x0, y0 = sm.to_window(sm.x, sm.y)
        return x0, y0, x0 + sm.width, y0 + sm.height
    except Exception:
        return 0.0, 0.0, float(W), float(H)


def _ret_janela(w):
    """(x, y, larg, alt) do widget em coordenadas da janela."""
    x, y = w.to_window(w.x, w.y)
    return x, y, w.width, w.height


def _remover_da_janela(w):
    try:
        if w is not None and w.parent is not None:
            Window.remove_widget(w)
    except Exception:
        pass


def _metades(camada, alvo, rx, ry, rw, rh):
    """Duas metades (foto real do widget) separadas por um corte diagonal."""
    try:
        tex = alvo.export_as_image().texture
    except Exception as e:
        print(f"[fatiar] sem foto do widget: {e}")
        tex = None
    ya, yb = ry + rh * 0.68, ry + rh * 0.32         # linha do corte (esq -> dir)

    def quad(pts):
        vs = []
        for x, y in pts:
            # a textura do export_as_image vem invertida na vertical
            vs.extend((x, y, (x - rx) / rw, 1.0 - (y - ry) / rh))
        return vs
    cima = [(rx, ry + rh), (rx + rw, ry + rh), (rx + rw, yb), (rx, ya)]
    baixo = [(rx, ya), (rx + rw, yb), (rx + rw, ry), (rx, ry)]
    pecas = []
    for pts, sentido in ((cima, 1), (baixo, -1)):
        w = Widget(size_hint=(None, None), size=(0, 0))
        with w.canvas:
            PushMatrix()
            tr = Translate(0, 0)
            rot = Rotate(angle=0, origin=(rx + rw / 2.0, ry + rh / 2.0))
            c = Color(1, 1, 1, 1) if tex else Color(0.05, 0.1, 0.2, 0.95)
            m = Mesh(mode='triangle_fan', indices=[0, 1, 2, 3], vertices=quad(pts))
            if tex:
                m.texture = tex
            Color(0.6, 0.95, 1, 0.9)
            Line(points=[rx, ya, rx + rw, yb], width=dp(1.4))
            PopMatrix()
        camada.add_widget(w)
        pecas.append((w, tr, rot, c, sentido))
    return pecas


def kirito_fatiar(alvo, on_fim=None):
    """Mini Kirito pula da borda mais proxima, fatia `alvo` de cima para
    baixo em duas metades e so entao vem a explosao de cacos
    (efeitos.explodir_estilhacos)."""
    fim = _Uma(on_fim)
    camada = [None]
    explodiu = [False]

    def _explodir():
        if explodiu[0]:
            return
        explodiu[0] = True
        try:
            alvo.opacity = 0
            from efeitos import explodir_estilhacos
            explodir_estilhacos(alvo, fim)
        except Exception as e:
            print(f"[fatiar] explosao: {e}")
            fim()

    try:
        W, H = Window.size
        rx, ry, rw, rh = _ret_janela(alvo)
        cam = Widget(size_hint=(None, None), size=(W, H), pos=(0, 0))
        camada[0] = cam
        Window.add_widget(cam)
        alt_boneco = max(dp(58), min(rh * 1.6, dp(86), H * 0.14))
        ps = max(2, int(round(alt_boneco / 26.0)))
        k = K.KiritoPixel(ps=ps)
        faiscas = K.Faiscas()
        cam.add_widget(k)
        cam.add_widget(faiscas)
        cy = ry + rh / 2.0
        bx0, by0, bx1, by1 = _limites()
        area = (bx0, by0, bx1, by1)
        meio = (bx0 + bx1) / 2.0
        esquerda = ((rx + rw / 2.0) < meio) if rw < (bx1 - bx0) * 0.7 else (random.random() < 0.5)
        pe = 8 * ps + dp(2)
        ini = (bx0 + pe, cy) if esquerda else (bx1 - pe, cy)
        k.rotacao = -90 if esquerda else 90
        k.espelhar = not esquerda
        k.ancorar(*ini)
        k.mostrar(K.POSE_A['grudado'])
        k.opacity = 0
        golpe = [K.POSE_A[n] for n in ('arma1', 'corta_desce', 'segue_desce')]
        k.precarregar([K.POSE_A[n] for n in ('agacha', 'pulo')] + golpe)
        faiscas.estourar(ini[0], ini[1], CIANO, n=8, forca=dp(70), tam=ps)
        # ataca pelo canto do widget do lado de onde veio, inteiro no quadro
        ataque = _no_quadro(k, rx - dp(6) if esquerda else rx + rw + dp(6), cy + rh * 0.35,
                            golpe, area, dp(2))
        saida = (bx1 + dp(80), cy + dp(60)) if esquerda else (bx0 - dp(80), cy + dp(60))

        def _fade_in(dt):
            k.opacity = min(1.0, k.opacity + dt / 0.18)
            return k.opacity < 1
        Clock.schedule_interval(_fade_in, 1 / 60.)

        def _pula():
            k.tocar(K.sequencia([(3, K.POSE_A['agacha']), (1, K.POSE_A['pulo'])]))
            Clock.schedule_once(lambda dt: _mover(
                k, k.ancora(), ataque, 0.26, altura=rh * 0.8 + dp(20),
                rot=(k.rotacao, 0), on_fim=_golpe), 0.1)

        def _golpe():
            k.rotacao = 0
            k.espelhar = not esquerda
            seq = K.sequencia([(2, K.POSE_A['arma1']), (1, K.smear(K.POSE_A['corta_desce'], 112)),
                               (4, K.POSE_A['segue_desce']), (1, K.POSE_A['segue_desce'])])
            k.tocar(seq, on_quadro=lambda i: i == 2 and _impacto(), on_fim=_sai)

        def _impacto():
            ccx, ccy = rx + rw / 2.0, ry + rh / 2.0
            cam.add_widget(CorteMeiaLua(
                centro=(ccx, ccy), raio=rw * 0.62, ang_ini=165 if esquerda else 15,
                ang_fim=-40 if esquerda else 220, espessura=max(dp(10), rh * 0.55),
                achat=0.35, rotacao=-8 if esquerda else 8))
            faiscas.estourar(ccx, ccy, CIANO, n=18, forca=dp(170), tam=ps)
            _som('corte')
            _tremer(8)
            pecas = _metades(cam, alvo, rx, ry, rw, rh)
            alvo.opacity = 0
            t = [0.0]

            def _separa(dt):
                try:
                    t[0] += dt
                    u = min(1.0, t[0] / 0.32)
                    e = 1 - (1 - u) ** 2
                    for w, tr, rot, c, s in pecas:
                        tr.xy = (-s * dp(10) * e, s * dp(12) * e)
                        rot.angle = s * 5 * e
                        c.a = 1 - 0.35 * e
                    if u >= 1:
                        for w, *_ in pecas:
                            if w.parent:
                                w.parent.remove_widget(w)
                        _explodir()
                        return False
                except Exception as ex:
                    print(f"[fatiar] separar: {ex}")
                    _explodir()
                    return False
            Clock.schedule_interval(_separa, 1 / 60.)

        def _sai():
            k.mostrar(K.POSE_A['pulo'])
            _som('pulo')
            _mover(k, k.ancora(), saida, 0.3, altura=dp(40), on_fim=_limpa)

        def _limpa():
            k.parar()
            Clock.schedule_once(lambda dt: _remover_da_janela(cam), 0.4)

        Clock.schedule_once(lambda dt: _pula(), 0.22)
        # seguranca: se algo travar, apaga mesmo assim e limpa a camada
        Clock.schedule_once(lambda dt: _explodir(), 3.5)
        Clock.schedule_once(lambda dt: _remover_da_janela(cam), 6.0)
    except Exception as e:
        print(f"[fatiar] ignorado: {e}")
        _remover_da_janela(camada[0])
        _explodir()


def kirito_wipe(widgets, on_fim=None):
    """WIPE: Kirito desce no meio da tela, saca as duas espadas e faz um
    combo cortando a lista inteira; cada golpe desintegra um grupo de itens."""
    fim = _Uma(on_fim)
    camada = [None]
    try:
        W, H = Window.size
        vis = []
        for w in widgets:
            try:
                x, y, ww, hh = _ret_janela(w)
                if y + hh > 0 and y < H and ww > 0:
                    vis.append((w, x, y, ww, hh))
            except Exception:
                pass
        vis.sort(key=lambda t: -t[2])                 # de cima para baixo
        cam = Widget(size_hint=(None, None), size=(W, H), pos=(0, 0))
        camada[0] = cam
        Window.add_widget(cam)
        ps = _ps_para(W, H)
        k = K.KiritoPixel(ps=ps)
        faiscas = K.Faiscas(n_max=120)
        cam.add_widget(k)
        cam.add_widget(faiscas)
        topo = max((y + hh for _, _, y, _, hh in vis), default=H * 0.7)
        base = min((y for _, _, y, _, _ in vis), default=H * 0.2)
        bx0, by0, bx1, by1 = _limites()
        area = (bx0, by0, bx1, by1)
        cx = (bx0 + bx1) / 2.0
        W = bx1 - bx0                                 # largura util (coluna)
        k.ancorar(cx, H + dp(60))
        k.mostrar(K.POSE_A['pulo'])
        k.precarregar([K.POSE_A[n] for n in K.POSE_A])
        _precarregar_sons(['sacar', 'corte', 'corte2', 'titulo', 'pulo'])
        grupos = [vis[i::4] for i in range(4)]
        golpes = [(0.20, 1, CIANO), (0.50, -1, AZUL), (0.35, 1, CIANO), (0.70, -1, AZUL)]
        poses_x = [K.POSE_A['x_arma'], K.POSE_A['x_corta']]

        def _desintegra(itens):
            from efeitos import explodir_estilhacos
            for w, *_ in itens:
                try:
                    explodir_estilhacos(w, lambda: None)
                except Exception as e:
                    print(f"[wipe] item: {e}")

        def _golpe(i):
            if i >= len(golpes):
                _final()
                return
            fy, lado, cor = golpes[i]
            y = base + (topo - base) * (1 - fy)
            k.espelhar = lado < 0
            alvo = _no_quadro(k, cx - lado * W * 0.28, y, poses_x, area, dp(2))

            def _ataca():
                k.espelhar = lado < 0
                seq = K.sequencia([(2, K.POSE_A['x_arma']), (1, K.smear(K.POSE_A['x_corta'], 140)),
                                   (3, K.POSE_A['x_corta']), (1, K.POSE_A['x_corta'])])

                def _q(q):
                    if q == 2:
                        cam.add_widget(CorteMeiaLua(
                            centro=(cx, y), raio=W * 0.55, ang_ini=165 if lado > 0 else 15,
                            ang_fim=-35 if lado > 0 else 215, espessura=dp(40),
                            achat=0.3, rotacao=-10 * lado, cor=cor))
                        faiscas.estourar(cx, y, cor, n=22, forca=dp(220), tam=ps)
                        _som('corte2' if cor == AZUL else 'corte')
                        _tremer(10)
                        _desintegra(grupos[i])
                k.tocar(seq, on_quadro=_q, on_fim=lambda: _golpe(i + 1))
            _mover(k, k.ancora(), alvo, 0.16, altura=dp(30), cor_fantasma=cor, on_fim=_ataca)

        def _saca():
            seq = K.sequencia([(3, K.POSE_A['pega2']), (3, K.POSE_A['saca2']),
                               (3, K.POSE_A['dupla']), (1, K.POSE_A['dupla'])])

            def _q(i):
                if i == 4:
                    mx, my = k.ponto_mao(2)
                    faiscas.estourar(mx, my, AZUL, n=16, forca=dp(120), tam=ps)
                    _som('sacar')
            k.tocar(seq, on_quadro=_q, on_fim=lambda: _golpe(0))

        def _final():
            k.espelhar = False
            alvo = _no_quadro(k, cx, (topo + base) / 2.0,
                              [K.POSE_A['final_arma'], K.POSE_A['final']], area, dp(2))

            def _ataca():
                k.espelhar = False
                seq = K.sequencia([(4, K.POSE_A['final_arma']), (1, K.smear(K.POSE_A['final'], 130)),
                                   (8, K.POSE_A['final']), (1, K.POSE_A['final'])])

                def _q(q):
                    if q == 4:
                        for sent, cor in ((1, CIANO), (-1, AZUL)):
                            cam.add_widget(CorteMeiaLua(
                                centro=(cx, alvo[1]), raio=max(W, H) * 0.5, ang_ini=160 if sent > 0 else 20,
                                ang_fim=-45 if sent > 0 else 225, espessura=dp(70), achat=0.5,
                                rotacao=35 * sent, cor=cor, dur_cheio=5 / 30.0, dur_decai=9 / 30.0))
                        faiscas.estourar(cx, alvo[1], CIANO, n=60, forca=dp(380), tam=ps)
                        _som('titulo')
                        _tremer(28)
                k.tocar(seq, on_quadro=_q, on_fim=_sai)
            _mover(k, k.ancora(), alvo, 0.2, altura=dp(50), on_fim=_ataca)

        def _sai():
            k.mostrar(K.POSE_A['pulo'])
            _som('pulo')
            _mover(k, k.ancora(), (cx + dp(40), H + dp(120)), 0.35, on_fim=_acabou)

        def _acabou():
            k.parar()
            _remover_da_janela(cam)
            fim()

        _mover(k, (cx, H + dp(60)), (cx, topo + dp(10)), 0.3, on_fim=_saca)

        def _seguranca(dt):
            _remover_da_janela(cam)
            fim()
        Clock.schedule_once(_seguranca, 7.0)
    except Exception as e:
        print(f"[wipe] ignorado: {e}")
        _remover_da_janela(camada[0])
        fim()
