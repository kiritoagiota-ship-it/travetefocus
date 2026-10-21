"""Retrato do Yoru em PIXEL ART grande e detalhado (fundo do cabecalho do menu).
As formas (cabelo, rosto 3/4 olhando para a esquerda, olhos, casaco de gola
alta) vem do desenho de dev/retrato_anime.py; aqui elas viram pixels numa
grade de GW x GH e sao pintadas com a paleta do Yoru (dev/paleta5.py):
contorno, 4 tons no cabelo, 3 na pele, iris em 3 azuis, luz de contorno ciano.
Quadros: normal, olho meio fechado, fechado e o cabelo balancando (2 lados).
uso: python dev/retrato_pixel.py [previa.png]   -> grava yoru_retrato.py (mapas)"""
import os
import sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from PIL import Image, ImageChops  # noqa: E402
import retrato_anime as RA  # noqa: E402
from paleta5 import P5  # noqa: E402

# a janela do desenho (coordenadas do retrato_anime) que vira a grade
X0, Y0, ESC = 196, 58, 0.4
GW, GH = 140, 116


def grade(mask):
    """Mascara do desenho (supersample) -> conjunto de pixels da grade."""
    box = (X0 * RA.SS, Y0 * RA.SS, int((X0 + GW / ESC) * RA.SS), int((Y0 + GH / ESC) * RA.SS))
    m = mask.crop(box).resize((GW, GH), Image.BOX)
    px = m.load()
    return {(x, y) for y in range(GH) for x in range(GW) if px[x, y] >= 128}


def desloca(s, dx, dy):
    return {(x + dx, y + dy) for (x, y) in s}


def borda(s):
    """Pixels de s com algum vizinho (4) fora de s."""
    return {(x, y) for (x, y) in s if any((x + a, y + b) not in s for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def quadro(olho='aberto', vento=0):
    # o cabelo balanca: as pontas das mechas de tras andam um pouco
    tras = RA.MECHAS_TRAS
    if vento:
        tras = [(b, (c[0] + vento * 4, c[1] - vento * 2), (p[0] + vento * 7, p[1] - vento * 3), w)
                for (b, c, p, w) in tras]
    salvo = RA.MECHAS_TRAS
    RA.MECHAS_TRAS = tras
    try:
        m = RA.camadas()
    finally:
        RA.MECHAS_TRAS = salvo
    g = {k: grade(v) for k, v in m.items()}
    px = {}

    def pinta(s, ch):
        for p in s:
            px[p] = ch

    # casaco, gola e a faixa ciano
    pinta(g['casaco'], 'C')
    pinta(borda(g['casaco']) & desloca(g['casaco'], 0, 1), 'A')          # luz no ombro
    pinta(g['camisa'], '2')
    pinta(g['gola'], 'A')
    pinta(g['gola'] - desloca(g['gola'], 2, 0), 'c')
    pinta(g['faixa'], 'O')
    pinta(g['faixa'] - desloca(g['faixa'], -1, 0), '0')
    # pescoco (na sombra do queixo)
    pinta(g['pescoco'], 's')
    pinta(g['pescoco'] & desloca(g['rosto'], 0, 4), 't')
    # cabelo de tras
    tras = g['cabelo_tras']
    pinta(tras, 'H')
    pinta(tras - desloca(tras, 0, 3), 'J')                             # a parte de baixo de cada volume
    # rosto
    rosto = g['rosto']
    pinta(rosto, 'S')
    pinta(rosto - desloca(rosto, 3, 0), 's')                           # o lado de longe (esquerda)
    pinta(g['sombra_rosto'], 's')
    pinta(g['sombra_rosto'] & desloca(g['franja'], 0, 2), 't')
    pinta(g['nariz'], 't')
    pinta(g['boca'], 'T')
    pinta(g['sobrancelha'], 'J')
    # olhos
    for o in ('perto', 'longe'):
        if olho == 'fechado':
            pinta(g['fechado_' + o], 'N')
            continue
        olh = g['olho_' + o]
        if olho == 'meio':
            topo = min((y for (_, y) in olh), default=0)
            meio = topo + max(1, (max((y for (_, y) in olh), default=0) - topo) // 2)
            olh = {(x, y) for (x, y) in olh if y >= meio}
        pinta(olh, 'n')
        pinta(olh - desloca(olh, 0, 2), 'i')                          # sombra da palpebra no branco
        iris = g['iris_' + o] & olh
        if iris:
            ys = [y for (_, y) in iris]
            y0, y1 = min(ys), max(ys)
            for (x, y) in iris:
                k = (y - y0) / float(max(1, y1 - y0))
                px[(x, y)] = 'e' if k < 0.35 else ('3' if k < 0.75 else 'm')
            pinta(g['pupila_' + o] & olh, 'E')
            if olho == 'aberto':
                pinta(g['reflexo_' + o] & olh, 'n')
        lid = g['palpebra_' + o]
        if olho == 'meio':
            lid = desloca(lid, 0, 2)
        pinta(lid, 'N')
    # franja por cima
    fr = g['franja']
    pinta(fr, 'H')
    pinta(fr - desloca(fr, 0, 3), 'J')
    # brilho do cabelo (anel de luz e os fios)
    br = g['brilho_cab']
    pinta(br, 'I')
    pinta(br & desloca(br, 0, 1) & desloca(br, 0, -1), 'h')
    # as mechas separadas: a borda de cada uma (por dentro do cabelo) escurece
    cabelo = tras | fr
    for (base, ctrl, ponta, larg) in RA.MECHAS_TRAS + RA.FRANJA:
        s = grade(RA.poli(RA.mascara(), RA.lamina(base, ctrl, ponta, larg, 0.7)))
        for (x, y) in borda(s):
            if (x, y) in cabelo and px.get((x, y)) in ('H', 'I') and (x, y + 1) in cabelo:
                px[(x, y)] = 'J'
    # contorno escuro por fora e entre as mechas da franja e o rosto
    corpo = set(px)
    fora = set()
    for (x, y) in corpo:
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + a, y + b)
            if q not in corpo and 0 <= q[0] < GW and 0 <= q[1] < GH:
                fora.add(q)
    for q in fora:
        px[q] = 'N'
    for p in borda(fr) & rosto:
        px[p] = 'N'
    # luz de contorno (vinda de tras, da direita): a borda da direita acende
    for (x, y) in list(corpo):
        if (x + 1, y) in fora or (x + 1, y) not in px:
            if px.get((x, y)) in ('H', 'J', 'I', 'h', 'C', 'A', 'c', '2'):
                px[(x, y)] = 'O'
                if px.get((x - 1, y)) in ('H', 'J', 'C', 'A'):
                    px[(x - 1, y)] = '0'
    linhas = []
    for y in range(GH):
        linhas.append(''.join(px.get((x, y), '.') for x in range(GW)))
    return linhas


QUADROS = [('normal', dict()), ('meio', dict(olho='meio')), ('fechado', dict(olho='fechado')),
           ('vento_a', dict(vento=1)), ('vento_b', dict(vento=-1))]


def gerar():
    return {nome: quadro(**kw) for nome, kw in QUADROS}


def previa(mapas, caminho, z=4):
    nomes = list(mapas)
    img = Image.new('RGB', (GW * z * len(nomes) + 10 * (len(nomes) - 1), GH * z), (12, 16, 30))
    for k, nome in enumerate(nomes):
        for y, ln in enumerate(mapas[nome]):
            for x, ch in enumerate(ln):
                if ch != '.':
                    c = P5[ch]
                    for a in range(z):
                        for b in range(z):
                            img.putpixel((k * (GW * z + 10) + x * z + a, y * z + b), c)
    img.save(caminho)


def gravar(mapas, caminho):
    usadas = sorted({ch for m in mapas.values() for ln in m for ch in ln if ch != '.'})
    with open(caminho, 'w', encoding='utf-8', newline='\n') as f:
        f.write('"""Retrato do Yoru em pixel art (fundo do cabecalho do menu).\n'
                'GERADO por dev/retrato_pixel.py - nao editar a mao."""\n\n')
        f.write('CORES = {\n')
        for ch in usadas:
            r, g, b = P5[ch]
            f.write(f"    {ch!r}: ({r / 255:.3f}, {g / 255:.3f}, {b / 255:.3f}),\n")
        ox = (RA.OLHO_PERTO['cx'] - X0) * ESC
        oy = (RA.OLHO_PERTO['cy'] - Y0) * ESC
        f.write('}\n\n')
        f.write(f'GW, GH = {GW}, {GH}\n')
        f.write(f'OLHO = ({ox:.1f}, {oy:.1f})      # o olho de perto (x, y de cima), para o brilho\n\n')
        f.write('MAPAS = {\n')
        for nome, m in mapas.items():
            f.write(f'    {nome!r}: [\n')
            for ln in m:
                f.write(f'        {ln!r},\n')
            f.write('    ],\n')
        f.write('}\n')


if __name__ == '__main__':
    mapas = gerar()
    if len(sys.argv) > 1:
        previa(mapas, sys.argv[1])
    gravar(mapas, os.path.join(os.path.dirname(AQUI), 'yoru_retrato.py'))
    print('ok', GW, 'x', GH, len(mapas), 'quadros')
