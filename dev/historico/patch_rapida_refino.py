"""Entrada rapida refinada: o mergulho gira na pose de bola (de 90 em 90
graus, so no meio do voo), sai da bola esticando para o iai; o pouso
amortece encolhendo. Sons precarregados (Tou!, Yatta!)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'cenas.py'), [
    ("""        _precarregar_sons(['pulo', 'sacar_iai', 'corte', 'embainhar', 'pouso', 'titulo'] + _GEMIDOS)""",
     """        _precarregar_sons(['pulo', 'sacar_iai', 'corte', 'embainhar', 'pouso', 'titulo', 'fala_tou'])"""),
    ("""                           'moedas', 'pouso'] + _GEMIDOS)""",
     """                           'moedas', 'pouso', 'fala_yatta'] + _GEMIDOS)"""),
    ("""            n = max(6, int(0.42 * K.FPS))
            kk.tocar(K.sequencia([(max(2, n // 3), K.esticado(p_pulo), 'out'),
                                  (n - n // 3, K.encolhido(p_pulo), 'suave'), (1, pronto)]))
            _som('pulo')
            kk.empurrar(capa=-10, cabelo=-8, lift=10)
            _mover(kk, ini, A0, 0.42, rot=(0, -720), fantasmas=4, ease='in', on_fim=_corta)""",
     """            n = max(6, int(0.42 * K.FPS))
            bola = K.bola(p_pulo)
            kk.tocar(K.sequencia([(max(2, n // 4), K.esticado(p_pulo), 'out'),
                                  (n - n // 4 - 2, bola, 'segura'), (2, bola, 'out'),
                                  (1, _com(pronto, estica=1))]))
            _som('pulo')
            kk.empurrar(capa=-10, cabelo=-8, lift=10)
            _mover(kk, ini, A0, 0.42, rot=(0, -720), fantasmas=4, ease='in', on_fim=_corta,
                   rot_janela=(0.12, 0.85))"""),
    ("""            kk.empurrar(lift=-8, capa=-6)
            _embainha()

        def _embainha():""", """            kk.empurrar(lift=-8, capa=-6)
            kk.mostrar(_com(K.POSE_A['agacha'], olhos='s', estica=-1))      # amortece
            ag.depois(0.08, _embainha)

        def _embainha():"""),
])
print('ok')
