"""Aplica a troca para R=3 no kirito.py (mapas novos, partes redesenhadas,
texturas recortadas)."""
import io, os, re, sys

AQUI = os.path.dirname(__file__)
ALVO = r'C:\Users\kirit\travetefocus\app\kirito.py'
raw = open(ALVO, 'rb').read()
crlf = b'\r\n' in raw
src = raw.decode('utf-8').replace('\r\n', '\n')


def ler(n):
    return open(os.path.join(AQUI, n), encoding='utf-8').read()


mapas = ler('mapas_src.txt')


def corpo_mapa(nome):
    m = re.search(r'^%s = _m\(\[\n(.*?)\n\]\)' % re.escape(nome), mapas, re.S | re.M)
    return m.group(1)


def troca_bloco(ini, fim, novo, incluir_fim=False):
    """Troca do inicio da linha que comeca com `ini` ate antes da linha que
    comeca com `fim`."""
    global src
    a = src.index(ini)
    b = src.index(fim, a + 1)
    if incluir_fim:
        b = src.index('\n', b) + 1
    src = src[:a] + novo + src[b:]


def troca(velho, novo, n=1):
    global src
    assert src.count(velho) == n, (velho[:60], src.count(velho))
    src = src.replace(velho, novo)


# ── paleta ─────────────────────────────────────────────────────────
troca("""    'b': (0.17, 0.18, 0.26, 1),                                  # bota: meio-tom
}""", """    'b': (0.17, 0.18, 0.26, 1),                                  # bota: meio-tom
    # detalhe fino (3 texels por unidade)
    't': (0.62, 0.44, 0.50, 1),                                  # pele: sombra funda (puxa para o vinho)
    'i': (0.84, 0.87, 0.96, 1),                                  # branco do olho (susto)
    '3': (0.33, 0.43, 0.70, 1),                                  # iris: meio-tom
    'U': (0.70, 0.82, 1.00, 1),                                  # cabelo: reflexo
    '%': (0.50, 0.58, 0.76, 1),                                  # couro: reflexo (bota, luva)
}""")
troca("""'2': 'D', '4': 'D', '7': 'D', 'e': 'V', 'n': 'L', 'K': 'D', 'Z': 'o', 'p': 'd', 'b': 'D'}""",
      """'2': 'D', '4': 'D', '7': 'D', 'e': 'V', 'n': 'L', 'K': 'D', 'Z': 'o', 'p': 'd', 'b': 'D',
           '3': 'V', 'm': 'o', 'i': 'd', 'U': 'o', '%': 'd'}""")
troca("_CORPO_M = set('HhSsDdVJIeT')", "_CORPO_M = set('HhSsDdVJIeTt')")
troca("""           'M': 'g', 'G': 'Q', 'D': 'd', 'd': 'o', '2': 'C', '4': 'C', '7': 'P', 'J': 'H', 'I': 'h'}""",
      """           'M': 'g', 'G': 'Q', 'D': 'd', 'd': 'o', '2': 'C', '4': 'C', '7': 'P', 'J': 'H', 'I': 'h',
           'U': 'Q', '%': 'Q'}""")
troca("_CORPO = set('CcAqGPBMSsHhE24JIen7')", "_CORPO = set('CcAqGPBMSsHhE24JIen7tU3%bp')")

# ── R=3, mapas de cabeca/tronco e cabelo ───────────────────────────
novo_a = ler('novo_a.txt').replace('@@LADO@@', corpo_mapa('_CAB2')).replace('@@TOR@@', corpo_mapa('_TOR2'))
troca_bloco('# ═══════════════════════════════════════════════════════════════════\n#  MONTAGEM EM DOBRO',
            'def _braco2(', novo_a + '\n\n')
# _braco2 (sem uso) sai
troca_bloco('def _braco2(', 'def _rastro2(', '')
# espadas, bainha e cabo
troca_bloco('def _katana2(', 'def _meia(', ler('novo_c.txt') + '\n\n')
# perna
troca_bloco('def _perna3(', '# ── vistas para o giro', ler('novo_d.txt') + '\n\n')
# vistas de frente/costas
novo_e = (ler('novo_e.txt').replace('@@FRENTE@@', corpo_mapa('_CAB_FRENTE'))
          .replace('@@COSTAS@@', corpo_mapa('_CAB_COSTAS')).replace('@@TORC@@', corpo_mapa('_TOR_COSTAS')))
troca_bloco('# ── vistas para o giro', '\n\ndef _pernas3(', novo_e.rstrip('\n'))
# bainha das costas, braco e mao
troca_bloco('def _bainha_costas(', 'def montar(', ler('novo_f.txt') + '\n\n')

# ── sobretudo: medidas em texels ───────────────────────────────────
troca("""    mv = int(fase * 8)
    top = _t(y0) + R - 1

    def dobra(x, kk):
        return (x + kk + mv) % 7""", """    mv = int(fase * 8 * E)
    top = _t(y0) + R - 1

    def dobra(x, kk):
        return (x + kk + mv) % 10""")
troca("""        def cor(x, y, a, b, kk, total):
            if kk >= total - 2:
                return 'c' if kk == total - 2 else '2'
            if x == b:
                return 'c'
            if x == a:
                return 'Z'                         # costura ciano na abertura
            if x == a + 1:
                return 'q'                         # forro
            d = dobra(x, kk)
            return '2' if d == 0 else ('A' if d == 1 else 'C')""", """        def cor(x, y, a, b, kk, total):
            if kk >= total - 2:
                return 'c' if kk == total - 2 else '2'
            if x == b:
                return 'c'
            if x == a:
                return 'Z'                         # costura ciano na abertura
            if x <= a + 2:
                return 'q'                         # forro
            d = dobra(x, kk)
            return '2' if d == 0 else ('A' if d in (1, 2) else 'C')""")
troca("""    def cor_tras(x, y, a, b, kk, total):
        if kk >= total - 2:
            return 'Z' if kk == total - 2 else '2'   # barra com friso ciano
        if x == a:
            return 'c'
        if kk >= n1 and x >= b - 1:
            return 'q'                             # forro aparecendo no vao
        d = dobra(x, kk)
        return '2' if d == 0 else 'C'
    def cor_int(x, y, a, b, kk, total):
        if kk >= total - 2:
            return 'Z' if kk == total - 2 else '2'
        if x <= a + 1:
            return 'q'                             # forro da cauda de dentro
        return '2' if dobra(x, kk) == 0 else 'C'""", """    def cor_tras(x, y, a, b, kk, total):
        if kk >= total - 2:
            return 'Z' if kk == total - 2 else '2'   # barra com friso ciano
        if x == a:
            return 'c'
        if x == a + 1:
            return 'A'
        if kk >= n1 and x >= b - 2:
            return 'q'                             # forro aparecendo no vao
        d = dobra(x, kk)
        return '2' if d == 0 else ('A' if d == 1 else 'C')

    def cor_int(x, y, a, b, kk, total):
        if kk >= total - 2:
            return 'Z' if kk == total - 2 else '2'
        if x <= a + 2:
            return 'q'                             # forro da cauda de dentro
        return '2' if dobra(x, kk) == 0 else 'C'""")

# ── montar ─────────────────────────────────────────────────────────
troca("""        desl = 2 * incl if r < 6 else (incl if r < 10 else 0)""",
      """        desl = R * incl if r < 3 * R else (int(round(R * incl / 2.0)) if r < 5 * R else 0)""")
troca("""        for i in range(1, 6):
            if (q[0] + vx * i, q[1] + vy * i) in px:""", """        for i in range(1, 2 * R + 2):
            if (q[0] + vx * i, q[1] + vy * i) in px:""")
troca("""        # olhando mais 5 texels na mesma direcao ainda ha boneco""",
      """        # olhando mais uns texels na mesma direcao ainda ha boneco""")

# ── imagem recortada (so a caixa do desenho: bem menos memoria) ────
troca_bloco('def _gerar_imagem(p):', 'def _bytes(p):', '''def _gerar_imagem(p):
    ch = _chave(p)
    item = _CACHE.get(ch)
    if item is not None:
        _CACHE.move_to_end(ch)
        return ch, item
    px = montar(p)
    x0 = y0 = X0 = Y0 = 10 ** 6
    x1 = y1 = X1 = Y1 = -10 ** 6
    for (x, y), c in px.items():
        if 0 <= x < TW and 0 <= y < TH:
            X0, X1 = min(X0, x), max(X1, x)
            Y0, Y1 = min(Y0, y), max(Y1, y)
            if c not in 'xX':                 # rastro nao conta para o enquadramento
                x0, x1 = min(x0, x), max(x1, x)
                y0, y1 = min(y0, y), max(y1, y)
    if X1 >= X0:
        w, h = X1 - X0 + 1, Y1 - Y0 + 1
        buf = bytearray(w * h * 4)
        for (x, y), c in px.items():
            if X0 <= x <= X1 and Y0 <= y <= Y1:
                i = ((y - Y0) * w + (x - X0)) * 4
                buf[i:i + 4] = _RGBA[c]
        recorte = (X0, Y0, w, h)
    else:
        buf, recorte = bytearray(4), (0, 0, 1, 1)
    # caixa em unidades da grade (as cenas trabalham nelas)
    cx = ((x0 / float(R), y0 / float(R), (x1 + 1) / float(R) - 1, (y1 + 1) / float(R) - 1)
          if x1 >= x0 else (_X0, _PES, _X0 + 12, _PES + 26))
    borda = bordas(px) if p.get('mugetsu') else None
    item = (bytes(buf), cx, borda, recorte)
    _CACHE[ch] = item
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)
    return ch, item


''')
troca_bloco('def _textura(p, silhueta=False, xadrez=False):', '# ═══', '''def _textura(p, silhueta=False, xadrez=False):
    """Pose -> (Texture so do recorte do desenho, recorte em texels). 1
    retangulo por quadro, bem leve no celular; o espelho e por tex_coords."""
    ch, item = _gerar_imagem(p)
    dados, rec = item[0], item[3]
    chave = (ch, silhueta, xadrez)
    tex = _TEX.get(chave)
    if tex is not None:
        _TEX.move_to_end(chave)
        return tex, rec
    w, h = rec[2], rec[3]
    if silhueta:                         # branco com o alpha do boneco (tingido por Color)
        b = bytearray(dados)
        for i in range(0, len(b), 4):
            if b[i + 3]:
                b[i] = b[i + 1] = b[i + 2] = 255
                if xadrez:                   # afterimage: so metade dos pixels (pixel art)
                    j = i // 4
                    if ((rec[0] + j % w) + (rec[1] + j // w)) % 2:
                        b[i + 3] = 0
        dados = bytes(b)
    tex = Texture.create(size=(w, h), colorfmt='rgba')
    tex.mag_filter = 'nearest'
    tex.min_filter = 'nearest'
    tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
    tex.add_reload_observer(
        lambda t, d=dados: t.blit_buffer(d, colorfmt='rgba', bufferfmt='ubyte'))
    _TEX[chave] = tex
    while len(_TEX) > _TEX_MAX:
        _TEX.popitem(last=False)
    return tex, rec


def _no_retangulo(rect, tex, rec, ps, espelhar):
    """Poe a textura recortada no lugar certo do quadro do boneco."""
    te = ps / float(R)
    x0, y0, w, h = rec
    if espelhar:
        x0 = TW - x0 - w
    rect.texture = tex
    rect.pos = (x0 * te, y0 * te)
    rect.size = (w * te, h * te)
    rect.tex_coords = _TC_ESPELHO if espelhar else _TC_NORMAL


''')
troca("""            self._rect.texture = _textura(self._pose)
            self._rect.tex_coords = _TC_ESPELHO if self.espelhar else _TC_NORMAL
            if self.clarao > 0:
                self._rect_clarao.texture = _textura(self._pose, silhueta=True)
                self._rect_clarao.tex_coords = self._rect.tex_coords
                self._rect_clarao.size = self._rect.size""", """            tex, rec = _textura(self._pose)
            _no_retangulo(self._rect, tex, rec, self.ps, self.espelhar)
            if self.clarao > 0:
                tex, rec = _textura(self._pose, silhueta=True)
                _no_retangulo(self._rect_clarao, tex, rec, self.ps, self.espelhar)""")
troca("""                Rectangle(pos=(0, 0), size=self.size, texture=_textura(self._pose, silhueta=True, xadrez=True),
                          tex_coords=_TC_ESPELHO if self.espelhar else _TC_NORMAL)""",
      """                tex, rec = _textura(self._pose, silhueta=True, xadrez=True)
                _no_retangulo(Rectangle(), tex, rec, self.ps, self.espelhar)""")
troca("""        self.ps = max(2, int(ps) - int(ps) % 2)      # texel = ps/2 (pixels todos iguais)""",
      """        self.ps = max(R, int(ps) - int(ps) % R)      # texel = ps/R (pixels todos iguais)""")
troca("_CACHE_MAX = 500", "_CACHE_MAX = 600")

open(ALVO, 'wb').write((src.replace('\n', '\r\n') if crlf else src).encode('utf-8'))
print('ok', len(src.splitlines()), 'linhas')
