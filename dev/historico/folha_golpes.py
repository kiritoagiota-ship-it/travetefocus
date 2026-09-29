import os, sys
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
from PIL import Image, ImageDraw
import kirito as K
P = K.POSE_A
BG = (8, 8, 16)
def render(p, te=2, caixa=(4, 4, 76, 70)):
    px = K.montar(p)
    x0, y0, x1, y1 = (v * K.R for v in caixa)
    im = Image.new('RGB', ((x1 - x0) * te, (y1 - y0) * te), BG)
    d = ImageDraw.Draw(im)
    for (x, y), c in px.items():
        if x0 <= x < x1 and y0 <= y < y1:
            r, g, b, a = K._PALETA[c]
            col = tuple(int(255 * (v * a) + bc * (1 - a)) for v, bc in zip((r, g, b), BG))
            X = (x - x0) * te; Y = (y1 - 1 - y) * te
            d.rectangle([X, Y, X + te - 1, Y + te - 1], fill=col)
    return im
linhas = [('abertura 1 (iai)', 'saca0', 'corta1'), ('abertura 2 / wipe', 'sobe_arma', 'sobe_corta'),
          ('abertura 3 / wipe', 'desce_arma', 'desce_corta'), ('abertura 4 / wipe', 'x_arma', 'x_corta'),
          ('apagar (registro/memorias/ganhos)', 'arma1', 'corta_desce')]
rows = []
for rot, a, c in linhas:
    chaves, i_r = K.golpe(P[a], P[c], n_arma=2, prende=1, segue=3, volta=4)
    seq = K.sequencia(chaves)
    idx = [0, max(0, i_r - 2), i_r - 1, i_r, i_r + 2, len(seq) - 1]
    ims = [render(seq[i]) for i in idx]
    rows.append((rot, ims))
w = ims[0].width; h = ims[0].height
S = Image.new('RGB', (w * 6, (h + 18) * len(rows)), (20, 20, 28))
d = ImageDraw.Draw(S)
for r, (rot, ims) in enumerate(rows):
    y = r * (h + 18)
    d.text((4, y + 3), rot, fill=(255, 230, 120))
    for i, im in enumerate(ims):
        S.paste(im, (i * w, y + 18))
S.save('t/golpes_hoje.png'); print(S.size)
