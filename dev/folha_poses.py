"""Folha com as poses (POSE_A) do Yoru. uso: folha_poses.py SAIDA [nomes,separados] [z]"""
import sys, os
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito as K
saida = sys.argv[1]
nomes = (sys.argv[2].split(';') if ';' in sys.argv[2] else sys.argv[2].split(',')) if len(sys.argv) > 2 and sys.argv[2] else list(K.POSE_A)
z = int(sys.argv[3]) if len(sys.argv) > 3 else 2
BG = (31, 53, 80)
x0, x1, y0, y1 = 0, K.TW, 0, K.TH
cols = 8
todos = []
for n in nomes:
    p = K.POSE_A[n] if n in K.POSE_A else eval(n)
    todos.append((n[:18], K.montar(p)))
bx0 = min(min(x for x, y in px) for n, px in todos); bx1 = max(max(x for x, y in px) for n, px in todos) + 1
by0 = min(min(y for x, y in px) for n, px in todos); by1 = max(max(y for x, y in px) for n, px in todos) + 1
WW, HH = bx1 - bx0, by1 - by0
ims = []
for n, px in todos:
    im = Image.new('RGB', (WW, HH), BG)
    pix = im.load()
    for (x, y), c in px.items():
        r, g, b, a = K._PALETA[c]
        pix[x - bx0, by1 - 1 - y] = tuple(int(255 * (v * a) + bg * (1 - a)) for v, bg in zip((r, g, b), BG))
    ims.append((n, im))
w, h = WW * z, HH * z
linhas = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (cols * w, linhas * (h + 14)), (10, 10, 20)); d = ImageDraw.Draw(S)
for i, (n, im) in enumerate(ims):
    x, y = (i % cols) * w, (i // cols) * (h + 14)
    S.paste(im.resize((w, h), Image.NEAREST), (x, y + 14)); d.text((x + 2, y + 1), n, fill='yellow')
S.save(saida); print(S.size, len(ims), WW, HH)
