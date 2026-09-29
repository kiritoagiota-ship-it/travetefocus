"""Compoe as 3 camadas como o widget faz e compara com o desenho inteiro."""
import sys, os, time
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image
import kirito as K
BG = (31, 53, 80)
x0, x1, y0, y1 = 20 * K.R, 60 * K.R, 11 * K.R, 50 * K.R


def pinta(im, dados, rec, ox, oy):
    X0, Y0, w, h = rec
    X0 += ox; Y0 += oy
    pix = im.load()
    for yy in range(h):
        for xx in range(w):
            i = (yy * w + xx) * 4
            a = dados[i + 3]
            if a:
                x, y = X0 + xx, Y0 + yy
                if x0 <= x < x1 and y0 <= y < y1:
                    r, g, b = dados[i:i + 3]
                    al = a / 255.0
                    bg = pix[x - x0, y1 - 1 - y]
                    pix[x - x0, y1 - 1 - y] = tuple(int(v * al + bb * (1 - al)) for v, bb in zip((r, g, b), bg))


def composto(q):
    im = Image.new('RGB', (x1 - x0, y1 - y0), BG)
    corpo, cauda, cabeca = K.chave_camadas(q)
    cx, topo, cab_x, cab_ty = K.ancoras(q)
    d, r = K.imagem_camada(q, 'cauda', cauda); pinta(im, d, r, cx, topo)
    d, r = K.imagem_camada(q, 'corpo', corpo); pinta(im, d, r, 0, 0)
    if cabeca:
        d, r = K.imagem_camada(q, 'cabeca', cabeca); pinta(im, d, r, cab_x + q.get('hx', 0), cab_ty + q.get('hy', 0))
    return im


def inteiro(q):
    im = Image.new('RGB', (x1 - x0, y1 - y0), BG)
    d, r = K._rasteriza(K.montar(q)); pinta(im, d, r, 0, 0)
    return im


P = K.POSE_A
qs = [dict(P['guarda'], capa=0.5, cabelo=0.5, fase=1/6), dict(P['corta_desce'], capa=1.5, cabelo=1.5, fase=0.5),
      dict(P['arma1'], capa=0.2, fase=2/6), dict(P['salto_arma'], lift=1.5, capa=0.5)]
z = 3
S = Image.new('RGB', ((x1 - x0) * z * len(qs), (y1 - y0) * z * 2), (0, 0, 0))
for i, q in enumerate(qs):
    S.paste(inteiro(q).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST), (i * (x1 - x0) * z, 0))
    S.paste(composto(q).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST), (i * (x1 - x0) * z, (y1 - y0) * z))
S.save(sys.argv[1])
# custo: corpo por pose; cauda e cabeca com cache
import random
rnd = random.Random(2)
K._CAM.clear(); K._PARTES.clear()
poses = [dict(p, capa=rnd.choice([0, .25, .5]), cabelo=rnd.choice([0, .25]), fase=rnd.choice([0, 1/6])) for p in P.values()]
for qual in ('corpo', 'cauda', 'cabeca'):
    t = time.perf_counter(); n = 0
    for q in poses:
        ch = K.chave_camadas(q)[('corpo', 'cauda', 'cabeca').index(qual)]
        if ch is None: continue
        K.imagem_camada(q, qual, ch); n += 1
    print(qual, '%.1f ms/pose (com cache)' % ((time.perf_counter() - t) * 1000 / max(1, n)), 'distintas', len([k for k in K._CAM if k[0] == qual]))
