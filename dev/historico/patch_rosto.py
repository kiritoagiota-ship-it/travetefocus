p = r'C:\Users\kirit\travetefocus\app\kirito.py'
s = open(p, 'rb').read().decode('utf-8').replace('\r\n', '\n')


def troca(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)


# cores novas: sombra funda do rosto e pele com reflexo roxo do fogo
troca("""    '&': (0.11, 0.075, 0.18, 1),                                 # roupa na sombra: meio-tom roxo
}""", """    '&': (0.11, 0.075, 0.18, 1),                                 # roupa na sombra: meio-tom roxo
    '~': (0.38, 0.22, 0.40, 1),                                  # rosto: sombra funda da franja (Mugetsu)
    '^': (0.86, 0.72, 0.98, 1),                                  # pele com reflexo roxo do fogo
}""")
troca("_CORPO_M = set('HhSsDdVJIeTt&')", "_CORPO_M = set('HhSsDdVJIeTt&~^')")
troca("_CORPO = set('CcAqGPBMSsHhE24JIen7tU3%bp')", "_CORPO = set('CcAqGPBMSsHhE24JIen7tU3%bp~^')")

# versoes Mugetsu das cabecas (geradas uma vez)
troca('''for _m_ in (_CAB_FRENTE, _CAB_COSTAS, _TOR_COSTAS) + tuple(_CABECAS_F.values()):
    assert all(len(_l) == 39 for _l in _m_), 'vista com largura errada\'''', '''for _m_ in (_CAB_FRENTE, _CAB_COSTAS, _TOR_COSTAS) + tuple(_CABECAS_F.values()):
    assert all(len(_l) == 39 for _l in _m_), 'vista com largura errada'


def _rosto_mugetsu(mapa):
    """Rosto na forma Mugetsu: sombra funda da franja caindo por cima dos
    olhos (a pele logo abaixo do cabelo escurece em 2 degraus), olhos em
    brasa (a iris inteira acesa, com o miolo claro) e reflexo roxo do fogo
    na borda do rosto."""
    c = [list(l) for l in mapa]
    H, W = len(c), len(c[0])
    cab = set('HJIhU')
    pele = set('Ss')
    for r in range(H):
        for col in range(W):
            ch = c[r][col]
            if ch in pele:
                if r >= 1 and mapa[r - 1][col] in cab:
                    c[r][col] = '~'
                elif r >= 2 and mapa[r - 2][col] in cab:
                    c[r][col] = 't'
                elif r >= 3 and mapa[r - 3][col] in cab and ch == 'S':
                    c[r][col] = 's'
                elif any(not (0 <= r + vy < H and 0 <= col + vx < W) or mapa[r + vy][col + vx] == '.'
                         for vx, vy in ((1, 0), (-1, 0), (0, 1))):
                    c[r][col] = '^'                  # borda do rosto: luz do fogo
            elif ch in '3m':
                c[r][col] = 'e'                      # iris toda acesa (vira roxo)
            elif ch == 'e' and r + 1 < H and mapa[r + 1][col] in '3m':
                c[r][col] = 'n'                      # miolo claro da brasa
    return [''.join(l) for l in c]


_CABECAS2_M = {k: _rosto_mugetsu(v) for k, v in _CABECAS2.items()}
_CABECAS_F_M = {k: _rosto_mugetsu(v) for k, v in _CABECAS_F.items()}


def olhos_texel(p):
    """Centro dos olhos (texels, sem espelho) na pose - para o brilho e o
    rastro de luz dos olhos na forma Mugetsu. De costas: nenhum."""
    vista = p.get('vista', 'lado')
    if vista == 'costas':
        return []
    dx, dy = _meia(p['dx']), _meia(p['dy'])
    topo = _PES + _alt_pernas(p) + dy + len(_TRONCO) - 1
    incl = int(round(p.get('incl', 0) or 0))
    cab_x = _t(_X0 + dx + incl) + int(round(p.get('hx', 0) or 0))
    cab_ty = _t(topo + len(_CABECA)) + R - 1 + int(round(p.get('hy', 0) or 0))
    cols = (12.5, 26.5) if vista == 'frente' else (22.5, 32.0)
    return [(cab_x + c, cab_ty - 23) for c in cols]''')

# montar usa as cabecas Mugetsu
troca('''    elif vista == 'frente':
        cabeca = _CABECAS_F.get(p['olhos'], _CABECAS_F['a'])
    else:
        cabeca = _CABECAS2.get(p['olhos'], _CABECAS2['a'])''', '''    elif vista == 'frente':
        caras = _CABECAS_F_M if mugetsu else _CABECAS_F
        cabeca = caras.get(p['olhos'], caras['a'])
    else:
        caras = _CABECAS2_M if mugetsu else _CABECAS2
        cabeca = caras.get(p['olhos'], caras['a'])''')
open(p, 'wb').write(s.replace('\n', '\r\n').encode('utf-8'))
print('ok')
