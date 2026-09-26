"""
cenas.py — TraveteFocus
Cenas com o Kirito pixel art (kirito.py) + cortes em meia-lua (espadachim.py):

  cena_titulo(tela, label, on_fim)  Kirito pendurado por uma mao num canto de
                                    cima, solta, saca num iai e escreve
                                    "TRAVETE FOCUS" em cima das letras. No
                                    golpe final (estilo Bleach) junta as duas
                                    espadas numa so, a espada suga o infinito
                                    da tela como reiatsu, evolui e solta uma
                                    onda de energia que completa a frase.
                                    Sempre inteiro no quadro; sai num teleporte.
  KiritoPin(caixa)                  espia por cima da caixa do PIN, com
                                    expressoes: pulinho nas teclas, susto no
                                    erro, balanca a cabeca no bloqueio e, no
                                    acerto, sobe na caixa e some num teleporte.
  kirito_fatiar(widget, on_fim)     mini Kirito se materializa, fatia o item
                                    que sera apagado e some num teleporte.
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
BRANCO = (1.0, 1.0, 1.0)

# efeitos que as cenas tocam (pre-carregados no inicio de cada cena)
_SONS_TITULO = ['agarra', 'koiguchi', 'pulo', 'pouso', 'sacar_iai', 'corte', 'sacar',
                'corte2', 'habilidade', 'voz_starburst', 'voz_stream', 'fusao', 'reiatsu',
                'absorve', 'carga', 'getsuga', 'separa', 'desliza', 'embainhar', 'titulo',
                'teleporte']
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


def _com(p, **kw):
    """Copia da pose com alguns campos trocados (ex: expressao, emote)."""
    q = dict(p)
    q.update(kw)
    return q


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


def _mover(k, de, para, dur, altura=0.0, rot=None, fantasmas=3,
           cor_fantasma=CIANO, on_fim=None, linear=False, cada=None, on_passo=None,
           ease=None, limite=None):
    """Move a ancora do Kirito em arco (parabola de `altura`), girando de
    rot[0] a rot[1]. Deixa `fantasmas` copias nitidas espalhadas pelo
    caminho (uma por quadro embolava num rastro de fumaca).
    ease: 'out' (desacelera), 'in' (acelera, queda) ou 'linear'.
    limite=(area, folga): o boneco (girado como estiver) nunca sai da area.
    on_passo(u) e chamado a cada quadro com o progresso 0..1."""
    t = [0.0]
    feito = [False]
    n_f = 3 if fantasmas is True else int(fantasmas or 0)
    marcas = [(i + 1) / float(n_f + 1) for i in range(n_f)]
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
            while marcas and u >= marcas[0]:
                marcas.pop(0)
                k.fantasma(cor=cor_fantasma, alfa=0.42, duracao=0.24)
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
#  EFEITOS DE CENA: camera, clarao, fundo, aneis, teleporte
# ═══════════════════════════════════════════════════════════════════
class _Camera:
    """Zoom da tela toda (infinito, titulo e Kirito juntos) em volta de um
    ponto: enquadramento de cinema nos momentos fortes."""

    def __init__(self, tela):
        self.tela = tela
        self._ev = None
        self.zoom = 1.0
        self.foco = (tela.width / 2.0, tela.height / 2.0)
        self._sc = Scale(1, 1, 1)
        try:
            tela.canvas.before.add(self._sc)       # depois do Translate da tela
        except Exception as e:
            print(f"[camera] {e}")
            self._sc = None

    def ir(self, zoom, foco=None, dur=0.6, foco_fn=None):
        if self._sc is None:
            return
        if self._ev is not None:
            self._ev.cancel()
        z0, f0 = self.zoom, self.foco
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur) if dur > 0 else 1.0
                e = u * u * (3 - 2 * u)
                alvo = foco_fn() if foco_fn else (foco or f0)
                self.zoom = z0 + (zoom - z0) * e
                self.foco = (f0[0] + (alvo[0] - f0[0]) * e, f0[1] + (alvo[1] - f0[1]) * e)
                if self._sc is not None:
                    self._sc.origin = self.foco
                    self._sc.x = self._sc.y = self.zoom
                if u >= 1:
                    self._ev = None
                    return False
            except Exception as ex:
                print(f"[camera] {ex}")
                return False
        self._ev = Clock.schedule_interval(_p, 1 / 60.)

    def soltar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self._sc is not None:
            try:
                self.tela.canvas.before.remove(self._sc)
            except Exception:
                pass
            self._sc = None


def _brilho_tela(camada, alfa=0.35, dur=0.18, cor=BRANCO):
    """Clarao na tela inteira (impacto)."""
    try:
        W, H = camada.size
        w = Widget(size_hint=(None, None), size=(0, 0))
        with w.canvas:
            c = Color(cor[0], cor[1], cor[2], alfa)
            Rectangle(pos=(-W, -H), size=(W * 3, H * 3))
        camada.add_widget(w)
        t = [0.0]

        def _p(dt):
            t[0] += dt
            c.a = alfa * max(0.0, 1 - t[0] / dur)
            if t[0] >= dur:
                if w.parent:
                    w.parent.remove_widget(w)
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[cena] clarao: {e}")


def _fundo(tela, reator=None, barra=None, dur=0.6):
    """Escurece/acende o fundo da loading (infinito e barra): durante a luta
    o foco fica no Kirito e no titulo."""
    try:
        from kivy.animation import Animation
        ids = getattr(tela, 'ids', {})
        for nome, alvo in (('reator_shader', reator), ('barra_loading', barra)):
            w = ids.get(nome) if hasattr(ids, 'get') else None
            if w is not None and alvo is not None:
                Animation.cancel_all(w, 'opacity')
                Animation(opacity=alvo, duration=dur).start(w)
    except Exception as e:
        print(f"[cena] fundo: {e}")


def _anel(camada, centro, r0, r1, dur, cor=CIANO, esp=None, achat=1.0):
    """Onda de choque: anel que abre e some."""
    try:
        cx, cy = centro
        e0 = esp or dp(3)
        w = Widget(size_hint=(None, None), size=(0, 0))
        with w.canvas:
            c = Color(cor[0], cor[1], cor[2], 0.9)
            ln = Line(ellipse=(cx - r0, cy - r0 * achat, 2 * r0, 2 * r0 * achat), width=e0)
        camada.add_widget(w)
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur)
                e = 1 - (1 - u) ** 3
                r = r0 + (r1 - r0) * e
                ln.ellipse = (cx - r, cy - r * achat, 2 * r, 2 * r * achat)
                ln.width = max(1.0, e0 * (1 - u))
                c.a = 0.9 * (1 - u)
                if u >= 1:
                    if w.parent:
                        w.parent.remove_widget(w)
                    return False
            except Exception:
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[cena] anel: {e}")


def _clarao_boneco(k, dur=0.3, de=1.0):
    """O boneco fica branco e volta a cor (fusao das espadas)."""
    t = [0.0]

    def _p(dt):
        try:
            t[0] += dt
            k.clarao = de * max(0.0, 1 - t[0] / dur)
            return t[0] < dur
        except Exception:
            return False
    Clock.schedule_interval(_p, 1 / 60.)


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


def _textura_radial():
    try:
        from infinito import textura_radial
        return textura_radial()
    except Exception:
        return None


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
                ra = larg * (0.6 + 1.2 * u)
                anel.ellipse = (ax - ra, base - dp(3) - u * dp(3), ra * 2, dp(6) + u * dp(6))
                c_anel.a = 0.9 * (1 - u)
                h = alt * min(1.0, u / 0.3)
                lw = larg * (1 - 0.55 * max(0.0, (u - 0.45) / 0.55))
                r_col.size = (lw, h)
                r_col.pos = (ax - lw / 2.0, base)
                r_nuc.size = (lw / 3.0, h * 0.9)
                r_nuc.pos = (ax - lw / 6.0, base)
                c_col.a = 0.55 * min(1.0, u / 0.15) * (1 - max(0.0, (u - 0.6) / 0.4))
                c_nuc.a = 0.8 * min(1.0, u / 0.15) * (1 - max(0.0, (u - 0.5) / 0.5))
                k.clarao = min(1.0, u / 0.25)
                if u > 0.25:
                    v = (u - 0.25) / 0.75
                    k.escala_x = max(0.04, 1 - v)
                    k.escala_y = 1 + 0.6 * v
                    k.opacity = max(0.0, 1 - v * 1.15)
                if cont[0] % 3 == 0 and u < 0.85:
                    faiscas.estourar(ax + random.uniform(-larg * 0.4, larg * 0.4),
                                     base + random.uniform(0, (baixo + cima) * 0.9),
                                     random.choice((cor, BRANCO)), n=2,
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


def _materializar(k, camada, faiscas, dur=0.32, on_fim=None, cor=CIANO):
    """Entrada de teleporte (o contrario do _teleporte): um anel se fecha,
    faiscas caem para o boneco e ele aparece branco, ganhando cor."""
    fim = _Uma(on_fim)
    try:
        ax, ay = k.ancora()
        esq, baixo, dir_, cima = k.extensao()
        r = max(esq + dir_, baixo + cima) * 0.7
        k.opacity = 0
        k.clarao = 1.0
        _som('materializa')
        w = Widget(size_hint=(None, None), size=(0, 0))
        with w.canvas:
            c = Color(cor[0], cor[1], cor[2], 0)
            ln = Line(circle=(ax, ay, r), width=dp(1.6))
        camada.add_widget(w)
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur)
                rr = max(1.0, r * (1 - u))
                ln.circle = (ax, ay, rr)
                c.a = 0.85 * (1 - u * 0.6)
                k.opacity = min(1.0, u * 2.2)
                k.clarao = 1.0 - u
                if random.random() < 0.6:
                    ang = random.uniform(0, 2 * math.pi)
                    faiscas.estourar(ax + math.cos(ang) * rr, ay + math.sin(ang) * rr,
                                     random.choice((cor, BRANCO)), n=1, forca=dp(20),
                                     tam=max(2, k.ps * 0.7), gravidade=0)
                if u >= 1:
                    k.clarao = 0.0
                    k.opacity = 1.0
                    if w.parent:
                        w.parent.remove_widget(w)
                    faiscas.estourar(ax, ay, cor, n=10, forca=dp(90), tam=max(2, k.ps * 0.8))
                    fim()
                    return False
            except Exception as e:
                print(f"[cena] materializar: {e}")
                k.opacity = 1.0
                k.clarao = 0.0
                fim()
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[cena] materializar ignorado: {e}")
        k.opacity = 1.0
        fim()


# ═══════════════════════════════════════════════════════════════════
#  GOLPE FINAL: aura da espada, fluxo do infinito e onda de energia
# ═══════════════════════════════════════════════════════════════════
class _AuraEspada(Widget):
    """Brilho de reiatsu em volta da lamina da espada fundida: acompanha o
    Kirito a cada quadro e solta faiscas subindo. `alvo` 0..1 (forca)."""

    def __init__(self, k, faiscas, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k = k
        self.faiscas = faiscas
        self.forca = 0.0
        self.alvo = 0.0
        self._t = 0.0
        tex = _textura_radial()
        with self.canvas:
            PushMatrix()
            self._rot = Rotate(angle=0, origin=(0, 0))
            self._c1 = Color(0.2, 0.85, 1.0, 0)
            self._r1 = Rectangle(texture=tex, size=(0, 0))
            self._c2 = Color(0.85, 1.0, 1.0, 0)
            self._r2 = Rectangle(texture=tex, size=(0, 0))
            PopMatrix()
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            self._t += dt
            self.forca += (self.alvo - self.forca) * (1 - math.exp(-dt * 5))
            k = self.k
            p = k._base
            if (k.parent is None or k.opacity < 0.05 or p.get('a1') is None
                    or p.get('tipo1', 1) < 3 or self.forca < 0.01):
                self._c1.a = self._c2.a = 0
                return
            hx, hy = k.ponto_mao(1)
            tx, ty = k.ponta_espada(1)
            comp = math.hypot(tx - hx, ty - hy) or 1.0
            ang = math.degrees(math.atan2(ty - hy, tx - hx))
            cx, cy = (hx + tx) / 2.0, (hy + ty) / 2.0
            f = self.forca
            tremor = 0.85 + 0.15 * math.sin(self._t * 23) + 0.05 * random.random()
            self._rot.origin = (cx, cy)
            self._rot.angle = ang
            l1, w1 = comp * 1.3, k.ps * (6 + 6 * f)
            self._r1.pos, self._r1.size = (cx - l1 / 2, cy - w1 / 2), (l1, w1)
            self._c1.a = 0.55 * f * tremor
            l2, w2 = comp * 1.08, k.ps * (2 + 2 * f)
            self._r2.pos, self._r2.size = (cx - l2 / 2, cy - w2 / 2), (l2, w2)
            self._c2.a = 0.75 * f * tremor
            if random.random() < f * 0.8:          # reiatsu subindo da lamina
                s = random.random()
                self.faiscas.estourar(hx + (tx - hx) * s, hy + (ty - hy) * s,
                                      random.choice((CIANO, BRANCO, (0.12, 0.25, 0.6))), n=1,
                                      forca=dp(28), tam=max(2, k.ps * 0.6), gravidade=-dp(240))
        except Exception as e:
            print(f"[aura] {e}")
            self._c1.a = self._c2.a = 0

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)


class _Fluxo(Widget):
    """Fios de luz arrancados do infinito e sugados em espiral para a ponta
    da espada (o reiatsu da tela)."""
    _N = 110

    def __init__(self, reator, alvo_fn, dur, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.reator = reator
        self.alvo_fn = alvo_fn
        self._dur = dur
        self._t = 0.0
        self._acum = 0.0
        self._p = []
        self._ins = []
        with self.canvas:
            for _ in range(self._N):
                c = Color(1, 1, 1, 0)
                ln = Line(points=[0, 0, 0, 0], width=dp(1.5), cap='round')
                self._ins.append((c, ln))
        self._livres = list(range(self._N))
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            self._t += dt
            u = self._t / self._dur
            ax, ay = self.alvo_fn()
            pts = getattr(self.reator, 'pontos_atuais', None) or []
            cor = tuple(getattr(self.reator, '_cor', CIANO))
            taxa = 90 * math.sin(math.pi * min(1.0, max(0.0, u)))
            self._acum += dt * taxa
            while self._acum >= 1 and self._livres and pts and u < 1:
                self._acum -= 1
                x, y = random.choice(pts)
                i = self._livres.pop()
                mistura = random.random() * 0.6
                c = tuple(cor[j] + (1 - cor[j]) * mistura for j in range(3))
                self._p.append([x, y, 0.0, 0.0, c, i, 0.0])
            vivas = []
            # o giro diminui com o tempo: a espiral fecha e tudo cai na ponta
            # (com giro constante alguns fios ficavam orbitando para sempre)
            giro = 0.45 * max(0.0, 1.0 - u)
            acc = dp(2400) * (1.0 if u < 1 else 3.0)
            for q in self._p:
                q[6] += dt
                dx, dy = ax - q[0], ay - q[1]
                d = math.hypot(dx, dy) or 1.0
                c, ln = self._ins[q[5]]
                if d < dp(10) or q[6] > 1.4 or u > 1.35:
                    c.a = 0
                    ln.points = [0, 0, 0, 0]
                    self._livres.append(q[5])
                    continue
                q[2] += (dx / d - dy / d * giro) * acc * dt
                q[3] += (dy / d + dx / d * giro) * acc * dt
                q[2] *= 0.93
                q[3] *= 0.93
                q[0] += q[2] * dt
                q[1] += q[3] * dt
                vn = math.hypot(q[2], q[3]) or 1.0
                comp = min(dp(30), vn * 0.035)
                ln.points = [q[0], q[1], q[0] - q[2] / vn * comp, q[1] - q[3] / vn * comp]
                c.rgba = (q[4][0], q[4][1], q[4][2], 0.9 * min(1.0, (1.4 - q[6]) / 0.3))
                vivas.append(q)
            self._p = vivas
            if u >= 1.0 and not vivas:
                self.parar()
                return False
        except Exception as e:
            print(f"[fluxo] {e}")
            self.parar()
            return False

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)


class _OndaGetsuga(Widget):
    """Onda de energia em meia-lua (miolo escuro, brilho ciano e borda
    branca) varrendo a frase: o ultimo golpe da espada evoluida."""

    def __init__(self, x0, x1, cy, altura, dur, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.x0, self.x1, self.cy = x0, x1, cy
        self.R = altura / 2.0
        self.dur = dur
        self._t = 0.0
        n = 26
        self._n = n
        idx = list(range(2 * (n + 1)))
        with self.canvas:
            self._c_glow = Color(0.2, 0.85, 1.0, 0)
            self._m_glow = Mesh(mode='triangle_strip', indices=idx, vertices=[0] * (8 * (n + 1)))
            self._c_corpo = Color(0.02, 0.03, 0.08, 0)
            self._m_corpo = Mesh(mode='triangle_strip', indices=idx, vertices=[0] * (8 * (n + 1)))
            self._c_borda = Color(0.85, 1.0, 1.0, 0)
            self._borda = Line(points=[0, 0, 0, 0], width=dp(2.2))
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _crescente(self, cx, escala, espessura):
        """Meia-lua virada para a direita: ")" grossa no meio, fina nas pontas."""
        R = self.R * escala
        a = R * 0.42
        vs, borda = [], []
        for i in range(self._n + 1):
            t = -math.pi / 2 + math.pi * i / self._n
            ex, ey = cx + math.cos(t) * a, self.cy + math.sin(t) * R
            w = espessura * math.cos(t)
            ix, iy = ex - w, self.cy + math.sin(t) * R * 0.94
            vs.extend((ex, ey, 0, 0, ix, iy, 0, 0))
            borda.extend((ex, ey))
        return vs, borda

    def _tick(self, dt):
        try:
            self._t += dt
            u = min(1.0, self._t / self.dur)
            e = u * u * (3 - 2 * u)
            cx = self.x0 + (self.x1 - self.x0) * e
            aparece = min(1.0, self._t / 0.06)
            some = 1.0 - max(0.0, (self._t - self.dur) / 0.25)
            a = aparece * max(0.0, some)
            esp = self.R * 0.55
            vg, _ = self._crescente(cx, 1.22, esp * 1.35)
            vc, borda = self._crescente(cx, 1.0, esp)
            self._m_glow.vertices = vg
            self._m_corpo.vertices = vc
            self._borda.points = borda
            self._c_glow.a = 0.45 * a
            self._c_corpo.a = 0.92 * a
            self._c_borda.a = (0.8 + 0.2 * math.sin(self._t * 40)) * a
            if some <= 0:
                self.parar()
                return False
        except Exception as ex:
            print(f"[getsuga] {ex}")
            self.parar()
            return False

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)


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
    alvo = min(dp(125), largura * 0.32, altura * 0.155)     # altura do boneco
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


class _NomeGolpe(Widget):
    """Nome da habilidade no estilo SAO: '- DUAL BLADES -' pequeno em cima e
    'STARBURST STREAM' grande, com brilho e linhas saindo dos lados.
    parte1(): 'STARBURST' aparece letra a letra; parte2(): 'STREAM' chega
    num impacto; sumir(): apaga tudo."""

    def __init__(self, cx, cy, largura_max, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        from kivy.metrics import sp
        # a Orbitron e larga: mede de verdade e encolhe ate caber (sobra
        # espaco nos lados para as linhas), senao corta em tela pequena
        fs = max(sp(12), min(sp(26), largura_max / 12.0))
        cabe = largura_max * 0.8
        for tentativa in range(3):
            t1 = CoreLabel(text="STARBURST", font_name="orbitron.ttf", font_size=fs, bold=True)
            t1.refresh()
            t2 = CoreLabel(text="STREAM", font_name="orbitron.ttf", font_size=fs, bold=True)
            t2.refresh()
            largura = t1.texture.width + fs * 0.55 + t2.texture.width
            if largura <= cabe or tentativa == 2:
                break
            fs = max(sp(9), fs * cabe / largura * 0.98)
        t0 = CoreLabel(text="-  DUAL BLADES  -", font_name="orbitron.ttf", font_size=max(sp(7), fs * 0.42))
        t0.refresh()
        self._tex1, self._tex2, self._tex0 = t1.texture, t2.texture, t0.texture
        w1, h1 = self._tex1.size
        w2, h2 = self._tex2.size
        esp = fs * 0.55
        total = w1 + esp + w2
        self._x1 = cx - total / 2.0
        self._x2 = self._x1 + w1 + esp
        self._y = cy - h1 / 2.0
        self._cx, self._cy, self._h = cx, cy, h1
        self._total = total
        with self.canvas:
            self._c_ln = Color(0.0, 0.9, 1.0, 0)
            self._ln_e = Line(points=[cx, cy, cx, cy], width=dp(1.3))
            self._ln_d = Line(points=[cx, cy, cx, cy], width=dp(1.3))
            self._c_sub = Color(0.6, 0.95, 1.0, 0)
            w0, h0 = self._tex0.size
            self._r_sub = Rectangle(texture=self._tex0, size=(w0, h0),
                                    pos=(cx - w0 / 2.0, self._y + h1 + dp(4)))
            # brilho (copia maior e ciano atras das letras)
            PushMatrix()
            self._sc_g = Scale(1.06, 1.18, 1, origin=(cx, cy))
            self._c_g1 = Color(0.0, 0.8, 1.0, 0)
            self._r_g1 = Rectangle(texture=self._tex1, size=(w1, h1), pos=(self._x1, self._y))
            self._c_g2 = Color(0.0, 0.8, 1.0, 0)
            self._r_g2 = Rectangle(texture=self._tex2, size=(w2, h2), pos=(self._x2, self._y))
            PopMatrix()
            self._c_1 = Color(1, 1, 1, 0)
            self._r_1 = Rectangle(texture=self._tex1, size=(0, h1), pos=(self._x1, self._y))
            PushMatrix()
            self._sc_2 = Scale(1, 1, 1, origin=(self._x2 + w2 / 2.0, cy))
            self._c_2 = Color(1, 1, 1, 0)
            self._r_2 = Rectangle(texture=self._tex2, size=(w2, h2), pos=(self._x2, self._y))
            PopMatrix()
        self._ev = None
        self._t1 = self._t2 = self._tsome = None
        self._t = 0.0

    def parte1(self):
        self._t1 = self._t
        self._ligar()

    def parte2(self):
        self._t2 = self._t
        self._ligar()

    def sumir(self):
        self._tsome = self._t
        self._ligar()

    def _ligar(self):
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            self._t += dt
            some = 1.0
            if self._tsome is not None:
                some = max(0.0, 1 - (self._t - self._tsome) / 0.45)
            w1, h1 = self._tex1.size
            if self._t1 is not None:
                u = min(1.0, (self._t - self._t1) / 0.55)
                w = max(1.0, w1 * u)
                self._r_1.texture = self._tex1.get_region(0, 0, w, h1)
                self._r_1.size = (w, h1)
                self._c_1.a = some
                self._c_g1.a = 0.35 * some * (0.8 + 0.2 * math.sin(self._t * 14))
                self._c_sub.a = 0.85 * min(1.0, u * 2) * some
                abre = min(1.0, (self._t - self._t1) / 0.35)
                meia = self._total / 2.0 + dp(10)
                alcance = meia + dp(34) * abre
                self._ln_e.points = [self._cx - meia, self._cy, self._cx - alcance, self._cy]
                self._ln_d.points = [self._cx + meia, self._cy, self._cx + alcance, self._cy]
                self._c_ln.a = 0.9 * abre * some
            if self._t2 is not None:
                u2 = min(1.0, (self._t - self._t2) / 0.16)
                s = 1.7 - 0.7 * (1 - (1 - u2) ** 3)
                self._sc_2.x = self._sc_2.y = s
                clarao = max(0.0, 1 - (self._t - self._t2) / 0.3)
                self._c_2.rgba = (1, 1, 1, min(1.0, u2 * 1.5) * some)
                self._c_g2.a = (0.35 + 0.5 * clarao) * some
                self._c_g1.a = (0.35 + 0.4 * clarao) * some
                self._sc_g.x = 1.06 + 0.08 * clarao
                self._sc_g.y = 1.18 + 0.25 * clarao
            if self._tsome is not None and some <= 0:
                self.parar()
                return False
        except Exception as e:
            print(f"[nome golpe] {e}")
            self.parar()
            return False

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)


def cena_titulo(tela, label, on_fim=None, texto="TRAVETE FOCUS"):
    """Kirito pendurado por uma mao num canto de cima, a outra no cabo da
    Elucidator: kamae, solta, iai na cintura; saca a Dark Repulser e segue o
    combo em cima das letras. No golpe final junta as duas espadas, suga o
    infinito da tela para a lamina, que evolui, e solta uma onda de energia
    que completa a frase. Pousa na frase, separa as espadas, embainha
    devagar - e so no clique da guarda a frase explode. Sai num teleporte,
    sem nunca deixar o quadro."""
    fim = _Uma(on_fim)
    camada = Widget(size_hint=(None, None), size=tela.size, pos=(0, 0))
    ag = _Agenda()
    camada._agenda = ag
    cam = [None]
    estado = {'reator': None, 'aura': None}

    def restaurar_fundo():
        try:
            if cam[0] is not None:
                cam[0].soltar()
            r = estado['reator']
            if r is not None and r.opacity < 0.99 and not getattr(r, '_absorvido', False):
                r.restaurar()
                _fundo(tela, reator=1.0, barra=1.0, dur=0.3)
        except Exception as e:
            print(f"[cena] restaurar fundo: {e}")

    camada._restaurar = restaurar_fundo

    def encerrar():
        ag.parar()
        if cam[0] is not None:
            cam[0].soltar()
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
        faiscas = K.Faiscas(n_max=140)
        ps = _ps_para(W, H)
        kk = K.KiritoPixel(ps=ps)
        kk.opacity = 0
        aura = _AuraEspada(kk, faiscas)
        estado['aura'] = aura
        camada.add_widget(aura)
        camada.add_widget(kk)
        camada.add_widget(faiscas)
        cam[0] = _Camera(tela)
        try:
            estado['reator'] = tela.ids.get('reator_shader')
        except Exception:
            estado['reator'] = None
        alt = 24 * ps
        th = titulo.th
        m = max(dp(4), ps)                              # folga ate a borda do quadro
        P = K.POSE_A
        kk.precarregar([P[n] for n in P])
        _precarregar_sons(_SONS_TITULO)
        ox_t, oy_t = titulo._origem()
        pe = kk.extensao(P['guardado'])[1] - ps         # ancora -> sola da bota
        # a luta acontece EM CIMA das letras (elas ficam sempre a vista)
        y_topo = oy_t + th * 0.82 + pe

        def quadro(x, y, poses):
            return _no_quadro(kk, x, y, [P[n] if isinstance(n, str) else n for n in poses], area, m)

        def corte_trecho(i, cor, sentido=1, som_corte='corte', cor2=None, arco=None,
                         achat=0.42):
            i0, i1 = _TRECHOS[i]
            cx, cy = titulo.x_do_trecho(i0, i1)
            larg = max(titulo._larg[i1] - titulo._larg[i0], th)
            a0, a1 = arco or ((160, -150) if sentido > 0 else (20, 330))
            camada.add_widget(CorteMeiaLua(centro=(cx, cy), raio=larg * 0.95, ang_ini=a0,
                                           ang_fim=a1, espessura=th * 0.9, achat=achat, cor=cor))
            if cor2 is not None:           # a segunda lamina: meia-lua junto, um pouco defasada
                d = 22 if a1 > a0 else -22
                camada.add_widget(CorteMeiaLua(centro=(cx, cy - th * 0.08), raio=larg * 0.82,
                                               ang_ini=a0 - d, ang_fim=a1 - d,
                                               espessura=th * 0.7, achat=achat, cor=cor2))
                _som('corte2')
            titulo.revelar(i0, i1, cor=(1, 1, 1) if cor == CIANO else AZUL)
            faiscas.estourar(cx, cy, cor, n=18, forca=dp(170), tam=ps)
            _som(som_corte)
            _tremer(6)
            _brilho_tela(camada, 0.10, 0.12)
            kk.pausar(0.07)                              # hit-stop
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
            seq = K.sequencia([(3, P['pendurado_b']), (1, P['pendurado_b']),
                               (1, _com(P['pendurado2'], olhos='s'))])
            kk.tocar(seq)
            kk.empurrar(capa=-6, lift=4)

            def _koiguchi():
                bx, by = kk.ponto_mao(1)
                faiscas.estourar(bx + (ps if lado < 0 else -ps), by, BRANCO, n=5,
                                 forca=dp(35), tam=max(2, ps * 0.7), gravidade=0)
                _som('koiguchi')
            ag.depois(0.2, _koiguchi)
        ag.depois(1.05, _kamae)
        # o fundo (infinito e barra) apaga: o foco vai para o Kirito e a frase
        ag.depois(1.5, lambda: _fundo(tela, reator=0.32, barra=0.2, dur=0.9))

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
            kk.mostrar(_com(P['pulo'], olhos='s'))
            _som('pulo')
            kk.empurrar(capa=-10, cabelo=-8, lift=12)
            alvo = quadro(ox_t - th * 0.7, oy_t + th * 0.5, POSES_G1)
            # giro para a frente (horario, olhando para a direita)
            _mover(kk, (ax, ay), alvo, 0.5, altura=0.0, rot=(0, -360), fantasmas=4, on_fim=_golpe1,
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
                (2, P['agacha']), (4, _com(P['saca1'], olhos='s')),
                (1, _com(K.smear(P['corta1'], K._BAINHA_ANG), olhos='g')), (1, _com(P['corta1'], olhos='g')),
                (6, _com(P['segue1'], olhos='s')), (1, _com(P['segue1'], olhos='s'))])

            def _q(i):
                if i == 2:
                    _som('sacar_iai')
                elif i == 6:
                    corte_trecho(0, CIANO, 1, 'corte')
            kk.tocar(seq, on_quadro=_q, on_fim=_saca2)

        # ── 4. saca a Dark Repulser (das costas) e toma guarda dupla ──
        def _saca2():
            seq = K.sequencia([(4, _com(P['pega2'], olhos='s')), (4, _com(P['saca2'], olhos='s')),
                               (5, _com(P['dupla'], olhos='s')), (6, _com(P['dupla'], olhos='s'))])

            def _q(i):
                if i == 5:
                    hx2, hy2 = kk.ponto_mao(2)
                    faiscas.estourar(hx2, hy2, AZUL, n=20, forca=dp(130), tam=ps)
                    _som('sacar')
                    kk.empurrar(cabelo=8)
            kk.tocar(seq, on_quadro=_q, on_fim=lambda: _combo(1))

        # ── 5. combo samurai com as duas: cada silaba de uma direcao ──
        # "VE": de baixo, cortando para cima | "TE ": do alto, no ar, cortando
        # para baixo | "FO": pela direita, virado, corte cruzado para tras
        GOLPES = {
            1: ('sobe_arma', 'sobe_corta', (235, 215), 'baixo', (225, 405), CIANO, AZUL, 'corte'),
            2: ('desce_arma', 'desce_corta', (100, 115), 'cima', (135, -45), CIANO, AZUL, 'corte'),
            3: ('x_arma', 'x_corta', (135, 160), 'direita', (-20, 200), AZUL, CIANO, 'corte2'),
        }

        def _alvo_golpe(lado, i, poses):
            i0, i1 = _TRECHOS[i]
            cx, cy = titulo.x_do_trecho(i0, i1)
            if lado == 'baixo':                       # cabeca abaixo das letras
                kk.espelhar = False
                cima_p = _ext(kk, [P[poses[0]]])[3]
                return quadro(cx - th * 0.35, oy_t - dp(4) - cima_p, poses)
            if lado == 'cima':                        # no ar, acima das letras
                kk.espelhar = False
                baixo_p = _ext(kk, [P[poses[0]]])[1]
                return quadro(cx - th * 0.45, oy_t + th + dp(10) + baixo_p, poses)
            kk.espelhar = True                         # 'direita': virado para a esquerda
            return quadro(ox_t + titulo._larg[i1] + th * 0.9, cy - th * 0.1, poses)

        def _combo(i):
            if i > 3:
                _final()
                return
            p_arma, p_corta, (s1, s2), lado, arco, cor, cor2, som_c = GOLPES[i]
            ax, ay = kk.ancora()
            alvo = _alvo_golpe(lado, i, [p_arma, p_corta])
            teto = area[3] - m - _ext(kk, [P[p_arma], P[p_corta]])[3]
            if lado == 'baixo':
                h, giro, dur = 0.0, None, 0.17               # desliza por baixo
            elif lado == 'cima':
                h, giro, dur = _arco(ay, alvo[1], th * 1.1, teto), None, 0.22   # salta
            else:
                h, giro, dur = _arco(ay, alvo[1], th * 0.6, teto), (0, 360), 0.22  # gira e vira
            kk.mostrar(_com(P[p_arma], olhos='s'))
            if lado != 'baixo':
                _som('pulo')

            def _ataca():
                kk.rotacao = 0
                seq = K.sequencia([(2, _com(P[p_arma], olhos='s')),
                                   (1, _com(K.smear(P[p_corta], s1, s2), olhos='g')),
                                   (1, _com(P[p_corta], olhos='g')), (3, _com(P[p_corta], olhos='s')),
                                   (1, _com(P[p_corta], olhos='s'))])
                kk.tocar(seq, on_quadro=lambda q: q == 2 and corte_trecho(
                    i, cor, 1, som_c, cor2, arco=arco, achat=0.5 if lado != 'direita' else 0.42),
                    on_fim=lambda: _combo(i + 1))
            _mover(kk, (ax, ay), alvo, dur, altura=h, rot=giro, cor_fantasma=cor,
                   on_fim=_ataca, limite=(area, m))

        # ── 6. golpe final (estilo Bleach) ───────────────────────────
        p_fim = ['evo_corte', 'evo_fim', 'dupla', 'chiburi', 'embainha_a', 'embainha_b',
                 'embainha_c', 'guardado']
        cx_meio = ox_t + titulo.tw / 2.0

        def _final():
            # sobe para o meio da frase, embaixo do infinito
            kk.espelhar = False
            alvo = quadro(cx_meio, y_topo, ['agacha', 'une_a', 'une_b', 'fund_alto', 'evo_alto'])
            ax, ay = kk.ancora()
            kk.mostrar(_com(P['pulo'], olhos='s'))
            _som('pulo')
            h = _arco(ay, alvo[1], th * 1.2, area[3] - m - _ext(kk, [P['pulo']])[3])
            _mover(kk, (ax, ay), alvo, 0.35, altura=h, on_fim=_fundir, limite=(area, m))

        def _fundir():
            _som('pouso')
            ax, ay = kk.ancora()
            poeira(ax, ay - kk.extensao()[1], n=8)
            cam[0].ir(1.12, foco=(ax, ay + alt * 0.35), dur=1.8)
            # nome da habilidade embaixo da frase (a acao e em cima dela)
            nome = _NomeGolpe(ox_t + titulo.tw / 2.0, oy_t - th * 1.5, W * 0.9)
            estado['nome'] = nome
            camada.add_widget(nome)
            # a pose: cruza as duas espadas no alto enquanto diz "Starburst...
            # Stream!" - o clarao da fusao cai no pico do "Stream"
            seq = K.sequencia([(3, _com(P['agacha'], olhos='s')), (5, _com(P['dupla'], olhos='s')),
                               (20, P['une_a']), (14, P['une_b']), (12, P['une_b'])])

            def _q(i):
                if i == 6:
                    _som('habilidade')
                    _som('voz_starburst')
                    nome.parte1()
                elif i == 8:
                    _som('pulo')                     # as duas sobem cruzadas
                elif i == 41:
                    _som('voz_stream')
            kk.tocar(seq, on_quadro=_q, on_fim=_flash_fusao)

        def _flash_fusao():
            hx2, hy2 = kk.ponto_mao(1)
            jx, jy = hx2, hy2 + 6 * ps                 # onde as laminas se encontram
            kk.mostrar(P['fund_alto'])
            _clarao_boneco(kk, 0.35)
            faiscas.estourar(jx, jy, BRANCO, n=26, forca=dp(220), tam=ps)
            faiscas.estourar(jx, jy, AZUL, n=16, forca=dp(160), tam=ps)
            _anel(camada, (jx, jy), ps * 2, ps * 22, 0.45, CIANO, esp=dp(4))
            _brilho_tela(camada, 0.45, 0.25)
            _som('fusao')
            _tremer(12)
            kk.pausar(0.1)
            kk.empurrar(cabelo=10, lift=8)
            aura.alvo = 0.35
            nome = estado.get('nome')
            if nome is not None:
                nome.parte2()
                ag.depois(1.1, nome.sumir)
            ag.depois(0.7, _sugar)

        def _sugar():
            reator = estado['reator']
            ponta = lambda: kk.ponta_espada(1)
            if reator is None or reator.parent is None:
                _absorveu()
                return
            _fundo(tela, reator=1.0, barra=0.1, dur=0.35)    # o infinito acende enquanto e puxado
            _som('reiatsu')
            aura.alvo = 0.7
            fluxo = _Fluxo(reator, ponta, dur=2.4)
            estado['fluxo'] = fluxo
            camada.add_widget(fluxo, index=1)
            reator.sugar(ponta, dur=2.4, on_fim=lambda: ag.depois(0.0, _absorveu))
            vento = [0.0]

            def _vento(dt):
                vento[0] += dt
                if vento[0] > 2.5:
                    return False
                kk.empurrar(lift=2.2, cabelo=-1.5, capa=-1.0)
                if int(vento[0] * 10) % 4 == 0:
                    _tremer(2)
                return True
            ag.cada(0.08, _vento)
            ag.depois(3.2, lambda: None if getattr(reator, '_absorvido', False) else _absorveu())

        def _absorveu():
            if estado.get('absorveu'):
                return
            estado['absorveu'] = True
            fl = estado.get('fluxo')
            if fl is not None:
                ag.depois(0.25, fl.parar)
            r = estado['reator']
            if r is not None:
                r._absorvido = True
            tx, ty = kk.ponta_espada(1)
            kk.mostrar(P['evo_alto'])
            _clarao_boneco(kk, 0.3, 0.8)
            _brilho_tela(camada, 0.7, 0.4, (0.85, 1.0, 1.0))
            _anel(camada, (tx, ty), ps * 3, max(W, H) * 0.6, 0.6, CIANO, esp=dp(5))
            _anel(camada, (tx, ty), ps * 2, max(W, H) * 0.35, 0.45, BRANCO, esp=dp(3))
            faiscas.estourar(tx, ty, CIANO, n=40, forca=dp(320), tam=ps)
            faiscas.estourar(tx, ty, BRANCO, n=20, forca=dp(240), tam=ps)
            _som('absorve')
            _tremer(22)
            kk.pausar(0.14)
            aura.alvo = 1.0
            ax, ay = kk.ancora()
            cam[0].ir(1.2, foco=(ax, ay + alt * 0.4), dur=0.5)
            ag.depois(1.0, _posiciona)

        def _posiciona():
            # sobe acima do comeco da frase e carrega flutuando (as letras
            # ficam a vista); o ultimo corte mergulha na diagonal
            kk.espelhar = False
            x_ini, y_ini = quadro(ox_t - th * 0.5, y_topo + alt * 0.6, ['evo_carga', 'evo_corte'])
            ax, ay = kk.ancora()
            kk.mostrar(P['evo_carga'])
            _som('pulo')
            cam[0].ir(1.0, dur=0.35)
            h = _arco(ay, y_ini, th * 1.4, area[3] - m - _ext(kk, [P['evo_carga']])[3])
            _mover(kk, (ax, ay), (x_ini, y_ini), 0.38, altura=h, fantasmas=4, on_fim=_carga,
                   limite=(area, m))

        def _carga():
            _som('pouso')
            ax, ay = kk.ancora()
            poeira(ax, ay - kk.extensao()[1], n=8)
            kk.tocar(K.sequencia([(5, P['evo_carga']), (1, P['evo_carga'])]))
            _som('carga')
            titulo.pulsar(0.9)
            cam[0].ir(1.16, foco=(ax, ay + alt * 0.2), dur=0.8)
            aura.alvo = 1.0
            t = [0.0]

            def _junta(dt):
                t[0] += dt
                if t[0] >= 0.9:
                    return False
                ax2, ay2 = kk.ancora()
                ang = random.uniform(0, 2 * math.pi)
                rr = alt * random.uniform(0.5, 0.9)
                faiscas.estourar(ax2 + math.cos(ang) * rr, ay2 + math.sin(ang) * rr * 0.7,
                                 random.choice((CIANO, AZUL, BRANCO)), n=2,
                                 forca=dp(40), tam=ps, gravidade=-160)
                kk.empurrar(capa=2.5, cabelo=2.5, lift=1.5)
                return True
            ag.cada(0.06, _junta)
            ag.depois(0.9, _silencio)

        def _silencio():
            # um instante de silencio: tudo segura a respiracao
            kk.pausar(0.28)
            ag.depois(0.28, _golpe_final)

        def _golpe_final():
            x_fim, y_fim = quadro(ox_t + titulo.tw - th * 0.8, y_topo, p_fim)
            ax, ay = kk.ancora()
            cam[0].ir(1.0, dur=0.12)
            kk.mostrar(P['evo_corte'])
            _som('getsuga')
            _tremer(26)
            _brilho_tela(camada, 0.55, 0.3, (0.8, 1.0, 1.0))
            _, cy = titulo.x_do_trecho(0, len(texto))
            xr0 = max(area[0] + m, min(ax, ox_t - th * 0.4))
            xr1 = min(area[2] - m, ox_t + titulo.tw + th * 0.6)
            dur = 0.2
            camada.add_widget(_OndaGetsuga(xr0, min(area[2] + th * 2, xr1 + th * 2.5), cy,
                                           altura=th * 4.2, dur=0.42))
            _risco_luz(camada, xr0, xr1, cy, dur, CIANO, espessura=max(dp(2), th * 0.09))
            titulo.varrer(dur * 1.6)
            # "CUS" aparece quando a onda passa por ele
            i0, i1 = _TRECHOS[4]
            cx5, _ = titulo.x_do_trecho(i0, i1)
            frac = max(0.0, min(1.0, (cx5 - xr0) / max(1.0, xr1 - xr0)))
            ag.depois(0.42 * frac, lambda: (titulo.revelar(i0, i1, dur=0.06),
                                            faiscas.estourar(cx5, cy, BRANCO, n=24, forca=dp(260), tam=ps)))
            _mover(kk, (ax, ay), (x_fim, y_fim), dur, linear=True, fantasmas=6,
                   cor_fantasma=CIANO, on_fim=_para, limite=(area, m))

        def _para():
            # para de costas para a frase... e o mundo segura a respiracao
            kk.mostrar(P['evo_fim'])
            kk.pausar(0.12)
            kk.empurrar(capa=-20, cabelo=-16)
            ag.depois(0.55, _separa)

        def _separa():
            # a espada evoluida se divide de novo nas duas
            hx2, hy2 = kk.ponto_mao(1)
            aura.alvo = 0.0
            kk.mostrar(_com(P['dupla'], olhos='s'))
            _clarao_boneco(kk, 0.3, 0.9)
            faiscas.estourar(hx2, hy2, BRANCO, n=18, forca=dp(160), tam=ps)
            faiscas.estourar(hx2, hy2, AZUL, n=10, forca=dp(120), tam=ps)
            _anel(camada, (hx2, hy2), ps * 2, ps * 14, 0.35, CIANO)
            _som('separa')
            ag.depois(0.45, _chiburi)

        def _chiburi():
            # chiburi (sacode a lamina) e noto: embainha devagar ate o clique
            seq = K.sequencia([(3, _com(P['chiburi'], olhos='s')), (6, P['embainha_a']),
                               (8, P['embainha_b']), (2, P['embainha_c']), (2, P['guardado']),
                               (1, P['guardado'])])

            def _q(q):
                if q == 1:
                    _som('pulo')
                elif q == 5:
                    _som('desliza')
                elif q == 17:
                    _som('embainhar')
                    bx, by = kk.ponto_mao(1)
                    faiscas.estourar(bx, by, BRANCO, n=6, forca=dp(50), tam=max(2, ps * 0.7),
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
            _brilho_tela(camada, 0.3, 0.3)
            titulo.clarao_final()
            ag.depois(1.4, _sai)

        def _sai():
            kk.parar()
            aura.parar()
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
            restaurar_fundo()
            encerrar()
        ag.depois(32.0, _seguranca)
    except Exception as e:
        print(f"[cena] falhou, seguindo sem ela: {e}")
        restaurar_fundo()
        encerrar()
    return camada


def limpar_cena(camada):
    try:
        ag = getattr(camada, '_agenda', None)
        if ag is not None:
            ag.parar()
        rest = getattr(camada, '_restaurar', None)
        if rest is not None:
            rest()
        for w in list(camada.children):
            if isinstance(w, K.KiritoPixel):
                w.parar()
            elif isinstance(w, (_AuraEspada, _Fluxo, _OndaGetsuga, _NomeGolpe)):
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
    digitado, da um pulinho a cada tecla, leva um susto no erro (!) e volta
    desconfiado; no bloqueio balanca a cabeca e afunda; no acerto sobe na
    caixa, sorri e some num teleporte."""

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
        self._bloq = False          # 3 erros: reacao final (nada mais interrompe)
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
        """PIN errado: leva um susto (!), se abaixa atras da caixa e depois
        volta a espiar devagar, desconfiado e suando."""
        try:
            if self.k is None or self._em_cima or self._escondido:
                return
            self._ocupado = True
            self._escondido = True
            _som('susto')
            ps = self.k.ps
            P = K.POSE_A
            self.k.empurrar(cabelo=18, lift=8)
            self.k.tocar(K.sequencia([(5, _com(P['espia_alto'], olhos='u', emote='!')),
                                      (1, _com(P['espia_alto'], olhos='u', emote='!')),
                                      (1, _com(P['espia_baixo'], olhos='u'))]))

            def _de_volta():
                if self._bloq:
                    return
                self._escondido = False
                seq = K.sequencia([(14, _com(P['espia_baixo'], olhos='s')),
                                   (22, _com(P['espia_olha'], olhos='s', emote='gota')),
                                   (1, _com(P['espia_olha'], olhos='s', emote='gota'))])
                self.k.tocar(seq, on_fim=self._esperar)

            def _volta():
                if self._bloq:
                    return
                self.k.mostrar(_com(P['espia_baixo'], olhos='s'))
                self._animar_desc(0.0, 0.45, on_fim=_de_volta)
            self._depois(0.2, lambda: self._animar_desc(
                13 * ps, 0.12, on_fim=lambda: self._depois(0.7, _volta)))
        except Exception as e:
            print(f"[kirito pin] susto: {e}")

    def bloqueado(self):
        """3 erros: fecha os olhos, balanca a cabeca (nao, nao...) com uma
        gota de suor e afunda devagar atras da caixa."""
        try:
            if self.k is None or self._em_cima or self._bloq:
                return
            self._bloq = True
            self._ocupado = True
            self._escondido = True
            P = K.POSE_A
            base = _com(P['espia_olha'], olhos='f', emote='gota')
            quadros = []
            for dx in (0, -1, -1, 1, 1, -1, -1, 1, 1, 0, 0, 0):
                q = dict(base)
                q['dx'] = dx
                q['m1'] = (base['m1'][0] - dx, base['m1'][1])     # maos paradas na borda
                q['m2'] = (base['m2'][0] - dx, base['m2'][1])
                quadros.extend([q, q])
            ps = self.k.ps

            def _afunda():
                self.k.mostrar(_com(P['espia_baixo'], olhos='f', emote='...'))
                self._animar_desc(13 * ps, 0.9)
            # se estava escondido (susto do erro), volta para a borda antes
            self.k.mostrar(base)
            self._animar_desc(0.0, 0.15, on_fim=lambda: self.k.tocar(quadros, on_fim=_afunda))
        except Exception as e:
            print(f"[kirito pin] bloqueado: {e}")

    def sumir(self):
        """Acesso liberado: sobe na caixa, sorri, faz que sim e some num
        teleporte (ele volta pendurado na cena do titulo)."""
        try:
            if self.k is None:
                return
            k = self.k
            self._ocupado = True
            P = K.POSE_A
            W, H = Window.size
            x0, topo, x1 = self._borda()
            ps = k.ps
            if H - topo < 30 * ps:
                # sem espaco para ficar em pe na caixa: some dali mesmo
                k.tocar(K.sequencia([(3, _com(P['espia_alto'], olhos='e', emote='brilho')),
                                     (4, _com(P['espia'], olhos='e', emote='brilho')),
                                     (1, _com(P['espia_alto'], olhos='e', emote='brilho'))]))
                self._depois(0.35, lambda: _teleporte(k, self.clip, self.faiscas, on_fim=self.remover))
                return
            k.tocar(K.sequencia([(3, P['espia_alto']), (1, P['espia_alto'])]))

            def _pula():
                ax, ay = k.ancora()
                self._em_cima = True
                k.mostrar(P['pulo'])
                _som('pulo')
                k.empurrar(capa=-8, lift=10)
                base = k.extensao(P['guardado'])[1]
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
                feliz = _com(P['guardado'], olhos='e', emote='brilho')
                k.tocar(K.sequencia([(3, P['agacha']), (4, feliz),
                                     (3, _com(feliz, dy=-1)),                 # faz que sim
                                     (4, feliz), (1, feliz)]),
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
    """Mini Kirito se materializa grudado na borda mais proxima, pula, fatia
    `alvo` de cima para baixo em duas metades (so entao vem a explosao de
    cacos, efeitos.explodir_estilhacos) e some num teleporte."""
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
        alt_boneco = max(dp(62), min(rh * 1.7, dp(96), H * 0.15))
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
        k.mostrar(_com(K.POSE_A['grudado'], olhos='s'))
        golpe = [K.POSE_A[n] for n in ('arma1', 'corta_desce', 'segue_desce')]
        k.precarregar([K.POSE_A[n] for n in ('agacha', 'pulo')] + golpe)
        # ataca pelo canto do widget do lado de onde veio, inteiro no quadro
        ataque = _no_quadro(k, rx - dp(6) if esquerda else rx + rw + dp(6), cy + rh * 0.35,
                            golpe, area, dp(2))

        def _pula():
            k.tocar(K.sequencia([(3, _com(K.POSE_A['agacha'], olhos='s')),
                                 (1, _com(K.POSE_A['pulo'], olhos='s'))]))
            Clock.schedule_once(lambda dt: _mover(
                k, k.ancora(), ataque, 0.26, altura=rh * 0.8 + dp(20),
                rot=(k.rotacao, 0), on_fim=_golpe), 0.1)

        def _golpe():
            k.rotacao = 0
            k.espelhar = not esquerda
            seq = K.sequencia([(2, _com(K.POSE_A['arma1'], olhos='s')),
                               (1, _com(K.smear(K.POSE_A['corta_desce'], 112), olhos='g')),
                               (4, _com(K.POSE_A['segue_desce'], olhos='g')),
                               (1, _com(K.POSE_A['segue_desce'], olhos='s'))])
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
            k.pausar(0.07)                                   # hit-stop
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
            _teleporte(k, cam, faiscas, on_fim=_limpa, dur=0.45, teto=by1 - dp(2))

        def _limpa():
            k.parar()
            Clock.schedule_once(lambda dt: _remover_da_janela(cam), 0.4)

        _materializar(k, cam, faiscas, dur=0.26, on_fim=lambda: Clock.schedule_once(lambda dt: _pula(), 0.08))
        # seguranca: se algo travar, apaga mesmo assim e limpa a camada
        Clock.schedule_once(lambda dt: _explodir(), 3.5)
        Clock.schedule_once(lambda dt: _remover_da_janela(cam), 6.0)
    except Exception as e:
        print(f"[fatiar] ignorado: {e}")
        _remover_da_janela(camada[0])
        _explodir()


def kirito_wipe(widgets, on_fim=None):
    """WIPE: Kirito se materializa no alto da lista, saca as duas espadas e
    faz um combo cortando a lista inteira; cada golpe desintegra um grupo de
    itens. No fim, um X gigante e ele some num teleporte."""
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
        k.mostrar(_com(K.POSE_A['guardado'], olhos='s'))
        ini = _no_quadro(k, cx, topo + dp(10), [K.POSE_A['guardado'], K.POSE_A['pega2'],
                                                 K.POSE_A['saca2'], K.POSE_A['dupla']], area, dp(4))
        k.ancorar(*ini)
        k.precarregar([K.POSE_A[n] for n in K.POSE_A])
        _precarregar_sons(['sacar', 'corte', 'corte2', 'titulo', 'pulo', 'teleporte'])
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
                seq = K.sequencia([(2, _com(K.POSE_A['x_arma'], olhos='s')),
                                   (1, _com(K.smear(K.POSE_A['x_corta'], 140), olhos='g')),
                                   (3, _com(K.POSE_A['x_corta'], olhos='g')),
                                   (1, _com(K.POSE_A['x_corta'], olhos='s'))])

                def _q(q):
                    if q == 2:
                        cam.add_widget(CorteMeiaLua(
                            centro=(cx, y), raio=W * 0.55, ang_ini=165 if lado > 0 else 15,
                            ang_fim=-35 if lado > 0 else 215, espessura=dp(40),
                            achat=0.3, rotacao=-10 * lado, cor=cor))
                        faiscas.estourar(cx, y, cor, n=22, forca=dp(220), tam=ps)
                        _som('corte2' if cor == AZUL else 'corte')
                        _tremer(10)
                        k.pausar(0.07)
                        _desintegra(grupos[i])
                k.tocar(seq, on_quadro=_q, on_fim=lambda: _golpe(i + 1))
            _mover(k, k.ancora(), alvo, 0.16, altura=dp(30), cor_fantasma=cor, on_fim=_ataca)

        def _saca():
            seq = K.sequencia([(3, _com(K.POSE_A['pega2'], olhos='s')), (3, _com(K.POSE_A['saca2'], olhos='s')),
                               (3, _com(K.POSE_A['dupla'], olhos='s')), (1, _com(K.POSE_A['dupla'], olhos='s'))])

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
                seq = K.sequencia([(4, _com(K.POSE_A['final_arma'], olhos='s')),
                                   (1, _com(K.smear(K.POSE_A['final'], 130), olhos='g')),
                                   (8, _com(K.POSE_A['final'], olhos='g')),
                                   (1, _com(K.POSE_A['final'], olhos='s'))])

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
                        k.pausar(0.12)
                        _brilho_tela(cam, 0.35, 0.3)
                k.tocar(seq, on_quadro=_q, on_fim=_sai)
            _mover(k, k.ancora(), alvo, 0.2, altura=dp(50), on_fim=_ataca)

        def _sai():
            _teleporte(k, cam, faiscas, on_fim=_acabou, teto=by1 - dp(2))

        def _acabou():
            k.parar()
            _remover_da_janela(cam)
            fim()

        _materializar(k, cam, faiscas, dur=0.32, on_fim=_saca)

        def _seguranca(dt):
            _remover_da_janela(cam)
            fim()
        Clock.schedule_once(_seguranca, 8.0)
    except Exception as e:
        print(f"[wipe] ignorado: {e}")
        _remover_da_janela(camada[0])
        fim()
