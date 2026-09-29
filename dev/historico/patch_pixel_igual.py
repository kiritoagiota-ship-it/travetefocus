"""No celular, o tamanho do boneco cai num multiplo exato da grade (R) quando
fica a ate 12% do tamanho pedido: todos os pixels do Yoru com o mesmo
tamanho (ex.: 2 px), nada de pixel de 1 e de 2 misturados."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'kirito.py'), [
    ("""    return max(R, int(round(3 * max(1, int(round(v / 3.0))) * TAMANHO)))""",
     """    ps = max(R, int(round(3 * max(1, int(round(v / 3.0))) * TAMANHO)))
    k = int(round(ps / float(R)))
    if k >= 2 and abs(k * R - ps) <= ps * 0.12:
        return k * R                 # pixels do boneco todos do mesmo tamanho
    return ps"""),
])
print('ok')
