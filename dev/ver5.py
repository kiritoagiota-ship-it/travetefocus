"""Yoru novo (grade fina) ao lado da referencia nativa, mesma escala.
uso: python ver5.py saida.png z "ROT=base|k=v;..." ..."""
import sys, os
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito as K
AQUI = os.path.dirname(os.path.abspath(__file__))
saida, z = sys.argv[1], int(sys.argv[2])
BG = (31, 53, 80)
x0, x1, y0, y1 = 10 * K.R, 58 * K.R, 11 * K.R, 50 * K.R
W, H = (x1 - x0), (y1 - y0)
ref = Image.open(os.path.join(AQUI, 'dados', 'ref_nativo1.png')).convert('RGB')
paineis = [ref]
for it in sys.argv[3:]:
    rot, resto = it.split('=', 1)
    base, _, kv = resto.partition('|')
    p = dict(K.POSE_A[base])
    for par in filter(None, kv.split(';')):
        k, v = par.split('=', 1)
        p[k.strip()] = eval(v)
    px = K.montar(p)
    im = Image.new('RGB', (W, H), BG)
    pix = im.load()
    for (x, y), c in px.items():
        if x0 <= x < x1 and y0 <= y < y1:
            r, g, b, a = K._PALETA[c]
            pix[x - x0, y1 - 1 - y] = tuple(int(255 * (v * a) + bg * (1 - a)) for v, bg in zip((r, g, b), BG))
    paineis.append(im)
Hm = max(p.height for p in paineis)
S = Image.new('RGB', (sum(p.width for p in paineis) * z + 10 * len(paineis), Hm * z), (10, 10, 20))
ox = 0
for pn in paineis:
    S.paste(pn.resize((pn.width * z, pn.height * z), Image.NEAREST), (ox, 0))
    ox += pn.width * z + 10
S.save(saida); print(S.size)
