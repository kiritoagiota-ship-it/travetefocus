"""Cabeca nova a partir dos pixels originais da referencia (grade nativa):
cada pixel vai para a cor mais perto do grupo certo (cabelo, pele, olho,
contorno ciano). Gera r1/cabN.txt e a previa r1/cabN.png.
uso: python nat_cab.py c0 r0 c1 r1"""
import os, sys
from PIL import Image, ImageDraw
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paleta5 import P5

AQUI = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.join(AQUI, 'dados')
c0, r0, c1, r1 = (int(v) for v in sys.argv[1:5])
nat = np.asarray(Image.open(os.path.join(R1, os.environ.get('NATIVO', 'ref_nativo1.png'))).convert('RGB')).astype(float)[r0:r1, c0:c1]
H, W = nat.shape[:2]
import os as _os2
if _os2.environ.get('FUNDO_FLOOD') == '1':
    import sys as _s2
    _s2.path.insert(0, _os2.path.dirname(_os2.path.abspath(__file__)))
    import fundo_flood as _ff
    _NATALL = np.asarray(Image.open(os.path.join(R1, os.environ.get('NATIVO', 'ref_nativo1.png'))).convert('RGB')).astype(float)
    _MASC = _ff.mascara(_NATALL)[r0:r1, c0:c1]
else:
    _MASC = None
FUNDO = np.array([31, 53, 80.])
GRUPOS = {
    'cabelo': 'NJHIhU',
    'pele': 'SstT',
    'olho': 'Ee3mni',
    'ciano': 'O0',
}


def perto(rgb, chars):
    return min(chars, key=lambda k: sum((a - b) ** 2 for a, b in zip(P5[k], rgb)))


def grupo(rgb):
    r, g, b = rgb
    L = 0.3 * r + 0.59 * g + 0.11 * b
    if np.linalg.norm(rgb - FUNDO) < 20:
        return None
    if r > 120 and r > b + 20:
        return 'pele'
    if b > 150 and g > 120 and r < 150 and b > r + 50 and g > r + 40:
        return 'ciano'
    if b > r + 30 and L > 45:
        return 'azul'
    if L > 170:
        return 'claro'
    return 'cabelo'


m = [['.'] * W for _ in range(H)]
for y in range(H):
    for x in range(W):
        if _MASC is not None and _MASC[y, x]:
            continue
        g = grupo(nat[y, x])
        if g is None:
            continue
        rgb = nat[y, x]
        if g == 'azul' and abs(rgb[0] - rgb[1]) < 25 and rgb[2] < rgb[0] + 70:
            g = 'cabelo'                     # brilho lilas do cabelo, nao contorno
        if g == 'azul':
            # azul perto de pele = iris; senao contorno escuro de luz
            viz = [grupo(nat[yy, xx]) for yy in range(max(0, y - 3), min(H, y + 4))
                   for xx in range(max(0, x - 3), min(W, x + 4))]
            m[y][x] = perto(rgb, GRUPOS['olho'] if 'pele' in viz else GRUPOS['ciano'])
        elif g == 'claro':
            viz = [grupo(nat[yy, xx]) for yy in range(max(0, y - 3), min(H, y + 4))
                   for xx in range(max(0, x - 3), min(W, x + 4))]
            m[y][x] = 'n' if 'pele' in viz else 'U'
        else:
            m[y][x] = perto(rgb, GRUPOS[g])
linhas = [''.join(l) for l in m]
open(os.path.join(R1, os.environ.get('SAIDA_CAB', 'cabN.txt')), 'w').write('\n'.join(linhas) + '\n')


def desenha(mapa, z, fundo=(31, 53, 80)):
    im = Image.new('RGB', (len(mapa[0]) * z, len(mapa) * z), fundo)
    d = ImageDraw.Draw(im)
    for r, l in enumerate(mapa):
        for c, ch in enumerate(l):
            if ch != '.':
                d.rectangle([c * z, r * z, c * z + z - 1, r * z + z - 1], fill=P5[ch])
    return im


z = 10
ref = Image.fromarray(nat.astype('uint8')).resize((W * z, H * z), Image.NEAREST)
S = Image.new('RGB', (W * z * 2 + 10, H * z), (0, 0, 0))
S.paste(ref, (0, 0))
S.paste(desenha(linhas, z), (W * z + 10, 0))
S.save(os.path.join(R1, os.environ.get('SAIDA_CAB', 'cabN.txt').replace('.txt', '.png')))
print(W, H)
