"""Desenho base (formas) do retrato do Yoru - o dev/retrato_pixel.py transforma em pixel art.
Desenho feito com formas (cabelo arrepiado, rosto 3/4 olhando para a
esquerda, olhos de anime, casaco de gola alta com a faixa ciano), pintado
com sombras e luz de contorno azul. Tres estilos a partir do mesmo desenho:
  silhueta  - escuro, so o contorno de luz e o olho aceso
  anime     - colorido (cel-shading) com luz azul
  holograma - linhas ciano de holograma, com as linhas de varredura
uso: python dev/retrato_anime.py PASTA [estilo ...]
     grava PASTA/retrato_<estilo>.png e retrato_<estilo>_fechado.png"""
import os
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops

W, H = 600, 500          # o desenho (x para a direita, y para BAIXO)
SS = 4                   # supersample (bordas lisas)


def S(pts):
    return [(x * SS, y * SS) for x, y in pts]


def mascara():
    return Image.new('L', (W * SS, H * SS), 0)


def poli(m, pts, v=255):
    ImageDraw.Draw(m).polygon(S(pts), fill=v)
    return m


def elipse(m, cx, cy, rx, ry, v=255):
    ImageDraw.Draw(m).ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=v)
    return m


def tira(m, pts, larg, v=255):
    ImageDraw.Draw(m).line(S(pts), fill=v, width=int(larg * SS), joint='curve')
    return m


# ── curvas ──────────────────────────────────────────────────
def bez(p0, p1, p2, n=28):
    out = []
    for i in range(n + 1):
        t = i / float(n)
        a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
        out.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return out


def suave(pts, n=10, fechado=True):
    """Catmull-Rom: passa por todos os pontos com curvas."""
    out = []
    k = len(pts)
    rng = range(k) if fechado else range(k - 1)
    for i in rng:
        p0 = pts[(i - 1) % k] if fechado or i > 0 else pts[0]
        p1 = pts[i]
        p2 = pts[(i + 1) % k]
        p3 = pts[(i + 2) % k] if fechado or i + 2 < k else pts[-1]
        for j in range(n):
            t = j / float(n)
            t2, t3 = t * t, t * t * t
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    if not fechado:
        out.append(pts[-1])
    return out


def lamina(base, ctrl, ponta, larg, curva_larg=1.0):
    """Mecha de anime: a linha do meio e uma curva, a largura afina ate a ponta."""
    c = bez(base, ctrl, ponta, 30)
    esq, dir_ = [], []
    for i, (x, y) in enumerate(c):
        t = i / float(len(c) - 1)
        if i < len(c) - 1:
            dx, dy = c[i + 1][0] - x, c[i + 1][1] - y
        else:
            dx, dy = x - c[i - 1][0], y - c[i - 1][1]
        L = max(1e-6, (dx * dx + dy * dy) ** 0.5)
        nx, ny = -dy / L, dx / L
        w = larg * 0.5 * (1 - t) ** curva_larg
        esq.append((x + nx * w, y + ny * w))
        dir_.append((x - nx * w, y - ny * w))
    return esq + dir_[::-1]


# ── o desenho (rosto 3/4 olhando para a esquerda) ──────────────
CRANIO = (314, 160, 74, 76)            # elipse: cx, cy, rx, ry
MECHAS_TRAS = [
    ((290, 120), (285, 72), (262, 34), 70),       # pra cima, um pouco para a frente
    ((322, 116), (350, 70), (372, 34), 62),
    ((350, 130), (420, 96), (470, 90), 66),       # as de tras (o "rabo" arrepiado)
    ((360, 160), (446, 150), (510, 162), 64),
    ((362, 190), (440, 200), (498, 232), 58),
    ((356, 214), (410, 246), (446, 290), 48),
    ((348, 236), (372, 276), (372, 318), 36),     # nuca
    ((262, 140), (220, 118), (188, 118), 54),     # do lado, para a frente
    ((340, 124), (382, 86), (414, 62), 44),       # mechas menores enchendo os vaos
    ((356, 176), (420, 178), (466, 198), 42),
    ((306, 118), (310, 80), (318, 54), 40),
]
FRANJA = [
    ((248, 150), (226, 206), (222, 256), 50),
    ((272, 140), (262, 204), (252, 240), 46),
    ((298, 138), (302, 184), (292, 214), 44),
    ((324, 140), (332, 196), (324, 224), 40),
    ((346, 152), (362, 204), (362, 250), 38),
    ((240, 168), (208, 192), (196, 226), 32),
]
MECHAS = MECHAS_TRAS + FRANJA
ROSTO = suave([(252, 160), (238, 196), (234, 226), (240, 256), (254, 282), (268, 300), (296, 300),
               (326, 288), (350, 262), (360, 228), (360, 168), (310, 150)], 8)
ORELHA = suave([(350, 222), (366, 218), (372, 236), (364, 256), (350, 252)], 6)
PESCOCO = [(298, 284), (336, 274), (340, 318), (300, 322)]
CASACO = suave([(110, 500), (150, 410), (222, 350), (300, 326), (372, 326), (446, 350), (514, 410),
                (560, 500)], 8)
GOLA_E = suave([(240, 500), (248, 380), (264, 322), (300, 296), (306, 340), (296, 500)], 6)
GOLA_D = suave([(334, 288), (384, 312), (408, 370), (430, 500), (346, 500), (340, 350)], 6)
CAMISA = [(296, 500), (306, 340), (340, 330), (346, 500)]
# olhos (olhando para a esquerda: o de perto e maior, a direita)
OLHO_PERTO = dict(cx=310, cy=234, rx=24, ry=17, iris=(305, 236, 12, 16))
OLHO_LONGE = dict(cx=257, cy=234, rx=14, ry=16, iris=(254, 236, 8, 15))


def camadas():
    """Mascaras (L) de cada parte, em supersample."""
    m = {}
    m['casaco'] = poli(mascara(), CASACO)
    m['gola'] = poli(poli(mascara(), GOLA_E), GOLA_D)
    m['camisa'] = poli(mascara(), CAMISA)
    m['pescoco'] = poli(mascara(), PESCOCO)
    m['rosto'] = poli(poli(mascara(), ROSTO), ORELHA)
    tras = elipse(mascara(), *CRANIO)
    for base, ctrl, ponta, larg in MECHAS_TRAS:
        poli(tras, lamina(base, ctrl, ponta, larg, 0.7))
    fr = mascara()
    for base, ctrl, ponta, larg in FRANJA:
        poli(fr, lamina(base, ctrl, ponta, larg, 0.7))
    m['cabelo_tras'] = tras
    m['franja'] = fr
    m['cabelo'] = ImageChops.lighter(tras, fr)
    # sombra do cabelo no rosto (o cabelo um pouco mais para baixo)
    sh = m['franja'].transform(m['franja'].size, Image.AFFINE, (1, 0, -6 * SS, 0, 1, -14 * SS))
    m['sombra_rosto'] = ImageChops.multiply(sh, m['rosto'])
    # a faixa ciano do casaco e a borda da gola
    f = mascara()
    tira(f, [(322, 340), (324, 500)], 8)
    tira(f, suave([(300, 296), (264, 322), (248, 380), (240, 500)], 6, fechado=False), 5)
    tira(f, suave([(334, 288), (384, 312), (408, 370), (430, 500)], 6, fechado=False), 5)
    m['faixa'] = f
    # mechas claras (o brilho do cabelo)
    b = mascara()
    for a0, a1 in ((0, 9), (12, 20), (23, 30)):                    # o anel de luz, quebrado pelas mechas
        tira(b, bez((236, 146), (300, 104), (372, 132), 30)[a0:a1], 9)
    for base, ctrl, ponta, larg in MECHAS:                         # um fio claro em cada mecha
        cc = bez(base, ctrl, ponta, 20)
        tira(b, cc[6:15], max(2, larg * 0.09))
    m['brilho_cab'] = ImageChops.multiply(b, m['cabelo'])
    # olhos
    for nome, o in (('perto', OLHO_PERTO), ('longe', OLHO_LONGE)):
        e = elipse(mascara(), o['cx'], o['cy'], o['rx'], o['ry'])
        m['olho_' + nome] = ImageChops.subtract(e, m['franja'])
        ix, iy, irx, iry = o['iris']
        m['iris_' + nome] = ImageChops.multiply(elipse(mascara(), ix, iy, irx, iry), m['olho_' + nome])
        m['pupila_' + nome] = ImageChops.multiply(elipse(mascara(), ix, iy + 1, irx * 0.45, iry * 0.55),
                                                  m['olho_' + nome])
        lid = mascara()
        tira(lid, [(o['cx'] - o['rx'] - 3, o['cy'] - 2), (o['cx'] - o['rx'] * 0.3, o['cy'] - o['ry'] - 2),
                   (o['cx'] + o['rx'] * 0.6, o['cy'] - o['ry'] - 1), (o['cx'] + o['rx'] + 3, o['cy'] - 4)],
             4 if nome == 'perto' else 3)
        m['palpebra_' + nome] = ImageChops.subtract(lid, m['franja'])
        brl = elipse(mascara(), ix + irx * 0.35, iy - iry * 0.4, irx * 0.32, iry * 0.25)
        elipse(brl, ix - irx * 0.35, iy + iry * 0.45, irx * 0.16, iry * 0.12)
        m['reflexo_' + nome] = ImageChops.multiply(brl, m['olho_' + nome])
        fech = mascara()
        tira(fech, [(o['cx'] - o['rx'], o['cy'] + 2), (o['cx'], o['cy'] + o['ry'] * 0.5),
                    (o['cx'] + o['rx'], o['cy'] + 1)], 4 if nome == 'perto' else 3)
        m['fechado_' + nome] = ImageChops.subtract(fech, m['franja'])
    boca = mascara()
    tira(boca, [(266, 284), (278, 285)], 2.5)
    m['boca'] = boca
    nariz = mascara()
    tira(nariz, [(248, 254), (244, 262), (252, 264)], 2.5)
    m['nariz'] = nariz
    sob = mascara()
    tira(sob, [(290, 206), (332, 200)], 4)
    tira(sob, [(244, 208), (268, 206)], 3)
    m['sobrancelha'] = ImageChops.subtract(sob, m['franja'])
    corpo = mascara()
    for k in ('casaco', 'gola', 'camisa', 'pescoco', 'rosto', 'cabelo'):
        corpo = ImageChops.lighter(corpo, m[k])
    m['corpo'] = corpo
    return m


def pinta(base, mask, cor, alfa=1.0):
    """Pinta `cor` (r,g,b 0..1) onde a mascara manda."""
    c = Image.new('RGBA', base.size, tuple(int(v * 255) for v in cor) + (255,))
    a = mask if alfa >= 1 else mask.point(lambda v: int(v * alfa))
    base.paste(c, (0, 0), a)


def contorno_luz(corpo, dx, larg):
    """A borda do lado da luz (deslocando a mascara)."""
    sh = corpo.transform(corpo.size, Image.AFFINE, (1, 0, dx * SS, 0, 1, 0))
    return ImageChops.subtract(corpo, sh).filter(ImageFilter.GaussianBlur(larg * SS * 0.3))


def brilho(mask, raio):
    return mask.filter(ImageFilter.GaussianBlur(raio * SS))


def desenhar(estilo, fechado=False):
    m = camadas()
    img = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
    olhos = ('perto', 'longe')
    if estilo == 'anime':
        pinta(img, m['casaco'], (0.05, 0.06, 0.1))
        pinta(img, m['camisa'], (0.02, 0.03, 0.06))
        pinta(img, m['gola'], (0.08, 0.09, 0.15))
        pinta(img, m['faixa'], (0.1, 0.85, 1.0))
        pinta(img, m['pescoco'], (0.62, 0.52, 0.6))
        pinta(img, m['cabelo_tras'], (0.07, 0.08, 0.15))
        pinta(img, m['rosto'], (0.96, 0.84, 0.78))
        pinta(img, m['sombra_rosto'], (0.72, 0.58, 0.66), 0.85)
        pinta(img, m['nariz'], (0.7, 0.52, 0.55))
        pinta(img, m['boca'], (0.55, 0.36, 0.4))
        pinta(img, m['sobrancelha'], (0.08, 0.08, 0.14))
        for o in olhos:
            if fechado:
                pinta(img, m['fechado_' + o], (0.1, 0.08, 0.14))
                continue
            pinta(img, m['olho_' + o], (0.97, 0.97, 1.0))
            pinta(img, m['iris_' + o], (0.12, 0.45, 0.95))
            pinta(img, m['pupila_' + o], (0.04, 0.12, 0.35))
            pinta(img, m['reflexo_' + o], (1, 1, 1))
            pinta(img, m['palpebra_' + o], (0.05, 0.04, 0.1))
        pinta(img, m['franja'], (0.07, 0.08, 0.15))
        pinta(img, m['brilho_cab'], (0.22, 0.35, 0.62), 0.8)
        rim = contorno_luz(m['corpo'], -7, 6)
        pinta(img, rim, (0.35, 0.75, 1.0), 0.95)
        pinta(img, brilho(rim, 6), (0.1, 0.5, 1.0), 0.6)
    elif estilo == 'silhueta':
        pinta(img, m['corpo'], (0.02, 0.035, 0.08))
        pinta(img, m['brilho_cab'], (0.06, 0.12, 0.24), 0.9)
        pinta(img, m['faixa'], (0.1, 0.75, 1.0), 0.9)
        rim = contorno_luz(m['corpo'], -6, 5)
        pinta(img, rim, (0.35, 0.8, 1.0))
        pinta(img, brilho(rim, 7), (0.1, 0.45, 1.0), 0.7)
        if not fechado:
            pinta(img, m['iris_perto'], (0.4, 0.95, 1.0))
            pinta(img, m['reflexo_perto'], (1, 1, 1))
            pinta(img, m['iris_longe'], (0.3, 0.8, 1.0), 0.8)
        else:
            pinta(img, m['fechado_perto'], (0.2, 0.5, 0.8), 0.6)
    elif estilo == 'holograma':
        pinta(img, m['corpo'], (0.0, 0.35, 0.55), 0.18)
        borda = ImageChops.subtract(m['corpo'], m['corpo'].filter(ImageFilter.MinFilter(9)))
        partes = mascara()
        for k in ('rosto', 'cabelo', 'gola', 'faixa', 'sombra_rosto'):
            partes = ImageChops.lighter(partes, ImageChops.subtract(m[k], m[k].filter(ImageFilter.MinFilter(5))))
        pinta(img, brilho(borda, 5), (0.0, 0.6, 1.0), 0.8)
        pinta(img, borda, (0.5, 0.95, 1.0))
        pinta(img, partes, (0.2, 0.85, 1.0), 0.7)
        pinta(img, m['brilho_cab'], (0.2, 0.8, 1.0), 0.35)
        for o in olhos:
            if fechado:
                pinta(img, m['fechado_' + o], (0.6, 1.0, 1.0))
            else:
                pinta(img, m['palpebra_' + o], (0.6, 1.0, 1.0))
                pinta(img, m['iris_' + o], (0.5, 1.0, 1.0), 0.9)
        # linhas de varredura
        lin = Image.new('L', img.size, 0)
        d = ImageDraw.Draw(lin)
        for y in range(0, H * SS, 5 * SS):
            d.rectangle([0, y, W * SS, y + 2 * SS], fill=110)
        a = img.getchannel('A')
        img.putalpha(ImageChops.subtract(a, ImageChops.multiply(lin, a)))
    return img.resize((W, H), Image.LANCZOS)


def olho_brilho(estilo):
    """Brilho do olho de perto (fica numa camada propria: pulsa no app)."""
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    m = elipse(Image.new('L', (W, H), 0), 296, 226, 16, 16)
    m = m.filter(ImageFilter.GaussianBlur(10))
    c = Image.new('RGBA', (W, H), (90, 220, 255, 255))
    g.paste(c, (0, 0), m)
    return g


if __name__ == '__main__':
    saida = sys.argv[1] if len(sys.argv) > 1 else '.'
    estilos = sys.argv[2:] or ['silhueta', 'anime', 'holograma']
    os.makedirs(saida, exist_ok=True)
    for e in estilos:
        desenhar(e).save(os.path.join(saida, f'retrato_{e}.png'))
        desenhar(e, fechado=True).save(os.path.join(saida, f'retrato_{e}_fechado.png'))
        print('ok', e)
