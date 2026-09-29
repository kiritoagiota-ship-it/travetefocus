"""Cabeca do Yoru na grade fina: rosto (mapa a mao) + cabelo em mechas.
Coordenadas de desenho: coluna para a direita, linha para BAIXO (como no
mapa); o angulo das mechas e em graus na tela (0 = direita, 90 = cima).
uso: python cab5.py  -> r1/cab5.png (referencia x nosso)"""
import os, sys, math
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito as K

AQUI = os.path.dirname(os.path.abspath(__file__))
W, H = 56, 56

# rosto: '.' = nao e rosto (o cabelo/cranio aparece). Colunas 12-45, linhas 30-53
ROSTO = {
    33: (30, "..ts...."),
    34: (29, ".tsst..."),
    35: (28, "tsSSSs.."),
    36: (27, "tsSSSSSs......."),
    37: (26, "tsSSSSSEEEEEEEEE.."),
    38: (15, "......ttsS.SSSSSSSEnneeeeeEsS"),
    39: (15, ".....tsSStsSSSSSSSinneEee3sSS"),
    40: (15, "....tsSSSstSSSSSSSii33ee33sSSs"),
    41: (15, "....tsSSSSstSSSSSSSi3mmm3sSSSS"),
    42: (15, "....tsSttSstSSSSSSSSsmmmsSSSSS"),
    43: (15, "....tsSStSstSSSSSSSSSsssSSSSSSS"),
    44: (15, "....tssSSsstSSSSSSSSSSSSSSSSSSS"),
    45: (15, ".....tssstsSSSSSSSSSSSSSSSSSSSs"),
    46: (15, "......tttssSSSSSSSSSSSSSSSSSSSs"),
    47: (15, "......tssSSSSSSSSSSSSSSSSSSSSs."),
    48: (15, "......tsSSSSSSSSSSSSSSSSStsSss.."),
    49: (15, "......tssSSSSSSSSSSSSSSSSSSSs..."),
    50: (15, "......ttssSSSSSSSSSSSSSSSSSs...."),
    51: (15, ".......tssssSSSSSSSSSSSSSs....."),
    52: (15, "........tttssssssssssssss......"),
}


def fita(x0, y0, ang0, comp, curva, larg, passo=0.4):
    """Como kirito._fita, em coordenadas de tela com y para BAIXO."""
    f = K._fita(x0, -y0, ang0, comp, curva, larg, passo)
    return {(x, -y): v for (x, y), v in f.items()}


# mechas: (col, lin da raiz, angulo, comprimento, meia-largura (luz, sombra), curva total, tipo)
# tipo: 'massa' (cabelo de tras/cranio), 'franja', 'fio' (fio solto fino)
MECHAS = [
    # cranio (de tras para a frente), formam o volume
    (20, 22, -100.0, 30.0, (9.0, 8.0), 14.0, 'massa'),
    (12, 18, -115.0, 30.0, (7.0, 7.0), 20.0, 'massa'),
    (24, 12, 175.0, 26.0, (8.0, 9.0), 14.0, 'massa'),
    (30, 16, 150.0, 22.0, (9.0, 9.0), 10.0, 'massa'),
    (34, 20, -95.0, 20.0, (9.0, 9.0), -6.0, 'massa'),
    # topo penteado para tras (vai para o tufo)
    (40, 10, 168.0, 30.0, (5.5, 5.5), 14.0, 'topo'),
    (44, 16, 160.0, 34.0, (5.0, 5.5), 22.0, 'topo'),
    # franja caindo na testa, pontas finas
    (30, 18, -78.0, 20.0, (4.5, 4.0), -8.0, 'franja'),
    (36, 17, -66.0, 22.0, (4.5, 4.5), -14.0, 'franja'),
    (42, 16, -58.0, 22.0, (4.5, 4.0), -22.0, 'franja'),
    (46, 14, -40.0, 16.0, (3.5, 3.5), -35.0, 'franja'),
    (24, 22, -88.0, 18.0, (4.0, 4.0), -4.0, 'franja'),
    # fios soltos no topo
    (26, 4, 100.0, 7.0, (1.0, 1.0), -25.0, 'fio'),
    (33, 4, 78.0, 6.0, (1.0, 1.0), -30.0, 'fio'),
    (42, 7, 45.0, 7.0, (1.0, 1.0), -35.0, 'fio'),
]


def cabeca(fase=0.0, vento=0.0):
    px = {}
    # cranio: base escura (garante que nao ha buraco entre as mechas)
    cx0, cy0, rx, ry = 26.0, 24.0, 22.0, 20.5
    for r in range(H):
        for c in range(W):
            if ((c - cx0) / rx) ** 2 + ((r - cy0) / ry) ** 2 <= 1.0:
                px[(c, r)] = 'J'
    # rosto por cima do cranio
    for r, (c0, txt) in ROSTO.items():
        for i, ch in enumerate(txt):
            if ch != '.':
                px[(c0 + i, r)] = ch
    cabelo = {}
    for i, (col, lin, ang, comp, (la, lb), cur, tipo) in enumerate(MECHAS):
        amp = 3.0 + 4.0 * vento

        def curva(u, cur=cur, i=i):
            return cur * u * u + amp * u * K._onda(fase, u, 0.7, i * 0.17)

        if tipo == 'fio':
            larg = lambda u, la=la: (la * (1 - u) + 0.3, la * (1 - u) + 0.3)
        else:
            larg = lambda u, la=la, lb=lb: (la * (1 - u) ** 0.8, lb * (1 - u) ** 1.1)
        f = fita(col, lin, ang, comp, curva, larg)
        for q, (u, v, Wd) in f.items():
            vf = v / Wd if Wd else 0.5
            if tipo == 'fio':
                ch = 'H'
            elif vf > 0.78 or u > 0.9:
                ch = 'J'                              # lado da sombra / ponta
            elif vf < 0.25 and 0.15 < u < 0.55 and tipo != 'massa':
                ch = 'h' if (vf < 0.12 and 0.25 < u < 0.42) else 'I'
            elif vf < 0.3 and 0.2 < u < 0.6:
                ch = 'I'
            else:
                ch = 'H'
            if q in cabelo and any((q[0] + a, q[1] + b) not in f for (a, b) in K._VIZ4):
                ch = 'J'                              # linha que separa as mechas
            cabelo[q] = ch
    px.update(cabelo)
    return px


def imagem(px, z, fundo=(31, 53, 80), cw=W, ch_=H):
    im = Image.new('RGB', (cw * z, ch_ * z), fundo)
    d = ImageDraw.Draw(im)
    for (c, r), ch in px.items():
        if 0 <= c < cw and 0 <= r < ch_:
            col = tuple(int(v * 255) for v in K._PALETA[ch][:3])
            d.rectangle([c * z, r * z, c * z + z - 1, r * z + z - 1], fill=col)
    return im


if __name__ == '__main__':
    ref = Image.open(os.path.join(AQUI, '..', 'refs', 'yoru_ref.jpg')).convert('RGB')
    z = 9
    rc = ref.crop((160, 38, 160 + int(W * 2.44), 38 + int(H * 2.44))).resize((W * z, H * z), Image.NEAREST)
    a = imagem(cabeca(0.0), z)
    S = Image.new('RGB', (W * z * 2 + 10, H * z), (20, 20, 30))
    S.paste(rc, (0, 0))
    S.paste(a, (W * z + 10, 0))
    S.save(os.path.join(AQUI, '..', 'r1', 'cab5.png'))
    print('ok')
