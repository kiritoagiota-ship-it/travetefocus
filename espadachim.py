"""
espadachim.py — TraveteFocus
  EspadachimPixel : espadachim estilo SAO em pixel art (desenhado em codigo),
                    com repouso (respirando) e combo de 2 golpes.
  CorteMeiaLua    : arco de espada em meia-lua (smear branco com brilho ciano)
                    que decai em filetes finos, como na referencia.
  golpe_tela()    : transicao em tela cheia com um corte gigante atravessando
                    a janela; troca de tela no pico (on_meio).

So instrucoes de canvas (sem shader, sem PIL). Callbacks de Clock nunca
deixam excecao escapar (no Android isso fecharia o app).
"""
import math
import random

from kivy.uix.widget import Widget
from kivy.graphics import (Color, Rectangle, Mesh, InstructionGroup,
                           PushMatrix, PopMatrix, Translate)
from kivy.graphics.texture import Texture
from kivy.properties import BooleanProperty
from kivy.clock import Clock
from kivy.core.window import Window

_Q = 1 / 30.0            # 1 quadro da referencia (30fps)

# ═══════════════════════════════════════════════════════════════════
#  SPRITE — partes em pixel art (linhas de cima para baixo, olhando p/ direita)
# ═══════════════════════════════════════════════════════════════════
_PALETA = {
    'H': (0.13, 0.14, 0.22, 1), 'h': (0.36, 0.40, 0.62, 1),     # cabelo
    'S': (1.00, 0.86, 0.74, 1), 's': (0.86, 0.66, 0.56, 1),     # pele
    'E': (0.08, 0.10, 0.18, 1),                                  # olho
    'C': (0.15, 0.15, 0.21, 1), 'c': (0.30, 0.31, 0.42, 1),     # sobretudo
    'G': (0.62, 0.66, 0.76, 1),                                  # detalhes cinza
    'P': (0.20, 0.20, 0.27, 1), 'B': (0.06, 0.06, 0.09, 1),     # calca / bota
    'W': (0.16, 0.18, 0.26, 1), 'L': (0.40, 0.96, 1.00, 1),     # lamina / fio ciano
    'O': (0.00, 0.78, 1.00, 0.85),                               # contorno (rim light)
}

_CABECA = [
    "....HHHHH....",
    "..HHHHHHHHH..",
    ".HHhhHHHHHHH.",
    "HHHHhHHHHHHHH",
    "HHHHHHHHHHHHH",
    "HHHHHHHSHHHSH",
    "HHHHHSSSSSSSS",
    "HHHHSSSSESSES",
    ".HHHSSSSESSES",
    "..HHSSSSSSSs.",
    "...HHsSSSss..",
]
_TRONCO = [
    "....CGGGC....",
    "...CCCGCCC...",
    "..CCCCGCCCC..",
    "..CCcCGCCCC..",
    "..CCcCGCCCC..",
    ".CCCcCGCCCCC.",
    ".CCCcCGCCCCC.",
    ".CCCCPPPCCCC.",
    "CCCC.PPP.CCCC",
    "CCC..P.P..CCC",
]
_PERNAS = {
    'repouso': [
        ".....PP.PP...",
        ".....PP.PP...",
        "....BBB.BBB..",
    ],
    'avanco': [
        "....PP...PP..",
        "...PP.....PP.",
        "..BBB.....BBB",
    ],
}

_GW, _GH = 52, 34        # grade total (sobra espaco para a espada)
_X0 = 17                 # coluna esquerda da cabeca

# pose: deslocamento do tronco (dx, dy), pernas, mao relativa ao ombro,
# angulo da espada (graus, 0 = para frente) e comprimento
_POSES = {
    'repouso0': dict(dx=0, dy=0, pernas='repouso', mao=(3, -4), ang=-40, comp=14),
    'repouso1': dict(dx=0, dy=-1, pernas='repouso', mao=(3, -5), ang=-42, comp=14),
    'antecipa': dict(dx=-1, dy=0, pernas='repouso', mao=(-4, 4), ang=145, comp=14),
    'golpe':    dict(dx=2, dy=-1, pernas='avanco', mao=(6, 0), ang=-4, comp=15),
    'segue':    dict(dx=2, dy=-1, pernas='avanco', mao=(5, -3), ang=-34, comp=15),
    'volta':    dict(dx=1, dy=0, pernas='avanco', mao=(4, 5), ang=118, comp=15),
}


def _estampar(px, mapa, x0, y_topo):
    for r, linha in enumerate(mapa):
        for c, ch in enumerate(linha):
            if ch != '.':
                px[(x0 + c, y_topo - r)] = ch


def _linha(px, x0, y0, x1, y1, ch, grossura=1):
    passos = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(passos + 1):
        x = round(x0 + (x1 - x0) * i / passos)
        y = round(y0 + (y1 - y0) * i / passos)
        px[(x, y)] = ch
        if grossura > 1:
            px[(x, y - 1)] = ch


def _montar_pose(nome):
    p = _POSES[nome]
    px = {}
    dx, dy = p['dx'], p['dy']
    pernas = _PERNAS[p['pernas']]
    y_pernas = len(pernas)                  # pes em y=1
    topo_tronco = y_pernas + len(_TRONCO) + dy
    _estampar(px, pernas, _X0, y_pernas)
    _estampar(px, _TRONCO, _X0 + dx, topo_tronco)
    _estampar(px, _CABECA, _X0 + dx, topo_tronco + len(_CABECA))

    # braco da frente (2px) + mao + espada
    ox, oy = _X0 + dx + 9, topo_tronco - 2
    mx, my = ox + p['mao'][0], oy + p['mao'][1]
    _linha(px, ox, oy, mx, my, 'C', grossura=2)
    px[(mx, my)] = 'S'
    px[(mx + 1, my)] = 's'
    a = math.radians(p['ang'])
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    for k in (-2, -1):                                   # cabo
        px[(round(mx + ux * k), round(my + uy * k))] = 'c'
    for k in (-1, 0, 1):                                 # guarda
        px[(round(mx + ux + nx * k), round(my + uy + ny * k))] = 'G'
    for k in range(2, p['comp'] + 1):                    # lamina + fio ciano
        bx, by = mx + ux * k, my + uy * k
        px[(round(bx), round(by))] = 'W'
        px[(round(bx + nx), round(by + ny))] = 'L'
    px[(round(mx + ux * (p['comp'] + 1)), round(my + uy * (p['comp'] + 1)))] = 'L'

    # contorno automatico (rim light ciano) para ler no fundo escuro
    for (x, y) in list(px.keys()):
        for vx, vy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + vx, y + vy)
            if q not in px:
                px[q] = 'O'
    return px


_PIXELS = {nome: _montar_pose(nome) for nome in _POSES}


class EspadachimPixel(Widget):
    espelhar = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._grupos = {}
        self._pose = 'repouso0'
        self._ev_idle = None
        self._evs = []
        self._cortes = []
        self._em_ataque = False
        self._ps_grupos = None
        # pixels em coordenadas locais; a posicao vem so do Translate
        self.canvas.add(PushMatrix())
        self._translate = Translate(0, 0)
        self.canvas.add(self._translate)
        self._grupo_atual = InstructionGroup()
        self.canvas.add(self._grupo_atual)
        self.canvas.add(PopMatrix())
        self.bind(pos=self._posicionar, x=self._posicionar, y=self._posicionar,
                  size=self._reconstruir, espelhar=self._reconstruir)

    # ── desenho ─────────────────────────────────────────────────────
    def _escala(self):
        return max(1, int(min(self.width / _GW, self.height / _GH)))

    def _origem(self, ps):
        # x/y direto: center_x/center_y tem cache e podem estar velhos aqui
        cx = self.x + self.width / 2.0
        cy = self.y + self.height / 2.0
        return (cx - _GW * ps / 2.0, cy - _GH * ps / 2.0)

    def _construir_grupo(self, nome):
        ps = self._escala()
        g = InstructionGroup()
        pix = _PIXELS[nome]
        # une pixels vizinhos da mesma cor em retangulos horizontais
        linhas = {}
        for (x, y), ch in pix.items():
            gx = (_GW - 1 - x) if self.espelhar else x
            linhas.setdefault(y, []).append((gx, ch))
        for y, itens in linhas.items():
            itens.sort()
            i = 0
            while i < len(itens):
                x, ch = itens[i]
                j = i
                while j + 1 < len(itens) and itens[j + 1] == (itens[j][0] + 1, ch):
                    j += 1
                g.add(Color(*_PALETA[ch]))
                g.add(Rectangle(pos=(x * ps, y * ps), size=((j - i + 1) * ps, ps)))
                i = j + 1
        return g

    def _posicionar(self, *_):
        ox, oy = self._origem(self._escala())
        self._translate.xy = (ox, oy)

    def _reconstruir(self, *_):
        try:
            self._posicionar()
            self._grupos = {}
            if self.width <= 1 or self.height <= 1:
                self._grupo_atual.clear()
                return
            self._mostrar(self._pose)
        except Exception as e:
            print(f"[espadachim] reconstruir: {e}")

    def _mostrar(self, nome):
        self._pose = nome
        if self.width <= 1 or self.height <= 1:
            return
        self._posicionar()
        g = self._grupos.get(nome)
        if g is None:
            g = self._grupos[nome] = self._construir_grupo(nome)
        if g is self._grupo_atual:
            return
        idx = self.canvas.indexof(self._grupo_atual)
        self.canvas.remove(self._grupo_atual)
        self._grupo_atual = g
        self.canvas.insert(idx, g)

    def centro_peito(self):
        ps = self._escala()
        ox, oy = self._origem(ps)
        x = _X0 + 6 + _POSES[self._pose]['dx']
        if self.espelhar:
            x = _GW - 1 - x
        return ox + x * ps, oy + 10 * ps, ps

    # ── repouso ─────────────────────────────────────────────────────
    def iniciar_idle(self):
        self._em_ataque = False
        if self._ev_idle is None:
            self._ev_idle = Clock.schedule_interval(self._respirar, 0.45)
        self._mostrar('repouso0')

    def _respirar(self, dt):
        try:
            if not self._em_ataque:
                self._mostrar('repouso1' if self._pose == 'repouso0' else 'repouso0')
        except Exception as e:
            print(f"[espadachim] respirar: {e}")

    def on_parent(self, inst, parent):
        if parent is None:
            self.parar()

    def parar(self):
        if self._ev_idle is not None:
            self._ev_idle.cancel()
            self._ev_idle = None
        for ev in self._evs:
            ev.cancel()
        self._evs = []
        for c in self._cortes:
            try:
                if c.parent:
                    c.parent.remove_widget(c)
            except Exception:
                pass
        self._cortes = []
        self._em_ataque = False

    # ── ataque ──────────────────────────────────────────────────────
    def atacar(self, combo=True, on_impacto=None, on_fim=None):
        """Timing da referencia: antecipacao curta, impacto seco, meia-lua
        por ~4 quadros, filetes ~3 quadros, pose segurada, golpe de volta."""
        self._em_ataque = True
        for ev in self._evs:
            ev.cancel()
        self._evs = []
        passos = [(0.0, lambda: self._mostrar('antecipa')),
                  (3 * _Q, lambda: self._golpe(1, on_impacto)),
                  (7 * _Q, lambda: self._mostrar('segue'))]
        t = 14 * _Q
        if combo:
            passos += [(t, lambda: self._mostrar('antecipa')),
                       (t + 2 * _Q, lambda: self._golpe(2, on_impacto)),
                       (t + 6 * _Q, lambda: self._mostrar('segue'))]
            t += 14 * _Q
        passos += [(t, lambda: self._mostrar('repouso0')),
                   (t + 4 * _Q, lambda: self._fim_ataque(on_fim))]
        for quando, acao in passos:
            self._evs.append(Clock.schedule_once(
                lambda dt, a=acao: self._seguro(a), quando))

    @staticmethod
    def _seguro(acao):
        try:
            acao()
        except Exception as e:
            print(f"[espadachim] passo do ataque ignorado: {e}")

    def _fim_ataque(self, on_fim):
        self._em_ataque = False
        if on_fim:
            on_fim()

    def _golpe(self, n, on_impacto):
        self._mostrar('golpe' if n == 1 else 'volta')
        cx, cy, ps = self.centro_peito()
        esp = -1 if self.espelhar else 1

        def _ang(g):                      # espelha o angulo se olhar p/ esquerda
            return g if esp > 0 else 180 - g
        if n == 1:      # de cima/tras, passando pela frente, ate baixo/tras ('>')
            corte = CorteMeiaLua(centro=(cx + esp * ps * 4, cy + ps), raio=ps * 21,
                                 ang_ini=_ang(160), ang_fim=_ang(-150),
                                 espessura=ps * 9, achat=0.42)
        else:           # golpe de volta: da frente/baixo subindo por cima da cabeca
            corte = CorteMeiaLua(centro=(cx, cy + ps * 7), raio=ps * 19,
                                 ang_ini=_ang(-30), ang_fim=_ang(200),
                                 espessura=ps * 8, achat=0.5)
        self.add_widget(corte)
        self._cortes.append(corte)
        corte.bind(parent=lambda w, p: (p is None and w in self._cortes and self._cortes.remove(w)))
        if on_impacto:
            try:
                on_impacto(n)
            except Exception as e:
                print(f"[espadachim] on_impacto: {e}")


# ═══════════════════════════════════════════════════════════════════
#  CORTE EM MEIA-LUA
# ═══════════════════════════════════════════════════════════════════
_TEX_FAIXA = {}


def _textura_faixa(dureza):
    """Alpha suave atravessando a faixa (v); `dureza` alta = borda mais seca."""
    tex = _TEX_FAIXA.get(dureza)
    if tex is None:
        nv = 32
        buf = bytearray(4 * nv * 4)
        for y in range(nv):
            v = y / (nv - 1.0)
            a = max(0.0, min(1.0, (1 - abs(2 * v - 1)) * dureza))
            a = a * a * (3 - 2 * a)
            for x in range(4):
                i = (y * 4 + x) * 4
                buf[i] = buf[i + 1] = buf[i + 2] = 255
                buf[i + 3] = int(255 * a)
        dados = bytes(buf)
        tex = Texture.create(size=(4, nv), colorfmt='rgba')
        tex.wrap = 'clamp_to_edge'
        tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
        tex.add_reload_observer(
            lambda t: t.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte'))
        _TEX_FAIXA[dureza] = tex
    return tex


class CorteMeiaLua(Widget):
    """Arco crescente: grosso perto da ponta que avanca, afinando nas pontas.
    Coordenadas em relacao ao pai (ou a janela, se adicionado na Window)."""
    _N = 48

    def __init__(self, centro, raio, ang_ini, ang_fim, espessura,
                 cor=(0.0, 0.9, 1.0), dur_cheio=4 * _Q, dur_decai=3 * _Q,
                 on_fim=None, achat=1.0, rotacao=0.0, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self._c = centro
        self._r = float(raio)
        self._a0 = math.radians(ang_ini)
        self._a1 = math.radians(ang_fim)
        self._esp = float(espessura)
        self._cor = cor
        self._dc = dur_cheio
        self._dd = dur_decai
        self._on_fim = on_fim
        self._achat = float(achat)          # elipse: altura/largura
        rot = math.radians(rotacao)
        self._cr, self._sr = math.cos(rot), math.sin(rot)
        self._t = 0.0
        self._ev = None
        self._ruido = [random.uniform(-1, 1) for _ in range(self._N)]
        idx = list(range(2 * self._N))
        vz = [0.0] * (8 * self._N)
        with self.canvas:
            self._c_glow = Color(*cor, 0)
            self._m_glow = Mesh(mode='triangle_strip', indices=idx, vertices=list(vz))
            self._c_core = Color(1, 1, 1, 0)
            self._m_core = Mesh(mode='triangle_strip', indices=idx, vertices=list(vz))
            self._c_f1 = Color(1, 1, 1, 0)
            self._m_f1 = Mesh(mode='triangle_strip', indices=idx, vertices=list(vz))
            self._c_f2 = Color(1, 1, 1, 0)
            self._m_f2 = Mesh(mode='triangle_strip', indices=idx, vertices=list(vz))

    def on_parent(self, inst, parent):
        try:
            if parent is not None:
                try:
                    self._m_glow.texture = _textura_faixa(1.2)
                    self._m_core.texture = _textura_faixa(5.0)
                    self._m_f1.texture = _textura_faixa(2.5)
                    self._m_f2.texture = _textura_faixa(2.5)
                except Exception as e:
                    print(f"[corte] textura: {e}")
                if self._ev is None:
                    self._desenhar()
                    self._ev = Clock.schedule_interval(self._tick, 1 / 60.)
            elif self._ev is not None:
                self._ev.cancel()
                self._ev = None
        except Exception as e:
            print(f"[corte] on_parent: {e}")

    def _faixa(self, mesh, s_ini, s_fim, r_ext, grossura, perfil=True):
        n = self._N
        vs = []
        cx, cy = self._c
        for i in range(n):
            s = s_ini + (s_fim - s_ini) * i / (n - 1.0)
            a = self._a0 + (self._a1 - self._a0) * s
            if perfil:
                # crescente: zero nas pontas, mais grosso perto da ponta que avanca
                g = grossura * (math.sin(math.pi * s) ** 0.75) * (0.45 + 0.55 * s)
            else:
                g = grossura * math.sin(math.pi * (i / (n - 1.0))) ** 0.5
            ext = r_ext + g * 0.10 + self._ruido[i] * grossura * 0.03 * (1 - s)
            inte = ext - g
            ca, sa = math.cos(a), math.sin(a) * self._achat
            cr, sr = self._cr, self._sr
            xe, ye = ca * ext, sa * ext
            xi, yi = ca * inte, sa * inte
            vs.extend((cx + xe * cr - ye * sr, cy + xe * sr + ye * cr, 0.5, 0.0,
                       cx + xi * cr - yi * sr, cy + xi * sr + yi * cr, 0.5, 1.0))
        mesh.vertices = vs

    def _desenhar(self):
        t = self._t
        r, e = self._r, self._esp
        cr, cg, cb = self._cor
        if t < self._dc:
            aparece = min(1.0, t / (1.3 * _Q))          # surge em ~1 quadro
            self._faixa(self._m_core, 0.0, aparece, r, e)
            self._faixa(self._m_glow, 0.0, aparece, r + e * 0.18, e * 1.55)
            self._c_core.a = 1.0
            self._c_glow.rgba = (cr, cg, cb, 0.55)
            self._c_f1.a = self._c_f2.a = 0.0
        else:
            k = min(1.0, (t - self._dc) / self._dd)
            ini = 0.15 + 0.55 * k                        # recolhe em direcao a ponta
            self._faixa(self._m_core, ini, 1.0, r, e * (1 - k) ** 2 * 0.6)
            self._faixa(self._m_glow, ini, 1.0, r + e * 0.1, e * 1.2 * (1 - k))
            self._c_core.a = (1 - k) * 0.9
            self._c_glow.rgba = (cr, cg, cb, 0.45 * (1 - k))
            fino = max(1.0, e * 0.075 * (1 - k * 0.6))
            self._faixa(self._m_f1, ini + 0.05, 1.0, r + e * 0.05, fino, perfil=False)
            self._faixa(self._m_f2, ini + 0.18, 0.92, r - e * 0.32, fino * 0.8, perfil=False)
            self._c_f1.a = 0.95 * (1 - k)
            self._c_f2.a = 0.75 * (1 - k)

    def _tick(self, dt):
        try:
            self._t += min(dt, 1 / 20.)
            if self._t >= self._dc + self._dd:
                self._encerrar()
                return
            self._desenhar()
        except Exception as e:
            print(f"[corte] frame ignorado: {e}")
            self._encerrar()

    def _encerrar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        try:
            if self.parent:
                self.parent.remove_widget(self)
        except Exception:
            pass
        cb, self._on_fim = self._on_fim, None
        if cb:
            try:
                cb()
            except Exception as e:
                print(f"[corte] on_fim: {e}")


# ═══════════════════════════════════════════════════════════════════
#  TRANSICAO EM TELA CHEIA
# ═══════════════════════════════════════════════════════════════════
def golpe_tela(on_meio=None, on_fim=None, cor=(0.0, 0.9, 1.0), sentido=1):
    """Corte gigante atravessando a janela (<= 0,5s). on_meio e chamado no
    pico (tela escurecida) para trocar de tela; garantido mesmo em erro."""
    estado = {'meio': False, 'fim': False}
    overlay = [None]

    def _meio():
        if not estado['meio']:
            estado['meio'] = True
            if on_meio:
                try:
                    on_meio()
                except Exception as e:
                    print(f"[golpe_tela] on_meio: {e}")

    def _fim(*_):
        _meio()
        if not estado['fim']:
            estado['fim'] = True
            try:
                if overlay[0] is not None and overlay[0].parent:
                    Window.remove_widget(overlay[0])
            except Exception:
                pass
            if on_fim:
                try:
                    on_fim()
                except Exception as e:
                    print(f"[golpe_tela] on_fim: {e}")

    try:
        W, H = Window.size
        ov = Widget(size=(W, H), pos=(0, 0))
        overlay[0] = ov
        with ov.canvas:
            c_veu = Color(0.0, 0.0, 0.02, 0.0)
            Rectangle(pos=(0, 0), size=(W, H))
            c_flash = Color(0.75, 0.95, 1.0, 0.0)
            Rectangle(pos=(0, 0), size=(W, H))
        Window.add_widget(ov)

        diag = math.hypot(W, H)
        raio = diag * 0.85
        # circulo grande cujo arco passa pelo centro da tela, na diagonal
        # (sentido 1: do canto superior esquerdo ao inferior direito)
        if sentido >= 0:
            nx, ny = -H / diag, -W / diag          # centro fica abaixo/esquerda
        else:
            nx, ny = H / diag, -W / diag           # centro fica abaixo/direita
        centro = (W / 2.0 + nx * raio, H / 2.0 + ny * raio)
        meio = math.degrees(math.atan2(-ny, -nx))
        a0, a1 = (meio + 42, meio - 42) if sentido >= 0 else (meio - 42, meio + 42)
        corte = CorteMeiaLua(centro=centro, raio=raio, ang_ini=a0, ang_fim=a1,
                             espessura=min(W, H) * 0.17, cor=cor,
                             dur_cheio=4 * _Q, dur_decai=9 * _Q)
        ov.add_widget(corte)

        t = [0.0]

        def _tick(dt):
            try:
                t[0] += min(dt, 1 / 20.)
                x = t[0]
                # veu escurece ate o impacto e clareia depois
                if x < 0.13:
                    c_veu.a = 0.55 * (x / 0.13)
                else:
                    c_veu.a = max(0.0, 0.55 * (1 - (x - 0.18) / 0.28)) if x > 0.18 else 0.55
                # flash curto no impacto
                if 0.12 <= x < 0.30:
                    c_flash.a = 0.13 * (1 - (x - 0.12) / 0.18)
                else:
                    c_flash.a = 0.0
                if x >= 0.14:
                    _meio()
                if x >= 0.48:
                    ev.cancel()
                    _fim()
                    return False
            except Exception as e:
                print(f"[golpe_tela] frame: {e}")
                ev.cancel()
                _fim()
                return False

        ev = Clock.schedule_interval(_tick, 1 / 60.)
        # rede de seguranca: se o loop parar por qualquer motivo
        Clock.schedule_once(lambda dt: _fim(), 1.2)
    except Exception as e:
        print(f"[golpe_tela] falhou, trocando direto: {e}")
        _fim()
