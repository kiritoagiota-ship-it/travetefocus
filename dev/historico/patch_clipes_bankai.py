"""O Bankai deixa de ser 6 desenhos parados (que trocavam seco) e vira o
BONECO ARTICULADO da referencia (dev/bankai_rig.py): clipes CONTINUOS a 30
quadros/s (idle flutuando, nasce, carga, carga_segura, corte, fim) guardados
em bankai/clipes.bin (1 byte por pixel + paleta). KiritoPixel.mostrar_clipe
toca um clipe (em loop ou uma vez, com aviso por quadro e no fim); mao,
ponta da espada, extensao, rastro, impacto e recorte vem de cada quadro."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'kirito.py'), [
    ("""# ═══════════════════════════════════════════════════════════════════
#  DESENHOS PRONTOS (Bankai copiado pixel a pixel da referencia)
# ═══════════════════════════════════════════════════════════════════
_DESENHOS = {}


def desenho_dados(nome):
    \"\"\"(quadros, silhuetas, meta) do desenho pronto `nome` (bankai/nome.png).\"\"\"
    d = _DESENHOS.get(nome)
    if d is not None:
        return d
    import bankai_desenhos as _BD
    from kivy.core.image import Image as _CoreImage
    meta = _BD.POSES[nome]
    base = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'bankai')
    w, h = meta['tam']
    n = meta['n']
    tiras = []
    for arq in (nome + '.png', nome + '_sil.png'):
        tex = _CoreImage(_os.path.join(base, arq)).texture
        tex.mag_filter = tex.min_filter = 'nearest'
        tiras.append([tex.get_region(i * w, 0, w, h) for i in range(n)])
    d = (tiras[0], tiras[1], meta)
    _DESENHOS[nome] = d
    return d
""", """# ═══════════════════════════════════════════════════════════════════
#  CLIPES DO BANKAI (boneco articulado feito com o desenho da referencia,
#  gerado no PC por dev/bankai_rig.py; aqui so toca os quadros prontos)
# ═══════════════════════════════════════════════════════════════════
_CLIPES = {}               # 'cab' -> cabecalho; 'dados' -> bytes; 'tab'/'sil' -> tabelas
_CLIPE_TEX = OrderedDict()
_CLIPE_TEX_MAX = 150


def clipes_dados():
    \"\"\"Cabecalho de bankai/clipes.bin (le uma vez).\"\"\"
    if 'cab' in _CLIPES:
        return _CLIPES['cab']
    caminho = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'bankai', 'clipes.bin')
    with open(caminho, 'rb') as f:
        dados = f.read()
    if dados[:4] != b'BK01':
        raise ValueError('clipes.bin de outra versao')
    n = int.from_bytes(dados[4:8], 'little')
    cab = _json.loads(_zlib.decompress(dados[8:8 + n]).decode('utf-8'))
    _CLIPES['base'] = 8 + n
    _CLIPES['dados'] = dados
    pal = cab['paleta']
    tabs = [bytearray(256) for _ in range(4)]
    for i, c in enumerate(pal):
        for k in range(4):
            tabs[k][i] = c[k]
    _CLIPES['tab'] = [bytes(t) for t in tabs]
    sil = bytearray(256)
    for i in range(1, len(pal)):
        sil[i] = 255
    _CLIPES['sil'] = bytes(sil)
    _CLIPES['cab'] = cab
    return cab


def quadro_clipe(nome, i, silhueta=False):
    \"\"\"(textura, caixa (x0, y0, w, h) na tela do clipe, mao, ponta) do
    quadro i do clipe `nome`.\"\"\"
    cab = clipes_dados()
    pos, tam, caixa_q, mao, ponta = cab['clipes'][nome]['quadros'][i]
    ch = (nome, i, silhueta)
    tex = _CLIPE_TEX.get(ch)
    if tex is None:
        ini = _CLIPES['base'] + pos
        idx = _zlib.decompress(_CLIPES['dados'][ini:ini + tam])
        buf = bytearray(len(idx) * 4)
        if silhueta:
            s = idx.translate(_CLIPES['sil'])
            buf[0::4] = s
            buf[1::4] = s
            buf[2::4] = s
            buf[3::4] = s
        else:
            t = _CLIPES['tab']
            buf[0::4] = idx.translate(t[0])
            buf[1::4] = idx.translate(t[1])
            buf[2::4] = idx.translate(t[2])
            buf[3::4] = idx.translate(t[3])
        w, h = caixa_q[2], caixa_q[3]
        tex = Texture.create(size=(w, h), colorfmt='rgba')
        tex.mag_filter = tex.min_filter = 'nearest'
        tex.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
        tex.flip_vertical()                     # as linhas vem de cima para baixo
        _CLIPE_TEX[ch] = tex
        while len(_CLIPE_TEX) > _CLIPE_TEX_MAX:
            _CLIPE_TEX.popitem(last=False)
    else:
        _CLIPE_TEX.move_to_end(ch)
    return tex, caixa_q, mao, ponta
"""),
    ("""        self._desenho = None              # nome do desenho pronto (None = boneco montado)""",
     """        self._desenho = None              # clipe do Bankai tocando (None = boneco montado)
        self._clipe_t = 0.0
        self._clipe_loop = True
        self._clipe_fim = None
        self._clipe_cb = None
        self._clipe_ult = -1"""),
    ("""    def _local_desenho(self, sx, sy):
        \"\"\"Pixel (sx, sy) do desenho pronto (y para baixo) -> px locais.\"\"\"
        meta = desenho_dados(self._desenho)[2]
        te = self.ps / float(R)
        ax, ay = self.ancora_local()
        qx, qy = meta['quadril']
        dx = (sx + 0.5 - qx) * te
        return (ax - dx if self.espelhar else ax + dx), ay + (qy - sy - 0.5) * te

    def corpo_desenho(self):
        \"\"\"(x0, x1, y_pe, altura) da parte firme do desenho pronto, no pai.\"\"\"
        meta = desenho_dados(self._desenho)[2]
        cx, meia = meta['corpo']
        qx, qy = meta['quadril']
        bx0, by0, bx1, by1 = meta['caixa']
        xa, ya = self._local_desenho(cx - meia * 1.8, by1)
        xb, yb = self._local_desenho(cx + meia * 1.8, by0)
        return (self.x + min(xa, xb), self.x + max(xa, xb), self.y + ya, yb - ya)

    def mao_local(self, qual=1, p=None):
        if p is None and self._desenho is not None:
            return self._local_desenho(*desenho_dados(self._desenho)[2]['mao'])""",
     """    def _local_desenho(self, sx, sy):
        \"\"\"Pixel (sx, sy) da tela do clipe (y para baixo) -> px locais.\"\"\"
        cab = clipes_dados()
        te = self.ps / float(R)
        ax, ay = self.ancora_local()
        qx, qy = cab['quadril']
        dx = (sx - qx) * te
        return (ax - dx if self.espelhar else ax + dx), ay + (qy - sy) * te

    def _quadro_atual(self):
        cab = clipes_dados()
        n = len(cab['clipes'][self._desenho]['quadros'])
        i = int(self._clipe_t * cab['fps'])
        return (i % n) if self._clipe_loop else min(i, n - 1)

    def corpo_desenho(self):
        \"\"\"(x0, x1, y_pe, altura) do corpo do Bankai (sem cabelo/espada), no pai.\"\"\"
        cab = clipes_dados()
        qx, qy = cab['quadril']
        xa, ya = self._local_desenho(qx - 14, qy + 60)
        xb, yb = self._local_desenho(qx + 16, qy - 105)
        return (self.x + min(xa, xb), self.x + max(xa, xb), self.y + ya, yb - ya)

    def mao_local(self, qual=1, p=None):
        if p is None and self._desenho is not None:
            mao = quadro_clipe(self._desenho, self._quadro_atual())[2]
            return self._local_desenho(*mao)"""),
    ("""        if p is None and self._desenho is not None:
            lx, ly = self._local_desenho(*desenho_dados(self._desenho)[2]['ponta'])
            return self.x + lx, self.y + ly""",
     """        if p is None and self._desenho is not None:
            lx, ly = self._local_desenho(*quadro_clipe(self._desenho, self._quadro_atual())[3])
            return self.x + lx, self.y + ly"""),
    ("""        if p is None and self._desenho is not None:
            meta = desenho_dados(self._desenho)[2]
            te = self.ps / float(R)
            qx, qy = meta['quadril']
            bx0, by0, bx1, by1 = meta['caixa']
            esq, dir_ = (qx - bx0) * te, (bx1 + 1 - qx) * te
            if self.espelhar:
                esq, dir_ = dir_, esq
            return esq, (by1 + 1 - qy) * te, dir_, (qy - by0) * te""",
     """        if p is None and self._desenho is not None:
            cab = clipes_dados()
            te = self.ps / float(R)
            qx, qy = cab['quadril']
            x0, y0, w, h = quadro_clipe(self._desenho, self._quadro_atual())[1]
            esq, dir_ = (qx - x0) * te, (x0 + w - qx) * te
            if self.espelhar:
                esq, dir_ = dir_, esq
            return esq, (y0 + h - qy) * te, dir_, (qy - y0) * te"""),
    ("""    def mostrar_desenho(self, nome, base=None):
        \"\"\"Mostra o desenho pronto `nome` (tocando os quadros dele) no lugar
        do boneco montado. base = a pose que os efeitos consultam (forma,
        espada acesa).\"\"\"
        self.parar()
        self._desenho = nome
        if base is not None:
            self._base = base
        self._desenhar(forcar=True)""",
     """    def mostrar_clipe(self, nome, loop=True, on_fim=None, on_quadro=None, base=None, t0=0.0):
        \"\"\"Toca o clipe `nome` do Bankai (quadros prontos, 30/s) no lugar do
        boneco montado. loop=False: para no ultimo quadro e chama on_fim.
        on_quadro(i) a cada quadro novo. base = a pose que os efeitos
        consultam (forma, espada acesa). t0 = de onde comeca (s).\"\"\"
        self.parar()
        self._desenho = nome
        self._clipe_t = float(t0)
        self._clipe_loop = loop
        self._clipe_fim = on_fim
        self._clipe_cb = on_quadro
        self._clipe_ult = -1
        if base is not None:
            self._base = base
        self._desenhar(forcar=True)

    def mostrar_desenho(self, nome, base=None):
        self.mostrar_clipe(nome, loop=True, base=base)

    def _avanca_clipe(self, dt):
        \"\"\"Chamado pela fisica (30/s): anda o clipe e avisa quadro/fim.\"\"\"
        if self._desenho is None:
            return
        self._clipe_t += dt
        i = self._quadro_atual()
        if i != self._clipe_ult:
            self._clipe_ult = i
            if self._clipe_cb is not None:
                try:
                    self._clipe_cb(i)
                except Exception as e:
                    print(f"[kirito] clipe quadro: {e}")
        if not self._clipe_loop:
            n = len(clipes_dados()['clipes'][self._desenho]['quadros'])
            if int(self._clipe_t * clipes_dados()['fps']) >= n and self._clipe_fim is not None:
                cb, self._clipe_fim = self._clipe_fim, None
                try:
                    cb()
                except Exception as e:
                    print(f"[kirito] clipe fim: {e}")"""),
])
print('ok 1')
