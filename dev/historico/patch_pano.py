import os
AQUI = os.path.dirname(os.path.abspath(__file__))
p = r'C:\Users\kirit\travetefocus\app\kirito.py'
c = open(p, encoding='utf-8').read()


def troca(a, b, n=1):
    global c
    assert c.count(a) == n, (a[:80], c.count(a))
    c = c.replace(a, b)


bloco = open(os.path.join(AQUI, 'pano.txt'), encoding='utf-8').read()
troca('def _bainha_costas(px, x, y):', bloco + 'def _bainha_costas(px, x, y):')
troca("""    _cabelo_tras2(px, cab_x, cab_ty, cb, sobe, fase)
    if sobe > 0.3:""", """    if mugetsu:
        _cabelo_tras2(px, cab_x, cab_ty, cb, sobe, fase)
    else:
        _mechas_tras(px, cab_x, cab_ty, cb, sobe, fase)
    if sobe > 0.3:""")
troca("""    _casaco3(px, base, topo - len(_TRONCO), p['capa'], p['lift'], fase, saia, 'tras', mugetsu)
    _pernas3(px, p, _X0 + 6.5, hip_y)
    _bainha2(px, boca[0], boca[1])
    _casaco3(px, base, topo - len(_TRONCO), p['capa'], p['lift'], fase, saia, 'frente', mugetsu)""",
      """    if mugetsu:
        _casaco3(px, base, topo - len(_TRONCO), p['capa'], p['lift'], fase, saia, 'tras', True)
        _pernas3(px, p, _X0 + 6.5, hip_y)
    else:
        _casaco4(px, base, topo - len(_TRONCO), p['capa'], p['lift'], fase, saia, 'tras')
        pernas = {}
        _pernas3(pernas, p, _X0 + 6.5, hip_y)
        _contorna(px, pernas, _PANO)            # perna separada do sobretudo
    _bainha2(px, boca[0], boca[1])
    if mugetsu:
        _casaco3(px, base, topo - len(_TRONCO), p['capa'], p['lift'], fase, saia, 'frente', True)
    else:
        _casaco4(px, base, topo - len(_TRONCO), p['capa'], p['lift'], fase, saia, 'frente')""")
troca("""_CORPO = set('CcAqGPBMSsHhE24JIen7tU3%bp~^')""", """_CORPO = set('CcAqGPBMSsHhE24JIen7tU3%bp~^')
_PANO = set('CcAq2Z')                                   # sobretudo""")
open(p, 'w', encoding='utf-8', newline='\r\n').write(c)
print('ok')
