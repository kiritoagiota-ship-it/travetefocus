import sys, importlib
sys.path.insert(0, 't')
from vermapa import ver, K
import mapas3 as M
from amplia import amplia
K._PALETA.update(M.NOVAS_CORES)
nomes = sys.argv[1].split(',')
lista = []
for n in nomes:
    if n.startswith('old:'):
        lista.append((n, amplia(eval('K.' + n[4:]))))
    else:
        lista.append((n, getattr(M, n)))
print(ver(lista, 't/m3.png', esc=int(sys.argv[2]) if len(sys.argv) > 2 else 10))
# tamanho real no celular (texel = 3 px)
ver(lista, 't/m3_real.png', esc=3)
