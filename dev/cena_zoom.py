"""cena_zoom.py PASTA cena SAIDA [cols] [passo]: quadros de uma cena recortados em volta do que mexe."""
import sys, os, json
from PIL import Image, ImageChops, ImageDraw
pasta, cena, saida = sys.argv[1], sys.argv[2], sys.argv[3]
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 6
passo = int(sys.argv[5]) if len(sys.argv) > 5 else 1
L = json.load(open(os.path.join(pasta, 'log.json'), encoding='utf-8'))
qs = [q for q in L['quadros'] if q[1].split()[0] == cena][::passo]
ims = [(q[1], Image.open(os.path.join(pasta, q[2])).convert('RGB')) for q in qs]
ref = ims[0][1]
x0 = y0 = 10 ** 6; x1 = y1 = 0
for _, im in ims[1:]:
    bb = ImageChops.difference(im, ref).convert('L').point(lambda v: 255 if v > 40 else 0).getbbox()
    if bb:
        x0, y0, x1, y1 = min(x0, bb[0]), min(y0, bb[1]), max(x1, bb[2]), max(y1, bb[3])
m = 20
W, H = ref.size
x0, y0, x1, y1 = max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m)
cw, ch = x1 - x0, y1 - y0
esc = min(1.0, 330.0 / max(cw, ch))
tw, th = int(cw * esc), int(ch * esc)
lin = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (cols * tw, lin * (th + 12)), (40, 40, 40)); d = ImageDraw.Draw(S)
for k, (rot, im) in enumerate(ims):
    c = im.crop((x0, y0, x1, y1)).resize((tw, th), Image.LANCZOS)
    x, y = (k % cols) * tw, (k // cols) * (th + 12)
    S.paste(c, (x, y + 12)); d.text((x + 2, y), rot, fill='yellow')
S.save(saida); print(S.size, (x0, y0, x1, y1))
