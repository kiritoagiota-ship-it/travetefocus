p = r'C:\Users\kirit\travetefocus\app\kirito.py'
s = open(p, 'rb').read().decode('utf-8').replace('\r\n', '\n')


def troca(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:80], s.count(a))
    s = s.replace(a, b)


# ── painel rasgado ──
troca('''def _casaco3(px, base, y0, capa, lift, fase, saia, parte):
    """Sobretudo com silhueta propria (texels). parte='tras': a aba de tras
    que abre em DUAS caudas longas ate o tornozelo e voa com o vento;
    parte='frente': a aba da frente ate o joelho, aberta (as pernas aparecem).
    Bordas com costura ciano, forro, dobras que andam com o pano, barra."""''', '''def _painel_rasgado(px, linhas, cor_fn, kk_ini, fase, vento):
    """Como _painel, mas da linha kk_ini para baixo o pano vira TIRAS
    rasgadas: cada tira (R texels) tem o seu comprimento, algumas tem um vao
    do lado e cada uma balanca sozinha, mais na ponta. A barra de cada tira
    ganha o friso (que brilha na forma Mugetsu)."""
    chao = _PES * R
    dois_pi = 2 * math.pi
    for (y, a, b, kk, total) in linhas:
        if b < a:
            a, b = b, a
        d = kk - kk_ini
        for x in range(a, b + 1):
            if d < 0:
                if y >= chao:
                    ch = cor_fn(x, y, a, b, kk, total)
                    if ch:
                        px[(x, y)] = ch
                continue
            rel = x - a
            h = math.sin((rel // R) * 12.9898 + 78.233) * 43758.5453
            h -= math.floor(h)                                 # 0..1, fixo por tira
            tot = total - int(R * (0.3 + 3.4 * h))             # cada tira de um tamanho
            if kk >= tot:
                continue
            if rel % R == R - 1 and d > R and h > 0.4:
                continue                                       # vao entre as tiras
            dx = int(round(math.sin(dois_pi * (fase * 1.5 + h) - d * 0.12) * d / float(R) * (0.35 + 0.3 * h)
                           - vento * d * 0.1))
            if y < chao:
                continue
            ch = cor_fn(x, y, a, b, kk, tot)
            if ch:
                px[(x + dx, y)] = ch


def _casaco3(px, base, y0, capa, lift, fase, saia, parte, rasgado=False):
    """Sobretudo com silhueta propria (texels). parte='tras': a aba de tras
    que abre em DUAS caudas longas ate o tornozelo e voa com o vento;
    parte='frente': a aba da frente ate o joelho, aberta (as pernas aparecem).
    Bordas com costura ciano, forro, dobras que andam com o pano, barra.
    rasgado (forma Mugetsu): sobretudo longo ate o chao, com a barra em
    tiras rasgadas voando e um friso aceso na borda."""''')
troca('''    if parte == 'frente':
        n = int(5.0 * R)
        linhas = []''', '''    if parte == 'frente':
        n = int((8.0 if rasgado else 5.0) * R)
        linhas = []''')
troca('''            if x == a:
                return 'Z'                         # costura ciano na abertura
            if x <= a + 2:
                return 'q'                         # forro
            d = dobra(x, kk)
            return '2' if d == 0 else ('A' if d in (1, 2) else 'C')
        _painel(px, linhas, cor)
        return''', '''            if x == a:
                return 'Z'                         # costura ciano na abertura
            if x <= a + 2:
                return 'q'                         # forro
            d = dobra(x, kk)
            return '2' if d == 0 else ('A' if d in (1, 2) else 'C')
        if rasgado:
            _painel_rasgado(px, linhas, cor, int(4.0 * R), fase + 0.37, vento)
        else:
            _painel(px, linhas, cor)
        return''')
troca('''    n1, n_ext, n_int = int(3.5 * R), int(11.0 * R), int(9.5 * R)''',
      '''    n1 = int(3.5 * R)
    n_ext, n_int = (int(14.5 * R), int(13.0 * R)) if rasgado else (int(11.0 * R), int(9.5 * R))''')
troca('''    def cor_tras(x, y, a, b, kk, total):
        if kk >= total - 2:
            return 'Z' if kk == total - 2 else '2'   # barra com friso ciano
        if x == a:
            return 'c'
        if x == a + 1:
            return 'A'
''', '''    def cor_tras(x, y, a, b, kk, total):
        if kk >= total - 2:
            return 'Z' if kk == total - 2 else '2'   # barra com friso ciano
        if x == a:
            return 'c'
        if x == a + 1:
            return 'A'
        if rasgado and x == a + 3 and kk > R:
            return 'Z'                             # friso aceso na borda
''')
troca('''    _painel(px, linhas_int, cor_int)              # a cauda de dentro fica atras
    _painel(px, linhas_ext, cor_tras)''', '''    if rasgado:
        _painel_rasgado(px, linhas_int, cor_int, int(7.0 * R), fase + 0.5, vento)
        _painel_rasgado(px, linhas_ext, cor_tras, int(7.5 * R), fase, vento)
    else:
        _painel(px, linhas_int, cor_int)          # a cauda de dentro fica atras
        _painel(px, linhas_ext, cor_tras)''')

# ── braco com faixas e ombreira ──
troca('''def _braco3(px, sx, sy, hx, hy, frente=False, bracadeira=False):''',
      '''def _braco3(px, sx, sy, hx, hy, frente=False, bracadeira=False, faixas=False, fase=0.0):''')
troca('''    def antebraco(j, t):
        if bracadeira and 0.28 < t < 0.8:''', '''    lb = math.hypot(hx - ex, hy - ey)

    def antebraco(j, t):
        if faixas and t < 0.84:                    # faixas enroladas (forma Mugetsu)
            if t < 0.1:
                return base_c
            if (int(t * lb) + j) % 4 == 0:
                return 'W'
            return 'g' if j >= 2 else 'u'
        if bracadeira and 0.28 < t < 0.8:''')
troca('''    if frente:                                     # contorno escuro por cima do corpo
        for (x, y) in meu:
            for vx, vy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + vx, y + vy)
                if q not in meu and px.get(q) in _CORPO:
                    px[q] = 'N'
    px.update(meu)


def _mao(''', '''    if faixas:                                     # ponta solta da faixa, voando para tras
        dois_pi = 2 * math.pi
        for (oy, fx) in ((1, 0.0), (-1, 0.4)):
            for i in range(int(4 * R)):
                x = int(round(hx - 3 - i))
                y = int(round(hy + oy + math.sin(dois_pi * (fase * 2.0 + fx) - i * 0.5) * i * 0.22))
                meu.setdefault((x, y), 'W' if i % 5 == 4 else 'u')
    if frente:                                     # contorno escuro por cima do corpo
        for (x, y) in meu:
            for vx, vy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + vx, y + vy)
                if q not in meu and px.get(q) in _CORPO:
                    px[q] = 'N'
    px.update(meu)


# ombreira de metal escuro (forma Mugetsu), em cima do ombro da frente:
# domo com reflexo, duas laminas e friso roxo aceso
_OMBREIRA = [
    "....uuuuu....",
    "..uugggkk+u..",
    ".ugggggggkku.",
    "uggggggggggku",
    "uuuuuuuuuuuuu",
    "oVoooooooVoo.",
    ".ugggggggku..",
    "..uuuuuuuu...",
    "...ooooooo...",
]


def _ombreira(px, sx, sy):
    _carimbo(px, _OMBREIRA, sx - 6, sy + 5)


def _mao(''')

# ── montar: usa tudo na forma Mugetsu ──
troca('''    if mugetsu:
        _cabelo_longo2(px, cab_x, cab_ty, cb, sobe, fase, R * (_PES + 4))''',
      '''    if mugetsu:
        _cabelo_longo2(px, cab_x, cab_ty, cb, sobe, fase, R * (_PES + 4), p.get('cresce', 1.0))''')
troca('''        _braco3(px, o2[0], o2[1], h2[0], h2[1], frente=ergue2)''',
      '''        _braco3(px, o2[0], o2[1], h2[0], h2[1], frente=ergue2, faixas=mugetsu, fase=fase + 0.3)''')
troca('''    _casaco3(px, base, topo - len(_TRONCO), p['capa'], p['lift'], fase, saia, 'tras')''',
      '''    _casaco3(px, base, topo - len(_TRONCO), p['capa'], p['lift'], fase, saia, 'tras', mugetsu)''')
troca('''    _casaco3(px, base, topo - len(_TRONCO), p['capa'], p['lift'], fase, saia, 'frente')''',
      '''    _casaco3(px, base, topo - len(_TRONCO), p['capa'], p['lift'], fase, saia, 'frente', mugetsu)''')
troca('''        _braco3(px, o1[0], o1[1], h1[0], h1[1], frente=True, bracadeira=True)''',
      '''        _braco3(px, o1[0], o1[1], h1[0], h1[1], frente=True, bracadeira=not mugetsu,
                faixas=mugetsu, fase=fase)
        if mugetsu:
            _ombreira(px, o1[0], o1[1])''')
troca('''                 pernas_b=None, pt=0.0, vista='lado',''', '''                 pernas_b=None, pt=0.0, vista='lado', cresce=1.0,''')
open(p, 'wb').write(s.replace('\n', '\r\n').encode('utf-8'))
print('ok')
