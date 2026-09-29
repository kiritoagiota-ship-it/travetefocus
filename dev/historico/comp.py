"""Antes x depois (kirito da HEAD x o do repo), mesma pose, lado a lado.
uso: python comp.py saida.png tam x0 x1 y0 y1 "ROTULO=base|k=v;..." ..."""
import sys, os
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app'))
sys.path.insert(0, os.path.join(AQUI, '..', 'velho'))
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito as K
import kirito_velho as KV

saida, ps = sys.argv[1], int(sys.argv[2])
x0, x1, y0, y1 = (int(v) * K.R for v in sys.argv[3:7])
itens = sys.argv[7:]
W, H = (x1 - x0) * ps, (y1 - y0) * ps
S = Image.new('RGB', (W * len(itens) * 2, H + 16), (6, 6, 12)); d = ImageDraw.Draw(S)
BG = (6, 6, 12)
for i, it in enumerate(itens):
    rot, resto = it.split('=', 1)
    base, _, kv = resto.partition('|')
    for j, M in enumerate((KV, K)):
        p = dict(M.POSE_A[base]) if base in M.POSE_A else M.pose()
        for par in filter(None, kv.split(';')):
            k, v = par.split('=', 1)
            p[k.strip()] = eval(v)
        px = M.montar(p); ox = (2 * i + j) * W
        d.text((ox + 3, 2), rot + (' ANTES' if j == 0 else ' DEPOIS'), fill='yellow')
        for (x, y), c in px.items():
            if not (x0 <= x < x1 and y0 <= y < y1):
                continue
            r, g, b, a = M._PALETA[c]
            col = tuple(int(255 * (v * a) + bgc * (1 - a)) for v, bgc in zip((r, g, b), BG))
            X = ox + (x - x0) * ps; Y = 16 + (y1 - 1 - y) * ps
            d.rectangle([X, Y, X + ps - 1, Y + ps - 1], fill=col)
S.save(saida); print(S.size)
