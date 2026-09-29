"""Mugetsu em camadas no montar e no widget."""
pk = r'C:\Users\kirit\travetefocus\app\kirito.py'
k = open(pk, encoding='utf-8').read()


def troca(a, b, n=1):
    global k
    assert k.count(a) == n, (a[:80], k.count(a))
    k = k.replace(a, b)


troca("""    return bool(acima2 or frente_erguido or p.get('mugetsu') or p.get('emote'))""",
      """    return bool(acima2 or frente_erguido or p.get('emote'))""")
troca("""    if camada == 'cauda':                     # sem cortar no chao (o widget corta)
        _casaco5(px, 0, 0, -100000, p['capa'], p['lift'], fase, saia, 'tras')
        return px if rapido else _contorno(px, False, None, None)
    if camada == 'cabeca':
        _cabeca5(px, p['olhos'], 0, 0, cb, sobe, fase)
        if sobe > 0.3:
            _espetos5(px, 0, 0, cb, sobe, fase)
        return px if rapido else _contorno(px, False, None, -47)""",
      """    cresce = round(p.get('cresce', 1.0) or 0.0, 2) if mugetsu else None
    if camada == 'cauda':                     # sem cortar no chao (o widget corta)
        _casaco5(px, 0, 0, -100000, p['capa'], p['lift'], fase, saia, 'tras', mug=mugetsu)
        if rapido:
            return px
        if mugetsu:
            _sombra_mugetsu(px)
        return _contorno(px, mugetsu, None, None)
    if camada == 'cabeca':
        _cabeca5(px, p['olhos'], 0, 0, cb, sobe, fase, cresce)
        if sobe > 0.3:
            _espetos5(px, 0, 0, cb, sobe, fase)
        if rapido:
            return px
        if mugetsu:
            _sombra_mugetsu(px)
        return _contorno(px, mugetsu, None, -47)""")
a = k.index("""    if mugetsu:
        cb_q, sobe_q = round(cb * 4) / 4.0, round(sobe * 4) / 4.0
        cr = round(p.get('cresce', 1.0), 2)
        alto = cab_ty - R * (_PES + 4)""")
b = k.index("\n", k.index("lambda d: _cabelo_longo2(d, 0, 0, cb_q, sobe_q, fase, -alto, cr))", a)) + 1
k = k[:a] + k[b:]
troca("""    if mugetsu:
        _casaco3(px, base + 1.5, hip_y - 1.2, p['capa'], p['lift'], fase, saia, 'tras', True)
    elif camada is None:
        _casaco5(px, cx, topo_casaco, chao, p['capa'], p['lift'], fase, saia, 'tras')""",
      """    if camada is None:
        _casaco5(px, cx, topo_casaco, chao, p['capa'], p['lift'], fase, saia, 'tras', mug=mugetsu)""")
troca("""    if mugetsu:
        _casaco3(px, base + 1.5, hip_y - 1.2, p['capa'], p['lift'], fase, saia, 'frente', True)
    else:
        _casaco5(px, cx, topo_casaco, chao, p['capa'], p['lift'], fase, saia, 'frente')""",
      """    _casaco5(px, cx, topo_casaco, chao, p['capa'], p['lift'], fase, saia, 'frente', mug=mugetsu)""")
troca("""        if mugetsu:
            _ombreira(px, o1[0], o1[1])
""", "")
troca("""    if cab_junto:
        _cabeca5(px, p['olhos'], cab_x, cab_ty, cb, sobe, fase)""", """    if cab_junto:
        _cabeca5(px, p['olhos'], cab_x, cab_ty, cb, sobe, fase, cresce)""")
troca("""    m1 = p['m1']
    ergue = m1 is not None and m1[1] > 4 and not p.get('frente1')

    def _braco_frente():
        if m1 is None:
            return
        h1 = mao(am1, m1)
        _braco5(""", """    if mugetsu:                              # faixas cruzando o peito
        for (xa, ya, xb, yb) in ((-12, 30, 13, 13), (-13, 21, 12, 5)):
            n = max(abs(xb - xa), abs(yb - ya))
            for i in range(n + 1):
                x = cx + li + xa + (xb - xa) * i // n
                y = hy + ya + (yb - ya) * i // n
                for dd, ch in ((0, 'o'), (-1, 'd'), (-2, 'd'), (-3, '&')):
                    q = (x, y + dd)
                    if q in px:
                        px[q] = ch

    m1 = p['m1']
    ergue = m1 is not None and m1[1] > 4 and not p.get('frente1')

    def _braco_frente():
        if m1 is None:
            return
        h1 = mao(am1, m1)
        _braco5(""")
troca("""    if mugetsu:
        for q, ch in list(px.items()):
            if ch in _SOMBRA:
                px[q] = _SOMBRA[ch]
    # no corpo sem as caudas""", """    if mugetsu:
        _sombra_mugetsu(px)
    # no corpo sem as caudas""")
troca("""def _cabeca_no_corpo(p):""", """def _sombra_mugetsu(px):
    \"\"\"A roupa escurece e as linhas ciano viram roxas (o rosto fica claro).\"\"\"
    for q, ch in list(px.items()):
        if ch in _SOMBRA:
            px[q] = _SOMBRA[ch]


def _cabeca_no_corpo(p):""")
troca("""    cauda = ('cauda', q4(q['capa']), q4(q['lift']), round(q.get('fase', 0.0) or 0.0, 3),
             q4(q.get('saia', 1.0)))""", """    mug = bool(q.get('mugetsu'))
    cauda = ('cauda', q4(q['capa']), q4(q['lift']), round(q.get('fase', 0.0) or 0.0, 3),
             q4(q.get('saia', 1.0)), mug)""")
troca("""        'cabeca', q['olhos'], q4(q['cabelo']), q4(q.get('sobe', 0.0)), round(q.get('fase', 0.0) or 0.0, 3))""",
      """        'cabeca', q['olhos'], q4(q['cabelo']), q4(q.get('sobe', 0.0)), round(q.get('fase', 0.0) or 0.0, 3),
        mug, round(q.get('cresce', 1.0) or 0.0, 2) if mug else None)""")
troca("""        if b.get('mugetsu'):
            # forma Mugetsu (ainda num desenho so): menos estados, para os
            # quadros virem prontos do arquivo
            q['hx'] = q['hy'] = 0
            q['fase'] = (int(self._fase * 3) % 3) / 3.0""", "")
a = k.index("""            if self._pose.get('mugetsu'):
                # forma Mugetsu: ainda num desenho so""")
b = k.index("""            else:
                camadas = self._camadas_da_pose(self._pose)""", a)
fim = k.index("""            self._cor_clarao.a = self.clarao""", b)
bloco = k[b:fim].replace("""            else:
                camadas = self._camadas_da_pose(self._pose)""", """            if True:
                camadas = self._camadas_da_pose(self._pose)""", 1)
k = k[:a] + bloco + k[fim:]
troca("""                if self._pose.get('mugetsu'):
                    tex, rec = _textura(self._pose, silhueta=True, xadrez=True)
                    _no_retangulo(Rectangle(), tex, rec, self.ps, self.espelhar)
                else:
                    for _r, _s, qual, ch, (ox, oy) in self._camadas_da_pose(self._pose):""", """                if True:
                    for _r, _s, qual, ch, (ox, oy) in self._camadas_da_pose(self._pose):""")
open(pk, 'w', encoding='utf-8', newline='\r\n').write(k)
print('ok')
