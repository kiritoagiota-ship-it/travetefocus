"""GIF de um trecho do filme.py (30 quadros/s, recortado em volta do Yoru).
uso: python dev/gif_filme.py PASTA ini_s fim_s SAIDA [escala=0.6] [margem=160] [x0,y0,x1,y1]"""
import sys
import os
import json
from PIL import Image

pasta, a, b, saida = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
esc = float(sys.argv[5]) if len(sys.argv) > 5 else 0.6
marg = int(sys.argv[6]) if len(sys.argv) > 6 else 160
rec = [int(v) for v in sys.argv[7].split(',')] if len(sys.argv) > 7 else None
L = json.load(open(os.path.join(pasta, 'filme.json'), encoding='utf-8'))
q0, q1 = int(a * 60), int(b * 60)
nomes = [q for q in range(q0, q1 + 1) if os.path.exists(os.path.join(pasta, f'f{q:05d}.png'))]
W, H = Image.open(os.path.join(pasta, f'f{nomes[0]:05d}.png')).size
if rec is None:
    xs, ys = [], []
    for rel, regs in L['quadros']:
        if q0 <= rel <= q1:
            for r in regs:
                if r['op'] > 0.05:
                    xs.append(r['x'])
                    ys.append(r['y'])
    x0, x1 = min(xs) - marg, max(xs) + marg
    y0, y1 = H - max(ys) - marg * 1.5, H - min(ys) + marg * 0.6
    rec = [int(max(0, x0)), int(max(0, y0)), int(min(W, x1)), int(min(H, y1))]
ims = []
for q in nomes:
    im = Image.open(os.path.join(pasta, f'f{q:05d}.png')).convert('RGB').crop(rec)
    im = im.resize((int(im.width * esc), int(im.height * esc)), Image.NEAREST)
    ims.append(im.quantize(colors=128, method=Image.Quantize.MEDIANCUT))
passo = (nomes[1] - nomes[0]) if len(nomes) > 1 else 2
dur = int(round(1000 * passo / 60.0))
ims[0].save(saida, save_all=True, append_images=ims[1:], duration=[dur] * (len(ims) - 1) + [1200],
            loop=0, optimize=True)
print(saida, len(ims), 'quadros', os.path.getsize(saida) // 1024, 'KB', rec)
