"""KiritoPixel mostra DESENHOS PRONTOS (o Bankai copiado pixel a pixel da
referencia do usuario, app/bankai/pN.png) no lugar do boneco montado:
mostrar_desenho(nome, base) - os quadros da tira tocam sozinhos (cabelo,
casaco e chamas ondulando), com o mesmo tamanho de pixel do Yoru, preso na
ancora (os pes no mesmo chao), espelhado se preciso. Mao, ponta da espada,
extensao, rastro (fantasma), clarao de impacto e recorte funcionam igual.
mostrar(pose) volta ao boneco montado."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'kirito.py'), [
    ("""def _no_retangulo(rect, tex, rec, ps, espelhar, chao=None):""",
     """# ═══════════════════════════════════════════════════════════════════
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


def _tc_espelhado(tc):
    u0, v0, u1, _, _, v1 = tc[0], tc[1], tc[2], tc[3], tc[4], tc[5]
    return (u1, v0, u0, v0, u0, v1, u1, v1)


def _no_retangulo(rect, tex, rec, ps, espelhar, chao=None):"""),
    ("""        self._ult_chave = None
        self._ev = None""", """        self._ult_chave = None
        self._desenho = None              # nome do desenho pronto (None = boneco montado)
        self._ev = None"""),
    ("""    def mao_local(self, qual=1, p=None):""", """    def _local_desenho(self, sx, sy):
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
            return self._local_desenho(*desenho_dados(self._desenho)[2]['mao'])"""),
    ("""    def ponta_espada(self, qual=1, p=None):""", """    def ponta_espada(self, qual=1, p=None):
        if p is None and self._desenho is not None:
            lx, ly = self._local_desenho(*desenho_dados(self._desenho)[2]['ponta'])
            return self.x + lx, self.y + ly"""),
    ("""    def extensao(self, p=None):""", """    def extensao(self, p=None):
        if p is None and self._desenho is not None:
            meta = desenho_dados(self._desenho)[2]
            te = self.ps / float(R)
            qx, qy = meta['quadril']
            bx0, by0, bx1, by1 = meta['caixa']
            esq, dir_ = (qx - bx0) * te, (bx1 + 1 - qx) * te
            if self.espelhar:
                esq, dir_ = dir_, esq
            return esq, (by1 + 1 - qy) * te, dir_, (qy - by0) * te"""),
    ("""    def mostrar(self, p):""", """    def mostrar_desenho(self, nome, base=None):
        \"\"\"Mostra o desenho pronto `nome` (tocando os quadros dele) no lugar
        do boneco montado. base = a pose que os efeitos consultam (forma,
        espada acesa).\"\"\"
        self.parar()
        self._desenho = nome
        if base is not None:
            self._base = base
        self._desenhar(forcar=True)

    def mostrar(self, p):
        self._desenho = None"""),
    ("""    def _desenhar(self, forcar=False):
        try:""", """    def _desenhar_desenho(self, forcar=False):
        quadros, silhuetas, meta = desenho_dados(self._desenho)
        import bankai_desenhos as _BD
        f = int(self._t * _BD.FPS) % meta['n']
        chave = ('des', self._desenho, f, self.espelhar, self.clarao > 0)
        if chave == self._ult_chave and not forcar:
            return
        self._ult_chave = chave
        te = self.ps / float(R)
        w, h = meta['tam']
        x0, y0 = self._local_desenho(0, h - 1)
        if self.espelhar:
            x0 -= (w - 1) * te
        x0 -= 0.5 * te
        y0 -= 0.5 * te
        for rect, tex, ligado in ((self._rect, quadros[f], True),
                                  (self._rect_clarao, silhuetas[f], self.clarao > 0)):
            if not ligado:
                rect.size = (0, 0)
                continue
            rect.texture = tex
            rect.pos = (x0, y0)
            rect.size = (w * te, h * te)
            rect.tex_coords = _tc_espelhado(tex.tex_coords) if self.espelhar else tex.tex_coords
        for rect in (self._rect_cauda, self._rect_cab, self._rect_clarao_cauda, self._rect_clarao_cab):
            rect.size = (0, 0)
        self._cor_clarao.a = self.clarao
        if self.ao_redesenhar is not None:
            self.ao_redesenhar()

    def _desenhar(self, forcar=False):
        if self._desenho is not None:
            try:
                return self._desenhar_desenho(forcar)
            except Exception as e:
                print(f"[kirito] desenho pronto: {e}")
                self._desenho = None
        try:"""),
    # rastro do desenho pronto
    ("""            with g.canvas:
                PushMatrix()
                Translate(self.x, self.y)
                Rotate(angle=self.rotacao, origin=orig)
                cor_sil = Color(cor[0], cor[1], cor[2], alfa)
                if True:""", """            with g.canvas:
                PushMatrix()
                Translate(self.x, self.y)
                Rotate(angle=self.rotacao, origin=orig)
                cor_sil = Color(cor[0], cor[1], cor[2], alfa)
                if self._desenho is not None:
                    r = self._rect_clarao
                    quadros, silhuetas, meta = desenho_dados(self._desenho)
                    import bankai_desenhos as _BD
                    tex = silhuetas[int(self._t * _BD.FPS) % meta['n']]
                    Rectangle(texture=tex, pos=self._rect.pos, size=self._rect.size,
                              tex_coords=_tc_espelhado(tex.tex_coords) if self.espelhar else tex.tex_coords)
                else:"""),
])
print('ok')
