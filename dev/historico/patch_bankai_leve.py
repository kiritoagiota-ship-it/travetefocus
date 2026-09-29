"""Bankai mais leve no celular: enquanto o cabelo cresce ele nao balanca (o
proprio crescimento e o movimento - 18 desenhos fixos, todos prontos no
arquivo); no Bankai o cabelo e o sobretudo andam em passos de meia unidade
e 3 fases de onda (menos combinacoes = quase tudo vem pronto)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'kirito.py'), [
    ("""        # cabeca: +-1 px de atraso
        q['hx'] = pr['hx']
        q['hy'] = pr['hy']""", """        # cabeca: +-1 px de atraso
        q['hx'] = pr['hx']
        q['hy'] = pr['hy']
        if b.get('mugetsu'):
            if (b.get('cresce', 1.0) or 0.0) < 0.999:          # crescendo: o cabelo so cresce
                q['cabelo'] = b['cabelo']
                q['fase_cab'] = 0.0
            else:
                q['cabelo'] = round(q['cabelo'] * 2) / 2.0
                q['fase_cab'] = (int(q['fase_cab'] * 3 + 1e-6) % 3) / 3.0
            q['capa'] = round(q['capa'] * 2) / 2.0
            q['lift'] = round(q['lift'] * 2) / 2.0
            q['fase'] = (int(q['fase'] * 3 + 1e-6) % 3) / 3.0"""),
])
print('ok')
