"""folha2.py PASTA ini fim SAIDA [cols] [esc] [recorte]: quadros qNNNN de ini a fim."""
import sys, os
from PIL import Image, ImageDraw
pasta, a, b, saida = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
cols = int(sys.argv[5]) if len(sys.argv) > 5 else 8
esc = float(sys.argv[6]) if len(sys.argv) > 6 else 0.33
rec = [float(v) for v in sys.argv[7].split(',')] if len(sys.argv) > 7 else None
ims = []
for i in range(a, b + 1):
    f = os.path.join(pasta, 'q%04d.png' % i)
    if not os.path.exists(f):
        continue
    im = Image.open(f).convert('RGB')
    if rec:
        W, H = im.size
        im = im.crop((int(rec[0] * W), int(rec[1] * H), int(rec[2] * W), int(rec[3] * H)))
    im = im.resize((int(im.width * esc), int(im.height * esc)), Image.LANCZOS)
    ims.append((str(i), im))
w, h = ims[0][1].size
lin = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (cols * w, lin * (h + 12)), (40, 40, 40)); d = ImageDraw.Draw(S)
for k, (r, im) in enumerate(ims):
    x, y = (k % cols) * w, (k // cols) * (h + 12)
    S.paste(im, (x, y + 12)); d.text((x + 2, y), r, fill='yellow')
S.save(saida); print(S.size)
