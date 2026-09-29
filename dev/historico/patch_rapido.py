"""Deixa o desenho do Yoru mais rapido (mesmo resultado): _fita, contorno
e a imagem final (um byte por texel + tabelas de cor)."""
p = r'C:\Users\kirit\travetefocus\app\kirito.py'
c = open(p, encoding='utf-8').read()


def troca(a, b):
    global c
    assert c.count(a) == 1, (a[:70], c.count(a))
    c = c.replace(a, b)


# ── _fita: laco apertado (nomes locais, sem math.floor, limpeza direta)
a = c.index('def _fita(x0, y0, ang0, comp, curva, larg, passo=0.5):')
b = c.index('\ndef _onda(', a)
c = c[:a] + '''def _fita(x0, y0, ang0, comp, curva, larg, passo=0.5):
    """-> {(x, y): (u, v, W)}. O eixo sai de (x0, y0) (texels) no angulo
    ang0 (graus) e dobra curva(u) graus; larg(u) -> (a, b): quanto a fita
    vai para o lado da luz (a) e para o outro (b). Cada texel fica com a
    amostra mais perto do seu centro: a cor nao pisca de um quadro para o
    outro."""
    n = max(2, int(comp / passo))
    ds = comp / float(n)
    x, y = float(x0), float(y0)
    melhor = {}
    pega = melhor.get
    rad, cos, sin = math.radians, math.cos, math.sin
    for i in range(n + 1):
        u = i / float(n)
        ang = rad(ang0 + curva(u))
        ux, uy = cos(ang), sin(ang)
        a, b = larg(u)
        W = a + b
        if W > 0.05:
            # nx, ny = uy, -ux (lado da luz)
            lx, ly = x + uy * a, y - ux * a
            m = int(W * 2.2) + 1
            px_, py_ = -uy * W / m, ux * W / m          # passo ao longo da fatia
            for k in range(m + 1):
                qx, qy = lx + px_ * k, ly + py_ * k
                ix, iy = int(qx + 4096.5) - 4096, int(qy + 4096.5) - 4096
                d = (qx - ix) * (qx - ix) + (qy - iy) * (qy - iy)
                q = (ix, iy)
                atual = pega(q)
                if atual is None or d < atual[0]:
                    melhor[q] = (d, u, W * k / m, W)
        x += ux * ds
        y += uy * ds
    f = {q: (u, v, W) for q, (d, u, v, W) in melhor.items()}
    # acabamento de pixel art: sem texel pendurado (1 vizinho so) na borda
    # e sem furinho de 1 texel no meio
    solto = []
    for q, val in f.items():
        if val[0] < 0.92:
            x, y = q
            viz = ((x + 1, y) in f) + ((x - 1, y) in f) + ((x, y + 1) in f) + ((x, y - 1) in f)
            if viz <= 1:
                solto.append(q)
    for q in solto:
        del f[q]
    furos = {}
    for (x, y) in f:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in f:
                furos[q] = furos.get(q, 0) + 1
    for q, n in furos.items():
        if n >= 3:
            x, y = q
            for vz in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                val = f.get(vz)
                if val is not None:
                    f[q] = val
                    break
    return f

''' + c[b:]

# ── contorno do montar novo: vizinhos vazios por conjuntos (em C)
a = c.index("    aro = 'o' if mugetsu else 'O'\n    novos = {}\n\n    def fora(q, vx, vy):\n        for i in range(1, 2 * R + 2):")
b = c.index("    px.update(novos)\n    return px", a)
c = c[:a] + '''    aro = 'o' if mugetsu else 'O'
    fonte = [q for q, ch in px.items() if ch not in _SEM_CONTORNO]
    ocup = px.keys()
    esq = {(x - 1, y) for (x, y) in fonte} - ocup
    cima = {(x, y + 1) for (x, y) in fonte} - ocup
    resto = ({(x + 1, y) for (x, y) in fonte} | {(x, y - 1) for (x, y) in fonte}) - ocup
    alcance = 2 * R + 2
    novos = {}
    for (x, y) in esq:                                     # vao interno nao e borda de fora
        if not any((x - i, y) in px for i in range(1, alcance)):
            novos[(x, y)] = aro
    for (x, y) in cima:
        if (x, y) not in novos and not any((x, y + i) in px for i in range(1, alcance)):
            novos[(x, y)] = aro
    for q in (esq | cima | resto):
        if q not in novos:
            novos[q] = 'N'
''' + c[b:]

# ── imagem final: um byte por texel e as 4 cores por tabela (em C)
troca('''        w, h = X1 - X0 + 1, Y1 - Y0 + 1
        buf = bytearray(w * h * 4)
        rgba = _RGBA
        for x, y, c in dentro:
            i = ((y - Y0) * w + (x - X0)) * 4
            buf[i:i + 4] = rgba[c]
        recorte = (X0, Y0, w, h)''', '''        w, h = X1 - X0 + 1, Y1 - Y0 + 1
        idx = bytearray(w * h)
        cod = _COD
        for x, y, c in dentro:
            idx[(y - Y0) * w + (x - X0)] = cod[c]
        buf = bytearray(w * h * 4)
        buf[0::4] = idx.translate(_TAB[0])
        buf[1::4] = idx.translate(_TAB[1])
        buf[2::4] = idx.translate(_TAB[2])
        buf[3::4] = idx.translate(_TAB[3])
        recorte = (X0, Y0, w, h)''')
troca('''_RGBA = {c: bytes(int(round(v * 255)) for v in cor) for c, cor in _PALETA.items()}''',
      '''_RGBA = {c: bytes(int(round(v * 255)) for v in cor) for c, cor in _PALETA.items()}
# cada cor da paleta vira um numero (0 = vazio) e 4 tabelas dao R, G, B e A
_COD = {c: i + 1 for i, c in enumerate(sorted(_PALETA))}
_TAB = [bytearray(256) for _ in range(4)]
for _c, _i in _COD.items():
    for _k in range(4):
        _TAB[_k][_i] = _RGBA[_c][_k]
_TAB = [bytes(t) for t in _TAB]''')
open(p, 'w', encoding='utf-8', newline='\r\n').write(c)
print('ok')
