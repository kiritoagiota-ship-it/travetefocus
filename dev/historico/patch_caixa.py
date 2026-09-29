import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'kirito.py')
patch(A, [("""    ch = _chave(p)
    item = _CACHE.get(ch)
    if item is not None:
        return item[1]
    cx = _CAIXAS.get(ch)
    if cx is None and _ASSADO_CAIXAS and _assado_valido():
        cx = _ASSADO_CAIXAS.get(repr(ch))
    if cx is None:
        _grava('caixa', ch, p)
        px = montar(p, rapido=True)""", """    ch = _chave(p)
    _grava('caixa', ch, p)               # (so anota quando esta assando os quadros)
    item = _CACHE.get(ch)
    if item is not None:
        return item[1]
    cx = _CAIXAS.get(ch)
    if cx is None and _ASSADO_CAIXAS and _assado_valido():
        cx = _ASSADO_CAIXAS.get(repr(ch))
    if cx is None:
        px = montar(p, rapido=True)""")])
print('ok')
