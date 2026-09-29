p = r'C:\Users\kirit\travetefocus\app\kirito.py'
s = open(p, 'rb').read().decode('utf-8').replace('\r\n', '\n')


def troca(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)


# cache de partes (espadas e cabelao): desenhadas uma vez na origem e so
# transladadas depois
troca('''def _girado(px, hx, hy, ux, uy, k0, k1, j0, j1, cor, evita=None):''', '''_PARTES = OrderedDict()
_PARTES_MAX = 140


def _parte(px, chave, x, y, desenha):
    """Partes que so mudam de lugar (espada num angulo, cabelao numa forma):
    desenhadas uma vez na origem e depois so copiadas para (x, y)."""
    item = _PARTES.get(chave)
    if item is None:
        tmp = {}
        desenha(tmp)
        item = tuple(tmp.items())
        _PARTES[chave] = item
        while len(_PARTES) > _PARTES_MAX:
            _PARTES.popitem(last=False)
    else:
        _PARTES.move_to_end(chave)
    for (a, b), ch in item:
        px[(x + a, y + b)] = ch


def _girado(px, hx, hy, ux, uy, k0, k1, j0, j1, cor, evita=None):''')

troca('''def _espada2(px, hx, hy, ang, comp, tipo, smear_de=None, brilho=None, fase=0.0):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    if smear_de is not None and abs(smear_de - ang) > 8:
        _rastro2(px, hx, hy, smear_de, ang, comp)
    b = brilho if smear_de is None else None
    if tipo == 1:
        _katana2(px, hx, hy, ux, uy, nx, ny, comp, b)
    elif tipo == 2:
        _repulser2(px, hx, hy, ux, uy, nx, ny, comp, b)
    else:
        _fundida2(px, hx, hy, ux, uy, nx, ny, comp, b, tipo == 4, fase)''', '''def _espada2(px, hx, hy, ang, comp, tipo, smear_de=None, brilho=None, fase=0.0):
    ang = float(round(ang))                        # grau inteiro: a lamina vira cache
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    if smear_de is not None and abs(smear_de - ang) > 8:
        _rastro2(px, hx, hy, smear_de, ang, comp)
    b = brilho if smear_de is None else None
    mv = int(fase * 18) if tipo >= 3 else 0

    def desenha(d):
        if tipo == 1:
            _katana2(d, 0, 0, ux, uy, nx, ny, comp, b)
        elif tipo == 2:
            _repulser2(d, 0, 0, ux, uy, nx, ny, comp, b)
        else:
            _fundida2(d, 0, 0, ux, uy, nx, ny, comp, b, tipo == 4, (mv + 0.5) / 18.0)
    _parte(px, ('esp', tipo, comp, ang, b, mv), hx, hy, desenha)''')

troca('''    if mugetsu:
        _cabelo_longo2(px, cab_x, cab_ty, cb, sobe, fase, R * (_PES + 4), p.get('cresce', 1.0))''',
      '''    if mugetsu:
        cb_q, sobe_q = round(cb * 4) / 4.0, round(sobe * 4) / 4.0
        cr = round(p.get('cresce', 1.0), 2)
        alto = cab_ty - R * (_PES + 4)
        _parte(px, ('cab', cb_q, sobe_q, fase, cr, alto), cab_x, cab_ty,
               lambda d: _cabelo_longo2(d, 0, 0, cb_q, sobe_q, fase, -alto, cr))''')
if 'from collections import OrderedDict' not in s:
    raise SystemExit('sem OrderedDict import?')
open(p, 'wb').write(s.replace('\n', '\r\n').encode('utf-8'))
print('ok')
