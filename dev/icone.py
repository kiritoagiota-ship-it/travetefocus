"""O ICONE do app em pixel art (o mesmo estilo do jogo), em 3 opcoes:
  yoru     - o busto do Yoru de frente (desenhado pelo proprio kirito.py) dentro
             de um anel holografico ciano;
  espadas  - as duas espadas dele cruzadas (a preta e a azul) atras de uma
             agulha de costura, com a linha fazendo o infinito;
  tf       - o monograma TF angular do HUD, com uma espada no T.
Cada um sai em 3 pecas, para o Android montar no formato do aparelho:
  icone_fundo.png  (o fundo, 432 px)   icone_frente.png (o desenho, 432 px,
  transparente, dentro da area segura)  icon.png (os dois juntos, 512 px).
uso: python dev/icone.py previa PASTA      (as 3 opcoes + como ficam no celular)
     python dev/icone.py usar NOME         (grava o escolhido na raiz do app)"""
import os
import sys
import math

os.environ.setdefault('KIVY_NO_ARGS', '1')
os.environ.setdefault('KIVY_LOG_MODE', 'PYTHON')
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP)
from PIL import Image, ImageDraw  # noqa: E402

G = 108                     # a grade do icone adaptativo (108 x 108 pontos; a area segura e o miolo de 66)
FUNDO = (5, 6, 16)
CIANO = (0, 229, 255)
AZUL = (60, 140, 255)


def nova(fundo=None):
    return Image.new('RGBA', (G, G), fundo + (255,) if fundo else (0, 0, 0, 0))


def fundo_holo():
    """O fundo: azul-noite com a grade do HUD e um brilho no meio, em faixas (sem degrade)."""
    im = nova(FUNDO)
    px = im.load()
    c = (G - 1) / 2.0
    for y in range(G):
        for x in range(G):
            d = math.hypot(x - c, y - c) / (G / 2.0)
            if d < 0.42:
                px[x, y] = (18, 34, 74, 255)
            elif d < 0.52:
                px[x, y] = (12, 22, 52, 255)
            elif d < 0.66:
                px[x, y] = (9, 14, 34, 255)
            elif d < 0.85:
                px[x, y] = (7, 9, 24, 255)
            if (x % 9 == 0 or y % 9 == 0) and d > 0.3:
                r, g, b, _ = px[x, y]
                px[x, y] = (r + 4, g + 14, b + 20, 255)          # a grade fininha
    return im


def anel(im, r, cor, falhas=True, esp=1):
    """Anel de pixels com cortes (o anel do HUD)."""
    px = im.load()
    c = (G - 1) / 2.0
    for k in range(720):
        a = 2 * math.pi * k / 720
        grau = math.degrees(a)
        if falhas and (40 < grau < 52 or 128 < grau < 160 or 220 < grau < 232 or 300 < grau < 338):
            continue
        for e in range(esp):
            x, y = int(round(c + math.cos(a) * (r - e))), int(round(c + math.sin(a) * (r - e)))
            if 0 <= x < G and 0 <= y < G:
                px[x, y] = cor + (255,)


def contorno(im, cor, por_fora=True):
    """Contorno de 1 pixel em volta do desenho (destaca do fundo)."""
    a = im.split()[3].load()
    out = im.copy()
    px = out.load()
    for y in range(G):
        for x in range(G):
            if a[x, y]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < G and 0 <= yy < G and a[xx, yy] > 0:
                    px[x, y] = cor + (255,)
                    break
    return out


# ── opcao 1: o Yoru ───────────────────────────────────────────────────
def yoru():
    import kirito as K
    K._ASSADO.clear()
    q = dict(K.POSE_A['vitoria'], olhos='v')
    pixels = K.montar(q)
    xs = [p[0] for p in pixels]
    ys = [p[1] for p in pixels]
    x0, x1, y1 = min(xs), max(xs), max(ys)
    w = x1 - x0 + 1
    h = y1 - min(ys) + 1
    spr = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sp = spr.load()
    idx = bytearray(w * h)
    for (x, y), ch in pixels.items():
        idx[(y - min(ys)) * w + (x - x0)] = K._COD[ch]
    idx = K.estilizar(bytes(idx), w, h)
    for i, v in enumerate(idx):
        if v:
            sp[i % w, h - 1 - i // w] = tuple(K._TAB[k][v] for k in range(4))
    # o busto: da ponta do cabelo ate o peito
    bb = spr.getbbox()
    busto = spr.crop((bb[0] + 4, bb[1], bb[2], bb[1] + 62))
    frente = nova()
    frente.alpha_composite(busto, ((G - busto.width) // 2 + 3, 23))
    frente = contorno(frente, (0, 170, 210))
    # medalhao: so o que cabe no circulo
    m = Image.new('L', (G, G), 0)
    ImageDraw.Draw(m).ellipse((22, 22, G - 23, G - 23), fill=255)
    a = Image.composite(frente, nova(), m)
    anel(a, 33, CIANO, esp=2)
    anel(a, 30, (0, 110, 150), falhas=False)
    return fundo_holo(), a


# ── opcao 2: espadas e agulha ─────────────────────────────────────────
def _linha(px, p0, p1, cor, esp=1):
    n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))) + 1
    for i in range(n):
        t = i / float(max(1, n - 1))
        x, y = p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t
        for ox in range(-(esp // 2), esp - esp // 2):
            for oy in range(-(esp // 2), esp - esp // 2):
                xx, yy = int(round(x + ox)), int(round(y + oy))
                if 0 <= xx < G and 0 <= yy < G:
                    px[xx, yy] = cor + (255,)


def _espada(px, cabo, ponta, lamina, fio, guarda):
    """Espada em pixels: lamina larga (3) com fio claro, guarda e cabo."""
    (cx, cy), (tx, ty) = cabo, ponta
    L = math.hypot(tx - cx, ty - cy)
    ux, uy = (tx - cx) / L, (ty - cy) / L
    nx, ny = -uy, ux
    g = (cx + ux * 9, cy + uy * 9)                     # a guarda
    _linha(px, g, (tx - ux * 3, ty - uy * 3), lamina, 4)
    _linha(px, (g[0] + nx * 1.5, g[1] + ny * 1.5), (tx - ux * 3 + nx * 1.5, ty - uy * 3 + ny * 1.5), fio, 1)
    _linha(px, (tx - ux * 4, ty - uy * 4), (tx, ty), fio, 2)
    _linha(px, (g[0] - nx * 6, g[1] - ny * 6), (g[0] + nx * 6, g[1] + ny * 6), guarda, 3)
    _linha(px, (cx, cy), g, (40, 40, 56), 3)
    px[int(cx), int(cy)] = guarda + (255,)


def espadas():
    f = nova()
    px = f.load()
    # a Elucidator (preta, fio prateado) e a Dark Repulser (cristal azul), cruzadas
    _espada(px, (36, 77), (76, 29), (22, 22, 32), (170, 180, 210), (150, 160, 190))
    _espada(px, (72, 77), (32, 29), (30, 90, 220), (170, 230, 255), (120, 200, 255))
    # a agulha de costura no meio (clara, com o buraco em cima)
    _linha(px, (54, 26), (54, 84), (230, 240, 250), 3)
    _linha(px, (54, 84), (54, 87), (255, 255, 255), 1)
    for y in (31, 32, 33):
        px[54, y] = (20, 34, 74, 255)                    # o buraco da agulha
    # o fio, saindo do buraco e fazendo o infinito na frente das espadas
    for k in range(480):
        a = 2 * math.pi * k / 480
        x = 54 + 22 * math.sin(a)
        y = 62 + 9 * math.sin(a) * math.cos(a)
        for e in (0, 1):
            xx, yy = int(round(x)), int(round(y)) + e
            if 0 <= xx < G and 0 <= yy < G:
                px[xx, yy] = (CIANO if e == 0 else (0, 140, 180)) + (255,)
    f = contorno(f, (2, 3, 8))
    anel(f, 33, (0, 120, 160))
    return fundo_holo(), f


# ── opcao 3: o monograma TF ───────────────────────────────────────────
def tf():
    f = nova()
    d = ImageDraw.Draw(f)
    ciano = CIANO + (255,)
    escuro = (0, 90, 120, 255)
    # o T: barra chanfrada e, no lugar da haste, uma espada apontando para baixo
    d.polygon([(31, 34), (57, 34), (60, 37), (57, 40), (31, 40), (28, 37)], fill=ciano)
    d.rectangle((42, 40, 45, 70), fill=(28, 28, 40, 255))
    d.line((43, 42, 43, 68), fill=(170, 180, 210, 255))
    d.polygon([(42, 70), (45, 70), (43, 75), (44, 75)], fill=(170, 180, 210, 255))
    d.rectangle((38, 40, 49, 42), fill=(150, 160, 190, 255))
    # o F: chanfrado, encaixado ao lado do T
    d.polygon([(53, 46), (80, 46), (77, 52), (59, 52), (59, 57), (74, 57), (71, 62), (59, 62), (59, 76), (53, 76)],
              fill=ciano)
    d.line((54, 47, 54, 75), fill=(200, 255, 255, 255))
    f = contorno(f, (0, 60, 90))
    anel(f, 33, (0, 120, 160), esp=2)
    return fundo_holo(), f


OPCOES = {'yoru': yoru, 'espadas': espadas, 'tf': tf}


def montar(fundo, frente, lado):
    im = fundo.copy()
    im.alpha_composite(frente)
    return im.resize((lado, lado), Image.NEAREST)


def gravar(nome, pasta):
    fundo, frente = OPCOES[nome]()
    fundo.resize((432, 432), Image.NEAREST).save(os.path.join(pasta, 'icone_fundo.png'))
    frente.resize((432, 432), Image.NEAREST).save(os.path.join(pasta, 'icone_frente.png'))
    junto = montar(fundo, frente, G * 5)
    lado = 512
    final = Image.new('RGBA', (lado, lado), FUNDO + (255,))
    final.paste(junto, ((lado - junto.width) // 2, (lado - junto.height) // 2))
    final.convert('RGB').save(os.path.join(pasta, 'icon.png'))
    print('gravado:', nome, '->', pasta)


def abertura(nome, pasta):
    """presplash.png (900 px): o mesmo medalhao do icone no fundo do app (#020204)."""
    fundo, frente = OPCOES[nome]()
    junto = montar(fundo, frente, G * 6)                   # 648 px, pixel de 6
    m = 76 * 6 // 2
    c = junto.width // 2
    corte = junto.crop((c - m, c - m, c + m, c + m))
    mask = Image.new('L', corte.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, corte.width - 1, corte.height - 1), fill=255)
    tela = Image.new('RGB', (900, 900), (2, 2, 4))
    tela.paste(corte, ((900 - corte.width) // 2, (900 - corte.height) // 2), mask)
    tela.save(os.path.join(pasta, 'presplash.png'))
    print('abertura gravada')


def previa(pasta):
    """As 3 opcoes grandes e como ficam na tela inicial (circulo, quadrado arredondado, pequeno)."""
    os.makedirs(pasta, exist_ok=True)
    W, H = 3 * 360 + 40, 760
    tela = Image.new('RGB', (W, H), (18, 18, 24))
    d = ImageDraw.Draw(tela)
    for i, nome in enumerate(OPCOES):
        fundo, frente = OPCOES[nome]()
        x0 = 20 + i * 360
        grande = montar(fundo, frente, 324)
        tela.paste(grande, (x0 + 8, 20))
        d.text((x0 + 8, 350), str(i + 1) + ') ' + nome, fill=(255, 230, 80))
        # como o Android corta: circulo e quadrado arredondado (so o miolo de 72 da grade aparece)
        m = 72
        corte = montar(fundo, frente, G * 4).crop(((G - m) * 2, (G - m) * 2, (G + m) * 2, (G + m) * 2))
        for j, forma in enumerate(('circulo', 'redondo')):
            ic = corte.resize((128, 128), Image.LANCZOS)
            mask = Image.new('L', (128, 128), 0)
            if forma == 'circulo':
                ImageDraw.Draw(mask).ellipse((0, 0, 127, 127), fill=255)
            else:
                ImageDraw.Draw(mask).rounded_rectangle((0, 0, 127, 127), 30, fill=255)
            tela.paste(ic, (x0 + 8 + j * 150, 380), mask)
        # no tamanho de verdade (48 dp num celular comum = ~130 px; aqui 64 px)
        peq = corte.resize((64, 64), Image.LANCZOS)
        mask = Image.new('L', (64, 64), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 63, 63), fill=255)
        tela.paste(peq, (x0 + 8, 540), mask)
        d.text((x0 + 80, 560), 'tamanho pequeno', fill=(150, 150, 170))
    tela.save(os.path.join(pasta, 'icones_opcoes.png'))
    for nome in OPCOES:
        fundo, frente = OPCOES[nome]()
        montar(fundo, frente, 540).save(os.path.join(pasta, 'icone_%s.png' % nome))
    print(os.path.join(pasta, 'icones_opcoes.png'))


if __name__ == '__main__':
    if sys.argv[1] == 'previa':
        previa(sys.argv[2])
    elif sys.argv[1] == 'usar':
        gravar(sys.argv[2], APP)
        abertura(sys.argv[2], APP)
