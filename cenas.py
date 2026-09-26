"""
cenas.py — TraveteFocus
Cenas com o Kirito pixel art (kirito.py) + cortes em meia-lua (espadachim.py):

  cena_titulo(tela, label, on_fim)  Kirito surge grudado numa borda aleatoria,
                                    pula ate o titulo e, com a Elucidator e
                                    depois a Dark Repulser, escreve
                                    "TRAVETE FOCUS" com o rastro dos golpes.
  espiar()                          so a cabeca dele espia de um canto (PIN ok).
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
           cor_fantasma=CIANO, on_fim=None):
    """Move a ancora do Kirito em arco (parabola de `altura`), girando de
    rot[0] a rot[1], deixando afterimages."""
    t = [0.0]
    cont = [0]

    def _p(dt):
        try:
            t[0] += dt
            u = min(1.0, t[0] / dur)
            e = 1 - (1 - u) ** 2 if altura >= 0 else u * u
            x = de[0] + (para[0] - de[0]) * e
            y = de[1] + (para[1] - de[1]) * e + altura * 4 * u * (1 - u)
            k.ancorar(x, y)
            if rot is not None:
                k.rotacao = rot[0] + (rot[1] - rot[0]) * e
            cont[0] += 1
            if fantasmas and cont[0] % 2 == 0 and u < 0.95:
                k.fantasma(cor=cor_fantasma, alfa=0.28, duracao=0.2)
            if u >= 1:
                if on_fim:
                    on_fim()
                return False
        except Exception as ex:
            print(f"[cenas] mover: {ex}")
            if on_fim:
                on_fim()
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


def cena_titulo(tela, label, on_fim=None, texto="TRAVETE FOCUS"):
    """Monta e roda a cena sobre `tela` (Screen). `label` define onde o
    titulo fica e o tamanho da fonte. Devolve a camada (para limpar)."""
    fim = _Uma(on_fim)
    camada = Widget(size_hint=(None, None), size=tela.size, pos=(0, 0))
    estado = {'evs': [], 'vivo': True}

    def depois(t, fn):
        def _x(dt):
            if not estado['vivo']:
                return
            try:
                fn()
            except Exception as e:
                print(f"[cena] passo ignorado: {e}")
        estado['evs'].append(Clock.schedule_once(_x, t))

    def encerrar(sucesso=True):
        estado['vivo'] = False
        for ev in estado['evs']:
            ev.cancel()
        fim()

    try:
        tela.add_widget(camada)
        W, H = tela.size
        # area do titulo em coords da tela
        wx, wy = label.to_window(label.x, label.y)
        lx, ly = tela.to_widget(wx, wy)
        fs = label.font_size
        titulo = TituloLuz(texto, fs, pos=(lx, ly), size=label.size)
        camada.add_widget(titulo)
        camada._titulo = titulo
        faiscas = K.Faiscas()
        ps = _ps_para(W, H)
        kk = K.KiritoPixel(ps=ps)
        kk.opacity = 0
        camada.add_widget(kk)
        camada.add_widget(faiscas)
        alt_boneco = 24 * ps

        # ── 1. surge grudado numa borda aleatoria ─────────────────────
        borda = random.choice(('esq', 'dir', 'teto'))
        pe = 8 * ps + dp(2)                     # quadril ate os pes
        if borda == 'esq':
            ini = (pe, random.uniform(0.18, 0.42) * H)
            rot0, esp = -90.0, False
        elif borda == 'dir':
            ini = (W - pe, random.uniform(0.18, 0.42) * H)
            rot0, esp = 90.0, True
        else:
            ini = (random.uniform(0.2, 0.8) * W, H - pe)
            rot0, esp = 180.0, random.random() < 0.5
        kk.espelhar = esp
        kk.rotacao = rot0
        kk.ancorar(*ini)
        kk.mostrar(K.POSE_A['grudado'])
        seq_all = []
        for nome in K.POSE_A:
            seq_all.append(K.POSE_A[nome])
        kk.precarregar(seq_all)

        def _equilibrio():
            # balanca preso na borda (o sobretudo esvoaca, pisca)
            base = K.POSE_A['grudado']
            quadros = []
            for f in range(30):
                q = dict(base)
                q['capa'] = 1.0 + 0.8 * math.sin(f / 30.0 * 4 * math.pi)
                q['cabelo'] = 0.6 + 0.6 * math.sin(f / 30.0 * 4 * math.pi + 1)
                q['olhos'] = 'f' if f in (18, 19) else 'a'
                quadros.append(q)
            kk.tocar(quadros, loop=True)
            t = [0.0]

            def _b(dt):
                if not estado['vivo'] or kk._em_pulo:
                    return False
                t[0] += dt
                kk.rotacao = rot0 + 6 * math.sin(t[0] * 5.5)
            Clock.schedule_interval(_b, 1 / 60.)

        kk._em_pulo = False

        def _surge():
            ax, ay = kk.ancora()
            faiscas.estourar(ax, ay, CIANO, n=10, forca=dp(90), tam=ps)
            _equilibrio()
            t = [0.0]

            def _f(dt):
                t[0] += dt
                kk.opacity = min(1.0, t[0] / 0.25)
                return kk.opacity < 1
            Clock.schedule_interval(_f, 1 / 60.)

        depois(0.05, _surge)

        # ── 2. pula ate o comeco do titulo ────────────────────────────
        y_ataque = ly + label.height / 2.0 + alt_boneco * 0.15
        cx1, _ = titulo.x_do_trecho(*_TRECHOS[0])
        lado = -1 if cx1 > ini[0] else 1            # de que lado do trecho ele fica
        alvo1 = (cx1 + lado * titulo.th * 1.1, y_ataque)

        def _pula():
            kk._em_pulo = True
            kk.espelhar = lado > 0                   # olha para o titulo
            seq = K.sequencia([(3, K.POSE_A['agacha']), (1, K.POSE_A['pulo'])])
            kk.tocar(seq)
            giro = 360.0 * (1 if lado < 0 else -1)
            _som('corte')
            depois(0.10, lambda: _mover(kk, kk.ancora(), alvo1, 0.42, altura=H * 0.12,
                                        rot=(rot0, giro), on_fim=_golpe1))
        depois(1.05, _pula)

        # ── 3. golpe 1 (Elucidator): escreve "TRA" ────────────────────
        def _corte_titulo(i, cor, sentido=1, grande=False):
            i0, i1 = _TRECHOS[i]
            cx, cy = titulo.x_do_trecho(i0, i1)
            larg = max(titulo._larg[i1] - titulo._larg[i0], titulo.th)
            raio = larg * (0.95 if not grande else 3.2)
            a0, a1 = (160, -150) if sentido > 0 else (20, 330)
            camada.add_widget(CorteMeiaLua(centro=(cx, cy), raio=raio, ang_ini=a0,
                                           ang_fim=a1, espessura=titulo.th * 0.9,
                                           achat=0.42, cor=cor))
            titulo.revelar(i0, i1, cor=(1, 1, 1) if cor == CIANO else AZUL)
            faiscas.estourar(cx, cy, cor, n=16 if not grande else 40,
                             forca=dp(160) if not grande else dp(300), tam=ps)
            _som('corte')
            _tremer(6 if not grande else 22)

        def _golpe1():
            kk.rotacao = 0
            seq = K.sequencia([
                (3, K.POSE_A['saca1']), (3, K.POSE_A['arma1']),
                (1, K.smear(K.POSE_A['corta1'], 150)),
                (5, K.POSE_A['segue1']), (1, K.POSE_A['segue1'])])
            kk.tocar(seq, on_quadro=lambda i: i == 6 and _corte_titulo(0, CIANO),
                     on_fim=_saca2)

        # ── 4. saca a Dark Repulser (brilho azul) ─────────────────────
        def _saca2():
            seq = K.sequencia([(4, K.POSE_A['pega2']), (4, K.POSE_A['saca2']),
                               (4, K.POSE_A['dupla']), (1, K.POSE_A['dupla'])])

            def _q(i):
                if i == 5:
                    mx, my = kk.ponto_mao(2)
                    faiscas.estourar(mx, my, AZUL, n=18, forca=dp(120), tam=ps)
                    _som('sacar')
            kk.tocar(seq, on_quadro=_q, on_fim=lambda: _combo(1))

        # ── 5. combo com as duas espadas: "VE", "TE ", "FO" ───────────
        def _combo(i):
            if i > 3:
                _final()
                return
            cx, _ = titulo.x_do_trecho(*_TRECHOS[i])
            lado_i = 1 if i % 2 else -1
            alvo = (cx + lado_i * titulo.th * 0.9, y_ataque + (titulo.th * 0.4 if i == 2 else 0))
            kk.espelhar = lado_i > 0
            giro = i == 2
            pose_arma = K.POSE_A['giro_a' if i == 2 else 'x_arma']
            pose_corta = K.POSE_A['giro_b' if i == 2 else 'x_corta']
            cor = AZUL if i % 2 else CIANO

            def _ataca():
                seq = K.sequencia([(2, pose_arma), (1, K.smear(pose_corta, 140)),
                                   (4, pose_corta), (1, pose_corta)])
                kk.tocar(seq, on_quadro=lambda q: q == 2 and _corte_titulo(i, cor, sentido=lado_i),
                         on_fim=lambda: _combo(i + 1))
            _mover(kk, kk.ancora(), alvo, 0.13, altura=titulo.th * 0.5,
                   rot=(0, 360 * (-lado_i)) if giro else None,
                   cor_fantasma=cor, on_fim=_ataca)

        # ── 6. golpe final em X: "CUS" + clarao ───────────────────────
        def _final():
            cx, cy = titulo.x_do_trecho(0, len(texto))
            alvo = (cx, y_ataque + titulo.th * 1.2)
            kk.espelhar = False

            def _ataca():
                kk.rotacao = 0
                seq = K.sequencia([(5, K.POSE_A['final_arma']), (1, K.smear(K.POSE_A['final'], 130)),
                                   (8, K.POSE_A['final']), (1, K.POSE_A['final'])])

                def _q(q):
                    if q == 5:
                        i0, i1 = _TRECHOS[4]
                        titulo.revelar(i0, i1)
                        for sent, cor in ((1, CIANO), (-1, AZUL)):
                            camada.add_widget(CorteMeiaLua(
                                centro=(cx, cy), raio=titulo.tw * 0.62, ang_ini=160 if sent > 0 else 20,
                                ang_fim=-45 if sent > 0 else 225, espessura=titulo.th * 1.2,
                                achat=0.34, rotacao=12 * sent, cor=cor,
                                dur_cheio=5 / 30.0, dur_decai=8 / 30.0))
                        faiscas.estourar(cx, cy, CIANO, n=40, forca=dp(320), tam=ps)
                        _som('golpe_final')
                        _tremer(24)
                        depois(0.12, titulo.clarao_final)
                kk.tocar(seq, on_quadro=_q, on_fim=_pousa)
            _mover(kk, kk.ancora(), alvo, 0.22, altura=titulo.th * 1.5, on_fim=_ataca)

        # ── 7. pousa, guarda as espadas e sai ─────────────────────────
        def _pousa():
            destino = (min(W - dp(40), titulo.x + titulo.width * 0.5 + titulo.tw * 0.45),
                       ly - alt_boneco * 0.3)

            def _guarda():
                seq = K.sequencia([(5, K.POSE_A['pousa']), (6, K.POSE_A['guarda2']),
                                   (6, K.POSE_A['fim']), (1, K.POSE_A['fim'])])
                kk.tocar(seq, on_fim=_sai)
            _mover(kk, kk.ancora(), destino, 0.3, altura=titulo.th, fantasmas=False,
                   on_fim=_guarda)

        def _sai():
            kk.mostrar(K.POSE_A['pulo'])
            ax, ay = kk.ancora()
            _mover(kk, (ax, ay), (ax + dp(30), H + dp(120)), 0.35, on_fim=_acabou)

        def _acabou():
            try:
                camada.remove_widget(kk)
            except Exception:
                pass
            encerrar()

        # rede de seguranca: a cena nunca prende o app
        Clock.schedule_once(lambda dt: (titulo.completo(), encerrar()) if estado['vivo'] else None, 9.0)
    except Exception as e:
        print(f"[cena] falhou, seguindo sem ela: {e}")
        encerrar()
    return camada


def limpar_cena(camada):
    try:
        for w in list(camada.children):
            if isinstance(w, K.KiritoPixel):
                w.parar()
        if camada.parent:
            camada.parent.remove_widget(camada)
    except Exception as e:
        print(f"[cena] limpar: {e}")


# ═══════════════════════════════════════════════════════════════════
#  ESPIAR (PIN aceito)
# ═══════════════════════════════════════════════════════════════════
def espiar(duracao=1.3):
    """So a cabeca do Kirito aparece num canto da janela e some."""
    try:
        W, H = Window.size
        ps = _ps_para(W, H)
        k = K.KiritoPixel(ps=ps)
        borda = random.choice(('esq', 'dir', 'baixo'))
        corpo = 16 * ps                     # quanto do corpo fica escondido
        bx0, _, bx1, _ = _limites()
        if bx0 > 1 or bx1 < W - 1:
            borda = 'baixo'                 # coluna no PC: pela lateral o corpo apareceria
        if borda == 'esq':
            k.rotacao, k.espelhar = -90, False
            y = random.uniform(0.2, 0.75) * H
            fora, dentro = (bx0 - corpo - 8 * ps, y), (bx0 - corpo * 0.35, y)
        elif borda == 'dir':
            k.rotacao, k.espelhar = 90, True
            y = random.uniform(0.2, 0.75) * H
            fora, dentro = (bx1 + corpo + 8 * ps, y), (bx1 + corpo * 0.35, y)
        else:
            k.rotacao, k.espelhar = 0, random.random() < 0.5
            x = bx0 + random.uniform(0.15, 0.85) * (bx1 - bx0)
            fora, dentro = (x, -corpo - 12 * ps), (x, -corpo * 0.5)
        k.ancorar(*fora)
        k.mostrar(K.POSE_A['fim'])
        Window.add_widget(k)

        def _pisca():
            q = dict(K.POSE_A['fim'])
            q['olhos'] = 'f'
            k.tocar([q, q, q, K.POSE_A['fim']])

        def _volta():
            _mover(k, k.ancora(), fora, 0.22, fantasmas=False, on_fim=_tira)

        def _tira():
            try:
                k.parar()
                Window.remove_widget(k)
            except Exception:
                pass

        _mover(k, fora, dentro, 0.25, fantasmas=False)
        Clock.schedule_once(lambda dt: _pisca(), 0.55)
        Clock.schedule_once(lambda dt: _volta(), duracao - 0.25)
        Clock.schedule_once(lambda dt: _tira(), duracao + 0.6)      # seguranca
    except Exception as e:
        print(f"[espiar] ignorado: {e}")


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
                        _som('corte')
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
                        _som('golpe_final')
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
