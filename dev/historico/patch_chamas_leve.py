"""Chamas do Bankai sem medir a pose a cada 10 quadros (cada medida era um
desenho novo): o corpo e estimado pela ancora e pelo tamanho do pixel."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'cenas.py'), [
    ("""    def _corpo(self):
        \"\"\"(x0, x1, y_pe, altura) do corpo (sem as espadas), a cada 10 quadros.\"\"\"
        self._n += 1
        if self._caixa is None or self._n % 10 == 0:
            k = self.k
            b = k._base
            esq, baixo, dir_, cima = k.extensao(dict(b, a1=None, a2=None))
            ax, ay = k.ancora()
            self._caixa = (ax - esq, ax + dir_, ay - baixo, baixo + cima)
        return self._caixa""", """    def _corpo(self):
        \"\"\"(x0, x1, y_pe, altura) do corpo, estimado pela ancora (quadril) e
        pelo tamanho da unidade - sem desenhar nada para medir.\"\"\"
        k = self.k
        ps = k.ps
        ax, ay = k.ancora()
        frente = -1 if k.espelhar else 1
        x0, x1 = sorted((ax - frente * 7 * ps, ax + frente * 5 * ps))
        dy = (k._base.get('dy', 0) or 0) * ps
        return (x0, x1, ay - 12 * ps - dy, 30 * ps)"""),
])
patch(os.path.join(A, 'dev', 'tour.py'), [
    ("""    LOG['montar'].append([round(agora(), 3), round((time.perf_counter() - t) * 1000, 3)])
    return r""", """    LOG['montar'].append([round(agora(), 3), round((time.perf_counter() - t) * 1000, 3),
                          1 if kw.get('rapido') else 0])
    return r"""),
])
print('ok')
