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
from bisect import bisect_left, bisect_right
from array import array
import random
from collections import OrderedDict

from kivy.uix.widget import Widget
from kivy.graphics import (Color, Rectangle, Mesh, PushMatrix, PopMatrix,
                           Translate, Rotate, Scale)
from kivy.graphics.stencil_instructions import StencilPush, StencilUse, StencilUnUse, StencilPop
from kivy.graphics.texture import Texture
from kivy.properties import BooleanProperty, NumericProperty
from kivy.clock import Clock

FPS = 30.0          # linha do tempo das poses (as sequencias e as cenas contam quadros de 30/s)
DESENHOS = 24.0     # o Yoru troca de desenho 24 vezes por segundo (corpo, sobretudo, cabelo)
FASES = 16          # passos do balanco do sobretudo/cabelo: um passo novo a cada desenho


class _Tocando:
    """Marca de 'sequencia tocando' (quem anda e o relogio do boneco)."""
    def cancel(self):
        pass


_TOCANDO = _Tocando()


class _NoDesenho:
    """O que foi preso no relogio do boneco (cancel() solta)."""
    def __init__(self, k, fn):
        self.k, self.fn = k, fn

    def cancel(self):
        try:
            self.k._a_cada_desenho.remove(self.fn)
        except ValueError:
            pass

_PALETA = {
    'H': (0.11, 0.10, 0.17, 1), 'h': (0.36, 0.36, 0.49, 1),     # cabelo
    'S': (0.97, 0.84, 0.70, 1), 's': (0.89, 0.63, 0.50, 1),     # pele
    'E': (0.03, 0.05, 0.14, 1),                                  # olho
    'C': (0.11, 0.10, 0.17, 1), 'c': (0.27, 0.27, 0.38, 1),     # sobretudo
    'A': (0.16, 0.15, 0.24, 1),                                  # manga do braco da frente
    'q': (0.12, 0.24, 0.45, 1),                                  # forro do sobretudo (roxo)
    'G': (0.46, 0.47, 0.58, 1),                                  # detalhes cinza
    'P': (0.08, 0.07, 0.13, 1), 'B': (0.04, 0.04, 0.08, 1),     # calca / bota
    'M': (0.05, 0.05, 0.10, 1),                                  # luva
    # Elucidator (preta): lamina, fio claro, costas, cabo, guarda, pontas
    'W': (0.08, 0.08, 0.12, 1), 'w': (0.60, 0.64, 0.78, 1), 'u': (0.24, 0.24, 0.33, 1),
    'v': (0.42, 0.44, 0.56, 1),                                  # filete da bainha
    'j': (0.30, 0.32, 0.43, 1),                                  # hamon (ondas no aco preto)
    '9': (0.67, 0.94, 1.00, 1),                                  # ciano aceso (reiatsu, olhos)
    '5': (1.00, 0.86, 0.30, 1),                                  # emote "!" / "..."
    '6': (0.62, 0.88, 1.00, 1),                                  # gota de suor
    'K': (0.19, 0.19, 0.27, 1), 'g': (0.31, 0.32, 0.42, 1), 'k': (0.67, 0.69, 0.78, 1),
    # Dark Repulser (cristal azul)
    'R': (0.20, 0.47, 1.00, 1), 'r': (0.67, 0.86, 1.00, 1), 'z': (0.09, 0.24, 0.78, 1),
    'y': (0.14, 0.33, 0.82, 1), 'Y': (0.55, 0.78, 1.00, 1),
    # brilho percorrendo a lamina
    '!': (1.00, 1.00, 1.00, 1), '1': (0.80, 0.96, 1.00, 0.85),
    # rastro de movimento da lamina (smear em pixel)
    'X': (0.88, 0.98, 1.00, 0.88), 'x': (0.42, 0.86, 1.00, 0.6),
    'O': (0.33, 0.78, 0.93, 1),                               # contorno (rim light)
    # forma Mugetsu (Bankai): corpo na sombra, olhos e chamas roxo/azul
    'D': (0.05, 0.04, 0.09, 1), 'd': (0.22, 0.13, 0.36, 1),     # roupa na sombra / brilho roxo
    'V': (0.90, 0.62, 1.00, 1),                                  # olhos acesos (roxo)
    'F': (0.62, 0.28, 1.00, 0.95), 'f': (0.28, 0.58, 1.00, 0.95),
    'L': (0.93, 0.86, 1.00, 0.9),                                # ponta clara da chama
    'o': (0.66, 0.36, 1.00, 0.9),                                # contorno roxo
    'Q': (0.52, 0.80, 0.98, 1),                                  # pixel aceso pela luz da lamina
    # sprite premium: degraus de volume
    'J': (0.05, 0.05, 0.10, 1), 'I': (0.18, 0.17, 0.27, 1),    # cabelo: sombra profunda / brilho medio
    'e': (0.12, 0.24, 0.45, 1), 'n': (0.91, 0.93, 0.96, 1),     # iris / brilho do olho
    '2': (0.05, 0.05, 0.10, 1),                                 # sobretudo: sombra profunda
    '4': (0.055, 0.055, 0.085, 1),                               # camisa preta (abertura do casaco)
    '7': (0.04, 0.04, 0.09, 1),                                  # calca: lado da sombra
    '+': (0.91, 0.92, 0.96, 1),                                  # reflexo no aco
    '0': (0.16, 0.43, 0.75, 1),                               # contorno do lado da sombra
    '8': (0.36, 0.17, 0.60, 0.85),                               # contorno roxo do lado da sombra
    'm': (0.31, 0.55, 0.78, 1),                                  # iris (parte clara, embaixo)
    'T': (0.43, 0.20, 0.19, 1),                                  # dentro da boca
    'Z': (0.27, 0.73, 0.92, 1),                                  # costura ciano da roupa (acende nos golpes)
    'N': (0.02, 0.02, 0.06, 1),                                  # contorno escuro
    'p': (0.24, 0.24, 0.35, 1),                                  # brilho cinza-azulado da calca
    'b': (0.13, 0.13, 0.20, 1),                                  # bota: meio-tom
    # detalhe fino (3 texels por unidade)
    't': (0.67, 0.36, 0.31, 1),                                  # pele: sombra funda (puxa para o vinho)
    'i': (0.75, 0.76, 0.84, 1),                                  # branco do olho (susto)
    '3': (0.19, 0.36, 0.60, 1),                                  # iris: meio-tom
    'U': (0.63, 0.65, 0.77, 1),                                  # cabelo: reflexo
    '%': (0.47, 0.49, 0.60, 1),                                  # couro: reflexo (bota, luva)
    '&': (0.11, 0.075, 0.18, 1),                                 # roupa na sombra: meio-tom roxo
    '~': (0.38, 0.22, 0.40, 1),                                  # rosto: sombra funda da franja (Mugetsu)
    '^': (0.86, 0.72, 0.98, 1),                                  # pele com reflexo roxo do fogo
    '<': (0.62, 0.34, 1.00, 0.6), '>': (0.92, 0.82, 1.00, 0.88),  # rastro roxo (Mugetsu)
}
_PALETA['a'] = (0.19, 0.36, 0.60, 1)
_PALETA['l'] = (0.31, 0.55, 0.80, 1)
_PALETA['$'] = (0.78, 0.63, 0.31, 1)
_PALETA['@'] = (0.47, 0.33, 0.16, 1)
_PALETA['*'] = (0.94, 0.84, 0.55, 1)
_SEM_CONTORNO = set('xX!1FfL<>O0')
# Mugetsu: a roupa escurece (o rosto continua claro, os olhos acendem)
_SOMBRA = {'a': 'd', 'l': 'o', '$': 'd', '@': 'D', '*': 'o', 'O': 'o', '0': '8', 'C': '&', 'c': 'd', 'A': 'd', 'q': 'D', 'P': '&', 'B': 'D', 'M': 'D', 'G': 'd', 'E': 'D',
           '2': 'D', '4': 'D', '7': 'D', 'e': 'V', 'n': '!', 'K': 'D', 'Z': 'o', 'p': 'd', 'b': '&',
           '3': 'V', 'm': 'L', 'i': 'd', 'U': 'o', '%': 'd', '9': 'L', 'x': '<', 'X': '>',
           'h': 'd', 'I': '&'}                      # cabelo: o brilho vira roxo
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
ESC_PERNAS = 0.85         # pernas 15% mais curtas (pedido do usuario, 29/09/2026)
_COXA, _CANELA = 7.5 * ESC_PERNAS, 7.5 * ESC_PERNAS
_PERNAS_P = {
    # (13/10/2026: em pe as pernas ficam quase retas - antes os joelhos dobravam
    # mesmo parado; no ar os joelhos dobram e cada pe vai num lugar - antes as
    # pernas penduravam retas e paralelas, como pernas de pau)
    'repouso':      dict(H=16.9, ar=False, f=(2.4, 0.0), b=(-2.1, 0.0)),
    'passo':        dict(H=16.4, ar=False, f=(4.2, 0.0), b=(-3.7, 0.0)),
    'avanco':       dict(H=14.8, ar=False, f=(7.2, 0.0), b=(-8.0, 0.0)),
    'avanco_baixo': dict(H=11.1, ar=False, f=(7.5, 0.0), b=(-8.8, 0.0)),
    'agachado':     dict(H=8.5, ar=False, f=(5.2, 0.0), b=(-4.1, 0.0)),
    'dobra':        dict(H=13.2, ar=False, f=(3.6, 0.0), b=(-2.8, 0.0)),
    # bases de espadachim: pes afastados e joelhos soltos
    'base':         dict(H=15.8, ar=False, f=(5.0, 0.0), b=(-4.5, 0.0)),
    'base_larga':   dict(H=14.3, ar=False, f=(6.5, 0.0), b=(-6.7, 0.0)),
    'recua':        dict(H=14.2, ar=False, f=(4.1, 0.0), b=(-6.2, 0.0)),     # peso na perna de tras
    'pulo':         dict(H=14.2, ar=True, f=(3.6, -8.5), b=(-0.5, -7.7)),
    'suspenso':     dict(H=15.9, ar=True, f=(3.4, -11.6), b=(-2.6, -12.8)),
    'solto':        dict(H=16.0, ar=True, f=(2.8, -12.6), b=(-1.8, -13.4)),
    'solto2':       dict(H=15.7, ar=True, f=(3.6, -11.4), b=(-5.2, -12.4)),
    'solto_meio':   dict(H=15.9, ar=True, f=(3.0, -12.0), b=(-3.6, -12.8)),
    'pendente':     dict(H=15.7, ar=True, f=(2.0, -13.4), b=(-0.4, -13.9)),
    'grudado':      dict(H=11.6, ar=True, f=(4.6, -8.3), b=(0.5, -8.0)),
}


def _encurta_pernas(tab, s):
    """Pernas mais curtas: o quadril desce (H) e os pes no ar sobem junto; a
    abertura dos pes no chao encolhe so pela metade (a base continua firme)."""
    out = {}
    for nome, v in tab.items():
        q = dict(v)
        q['H'] = v['H'] * s
        for k in ('f', 'b'):
            x, y = v[k]
            q[k] = (x * (0.5 + 0.5 * s), y * s)
        out[nome] = q
    return out


_PERNAS_P = _encurta_pernas(_PERNAS_P, ESC_PERNAS)
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


_CORPO = set('CcAqGPBMSsHhE24JIen7tU3%bp~^alkZN')
_PANO = set('CcAq2Zal')                                   # sobretudo           # cores de corpo/roupa (para o contorno do braco)


def _p(x, y):
    return (round(x), round(y))


_GUARDA_INF = [(0, -2), (0, -1), (0, 1), (0, 2), (1, -3), (1, 0), (1, 3),
               (2, -2), (2, -1), (2, 1), (2, 2)]


_BAINHA_ANG = 222.0
_BAINHA_COMP = 13


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
                 pernas_b=None, pt=0.0, vista='lado', cresce=1.0, estica=0,
                 m1=(3, -5), a1=-40.0, c1=15, s1=None,
                 m2=None, a2=None, c2=15, s2=None)


# ═══════════════════════════════════════════════════════════════════
#  MONTAGEM EM TEXELS
#  As poses continuam na grade de sempre (unidades). O desenho e feito em
#  texels, 3 por unidade: rosto, mechas, dobras, maos e laminas com bem
#  mais detalhe e contorno fino. E = escala das medidas em texels que
#  foram pensadas na grade antiga de 2 por unidade.
# ═══════════════════════════════════════════════════════════════════
R = 5
E = R / 2.0
TW, TH = GW * R, GH * R


TAMANHO = 1.15             # o Yoru novo e 15% maior que o de antes


def ps_inteiro(v):
    """Tamanho da unidade (px de tela): o que o Yoru tinha antes (degraus de
    3 px) e 15% a mais, exato. Os texels podem ficar com 1 px de diferenca
    entre si (invisivel no celular)."""
    ps = max(R, int(round(3 * max(1, int(round(v / 3.0))) * TAMANHO)))
    k = int(round(ps / float(R)))
    if k >= 2 and abs(k * R - ps) <= ps * 0.12:
        return k * R                 # pixels do boneco todos do mesmo tamanho
    return ps


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
_PARTES_MAX = 420


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
    "..HHHHHHHH|HHHHHHHHHH|HHHHHHHHHH|HHHJ.....",  # 6
    "..HHHHHHHH|HHHHIIIIJI|IIIIIHHHHH|HHHHJ....",  # 7
    "..JHHHHHHH|HIIhhhhhJh|hUUhhIJHHH|HHHHHJ...",  # 8
    "..HHHHHHHI|IhhIIIIIJH|IIIIhhJIHH|HHHHHHJ..",  # 9
    "..JJHHHHIh|hIIHHHHHHJ|HHHHIIhJIH|HHHHHHHJJ",  # 10
    "..JJHHHHHI|IHHHHHHHHH|HHHHHHIIJI|HHHHHHHJJ",  # 11
    "..HHJJHHHH|HHHHHHHHHH|HHHHHHHHII|IIHHHHHHJ",  # 12
    "..HHJJHHHH|HHHHHHHHHH|JHHHHHHHHH|HhIHHHHHJ",  # 13
    "..JHJJHHHH|HHHHHHHHHJ|HHHHHHHJHH|HHHHHHHHH",  # 14
    "..HHJJHHHH|HHHHHHHHJH|HHHHHHJHHH|HHHJHHHHH",  # 15
    "..JHHHJJHH|HHHHHHHJHH|HHHHHJHHHH|HHHJHHHHH",  # 16
    "..JHHHJJHH|HHHHHHJHHH|HHHHJHHHHH|HHJHHHHHH",  # 17
    "..HHHHJJHH|HHHHHJHHHH|HHHHJHIIHH|HHJHHHHHH",  # 18
    "..HHHHJJHH|HHHHJHHHHH|HHHJHIIHHH|HHJHHHHHH",  # 19
    "..HHHHHHJH|HHHHssHHHS|SsssJHHHss|ssssssHHs",  # 20
    "..HHHHHHHH|HHHHssHHss|EEEEEEHHss|SEEESSHHH",  # 21
    "..HHHHHHHH|HHHHsSSSSE|eeEEnnSSSS|SeEnSSSSs",  # 22
    "..HHHHHHHH|HHHsSSSSSS|e3EEn3SSSS|S3EeSSSSs",  # 23
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


def _repulser2(px, hx, hy, ux, uy, nx, ny, comp, brilho):
    """Dark Repulser: lamina reta de cristal com facetas em diagonal, fio
    claro, reflexo; guarda em cruz com pontas de cristal e gema; cabo curto
    com anel e pomo."""
    L = comp * 3
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
    # mais fina que o desenho antigo ampliado (como a espada azul da referencia)
    fw = F * 0.6
    _girado(px, hx, hy, ux, uy, -11.0 * F, (L + 1.5) * F, -8.0 * fw, 8.0 * fw,
            lambda k, j: cor(k / F, j / fw))


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
    L = comp * 3
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
        if evo:                                            # lamina do Bankai (referencia)
            w = 6.5 if k < L - 16 else 6.5 * max(0.0, (L + 2 - k) / 18.0)
            if abs(j) > w + 0.01:
                return None
            borda = w - abs(j)
            if borda < 1.0:
                return 'L' if j > 0 else 'V'                  # fio aceso (lado da luz mais claro)
            if borda < 2.0:
                return 'V' if j > 0 else 'F'
            if borda < 3.0:
                return 'F' if j > 0 else 'd'
            if jn == 0:
                return 'o' if (kk + mv) % 11 < 2 else 'K'    # sulco central com runas correndo
            return 'W' if jn > 0 else 'D'
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
    _girado_esc(px, hx, hy, ux, uy, -22.0, L + 3.5, -10.0, 10.0, cor, F)
    if evo:
        def pp(k, j, ch):
            px[(int(round(hx + (ux * k + nx * j) * F)), int(round(hy + (uy * k + ny * j) * F)))] = ch
        for (cx, cy) in _INF:                                  # guarda: o infinito (roxo)
            for dj in (-0.5, 0.0, 0.5):
                pp(4.0 + cy * 6.0, cx * 10.5 + dj, 'V')
        for (cx, cy) in _INF[::4]:
            pp(4.0 + cy * 6.0 * 0.82, cx * 10.5 * 0.9, 'L')
        for j in (-6, 6):
            pp(4.0, j, 'L')
        pp(4.0, 0, '!')


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
            _katana5(d, 0, 0, ux, uy, nx, ny, comp, b)
        elif tipo == 2:
            _repulser2(d, 0, 0, ux, uy, nx, ny, comp, b)
        else:
            _fundida2(d, 0, 0, ux, uy, nx, ny, comp, b, tipo == 4, (mv + 0.5) / 18.0)
    _parte(px, ('esp', tipo, comp, ang, b, mv), hx, hy, desenha)


def _meia(v):
    """Posicao do corpo em passos de 1 texel (1/R de unidade): o corpo anda
    de pixel em pixel, sem pulinhos de 1,5."""
    return round(v * R) / float(R)


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


def _ds(p):
    """Quanto o tronco de cima sobe (estica) ou desce (encolhe), em texels."""
    return int(round(p.get('estica', 0) or 0)) * 3


def olhos_texel(p):
    """Centro do olho (texels, sem espelho) na pose - para o brilho e o
    rastro de luz dos olhos na forma Mugetsu."""
    dx, dy = _meia(p['dx']), _meia(p['dy'])
    hip_y = _PES + _alt_pernas(p) + dy
    incl = int(round(p.get('incl', 0) or 0))
    cx = _t(_X0 + dx + 6.5)
    hy = _t(hip_y)
    cab_x = cx + _GOLA[0] - _CAB_PESCOCO[0] + 4 * incl + int(round(p.get('hx', 0) or 0))
    cab_ty = hy + _GOLA[1] + _CAB_PESCOCO[1] + int(round(p.get('hy', 0) or 0)) + _ds(p)
    return [(cab_x + _OLHO5[0], cab_ty - _OLHO5[1])]


def maos_texel(p, qual=1):
    """((mao), (ponta da lamina)) da mao `qual` em texels (sem espelho),
    como o montar desenha. Sem lamina na mao, a ponta e a propria mao."""
    dx, dy = _meia(p['dx']), _meia(p['dy'])
    hy = _t(_PES + _alt_pernas(p) + dy)
    incl = int(round(p.get('incl', 0) or 0))
    cx = _t(_X0 + dx + 6.5)
    if qual == 1:
        ax, m, ang, comp = cx + int(2.5 * R), p['m1'] or (1, -3), p['a1'], p['c1']
    else:
        ax, m, ang, comp = cx - int(3.5 * R), p['m2'] or (-1, -6), p['a2'], p['c2']
    mx = ax + R * incl + R * m[0]
    my = hy + 5 * R + R * m[1] + _ds(p)
    if ang is None or (qual == 1 and p['m1'] is None) or (qual == 2 and p['m2'] is None):
        return (mx, my), (mx, my)
    a = math.radians(ang)
    L = comp * R + 3
    return (mx, my), (mx + math.cos(a) * L, my + math.sin(a) * L)

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


# ═══════════════════════════════════════════════════════════════════
#  PANO E MECHAS DESENHADOS COMO FITAS
#  Um eixo que dobra aos poucos (a ponta atrasa em relacao a raiz) e uma
#  largura que muda ao longo dele. Cada texel sabe onde esta na fita
#  (u = 0 na raiz .. 1 na ponta; v = texels a partir da borda de tras/de
#  cima, que e o lado da luz) e e isso que escolhe a cor: dobras que
#  acompanham o pano, brilho so onde a luz pega, barra e forro. Sem faixas
#  soltas e sem texel perdido na borda.
# ═══════════════════════════════════════════════════════════════════
_VIZ4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _fita(x0, y0, ang0, comp, curva, larg, passo=0.5):
    """-> {(x, y): (u, v, W)}. O eixo sai de (x0, y0) (texels) no angulo
    ang0 (graus) e dobra curva(u) graus; larg(u) -> (a, b): quanto a fita
    vai para o lado da luz (a) e para o outro (b). Cada texel fica com a
    amostra mais perto do seu centro: a cor nao pisca de um quadro para o
    outro."""
    n = max(2, int(comp / passo))
    ds = comp / float(n)
    x, y = float(x0), float(y0)
    melhor = {}
    pega = melhor.get
    rad, cos, sin = math.radians, math.cos, math.sin
    for i in range(n + 1):
        u = i / float(n)
        ang = rad(ang0 + curva(u))
        ux, uy = cos(ang), sin(ang)
        a, b = larg(u)
        W = a + b
        if W > 0.05:
            # nx, ny = uy, -ux (lado da luz)
            lx, ly = x + uy * a, y - ux * a
            m = int(W * 2.2) + 1
            px_, py_ = -uy * W / m, ux * W / m          # passo ao longo da fatia
            for k in range(m + 1):
                qx, qy = lx + px_ * k, ly + py_ * k
                ix, iy = int(qx + 4096.5) - 4096, int(qy + 4096.5) - 4096
                d = (qx - ix) * (qx - ix) + (qy - iy) * (qy - iy)
                q = (ix, iy)
                atual = pega(q)
                if atual is None or d < atual[0]:
                    melhor[q] = (d, u, W * k / m, W)
        x += ux * ds
        y += uy * ds
    f = {q: (u, v, W) for q, (d, u, v, W) in melhor.items()}
    # acabamento de pixel art: sem texel pendurado (1 vizinho so) na borda
    # e sem furinho de 1 texel no meio
    solto = []
    for q, val in f.items():
        if val[0] < 0.92:
            x, y = q
            viz = ((x + 1, y) in f) + ((x - 1, y) in f) + ((x, y + 1) in f) + ((x, y - 1) in f)
            if viz <= 1:
                solto.append(q)
    for q in solto:
        del f[q]
    furos = {}
    for (x, y) in f:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in f:
                furos[q] = furos.get(q, 0) + 1
    for q, n in furos.items():
        if n >= 3:
            x, y = q
            for vz in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                val = f.get(vz)
                if val is not None:
                    f[q] = val
                    break
    return f


def _onda(fase, u, atraso, desloc=0.0):
    """Ondulacao que desce pelo pano: a ponta chega depois da raiz."""
    return math.sin(2 * math.pi * (fase - u * atraso + desloc))


def _cauda(px, x0, y0, ang0, comp, curva, larg, ponta, cor, chao, barra=('Z', '2')):
    """Uma cauda do sobretudo (ou a aba da frente). ponta(vf) = ate onde
    (u) a fita vai em cada ponto da largura (vf 0 = borda da luz .. 1):
    corta a barra na diagonal. cor(u, v, W) pinta o pano; a barra (a borda
    do fim da fita, seguindo o contorno) ganha a linha escura e o friso."""
    f = _fita(x0, y0, ang0, comp, curva, larg)
    dentro = {}
    for q, (u, v, W) in f.items():
        if q[1] < chao:
            continue                              # o pano nao atravessa o chao
        if u <= ponta(v / W if W else 0.0):
            dentro[q] = (u, v, W)
    fogo = getattr(cor, 'fogo', None)
    ang = math.radians(ang0 + curva(1.0))         # para onde a ponta aponta
    sx = 1 if math.cos(ang) > 0.38 else (-1 if math.cos(ang) < -0.38 else 0)
    sy = 1 if math.sin(ang) > 0.38 else (-1 if math.sin(ang) < -0.38 else 0)

    def fora(q, n):
        return ((sx and (q[0] + sx * n, q[1]) not in dentro) or
                (sy and (q[0], q[1] + sy * n) not in dentro))
    for q, (u, v, W) in dentro.items():
        if u > 0.72 and fora(q, 1):
            ch = barra[1]
        elif u > 0.72 and fora(q, 2):
            ch = barra[0]
        else:
            ch = cor(u, v, W)
        if fogo is not None:
            ch = fogo(ch, u, ponta(v / W if W else 0.0), q)
        if ch:
            px[q] = ch


# mechas de tras: (coluna, linha) da raiz no mapa da cabeca, angulo (graus),
# comprimento e meia-largura na raiz (texels). De baixo para cima (as de
# cima ficam por cima).
_MECHAS = ((13, 25, 228.0, 13.0, 5.0), (10, 20, 207.0, 19.0, 6.5), (9, 14, 190.0, 21.0, 7.0),
           (10, 8, 172.0, 19.0, 6.5), (15, 4, 140.0, 12.0, 4.6))


# espetos do topo que crescem com o reiatsu: (coluna da raiz, angulo, tamanho)
_ESPETOS = ((12, 118.0, 1.0), (19, 104.0, 1.25), (26, 92.0, 1.1), (32, 80.0, 0.8))


def _contorna(px, meu, tons):
    """Contorno escuro de 1 texel em volta de `meu` onde ele encosta em
    texels de `tons` (ex.: perna na frente do sobretudo)."""
    for (x, y) in meu:
        for (a, b) in _VIZ4:
            q = (x + a, y + b)
            if q not in meu and px.get(q) in tons:
                px[q] = 'N'
    px.update(meu)


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


# ═══════════════════════════════════════════════════════════════════
#  YORU NA GRADE FINA (5 texels por unidade) - o desenho da referencia
#  oficial. Cabeca (com o tufo) e tronco sao mapas tirados dela
#  (yoru_mapas.py); bracos, pernas, sobretudo e espadas sao montados em
#  cada pose, no mesmo estilo: preto arroxeado, couro com brilho cinza,
#  forro azul royal, contorno de luz ciano e metais prata e ouro.
# ═══════════════════════════════════════════════════════════════════
import yoru_mapas as _YM

F = R / 3.0                        # medidas antigas (grade de 3) -> grade fina
_CAB_PESCOCO = (36, 50)            # base do pescoco no mapa da cabeca (coluna, linha)
_TOR_QUADRIL = (22, 33)            # centro do quadril no mapa do tronco
# a partir do centro do quadril, em texels (x para a frente, y para cima)
_GOLA = (-2, 30)                   # onde a cabeca encaixa
_OMBRO1 = (13, 25)                 # ombro da frente
_OMBRO2 = (-17, 24)                # ombro de tras (em 3/4 ele aparece do lado do tronco)
_OLHO5 = (45, 38)                  # centro do olho no mapa da cabeca
_TOPO_CAB = 80                     # topo do mapa da cabeca acima do quadril (texels)


_RAIZ_TUFO = (27.0, 22.0)          # onde o tufo nasce no mapa da cabeca


def _no_tufo(c, r):
    return r < 44 and c < 30 - max(0, r - 16) * 0.45 and not (r > 30 and c > 16)


# mechas do cabelao do Mugetsu: (coluna, linha da raiz no mapa da cabeca,
# angulo na raiz, quanto curva para baixo, comprimento, meia-largura, fase).
# Nascem da nuca indo para tras e caem numa curva (as de tras primeiro).
_CABELAO = ((20, 40, -150.0, 42.0, 96.0, 5.5, 0.00), (24, 32, -158.0, 50.0, 124.0, 6.5, 0.21),
            (30, 24, -165.0, 58.0, 132.0, 7.0, 0.43), (34, 14, -172.0, 66.0, 118.0, 6.5, 0.61),
            (38, 8, -178.0, 70.0, 104.0, 6.0, 0.80), (18, 46, -140.0, 30.0, 78.0, 5.0, 0.12),
            (28, 18, -168.0, 62.0, 138.0, 6.0, 0.35), (36, 12, -175.0, 72.0, 92.0, 4.5, 0.55),
            (26, 28, -155.0, 46.0, 110.0, 5.5, 0.90))


def _cabelao(px, cb, sobe, fase, cresce):
    """Cabelao do Mugetsu (coordenadas do mapa da cabeca, y para cima):
    mechas longas de comprimentos diferentes que saem da nuca para tras e
    caem numa curva, engordam no meio e afinam ate a ponta. Brilho so perto
    da raiz; as pontas se desfazem em fumaca e brasa roxa. O vento deita
    para tras, o reiatsu levanta e uma onda desce da raiz para a ponta."""
    cabelo = {}
    corre = max(0.0, min(2.5, cb)) * 0.3
    amp = 5.0 + 3.0 * min(2.0, abs(cb)) + 6.0 * sobe
    f6 = int(round(fase * 6)) % 6
    cresce = max(0.06, min(1.0, cresce))
    for i, (col, lin, ang, curv, comp, larg, fz) in enumerate(_CABELAO):
        cp = comp * cresce
        if cp < 6:
            continue
        cai = curv * (1.0 - min(0.8, corre)) * (1.0 - 0.6 * sobe)

        def curva(u, cai=cai, fz=fz):
            return cai * u ** 1.4 + amp * u * _onda(fase * 1.2, u, 1.1, fz)

        def larg_f(u, w=larg):
            gorda = 1.0 + 0.35 * math.sin(math.pi * min(1.0, u * 1.6))      # engorda no meio
            return (w * gorda * (1.0 - u) ** 0.75, w * gorda * (1.0 - u) ** 0.9)

        f = _fita(col, -lin, ang + sobe * 25.0, cp, curva, larg_f, passo=0.6)
        fim = 0.84
        for q, (u, v, W) in f.items():
            vf = v / W if W else 0.5
            h = (q[0] * 3 + q[1] * 5 + f6 * 2) % 7
            if u > fim + 0.08:                             # ponta: lascas de chama soltas
                if h > 1:
                    continue
                ch = 'L' if h == 0 else 'V'
            elif u > fim:                                  # a ponta pega fogo aos poucos
                ch = 'F' if h < 2 else ('o' if h < 4 else 'd')
            elif vf > 0.66:
                ch = 'J'
            elif vf < 0.2 and 0.1 < u < fim - 0.04:
                ch = 'h'                                   # brilho roxo pela borda da mecha
            elif vf < 0.34 and u < 0.5:
                ch = 'I'
            else:
                ch = 'H'
            if q in cabelo and cabelo[q] in 'JHIh' and ch in 'JHIh' and                     any((q[0] + a, q[1] + b) not in f for (a, b) in _VIZ4):
                ch = 'J'                                   # linha que separa as mechas
            cabelo[q] = ch
    px.update(cabelo)


def _cabeca5(px, olhos, cab_x, cab_ty, cb, sobe, fase, cresce=None):
    """Cabeca da referencia com o TUFO vivo: cada texel do tufo anda um
    pouco (quanto mais longe da raiz, mais): o vento deita o tufo para tras,
    o reiatsu levanta, e uma onda passa da raiz para as pontas. O desenho
    de cada estado fica guardado."""
    q4 = lambda v: round(v * 4) / 4.0
    cb, sobe = q4(max(-1.0, min(3.0, cb))), q4(sobe)
    olhos = olhos if olhos in _YM.CABECAS else 'a'
    cr = None if cresce is None else round(cresce, 2)
    _parte(px, ('cab5', olhos, cb, sobe, round(fase, 3), cr), cab_x, cab_ty,
           lambda d: _cabeca5_desenho(d, olhos, cb, sobe, fase, cr))


def _cabeca5_desenho(d, olhos, cb, sobe, fase, cresce=None):
    if cresce is not None:
        _cabelao(d, cb, sobe, fase, cresce)             # o cabelao fica atras da cabeca
    sem_tufo = cresce is not None and cresce >= 0.3
    mapa = _YM.CABECAS[olhos]
    rx, ry = _RAIZ_TUFO
    corre = max(0.0, min(2.5, cb))
    amp = 1.1 + 0.8 * min(2.0, abs(cb)) + 2.2 * sobe
    tufo = {}
    resto = {}
    for r, linha in enumerate(mapa):
        for c, ch in enumerate(linha):
            if ch == '.':
                continue
            if not _no_tufo(c, r):
                resto[(c, -r)] = ch
                continue
            if sem_tufo:
                continue                                # o tufo virou o cabelao
            dist = math.hypot(c - rx, r - ry)
            w = max(0.0, min(1.0, (dist - 3.0) / 30.0)) ** 1.2
            dxx = -corre * 3.2 * w - sobe * 1.2 * w
            dyy = corre * 1.6 * w + sobe * 4.5 * w + amp * w * math.sin(2 * math.pi * (fase * 1.3 - dist / 30.0))
            tufo[(c + int(round(dxx)), -r + int(round(dyy)))] = ch
    # furinhos que a onda abriu no tufo: tapa com o vizinho
    furos = {}
    for (x, y) in tufo:
        for (a, b) in _VIZ4:
            q = (x + a, y + b)
            if q not in tufo:
                furos[q] = furos.get(q, 0) + 1
    for q, n in furos.items():
        if n >= 3:
            for (a, b) in _VIZ4:
                v = tufo.get((q[0] + a, q[1] + b))
                if v is not None:
                    tufo[q] = v
                    break
    d.update(tufo)
    d.update(resto)                                     # a cabeca por cima da raiz do tufo


def _girado_esc(px, hx, hy, ux, uy, k0, k1, j0, j1, cor, s, evita=None):
    """_girado de um desenho feito na grade antiga, ampliado s vezes (a
    forma e amostrada de novo em cada texel: sem blocos)."""
    _girado(px, hx, hy, ux, uy, k0 * s, k1 * s, j0 * s, j1 * s,
            lambda k, j: cor(k / s, j / s), evita)


# ── pe de bota (sola no chao, calcanhar a esquerda): biqueira prateada
_PE5 = [
    "...bbbbbbb..........",
    "..Bbbbbbbbbb........",
    "..Bbbbbbbbbbbb......",
    "..BBbbbbbbbbbbKK....",
    "..BBbbbbbbbbbbbKKk..",
    ".BBBbbbbbbbbbbGkk+k.",
    ".BBBBbbbbbbbbbGkk++k",
    "BBBBBbbbbbbbbbbGkkkk",
    "GGGGGGggggggggggGGGG",
    "KKKK..KKKKKKKKKKKKKK",
]


def _perna5(px, quad, joelho, pe, frente, no_ar, chao):
    """Perna na grade fina: calca preta com vinco claro e joelho marcado,
    bota alta com a cinta prateada na canela; pe com biqueira prateada no
    chao, ou em ponta no ar."""
    Q = (quad[0] * R, quad[1] * R)
    J = (joelho[0] * R, joelho[1] * R)
    P = (pe[0] * R, pe[1] * R)
    luz = 'p' if frente else 'b'

    def calca(j, t):
        if j >= 4:
            return luz                            # borda da luz
        if j >= 0:
            return 'P'
        return 'P' if (frente and j >= -2) else '7'

    def coxa(j, t):
        if frente and 0.25 < t < 0.85 and j == 2:
            return 'p'                            # vinco da calca
        return calca(j, t)

    def canela(j, t):
        if t > 0.32:                              # bota
            if 0.46 < t < 0.56:                   # cinta prateada
                return '+' if (j >= 3 and frente) else ('k' if j >= 0 else 'G')
            if j >= 3:
                return 'K' if frente else 'b'
            return 'b' if (frente and j >= -2) else 'B'
        if t > 0.27:
            return 'K' if j >= 0 else 'B'         # boca da bota
        return calca(j, t)
    _tubo(px, Q, J, 7.2, coxa)
    _tubo(px, J, P, 6.2, canela)
    jx, jy = int(round(J[0])), int(round(J[1]))
    if frente:                                    # joelho marcado
        for (ox, oy) in ((2, 2), (3, 1), (4, 0), (4, -1)):
            px[(jx + ox, jy + oy)] = 'p'
    if no_ar:
        ang = math.radians(-62)
        fim = (P[0] + math.cos(ang) * 11, P[1] + math.sin(ang) * 11)
        _tubo(px, P, fim, 3.6, lambda j, t: ('k' if j >= 0 else 'G') if t > 0.8 else
              ('K' if j >= 2 else ('b' if frente else 'B')))
        return
    x0, y0 = int(round(P[0])) - 6, chao + len(_PE5) - 1
    for r, linha in enumerate(_PE5):
        for c, ch in enumerate(linha):
            if ch != '.':
                if not frente and ch in 'bk+':
                    ch = {'b': 'B', 'k': 'G', '+': 'k'}[ch]
                px[(x0 + c, y0 - r)] = ch


def _pernas5(px, p, hip_x, hip_y):
    """As duas pernas (a de tras primeiro), como _pernas3, na grade fina."""
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
                y += math.sin(math.pi * pt) * min(2.8, anda * 0.45)
            return (x, y)
        pf, pb = passo(pf, pf2), passo(pb, pb2)
        ar = ar2 if pt >= 0.5 else ar
    frente_primeiro = lambda c1, c2: c1 if c1[0] >= c2[0] else c2      # joelho para a frente
    for (qx, pe, frente) in ((hip_x - 1.2, pb, False), (hip_x + 1.2, pf, True)):
        quad = (qx, hip_y - 0.3)
        tornozelo = (pe[0], pe[1] + (0.0 if ar else 1.9))
        joelho = _ik(quad[0], quad[1], tornozelo[0], tornozelo[1], _COXA, _CANELA, frente_primeiro)
        bx, by = int(math.floor(tornozelo[0] * R)), int(math.floor(tornozelo[1] * R))
        q4 = lambda v, o: int(round((v * R - o) * 4))
        chave = ('perna5', q4(quad[0], bx), q4(quad[1], by), q4(joelho[0], bx), q4(joelho[1], by),
                 frente, ar, by - _PES * R)
        rel = lambda c: ((c[0] * R - bx) / float(R), (c[1] * R - by) / float(R))
        _parte(px, chave, bx, by,
               lambda d, a=rel(quad), b=rel(joelho), c=rel(tornozelo), f=frente, r=ar, ch=_PES * R - by:
               _perna5(d, a, b, c, f, r, ch))


def _braco5(px, sx, sy, hx, hy, frente=False, luva=True, faixas=False, fase=0.0):
    """Braco com a manga de couro acolchoado (vincos e brilho em blocos),
    cotovelo, antebraco e luva preta com punho; o da frente tem contorno
    escuro por cima do corpo."""
    fs = round(fase, 2) if faixas else 0.0
    meu = {}
    _parte(meu, ('braco5', hx - sx, hy - sy, frente, luva, faixas, fs), sx, sy,
           lambda d: _braco5_desenho(d, 0, 0, hx - sx, hy - sy, frente, luva, faixas, fs))
    if frente:
        for (x, y) in meu:
            for vx, vy in _VIZ4:
                q = (x + vx, y + vy)
                if q not in meu and px.get(q) in _CORPO:
                    px[q] = 'N'
    px.update(meu)


def _braco5_desenho(meu, sx, sy, hx, hy, frente, luva, faixas, fase):
    LA, LB = 4.4 * R, 4.4 * R
    abaixo = lambda c1, c2: c1 if c1[1] <= c2[1] else c2                # cotovelo para baixo
    ex, ey = _ik(sx, sy, hx, hy, LA, LB, abaixo)
    luz, base_c, sombra = ('c', 'A', 'C') if frente else ('A', 'C', '2')
    la = math.hypot(ex - sx, ey - sy) or 1.0
    lb = math.hypot(hx - ex, hy - ey) or 1.0

    def couro(j, t, L):
        k = int(t * L)
        if j >= 4:
            return luz
        if k % 8 == 0 and -3 <= j <= 3:
            return sombra                          # vinco do acolchoado
        if k % 8 == 1 and 0 <= j <= 3:
            return luz if frente else base_c       # brilho logo abaixo do vinco
        if j >= -2:
            return base_c
        return sombra

    def braco(j, t):
        # deltoide cheio no ombro, afina ate o cotovelo (lado da luz mais cheio)
        r = 6.4 - 1.3 * t + (0.5 if j > 0 and t < 0.35 else 0.0)
        if abs(j) > r:
            return None
        if j <= -r + 1.0:
            return sombra                          # borda de baixo sempre na sombra
        return couro(j, t, la)

    def antebraco(j, t):
        if luva and 0.64 < t < 0.76:
            r = 5.6                                # punho da luva mais largo
        elif luva and t >= 0.76:
            r = 4.6
        else:
            r = 5.2 - 0.9 * t
        if abs(j) > r:
            return None
        if t < 0.08 and j <= -1:
            return '2'                             # vinco na dobra do cotovelo
        if faixas and t < 0.84:                    # faixas enroladas na diagonal (Mugetsu)
            d = (int(t * lb) + j) % 6
            if d == 0:
                return '&'                          # vao entre as voltas
            if d == 1:
                return 'o' if j >= 1 else 'd'       # beirada acesa de cada volta
            return 'd' if j >= -1 else '&'
        if luva and t > 0.66:
            if t < 0.74:
                return 'G' if j >= 1 else 'K'      # punho da luva
            return 'K' if j >= 3 else 'M'
        return couro(j, t, lb)
    _tubo(meu, (sx, sy), (ex, ey), 7.0, braco)
    for ox in range(-5, 6):                        # cotovelo
        for oy in range(-5, 6):
            if ox * ox + oy * oy <= 26:
                meu[(int(round(ex)) + ox, int(round(ey)) + oy)] = base_c if oy < 2 else luz
    _tubo(meu, (ex, ey), (hx, hy), 6.0, antebraco)
    for ox in range(-6, 7):                        # ombro
        for oy in range(-6, 7):
            if ox * ox + oy * oy <= 38:
                meu[(sx + ox, sy + oy)] = luz if (oy >= 3 or (oy >= 1 and ox <= -2)) else base_c
    if faixas:                                     # ponta solta da faixa, voando para tras
        dois_pi = 2 * math.pi
        for (oy, fx) in ((2, 0.0), (-2, 0.4)):
            for i in range(20):
                x = int(round(hx - 5 - i))
                y = int(round(hy + oy + math.sin(dois_pi * (fase * 2.0 + fx) - i * 0.3) * i * 0.2))
                meu.setdefault((x, y), 'W' if i % 7 == 6 else 'u')


# mao fechada (luva preta, nos marcados), centro no meio do mapa
_MAO5 = [
    "..KMMMMK..",
    ".MMMMMMMK.",
    "MgMMMMMMMK",
    "MMMMMMMMMK",
    "MMMMMMMMMM",
    "MMMMMMMMKM",
    "MKgMKgMKgM",
    ".MMMMMMMM.",
    "..MMMMMM..",
]


def _mao5(px, hx, hy, metal=False):
    for r, linha in enumerate(_MAO5):
        for c, ch in enumerate(linha):
            if ch != '.':
                if metal and ch == 'g':
                    ch = 'k'
                px[(hx - 5 + c, hy + 4 - r)] = ch


def _katana5(px, hx, hy, ux, uy, nx, ny, comp, brilho):
    """Katana da referencia: cabo preto trancado com losangos claros,
    kashira e tsuba DOURADAS, habaki prateado e lamina fina e curva: costas
    escuras, miolo preto, fio branco brilhante e ponta (kissaki)."""
    L = comp * R
    ini = 7
    sori = max(3.0, L * 0.07)
    kb = None if brilho is None else ini + brilho * (L - ini)

    def cor(k, j):
        kk, jn = int(math.floor(k + 0.5)), int(math.floor(j + 0.5))
        if k < -17.5:
            return None
        if k < -14.5:
            return ('k' if j > 1 else 'K') if abs(j) <= 3.0 else None         # kashira
        if k < -0.5:                                                         # cabo trancado
            if abs(j) > 3.2:
                return None
            if abs(j) > 2.4:
                return 'K' if j > 0 else 'W'
            cruza = (kk + jn) % 6 == 0 or (kk - jn) % 6 == 0
            return ('k' if (kk + jn) % 12 == 0 else 'g') if cruza else 'W'
        if k < 3.5:                                                          # tsuba
            d = ((k - 1.5) / 2.2) ** 2 + (j / 7.6) ** 2
            if d > 1.0:
                return None
            if d > 0.62:
                return 'G' if j < 0 else 'k'
            return '+' if (j > 3 and k < 2.5) else ('k' if (kk + jn) % 3 else 'G')
        if k < ini:                                                          # habaki
            if -2.5 <= j <= 3.4:
                return '+' if j > 2.4 else 'k'
            return None
        if L < ini:
            return None
        u = (k - ini) / float(max(1, L - ini))
        jj = j + sori * u * u                                                # a lamina curva
        corta = max(0.0, k - (L - 9))                                        # kissaki
        if jj > 3.0 or jj < -2.8 + corta * 0.62:
            return None
        jn2 = int(math.floor(jj + 0.5))
        if kb is not None and abs(k - kb) < 2.2 and jn2 >= 1:
            return '!' if jn2 >= 2 else '1'
        if jn2 >= 3 or (corta > 0.5 and jn2 >= 2):
            return '+'                                                       # fio branco
        if jn2 == 2:
            return 'w'
        if jn2 == 1:
            return 'j' if math.sin(k * 0.35) > 0.2 else 'W'                  # hamon
        if jj < -1.8 + corta * 0.62:
            return 'u'                                                       # costas (mune)
        return 'W'
    _girado(px, hx, hy, ux, uy, -18.0, L + 0.5, -8.0, 8.0, cor)


def _bainha5(px, bx, by):
    """Bainha da cintura na grade fina: laca preta com filete, reflexo e
    ponteira dourada."""
    a = math.radians(_BAINHA_ANG)
    L = _BAINHA_COMP * R

    def cor(k, j):
        jn = int(math.floor(j + 0.5))
        if k > L:
            return '$' if jn <= -2 else '@'
        if jn <= -3:
            return 'v'
        if jn == -2:
            return 'u' if 12 < k < 22 else 'W'
        if jn >= 2:
            return 'u'
        return 'W'
    _girado(px, bx, by, math.cos(a), math.sin(a), 0.0, L + 3.5, -3.4, 2.4, cor,
            evita=('P', 'B', '7', 'K', 'p', 'b', '%', 'G', 'k', '+'))


def _cabo_cintura5(px, bx, by):
    """Cabo da katana guardada na cintura: tsuba dourada e cabo trancado."""
    a = math.radians(_BAINHA_ANG)

    def cor(k, j):
        kk, jn = int(math.floor(k + 0.5)), int(math.floor(j + 0.5))
        if k > -1.5:
            d = ((k - 0.5) / 2.0) ** 2 + (j / 7.4) ** 2
            if d > 1.0:
                return None
            return 'G' if d > 0.62 and j < 0 else 'k'
        if abs(j) > 3.2:
            return None
        if k < -14.5:
            return 'k' if j > 1 else 'K'
        cruza = (kk + jn) % 6 == 0 or (kk - jn) % 6 == 0
        return ('k' if (kk + jn) % 12 == 0 else 'g') if cruza else 'W'
    _girado(px, bx, by, math.cos(a), math.sin(a), -17.5, 2.5, -8.0, 8.0, cor)


def _bainha_costas5(px, X, Y):
    """Dark Repulser guardada nas costas (o desenho de sempre, ampliado
    para a grade fina): cabo com a guarda de cristal por cima do ombro e a
    bainha descendo por tras."""
    def reta(ang, comp, j0, j1, fn):
        a = math.radians(ang)
        _girado_esc(px, X, Y, math.cos(a), math.sin(a), 0.0, comp, j0, j1, fn, F)

    def bainha(k, j):
        if k > 36:
            return 'k' if j < 0 else 'g'
        if int(k) % 13 in (6, 7):
            return 'G'
        return 'v' if j > 0.8 else ('u' if -0.3 < j < 0.3 and 10 < k < 16 else 'W')

    def cabo(k, j):
        if k > 13.5:
            return 'Y' if abs(j) < 0.8 else None
        return 'y' if int(k) % 4 == 1 else ('g' if j > 0.5 else 'K')
    reta(292, 36, -1.3, 1.3, bainha)
    reta(122, 14, -1.1, 1.1, cabo)

    def guarda(k, j):
        if abs(j) >= 4.5:
            return 'Y'
        return 'r' if abs(j) < 0.8 else 'y'
    reta(122, 2.4, -6.0, 6.0, guarda)


def _casaco5(px, cx, top, chao, capa, lift, fase, saia, parte, mug=False):
    """Sobretudo da referencia (na grade fina), guardado pronto."""
    q4 = lambda v: round(v * 4) / 4.0
    capa, lift, saia = q4(capa), q4(lift), q4(saia)
    _parte(px, ('casaco5', parte, capa, lift, round(fase, 3), saia, chao - top, mug), cx, top,
           lambda d: _casaco5_desenho(d, 0, 0, chao - top, capa, lift, fase, saia, parte, mug))


def _casaco5_desenho(px, cx, top, chao, capa, lift, fase, saia, parte, mug=False):
    """Aba da frente na coxa (borda clara e friso azul), e atras duas
    caudas longas que abrem: a de fora mostra o FORRO AZUL na borda de tras
    e a barra e rasgada em pontas. A ponta chega depois da raiz."""
    vento = max(-1.0, min(2.2, capa))
    ergue = max(-0.6, min(2.6, lift))
    amp = 5.0 + 4.0 * min(3.0, abs(capa)) + 2.5 * abs(ergue)
    estica = (1.0 + 0.2 * max(0.0, vento) + 0.1 * max(0.0, ergue)) * (1.3 if mug else 1.0)
    f6 = int(round(fase * 6)) % 6

    def rasga(vf, base):
        """Barra: no Mugetsu, rasgada em pontas longas e desiguais."""
        if not mug:
            return base
        return base - 0.05 - 0.13 * abs(math.sin(vf * 11.0 + 0.7)) - 0.06 * abs(math.sin(vf * 23.0))

    def em_chamas(ch, u, fim_u, q):
        """As pontas do sobretudo do Mugetsu viram fogo roxo."""
        if not mug or u < fim_u - 0.2:
            return ch
        k2 = (fim_u - u) / 0.2                         # 1 longe da ponta .. 0 na ponta
        h = (q[0] * 5 + q[1] * 3 + f6 * 2) % 7
        if k2 < 0.35:
            return 'L' if h < 2 else ('V' if h < 5 else None)
        if k2 < 0.7:
            return 'V' if h < 3 else 'o'
        return 'o' if h < 3 else ch

    if parte == 'frente':
        def curva(u):
            return (6.0 * (saia - 1.0) + 2.0) * u - vento * 24.0 * u ** 1.3 - ergue * 20.0 * u \
                + amp * 0.5 * u * _onda(fase, u, 0.7, 0.37)

        def cor(u, v, W):
            if v > W - 1.2:
                return 'c'                        # borda da frente clara
            if v < 1.2:
                return 'a'                        # friso azul do lado de tras
            if u > 0.2 and abs(v - W * 0.55 - 0.8 * _onda(fase, u, 0.8, 0.2) * u) < 0.6:
                return '2'                        # dobra
            if u > 0.2 and abs(v - W * 0.55 - 0.8 * _onda(fase, u, 0.8, 0.2) * u + 1) < 0.6:
                return 'A'
            return 'C'
        cor.fogo = em_chamas if mug else None
        _cauda(px, cx + 15.0, top, -92.0, 30.0 * (1.5 if mug else 1.0), curva,
               lambda u: (6.5 + 1.0 * u, 5.5 + 1.0 * u * saia),
               lambda vf: rasga(vf, 1.0 - 0.05 * vf), cor, chao, barra=('a', '2'))
        return

    # ── cauda de dentro: quase toda na sombra, forro azul no vao
    def curva_d(u):
        return -8.0 * u - vento * 38.0 * u ** 0.85 - ergue * 26.0 * u ** 0.95 \
            + amp * 0.8 * u * _onda(fase, u, 0.85, 0.3)

    def cor_d(u, v, W):
        if v < 3.0 and u > 0.25:
            return 'q'                           # forro, no vao entre as caudas
        if v < 4.5 and u > 0.35:
            return 'a' if (u > 0.6 and v < 3.8) else 'C'
        if v > W - 1.5:
            return '2'
        return 'C' if int(v + u * 9) % 6 else '2'
    cor_d.fogo = em_chamas if mug else None
    _cauda(px, cx - 2.0, top, -92.0, 56.0 * estica, curva_d,
           lambda u: (6.0 + 4.0 * u, 6.0 + 2.0 * u),
           lambda vf: rasga(vf, 1.0 - 0.08 * (1.0 - vf) - 0.05 * abs(math.sin(vf * 7.0))),
           cor_d, chao, barra=('a', 'q'))

    # ── cauda de fora (a de tras): a maior, abre para tras e voa mais; o
    #    forro azul aparece na borda de tras, e a barra e rasgada em pontas
    def curva_f(u):
        return -(24.0 + 8.0 * max(0.0, saia - 0.6)) * u - vento * 44.0 * u ** 0.8 \
            - ergue * 34.0 * u ** 0.9 + amp * u * _onda(fase, u, 0.85)

    def cor_f(u, v, W):
        forro = 0.18 + 0.22 * max(0.0, u - 0.35)          # a faixa azul alarga para baixo
        if u > 0.3 and v < W * forro:
            return 'l' if v < 1.2 else ('a' if v < W * forro * 0.55 else 'q')
        if v < 1.2 and u > 0.06:
            return 'c'                           # borda de tras acesa
        if v < 2.5 and 0.1 < u < 0.4:
            return 'A'
        dob = W * 0.55 + 1.6 * _onda(fase, u, 0.9) * u
        if u > 0.2:
            if dob - 0.6 <= v < dob + 0.6 + 3.0 * (u - 0.2):
                return '2'                       # dobra: cunha de sombra que abre
            if dob - 2.0 <= v < dob - 0.6 and u > 0.28:
                return 'A'                       # brilho da dobra
            if v >= dob:
                return 'C' if int(v + u * 11) % 7 else '2'
        return 'C'
    cor_f.fogo = em_chamas if mug else None
    _cauda(px, cx - 10.0, top, -100.0, 64.0 * estica, curva_f,
           lambda u: (7.0 + (14.0 if mug else 11.0) * u, 7.0 + 3.0 * u),
           lambda vf: rasga(vf, 1.0 - 0.1 * vf - 0.07 * abs(math.sin(vf * 9.4))),
           cor_f, chao, barra=('l', 'q'))


def _espetos5(px, cx, ty, cb, sobe, fase):
    """Com o reiatsu, mechas finas do topo se arrepiam, curvando para tras."""
    cabelo = {}
    for i, (col, ang, tam) in enumerate(((24, 128.0, 0.9), (31, 116.0, 1.15), (38, 104.0, 1.3),
                                          (45, 94.0, 1.2), (52, 86.0, 1.0), (58, 76.0, 0.8))):
        cresce = sobe * (0.75 + 0.25 * math.sin(2 * math.pi * (fase * 1.5 + i * 0.27)))
        comp = (5.0 + 17.0 * cresce) * tam
        if comp < 7.0:
            continue
        a0 = ang + 16.0 * min(1.0, max(0.0, cb) * 0.3) + 6.0 * math.sin(2 * math.pi * (fase + i * 0.31))

        def curva(u, i=i):
            return 26.0 * u * u + 5.0 * u * _onda(fase * 1.4, u, 0.7, i * 0.2)
        f = _fita(cx + col, ty - 7, a0, comp, curva,
                  lambda u: (2.8 * (1.0 - u) ** 1.2, 2.2 * (1.0 - u) ** 0.9))
        for q, (u, v, W) in f.items():
            vf = v / W if W else 0.5
            if vf > 0.62 or u > 0.8:
                ch = 'J'
            elif vf < 0.35 and 0.15 < u < 0.6:
                ch = 'I'
            else:
                ch = 'H'
            cabelo[q] = ch
    for q, ch in cabelo.items():
        if q not in px:
            px[q] = ch

def _sombra_mugetsu(px):
    """A roupa escurece e as linhas ciano viram roxas (o rosto fica claro)."""
    for q, ch in list(px.items()):
        if ch in _SOMBRA:
            px[q] = _SOMBRA[ch]


def _cabeca_no_corpo(p):
    """Quando um braco passa por cima da cabeca, ela vai junto no corpo."""
    m1, m2 = p['m1'], p['m2']
    acima2 = m2 is not None and m2[1] > 10
    frente_erguido = m1 is not None and m1[1] > 4 and p.get('frente1')
    return bool(acima2 or frente_erguido or p.get('emote'))


def ancoras(p):
    """(cx, topo_casaco, cab_x, cab_ty) em texels para a pose (sem a fisica
    da cabeca): onde as camadas das caudas e da cabeca se encaixam."""
    dx, dy = _meia(p['dx']), _meia(p['dy'])
    hip_y = _PES + _alt_pernas(p) + dy
    incl = int(round(p.get('incl', 0) or 0))
    cx = _t(_X0 + dx + 6.5)
    hy = _t(hip_y)
    return (cx, hy + 6, cx + _GOLA[0] - _CAB_PESCOCO[0] + 4 * incl,
            hy + _GOLA[1] + _CAB_PESCOCO[1] + _ds(p))


def montar(p, rapido=False, camada=None):
    """Pose (dict, em unidades) -> {(x, y) em texels: cor}. rapido=True:
    so o desenho cru (sem luz, cores da forma Mugetsu e contorno) - basta
    para medir o tamanho da pose. camada: None = tudo junto; 'corpo' = sem
    as caudas (e sem a cabeca, se ela nao precisar ir junto); 'cauda' = so
    as caudas, a partir de (cx, topo_casaco); 'cabeca' = so a cabeca, a
    partir de (cab_x, cab_ty)."""
    px = {}
    dx, dy = _meia(p['dx']), _meia(p['dy'])
    hip_y = _PES + _alt_pernas(p) + dy                     # quadril (unidades)
    base = _X0 + dx
    incl = int(round(p.get('incl', 0) or 0))
    fase = p.get('fase', 0.0) or 0.0
    cb = p['cabelo']
    sobe = max(0.0, min(1.2, p.get('sobe', 0.0) or 0.0))
    mugetsu = p.get('mugetsu', False)
    saia = p.get('saia', 1.0)
    cx = _t(base + 6.5)                                    # centro do quadril (texels)
    hy = _t(hip_y)
    li = 4 * incl                                          # inclinacao do tronco (texels)
    ds = _ds(p)                                            # tronco esticado/encolhido
    o1 = (cx + _OMBRO1[0] + li, hy + _OMBRO1[1] + ds)
    o2 = (cx + _OMBRO2[0] + li, hy + _OMBRO2[1] + ds)
    cab_x = cx + _GOLA[0] - _CAB_PESCOCO[0] + li + int(round(p.get('hx', 0) or 0))
    cab_ty = hy + _GOLA[1] + _CAB_PESCOCO[1] + int(round(p.get('hy', 0) or 0)) + ds
    boca = (cx + int(2.5 * R), hy + int(1.6 * R))          # boca da bainha (cinto)
    # as maos continuam medidas a partir do ombro antigo (as poses sao as mesmas)
    am1 = (cx + int(2.5 * R) + R * incl, hy + 5 * R + ds)
    am2 = (cx - int(3.5 * R) + R * incl, hy + 5 * R + ds)

    def mao(anc, m):
        return (int(round(anc[0] + R * m[0])), int(round(anc[1] + R * m[1])))

    chao = _PES * R
    topo_casaco = hy + 6
    cresce = round(p.get('cresce', 1.0) or 0.0, 2) if mugetsu else None
    if camada == 'cauda':                     # sem cortar no chao (o widget corta)
        _casaco5(px, 0, 0, -100000, p['capa'], p['lift'], fase, saia, 'tras', mug=mugetsu)
        if rapido:
            return px
        if mugetsu:
            _sombra_mugetsu(px)
        return _contorno(px, mugetsu, None, None)
    if camada == 'cabeca':
        fase = p.get('fase_cab', fase) or 0.0
        _cabeca5(px, p['olhos'], 0, 0, cb, sobe, fase, cresce)
        if sobe > 0.3:
            _espetos5(px, 0, 0, cb, sobe, fase)
        if rapido:
            return px
        if mugetsu:
            _sombra_mugetsu(px)
        return _contorno(px, mugetsu, None, -47)
    cab_junto = camada is None or _cabeca_no_corpo(p)
    if camada == 'corpo':                    # a aba da frente fica parada nesta camada
        p = dict(p, capa=0.0, lift=0.0)
        fase = 0.0


    if p['a2'] is None and not p.get('fusao'):
        _bainha_costas5(px, cx - 15, hy + 36)

    m2 = p['m2'] if p['m2'] is not None else (-1, -6)
    h2 = mao(am2, m2)
    ergue2 = m2[1] > 4
    acima2 = m2[1] > 10

    def _braco_tras():
        _braco5(px, o2[0], o2[1], h2[0], h2[1], frente=ergue2, faixas=mugetsu, fase=fase + 0.3)
        if p['a2'] is not None:
            _espada2(px, h2[0], h2[1], p['a2'], int(p['c2']), 2, p['s2'], p.get('brilho'), fase)
        _mao5(px, h2[0], h2[1])
    if not ergue2:
        _braco_tras()
    if sobe > 0.3 and cab_junto:
        _espetos5(px, cab_x, cab_ty, cb, sobe, fase)
    if ergue2 and not acima2:
        _braco_tras()

    if camada is None:
        _casaco5(px, cx, topo_casaco, chao, p['capa'], p['lift'], fase, saia, 'tras', mug=mugetsu)
    pernas = {}
    _pernas5(pernas, p, _X0 + 6.5, hip_y)
    _contorna(px, pernas, _PANO)                           # perna separada do sobretudo
    _bainha5(px, boca[0], boca[1])
    _casaco5(px, cx, topo_casaco, chao, p['capa'], p['lift'], fase, saia, 'frente', mug=mugetsu)
    # tronco (a parte de cima inclina junto com os ombros)
    qx, qy = _TOR_QUADRIL
    CINTA = 20                                             # linha do mapa onde o tronco dobra
    for r in range(len(_YM.TRONCO) - 1, -1, -1):          # de baixo para cima: o peito por cima
        linha = _YM.TRONCO[r]
        desl = li if r < 12 else (li // 2 if r < 21 else 0)
        y = hy + qy - r + (ds if r < CINTA else 0)
        vezes = ds + 1 if (ds > 0 and r == CINTA) else 1   # esticado: a cintura repete no vao
        for k in range(vezes):
            for c, ch in enumerate(linha):
                if ch != '.':
                    px[(cx - qx + c + desl, y + k)] = ch

    if mugetsu:                              # faixas cruzando o peito
        for (xa, ya, xb, yb) in ((-12, 30, 13, 13), (-13, 21, 12, 5)):
            n = max(abs(xb - xa), abs(yb - ya))
            for i in range(n + 1):
                x = cx + li + xa + (xb - xa) * i // n
                y = hy + ya + (yb - ya) * i // n
                for dd, ch in ((0, 'o'), (-1, 'd'), (-2, 'd'), (-3, '&')):
                    q = (x, y + dd)
                    if q in px:
                        px[q] = ch

    m1 = p['m1']
    ergue = m1 is not None and m1[1] > 4 and not p.get('frente1')

    def _braco_frente():
        if m1 is None:
            return
        h1 = mao(am1, m1)
        _braco5(px, o1[0], o1[1], h1[0], h1[1], frente=True, faixas=mugetsu, fase=fase)
        if p['a1'] is not None:
            _espada2(px, h1[0], h1[1], p['a1'], int(p['c1']), p.get('tipo1', 1), p['s1'],
                     p.get('brilho'), fase)
        _mao5(px, h1[0], h1[1], metal=True)
    if ergue:
        _braco_frente()
    if cab_junto:
        _cabeca5(px, p['olhos'], cab_x, cab_ty, cb, sobe, fase, cresce)
    if acima2:
        _braco_tras()
    if p['a1'] is None:
        _cabo_cintura5(px, boca[0], boca[1])
    if not ergue:
        _braco_frente()
    if p.get('agarra') and p['m2'] is not None:
        # a outra mao SEGURA o braco da espada (gesto do BAN-KAI): o punho de
        # tras aparece por cima do antebraco da frente
        _mao5(px, h2[0], h2[1])
    if p.get('emote'):
        t = {}
        _emote(t, p['emote'], int(round(cab_x / float(R))) + 2, int(round(cab_ty / float(R))) - 1)
        _up(px, t)

    if rapido:
        return px
    luz = p.get('luz', 0.0) or 0.0
    if luz > 0.2:
        _iluminar(px, luz, 2)
    if luz >= 0.5:                                           # costuras acendem no golpe
        for q, ch in list(px.items()):
            if ch == 'Z':
                px[q] = '9'
    if mugetsu:
        _sombra_mugetsu(px)
    # no corpo sem as caudas, a borda de tras das pernas fica escura (as
    # caudas cobrem ali); o ciano so em cima do quadril
    return _contorno(px, mugetsu, (hy + 5) if camada == 'corpo' else None, None)


def _contorno(px, mugetsu, luz_acima=None, sem_abaixo=None):
    """Contorno de 1 texel: escuro; ciano so como luz de fundo, do lado de
    tras e em cima (roxo na forma Mugetsu). luz_acima: so ha luz de fundo
    acima dessa linha. sem_abaixo: nao contorna abaixo dessa linha (o
    pescoco da cabeca encaixa na gola sem risco escuro)."""
    aro = 'o' if mugetsu else 'O'
    fonte = [q for q, ch in px.items() if ch not in _SEM_CONTORNO]
    ocup = px.keys()
    esq = {(x - 1, y) for (x, y) in fonte} - ocup
    cima = {(x, y + 1) for (x, y) in fonte} - ocup
    resto = ({(x + 1, y) for (x, y) in fonte} | {(x, y - 1) for (x, y) in fonte}) - ocup
    alcance = 2 * R + 2
    # vao interno (entre perna e casaco, por ex.) nao e borda de fora: ha
    # boneco a menos de `alcance` texels na mesma direcao. Linhas e colunas
    # ordenadas + busca binaria (bem mais leve que olhar texel a texel)
    linhas, colunas = {}, {}
    for (x, y) in ocup:
        linhas.setdefault(y, []).append(x)
        colunas.setdefault(x, []).append(y)
    for v in linhas.values():
        v.sort()
    for v in colunas.values():
        v.sort()
    novos = {}
    for (x, y) in esq:
        v = linhas.get(y)
        i = bisect_left(v, x) if v else 0
        if not (v and i > 0 and x - v[i - 1] < alcance):   # nada logo a esquerda
            novos[(x, y)] = aro
    for (x, y) in cima:
        if (x, y) in novos:
            continue
        v = colunas.get(x)
        i = bisect_right(v, y) if v else 0
        if not (v and i < len(v) and v[i] - y < alcance):  # nada logo acima
            novos[(x, y)] = aro
    for q in (esq | cima | resto):
        if q not in novos:
            novos[q] = 'N'
    if luz_acima is not None:
        for q, ch in novos.items():
            if ch == aro and q[1] < luz_acima:
                novos[q] = 'N'
    if sem_abaixo is not None:
        novos = {q: ch for q, ch in novos.items() if q[1] > sem_abaixo}
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
            return round(v * R) / float(R)       # passo de 1 texel
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


def _mao_arco(a, b, t):
    """Mao de a para b girando no OMBRO (m1/m2 ja sao medidos a partir
    dele): o braco varre um arco, como numa animacao desenhada, em vez de a
    mao andar em linha reta pelo meio do corpo."""
    ra, rb = math.hypot(a[0], a[1]), math.hypot(b[0], b[1])
    if ra < 1.0 or rb < 1.0:
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    aa, ab = math.atan2(a[1], a[0]), math.atan2(b[1], b[0])
    d = (ab - aa + math.pi) % (2 * math.pi) - math.pi
    if abs(abs(d) - math.pi) < 0.15:               # meia volta exata: vai por cima
        d = abs(d)
    ang = aa + d * t
    r = ra + (rb - ra) * t
    return (r * math.cos(ang), r * math.sin(ang))


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
            q[k] = _mao_arco(a, b, t)
    l0, l1 = p0['pernas'], p1['pernas']
    if l0 != l1:
        # as pernas passam de uma posicao para a outra continuamente (pes e
        # joelhos interpolados) e o quadril sobe/desce junto
        q['pernas'], q['pernas_b'] = l0, l1
        q['pt'] = max(0.0, min(1.0, t))
        h = altura(p0) + (altura(p1) - altura(p0)) * t
        q['dy'] = h - _alt_pernas(q)
    return q


EM_DOIS = 1        # desenhos do meio a cada quadro (30 por segundo): movimento continuo


def sequencia(chaves, passo=None):
    """chaves: [(quadros, pose) ou (quadros, pose, curva), ...] -> lista de
    poses (1 por quadro, 30 por segundo). `quadros` = duracao do trecho ate
    a proxima chave; `curva` = como o tempo corre nele (ver _facil; padrao
    'suave'). Como numa animacao desenhada, os desenhos do meio ficam 2
    quadros cada (`passo`): a chave segura e o movimento anda em degraus
    (trechos de 3 quadros ou menos - o golpe rapido - vao de 1 em 1).
    Numeros interpolam, as maos giram no ombro e as pernas passam por um
    quadro do meio."""
    passo = EM_DOIS if passo is None else max(1, int(passo))
    out = []
    for i, ch in enumerate(chaves):
        n, p0 = ch[0], ch[1]
        curva = ch[2] if len(ch) > 2 else 'suave'
        p1 = chaves[i + 1][1] if i + 1 < len(chaves) else p0
        n = max(1, int(n))
        pa = passo if n > 3 else 1
        ult = None
        for f in range(n):
            fs = f - (f % pa)
            if p1 is p0 or curva == 'segura' or fs == 0:
                out.append(dict(p0))
            elif fs == ult:
                out.append(dict(out[-1]))
            else:
                tl = fs / float(n)
                out.append(misturar(p0, p1, _facil(curva, tl), tl))
            ult = fs
    return out


# ═══════════════════════════════════════════════════════════════════
#  CACHE
# ═══════════════════════════════════════════════════════════════════
_CACHE = OrderedDict()     # chave_pose -> (bytes RGBA (GW x GH), caixa)
_CACHE_MAX = 600
_TEX = OrderedDict()       # (chave_pose, silhueta) -> Texture
_TEX_MAX = 220
_RGBA = {c: bytes(int(round(v * 255)) for v in cor) for c, cor in _PALETA.items()}
# cada cor da paleta vira um numero (0 = vazio) e 4 tabelas dao R, G, B e A
_COD = {c: i + 1 for i, c in enumerate(sorted(_PALETA))}
_TAB = [bytearray(256) for _ in range(4)]
for _c, _i in _COD.items():
    for _k in range(4):
        _TAB[_k][_i] = _RGBA[_c][_k]
# ── LUZ DO AMBIENTE (o Yoru no mesmo mundo do chefe): na roupa, no cabelo, no
# couro e no aco, os pixels da BORDA DE FORA sao marcados - os de cima/esquerda
# (numero da cor + _OFF_LUZ) e os de baixo/direita (+ _OFF_SOMBRA). Em cada
# ambiente esses pixels tem uma cor:
#   ''      (o app): a borda de cima ganha um fio de luz fria; a de baixo fica igual;
#   'brasa' (a luta): em cima a luz da lua, mais forte; embaixo a BRASA do chao
#           e do chefe refletida (e o contorno do lado da sombra fica em brasa).
# Nada de textura por dentro: o desenho continua limpo.
_OFF_LUZ, _OFF_SOMBRA = 80, 160
_MATERIAIS = 'HhCcAqPBMJI247pbKgWuDd&'
_LUZ_FRIA = (0.60, 0.70, 0.98)
_BRASA_REFLEXO = (0.92, 0.20, 0.12)
_TABS = {}
for _zz_amb in ('', 'brasa'):
    _zz_t = [bytearray(t) for t in _TAB]
    for _zz_c in _MATERIAIS:
        _zz_i = _COD[_zz_c]
        _zz_r, _zz_g, _zz_b, _zz_a = _PALETA[_zz_c]
        _zz_kl = 0.20 if _zz_amb == '' else 0.40
        _zz_luz = tuple(v + (l - v) * _zz_kl for v, l in zip((_zz_r, _zz_g, _zz_b), _LUZ_FRIA))
        _zz_som = (_zz_r, _zz_g, _zz_b) if _zz_amb == '' else tuple(v + (l - v) * 0.62 for v, l in zip((_zz_r, _zz_g, _zz_b), _BRASA_REFLEXO))
        for _zz_k in range(3):
            _zz_t[_zz_k][_zz_i + _OFF_LUZ] = int(round(_zz_luz[_zz_k] * 255))
            _zz_t[_zz_k][_zz_i + _OFF_SOMBRA] = int(round(_zz_som[_zz_k] * 255))
        _zz_t[3][_zz_i + _OFF_LUZ] = _zz_t[3][_zz_i + _OFF_SOMBRA] = int(round(_zz_a * 255))
    if _zz_amb == 'brasa':                         # o contorno do lado da sombra reflete o fogo
        for _zz_k, _zz_v in enumerate((255, 74, 40)):
            _zz_t[_zz_k][_COD['0']] = _zz_v
    _TABS[_zz_amb] = [bytes(t) for t in _zz_t]
_AMBIENTE = ['']


def definir_ambiente(nome=''):
    """Troca a luz do ambiente ('' = o app; 'brasa' = a luta contra o chefe).
    Os desenhos ja montados sao esquecidos (serao refeitos com a luz nova)."""
    global _TAB
    nome = nome if nome in _TABS else ''
    if nome == _AMBIENTE[0]:
        return
    _AMBIENTE[0] = nome
    _TAB = _TABS[nome]
    for cache in (_CACHE, _TEX, _TEX_MAPA):
        try:
            cache.clear()
        except Exception:
            pass
    for nome_c in ('_TEXC', '_CACHE_CAMADAS', '_TEX_CAMADAS', '_CACHE_PARTES'):
        c = globals().get(nome_c)
        if hasattr(c, 'clear'):
            c.clear()


_E_MATERIAL = bytearray(256)
for _c in _MATERIAIS:
    _E_MATERIAL[_COD[_c]] = 1
_E_MATERIAL = bytes(_E_MATERIAL)


def estilizar(idx, w, h):
    """Da o acabamento a uma imagem de indices (linha 0 = embaixo): devolve
    os indices com os tons de luz/sombra. Feito no PC ao assar os desenhos (e
    aqui mesmo nos poucos desenhos montados na hora)."""
    mat = _E_MATERIAL
    out = bytearray(idx)
    n = w * h
    for i in range(n):
        c = idx[i]
        if not mat[c]:
            continue
        x = i % w
        y = i // w
        cima = idx[i + w] if y < h - 1 else 0
        baixo = idx[i - w] if y > 0 else 0
        esq = idx[i - 1] if x > 0 else 0
        dire = idx[i + 1] if x < w - 1 else 0
        luz = not mat[cima] or not mat[esq]
        som = not mat[baixo] or not mat[dire]
        if luz and not som:
            out[i] = c + _OFF_LUZ
        elif som and not luz:
            out[i] = c + _OFF_SOMBRA
    return bytes(out)


_TAB = _TABS['']
_TC_NORMAL = (0, 0, 1, 0, 1, 1, 0, 1)
_TC_ESPELHO = (1, 0, 0, 0, 0, 1, 1, 1)
_BRANCO_SE = bytes([0] + [255] * 255)     # alpha > 0 -> 255 (silhueta branca)


def _gerar_imagem(p):
    ch = _chave(p)
    item = _CACHE.get(ch)
    if item is not None:
        _CACHE.move_to_end(ch)
        return ch, item
    _grava('inteiro', ch, p)
    pronto = _do_assado('inteiro', ch)
    if pronto:
        dados, rec, extra = pronto
        item = (dados, tuple(extra['caixa']), [tuple(b) for b in extra['bordas']] if extra.get('bordas') else None,
                rec)
        _CACHE[ch] = item
        while len(_CACHE) > _CACHE_MAX:
            _CACHE.popitem(last=False)
        return ch, item
    px = montar(p)
    dentro = [(x, y, c) for (x, y), c in px.items() if 0 <= x < TW and 0 <= y < TH]
    x0 = y0 = 10 ** 6
    x1 = y1 = -10 ** 6
    if dentro:
        xs = [d[0] for d in dentro]
        ys = [d[1] for d in dentro]
        X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)
        rastro = [d for d in dentro if d[2] in 'xX<>']
        if not rastro:                                   # o normal: caixa = recorte
            x0, x1, y0, y1 = X0, X1, Y0, Y1
        else:                                            # rastro nao conta para o enquadramento
            corpo = [d for d in dentro if d[2] not in 'xX<>']
            if corpo:
                xs = [d[0] for d in corpo]
                ys = [d[1] for d in corpo]
                x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        w, h = X1 - X0 + 1, Y1 - Y0 + 1
        idx = bytearray(w * h)
        cod = _COD
        for x, y, c in dentro:
            idx[(y - Y0) * w + (x - X0)] = cod[c]
        idx = estilizar(idx, w, h)
        buf = bytearray(w * h * 4)
        buf[0::4] = idx.translate(_TAB[0])
        buf[1::4] = idx.translate(_TAB[1])
        buf[2::4] = idx.translate(_TAB[2])
        buf[3::4] = idx.translate(_TAB[3])
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


_CAM = OrderedDict()       # (camada, chave) -> (bytes, recorte relativo)
_CAM_MAX = 900


def _rasteriza(px):
    """{(x, y): cor} -> (bytes RGBA, (x0, y0, w, h)) do recorte."""
    if not px:
        return bytes(4), (0, 0, 1, 1)
    xs = [q[0] for q in px]
    ys = [q[1] for q in px]
    X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = X1 - X0 + 1, Y1 - Y0 + 1
    idx = bytearray(w * h)
    cod = _COD
    for (x, y), c in px.items():
        idx[(y - Y0) * w + (x - X0)] = cod[c]
    idx = estilizar(idx, w, h)
    buf = bytearray(w * h * 4)
    buf[0::4] = idx.translate(_TAB[0])
    buf[1::4] = idx.translate(_TAB[1])
    buf[2::4] = idx.translate(_TAB[2])
    buf[3::4] = idx.translate(_TAB[3])
    return bytes(buf), (X0, Y0, w, h)


_FISICA = ('capa', 'cabelo', 'lift', 'fase', 'fase_cab', 'hx', 'hy', 'sobe', 'cresce')


def chave_camadas(q):
    """As 3 chaves (corpo, cauda, cabeca) da pose composta q (com fisica).
    O corpo nao depende da fisica; a cauda e a cabeca so dela."""
    q4 = lambda v: round((v or 0.0) * 4) / 4.0
    corpo = tuple(kv for kv in _chave(q) if kv[0] not in _FISICA)
    cx, topo, cab_x, cab_ty = ancoras(q)
    mug = bool(q.get('mugetsu'))
    cauda = ('cauda', q4(q['capa']), q4(q['lift']), round(q.get('fase', 0.0) or 0.0, 3),
             q4(q.get('saia', 1.0)), mug)
    fcab = q.get('fase_cab', q.get('fase', 0.0))
    cabeca = None if _cabeca_no_corpo(q) else (
        'cabeca', q['olhos'], q4(q['cabelo']), q4(q.get('sobe', 0.0)), round(fcab or 0.0, 3),
        mug, round(q.get('cresce', 1.0) or 0.0, 2) if mug else None)
    return corpo, cauda, cabeca


def imagem_camada(q, qual, chave):
    """(bytes, recorte relativo) da camada `qual` da pose q, com cache."""
    k = (qual, chave)
    item = _CAM.get(k)
    if item is not None:
        _CAM.move_to_end(k)
        return item
    _grava(qual, chave, q)
    pronto = _do_assado(qual, chave)
    if not pronto and qual in ('cauda', 'cabeca') and not _GRAVA:
        pronto = _assado_vizinho(qual, chave)
    item = (pronto[0], pronto[1]) if pronto else _rasteriza(montar(q, camada=qual))
    _CAM[k] = item
    while len(_CAM) > _CAM_MAX:
        _CAM.popitem(last=False)
    return item


_TEXC = OrderedDict()
_TEXC_MAX = 260


def textura_camada(q, qual, chave, silhueta=False, xadrez=False):
    """Texture da camada (e o recorte relativo)."""
    k = (qual, chave, silhueta, xadrez)
    tex = _TEXC.get(k)
    dados, rec = imagem_camada(q, qual, chave)
    if tex is not None:
        _TEXC.move_to_end(k)
        return tex, rec
    tex = _criar_textura(dados, rec, silhueta, xadrez)
    _TEXC[k] = tex
    while len(_TEXC) > _TEXC_MAX:
        _TEXC.popitem(last=False)
    return tex, rec


# ═══════════════════════════════════════════════════════════════════
#  QUADROS PRONTOS (assados no PC; o arquivo vai no APK)
#  Formato: b'YQ01' + tamanho do cabecalho (4 bytes) + cabecalho (json em
#  zlib) + as imagens, cada uma em zlib (1 byte por texel = cor da paleta).
#  Se o desenho mudou depois de assar (a pose de prova sai diferente), o
#  arquivo e ignorado e tudo e desenhado na hora, como antes.
# ═══════════════════════════════════════════════════════════════════
import os as _os
import json as _json
import zlib as _zlib
import hashlib as _hashlib

_ASSADO = {}               # repr((camada, chave)) -> (inicio, tamanho, recorte, extra)
_ASSADO_CAIXAS = {}        # repr(chave da pose) -> caixa
_ASSADO_DADOS = [None]
_ASSADO_OK = [None]        # None = ainda nao conferido
_ASSADO_PROVA = [None]
_GRAVA = _os.environ.get('YORU_GRAVA')
_GRAVADOS = {}


def _pose_prova():
    return dict(POSE_A['guarda'], capa=0.0, cabelo=0.0, lift=0.0, fase=0.0)


def _digital(dados):
    return _hashlib.md5(dados).hexdigest()[:16]


def carregar_assado(caminho=None):
    """Le o indice do arquivo de quadros prontos (as imagens so quando
    forem pedidas)."""
    try:
        caminho = caminho or _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'yoru_quadros.bin')
        if not _os.path.exists(caminho):
            return False
        with open(caminho, 'rb') as f:
            dados = f.read()
        if dados[:4] != b'YQ01':
            return False
        n = int.from_bytes(dados[4:8], 'little')
        cab = _json.loads(_zlib.decompress(dados[8:8 + n]).decode('utf-8'))
        if cab.get('paleta') != ''.join(sorted(_PALETA)) or cab.get('R') != R:
            print('[kirito] quadros prontos de outra versao: ignorados')
            return False
        base = 8 + n
        for ch, (ini, tam, rec, extra) in cab['itens'].items():
            _ASSADO[ch] = (base + ini, tam, tuple(rec), extra)
        for ch, cx in cab.get('caixas', {}).items():
            _ASSADO_CAIXAS[ch] = tuple(cx)
        _ASSADO_PROVA[0] = cab.get('prova')
        _ASSADO_DADOS[0] = dados
        print(f"[kirito] quadros prontos: {len(_ASSADO)} imagens, {len(_ASSADO_CAIXAS)} caixas")
        return True
    except Exception as e:
        print(f"[kirito] quadros prontos: {e}")
        return False


def _assado_valido():
    """Confere uma vez se o desenho de hoje e o mesmo de quando assou."""
    if _ASSADO_OK[0] is None:
        try:
            q = _pose_prova()
            dados, rec = _rasteriza(montar(q, camada='corpo'))
            _ASSADO_OK[0] = bool(_ASSADO) and _digital(dados) == _ASSADO_PROVA[0]
            if not _ASSADO_OK[0] and _ASSADO:
                print('[kirito] quadros prontos desatualizados: ignorados')
        except Exception as e:
            print(f"[kirito] prova: {e}")
            _ASSADO_OK[0] = False
    return _ASSADO_OK[0]


def _do_assado(qual, chave):
    """(bytes RGBA, recorte, extra) da imagem pronta, ou None."""
    if not _ASSADO:
        return None
    item = _ASSADO.get(repr((qual, chave)))
    if item is None or not _assado_valido():
        return None
    ini, tam, rec, extra = item
    idx = _zlib.decompress(_ASSADO_DADOS[0][ini:ini + tam])
    buf = bytearray(len(idx) * 4)
    buf[0::4] = idx.translate(_TAB[0])
    buf[1::4] = idx.translate(_TAB[1])
    buf[2::4] = idx.translate(_TAB[2])
    buf[3::4] = idx.translate(_TAB[3])
    return bytes(buf), rec, extra


_VIZINHOS = {}            # (camada, assinatura) -> [(fisica, chave repr)]


def _partes_fisica(qual, chave):
    """(assinatura, fisica) de uma chave de camada: o que tem que bater
    exato e o que pode ser so parecido."""
    if qual == 'cauda':            # ('cauda', capa, lift, fase, saia, mug)
        return (chave[4], chave[5]), (chave[1], chave[2], chave[3])
    # ('cabeca', olhos, cabelo, sobe, fase, mug, cresce)
    return (chave[1], chave[5], chave[6]), (chave[2], chave[3], chave[4])


def _assado_vizinho(qual, chave):
    """Desenho pronto mais parecido (so o balanco diferente), ou None."""
    try:
        if not _ASSADO or not _assado_valido():
            return None
        if not _VIZINHOS:
            import ast
            for ch in _ASSADO:
                if ch.startswith("('cauda'") or ch.startswith("('cabeca'"):
                    try:
                        qq, cc = ast.literal_eval(ch)
                        ass, fis = _partes_fisica(qq, cc)
                        _VIZINHOS.setdefault((qq, ass), []).append((fis, ch))
                    except Exception:
                        pass
            _VIZINHOS[None] = True
        ass, fis = _partes_fisica(qual, chave)
        lista = _VIZINHOS.get((qual, ass))
        if not lista:
            return None

        def dist(f):
            df = abs((f[2] or 0.0) - (fis[2] or 0.0)) % 1.0
            return (abs((f[0] or 0.0) - (fis[0] or 0.0)) + abs((f[1] or 0.0) - (fis[1] or 0.0))
                    + min(df, 1.0 - df) * 1.5)
        melhor = min(lista, key=lambda it: dist(it[0]))
        if dist(melhor[0]) > 1.6:
            return None                  # longe demais: melhor desenhar certo
        ini, tam, rec, extra = _ASSADO[melhor[1]]
        idx = _zlib.decompress(_ASSADO_DADOS[0][ini:ini + tam])
        buf = bytearray(len(idx) * 4)
        buf[0::4] = idx.translate(_TAB[0])
        buf[1::4] = idx.translate(_TAB[1])
        buf[2::4] = idx.translate(_TAB[2])
        buf[3::4] = idx.translate(_TAB[3])
        return bytes(buf), rec, extra
    except Exception as e:
        print(f"[kirito] vizinho: {e}")
        return None


def _grava(qual, chave, q):
    """Anota o pedido (so no PC, quando assando)."""
    if _GRAVA:
        _GRAVADOS.setdefault(repr((qual, chave)), (qual, q))


def salvar_gravados():
    if not _GRAVA:
        return
    try:
        velho = {}
        if _os.path.exists(_GRAVA):
            with open(_GRAVA, encoding='utf-8') as f:
                velho = _json.load(f)
        for ch, (qual, q) in _GRAVADOS.items():
            velho[ch] = [qual, {kk: (list(v) if isinstance(v, tuple) else v) for kk, v in q.items()}]
        with open(_GRAVA, 'w', encoding='utf-8') as f:
            _json.dump(velho, f)
        print(f"[kirito] gravados {len(_GRAVADOS)} pedidos (total {len(velho)})")
    except Exception as e:
        print(f"[kirito] gravar: {e}")


_TEX_MAPA = {}


def textura_mapa(linhas):
    """Texture (pixel duro) de um mapa de caracteres da paleta (linha 0 em
    cima). Guardada."""
    chave = id(linhas)
    tex = _TEX_MAPA.get(chave)
    if tex is not None:
        return tex
    h, w = len(linhas), len(linhas[0])
    idx = bytearray(w * h)
    for r, l in enumerate(linhas):
        base = (h - 1 - r) * w
        for cc, ch in enumerate(l):
            if ch != '.':
                idx[base + cc] = _COD[ch]
    buf = bytearray(w * h * 4)
    for i in range(4):
        buf[i::4] = idx.translate(_TAB[i])
    dados = bytes(buf)
    tex = Texture.create(size=(w, h), colorfmt='rgba')
    tex.mag_filter = 'nearest'
    tex.min_filter = 'nearest'
    tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
    tex.add_reload_observer(lambda t, d=dados: t.blit_buffer(d, colorfmt='rgba', bufferfmt='ubyte'))
    _TEX_MAPA[chave] = tex
    return tex


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
    boneco e isso nao pode travar o quadro. A fisica (vento, cabelo) nao
    conta: a caixa quase nao muda com ela."""
    if not p.get('mugetsu'):
        p = dict(p, capa=0.0, cabelo=0.0, lift=0.0, fase=0.0, hx=0, hy=0)
    ch = _chave(p)
    _grava('caixa', ch, p)               # (so anota quando esta assando os quadros)
    item = _CACHE.get(ch)
    if item is not None:
        return item[1]
    cx = _CAIXAS.get(ch)
    if cx is None and _ASSADO_CAIXAS and _assado_valido():
        cx = _ASSADO_CAIXAS.get(repr(ch))
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


def _criar_textura(dados, rec, silhueta=False, xadrez=False):
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
    return tex


# ═══════════════════════════════════════════════════════════════════
#  CLIPES DO BANKAI (boneco articulado feito com o desenho da referencia,
#  gerado no PC por dev/bankai_rig.py; aqui so toca os quadros prontos)
# ═══════════════════════════════════════════════════════════════════
_CLIPES = {}               # 'cab' -> cabecalho; 'dados' -> bytes; 'tab'/'sil' -> tabelas
_CLIPE_TEX = OrderedDict()
_CLIPE_TEX_MAX = 320       # todos os desenhos do Bankai e do reiatsu cabem (nada e refeito)


def aquecer_clipes(nomes=None, por_quadro=2):
    """Cria antes as texturas dos clipes (`por_quadro` por quadro da tela):
    na hora do BAN-KAI nenhum desenho precisa ser montado - no celular,
    montar varios de uma vez no estouro dava tranco."""
    try:
        cab = clipes_dados()
    except Exception as e:
        print(f"[kirito] aquecer clipes: {e}")
        return
    fila = []
    vistos = set()
    for nome in (nomes or list(cab['clipes'])):
        c = cab['clipes'].get(nome)
        if not c:
            continue
        for i, q in enumerate(c['quadros']):
            if q[0] in vistos:                 # quadro repetido: mesma imagem
                continue
            vistos.add(q[0])
            fila.append((nome, i))

    def _passo(dt):
        try:
            for _ in range(por_quadro):
                if not fila:
                    return False
                nome, i = fila.pop(0)
                quadro_clipe(nome, i)
        except Exception as e:
            print(f"[kirito] aquecer clipes: {e}")
            return False
    Clock.schedule_interval(_passo, 0)


def clipes_dados():
    """Cabecalho de bankai/clipes.bin (le uma vez)."""
    if 'cab' in _CLIPES:
        return _CLIPES['cab']
    caminho = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'bankai', 'clipes.bin')
    with open(caminho, 'rb') as f:
        dados = f.read()
    if dados[:4] != b'BK01':
        raise ValueError('clipes.bin de outra versao')
    n = int.from_bytes(dados[4:8], 'little')
    cab = _json.loads(_zlib.decompress(dados[8:8 + n]).decode('utf-8'))
    _CLIPES['base'] = 8 + n
    _CLIPES['dados'] = dados
    pal = cab['paleta']
    tabs = [bytearray(256) for _ in range(4)]
    for i, c in enumerate(pal):
        for k in range(4):
            tabs[k][i] = c[k]
    _CLIPES['tab'] = [bytes(t) for t in tabs]
    sil = bytearray(256)
    for i in range(1, len(pal)):
        sil[i] = 255
    _CLIPES['sil'] = bytes(sil)
    _CLIPES['cab'] = cab
    return cab


def quadro_clipe(nome, i, silhueta=False):
    """(textura, caixa (x0, y0, w, h) na tela do clipe, mao, ponta) do
    quadro i do clipe `nome`."""
    cab = clipes_dados()
    pos, tam, caixa_q, mao, ponta = cab['clipes'][nome]['quadros'][i]
    ch = (pos, silhueta)                   # quadro repetido (desenho segurado) usa a mesma textura
    tex = _CLIPE_TEX.get(ch)
    if tex is None:
        ini = _CLIPES['base'] + pos
        idx = _zlib.decompress(_CLIPES['dados'][ini:ini + tam])
        buf = bytearray(len(idx) * 4)
        if silhueta:
            s = idx.translate(_CLIPES['sil'])
            buf[0::4] = s
            buf[1::4] = s
            buf[2::4] = s
            buf[3::4] = s
        else:
            t = _CLIPES['tab']
            buf[0::4] = idx.translate(t[0])
            buf[1::4] = idx.translate(t[1])
            buf[2::4] = idx.translate(t[2])
            buf[3::4] = idx.translate(t[3])
        w, h = caixa_q[2], caixa_q[3]
        tex = Texture.create(size=(w, h), colorfmt='rgba')
        tex.mag_filter = tex.min_filter = 'nearest'
        tex.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
        tex.flip_vertical()                     # as linhas vem de cima para baixo
        _CLIPE_TEX[ch] = tex
        while len(_CLIPE_TEX) > _CLIPE_TEX_MAX:
            _CLIPE_TEX.popitem(last=False)
    else:
        _CLIPE_TEX.move_to_end(ch)
    return tex, caixa_q, mao, ponta


def _tc_espelhado(tc):
    u0, v0, u1, _, _, v1 = tc[0], tc[1], tc[2], tc[3], tc[4], tc[5]
    return (u1, v0, u0, v0, u0, v1, u1, v1)


def _no_retangulo(rect, tex, rec, ps, espelhar, chao=None):
    """Poe a textura recortada no lugar certo do quadro do boneco. chao: o
    que ficar abaixo dessa linha (texels) nao aparece (as caudas do
    sobretudo nao atravessam o chao)."""
    te = ps / float(R)
    x0, y0, w, h = rec
    corte = 0
    if chao is not None and y0 < chao:
        corte = min(h, chao - y0)
    if espelhar:
        x0 = TW - x0 - w
    rect.texture = tex
    rect.pos = (x0 * te, (y0 + corte) * te)
    rect.size = (w * te, (h - corte) * te)
    if corte:
        v = corte / float(h)
        rect.tex_coords = (1, v, 0, v, 0, 1, 1, 1) if espelhar else (0, v, 1, v, 1, 1, 0, 1)
    else:
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
        self.ps = max(R, int(round(ps)))                  # texel = ps/R
        self.size = (GW * self.ps, GH * self.ps)
        self.pivo = None
        self._base = pose()               # pose da sequencia (sem fisica)
        self._pose = self._base           # pose desenhada (com fisica)
        self._ult_chave = None
        self._desenho = None              # clipe do Bankai tocando (None = boneco montado)
        self.escala_clipe = 1.0           # tamanho do desenho dos clipes (2 = cada ponto vira 2x2)
        self._clipe_t = 0.0
        self._clipe_loop = True
        self._clipe_fim = None
        self._clipe_cb = None
        self._clipe_ult = -1
        self._ev = None
        self._ev_vida = None
        self._seq = []
        self._i = 0
        self._t_seq = 0.0
        self._grade = -1                  # ultimo desenho da grade de 24/s
        self._dt_des = 0.0                # tempo desde o ultimo desenho
        self._no_relogio = False          # dentro do tique de desenho (mostrar so guarda a pose)
        self._a_cada_desenho = []         # quem anda junto com os desenhos (ex.: o deslocamento)
        self._on_quadro = None
        self._on_fim = None
        self._loop = False
        self.ao_redesenhar = None         # chamado quando a imagem da pose muda
        self._pausa = 0.0                 # hit-stop: segundos congelado no impacto
        self.aura = 0.0                   # borda de energia fervendo (0 = desligada)
        self._aura_camadas = []
        self._aura_t = 0.0
        self._aura_n = 0
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
        # o que a fisica mostra fica preso em batidas (como desenhos em 2s):
        # o sobretudo troca num tique, o cabelo no outro, a cabeca a cada 2 -
        # o corpo vai primeiro e o resto chega depois, cada um no seu tempo
        self._batida = 0
        self._preso = {'capa': 0.0, 'lift': 0.0, 'fase': 0.0, 'cabelo': 0.0, 'fase_cab': 0.0,
                       'hx': 0, 'hy': 0}
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
            # borda de energia (BAN...): a silhueta repetida em volta, em roxo
            self._cor_aura = Color(0.66, 0.40, 1.0, 0)
            self._aura_rects = [Rectangle(pos=(0, 0), size=(0, 0)) for _ in range(24)]
            Color(1, 1, 1, 1)
            self._rect_cauda = Rectangle(pos=(0, 0), size=(0, 0))
            self._rect = Rectangle(pos=(0, 0), size=(GW * self.ps, GH * self.ps))
            self._rect_cab = Rectangle(pos=(0, 0), size=(0, 0))
            self._cor_clarao = Color(0.85, 0.97, 1, 0)
            self._rect_clarao_cauda = Rectangle(pos=(0, 0), size=(0, 0))
            self._rect_clarao = Rectangle(pos=(0, 0), size=(0, 0))
            self._rect_clarao_cab = Rectangle(pos=(0, 0), size=(0, 0))
            PopMatrix()
        self.bind(pos=self._mover, x=self._mover, y=self._mover,
                  rotacao=self._mover, escala_y=self._mover, escala_x=self._mover,
                  espelhar=self._virou,
                  clarao=lambda *_: self._desenhar(forcar=True))
        self._mover()
        self._desenhar()

    # ── geometria ────────────────────────────────────────────────────
    def recortar(self, y0=None, y1=None):
        """Mostra so a faixa de altura y0..y1 do boneco (coordenadas do pai;
        None = sem limite). recortar() tira o recorte. Na transformacao: o
        Yoru normal por cima da linha de energia e o Bankai por baixo."""
        if y0 is None and y1 is None:
            if getattr(self, '_recorte', None) is not None:
                for grupo, ins in self._recorte:
                    for i in ins:
                        try:
                            grupo.remove(i)
                        except Exception:
                            pass
                self._recorte = None
            return
        a = -100000.0 if y0 is None else float(y0)
        b = 100000.0 if y1 is None else float(y1)
        if getattr(self, '_recorte', None) is None:
            r1 = Rectangle(pos=(-100000, a), size=(200000, b - a))
            r2 = Rectangle(pos=(-100000, a), size=(200000, b - a))
            antes = [StencilPush(), r1, StencilUse()]
            depois = [StencilUnUse(), r2, StencilPop()]
            for i in antes:
                self.canvas.before.add(i)
            for i in depois:
                self.canvas.after.add(i)
            self._recorte = [(self.canvas.before, antes), (self.canvas.after, depois)]
            self._rec_rects = (r1, r2)
        for r in self._rec_rects:
            r.pos = (-100000, a)
            r.size = (200000, max(0.0, b - a))

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

    def _local_texel(self, x, y):
        """Texel do sprite -> px locais (com o espelho)."""
        te = self.ps / float(R)
        if self.espelhar:
            x = TW - 1 - x
        return (x + 0.5) * te, (y + 0.5) * te

    def te_clipe(self):
        """Tamanho na tela de um ponto do desenho dos clipes (Bankai, reiatsu)."""
        return self.ps / float(R) * self.escala_clipe

    def _local_desenho(self, sx, sy):
        """Pixel (sx, sy) da tela do clipe (y para baixo) -> px locais."""
        cab = clipes_dados()
        te = self.te_clipe()
        ax, ay = self.ancora_local()
        qx, qy = cab['quadril']
        dx = (sx - qx) * te
        return (ax - dx if self.espelhar else ax + dx), ay + (qy - sy) * te

    def _fps_clipe(self, nome=None):
        cab = clipes_dados()
        return float(cab['clipes'][nome or self._desenho].get('fps', cab['fps']))

    def _quadro_atual(self):
        cab = clipes_dados()
        n = len(cab['clipes'][self._desenho]['quadros'])
        i = int(self._clipe_t * self._fps_clipe() + 1e-6)
        return (i % n) if self._clipe_loop else min(i, n - 1)

    def corpo_desenho(self):
        """(x0, x1, y_pe, altura) do corpo do Bankai (sem cabelo/espada), no pai."""
        cab = clipes_dados()
        qx, qy = cab['quadril']
        if cab.get('corpo'):
            x0, x1, y_topo, y_pe = cab['corpo']
            xa, ya = self._local_desenho(x0, y_pe)
            xb, yb = self._local_desenho(x1, y_topo)
        else:
            xa, ya = self._local_desenho(qx - 14, qy + 60)
            xb, yb = self._local_desenho(qx + 16, qy - 105)
        return (self.x + min(xa, xb), self.x + max(xa, xb), self.y + ya, yb - ya)

    def olhos_desenho(self):
        """(x, y) dos olhos do Bankai no pai (para acenderem dentro do reiatsu)."""
        cab = clipes_dados()
        o = cab.get('olhos')
        if not o:
            return None
        lx, ly = self._local_desenho(o[0], o[1])
        return self.x + lx, self.y + ly

    def mao_local(self, qual=1, p=None):
        if p is None and self._desenho is not None:
            mao = quadro_clipe(self._desenho, self._quadro_atual())[2]
            return self._local_desenho(*mao)
        return self._local_texel(*maos_texel(p or self._base, qual)[0])

    def ponto_mao(self, qual=1):
        """Posicao da mao (coords do pai), sem considerar rotacao."""
        lx, ly = self.mao_local(qual)
        return self.x + lx, self.y + ly

    def ponta_espada(self, qual=1, p=None):
        if p is None and self._desenho is not None:
            lx, ly = self._local_desenho(*quadro_clipe(self._desenho, self._quadro_atual())[3])
            return self.x + lx, self.y + ly
        """(x, y) da ponta da lamina `qual` (coords do pai), sem rotacao."""
        lx, ly = self._local_texel(*maos_texel(p or self._base, qual)[1])
        return self.x + lx, self.y + ly

    def extensao(self, p=None):
        if p is None and self._desenho is not None:
            cab = clipes_dados()
            te = self.te_clipe()
            qx, qy = cab['quadril']
            x0, y0, w, h = quadro_clipe(self._desenho, self._quadro_atual())[1]
            esq, dir_ = (qx - x0) * te, (x0 + w - qx) * te
            if self.espelhar:
                esq, dir_ = dir_, esq
            return esq, (y0 + h - qy) * te, dir_, (qy - y0) * te
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
    def mostrar_clipe(self, nome, loop=True, on_fim=None, on_quadro=None, base=None, t0=0.0):
        """Toca o clipe `nome` do Bankai (quadros prontos, 30/s) no lugar do
        boneco montado. loop=False: para no ultimo quadro e chama on_fim.
        on_quadro(i) a cada quadro novo. base = a pose que os efeitos
        consultam (forma, espada acesa). t0 = de onde comeca (s)."""
        self.parar()
        self._desenho = nome
        self._clipe_t = float(t0)
        self._clipe_loop = loop
        self._clipe_fim = on_fim
        self._clipe_cb = on_quadro
        self._clipe_ult = -1
        if base is not None:
            self._base = base
        self._desenhar(forcar=True)

    def mostrar_desenho(self, nome, base=None):
        self.mostrar_clipe(nome, loop=True, base=base)

    def _avanca_clipe(self, dt):
        """Chamado pela fisica (30/s): anda o clipe e avisa quadro/fim."""
        if self._desenho is None:
            return
        self._clipe_t += dt
        n = len(clipes_dados()['clipes'][self._desenho]['quadros'])
        dur = n / self._fps_clipe()
        t = (self._clipe_t % dur) if self._clipe_loop else min(self._clipe_t, dur - 1e-6)
        i = int(t * FPS + 1e-6)                    # aviso em quadros de 30/s (as cenas contam assim)
        if i != self._clipe_ult:
            ult = self._clipe_ult
            self._clipe_ult = i
            if self._clipe_cb is not None:
                # avisa tambem os quadros que passaram entre dois tiques
                seq = range(ult + 1, i + 1) if 0 <= ult < i and i - ult <= 4 else (i,)
                for j in seq:
                    try:
                        self._clipe_cb(j)
                    except Exception as e:
                        print(f"[kirito] clipe quadro: {e}")
        if not self._clipe_loop:
            if self._clipe_t >= dur and self._clipe_fim is not None:
                cb, self._clipe_fim = self._clipe_fim, None
                try:
                    cb()
                except Exception as e:
                    print(f"[kirito] clipe fim: {e}")

    def mostrar(self, p):
        self._desenho = None
        if self._no_relogio or (self._ev_vida is not None and self._ult_chave is not None):
            # com o relogio andando, a pose nova aparece no proximo desenho
            # (24/s, junto com a fisica) - nunca fora do compasso
            self._base = p
            return
        if self._base is not p and self.fisica:
            ant = self._base
            if ant is None or any(ant.get(k) != p.get(k) for k in ('dx', 'dy', 'm1', 'm2', 'a1', 'a2',
                                                                     'pernas', 'pt', 'olhos', 'incl')):
                self._travar_batida(forcar=True)       # corpo mudou: o resto e redesenhado junto
        self._base = p
        self._desenhar()

    def _composta(self):
        b = self._base
        if not self.fisica:
            return b
        q = dict(b)
        pr = self._preso
        q['capa'] = b['capa'] + pr['capa']
        q['cabelo'] = b['cabelo'] + pr['cabelo']
        q['lift'] = b['lift'] + pr['lift']
        q['fase'] = pr['fase']
        q['fase_cab'] = pr['fase_cab']
        # cabeca: +-1 px de atraso
        q['hx'] = pr['hx']
        q['hy'] = pr['hy']
        if b.get('mugetsu'):
            if (b.get('cresce', 1.0) or 0.0) < 0.999:          # crescendo: o cabelo so cresce
                q['cabelo'] = b['cabelo']
                q['fase_cab'] = 0.0
            else:
                q['cabelo'] = round(q['cabelo'] * 2) / 2.0
                q['fase_cab'] = (int(q['fase_cab'] * 3 + 1e-6) % 3) / 3.0
            q['fase'] = (int(q['fase'] * 3 + 1e-6) % 3) / 3.0
        else:
            q['cabelo'] = round(q['cabelo'] * 2) / 2.0
        q['capa'] = round(q['capa'] * 2) / 2.0
        q['lift'] = round(q['lift'] * 2) / 2.0
        # laminas: seguem a pose com um pouquinho de atraso/mola (max 8 graus)
        # (as laminas nao atrasam: o corpo e desenhado uma vez por pose)

        # luz: aura da lamina ou clarao de impacto, em 3 degraus
        luz = max(self.luz, self._luz_imp)
        q['luz'] = 1.0 if luz >= 0.75 else (0.5 if luz >= 0.3 else 0.0)
        # brilho percorre as laminas a cada ~2,6 s
        ciclo = self._t % 2.6
        if b.get('brilho') is not None:
            q['brilho'] = b['brilho']
        else:
            q['brilho'] = (round(ciclo / 0.45 * 11) / 11.0) if (ciclo < 0.45 and self._loop
                                                                  and not b.get('mugetsu')) else None
        return q

    def _camadas_da_pose(self, q):
        """[(retangulo, retangulo da silhueta, qual, chave, deslocamento)]"""
        corpo, cauda, cabeca = chave_camadas(q)
        cx, topo, cab_x, cab_ty = ancoras(q)
        out = [(self._rect_cauda, self._rect_clarao_cauda, 'cauda', cauda, (cx, topo)),
               (self._rect, self._rect_clarao, 'corpo', corpo, (0, 0))]
        if cabeca is not None:
            out.append((self._rect_cab, self._rect_clarao_cab, 'cabeca', cabeca,
                        (cab_x + int(q.get('hx', 0) or 0), cab_ty + int(q.get('hy', 0) or 0))))
        else:
            self._rect_cab.size = (0, 0)
            self._rect_clarao_cab.size = (0, 0)
        return out

    def _desenhar_desenho(self, forcar=False):
        f = self._quadro_atual()
        chave = ('clipe', self._desenho, f, self.espelhar, self.clarao > 0)
        if chave == self._ult_chave and not forcar:
            return
        self._ult_chave = chave
        te = self.te_clipe()
        tex, (cx0, cy0, w, h), _, _ = quadro_clipe(self._desenho, f)
        # canto de baixo/esquerda do quadro (a tela do clipe tem y para baixo)
        xa, y0 = self._local_desenho(cx0, cy0 + h)
        x0 = xa - w * te if self.espelhar else xa
        for rect, ligado in ((self._rect, True), (self._rect_clarao, self.clarao > 0)):
            if not ligado:
                rect.size = (0, 0)
                continue
            t = tex if rect is self._rect else quadro_clipe(self._desenho, f, silhueta=True)[0]
            rect.texture = t
            rect.pos = (x0, y0)
            rect.size = (w * te, h * te)
            rect.tex_coords = _tc_espelhado(t.tex_coords) if self.espelhar else t.tex_coords
        for rect in (self._rect_cauda, self._rect_cab, self._rect_clarao_cauda, self._rect_clarao_cab):
            rect.size = (0, 0)
        self._pos_aura()
        self._cor_clarao.a = self.clarao
        if self.ao_redesenhar is not None:
            self.ao_redesenhar()

    def borda_energia(self, v):
        """Borda de energia fervendo em volta do boneco (o BAN... do Ichigo):
        a silhueta repetida 1-2 pixels para fora em roxo, trocando 12 vezes
        por segundo (sobe mais que desce, como chama). v = 0 desliga."""
        self.aura = max(0.0, float(v))
        self._desenhar(forcar=True)
        if self.aura <= 0:
            self._aura_camadas = []
            self._pos_aura()

    def _pos_aura(self):
        rects = self._aura_rects
        if self.aura <= 0 or not self._aura_camadas or self._desenho is not None:
            for r in rects:
                r.size = (0, 0)
            self._cor_aura.a = 0
            return
        te = self.ps / float(R)
        dirs = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1))
        i = 0
        n = self._aura_n
        for (tex, pos, size, tc) in self._aura_camadas:
            for j, (dx, dy) in enumerate(dirs):
                if i >= len(rects):
                    break
                # ferve em ritmo: cada lado pulsa 1-2 pixels em alternancia (sem
                # sortear saltos grandes); em cima a chama sobe mais
                k = 1 + ((n + j) % 2 if self.aura >= 0.5 else 0)
                if dy > 0 and self.aura >= 0.7 and (n + j) % 3 == 0:
                    k += 1
                if dx and dy:
                    k = 1
                r = rects[i]
                i += 1
                r.texture = tex
                r.pos = (pos[0] + dx * k * te, pos[1] + dy * k * te)
                r.size = size
                r.tex_coords = tc
        for r in rects[i:]:
            r.size = (0, 0)
        self._cor_aura.a = 1.0 if self.aura >= 0.5 else 0.55

    def _desenhar(self, forcar=False):
        if self._desenho is not None:
            try:
                return self._desenhar_desenho(forcar)
            except Exception as e:
                print(f"[kirito] desenho pronto: {e}")
                self._desenho = None
        try:
            self._pose = self._composta()
            if True:
                camadas = self._camadas_da_pose(self._pose)
                chave = (tuple((c[3], c[4]) for c in camadas), self.espelhar, self.clarao > 0)
                if chave == self._ult_chave and not forcar:
                    return
                self._ult_chave = chave
                aura = []
                for rect, rect_s, qual, ch, (ox, oy) in camadas:
                    tex, rec = textura_camada(self._pose, qual, ch)
                    rec2 = (rec[0] + ox, rec[1] + oy, rec[2], rec[3])
                    chao = _PES * R if qual == 'cauda' else None
                    _no_retangulo(rect, tex, rec2, self.ps, self.espelhar, chao)
                    if self.clarao > 0:
                        tex, rec = textura_camada(self._pose, qual, ch, silhueta=True)
                        _no_retangulo(rect_s, tex, rec2, self.ps, self.espelhar, chao)
                    else:
                        rect_s.size = (0, 0)
                    if self.aura > 0:
                        tex_s, rec = textura_camada(self._pose, qual, ch, silhueta=True)
                        r0 = self._aura_rects[-1]
                        _no_retangulo(r0, tex_s, rec2, self.ps, self.espelhar, chao)
                        aura.append((tex_s, tuple(r0.pos), tuple(r0.size), tuple(r0.tex_coords)))
                self._aura_camadas = aura
                self._pos_aura()
            self._cor_clarao.a = self.clarao
            if self.ao_redesenhar is not None:
                self.ao_redesenhar()
        except Exception as e:
            print(f"[kirito] desenho ignorado: {e}")

    def _vida(self, dt):
        """O relogio do boneco (todo quadro da tela): a borda de energia
        ferve a 30/s; na grade de 24/s anda a sequencia, roda a fisica do
        sobretudo/cabelo (pela velocidade real do boneco) e troca o desenho -
        corpo, pano e cabelo no mesmo tique, como um quadro de anime."""
        try:
            if (self.parent is None and self._ev is None and self._desenho is None
                    and not self._a_cada_desenho):
                self._ev_vida = None                 # fora da tela e sem nada tocando
                return False
            if self._pausa > 0:                      # hit-stop: congela tudo
                self._pausa = max(0.0, self._pausa - dt)
                return
            dt = min(dt, 1 / 15.)
            self._t += dt
            if self._desenho is not None:
                self._avanca_clipe(dt)
                self._desenhar()                     # clipe: segue o ritmo do proprio clipe
            if self.aura > 0:                        # a borda de energia ferve (30/s)
                self._aura_t += dt
                if self._aura_t >= 1 / 30.:
                    self._aura_t = 0.0
                    self._aura_n += 1
                    self._pos_aura()
            self._dt_des += dt
            g = int(self._t * DESENHOS)
            if g == self._grade:
                return
            self._grade = g
            dt, self._dt_des = min(self._dt_des, 1 / 15.), 0.0
            self._no_relogio = True
            try:
                for fn in list(self._a_cada_desenho):    # o deslocamento anda no mesmo tique
                    try:
                        if fn(dt) is False and fn in self._a_cada_desenho:
                            self._a_cada_desenho.remove(fn)
                    except Exception as e:
                        print(f"[kirito] a cada desenho: {e}")
                        if fn in self._a_cada_desenho:
                            self._a_cada_desenho.remove(fn)
                if self._ev is not None:
                    self._mostra_seq(dt)             # a pose deste instante
            finally:
                self._no_relogio = False
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
            self._travar_batida(forcar=True)
            self._desenhar()
        except Exception as e:
            print(f"[kirito] fisica: {e}")

    def _travar_batida(self, forcar=False):
        """Copia o estado das molas para o desenho, a cada desenho (24/s).
        O atraso do cabelo e do sobretudo vem das molas; o balanco anda um
        passo (de FASES) por desenho, entao o pano nunca fica congelado."""
        self._batida = 0
        pr = self._preso
        pr['capa'] = self._m_capa.x
        pr['lift'] = self._m_lift.x
        pr['fase'] = (int(self._fase * FASES) % FASES) / float(FASES)
        pr['cabelo'] = self._m_cab.x
        pr['fase_cab'] = (int(self._fase * FASES + 1) % FASES) / float(FASES)   # o cabelo vai 1 passo atras do pano
        pr['hx'] = int(round(max(-1.0, min(1.0, self._m_hx.x))))
        pr['hy'] = int(round(max(-1.0, min(1.0, self._m_hy.x))))

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
        if getattr(self, 'clarao_preso', False):
            return
        # quadro de impacto: o boneco inteiro branco e chapado por 2 quadros
        # (3 no forte) e volta de uma vez - nada de cinza meio transparente
        self.clarao = 1.0
        n = [3 if forte else 2]

        def _p(dt):
            if getattr(self, 'clarao_preso', False):
                return False                        # um quadro de impacto esta usando a silhueta
            n[0] -= 1
            if n[0] <= 0:
                self.clarao = 0.0
                return False
            return True
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
                    p = fila.pop(0)
                    if p.get('mugetsu'):
                        _bytes(p)
                    else:                        # o corpo (a parte cara) fica pronto
                        q = dict(p, luz=0.0, brilho=None)
                        imagem_camada(q, 'corpo', chave_camadas(q)[0])
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
        self._t_seq = 0.0
        self._ev = _TOCANDO
        self._mostra_seq(0.0)
        self._ligar_relogio()

    def a_cada_desenho(self, fn):
        """fn(dt) roda a cada desenho do boneco (24/s), antes de desenhar;
        devolver False solta. Devolve algo com cancel()."""
        self._a_cada_desenho.append(fn)
        self._ligar_relogio()
        return _NoDesenho(self, fn)

    def _ligar_relogio(self):
        if self._ev_vida is None:
            self._ult = None
            self._grade = int(self._t * DESENHOS)
            self._ev_vida = Clock.schedule_interval(self._vida, 1 / 60.)

    def amassar(self, v, quadros=5):
        """Amassa (v < 0) ou estica (v > 0) o corpo por alguns quadros e volta
        em degraus, passando um pouco do ponto: pouso, arrancada, impacto."""
        try:
            ev = getattr(self, '_ev_amassa', None)
            if ev is not None:
                ev.cancel()
            passos = [1.0, 0.7, 0.3, -0.25, 0.0] if quadros >= 5 else [1.0, 0.4, 0.0]
            i = [0]

            def _p(dt):
                f = passos[min(i[0], len(passos) - 1)]
                self.escala_y = 1.0 + v * f
                self.escala_x = 1.0 - v * f * 0.6
                i[0] += 1
                if i[0] >= len(passos):
                    self.escala_x = self.escala_y = 1.0
                    self._ev_amassa = None
                    return False
            _p(0)
            self._ev_amassa = Clock.schedule_interval(_p, 1 / DESENHOS)     # no ritmo dos desenhos
        except Exception as e:
            print(f"[kirito] amassar: {e}")

    def pausar(self, seg):
        """Hit-stop: congela a animacao (e a fisica) por `seg` no instante do
        impacto - o golpe parece mais pesado."""
        self._pausa = max(self._pausa, float(seg))

    def _mostra_seq(self, dt):
        """Anda a sequencia (poses de 30/s) pelo TEMPO e mostra a pose do
        instante - chamado a cada desenho (24/s). Os quadros que passaram
        entre dois desenhos tambem sao avisados (as cenas marcam golpes e
        efeitos pelo numero do quadro)."""
        try:
            if self._ev is None or not self._seq:
                return
            seq = self._seq
            self._t_seq += dt
            n = len(seq)
            alvo = int(self._t_seq * FPS + 1e-6)
            if alvo >= n:
                if self._i < n:
                    alvo = n - 1                     # o ultimo aparece antes de acabar
                elif self._loop:
                    self._t_seq -= n / FPS
                    self._i = 0
                    alvo = min(n - 1, int(self._t_seq * FPS + 1e-6))
                else:
                    self._ev = None
                    cb, self._on_fim = self._on_fim, None
                    if cb:
                        cb()
                    return
            if alvo < self._i:
                return
            for j in range(self._i, alvo):           # quadros pulados: so o aviso
                if self._on_quadro:
                    self._on_quadro(j)
                if self._seq is not seq or self._ev is None:
                    return                           # o aviso trocou a sequencia
            self._i = alvo + 1
            self.mostrar(seq[alvo])
            if self._on_quadro:
                self._on_quadro(alvo)
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
        else:
            self._ligar_relogio()

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
            # respira de texel em texel (0, 1, 2 e volta): sem tranco
            q['dy'] = b['dy'] - round(1.0 - math.cos(t)) / float(R)
            atras = round(1.0 - math.cos(t - 0.6)) / float(R)   # maos vem depois
            if b['m1'] is not None:
                q['m1'] = (b['m1'][0], b['m1'][1] - atras)
            if b['m2'] is not None:
                q['m2'] = (b['m2'][0], b['m2'][1] - atras)
            if b['a1'] is not None:
                q['a1'] = b['a1'] + round(2.0 * math.sin(2 * t + 0.8))
            if b['a2'] is not None:
                q['a2'] = b['a2'] + round(2.0 * math.sin(2 * t + 2.0))
            if piscar and (70 <= f <= 72 or 104 <= f <= 105 or 108 <= f <= 109):
                q['olhos'] = 'f'
            quadros.append(q)
        self.tocar(quadros, loop=True)

    # ── afterimage ───────────────────────────────────────────────────
    def fantasma(self, cor=None, alfa=0.42, duracao=0.12):
        """Afterimage: a silhueta da pose atual em cor chapada, que some em
        3 degraus (sem pontilhado nem fade liso) - so uma indicacao de
        velocidade. Sem cor: ciano (roxo no Bankai)."""
        if cor is None:
            cor = (0.42, 0.18, 0.78) if self._base.get('mugetsu') else (0.0, 0.5, 0.82)
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
                if self._desenho is not None:
                    tex = quadro_clipe(self._desenho, self._quadro_atual(), silhueta=True)[0]
                    Rectangle(texture=tex, pos=self._rect.pos, size=self._rect.size,
                              tex_coords=_tc_espelhado(tex.tex_coords) if self.espelhar else tex.tex_coords)
                else:
                    for _r, _s, qual, ch, (ox, oy) in self._camadas_da_pose(self._pose):
                        tex, rec = textura_camada(self._pose, qual, ch, silhueta=True)
                        _no_retangulo(Rectangle(), tex, (rec[0] + ox, rec[1] + oy, rec[2], rec[3]),
                                      self.ps, self.espelhar, _PES * R if qual == 'cauda' else None)
                PopMatrix()
            idx = pai.children.index(self) + 1 if self in pai.children else 0
            pai.add_widget(g, index=idx)
            t = [0.0]

            def _some(dt):
                try:
                    t[0] += dt
                    k = min(1.0, t[0] / duracao)
                    cor_sil.a = alfa * (1.0 if k < 0.34 else (0.55 if k < 0.67 else 0.25))
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
          graus=16.0, lamina_recua=True, seg=None, duplo=True, meios=(0.34, 0.68)):
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
    ant['estica'] = -1                               # encolhe juntando forca
    if altura(arma) > 3:
        ant['dy'] = arma['dy'] - 1                   # e abaixa (se nao estiver agachado)
    imp = dict(corta, olhos=olhos[1], incl=1, vista='frente', estica=1)   # corta esticado, peso a frente
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
        seg['estica'] = 0
        seg['vista'] = 'lado'                        # volta de perfil na acomodacao
    else:
        seg = dict(seg, olhos=olhos[1], incl=1, vista='lado', estica=0)
    fim = dict(corta, olhos=olhos[2])
    chaves = [(n_arma, arma, 'suave'), (prende, ant, 'segura')]
    if duplo:                                         # meio do golpe: quadros de rastro
        for fr in meios:
            meio = misturar(ant, imp, fr, fr)
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


def bola(p):
    """Mortal: todo encolhido (joelhos no peito, bracos junto das pernas,
    cabeca para a frente) - a pose que gira de 90 em 90 graus no ar."""
    q = encolhido(p)
    q['m1'] = (3.0, -3.0)
    if q.get('m2') is not None:
        q['m2'] = (1.0, -3.5)
    q['incl'] = 1
    q['estica'] = -1
    q['lift'] = max(q.get('lift', 0.0), 0.8)
    return q


def esticado(p):
    """A mesma pose com as pernas esticadas (impulso do pulo / indo pousar)."""
    q = dict(p)
    q['pernas'] = 'suspenso'
    q['pernas_b'] = None
    q['dy'] = 0
    q['estica'] = 1                                  # o corpo todo estica no impulso
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
            # um Mesh aceita no maximo 65535 vertices (16383 quadradinhos)
            rs = pontos.get(nome, ())[:16000]
            vs = []
            ext = vs.extend
            for r in rs:
                x, y, w = r[0], r[1], r[2]
                h = r[3] if len(r) > 3 else w
                xw = x + w
                yh = y + h
                ext((x, y, 0, 0, xw, y, 0, 0, xw, yh, 0, 0, x, yh, 0, 0))
            mesh.vertices = vs
            mesh.indices = _indices_quads(len(rs))       # sempre os mesmos: lista pronta
            c.a = a0 * alfa


_IDS_QUADS = []


def _indices_quads(n):
    """Indices de n quadradinhos (0,1,2, 0,2,3, 4,5,6, ...): feitos uma vez so."""
    falta = n - len(_IDS_QUADS) // 6
    if falta > 0:
        b0 = len(_IDS_QUADS) // 6
        for i in range(b0, n):
            b = 4 * i
            _IDS_QUADS.extend((b, b + 1, b + 2, b, b + 2, b + 3))
    return _IDS_QUADS[:6 * n]


# ═══════════════════════════════════════════════════════════════════
#  FITA DE FOGO DO MUGETSU (como o vapor do Luffy no Gear 4)
#  Uma fita grossa de fogo roxo com azul da voltas em volta dele: um laco
#  em volta dos ombros e da cabeca e uma espiral que sobe dos pes ate o
#  peito. O que passa por tras fica atras dele, o que passa na frente fica
#  por cima. Miolo claro, corpo roxo (trechos azuis correndo pela fita),
#  borda escura, linguas de fogo subindo e brasas. 12 quadros prontos de
#  pixel art (gerados aos poucos, fora da hora da cena).
# ═══════════════════════════════════════════════════════════════════
_N_FITA = 12
_FITA_X0, _FITA_Y0, _FITA_W, _FITA_H = -70, -80, 140, 175     # caixa (texels, a partir do quadril)
_FITA_QUADROS = {}                                            # (quadro, 'tras'/'frente') -> idx bytes


def _caminhos_fita():
    """[(pontos [(x, y, prof, s)], largura base)] em texels a partir do
    quadril. prof > 0 = na frente dele."""
    out = []
    # laco em volta dos ombros e da cabeca (inclinado)
    pts = []
    n = 220
    for i in range(n + 1):
        t = 2 * math.pi * i / n
        x = 40.0 * math.cos(t)
        y = 58.0 + 14.0 * math.sin(t) + 6.0 * math.cos(t)
        pts.append((x, y, math.sin(t), i * 1.15))
    out.append((pts, 7.0))
    # espiral que sobe dos pes ate o peito (uma volta e meia)
    pts = []
    n = 300
    for i in range(n + 1):
        u = i / float(n)
        t = 2 * math.pi * 1.55 * u + 0.6
        r = 30.0 + 6.0 * u
        x = r * math.cos(t)
        y = -70.0 + 88.0 * u + 9.0 * math.sin(t)           # para no peito (nao passa no rosto)
        pts.append((x, y, math.sin(t), i * 1.1))
    out.append((pts, 6.0))
    return out


def _quadro_fita(f):
    """Um quadro da fita: {'tras': {(x,y): cor}, 'frente': {...}}"""
    fase = f / float(_N_FITA)
    camadas = {'tras': {}, 'frente': {}}
    for (pts, larg) in _caminhos_fita():
        for j in range(1, len(pts)):
            x0, y0, p0, s0 = pts[j - 1]
            x1, y1, p1, s1 = pts[j]
            tx, ty = x1 - x0, y1 - y0
            nrm = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / nrm, tx / nrm
            s = s0
            # largura que pulsa correndo pela fita
            w = larg * (0.72 + 0.38 * math.sin(s * 0.08 - fase * 2 * math.pi * 2)
                        + 0.2 * math.sin(s * 0.21 + fase * 2 * math.pi))
            alvo = camadas['frente' if p0 >= 0 else 'tras']
            azul = math.sin(s * 0.045 - fase * 2 * math.pi) > 0.45     # trechos azuis correndo
            passos = int((w + 2.0) * 2.6) + 1
            for k in range(passos + 1):
                d = -(w + 2.0) + 2 * (w + 2.0) * k / passos
                if abs(d) > w:                              # brilho em volta: pontilhado
                    x = int(math.floor(x0 + nx * d + 0.5))
                    y = int(math.floor(y0 + ny * d + 0.5))
                    if (x + y + f) % 2 == 0 and (x, y) not in alvo:
                        alvo[(x, y)] = '8'
                    continue
                x = int(math.floor(x0 + nx * d + 0.5))
                y = int(math.floor(y0 + ny * d + 0.5))
                a = abs(d) / max(0.5, w)
                if a < 0.28:
                    ch = '!' if (int(s) + f) % 5 == 0 else 'L'
                elif a < 0.62:
                    ch = 'f' if azul else 'V'
                elif a < 0.86:
                    ch = 'f' if (azul and a < 0.75) else 'o'
                else:
                    ch = '8'
                q = (x, y)
                if q not in alvo or a < 0.62:
                    alvo[q] = ch
            # lingua de fogo que sobe da borda de cima (de tempos em tempos)
            if int(s) % 5 == 0 and s1 - s0 > 0:
                alt = 3 + int(9 * (0.5 + 0.5 * math.sin(s * 0.7 + fase * 2 * math.pi * 3)))
                bx = int(round(x0 + (nx if ny > 0 else -nx) * w))
                by = int(round(y0 + abs(ny) * w))
                tomba = math.sin(fase * 2 * math.pi + s)
                for h in range(alt):
                    uu = h / float(max(1, alt - 1))
                    xx = bx + int(round(tomba * uu * 2))
                    for dx in range(-1 if uu < 0.5 else 0, 1 if uu < 0.3 else 0 + 1):
                        q = (xx + dx, by + h)
                        if q not in alvo:
                            alvo[q] = 'V' if uu < 0.4 else ('o' if uu < 0.8 else 'L')
    # brasas subindo
    rnd = random.Random(99)
    for i in range(70):
        bx = rnd.uniform(-46, 46)
        by0 = rnd.uniform(-70, 60)
        by = by0 + ((fase + rnd.random()) % 1.0) * 30
        q = (int(bx), int(by))
        (camadas['frente'] if rnd.random() < 0.5 else camadas['tras']).setdefault(q, 'L' if rnd.random() < 0.3 else 'o')
    return camadas


def _idx_fita(px):
    idx = bytearray(_FITA_W * _FITA_H)
    for (x, y), ch in px.items():
        xx, yy = x - _FITA_X0, y - _FITA_Y0
        if 0 <= xx < _FITA_W and 0 <= yy < _FITA_H:
            idx[yy * _FITA_W + xx] = _COD[ch]
    return bytes(idx)


_TEX_FITA = {}


carregar_assado()
if _GRAVA:
    import atexit
    atexit.register(salvar_gravados)
