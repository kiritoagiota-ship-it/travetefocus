"""Desenha so as partes do sobretudo (sem o resto) para ver o formato."""
import sys, os
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito as K
esc = 10
casos = [('repouso', 0, 0, 0.0, 1.0), ('fase .5', 0, 0, 0.5, 1.0), ('vento', 1.6, 0, 0.3, 1.0), ('queda', 0.3, 2.0, 0.6, 1.0)]
ims = []
for nome, capa, lift, fase, saia in casos:
    px = {}
    base, y0 = K._X0, K._PES + 11.2 - 1
    K._casaco4(px, base, y0, capa, lift, fase, saia, 'tras')
    tras = dict(px)
    K._casaco4(px, base, y0, capa, lift, fase, saia, 'frente')
    x0, x1, y0t, y1 = 30, 130, 36, 80
    im = Image.new('RGB', ((x1 - x0) * esc, (y1 - y0t) * esc + 14), (60, 60, 70))
    d = ImageDraw.Draw(im)
    for (x, y), c in px.items():
        if x0 <= x < x1 and y0t <= y < y1:
            r, g, b, a = K._PALETA[c]
            X, Y = (x - x0) * esc, 14 + (y1 - 1 - y) * esc
            d.rectangle([X, Y, X + esc - 1, Y + esc - 1], fill=(int(r * 255), int(g * 255), int(b * 255)))
    d.text((3, 1), nome, fill='yellow')
    ims.append(im)
W, H = ims[0].size
S = Image.new('RGB', (W * 2, H * 2))
for i, im in enumerate(ims):
    S.paste(im, ((i % 2) * W, (i // 2) * H))
S.save(sys.argv[1]); print(S.size)
