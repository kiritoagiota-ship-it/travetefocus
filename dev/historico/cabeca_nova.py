"""Cabeca nova do Yoru (grade fina, R=5): cabelo tirado da referencia e
limpo, rosto desenhado a mao por cima. Gera o mapa (texto) e previas.
uso: python cabeca_nova.py"""
import os, sys
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito as K

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(AQUI, '..', 'r1', 'cab_q2.txt')
W, H = 50, 53                      # colunas 0-49, linhas 0-52 (queixo na 51)

auto = open(BASE).read().split()
m = [list((l + '.' * 60)[:W]) for l in auto[:H]]
CAB = set('JHIhU')


def viz(r, c):
    return [m[r + a][c + b] for a in (-1, 0, 1) for b in (-1, 0, 1)
            if (a or b) and 0 <= r + a < H and 0 <= c + b < W]


# 1) cabelo: tons em blocos (sem pontinho solto), 2 passadas
for _ in range(2):
    novo = [l[:] for l in m]
    for r in range(H):
        for c in range(W):
            if m[r][c] in CAB:
                v = [x for x in viz(r, c) if x in CAB]
                if v and v.count(m[r][c]) <= 1:
                    novo[r][c] = max(set(v), key=v.count)
    m = novo

# 2) rosto a mao: colunas 12-44, linhas 32-52 (None = deixa o que esta)
ROSTO = {
    32: (12, "JJJHHHHHHHHHHHHHHHHHHHHttJJHHHHHH"),
    33: (12, "JJJHHHHHHHHHHHHHHHHHHHtstJJHHHHHH"),
    34: (12, "JJJJHHHHHHHHHHHHHHHtssstsJJHHHHHJ"),
    35: (12, "JJJJJHHHHHHHHHHHHHtsSSSstJJJHHHJ."),
    36: (12, "JJJJJJHHHHHHHHHHHHtsSSSSsEEJJHJ.."),
    37: (12, "JJJJJJJHHHHHHHtsHHssSSEEEEEEEEEJ."),
    38: (12, "JJJJJJJHHJJttssSsSSSSEnneeeeeEsSJ"),
    39: (12, "JJJJJJHHJtstSsSSSSSSSinneEee3sSSJ"),
    40: (12, "JJJJJJHJtsSSstSSSSSSSii33ee33sSSJ"),
    41: (12, "JJJJJJJtsSSSSstSSSSSSSi3mmm3sSSSJ"),
    42: (12, "JJJJJJJtsSttSstSSSSSSSSsmmmsSSSSJ"),
    43: (12, "JJJJJJJtsSStSstSSSSSSSSSsssSSSSS."),
    44: (12, "JJJJJJJtssSSsstSSSSSSSSSSSSSSSSS."),
    45: (12, "JJJJJJJJtssstsSSSSSSSSSSSSSSSSSs."),
    46: (12, "JJJJJJJJJtttssSSSSSSSSSSSSSSSSSs."),
    47: (12, "JJJJJJJJJtssSSSSSSSSSSSSSSSSSss.."),
    48: (12, "JJJJJJJJJtsSSSSSSSSSSSSSSSStsSs.."),
    49: (12, "JJJJJJJJJtssSSSSSSSSSSSSSSSSSs..."),
    50: (12, "JJJJJJJJJttssSSSSSSSSSSSSSSSs...."),
    51: (12, "JJJJJJJJJJtssssSSSSSSSSSSSss....."),
    52: (12, "JJJJJJJJJJJtttssssssssssss......."),
}
for r, (c0, txt) in ROSTO.items():
    for i, ch in enumerate(txt):
        if c0 + i < W:
            m[r][c0 + i] = ch
# a direita do rosto (colunas 45+) nas linhas do rosto: fundo
for r in range(38, H):
    for c in range(45, W):
        if m[r][c] not in CAB:
            m[r][c] = '.'
# o que sobrou de pele/olho fora do rosto vira cabelo; ciano solto some
for r in range(H):
    for c in range(W):
        ch = m[r][c]
        if ch in 'Ssteimn3E' and r < 32:
            m[r][c] = 'H'
        if ch == 'O':
            m[r][c] = 'O'

MAPA = [''.join(l) for l in m]
open(os.path.join(AQUI, '..', 'r1', 'cab_nova.txt'), 'w').write('\n'.join(MAPA) + '\n')


def desenha(mapa, z, fundo=(31, 53, 80)):
    im = Image.new('RGB', (len(mapa[0]) * z, len(mapa) * z), fundo)
    d = ImageDraw.Draw(im)
    for r, l in enumerate(mapa):
        for c, ch in enumerate(l):
            if ch != '.':
                col = tuple(int(v * 255) for v in K._PALETA[ch][:3])
                d.rectangle([c * z, r * z, c * z + z - 1, r * z + z - 1], fill=col)
    return im


if __name__ == '__main__':
    ref = Image.open(os.path.join(AQUI, '..', 'refs', 'yoru_ref.jpg')).convert('RGB')
    rc = ref.crop((160, 40, 160 + int(W * 2.44), 40 + int(H * 2.44))).resize((W * 10, H * 10), Image.NEAREST)
    a = desenha(MAPA, 10)
    S = Image.new('RGB', (W * 20 + 10, H * 10), (20, 20, 30))
    S.paste(rc, (0, 0))
    S.paste(a, (W * 10 + 10, 0))
    S.save(os.path.join(AQUI, '..', 'r1', 'cab_nova.png'))
    print('\n'.join('%2d %s' % (r, l) for r, l in enumerate(MAPA)))
