"""
kirito.py — TraveteFocus
Kirito em pixel art, montado por partes a partir de parametros de pose
(tronco, pernas, 2 bracos, 2 espadas, cabelo e sobretudo), com muitos
quadros interpolados por golpe.

  Elucidator    : espada preta (mao da frente), bainha na cintura como
                  uma katana - cabo para a frente, bainha para tras e para
                  baixo, rente a aba do sobretudo
  Dark Repulser : espada azulada/cristalina (mao de tras), nas costas

Sobretudo de verdade (nao capa): saia presa na cintura toda, aberta na
frente, barra no meio da canela. Bracos de 3 px com luva; o da frente tem
manga mais clara e contorno escuro para nao sumir no sobretudo preto.

Fisica secundaria: o sobretudo e o cabelo reagem ao movimento real do
boneco (molas que passam do ponto e voltam) e ondulam continuamente; um
brilho percorre as laminas de tempos em tempos.

KiritoPixel(Widget) — poses/sequencias (cache por pose), idle, rotacao em
                      torno do quadril ou de um pivo (ex: mao pendurada),
                      afterimages.
Faiscas(Widget)     — faiscas quadradas (pixel) nos impactos.
"""
import math
import time
from array import array
import random
from collections import OrderedDict

from kivy.uix.widget import Widget
from kivy.graphics import (Color, Rectangle, Mesh, PushMatrix, PopMatrix,
                           Translate, Rotate, Scale)
from kivy.graphics.texture import Texture
from kivy.properties import BooleanProperty, NumericProperty
from kivy.clock import Clock

FPS = 30.0

_PALETA = {
    'H': (0.13, 0.14, 0.22, 1), 'h': (0.36, 0.40, 0.62, 1),     # cabelo
    'S': (1.00, 0.86, 0.74, 1), 's': (0.86, 0.66, 0.56, 1),     # pele
    'E': (0.08, 0.10, 0.18, 1),                                  # olho
    'C': (0.17, 0.17, 0.24, 1), 'c': (0.32, 0.33, 0.45, 1),     # sobretudo
    'A': (0.24, 0.24, 0.33, 1),                                  # manga do braco da frente
    'q': (0.21, 0.19, 0.30, 1),                                  # forro do sobretudo
    'G': (0.62, 0.66, 0.76, 1),                                  # detalhes cinza
    'P': (0.10, 0.10, 0.15, 1), 'B': (0.05, 0.05, 0.08, 1),     # calca / bota
    'M': (0.09, 0.09, 0.13, 1),                                  # luva
    # Elucidator (preta): lamina, fio claro, costas, cabo, guarda, pontas
    'W': (0.08, 0.08, 0.12, 1), 'w': (0.60, 0.64, 0.78, 1), 'u': (0.24, 0.24, 0.33, 1),
    'v': (0.42, 0.44, 0.56, 1),                                  # filete da bainha
    'j': (0.30, 0.32, 0.43, 1),                                  # hamon (ondas no aco preto)
    '9': (0.55, 1.00, 1.00, 1),                                  # ciano aceso (reiatsu, olhos)
    '5': (1.00, 0.86, 0.30, 1),                                  # emote "!" / "..."
    '6': (0.62, 0.88, 1.00, 1),                                  # gota de suor
    'K': (0.20, 0.20, 0.27, 1), 'g': (0.34, 0.34, 0.44, 1), 'k': (0.66, 0.68, 0.80, 1),
    # Dark Repulser (cristal azul)
    'R': (0.40, 0.78, 1.00, 1), 'r': (0.88, 0.98, 1.00, 1), 'z': (0.22, 0.52, 0.86, 1),
    'y': (0.30, 0.62, 0.86, 1), 'Y': (0.82, 0.95, 1.00, 1),
    # brilho percorrendo a lamina
    '!': (1.00, 1.00, 1.00, 1), '1': (0.80, 0.96, 1.00, 0.85),
    # rastro de movimento da lamina (smear em pixel)
    'X': (0.88, 0.98, 1.00, 0.88), 'x': (0.42, 0.86, 1.00, 0.6),
    'O': (0.00, 0.78, 1.00, 0.85),                               # contorno (rim light)
    # forma Mugetsu (Bankai): corpo na sombra, olhos e chamas roxo/azul
    'D': (0.05, 0.04, 0.09, 1), 'd': (0.22, 0.13, 0.36, 1),     # roupa na sombra / brilho roxo
    'V': (0.90, 0.62, 1.00, 1),                                  # olhos acesos (roxo)
    'F': (0.62, 0.28, 1.00, 0.95), 'f': (0.28, 0.58, 1.00, 0.95),
    'L': (0.93, 0.86, 1.00, 0.9),                                # ponta clara da chama
    'o': (0.66, 0.36, 1.00, 0.9),                                # contorno roxo
    'Q': (0.52, 0.80, 0.98, 1),                                  # pixel aceso pela luz da lamina
    # sprite premium: degraus de volume
    'J': (0.07, 0.075, 0.13, 1), 'I': (0.23, 0.25, 0.40, 1),    # cabelo: sombra profunda / brilho medio
    'e': (0.24, 0.30, 0.47, 1), 'n': (0.94, 0.97, 1.00, 1),     # iris / brilho do olho
    '2': (0.10, 0.10, 0.155, 1),                                 # sobretudo: sombra profunda
    '4': (0.055, 0.055, 0.085, 1),                               # camisa preta (abertura do casaco)
    '7': (0.06, 0.06, 0.10, 1),                                  # calca: lado da sombra
    '+': (0.90, 0.94, 1.00, 1),                                  # reflexo no aco
    '0': (0.00, 0.42, 0.64, 0.85),                               # contorno do lado da sombra
    '8': (0.36, 0.17, 0.60, 0.85),                               # contorno roxo do lado da sombra
    'm': (0.42, 0.50, 0.72, 1),                                  # iris (parte clara, embaixo)
    'T': (0.62, 0.30, 0.34, 1),                                  # dentro da boca
    'Z': (0.15, 0.72, 0.95, 1),                                  # costura ciano da roupa (acende nos golpes)
    'N': (0.02, 0.03, 0.07, 1),                                  # contorno escuro
    'p': (0.30, 0.33, 0.46, 1),                                  # brilho cinza-azulado da calca
    'b': (0.17, 0.18, 0.26, 1),                                  # bota: meio-tom
    # detalhe fino (3 texels por unidade)
    't': (0.62, 0.44, 0.50, 1),                                  # pele: sombra funda (puxa para o vinho)
    'i': (0.84, 0.87, 0.96, 1),                                  # branco do olho (susto)
    '3': (0.33, 0.43, 0.70, 1),                                  # iris: meio-tom
    'U': (0.70, 0.82, 1.00, 1),                                  # cabelo: reflexo
    '%': (0.50, 0.58, 0.76, 1),                                  # couro: reflexo (bota, luva)
    '&': (0.11, 0.075, 0.18, 1),                                 # roupa na sombra: meio-tom roxo
    '~': (0.38, 0.22, 0.40, 1),                                  # rosto: sombra funda da franja (Mugetsu)
    '^': (0.86, 0.72, 0.98, 1),                                  # pele com reflexo roxo do fogo
    '<': (0.62, 0.34, 1.00, 0.6), '>': (0.92, 0.82, 1.00, 0.88),  # rastro roxo (Mugetsu)
}
_SEM_CONTORNO = set('xX!1FfL<>')
# Mugetsu: a roupa escurece (o rosto continua claro, os olhos acendem)
_SOMBRA = {'C': '&', 'c': 'd', 'A': 'd', 'q': 'D', 'P': '&', 'B': 'D', 'M': 'D', 'G': 'd', 'E': 'D',
           '2': 'D', '4': 'D', '7': 'D', 'e': 'V', 'n': '!', 'K': 'D', 'Z': 'o', 'p': 'd', 'b': '&',
           '3': 'V', 'm': 'L', 'i': 'd', 'U': 'o', '%': 'd', '9': 'L', 'x': '<', 'X': '>'}
_CORPO_M = set('HhSsDdVJIeTt&~^')
# luz dinamica: pixels do corpo perto da lamina acesa clareiam um degrau
_LAMINA = set('wjRrzY9!')                  # so as partes claras (a bainha usa W/u)
_ACENDE = {'C': 'c', 'A': 'c', 'q': 'c', 'P': 'c', 'c': 'Q', 'H': 'h', 'h': 'Q', 'B': 'K',
           'M': 'g', 'G': 'Q', 'D': 'd', 'd': 'o', '2': 'C', '4': 'C', '7': 'P', 'J': 'H', 'I': 'h',
           'U': 'Q', '%': 'Q', '&': 'd'}


def _iluminar(px, luz, esc=1):
    """Luz da lamina no corpo: os pixels encostados nela sobem 2 degraus
    (ate o azul aceso), os mais longe sobem 1. Sem blur: so troca de cor em
    clusters. A distancia sai por aneis (cada anel = os vizinhos do anel
    anterior): bem mais leve que medir pixel a pixel."""
    lamina = [q for q, ch in px.items() if ch in _LAMINA]
    if not lamina:
        return
    r = (2 if luz >= 0.75 else 1) * esc
    forte = luz >= 0.75
    visto = set(lamina)
    anel = lamina
    for d in range(1, r + 1):
        novo = []
        for (x, y) in anel:
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),
                      (x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)):
                if q not in visto:
                    visto.add(q)
                    novo.append(q)
        for q in novo:
            ch = px.get(q)
            if ch in _ACENDE:
                ch = _ACENDE[ch]
                if d <= esc and forte and ch in _ACENDE:
                    ch = _ACENDE[ch]
                px[q] = ch
        anel = novo


_CABECA = [
    "....JHHHJ....",
    "..JHHIhhHHJ..",
    ".JHHIhhIHHHH.",
    "JHHHIhHHHHHHH",
    "JHHHHHHHHIHHH",
    "JJHHHHHsHHHsh",
    "JHHHHsSSSSSSS",
    "JHHHsSSEESSES",
    ".JHHsSSenSSeS",
    "..JHsSSSSSsS.",
    "...JHssSSss..",
]


def _cabeca_var(trocas, base=None):
    c = list(base or _CABECA)
    for i, linha in trocas.items():
        c[i] = linha
    return c


# piscando: so a linha de baixo do olho
_CABECA_PISCA = _cabeca_var({7: "JHHHsSSSSSSSS", 8: ".JHHsSSEESSES"})
# olhando para baixo (o PIN sendo digitado)
_CABECA_BAIXO = _cabeca_var({7: "JHHHsSSSSSSSS", 8: ".JHHsSSEESSES", 9: "..JHsSSenSSe."})
# serio/determinado: sobrancelha franzida por cima de olhos estreitos
_CABECA_SERIO = _cabeca_var({6: "JHHHHsSEESSEE", 7: "JHHHsSSenSSeS", 8: ".JHHsSSSSSSSS"})
# gritando no golpe: serio + boca aberta
_CABECA_GRITO = _cabeca_var({9: "..JHsSSSSSEs.", 10: "...JHssSSEs.."}, _CABECA_SERIO)
# olhos acesos em ciano (reiatsu da espada evoluida)
_CABECA_LUZ = _cabeca_var({6: "JHHHHsSEESSEE", 7: "JHHHsSS99SS9S", 8: ".JHHsSS99SS9S"})
# susto: olhos arregalados e boca em "o"
_CABECA_SUSTO = _cabeca_var({6: "JHHHHsSEESSES", 7: "JHHHsSSenSSeS", 8: ".JHHsSSeeSSeS",
                             9: "..JHsSSSSSEs."})
# feliz: olhos fechados em arco (^^) e sorriso
_CABECA_FELIZ = _cabeca_var({7: "JHHHsSSEESSSS", 8: ".JHHsSESSESES", 9: "..JHsSSSSsSS."})
_CABECAS = {'a': _CABECA, 'f': _CABECA_PISCA, 'b': _CABECA_BAIXO, 's': _CABECA_SERIO,
            'g': _CABECA_GRITO, 'l': _CABECA_LUZ, 'u': _CABECA_SUSTO, 'e': _CABECA_FELIZ}
_TRONCO = [
    "...2CCsSsCc..",          # gola alta e o pescoco entre elas
    "...2CG4GAc...",          # abertura do casaco: camisa preta e friso prateado
    "..2CCG4GCAc..",
    "..2CcCGCCAc..",
    "..2CcCGC2Ac..",          # dobra
    ".2CCcCGC2CAc.",
    ".2MMMgkgMMMc.",          # cinto (fivela prateada com brilho)
    ".2CCCPPPCCAc.",
]
# pernas de verdade: quadril, joelho (calculado por IK) e pe.
# H = altura do quadril acima da linha dos pes (_PES). Em pe (ar=False) os
# pes ficam no chao e, se o corpo abaixa (dy), os joelhos dobram sozinhos;
# no ar (ar=True) os pes vao presos ao quadril. f/b = pe da frente/de tras
# (x relativo ao quadril; y relativo ao quadril quando no ar).
_COXA, _CANELA = 6.3, 6.3
_PERNAS_P = {
    'repouso':      dict(H=12.0, ar=False, f=(2.0, 0.0), b=(-1.8, 0.0)),
    'passo':        dict(H=11.8, ar=False, f=(3.4, 0.0), b=(-3.0, 0.0)),
    'avanco':       dict(H=11.0, ar=False, f=(5.6, 0.0), b=(-6.2, 0.0)),
    'avanco_baixo': dict(H=8.6, ar=False, f=(5.8, 0.0), b=(-6.8, 0.0)),
    'agachado':     dict(H=6.6, ar=False, f=(4.0, 0.0), b=(-3.2, 0.0)),
    'dobra':        dict(H=10.2, ar=False, f=(2.8, 0.0), b=(-2.2, 0.0)),
    # bases de espadachim: pes afastados e joelhos soltos
    'base':         dict(H=11.2, ar=False, f=(3.9, 0.0), b=(-3.5, 0.0)),
    'base_larga':   dict(H=10.3, ar=False, f=(5.0, 0.0), b=(-5.2, 0.0)),
    'recua':        dict(H=10.4, ar=False, f=(3.2, 0.0), b=(-4.8, 0.0)),     # peso na perna de tras
    'pulo':         dict(H=11.0, ar=True, f=(2.8, -6.6), b=(-0.4, -6.0)),
    'suspenso':     dict(H=12.3, ar=True, f=(1.8, -12.2), b=(-1.4, -11.7)),
    'solto':        dict(H=12.4, ar=True, f=(1.0, -12.4), b=(-1.1, -12.2)),
    'solto2':       dict(H=12.2, ar=True, f=(1.5, -12.2), b=(-3.9, -11.3)),
    'solto_meio':   dict(H=12.3, ar=True, f=(1.2, -12.3), b=(-2.5, -11.9)),
    'pendente':     dict(H=12.2, ar=True, f=(1.6, -12.1), b=(-0.4, -12.0)),
    'grudado':      dict(H=9.0, ar=True, f=(3.6, -6.4), b=(0.4, -6.2)),
}
_PERNAS = _PERNAS_P                      # (nomes das pernas usados nas poses)


def _alt_pernas(p):
    a = _PERNAS_P[p['pernas']]['H']
    b = p.get('pernas_b')
    if b:
        a += (_PERNAS_P[b]['H'] - a) * (p.get('pt', 0.0) or 0.0)
    return a


def altura(p):
    """Altura do quadril (em unidades) acima da sola da bota."""
    return _alt_pernas(p) + p['dy']


GW, GH = 80, 80          # grade total (espadas cabem para qualquer lado, ate a fundida erguida)
_X0 = 25                 # coluna esquerda do tronco/cabeca
_PES = 14                # linha dos pes (sobra embaixo para espadas apontando p/ baixo)


_CORPO = set('CcAqGPBMSsHhE24JIen7tU3%bp~^')           # cores de corpo/roupa (para o contorno do braco)


def _p(x, y):
    return (round(x), round(y))


_GUARDA_INF = [(0, -2), (0, -1), (0, 1), (0, 2), (1, -3), (1, 0), (1, 3),
               (2, -2), (2, -1), (2, 1), (2, 2)]


_BAINHA_ANG = 222.0
_BAINHA_COMP = 11


def _alca_peito(px, base_x, topo):
    """Alca diagonal que prende a bainha da Dark Repulser nas costas, com
    fivela prateada (detalhe do sobretudo do Kirito)."""
    for i, (x, y) in enumerate(((3, 0), (4, -1), (5, -2), (6, -3), (7, -3), (8, -4), (9, -5))):
        px[(base_x + x, topo + y)] = 'G' if i == 3 else 'B'


def _emote(px, qual, base_x, topo_cab):
    """Balaozinho de expressao por cima da cabeca (simetrico: o boneco pode
    estar espelhado): '!', 'gota', '...', 'brilho'."""
    if qual == '!':
        for y in range(topo_cab + 5, topo_cab + 9):
            px[(base_x + 11, y)] = '5'
            px[(base_x + 12, y)] = '5'
        px[(base_x + 11, topo_cab + 3)] = '5'
        px[(base_x + 12, topo_cab + 3)] = '5'
    elif qual == 'gota':
        for (x, y) in ((1, 0), (0, -1), (1, -1), (2, -1), (0, -2), (1, -2), (2, -2), (1, -3)):
            px[(base_x + x, topo_cab - 1 + y)] = '6'
        px[(base_x + 2, topo_cab - 2)] = '!'
    elif qual == '...':
        for x0 in (3, 6, 9):
            for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                px[(base_x + x0 + dx, topo_cab + 4 + dy)] = '5'
    elif qual == 'brilho':
        cx, cy = base_x + 13, topo_cab + 2
        px[(cx, cy)] = '!'
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            px[(cx + dx, cy + dy)] = '1'


# pose padrao: todos os campos que a montagem entende
POSE_BASE = dict(dx=0, dy=0, pernas='repouso', olhos='a', cabelo=0.0, capa=0.0,
                 lift=0.0, sobe=0.0, fase=0.0, brilho=None, saia=1.0, frente1=False,
                 tipo1=1, fusao=False, emote=None, mugetsu=False, hx=0, hy=0, luz=0.0, incl=0,
                 pernas_b=None, pt=0.0, vista='lado', cresce=1.0,
                 m1=(3, -5), a1=-40.0, c1=15, s1=None,
                 m2=None, a2=None, c2=15, s2=None)


# ═══════════════════════════════════════════════════════════════════
#  MONTAGEM EM TEXELS
#  As poses continuam na grade de sempre (unidades). O desenho e feito em
#  texels, 3 por unidade: rosto, mechas, dobras, maos e laminas com bem
#  mais detalhe e contorno fino. E = escala das medidas em texels que
#  foram pensadas na grade antiga de 2 por unidade.
# ═══════════════════════════════════════════════════════════════════
R = 3
E = R / 2.0
TW, TH = GW * R, GH * R


def ps_inteiro(v):
    """Tamanho da unidade (px de tela) -> multiplo de R mais proximo: os
    texels ficam todos do mesmo tamanho (pixel art de verdade)."""
    return max(R, R * int(round(v / float(R))))


def _t(v):
    """Unidade de pose -> texel (canto de baixo/esquerda da unidade)."""
    return int(math.floor(v * R + 1e-6))


def _up(px, t):
    """Desenho feito na grade de unidades -> blocos de R x R texels."""
    for (x, y), ch in t.items():
        X, Y = x * R, y * R
        for a in range(R):
            for b in range(R):
                px[(X + a, Y + b)] = ch


def _carimbo(px, mapa, x0, y_topo):
    for r, linha in enumerate(mapa):
        y = y_topo - r
        for c, ch in enumerate(linha):
            if ch != '.':
                px[(x0 + c, y)] = ch


def _m(linhas):
    """Mapa escrito em blocos de 10 colunas separados por '|' (so para
    facilitar contar as colunas na hora de desenhar)."""
    return [l.replace('|', '') for l in linhas]


def _intervalo(c0, c1, a, b):
    """Valores de t com a <= c0 + c1 * t <= b (None se nenhum)."""
    if abs(c1) < 1e-9:
        return (-1e9, 1e9) if a <= c0 <= b else None
    lo, hi = (a - c0) / c1, (b - c0) / c1
    return (lo, hi) if lo <= hi else (hi, lo)


def _varre(px, ox, oy, ux, uy, nx, ny, k0, k1, j0, j1, cor, evita=None):
    """Pinta o retangulo girado k0..k1 x j0..j1 (k ao longo de u, j ao
    longo de n, a partir de (ox, oy)) visitando so os texels de dentro:
    para cada coluna x, as linhas y que caem nas duas faixas. Sem buracos."""
    xs = [ox + ux * k + nx * j for k in (k0, k1) for j in (j0, j1)]
    for x in range(int(math.floor(min(xs))), int(math.ceil(max(xs))) + 1):
        dx = x - ox
        f1 = _intervalo(dx * ux, uy, k0, k1)
        if f1 is None:
            continue
        f2 = _intervalo(dx * nx, ny, j0, j1)
        if f2 is None:
            continue
        lo, hi = max(f1[0], f2[0]), min(f1[1], f2[1])
        if lo > hi:
            continue
        for y in range(int(math.ceil(oy + lo - 1e-9)), int(math.floor(oy + hi + 1e-9)) + 1):
            dy = y - oy
            ch = cor(dx * ux + dy * uy, dx * nx + dy * ny)
            if ch and (evita is None or px.get((x, y)) not in evita):
                px[(x, y)] = ch


_PARTES = OrderedDict()
_PARTES_MAX = 160


def _parte(px, chave, x, y, desenha):
    """Partes que so mudam de lugar (espada num angulo, cabelao numa forma):
    desenhadas uma vez na origem e depois so copiadas para (x, y)."""
    item = _PARTES.get(chave)
    if item is None:
        tmp = {}
        desenha(tmp)
        # guardado compacto (2 bytes por coordenada, 1 por cor): cabe muito
        # mais no celular do que uma tupla por pixel
        item = (array('h', [q[0] for q in tmp]), array('h', [q[1] for q in tmp]), ''.join(tmp.values()))
        _PARTES[chave] = item
        while len(_PARTES) > _PARTES_MAX:
            _PARTES.popitem(last=False)
    else:
        _PARTES.move_to_end(chave)
    for a, b, ch in zip(item[0], item[1], item[2]):
        px[(x + a, y + b)] = ch


def _girado(px, hx, hy, ux, uy, k0, k1, j0, j1, cor, evita=None):
    """Desenha um objeto girado (espadas, bainhas) sem buracos: cor(k, j)
    nas coordenadas do objeto - k ao longo da direcao (ux, uy), j ao longo
    da normal. None = vazio."""
    _varre(px, hx, hy, ux, uy, -uy, ux, k0, k1, j0, j1, cor, evita)


# ── cabeca 39 x 33: cabelo em 5 tons (sombra funda, base, meio, brilho e
#    reflexo), arco de brilho azulado quebrado nas mechas, franja em pontas
#    com os fios marcados; olho grande com cilio grosso e ponta, iris em 3
#    tons, pupila e brilho duplo; sombra da franja na testa
_CAB2 = _m([
    "..........|......J...|.......J..|.........",  # 0
    "..........|.....JHJ..|......JJ..|.........",  # 1
    "........J.|...JJHIJJ.|..JJHHJ...|.........",  # 2
    ".......JHJ|JJJHHIHHHJ|JJHHHHHJJ.|.........",  # 3
    "..JJJ.JHHH|HHHHHHHHHH|HHHHHHHHHH|JJ.......",  # 4
    "..JHHJHHHH|HHHHHHHHHH|HHHHHHHHHH|HHJ......",  # 5
    "JJHHHHHHHH|HHHHHHHHHH|HHHHHHHHHH|HHHJ.....",  # 6
    "JJHHHHHHHH|HHHHIIIIHI|IIIIIHHHHH|HHHHJ....",  # 7
    "..JHHHHHHH|HIIhhhhhIh|hUUhhIIHHH|HHHHHJ...",  # 8
    "JJHHHHHHHI|IhhIIIIIHI|IIIIhhIIHH|HHHHHHJ..",  # 9
    "..JJHHHHIh|hIIHHHHHHH|HHHHIIhhIH|HHHHHHHJJ",  # 10
    "..JJHHHHHI|IHHHHHHHHH|HHHHHHIIhI|HHHHHHHJJ",  # 11
    "JJHHJJHHHH|HHHHHHHHHH|HHHHHHHHII|IIHHHHHHJ",  # 12
    "JJHHJJHHHH|HHHHHHHHHH|JHHHHHHHHH|HhIHHHHHJ",  # 13
    "..JHJJHHHH|HHHHHHHHHJ|HHHHHHHJHH|HHHHHHHHH",  # 14
    "JJHHJJHHHH|HHHHHHHHJH|HHHHHHJHHH|HHHJHHHHH",  # 15
    "..JHHHJJHH|HHHHHHHJHH|HHHHHJHHHH|HHHJHHHHH",  # 16
    "..JHHHJJHH|HHHHHHJHHH|HHHHJHHHHH|HHJHHHHHH",  # 17
    "JJHHHHJJHH|HHHHHJHHHH|HHHHJHIIHH|HHJHHHHHH",  # 18
    "JJHHHHJJHH|HHHHJHHHHH|HHHJHIIHHH|HHJHHHHHH",  # 19
    "JJHHHHHHJH|HHHHssHHHS|SsssJHHHss|ssssssHHs",  # 20
    "JJHHHHHHHH|HHHHssHHss|EEEEEEHHss|SEEESSHHH",  # 21
    "JJHHHHHHHH|HHHHsSSSSE|eeEEnnSSSS|SeEnSSSSs",  # 22
    ".JHHHHHHHH|HHHsSSSSSS|e3EEn3SSSS|S3EeSSSSs",  # 23
    "..JJHHHHHH|HHssSSSSSS|33mmm3SSSS|S3m3SSSss",  # 24
    "..JJHHHHHH|HHssSSSSSS|SmmmmSSSSS|SmmSSSSss",  # 25
    "...JHHHHHH|HHsSSSSSSS|SssssSSSSS|SSSSSSssS",  # 26
    "...JHHHHHH|HsSSSSSSSS|SSSSSSSSSS|SSSsSS...",  # 27
    "....JJHHHH|ssSSSSSSSS|SSSSSSSSss|ssSSS....",  # 28
    "....JJHHHH|HsSSSSSSSS|SSSSSSSSSs|sSSS.....",  # 29
    "......JHHH|HHssSSSSSS|SSSSSSSSSS|Ss.......",  # 30
    ".......JHH|HHssSSSSSS|SSSSSSSSSS|SS.......",  # 31
    ".........J|HHHHssssSS|SSSSSSss..|.........",  # 32
])
_OLHO_CH = set('Een3mi9!')
_OLHOS = [(c, r) for r in range(20, 26) for c in list(range(19, 26)) + list(range(30, 35))]


def _cab2(trocas):
    c = [list(linha) for linha in _CAB2]
    for (col, r) in _OLHOS:                    # olhos limpos (pele)
        if c[r][col] in _OLHO_CH:
            c[r][col] = 'S'
    for (col, r), ch in trocas.items():
        c[r][col] = ch
    return [''.join(linha) for linha in c]


def _linha_olho(r, c0, texto):
    return {(c0 + i, r): ch for i, ch in enumerate(texto) if ch != '.'}


def _junta(*ds):
    out = {}
    for d in ds:
        out.update(d)
    return out


def _lo(*itens):
    """Varias linhas de olho: (linha, coluna, texto), ..."""
    return _junta(*(_linha_olho(r, c, t) for (r, c, t) in itens))


# de lado: olho da frente nas colunas 20-25 (ponta do cilio na 19), o de
# tras (3/4) nas colunas 31-33; boca na linha 28
_OLHO_ABERTO = _lo((21, 20, "EEEEEE"), (22, 19, "EeeEEnn"), (23, 20, "e3EEn3"), (24, 20, "33mmm3"),
                   (25, 21, "mmmm"), (21, 31, "EEE"), (22, 31, "eEn"), (23, 31, "3Ee"), (24, 31, "3m3"),
                   (25, 31, "mm"))
_SOBRANCELHA = _lo((20, 19, "EEEEE"), (20, 30, "EEE"))
_OLHO_SERIO = _lo((21, 19, "EEEEEEE"), (22, 20, "eeEEnn"), (23, 20, "33mmm3"),
                  (21, 31, "EEE"), (22, 31, "eEn"), (23, 31, "3m3"))
_CABECAS2 = {
    'a': _cab2(_OLHO_ABERTO),
    'f': _cab2(_lo((23, 19, "EEEEEEE"), (22, 20, "ssssss"), (23, 31, "EEE"), (22, 31, "sss"))),
    'b': _cab2(_lo((21, 20, "ssssss"), (22, 19, "EEEEEEE"), (23, 20, "eeEEnn"), (24, 20, "e3EEn3"),
                   (25, 20, "33mmm3"), (21, 31, "sss"), (22, 31, "EEE"), (23, 31, "eEn"), (24, 31, "3Ee"),
                   (25, 31, "3m3"))),
    's': _cab2(_junta(_SOBRANCELHA, _OLHO_SERIO)),
    'g': _cab2(_junta(_SOBRANCELHA, _OLHO_SERIO,
                      _lo((27, 27, "EEEE"), (28, 27, "ETTE"), (29, 27, "ETTE"), (30, 28, "EE")))),
    'l': _cab2(_junta(_SOBRANCELHA, _lo((21, 19, "EEEEEEE"), (22, 20, "99!!99"), (23, 20, "999999"),
                                        (21, 31, "EEE"), (22, 31, "9!9"), (23, 31, "999")))),
    'u': _cab2(_lo((20, 20, "EEEEEE"), (21, 20, "iieeii"), (22, 20, "ieEnei"), (23, 20, "ie3mei"),
                   (24, 20, "iimmii"), (20, 31, "EEE"), (21, 31, "iei"), (22, 31, "iEn"), (23, 31, "imi"),
                   (28, 28, "EE"), (29, 28, "TT"), (30, 28, "EE"))),
    'e': _cab2(_lo((21, 22, "EE"), (22, 21, "E..E"), (23, 20, "E....E"), (21, 32, "E"), (22, 31, "E.E"),
                   (28, 27, "tSSSt"), (29, 28, "ttt"))),
    # vitoria: olhos semicerrados (confiante) e meio sorriso de lado
    'v': _cab2(_lo((21, 20, "ssssss"), (22, 19, "EEEEEEE"), (23, 20, "eeEEnn"), (24, 20, "33mmm3"),
                   (21, 31, "sss"), (22, 31, "EEE"), (23, 31, "eEn"), (24, 31, "3m3"),
                   (28, 28, "SStS"), (29, 28, "ttSS"))),
}

# ── tronco 39 x 24: gola alta com a sombra no pescoco, abertura em V com a
#    camisa preta e a costura ciano, dobras do couro, cinto com passadores
#    e fivela de metal com reflexo
_TOR2 = _m([
    ".........2|CCCCctSSSS|StCCcccc..|.........",  # 0
    ".........2|CCCCctSSSS|StCCcccc..|.........",  # 1
    ".........2|CCCCcsSSSS|SsCCAAcc..|.........",  # 2
    ".........2|CCZZCZZZ44|4ZZZAAcc..|.........",  # 3
    ".........2|CCCZZZ4444|4ZZZAAcccc|.........",  # 4
    "........22|CCCCZZ4C44|4ZZZAAAccc|.........",  # 5
    "......222C|CCCCCCZZ44|4ZZCCCAAAA|cc.......",  # 6
    "......22CC|CCCCCCZZ44|4ZCCCCCAAA|ccc......",  # 7
    "......22CC|ccCCCCCZZ4|ZZCCCCCAAA|AAc......",  # 8
    "......22CC|ccCCCCCCZZ|ZZCCCCCAAA|AAc......",  # 9
    "......22CC|ccCCCCCCZZ|2CCCCC2AAA|AAc......",  # 10
    "......22CC|ccCCCCCCZZ|2CCCCC2AAA|AAc......",  # 11
    "......222C|ccCCCCCCZZ|2CCC22CAAA|AAc......",  # 12
    "......222C|ccCCCCCCZZ|2CCC22CAAA|AAc......",  # 13
    ".....22CCC|ccCCCCCCZZ|2C22CCCCAA|AAcc.....",  # 14
    "....22CCCC|ccCCCCCCZZ|2C22CCCCAA|AAccc....",  # 15
    "...22CCCCC|ccCCCCCCZZ|2CCC22CCAA|AAAccc...",  # 16
    "...22CCCCC|ccCCCCCCZZ|2CCC22CCAA|AAAccc...",  # 17
    "...2MKMMMM|MMMMMgGkkk|GgMMMMMMKM|MMMMcc...",  # 18
    "...2MgMMMM|MMMMMgK++k|KgMMMMMMgM|MMMMcc...",  # 19
    "...222MKMM|MMMMMgGkkk|GgMMMMMMKM|MMMMcc...",  # 20
    "...222CCCC|CCCCCPPPPP|PPPPCCCCCC|AAAccc...",  # 21
    "...222CCCC|CCCCC7PPPP|PPPPCCCCCC|AAAccc...",  # 22
    "...222CCCC|CCCCC7PPPP|PPP7CCCCCC|AAAccc...",  # 23
])
for _m_ in (_CAB2, _TOR2) + tuple(_CABECAS2.values()):
    assert all(len(_l) == 39 for _l in _m_), 'mapa com largura errada'


def _cabelo_tras2(px, cx, ty, cb, sobe, fase):
    """Mechas de tras em texels: R texels de grossura (brilho em cima,
    sombra embaixo), afinando ate a ponta; as de cima pegam o brilho."""
    dois_pi = 2 * math.pi
    amp = 0.35 + 0.28 * min(3.0, abs(cb)) + 0.35 * sobe
    for linha, base in ((2, 1), (3, 2), (4, 2), (5, 3), (6, 2), (7, 3), (8, 1)):
        comp = base + int(round(max(0.0, cb) * (0.5 + linha * 0.12))) + int(round(sobe * 1.4))
        caida = max(0.0, cb) * 0.25 * (linha - 4) / 4.0
        n2 = comp * R
        for i2 in range(n2):
            i = i2 / float(R)
            uu = (i + 1) / float(comp)
            onda = amp * uu * math.sin(dois_pi * (fase * 1.3 - i / 4.0 - linha * 0.1))
            ergue = sobe * (i + 1) * 0.6
            yy = -linha - ((caida if i > comp // 2 else 0) + onda - ergue)
            x = cx - 1 - i2
            y = ty + int(round(yy * R))
            resta = n2 - 1 - i2
            grossura = max(1, min(R + 1, resta + 1))      # afina na ponta (encosta na de baixo)
            for g in range(grossura):
                if g == 0:
                    if linha <= 3 and 1 <= i2 <= R + 1:
                        ch = 'I'
                    elif resta < R and linha in (3, 5):
                        ch = 'h'
                    else:
                        ch = 'H'
                elif g >= grossura - 1 and grossura > 1:
                    ch = 'J' if linha >= 5 else 'H'
                else:
                    ch = 'H'
                px[(x, y - g)] = ch


def _espetos2(px, cx, ty, cb, sobe, fase):
    """Fios espetados no topo: pontas que afinam, cada uma de uma altura,
    balancando; com o reiatsu elas crescem e deitam para tras (vento)."""
    dois_pi = 2 * math.pi
    fios = [(4, 0.0, 3), (8, 0.35, 2)]
    if sobe > 0.5:
        fios += [(2, 0.2, 2), (6, 0.6, 4), (10, 0.85, 3)]
    for bxx, fx, alto in fios:
        osc = 0.7 * math.sin(dois_pi * (fase + fx)) - min(1.0, max(0.0, cb) * 0.4)
        x = cx + int(round((bxx + osc) * R))
        alto = int(round((alto + sobe * 3 * (0.6 + 0.4 * math.sin(dois_pi * (fase * 1.5 + fx)))) * E))
        deita = 0.35 + 0.5 * sobe                        # tomba para tras com o vento
        for h in range(alto):
            xx = x - int(round(h * deita))
            larg = max(1, R - (h * R) // max(1, alto))    # afina na ponta
            for w in range(larg):
                if h == alto - 1:
                    ch = 'J'
                elif w == larg - 1 and h <= 1:
                    ch = 'I'
                else:
                    ch = 'H'
                px[(xx + w, ty + 1 + h)] = ch


def _cabelo_longo2(px, cx, ty, cb, sobe, fase, y_joelho, cresce=1.0):
    """Mugetsu: cabelao preto ate os joelhos - uma massa so, com os fios
    marcados, faixa de brilho azulado e pontas desiguais; ondula e, com o
    reiatsu, levanta e voa para tras. cresce (0..1) = quanto do comprimento
    ja cresceu (transformacao)."""
    dois_pi = 2 * math.pi
    vento = min(0.9, max(0.0, cb) * 0.2 + sobe * 0.5)
    ax, ay = cx + 9.0, ty - 5.0 * E                      # nasce na parte de tras da cabeca
    comp = max(6.0, ay - y_joelho) * max(0.06, min(1.0, cresce))
    th = 0.22 + vento * 1.05                             # inclinacao para tras
    dx, dy = -math.sin(th), -math.cos(th)
    nx, ny = math.cos(th), -math.sin(th)
    amp = (1.6 + 2.6 * sobe) * E
    # percorre os texels da caixa e acha (s ao longo, v de lado) de cada um:
    # sem buracos e bem mais leve que carimbar ponto a ponto
    ns = int(comp) + 2
    ond = [amp * (i / max(1.0, comp)) * math.sin(dois_pi * (fase * 1.2 - i / max(1.0, comp) * 1.6))
           for i in range(ns + 1)]
    hw_max = 7.0 + 2.2 + 1.0
    cantos = [(ax + dx * sv + nx * vv, ay + dy * sv + ny * vv)
              for sv in (0.0, comp) for vv in (-hw_max - amp, hw_max + amp)]
    x_a = int(math.floor(min(c[0] for c in cantos)))
    x_b = int(math.ceil(max(c[0] for c in cantos)))
    y_a = int(math.floor(min(c[1] for c in cantos)))
    y_b = int(math.ceil(max(c[1] for c in cantos)))
    for x in range(x_a, x_b + 1):
        rx = x - ax
        for y in range(y_a, y_b + 1):
            ry = y - ay
            sv = rx * dx + ry * dy
            if sv < 0 or sv > comp:
                continue
            i = int(sv)
            o = ond[i] + (ond[i + 1] - ond[i]) * (sv - i)
            v = rx * nx + ry * ny - o
            u = sv / comp
            hw = 7.0 + 2.2 * u                           # abre um pouco para baixo
            if v < -hw or v > hw:
                continue
            w = v / hw                                   # -1 (costas) .. 1 (frente)
            ponta = 1.0 - 0.13 * abs(math.sin(w * 7.3 + 1.1)) - (0.05 if w > 0.3 else 0.0)
            if u > ponta:
                continue
            fio = abs(((w + 1.0) * 2.6 + 0.35 * u) % 1.0 - 0.5)   # perto de 0.5 = entre duas mechas
            if u > ponta - 0.035:
                ch = 'J'
            elif w < -0.72:
                ch = 'I' if w < -0.86 else 'H'
            elif w > 0.8:
                ch = 'J'
            elif fio > 0.44:
                ch = 'J'                                 # separacao das mechas
            elif 0.16 < u < 0.23 and abs(w) < 0.62:
                ch = 'U' if (abs(u - 0.195) < 0.008 and -0.2 < w < 0.05) else ('h' if 0.18 < u < 0.21 else 'I')
            else:
                ch = 'H'
            px[(x, y)] = ch


def _rastro2(px, hx, hy, de, ang, comp):
    """Rastro do golpe (smear) em ARCO SOLIDO: o setor varrido pela lamina,
    da metade dela ate a ponta. Perto da lamina e na borda de fora fica
    claro e cheio; indo para o comeco do golpe vai ralando em xadrez (pixel
    art) ate sumir. Nao passa por cima do boneco nem da espada."""
    L = comp * R
    r0, r1 = L * 0.42, L + 1.5
    lo, hi = min(de, ang), max(de, ang)
    if hi - lo < 1:
        return
    ri = int(math.ceil(r1))
    r0q, r1q = r0 * r0, r1 * r1
    for ox in range(-ri, ri + 1):
        for oy in range(-ri, ri + 1):
            d2 = ox * ox + oy * oy
            if d2 < r0q or d2 > r1q:
                continue
            a = math.degrees(math.atan2(oy, ox))
            a = lo + (a - lo) % 360.0
            if a > hi:
                continue
            f = (a - de) / float(ang - de)                  # 0 = comeco do golpe, 1 = lamina
            rr = (math.sqrt(d2) - r0) / (r1 - r0)           # 0 = meio da lamina, 1 = ponta
            q = (hx + ox, hy + oy)
            if q in px:
                continue
            xadrez = (ox + oy) % 2 == 0
            if f < 0.3:
                ch = 'x' if (xadrez and rr > 0.55 and f > 0.08) else None
            elif rr > 0.84:
                ch = 'X'
            elif f > 0.72 or rr > 0.5:
                ch = 'X' if (f > 0.8 and rr > 0.55) else 'x'
            else:
                ch = 'x' if xadrez else None
            if ch:
                px[q] = ch


def _trancado(k, j, borda, fita='g', luz='k'):
    """Cabo trancado (tsuka-ito): fitas em X com losangos escuros no meio;
    borda clara de um lado, escura do outro."""
    kk, jj = int(math.floor(k + 0.5)), int(math.floor(j + 0.5))
    if jj >= borda:
        return luz if (kk + jj) % 4 == 0 else fita
    if jj <= -borda:
        return 'W'
    cruza = (kk + jj) % 4 == 0 or (kk - jj) % 4 == 0
    if cruza:
        return luz if (kk + jj) % 8 == 0 and (kk - jj) % 4 == 0 else fita
    return 'K'


def _katana2(px, hx, hy, ux, uy, nx, ny, comp, brilho):
    """Elucidator: cabo trancado em losangos, kashira, tsuba oval com aro,
    habaki com reflexo e lamina curva: costas claras (mune), miolo preto,
    aresta (shinogi), hamon ondulado, fio claro, reflexo e kissaki."""
    L = comp * R
    ini = 6
    sori = max(2.2, L * 0.13)
    ref = ini + int((L - ini) * 0.3)
    kb = None if brilho is None else ini + brilho * (L - ini)

    def cor(k, j):
        if k < 0.5 and abs(j) > 2.5:
            return None
        if k < -16.5:
            return 'k' if k > -17.6 else 'g'                   # kashira
        if k < 0.5:
            return _trancado(k, j, 2)
        if k < 3.5:                                            # tsuba oval com aro
            d = ((k - 2.0) / 1.6) ** 2 + (j / 6.4) ** 2
            if d > 1.0:
                return None
            if d > 0.62:
                return 'k' if j > 2 else 'g'
            return '+' if (j > 3.5 and k < 2) else 'K'
        if k < ini:                                            # habaki
            if -2.5 <= j <= 3.5:
                return '+' if j > 2.5 else 'k'
            return None
        if L < ini:
            return None
        u = (k - ini) / float(max(1, L - ini))
        jj = j + sori * u * u                                  # a lamina curva
        corta = max(0.0, k - (L - 6))                          # kissaki: as costas descem ate o fio
        if jj > 3.5 or jj < -3.5 + corta:
            return None
        jn = int(math.floor(jj + 0.5))
        if kb is not None and abs(k - kb) < 1.6 and jn >= 2:
            return '!' if jn >= 3 else '1'
        if jn >= 3:
            return '+' if (ref <= k <= ref + 3 or k >= L - 1.5) else 'w'
        if jn == 2:
            return 'w' if ref <= k <= ref + 3 else ('j' if math.sin(k * 0.55) > 0.1 else 'W')
        if jj < -2.5 + corta:
            return 'u'                                         # costas (mune)
        if jn == 0 and corta < 0.5:
            return 'K'                                         # aresta (shinogi)
        return 'W'
    _girado(px, hx, hy, ux, uy, -18.5, L + 0.5, -7.0, 7.0, cor)


def _repulser2(px, hx, hy, ux, uy, nx, ny, comp, brilho):
    """Dark Repulser: lamina reta de cristal com facetas em diagonal, fio
    claro, reflexo; guarda em cruz com pontas de cristal e gema; cabo curto
    com anel e pomo."""
    L = comp * R
    ref = 4 + int((L - 4) * 0.35)
    kb = None if brilho is None else 4 + brilho * (L - 4)

    def cor(k, j):
        kk, jn = int(math.floor(k + 0.5)), int(math.floor(j + 0.5))
        if k < -9.5:
            return 'Y' if abs(j) < 1.6 else None               # pomo
        if k < 0.5:
            if abs(j) > 1.6:
                return None
            return 'y' if kk % 4 == 0 else ('g' if jn >= 1 else 'K')
        if k < 3.5:                                            # guarda em cruz
            if abs(j) > 7.5:
                return None
            if abs(j) >= 5.5:
                return 'Y' if (k > 1.4 or abs(j) < 6.5) else None
            if abs(jn) <= 1:
                return 'n' if (jn == 1 and kk == 1) else 'r'
            return 'y'
        corta = max(0.0, k - (L - 4.5))
        if abs(j) > 3.4 - corta:
            return None
        if kb is not None and abs(k - kb) < 1.6 and jn >= 1:
            return '!' if jn >= 2 else '1'
        if jn >= 3 or (corta > 0.5 and jn >= 2):
            return '+' if ref <= k <= ref + 3 else 'r'
        if jn <= -3:
            return 'z'
        if (kk - 2 * jn) % 10 == 0:
            return 'Y'                                         # faceta
        if jn == -2:
            return 'y'
        if jn == 2:
            return 'Y' if kk % 9 in (2, 3, 4) else 'r'
        return 'r' if (jn == 0 and kk % 9 in (1, 2)) else 'R'
    _girado(px, hx, hy, ux, uy, -11.0, L + 1.5, -8.0, 8.0, cor)


_INF = []
for _i in range(160):                            # simbolo do infinito (lemniscata)
    _a = 2 * math.pi * _i / 160.0
    _d = 1 + math.sin(_a) ** 2
    _INF.append((math.cos(_a) / _d, math.sin(_a) * math.cos(_a) / _d))


def _fundida2(px, hx, hy, ux, uy, nx, ny, comp, brilho, evo, fase):
    """As duas espadas fundidas: lamina larga e pesada preta, com costas de
    aco, fio aceso em 3 degraus (cristal azul; evoluida: branco, azul e
    roxo), aresta central, veios de energia que correm pela lamina e guarda
    em cruz (evoluida: o simbolo do infinito). Cabo longo trancado."""
    L = comp * R
    ini = 9 if evo else 6
    fio, fio2, fio3 = ('!', 'f', 'F') if evo else ('r', 'R', 'z')
    mv = int(fase * 18)
    kb = None if brilho is None else ini + brilho * (L - ini)

    def cor(k, j):
        kk, jn = int(math.floor(k + 0.5)), int(math.floor(j + 0.5))
        if k < -18.5:
            if k < -21.0:
                return ('L' if evo else 'Y') if abs(j) < 0.6 else None
            return ('L' if evo else 'Y') if abs(j) < 3.1 else None
        if k < 0.5:
            if abs(j) > 2.5:
                return None
            return _trancado(k, j, 2, fita='F' if evo else 'y', luz='L' if evo else 'Y')
        if not evo and k < ini:                               # guarda em cruz
            if abs(j) > 9.5 or (abs(j) > 6.5 and not (1.5 < k < 3.5)):
                return None
            if abs(j) >= 7.5:
                return 'Y'
            if abs(jn) <= 1:
                return 'r'
            return 'k' if k < 1.5 else 'y'
        if evo and k < ini:
            return None
        corta = max(0.0, k - (L - 9))
        if j > 6.5 or j < -6.5 + corta:
            return None
        if kb is not None and abs(k - kb) < 1.6 and jn >= 1:
            return '!' if jn >= 3 else '1'
        if jn >= 6:
            return fio
        if jn == 5:
            return fio2
        if jn == 4:
            return fio3
        if j < -5.5 + corta:
            return 'u'
        if j < -4.5 + corta:
            return '2'                                         # chanfro das costas
        veia = int(round(1.6 * math.sin(k * 0.24 + 1.3))) - 2
        if jn == veia and (kk + mv) % 14 < (8 if evo else 5):
            return ('9' if (kk + mv) % 14 < 3 else 'V') if evo else 'z'
        if jn in (1, 2):
            return 'K' if jn == 1 else 'g'                     # aresta central (shinogi)
        return 'W'
    _girado(px, hx, hy, ux, uy, -22.0, L + 3.5, -10.0, 10.0, cor)
    if evo:
        def pp(k, j, ch):
            px[(int(round(hx + ux * k + nx * j)), int(round(hy + uy * k + ny * j)))] = ch
        for (cx, cy) in _INF:                                  # guarda: o infinito
            for dj in (-0.5, 0.0, 0.5):
                pp(4.0 + cy * 6.0, cx * 10.5 + dj, 'Y')
        for (cx, cy) in _INF[::4]:
            pp(4.0 + cy * 6.0 * 0.82, cx * 10.5 * 0.9, 'F')
        for j in (-6, 6):
            pp(4.0, j, '9')
        pp(4.0, 0, '!')
        pp(L + 2, 6, fio)
        pp(L + 3, 6, fio)


def _espada2(px, hx, hy, ang, comp, tipo, smear_de=None, brilho=None, fase=0.0):
    ang = float(round(ang))                        # grau inteiro: a lamina vira cache
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    if smear_de is not None and abs(smear_de - ang) > 8:
        _rastro2(px, hx, hy, smear_de, ang, comp)
    b = brilho if smear_de is None else None
    mv = int(fase * 18) if tipo >= 3 else 0

    def desenha(d):
        if tipo == 1:
            _katana2(d, 0, 0, ux, uy, nx, ny, comp, b)
        elif tipo == 2:
            _repulser2(d, 0, 0, ux, uy, nx, ny, comp, b)
        else:
            _fundida2(d, 0, 0, ux, uy, nx, ny, comp, b, tipo == 4, (mv + 0.5) / 18.0)
    _parte(px, ('esp', tipo, comp, ang, b, mv), hx, hy, desenha)


def _bainha2(px, bx, by):
    """Bainha (saya) da cintura: laca escura com filete claro em cima,
    reflexo, sombra embaixo e ponteira de metal. Nao passa por cima das
    pernas."""
    a = math.radians(_BAINHA_ANG)
    L = _BAINHA_COMP * R

    def cor(k, j):
        jn = int(math.floor(j + 0.5))
        if k > L:
            return 'k' if jn <= -2 else ('+' if (jn == -1 and k < L + 1.5) else 'g')
        if jn <= -2:
            return 'v'
        if jn == -1:
            return 'u' if 8 < k < 13 else 'W'                 # reflexo da laca
        if jn >= 1:
            return 'u'
        return 'W'
    _girado(px, bx, by, math.cos(a), math.sin(a), 0.0, L + 5.0, -2.4, 1.4, cor,
            evita=('P', 'B', '7', 'K', 'p', 'b', '%'))


def _cabo_cintura2(px, bx, by):
    """Cabo da Elucidator guardada: tsuba e cabo trancado para fora."""
    a = math.radians(_BAINHA_ANG)

    def cor(k, j):
        if k > -1.0:
            if abs(j) > 5.2:
                return None
            return 'k' if j <= -3 else ('g' if abs(j) >= 3 else 'K')
        if abs(j) > 2.5:
            return None
        if k < -16.0:
            return 'k'
        return _trancado(-k, -j, 2)
    _girado(px, bx, by, math.cos(a), math.sin(a), -17.5, 1.0, -5.5, 5.5, cor)


def _meia(v):
    return round(v * 2) / 2.0


def _ik(ax, ay, bx, by, la, lb, preferir):
    """Junta do meio (joelho/cotovelo) de uma corrente de 2 ossos que vai de
    (ax, ay) a (bx, by). preferir(c1, c2) escolhe o lado da dobra. Se nao
    alcanca, estica reto (proporcional)."""
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy) or 1e-6
    if d >= la + lb - 1e-6:
        k = la / float(la + lb)
        return ax + dx * k, ay + dy * k
    ca = max(-1.0, min(1.0, (la * la + d * d - lb * lb) / (2 * la * d)))
    a = math.acos(ca)
    base = math.atan2(dy, dx)
    c1 = (ax + math.cos(base + a) * la, ay + math.sin(base + a) * la)
    c2 = (ax + math.cos(base - a) * la, ay + math.sin(base - a) * la)
    return preferir(c1, c2)


def _tubo(px, a, b, raio, cor_fn):
    """Segmento grosso em texels: cor_fn(j, t) escolhe a cor pela distancia
    j (inteira) ao eixo (lado da luz positivo) e pelo ponto t (0..1) ao
    longo dele."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1e-6
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    if nx * -0.6 + ny * 0.8 < 0:                 # luz vem de tras/de cima
        nx, ny = -nx, -ny
    r = int(math.floor(raio + 0.01))

    def cor(k, j):
        jn = int(math.floor(j + 0.5))
        if jn < -r or jn > r:
            return None
        return cor_fn(jn, min(1.0, max(0.0, k / L)))
    _varre(px, a[0], a[1], ux, uy, nx, ny, -0.5, L + 0.5, -r - 0.5, r + 0.49, cor)


def _perna3(px, quad, joelho, pe, frente, no_ar):
    """Perna com volume: coxa e canela com luz/sombra e dobra no joelho,
    bota alta de couro com reflexo e fivela prateada, e o pe (no chao para a
    frente, com sola clara e biqueira de metal; no ar, em ponta)."""
    Q = (quad[0] * R, quad[1] * R)
    J = (joelho[0] * R, joelho[1] * R)
    P = (pe[0] * R, pe[1] * R)

    def calca(j, t):
        if frente:                                # luz / meio / base / sombra
            if j >= 3:
                return 'p'
            if j >= 1:
                return 'C'
            return 'P' if j >= -1 else '7'
        return 'C' if j >= 3 else ('P' if j >= 0 else '7')

    def coxa(j, t):
        if frente and t > 0.84 and -1 <= j <= 1:
            return '7'                            # vinco da calca em cima do joelho
        return calca(j, t)

    def canela(j, t):
        if t > 0.36:                              # cano alto da bota
            if 0.44 < t < 0.56:
                if t < 0.465 or t > 0.535:
                    return 'K'
                return 'k' if j >= 2 else 'G'     # fivela prateada
            if frente:
                if j >= 3:
                    return '%' if 0.6 < t < 0.9 else 'K'
                return 'K' if j >= 2 else ('b' if j >= -1 else 'B')
            return 'b' if j >= 2 else 'B'
        if t > 0.3:
            return 'K' if j >= 0 else 'B'         # boca da bota
        return calca(j, t)
    _tubo(px, Q, J, 2.5 * E, coxa)
    _tubo(px, J, P, 2.3 * E, canela)
    jx, jy = int(round(J[0])), int(round(J[1]))
    if frente:                                    # joelho marcado
        for (ox, oy) in ((1, 2), (2, 1), (3, 0)):
            px[(jx + ox, jy + oy)] = 'p'
    # pe
    if no_ar:
        ang = math.radians(-65)
        fim = (P[0] + math.cos(ang) * 5 * E, P[1] + math.sin(ang) * 5 * E)
        _tubo(px, P, fim, 1.8 * E, lambda j, t: 'k' if t > 0.82 else ('K' if j >= 1 else 'B'))
    else:
        x0, y0 = int(round(P[0])) - 4, int(round(P[1]))
        fim_x = (12, 12, 10, 8, 6, 6)             # o peito do pe desce ate a ponta
        corpo = 'b' if frente else 'B'
        for r, fx in enumerate(fim_x):
            for c in range(0, fx + 1):
                xx, yy = x0 + c, y0 + r
                if r == 0:
                    ch = 'K' if c <= 3 else 'g'   # salto escuro e sola clara
                elif c >= 9 and r <= 2:
                    ch = 'k' if (r == 1 and c == 11) else 'G'   # biqueira de metal
                elif c == fx or (r == len(fim_x) - 1):
                    ch = 'K'
                elif frente and ((c, r) in ((6, 3), (7, 2), (5, 4))):
                    ch = '%'                      # reflexo do couro
                else:
                    ch = corpo
                px[(xx, yy)] = ch


# ── vistas para o giro do corpo nos golpes: de frente (rosto e peito para
#    quem olha) e de costas (cabelo por tras, costura ciano nas costas)
_CAB_FRENTE = _m([
    "..........|.....J....|.....J....|.........",  # 0
    "..........|....JHJ...|....JHJ...|.........",  # 1
    "..........|..JJHIHJJ.|..JJHIHJJ.|.........",  # 2
    "..........|.JHHHIHHHJ|JJHHHIHHHJ|J........",  # 3
    ".......JJJ|HHHHHHHHHH|HHHHHHHHHH|HJJ......",  # 4
    "......JHHH|HHHHHHHHHH|HHHHHHHHHH|HHHJ.....",  # 5
    "....JJHHHH|HHHHHHIIII|IIIIIHHHHH|HHHHJJ...",  # 6
    "....JHHHHH|HHHIIIhhhh|hUUhhIIIHH|HHHHHJ...",  # 7
    "...JHHHHHH|HIIhhhIIII|IIIIhhhIIH|HHHHHHJ..",  # 8
    "...JHHHHHI|IhhIIHHHHH|HHHHHIIhhI|IHHHHHJJ.",  # 9
    "..JJHHHHHI|hIHHHHHHHH|HHHHHHHHIh|IHHHHHHJJ",  # 10
    "..JJHHHHHH|IHHHHHHHHH|HHHHHHHHHI|HHHHHHHJJ",  # 11
    "..JHHHHHHH|HHHHJHHHHH|HHHJHHHHHH|HHHHHHHHJ",  # 12
    "..JHHHHHHH|HHHHJHHHHH|HHHJHHHHHH|HHHHHHHHJ",  # 13
    "..JHHHHHHH|HHHJHHHHHJ|HHHHJHHHHH|HHIIHHHHJ",  # 14
    "..JHHHHHHH|HHHJHHHHHJ|HHHHJHHHHH|HHhIHHHHJ",  # 15
    "..JHHHHHHH|HHJHHHHHJH|JHHHHJHHHH|HHHHHHHHJ",  # 16
    "..JHHHHHHH|HHJHHHHHJH|JHHHHJHHHH|HHHHHHHHJ",  # 17
    "..JHHHHHHH|sJHHHHHJsH|sJHHHHJHHH|sHHHHHHHJ",  # 18
    "..JHHHHHHJ|sJHHHHHJss|sJHHHHJHHs|sHHHHHHHJ",  # 19
    "..JHHHHsSS|sJHHHHJsSS|SsJHHJssSS|SsHHHHHHJ",  # 20
    "..JHHHssSs|EEEEEEsSSS|SSSsEEEEEE|sSSsHHHHJ",  # 21
    "..JHHHssSS|eeEEnnSSSS|SSSSnnEEee|SSSsHHHHJ",  # 22
    "..JHHHssSS|e3EEn3SSSS|SSSS3nEE3e|SSSsHHHJJ",  # 23
    "..JJHHssSS|33mmm3SSSS|SSSS3mmm33|SSSsHHJJ.",  # 24
    "..JJHHssSS|SmmmmSSSSS|SSSSSmmmmS|SSSsHHJJ.",  # 25
    "...JHHssSS|SSssSSSSSS|sSSSSSssSS|SSssHHJ..",  # 26
    "...JHHHsSS|SSSSSSSSSS|SSSSSSSSSS|SSssHJ...",  # 27
    "....JJHHsS|SSSSSSSSSs|ssSSSSSSSS|SSsJJ....",  # 28
    "....JJHHss|SSSSSSSSSS|SSSSSSSSSS|SsJJ.....",  # 29
    "......JHss|SSSSSSSSSS|SSSSSSSSSS|ssJ......",  # 30
    ".......JHs|SSSSSSSSSS|SSSSSSSSSS|ss.......",  # 31
    ".........J|HHssssSSSS|SSSSssssJJ|.........",  # 32
])
_CAB_COSTAS = _m([
    "..........|.....J....|.....J....|.........",  # 0
    "..........|....JHJ...|....JHJ...|.........",  # 1
    "..........|..JJHIHJJ.|..JJHIHJJ.|.........",  # 2
    "..........|.JHHHIHHHJ|JJHHHIHHHJ|J........",  # 3
    ".......JJJ|HHHHHHHHHH|HHHHHHHHHH|HJJ......",  # 4
    "......JHHH|HHHHHHHHHH|HHHHHHHHHH|HHHJ.....",  # 5
    "....JJHHHH|HHHHHHIIII|IIIIIHHHHH|HHHHJJ...",  # 6
    "....JHHHHH|HHHIIIhhhh|hUUhhIIIHH|HHHHHJ...",  # 7
    "...JHHHHHH|HIIhhhIIII|IIIIhhhIIH|HHHHHHJ..",  # 8
    "...JHHHHHI|IhhIIHHHHH|HHHHHIIhhI|IHHHHHJJ.",  # 9
    "..JJHHHHHI|hIHHHHHHHH|HHHHHHHHIh|IHHHHHHJJ",  # 10
    "..JJHHHHHH|IHHHHHHHHH|HHHHHHHHHI|HHHHHHHJJ",  # 11
    "..JHHHHHJH|HHHHHHHHJJ|HHHHHHHHJJ|HHHHHHHHJ",  # 12
    "..JHHHHHJH|HHHHHHHHJH|HHHHHHHHJH|HHHHHHHHJ",  # 13
    "..JHHHHHJJ|HHHHHHHHJH|HHHHHHHJHH|HHIHHHHHJ",  # 14
    "..JHHHHHIJ|HHHHHHHHJH|HHHHHHHJHH|HHhIHHHHJ",  # 15
    "..JHHHHHHJ|HHHHHHHHHJ|HHHHHHJHHH|HHHHHHHHJ",  # 16
    "..JHHHHHHJ|JHHHHHHHHJ|HHHHHJIHHH|HHHHHHHJJ",  # 17
    "ssJHHHHHHI|JJHHHHHHHJ|HHHHHJHHHH|HHHHHHJJs",  # 18
    "ssJHHHHHHH|IJHHHHHHHJ|HHHHJHHHHH|HHHHHHJJs",  # 19
    "ssJHHHHHHH|HJHHHHHHHJ|HHHHJHHHHH|HHHHHHJJs",  # 20
    "..JHHHHHHH|HJHHHHHHHI|JHHHJHHHHH|HHHHHHJJ.",  # 21
    "..JHHHHHHH|JHHHHHHHHH|JHHHJHHHHH|HHHHHHJJ.",  # 22
    "..JJHHHHHH|JHHHHHHHHH|JHHHJHHHHH|HHHHHHJ..",  # 23
    "..JJHHHHHJ|HHHHHHHHHH|JHHHJHHHHH|HHHHJJ...",  # 24
    "...JHHHHHJ|HHHHHHHHHJ|HHHHHJHHHH|HHHHJJ...",  # 25
    "....HHHHJH|HHHHHHHHJH|HHHHHHJHHH|HHJJ.....",  # 26
    "....JJHHJH|HHJJHHHJHH|HHJJHHJHHH|JJJJ.....",  # 27
    "......JHHH|..JJHHtSSS|StHHHHJ.JH|HHJ......",  # 28
    "......JHHH|..JJHHsSSS|SsHHHH...J|HH.......",  # 29
    ".........J|....HHsSSS|SsHHJJ....|.........",  # 30
    ".........J|....JHsSSS|SsHH......|.........",  # 31
    "..........|.....sSSSS|Ss........|.........",  # 32
])
_TOR_COSTAS = _m([
    ".........2|CCCCCCCCCC|CCCCcccc..|.........",  # 0
    ".........2|CCCCCCCCCC|CCCCcccc..|.........",  # 1
    ".........2|CCCCCCCCCC|CCCCAAcc..|.........",  # 2
    ".........2|CCCCCCCCCZ|CCCCAAcc..|.........",  # 3
    ".........2|CCCCCCCCZZ|ZCCCAAcccc|.........",  # 4
    "........22|CCCCCCCCZZ|ZCCCAAAccc|.........",  # 5
    "......222C|CCCCCCCCZZ|ZCCCCCAAAA|cc.......",  # 6
    "......22CC|CCCCCCCCZZ|ZCCCCCCAAA|ccc......",  # 7
    "......22CC|ccCCCCCCZZ|ZCCCCCCAAA|AAc......",  # 8
    "......22CC|ccCCCCCCZZ|ZCCCCCCAAA|AAc......",  # 9
    "......22CC|ccCCC2CCZZ|ZC22CCCAAA|AAc......",  # 10
    "......22CC|ccCCC2CCZZ|ZC22CCCAAA|AAc......",  # 11
    "......222C|ccCC2CCCZZ|ZCCC22CAAA|AAc......",  # 12
    "......222C|ccCC2CCCZZ|ZCCC22CAAA|AAc......",  # 13
    ".....22CCC|ccCCCCCCZZ|ZCCCCCCCAA|AAcc.....",  # 14
    "....22CCCC|ccCCCCCCZZ|ZCCCCCCCAA|AAccc....",  # 15
    "...22CCCCC|ccCCCCCCZZ|ZCCCCCCCAA|AAAccc...",  # 16
    "...22CCCCC|ccCCCCCCZZ|ZCCCCCCCAA|AAAccc...",  # 17
    "...2MKMMMM|MMMMMMMKMM|MMMMMMMMKM|MMMMcc...",  # 18
    "...2MgMMMM|MMMMMMMgMM|MMMMMMMMgM|MMMMcc...",  # 19
    "...222MKMM|MMMMMMMKMM|MMMMMMMMKM|MMMMcc...",  # 20
    "...222CCCC|CCCCCCCCCC|CCCCCCCCCC|AAAccc...",  # 21
    "...222CCCC|CCCCCCCCCC|CCCCCCCCCC|AAAccc...",  # 22
    "...222CCCC|CCCCCCCCCC|CCCCCCCCCC|AAAccc...",  # 23
])
_OLHOS_F = [(c, r) for r in range(20, 26) for c in list(range(10, 16)) + list(range(24, 30))]


def _cab_f(trocas):
    c = [list(linha) for linha in _CAB_FRENTE]
    for (col, r) in _OLHOS_F:
        if c[r][col] in _OLHO_CH:
            c[r][col] = 'S'
    for (col, r), ch in trocas.items():
        c[r][col] = ch
    return [''.join(linha) for linha in c]


def _dois_olhos(linhas):
    """linhas = {r: 'xxxxxx'} -> mesmos olhos nos dois lados (de frente),
    o da direita espelhado (colunas 10-15 e 24-29)."""
    out = {}
    for r, txt in linhas.items():
        out.update(_linha_olho(r, 10, txt))
        out.update(_linha_olho(r, 24, txt[::-1]))
    return out


_OLHOS_F_ABERTOS = {21: "EEEEEE", 22: "eeEEnn", 23: "e3EEn3", 24: "33mmm3", 25: ".mmmm."}
_SOB_F = _lo((20, 17, "E"), (21, 16, "E"), (20, 21, "E"), (21, 23, "E"))
_OLHOS_F_SERIOS = {21: "EEEEEE", 22: "eeEEnn", 23: "33mmm3"}
_CABECAS_F = {
    'a': _cab_f(_dois_olhos(_OLHOS_F_ABERTOS)),
    'f': _cab_f(_dois_olhos({22: "ssssss", 23: "EEEEEE"})),
    'b': _cab_f(_dois_olhos({21: "ssssss", 22: "EEEEEE", 23: "eeEEnn", 24: "e3EEn3", 25: "33mmm3"})),
    's': _cab_f(_junta(_SOB_F, _dois_olhos(_OLHOS_F_SERIOS))),
    'g': _cab_f(_junta(_SOB_F, _dois_olhos(_OLHOS_F_SERIOS),
                       _lo((27, 18, "EEEE"), (28, 18, "ETTE"), (29, 18, "ETTE"), (30, 19, "EE")))),
    'l': _cab_f(_junta(_SOB_F, _dois_olhos({21: "EEEEEE", 22: "99!!99", 23: "999999"}))),
    'u': _cab_f(_junta(_dois_olhos({20: "EEEEEE", 21: "iieeii", 22: "ieEnei", 23: "ie3mei", 24: "iimmii"}),
                       _lo((28, 19, "EE"), (29, 19, "TT"), (30, 19, "EE")))),
    'e': _cab_f(_junta(_dois_olhos({21: "..EE..", 22: ".E..E.", 23: "E....E"}),
                       _lo((28, 18, "tSSSt"), (29, 19, "ttt")))),
    # vitoria: olhos semicerrados (confiante) e meio sorriso de lado
    'v': _cab_f(_junta(_dois_olhos({21: "ssssss", 22: "EEEEEE", 23: "eeEEnn", 24: "33mmm3"}),
                       _lo((28, 19, "SSt"), (29, 19, "tt")))),
}
for _m_ in (_CAB_FRENTE, _CAB_COSTAS, _TOR_COSTAS) + tuple(_CABECAS_F.values()):
    assert all(len(_l) == 39 for _l in _m_), 'vista com largura errada'


def _rosto_mugetsu(mapa):
    """Rosto na forma Mugetsu: sombra funda da franja caindo por cima dos
    olhos (a pele logo abaixo do cabelo escurece em 2 degraus), olhos em
    brasa (a iris inteira acesa, com o miolo claro) e reflexo roxo do fogo
    na borda do rosto."""
    c = [list(l) for l in mapa]
    H, W = len(c), len(c[0])
    cab = set('HJIhU')
    pele = set('Ss')
    for r in range(H):
        for col in range(W):
            ch = c[r][col]
            if ch in pele:
                if r >= 1 and mapa[r - 1][col] in cab:
                    c[r][col] = '~'
                elif r >= 2 and mapa[r - 2][col] in cab:
                    c[r][col] = 't'
                elif r >= 3 and mapa[r - 3][col] in cab and ch == 'S':
                    c[r][col] = 's'
                elif any(not (0 <= r + vy < H and 0 <= col + vx < W) or mapa[r + vy][col + vx] == '.'
                         for vx, vy in ((1, 0), (-1, 0), (0, 1))):
                    c[r][col] = '^'                  # borda do rosto: luz do fogo
    # brasa: um risquinho de luz sai do canto de fora de cada olho
    olho = set('Ee3mn')
    linhas_olho = [r for r in range(H) if any(ch in '3m' for ch in mapa[r])]
    if linhas_olho:
        r = linhas_olho[0]
        cols = [col for col in range(W) if mapa[r][col] in olho]
        grupos = []
        for col in cols:
            if grupos and col - grupos[-1][-1] <= 1:
                grupos[-1].append(col)
            else:
                grupos.append([col])
        meio = W / 2.0
        for g in grupos:
            if len(g) < 3:
                continue                             # o olho de tras (3/4) fica sem risco
            fora = -1 if (g[0] + g[-1]) / 2.0 < meio or len(grupos) == 1 else 1
            ponta = g[0] if fora < 0 else g[-1]
            for i, ch in enumerate('Vo8'):
                col = ponta + fora * (i + 1)
                if 0 <= col < W and c[r][col] != '.':
                    c[r][col] = ch
    return [''.join(l) for l in c]


_CABECAS2_M = {k: _rosto_mugetsu(v) for k, v in _CABECAS2.items()}
_CABECAS_F_M = {k: _rosto_mugetsu(v) for k, v in _CABECAS_F.items()}


def olhos_texel(p):
    """Centro dos olhos (texels, sem espelho) na pose - para o brilho e o
    rastro de luz dos olhos na forma Mugetsu. De costas: nenhum."""
    vista = p.get('vista', 'lado')
    if vista == 'costas':
        return []
    dx, dy = _meia(p['dx']), _meia(p['dy'])
    topo = _PES + _alt_pernas(p) + dy + len(_TRONCO) - 1
    incl = int(round(p.get('incl', 0) or 0))
    cab_x = _t(_X0 + dx + incl) + int(round(p.get('hx', 0) or 0))
    cab_ty = _t(topo + len(_CABECA)) + R - 1 + int(round(p.get('hy', 0) or 0))
    cols = (12.5, 26.5) if vista == 'frente' else (22.5, 32.0)
    return [(cab_x + c, cab_ty - 23) for c in cols]

def _pernas3(px, p, hip_x, hip_y):
    """As duas pernas (a de tras primeiro). Pes no chao ficam no chao e os
    joelhos dobram para a frente, calculados a cada pose."""
    nome, nome_b = p['pernas'], p.get('pernas_b')
    pt = p.get('pt', 0.0) or 0.0

    def pes(nm):
        P = _PERNAS_P[nm]
        out = []
        for k in ('f', 'b'):
            ox, oy = P[k]
            out.append((hip_x + ox, hip_y + oy) if P['ar'] else (hip_x + ox, float(_PES)))
        return out, P['ar']
    (pf, pb), ar = pes(nome)
    if nome_b:
        (pf2, pb2), ar2 = pes(nome_b)

        def passo(a, b):
            x = a[0] + (b[0] - a[0]) * pt
            y = a[1] + (b[1] - a[1]) * pt
            anda = abs(b[0] - a[0])
            if anda > 0.8 and not ar and not ar2:          # levanta o pe no meio do passo
                y += math.sin(math.pi * pt) * min(2.2, anda * 0.45)
            return (x, y)
        pf, pb = passo(pf, pf2), passo(pb, pb2)
        ar = ar2 if pt >= 0.5 else ar
    frente_primeiro = lambda c1, c2: c1 if c1[0] >= c2[0] else c2      # joelho para a frente
    for (qx, pe, frente) in ((hip_x - 1.3, pb, False), (hip_x + 1.3, pf, True)):
        quad = (qx, hip_y - 0.3)
        joelho = _ik(quad[0], quad[1], pe[0], pe[1] + 0.6, _COXA, _CANELA, frente_primeiro)
        # a perna so muda de lugar: guarda o desenho relativo ao texel do pe
        bx, by = int(math.floor(pe[0] * R)), int(math.floor(pe[1] * R))
        q4 = lambda v, o: int(round((v * R - o) * 4))
        chave = ('perna', q4(quad[0], bx), q4(quad[1], by), q4(joelho[0], bx), q4(joelho[1], by),
                 q4(pe[0], bx), q4(pe[1], by), frente, ar)
        rel = lambda c: ((c[0] * R - bx) / float(R), (c[1] * R - by) / float(R))
        _parte(px, chave, bx, by,
               lambda d, a=rel(quad), b=rel(joelho), c=rel(pe), f=frente, r=ar: _perna3(d, a, b, c, f, r))


def _painel(px, linhas, cor_fn):
    """Preenche um pedaco de pano: linhas = [(y, x0, x1), ...] em texels."""
    chao = _PES * R
    for (y, a, b, kk, total) in linhas:
        if y < chao:
            continue                              # o pano nao atravessa o chao
        if b < a:
            a, b = b, a
        for x in range(a, b + 1):
            ch = cor_fn(x, y, a, b, kk, total)
            if ch:
                px[(x, y)] = ch


def _painel_rasgado(px, linhas, cor_fn, kk_ini, fase, vento):
    """Como _painel, mas da linha kk_ini para baixo o pano vira TIRAS
    rasgadas: cada tira (R texels) tem o seu comprimento, algumas tem um vao
    do lado e cada uma balanca sozinha, mais na ponta. A barra de cada tira
    ganha o friso (que brilha na forma Mugetsu)."""
    chao = _PES * R
    dois_pi = 2 * math.pi
    for (y, a, b, kk, total) in linhas:
        if b < a:
            a, b = b, a
        d = kk - kk_ini
        for x in range(a, b + 1):
            if d < 0:
                if y >= chao:
                    ch = cor_fn(x, y, a, b, kk, total)
                    if ch:
                        px[(x, y)] = ch
                continue
            rel = x - a
            h = math.sin((rel // R) * 12.9898 + 78.233) * 43758.5453
            h -= math.floor(h)                                 # 0..1, fixo por tira
            tot = total - int(R * (0.3 + 3.4 * h))             # cada tira de um tamanho
            if kk >= tot:
                continue
            if rel % R == R - 1 and d > R and h > 0.4:
                continue                                       # vao entre as tiras
            dx = int(round(math.sin(dois_pi * (fase * 1.5 + h) - d * 0.12) * d / float(R) * (0.35 + 0.3 * h)
                           - vento * d * 0.1))
            if y < chao:
                continue
            ch = cor_fn(x, y, a, b, kk, tot)
            if ch:
                px[(x + dx, y)] = ch


def _casaco3(px, base, y0, capa, lift, fase, saia, parte, rasgado=False):
    """Sobretudo com silhueta propria (texels). parte='tras': a aba de tras
    que abre em DUAS caudas longas ate o tornozelo e voa com o vento;
    parte='frente': a aba da frente ate o joelho, aberta (as pernas aparecem).
    Bordas com costura ciano, forro, dobras que andam com o pano, barra.
    rasgado (forma Mugetsu): sobretudo longo ate o chao, com a barra em
    tiras rasgadas voando e um friso aceso na borda."""
    dois_pi = 2 * math.pi
    amp = 0.75 + 0.25 * min(3.0, abs(capa))       # balanca um pouco mesmo sem vento
    vento = max(-1.0, min(1.6, capa))
    mv = int(fase * 8 * E)
    top = _t(y0) + R - 1

    def dobra(x, kk):
        return (x + kk + mv) % 10

    if parte == 'frente':
        n = int((8.0 if rasgado else 5.0) * R)
        linhas = []
        for kk in range(n):
            k = kk / float(R)
            onda = amp * (k / 5.0) * math.sin(dois_pi * (fase - k / 5.0))
            y = top - kk + int(round(lift * k * 0.28 * R))
            a = _t(base + 9.4 + 0.25 * k * saia - vento * 0.2 * k)
            b = _t(base + 12.0 + 0.5 * k * saia - vento * 0.3 * k - onda * 0.5) + 1
            linhas.append((y, a, b, kk, n))

        def cor(x, y, a, b, kk, total):
            if kk >= total - 2:
                return 'c' if kk == total - 2 else '2'
            if x == b:
                return 'c'
            if x == a:
                return 'Z'                         # costura ciano na abertura
            if x <= a + 2:
                return 'q'                         # forro
            d = dobra(x, kk)
            return '2' if d == 0 else ('A' if d in (1, 2) else 'C')
        if rasgado:
            _painel_rasgado(px, linhas, cor, int(4.0 * R), fase + 0.37, vento)
        else:
            _painel(px, linhas, cor)
        return

    # aba de tras: ate k=3.5 inteira; depois se divide em duas caudas
    n1 = int(3.5 * R)
    n_ext, n_int = (int(13.0 * R), int(12.0 * R)) if rasgado else (int(11.0 * R), int(9.5 * R))
    linhas_ext, linhas_int = [], []
    for kk in range(n_ext):
        k = kk / float(R)
        u = k / 11.0
        onda = amp * u * math.sin(dois_pi * (fase - k / 9.0))
        onda2 = amp * u * math.sin(dois_pi * (fase - k / 9.0 - 0.3))
        y = top - kk + int(round(lift * k * 0.30 * R))
        ven = vento * 0.55 * k                      # as caudas voam mais que o resto
        x_esq = base + 0.8 - 0.35 * k * saia - ven - onda
        x_dir = base + 4.6 - 0.12 * k - ven * 0.6
        if kk < n1:
            linhas_ext.append((y, _t(x_esq), _t(x_dir) + 1, kk, n_ext))
        else:
            abre = min(1.0, (k - 3.5) / 2.0)          # o vao entre as caudas abre para baixo
            meio = x_esq + (x_dir - x_esq) * 0.46
            linhas_ext.append((y, _t(x_esq), _t(meio - 0.5 * abre), kk, n_ext))
            if kk < n_int:
                y2 = top - kk + int(round(lift * k * 0.22 * R))
                linhas_int.append((y2, _t(meio + 0.7 * abre - onda2 * 0.6 + ven * 0.15),
                                   _t(x_dir - onda2 * 0.3) + 1, kk, n_int))

    def cor_tras(x, y, a, b, kk, total):
        if kk >= total - 2:
            return 'Z' if kk == total - 2 else '2'   # barra com friso ciano
        if x == a:
            return 'c'
        if x == a + 1:
            return 'A'
        if rasgado and x == a + 3 and kk > R:
            return 'Z'                             # friso aceso na borda
        if kk >= n1 and x >= b - 2:
            return 'q'                             # forro aparecendo no vao
        d = dobra(x, kk)
        return '2' if d == 0 else ('A' if d == 1 else 'C')

    def cor_int(x, y, a, b, kk, total):
        if kk >= total - 2:
            return 'Z' if kk == total - 2 else '2'
        if x <= a + 2:
            return 'q'                             # forro da cauda de dentro
        return '2' if dobra(x, kk) == 0 else 'C'
    if rasgado:
        _painel_rasgado(px, linhas_int, cor_int, int(7.0 * R), fase + 0.5, vento)
        _painel_rasgado(px, linhas_ext, cor_tras, int(7.5 * R), fase, vento)
    else:
        _painel(px, linhas_int, cor_int)          # a cauda de dentro fica atras
        _painel(px, linhas_ext, cor_tras)


def _bainha_costas(px, x, y):
    """Dark Repulser guardada nas costas, na diagonal: o cabo com a guarda
    de cristal aparece por cima do ombro; a bainha desce por tras."""
    X, Y = x * R, y * R

    def reta(ang, comp, j0, j1, fn):
        a = math.radians(ang)
        _girado(px, X, Y, math.cos(a), math.sin(a), 0.0, comp, j0, j1, fn)

    def bainha(k, j):
        if k > 36:
            return 'k' if j < 0 else 'g'
        if int(k) % 13 in (6, 7):
            return 'G'                            # anel de metal
        return 'v' if j > 0.8 else ('u' if -0.3 < j < 0.3 and 10 < k < 16 else 'W')

    def cabo(k, j):
        if k > 13.5:
            return 'Y' if abs(j) < 0.8 else None
        return 'y' if int(k) % 4 == 1 else ('g' if j > 0.5 else 'K')
    reta(292, 39, -1.5, 1.5, bainha)
    reta(122, 15, -1.2, 1.2, cabo)

    def guarda(k, j):
        if abs(j) >= 4.5:
            return 'Y'
        return 'r' if abs(j) < 0.8 else 'y'
    reta(122, 2.4, -6.4, 6.4, guarda)


def _braco3(px, sx, sy, hx, hy, frente=False, bracadeira=False, faixas=False, fase=0.0):
    """Braco com cotovelo (IK): manga larga com vinco, antebraco mais fino,
    cotovelo arredondado, punho prateado; o da espada leva a bracadeira de
    metal com a linha ciano e reflexo. Mao fechada. O desenho do braco e
    guardado (so muda de lugar); o contorno escuro por cima do corpo e
    feito aqui, porque depende do que ja esta desenhado."""
    fs = round(fase, 2) if faixas else 0.0
    meu = {}
    _parte(meu, ('braco', hx - sx, hy - sy, frente, bracadeira, faixas, fs), sx, sy,
           lambda d: _braco3_desenho(d, 0, 0, hx - sx, hy - sy, frente, bracadeira, faixas, fs))
    if frente:                                     # contorno escuro por cima do corpo
        for (x, y) in meu:
            for vx, vy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + vx, y + vy)
                if q not in meu and px.get(q) in _CORPO:
                    px[q] = 'N'
    px.update(meu)


def _braco3_desenho(meu, sx, sy, hx, hy, frente, bracadeira, faixas, fase):
    LA, LB = 4.4 * R, 4.4 * R
    abaixo = lambda c1, c2: c1 if c1[1] <= c2[1] else c2                # cotovelo para baixo
    ex, ey = _ik(sx, sy, hx, hy, LA, LB, abaixo)
    luz, base_c, sombra = ('c', 'A', 'C') if frente else ('c', 'C', '2')

    def manga(j, t):
        if j >= 3:
            return luz
        return base_c if j >= -1 else sombra

    def braco(j, t):
        if 0.62 < t < 0.7 and j <= 1:
            return sombra                          # vinco da manga
        return manga(j, t)

    lb = math.hypot(hx - ex, hy - ey)

    def antebraco(j, t):
        if faixas and t < 0.84:                    # faixas enroladas (forma Mugetsu)
            if t < 0.1:
                return base_c
            if (int(t * lb) + j) % 4 == 0:
                return 'W'
            return 'g' if j >= 2 else 'u'
        if bracadeira and 0.28 < t < 0.8:
            if t < 0.34 or t > 0.74:
                return 'K'
            if j == 0:
                return 'Z'
            if j >= 2:
                return '+' if 0.45 < t < 0.55 else 'k'
            return 'G' if j >= -1 else 'g'
        if t > 0.82:
            return 'k' if j >= 1 else 'G'           # punho
        return manga(j, t)
    _tubo(meu, (sx, sy), (ex, ey), 2.4 * E, braco)
    for ox in range(-3, 4):                        # cotovelo
        for oy in range(-3, 4):
            if ox * ox + oy * oy <= 10:
                meu[(int(round(ex)) + ox, int(round(ey)) + oy)] = base_c
    _tubo(meu, (ex, ey), (hx, hy), 2.0 * E, antebraco)
    for ox in range(-3, 4):                        # ombro
        for oy in range(-3, 4):
            if ox * ox + oy * oy <= 11:
                meu[(sx + ox, sy + oy)] = luz if (oy >= 2 or (oy >= 1 and ox <= -1)) else base_c
    if faixas:                                     # ponta solta da faixa, voando para tras
        dois_pi = 2 * math.pi
        for (oy, fx) in ((1, 0.0), (-1, 0.4)):
            for i in range(int(4 * R)):
                x = int(round(hx - 3 - i))
                y = int(round(hy + oy + math.sin(dois_pi * (fase * 2.0 + fx) - i * 0.5) * i * 0.22))
                meu.setdefault((x, y), 'W' if i % 5 == 4 else 'u')


# ombreira de metal escuro (forma Mugetsu), em cima do ombro da frente:
# domo com reflexo, duas laminas e friso roxo aceso
_OMBREIRA = [
    "....uuuuu....",
    "..uugggkk+u..",
    ".ugggggggkku.",
    "uggggggggggku",
    "uuuuuuuuuuuuu",
    "oVoooooooVoo.",
    ".ugggggggku..",
    "..uuuuuuuu...",
    "...ooooooo...",
]


def _ombreira(px, sx, sy):
    _carimbo(px, _OMBREIRA, sx - 6, sy + 5)


def _mao(px, hx, hy, metal=False):
    """Mao fechada no cabo: luva com os dedos marcados, nos claros (de metal
    na mao da espada) e o polegar por cima."""
    for ox in range(-2, 4):
        for oy in range(-2, 4):
            if (ox in (-2, 3)) and (oy in (-2, 3)):
                continue                           # cantos arredondados
            px[(hx + ox, hy + oy)] = 'M'
    no = 'k' if metal else 'g'
    for ox in range(-1, 3):
        px[(hx + ox, hy + 3)] = no                 # nos dos dedos
        px[(hx + ox, hy + 2)] = 'K' if ox in (0, 2) else 'M'
    if metal:
        px[(hx, hy + 3)] = '+'
    px[(hx + 3, hy + 1)] = 'K'                     # polegar
    px[(hx + 3, hy)] = 'K'
    px[(hx + 2, hy + 1)] = 'g'
    px[(hx - 2, hy + 1)] = '%'                     # reflexo do couro


def montar(p, rapido=False):
    """Pose (dict, em unidades) -> {(x, y) em texels: cor}. rapido=True:
    so o desenho cru (sem luz, cores da forma Mugetsu e contorno) - basta
    para medir o tamanho da pose."""
    px = {}
    dx, dy = _meia(p['dx']), _meia(p['dy'])
    hip_y = _PES + _alt_pernas(p) + dy                     # quadril (unidades)
    topo = hip_y + len(_TRONCO) - 1                          # linha de cima do tronco
    base = _X0 + dx
    incl = int(round(p.get('incl', 0) or 0))
    fase = p.get('fase', 0.0) or 0.0
    cb = p['cabelo']
    sobe = max(0.0, min(1.2, p.get('sobe', 0.0) or 0.0))
    top_t = _t(topo) + R - 1
    bx_t = _t(base)
    o1 = (_t(base + 9 + incl) + 1, _t(topo - 2) + 1)
    o2 = (_t(base + 3 + incl) + 1, _t(topo - 2) + 1)
    cab_x = _t(base + incl) + int(round(p.get('hx', 0) or 0))
    cab_ty = _t(topo + len(_CABECA)) + R - 1 + int(round(p.get('hy', 0) or 0))
    boca = (_t(base + 9) + 1, _t(topo - 6) + 1)                # boca da bainha (cinto)
    mugetsu = p.get('mugetsu', False)
    saia = p.get('saia', 1.0)

    def mao(ombro_u, m):
        return (int(round(R * (ombro_u[0] + m[0]))) + 1, int(round(R * (ombro_u[1] + m[1]))) + 1)

    if mugetsu:
        cb_q, sobe_q = round(cb * 4) / 4.0, round(sobe * 4) / 4.0
        cr = round(p.get('cresce', 1.0), 2)
        alto = cab_ty - R * (_PES + 4)
        _parte(px, ('cab', cb_q, sobe_q, fase, cr, alto), cab_x, cab_ty,
               lambda d: _cabelo_longo2(d, 0, 0, cb_q, sobe_q, fase, -alto, cr))

    if p['a2'] is None and not p.get('fusao'):
        _bainha_costas(px, base + 1.2 + incl, topo + 1.0)

    m2 = p['m2'] if p['m2'] is not None else (-1, -6)
    h2 = mao((base + 3 + incl, topo - 2), m2)
    ergue2 = m2[1] > 4
    acima2 = m2[1] > 10

    def _braco_tras():
        _braco3(px, o2[0], o2[1], h2[0], h2[1], frente=ergue2, faixas=mugetsu, fase=fase + 0.3)
        if p['a2'] is not None:
            _espada2(px, h2[0], h2[1], p['a2'], int(p['c2']), 2, p['s2'], p.get('brilho'), fase)
        _mao(px, h2[0], h2[1])
    if not ergue2:
        _braco_tras()

    _cabelo_tras2(px, cab_x, cab_ty, cb, sobe, fase)
    if sobe > 0.3:
        _espetos2(px, cab_x, cab_ty, cb, sobe, fase)

    if ergue2 and not acima2:
        _braco_tras()

    _casaco3(px, base, topo - len(_TRONCO), p['capa'], p['lift'], fase, saia, 'tras', mugetsu)
    _pernas3(px, p, _X0 + 6.5, hip_y)
    _bainha2(px, boca[0], boca[1])
    _casaco3(px, base, topo - len(_TRONCO), p['capa'], p['lift'], fase, saia, 'frente', mugetsu)
    vista = p.get('vista', 'lado')
    tronco = _TOR_COSTAS if vista == 'costas' else _TOR2
    for r, linha in enumerate(tronco):
        desl = R * incl if r < 3 * R else (int(round(R * incl / 2.0)) if r < 5 * R else 0)
        y = top_t - r
        for c, ch in enumerate(linha):
            if ch != '.':
                px[(bx_t + desl + c, y)] = ch
    if vista == 'costas':
        if p['a2'] is None and not p.get('fusao'):
            _bainha_costas(px, base + 5.5 + incl, topo + 0.5)   # a espada nas costas, a mostra
    else:
        t = {}
        _alca_peito(t, int(round(base + incl)), int(round(topo)))
        _up(px, t)

    m1 = p['m1']
    ergue = m1 is not None and m1[1] > 4 and not p.get('frente1')

    def _braco_frente():
        if m1 is None:
            return
        h1 = mao((base + 9 + incl, topo - 2), m1)
        _braco3(px, o1[0], o1[1], h1[0], h1[1], frente=True, bracadeira=not mugetsu,
                faixas=mugetsu, fase=fase)
        if mugetsu:
            _ombreira(px, o1[0], o1[1])
        if p['a1'] is not None:
            _espada2(px, h1[0], h1[1], p['a1'], int(p['c1']), p.get('tipo1', 1), p['s1'],
                     p.get('brilho'), fase)
        _mao(px, h1[0], h1[1], metal=True)
    if ergue:
        _braco_frente()
    if vista == 'costas':
        cabeca = _CAB_COSTAS
    elif vista == 'frente':
        caras = _CABECAS_F_M if mugetsu else _CABECAS_F
        cabeca = caras.get(p['olhos'], caras['a'])
    else:
        caras = _CABECAS2_M if mugetsu else _CABECAS2
        cabeca = caras.get(p['olhos'], caras['a'])
    _carimbo(px, cabeca, cab_x, cab_ty)
    if acima2:
        _braco_tras()
    if p['a1'] is None:
        _cabo_cintura2(px, boca[0], boca[1])
    if not ergue:
        _braco_frente()
    if p.get('emote'):
        t = {}
        _emote(t, p['emote'], int(round(base + incl)), int(round(topo + len(_CABECA))))
        _up(px, t)

    if rapido:
        return px
    luz = p.get('luz', 0.0) or 0.0
    if luz > 0.2:
        _iluminar(px, luz, R)
    if luz >= 0.5:                                           # costuras acendem no golpe
        for q, ch in list(px.items()):
            if ch == 'Z':
                px[q] = '9'
    if mugetsu:
        for q, ch in list(px.items()):
            if ch in _SOMBRA:
                px[q] = _SOMBRA[ch]
    # contorno de 1 texel: escuro; o ciano fica so como luz de fundo, do
    # lado de tras e em cima (roxo na forma Mugetsu)
    aro = 'o' if mugetsu else 'O'
    novos = {}

    def fora(q, vx, vy):
        # vao interno (entre perna e casaco, por ex.) nao e borda de fora:
        # olhando mais uns texels na mesma direcao ainda ha boneco
        for i in range(1, 2 * R + 2):
            if (q[0] + vx * i, q[1] + vy * i) in px:
                return False
        return True
    for (x, y) in list(px.keys()):
        if px[(x, y)] in _SEM_CONTORNO:
            continue
        for vx, vy in ((-1, 0), (0, 1), (1, 0), (0, -1)):
            q = (x + vx, y + vy)
            if q not in px:
                ch = aro if ((vx == -1 or vy == 1) and fora(q, vx, vy)) else 'N'
                if novos.get(q) != aro:
                    novos[q] = ch
    px.update(novos)
    return px


def bordas(px):
    """Pontos do contorno do corpo (em texels) de onde o fogo da Bankai sobe:
    as bordas de cima e dos lados (sem as laminas)."""
    corpo = set(q for q, ch in px.items() if ch in _CORPO_M)
    out = []
    for (x, y) in corpo:
        if (x, y + 1) not in corpo or (x - 1, y) not in corpo or (x + 1, y) not in corpo:
            out.append((x, y))
    return out


def pose(**kw):
    p = dict(POSE_BASE)
    p.update(kw)
    return p


def _chave(p):
    passo_f = 2.0 if p.get('mugetsu') else 4.0

    def r(k, v):
        if k == 'pt':
            return round(v * 8) / 8.0
        if k in ('capa', 'cabelo', 'lift', 'sobe'):
            return round(v * passo_f) / passo_f  # fisica: passos de 0.25 (Mugetsu: 0.5)
        if k in ('dx', 'dy'):
            return round(v * 2) / 2.0            # meio passo (1 texel)
        if k in ('hx', 'hy', 'incl'):
            return int(round(v))
        if isinstance(v, float):
            return round(v, 1)
        if isinstance(v, tuple):
            return tuple(round(x * 2) / 2.0 for x in v)
        return v
    return tuple((k, r(k, p[k])) for k in sorted(p))


# ═══════════════════════════════════════════════════════════════════
#  SEQUENCIAS (keyframes interpolados a 30fps)
# ═══════════════════════════════════════════════════════════════════
_NUM = ('dx', 'dy', 'cabelo', 'capa', 'lift', 'sobe', 'a1', 'a2', 'c1', 'c2', 'saia', 'incl')


def _ease(t):
    return t * t * (3 - 2 * t)


def _facil(nome, t):
    """Curvas de tempo de um trecho:
    suave  - comeca e termina devagar (padrao)
    out    - arranca rapido e freia (golpes, reacoes)
    in     - comeca devagar e acelera (preparacao)
    mola   - chega, passa um pouco do ponto e volta (acomodar depois do golpe)
    linear - velocidade constante
    segura - fica parado na chave (tensao antes do golpe)"""
    if nome == 'segura':
        return 0.0
    if nome == 'linear':
        return t
    if nome == 'out':
        return 1 - (1 - t) ** 3
    if nome == 'in':
        return t * t
    if nome == 'mola':
        c1 = 1.4
        return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2
    return _ease(t)


def misturar(p0, p1, t, tl=None):
    """Pose entre p0 e p1: numeros e maos por `t` (ja com a curva de tempo);
    se as pernas mudam, passa pelo quadro do meio (escolhido pelo progresso
    linear `tl`) e o quadril sobe/desce continuo, sem pulo de altura."""
    tl = t if tl is None else tl
    q = dict(p0)
    for k in _NUM:
        a, b = p0[k], p1[k]
        if a is not None and b is not None:
            q[k] = a + (b - a) * t
    for k in ('m1', 'm2'):
        a, b = p0[k], p1[k]
        if a is not None and b is not None:
            q[k] = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    l0, l1 = p0['pernas'], p1['pernas']
    if l0 != l1:
        # as pernas passam de uma posicao para a outra continuamente (pes e
        # joelhos interpolados) e o quadril sobe/desce junto
        q['pernas'], q['pernas_b'] = l0, l1
        q['pt'] = max(0.0, min(1.0, t))
        h = altura(p0) + (altura(p1) - altura(p0)) * t
        q['dy'] = h - _alt_pernas(q)
    return q


def sequencia(chaves):
    """chaves: [(quadros, pose) ou (quadros, pose, curva), ...] -> lista de
    poses (1 por quadro). `quadros` = duracao do trecho ate a proxima chave;
    `curva` = como o tempo corre nele (ver _facil; padrao 'suave'). Campos
    numericos e maos interpolam; as pernas passam por um quadro do meio."""
    out = []
    for i, ch in enumerate(chaves):
        n, p0 = ch[0], ch[1]
        curva = ch[2] if len(ch) > 2 else 'suave'
        p1 = chaves[i + 1][1] if i + 1 < len(chaves) else p0
        n = max(1, int(n))
        for f in range(n):
            tl = f / float(n)
            if p1 is p0 or curva == 'segura' or f == 0:
                out.append(dict(p0))
            else:
                out.append(misturar(p0, p1, _facil(curva, tl), tl))
    return out


# ═══════════════════════════════════════════════════════════════════
#  CACHE
# ═══════════════════════════════════════════════════════════════════
_CACHE = OrderedDict()     # chave_pose -> (bytes RGBA (GW x GH), caixa)
_CACHE_MAX = 600
_TEX = OrderedDict()       # (chave_pose, silhueta) -> Texture
_TEX_MAX = 220
_RGBA = {c: bytes(int(round(v * 255)) for v in cor) for c, cor in _PALETA.items()}
_TC_NORMAL = (0, 0, 1, 0, 1, 1, 0, 1)
_TC_ESPELHO = (1, 0, 0, 0, 0, 1, 1, 1)
_BRANCO_SE = bytes([0] + [255] * 255)     # alpha > 0 -> 255 (silhueta branca)


def _gerar_imagem(p):
    ch = _chave(p)
    item = _CACHE.get(ch)
    if item is not None:
        _CACHE.move_to_end(ch)
        return ch, item
    px = montar(p)
    dentro = [(x, y, c) for (x, y), c in px.items() if 0 <= x < TW and 0 <= y < TH]
    x0 = y0 = 10 ** 6
    x1 = y1 = -10 ** 6
    if dentro:
        xs = [d[0] for d in dentro]
        ys = [d[1] for d in dentro]
        X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)
        corpo = [d for d in dentro if d[2] not in 'xX<>']   # rastro nao conta para o enquadramento
        if corpo:
            xs = [d[0] for d in corpo]
            ys = [d[1] for d in corpo]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        w, h = X1 - X0 + 1, Y1 - Y0 + 1
        buf = bytearray(w * h * 4)
        rgba = _RGBA
        for x, y, c in dentro:
            i = ((y - Y0) * w + (x - X0)) * 4
            buf[i:i + 4] = rgba[c]
        recorte = (X0, Y0, w, h)
    else:
        buf, recorte = bytearray(4), (0, 0, 1, 1)
    # caixa em unidades da grade (as cenas trabalham nelas)
    cx = ((x0 / float(R), y0 / float(R), (x1 + 1) / float(R) - 1, (y1 + 1) / float(R) - 1)
          if x1 >= x0 else (_X0, _PES, _X0 + 12, _PES + 26))
    borda = bordas(px) if p.get('mugetsu') else None
    item = (bytes(buf), cx, borda, recorte)
    _CACHE[ch] = item
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)
    return ch, item


def _bytes(p):
    """Pose -> imagem RGBA (GW x GH) em bytes. Cache LRU; so Python puro
    (pode rodar antes do primeiro quadro, sem contexto grafico)."""
    ch, item = _gerar_imagem(p)
    return ch, item[0]


_CAIXAS = OrderedDict()


def caixa(p):
    """Retangulo ocupado pela pose (x0, y0, x1, y1), em unidades da grade.
    Se a imagem ainda nao existe, mede pelo desenho cru (+1 texel do
    contorno): as cenas medem muitas poses de uma vez para enquadrar o
    boneco e isso nao pode travar o quadro."""
    ch = _chave(p)
    item = _CACHE.get(ch)
    if item is not None:
        return item[1]
    cx = _CAIXAS.get(ch)
    if cx is None:
        px = montar(p, rapido=True)
        xs = [q[0] for q, c in px.items() if c not in 'xX<>']
        ys = [q[1] for q, c in px.items() if c not in 'xX<>']
        if xs:
            x0, x1 = max(0, min(xs) - 1), min(TW - 1, max(xs) + 1)
            y0, y1 = max(0, min(ys) - 1), min(TH - 1, max(ys) + 1)
            cx = (x0 / float(R), y0 / float(R), (x1 + 1) / float(R) - 1, (y1 + 1) / float(R) - 1)
        else:
            cx = (_X0, _PES, _X0 + 12, _PES + 26)
        _CAIXAS[ch] = cx
        while len(_CAIXAS) > 1500:
            _CAIXAS.popitem(last=False)
    return cx


def bordas_pose(p):
    """Contorno do corpo (texels) da pose na forma Mugetsu (ou None)."""
    return _gerar_imagem(p)[1][2]


def _runs(p, espelhar=False):
    """(compatibilidade) pre-gera a imagem da pose."""
    return _bytes(p)


def _textura(p, silhueta=False, xadrez=False):
    """Pose -> (Texture so do recorte do desenho, recorte em texels). 1
    retangulo por quadro, bem leve no celular; o espelho e por tex_coords."""
    ch, item = _gerar_imagem(p)
    dados, rec = item[0], item[3]
    chave = (ch, silhueta, xadrez)
    tex = _TEX.get(chave)
    if tex is not None:
        _TEX.move_to_end(chave)
        return tex, rec
    w, h = rec[2], rec[3]
    if silhueta:                         # branco com o alpha do boneco (tingido por Color)
        alfa = bytearray(dados[3::4])
        if xadrez:                           # afterimage: so metade dos pixels (pixel art)
            for y in range(h):
                ini = (rec[0] + rec[1] + y + 1) % 2
                alfa[y * w + ini:(y + 1) * w:2] = bytes(len(range(y * w + ini, (y + 1) * w, 2)))
        branco = bytes(alfa).translate(_BRANCO_SE)
        b = bytearray(len(dados))
        b[0::4] = branco
        b[1::4] = branco
        b[2::4] = branco
        b[3::4] = alfa
        dados = bytes(b)
    tex = Texture.create(size=(w, h), colorfmt='rgba')
    tex.mag_filter = 'nearest'
    tex.min_filter = 'nearest'
    tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
    tex.add_reload_observer(
        lambda t, d=dados: t.blit_buffer(d, colorfmt='rgba', bufferfmt='ubyte'))
    _TEX[chave] = tex
    while len(_TEX) > _TEX_MAX:
        _TEX.popitem(last=False)
    return tex, rec


def _no_retangulo(rect, tex, rec, ps, espelhar):
    """Poe a textura recortada no lugar certo do quadro do boneco."""
    te = ps / float(R)
    x0, y0, w, h = rec
    if espelhar:
        x0 = TW - x0 - w
    rect.texture = tex
    rect.pos = (x0 * te, y0 * te)
    rect.size = (w * te, h * te)
    rect.tex_coords = _TC_ESPELHO if espelhar else _TC_NORMAL


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
    escala_x = NumericProperty(1.0)
    clarao = NumericProperty(0.0)          # 0..1: boneco todo branco (teleporte)

    def __init__(self, ps=4, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self.ps = max(R, int(ps) - int(ps) % R)      # texel = ps/R (pixels todos iguais)
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
        self.ao_redesenhar = None         # chamado quando a imagem da pose muda
        self._pausa = 0.0                 # hit-stop: segundos congelado no impacto
        # fisica secundaria
        self._m_capa = _Mola(95, 9)
        self._m_cab = _Mola(110, 10)
        self._m_lift = _Mola(80, 8)
        # camadas com inercia propria: cabeca (atrasa 1 px) e as duas laminas
        # (ficam um pouco para tras no giro e passam do ponto quando param)
        self._m_hx = _Mola(150, 13)
        self._m_hy = _Mola(150, 11)
        self._m_a = {1: None, 2: None}
        self._ult_base = None
        self.luz = 0.0                   # luz da lamina (aura), 0..1
        self._luz_imp = 0.0              # luz de impacto (cai sozinha)
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
            self._cor_clarao = Color(0.85, 0.97, 1, 0)
            self._rect_clarao = Rectangle(pos=(0, 0), size=(0, 0))
            PopMatrix()
        self.bind(pos=self._mover, x=self._mover, y=self._mover,
                  rotacao=self._mover, escala_y=self._mover, escala_x=self._mover,
                  espelhar=self._virou,
                  clarao=lambda *_: self._desenhar(forcar=True))
        self._mover()
        self._desenhar()

    # ── geometria ────────────────────────────────────────────────────
    def _virou(self, *_):
        """Ao virar de lado, o quadril fica no mesmo ponto da tela (sem o
        boneco dar um pulinho de lado no quadro da virada)."""
        try:
            a = (_X0 + 6 + 0.5) * self.ps
            b = (GW - 1 - (_X0 + 6) + 0.5) * self.ps
            self.x += (a - b) if self.espelhar else (b - a)
        except Exception:
            pass
        self._desenhar(forcar=True)

    def ancora_local(self):
        """Centro do quadril em coordenadas do proprio sprite (px de tela)."""
        cx = (_X0 + 6) if not self.espelhar else (GW - 1 - (_X0 + 6))
        return (cx + 0.5) * self.ps, (_PES + 12) * self.ps

    def ancorar(self, x, y):
        ax, ay = self.ancora_local()
        self.pos = (x - ax, y - ay)

    def ancora(self):
        ax, ay = self.ancora_local()
        return self.x + ax, self.y + ay

    def mao_local(self, qual=1, p=None):
        p = p or self._base
        topo_tronco = _PES + _alt_pernas(p) + len(_TRONCO) - 1 + _meia(p['dy'])
        base_x = _X0 + _meia(p['dx']) + int(round(p.get('incl', 0) or 0))
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

    def ponta_espada(self, qual=1, p=None):
        """(x, y) da ponta da lamina `qual` (coords do pai), sem rotacao."""
        p = p or self._base
        ang = p['a1'] if qual == 1 else p['a2']
        if ang is None:
            return self.ponto_mao(qual)
        comp = (p['c1'] if qual == 1 else p['c2']) + 2
        hx, hy = self.x + self.mao_local(qual, p)[0], self.y + self.mao_local(qual, p)[1]
        a = math.radians(ang)
        dx = math.cos(a) * comp * self.ps
        return hx + (-dx if self.espelhar else dx), hy + math.sin(a) * comp * self.ps

    def extensao(self, p=None):
        """(esq, baixo, dir, cima): quanto a pose (com espadas) se estende a
        partir da ancora, em px de tela. Para manter o boneco no quadro."""
        x0, y0, x1, y1 = caixa(p or self._base)
        ps = self.ps
        ax, ay = self.ancora_local()
        if self.espelhar:
            x0, x1 = GW - 1 - x1, GW - 1 - x0
        return ax - x0 * ps, ay - y0 * ps, (x1 + 1) * ps - ax, (y1 + 1) * ps - ay

    def _mover(self, *_):
        self._tr.xy = (self.x, self.y)
        orig = self.pivo if self.pivo is not None else self.ancora_local()
        self._rot.origin = orig
        self._rot.angle = self.rotacao
        ax, ay = self.ancora_local()
        self._sc.origin = (ax, ay)
        self._sc.x = self.escala_x
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
        # cabeca: +-1 px de atraso
        q['hx'] = int(round(max(-1.0, min(1.0, self._m_hx.x))))
        q['hy'] = int(round(max(-1.0, min(1.0, self._m_hy.x))))
        # laminas: seguem a pose com um pouquinho de atraso/mola (max 8 graus)
        for i, ch in ((1, 'a1'), (2, 'a2')):
            m = self._m_a[i]
            if m is not None and b[ch] is not None:
                q[ch] = b[ch] + max(-8.0, min(8.0, round(m.x - b[ch])))
        # luz: aura da lamina ou clarao de impacto, em 3 degraus
        luz = max(self.luz, self._luz_imp)
        q['luz'] = 1.0 if luz >= 0.75 else (0.5 if luz >= 0.3 else 0.0)
        # brilho percorre as laminas a cada ~2,6 s
        ciclo = self._t % 2.6
        q['brilho'] = (round(ciclo / 0.45 * 6) / 6.0) if (ciclo < 0.45 and not b.get('mugetsu')) else None
        return q

    def _desenhar(self, forcar=False):
        try:
            self._pose = self._composta()
            chave = (_chave(self._pose), self.espelhar)
            if chave == self._ult_chave and not forcar:
                return
            self._ult_chave = chave
            tex, rec = _textura(self._pose)
            _no_retangulo(self._rect, tex, rec, self.ps, self.espelhar)
            if self.clarao > 0:
                tex, rec = _textura(self._pose, silhueta=True)
                _no_retangulo(self._rect_clarao, tex, rec, self.ps, self.espelhar)
            else:
                self._rect_clarao.size = (0, 0)
            self._cor_clarao.a = self.clarao
            if self.ao_redesenhar is not None:
                self.ao_redesenhar()
        except Exception as e:
            print(f"[kirito] desenho ignorado: {e}")

    def _vida(self, dt):
        """Fisica do sobretudo/cabelo a partir da velocidade real do boneco."""
        try:
            if self._pausa > 0:
                return
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
            self._camadas(dt, frente, cima)
            self._desenhar()
        except Exception as e:
            print(f"[kirito] fisica: {e}")

    def _camadas(self, dt, frente, cima):
        """Movimento secundario: o que o tronco e as laminas fazem na pose
        empurra cabeca, cabelo e sobretudo (que chegam depois e passam do
        ponto), mesmo com o boneco parado no lugar."""
        b = self._base
        ub = self._ult_base
        if ub is not None:
            ddx = (b['dx'] or 0) - (ub['dx'] or 0)
            ddy = (b['dy'] or 0) - (ub['dy'] or 0)
            if abs(ddx) < 4 and abs(ddy) < 4:            # troca brusca de pose nao conta
                self._m_hx.v -= ddx * 7.0
                self._m_hy.v -= ddy * 7.0
                self._m_cab.v += ddx * 5.0
                self._m_capa.v += ddx * 4.0
                self._m_lift.v -= ddy * 3.0
        self._ult_base = b
        # a cabeca atrasa quando o corpo acelera (sobe -> cabeca fica embaixo)
        self._m_hx.passo(max(-1.2, min(1.2, -frente / 420.0)), dt)
        self._m_hy.passo(max(-1.2, min(1.2, -cima / 380.0)), dt)
        for i, ch in ((1, 'a1'), (2, 'a2')):
            alvo = b[ch]
            m = self._m_a[i]
            if alvo is None:
                self._m_a[i] = None
                continue
            if m is None or abs(alvo - m.x) > 70:        # golpe (salto grande): sem atraso
                m = _Mola(700, 34)
                m.x = alvo
                self._m_a[i] = m
                continue
            antes = m.x
            m.passo(alvo, dt)
            giro = abs(m.x - antes)
            if giro > 3:                                  # lamina girando: o sobretudo sente
                self._m_capa.v += min(6.0, giro * 0.08)
        if self._luz_imp > 0:
            self._luz_imp = max(0.0, self._luz_imp - dt / 0.16)

    def impacto(self, forte=False):
        """Quadro de impacto: a luz da lamina acende o corpo e o boneco
        pisca claro por 1-2 quadros (sem congelar a cena)."""
        self._luz_imp = 1.0
        self.clarao = 0.9 if forte else 0.45
        t = [0.0]

        def _p(dt):
            t[0] += dt
            self.clarao = max(0.0, (0.9 if forte else 0.45) * (1 - t[0] / 0.07))
            return t[0] < 0.07
        Clock.schedule_interval(_p, 1 / 60.)

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
                t0 = time.time()                     # no maximo ~10 ms por quadro
                while time.time() - t0 < 0.010:
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

    def pausar(self, seg):
        """Hit-stop: congela a animacao (e a fisica) por `seg` no instante do
        impacto - o golpe parece mais pesado."""
        self._pausa = max(self._pausa, float(seg))

    def _quadro(self, dt):
        try:
            if self._pausa > 0:
                self._pausa -= dt
                return
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
        """Parado, mas vivo: respira (o tronco desce 1 px e as maos vem 3
        quadros depois), a lamina flutua um pouquinho, pisca de vez em quando
        (as vezes duas vezes). Cabeca, cabelo e sobretudo reagem sozinhos
        pela fisica, com atraso."""
        b = dict(base or POSE_A['guarda'])
        quadros = []
        n = 120                                      # 4 s
        for f in range(n):
            t = f / float(n) * 2 * math.pi
            q = dict(b)
            q['dy'] = b['dy'] - (1 if math.sin(t) < -0.35 else 0)
            atras = math.sin(t - 0.6)                # maos acompanham com atraso
            if b['m1'] is not None:
                q['m1'] = (b['m1'][0], b['m1'][1] - (1 if atras < -0.35 else 0))
            if b['m2'] is not None:
                q['m2'] = (b['m2'][0], b['m2'][1] - (1 if atras < -0.35 else 0))
            if b['a1'] is not None:
                q['a1'] = b['a1'] + round(2.0 * math.sin(2 * t + 0.8))
            if b['a2'] is not None:
                q['a2'] = b['a2'] + round(2.0 * math.sin(2 * t + 2.0))
            if piscar and (70 <= f <= 72 or 104 <= f <= 105 or 108 <= f <= 109):
                q['olhos'] = 'f'
            quadros.append(q)
        self.tocar(quadros, loop=True)

    # ── afterimage ───────────────────────────────────────────────────
    def fantasma(self, cor=(0.0, 0.85, 1.0), alfa=0.36, duracao=0.16):
        """Afterimage: silhueta pontilhada (metade dos pixels) da pose atual,
        bem curta - so uma indicacao de velocidade."""
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
                tex, rec = _textura(self._pose, silhueta=True, xadrez=True)
                _no_retangulo(Rectangle(), tex, rec, self.ps, self.espelhar)
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
    'guarda':     pose(pernas='base', m1=(3, -5), a1=-40.0),
    # guardado: mao no cabo da Elucidator (na cintura), como um samurai em repouso
    'guardado':   pose(pernas='base', m1=(2, -3), a1=None),
    # vitoria: base firme, mao no cabo, vira o rosto para quem olha
    'vitoria':    pose(pernas='base', m1=(2, -3), a1=None, olhos='v', vista='frente'),
    'fim':        pose(m1=(2, -3), a1=None),
    # tela do PIN: espiando por cima da borda da caixa, as duas maos apoiadas
    # nela e os olhos no codigo sendo digitado (o corpo fica escondido atras)
    # (a borda fica na linha topo+2 da pose sem dy; as maos ficam paradas nela
    # enquanto a cabeca sobe/desce: m_y = 4 - dy)
    'espia':       pose(dy=1, m1=(3, 3), a1=None, m2=(-3, 3), a2=None, olhos='b', frente1=True),
    'espia_olha':  pose(dy=1, m1=(3, 3), a1=None, m2=(-3, 3), a2=None, frente1=True),
    'espia_alto':  pose(dy=3, m1=(3, 1), a1=None, m2=(-3, 1), a2=None, frente1=True),
    'espia_baixo': pose(dy=-3, m1=(3, 7), a1=None, m2=(-3, 7), a2=None, frente1=True),
    'susto':      pose(pernas='pulo', dx=-1, dy=1, m1=(3, 7), a1=None, m2=(-2, 7)),
    # agarrado na parede (espadas guardadas), corpo encolhido
    'grudado':    pose(pernas='grudado', dy=-2, m1=(3, 3), a1=None),
    # pendurado por uma mao na borda de cima (braco esticado ao lado da
    # cabeca), a outra no cabo da Elucidator: samurai pronto para sacar.
    # A mao que segura a borda fica no MESMO ponto nas 3 poses.
    'pendurado':   pose(pernas='solto', m2=(-3, 15), a2=None, m1=(2, -3), a1=None, saia=0.35),
    'pendurado_b': pose(pernas='solto2', m2=(-3, 15), a2=None, m1=(2, -3), a1=None, saia=0.35),
    # kamae: recolhe as pernas e empurra a guarda com o polegar (koiguchi)
    'pendurado2':  pose(pernas='pulo', dy=3, m2=(-3, 15), a2=None, m1=(3, -2), a1=None, saia=0.5),
    'agacha':     pose(pernas='agachado', dy=-3, m1=(2, -3), a1=None, incl=1),
    'pulo':       pose(pernas='pulo', dy=-1, m1=(2, -3), a1=None),
    # saque iai: a lamina sai da bainha da cintura e corta na horizontal, subindo
    'saca1':      pose(pernas='avanco', dx=1, m1=(4, -1), a1=_BAINHA_ANG, c1=7, m2=(-2, 1)),
    'corta1':     pose(pernas='avanco', dx=2, dy=-1, m1=(8, 0), a1=370.0, m2=(-4, 1)),
    'segue1':     pose(pernas='avanco', dx=2, dy=-1, m1=(6, 3), a1=395.0, m2=(-4, 1)),
    # golpe de cima para baixo (mini Kirito ao apagar)
    'arma1':      pose(pernas='recua', dx=-1, m1=(0, 9), a1=112.0, m2=(4, 1)),
    'corta_desce': pose(pernas='avanco', dx=2, dy=-1, m1=(7, -2), a1=-38.0, m2=(-4, 2)),
    'segue_desce': pose(pernas='avanco', dx=2, dy=-1, m1=(4, -6), a1=-70.0, m2=(-4, 1)),
    # saca a Dark Repulser (mao de tras sobe ate o cabo nas costas)
    'pega2':      pose(pernas='base', dx=1, m1=(5, -4), a1=-40.0, m2=(-1, 8), a2=None),
    'saca2':      pose(pernas='avanco', dx=1, m1=(5, -4), a1=-40.0, m2=(-3, 8), a2=100.0, c2=14),
    'dupla':      pose(pernas='base_larga', m1=(6, 3), a1=40.0, m2=(-5, -1), a2=205.0),
    # combo samurai com as duas
    'c2_arma':    pose(pernas='recua', dx=-1, m1=(-1, 9), a1=120.0, m2=(-4, -2), a2=200.0),
    'c2_corta':   pose(pernas='avanco', dx=2, dy=-1, m1=(7, -2), a1=-45.0, m2=(-5, -3), a2=215.0),
    'c3_arma':    pose(pernas='avanco', m1=(5, -4), a1=-60.0, m2=(-5, -4), a2=225.0),
    'c3_corta':   pose(pernas='avanco', dx=2, m1=(-3, 3), a1=160.0, m2=(5, 8), a2=75.0),
    'giro_a':     pose(pernas='pulo', m1=(5, 4), a1=60.0, m2=(-6, -2), a2=230.0),
    'giro_b':     pose(pernas='pulo', m1=(-5, -2), a1=240.0, m2=(5, 4), a2=50.0),
    # golpe final (iai): carga, corte atravessando, chiburi, embainhar
    'iai_carga':  pose(pernas='agachado', dx=-1, dy=-3, m1=(-3, -1), a1=192.0, m2=(-5, -2), a2=202.0),
    'iai_corte':  pose(pernas='avanco', dx=3, dy=-2, m1=(8, 0), a1=-5.0, c1=17, m2=(7, -4), a2=-28.0, c2=17),
    'iai_fim':    pose(pernas='avanco', dx=3, dy=-3, m1=(8, -1), a1=-12.0, c1=17, m2=(7, -5), a2=-35.0, c2=17),
    'chiburi':    pose(pernas='base_larga', dx=2, m1=(6, 3), a1=30.0, m2=(5, -1), a2=10.0),
    # embainhar (noto): a ponta da preta entra na boca da bainha da cintura e
    # desliza ate o clique; a azul volta para as costas
    # (angulo -138 = 222 - 360: vindo do chiburi a lamina desce pela frente
    # ate a boca da bainha, em vez de dar a volta por cima da cabeca)
    'embainha_a': pose(pernas='base', m1=(6, 1), a1=_BAINHA_ANG - 360, c1=8, m2=(-2, 9), a2=268.0, c2=10),
    'embainha_b': pose(pernas='base', m1=(3, -2), a1=_BAINHA_ANG - 360, c1=4, m2=(-2, 6), a2=268.0, c2=5),
    'embainha_c': pose(pernas='base', m1=(2, -3), a1=_BAINHA_ANG - 360, c1=0, m2=(-2, 5), a2=268.0, c2=0),
    # compatibilidade com cenas antigas
    'embainha':   pose(pernas='repouso', m1=(3, -2), a1=_BAINHA_ANG - 360, c1=4, m2=(-2, 6), a2=268.0, c2=5),
    'espreita':   pose(dy=1, m1=(3, 3), a1=None, m2=(-3, 3), a2=None, frente1=True),
    'espreita2':  pose(dy=3, m1=(3, 1), a1=None, m2=(-3, 1), a2=None, frente1=True),
    'x_arma':     pose(pernas='recua', dx=-1, m1=(-3, 6), a1=135.0, m2=(-5, 6), a2=160.0),
    'x_corta':    pose(pernas='avanco', dx=2, dy=-1, m1=(7, 0), a1=-20.0, m2=(6, -3), a2=-40.0),
    'final_arma': pose(pernas='agachado', dy=-2, m1=(-4, 7), a1=120.0, m2=(-6, 7), a2=140.0),
    'final':      pose(pernas='avanco', dx=3, dy=-1, m1=(7, -2), a1=-25.0, m2=(7, -5), a2=-50.0, c1=16, c2=16),
    'pousa':      pose(pernas='agachado', dy=-3, m1=(5, -3), a1=-50.0, m2=(-4, -3), a2=230.0),
    'guarda2':    pose(m1=(0, 6), a1=95.0, c1=8, m2=(-2, 7), a2=100.0, c2=8),
}


def _duas_maos(m1, a1, recuo=3.0):
    """m2 (mao de tras) segurando o mesmo cabo, `recuo` px atras da mao da
    frente (empunhadura de duas maos da espada fundida)."""
    a = math.radians(a1)
    return (6 + m1[0] - math.cos(a) * recuo, m1[1] - math.sin(a) * recuo)


def _fund(**kw):
    """Pose com a espada fundida (evo=True: evoluida), segurada com as duas maos."""
    evo = kw.pop('evo', False)
    kw.setdefault('tipo1', 4 if evo else 3)
    kw.setdefault('c1', 23 if evo else 20)
    kw['fusao'] = True
    if 'm2' not in kw:
        kw['m2'] = _duas_maos(kw['m1'], kw['a1'])
    return pose(**kw)


# combo de samurai: cada silaba vem de uma direcao diferente
POSE_A.update({
    # de baixo para cima (kiriage): agachado com as laminas baixas para tras
    'sobe_arma':   pose(pernas='agachado', dy=-3, m1=(-3, -1), a1=235.0, m2=(-5, -1), a2=215.0, olhos='s'),
    'sobe_corta':  pose(pernas='avanco', dx=2, m1=(5, 7), a1=430.0, m2=(3, 8), a2=445.0, olhos='g'),
    # do alto para baixo (kirioroshi): no ar, as duas acima da cabeca
    'desce_arma':  pose(pernas='pulo', m1=(-1, 12), a1=100.0, m2=(-2, 12), a2=115.0, olhos='s'),
    'desce_corta': pose(pernas='pulo', dy=-1, m1=(6, -4), a1=-60.0, m2=(4, -3), a2=-45.0, olhos='g'),
    # preparacao do iai: mais baixo, pende para tras, mao firme no cabo
    'saca0':       pose(pernas='avanco_baixo', dx=-1, m1=(3, -2), a1=_BAINHA_ANG, c1=4, m2=(-3, 0), olhos='s'),
    # chiburi em dois tempos: ergue as laminas e sacode para baixo
    'chiburi_a':   pose(pernas='avanco', dx=1, dy=-1, m1=(5, 6), a1=70.0, m2=(4, 2), a2=50.0, olhos='s'),
})

# golpe final (estilo Bleach): junta as duas espadas acima da cabeca, a
# fundida suga o infinito da tela, evolui e da o ultimo corte
POSE_A.update({
    'une_a':       pose(m1=(-1, 16), a1=110.0, m2=(-1, 15), a2=70.0, olhos='s'),
    'une_b':       pose(m1=(-6, 18), a1=90.0, m2=(0, 15), a2=90.0, olhos='s'),
    'fund_alto':   _fund(m1=(-6, 18), a1=90.0, m2=(0, 15), olhos='s'),
    'evo_alto':    _fund(m1=(-6, 18), a1=90.0, m2=(0, 15), olhos='l', evo=True),
    'evo_carga':   _fund(pernas='agachado', dx=-1, dy=-3, m1=(-3, -1), a1=195.0, olhos='l', evo=True),
    'evo_corte':   _fund(pernas='avanco', dx=3, dy=-2, m1=(8, 0), a1=-5.0, olhos='g', evo=True),
    'evo_fim':     _fund(pernas='avanco', dx=3, dy=-3, m1=(8, -1), a1=-12.0, olhos='l', evo=True),
})


# golpes proprios de cada acao (cada um com a sua mecanica de corpo)
POSE_A.update({
    # estocada (apagar turno): recolhe a lamina ao lado do rosto, mira com a
    # outra mao e se lanca com o braco todo esticado
    'estoca_arma': pose(pernas='recua', dx=-2, m1=(-3, 4), a1=-4.0, m2=(6, 3), olhos='s'),
    'estoca':      pose(pernas='avanco_baixo', dx=3, dy=-1, m1=(11, 1), a1=0.0, c1=16, m2=(-5, -1),
                        olhos='g'),
    'estoca_puxa': pose(pernas='avanco', dx=1, m1=(3, 1), a1=4.0, m2=(-4, -1), olhos='s'),
    # giro de 360 (abertura): as duas laminas abertas na horizontal
    'giro_1':      pose(pernas='base_larga', m1=(9, 2), a1=2.0, m2=(-8, 2), a2=178.0, olhos='s'),
    'giro_2':      pose(pernas='base_larga', m1=(9, 2), a1=2.0, m2=(-8, 2), a2=178.0, vista='costas'),
    'giro_3':      pose(pernas='base_larga', m1=(9, 2), a1=2.0, m2=(-8, 2), a2=178.0, vista='frente',
                        olhos='g'),
    # mergulho do alto (abertura): sobe com a lamina erguida e desce de ponta
    'mergulho_sobe': pose(pernas='pulo', m1=(0, 12), a1=95.0, m2=(-1, 11), olhos='s'),
    'mergulho':      pose(pernas='solto', dy=2, m1=(3, 4), a1=-90.0, c1=17, m2=(1, 4), olhos='g'),
    'mergulho_fim':  pose(pernas='agachado', dy=-3, m1=(4, -4), a1=-88.0, c1=17, m2=(2, -3), olhos='s'),
    # golpe subindo com salto (abertura): agachado com a lamina baixa atras,
    # corta subindo e o corpo vai junto para o alto
    'salto_arma':  pose(pernas='agachado', dy=-3, dx=-1, m1=(-4, -2), a1=205.0, m2=(-2, -3), olhos='s'),
    'salto':       pose(pernas='pulo', dy=1, m1=(6, 8), a1=70.0, m2=(-5, 2), olhos='g'),
    'salto_fim':   pose(pernas='suspenso', dy=2, m1=(3, 12), a1=100.0, m2=(-5, 3), olhos='s'),
    # saque de uma espada so (apagar lote): chiburi e embainhar sem a azul
    'chiburi1_a':  pose(pernas='avanco', dx=1, dy=-1, m1=(5, 6), a1=70.0, m2=(-3, 0), olhos='s'),
    'chiburi1':    pose(pernas='base_larga', dx=2, m1=(6, 2), a1=-30.0, m2=(-3, 0), olhos='s'),
    'embainha1_a': pose(pernas='base', m1=(6, 1), a1=_BAINHA_ANG - 360, c1=8, olhos='s'),
    'embainha1_b': pose(pernas='base', m1=(3, -2), a1=_BAINHA_ANG - 360, c1=4),
    'embainha1_c': pose(pernas='base', m1=(2, -3), a1=_BAINHA_ANG - 360, c1=0),
    # arremesso do pergaminho de luz (enviar pro WhatsApp)
    'joga_arma':   pose(pernas='recua', dx=-1, m1=(-4, 6), a1=None, m2=(5, 2), olhos='s'),
    'joga':        pose(pernas='avanco', dx=2, m1=(9, 7), a1=None, m2=(-4, -1), olhos='g'),
    # Starburst Stream (WIPE): 16 golpes rapidos, alternando as espadas
    # (cada par: preparo -> corte; so uma lamina se mexe por golpe)
    'sb1_a': pose(pernas='base_larga', m1=(1, 9), a1=115.0, m2=(-5, -1), a2=205.0, olhos='s'),
    'sb1_b': pose(pernas='avanco', dx=2, m1=(8, -2), a1=-40.0, m2=(-5, -1), a2=205.0, olhos='g'),
    'sb2_a': pose(pernas='avanco', m1=(4, 4), a1=60.0, m2=(-6, -4), a2=235.0, olhos='s'),
    'sb2_b': pose(pernas='base_larga', dx=1, m1=(4, 4), a1=60.0, m2=(6, 6), a2=55.0, olhos='g'),
    'sb3_a': pose(pernas='base_larga', m1=(-2, 3), a1=175.0, m2=(-5, -2), a2=210.0, olhos='s'),
    'sb3_b': pose(pernas='avanco', dx=2, m1=(9, 2), a1=5.0, m2=(-5, -2), a2=210.0, olhos='g'),
    'sb4_a': pose(pernas='avanco', m1=(5, 3), a1=40.0, m2=(-7, 2), a2=185.0, olhos='s'),
    'sb4_b': pose(pernas='base_larga', dx=1, m1=(5, 3), a1=40.0, m2=(7, 1), a2=-5.0, olhos='g'),
    # carimbo do +XP (adicionar lote): corte curto na horizontal
    'carimbo_arma': pose(pernas='base', m1=(-2, 5), a1=150.0, c1=12, olhos='s'),
    'carimbo':      pose(pernas='avanco', dx=2, m1=(8, 1), a1=-8.0, c1=12, olhos='g'),
})


def smear(p, de=None, de2=None):
    """Copia da pose com rastro da espada 1 (e/ou 2) vindo dos angulos dados."""
    q = dict(p)
    q['s1'] = de
    q['s2'] = de2
    return q


# ═══════════════════════════════════════════════════════════════════
#  MOVIMENTO SOLTO: preparacao, golpe, continuidade e acomodacao
# ═══════════════════════════════════════════════════════════════════
def _sentido(a, b):
    if a is None or b is None or a == b:
        return 0
    return 1 if b > a else -1


def _passo_mao(m_de, m_para, d, recuar):
    """Mao `d` px para tras (recuar) ou para a frente do caminho do golpe."""
    if m_de is None or m_para is None:
        return m_para if not recuar else m_de
    vx, vy = m_para[0] - m_de[0], m_para[1] - m_de[1]
    n = math.hypot(vx, vy) or 1.0
    if recuar:
        return (m_de[0] - vx / n * d, m_de[1] - vy / n * d)
    return (m_para[0] + vx / n * d, m_para[1] + vy / n * d)


def golpe(arma, corta, olhos=('s', 'g', 's'), n_arma=3, prende=2, segue=3, volta=6,
          graus=16.0, lamina_recua=True, seg=None, duplo=True):
    """Chaves de um corte com cara de animacao desenhada a mao:
      arma -> preparacao (a lamina recua mais, o corpo abaixa e pende para
      tras; segura um instante) -> meio do golpe (rastro) -> rastro do golpe
      inteiro -> impacto que passa do ponto (corpo inclina para a frente) ->
      volta com uma molinha para a pose do corte.
    Devolve (chaves, i_rastro): i_rastro = quadro do rastro completo (onde
    entram o efeito, o som e o hit-stop)."""
    s1 = _sentido(arma['a1'], corta['a1'])
    s2 = _sentido(arma['a2'], corta['a2'])
    arma = dict(arma, olhos=olhos[0])
    ant = dict(arma)
    if lamina_recua:
        if arma['a1'] is not None:
            ant['a1'] = arma['a1'] - s1 * graus * 0.7
        if arma['a2'] is not None:
            ant['a2'] = arma['a2'] - s2 * graus * 0.7
    ant['m1'] = _passo_mao(arma['m1'], corta['m1'], 1.0, True)
    if arma['m2'] is not None and corta['m2'] is not None:
        ant['m2'] = _passo_mao(arma['m2'], corta['m2'], 1.0, True)
    ant['dx'] = arma['dx'] - 1                       # pende para tras
    ant['incl'] = -1                                 # ombros e cabeca vao para tras
    ant['vista'] = 'costas'                          # torce o corpo: mostra as costas
    if altura(arma) > 3:
        ant['dy'] = arma['dy'] - 1                   # e abaixa (se nao estiver agachado)
    imp = dict(corta, olhos=olhos[1], incl=1, vista='frente')   # corta de frente, peso a frente
    if seg is None:
        seg = dict(imp)
        if corta['a1'] is not None and s1:
            seg['a1'] = corta['a1'] + s1 * graus
        if corta['a2'] is not None and s2:
            seg['a2'] = corta['a2'] + s2 * graus
        seg['m1'] = _passo_mao(arma['m1'], corta['m1'], 1.0, False)
        if arma['m2'] is not None and corta['m2'] is not None:
            seg['m2'] = _passo_mao(arma['m2'], corta['m2'], 1.0, False)
        seg['dx'] = corta['dx'] + 1                  # inclina para a frente
        seg['incl'] = 1
        seg['vista'] = 'lado'                        # volta de perfil na acomodacao
    else:
        seg = dict(seg, olhos=olhos[1], incl=1, vista='lado')
    fim = dict(corta, olhos=olhos[2])
    chaves = [(n_arma, arma, 'suave'), (prende, ant, 'segura')]
    if duplo:                                         # meio do golpe: 2 quadros de rastro
        meio = misturar(ant, imp, 0.5, 0.5)
        meio = smear(meio, ant['a1'] if s1 else None, ant['a2'] if s2 else None)
        chaves.append((1, meio, 'segura'))
    rastro = smear(imp, ant['a1'] if s1 else None, ant['a2'] if s2 else None)
    i_rastro = sum(c[0] for c in chaves)
    chaves += [(1, rastro, 'segura'), (segue, imp, 'out'), (volta, seg, 'mola'), (1, fim, 'segura')]
    return chaves, i_rastro


# tremor de poder (px no tronco): as pernas ficam firmes, so o tronco treme
_TREMOR = (0, 1, 1, 0, -1, 0, 1, 0, -1, -1, 0, 1)


def poder(base, n=36, forca=1.0, sobe=1.0, lift=1.6, olhos=None, de=0.0):
    """Quadros de uma pose segurando energia: tronco tremendo, cabelo
    arrepiando para cima e sobretudo levantando com o vento de reiatsu.
    `de` = de onde parte a energia (0..1): cresce ate `forca` ao longo dos
    quadros. Para tocar em loop (loop=True)."""
    quadros = []
    for f in range(n):
        u = de + (1.0 - de) * min(1.0, f / max(1.0, n * 0.35))
        q = dict(base)
        if olhos:
            q['olhos'] = olhos
        q['sobe'] = sobe * u
        q['lift'] = base['lift'] + lift * u
        treme = _TREMOR[(f // 2) % len(_TREMOR)]
        if forca * u >= 0.5:
            q['dx'] = base['dx'] + treme
        quadros.append(q)
    return quadros


def encolhido(p):
    """A mesma pose com as pernas recolhidas (no alto de um pulo)."""
    q = dict(p)
    q['pernas'] = 'pulo'
    q['pernas_b'] = None
    q['dy'] = max(-3.0, min(3.0, altura(p) - _PERNAS_P['pulo']['H']))
    return q


def esticado(p):
    """A mesma pose com as pernas esticadas (impulso do pulo / indo pousar)."""
    q = dict(p)
    q['pernas'] = 'suspenso'
    q['pernas_b'] = None
    q['dy'] = 0
    return q


# ═══════════════════════════════════════════════════════════════════
#  FAISCAS
# ═══════════════════════════════════════════════════════════════════
class Faiscas(Widget):
    """Pool de faiscas de pixel. Cada uma tem velocidade, arrasto, gravidade,
    balanco e tempo de vida proprios; fica sempre na grade de pixels (tam),
    diminui em degraus, pisca antes de sumir e algumas deixam 1 pixel de
    rastro. estourar(x, y, cor, n)."""

    def __init__(self, n_max=60, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self._p = []
        self._ins = []
        with self.canvas:
            for _ in range(n_max):
                c2 = Color(1, 1, 1, 0)
                r2 = Rectangle(size=(0, 0))          # rastro (1 pixel atras)
                c = Color(1, 1, 1, 0)
                r = Rectangle(size=(0, 0))
                self._ins.append((c, r, c2, r2))
        self._livres = list(range(n_max))
        self._ev = None

    def estourar(self, x, y, cor=(0.4, 0.95, 1.0), n=14, forca=260.0, tam=4.0, gravidade=420.0,
                 rastro=0.3):
        tam = max(1.0, float(tam))
        for _ in range(n):
            if not self._livres:
                break
            i = self._livres.pop()
            a = random.uniform(0, 2 * math.pi)
            v = forca * random.uniform(0.35, 1.0)
            vida = random.uniform(0.25, 0.55)
            self._p.append({
                'x': x, 'y': y, 'vx': math.cos(a) * v, 'vy': math.sin(a) * v,
                'vida': vida, 'v0': vida, 'u': tam, 'mult': random.choice((1, 1, 1, 2)),
                'i': i, 'cor': cor, 'g': gravidade, 'arrasto': random.uniform(0.86, 0.93),
                'bal': random.uniform(0, 0.25) * forca, 'fb': random.uniform(6, 14),
                'fase': random.uniform(0, 6.3), 't': 0.0, 'trilha': random.random() < rastro,
                'ult': None})
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            vivas = []
            for f in self._p:
                f['vida'] -= dt
                f['t'] += dt
                c, r, c2, r2 = self._ins[f['i']]
                if f['vida'] <= 0:
                    c.a = c2.a = 0
                    r.size = r2.size = (0, 0)
                    self._livres.append(f['i'])
                    continue
                arr = f['arrasto'] ** (dt * 60)
                f['vx'] = f['vx'] * arr + math.sin(f['t'] * f['fb'] + f['fase']) * f['bal'] * dt
                f['vy'] = f['vy'] * arr - f['g'] * dt
                f['x'] += f['vx'] * dt
                f['y'] += f['vy'] * dt
                k = f['vida'] / f['v0']
                u = f['u']
                s = u * (f['mult'] if k > 0.45 else 1)     # diminui em degraus
                px, py = round(f['x'] / u) * u, round(f['y'] / u) * u
                cr = f['cor']
                if k > 0.7:                                 # cor em 3 degraus: branco -> meio -> cor
                    rgb = (1.0, 1.0, 1.0)
                elif k > 0.35:
                    rgb = ((1 + cr[0]) / 2, (1 + cr[1]) / 2, (1 + cr[2]) / 2)
                else:
                    rgb = cr
                a = 1.0 if k > 0.25 else (1.0 if int(f['t'] * 30) % 2 else 0.0)   # pisca e some
                r.pos = (px - s / 2, py - s / 2)
                r.size = (s, s)
                c.rgba = (rgb[0], rgb[1], rgb[2], a)
                if f['trilha'] and f['ult'] is not None and f['ult'] != (px, py):
                    ux, uy = f['ult']
                    r2.pos = (ux - u / 2, uy - u / 2)
                    r2.size = (u, u)
                    c2.rgba = (cr[0], cr[1], cr[2], 0.45 * a)
                else:
                    r2.size = (0, 0)
                f['ult'] = (px, py)
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


class RastroLamina(Widget):
    """Rastro da ponta da lamina em pixels: quando ela passa rapido, deixa
    uma trilha de quadradinhos que nasce forte, perde a cor em degraus e
    alguns viram faiscas. Curto e so no movimento rapido."""

    def __init__(self, k, faiscas=None, n_max=36, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k = k
        self.faiscas = faiscas
        self._q = []
        self._ins = []
        with self.canvas:
            for _ in range(n_max):
                c = Color(1, 1, 1, 0)
                r = Rectangle(size=(0, 0))
                self._ins.append((c, r))
        self._livres = list(range(n_max))
        self._ult = {1: None, 2: None}
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            k = self.k
            if k.parent is None or self.get_root_window() is None:
                return self.parar()                  # cena acabou: para o relogio
            u = k.ps
            p = k._base
            ativo = k.opacity > 0.5 and k.rotacao == 0 and k._pausa <= 0
            for qual, cor in ((1, (0.55, 1.0, 1.0)), (2, (0.45, 0.7, 1.0))):
                if not ativo or p.get('a1' if qual == 1 else 'a2') is None:
                    self._ult[qual] = None
                    continue
                x, y = k.ponta_espada(qual)
                ult = self._ult[qual]
                self._ult[qual] = (x, y)
                if ult is None:
                    continue
                dist = math.hypot(x - ult[0], y - ult[1])
                if dist < 1.8 * u:
                    continue
                passos = min(6, int(dist / u))
                for j in range(passos):
                    if not self._livres:
                        break
                    t = (j + 1) / float(passos)
                    i = self._livres.pop()
                    vida = 0.09 + 0.05 * t
                    self._q.append([ult[0] + (x - ult[0]) * t, ult[1] + (y - ult[1]) * t,
                                    vida, vida, i, cor])
            vivos = []
            for q in self._q:
                q[2] -= dt
                c, r = self._ins[q[4]]
                if q[2] <= 0:
                    c.a = 0
                    r.size = (0, 0)
                    self._livres.append(q[4])
                    if self.faiscas is not None and random.random() < 0.12:
                        self.faiscas.estourar(q[0], q[1], q[5], n=1, forca=u * 10, tam=max(2, u * 0.7),
                                              gravidade=-u * 20, rastro=0)
                    continue
                kk = q[2] / q[3]
                s = u if kk > 0.5 else max(1.0, round(u * 0.6))
                r.pos = (round(q[0] / u) * u - s / 2, round(q[1] / u) * u - s / 2)
                r.size = (s, s)
                cr = q[5]
                if kk > 0.66:
                    c.rgba = (1, 1, 1, 0.9)
                else:
                    c.rgba = (cr[0], cr[1], cr[2], 0.8 if kk > 0.33 else 0.45)
                vivos.append(q)
            self._q = vivos
        except Exception as e:
            print(f"[rastro] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)
        return False


class LotePixels:
    """Pixels quadrados de poucas cores, um Mesh por cor: bem mais leve no
    celular que um Rectangle por pixel. cores = ((nome, rgba), ...);
    desenhar({nome: [(x, y, lado) ou (x, y, largura, altura), ...]})."""

    def __init__(self, canvas, cores):
        self.m = {}
        with canvas:
            for nome, rgba in cores:
                c = Color(*rgba)
                self.m[nome] = (c, rgba[3], Mesh(mode='triangles', vertices=[], indices=[]))

    def desenhar(self, pontos, alfa=1.0):
        for nome, (c, a0, mesh) in self.m.items():
            vs, ids = [], []
            for i, r in enumerate(pontos.get(nome, ())):
                x, y, w = r[0], r[1], r[2]
                h = r[3] if len(r) > 3 else w
                vs.extend((x, y, 0, 0, x + w, y, 0, 0, x + w, y + h, 0, 0, x, y + h, 0, 0))
                b = 4 * i
                ids.extend((b, b + 1, b + 2, b, b + 2, b + 3))
            mesh.vertices = vs
            mesh.indices = ids
            c.a = a0 * alfa


# ── fogo em quadros (flip-book de pixel art, como nos jogos) ─────────────
# Cada lingua de fogo e uma animacao de 8 quadros gerada uma vez (3 tamanhos,
# 3 variacoes, roxo e azul): miolo claro perto da base, corpo lilas/roxo,
# borda escura, ponta ondulada que tomba para tras, uma lambida do lado de
# vez em quando e uma gota que se solta e sobe. Na tela cada lingua e so um
# retangulo com textura: leve no celular.
_N_CHAMA = 8
_TAM_CHAMA = ((7, 14), (9, 20), (12, 28))
_PAL_CHAMA = {
    'roxo': ((66, 20, 128, 235), (128, 56, 235, 245), (194, 143, 255, 255), (247, 235, 255, 255)),
    'azul': ((22, 34, 120, 235), (60, 108, 245, 245), (140, 205, 255, 255), (240, 250, 255, 255)),
}
_TEX_CHAMA = {}


def _quadro_chama(w, h, f, n=_N_CHAMA, inclina=-0.3, semente=0):
    """Um quadro de uma lingua de fogo w x h texels (y=0 embaixo):
    {(x, y): nivel}, nivel 0 (borda escura) .. 3 (miolo claro). O ciclo de
    n quadros fecha (loop)."""
    dois_pi = 2 * math.pi
    fs = f / float(n)
    rnd = random.Random(semente * 1000 + f)
    out = {}

    def perfil(u):
        # larga embaixo (bojo em ~25% da altura), afina ate a ponta
        return (1.0 - u) ** 1.15 * (1.0 - 0.55 * math.exp(-u * 8.0))

    alt = h * (0.8 + 0.12 * math.sin(dois_pi * (fs + semente * 0.21)))    # a lingua respira
    lado = 1 if (semente % 2) else -1
    lambida = 0.5 + 0.5 * math.sin(dois_pi * (fs * 2 + semente * 0.4))    # lambida do lado
    solta_y = alt + (h - alt) * fs * 1.1 - 1
    solta_r = max(0.0, 1.2 - 1.3 * fs) * (w / 6.0)
    for y in range(h):
        u = y / max(1.0, alt)
        for x in range(w):
            melhor = None
            if u < 1.0:
                cx = (w - 1) / 2.0 + math.sin(dois_pi * (fs + u * 0.8 + semente * 0.37)) * u * w * 0.2 \
                    + inclina * u * alt * 0.3
                meia = (w / 2.0) * perfil(u) / 0.62
                d = abs(x - cx) / max(0.45, meia)
                melhor = (d, u)
                if lambida > 0.35:
                    u2 = (y - alt * 0.22) / max(1.0, alt * 0.55 * lambida)
                    if 0 <= u2 < 1:
                        cx2 = cx + lado * (1.2 + 2.2 * u2) * (w / 8.0)
                        m2 = (w / 4.2) * (1 - u2) ** 1.2
                        d2 = abs(x - cx2) / max(0.4, m2)
                        if d2 < d:
                            melhor = (d2 * 1.08 + 0.1, u + 0.12)
            if solta_r > 0.35:                                   # gota de fogo que se soltou
                bx = (w - 1) / 2.0 + inclina * alt * 0.3 + math.sin(dois_pi * fs) * 0.6
                db = math.hypot((x - bx) / max(0.6, solta_r), (y - solta_y) / max(0.8, solta_r * 1.6))
                if db <= 1.0 and (melhor is None or db < melhor[0]):
                    melhor = (db * 0.9 + 0.35, 0.9)
            if melhor is None:
                continue
            d, uu = melhor
            if d > 1.0 + rnd.uniform(-0.1, 0.04):
                continue
            if d < 0.26 and uu < 0.27:
                nivel = 3
            elif d < 0.56 and uu < 0.56:
                nivel = 2
            elif d < 0.82:
                nivel = 1
            else:
                nivel = 0
            if uu > 0.78:
                nivel = min(nivel, 1)
            out[(x, y)] = nivel
    return out


def _textura_chama(tam, pal, f, semente):
    chave = (tam, pal, f, semente)
    tex = _TEX_CHAMA.get(chave)
    if tex is None:
        w, h = _TAM_CHAMA[tam]
        buf = bytearray(w * h * 4)
        cores = _PAL_CHAMA[pal]
        for (x, y), n in _quadro_chama(w, h, f, semente=semente).items():
            i = (y * w + x) * 4
            buf[i:i + 4] = bytes(cores[n])
        dados = bytes(buf)
        tex = Texture.create(size=(w, h), colorfmt='rgba')
        tex.mag_filter = 'nearest'
        tex.min_filter = 'nearest'
        tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
        tex.add_reload_observer(lambda t, d=dados: t.blit_buffer(d, colorfmt='rgba', bufferfmt='ubyte'))
        _TEX_CHAMA[chave] = tex
    return tex


def preparar_chamas():
    """Gera os quadros do fogo aos poucos (alguns por quadro de tela), antes
    da transformacao: nada trava quando o fogo acende."""
    fila = [(t, p, f, s) for t in range(3) for p in ('roxo', 'azul') for s in range(3) for f in range(_N_CHAMA)]

    def _passo(dt):
        try:
            t0 = time.time()
            while fila and time.time() - t0 < 0.006:
                _textura_chama(*fila.pop(0))
            return bool(fila)
        except Exception as e:
            print(f"[chamas] preparar: {e}")
            return False
    Clock.schedule_interval(_passo, 0)


class ChamasReiatsu(Widget):
    """Fogo roxo da forma Mugetsu, na grade de pixels do Yoru. Cada lingua e
    uma animacao de pixel art (8 quadros) presa num ponto do contorno do
    corpo: as grandes nascem na cabeca, nos ombros e nas costas, as menores
    nos lados; cada uma vive um pouco, se apaga e nasce outra noutro ponto.
    Umas poucas sao azuladas. Brasas soltas sobem piscando. Liga sozinho
    quando a pose esta na forma Mugetsu. `frente=True`: linguas pequenas
    por cima dele (profundidade)."""

    def __init__(self, k, n_max=520, linguas=30, frente=False, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k = k
        self.frente = frente
        self._linguas = []
        with self.canvas:
            for _ in range(linguas):
                c = Color(1, 1, 1, 0)
                r = Rectangle(size=(0, 0))
                self._linguas.append({'c': c, 'r': r, 'vida': 0.0, 't': 1.0})
        self._brasas = []
        self._olhos = []                  # posicoes recentes dos olhos (rastro de luz)
        self._lote = LotePixels(self.canvas, (('b0', (0.62, 0.30, 1.0, 1.0)), ('b1', (0.86, 0.72, 1.0, 1.0)),
                                              ('b2', (1.0, 1.0, 1.0, 1.0)), ('o2', (0.42, 0.18, 0.78, 0.55)),
                                              ('o1', (0.70, 0.42, 1.0, 0.8)), ('o0', (0.96, 0.84, 1.0, 1.0))))
        self._ev = Clock.schedule_interval(self._tick, 1 / 30.)

    def _nascer(self, L, bordas, topo, base):
        a = random.choice(bordas)
        b = random.choice(bordas)
        tx, ty = a if a[1] >= b[1] else b            # prefere as bordas de cima
        altura = (ty - base) / float(max(1, topo - base))
        if self.frente:
            tam = 0
        elif altura > 0.72:
            tam = 2 if random.random() < 0.65 else 1
        elif altura > 0.4:
            tam = 1 if random.random() < 0.7 else 0
        else:
            tam = 0 if random.random() < 0.7 else 1
        L.update(tx=tx, ty=ty, tam=tam, pal='azul' if random.random() < 0.16 else 'roxo',
                 sem=random.randrange(3), f0=random.uniform(0, _N_CHAMA), t=0.0,
                 vida=random.uniform(0.45, 0.9) * (1.2 if tam == 2 else 1.0),
                 vel=random.uniform(10.0, 15.0))

    def _rastro_olhos(self, k, te):
        """Olhos em brasa: quando ele se mexe rapido, os olhos deixam um
        risco de luz roxa que some em poucos quadros."""
        olhos = []
        for (ex, ey) in olhos_texel(k._pose):
            if k.espelhar:
                ex = TW - 1 - ex
            olhos.append((k.x + ex * te, k.y + ey * te))
        self._olhos.append(olhos)
        del self._olhos[:-7]
        pontos = {}
        for i in range(len(self._olhos) - 1, 0, -1):
            idade = len(self._olhos) - 1 - i
            cor = 'o0' if idade < 1 else ('o1' if idade < 3 else 'o2')
            for (a, b) in zip(self._olhos[i], self._olhos[i - 1]):
                d = math.hypot(b[0] - a[0], b[1] - a[1]) / te
                if d < 1.5:
                    continue
                n = int(d) + 1
                for j in range(n):
                    u = j / float(n)
                    x = a[0] + (b[0] - a[0]) * u
                    y = a[1] + (b[1] - a[1]) * u
                    pontos.setdefault(cor, []).append(
                        (k.x + math.floor((x - k.x) / te) * te, k.y + math.floor((y - k.y) / te) * te, te))
        self._lote.desenhar(pontos)

    def _tick(self, dt):
        try:
            k = self.k
            if k.parent is None or self.get_root_window() is None:
                return self.parar()
            te = k.ps / float(R)
            pose = k._pose
            ativo = pose.get('mugetsu') and k.opacity > 0.3
            bordas = bordas_pose(pose) if ativo else None
            if not bordas:
                for L in self._linguas:
                    L['c'].a = 0
                    L['vida'] = 0.0
                self._brasas = []
                self._olhos = []
                self._lote.desenhar({})
                return
            topo = max(y for _, y in bordas)
            base = min(y for _, y in bordas)
            ox, oy = k.x, k.y
            esp = k.espelhar
            for L in self._linguas:
                L['t'] += dt
                if L['t'] >= L['vida']:
                    self._nascer(L, bordas, topo, base)
                    L['t'] = random.uniform(0, 0.1)
                w, h = _TAM_CHAMA[L['tam']]
                f = int(L['t'] * L['vel'] + L['f0']) % _N_CHAMA
                tex = _textura_chama(L['tam'], L['pal'], f, L['sem'])
                x0 = L['tx'] - w // 2
                y0 = L['ty'] - (1 if self.frente else 3)             # a base entra no corpo
                if esp:
                    x0 = TW - x0 - w
                r = L['r']
                r.texture = tex
                r.tex_coords = _TC_ESPELHO if esp else _TC_NORMAL
                r.pos = (ox + x0 * te, oy + y0 * te)
                r.size = (w * te, h * te)
                u = L['t'] / L['vida']
                a = min(1.0, L['t'] / 0.08) * (1.0 if u < 0.75 else max(0.0, (1 - u) / 0.25))
                L['c'].a = a * (0.85 if self.frente else 1.0)
            if self.frente:
                self._rastro_olhos(k, te)
            # brasas: pixels soltos subindo, balancando e piscando
            if not self.frente:
                while len(self._brasas) < 16:
                    bx, by = random.choice(bordas)
                    self._brasas.append({'x': float(bx), 'y': float(by), 'vy': random.uniform(22, 40),
                                         'fase': random.uniform(0, 6.3), 't': 0.0, 'vida': random.uniform(0.5, 1.1)})
                pontos = {}
                vivas = []
                for b in self._brasas:
                    b['t'] += dt
                    if b['t'] >= b['vida']:
                        continue
                    vivas.append(b)
                    b['y'] += b['vy'] * dt
                    lx = b['x'] + math.sin(b['fase'] + b['t'] * 7) * 1.5 - b['t'] * 6
                    tx = (TW - 1 - lx) if esp else lx
                    u = b['t'] / b['vida']
                    if u > 0.7 and int(b['t'] * 20) % 2:
                        continue                                   # pisca antes de sumir
                    nome = 'b2' if u < 0.2 else ('b1' if u < 0.55 else 'b0')
                    pontos.setdefault(nome, []).append((ox + round(tx) * te, oy + round(b['y']) * te, te))
                self._brasas = vivas
                self._lote.desenhar(pontos)
        except Exception as e:
            print(f"[chamas] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)
        return False
