"""
cenas.py — TraveteFocus
Cenas com o Kirito pixel art (kirito.py) + cortes em meia-lua (espadachim.py):

  cena_titulo(tela, label, on_fim)  Kirito surge grudado numa borda aleatoria,
                                    pula ate o titulo e, com a Elucidator e
                                    depois a Dark Repulser, escreve
                                    "TRAVETE FOCUS" com o rastro dos golpes.
  KiritoPin                         escondido num canto da tela do PIN,
                                    reagindo as teclas, ao erro e ao acerto.
  kirito_fatiar(widget, on_fim)     mini Kirito fatia o item que sera apagado
                                    (depois vem a explosao de cacos).
  kirito_wipe(widgets, on_fim)      versao epica: combo cortando a lista toda.

Tudo tolerante a falha: se algo der errado, on_fim ainda e chamado (a
historia do app nunca trava por causa de uma animacao).
"""
import math
import random

from kivy.uix.widget import Widget
from kivy.graphics import (Color, Rectangle, Line, Mesh, PushMatrix, PopMatrix,
                           Scale, Translate, Rotate, InstructionGroup)
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp

import kirito as K
from espadachim import CorteMeiaLua

CIANO = (0.0, 0.9, 1.0)
AZUL = (0.35, 0.65, 1.0)        # rastro da Dark Repulser


def _som(nome):
    try:
        import som
        som.tocar(nome)
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
           cor_fantasma=CIANO, on_fim=None, linear=False, cada=2, on_passo=None):
    """Move a ancora do Kirito em arco (parabola de `altura`), girando de
    rot[0] a rot[1], deixando afterimages (1 a cada `cada` quadros).
    on_passo(u) e chamado a cada quadro com o progresso 0..1."""
    t = [0.0]
    cont = [0]
    feito = [False]

    def _acabar():
        if not feito[0]:
            feito[0] = True
            if on_fim:
                on_fim()

    def _p(dt):
        try:
            t[0] += dt
            u = min(1.0, t[0] / dur)
            if linear:
                e = u
            else:
                e = 1 - (1 - u) ** 2 if altura >= 0 else u * u
            x = de[0] + (para[0] - de[0]) * e
            y = de[1] + (para[1] - de[1]) * e + altura * 4 * u * (1 - u)
            k.ancorar(x, y)
            if rot is not None:
                k.rotacao = rot[0] + (rot[1] - rot[0]) * e
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


def cena_titulo(tela, label, on_fim=None, texto="TRAVETE FOCUS"):
    """Kirito pendurado num canto em pose de samurai; solta, saca a
    Elucidator e escreve a frase; saca a Dark Repulser e segue o combo (uma
    nota por trecho); no golpe final (iai) carrega, atravessa a frase inteira
    num corte so, para, embainha - e so entao a frase explode com o acorde."""
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
        wx, wy = label.to_window(label.x, label.y)
        lx, ly = tela.to_widget(wx, wy)
        titulo = TituloLuz(texto, label.font_size, pos=(lx, ly), size=label.size)
        camada.add_widget(titulo)
        camada._titulo = titulo
        faiscas = K.Faiscas(n_max=100)
        ps = _ps_para(W, H)
        kk = K.KiritoPixel(ps=ps)
        kk.opacity = 0
        camada.add_widget(kk)
        camada.add_widget(faiscas)
        alt = 24 * ps
        th = titulo.th
        margem = 8 * ps
        kk.precarregar([K.POSE_A[n] for n in K.POSE_A])
        y_ataque = ly + label.height / 2.0 + alt * 0.12

        def clamp_x(x):
            return max(margem, min(W - margem, x))

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
            _som(f'nota{i + 1}')
            _tremer(6)
            kk.empurrar(capa=16, cabelo=14)

        # ── 1. pendurado num canto do topo, pose de samurai ──────────
        lado = random.choice((-1, 1))                # -1 canto esquerdo, 1 direito
        kk.espelhar = lado > 0                       # olha para o centro
        p_pend = K.POSE_A['pendurado']
        kk.mostrar(p_pend)
        mx, my = kk.mao_local(2, p_pend)             # mao que segura a borda
        kk.pivo = (mx, my)
        hx = (dp(8) + 7 * ps) if lado < 0 else (W - dp(8) - 7 * ps)
        hy = H - dp(4)
        kk.pos = (hx - mx, hy - my)
        balanco = {'ativo': True, 't': 0.0, 'amp': 16.0}

        def _balanca(dt):
            try:
                if not ag.vivo or not balanco['ativo']:
                    return False
                balanco['t'] += dt
                t = balanco['t']
                a = balanco['amp'] * math.exp(-t * 1.1) + 3.0
                kk.rotacao = a * math.sin(2 * math.pi * 0.85 * t) * (-lado)
            except Exception:
                return False
        Clock.schedule_interval(_balanca, 1 / 60.)

        def _surge():
            faiscas.estourar(hx, hy - dp(4), CIANO, n=10, forca=dp(80), tam=ps, gravidade=120)
            _som('surge')
            t = [0.0]

            def _f(dt):
                t[0] += dt
                kk.opacity = min(1.0, t[0] / 0.3)
                return kk.opacity < 1
            Clock.schedule_interval(_f, 1 / 60.)
            quadros = []
            for f in range(60):
                q = dict(p_pend)
                q['olhos'] = 'f' if f in (40, 41) else 'a'
                quadros.append(q)
            kk.tocar(quadros, loop=True)
        ag.depois(0.05, _surge)

        def _kamae():
            # recolhe as pernas e leva o polegar a guarda: pronto para sacar
            seq = K.sequencia([(6, p_pend), (1, K.POSE_A['pendurado2'])])
            kk.tocar(seq)
            hx2, hy2 = kk.ponto_mao(1)
            faiscas.estourar(hx2, hy2, (1, 1, 1), n=5, forca=dp(40), tam=ps, gravidade=0)
            _som('koiguchi')
        ag.depois(0.95, _kamae)

        # ── 2. solta e cai girando ate o inicio da frase ─────────────
        cx1, _ = titulo.x_do_trecho(*_TRECHOS[0])
        alvo1 = (clamp_x(cx1 - th * 1.3), y_ataque)

        def _solta():
            # endireita o balanco antes de trocar o pivo (sem salto visual)
            t = [0.0]
            r0 = kk.rotacao

            def _reto(dt):
                try:
                    t[0] += dt
                    u = min(1.0, t[0] / 0.12)
                    kk.rotacao = r0 * (1 - u)
                    if u >= 1:
                        balanco['ativo'] = False
                        _pula()
                        return False
                except Exception:
                    _pula()
                    return False
            balanco['ativo'] = False
            Clock.schedule_interval(_reto, 1 / 60.)

        def _pula():
            ax, ay = kk.ancora()                 # ancora sem rotacao (rotacao ~0)
            kk.pivo = None
            kk.rotacao = 0
            kk.ancorar(ax, ay)
            kk.espelhar = False
            kk.mostrar(K.POSE_A['pulo'])
            _som('pulo')
            giro = 360.0 if lado > 0 else -360.0
            _mover(kk, (ax, ay), alvo1, 0.5, altura=th * 1.2, rot=(0, giro), on_fim=_golpe1)
        ag.depois(1.75, _solta)

        # ── 3. golpe 1 (Elucidator, saque iai): escreve "TRA" ────────
        def _golpe1():
            kk.rotacao = 0
            _som('pouso')
            seq = K.sequencia([
                (3, K.POSE_A['saca1']), (3, K.POSE_A['arma1']),
                (1, K.smear(K.POSE_A['corta1'], 112)), (1, K.POSE_A['corta1']),
                (5, K.POSE_A['segue1']), (1, K.POSE_A['segue1'])])
            kk.tocar(seq, on_quadro=lambda i: i == 6 and corte_trecho(0, CIANO, 1, 'corte'),
                     on_fim=_saca2)

        # ── 4. saca a Dark Repulser (brilho azul) e toma guarda dupla ─
        def _saca2():
            seq = K.sequencia([(4, K.POSE_A['pega2']), (4, K.POSE_A['saca2']),
                               (5, K.POSE_A['dupla']), (6, K.POSE_A['dupla'])])

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
            if i == 3:
                alvo = (clamp_x(cx - th * 0.5), y_ataque + th * 0.6)
            else:
                alvo = (clamp_x(cx - th * 1.0), y_ataque)
            kk.espelhar = False

            def _ataca():
                kk.rotacao = 0
                seq = K.sequencia([(2, K.POSE_A[p_arma]),
                                   (1, K.smear(K.POSE_A[p_corta], s1, s2)),
                                   (1, K.POSE_A[p_corta]), (3, K.POSE_A[p_corta]),
                                   (1, K.POSE_A[p_corta])])
                kk.tocar(seq, on_quadro=lambda q: q == 2 and corte_trecho(i, cor, sentido, som_c, cor2),
                         on_fim=lambda: _combo(i + 1))
            _mover(kk, kk.ancora(), alvo, 0.15, altura=th * (0.9 if i == 3 else 0.4),
                   rot=(0, -360) if i == 3 else None, cor_fantasma=cor, on_fim=_ataca)

        # ── 6. golpe final (iai): carga -> corte atravessando a frase ─
        def _iai():
            x_ini = clamp_x(titulo.x_do_trecho(0, 1)[0] - th * 1.6)
            x_fim = clamp_x(titulo.x_do_trecho(len(texto) - 1, len(texto))[0] + th * 1.6)
            y_iai = y_ataque - th * 0.15
            kk.espelhar = False
            kk.mostrar(K.POSE_A['pulo'])
            _som('pulo')

            def _carrega():
                _som('pouso')
                kk.tocar(K.sequencia([(5, K.POSE_A['iai_carga']), (1, K.POSE_A['iai_carga'])]))
                _som('carga')
                titulo.pulsar(0.85)
                t = [0.0]

                def _aura(dt):
                    try:
                        t[0] += dt
                        if t[0] >= 0.85 or not ag.vivo:
                            return False
                        ax, ay = kk.ancora()
                        faiscas.estourar(ax + random.uniform(-alt * 0.4, alt * 0.4),
                                         ay + random.uniform(-alt * 0.2, alt * 0.6),
                                         random.choice((CIANO, AZUL)), n=2,
                                         forca=dp(40), tam=ps, gravidade=-160)
                        kk.empurrar(capa=2.5, cabelo=2.5, lift=1.5)
                    except Exception:
                        return False
                Clock.schedule_interval(_aura, 0.07)
                ag.depois(0.85, _atravessa)
            _mover(kk, kk.ancora(), (x_ini, y_iai), 0.3, altura=th * 1.4, on_fim=_carrega)

            def _atravessa():
                kk.mostrar(K.POSE_A['iai_corte'])
                _som('golpe_final')
                _tremer(10)
                dur = 0.16
                _, cy = titulo.x_do_trecho(0, len(texto))
                _risco_luz(camada, x_ini, x_fim, cy, dur, CIANO, espessura=max(dp(2), th * 0.08))
                titulo.varrer(dur)
                # "CUS" aparece quando a lamina passa por ele
                i0, i1 = _TRECHOS[4]
                cx5, _ = titulo.x_do_trecho(i0, i1)
                frac = max(0.0, min(1.0, (cx5 - x_ini) / max(1.0, x_fim - x_ini)))
                ag.depois(dur * frac, lambda: (titulo.revelar(i0, i1, dur=0.06), _som('nota5')))
                _mover(kk, kk.ancora(), (x_fim, y_iai), dur, linear=True, cada=1,
                       cor_fantasma=CIANO, on_fim=_para)

            def _para():
                # para de costas para a frase... e o mundo segura a respiracao
                kk.mostrar(K.POSE_A['iai_fim'])
                kk.empurrar(capa=-20, cabelo=-16)
                ag.depois(0.45, _chiburi)

            def _chiburi():
                seq = K.sequencia([(3, K.POSE_A['chiburi']), (7, K.POSE_A['embainha']),
                                   (2, K.POSE_A['guardado']), (1, K.POSE_A['guardado'])])

                def _q(q):
                    if q == 1:
                        _som('pulo')
                    if q == 10:
                        _som('embainhar')
                        ag.depois(0.12, _explode)
                kk.tocar(seq, on_quadro=_q, on_fim=lambda: kk.idle(base=K.POSE_A['guardado']))

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
            ag.depois(1.3, _sai)

        def _sai():
            kk.mostrar(K.POSE_A['pulo'])
            _som('pulo')
            ax, ay = kk.ancora()
            _mover(kk, (ax, ay), (ax + dp(30), H + alt * 1.5), 0.4, on_fim=_acabou)

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
#  KIRITO NA TELA DO PIN (escondido num canto, esperando)
# ═══════════════════════════════════════════════════════════════════
class KiritoPin:
    """Espia pela borda de cima da tela enquanto o PIN e digitado: reage a
    cada tecla, se assusta no erro e pula embora quando o acesso e liberado.
    Fica na janela (por cima do popup) e sempre com metade do corpo visivel."""

    def __init__(self):
        self.k = None
        self._ev_espia = None
        self._ocupado = False
        self._pos_visivel = None
        self._pos_escondido = None

    def aparecer(self):
        try:
            if self.k is not None:
                return
            W, H = Window.size
            bx0, _, bx1, _ = _limites()
            ps = _ps_para(bx1 - bx0, H) + 1          # um pouco maior: tem que dar para ver
            k = K.KiritoPixel(ps=ps)
            self.k = k
            lado = random.choice((-1, 1))            # -1 borda esquerda, 1 direita
            k.espelhar = lado > 0                     # olha para o centro
            base = K.POSE_A['espreita']
            k.mostrar(base)
            # quadril perto da borda: so as costas ficam escondidas atras dela
            ay = H - dp(12) - 15 * ps
            if lado < 0:
                vis, esc = (bx0 + 4 * ps, ay), (bx0 - 9 * ps, ay)
            else:
                vis, esc = (bx1 - 4 * ps, ay), (bx1 + 9 * ps, ay)
            self._pos_visivel, self._pos_escondido = vis, esc
            self._lado = lado
            k.ancorar(*esc)
            Window.add_widget(k)
            _som('surge')
            _mover(k, esc, vis, 0.35, fantasmas=False, on_fim=self._esperar)
            self._ev_espia = Clock.schedule_interval(self._espiar_mais, 3.2)
        except Exception as e:
            print(f"[kirito pin] aparecer: {e}")
            self.remover()

    def _esperar(self):
        if self.k is not None:
            self._ocupado = False
            self.k.idle(base=K.POSE_A['espreita'])

    def _espiar_mais(self, dt):
        """De vez em quando se inclina um pouco mais para fora e volta."""
        try:
            if self.k is None or self._ocupado:
                return
            self._ocupado = True
            vx, vy = self._pos_visivel
            fora = (vx - self._lado * 3 * self.k.ps, vy)
            _mover(self.k, (vx, vy), fora, 0.25, fantasmas=False,
                   on_fim=lambda: Clock.schedule_once(
                       lambda _: self.k is not None and _mover(
                           self.k, fora, (vx, vy), 0.3, fantasmas=False, on_fim=self._esperar), 0.6))
        except Exception as e:
            print(f"[kirito pin] espiar: {e}")

    def reagir_tecla(self):
        """Balanca a cabeca a cada tecla digitada."""
        try:
            if self.k is None or self._ocupado:
                return
            seq = K.sequencia([(2, K.POSE_A['espreita2']), (2, K.POSE_A['espreita']),
                               (1, K.POSE_A['espreita'])])
            self.k.tocar(seq, on_fim=self._esperar)
        except Exception as e:
            print(f"[kirito pin] tecla: {e}")

    def susto(self):
        """PIN errado: pulinho de susto para tras e volta a espiar."""
        try:
            if self.k is None:
                return
            self._ocupado = True
            _som('susto')
            vx, vy = self._pos_visivel
            tras = (vx + self._lado * 2 * self.k.ps, vy + self.k.ps * 2)
            self.k.tocar(K.sequencia([(2, K.POSE_A['espreita']), (6, K.POSE_A['susto']),
                                      (1, K.POSE_A['susto'])]))
            self.k.empurrar(cabelo=20, lift=10)
            _mover(self.k, (vx, vy), tras, 0.12, altura=self.k.ps * 3, fantasmas=False,
                   on_fim=lambda: Clock.schedule_once(
                       lambda _: self.k is not None and _mover(
                           self.k, tras, (vx, vy), 0.35, fantasmas=False, on_fim=self._esperar), 0.45))
        except Exception as e:
            print(f"[kirito pin] susto: {e}")

    def sumir(self):
        """Acesso liberado: pula para fora da tela (ele volta na cena do titulo)."""
        try:
            if self.k is None:
                return
            self._parar_espia()
            k = self.k
            self._ocupado = True
            k.mostrar(K.POSE_A['pulo'])
            _som('pulo')
            ax, ay = k.ancora()
            _, H = Window.size
            _mover(k, (ax, ay), (ax - self._lado * 4 * k.ps, H + 30 * k.ps), 0.4,
                   altura=k.ps * 6, on_fim=self.remover)
        except Exception as e:
            print(f"[kirito pin] sumir: {e}")
            self.remover()

    def _parar_espia(self):
        if self._ev_espia is not None:
            self._ev_espia.cancel()
            self._ev_espia = None

    def remover(self, *_):
        self._parar_espia()
        k, self.k = self.k, None
        if k is not None:
            try:
                k.parar()
                _remover_da_janela(k)
            except Exception:
                pass


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
    """Mini Kirito pula da borda mais proxima, fatia `alvo` em duas metades
    e so entao vem a explosao de cacos (efeitos.explodir_estilhacos)."""
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
        bx0, _, bx1, _ = _limites()
        meio = (bx0 + bx1) / 2.0
        esquerda = ((rx + rw / 2.0) < meio) if rw < (bx1 - bx0) * 0.7 else (random.random() < 0.5)
        pe = 8 * ps + dp(2)
        ini = (bx0 + pe, cy) if esquerda else (bx1 - pe, cy)
        k.rotacao = -90 if esquerda else 90
        k.espelhar = not esquerda
        k.ancorar(*ini)
        k.mostrar(K.POSE_A['grudado'])
        k.opacity = 0
        k.precarregar([K.POSE_A[n] for n in ('agacha', 'pulo', 'saca1', 'arma1', 'corta1', 'segue1')])
        faiscas.estourar(ini[0], ini[1], CIANO, n=8, forca=dp(70), tam=ps)
        # ataca pelo canto do widget do lado de onde veio
        margem = 7 * ps                          # nao deixa o boneco sair da tela
        ataque = (max(bx0 + margem, rx - dp(6)) if esquerda else min(bx1 - margem, rx + rw + dp(6)),
                  cy + rh * 0.35)
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
            seq = K.sequencia([(2, K.POSE_A['saca1']), (2, K.POSE_A['arma1']),
                               (1, K.smear(K.POSE_A['corta1'], 150)),
                               (4, K.POSE_A['segue1']), (1, K.POSE_A['segue1'])])
            k.tocar(seq, on_quadro=lambda i: i == 4 and _impacto(), on_fim=_sai)

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
        bx0, _, bx1, _ = _limites()
        cx = (bx0 + bx1) / 2.0
        W = bx1 - bx0                                 # largura util (coluna)
        k.ancorar(cx, H + dp(60))
        k.mostrar(K.POSE_A['pulo'])
        k.precarregar([K.POSE_A[n] for n in K.POSE_A])
        grupos = [vis[i::4] for i in range(4)]
        golpes = [(0.20, 1, CIANO), (0.50, -1, AZUL), (0.35, 1, CIANO), (0.70, -1, AZUL)]

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
            alvo = (cx - lado * W * 0.28, y)

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
            y = (topo + base) / 2.0

            def _ataca():
                k.espelhar = False
                seq = K.sequencia([(4, K.POSE_A['final_arma']), (1, K.smear(K.POSE_A['final'], 130)),
                                   (8, K.POSE_A['final']), (1, K.POSE_A['final'])])

                def _q(q):
                    if q == 4:
                        for sent, cor in ((1, CIANO), (-1, AZUL)):
                            cam.add_widget(CorteMeiaLua(
                                centro=(cx, y), raio=max(W, H) * 0.5, ang_ini=160 if sent > 0 else 20,
                                ang_fim=-45 if sent > 0 else 225, espessura=dp(70), achat=0.5,
                                rotacao=35 * sent, cor=cor, dur_cheio=5 / 30.0, dur_decai=9 / 30.0))
                        faiscas.estourar(cx, y, CIANO, n=60, forca=dp(380), tam=ps)
                        _som('titulo')
                        _tremer(28)
                k.tocar(seq, on_quadro=_q, on_fim=_sai)
            _mover(k, k.ancora(), (cx, y), 0.2, altura=dp(50), on_fim=_ataca)

        def _sai():
            k.mostrar(K.POSE_A['pulo'])
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
