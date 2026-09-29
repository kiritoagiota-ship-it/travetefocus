"""Plano dos golpes da abertura (fora do app): mostra a frase, onde o Yoru
fica no comeco/fim de cada golpe e o arco da ponta da lamina.
uso: plano.py SAIDA   (geometria do 720x1560 @1.75)"""
import math, sys, os, types
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito as K
src = open(r'C:\Users\kirit\travetefocus\app\cenas.py', encoding='utf-8').read()
ns = {'math': math}
exec(src[src.index('_PAL_CORTE = {'):src.index('class OficinaCortes')], ns)
ArcoCorte = ns['ArcoCorte']

if os.environ.get('GEO') == '1080':
    W, H = 1080, 2340
    th, ps = 90.0, 7
    ox_t, oy_t = 183.5, 1195.2
    larg = [0.0, 54.0, 113.0, 172.0, 243.0, 297.0, 351.0, 405.0, 427.0, 479.0, 537.0, 595.0, 654.0, 713.0]
    m = max(2.625 * 4, ps)
else:
    W, H = 720, 1560
    th, ps = 59.0, 7
    ox_t, oy_t = 123.5, 797.3
    larg = [0.0, 36.0, 75.0, 114.0, 161.0, 197.0, 233.0, 269.0, 283.0, 317.0, 356.0, 395.0, 434.0, 473.0]
    m = max(1.75 * 4, ps)
area = (0.0, 0.0, float(W), float(H))
kk = types.SimpleNamespace(ps=ps, espelhar=True)
kk._local_texel = lambda x, y: K.KiritoPixel._local_texel(kk, x, y)
kk.ancora_local = lambda: K.KiritoPixel.ancora_local(kk)
kk.extensao = lambda p=None: K.KiritoPixel.extensao(kk, p)
P = K.POSE_A


def _perto(a, alvo):
    if a is None or alvo is None:
        return a
    while a - alvo > 180:
        a -= 360
    while alvo - a > 180:
        a += 360
    return a


def _com(p, **kw):
    q = dict(p); q.update(kw); return q


def _ext(poses):
    e = [0.0] * 4
    for p in poses:
        for i, v in enumerate(kk.extensao(p)):
            e[i] = max(e[i], v)
    return e


def quadro(x, y, poses):
    poses = [P[n] if isinstance(n, str) else n for n in poses]
    esq, baixo, dir_, cima = _ext(poses)
    x0, y0, x1, y1 = area
    lo, hi = x0 + m + esq, x1 - m - dir_
    x = (lo + hi) / 2.0 if lo > hi else min(hi, max(lo, x))
    lo, hi = y0 + m + baixo, y1 - m - cima
    y = (lo + hi) / 2.0 if lo > hi else min(hi, max(lo, y))
    return x, y


VIS = [(0, 3), (3, 5), (5, 7), (8, 10), (10, 13)]


def silaba(i):
    a, b = VIS[i]
    x0, x1 = ox_t + larg[a], ox_t + larg[b]
    return (x0 + x1) / 2.0, oy_t + th * 0.5, x1 - x0


# ── o mesmo codigo da cena (copiado de cenas.py) ──
blk = src[src.index('        def ponta(pose, anc, qual=1):'):src.index('        def cortar(chave, i,')]
blk = '\n'.join(l[8:] for l in blk.split('\n'))
ARCOS = {}
PEDIDOS = []
oficina = types.SimpleNamespace(pedir=lambda ch, a, pal: PEDIDOS.append(ch))
g = dict(globals())
exec(blk, g)
posicionar = g['posicionar']
exec_poses = src[src.index("        pronto = _com(P['saca0'], olhos='s')"):src.index("        # o do Mugetsu atravessa")]
exec_poses = '\n'.join(l[8:] for l in exec_poses.split('\n'))
g['ARCOS'] = ARCOS
exec(exec_poses, g)
PASSOS = [('tra', 'A0', 'A1', 'pronto', 'corta_tra'), ('ve', 'B0', 'B1', 'arma_ve', 'corta_ve'),
          ('te', 'C0', 'C1', 'arma_te', 'corta_te'), ('fo', 'Dm', 'D1', 'arma_fo', 'corta_fo')]


def sprite(p, anc, esp):
    px = K.montar(p)
    te = ps / float(K.R)
    ax, ay = K.KiritoPixel.ancora_local(kk)
    out = []
    for (x, y), c in px.items():
        xx = (K.TW - 1 - x) if esp else x
        out.append((anc[0] - ax + (xx + 0.5) * te, anc[1] - ay + (y + 0.5) * te, K._PALETA[c]))
    return out


def desenha(nome, a0, a1, p0, p1, arcs):
    Y0, Y1 = int(oy_t - 400), int(oy_t + 400)
    im = Image.new('RGB', (W, Y1 - Y0), (6, 8, 14))
    d = ImageDraw.Draw(im)
    tr = lambda x, y: (x, (H - y) - (H - Y1))
    for i in range(5):
        cx, cy, w = silaba(i)
        d.rectangle([tr(cx - w / 2, oy_t + th * 0.72), tr(cx + w / 2, oy_t + th * 0.28)], outline=(0, 160, 190))
    for (x, y, c) in sprite(p0, a0, True):
        X, Y = tr(x, y)
        d.point((X, Y), fill=tuple(int(v * 110) for v in c[:3]))
    for (x, y, c) in sprite(p1, a1, True):
        X, Y = tr(x, y)
        d.point((X, Y), fill=tuple(int(v * 255) for v in c[:3]))
    for a, cor in arcs:
        pts = [tr(*a.ponto(s / 40.0)) for s in range(41)]
        d.line(pts, fill=cor, width=2)
        pts = [tr(*a.ponto(s / 40.0, -0.4 * a.esp)) for s in range(41)]
        d.line(pts, fill=(255, 255, 0), width=1)
        d.ellipse([tr(*a.ponto(0.0))[0] - 4, tr(*a.ponto(0.0))[1] - 4, tr(*a.ponto(0.0))[0] + 4, tr(*a.ponto(0.0))[1] + 4], outline=cor)
    for (x, y), cor in ((a0, (255, 80, 80)), (a1, (80, 255, 80))):
        X, Y = tr(x, y)
        d.ellipse([X - 4, Y - 4, X + 4, Y + 4], fill=cor)
    d.text((4, 4), nome, fill='yellow')
    return im


ims = []
for ch, n0, n1, pp0, pp1 in PASSOS:
    arcs = [(ARCOS[ch][0], (0, 230, 255))]
    if ch + '2' in ARCOS:
        arcs.append((ARCOS[ch + '2'][0], (90, 110, 255)))
    ims.append(desenha(ch, g[n0], g[n1], g[pp0], g[pp1], arcs))
    print(ch, [round(v) for v in g[n0]], [round(v) for v in g[n1]])
print('D0', [round(v) for v in g['D0']], 'y_chao', round(g['y_chao']))
S = Image.new('RGB', (W * 2 + 10, (ims[0].height + 10) * 2))
for k, im in enumerate(ims):
    S.paste(im, ((k % 2) * (W + 10), (k // 2) * (im.height + 10)))
S.save(sys.argv[1]); print(S.size)
a = ARCOS['ve'][0]
cx, cy, w = silaba(1)
print('VE centro', round(cx), round(cy))
for k in range(0, 41, 2):
    x, y = a.ponto(k / 40.0, -0.4 * a.esp)
    print(k, round(x), round(y), end=' | ')
print()
print('B0', g['B0'], 'quadro B0', quadro(g['B0'][0], g['B0'][1], [g['arma_ve']]))
import time
des = ns['_desenho_corte']; PAL = ns['_PAL_CORTE']
u = (ps / 5.0) * max(1, int(round(2.4 / (ps / 5.0))))
ARCOS['cus'] = (ArcoCorte.pelo_meio((ox_t + larg[-1] / 2.0, oy_t + th * 0.5), 0, W * 1.02, -0.05, th * 1.35), 'mug')
tot = 0
for ch, (a, pal) in ARCOS.items():
    t0 = time.time(); n = 0
    for r in des(a, PAL[pal], u):
        n += 1
        if r is not None:
            w, h = r[3], r[4]
    dtm = (time.time() - t0) * 1000; tot += dtm
    print(f'{ch}: {dtm:.0f} ms  {w}x{h} celulas, {n} passos, comp {a.comp:.0f}px')
print('total', round(tot), 'ms (PC)')
