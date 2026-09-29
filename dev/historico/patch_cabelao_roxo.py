"""Cabelao do Bankai: brilho roxo correndo pela borda de cima de cada mecha e
pontas que viram chama aos poucos (escuro -> roxo -> lascas claras soltas),
em vez de garras claras."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'kirito.py'), [
    ("""            if u > fim:                                    # a ponta queima em chama roxa
                h = (q[0] * 3 + q[1] * 5 + f6 * 2) % 7
                if u > fim + 0.09 and h > 2:
                    continue                               # lingua de fogo solta na ponta
                ch = 'L' if h == 0 else ('V' if h < 3 else ('F' if h < 5 else 'o'))
            elif vf > 0.66:
                ch = 'J'
            elif vf < 0.3 and u < 0.42:
                ch = 'h' if (vf < 0.14 and 0.08 < u < 0.26) else 'I'
            else:
                ch = 'H'""", """            h = (q[0] * 3 + q[1] * 5 + f6 * 2) % 7
            if u > fim + 0.08:                             # ponta: lascas de chama soltas
                if h > 1:
                    continue
                ch = 'L' if h == 0 else 'V'
            elif u > fim:                                  # a ponta pega fogo aos poucos
                ch = 'F' if h < 2 else ('o' if h < 4 else 'd')
            elif vf > 0.66:
                ch = 'J'
            elif vf < 0.2 and 0.1 < u < fim - 0.04:
                ch = 'h'                                   # brilho roxo pela borda da mecha
            elif vf < 0.34 and u < 0.5:
                ch = 'I'
            else:
                ch = 'H'"""),
])
print('ok')
