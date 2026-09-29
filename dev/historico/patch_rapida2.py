import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'cenas.py'), [
    ("        fs = font_size or (sp(30) if grito else sp(15))\n",
     "        fs = font_size or (sp(32) if grito else sp(18))\n"),
    ("""        def _freia():
            # freia do outro lado: poeirinha, o sobretudo passa do ponto
            _som('corte')
            _tremer(8)
            kk.impacto()
            kk.pausar(0.05)
            kk.empurrar(capa=-18, cabelo=-14)
            ax, ay = kk.ancora()
            faiscas.estourar(ax, ay - kk.extensao()[1], POEIRA, n=8, forca=dp(90), tam=max(2, ps * 0.8),
                             gravidade=dp(300))
            ag.depois(0.18, _embainha)
""", """        # no fim ele sobe e pousa EM CIMA da frase (sem tapar as letras)
        pe = kk.extensao(P['guardado'])[1] - ps
        y_topo = oy_t + th * 0.82 + pe
        B = _no_quadro(kk, ox_t + titulo.tw - th * 0.75, y_topo, [fim_p, P['chiburi1']], area, m)

        def _freia():
            # freia do outro lado (o sobretudo passa do ponto) e ja salta
            _som('corte')
            _tremer(8)
            kk.impacto()
            kk.pausar(0.05)
            kk.empurrar(capa=-18, cabelo=-14)
            p_pulo = _com(P['pulo'], olhos='s')
            ax, ay = kk.ancora()
            kk.tocar(K.sequencia([(3, K.esticado(p_pulo), 'out'), (4, K.encolhido(p_pulo), 'suave'),
                                  (1, K.esticado(fim_p))]))
            h = _arco(ay, B[1], th * 0.9, area[3] - m - _ext(kk, [K.encolhido(p_pulo)])[3])
            ag.depois(0.06, lambda: _mover(kk, kk.ancora(), B, 0.26, altura=h, fantasmas=2,
                                           limite=(area, m), on_fim=_pousa))

        def _pousa():
            _som('pouso')
            ax, ay = kk.ancora()
            faiscas.estourar(ax, ay - kk.extensao()[1], POEIRA, n=8, forca=dp(90), tam=max(2, ps * 0.8),
                             gravidade=dp(300))
            kk.empurrar(lift=-8, capa=-6)
            _embainha()
"""),
])
print('ok')
