"""Renderiza poses em texels (Kirito 2x) lado a lado.
uso: python ver2.py saida.png tam x0 x1 y0 y1 "ROTULO=base|chave=valor;..." ...
  x0..y1 em unidades da grade (sao multiplicados por 2); tam = px por texel."""
import sys, os
sys.path.insert(0, os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app'))
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito as K

saida, ps = sys.argv[1], int(sys.argv[2])
x0, x1, y0, y1 = (int(v) * K.R for v in sys.argv[3:7])
itens = sys.argv[7:]
W, H = (x1 - x0) * ps, (y1 - y0) * ps
S = Image.new('RGB', (W * len(itens), H + 16), (6, 6, 12)); d = ImageDraw.Draw(S)
for i, it in enumerate(itens):
    rot, resto = it.split('=', 1)
    base, _, kv = resto.partition('|')
    p = dict(K.POSE_A[base]) if base in K.POSE_A else K.pose()
    for par in filter(None, kv.split(';')):
        k, v = par.split('=', 1)
        p[k.strip()] = eval(v)
    px = K.montar(p); ox = i * W
    d.text((ox + 3, 2), rot, fill='yellow')
    for (x, y), c in px.items():
        if not (x0 <= x < x1 and y0 <= y < y1):
            continue
        r, g, b, a = K._PALETA[c]; bg = (6, 6, 12)
        col = tuple(int(255 * (v * a) + bgc * (1 - a)) for v, bgc in zip((r, g, b), bg))
        X = ox + (x - x0) * ps; Y = 16 + (y1 - 1 - y) * ps
        d.rectangle([X, Y, X + ps - 1, Y + ps - 1], fill=col)
S.save(saida); print(S.size)
