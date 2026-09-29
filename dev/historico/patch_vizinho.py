"""Sobretudo e cabelo: se a combinacao exata do balanco (capa, vento,
cabelo, fase da onda) nao estiver pronta no arquivo, usa o desenho pronto
MAIS PARECIDO (mesma forma, mesmos olhos, mesmo tamanho de cabelo) em vez de
desenhar na hora - o balanco varia um tiquinho a cada vez e isso gerava
centenas de desenhos na hora (engasgos no celular). O corpo continua exato."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'kirito.py'), [
    ("""    _grava(qual, chave, q)
    pronto = _do_assado(qual, chave)
    item = (pronto[0], pronto[1]) if pronto else _rasteriza(montar(q, camada=qual))""",
     """    _grava(qual, chave, q)
    pronto = _do_assado(qual, chave)
    if not pronto and qual in ('cauda', 'cabeca') and not _GRAVA:
        pronto = _assado_vizinho(qual, chave)
    item = (pronto[0], pronto[1]) if pronto else _rasteriza(montar(q, camada=qual))"""),
    ("""def _grava(qual, chave, q):""", """_VIZINHOS = {}            # (camada, assinatura) -> [(fisica, chave repr)]


def _partes_fisica(qual, chave):
    \"\"\"(assinatura, fisica) de uma chave de camada: o que tem que bater
    exato e o que pode ser so parecido.\"\"\"
    if qual == 'cauda':            # ('cauda', capa, lift, fase, saia, mug)
        return (chave[4], chave[5]), (chave[1], chave[2], chave[3])
    # ('cabeca', olhos, cabelo, sobe, fase, mug, cresce)
    return (chave[1], chave[5], chave[6]), (chave[2], chave[3], chave[4])


def _assado_vizinho(qual, chave):
    \"\"\"Desenho pronto mais parecido (so o balanco diferente), ou None.\"\"\"
    try:
        if not _ASSADO or not _assado_valido():
            return None
        if not _VIZINHOS:
            import ast
            for ch in _ASSADO:
                if ch.startswith("('cauda'") or ch.startswith("('cabeca'"):
                    try:
                        qq, cc = ast.literal_eval(ch)
                        ass, fis = _partes_fisica(qq, cc)
                        _VIZINHOS.setdefault((qq, ass), []).append((fis, ch))
                    except Exception:
                        pass
            _VIZINHOS[None] = True
        ass, fis = _partes_fisica(qual, chave)
        lista = _VIZINHOS.get((qual, ass))
        if not lista:
            return None

        def dist(f):
            df = abs((f[2] or 0.0) - (fis[2] or 0.0)) % 1.0
            return abs((f[0] or 0.0) - (fis[0] or 0.0)) + abs((f[1] or 0.0) - (fis[1] or 0.0)) + \
                min(df, 1.0 - df) * 1.5
        melhor = min(lista, key=lambda it: dist(it[0]))
        if dist(melhor[0]) > 1.6:
            return None                  # longe demais: melhor desenhar certo
        ini, tam, rec, extra = _ASSADO[melhor[1]]
        idx = _zlib.decompress(_ASSADO_DADOS[0][ini:ini + tam])
        buf = bytearray(len(idx) * 4)
        buf[0::4] = idx.translate(_TAB[0])
        buf[1::4] = idx.translate(_TAB[1])
        buf[2::4] = idx.translate(_TAB[2])
        buf[3::4] = idx.translate(_TAB[3])
        return bytes(buf), rec, extra
    except Exception as e:
        print(f"[kirito] vizinho: {e}")
        return None


def _grava(qual, chave, q):"""),
])
print('ok')
