p = r'C:\Users\kirit\travetefocus\app\kirito.py'
s = open(p, 'rb').read().decode('utf-8').replace('\r\n', '\n')


def troca(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)


# ── pernas: cada perna desenhada uma vez por forma (so muda de lugar) ──
troca('''        joelho = _ik(quad[0], quad[1], pe[0], pe[1] + 0.6, _COXA, _CANELA, frente_primeiro)
        _perna3(px, quad, joelho, pe, frente, ar)''', '''        joelho = _ik(quad[0], quad[1], pe[0], pe[1] + 0.6, _COXA, _CANELA, frente_primeiro)
        # a perna so muda de lugar: guarda o desenho relativo ao texel do pe
        bx, by = int(math.floor(pe[0] * R)), int(math.floor(pe[1] * R))
        q4 = lambda v, o: int(round((v * R - o) * 4))
        chave = ('perna', q4(quad[0], bx), q4(quad[1], by), q4(joelho[0], bx), q4(joelho[1], by),
                 q4(pe[0], bx), q4(pe[1], by), frente, ar)
        rel = lambda c: ((c[0] * R - bx) / float(R), (c[1] * R - by) / float(R))
        _parte(px, chave, bx, by,
               lambda d, a=rel(quad), b=rel(joelho), c=rel(pe), f=frente, r=ar: _perna3(d, a, b, c, f, r))''')

# ── bracos: o desenho do braco vira cache (o contorno por cima do corpo e
#    feito depois, porque depende do que ja esta desenhado) ──
troca('''def _braco3(px, sx, sy, hx, hy, frente=False, bracadeira=False, faixas=False, fase=0.0):
    """Braco com cotovelo (IK): manga larga com vinco, antebraco mais fino,
    cotovelo arredondado, punho prateado; o da espada leva a bracadeira de
    metal com a linha ciano e reflexo. Mao fechada."""
    LA, LB = 4.4 * R, 4.4 * R''', '''def _braco3(px, sx, sy, hx, hy, frente=False, bracadeira=False, faixas=False, fase=0.0):
    """Braco com cotovelo (IK): manga larga com vinco, antebraco mais fino,
    cotovelo arredondado, punho prateado; o da espada leva a bracadeira de
    metal com a linha ciano e reflexo. Mao fechada. O desenho do braco e
    guardado (so muda de lugar); o contorno escuro por cima do corpo e
    feito aqui, porque depende do que ja esta desenhado."""
    fs = round(fase, 2) if faixas else 0.0
    meu = {}
    _parte(meu, ('braco', hx - sx, hy - sy, frente, bracadeira, faixas, fs), sx, sy,
           lambda d: _braco3_desenho(d, 0, 0, hx - sx, hy - sy, frente, bracadeira, faixas, fs))
    if frente:                                     # contorno escuro por cima do corpo
        for (x, y) in meu:
            for vx, vy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + vx, y + vy)
                if q not in meu and px.get(q) in _CORPO:
                    px[q] = 'N'
    px.update(meu)


def _braco3_desenho(meu, sx, sy, hx, hy, frente, bracadeira, faixas, fase):
    LA, LB = 4.4 * R, 4.4 * R''')
troca('''                meu.setdefault((x, y), 'W' if i % 5 == 4 else 'u')
    if frente:                                     # contorno escuro por cima do corpo
        for (x, y) in meu:
            for vx, vy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + vx, y + vy)
                if q not in meu and px.get(q) in _CORPO:
                    px[q] = 'N'
    px.update(meu)''', '''                meu.setdefault((x, y), 'W' if i % 5 == 4 else 'u')''')
troca('''    meu = {}
    _tubo(meu, (sx, sy), (ex, ey), 2.4 * E, braco)''', '''    _tubo(meu, (sx, sy), (ex, ey), 2.4 * E, braco)''')

# ── chave: na forma Mugetsu a fisica do pano/cabelo anda em passos de 0.5
#    (bem menos desenhos diferentes; o fogo e a aura escondem a diferenca) ──
troca('''def _chave(p):
    def r(k, v):
        if k == 'pt':
            return round(v * 8) / 8.0
        if k in ('capa', 'cabelo', 'lift', 'sobe'):
            return round(v * 4) / 4.0            # fisica: passos de 0.25''', '''def _chave(p):
    passo_f = 2.0 if p.get('mugetsu') else 4.0

    def r(k, v):
        if k == 'pt':
            return round(v * 8) / 8.0
        if k in ('capa', 'cabelo', 'lift', 'sobe'):
            return round(v * passo_f) / passo_f  # fisica: passos de 0.25 (Mugetsu: 0.5)''')
troca('''        q['brilho'] = (round(ciclo / 0.45 * 6) / 6.0) if ciclo < 0.45 else None''',
      '''        q['brilho'] = (round(ciclo / 0.45 * 6) / 6.0) if (ciclo < 0.45 and not b.get('mugetsu')) else None''')
open(p, 'wb').write(s.replace('\n', '\r\n').encode('utf-8'))
print('ok')
