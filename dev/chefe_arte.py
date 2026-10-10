"""O CHEFE da abertura (o vilao do Yoru): "THE ABYSS WARDEN", um cavaleiro-
demonio de armadura de obsidiana com fendas em brasa, chifres, capa rasgada
e um montante enorme. Pixel art DESENHADA AQUI (nao tem referencia): cada
peca e uma forma (poligonos e curvas) pintada em faixas de cor - rampa
curta, luz de cima/esquerda, borda escura, filete claro do lado da luz - e
depois recebe os detalhes (quinas, frisos, rebites, riscos, fendas acesas,
dobras do pano).

As pecas saem separadas (capa, braco de tras, pernas, saiote, tabardo,
tronco, cabeca, ombreiras, braco, antebraco, espada) para o chefe_rig.py
animar peca por peca, como o Bankai.

uso: python dev/chefe_arte.py previa SAIDA.png [zoom]   (o chefe montado, parado)
     python dev/chefe_arte.py pecas  SAIDA.png          (cada peca separada)"""
import os
import sys
import math
import numpy as np
from PIL import Image, ImageDraw

CW, CH = 640, 600                # tela de trabalho (os golpes precisam de espaco)
OX, OY = 170, 230                # onde o desenho (340x320) fica dentro dela
CHAO = 318                       # y do chao no desenho

# ── paleta (indice 0 = vazio) ────────────────────────────────────────
PAL = [(0, 0, 0, 0)]


def _cor(*rgb):
    PAL.append((rgb[0], rgb[1], rgb[2], 255))
    return len(PAL) - 1


LINHA = _cor(8, 6, 14)                                     # contorno
# armadura de obsidiana (fria, puxando para o roxo)
A0, A1, A2, A3, A4, A5 = (_cor(*c) for c in ((17, 15, 26), (28, 25, 42), (43, 38, 62), (66, 58, 92),
                                             (102, 92, 134), (170, 160, 202)))
# metal dos frisos (bronze velho)
B0, B1, B2, B3 = (_cor(*c) for c in ((52, 30, 24), (98, 58, 34), (156, 100, 50), (226, 176, 100)))
# pano (vinho)
C0, C1, C2, C3, C4 = (_cor(*c) for c in ((24, 5, 12), (46, 8, 18), (74, 12, 24), (112, 20, 32), (164, 40, 42)))
# osso (chifres, garras, dentes)
O0, O1, O2, O3 = (_cor(*c) for c in ((50, 40, 46), (106, 92, 90), (176, 162, 144), (236, 226, 202)))
# brasa (olhos, nucleo, fendas, fio da lamina)
G0, G1, G2, G3, G4 = (_cor(*c) for c in ((92, 14, 14), (172, 34, 18), (240, 96, 28), (255, 176, 64), (255, 240, 184)))
# luz de fundo na borda de fora (como o aro roxo do Bankai, aqui em brasa)
ARO = _cor(146, 30, 24)
FECHO = _cor(12, 9, 18)
# rastro do golpe
R0, R1, R2 = _cor(120, 22, 20), _cor(232, 84, 30), _cor(255, 226, 170)

RAMPA_A = [A0, A1, A2, A3, A4, A5]
RAMPA_AE = [A0, A0, A1, A2, A3, A4]          # armadura do lado de tras (mais escura)
RAMPA_B = [B0, B1, B2, B3]
RAMPA_C = [C0, C1, C2, C3, C4]
RAMPA_O = [O0, O1, O2, O3]
RAMPA_OE = [O0, O0, O1, O2]
LUZ = (-0.55, -0.83)             # de onde vem a luz (cima/esquerda), y para baixo
_LIM5 = [0.14, 0.40, 0.60, 0.78, 0.93]

_ys, _xs = np.mgrid[0:CH, 0:CW]
XS = _xs.astype(float)
YS = _ys.astype(float)


def P(x, y):
    """ponto do desenho -> tela"""
    return (x + OX, y + OY)


# ═════════════════════════════════════════════════════════════════════
#  FORMAS
# ═════════════════════════════════════════════════════════════════════
def curva(pts, fechada=True, passo=1.0):
    """Curva suave (Catmull-Rom) pelos pontos."""
    pts = [np.array(p, float) for p in pts]
    n = len(pts)
    out = []
    faixa = range(n) if fechada else range(n - 1)
    for i in faixa:
        p0 = pts[(i - 1) % n] if fechada or i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if fechada or i + 2 < n else pts[min(i + 1, n - 1)]
        m = max(2, int(np.hypot(*(p2 - p1)) / passo))
        for k in range(m):
            t = k / float(m)
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not fechada:
        out.append(pts[-1])
    return [(float(p[0]), float(p[1])) for p in out]


def poli(pts, suave=False):
    """Mascara (bool) de um poligono (pontos do desenho)."""
    if suave:
        pts = curva(pts)
    im = Image.new('1', (CW, CH), 0)
    ImageDraw.Draw(im).polygon([P(x, y) for x, y in pts], fill=1)
    return np.array(im, bool)


def risco(pts, larg=1, suave=False):
    """Mascara de uma linha."""
    if suave:
        pts = curva(pts, fechada=False)
    im = Image.new('1', (CW, CH), 0)
    ImageDraw.Draw(im).line([P(x, y) for x, y in pts], fill=1, width=larg)
    return np.array(im, bool)


def elipse(cx, cy, rx, ry, ang=0.0):
    cx, cy = P(cx, cy)
    a = math.radians(ang)
    dx, dy = XS - cx, YS - cy
    u = dx * math.cos(a) + dy * math.sin(a)
    v = -dx * math.sin(a) + dy * math.cos(a)
    return (u / rx) ** 2 + (v / ry) ** 2 <= 1.0


def tubo(pts, raios):
    """Membro: bolas ao longo da espinha, com o raio mudando (afina)."""
    esp = curva(pts, fechada=False, passo=1.0)
    n = len(esp)
    m = np.zeros((CH, CW), bool)
    rs = np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(raios)), raios)
    for (x, y), r in zip(esp, rs):
        x, y = P(x, y)
        x0, x1 = int(max(0, x - r - 1)), int(min(CW, x + r + 2))
        y0, y1 = int(max(0, y - r - 1)), int(min(CH, y + r + 2))
        m[y0:y1, x0:x1] |= (XS[y0:y1, x0:x1] - x) ** 2 + (YS[y0:y1, x0:x1] - y) ** 2 <= r * r
    return m


def dilata(m, n=1):
    out = m.copy()
    for _ in range(n):
        v = out.copy()
        v[1:, :] |= out[:-1, :]
        v[:-1, :] |= out[1:, :]
        v[:, 1:] |= out[:, :-1]
        v[:, :-1] |= out[:, 1:]
        out = v
    return out


def erode(m, n=1):
    return ~dilata(~m, n)


def fundura(m, maximo=40):
    """Quantos pixels cada ponto esta para dentro da forma (1 na borda)."""
    d = np.zeros(m.shape, np.int32)
    cur = m.copy()
    k = 0
    while cur.any() and k < maximo:
        k += 1
        d[cur] = k
        cur = erode(cur, 1)
    return d


def borra(a, n):
    """Media em cruz repetida n vezes."""
    a = a.astype(float)
    for _ in range(n):
        a = (a + np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1)) / 5.0
    return a


def ruido(semente, escala):
    """Ruido de valor liso (0..1) na tela."""
    rnd = np.random.default_rng(semente)
    gw, gh = int(CW / escala) + 3, int(CH / escala) + 3
    g = rnd.random((gh, gw))
    gx, gy = XS / escala, YS / escala
    x0, y0 = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - x0, gy - y0
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
    b = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def ligado(m, semente):
    """So a parte de `m` ligada a `semente` (tira ilhas soltas)."""
    cur = m & semente
    while True:
        nv = dilata(cur, 1) & m
        if (nv == cur).all():
            return cur
        cur = nv


def lado_de(p0, p1):
    """Mascara do lado ESQUERDO da reta p0 -> p1 (andando de p0 para p1)."""
    x0, y0 = P(*p0)
    x1, y1 = P(*p1)
    return (x1 - x0) * (YS - y0) - (y1 - y0) * (XS - x0) < 0


def zigue(p0, p1, n, amp, semente):
    """Pontos em zigue-zague de p0 a p1."""
    rnd = np.random.default_rng(semente)
    p0, p1 = np.array(p0, float), np.array(p1, float)
    v = p1 - p0
    L = np.hypot(*v)
    nrm = np.array([-v[1], v[0]]) / max(1e-6, L)
    pts = [tuple(p0)]
    for i in range(1, n):
        t = i / float(n)
        pts.append(tuple(p0 + v * t + nrm * rnd.uniform(-amp, amp)))
    pts.append(tuple(p1))
    return pts


_TEX = {}


def tex(nome):
    if not _TEX:
        _TEX['metal'] = 0.55 * ruido(11, 8.0) + 0.45 * ruido(12, 3.5)
        _TEX['pano'] = 0.5 * ruido(21, 14.0) + 0.5 * ruido(22, 5.0)
    return _TEX[nome]


# ═════════════════════════════════════════════════════════════════════
#  PINTURA
# ═════════════════════════════════════════════════════════════════════
class Peca:
    """Uma peca: imagem (indices da paleta) do tamanho da tela + pontos."""

    def __init__(self, nome):
        self.nome = nome
        self.img = np.zeros((CH, CW), np.uint8)
        self.pts = {}

    @property
    def masc(self):
        return self.img > 0

    def volume(self, m, rampa, bojo=6, chapa=0, luz=LUZ, base=0.0, contraste=1.0, textura='metal',
               forca_tex=0.16, queda=0.2):
        """Pinta a forma `m` com volume: a forma e 'inflada' (bojo = quantos
        pixels de borda arredondada; chapa > 0 = placa chata com chanfro) e
        iluminada de `luz`; escurece para baixo (queda) e o resultado cai nas
        faixas da `rampa`."""
        if not m.any():
            return
        d = fundura(m, max(bojo, chapa) + 2).astype(float)
        if chapa:
            alt = np.minimum(d, chapa) / float(chapa)
        else:
            alt = np.sqrt(np.clip(1 - (1 - np.minimum(d, bojo) / float(bojo)) ** 2, 0, 1))
        alt = borra(np.where(m, alt, 0.0), 2) * (bojo if not chapa else chapa) * 0.9
        gy, gx = np.gradient(alt)
        norma = np.sqrt(gx * gx + gy * gy + 1.0)
        lz = 0.5
        ln = math.sqrt(luz[0] ** 2 + luz[1] ** 2 + lz * lz)
        lamb = (-gx / norma * luz[0] - gy / norma * luz[1] + lz / norma) / ln
        ys = np.nonzero(m.any(axis=1))[0]
        fy = (YS - ys.min()) / max(1.0, float(ys.max() - ys.min()))
        v = base + contraste * lamb - queda * (fy - 0.4)
        if textura:
            v = v + (tex(textura) - 0.5) * forca_tex
        n = len(rampa)
        lim = np.interp(np.linspace(0, 1, n - 1), np.linspace(0, 1, 5), _LIM5)
        faixa = np.zeros(m.shape, int)
        for t in lim:
            faixa += (v > t)
        cor = np.array(rampa, np.uint8)[np.clip(faixa, 0, n - 1)]
        self.img[m] = cor[m]

    def tom(self, m, rampa, delta):
        """Clareia (+) ou escurece (-) `delta` degraus da rampa dentro de m."""
        r = np.array(rampa)
        pos = np.full(256, -1)
        for i, c in enumerate(rampa):
            if pos[c] < 0 or delta > 0:
                pos[c] = i
        p = pos[self.img]
        ok = m & (p >= 0)
        self.img[ok] = r[np.clip(p[ok] + delta, 0, len(rampa) - 1)]

    def quina(self, m, p0, p1, rampa, d=1):
        """Quina (vinco) na placa: um lado da reta fica mais claro e o outro
        mais escuro; a propria quina ganha um filete claro."""
        esq = lado_de(p0, p1)
        self.tom(m & esq, rampa, d)
        self.tom(m & ~esq, rampa, -d)
        lin = risco([p0, p1]) & m
        self.tom(lin, rampa, 2)

    def chapado(self, m, cor):
        self.img[m] = cor

    def contorno(self, m, cor=LINHA, filete=None, luz=LUZ):
        """Borda escura por dentro da forma e, do lado da luz, um filete
        claro logo depois dela."""
        borda = m & ~erode(m, 1)
        if filete is not None:
            dentro2 = erode(m, 1) & ~erode(m, 2)
            dx = 1 if luz[0] < 0 else -1
            dy = 1 if luz[1] < 0 else -1
            fora_x = ~np.roll(m, dx, axis=1)
            fora_y = ~np.roll(m, dy, axis=0)
            lado = np.roll(fora_x, dx, axis=1) | np.roll(fora_y, dy, axis=0)
            self.img[dentro2 & lado] = filete
        self.img[borda] = cor

    def placa(self, pts, rampa=None, chapa=3, bojo=0, base=0.0, filete=None, suave=False, queda=0.2, tx=0.16):
        """Uma placa de armadura completa: forma, volume, borda e filete."""
        rampa = rampa or RAMPA_A
        m = poli(pts, suave)
        if bojo:
            self.volume(m, rampa, bojo=bojo, base=base, queda=queda, forca_tex=tx)
        else:
            self.volume(m, rampa, chapa=chapa, base=base, queda=queda, forca_tex=tx)
        self.contorno(m, LINHA, filete=filete if filete is not None else rampa[-1])
        return m

    def linha(self, pts, cor, larg=1, suave=False, so=None):
        m = risco(pts, larg, suave) & self.masc
        if so is not None:
            m &= so
        self.img[m] = cor
        return m

    def friso(self, pts, suave=False, so=None, claro=B2, escuro=B0, brilho=B3):
        """Friso de bronze: linha clara com sombra embaixo e pontos de brilho."""
        self.linha([(x, y + 1) for x, y in pts], escuro, suave=suave, so=so)
        m = self.linha(pts, claro, suave=suave, so=so)
        ys, xs = np.nonzero(m)
        for k in range(0, len(xs), 7):
            self.img[ys[k], xs[k]] = brilho

    def ponto(self, x, y, cor, so_dentro=True):
        x, y = P(x, y)
        x, y = int(round(x)), int(round(y))
        if 0 <= x < CW and 0 <= y < CH and (not so_dentro or self.img[y, x] > 0):
            self.img[y, x] = cor

    def rebite(self, x, y, claro=A5, meio=A3):
        self.ponto(x, y, claro)
        self.ponto(x + 1, y, meio)
        self.ponto(x, y + 1, meio)
        self.ponto(x + 1, y + 1, LINHA)

    def riscos(self, m, n, semente, rampa=None):
        """Arranhoes de batalha: risquinhos claros com sombra."""
        rampa = rampa or RAMPA_A
        rnd = np.random.default_rng(semente)
        ys, xs = np.nonzero(erode(m, 3))
        if len(xs) == 0:
            return
        for _ in range(n):
            k = rnd.integers(0, len(xs))
            x, y = xs[k] - OX, ys[k] - OY
            L = rnd.integers(3, 8)
            a = rnd.uniform(-1.0, -0.4)
            p1 = (x + L * math.cos(a), y + L * math.sin(a))
            self.linha([(x, y + 1), (p1[0], p1[1] + 1)], rampa[0], so=m)
            self.linha([(x, y), p1], rampa[min(len(rampa) - 1, 4)], so=m)

    def brasa(self, m, nucleo=None, so=None):
        """Coisa acesa: borda vermelha escura, corpo laranja, miolo claro."""
        if so is not None:
            m = m & so
        halo = dilata(m, 1) & self.masc & ~m
        self.img[halo] = G0
        self.img[m] = G2
        d = fundura(m, 6)
        self.img[m & (d >= 2)] = G3
        if nucleo is None:
            nucleo = m & (d >= 3)
        self.img[nucleo & m] = G4

    def fenda(self, pts, clara=True, so=None, ramos=0, semente=1):
        """Fenda de lava na armadura: risco em zigue-zague aceso, com
        raminhos mais fracos."""
        m = risco(pts) & self.masc
        if so is not None:
            m &= so
        halo = dilata(m, 1) & self.masc & ~m
        if so is not None:
            halo &= so
        self.img[halo & np.isin(self.img, RAMPA_A + [LINHA])] = G0
        self.img[m] = G3 if clara else G2
        rnd = np.random.default_rng(semente)
        for _ in range(ramos):
            k = rnd.integers(1, len(pts) - 1)
            a = rnd.uniform(0, 2 * math.pi)
            L = rnd.uniform(3, 7)
            p = pts[k]
            rm = risco([p, (p[0] + L * math.cos(a), p[1] + L * math.sin(a))]) & self.masc & ~m
            if so is not None:
                rm &= so
            self.img[rm] = G1
        return m


def _pano(pc, m, origem, k, semente, rampa=RAMPA_C, sombra=60.0):
    """Pano com dobras compridas que descem em leque a partir de `origem`:
    vincos finos e escuros, faixas largas no tom do meio e filetes de luz."""
    ox, oy = P(*origem)
    ang = np.arctan2(YS - oy, XS - ox)
    r = np.hypot(XS - ox, YS - oy)
    rz = ruido(semente, 30.0)
    v = np.sin(ang * k + 1.1 * rz + r * 0.012)
    v2 = np.sin(ang * k * 2.6 + 2.4 * ruido(semente + 1, 18.0) + 1.3)
    v = 0.72 * v + 0.28 * v2
    faixa = np.digitize(v, [-0.74, -0.25, 0.42, 0.86])
    perto = np.clip(1.0 - r / sombra, 0, 1)              # sombra do corpo em cima
    faixa = np.clip(faixa - (perto > 0.3).astype(int) - (perto > 0.65).astype(int), 0, len(rampa) - 1)
    cor = np.array(rampa, np.uint8)[faixa]
    pc.img[m] = cor[m]


# ═════════════════════════════════════════════════════════════════════
#  O CHEFE (olhando para a ESQUERDA; pontos do desenho, y para baixo)
# ═════════════════════════════════════════════════════════════════════
QUADRIL = (184.0, 198.0)
PEITO = (170.0, 140.0)
PESCOCO = (156.0, 104.0)
CABECA = (140.0, 84.0)
OMBRO = (226.0, 110.0)            # braco da FRENTE (garra aberta)
COTOVELO = (252.0, 158.0)
MAO = (246.0, 206.0)
OMBRO_T = (118.0, 116.0)          # braco de TRAS: a mao segura o montante cravado no chao
COTOVELO_T = (100.0, 146.0)
MAO_T = (80.0, 138.0)
PONTA = (62.0, 318.0)             # ponta da lamina (no chao, na frente dele)
NUCLEO = (165.0, 141.0)
OLHO = (127.0, 89.0)


def _u_lamina():
    v = np.array(PONTA) - np.array(MAO_T)
    L = float(np.hypot(*v))
    u = v / L
    return u, np.array([-u[1], u[0]]), L


def capa():
    pc = Peca('capa')
    borda = [(138, 104), (232, 96), (262, 122), (288, 164), (306, 214), (316, 262), (320, 300), (312, 318),
             (304, 296), (294, 318), (284, 290), (272, 316), (262, 286), (250, 312), (240, 282), (228, 306),
             (218, 280), (206, 302), (196, 278), (186, 298), (176, 276), (166, 294), (156, 274), (150, 230),
             (146, 180)]
    m = poli(borda)
    # barra rasgada: lascas e furos (mais para o fim do pano)
    rz = 0.6 * ruido(31, 6.0) + 0.4 * ruido(32, 3.0)
    barra = (YS > OY + 276) & (rz > 0.5 + (OY + 318 - YS) / 120.0)
    m &= ~barra
    m = dilata(erode(m, 1), 1) | (m & (YS < OY + 284))
    m = ligado(m, YS < OY + 240)
    _pano(pc, m, (196, 92), 11.0, 41, sombra=70.0)
    pc.contorno(m, C0)
    # a beirada de fora pega a luz da brasa
    beira = m & ~erode(m, 2) & (XS > OX + 250) & (YS < OY + 300)
    pc.tom(beira & ~(m & ~erode(m, 1)), RAMPA_C, 1)
    pc.pts['raiz'] = (196, 100)
    return pc


def _perna(pc, q, j, t, pe, larg, rampa, fil, espelho=1, b0=0.0):
    """Perna de armadura: coxa em placas, joelheira com espinho, greva com
    quina no meio e sabato pontudo. q, j, t = quadril, joelho, tornozelo."""
    w = larg
    # coxa (placa de cima + placa de baixo que entra por baixo dela)
    coxa2 = pc.placa([(j[0] - w * 0.78, j[1] - 22), (j[0] + w * 0.78, j[1] - 22), (j[0] + w * 0.66, j[1] - 2),
                      (j[0] - w * 0.66, j[1] - 2)], rampa, chapa=3, base=b0 - 0.08, filete=fil)
    coxa = pc.placa([(q[0] - w, q[1] - 2), (q[0] + w, q[1] - 2), (j[0] + w * 0.84, j[1] - 16),
                     (j[0] + w * 0.3, j[1] - 8), (j[0] - w * 0.84, j[1] - 14)], rampa, chapa=4, base=b0, filete=fil)
    pc.quina(erode(coxa, 2), ((q[0] + j[0]) / 2.0 - w * 0.25, q[1]), (j[0] - w * 0.1, j[1] - 12), rampa)
    pc.friso([(j[0] - w * 0.8, j[1] - 16), (j[0] + w * 0.3, j[1] - 10), (j[0] + w * 0.82, j[1] - 18)], so=coxa)
    pc.riscos(coxa, 3, int(q[0]), rampa)
    # greva com quina
    gr = pc.placa([(j[0] - w * 0.6, j[1] + 4), (j[0] + w * 0.62, j[1] + 4), (t[0] + w * 0.56, t[1] - 6),
                   (t[0] + w * 0.4, t[1] + 2), (t[0] - w * 0.44, t[1] + 2), (t[0] - w * 0.56, t[1] - 6)],
                  rampa, chapa=3, base=b0 + 0.04, filete=fil)
    pc.quina(erode(gr, 2), (j[0] - 2 * espelho, j[1] + 4), (t[0] - 3 * espelho, t[1] + 2), rampa)
    pc.linha([(j[0] - w * 0.56, j[1] + 22), (j[0] + w * 0.58, j[1] + 20)], LINHA, so=gr)
    pc.linha([(j[0] - w * 0.54, j[1] + 23), (j[0] + w * 0.56, j[1] + 21)], rampa[3], so=gr)
    # sabato: 3 placas e ponta
    dx = pe[0] - t[0]
    sab = pc.placa([(t[0] - w * 0.5, t[1] - 4), (t[0] + w * 0.56, t[1] - 4), (t[0] + w * 0.8, CHAO),
                    (pe[0] - 6, CHAO), (pe[0], CHAO - 5), (t[0] + dx * 0.55, CHAO - 12),
                    (t[0] + dx * 0.2, CHAO - 15)], rampa, chapa=3, base=b0 + 0.06, filete=fil)
    for f in (0.3, 0.55, 0.78):
        pc.linha([(t[0] + dx * f, CHAO - 14), (t[0] + dx * (f + 0.06), CHAO - 1)], LINHA, so=sab)
        pc.linha([(t[0] + dx * f - 1, CHAO - 13), (t[0] + dx * (f + 0.06) - 1, CHAO - 2)], rampa[3], so=sab)
    pc.linha([(t[0] + w * 0.8, CHAO - 1), (pe[0], CHAO - 1)], LINHA)
    # joelheira com espinho para a frente
    esp = poli([(j[0] - w * 0.5, j[1] - 9), (j[0] - w * 1.5, j[1] - 14), (j[0] - w * 0.55, j[1] + 3)])
    pc.volume(esp, rampa, bojo=3, base=0.12)
    pc.contorno(esp, LINHA, filete=fil)
    jo = pc.placa([(j[0] - w * 0.72, j[1] - 10), (j[0] + w * 0.4, j[1] - 12), (j[0] + w * 0.78, j[1] - 2),
                   (j[0] + w * 0.6, j[1] + 9), (j[0] - w * 0.2, j[1] + 13), (j[0] - w * 0.74, j[1] + 6)],
                  rampa, bojo=6, base=0.1, filete=fil)
    pc.rebite(j[0], j[1] - 1, rampa[-1], rampa[3])
    return jo


def perna_tras():
    pc = Peca('perna_tras')
    _perna(pc, (164, 206), (146, 258), (138, 302), (100, 318), 17, RAMPA_AE, A3, b0=0.1)
    return pc


def perna_frente():
    pc = Peca('perna_frente')
    _perna(pc, (202, 206), (208, 258), (210, 302), (166, 318), 20, RAMPA_A, A5, b0=0.12)
    pc.fenda(zigue((196, 214), (214, 240), 5, 3.0, 5), ramos=2, semente=4)
    pc.fenda(zigue((204, 272), (214, 294), 4, 2.5, 6), clara=False)
    return pc


def saiote():
    """cinto + placas dos lados do quadril"""
    pc = Peca('saiote')
    lt = pc.placa([(140, 206), (166, 206), (164, 240), (148, 250), (132, 238)], RAMPA_AE, chapa=3, filete=A3)
    pc.friso([(134, 237), (148, 247), (163, 239)], so=lt, claro=B1, brilho=B2)
    ld = pc.placa([(200, 204), (232, 202), (240, 240), (222, 256), (202, 244)], RAMPA_A, chapa=3, filete=A5)
    pc.friso([(203, 242), (222, 253), (239, 238)], so=ld)
    pc.quina(erode(ld, 2), (216, 204), (222, 254), RAMPA_A)
    pc.rebite(208, 214)
    pc.rebite(228, 214)
    pc.riscos(ld, 3, 8)
    # cinto com fivela (caveira)
    cinto = pc.placa([(146, 194), (222, 192), (226, 208), (144, 210)], RAMPA_B, chapa=2, base=0.05, filete=B3)
    for x in range(152, 222, 9):
        pc.linha([(x, 196), (x - 1, 207)], B0, so=cinto)
    cav = elipse(184, 200, 12, 10) | poli([(176, 206), (192, 206), (190, 217), (178, 217)])
    pc.volume(cav, RAMPA_O, bojo=6, base=0.3, textura=None, queda=0.1)
    pc.contorno(cav, LINHA)
    pc.chapado(elipse(179.5, 200, 3.2, 3.4), LINHA)
    pc.chapado(elipse(188.5, 200, 3.2, 3.4), LINHA)
    pc.ponto(179, 200, G3)
    pc.ponto(180, 200, G2)
    pc.ponto(188, 200, G3)
    pc.ponto(189, 200, G2)
    pc.linha([(184, 204), (183, 207)], LINHA)
    pc.linha([(185, 204), (185, 207)], LINHA)
    for x in (180, 184, 188):
        pc.linha([(x, 211), (x, 216)], LINHA)
    return pc


def tabardo():
    """pano vinho que desce do cinto entre as pernas, com barra dourada"""
    pc = Peca('tabardo')
    m = poli([(164, 208), (204, 208), (208, 248), (204, 284), (196, 272), (188, 292), (180, 274), (172, 288),
              (164, 270), (160, 246)])
    _pano(pc, m, (184, 170), 13.0, 71, sombra=52.0)
    pc.contorno(m, C0)
    barra = m & ~erode(m, 4) & (YS > OY + 262)
    pc.chapado(barra & ~(m & ~erode(m, 1)), B1)
    pc.chapado(barra & erode(m, 2) & ~erode(m, 3), B2)
    # emblema: losango em brasa apagada
    emb = poli([(184, 226), (192, 238), (184, 252), (176, 238)])
    pc.chapado(emb & m, B1)
    pc.chapado(erode(emb, 1) & m, B2)
    pc.chapado(erode(emb, 3) & m, C1)
    pc.pts['raiz'] = (184, 208)
    return pc


def tronco():
    pc = Peca('tronco')
    # barriga: 3 gomos que encolhem
    for i, (ya, yb, xa, xb) in enumerate(((164, 180, 138, 216), (177, 192, 142, 214), (189, 203, 146, 214))):
        g = pc.placa([(xa, ya), (xb, ya - 2), (xb - 2, yb), (xa + 4, yb + 1)], RAMPA_AE, chapa=3, base=-0.02,
                     filete=A3)
        pc.quina(erode(g, 2), (176, ya), (178, yb), RAMPA_AE)
    # peitoral facetado, com quina no meio
    peito = pc.placa([(120, 114), (146, 102), (178, 98), (212, 104), (232, 120), (232, 150), (218, 172),
                      (172, 184), (136, 172), (120, 150), (116, 130)], RAMPA_A, bojo=13, base=0.02, filete=A5,
                     queda=0.3, tx=0.2)
    dentro = erode(peito, 2)
    pc.quina(dentro, (168, 98), (172, 184), RAMPA_A)
    # musculos/costelas gravados
    for (a, b, c) in (((126, 128), (142, 136), (152, 132)), ((124, 144), (140, 152), (150, 150)),
                      ((128, 160), (142, 166), (152, 166)), ((182, 132), (204, 132), (226, 122)),
                      ((182, 150), (206, 148), (228, 140)), ((180, 166), (202, 166), (220, 160))):
        pc.linha([a, b, c], A0, so=dentro, suave=True)
        pc.linha([(a[0], a[1] + 1), (b[0], b[1] + 1), (c[0], c[1] + 1)], A4, so=dentro, suave=True)
    pc.riscos(peito, 6, 3)
    # moldura de bronze do nucleo (losango) e o NUCLEO em brasa
    nx, ny = NUCLEO
    mold = poli([(nx, ny - 17), (nx + 14, ny), (nx, ny + 17), (nx - 14, ny)])
    pc.volume(mold, RAMPA_B, chapa=3, base=0.06, textura=None)
    pc.contorno(mold, LINHA, filete=B3)
    poco = poli([(nx, ny - 12), (nx + 10, ny), (nx, ny + 12), (nx - 10, ny)])
    pc.chapado(poco, G0)
    pc.brasa(poli([(nx, ny - 10), (nx + 8, ny), (nx, ny + 10), (nx - 8, ny)]))
    for (dx, dy) in ((0, -17), (14, 0), (0, 17), (-14, 0)):
        pc.rebite(nx + dx * 0.82 - 0.5, ny + dy * 0.82 - 0.5, B3, B2)
    # fendas saindo do nucleo
    for i, alvo in enumerate(((128, 120), (126, 156), (140, 174), (200, 108), (226, 134), (212, 170), (186, 180))):
        ini = (nx + (alvo[0] - nx) * 0.36, ny + (alvo[1] - ny) * 0.36)
        pc.fenda(zigue(ini, alvo, 6, 3.4, 60 + i), clara=(i % 2 == 0), so=dentro, ramos=2, semente=80 + i)
    # gola alta
    gola = pc.placa([(132, 106), (150, 96), (182, 94), (198, 110), (172, 122), (140, 118)], RAMPA_A, chapa=3,
                    base=0.1, filete=A5)
    pc.friso([(136, 116), (156, 119), (172, 120), (195, 110)], so=gola, suave=True)
    pc.pts['nucleo'] = NUCLEO
    return pc


def cabeca():
    pc = Peca('cabeca')
    # chifre de tras (mais escuro)
    ch_t = tubo([(130, 76), (112, 70), (96, 50), (100, 20)], [8.5, 7.5, 4.8, 1.2])
    pc.volume(ch_t, RAMPA_OE, bojo=5, base=0.2, textura=None, queda=0.0)
    pc.contorno(ch_t, LINHA, filete=O2)
    for (x, y, a) in ((121, 73, 70), (110, 66, 55), (101, 54, 30), (98, 40, 5)):
        r = math.radians(a)
        pc.linha([(x - 7 * math.cos(r), y - 7 * math.sin(r)), (x + 7 * math.cos(r), y + 7 * math.sin(r))], O0,
                 so=ch_t)
    # crista (lamina) em cima do elmo
    crista = pc.placa([(134, 64), (146, 46), (164, 48), (178, 66), (176, 82), (166, 72), (150, 64)], RAMPA_A,
                      chapa=2, base=0.12, filete=A5)
    pc.linha([(146, 50), (160, 56), (172, 70)], A0, so=crista, suave=True)
    # elmo (calota)
    elmo = pc.placa([(122, 86), (126, 70), (138, 60), (154, 60), (166, 68), (170, 86), (166, 102), (152, 110),
                     (134, 108), (122, 98)], RAMPA_A, bojo=11, base=0.06, filete=A5, suave=True)
    pc.riscos(elmo, 3, 12)
    # queixada com presas
    qx = pc.placa([(112, 104), (138, 100), (140, 112), (128, 122), (114, 116)], RAMPA_AE, chapa=2, base=-0.04,
                  filete=A3)
    # boca: brasa atras dos dentes
    boca = poli([(112, 100), (138, 97), (138, 105), (112, 108)])
    pc.chapado(boca, G1)
    pc.chapado(poli([(114, 101), (136, 99), (136, 102), (114, 104)]), G2)
    for x in (116, 121, 126, 131, 136):                          # dentes de cima e de baixo
        d1 = poli([(x - 2, 97), (x + 2, 97), (x, 103)])
        pc.chapado(d1, O3)
        pc.chapado(d1 & (XS > OX + x), O2)
    for x in (118, 124, 129, 134):
        d2 = poli([(x - 2, 109), (x + 2, 109), (x, 103.5)])
        pc.chapado(d2, O2)
    # viseira em cunha, com quina, avancando para a esquerda
    vis = pc.placa([(110, 92), (124, 80), (144, 82), (148, 96), (138, 100), (112, 100)], RAMPA_A, chapa=3,
                   base=0.08, filete=A5)
    pc.quina(erode(vis, 2), (112, 96), (146, 88), RAMPA_A)
    # fresta dos olhos, em brasa, com a chama subindo para tras
    fresta = poli([(114, 91), (140, 84), (143, 88), (118, 95)])
    pc.chapado(fresta, LINHA)
    pc.brasa(poli([(118, 91), (134, 86.5), (135, 89.5), (121, 94)]),
             nucleo=poli([(121, 91), (130, 88.5), (130, 90.5), (123, 93)]))
    # friso de bronze na testa e rebites
    pc.friso([(123, 84), (136, 76), (156, 74), (168, 82)], suave=True, so=elmo)
    for (x, y) in ((130, 70), (146, 66), (160, 70)):
        pc.rebite(x, y)
    # chifre da frente (osso claro), grande, com aneis
    ch = tubo([(158, 74), (182, 64), (200, 40), (192, 8)], [9.5, 8.5, 5.5, 1.3])
    pc.volume(ch, RAMPA_O, bojo=6, base=0.02, textura=None)
    pc.contorno(ch, LINHA, filete=O3)
    for (x, y, a) in ((168, 71, 75), (179, 65, 60), (190, 54, 35), (197, 42, 15), (198, 30, -5), (196, 20, -15)):
        r = math.radians(a)
        L = 9 if y > 40 else 6
        pc.linha([(x - L * math.cos(r), y - L * math.sin(r)), (x + L * math.cos(r), y + L * math.sin(r))], O0, so=ch)
        pc.linha([(x - L * math.cos(r), y - L * math.sin(r) + 1), (x + L * math.cos(r), y + L * math.sin(r) + 1)],
                 O1, so=ch)
    # base de bronze do chifre
    anel = ch & elipse(160, 74, 11, 11)
    pc.chapado(anel & ~erode(ch, 1) | anel & elipse(160, 74, 11, 11) & ~elipse(160, 74, 8, 8), B1)
    pc.contorno(ch & elipse(160, 74, 11, 11), LINHA)
    pc.pts['olho'] = OLHO
    pc.pts['pescoco'] = PESCOCO
    return pc


def _lames(pc, placas, espinhos, rampa, base, fil, com_friso=True):
    """Ombreira em laminas sobrepostas (de baixo para cima) + espinhos."""
    for e in espinhos:
        m = poli(e)
        pc.volume(m, rampa, bojo=3, base=base + 0.14, textura=None)
        pc.contorno(m, LINHA, filete=fil)
    feitas = []
    for i, pts in enumerate(reversed(placas)):
        topo = (i == len(placas) - 1)
        m = pc.placa(pts, rampa, bojo=11 if topo else 0, chapa=3, base=base + (0.04 if topo else -0.04 * (len(placas) - i)),
                     filete=fil, suave=topo, tx=0.22 if topo else 0.14)
        feitas.append(m)
    return feitas


def ombreira():
    pc = Peca('ombreira')
    pl = _lames(pc,
                [[(194, 98), (212, 82), (240, 78), (264, 90), (272, 110), (262, 124), (232, 130), (204, 124), (190, 110)],
                 [(196, 118), (232, 130), (266, 120), (268, 138), (234, 150), (200, 138)],
                 [(202, 134), (234, 150), (262, 136), (262, 152), (234, 164), (206, 152)]],
                [[(204, 92), (202, 56), (220, 84)], [(226, 82), (240, 42), (250, 84)], [(254, 92), (280, 62), (270, 106)]],
                RAMPA_A, 0.04, A5)
    topo = pl[-1]
    pc.friso([(192, 112), (206, 122), (232, 127), (260, 121), (270, 110)], suave=True, so=topo)
    pc.friso([(200, 136), (234, 147), (266, 136)], so=pl[1])
    pc.friso([(206, 150), (234, 161), (260, 150)], so=pl[0])
    for (x, y) in ((200, 108), (214, 118), (232, 121), (250, 117), (263, 106)):
        pc.rebite(x, y)
    pc.riscos(topo, 5, 21)
    pc.fenda(zigue((214, 88), (236, 110), 6, 3.2, 9), so=topo, ramos=3, semente=14)
    pc.fenda(zigue((236, 110), (258, 100), 4, 2.4, 10), clara=False, so=topo)
    pc.fenda(zigue((236, 110), (228, 124), 3, 2.0, 11), clara=False, so=topo)
    return pc


def ombreira_tras():
    pc = Peca('ombreira_tras')
    pl = _lames(pc,
                [[(90, 118), (100, 100), (122, 94), (142, 102), (144, 122), (132, 132), (106, 132)],
                 [(96, 128), (118, 136), (140, 126), (140, 140), (118, 150), (98, 142)]],
                [[(100, 106), (94, 78), (112, 98)], [(120, 96), (124, 66), (136, 100)]],
                RAMPA_AE, -0.04, A3)
    pc.friso([(92, 120), (106, 129), (130, 129), (143, 121)], suave=True, so=pl[-1], claro=B1, brilho=B2)
    pc.rebite(108, 118, A4, A2)
    pc.rebite(126, 120, A4, A2)
    return pc


def braco():
    """braco da frente (do ombro ao cotovelo)"""
    pc = Peca('braco')
    m = tubo([OMBRO, (242, 134), COTOVELO], [16, 15, 13])
    pc.volume(m, RAMPA_A, bojo=9, base=-0.02)
    pc.contorno(m, LINHA, filete=A4)
    for (a, b) in (((228, 138), (256, 126)), ((234, 150), (262, 140))):
        pc.linha([a, b], LINHA, so=m)
        pc.linha([(a[0], a[1] + 1), (b[0], b[1] + 1)], A3, so=m)
    pc.fenda(zigue((238, 124), (248, 146), 4, 2.4, 33), clara=False, so=erode(m, 2))
    return pc


def antebraco():
    """braçadeira, cotoveleira com espinho e a GARRA aberta (mao da frente)"""
    pc = Peca('antebraco')
    cx, cy = COTOVELO
    mx, my = MAO
    vb = pc.placa([(cx - 15, cy - 2), (cx + 12, cy + 2), (cx + 13, cy + 18), (mx + 13, my - 8), (mx - 1, my - 12),
                   (mx - 14, my - 6), (cx - 17, cy + 14)], RAMPA_A, bojo=8, base=0.02, filete=A5)
    pc.quina(erode(vb, 2), (cx - 3, cy), (mx, my - 10), RAMPA_A)
    pc.friso([(mx - 13, my - 8), (mx - 1, my - 13), (mx + 12, my - 10)], so=vb)
    pc.friso([(cx - 16, cy + 12), (cx - 2, cy + 18), (cx + 12, cy + 16)], so=vb)
    pc.riscos(vb, 3, 44)
    for k in range(3):                                   # barbatanas na braçadeira
        bx, by = cx + 12 - k * 2, cy + 14 + k * 9
        b = poli([(bx - 2, by - 4), (bx + 10, by + 3), (bx - 3, by + 5)])
        pc.volume(b, RAMPA_A, bojo=2, base=0.14, textura=None)
        pc.contorno(b, LINHA, filete=A5)
    esp = poli([(cx + 4, cy - 9), (cx + 30, cy - 14), (cx + 8, cy + 5)])
    pc.volume(esp, RAMPA_A, bojo=3, base=0.14, textura=None)
    pc.contorno(esp, LINHA, filete=A5)
    pc.placa([(cx - 13, cy - 6), (cx, cy - 13), (cx + 12, cy - 5), (cx + 11, cy + 9), (cx - 4, cy + 13),
              (cx - 14, cy + 5)], RAMPA_A, bojo=6, base=0.1, filete=A5, suave=True)
    pc.rebite(cx - 1, cy - 1)
    # garra: 4 dedos de armadura abertos, com unhas compridas de osso
    for (bx, by, jx, jy, tx, ty) in ((mx - 9, my + 4, mx - 18, my + 16, mx - 26, my + 36),
                                     (mx - 3, my + 8, mx - 7, my + 22, mx - 12, my + 44),
                                     (mx + 4, my + 8, mx + 5, my + 23, mx + 3, my + 45),
                                     (mx + 10, my + 4, mx + 16, my + 16, mx + 20, my + 34)):
        dedo = tubo([(bx, by), (jx, jy)], [4.2, 3.6])
        pc.volume(dedo, RAMPA_A, bojo=3, base=0.04, textura=None)
        pc.contorno(dedo, LINHA, filete=A4)
        d = np.hypot(tx - jx, ty - jy)
        nx_, ny_ = -(ty - jy) / d, (tx - jx) / d
        g = poli([(jx - nx_ * 3.4, jy - ny_ * 3.4), (jx + nx_ * 3.4, jy + ny_ * 3.4), (tx, ty)])
        pc.volume(g, RAMPA_O, bojo=3, base=0.0, textura=None)
        pc.contorno(g, LINHA, filete=O3)
    pol = tubo([(mx - 12, my - 2), (mx - 22, my + 6)], [4.0, 3.2])            # polegar
    pc.volume(pol, RAMPA_A, bojo=3, base=0.04, textura=None)
    pc.contorno(pol, LINHA, filete=A4)
    g = poli([(mx - 21, my + 2), (mx - 19, my + 9), (mx - 34, my + 16)])
    pc.volume(g, RAMPA_O, bojo=3, textura=None)
    pc.contorno(g, LINHA, filete=O3)
    mao = pc.placa([(mx - 12, my - 6), (mx, my - 11), (mx + 12, my - 6), (mx + 13, my + 6), (mx + 2, my + 12),
                    (mx - 11, my + 8)], RAMPA_A, bojo=6, base=0.08, filete=A5, suave=True)
    for k in range(3):                                   # espinhos dos nos dos dedos
        sp = poli([(mx - 8 + k * 7, my + 4 + k), (mx - 5 + k * 7, my - 4 + k), (mx - 1 + k * 7, my + 5 + k)])
        pc.volume(sp, RAMPA_A, bojo=2, base=0.2, textura=None)
        pc.contorno(sp, LINHA)
    pc.fenda(zigue((mx - 4, my - 4), (mx + 8, my + 4), 3, 2.0, 91), clara=False, so=erode(mao, 2))
    pc.pts['mao'] = MAO
    return pc


def braco_tras():
    """braco de TRAS, do ombro ao cotovelo (vai para a frente, ate o cabo)"""
    pc = Peca('braco_tras')
    m = tubo([OMBRO_T, (108, 132), COTOVELO_T], [14, 13, 11.5])
    pc.volume(m, RAMPA_AE, bojo=8, base=-0.04)
    pc.contorno(m, LINHA, filete=A3)
    pc.linha([(98, 126), (118, 138)], LINHA, so=m)
    pc.linha([(98, 127), (118, 139)], A2, so=m)
    return pc


def antebraco_tras():
    """antebraco de tras + a manopla fechada no cabo do montante"""
    pc = Peca('antebraco_tras')
    rampa = RAMPA_AE
    cx, cy = COTOVELO_T
    mx, my = MAO_T
    vb = tubo([COTOVELO_T, ((cx + mx) / 2.0, (cy + my) / 2.0 + 2), MAO_T], [11.5, 12.5, 10])
    pc.volume(vb, rampa, bojo=7, base=-0.02)
    pc.contorno(vb, LINHA, filete=A3)
    pc.friso([(mx + 5, my - 9), (mx + 10, my), (mx + 9, my + 10)], so=vb, claro=B1, brilho=B2)
    esp = poli([(cx - 2, cy + 6), (cx + 6, cy + 24), (cx + 9, cy + 5)])
    pc.volume(esp, rampa, bojo=3, base=0.1, textura=None)
    pc.contorno(esp, LINHA, filete=A3)
    pc.placa([(cx - 9, cy - 8), (cx + 5, cy - 10), (cx + 11, cy), (cx + 6, cy + 9), (cx - 8, cy + 8)], rampa,
             bojo=5, base=0.04, filete=A4, suave=True)
    mao = pc.placa([(mx - 10, my - 10), (mx + 4, my - 12), (mx + 11, my - 3), (mx + 9, my + 10), (mx - 4, my + 13),
                    (mx - 12, my + 4)], RAMPA_A, bojo=6, base=0.02, filete=A4, suave=True)
    for k in range(4):                                   # dedos fechados em volta do cabo
        pc.linha([(mx - 10, my - 6 + k * 5), (mx + 4, my - 8 + k * 5)], LINHA, so=mao)
        pc.ponto(mx - 7, my - 8 + k * 5, A4)
    pc.pts['mao'] = MAO_T
    return pc


def espada():
    pc = Peca('espada')
    u, n, L = _u_lamina()
    mao = np.array(MAO_T)

    def pt(s, w):
        p = mao + u * s + n * w
        return (float(p[0]), float(p[1]))
    g0 = 16.0                                     # onde a guarda fica (depois da mao)
    # lamina: costas (lado de cima) com ganchos e dentes; fio (lado de baixo) largo
    costas = [(g0, -8), (g0 + 8, -8), (g0 + 12, -17), (g0 + 20, -9), (g0 + 30, -9), (g0 + 36, -15), (g0 + 44, -10),
              (g0 + 58, -15), (L * 0.5, -15), (L * 0.78, -12), (L * 0.92, -6), (L, 1)]
    fio = [(L * 0.94, 8), (L * 0.8, 15), (L * 0.55, 18), (L * 0.3, 17), (g0 + 14, 14), (g0 + 8, 19), (g0, 9)]
    lam = poli([pt(s, w) for s, w in costas + fio])
    pc.volume(lam, RAMPA_A, chapa=6, base=0.06, forca_tex=0.14, queda=0.0)
    pc.contorno(lam, LINHA, filete=A5)
    dentro = erode(lam, 2)
    pc.quina(dentro & ~lado_de(pt(g0, 4), pt(L, 4)), pt(g0 + 4, -3), pt(L * 0.96, -1), RAMPA_A)
    pc.riscos(lam, 9, 5)
    # fio em brasa (lado de baixo): faixa vermelha, laranja na beirada, miolo claro na borda
    faixa_fio = lam & lado_de(pt(L, 7.5), pt(g0, 9.5))
    pc.chapado(faixa_fio & erode(lam, 1), G0)
    pc.chapado(faixa_fio & erode(lam, 1) & ~erode(lam, 5), G1)
    pc.chapado(faixa_fio & erode(lam, 1) & ~erode(lam, 3), G2)
    pc.chapado(faixa_fio & erode(lam, 1) & ~erode(lam, 2) & lado_de(pt(L, 12), pt(g0, 13)), G3)
    # veios de lava subindo do fio para o meio da lamina
    for k in range(7):
        s = g0 + 26 + k * (L * 0.68 / 7.0)
        pc.fenda(zigue(pt(s, 9), pt(s + 6 + (k % 3) * 2, 1 - (k % 2) * 3), 3, 1.8, 40 + k), clara=False, so=dentro)
    # sulco no meio com runas acesas
    pc.linha([pt(g0 + 10, -5), pt(L * 0.8, -4)], A0, so=dentro)
    pc.linha([pt(g0 + 10, -4), pt(L * 0.8, -3)], A4, so=dentro)
    rnd = np.random.default_rng(77)
    for k in range(10):
        s = g0 + 22 + k * (L * 0.66 / 10.0)
        forma = rnd.integers(0, 4)
        if forma == 0:
            pc.linha([pt(s, -10), pt(s + 4, -7)], G2, so=dentro)
            pc.linha([pt(s, -7), pt(s + 4, -10)], G2, so=dentro)
        elif forma == 1:
            pc.linha([pt(s, -10), pt(s + 5, -10)], G2, so=dentro)
            pc.linha([pt(s + 2, -11), pt(s + 2, -7)], G3, so=dentro)
        elif forma == 2:
            pc.linha([pt(s, -10), pt(s + 3, -7), pt(s + 6, -10)], G2, so=dentro)
        else:
            pc.linha([pt(s, -7), pt(s + 3, -10), pt(s + 6, -7)], G2, so=dentro)
            pc.ponto(*pt(s + 3, -8), G3)
    # guarda (cruzeta) em asa de morcego, de bronze, com caveira no meio
    gd = poli([pt(g0 - 6, -30), pt(g0 + 2, -34), pt(g0 + 4, -22), pt(g0 + 9, -14), pt(g0 + 7, -6), pt(g0 + 7, 6),
               pt(g0 + 9, 14), pt(g0 + 4, 22), pt(g0 + 2, 32), pt(g0 - 6, 28), pt(g0 - 2, 14), pt(g0 - 4, 0),
               pt(g0 - 2, -14)])
    pc.volume(gd, RAMPA_B, chapa=3, base=0.06, textura=None)
    pc.contorno(gd, LINHA, filete=B3)
    cxg, cyg = pt(g0 + 1, 0)
    cav = elipse(cxg, cyg, 6.5, 6.5)
    pc.volume(cav, RAMPA_O, bojo=4, base=0.06, textura=None)
    pc.contorno(cav, LINHA)
    e1, e2 = pt(g0 + 2.5, -2.5), pt(g0 + 2.5, 2.5)
    pc.ponto(e1[0], e1[1], G3)
    pc.ponto(e2[0], e2[1], G3)
    # cabo enfaixado e pomo com espinho
    cabo = poli([pt(g0 - 4, -4.5), pt(g0 - 4, 4.5), pt(-26, 4), pt(-26, -4)])
    pc.volume(cabo, RAMPA_C, chapa=2, base=0.12, textura=None)
    pc.contorno(cabo, LINHA)
    for s in range(-22, int(g0) - 4, 5):
        pc.linha([pt(s, -4), pt(s + 3, 4)], C0, so=cabo)
        pc.linha([pt(s + 1, -4), pt(s + 4, 4)], C4, so=cabo)
    px_, py_ = pt(-30, 0)
    pomo = elipse(px_, py_, 7, 7) | poli([pt(-34, -3), pt(-46, 0), pt(-34, 3)])
    pc.volume(pomo, RAMPA_B, bojo=4, base=0.08, textura=None)
    pc.contorno(pomo, LINHA, filete=B3)
    pc.pts['mao'] = MAO_T
    pc.pts['ponta'] = PONTA
    return pc


ORDEM = ['capa', 'espada', 'braco_tras', 'antebraco_tras', 'ombreira_tras', 'perna_tras', 'perna_frente',
         'tabardo', 'tronco', 'saiote', 'cabeca', 'braco', 'antebraco', 'ombreira']


def montar():
    """{nome: Peca} de todas as pecas (cada uma na pose de repouso)."""
    f = dict(capa=capa, espada=espada, braco_tras=braco_tras, antebraco_tras=antebraco_tras,
             ombreira_tras=ombreira_tras, perna_tras=perna_tras, perna_frente=perna_frente, tabardo=tabardo,
             saiote=saiote, tronco=tronco, cabeca=cabeca, braco=braco, antebraco=antebraco, ombreira=ombreira)
    return {n: f[n]() for n in ORDEM}


def aro(img):
    """Fecha buraquinhos e poe a luz de brasa na borda de FORA, nas costas
    (direita) e em cima - destaca do fundo escuro do app."""
    cheio = img > 0
    solido = erode(dilata(cheio, 2), 2)
    out = img.copy()
    out[solido & ~cheio] = FECHO
    s = solido
    viz_e = np.zeros_like(s)
    viz_b = np.zeros_like(s)
    viz_e[:, 1:] = s[:, :-1]                       # tem desenho a esquerda (borda da direita)
    viz_b[:-1, :] = s[1:, :]                       # tem desenho embaixo (borda de cima)
    out[~s & (viz_e | viz_b)] = ARO
    return out


def compor(pecas, ordem=ORDEM):
    img = np.zeros((CH, CW), np.uint8)
    for n in ordem:
        m = pecas[n].masc
        img[m] = pecas[n].img[m]
    return aro(img)


def rgba(idx, fundo=(6, 6, 12)):
    p = np.array(PAL, np.uint8)
    r = p[idx]
    f = np.zeros_like(r)
    f[...] = (fundo[0], fundo[1], fundo[2], 255)
    return np.where(r[..., 3:4] > 0, r, f)


def salvar(idx, caminho, zoom=3, recorte=None):
    a = rgba(idx)[..., :3]
    if recorte is None:
        ys, xs = np.nonzero(idx)
        recorte = (xs.min() - 6, ys.min() - 6, xs.max() + 7, ys.max() + 7)
    x0, y0, x1, y1 = recorte
    im = Image.fromarray(a[y0:y1, x0:x1])
    im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    im.save(caminho)
    print(caminho, im.size)


if __name__ == '__main__':
    cmd = sys.argv[1]
    pecas = montar()
    if cmd == 'previa':
        salvar(compor(pecas), sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 3)
    elif cmd == 'pecas':
        cols = 5
        tiras = []
        for n in ORDEM:
            idx = pecas[n].img
            ys, xs = np.nonzero(idx)
            tiras.append(rgba(idx)[ys.min() - 2:ys.max() + 3, xs.min() - 2:xs.max() + 3, :3])
        hmax = max(t.shape[0] for t in tiras)
        wmax = max(t.shape[1] for t in tiras)
        lin = (len(tiras) + cols - 1) // cols
        S = np.zeros((lin * (hmax + 4), cols * (wmax + 4), 3), np.uint8) + 20
        for i, t in enumerate(tiras):
            y, x = (i // cols) * (hmax + 4), (i % cols) * (wmax + 4)
            S[y:y + t.shape[0], x:x + t.shape[1]] = t
        Image.fromarray(S).resize((S.shape[1] * 2, S.shape[0] * 2), Image.NEAREST).save(sys.argv[2])
        print(sys.argv[2])
