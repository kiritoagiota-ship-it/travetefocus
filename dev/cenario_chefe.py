"""O CENARIO da luta contra o chefe (do desenho do usuario: lua vermelha em
eclipse, castelo, chao rachado em brasa), em pixel art grossa (1 ponto = 4 px
num celular de 720): 3 camadas que o app move em velocidades diferentes.
  chefe/cenario_ceu.png    ceu + lua (a linha de baixo e o horizonte)
  chefe/cenario_longe.png  montanhas e castelo (fundo transparente)
  chefe/cenario_chao.png   o chao, do horizonte para baixo
uso: python dev/cenario_chefe.py [PREVIA.png]"""
import os
import sys
import math
import numpy as np
from PIL import Image

APP = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'chefe')
W = 200                    # um pouco mais largo que a tela (180): sobra para a camera andar
H_CEU, H_LONGE, H_CHAO = 270, 120, 150
rnd = np.random.default_rng(11)


def ruido(w, h, escala, semente):
    r = np.random.default_rng(semente)
    gw, gh = int(w / escala) + 3, int(h / escala) + 3
    g = r.random((gh, gw))
    ys, xs = np.mgrid[0:h, 0:w]
    fx, fy = xs / escala, ys / escala
    x0, y0 = fx.astype(int), fy.astype(int)
    tx, ty = fx - x0, fy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = g[y0, x0] * (1 - tx) + g[y0, x0 + 1] * tx
    b = g[y0 + 1, x0] * (1 - tx) + g[y0 + 1, x0 + 1] * tx
    return a * (1 - ty) + b * ty


def faixas(v, cores):
    """v 0..1 -> cor da faixa (sem degrade: degraus, com a borda em xadrez)."""
    n = len(cores)
    h, w = v.shape
    ys, xs = np.mgrid[0:h, 0:w]
    f = v * (n - 1)
    i = np.floor(f).astype(int)
    fr = f - i
    sobe = (fr > 0.72) & (((xs + ys) % 2) == 0) | (fr > 0.9)
    i = np.clip(i + sobe.astype(int), 0, n - 1)
    return np.array(cores, np.uint8)[i]


def ceu():
    h, w = H_CEU, W
    ys, xs = np.mgrid[0:h, 0:w]
    alto = 1.0 - ys / float(h - 1)                         # 1 no topo, 0 no horizonte
    nuv = 0.6 * ruido(w, h, 26, 1) + 0.4 * ruido(w, h, 9, 2)
    v = np.clip((1 - alto) ** 1.6 * 0.75 + (nuv - 0.5) * 0.55 * (1 - alto * 0.6), 0, 1)
    img = faixas(v, [(7, 4, 9), (14, 5, 11), (24, 6, 13), (40, 7, 15), (62, 9, 17), (92, 12, 20), (128, 16, 22)])
    # a lua em eclipse: disco escuro, aro aceso e um halo irregular
    cx, cy, R = int(w * 0.63), int(h * 0.34), 40
    d = np.hypot(xs - cx, ys - cy)
    halo = ruido(w, h, 7, 5)
    ang = np.arctan2(ys - cy, xs - cx)
    img[(d < R + 22 + halo * 16) & (d >= R)] = (70, 8, 16)
    img[(d < R + 11 + halo * 10) & (d >= R)] = (130, 14, 20)
    img[(d < R + 5 + halo * 5) & (d >= R)] = (196, 22, 24)
    img[(d < R + 2.2) & (d >= R - 0.5)] = (255, 70, 44)
    img[(d < R + 1.0) & (d >= R - 0.5) & (np.sin(ang * 3 + 1) > 0.2)] = (255, 170, 110)
    img[d < R - 0.5] = (15, 5, 10)
    img[(d < R - 0.5) & (ruido(w, h, 11, 8) > 0.62)] = (24, 7, 13)
    return img


def longe():
    h, w = H_LONGE, W
    img = np.zeros((h, w, 4), np.uint8)
    xs = np.arange(w)
    # montanhas ao fundo
    serra = 16 + 14 * ruido(w, 2, 22, 3)[0] + 9 * ruido(w, 2, 7, 4)[0]
    serra2 = 8 + 12 * ruido(w, 2, 30, 6)[0] + 5 * ruido(w, 2, 5, 7)[0]
    for x in xs:
        img[h - int(serra[x]):, x] = (20, 6, 13, 255)
        img[h - int(serra2[x]):, x] = (13, 4, 9, 255)
    # o castelo (a direita): torres pontudas
    def torre(x0, larg, alt, ponta):
        x1 = x0 + larg
        img[h - alt:, x0:x1] = (11, 4, 9, 255)
        for k in range(ponta):                              # telhado em agulha
            a = int(round(larg / 2.0 * (1 - k / float(ponta))))
            m = x0 + larg // 2
            img[h - alt - k - 1, max(0, m - a):m + a + 1] = (11, 4, 9, 255)
        img[h - alt:, x0] = (34, 8, 16, 255)                # a luz da lua na quina
        for j in range(3):                                  # janelas acesas
            jy = h - alt + 6 + j * 13 + int(rnd.integers(0, 4))
            if jy < h - 6 and larg > 4:
                img[jy:jy + 3, x0 + larg // 2] = (230, 40, 26, 255)
    for x0, larg, alt, ponta in ((142, 9, 44, 10), (153, 13, 78, 22), (168, 8, 58, 14), (177, 11, 40, 9),
                                 (160, 5, 96, 12), (189, 9, 50, 12), (136, 5, 30, 7)):
        torre(x0, larg, alt, ponta)
    img[h - 22:, 138:W] = np.where(img[h - 22:, 138:W, 3:4] > 0, img[h - 22:, 138:W], (11, 4, 9, 255))
    # estandarte com o losango (como no desenho)
    img[h - 60:h - 30, 156:162] = (60, 8, 14, 255)
    img[h - 50:h - 44, 158:160] = (200, 30, 22, 255)
    return img


def chao():
    h, w = H_CHAO, W
    ys, xs = np.mgrid[0:h, 0:w]
    fundo = ys / float(h - 1)
    pedra = 0.55 * ruido(w, h, 14, 21) + 0.45 * ruido(w, h, 4, 22)
    v = np.clip((1 - fundo) ** 1.3 * 0.8 + (pedra - 0.5) * 0.35, 0, 1)
    img = faixas(v, [(4, 2, 5), (8, 3, 7), (14, 5, 10), (22, 6, 12), (34, 8, 14), (50, 10, 16)])
    img[0] = (96, 14, 20)                                     # a linha do horizonte
    img[1, ::2] = (70, 10, 18)
    # fendas de lava abrindo em leque do horizonte para a frente
    luz = np.zeros((h, w), int)
    for k in range(11):
        x = w * (0.06 + 0.88 * k / 10.0) + rnd.uniform(-4, 4)
        dxdy = (x - w / 2.0) / (h * 0.55)
        y = rnd.uniform(2, 20)
        while y < h - 1:
            passo = rnd.integers(4, 11)
            desvio = rnd.uniform(-1.3, 1.3)
            for _ in range(passo):
                xi, yi = int(round(x)), int(y)
                if 0 <= xi < w and yi < h:
                    luz[yi, xi] = max(luz[yi, xi], 2)
                    for dx in (-1, 1):
                        if 0 <= xi + dx < w:
                            luz[yi, xi + dx] = max(luz[yi, xi + dx], 1)
                y += 1
                x += dxdy * (0.5 + 1.2 * y / h) + desvio * 0.5
                if y >= h - 1:
                    break
            if rnd.random() < 0.25:
                y += rnd.integers(3, 9)                         # a fenda some e volta
    perto = (1 - fundo)
    img[(luz == 1) & (perto > 0.25)] = (120, 14, 18)
    img[(luz == 1) & (perto <= 0.25)] = (60, 8, 14)
    img[(luz == 2) & (perto > 0.55)] = (255, 96, 44)
    img[(luz == 2) & (perto <= 0.55) & (perto > 0.25)] = (230, 40, 26)
    img[(luz == 2) & (perto <= 0.25)] = (130, 16, 20)
    return img


if __name__ == '__main__':
    c, l, g = ceu(), longe(), chao()
    os.makedirs(APP, exist_ok=True)
    Image.fromarray(c).save(os.path.join(APP, 'cenario_ceu.png'), optimize=True)
    Image.fromarray(l).save(os.path.join(APP, 'cenario_longe.png'), optimize=True)
    Image.fromarray(g).save(os.path.join(APP, 'cenario_chao.png'), optimize=True)
    for n in ('ceu', 'longe', 'chao'):
        print(n, os.path.getsize(os.path.join(APP, 'cenario_%s.png' % n)) // 1024, 'KB')
    if len(sys.argv) > 1:
        full = np.zeros((H_CEU + H_CHAO, W, 3), np.uint8)
        full[:H_CEU] = c
        a = l[..., 3:4] > 0
        full[H_CEU - H_LONGE:H_CEU] = np.where(a, l[..., :3], full[H_CEU - H_LONGE:H_CEU])
        full[H_CEU:] = g
        Image.fromarray(full).resize((W * 3, (H_CEU + H_CHAO) * 3), Image.NEAREST).save(sys.argv[1])
        print(sys.argv[1])
