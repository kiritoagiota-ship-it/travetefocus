"""Cabelo, sobretudo e cabeca trocam de desenho JUNTO com o corpo (como num
desenho a mao: tudo e redesenhado no mesmo quadro, o atraso vem da mola);
com o corpo parado, trocam so 10 vezes por segundo."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'kirito.py'), [
    ("""    def _travar_batida(self):
        \"\"\"Copia o estado das molas para o desenho so em algumas batidas
        (a fisica roda a 30/s): o sobretudo muda nas batidas pares, o cabelo
        nas impares (chega depois do corpo e do sobretudo), a cabeca a cada 2.\"\"\"
        self._batida = (self._batida + 1) % 6
        pr = self._preso
        f6 = (int(self._fase * 6) % 6) / 6.0
        if self._batida % 2 == 0:
            pr['capa'] = self._m_capa.x
            pr['lift'] = self._m_lift.x
            pr['fase'] = f6
        else:
            pr['cabelo'] = self._m_cab.x
            pr['fase_cab'] = f6
        if self._batida % 2 == 1:
            pr['hx'] = int(round(max(-1.0, min(1.0, self._m_hx.x))))
            pr['hy'] = int(round(max(-1.0, min(1.0, self._m_hy.x))))
""", """    def _travar_batida(self, forcar=False):
        \"\"\"Copia o estado das molas para o desenho: junto com cada desenho
        novo do corpo (forcar) ou, com o corpo parado, a cada 3 tiques da
        fisica (10 por segundo). O atraso do cabelo e do sobretudo vem das
        molas; a troca de desenho acontece no mesmo quadro do corpo.\"\"\"
        self._batida += 1
        if not forcar and self._batida < 3:
            return
        self._batida = 0
        pr = self._preso
        f6 = (int(self._fase * 6) % 6) / 6.0
        pr['capa'] = self._m_capa.x
        pr['lift'] = self._m_lift.x
        pr['fase'] = f6
        pr['cabelo'] = self._m_cab.x
        pr['fase_cab'] = (int(self._fase * 6 + 1) % 6) / 6.0     # o cabelo vai 1 passo atras do pano
        pr['hx'] = int(round(max(-1.0, min(1.0, self._m_hx.x))))
        pr['hy'] = int(round(max(-1.0, min(1.0, self._m_hy.x))))
"""),
    ("""    def mostrar(self, p):
        self._base = p
        self._desenhar()""", """    def mostrar(self, p):
        if self._base is not p and self.fisica:
            ant = self._base
            if ant is None or any(ant.get(k) != p.get(k) for k in ('dx', 'dy', 'm1', 'm2', 'a1', 'a2',
                                                                     'pernas', 'pt', 'olhos', 'incl')):
                self._travar_batida(forcar=True)       # corpo mudou: o resto e redesenhado junto
        self._base = p
        self._desenhar()"""),
])
print('ok')
