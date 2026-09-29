"""Cor das chamas do Bankai: base roxa, meio lilas e so a pontinha clara
(quando nova); envelhecendo escurecem para roxo escuro."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'cenas.py'), [
    ("""                for i in range(n):
                    c = min(4, int(a * 3.2) + (1 if i >= n - 1 else 0) + (1 if i == 0 and a > 0.5 else 0))
                    nome = ('L', 'V', 'F', 'o', 'd')[c]""",
     """                c = min(4, int(a * 2.6))
                for i in range(n):
                    if i == n - 1:
                        nome = ('L', 'V', 'F', 'o', 'd')[c]           # pontinha clara so quando nova
                    elif i == n - 2:
                        nome = ('V', 'F', 'o', 'd', 'd')[c]
                    else:
                        nome = ('F', 'F', 'o', 'd', 'd')[c]           # base roxa"""),
])
print('ok')
