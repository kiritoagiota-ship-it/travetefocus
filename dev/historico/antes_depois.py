import os, sys, importlib
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
sys.path.insert(0, 't'); sys.path.insert(1, r'C:\Users\kirit\travetefocus\app')
Kold = importlib.import_module('kirito_old')
import kirito as Knew
BG = (8, 8, 16)
def render(K, p, ps):
    te = ps // K.R
    px = K.montar(p)
    xs = [x for x, y in px]; ys = [y for x, y in px]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    im = Image.new('RGB', ((x1 - x0 + 1) * te, (y1 - y0 + 1) * te), BG)
    d = ImageDraw.Draw(im)
    for (x, y), c in px.items():
        r, g, b, a = K._PALETA[c]
        col = tuple(int(255 * (v * a) + bc * (1 - a)) for v, bc in zip((r, g, b), BG))
        X = (x - x0) * te; Y = (y1 - y) * te
        d.rectangle([X, Y, X + te - 1, Y + te - 1], fill=col)
    return im
pares = [('guarda', {}), ('evo_carga', {'mugetsu': True, 'sobe': 1.0, 'capa': 1.0, 'olhos': 'l'})]
ims = []
for nome, extra in pares:
    for K, ps, rot in ((Kold, 8, 'antes'), (Knew, 9, 'agora')):
        p = dict(K.POSE_A[nome]); p.update(extra)
        ims.append((rot, render(K, p, ps)))
esc = 2
W = sum(i.width * esc + 30 for _, i in ims) + 30
H = max(i.height for _, i in ims) * esc + 50
S = Image.new('RGB', (W, H), BG)
d = ImageDraw.Draw(S)
x = 30
for rot, im in ims:
    im2 = im.resize((im.width * esc, im.height * esc), Image.NEAREST)
    S.paste(im2, (x, H - im2.height - 10))
    d.text((x, 10), rot, fill=(255, 230, 120))
    x += im2.width + 30
S.save('yoru_antes_agora.png'); print(S.size)
