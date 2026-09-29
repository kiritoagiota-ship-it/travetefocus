"""Folha de contato: folha.py PASTA PREFIXO SAIDA [colunas] [escala] [recorte x0,y0,x1,y1 (fração)]"""
import sys, os, json
from PIL import Image, ImageDraw
pasta, prefixo, saida = sys.argv[1], sys.argv[2], sys.argv[3]
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 6
esc = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
rec = [float(v) for v in sys.argv[6].split(',')] if len(sys.argv) > 6 else None
L = json.load(open(os.path.join(pasta, os.environ.get('LOG', 'log.json')), encoding='utf-8'))
qs = [q for q in L['quadros'] if q[1].startswith(prefixo)]
passo = int(os.environ.get('PASSO', 1))
qs = qs[::passo]
ims = []
for t, rot, arq in qs:
    im = Image.open(os.path.join(pasta, arq)).convert('RGB')
    if rec:
        W, H = im.size
        im = im.crop((int(rec[0] * W), int(rec[1] * H), int(rec[2] * W), int(rec[3] * H)))
    im = im.resize((max(1, int(im.size[0] * esc)), max(1, int(im.size[1] * esc))), Image.NEAREST if esc >= 1 else Image.LANCZOS)
    ims.append((f'{t:.2f} {rot}', im))
if not ims:
    print('nada'); sys.exit()
w, h = ims[0][1].size
linhas = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (cols * w, linhas * (h + 14)), (30, 30, 30)); d = ImageDraw.Draw(S)
for i, (r, im) in enumerate(ims):
    x, y = (i % cols) * w, (i // cols) * (h + 14)
    S.paste(im, (x, y + 14)); d.text((x + 2, y + 1), r, fill='yellow')
S.save(saida); print(S.size, len(ims))
