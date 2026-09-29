p = r'C:\Users\kirit\travetefocus\app\kirito.py'
c = open(p, encoding='utf-8').read()


def troca(a, b):
    global c
    assert c.count(a) == 1, (a[:70], c.count(a))
    c = c.replace(a, b)


troca("""def _girado_esc(px, hx, hy, ux, uy, k0, k1, j0, j1, cor, s, evita=None):""", '''_RAIZ_TUFO = (34.0, 14.0)          # onde o tufo nasce no mapa da cabeca


def _no_tufo(c, r):
    return r < 40 and c < 38 - (r - 4) * 0.62


def _cabeca5(px, olhos, cab_x, cab_ty, cb, sobe, fase):
    """Cabeca da referencia com o TUFO vivo: cada texel do tufo anda um
    pouco (quanto mais longe da raiz, mais): o vento deita o tufo para tras,
    o reiatsu levanta, e uma onda passa da raiz para as pontas. O desenho
    de cada estado fica guardado."""
    q4 = lambda v: round(v * 4) / 4.0
    cb, sobe = q4(max(-1.0, min(3.0, cb))), q4(sobe)
    olhos = olhos if olhos in _YM.CABECAS else 'a'
    _parte(px, ('cab5', olhos, cb, sobe, round(fase, 3)), cab_x, cab_ty,
           lambda d: _cabeca5_desenho(d, olhos, cb, sobe, fase))


def _cabeca5_desenho(d, olhos, cb, sobe, fase):
    mapa = _YM.CABECAS[olhos]
    rx, ry = _RAIZ_TUFO
    corre = max(0.0, min(2.5, cb))
    amp = 1.1 + 0.8 * min(2.0, abs(cb)) + 2.2 * sobe
    tufo = {}
    resto = {}
    for r, linha in enumerate(mapa):
        for c, ch in enumerate(linha):
            if ch == '.':
                continue
            if not _no_tufo(c, r):
                resto[(c, -r)] = ch
                continue
            dist = math.hypot(c - rx, r - ry)
            w = max(0.0, min(1.0, (dist - 3.0) / 30.0)) ** 1.2
            dxx = -corre * 3.2 * w - sobe * 1.2 * w
            dyy = corre * 1.6 * w + sobe * 4.5 * w + amp * w * math.sin(2 * math.pi * (fase * 1.3 - dist / 30.0))
            tufo[(c + int(round(dxx)), -r + int(round(dyy)))] = ch
    # furinhos que a onda abriu no tufo: tapa com o vizinho
    furos = {}
    for (x, y) in tufo:
        for (a, b) in _VIZ4:
            q = (x + a, y + b)
            if q not in tufo:
                furos[q] = furos.get(q, 0) + 1
    for q, n in furos.items():
        if n >= 3:
            for (a, b) in _VIZ4:
                v = tufo.get((q[0] + a, q[1] + b))
                if v is not None:
                    tufo[q] = v
                    break
    d.update(tufo)
    d.update(resto)                                     # a cabeca por cima da raiz do tufo


def _girado_esc(px, hx, hy, ux, uy, k0, k1, j0, j1, cor, s, evita=None):''')
troca("""    cabeca = _YM.CABECAS.get(p['olhos']) or _YM.CABECAS['a']
    _carimbo(px, cabeca, cab_x, cab_ty)""", """    _cabeca5(px, p['olhos'], cab_x, cab_ty, cb, sobe, fase)""")
open(p, 'w', encoding='utf-8', newline='\r\n'.encode().decode('unicode_escape')).write(c)
print('ok')
