import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'cenas.py')
patch(A, [
    ("""                    faiscas.estourar(ccx, cy, cor, n=7, forca=dp(170), tam=ps)
                    _som('corte2' if qual == 2 else 'corte')
                    k.impacto()""", """                    faiscas.estourar(ccx, cy, cor, n=7, forca=dp(170), tam=ps)
                    _som('corte2' if qual == 2 else 'corte')
                    if j % 3 == 0:
                        _gemido()                       # gemidinho a cada 3 golpes
                    k.impacto()"""),
    ("""                        _estrela(cam, gcx, gcy, ps, CIANO, raios=8, dur=0.2)
                        _som('titulo')""", """                        _estrela(cam, gcx, gcy, ps, CIANO, raios=8, dur=0.2)
                        _som('titulo')
                        _gemido()"""),
    ("""        _precarregar_sons(['sacar', 'corte', 'corte2', 'titulo', 'pulo', 'teleporte', 'voz_starburst',
                           'voz_stream'])""", """        _precarregar_sons(['sacar', 'corte', 'corte2', 'titulo', 'pulo', 'teleporte', 'voz_starburst',
                           'voz_stream'] + _GEMIDOS)"""),
])
print('ok')
