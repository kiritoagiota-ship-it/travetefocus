p = r'C:\Users\kirit\travetefocus\app\kirito.py'
c = open(p, encoding='utf-8').read()


def troca(a, b):
    global c
    assert c.count(a) == 1, (a[:70], c.count(a))
    c = c.replace(a, b)


troca('''    alcance = 2 * R + 2
    novos = {}
    for (x, y) in esq:                                     # vao interno nao e borda de fora
        if not any((x - i, y) in px for i in range(1, alcance)):
            novos[(x, y)] = aro
    for (x, y) in cima:
        if (x, y) not in novos and not any((x, y + i) in px for i in range(1, alcance)):
            novos[(x, y)] = aro''', '''    alcance = 2 * R + 2
    # vao interno (entre perna e casaco, por ex.) nao e borda de fora: ha
    # boneco a menos de `alcance` texels na mesma direcao. Linhas e colunas
    # ordenadas + busca binaria (bem mais leve que olhar texel a texel)
    linhas, colunas = {}, {}
    for (x, y) in ocup:
        linhas.setdefault(y, []).append(x)
        colunas.setdefault(x, []).append(y)
    for v in linhas.values():
        v.sort()
    for v in colunas.values():
        v.sort()
    novos = {}
    for (x, y) in esq:
        v = linhas.get(y)
        i = bisect_left(v, x) if v else 0
        if not (v and i > 0 and x - v[i - 1] < alcance):   # nada logo a esquerda
            novos[(x, y)] = aro
    for (x, y) in cima:
        if (x, y) in novos:
            continue
        v = colunas.get(x)
        i = bisect_right(v, y) if v else 0
        if not (v and i < len(v) and v[i] - y < alcance):  # nada logo acima
            novos[(x, y)] = aro''')
troca('import math\nimport time\n', 'import math\nimport time\nfrom bisect import bisect_left, bisect_right\n')
# imagem final: caixa numa passada so
troca('''    px = montar(p)
    dentro = [(x, y, c) for (x, y), c in px.items() if 0 <= x < TW and 0 <= y < TH]
    x0 = y0 = 10 ** 6
    x1 = y1 = -10 ** 6
    if dentro:
        xs = [d[0] for d in dentro]
        ys = [d[1] for d in dentro]
        X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)
        corpo = [d for d in dentro if d[2] not in 'xX<>']   # rastro nao conta para o enquadramento
        if corpo:
            xs = [d[0] for d in corpo]
            ys = [d[1] for d in corpo]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)''', '''    px = montar(p)
    dentro = [(x, y, c) for (x, y), c in px.items() if 0 <= x < TW and 0 <= y < TH]
    x0 = y0 = 10 ** 6
    x1 = y1 = -10 ** 6
    if dentro:
        xs = [d[0] for d in dentro]
        ys = [d[1] for d in dentro]
        X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)
        rastro = [d for d in dentro if d[2] in 'xX<>']
        if not rastro:                                   # o normal: caixa = recorte
            x0, x1, y0, y1 = X0, X1, Y0, Y1
        else:                                            # rastro nao conta para o enquadramento
            corpo = [d for d in dentro if d[2] not in 'xX<>']
            if corpo:
                xs = [d[0] for d in corpo]
                ys = [d[1] for d in corpo]
                x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)''')
open(p, 'w', encoding='utf-8', newline='\r\n').write(c)
print('ok')
