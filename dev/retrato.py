"""Close de anime do Yoru: faixa com o olho e o rosto em pixel grande.
Desenho feito com formas (curvas das mechas, palpebra, iris) direto na
grade do retrato e depois pintado nas cores da paleta. Gera os mapas
(normal, poder, mugetsu, e o olho abrindo) e a previa.
uso: python retrato.py [saida.png]"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paleta5 import P5
from PIL import Image, ImageDraw

W, H = 104, 40          # grade do retrato (x para a direita, y para CIMA)


def fita(x0, y0, ang0, comp, curva, larg, passo=0.3):
    """Mecha/lasca: {(x, y): (u, v, W)} (igual ao kirito._fita)."""
    n = max(2, int(comp / passo))
    ds = comp / float(n)
    x, y = float(x0), float(y0)
    melhor = {}
    for i in range(n + 1):
        u = i / float(n)
        a = math.radians(ang0 + curva(u))
        ux, uy = math.cos(a), math.sin(a)
        la, lb = larg(u)
        Wd = la + lb
        if Wd > 0.05:
            lx, ly = x + uy * la, y - ux * la
            m = int(Wd * 2.5) + 1
            for k in range(m + 1):
                qx, qy = lx - uy * Wd * k / m, ly + ux * Wd * k / m
                ix, iy = int(math.floor(qx + 0.5)), int(math.floor(qy + 0.5))
                d = (qx - ix) ** 2 + (qy - iy) ** 2
                at = melhor.get((ix, iy))
                if at is None or d < at[0]:
                    melhor[(ix, iy)] = (d, u, Wd * k / m, Wd)
        x += ux * ds
        y += uy * ds
    return {q: (u, v, Wd) for q, (d, u, v, Wd) in melhor.items()}


def dentro_elipse(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


def retrato(olho='normal', abre=1.0):
    """olho: 'normal', 'poder', 'mugetsu'. abre: 0 (fechado) .. 1 (aberto)."""
    px = {}
    # ── pele (rosto de perfil virado para a direita): testa, bochecha e
    #    o nariz saindo na borda direita
    for y in range(0, 32):
        for x in range(26, W):
            borda = W - 3 - (3 if y > 20 else 0) - max(0, 6 - abs(y - 9)) * 0.0
            nariz = W - 1 if 5 <= y <= 12 else W - 4
            if x <= nariz and x <= borda + (3 if 5 <= y <= 12 else 0):
                px[(x, y)] = 'S'
    # sombra da franja na testa e sombra da bochecha (lado de tras)
    for (x, y), ch in list(px.items()):
        if y > 24:
            px[(x, y)] = 't' if y > 27 else 's'
        elif x < 40:
            px[(x, y)] = 's' if x > 32 else 't'
    # ── cabelo de tras (massa escura) e o tufo voando para a esquerda
    for y in range(0, H):
        for x in range(0, 40 - int(max(0, 20 - y) * 0.35)):
            px[(x, y)] = 'J' if (x + y) % 11 else 'H'
    mechas = [  # (x, y, angulo, comp, largura, curva)  -> tufo e massa
        (30, 30, 172, 34, 7.0, 10), (32, 22, 188, 36, 7.5, 6), (30, 14, 200, 32, 6.5, -4),
        (32, 36, 160, 28, 5.5, 12), (28, 6, 214, 26, 5.5, -8)]
    for i, (x0, y0, a0, cp, lg, cu) in enumerate(mechas):
        f = fita(x0, y0, a0, cp, lambda u, cu=cu: cu * u * u, lambda u, lg=lg: (lg * (1 - u) ** 1.1, lg * (1 - u) ** 0.9))
        for q, (u, v, Wd) in f.items():
            vf = v / Wd if Wd else .5
            ch = 'J' if vf > 0.68 or u > 0.86 else ('I' if vf < 0.25 and 0.2 < u < 0.6 else 'H')
            if q in px and px[q] in 'JHI' and any((q[0] + a, q[1] + b) not in f for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                ch = 'J'
            px[q] = ch
    # ── topo do cabelo (a franja nasce aqui)
    for y in range(31, H):
        for x in range(26, W):
            px[(x, y)] = 'H' if (x * 3 + y) % 13 else 'I'
    # brilho em arco (mechas) no topo
    for x in range(40, 96):
        yy = 36 + int(1.6 * math.sin((x - 40) / 56.0 * math.pi))
        if (x // 7) % 3 != 2:
            px[(x, yy)] = 'h' if (x // 7) % 2 else 'I'
            px[(x, yy - 1)] = 'I'
    # ── franja: mechas pontudas caindo por cima da testa e do olho
    franja = [  # (x_raiz, angulo, comp, larg)
        (44, -96, 16, 4.0), (52, -100, 19, 4.5), (60, -86, 17, 4.2), (69, -80, 13, 4.0),
        (77, -84, 16, 4.2), (86, -76, 14, 3.8), (94, -70, 12, 3.4), (100, -66, 10, 3.0)]
    for i, (x0, a0, cp, lg) in enumerate(franja):
        f = fita(x0, 34, a0, cp, lambda u, i=i: (6 if i % 2 else -5) * u * u,
                 lambda u, lg=lg: (lg * (1 - u) ** 0.9, lg * (1 - u) ** 1.2))
        for q, (u, v, Wd) in f.items():
            vf = v / Wd if Wd else .5
            ch = 'J' if (vf > 0.7 or u > 0.84) else ('I' if (vf < 0.3 and 0.15 < u < 0.55) else 'H')
            if q in px and px[q] in 'JHIh' and any((q[0] + a, q[1] + b) not in f for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                ch = 'J'
            px[q] = ch
            # sombra que a mecha faz na testa
            s = (q[0] + 1, q[1] - 1)
            if px.get(s) == 'S':
                px[s] = 's'
    # ── orelha (atras da bochecha)
    for y in range(4, 18):
        for x in range(30, 40):
            if dentro_elipse(x, y, 34.5, 11, 4.6, 6.8):
                borda = not dentro_elipse(x, y, 34.5, 11, 3.4, 5.6)
                px[(x, y)] = 't' if borda else ('s' if (x < 34 or y < 8) else 'S')
    # ── sobrancelha (grossa, descendo para o nariz: olhar serio) - fica
    #    por baixo da franja (so aparece entre as mechas)
    for x in range(60, 88):
        yy = 26 - (x - 60) * 0.12
        for d in (0, 1, 2):
            q = (x, int(round(yy)) - d)
            if px.get(q) in ('S', 's', 't') and d < (2 if x < 82 else 1) + 1:
                px[q] = 'N' if d < 2 else 'T'
    # ── OLHO semicerrado (olhar serio): palpebra de cima grossa e caida
    #    cortando a iris; iris grande; pupila olhando para a frente; brilho
    #    duplo. No Mugetsu o branco vira preto e a iris acende roxa.
    x0o, x1o = 63, 91                       # canto de fora .. canto de dentro
    def cima(x):                            # borda de cima do olho (desce para o nariz)
        u = (x - x0o) / float(x1o - x0o)
        return 19.5 + 2.2 * math.sin(math.pi * min(1.0, u * 1.15)) - 3.0 * u
    def baixo(x):
        u = (x - x0o) / float(x1o - x0o)
        return 11.0 - 2.4 * math.sin(math.pi * u) + 1.5 * u
    ic, ir = (79.5, 14.4), 7.6              # iris
    fechado = 1.0 - abre
    for x in range(x0o - 1, x1o + 2):
        yc, yb = cima(x), baixo(x)
        yc2 = yc - (yc - yb) * fechado * 0.92
        for y in range(int(yb) - 2, int(yc) + 5):
            q = (x, y)
            if x0o <= x <= x1o and yb <= y <= yc2:
                if dentro_elipse(x, y, ic[0], ic[1], ir * 0.92, ir * 1.08):
                    rel = (y - (ic[1] - ir)) / (2 * ir)
                    if dentro_elipse(x, y, ic[0] + 0.8, ic[1] + 0.3, 2.2, 3.4):
                        ch = 'E'                                   # pupila
                    elif y > yc2 - 1.6:
                        ch = 'E'                                   # sombra do cilio
                    elif rel > 0.62:
                        ch = 'e'
                    elif rel > 0.3:
                        ch = '3'
                    else:
                        ch = 'm'
                    if not dentro_elipse(x, y, ic[0], ic[1], ir * 0.72, ir * 0.88) and ch not in ('E',):
                        ch = 'e'                                   # aro escuro da iris
                else:
                    ch = 'i' if y > yc2 - 1.6 else 'n'             # branco (sombra embaixo do cilio)
                px[q] = ch
            elif yc2 < y <= yc2 + 2.6 + (1.6 if x < x0o + 8 else 0) and x0o - 1 <= x <= x1o + 1:
                px[q] = 'N'                                        # cilio de cima grosso
            elif yb - 1.3 <= y < yb and x0o + 3 <= x <= x1o - 2:
                px[q] = 's'                                        # palpebra de baixo
    if abre > 0.5:
        for (bx, by) in ((76, 18), (77, 18), (76, 17), (77, 17), (83, 11), (84, 11)):
            if px.get((bx, by)) in ('E', 'e', '3', 'm'):
                px[(bx, by)] = 'n'                                 # brilhos
        for (bx, by) in ((62, 20), (61, 21), (60, 22), (59, 23), (61, 20), (60, 21)):
            px[(bx, by)] = 'N'                                     # ponta do cilio
        px[(x1o + 2, 15)] = 'N'                                    # canto de dentro
    # sombra embaixo do cilio (na pele) e bochecha rosada
    for x in range(64, 92):
        for y in range(4, 8):
            if px.get((x, y)) == 'S' and 0.0 < ((x - 80) / 9.0) ** 2 + ((y - 5.5) / 1.8) ** 2 < 1.0 and (x + y) % 2 == 0:
                px[(x, y)] = 's'
    # ── cores por tipo de olho
    if olho == 'poder':
        troca = {'e': '0', '3': 'Z', 'm': '9', 'E': '0'}
        for q, ch in list(px.items()):
            if 62 <= q[0] <= 92 and 6 <= q[1] <= 24 and ch in troca:
                px[q] = troca[ch]
    if olho == 'mugetsu':
        troca = {'n': 'D', 'i': 'D', 'e': 'V', '3': 'o', 'm': 'L', 'E': '&'}
        for q, ch in list(px.items()):
            if 62 <= q[0] <= 92 and 6 <= q[1] <= 24 and ch in troca:
                if ch in ('n',) and dentro_elipse(q[0], q[1], 79.5, 14.4, 7.6, 8.2):
                    px[q] = '!'                                    # os brilhos continuam brancos
                else:
                    px[q] = troca[ch]
        for q, ch in list(px.items()):
            if ch in ('S', 's'):
                d = math.hypot((q[0] - 80) / 1.3, q[1] - 14)
                if d < 11 and (q[0] + q[1]) % 2 == 0:
                    px[q] = '^'                                    # luz roxa na pele (pontilhada)
                elif ch == 's':
                    px[q] = 't'
    return px


def mapa(px):
    linhas = []
    for y in range(H - 1, -1, -1):
        linhas.append(''.join(px.get((x, y), '.') for x in range(W)))
    return linhas


PALETA_EXTRA = {'^': (219, 184, 250), '&': (28, 19, 46), 'V': (230, 158, 255), 'L': (237, 219, 255),
                'D': (13, 10, 23), 'o': (168, 92, 255), '!': (255, 255, 255), '9': (170, 240, 255)}


def ver(mapas, saida, z=8):
    S = Image.new('RGB', (W * z, (H * z + 10) * len(mapas)), (0, 0, 0))
    d = ImageDraw.Draw(S)
    for i, m in enumerate(mapas):
        oy = i * (H * z + 10)
        d.rectangle([0, oy, W * z, oy + H * z], fill=(18, 16, 30))
        for r, l in enumerate(m):
            for c, ch in enumerate(l):
                if ch != '.':
                    col = P5.get(ch) or PALETA_EXTRA.get(ch, (255, 0, 255))
                    d.rectangle([c * z, oy + r * z, c * z + z - 1, oy + r * z + z - 1], fill=col)
    S.save(saida)


def gravar_mapas(caminho):
    """Acrescenta RETRATOS ao yoru_mapas.py (substitui se ja existir)."""
    txt = open(caminho, encoding='utf-8').read()
    if '\nRETRATOS = {' in txt:
        txt = txt[:txt.index('\nRETRATOS = {')]
    variantes = {'normal': retrato('normal'), 'normal_meio': retrato('normal', 0.35),
                 'poder': retrato('poder'), 'mugetsu': retrato('mugetsu'),
                 'mugetsu_meio': retrato('mugetsu', 0.35)}
    partes = ['', 'RETRATOS = {']
    for k, px in variantes.items():
        partes.append("    '%s': [" % k)
        for l in mapa(px):
            partes.append('        "%s",' % l)
        partes.append('    ],')
    partes.append('}')
    open(caminho, 'w', encoding='utf-8', newline='\r\n').write(txt.rstrip('\n') + '\n' + '\n'.join(partes) + '\n')


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[2] == 'gravar':
        gravar_mapas(os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'yoru_mapas.py'))
    ms = [mapa(retrato('normal')), mapa(retrato('normal', 0.4)), mapa(retrato('poder')), mapa(retrato('mugetsu'))]
    ver(ms, sys.argv[1] if len(sys.argv) > 1 else os.path.join(r'C:\Users\kirit\travetefocus\ferramentas\saida_testes', 'retrato.png'))
    print('ok')
