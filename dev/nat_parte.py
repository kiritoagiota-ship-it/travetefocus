"""Pedaco da referencia (grade nativa) -> mapa com as cores do casaco/corpo.
uso: python nat_parte.py c0 r0 c1 r1 saida.txt [img]"""
import os, sys
from PIL import Image
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paleta5 import P5
AQUI = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.join(AQUI, 'dados')
c0, r0, c1, r1 = (int(v) for v in sys.argv[1:5])
img = sys.argv[6] if len(sys.argv) > 6 else 'ref_nativo1.png'
nat = np.asarray(Image.open(os.path.join(R1, img)).convert('RGB')).astype(float)[r0:r1, c0:c1]
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
ESCUROS = 'N2CAcGk+'
PELE = 'SstT'
CIANO = 'OZ09'
AZUL = 'qal'
OURO = '$@*'


def perto(rgb, chars):
    return min(chars, key=lambda k: sum((a - b) ** 2 for a, b in zip(P5[k], rgb)))


m = []
for y in range(H):
    l = ''
    for x in range(W):
        rgb = nat[y, x]
        r, g, b = rgb
        if np.linalg.norm(rgb - FUNDO) < 18 or (_MASC is not None and _MASC[y, x]):
            l += '.'
        elif r > 120 and r > b + 20 and g < r - 25:
            l += perto(rgb, PELE)
        elif r > 110 and g > 80 and b < 90 and r > b + 40:
            l += perto(rgb, OURO)
        elif b > 150 and g > 120 and g > r + 40:
            l += perto(rgb, CIANO)
        elif b > r + 35 and b > 60:
            l += perto(rgb, AZUL + CIANO)
        else:
            l += perto(rgb, ESCUROS)
    m.append(l)
open(os.path.join(R1, sys.argv[5]), 'w').write('\n'.join(m) + '\n')
print(W, H)
