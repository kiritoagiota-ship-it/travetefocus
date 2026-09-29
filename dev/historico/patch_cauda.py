pk = r'C:\Users\kirit\travetefocus\app\kirito.py'
k = open(pk, encoding='utf-8').read()


def troca(a, b, n=1):
    global k
    assert k.count(a) == n, (a[:70], k.count(a))
    k = k.replace(a, b)


# caudas sem o chao: o widget corta na hora de mostrar
troca("""    if camada == 'cauda':
        _casaco5(px, 0, 0, chao - topo_casaco, p['capa'], p['lift'], fase, saia, 'tras')""",
      """    if camada == 'cauda':                     # sem cortar no chao (o widget corta)
        _casaco5(px, 0, 0, -100000, p['capa'], p['lift'], fase, saia, 'tras')""")
troca("""    cauda = ('cauda', q4(q['capa']), q4(q['lift']), round(q.get('fase', 0.0) or 0.0, 3),
             round(q.get('saia', 1.0), 2), _PES * R - topo)""",
      """    cauda = ('cauda', q4(q['capa']), q4(q['lift']), round(q.get('fase', 0.0) or 0.0, 3),
             q4(q.get('saia', 1.0)))""")
troca("""    q4 = lambda v: round(v * 4) / 4.0
    capa, lift, saia = q4(capa), q4(lift), round(saia, 2)
    _parte(px, ('casaco5', parte""", """    q4 = lambda v: round(v * 4) / 4.0
    capa, lift, saia = q4(capa), q4(lift), q4(saia)
    _parte(px, ('casaco5', parte""")
# corte no chao na hora de mostrar
troca('''def _no_retangulo(rect, tex, rec, ps, espelhar):
    """Poe a textura recortada no lugar certo do quadro do boneco."""
    te = ps / float(R)
    x0, y0, w, h = rec
    if espelhar:
        x0 = TW - x0 - w
    rect.texture = tex
    rect.pos = (x0 * te, y0 * te)
    rect.size = (w * te, h * te)
    rect.tex_coords = _TC_ESPELHO if espelhar else _TC_NORMAL''', '''def _no_retangulo(rect, tex, rec, ps, espelhar, chao=None):
    """Poe a textura recortada no lugar certo do quadro do boneco. chao: o
    que ficar abaixo dessa linha (texels) nao aparece (as caudas do
    sobretudo nao atravessam o chao)."""
    te = ps / float(R)
    x0, y0, w, h = rec
    corte = 0
    if chao is not None and y0 < chao:
        corte = min(h, chao - y0)
    if espelhar:
        x0 = TW - x0 - w
    rect.texture = tex
    rect.pos = (x0 * te, (y0 + corte) * te)
    rect.size = (w * te, (h - corte) * te)
    if corte:
        v = corte / float(h)
        rect.tex_coords = (1, v, 0, v, 0, 1, 1, 1) if espelhar else (0, v, 1, v, 1, 1, 0, 1)
    else:
        rect.tex_coords = _TC_ESPELHO if espelhar else _TC_NORMAL''')
troca('''                for rect, rect_s, qual, ch, (ox, oy) in camadas:
                    tex, rec = textura_camada(self._pose, qual, ch)
                    rec2 = (rec[0] + ox, rec[1] + oy, rec[2], rec[3])
                    _no_retangulo(rect, tex, rec2, self.ps, self.espelhar)
                    if self.clarao > 0:
                        tex, rec = textura_camada(self._pose, qual, ch, silhueta=True)
                        _no_retangulo(rect_s, tex, rec2, self.ps, self.espelhar)''', '''                for rect, rect_s, qual, ch, (ox, oy) in camadas:
                    tex, rec = textura_camada(self._pose, qual, ch)
                    rec2 = (rec[0] + ox, rec[1] + oy, rec[2], rec[3])
                    chao = _PES * R if qual == 'cauda' else None
                    _no_retangulo(rect, tex, rec2, self.ps, self.espelhar, chao)
                    if self.clarao > 0:
                        tex, rec = textura_camada(self._pose, qual, ch, silhueta=True)
                        _no_retangulo(rect_s, tex, rec2, self.ps, self.espelhar, chao)''')
troca('''                        tex, rec = textura_camada(self._pose, qual, ch, silhueta=True, xadrez=True)
                        _no_retangulo(Rectangle(), tex, (rec[0] + ox, rec[1] + oy, rec[2], rec[3]),
                                      self.ps, self.espelhar)''', '''                        tex, rec = textura_camada(self._pose, qual, ch, silhueta=True, xadrez=True)
                        _no_retangulo(Rectangle(), tex, (rec[0] + ox, rec[1] + oy, rec[2], rec[3]),
                                      self.ps, self.espelhar, _PES * R if qual == 'cauda' else None)''')
# caixa: a fisica nao conta (a caixa quase nao muda com ela)
troca('''    contorno): as cenas medem muitas poses de uma vez para enquadrar o
    boneco e isso nao pode travar o quadro."""
    ch = _chave(p)''', '''    contorno): as cenas medem muitas poses de uma vez para enquadrar o
    boneco e isso nao pode travar o quadro. A fisica (vento, cabelo) nao
    conta: a caixa quase nao muda com ela."""
    if not p.get('mugetsu'):
        p = dict(p, capa=0.0, cabelo=0.0, lift=0.0, fase=0.0, hx=0, hy=0)
    ch = _chave(p)''')
open(pk, 'w', encoding='utf-8', newline='\r\n').write(k)
print('ok')
