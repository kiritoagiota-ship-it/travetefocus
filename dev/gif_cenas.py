"""GIF com varias cenas curtas em sequencia, cada uma recortada em volta do Yoru."""
import sys, os, json
from PIL import Image, ImageChops, ImageDraw
pasta, saida = sys.argv[1], sys.argv[2]
cenas = sys.argv[3].split(',')
titulos = dict(t.split('=') for t in sys.argv[4].split(';')) if len(sys.argv) > 4 else {}
L = json.load(open(os.path.join(pasta, 'log.json'), encoding='utf-8'))
LW, LH = 400, 330
quadros, durs = [], []
for cena in cenas:
    qs = [q for q in L['quadros'] if q[1].split()[0] == cena]
    ims = [Image.open(os.path.join(pasta, q[2])).convert('RGB') for q in qs]
    ref = ims[0]
    x0 = y0 = 10 ** 6; x1 = y1 = 0
    for im in ims[1:]:
        bb = ImageChops.difference(im, ref).convert('L').point(lambda v: 255 if v > 40 else 0).getbbox()
        if bb and bb[2] - bb[0] < 260 and bb[3] - bb[1] < 300:     # so o Yoru (sem explosoes)
            x0, y0, x1, y1 = min(x0, bb[0]), min(y0, bb[1]), max(x1, bb[2]), max(y1, bb[3])
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + 10
    w = max(x1 - x0 + 60, (y1 - y0 + 60) * LW / LH, 250)
    h = w * LH / LW
    W, H = ref.size
    bx0 = max(0, min(W - w, cx - w / 2)); by0 = max(0, min(H - h, cy - h / 2))
    for k, im in enumerate(ims):
        c = im.crop((int(bx0), int(by0), int(bx0 + w), int(by0 + h))).resize((LW, LH), Image.LANCZOS)
        d = ImageDraw.Draw(c)
        d.rectangle((0, 0, LW, 18), fill=(0, 0, 0))
        d.text((6, 3), titulos.get(cena, cena), fill=(255, 220, 90))
        quadros.append(c.quantize(colors=96, method=Image.Quantize.MEDIANCUT))
        durs.append(50)
    durs[-1] = 600
quadros[0].save(saida, save_all=True, append_images=quadros[1:], duration=durs, loop=0, optimize=True)
print(saida, len(quadros), os.path.getsize(saida) // 1024, 'KB')
