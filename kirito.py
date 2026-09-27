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
    'X': (0.85, 0.97, 1.00, 0.55), 'x': (0.50, 0.85, 1.00, 0.35),
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
}
_SEM_CONTORNO = set('xX!1FfL')
# Mugetsu: a roupa escurece (o rosto continua claro, os olhos acendem)
_SOMBRA = {'C': 'D', 'c': 'd', 'A': 'd', 'q': 'D', 'P': 'D', 'B': 'D', 'M': 'D', 'G': 'd', 'E': 'V',
           '2': 'D', '4': 'D', '7': 'D', 'e': 'V', 'n': 'L', 'K': 'D'}
_CORPO_M = set('HhSsDdVJIeT')
# luz dinamica: pixels do corpo perto da lamina acesa clareiam um degrau
_LAMINA = set('wjRrzY9!')                  # so as partes claras (a bainha usa W/u)
_ACENDE = {'C': 'c', 'A': 'c', 'q': 'c', 'P': 'c', 'c': 'Q', 'H': 'h', 'h': 'Q', 'B': 'K',
           'M': 'g', 'G': 'Q', 'D': 'd', 'd': 'o', '2': 'C', '4': 'C', '7': 'P', 'J': 'H', 'I': 'h'}


def _iluminar(px, luz, esc=1):
    """Luz da lamina no corpo: os pixels encostados nela sobem 2 degraus
    (ate o azul aceso), os de 2 px de distancia sobem 1. Sem blur: so troca
    de cor em clusters."""
    lamina = [q for q, ch in px.items() if ch in _LAMINA]
    if not lamina:
        return
    r = (2 if luz >= 0.75 else 1) * esc
    dist = {}
    for (x, y) in lamina:
        for ox in range(-r, r + 1):
            for oy in range(-r, r + 1):
                d = max(abs(ox), abs(oy))
                q = (x + ox, y + oy)
                if d and dist.get(q, 9) > d:
                    dist[q] = d
    for q, d in dist.items():
        ch = px.get(q)
        if ch in _ACENDE:
            ch = _ACENDE[ch]
            if d <= esc and luz >= 0.75 and ch in _ACENDE:
                ch = _ACENDE[ch]
            px[q] = ch

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
_PERNAS = {
    # em pe: 7 linhas (coxa, joelho, canela, bota). O sobretudo cobre as 5
    # primeiras e a barra fica no meio da canela, como um sobretudo longo.
    'repouso':  ["....PP.PP....", "....PP.PP....", "....PP.PP....", "....PP.PP....",
                 "....PP.PP....", "....BB.BB....", "...BBB.BBB..."],
    'avanco':   ["....PP..PP...", "....PP...PP..", "...PP....PP..", "...PP.....PP.",
                 "..PP......PP.", "..BB......BB.", ".BBB......BBB"],
    'suspenso': ["....PP.PP....", "....PP.PP....", "....PP..PP...", "....PP..PP...",
                 "...PP...PP...", "...PP....PP..", "...BB....BB.."],
    'pendente': ["....PP.PP....", "....PP.PP....", "....PP..PP...", "....PP..PP...",
                 "....PP..PP...", "....BB..BB...", "....BB...BB.."],
    # pendurado: pernas soltas, pontas dos pes para baixo (2 quadros de balanco)
    'solto':    ["....PP.PP....", "....PP.PP....", "....PP.PP....", "....PP.PP....",
                 "....PP..PP...", "....BB..BB...", ".....B...B..."],
    'solto2':   ["....PP.PP....", "....PP.PP....", "....PP.PP....", "...PP..PP....",
                 "..PP...PP....", "..BB...BB....", "..B.....B...."],
    # dobradas: 4 linhas
    'agachado': ["..PPP..PPP...", "..PP....PPP..", "..PP.....PP..", "..BBB...BBBB."],
    'pulo':     ["...PPP.PPP...", "...PP...PP...", "...PP...PP...", "....BB..BB..."],
    'grudado':  [".PPP...PPP...", ".PP.....PP...", ".PP.....PP...", ".BB.....BB..."],
    # quadros do meio (entram sozinhos na troca de pernas, ver _TRANS_PERNAS):
    # meio passo (em pe -> avanco), avanco baixo (agachado -> avanco),
    # joelhos dobrando (em pe -> agachado) e o balanco solto do meio
    'passo':    ["....PP.PP....", "....PP..PP...", "...PP...PP...", "...PP....PP..",
                 "...PP....PP..", "...BB....BB..", "..BBB....BBB."],
    'avanco_baixo': ["...PP..PPP...", "..PP.....PP..", "..PP......PP.", ".BB.......BB.",
                     "BBB.......BBB"],
    'dobra':    ["...PPP.PPP...", "...PP...PP...", "...PP....PP..", "...PP....PP..",
                 "...BB...BBB..", "..BBB...BBBB."],
    'solto_meio': ["....PP.PP....", "....PP.PP....", "....PP.PP....", "....PP.PP....",
                   "...PP...PP...", "...BB...BB...", "...B.....B..."],
}

# troca de pernas entre duas chaves: passa por um quadro do meio (o corpo
# desce/sobe junto, sem pular de uma altura para a outra)
_TRANS_PERNAS = {
    ('repouso', 'avanco'): 'passo', ('avanco', 'repouso'): 'passo',
    ('agachado', 'avanco'): 'avanco_baixo', ('avanco', 'agachado'): 'avanco_baixo',
    ('repouso', 'agachado'): 'dobra', ('agachado', 'repouso'): 'dobra',
    ('solto', 'solto2'): 'solto_meio', ('solto2', 'solto'): 'solto_meio',
    ('solto', 'pulo'): 'dobra', ('solto2', 'pulo'): 'dobra',
    ('avanco', 'pulo'): 'suspenso', ('pulo', 'avanco'): 'suspenso',
    ('repouso', 'pulo'): 'suspenso', ('pulo', 'repouso'): 'suspenso',
    ('suspenso', 'agachado'): 'dobra', ('agachado', 'suspenso'): 'dobra',
    ('suspenso', 'avanco'): 'passo', ('avanco', 'suspenso'): 'passo',
}


def altura(p):
    """Altura do quadril (em px da grade) acima da sola da bota."""
    return len(_PERNAS[p['pernas']]) + p['dy']

GW, GH = 80, 72          # grade total (espadas cabem para qualquer lado, ate a fundida erguida)
_X0 = 25                 # coluna esquerda do tronco/cabeca
_PES = 14                # linha dos pes (sobra embaixo para espadas apontando p/ baixo)


def _estampar(px, mapa, x0, y_topo):
    for r, linha in enumerate(mapa):
        for c, ch in enumerate(linha):
            if ch != '.':
                px[(x0 + c, y_topo - r)] = ch


_CORPO = set('CcAqGPBMSsHhE24JIen7')           # cores de corpo/roupa (para o contorno do braco)


def _p(x, y):
    return (round(x), round(y))


_GUARDA_INF = [(0, -2), (0, -1), (0, 1), (0, 2), (1, -3), (1, 0), (1, 3),
               (2, -2), (2, -1), (2, 1), (2, 2)]


def _cabo_nas_costas(px, x, y, tipo):
    """Cabo da Dark Repulser aparecendo por cima do ombro (bainha nas costas)."""
    guarda, ponta = ('g', 'k') if tipo == 1 else ('y', 'Y')
    px[(x - 2, y)] = ponta
    px[(x - 1, y)] = guarda
    px[(x, y)] = guarda
    px[(x + 1, y)] = guarda
    px[(x + 2, y)] = ponta
    px[(x, y + 1)] = 'K'
    px[(x, y + 2)] = 'K'
    px[(x, y + 3)] = guarda if tipo == 1 else 'Y'


# bainha da Elucidator: da cintura para tras e para baixo, rente a aba de tras
# do sobretudo (mais na horizontal ela saia do corpo e parecia um rabo)
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
                 m1=(3, -5), a1=-40.0, c1=15, s1=None,
                 m2=None, a2=None, c2=15, s2=None)


# ═══════════════════════════════════════════════════════════════════
#  MONTAGEM EM DOBRO DE PIXELS
#  As poses continuam na grade de sempre (unidades). O desenho e feito em
#  texels, 2 por unidade: o mesmo tamanho na tela, com o dobro de detalhe
#  (rosto, mechas, dobras, maos e laminas) e contorno mais fino.
# ═══════════════════════════════════════════════════════════════════
R = 2
TW, TH = GW * R, GH * R


def _t(v):
    """Unidade de pose -> texel (canto de baixo/esquerda da unidade)."""
    return int(math.floor(v * R + 1e-6))


def _dobrar(mapa):
    return [''.join(ch * R for ch in linha) for linha in mapa for _ in range(R)]


def _up(px, t):
    """Desenho feito na grade de unidades -> blocos de 2x2 texels."""
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


# ── cabeca 26 x 22: cabelo em 4 tons com mechas, franja em pontas,
#    olho grande com cilio, iris em 2 tons e brilho; sombra e maxilar
_CAB2 = [
    "..........................",
    "........JJHHJJJHHHJJ......",
    ".....JJJHHHHHHHHHHHHHJ....",
    "....JHHHHHHHHHHHHHHHHHJ...",
    "..JJHHHHHHHHHHHHHHHHHHHJ..",
    "..JHHHHHHIIhhhhIIHHHHHHJ..",
    ".JHHHHHIIHHHHHHHHIIHHHHHJ.",
    "JHHHHHHHHHHHHHHHHHHHHHHHHJ",
    "JHHJHHHHHHHHHHHHHHHHIHHHHJ",
    "JHJHHHHHHHHHHHHHHHHIhHHHHH",
    "JHHJHHHHHHHHHHHHHHHHHHHHHH",
    "JJHHJHHHHHHHsHHHHsHHHHsHHH",
    "JHHHJHHHHHsSsHHHsSsHHsSSHH",
    "JHHHHJHHHHsSSSSHSSSSSsHSSs",
    "JHHHHHHHHsSSSSEEEESSSSEESS",
    ".JHHHHHHHsSSSSeEneSSSSeESs",
    ".JHHHHHHsSSSSSemmeSSSSmeSs",
    "..JHHHHHsSSSSSSssSSSSSSSsS",
    "..JHHHHsSSSSSSSSSSSSSSsS..",
    "...JHHHsSSSSSSSSSSSssSS...",
    "....JHHHsSSSSSSSSSSSSs....",
    "......JHHsssSSSSSss.......",
]
_OLHOS = [(c, r) for r in (14, 15, 16) for c in (14, 15, 16, 17, 22, 23)]


def _cab2(trocas):
    c = [list(linha) for linha in _CAB2]
    for (col, r) in _OLHOS:                    # olhos limpos (pele)
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


_OLHO_ABERTO = _junta(_linha_olho(14, 14, "EEEE"), _linha_olho(15, 14, "eEne"), _linha_olho(16, 14, "emme"),
                      _linha_olho(14, 22, "EE"), _linha_olho(15, 22, "eE"), _linha_olho(16, 22, "me"))
_SOBRANCELHA = _junta(_linha_olho(12, 13, "E"), _linha_olho(13, 14, "EEEE"),
                      _linha_olho(13, 21, "EE"), _linha_olho(12, 23, "E"))
_CABECAS2 = {
    'a': _cab2(_OLHO_ABERTO),
    'f': _cab2(_junta(_linha_olho(15, 14, "EEEE"), _linha_olho(15, 22, "EE"))),
    'b': _cab2(_junta(_linha_olho(15, 14, "EEEE"), _linha_olho(16, 14, "eEne"), _linha_olho(17, 14, "emme"),
                      _linha_olho(15, 22, "EE"), _linha_olho(16, 22, "eE"), _linha_olho(17, 22, "me"))),
    's': _cab2(_junta(_SOBRANCELHA, _linha_olho(14, 14, "EEEE"), _linha_olho(15, 14, "eEne"),
                      _linha_olho(14, 22, "EE"), _linha_olho(15, 22, "eE"))),
    'g': _cab2(_junta(_SOBRANCELHA, _linha_olho(14, 14, "EEEE"), _linha_olho(15, 14, "eEne"),
                      _linha_olho(14, 22, "EE"), _linha_olho(15, 22, "eE"),
                      _linha_olho(19, 18, "EEE"), _linha_olho(20, 18, "ETE"))),
    'l': _cab2(_junta(_SOBRANCELHA, _linha_olho(14, 14, "9999"), _linha_olho(15, 14, "9!!9"),
                      _linha_olho(14, 22, "99"), _linha_olho(15, 22, "9!"))),
    'u': _cab2(_junta(_linha_olho(13, 14, "EEEE"), _linha_olho(14, 14, "enee"), _linha_olho(15, 14, "eEEe"),
                      _linha_olho(16, 14, "meem"), _linha_olho(13, 22, "EE"), _linha_olho(14, 22, "ne"),
                      _linha_olho(15, 22, "eE"), _linha_olho(16, 22, "me"),
                      _linha_olho(19, 19, "EE"), _linha_olho(20, 19, "EE"))),
    'e': _cab2(_junta(_linha_olho(14, 15, "EE"), _linha_olho(15, 14, "E..E"), _linha_olho(14, 22, "EE"),
                      _linha_olho(19, 18, "sSSs"), _linha_olho(20, 19, "ss"))),
}

# ── tronco 26 x 16: gola alta, pescoco, abertura em V com a camisa preta,
#    friso prateado, dobras, cinto com fivela vazada
_TOR2 = [
    "......2CCcsSSSsCcc........",
    "......2CCcsSSSsCAcc.......",
    "......2CCCGG44GGAcc.......",
    "......2CCCGk44kGAAcc......",
    "....22CCCCCG44GCCCAAcc....",
    "....2CCCCCCGk4GCCCAAAc....",
    "....2CCcCCCCGGCCCCAAAc....",
    "....2CCcCCCCGkCCC2AAAc....",
    "....22CcCCCCGGCC2CAAAc....",
    "....2CCcCCCCGkC2CCAAAc....",
    "..22CCCcCCCCGGC2CCCAAAcc..",
    "..2CCCCcCCCCGkCC2CCAAAcc..",
    "..2MMMMMMMMgkkgMMMMMMMMc..",
    "..2MMMMMMMMgMMgMMMMMMMMc..",
    "..22CCCCCCPPPPPPCCCCAAcc..",
    "..22CCCCCC7PPPP7CCCCAAcc..",
]
for _m in (_CAB2, _TOR2) + tuple(_CABECAS2.values()):
    assert all(len(_l) == 26 for _l in _m), 'mapa 2x com largura errada'


def _pernas2(px, mapa, x0, y_topo):
    """Pernas em texels: lado de tras na sombra, brilho na ponta da bota."""
    m2 = _dobrar(mapa)
    ult = len(m2) - 1
    for r, linha in enumerate(m2):
        for c, ch in enumerate(linha):
            if ch == '.':
                continue
            antes = linha[c - 1] if c > 0 else '.'
            depois = linha[c + 1] if c + 1 < len(linha) else '.'
            if ch == 'P' and antes != 'P':
                ch = '7'
            elif ch == 'B' and r == ult - 1 and depois != 'B':
                ch = 'K'                             # biqueira da bota
            px[(x0 + c, y_topo - r)] = ch


def _sobretudo2(px, bx, y0, n, capa, lift, fase, pernas, saia):
    """Saia do sobretudo em texels: abas com borda de luz, friso e forro,
    dobras em diagonal (sombra + luz) que andam com o pano, barra com
    espessura. Mesma forma da versao de unidades, so que mais fina."""
    ultima = pernas[-1]
    xs = [x for x, ch in enumerate(ultima) if ch != '.']
    p_min, p_max = R * (_X0 + min(xs)), R * (_X0 + max(xs)) + R - 1
    amp = 0.55 + 0.25 * min(3.0, abs(capa))
    dois_pi = 2 * math.pi
    nb0 = R * (len(pernas) - 1)
    total = R * n
    mv = int(fase * 8)
    for kk in range(total):
        k = kk / float(R)
        u = k / float(max(1, n - 1))
        onda = amp * u * math.sin(dois_pi * (fase - k / float(n)))
        y = _t(y0) + R - 1 - kk + int(round(lift * k * 0.28 * R))
        abre = 0.45 * k * saia
        vento = max(-1.0, min(1.6, capa)) * 0.45 * k
        xe0 = _t(bx + 1 - (abre + vento + onda))
        xe1 = _t(bx + 4 - vento * 0.30) + R - 1
        xd0 = _t(bx + 8 - vento * 0.45)
        xd1 = _t(bx + 11 + abre - (vento * 0.55 + onda * 0.5)) + R - 1
        barra = kk >= total - 2
        nas_botas = nb0 <= kk < nb0 + R
        for (a, b, lado) in ((xe0, xe1, 'e'), (xd0, xd1, 'd')):
            if b < a:
                a, b = b, a
            for x in range(a, b + 1):
                if nas_botas and p_min <= x <= p_max:
                    continue
                if barra:
                    ch = 'c' if kk == total - 2 else '2'
                elif (lado == 'e' and x == a) or (lado == 'd' and x == b):
                    ch = 'c'
                elif (lado == 'e' and x == b) or (lado == 'd' and x == a):
                    ch = 'q' if vento > 1.2 else 'G'
                elif (lado == 'e' and x == b - 1) or (lado == 'd' and x == a + 1):
                    ch = 'q' if vento > 0.6 else '2'     # forro / sombra junto do friso
                else:
                    d = (x + kk + mv) % 7
                    if lado == 'e':
                        ch = '2' if (d == 0 or x == a + 1) else 'C'
                    else:
                        ch = '2' if d == 0 else ('A' if d == 1 else 'C')
                px[(x, y)] = ch


def _cabelo_tras2(px, cx, ty, cb, sobe, fase):
    """Mechas de tras em texels: 2 texels cada (luz em cima, sombra embaixo),
    afinando na ponta; as de cima pegam brilho."""
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
            ponta = i2 >= n2 - 2
            if linha <= 3 and 1 <= i2 <= 3:
                cima = 'I'
            elif ponta and linha in (3, 5):
                cima = 'h'
            else:
                cima = 'H'
            px[(x, y)] = cima
            if not ponta:
                px[(x, y - 1)] = 'J' if linha >= 5 else 'H'


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
        alto = alto + int(round(sobe * 3 * (0.6 + 0.4 * math.sin(dois_pi * (fase * 1.5 + fx)))))
        deita = 0.35 + 0.5 * sobe                        # tomba para tras com o vento
        for h in range(alto):
            xx = x - int(round(h * deita))
            larg = 2 if h < alto // 2 else 1              # afina na ponta
            for w in range(larg):
                px[(xx + w, ty + 1 + h)] = 'J' if h == alto - 1 else ('I' if (w == 1 and h == 0) else 'H')


def _cabelo_longo2(px, cx, ty, cb, sobe, fase, y_joelho):
    """Mugetsu: cabelao preto ate os joelhos, solto em mechas, ondulando;
    com o reiatsu ele levanta e voa para tras."""
    dois_pi = 2 * math.pi
    vento = min(0.9, max(0.0, cb) * 0.2 + sobe * 0.5)
    fios = ((4, -4), (6, -6), (2, -7), (5, -9), (1, -10), (3, -12), (7, -11), (0, -14), (4, -16))
    for fio, (x0, y0) in enumerate(fios):
        n = max(12, int(((ty + y0) - y_joelho) * (1.0 - vento * 0.25)))
        for k in range(n):
            u = k / float(n - 1)
            onda = (1.4 + 1.8 * sobe) * u * math.sin(dois_pi * (fase * 1.2 - k / 14.0 - fio * 0.19))
            x = cx + x0 - int(round(k * (0.34 + vento * 0.95) + onda))
            y = ty + y0 - int(round(k * (1.0 - vento * 0.75)))
            if fio in (0, 4, 8):
                ch = 'J'
            elif (k + fio * 3) % 12 == 0:
                ch = 'I'
            else:
                ch = 'H'
            px[(x, y)] = ch
            if k < n - 4:
                px[(x - 1, y)] = 'J' if fio % 2 else 'H'


def _braco2(px, x0, y0, x1, y1, luva=True, frente=False):
    """Braco com manga em texels (5 de largura): luz, meio-tom, base e
    sombra; ombro arredondado, punho prateado e luva com brilho."""
    dx, dy = x1 - x0, y1 - y0
    L = max(1.0, math.hypot(dx, dy))
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    if nx * 0.6 + ny * 0.8 < 0:                  # normal apontando para a luz
        nx, ny = -nx, -ny
    tons = ({2: 'c', 1: 'A', 0: 'A', -1: 'C', -2: '2'} if frente
            else {2: 'c', 1: 'C', 0: 'C', -1: '2', -2: '2'})
    meu = {}
    passos = int(L * 2) + 1
    for i in range(passos + 1):
        t = i / 2.0
        punho = t >= L - 3.5 and L > 6
        for j in (-2, -1, 0, 1, 2):
            q = (int(round(x0 + ux * t + nx * j)), int(round(y0 + uy * t + ny * j)))
            if punho:
                meu[q] = 'k' if j == 2 else 'G'
            else:
                meu[q] = tons[j]
    for ox in (-2, -1, 0, 1, 2):                   # ombro arredondado
        for oy in (-2, -1, 0, 1, 2):
            if ox * ox + oy * oy <= 5:
                meu[(x0 + ox, y0 + oy)] = 'c' if (ox + oy) >= 2 else ('A' if frente else 'C')
    if luva:
        for ox in (-1, 0, 1, 2):
            for oy in (-1, 0, 1, 2):
                meu[(x1 + ox, y1 + oy)] = 'M'
        meu[(x1 + 2, y1 + 2)] = 'g'
        meu[(x1 + 1, y1 + 2)] = 'g'
        meu[(x1 + 2, y1 + 1)] = 'K'
    if frente:                                    # contorno escuro por cima do corpo
        for (x, y) in meu:
            for vx, vy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + vx, y + vy)
                if q not in meu and px.get(q) in _CORPO:
                    px[q] = 'B'
    px.update(meu)


def _rastro2(px, hx, hy, de, ang, comp):
    """Smear em texels: leque de pixels do angulo `de` ate a lamina."""
    passo = 4 if de < ang else -4
    g = de
    L = comp * R
    while (passo > 0 and g < ang) or (passo < 0 and g > ang):
        ga = math.radians(g)
        c, sn = math.cos(ga), math.sin(ga)
        for k in range(int(L * 0.45), L + 1):
            q = (int(round(hx + c * k)), int(round(hy + sn * k)))
            if q not in px:
                px[q] = 'x' if k < L * 0.75 else 'X'
        g += passo


def _katana2(px, hx, hy, ux, uy, nx, ny, comp, brilho):
    """Elucidator: cabo trancado em losangos, kashira, tsuba oval, habaki e
    lamina curva com costas, miolo preto, hamon ondulado, fio e reflexos."""
    def pp(k, j, ch):
        px[(int(round(hx + ux * k + nx * j)), int(round(hy + uy * k + ny * j)))] = ch
    for k in range(1, 11):
        for j in (-1, 0, 1):
            pp(-k, j, 'k' if (k + 2 * j) % 4 == 0 else ('g' if j == 1 else 'K'))
    for j in (-1, 0, 1):
        pp(-11, j, 'k')
        pp(-12, j, 'g')
    L = comp * R
    if L < 2:
        return
    for k in (1, 2):
        for j in range(-4, 5):
            pp(k, j, 'k' if (j >= 2 and k == 1) else ('g' if abs(j) >= 3 else 'K'))
    if L < 4:
        return
    for j in (-1, 0, 1, 2):
        pp(3, j, '+' if j == 2 else 'k')
    sori = max(1.5, L * 0.13)
    ini = 4
    ref = ini + int((L - ini) * 0.3)
    for k in range(ini, L + 1):
        u = (k - ini) / float(max(1, L - ini))
        off = -sori * u * u
        corta = max(0, k - (L - 4))              # afina no kissaki
        for j in range(-2 + corta, 3):
            if j == 2:
                ch = '+' if (ref <= k <= ref + 2 or k >= L - 1) else 'w'
            elif j == 1:
                ch = 'w' if ref <= k <= ref + 2 else ('j' if math.sin(k * 0.8) > 0 else 'W')
            elif j == -2 or j == -2 + corta:
                ch = 'u'
            else:
                ch = 'W'
            pp(k, off + j, ch)
    if brilho is not None:
        k = ini + int(brilho * (L - ini))
        u = (k - ini) / float(max(1, L - ini))
        off = -sori * u * u
        for kk in (k, k - 1):
            pp(kk, off + 2, '!')
            pp(kk, off + 1, '1')


def _repulser2(px, hx, hy, ux, uy, nx, ny, comp, brilho):
    """Dark Repulser: lamina reta de cristal com facetas, fio claro, reflexo;
    guarda em cruz com pontas de cristal e gema; cabo curto com pomo."""
    def pp(k, j, ch):
        px[(int(round(hx + ux * k + nx * j)), int(round(hy + uy * k + ny * j)))] = ch
    for k in range(1, 7):
        for j in (-1, 0, 1):
            pp(-k, j, 'y' if (k % 3 == 0) else 'K')
    for j in (-1, 0, 1):
        pp(-7, j, 'Y')
    L = comp * R
    for k in (1, 2):
        for j in range(-5, 6):
            pp(k, j, 'Y' if abs(j) >= 4 else ('r' if abs(j) <= 1 else 'y'))
    pp(1, 1, 'n')
    ref = 3 + int((L - 3) * 0.35)
    for k in range(3, L + 1):
        corta = max(0, k - (L - 3))
        for j in range(-2 + corta, 3 - corta):
            if j == 2 or (j == 2 - corta and corta):
                ch = '+' if ref <= k <= ref + 2 else 'r'
            elif j == -2 + corta:
                ch = 'z'
            elif j == 0:
                ch = 'r' if k % 6 in (1, 2) else 'R'
            elif j == 1:
                ch = 'Y' if k % 6 in (2, 3) else 'r'
            else:
                ch = 'R'
            pp(k, j, ch)
    pp(L + 1, 0, 'r')
    if brilho is not None:
        k = 3 + int(brilho * (L - 3))
        for kk in (k, k - 1):
            pp(kk, 1, '!')
            pp(kk, 0, '1')


_INF = []
for _i in range(96):                             # simbolo do infinito (lemniscata)
    _a = 2 * math.pi * _i / 96.0
    _d = 1 + math.sin(_a) ** 2
    _INF.append((math.cos(_a) / _d, math.sin(_a) * math.cos(_a) / _d))


def _fundida2(px, hx, hy, ux, uy, nx, ny, comp, brilho, evo, fase):
    """As duas espadas fundidas: lamina larga e pesada (9 texels) preta, com
    costas de aco, fio aceso (cristal azul; evoluida: roxo-azul e branco),
    veios de energia que correm pela lamina e guarda em cruz (evoluida: o
    simbolo do infinito). Cabo longo trancado."""
    def pp(k, j, ch):
        px[(int(round(hx + ux * k + nx * j)), int(round(hy + uy * k + ny * j)))] = ch
    fita = 'F' if evo else 'y'
    for k in range(1, 13):
        for j in (-1, 0, 1):
            pp(-k, j, fita if (k + 2 * j) % 4 == 0 else ('g' if j == 1 else 'K'))
    for j in (-2, -1, 0, 1, 2):
        pp(-13, j, 'L' if evo else 'Y')
    pp(-14, 0, 'L' if evo else 'Y')
    L = comp * R
    if evo:
        for (cx, cy) in _INF:
            pp(2.5 + cy * 4.0, cx * 7.0, 'Y')
        for j in (-4, 4):
            pp(2.5, j, '9')
        pp(2.5, 0, '!')
        ini = 6
    else:
        for k in (1, 2, 3):
            for j in range(-6, 7):
                if k == 2 or abs(j) <= 4:
                    pp(k, j, 'Y' if abs(j) >= 5 else ('r' if abs(j) <= 1 else ('k' if k == 1 else 'y')))
        ini = 4
    fio, fio2, fio3 = ('!', 'f', 'F') if evo else ('r', 'R', 'z')
    mv = int(fase * 12)
    for k in range(ini, L + 1):
        corta = max(0, k - (L - 6))
        veia = int(round(math.sin(k * 0.35 + 1.3))) - 1
        for j in range(-4 + corta, 5):
            if j == 4:
                ch = fio
            elif j == 3:
                ch = fio2
            elif j == 2:
                ch = fio3
            elif j == -4 + corta:
                ch = 'u'
            elif j == veia and (k + mv) % 9 < (5 if evo else 3):
                ch = ('9' if (k + mv) % 9 < 2 else 'V') if evo else 'z'
            elif j == 1:
                ch = 'K'                                   # aresta central (shinogi)
            elif j == -3 + corta:
                ch = '2'                                   # chanfro das costas
            else:
                ch = 'W'
            pp(k, j, ch)
    pp(L + 1, 4, fio)
    pp(L + 2, 4, fio)
    if brilho is not None:
        k = ini + int(brilho * (L - ini))
        for j in range(0, 5):
            pp(k, j, '!' if j >= 2 else '1')


def _espada2(px, hx, hy, ang, comp, tipo, smear_de=None, brilho=None, fase=0.0):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    if smear_de is not None and abs(smear_de - ang) > 8:
        _rastro2(px, hx, hy, smear_de, ang, comp)
    b = brilho if smear_de is None else None
    if tipo == 1:
        _katana2(px, hx, hy, ux, uy, nx, ny, comp, b)
    elif tipo == 2:
        _repulser2(px, hx, hy, ux, uy, nx, ny, comp, b)
    else:
        _fundida2(px, hx, hy, ux, uy, nx, ny, comp, b, tipo == 4, fase)


def _bainha2(px, bx, by):
    """Bainha (saya) da cintura: laca escura com filete claro em cima,
    sombra embaixo e ponteira de metal. Nao passa por cima das pernas."""
    a = math.radians(_BAINHA_ANG)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    L = _BAINHA_COMP * R

    def pinta(k, j, ch):
        q = (int(round(bx + ux * k + nx * j)), int(round(by + uy * k + ny * j)))
        if px.get(q) not in ('P', 'B', '7', 'K'):
            px[q] = ch
    for k in range(0, L):
        pinta(k, -1, 'v')
        pinta(k, 0, 'W')
        pinta(k, 1, 'u')
    for k in range(L, L + 4):
        for j in (-1, 0, 1):
            pinta(k, j, 'k' if j == -1 else 'g')


def _cabo_cintura2(px, bx, by):
    """Cabo da Elucidator guardada: tsuba e cabo trancado para fora."""
    a = math.radians(_BAINHA_ANG)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux

    def pp(k, j, ch):
        px[(int(round(bx + ux * k + nx * j)), int(round(by + uy * k + ny * j)))] = ch
    for j in range(-3, 4):
        pp(0, j, 'k' if j <= -2 else ('g' if abs(j) >= 2 else 'K'))
    for k in range(1, 11):
        for j in (-1, 0, 1):
            pp(-k, j, 'k' if (k + 2 * j) % 4 == 0 else ('g' if j == -1 else 'K'))
    for j in (-1, 0, 1):
        pp(-11, j, 'k')


def _fivelas2(px):
    botas = [q for q, ch in px.items() if ch in ('B', 'K') and q[1] < R * (_PES + 4)]
    if not botas:
        return
    topo = max(y for _, y in botas)
    for (x, y) in botas:
        if y == topo and px.get((x - 1, y)) in ('B', 'K') and px.get((x + 1, y)) not in ('B', 'K'):
            px[(x, y)] = 'k'
            px[(x - 1, y)] = 'G'


def _meia(v):
    return round(v * 2) / 2.0


def montar(p):
    """Pose (dict, em unidades) -> {(x, y) em texels: cor}."""
    px = {}
    dx, dy = _meia(p['dx']), _meia(p['dy'])
    pernas = _PERNAS[p['pernas']]
    topo = _PES + len(pernas) + len(_TRONCO) - 1 + dy       # linha de cima do tronco (unidades)
    base = _X0 + dx
    incl = int(round(p.get('incl', 0) or 0))
    fase = p.get('fase', 0.0) or 0.0
    cb = p['cabelo']
    sobe = max(0.0, min(1.2, p.get('sobe', 0.0) or 0.0))
    top_t = _t(topo) + R - 1                                 # texel de cima do tronco
    bx_t = _t(base)
    # ombros e cabeca vao com a inclinacao (peso)
    o1 = (_t(base + 9 + incl) + 1, _t(topo - 2) + 1)
    o2 = (_t(base + 3 + incl) + 1, _t(topo - 2) + 1)
    cab_x = _t(base + incl) + int(round(p.get('hx', 0) or 0))
    cab_ty = _t(topo + len(_CABECA)) + R - 1 + int(round(p.get('hy', 0) or 0))
    y_cinto = topo - 6
    boca = (_t(base + 9) + 1, _t(y_cinto) + 1)                 # boca da bainha
    mugetsu = p.get('mugetsu', False)

    def mao(ombro_u, m, t_o):
        return (int(round(R * (ombro_u[0] + m[0]))) + 1, int(round(R * (ombro_u[1] + m[1]))) + 1)

    if mugetsu:
        _cabelo_longo2(px, cab_x, cab_ty, cb, sobe, fase, R * (_PES + 3))

    if p['a2'] is None and not p.get('fusao'):
        t = {}
        _cabo_nas_costas(t, int(round(base + 1 + incl)), int(round(topo + 1)), 2)
        _up(px, t)

    m2 = p['m2'] if p['m2'] is not None else (-1, -6)
    h2 = mao((base + 3 + incl, topo - 2), m2, o2)
    ergue2 = m2[1] > 4
    acima2 = m2[1] > 10

    def _braco_tras():
        _braco2(px, o2[0], o2[1], h2[0], h2[1], frente=ergue2)
        if p['a2'] is not None:
            _espada2(px, h2[0], h2[1], p['a2'], int(p['c2']), 2, p['s2'], p.get('brilho'), fase)
            for ox in (0, 1):
                for oy in (0, 1):
                    px[(h2[0] + ox, h2[1] + oy)] = 'M'
    if not ergue2:
        _braco_tras()

    _cabelo_tras2(px, cab_x, cab_ty, cb, sobe, fase)
    _espetos2(px, cab_x, cab_ty, cb, sobe, fase)

    if ergue2 and not acima2:
        _braco_tras()

    _pernas2(px, pernas, R * _X0, R * (_PES + len(pernas) - 1) + R - 1)
    _sobretudo2(px, base, topo - len(_TRONCO), len(pernas) - 2 if len(pernas) > 4 else len(pernas) - 1,
                p['capa'], p['lift'], fase, pernas, p.get('saia', 1.0))
    _bainha2(px, boca[0], boca[1])
    # tronco: peito/ombros inclinam mais que a barriga (a cintura fica)
    for r, linha in enumerate(_TOR2):
        desl = 2 * incl if r < 6 else (incl if r < 10 else 0)
        y = top_t - r
        for c, ch in enumerate(linha):
            if ch != '.':
                px[(bx_t + desl + c, y)] = ch
    t = {}
    _alca_peito(t, int(round(base + incl)), int(round(topo)))
    _up(px, t)
    _fivelas2(px)

    m1 = p['m1']
    ergue = m1 is not None and m1[1] > 4 and not p.get('frente1')

    def _braco_frente():
        if m1 is None:
            return
        h1 = mao((base + 9 + incl, topo - 2), m1, o1)
        _braco2(px, o1[0], o1[1], h1[0], h1[1], frente=True)
        if p['a1'] is not None:
            _espada2(px, h1[0], h1[1], p['a1'], int(p['c1']), p.get('tipo1', 1), p['s1'],
                     p.get('brilho'), fase)
            for ox in (-1, 0, 1, 2):
                for oy in (0, 1):
                    px[(h1[0] + ox, h1[1] + oy)] = 'M'
            px[(h1[0] + 2, h1[1] + 1)] = 'g'
    if ergue:
        _braco_frente()
    _carimbo(px, _CABECAS2.get(p['olhos'], _CABECAS2['a']), cab_x, cab_ty)
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

    luz = p.get('luz', 0.0) or 0.0
    if luz > 0.2:
        _iluminar(px, luz, R)
    if mugetsu:
        for q, ch in list(px.items()):
            if ch in _SOMBRA:
                px[q] = _SOMBRA[ch]
    # contorno de 1 texel: luz em cima/na frente, sombra embaixo/atras
    aro, aro_sombra = ('o', '8') if mugetsu else ('O', '0')
    novos = {}
    for (x, y) in list(px.keys()):
        if px[(x, y)] in _SEM_CONTORNO:
            continue
        for vx, vy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            q = (x + vx, y + vy)
            if q not in px:
                ch = aro if (vx == 1 or vy == 1) else aro_sombra
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
    def r(k, v):
        if k in ('capa', 'cabelo', 'lift', 'sobe'):
            return round(v * 4) / 4.0            # fisica: passos de 0.25
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
        cam = [l0, l1]
        meio = _TRANS_PERNAS.get((l0, l1))
        if meio is not None:
            n0, n1, nm = len(_PERNAS[l0]), len(_PERNAS[l1]), len(_PERNAS[meio])
            if min(n0, n1) <= nm <= max(n0, n1):
                cam = [l0, meio, l1]
        q['pernas'] = cam[min(len(cam) - 1, max(0, int(tl * len(cam))))]
        h = altura(p0) + (altura(p1) - altura(p0)) * t
        q['dy'] = h - len(_PERNAS[q['pernas']])
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
_CACHE_MAX = 500
_TEX = OrderedDict()       # (chave_pose, silhueta) -> Texture
_TEX_MAX = 220
_RGBA = {c: bytes(int(round(v * 255)) for v in cor) for c, cor in _PALETA.items()}
_TC_NORMAL = (0, 0, 1, 0, 1, 1, 0, 1)
_TC_ESPELHO = (1, 0, 0, 0, 0, 1, 1, 1)


def _gerar_imagem(p):
    ch = _chave(p)
    item = _CACHE.get(ch)
    if item is not None:
        _CACHE.move_to_end(ch)
        return ch, item
    buf = bytearray(TW * TH * 4)
    x0 = y0 = 10 ** 6
    x1 = y1 = -10 ** 6
    px = montar(p)
    for (x, y), c in px.items():
        if 0 <= x < TW and 0 <= y < TH:
            i = (y * TW + x) * 4
            buf[i:i + 4] = _RGBA[c]
            if c not in 'xX':                 # rastro nao conta para o enquadramento
                x0, x1 = min(x0, x), max(x1, x)
                y0, y1 = min(y0, y), max(y1, y)
    # caixa em unidades da grade (as cenas trabalham nelas)
    cx = ((x0 / float(R), y0 / float(R), (x1 + 1) / float(R) - 1, (y1 + 1) / float(R) - 1)
          if x1 >= x0 else (_X0, _PES, _X0 + 12, _PES + 26))
    borda = bordas(px) if p.get('mugetsu') else None
    item = (bytes(buf), cx, borda)
    _CACHE[ch] = item
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)
    return ch, item


def _bytes(p):
    """Pose -> imagem RGBA (GW x GH) em bytes. Cache LRU; so Python puro
    (pode rodar antes do primeiro quadro, sem contexto grafico)."""
    ch, item = _gerar_imagem(p)
    return ch, item[0]


def caixa(p):
    """Retangulo ocupado pela pose (x0, y0, x1, y1), em unidades da grade."""
    return _gerar_imagem(p)[1][1]


def bordas_pose(p):
    """Contorno do corpo (texels) da pose na forma Mugetsu (ou None)."""
    return _gerar_imagem(p)[1][2]


def _runs(p, espelhar=False):
    """(compatibilidade) pre-gera a imagem da pose."""
    return _bytes(p)


def _textura(p, silhueta=False, xadrez=False):
    """Pose -> Texture pequena (1 retangulo por quadro, em vez de ~250:
    bem mais leve no celular). O espelho e feito por tex_coords."""
    ch, dados = _bytes(p)
    chave = (ch, silhueta, xadrez)
    tex = _TEX.get(chave)
    if tex is not None:
        _TEX.move_to_end(chave)
        return tex
    if silhueta:                         # branco com o alpha do boneco (tingido por Color)
        b = bytearray(dados)
        for i in range(0, len(b), 4):
            if b[i + 3]:
                b[i] = b[i + 1] = b[i + 2] = 255
                if xadrez:                   # afterimage: so metade dos pixels (pixel art)
                    j = i // 4
                    if ((j % TW) + (j // TW)) % 2:
                        b[i + 3] = 0
        dados = bytes(b)
    tex = Texture.create(size=(TW, TH), colorfmt='rgba')
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
    escala_x = NumericProperty(1.0)
    clarao = NumericProperty(0.0)          # 0..1: boneco todo branco (teleporte)

    def __init__(self, ps=4, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self.ps = max(2, int(ps) - int(ps) % 2)      # texel = ps/2 (pixels todos iguais)
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
        topo_tronco = _PES + len(pernas) + len(_TRONCO) - 1 + _meia(p['dy'])
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
            if self.clarao > 0:
                self._rect_clarao.texture = _textura(self._pose, silhueta=True)
                self._rect_clarao.tex_coords = self._rect.tex_coords
                self._rect_clarao.size = self._rect.size
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
                Rectangle(pos=(0, 0), size=self.size, texture=_textura(self._pose, silhueta=True, xadrez=True),
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
    # guardado: mao no cabo da Elucidator (na cintura), como um samurai em repouso
    'guardado':   pose(m1=(2, -3), a1=None),
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
    'arma1':      pose(pernas='avanco', dx=-1, m1=(0, 9), a1=112.0, m2=(4, 1)),
    'corta_desce': pose(pernas='avanco', dx=2, dy=-1, m1=(7, -2), a1=-38.0, m2=(-4, 2)),
    'segue_desce': pose(pernas='avanco', dx=2, dy=-1, m1=(4, -6), a1=-70.0, m2=(-4, 1)),
    # saca a Dark Repulser (mao de tras sobe ate o cabo nas costas)
    'pega2':      pose(pernas='avanco', dx=1, m1=(5, -4), a1=-40.0, m2=(-1, 8), a2=None),
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
    # embainhar (noto): a ponta da preta entra na boca da bainha da cintura e
    # desliza ate o clique; a azul volta para as costas
    # (angulo -138 = 222 - 360: vindo do chiburi a lamina desce pela frente
    # ate a boca da bainha, em vez de dar a volta por cima da cabeca)
    'embainha_a': pose(pernas='repouso', m1=(6, 1), a1=_BAINHA_ANG - 360, c1=8, m2=(-2, 9), a2=268.0, c2=10),
    'embainha_b': pose(pernas='repouso', m1=(3, -2), a1=_BAINHA_ANG - 360, c1=4, m2=(-2, 6), a2=268.0, c2=5),
    'embainha_c': pose(pernas='repouso', m1=(2, -3), a1=_BAINHA_ANG - 360, c1=0, m2=(-2, 5), a2=268.0, c2=0),
    # compatibilidade com cenas antigas
    'embainha':   pose(pernas='repouso', m1=(3, -2), a1=_BAINHA_ANG - 360, c1=4, m2=(-2, 6), a2=268.0, c2=5),
    'espreita':   pose(dy=1, m1=(3, 3), a1=None, m2=(-3, 3), a2=None, frente1=True),
    'espreita2':  pose(dy=3, m1=(3, 1), a1=None, m2=(-3, 1), a2=None, frente1=True),
    'x_arma':     pose(pernas='avanco', dx=-1, m1=(-3, 6), a1=135.0, m2=(-5, 6), a2=160.0),
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
    if altura(arma) > 3:
        ant['dy'] = arma['dy'] - 1                   # e abaixa (se nao estiver agachado)
    imp = dict(corta, olhos=olhos[1], incl=1)       # o peso vai para a frente no corte
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
    else:
        seg = dict(seg, olhos=olhos[1], incl=1)
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
    q['dy'] = max(-1, min(3, altura(p) - 4))
    return q


def esticado(p):
    """A mesma pose com as pernas esticadas (impulso do pulo / indo pousar)."""
    q = dict(p)
    q['pernas'] = 'suspenso'
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


class ChamasReiatsu(Widget):
    """Fogo roxo e azul da forma Mugetsu, com pixels do mesmo tamanho dos
    do Kirito. O fogo e feito de LINGUAS: cada uma nasce num ponto do
    contorno do corpo (mais na cabeca e nos ombros) e solta pixels um atras
    do outro, que sobem ondulando juntos - uma coluna de fogo que balanca,
    tomba para tras com o vento e esfria em degraus (branco -> ciano ->
    azul -> roxo -> roxo escuro). Acompanha o corpo. Liga sozinho quando a
    pose esta na forma Mugetsu. `frente=True`: camada fina por cima."""
    DEGRAUS = (((0.97, 0.93, 1.00), 1.0), ((0.55, 0.86, 1.00), 1.0), ((0.34, 0.55, 1.00), 0.95),
               ((0.60, 0.30, 1.00), 0.9), ((0.36, 0.15, 0.64), 0.72))

    def __init__(self, k, n_max=520, linguas=30, frente=False, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k = k
        self.frente = frente
        self.n_linguas = linguas
        self._linguas = []
        self._p = []
        self._ins = []
        with self.canvas:
            for _ in range(n_max):
                c = Color(1, 1, 1, 0)
                r = Rectangle(size=(0, 0))
                self._ins.append((c, r))
        self._livres = list(range(n_max))
        self._ev = Clock.schedule_interval(self._tick, 1 / 30.)

    def _nova_lingua(self, bordas):
        topo = max(y for _, y in bordas)
        a = random.choice(bordas)
        b = random.choice(bordas)
        tx, ty = a if a[1] >= b[1] else b            # prefere as bordas de cima
        alto = ty >= topo - 16
        vida = random.uniform(0.25, 0.5) * (1.3 if alto else 1.0)
        return {'tx': tx, 'ty': ty, 'vida': vida, 'fase': random.uniform(0, 6.3),
                'f': random.uniform(8, 14), 'amp': random.uniform(1.5, 3.5),
                'vy': random.uniform(30, 48) * (1.25 if alto else 1.0),
                'vida_p': random.uniform(0.32, 0.55) * (1.35 if alto else 1.0)}

    def _tick(self, dt):
        try:
            k = self.k
            if k.parent is None or self.get_root_window() is None:
                return self.parar()
            te = k.ps / float(R)
            pose = k._pose
            ativo = pose.get('mugetsu') and k.opacity > 0.3
            bordas = bordas_pose(pose) if ativo else None
            if bordas:
                while len(self._linguas) < self.n_linguas:
                    self._linguas.append(self._nova_lingua(bordas))
            vivas = []
            for L in self._linguas:
                L['vida'] -= dt
                if L['vida'] <= 0 or not bordas:
                    continue
                vivas.append(L)
                if self.frente and random.random() < 0.7:
                    continue
                if not self._livres:
                    continue
                i = self._livres.pop()
                vida = L['vida_p'] * (0.5 if self.frente else 1.0)
                self._p.append({'i': i, 'x': L['tx'] + random.uniform(-0.6, 0.6), 'y': float(L['ty']),
                                'vy': L['vy'], 'vida': vida, 'v0': vida, 'fase': L['fase'],
                                'f': L['f'], 'amp': L['amp'], 'esp': k.espelhar})
            self._linguas = vivas
            vivos = []
            ox, oy = k.x, k.y
            for f in self._p:
                f['vida'] -= dt
                c, r = self._ins[f['i']]
                if f['vida'] <= 0:
                    c.a = 0
                    r.size = (0, 0)
                    self._livres.append(f['i'])
                    continue
                u = 1 - f['vida'] / f['v0']
                f['y'] += f['vy'] * dt
                f['vy'] *= 0.985
                # a lingua ondula (mais na ponta) e tomba para tras
                lx = f['x'] + math.sin(f['fase'] + u * f['f']) * f['amp'] * u - 5.0 * u
                tx = (TW - 1 - lx) if f['esp'] else lx
                cor, alfa = self.DEGRAUS[min(4, int(u * 5))]
                tam = 2 if (u < 0.4 and not self.frente) else 1
                X = ox + round(tx) * te
                Y = oy + round(f['y']) * te
                r.pos = (X, Y)
                r.size = (tam * te, tam * te)
                c.rgba = (cor[0], cor[1], cor[2], alfa * (0.8 if self.frente else 1.0))
                vivos.append(f)
            self._p = vivos
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
