"""Referencia -> mapa na grade nova, classificando cada pixel por tipo
(fundo, cabelo, pele, olho, contorno ciano) e depois tirando o ruido.
uso: python quant2.py x0 y0 x1 y1 escala saida.txt [previa.png]"""
import sys, os
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import numpy as np
import kirito as K
x0, y0, x1, y1 = (int(v) for v in sys.argv[1:5])
esc = float(sys.argv[5])
ref = Image.open('refs/yoru_ref.jpg').convert('RGB').crop((x0, y0, x1, y1))
w, h = round((x1 - x0) / esc), round((y1 - y0) / esc)
p = np.asarray(ref.resize((w, h), Image.BOX)).astype(float)
FUNDO = np.array([31, 53, 80.])


def classe(r, g, b):
    L = 0.3 * r + 0.59 * g + 0.11 * b
    if np.linalg.norm(np.array([r, g, b]) - FUNDO) < 26:
        return '.'
    if b > 140 and g > 90 and r < 120 and b > r + 60:
        return 'O'                                    # contorno ciano
    if r > 140 and r > b + 25 and g > b - 10:
        if L > 205:
            return 'S'
        if L > 160:
            return 's'
        return 't'
    if L > 185 and b >= r - 10:
        return 'n'
    if b > r + 45 and L > 55:
        return 'm' if L > 105 else '3'
    if L < 24:
        return 'J'
    if L < 46:
        return 'H'
    if L < 88:
        return 'I'
    if L < 140:
        return 'h'
    return 'U'


lab = [[classe(*p[r, c]) for c in range(w)] for r in range(h)]
# ciano longe do fundo nao e contorno: e iris (azul do olho)
for r in range(h):
    for c in range(w):
        if lab[r][c] == 'O':
            perto = any(lab[r + a][c + b] == '.' for a in range(-2, 3) for b in range(-2, 3)
                        if 0 <= r + a < h and 0 <= c + b < w)
            if not perto:
                lab[r][c] = 'm' if 0.3 * p[r, c][0] + 0.59 * p[r, c][1] + 0.11 * p[r, c][2] > 120 else '3'
# tira o ruido: um texel sozinho (nenhum vizinho igual) vira o mais comum em volta
for _ in range(2):
    novo = [l[:] for l in lab]
    for r in range(h):
        for c in range(w):
            viz = [lab[r + a][c + b] for a in (-1, 0, 1) for b in (-1, 0, 1)
                   if (a or b) and 0 <= r + a < h and 0 <= c + b < w]
            if lab[r][c] not in viz:
                novo[r][c] = max(set(viz), key=viz.count)
    lab = novo
linhas = [''.join(l) for l in lab]
open(sys.argv[6], 'w').write('\n'.join(linhas) + '\n')
if len(sys.argv) > 7:
    z = 10
    S = Image.new('RGB', (w * z * 2 + 10, h * z), (20, 22, 32))
    S.paste(ref.resize((w * z, h * z), Image.NEAREST), (0, 0))
    d = ImageDraw.Draw(S)
    for r, l in enumerate(linhas):
        for c, ch in enumerate(l):
            if ch != '.':
                col = tuple(int(v * 255) for v in K._PALETA[ch][:3])
                d.rectangle([w * z + 10 + c * z, r * z, w * z + 10 + c * z + z - 1, r * z + z - 1], fill=col)
    S.save(sys.argv[7])
print(w, h)
