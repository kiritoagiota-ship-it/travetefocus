"""Folha de quadros do filme.py num trecho, recortada em volta do Yoru
(recorte fixo no trecho, para ver o movimento de verdade).
uso: python dev/folha_filme.py PASTA ini_s fim_s passo_quadros SAIDA [colunas] [zoom] [margem_px]"""
import sys
import os
import json
from PIL import Image, ImageDraw

pasta, a, b, passo, saida = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
cols = int(sys.argv[6]) if len(sys.argv) > 6 else 6
zoom = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
marg = int(sys.argv[8]) if len(sys.argv) > 8 else 150
L = json.load(open(os.path.join(pasta, 'filme.json'), encoding='utf-8'))
q0, q1 = int(a * 60), int(b * 60)
xs, ys = [], []
for rel, regs in L['quadros']:
    if q0 <= rel <= q1:
        for r in regs:
            if r['op'] > 0.05:
                xs.append(r['x'])
                ys.append(r['y'])
nomes = [f'f{q:05d}.png' for q in range(q0, q1 + 1) if os.path.exists(os.path.join(pasta, f'f{q:05d}.png'))]
nomes = nomes[::max(1, passo // 2)] if passo > 1 else nomes
W, H = Image.open(os.path.join(pasta, nomes[0])).size
if xs:
    x0, x1 = min(xs) - marg, max(xs) + marg
    y0, y1 = H - max(ys) - marg * 1.5, H - min(ys) + marg * 0.6
else:
    x0, y0, x1, y1 = 0, 0, W, H
x0, y0, x1, y1 = int(max(0, x0)), int(max(0, y0)), int(min(W, x1)), int(min(H, y1))
tw, th = int((x1 - x0) * zoom), int((y1 - y0) * zoom)
lin = (len(nomes) + cols - 1) // cols
S = Image.new('RGB', (cols * (tw + 4), lin * (th + 14)), (50, 50, 50))
d = ImageDraw.Draw(S)
for k, n in enumerate(nomes):
    im = Image.open(os.path.join(pasta, n)).crop((x0, y0, x1, y1))
    if zoom != 1.0:
        im = im.resize((tw, th), Image.NEAREST)
    x, y = (k % cols) * (tw + 4), (k // cols) * (th + 14)
    S.paste(im, (x, y + 14))
    q = int(n[1:6])
    d.text((x + 2, y + 1), f'{q / 60.0:.2f}s q{q}', fill='yellow')
S.save(saida)
print(saida, S.size, (x0, y0, x1, y1), len(nomes), 'quadros')
