import os
REPO = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
CR, LF = chr(13), chr(10)


def _ler(nome):
    p = os.path.join(REPO, nome)
    s = open(p, encoding='utf-8', newline='').read()
    crlf = (CR + LF) in s
    return p, s.replace(CR + LF, LF), crlf


def _gravar(p, s, crlf):
    if crlf:
        s = s.replace(LF, CR + LF)
    open(p, 'w', encoding='utf-8', newline='').write(s)


def editar(nome, trocas):
    """Troca trechos exatos (cada um tem que aparecer 1 vez), preservando CRLF."""
    p, s, crlf = _ler(nome)
    for old, new in trocas:
        assert s.count(old) == 1, (nome, old[:80], s.count(old))
        s = s.replace(old, new)
    _gravar(p, s, crlf)
    print('ok', nome)


def trocar_bloco(nome, inicio, fim, novo):
    """Troca tudo de `inicio` (inclusive) ate `fim` (exclusive) por `novo`."""
    p, s, crlf = _ler(nome)
    assert s.count(inicio) == 1 and s.count(fim) >= 1, (nome, inicio[:60], fim[:60])
    i0 = s.index(inicio)
    i1 = s.index(fim, i0)
    s = s[:i0] + novo + s[i1:]
    _gravar(p, s, crlf)
    print('ok bloco', nome)
