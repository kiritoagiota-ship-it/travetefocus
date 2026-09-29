"""Desenho dos clipes do Bankai no widget (parte 2): o quadro do clipe vai no
retangulo do corpo (espelhado se preciso), a fisica anda o clipe (30/s) e o
rastro usa a silhueta do quadro atual."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'kirito.py'), [
    ("""    def _desenhar_desenho(self, forcar=False):
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
            rect.tex_coords = _tc_espelhado(tex.tex_coords) if self.espelhar else tex.tex_coords""",
     """    def _desenhar_desenho(self, forcar=False):
        f = self._quadro_atual()
        chave = ('clipe', self._desenho, f, self.espelhar, self.clarao > 0)
        if chave == self._ult_chave and not forcar:
            return
        self._ult_chave = chave
        te = self.ps / float(R)
        tex, (cx0, cy0, w, h), _, _ = quadro_clipe(self._desenho, f)
        # canto de baixo/esquerda do quadro (a tela do clipe tem y para baixo)
        xa, y0 = self._local_desenho(cx0, cy0 + h)
        x0 = xa - w * te if self.espelhar else xa
        for rect, ligado in ((self._rect, True), (self._rect_clarao, self.clarao > 0)):
            if not ligado:
                rect.size = (0, 0)
                continue
            t = tex if rect is self._rect else quadro_clipe(self._desenho, f, silhueta=True)[0]
            rect.texture = t
            rect.pos = (x0, y0)
            rect.size = (w * te, h * te)
            rect.tex_coords = _tc_espelhado(t.tex_coords) if self.espelhar else t.tex_coords"""),
    ("""            dt = min(dt, 1 / 15.)
            self._t += dt
            ax, ay = self.ancora()""", """            dt = min(dt, 1 / 15.)
            self._t += dt
            self._avanca_clipe(dt)
            ax, ay = self.ancora()"""),
    ("""                if self._desenho is not None:
                    quadros, silhuetas, meta = desenho_dados(self._desenho)
                    import bankai_desenhos as _BD
                    tex = silhuetas[int(self._t * _BD.FPS) % meta['n']]
                    Rectangle(texture=tex, pos=self._rect.pos, size=self._rect.size,""",
     """                if self._desenho is not None:
                    tex = quadro_clipe(self._desenho, self._quadro_atual(), silhueta=True)[0]
                    Rectangle(texture=tex, pos=self._rect.pos, size=self._rect.size,"""),
])
print('ok 2')
