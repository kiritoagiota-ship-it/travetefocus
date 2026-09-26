"""
kirito.py — TraveteFocus
Kirito em pixel art, montado por partes a partir de parametros de pose
(tronco, pernas, 2 bracos, 2 espadas, cabelo e sobretudo), com muitos
quadros interpolados por golpe.

  Elucidator    : espada preta (mao da frente)
  Dark Repulser : espada azulada/cristalina (mao de tras)

Fisica secundaria: o sobretudo e o cabelo reagem ao movimento real do
boneco (molas que passam do ponto e voltam) e ondulam continuamente; um
brilho percorre as laminas de tempos em tempos.

KiritoPixel(Widget) — poses/sequencias (cache por pose), idle, rotacao em
                      torno do quadril ou de um pivo (ex: mao pendurada),
                      afterimages.
Faiscas(Widget)     — faiscas quadradas (pixel) nos impactos.
"""
import math
import random
from collections import OrderedDict

from kivy.uix.widget import Widget
from kivy.graphics import (Color, Rectangle, PushMatrix, PopMatrix,
                           Translate, Rotate, Scale)
from kivy.graphics.texture import Texture
from kivy.properties import BooleanProperty, NumericProperty
from kivy.clock import Clock

FPS = 30.0

_PALETA = {
    'H': (0.13, 0.14, 0.22, 1), 'h': (0.36, 0.40, 0.62, 1),     # cabelo
    'S': (1.00, 0.86, 0.74, 1), 's': (0.86, 0.66, 0.56, 1),     # pele
    'E': (0.08, 0.10, 0.18, 1),                                  # olho
    'C': (0.15, 0.15, 0.21, 1), 'c': (0.30, 0.31, 0.42, 1),     # sobretudo
    'q': (0.21, 0.19, 0.30, 1),                                  # forro do sobretudo
    'G': (0.62, 0.66, 0.76, 1),                                  # detalhes cinza
    'P': (0.20, 0.20, 0.27, 1), 'B': (0.06, 0.06, 0.09, 1),     # calca / bota
    'M': (0.09, 0.09, 0.13, 1),                                  # luva
    # Elucidator (preta): lamina, fio claro, costas, cabo, guarda, pontas
    'W': (0.08, 0.08, 0.12, 1), 'w': (0.60, 0.64, 0.78, 1), 'u': (0.24, 0.24, 0.33, 1),
    'K': (0.20, 0.20, 0.27, 1), 'g': (0.34, 0.34, 0.44, 1), 'k': (0.66, 0.68, 0.80, 1),
    # Dark Repulser (cristal azul)
    'R': (0.40, 0.78, 1.00, 1), 'r': (0.88, 0.98, 1.00, 1), 'z': (0.22, 0.52, 0.86, 1),
    'y': (0.30, 0.62, 0.86, 1), 'Y': (0.82, 0.95, 1.00, 1),
    # brilho percorrendo a lamina
    '!': (1.00, 1.00, 1.00, 1), '1': (0.80, 0.96, 1.00, 0.85),
    # rastro de movimento da lamina (smear em pixel)
    'X': (0.85, 0.97, 1.00, 0.55), 'x': (0.50, 0.85, 1.00, 0.35),
    'O': (0.00, 0.78, 1.00, 0.85),                               # contorno (rim light)
}
_SEM_CONTORNO = set('xX!1')

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
_CABECA_PISCA = list(_CABECA)
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
    'pendente': ["....PP..PP...", "....PP..PP...", "....BB...BB.."],
}

GW, GH = 64, 58          # grade total (espadas cabem para qualquer lado)
_X0 = 25                 # coluna esquerda do tronco/cabeca
_PES = 14                # linha dos pes (sobra embaixo para espadas apontando p/ baixo)


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


def _espada(px, mx, my, ang, comp, tipo, smear_de=None, brilho=None):
    """tipo 1 = Elucidator (preta), 2 = Dark Repulser (cristal azul).
    Lamina de 3 px (fio claro / miolo / costas), guarda em cruz, pomo."""
    if tipo == 1:
        lam, fio, costas, guarda, ponta_g, centro_g, pomo = 'W', 'w', 'u', 'g', 'k', 'k', 'g'
    else:
        lam, fio, costas, guarda, ponta_g, centro_g, pomo = 'R', 'r', 'z', 'y', 'Y', 'r', 'Y'
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
    for k in (-3, -2, -1):                               # cabo + pomo
        px[(round(mx + ux * k), round(my + uy * k))] = 'K' if k > -3 else pomo
    for k in (-2, -1, 0, 1, 2):                          # guarda em cruz
        ch = ponta_g if abs(k) == 2 else (centro_g if k == 0 else guarda)
        px[(round(mx + ux + nx * k), round(my + uy + ny * k))] = ch
    for k in range(2, comp + 1):                         # lamina: fio / miolo / costas
        bx, by = mx + ux * k, my + uy * k
        px[(round(bx), round(by))] = lam
        px[(round(bx + nx), round(by + ny))] = fio
        if k < comp - 1:
            px[(round(bx - nx), round(by - ny))] = costas
    px[(round(mx + ux * (comp + 1)), round(my + uy * (comp + 1)))] = fio
    if brilho is not None and smear_de is None:          # brilho correndo na lamina
        k = 2 + int(brilho * (comp - 2))
        px[(round(mx + ux * k + nx), round(my + uy * k + ny))] = '!'
        px[(round(mx + ux * (k - 1) + nx), round(my + uy * (k - 1) + ny))] = '1'
        px[(round(mx + ux * k), round(my + uy * k))] = '1'


def _cabo_nas_costas(px, x, y, tipo):
    guarda, ponta = ('g', 'k') if tipo == 1 else ('y', 'Y')
    px[(x - 2, y)] = ponta
    px[(x - 1, y)] = guarda
    px[(x, y)] = guarda
    px[(x + 1, y)] = guarda
    px[(x + 2, y)] = ponta
    px[(x, y + 1)] = 'K'
    px[(x, y + 2)] = 'K'
    px[(x, y + 3)] = guarda if tipo == 1 else 'Y'


# pose padrao: todos os campos que a montagem entende
POSE_BASE = dict(dx=0, dy=0, pernas='repouso', olhos='a', cabelo=0.0, capa=0.0,
                 lift=0.0, fase=0.0, brilho=None,
                 m1=(3, -5), a1=-40.0, c1=15, s1=None,
                 m2=None, a2=None, c2=15, s2=None)


def montar(p):
    """Pose (dict) -> {(x, y): cor}."""
    px = {}
    dx, dy = int(p['dx']), int(p['dy'])
    pernas = _PERNAS[p['pernas']]
    topo_tronco = _PES + len(pernas) + len(_TRONCO) - 1 + dy
    base_x = _X0 + dx
    ombro1 = (base_x + 9, topo_tronco - 2)
    ombro2 = (base_x + 3, topo_tronco - 2)
    fase = p.get('fase', 0.0) or 0.0
    dois_pi = 2 * math.pi

    # braco/espada de tras (atras do corpo); sem pose = braco relaxado
    m2 = p['m2'] if p['m2'] is not None else (-1, -6)
    mx2, my2 = ombro2[0] + int(round(m2[0])), ombro2[1] + int(round(m2[1]))
    _linha(px, ombro2[0], ombro2[1], mx2, my2, 'C', grossura=2)
    if p['a2'] is not None:
        _espada(px, mx2, my2, p['a2'], int(p['c2']), 2, p['s2'], p.get('brilho'))
    px[(mx2, my2)] = 'M'
    if p['a2'] is None:
        _cabo_nas_costas(px, base_x + 1, topo_tronco + 1, 2)
    if p['a1'] is None:
        _cabo_nas_costas(px, base_x + 4, topo_tronco + 2, 1)

    # cabelo: mechas continuas que se alongam com o vento e ondulam
    topo_cab = topo_tronco + len(_CABECA)
    cb = p['cabelo']
    amp = 0.35 + 0.28 * min(3.0, abs(cb))
    for linha, base in ((2, 1), (3, 2), (4, 2), (5, 3), (6, 2), (7, 3), (8, 1)):
        comp = base + int(round(max(0.0, cb) * (0.5 + linha * 0.12)))
        caida = max(0.0, cb) * 0.25 * (linha - 4) / 4.0
        for i in range(comp):
            u = (i + 1) / float(comp)
            onda = amp * u * math.sin(dois_pi * (fase * 1.3 - i / 4.0 - linha * 0.1))
            y = topo_cab - linha - int(round((caida if i > comp // 2 else 0) + onda))
            px[(base_x - 1 - i, y)] = 'h' if (linha == 5 and i == comp - 1) else 'H'
    # fios espetados no topo que balancam
    for bx, fx in ((4, 0.0), (8, 0.35)):
        oscila = int(round(0.7 * math.sin(dois_pi * (fase + fx)) - min(1.0, max(0.0, cb) * 0.4)))
        px[(base_x + bx + oscila, topo_cab + 1)] = 'H'

    # sobretudo: aba de tras longa com forro + aba da frente (ondulam)
    capa, lift = p['capa'], p['lift']
    y_cint = topo_tronco - len(_TRONCO)
    amp_c = 0.55 + 0.35 * min(3.0, abs(capa))
    n_aba = 8
    for k in range(n_aba):
        u = k / float(n_aba - 1)
        onda = amp_c * u * math.sin(dois_pi * (fase - k / 7.0))
        y = y_cint - k + int(round(lift * k * 0.45))
        x_ini = base_x - int(round(capa * k * 0.55 + onda))
        x_fim = base_x + 4 - int(round(capa * k * 0.30 + onda * 0.6))
        if x_fim < x_ini:
            x_ini, x_fim = x_fim, x_ini
        for x in range(x_ini, x_fim + 1):
            if k == n_aba - 1 or x == x_ini:
                ch = 'c'                                  # barra / borda do sobretudo
            elif x == x_fim and k >= 2:
                ch = 'q'                                  # forro aparecendo
            else:
                ch = 'C'
            px[(x, y)] = ch
    for k in range(5):
        u = k / 4.0
        onda = 0.5 * amp_c * u * math.sin(dois_pi * (fase - k / 5.0 + 0.3))
        y = y_cint - k + int(round(lift * k * 0.3))
        x0 = base_x + 8 - int(round(capa * k * 0.15 + onda))
        x1 = base_x + 12 - int(round(capa * k * 0.10 + onda))
        for x in range(x0, x1):
            px[(x, y)] = 'q' if (x == x0 and k >= 2) else 'C'

    _estampar(px, pernas, _X0, _PES + len(pernas) - 1)
    _estampar(px, _TRONCO, base_x, topo_tronco)
    _estampar(px, _CABECA_PISCA if p['olhos'] == 'f' else _CABECA, base_x, topo_cab)

    # braco/espada da frente
    if p['m1'] is not None:
        mx, my = ombro1[0] + int(round(p['m1'][0])), ombro1[1] + int(round(p['m1'][1]))
        _linha(px, ombro1[0], ombro1[1], mx, my, 'C', grossura=2)
        if p['a1'] is not None:
            _espada(px, mx, my, p['a1'], int(p['c1']), 1, p['s1'], p.get('brilho'))
        px[(mx, my)] = 'M'
        px[(mx + 1, my)] = 'M'

    # contorno (rim light ciano) para ler no fundo escuro
    for (x, y) in list(px.keys()):
        if px[(x, y)] in _SEM_CONTORNO:
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
    def r(k, v):
        if k in ('capa', 'cabelo', 'lift'):
            return round(v * 4) / 4.0            # fisica: passos de 0.25
        if isinstance(v, float):
            return round(v, 1)
        if isinstance(v, tuple):
            return tuple(int(round(x)) for x in v)
        return v
    return tuple((k, r(k, p[k])) for k in sorted(p))


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
#  CACHE
# ═══════════════════════════════════════════════════════════════════
_CACHE = OrderedDict()     # chave_pose -> bytes RGBA (GW x GH)
_CACHE_MAX = 900
_TEX = OrderedDict()       # (chave_pose, silhueta) -> Texture
_TEX_MAX = 220
_RGBA = {c: bytes(int(round(v * 255)) for v in cor) for c, cor in _PALETA.items()}
_TC_NORMAL = (0, 0, 1, 0, 1, 1, 0, 1)
_TC_ESPELHO = (1, 0, 0, 0, 0, 1, 1, 1)


def _bytes(p):
    """Pose -> imagem RGBA (GW x GH) em bytes. Cache LRU; so Python puro
    (pode rodar antes do primeiro quadro, sem contexto grafico)."""
    ch = _chave(p)
    dados = _CACHE.get(ch)
    if dados is not None:
        _CACHE.move_to_end(ch)
        return ch, dados
    buf = bytearray(GW * GH * 4)
    for (x, y), c in montar(p).items():
        if 0 <= x < GW and 0 <= y < GH:
            i = (y * GW + x) * 4
            buf[i:i + 4] = _RGBA[c]
    dados = bytes(buf)
    _CACHE[ch] = dados
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)
    return ch, dados


def _runs(p, espelhar=False):
    """(compatibilidade) pre-gera a imagem da pose."""
    return _bytes(p)


def _textura(p, silhueta=False):
    """Pose -> Texture pequena (1 retangulo por quadro, em vez de ~250:
    bem mais leve no celular). O espelho e feito por tex_coords."""
    ch, dados = _bytes(p)
    chave = (ch, silhueta)
    tex = _TEX.get(chave)
    if tex is not None:
        _TEX.move_to_end(chave)
        return tex
    if silhueta:                         # branco com o alpha do boneco (tingido por Color)
        b = bytearray(dados)
        for i in range(0, len(b), 4):
            if b[i + 3]:
                b[i] = b[i + 1] = b[i + 2] = 255
        dados = bytes(b)
    tex = Texture.create(size=(GW, GH), colorfmt='rgba')
    tex.mag_filter = 'nearest'
    tex.min_filter = 'nearest'
    tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
    tex.add_reload_observer(
        lambda t, d=dados: t.blit_buffer(d, colorfmt='rgba', bufferfmt='ubyte'))
    _TEX[chave] = tex
    while len(_TEX) > _TEX_MAX:
        _TEX.popitem(last=False)
    return tex


# ═══════════════════════════════════════════════════════════════════
#  WIDGET
# ═══════════════════════════════════════════════════════════════════
class _Mola:
    """Mola amortecida (passa do ponto e volta): sobretudo/cabelo."""
    __slots__ = ('x', 'v', 'k', 'c')

    def __init__(self, k=90.0, c=9.0):
        self.x = 0.0
        self.v = 0.0
        self.k = k
        self.c = c

    def passo(self, alvo, dt):
        a = self.k * (alvo - self.x) - self.c * self.v
        self.v += a * dt
        self.x += self.v * dt
        return self.x


class KiritoPixel(Widget):
    """Tamanho em pixels de tela = (GW*ps, GH*ps). Posicione pela ancora
    (centro do quadril) com ancorar(x, y). `rotacao` gira em torno da ancora
    ou, se `pivo` for dado (coords locais), em torno dele."""
    espelhar = BooleanProperty(False)
    rotacao = NumericProperty(0.0)
    escala_y = NumericProperty(1.0)

    def __init__(self, ps=4, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self.ps = max(1, int(ps))
        self.size = (GW * self.ps, GH * self.ps)
        self.pivo = None
        self._base = pose()               # pose da sequencia (sem fisica)
        self._pose = self._base           # pose desenhada (com fisica)
        self._ult_chave = None
        self._ev = None
        self._ev_vida = None
        self._seq = []
        self._i = 0
        self._on_quadro = None
        self._on_fim = None
        self._loop = False
        # fisica secundaria
        self._m_capa = _Mola(95, 9)
        self._m_cab = _Mola(110, 10)
        self._m_lift = _Mola(80, 8)
        self._fase = random.random()
        self._t = 0.0
        self._ult = None
        self._vel = (0.0, 0.0)
        self.fisica = True
        with self.canvas:
            PushMatrix()
            self._tr = Translate(0, 0)
            self._rot = Rotate(angle=0, origin=(0, 0))
            self._sc = Scale(1, 1, 1)
            Color(1, 1, 1, 1)
            self._rect = Rectangle(pos=(0, 0), size=(GW * self.ps, GH * self.ps))
            PopMatrix()
        self.bind(pos=self._mover, x=self._mover, y=self._mover,
                  rotacao=self._mover, escala_y=self._mover,
                  espelhar=lambda *_: self._desenhar(forcar=True))
        self._mover()
        self._desenhar()

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

    def mao_local(self, qual=1, p=None):
        p = p or self._base
        pernas = _PERNAS[p['pernas']]
        topo_tronco = _PES + len(pernas) + len(_TRONCO) - 1 + int(p['dy'])
        base_x = _X0 + int(p['dx'])
        if qual == 1 and p['m1'] is not None:
            x, y = base_x + 9 + p['m1'][0], topo_tronco - 2 + p['m1'][1]
        elif qual == 2:
            m2 = p['m2'] if p['m2'] is not None else (-1, -6)
            x, y = base_x + 3 + m2[0], topo_tronco - 2 + m2[1]
        else:
            x, y = base_x + 6, topo_tronco - 4
        if self.espelhar:
            x = GW - 1 - x
        return (x + 0.5) * self.ps, (y + 0.5) * self.ps

    def ponto_mao(self, qual=1):
        """Posicao aproximada da mao (coords do pai), sem considerar rotacao."""
        lx, ly = self.mao_local(qual)
        return self.x + lx, self.y + ly

    def _mover(self, *_):
        self._tr.xy = (self.x, self.y)
        orig = self.pivo if self.pivo is not None else self.ancora_local()
        self._rot.origin = orig
        self._rot.angle = self.rotacao
        ax, ay = self.ancora_local()
        self._sc.origin = (ax, ay)
        self._sc.y = self.escala_y

    # ── desenho ──────────────────────────────────────────────────────
    def mostrar(self, p):
        self._base = p
        self._desenhar()

    def _composta(self):
        b = self._base
        if not self.fisica:
            return b
        q = dict(b)
        q['capa'] = b['capa'] + self._m_capa.x
        q['cabelo'] = b['cabelo'] + self._m_cab.x
        q['lift'] = b['lift'] + self._m_lift.x
        q['fase'] = (int(self._fase * 6) % 6) / 6.0
        # brilho percorre as laminas a cada ~2,6 s
        ciclo = self._t % 2.6
        q['brilho'] = (round(ciclo / 0.45 * 6) / 6.0) if ciclo < 0.45 else None
        return q

    def _desenhar(self, forcar=False):
        try:
            self._pose = self._composta()
            chave = (_chave(self._pose), self.espelhar)
            if chave == self._ult_chave and not forcar:
                return
            self._ult_chave = chave
            self._rect.texture = _textura(self._pose)
            self._rect.tex_coords = _TC_ESPELHO if self.espelhar else _TC_NORMAL
        except Exception as e:
            print(f"[kirito] desenho ignorado: {e}")

    def _vida(self, dt):
        """Fisica do sobretudo/cabelo a partir da velocidade real do boneco."""
        try:
            dt = min(dt, 1 / 15.)
            self._t += dt
            ax, ay = self.ancora()
            if self._ult is not None and dt > 0:
                vx = (ax - self._ult[0]) / dt
                vy = (ay - self._ult[1]) / dt
                self._vel = (self._vel[0] * 0.5 + vx * 0.5, self._vel[1] * 0.5 + vy * 0.5)
            self._ult = (ax, ay)
            vx, vy = self._vel
            # para o referencial do boneco (rotacao e espelho)
            r = math.radians(-self.rotacao)
            lx = vx * math.cos(r) - vy * math.sin(r)
            ly = vx * math.sin(r) + vy * math.cos(r)
            frente = lx * (-1 if self.espelhar else 1) / float(self.ps)
            cima = ly / float(self.ps)
            capa = max(-1.0, min(3.0, frente / 70.0))
            cab = max(-1.0, min(3.2, frente / 60.0))
            lift = max(-0.6, min(2.6, -cima / 90.0))
            self._m_capa.passo(capa, dt)
            self._m_cab.passo(cab, dt)
            self._m_lift.passo(lift, dt)
            vel = math.hypot(frente, cima)
            self._fase = (self._fase + dt * (1.6 + min(3.0, vel / 120.0))) % 1.0
            self._desenhar()
        except Exception as e:
            print(f"[kirito] fisica: {e}")

    def empurrar(self, capa=0.0, cabelo=0.0, lift=0.0):
        """Tranco nas molas (ex: impacto de um golpe, pouso)."""
        self._m_capa.v += capa
        self._m_cab.v += cabelo
        self._m_lift.v += lift

    def precarregar(self, poses):
        """Gera o cache das poses aos poucos (sem travar o primeiro play)."""
        fila = list(poses)

        def _passo(dt):
            try:
                for _ in range(3):
                    if not fila:
                        return False
                    _bytes(fila.pop(0))
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
            if self._ev_vida is not None:
                self._ev_vida.cancel()
                self._ev_vida = None
        elif self._ev_vida is None:
            self._ult = None
            self._ev_vida = Clock.schedule_interval(self._vida, 1 / FPS)

    def idle(self, base=None, piscar=True):
        """Respiracao e piscar (o vento no sobretudo/cabelo vem da fisica)."""
        b = dict(base or POSE_A['guarda'])
        quadros = []
        for f in range(84):                          # 2,8 s
            t = f / 84.0 * 2 * math.pi
            q = dict(b)
            q['dy'] = b['dy'] - (1 if math.sin(t) < -0.3 else 0)
            q['olhos'] = 'f' if (piscar and 58 <= f <= 60) else b['olhos']
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
            orig = self.pivo if self.pivo is not None else self.ancora_local()
            with g.canvas:
                PushMatrix()
                Translate(self.x, self.y)
                Rotate(angle=self.rotacao, origin=orig)
                cor_sil = Color(cor[0], cor[1], cor[2], alfa)
                Rectangle(pos=(0, 0), size=self.size, texture=_textura(self._pose, silhueta=True),
                          tex_coords=_TC_ESPELHO if self.espelhar else _TC_NORMAL)
                PopMatrix()
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
    'guarda':     pose(m1=(3, -5), a1=-40.0),
    'fim':        pose(m1=(3, -5), a1=None),
    # tela do PIN: espiando pela borda, as maos segurando a quina da tela
    'espreita':   pose(dx=1, m1=(4, 5), a1=None, m2=(3, 4)),
    'espreita2':  pose(dx=1, dy=-1, m1=(4, 4), a1=None, m2=(3, 3)),
    'susto':      pose(pernas='pulo', dx=-1, dy=1, m1=(3, 8), a1=None, m2=(-2, 7)),
    # agarrado na parede (espadas nas costas), corpo encolhido
    'grudado':    pose(pernas='grudado', dy=-2, m1=(3, 3), a1=None),
    # pendurado por uma mao, a outra no cabo da Elucidator (samurai pronto)
    'pendurado':  pose(pernas='pendente', m2=(-1, 17), a2=None, m1=(-3, 8), a1=None, lift=-0.4),
    'pendurado2': pose(pernas='pulo', dy=1, m2=(-1, 16), a2=None, m1=(-4, 9), a1=None, lift=-0.2),
    'agacha':     pose(pernas='agachado', dy=-3, m1=(2, 3), a1=None),
    'pulo':       pose(pernas='pulo', dy=-1, m1=(4, 2), a1=None),
    # saca a Elucidator das costas (iai) e golpe 1 (jodan -> diagonal)
    'saca1':      pose(pernas='pulo', m1=(-2, 7), a1=110.0, c1=10, m2=(4, 2)),
    'arma1':      pose(pernas='avanco', dx=-1, m1=(0, 9), a1=112.0, m2=(4, 1)),
    'corta1':     pose(pernas='avanco', dx=2, dy=-1, m1=(7, -2), a1=-38.0, m2=(-4, 2)),
    'segue1':     pose(pernas='avanco', dx=2, dy=-1, m1=(4, -6), a1=-70.0, m2=(-4, 1)),
    # saca a Dark Repulser (mao de tras sobe ate o cabo nas costas)
    'pega2':      pose(pernas='avanco', dx=1, m1=(5, -4), a1=-40.0, m2=(-1, 7), a2=None),
    'saca2':      pose(pernas='avanco', dx=1, m1=(5, -4), a1=-40.0, m2=(-3, 8), a2=100.0, c2=14),
    'dupla':      pose(pernas='avanco', dy=-1, m1=(6, 3), a1=40.0, m2=(-5, -1), a2=205.0),
    # combo samurai com as duas
    'c2_arma':    pose(pernas='avanco', dx=-1, m1=(-1, 9), a1=120.0, m2=(-4, -2), a2=200.0),
    'c2_corta':   pose(pernas='avanco', dx=2, dy=-1, m1=(7, -2), a1=-45.0, m2=(-5, -3), a2=215.0),
    'c3_arma':    pose(pernas='avanco', m1=(5, -4), a1=-60.0, m2=(-5, -4), a2=225.0),
    'c3_corta':   pose(pernas='avanco', dx=2, m1=(-3, 3), a1=160.0, m2=(5, 8), a2=75.0),
    'giro_a':     pose(pernas='pulo', m1=(5, 4), a1=60.0, m2=(-6, -2), a2=230.0),
    'giro_b':     pose(pernas='pulo', m1=(-5, -2), a1=240.0, m2=(5, 4), a2=50.0),
    # golpe final (iai): carga, corte atravessando, chiburi, embainhar
    'iai_carga':  pose(pernas='agachado', dx=-1, dy=-3, m1=(-3, -1), a1=192.0, m2=(-5, -2), a2=202.0),
    'iai_corte':  pose(pernas='avanco', dx=3, dy=-2, m1=(8, 0), a1=-5.0, c1=17, m2=(7, -4), a2=-28.0, c2=17),
    'iai_fim':    pose(pernas='avanco', dx=3, dy=-3, m1=(8, -1), a1=-12.0, c1=17, m2=(7, -5), a2=-35.0, c2=17),
    'chiburi':    pose(pernas='avanco', dx=2, dy=-2, m1=(6, 3), a1=30.0, m2=(5, -1), a2=10.0),
    'embainha':   pose(pernas='repouso', m1=(0, 9), a1=95.0, c1=9, m2=(-2, 9), a2=100.0, c2=9),
    'guardado':   pose(pernas='repouso', m1=(3, -5), a1=None, m2=None, a2=None),
    # compatibilidade com cenas antigas
    'x_arma':     pose(pernas='avanco', dx=-1, m1=(-3, 6), a1=135.0, m2=(-5, 6), a2=160.0),
    'x_corta':    pose(pernas='avanco', dx=2, dy=-1, m1=(7, 0), a1=-20.0, m2=(6, -3), a2=-40.0),
    'final_arma': pose(pernas='agachado', dy=-2, m1=(-4, 7), a1=120.0, m2=(-6, 7), a2=140.0),
    'final':      pose(pernas='avanco', dx=3, dy=-1, m1=(7, -2), a1=-25.0, m2=(7, -5), a2=-50.0, c1=16, c2=16),
    'pousa':      pose(pernas='agachado', dy=-3, m1=(5, -3), a1=-50.0, m2=(-4, -3), a2=230.0),
    'guarda2':    pose(m1=(0, 6), a1=95.0, c1=8, m2=(-2, 7), a2=100.0, c2=8),
}


def smear(p, de=None, de2=None):
    """Copia da pose com rastro da espada 1 (e/ou 2) vindo dos angulos dados."""
    q = dict(p)
    q['s1'] = de
    q['s2'] = de2
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

    def estourar(self, x, y, cor=(0.4, 0.95, 1.0), n=14, forca=260.0, tam=4.0, gravidade=420.0):
        for _ in range(n):
            if not self._livres:
                break
            i = self._livres.pop()
            a = random.uniform(0, 2 * math.pi)
            v = forca * random.uniform(0.35, 1.0)
            vida = random.uniform(0.25, 0.55)
            self._p.append([x, y, math.cos(a) * v, math.sin(a) * v, vida, vida,
                            tam * random.choice((1, 1, 1.5, 2)), i, cor, gravidade])
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
                f[3] = f[3] * 0.90 - f[9] * dt
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
