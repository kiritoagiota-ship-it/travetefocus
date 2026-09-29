"""Desenho do Yoru em 3 camadas: caudas do sobretudo (atras), corpo e
cabeca (na frente). O corpo so depende da pose; caudas e cabeca so do vento,
do reiatsu e da ondulacao (poucos estados, guardados prontos)."""
p = r'C:\Users\kirit\travetefocus\app\kirito.py'
c = open(p, encoding='utf-8').read()


def troca(a, b, n=1):
    global c
    assert c.count(a) == n, (a[:70], c.count(a))
    c = c.replace(a, b)


# ── 1) montar por camada ───────────────────────────────────────────
troca('''def montar(p, rapido=False):
    """Pose (dict, em unidades) -> {(x, y) em texels: cor}. rapido=True:
    so o desenho cru (sem luz, cores da forma Mugetsu e contorno) - basta
    para medir o tamanho da pose."""
    px = {}''', '''def _cabeca_no_corpo(p):
    """Quando um braco passa por cima da cabeca, ela vai junto no corpo."""
    m1, m2 = p['m1'], p['m2']
    acima2 = m2 is not None and m2[1] > 10
    frente_erguido = m1 is not None and m1[1] > 4 and p.get('frente1')
    return bool(acima2 or frente_erguido or p.get('mugetsu') or p.get('emote'))


def ancoras(p):
    """(cx, topo_casaco, cab_x, cab_ty) em texels para a pose (sem a fisica
    da cabeca): onde as camadas das caudas e da cabeca se encaixam."""
    dx, dy = _meia(p['dx']), _meia(p['dy'])
    hip_y = _PES + _alt_pernas(p) + dy
    incl = int(round(p.get('incl', 0) or 0))
    cx = _t(_X0 + dx + 6.5)
    hy = _t(hip_y)
    return (cx, hy + 6, cx + _GOLA[0] - _CAB_PESCOCO[0] + 4 * incl, hy + _GOLA[1] + _CAB_PESCOCO[1])


def montar(p, rapido=False, camada=None):
    """Pose (dict, em unidades) -> {(x, y) em texels: cor}. rapido=True:
    so o desenho cru (sem luz, cores da forma Mugetsu e contorno) - basta
    para medir o tamanho da pose. camada: None = tudo junto; 'corpo' = sem
    as caudas (e sem a cabeca, se ela nao precisar ir junto); 'cauda' = so
    as caudas, a partir de (cx, topo_casaco); 'cabeca' = so a cabeca, a
    partir de (cab_x, cab_ty)."""
    px = {}''')
troca('''    def mao(anc, m):
        return (int(round(anc[0] + R * m[0])), int(round(anc[1] + R * m[1])))

    if mugetsu:
        cb_q, sobe_q''', '''    def mao(anc, m):
        return (int(round(anc[0] + R * m[0])), int(round(anc[1] + R * m[1])))

    chao = _PES * R
    topo_casaco = hy + 6
    if camada == 'cauda':
        _casaco5(px, 0, 0, chao - topo_casaco, p['capa'], p['lift'], fase, saia, 'tras')
        return px if rapido else _contorno(px, False, None, None)
    if camada == 'cabeca':
        _cabeca5(px, p['olhos'], 0, 0, cb, sobe, fase)
        if sobe > 0.3:
            _espetos5(px, 0, 0, cb, sobe, fase)
        return px if rapido else _contorno(px, False, None, -47)
    cab_junto = camada is None or _cabeca_no_corpo(p)
    if camada == 'corpo':                    # a aba da frente fica parada nesta camada
        p = dict(p, capa=0.0, lift=0.0)
        fase = 0.0

    if mugetsu:
        cb_q, sobe_q''')
troca('''    if sobe > 0.3:
        _espetos5(px, cab_x, cab_ty, cb, sobe, fase)
    if ergue2 and not acima2:''', '''    if sobe > 0.3 and cab_junto:
        _espetos5(px, cab_x, cab_ty, cb, sobe, fase)
    if ergue2 and not acima2:''')
troca('''    chao = _PES * R
    topo_casaco = hy + 6
    if mugetsu:
        _casaco3(px, base + 1.5, hip_y - 1.2, p['capa'], p['lift'], fase, saia, 'tras', True)
    else:
        _casaco5(px, cx, topo_casaco, chao, p['capa'], p['lift'], fase, saia, 'tras')''', '''    if mugetsu:
        _casaco3(px, base + 1.5, hip_y - 1.2, p['capa'], p['lift'], fase, saia, 'tras', True)
    elif camada is None:
        _casaco5(px, cx, topo_casaco, chao, p['capa'], p['lift'], fase, saia, 'tras')''')
troca('''    _cabeca5(px, p['olhos'], cab_x, cab_ty, cb, sobe, fase)
    if acima2:''', '''    if cab_junto:
        _cabeca5(px, p['olhos'], cab_x, cab_ty, cb, sobe, fase)
    if acima2:''')
# o contorno vira funcao (cada camada tem o seu)
a = c.index('''    # contorno de 1 texel: escuro; ciano so como luz de fundo, do lado de
    # tras e em cima (roxo na forma Mugetsu)
    aro = 'o' if mugetsu else 'O'
    fonte = [q for q, ch in px.items() if ch not in _SEM_CONTORNO]''')
b = c.index('    px.update(novos)\n    return px', a)
corpo_contorno = c[a:b]
c = c[:a] + '''    # no corpo sem as caudas, a borda de tras das pernas fica escura (as
    # caudas cobrem ali); o ciano so em cima do quadril
    return _contorno(px, mugetsu, (hy + 5) if camada == 'corpo' else None, None)


def _contorno(px, mugetsu, luz_acima=None, sem_abaixo=None):
    """Contorno de 1 texel: escuro; ciano so como luz de fundo, do lado de
    tras e em cima (roxo na forma Mugetsu). luz_acima: so ha luz de fundo
    acima dessa linha. sem_abaixo: nao contorna abaixo dessa linha (o
    pescoco da cabeca encaixa na gola sem risco escuro)."""
''' + corpo_contorno.split('\n', 2)[2].replace('\n    for q in (esq | cima | resto):\n        if q not in novos:\n            novos[q] = \'N\'\n',
                                            "\n    for q in (esq | cima | resto):\n        if q not in novos:\n            novos[q] = 'N'\n") + '''    if luz_acima is not None:
        for q, ch in novos.items():
            if ch == aro and q[1] < luz_acima:
                novos[q] = 'N'
    if sem_abaixo is not None:
        novos = {q: ch for q, ch in novos.items() if q[1] > sem_abaixo}
''' + c[b:]

# ── 2) imagem de uma camada (cache proprio) ─────────────────────────
troca('''def _bytes(p):''', '''_CAM = OrderedDict()       # (camada, chave) -> (bytes, recorte relativo)
_CAM_MAX = 900


def _rasteriza(px):
    """{(x, y): cor} -> (bytes RGBA, (x0, y0, w, h)) do recorte."""
    if not px:
        return bytes(4), (0, 0, 1, 1)
    xs = [q[0] for q in px]
    ys = [q[1] for q in px]
    X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = X1 - X0 + 1, Y1 - Y0 + 1
    idx = bytearray(w * h)
    cod = _COD
    for (x, y), c in px.items():
        idx[(y - Y0) * w + (x - X0)] = cod[c]
    buf = bytearray(w * h * 4)
    buf[0::4] = idx.translate(_TAB[0])
    buf[1::4] = idx.translate(_TAB[1])
    buf[2::4] = idx.translate(_TAB[2])
    buf[3::4] = idx.translate(_TAB[3])
    return bytes(buf), (X0, Y0, w, h)


_FISICA = ('capa', 'cabelo', 'lift', 'fase', 'hx', 'hy', 'sobe', 'cresce')


def chave_camadas(q):
    """As 3 chaves (corpo, cauda, cabeca) da pose composta q (com fisica).
    O corpo nao depende da fisica; a cauda e a cabeca so dela."""
    q4 = lambda v: round((v or 0.0) * 4) / 4.0
    corpo = tuple(kv for kv in _chave(q) if kv[0] not in _FISICA)
    cx, topo, cab_x, cab_ty = ancoras(q)
    cauda = ('cauda', q4(q['capa']), q4(q['lift']), round(q.get('fase', 0.0) or 0.0, 3),
             round(q.get('saia', 1.0), 2), _PES * R - topo)
    cabeca = None if _cabeca_no_corpo(q) else (
        'cabeca', q['olhos'], q4(q['cabelo']), q4(q.get('sobe', 0.0)), round(q.get('fase', 0.0) or 0.0, 3))
    return corpo, cauda, cabeca


def imagem_camada(q, qual, chave):
    """(bytes, recorte relativo) da camada `qual` da pose q, com cache."""
    k = (qual, chave)
    item = _CAM.get(k)
    if item is not None:
        _CAM.move_to_end(k)
        return item
    item = _rasteriza(montar(q, camada=qual))
    _CAM[k] = item
    while len(_CAM) > _CAM_MAX:
        _CAM.popitem(last=False)
    return item


_TEXC = OrderedDict()
_TEXC_MAX = 260


def textura_camada(q, qual, chave, silhueta=False, xadrez=False):
    """Texture da camada (e o recorte relativo)."""
    k = (qual, chave, silhueta, xadrez)
    tex = _TEXC.get(k)
    dados, rec = imagem_camada(q, qual, chave)
    if tex is not None:
        _TEXC.move_to_end(k)
        return tex, rec
    tex = _criar_textura(dados, rec, silhueta, xadrez)
    _TEXC[k] = tex
    while len(_TEXC) > _TEXC_MAX:
        _TEXC.popitem(last=False)
    return tex, rec


def _bytes(p):''')
# a criacao da textura vira funcao (usada pelas camadas e pela pose inteira)
troca('''    w, h = rec[2], rec[3]
    if silhueta:                         # branco com o alpha do boneco (tingido por Color)''',
      '''    tex = _criar_textura(dados, rec, silhueta, xadrez)
    _TEX[chave] = tex
    while len(_TEX) > _TEX_MAX:
        _TEX.popitem(last=False)
    return tex, rec


def _criar_textura(dados, rec, silhueta=False, xadrez=False):
    w, h = rec[2], rec[3]
    if silhueta:                         # branco com o alpha do boneco (tingido por Color)''')
troca('''    tex.add_reload_observer(
        lambda t, d=dados: t.blit_buffer(d, colorfmt='rgba', bufferfmt='ubyte'))
    _TEX[chave] = tex
    while len(_TEX) > _TEX_MAX:
        _TEX.popitem(last=False)
    return tex, rec''', '''    tex.add_reload_observer(
        lambda t, d=dados: t.blit_buffer(d, colorfmt='rgba', bufferfmt='ubyte'))
    return tex''')

# ── 3) widget: 3 retangulos (e 3 silhuetas) ────────────────────────
troca('''            Color(1, 1, 1, 1)
            self._rect = Rectangle(pos=(0, 0), size=(GW * self.ps, GH * self.ps))
            self._cor_clarao = Color(0.85, 0.97, 1, 0)
            self._rect_clarao = Rectangle(pos=(0, 0), size=(0, 0))''', '''            Color(1, 1, 1, 1)
            self._rect_cauda = Rectangle(pos=(0, 0), size=(0, 0))
            self._rect = Rectangle(pos=(0, 0), size=(GW * self.ps, GH * self.ps))
            self._rect_cab = Rectangle(pos=(0, 0), size=(0, 0))
            self._cor_clarao = Color(0.85, 0.97, 1, 0)
            self._rect_clarao_cauda = Rectangle(pos=(0, 0), size=(0, 0))
            self._rect_clarao = Rectangle(pos=(0, 0), size=(0, 0))
            self._rect_clarao_cab = Rectangle(pos=(0, 0), size=(0, 0))''')
troca('''    def _desenhar(self, forcar=False):
        try:
            self._pose = self._composta()
            chave = (_chave(self._pose), self.espelhar)
            if chave == self._ult_chave and not forcar:
                return
            self._ult_chave = chave
            tex, rec = _textura(self._pose)
            _no_retangulo(self._rect, tex, rec, self.ps, self.espelhar)
            if self.clarao > 0:
                tex, rec = _textura(self._pose, silhueta=True)
                _no_retangulo(self._rect_clarao, tex, rec, self.ps, self.espelhar)
            else:
                self._rect_clarao.size = (0, 0)
            self._cor_clarao.a = self.clarao''', '''    def _camadas_da_pose(self, q):
        """[(retangulo, retangulo da silhueta, qual, chave, deslocamento)]"""
        corpo, cauda, cabeca = chave_camadas(q)
        cx, topo, cab_x, cab_ty = ancoras(q)
        out = [(self._rect_cauda, self._rect_clarao_cauda, 'cauda', cauda, (cx, topo)),
               (self._rect, self._rect_clarao, 'corpo', corpo, (0, 0))]
        if cabeca is not None:
            out.append((self._rect_cab, self._rect_clarao_cab, 'cabeca', cabeca,
                        (cab_x + int(q.get('hx', 0) or 0), cab_ty + int(q.get('hy', 0) or 0))))
        else:
            self._rect_cab.size = (0, 0)
            self._rect_clarao_cab.size = (0, 0)
        return out

    def _desenhar(self, forcar=False):
        try:
            self._pose = self._composta()
            if self._pose.get('mugetsu'):
                # forma Mugetsu: ainda num desenho so (sera refeita)
                chave = (_chave(self._pose), self.espelhar)
                if chave == self._ult_chave and not forcar:
                    return
                self._ult_chave = chave
                for r in (self._rect_cauda, self._rect_cab, self._rect_clarao_cauda, self._rect_clarao_cab):
                    r.size = (0, 0)
                tex, rec = _textura(self._pose)
                _no_retangulo(self._rect, tex, rec, self.ps, self.espelhar)
                if self.clarao > 0:
                    tex, rec = _textura(self._pose, silhueta=True)
                    _no_retangulo(self._rect_clarao, tex, rec, self.ps, self.espelhar)
                else:
                    self._rect_clarao.size = (0, 0)
            else:
                camadas = self._camadas_da_pose(self._pose)
                chave = (tuple((c[3], c[4]) for c in camadas), self.espelhar, self.clarao > 0)
                if chave == self._ult_chave and not forcar:
                    return
                self._ult_chave = chave
                for rect, rect_s, qual, ch, (ox, oy) in camadas:
                    tex, rec = textura_camada(self._pose, qual, ch)
                    rec2 = (rec[0] + ox, rec[1] + oy, rec[2], rec[3])
                    _no_retangulo(rect, tex, rec2, self.ps, self.espelhar)
                    if self.clarao > 0:
                        tex, rec = textura_camada(self._pose, qual, ch, silhueta=True)
                        _no_retangulo(rect_s, tex, rec2, self.ps, self.espelhar)
                    else:
                        rect_s.size = (0, 0)
            self._cor_clarao.a = self.clarao''')
# fantasma: silhueta pontilhada de cada camada
troca('''                cor_sil = Color(cor[0], cor[1], cor[2], alfa)
                tex, rec = _textura(self._pose, silhueta=True, xadrez=True)
                _no_retangulo(Rectangle(), tex, rec, self.ps, self.espelhar)''', '''                cor_sil = Color(cor[0], cor[1], cor[2], alfa)
                if self._pose.get('mugetsu'):
                    tex, rec = _textura(self._pose, silhueta=True, xadrez=True)
                    _no_retangulo(Rectangle(), tex, rec, self.ps, self.espelhar)
                else:
                    for _r, _s, qual, ch, (ox, oy) in self._camadas_da_pose(self._pose):
                        tex, rec = textura_camada(self._pose, qual, ch, silhueta=True, xadrez=True)
                        _no_retangulo(Rectangle(), tex, (rec[0] + ox, rec[1] + oy, rec[2], rec[3]),
                                      self.ps, self.espelhar)''')
# a lamina nao atrasa mais (cada angulo seria um corpo novo); o brilho so no parado
troca('''        for i, ch in ((1, 'a1'), (2, 'a2')):
            m = self._m_a[i]
            if m is not None and b[ch] is not None:
                q[ch] = b[ch] + max(-8.0, min(8.0, round(m.x - b[ch])))''', '''        # (as laminas nao atrasam: o corpo e desenhado uma vez por pose)''')
troca('''        q['brilho'] = (round(ciclo / 0.45 * 6) / 6.0) if (ciclo < 0.45 and not b.get('mugetsu')) else None''',
      '''        q['brilho'] = (round(ciclo / 0.45 * 6) / 6.0) if (ciclo < 0.45 and self._loop
                                                            and not b.get('mugetsu')) else None''')
open(p, 'w', encoding='utf-8', newline='\r\n').write(c)
print('ok')
