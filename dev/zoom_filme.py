"""Tira de quadros do filme.py ampliados (pixel duro) em volta do Yoru.
uso: python dev/zoom_filme.py PASTA SAIDA q1,q2,... [larg=300] [alt=300] [zoom=2] [sobe=0.7] [dx=0]
(q = quadro a 60/s contado do comeco da cena; so existem os que o filme gravou)"""
import sys
import os
import json
from PIL import Image, ImageDraw

pasta, saida = sys.argv[1], sys.argv[2]
qs = [int(v) for v in sys.argv[3].split(',')]
w = int(sys.argv[4]) if len(sys.argv) > 4 else 300
h = int(sys.argv[5]) if len(sys.argv) > 5 else 300
zoom = float(sys.argv[6]) if len(sys.argv) > 6 else 2
sobe = float(sys.argv[7]) if len(sys.argv) > 7 else 0.7
dx = int(sys.argv[8]) if len(sys.argv) > 8 else 0
L = json.load(open(os.path.join(pasta, 'filme.json'), encoding='utf-8'))
Q = {rel: regs for rel, regs in L['quadros']}
ims = []
for q in qs:
    im = Image.open(os.path.join(pasta, f'f{q:05d}.png'))
    H = im.size[1]
    vis = [r for r in Q.get(q, []) if r['op'] > 0.05]
    cx, cy = (vis[0]['x'], H - vis[0]['y']) if vis else (im.size[0] / 2, H / 2)
    cx += dx
    c = im.crop((int(cx - w / 2), int(cy - h * sobe), int(cx + w / 2), int(cy + h * (1 - sobe))))
    c = c.resize((int(w * zoom), int(h * zoom)), Image.NEAREST)
    ImageDraw.Draw(c).text((4, 2), f'{q / 60.0:.2f}s q{q}', fill='yellow')
    ims.append(c)
S = Image.new('RGB', (sum(i.width for i in ims) + 6 * (len(ims) - 1), ims[0].height), (60, 60, 60))
x = 0
for i in ims:
    S.paste(i, (x, 0))
    x += i.width + 6
S.save(saida)
print(saida, S.size)
