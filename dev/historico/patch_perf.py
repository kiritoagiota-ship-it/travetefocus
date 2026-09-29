p = r'C:\Users\kirit\travetefocus\app\kirito.py'
s = open(p, 'rb').read().decode('utf-8').replace('\r\n', '\n')

a = s.index('def _iluminar(px, luz, esc=1):')
b = s.index('\n\n\n', a)
s = s[:a] + '''def _iluminar(px, luz, esc=1):
    """Luz da lamina no corpo: os pixels encostados nela sobem 2 degraus
    (ate o azul aceso), os mais longe sobem 1. Sem blur: so troca de cor em
    clusters. A distancia sai por aneis (cada anel = os vizinhos do anel
    anterior): bem mais leve que medir pixel a pixel."""
    lamina = [q for q, ch in px.items() if ch in _LAMINA]
    if not lamina:
        return
    r = (2 if luz >= 0.75 else 1) * esc
    forte = luz >= 0.75
    visto = set(lamina)
    anel = lamina
    for d in range(1, r + 1):
        novo = []
        for (x, y) in anel:
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1),
                      (x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)):
                if q not in visto:
                    visto.add(q)
                    novo.append(q)
        for q in novo:
            ch = px.get(q)
            if ch in _ACENDE:
                ch = _ACENDE[ch]
                if d <= esc and forte and ch in _ACENDE:
                    ch = _ACENDE[ch]
                px[q] = ch
        anel = novo''' + s[b:]

velho = s[s.index('    px = montar(p)\n    x0 = y0 = X0 = Y0 = 10 ** 6'):s.index('    # caixa em unidades da grade (as cenas trabalham nelas)')]
novo = '''    px = montar(p)
    dentro = [(x, y, c) for (x, y), c in px.items() if 0 <= x < TW and 0 <= y < TH]
    x0 = y0 = 10 ** 6
    x1 = y1 = -10 ** 6
    if dentro:
        xs = [d[0] for d in dentro]
        ys = [d[1] for d in dentro]
        X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)
        corpo = [d for d in dentro if d[2] not in 'xX']   # rastro nao conta para o enquadramento
        if corpo:
            xs = [d[0] for d in corpo]
            ys = [d[1] for d in corpo]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        w, h = X1 - X0 + 1, Y1 - Y0 + 1
        buf = bytearray(w * h * 4)
        rgba = _RGBA
        for x, y, c in dentro:
            i = ((y - Y0) * w + (x - X0)) * 4
            buf[i:i + 4] = rgba[c]
        recorte = (X0, Y0, w, h)
    else:
        buf, recorte = bytearray(4), (0, 0, 1, 1)
'''
s = s.replace(velho, novo)
open(p, 'wb').write(s.replace('\n', '\r\n').encode('utf-8'))
print('ok')
