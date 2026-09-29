import sys; sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
import os; os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito
itens = [x.split(':') for x in sys.argv[2].split(',')]      # nome:capa:fase
ps = int(sys.argv[3]) if len(sys.argv) > 3 else 10
x0, x1, y0, y1 = int(os.environ.get("X0", 8)), int(os.environ.get("X1", 58)), int(os.environ.get("Y0", 6)), int(os.environ.get("Y1", 52))
W, H = (x1 - x0) * ps, (y1 - y0) * ps
S = Image.new('RGB', (W * len(itens), H + 16), (6, 6, 12)); d = ImageDraw.Draw(S)
for i, it in enumerate(itens):
    n = it[0]; p = dict(kirito.POSE_A[n])
    if len(it) > 1: p['capa'] += float(it[1]); p['cabelo'] += float(it[1])
    if len(it) > 2: p['fase'] = float(it[2])
    if len(it) > 3: p['lift'] += float(it[3])
    px = kirito.montar(p); ox = i * W
    d.text((ox + 3, 2), '/'.join(it), fill='yellow')
    for (x, y), c in px.items():
        if not (x0 <= x < x1 and y0 <= y < y1): continue
        r, g, b, a = kirito._PALETA[c]; bg = (6, 6, 12)
        col = tuple(int(255 * (v * a) + bgc * (1 - a)) for v, bgc in zip((r, g, b), bg))
        X = ox + (x - x0) * ps; Y = 16 + (y1 - 1 - y) * ps
        d.rectangle([X, Y, X + ps - 1, Y + ps - 1], fill=col)
S.save(sys.argv[1]); print(S.size)
