import sys, os
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito as K
nomes = sys.argv[2].split(',')
BG = (31, 53, 80)
ims = []
for n in nomes:
    p = K.POSE_A[n]
    px = K.montar(p)
    x0 = min(x for x, y in px) - 10; x1 = max(x for x, y in px) + 10
    y0 = min(y for x, y in px) - 10; y1 = max(y for x, y in px) + 10
    for q in (1, 2):
        for (x, y) in K.maos_texel(p, q):
            x0 = min(x0, int(x) - 5); x1 = max(x1, int(x) + 5); y0 = min(y0, int(y) - 5); y1 = max(y1, int(y) + 5)
    im = Image.new('RGB', (x1 - x0, y1 - y0), BG); pix = im.load()
    for (x, y), c in px.items():
        r, g, b, a = K._PALETA[c]
        pix[x - x0, y1 - 1 - y] = tuple(int(255 * (v * a) + bg * (1 - a)) for v, bg in zip((r, g, b), BG))
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for q, cor in ((1, (255, 60, 60)), (2, (255, 230, 0))):
        (mx, my), (tx, ty) = K.maos_texel(p, q)
        for (x, y), rr in (((mx, my), 3), ((tx, ty), 5)):
            X, Y = (x - x0) * 2, (y1 - 1 - y) * 2
            d.ellipse((X - rr, Y - rr, X + rr, Y + rr), outline=cor, width=2)
    d.text((2, 2), n, fill='yellow')
    ims.append(im)
W = sum(i.width for i in ims); H = max(i.height for i in ims)
S = Image.new('RGB', (W, H), (0, 0, 0)); x = 0
for i in ims:
    S.paste(i, (x, 0)); x += i.width
S.save(sys.argv[1]); print(S.size)
