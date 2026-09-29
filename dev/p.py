"""patch(caminho, [(antes, depois), ...]) mantendo o fim de linha do arquivo."""


def patch(caminho, reps):
    raw = open(caminho, 'rb').read()
    crlf = b'\r\n' in raw
    c = raw.decode('utf-8').replace('\r\n', '\n')
    for a, b in reps:
        n = c.count(a)
        assert n == 1, (caminho, a[:80], n)
        c = c.replace(a, b)
    open(caminho, 'w', encoding='utf-8', newline='\r\n' if crlf else '\n').write(c)
