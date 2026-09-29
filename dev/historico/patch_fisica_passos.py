"""Cabelo e sobretudo (forma normal tambem) em passos de meia unidade: o
balanco anda em degraus maiores, como desenho quadro a quadro, e ha bem
menos combinacoes - quase tudo vem pronto do arquivo (golpes rapidos como o
WIPE nao engasgam no celular)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'kirito.py'), [
    ("""            q['capa'] = round(q['capa'] * 2) / 2.0
            q['lift'] = round(q['lift'] * 2) / 2.0
            q['fase'] = (int(q['fase'] * 3 + 1e-6) % 3) / 3.0""",
     """            q['fase'] = (int(q['fase'] * 3 + 1e-6) % 3) / 3.0
        else:
            q['cabelo'] = round(q['cabelo'] * 2) / 2.0
        q['capa'] = round(q['capa'] * 2) / 2.0
        q['lift'] = round(q['lift'] * 2) / 2.0"""),
])
print('ok')
