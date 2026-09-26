"""
kirito.py — TraveteFocus
Kirito em pixel art, montado por partes a partir de parametros de pose
(tronco, pernas, 2 bracos, 2 espadas, cabelo e sobretudo esvoacando, olhos),
o que permite muitos quadros interpolados por golpe.

  Elucidator    : espada preta (mao da frente)
  Dark Repulser : espada azulada (mao de tras), sacada no meio do combo

KiritoPixel(Widget)  — desenha poses/sequencias (cache por pose), idle com
                       respiracao/piscar, giro/rotacao, afterimages.
Faiscas(Widget)      — faiscas quadradas (pixel) nos impactos.

So instrucoes de canvas; nenhum callback de Clock deixa excecao escapar.
"""
import math
import random

from kivy.uix.widget import Widget
from kivy.graphics import (Color, Rectangle, InstructionGroup, PushMatrix,
                           PopMatrix, Translate, Rotate, Scale)
from kivy.properties import BooleanProperty, NumericProperty
from kivy.clock import Clock

FPS = 30.0

_PALETA = {
    'H': (0.13, 0.14, 0.22, 1), 'h': (0.36, 0.40, 0.62, 1),     # cabelo
    'S': (1.00, 0.86, 0.74, 1), 's': (0.86, 0.66, 0.56, 1),     # pele
    'E': (0.08, 0.10, 0.18, 1),                                  # olho
    'C': (0.15, 0.15, 0.21, 1), 'c': (0.30, 0.31, 0.42, 1),     # sobretudo
    'G': (0.62, 0.66, 0.76, 1),                                  # detalhes cinza
    'P': (0.20, 0.20, 0.27, 1), 'B': (0.06, 0.06, 0.09, 1),     # calca / bota
    'M': (0.09, 0.09, 0.13, 1),                                  # luva
    # Elucidator (preta)
    'W': (0.10, 0.10, 0.15, 1), 'w': (0.58, 0.62, 0.76, 1),
    'K': (0.20, 0.20, 0.27, 1), 'g': (0.36, 0.36, 0.46, 1),
    # Dark Repulser (azulada, cristalina)
    'R': (0.40, 0.78, 1.00, 1), 'r': (0.86, 0.97, 1.00, 1), 'y': (0.30, 0.62, 0.86, 1),
    # rastro de movimento da lamina (smear em pixel)
    'X': (0.85, 0.97, 1.00, 0.55), 'x': (0.50, 0.85, 1.00, 0.35),
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
_CABECA_PISCA = [linha for linha in _CABECA]
_CABECA_PISCA[7] = "HHHHSSSSSSSSS"          # olho fechado = so a linha de baixo
_TRONCO = [
    "....CGGGC....",
    "...CCCGCCC...",
    "..CCCCGCCCC..",
    "..CCcCGCCCC..",
    "..CCcCGCCCC..",
    ".CCCcCGCCCCC.",
    ".CCCcCGCCCCC.",
    ".CCCCPPPCCCC.",
]
_PERNAS = {
    'repouso':  ["....PP.PP....", "....PP.PP....", "...BBB.BBB..."],
    'avanco':   ["...PP...PP...", "..PP.....PP..", ".BBB.....BBB."],
    'agachado': ["..PPP..PPP...", "..BBB..BBBB.."],
    'pulo':     ["...PPP.PPP...", "....BB..BB..."],
    'grudado':  [".PPP...PPP...", ".BB.....BB..."],
}

GW, GH = 64, 50          # grade total (espadas cabem para qualquer lado)
_X0 = 25                 # coluna esquerda do tronco/cabeca
_PES = 8                 # linha dos pes


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


def _espada(px, mx, my, ang, comp, tipo, smear_de=None):
    """tipo 1 = Elucidator (preta), 2 = Dark Repulser (azulada)."""
    lam, fio, guarda = ('W', 'w', 'g') if tipo == 1 else ('R', 'r', 'y')
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    # rastro (smear) antes da lamina, para ficar por baixo
    if smear_de is not None and abs(smear_de - ang) > 8:
        passo = 7 if smear_de < ang else -7
        g = smear_de
        while (passo > 0 and g < ang) or (passo < 0 and g > ang):
            ga = math.radians(g)
            for k in range(int(comp * 0.45), comp + 1):
                q = (round(mx + math.cos(ga) * k), round(my + math.sin(ga) * k))
                if q not in px:
                    px[q] = 'x' if k < comp * 0.75 else 'X'
            g += passo
    for k in (-2, -1):                                   # cabo
        px[(round(mx + ux * k), round(my + uy * k))] = 'K'
    for k in (-1, 0, 1):                                 # guarda
        px[(round(mx + ux + nx * k), round(my + uy + ny * k))] = guarda
    for k in range(2, comp + 1):                         # lamina + fio
        bx, by = mx + ux * k, my + uy * k
        px[(round(bx), round(by))] = lam
        px[(round(bx + nx), round(by + ny))] = fio
    px[(round(mx + ux * (comp + 1)), round(my + uy * (comp + 1)))] = fio


def _cabo_nas_costas(px, x, y, tipo):
    guarda = 'g' if tipo == 1 else 'y'
    px[(x, y)] = guarda
    px[(x - 1, y)] = guarda
    px[(x + 1, y)] = guarda
    px[(x, y + 1)] = 'K'
    px[(x, y + 2)] = 'K'


# pose padrao: todos os campos que a montagem entende
POSE_BASE = dict(dx=0, dy=0, pernas='repouso', olhos='a', cabelo=0.0, capa=0.0,
                 lift=0.0, m1=(3, -5), a1=-40.0, c1=14, s1=None,
                 m2=None, a2=None, c2=14, s2=None)


def montar(p):
    """Pose (dict) -> {(x, y): cor}."""
    px = {}
    dx, dy = int(p['dx']), int(p['dy'])
    pernas = _PERNAS[p['pernas']]
    topo_tronco = _PES + len(pernas) + len(_TRONCO) - 1 + dy
    base_x = _X0 + dx
    ombro1 = (base_x + 9, topo_tronco - 2)
    ombro2 = (base_x + 3, topo_tronco - 2)

    # braco/espada de tras (atras do corpo)
    if p['m2'] is not None:
        mx, my = ombro2[0] + int(p['m2'][0]), ombro2[1] + int(p['m2'][1])
        _linha(px, ombro2[0], ombro2[1], mx, my, 'C', grossura=2)
        if p['a2'] is not None:
            _espada(px, mx, my, p['a2'], int(p['c2']), 2, p['s2'])
        px[(mx, my)] = 'M'
    if p['a2'] is None:
        _cabo_nas_costas(px, base_x + 1, topo_tronco + 1, 2)
    if p['a1'] is None:
        _cabo_nas_costas(px, base_x + 3, topo_tronco + 2, 1)

    # cabelo esvoacando atras da cabeca
    topo_cab = topo_tronco + len(_CABECA)
    cb = p['cabelo']
    # mechas continuas que se alongam para tras com o vento
    for linha, base in ((2, 1), (3, 2), (4, 2), (5, 3), (6, 2), (7, 3), (8, 1)):
        comp = base + int(round(max(0.0, cb) * (0.5 + linha * 0.12)))
        caida = int(round(max(0.0, cb) * 0.25 * (linha - 4) / 4.0))
        for i in range(comp):
            px[(base_x - 1 - i, topo_cab - linha - (caida if i > comp // 2 else 0))] = 'h' if (linha == 5 and i == comp - 1) else 'H'

    # sobretudo: abas de tras e da frente (parametrico = esvoaca)
    capa, lift = p['capa'], p['lift']
    y_cint = topo_tronco - len(_TRONCO)
    for k in range(6):
        y = y_cint - k + int(lift * k * 0.45)
        x_ini = base_x + 0 - int(capa * k * 0.55)
        x_fim = base_x + 4 - int(capa * k * 0.30)
        for x in range(x_ini, x_fim + 1):
            px[(x, y)] = 'c' if x == x_ini else 'C'
    for k in range(4):
        y = y_cint - k + int(lift * k * 0.3)
        for x in range(base_x + 8 - int(capa * k * 0.15), base_x + 12 - int(capa * k * 0.10)):
            px[(x, y)] = 'C'

    _estampar(px, pernas, _X0, _PES + len(pernas) - 1)
    _estampar(px, _TRONCO, base_x, topo_tronco)
    _estampar(px, _CABECA_PISCA if p['olhos'] == 'f' else _CABECA, base_x, topo_cab)

    # braco/espada da frente
    if p['m1'] is not None:
        mx, my = ombro1[0] + int(p['m1'][0]), ombro1[1] + int(p['m1'][1])
        _linha(px, ombro1[0], ombro1[1], mx, my, 'C', grossura=2)
        if p['a1'] is not None:
            _espada(px, mx, my, p['a1'], int(p['c1']), 1, p['s1'])
        px[(mx, my)] = 'M'
        px[(mx + 1, my)] = 'M'

    # contorno (rim light ciano) para ler no fundo escuro
    for (x, y) in list(px.keys()):
        if px[(x, y)] in 'xX':
            continue
        for vx, vy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + vx, y + vy)
            if q not in px:
                px[q] = 'O'
    return px


def pose(**kw):
    p = dict(POSE_BASE)
    p.update(kw)
    return p


def _chave(p):
    def r(v):
        if isinstance(v, float):
            return round(v, 1)
        if isinstance(v, tuple):
            return tuple(int(round(x)) for x in v)
        return v
    return tuple((k, r(p[k])) for k in sorted(p))


# ═══════════════════════════════════════════════════════════════════
#  SEQUENCIAS (keyframes interpolados a 30fps)
# ═══════════════════════════════════════════════════════════════════
_NUM = ('dx', 'dy', 'cabelo', 'capa', 'lift', 'a1', 'a2', 'c1', 'c2')


def _ease(t):
    return t * t * (3 - 2 * t)


def sequencia(chaves):
    """chaves: [(quadros, pose), ...] -> lista de poses (1 por quadro).
    `quadros` = duracao do trecho ate a proxima chave. Campos numericos e
    posicoes das maos interpolam; os demais trocam na chave."""
    out = []
    for i, (n, p0) in enumerate(chaves):
        p1 = chaves[i + 1][1] if i + 1 < len(chaves) else p0
        n = max(1, int(n))
        for f in range(n):
            t = _ease(f / float(n)) if p1 is not p0 else 0.0
            q = dict(p0)
            for k in _NUM:
                a, b = p0[k], p1[k]
                if a is not None and b is not None:
                    q[k] = a + (b - a) * t
            for k in ('m1', 'm2'):
                a, b = p0[k], p1[k]
                if a is not None and b is not None:
                    q[k] = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            out.append(q)
    return out


# ═══════════════════════════════════════════════════════════════════
#  WIDGET
# ═══════════════════════════════════════════════════════════════════
_CACHE = {}          # (chave_pose, espelhar) -> lista [(cor, x, y, larg)]


def _runs(p, espelhar):
    ch = (_chave(p), espelhar)
    runs = _CACHE.get(ch)
    if runs is None:
        pix = montar(p)
        linhas = {}
        for (x, y), c in pix.items():
            gx = (GW - 1 - x) if espelhar else x
            linhas.setdefault(y, []).append((gx, c))
        runs = []
        for y, itens in linhas.items():
            itens.sort()
            i = 0
            while i < len(itens):
                x, c = itens[i]
                j = i
                while j + 1 < len(itens) and itens[j + 1] == (itens[j][0] + 1, c):
                    j += 1
                runs.append((c, x, y, j - i + 1))
                i = j + 1
        runs.sort(key=lambda r: r[0])
        if len(_CACHE) > 600:
            _CACHE.clear()
        _CACHE[ch] = runs
    return runs


def _grupo(runs, ps, silhueta=None):
    g = InstructionGroup()
    cor_atual = None
    for c, x, y, n in runs:
        if silhueta is None:
            if c != cor_atual:
                g.add(Color(*_PALETA[c]))
                cor_atual = c
        elif cor_atual is None:
            g.add(Color(*silhueta))
            cor_atual = 1
        g.add(Rectangle(pos=(x * ps, y * ps), size=(n * ps, ps)))
    return g


class KiritoPixel(Widget):
    """Tamanho em pixels de tela = (GW*ps, GH*ps). Posicione pela ancora
    (centro do quadril) com ancorar(x, y). rotacao gira em torno da ancora."""
    espelhar = BooleanProperty(False)
    rotacao = NumericProperty(0.0)
    escala_y = NumericProperty(1.0)

    def __init__(self, ps=4, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self.ps = max(1, int(ps))
        self.size = (GW * self.ps, GH * self.ps)
        self._pose = pose()
        self._grupos = {}
        self._ev = None
        self._seq = []
        self._i = 0
        self._on_quadro = None
        self._on_fim = None
        self._loop = False
        with self.canvas:
            PushMatrix()
            self._tr = Translate(0, 0)
            self._rot = Rotate(angle=0, origin=(0, 0))
            self._sc = Scale(1, 1, 1)
        self._g = InstructionGroup()
        self.canvas.add(self._g)
        self.canvas.add(PopMatrix())
        self.bind(pos=self._mover, x=self._mover, y=self._mover,
                  rotacao=self._mover, escala_y=self._mover,
                  espelhar=lambda *_: self._redesenhar(forcar=True))
        self._mover()
        self._redesenhar()

    # ── geometria ────────────────────────────────────────────────────
    def ancora_local(self):
        """Centro do quadril em coordenadas do proprio sprite (px de tela)."""
        cx = (_X0 + 6) if not self.espelhar else (GW - 1 - (_X0 + 6))
        return (cx + 0.5) * self.ps, (_PES + 8) * self.ps

    def ancorar(self, x, y):
        ax, ay = self.ancora_local()
        self.pos = (x - ax, y - ay)

    def ancora(self):
        ax, ay = self.ancora_local()
        return self.x + ax, self.y + ay

    def ponto_mao(self, qual=1):
        """Posicao aproximada da mao (para centralizar cortes)."""
        p = self._pose
        pernas = _PERNAS[p['pernas']]
        topo_tronco = _PES + len(pernas) + len(_TRONCO) - 1 + int(p['dy'])
        base_x = _X0 + int(p['dx'])
        if qual == 1 and p['m1'] is not None:
            x, y = base_x + 9 + p['m1'][0], topo_tronco - 2 + p['m1'][1]
        elif qual == 2 and p['m2'] is not None:
            x, y = base_x + 3 + p['m2'][0], topo_tronco - 2 + p['m2'][1]
        else:
            x, y = base_x + 6, topo_tronco - 4
        if self.espelhar:
            x = GW - 1 - x
        return self.x + x * self.ps, self.y + y * self.ps

    def _mover(self, *_):
        self._tr.xy = (self.x, self.y)
        ax, ay = self.ancora_local()
        self._rot.origin = (ax, ay)
        self._rot.angle = self.rotacao
        self._sc.origin = (ax, ay)
        self._sc.y = self.escala_y

    # ── desenho ──────────────────────────────────────────────────────
    def mostrar(self, p):
        self._pose = p
        self._redesenhar()

    def _redesenhar(self, forcar=False):
        try:
            runs = _runs(self._pose, self.espelhar)
            g = self._grupos.get(id(runs))
            if g is None or forcar:
                g = _grupo(runs, self.ps)
                if len(self._grupos) > 120:
                    self._grupos.clear()
                self._grupos[id(runs)] = g
            if g is self._g:
                return
            i = self.canvas.indexof(self._g)
            self.canvas.remove(self._g)
            self.canvas.insert(i, g)
            self._g = g
        except Exception as e:
            print(f"[kirito] desenho ignorado: {e}")

    def precarregar(self, poses):
        """Gera o cache das poses aos poucos (sem travar o primeiro play)."""
        fila = list(poses)

        def _passo(dt):
            try:
                for _ in range(4):
                    if not fila:
                        return False
                    _runs(fila.pop(0), self.espelhar)
            except Exception as e:
                print(f"[kirito] precarregar: {e}")
                return False
        Clock.schedule_interval(_passo, 0)

    # ── reproducao ───────────────────────────────────────────────────
    def tocar(self, seq, on_fim=None, on_quadro=None, loop=False):
        self.parar()
        if not seq:
            if on_fim:
                on_fim()
            return
        self._seq, self._i = seq, 0
        self._on_fim, self._on_quadro, self._loop = on_fim, on_quadro, loop
        self._quadro(0)
        self._ev = Clock.schedule_interval(self._quadro, 1 / FPS)

    def _quadro(self, dt):
        try:
            if self._i >= len(self._seq):
                if self._loop:
                    self._i = 0
                else:
                    if self._ev is not None:
                        self._ev.cancel()
                        self._ev = None
                    cb, self._on_fim = self._on_fim, None
                    if cb:
                        cb()
                    return False
            self.mostrar(self._seq[self._i])
            if self._on_quadro:
                self._on_quadro(self._i)
            self._i += 1
        except Exception as e:
            print(f"[kirito] quadro ignorado: {e}")
            if self._ev is not None:
                self._ev.cancel()
                self._ev = None
            cb, self._on_fim = self._on_fim, None
            if cb:
                try:
                    cb()
                except Exception:
                    pass
            return False

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        self._on_fim = None
        self._on_quadro = None

    def on_parent(self, inst, parent):
        if parent is None:
            self.parar()

    def idle(self, base=None):
        """Respiracao, sobretudo balancando e piscar de olhos (loop)."""
        b = dict(base or POSE_A['guarda'])
        quadros = []
        for f in range(72):                          # 2,4 s
            t = f / 72.0 * 2 * math.pi
            q = dict(b)
            q['dy'] = b['dy'] - (1 if math.sin(t) < -0.3 else 0)
            q['capa'] = b['capa'] + 0.6 + 0.6 * math.sin(t * 2)
            q['cabelo'] = b['cabelo'] + 0.5 * math.sin(t * 2 + 1)
            q['olhos'] = 'f' if 50 <= f <= 52 else b['olhos']
            quadros.append(q)
        self.tocar(quadros, loop=True)

    # ── afterimage ───────────────────────────────────────────────────
    def fantasma(self, cor=(0.0, 0.85, 1.0), alfa=0.45, duracao=0.28):
        """Copia translucida da pose atual que some (rastro de velocidade)."""
        try:
            pai = self.parent
            if pai is None:
                return
            g = Widget(size_hint=(None, None), size=self.size, pos=self.pos)
            ax, ay = self.ancora_local()
            with g.canvas:
                PushMatrix()
                Translate(self.x, self.y)
                Rotate(angle=self.rotacao, origin=(ax, ay))
            sil = _grupo(_runs(self._pose, self.espelhar), self.ps,
                         silhueta=(cor[0], cor[1], cor[2], alfa))
            cor_sil = sil.children[0]                 # a unica Color do grupo
            g.canvas.add(sil)
            g.canvas.add(PopMatrix())
            idx = pai.children.index(self) + 1 if self in pai.children else 0
            pai.add_widget(g, index=idx)
            t = [0.0]

            def _some(dt):
                try:
                    t[0] += dt
                    k = min(1.0, t[0] / duracao)
                    cor_sil.a = alfa * (1 - k)
                    if k >= 1:
                        if g.parent:
                            g.parent.remove_widget(g)
                        return False
                except Exception:
                    try:
                        if g.parent:
                            g.parent.remove_widget(g)
                    except Exception:
                        pass
                    return False
            Clock.schedule_interval(_some, 1 / 60.)
        except Exception as e:
            print(f"[kirito] fantasma: {e}")


# ═══════════════════════════════════════════════════════════════════
#  POSES-CHAVE
# ═══════════════════════════════════════════════════════════════════
POSE_A = {
    # uma espada, em guarda
    'guarda':    pose(m1=(3, -5), a1=-40.0),
    # agarrado na parede (espadas nas costas), corpo encolhido
    'grudado':   pose(pernas='grudado', dy=-2, m1=(3, 3), a1=None, capa=1.0, cabelo=0.5),
    'agacha':    pose(pernas='agachado', dy=-3, m1=(2, 3), a1=None, capa=0.5),
    'pulo':      pose(pernas='pulo', dy=-1, m1=(4, 2), a1=None, capa=2.6, lift=1.6, cabelo=2.0),
    # saca a Elucidator das costas e golpeia
    'saca1':     pose(pernas='pulo', m1=(-2, 6), a1=110.0, c1=10, capa=2.4, lift=1.4, cabelo=1.8),
    'arma1':     pose(pernas='avanco', dx=-1, m1=(-4, 5), a1=150.0, capa=1.2, cabelo=0.8),
    'corta1':    pose(pernas='avanco', dx=2, dy=-1, m1=(7, -1), a1=-10.0, c1=15, capa=2.2, cabelo=1.6),
    'segue1':    pose(pernas='avanco', dx=2, dy=-1, m1=(5, -4), a1=-38.0, c1=15, capa=1.6, cabelo=1.2),
    # saca a Dark Repulser (mao de tras sobe ate o cabo nas costas)
    'pega2':     pose(pernas='avanco', dx=1, m1=(5, -4), a1=-38.0, m2=(-1, 6), a2=None, capa=1.0),
    'saca2':     pose(pernas='avanco', dx=1, m1=(5, -4), a1=-38.0, m2=(-3, 7), a2=100.0, c2=14, capa=1.2, cabelo=0.8),
    'dupla':     pose(pernas='avanco', m1=(4, -3), a1=-30.0, m2=(-3, -3), a2=210.0, capa=1.0),
    # combo com as duas
    'x_arma':    pose(pernas='avanco', dx=-1, m1=(-3, 6), a1=135.0, m2=(-5, 6), a2=160.0, capa=1.4, cabelo=1.0),
    'x_corta':   pose(pernas='avanco', dx=2, dy=-1, m1=(7, 0), a1=-20.0, m2=(6, -3), a2=-40.0, capa=2.4, cabelo=1.8),
    'giro_a':    pose(pernas='pulo', m1=(5, 4), a1=60.0, m2=(-6, -2), a2=230.0, capa=2.8, lift=1.5, cabelo=2.2),
    'giro_b':    pose(pernas='pulo', m1=(-5, -2), a1=240.0, m2=(5, 4), a2=50.0, capa=2.8, lift=1.5, cabelo=2.2),
    'final_arma': pose(pernas='agachado', dy=-2, m1=(-4, 7), a1=120.0, m2=(-6, 7), a2=140.0, capa=1.0),
    'final':     pose(pernas='avanco', dx=3, dy=-1, m1=(7, -2), a1=-25.0, m2=(7, -5), a2=-50.0, c1=16, c2=16, capa=2.8, cabelo=2.0),
    # pousa e guarda as espadas
    'pousa':     pose(pernas='agachado', dy=-3, m1=(5, -3), a1=-50.0, m2=(-4, -3), a2=230.0, capa=0.4),
    'guarda2':   pose(m1=(0, 6), a1=95.0, c1=8, m2=(-2, 7), a2=100.0, c2=8),
    'fim':       pose(m1=(3, -5), a1=None, m2=None, a2=None),
}


def smear(p, de):
    """Copia da pose com rastro da espada 1 vindo do angulo `de`."""
    q = dict(p)
    q['s1'] = de
    return q


# ═══════════════════════════════════════════════════════════════════
#  FAISCAS
# ═══════════════════════════════════════════════════════════════════
class Faiscas(Widget):
    """Pool de faiscas quadradas. estourar(x, y, cor, n)."""

    def __init__(self, n_max=60, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self._p = []
        self._ins = []
        with self.canvas:
            for _ in range(n_max):
                c = Color(1, 1, 1, 0)
                r = Rectangle(size=(0, 0))
                self._ins.append((c, r))
        self._livres = list(range(n_max))
        self._ev = None

    def estourar(self, x, y, cor=(0.4, 0.95, 1.0), n=14, forca=260.0, tam=4.0):
        for _ in range(n):
            if not self._livres:
                break
            i = self._livres.pop()
            a = random.uniform(0, 2 * math.pi)
            v = forca * random.uniform(0.35, 1.0)
            vida = random.uniform(0.25, 0.55)
            self._p.append([x, y, math.cos(a) * v, math.sin(a) * v, vida, vida,
                            tam * random.choice((1, 1, 1.5, 2)), i, cor])
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            vivas = []
            for f in self._p:
                f[4] -= dt
                c, r = self._ins[f[7]]
                if f[4] <= 0:
                    c.a = 0
                    r.size = (0, 0)
                    self._livres.append(f[7])
                    continue
                f[0] += f[2] * dt
                f[1] += f[3] * dt
                f[2] *= 0.90
                f[3] = f[3] * 0.90 - 420 * dt
                k = f[4] / f[5]
                s = max(1.0, f[6] * (0.5 + 0.5 * k))
                r.pos = (int(f[0] - s / 2), int(f[1] - s / 2))
                r.size = (s, s)
                cr = f[8]
                c.rgba = (cr[0] + (1 - cr[0]) * k, cr[1] + (1 - cr[1]) * k, cr[2] + (1 - cr[2]) * k, k)
                vivas.append(f)
            self._p = vivas
            if not vivas:
                self._ev = None
                return False
        except Exception as e:
            print(f"[faiscas] {e}")
            self._ev = None
            return False

    def on_parent(self, inst, parent):
        if parent is None and self._ev is not None:
            self._ev.cancel()
            self._ev = None
