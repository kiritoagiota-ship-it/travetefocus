"""Reduz um pedaco da referencia para a grade do Yoru e mapeia nas cores da
paleta (o mais perto). uso: python reduz.py x0 y0 x1 y1 escala saida.png [cores]"""
import sys, os
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import numpy as np
import kirito as K

x0, y0, x1, y1 = (int(v) for v in sys.argv[1:5])
esc = float(sys.argv[5])
saida = sys.argv[6]
cores = sys.argv[7] if len(sys.argv) > 7 else 'JHIhUSstEe3mnNCcA2qGPBMKgkZO'
im = Image.open(r'refs/yoru_ref.jpg').convert('RGB').crop((x0, y0, x1, y1))
a = np.asarray(im).astype(float)
W, H = int(round((x1 - x0) / esc)), int(round((y1 - y0) / esc))
FUNDO = np.array([31, 53, 80], float)                 # azul do fundo da referencia
pal = {c: np.array(K._PALETA[c][:3]) * 255 for c in cores}
linhas = []
for r in range(H):
    l = ''
    for c in range(W):
        bx0, bx1 = int(c * esc), int((c + 1) * esc)
        by0, by1 = int(r * esc), int((r + 1) * esc)
        bloco = a[by0 + 1:max(by0 + 2, by1 - 1), bx0 + 1:max(bx0 + 2, bx1 - 1)].reshape(-1, 3)
        m = np.median(bloco, axis=0)
        if np.linalg.norm(m - FUNDO) < 28:
            l += '.'
            continue
        l += min(pal, key=lambda k: np.linalg.norm(pal[k] - m))
    linhas.append(l)
open(saida.replace('.png', '.txt'), 'w').write('\n'.join(linhas))
z = 12
S = Image.new('RGB', (W * z * 2 + 20, H * z), (20, 20, 30))
d = ImageDraw.Draw(S)
S.paste(im.resize((W * z, H * z), Image.NEAREST), (0, 0))
for r, l in enumerate(linhas):
    for c, ch in enumerate(l):
        if ch != '.':
            col = tuple(int(v) for v in pal[ch])
            d.rectangle([W * z + 20 + c * z, r * z, W * z + 20 + c * z + z - 1, r * z + z - 1], fill=col)
S.save(saida)
print(W, H)
for r, l in enumerate(linhas):
    print('%2d %s' % (r, l))
