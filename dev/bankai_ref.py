"""Copia os desenhos da referencia do Bankai (referencias/2026-09-29_bankai_referencia.png,
6 poses em 3x2 quadros de 512 px) para pixel art LIMPA na grade nativa:
1) reduz a imagem a uma paleta curta (k-medias + cores fixas de pele, branco
   e olho, para o rosto nao virar roxo);
2) cada bloco de `s` px vira 1 pixel com a cor que MAIS aparece nele (pele,
   branco e olho valem o dobro: detalhe pequeno nao some) - bordas duras,
   sem borrao;
3) o fundo quase preto ligado a borda do quadro vira transparente;
4) tira pixels soltos.
A escala (s = 2.65 px por pixel) deixa o Bankai ~15% mais alto que o Yoru
normal (157 -> ~180 pixels), com o pixel do mesmo tamanho.
uso: python dev/bankai_ref.py POSE(1-6) SAIDA.png [s=2.65] [n_cores=28]
     python dev/bankai_ref.py todas PASTA"""
import os
import sys
from collections import deque
import numpy as np
from PIL import Image

REF = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'referencias',
                   '2026-09-29_bankai_referencia.png')
S_PADRAO = 2.65
FIXAS = np.array([(250, 205, 192), (228, 172, 168), (192, 126, 140),     # pele
                  (246, 238, 230),                                      # branco
                  (176, 72, 208), (120, 40, 170)], float)               # olho / iris
PESO_FIXAS = 2.0


def kmedias(px, k, iters=14, semente=3):
    rnd = np.random.default_rng(semente)
    amostra = px[rnd.choice(len(px), min(len(px), 50000), replace=False)]
    ordem = np.argsort(amostra.sum(axis=1))
    c = amostra[ordem[np.linspace(0, len(ordem) - 1, k).astype(int)]].copy()
    for _ in range(iters):
        d = ((amostra[:, None, :] - c[None, :, :]) ** 2).sum(axis=2)
        lab = d.argmin(axis=1)
        for i in range(k):
            m = amostra[lab == i]
            if len(m):
                c[i] = m.mean(axis=0)
    return c


def extrair(pose, s=S_PADRAO, k=28, tol=15.0):
    im = np.asarray(Image.open(REF).convert('RGB')).astype(float)
    col, lin = (pose - 1) % 3, (pose - 1) // 3
    q = im[lin * 512:(lin + 1) * 512, col * 512:(col + 1) * 512]
    H, W = q.shape[:2]
    cores = np.concatenate([kmedias(q.reshape(-1, 3), k), FIXAS])
    nf = len(FIXAS)
    d = ((q.reshape(-1, 3)[:, None, :] - cores[None, :, :]) ** 2).sum(axis=2)
    idx = d.argmin(axis=1).reshape(H, W)
    peso = np.ones(len(cores))
    peso[-nf:] = PESO_FIXAS
    h, w = int(H / s), int(W / s)
    nat = np.zeros((h, w), int)
    for y in range(h):
        for x in range(w):
            bl = idx[int(y * s):int((y + 1) * s), int(x * s):int((x + 1) * s)].ravel()
            cont = np.bincount(bl, minlength=len(cores)) * peso
            nat[y, x] = int(cont.argmax())
    rgb = cores[nat]
    borda = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    fundo = np.median(borda, axis=0)
    perto = np.linalg.norm(rgb - fundo, axis=2) < tol
    m = np.zeros((h, w), bool)
    fila = deque()
    for y in range(h):
        for x in range(w):
            if (y in (0, h - 1) or x in (0, w - 1)) and perto[y, x]:
                m[y, x] = True
                fila.append((y, x))
    while fila:
        y, x = fila.popleft()
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + a, x + b
            if 0 <= yy < h and 0 <= xx < w and perto[yy, xx] and not m[yy, xx]:
                m[yy, xx] = True
                fila.append((yy, xx))
    for _ in range(2):                                   # pixel solto vira fundo
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if not m[y, x] and m[y - 1:y + 2, x - 1:x + 2].sum() >= 7:
                    m[y, x] = True
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    rgba[..., 3] = np.where(m, 0, 255)
    return rgba


if __name__ == '__main__':
    if sys.argv[1] == 'todas':
        pasta = sys.argv[2]
        os.makedirs(pasta, exist_ok=True)
        for p in range(1, 7):
            rgba = extrair(p)
            Image.fromarray(rgba, 'RGBA').save(os.path.join(pasta, f'bruto{p}.png'))
            ys, xs = np.nonzero(rgba[..., 3])
            print(p, rgba.shape[1], 'x', rgba.shape[0], '| personagem', xs.max() - xs.min() + 1, 'x',
                  ys.max() - ys.min() + 1)
    else:
        pose = int(sys.argv[1])
        rgba = extrair(pose, float(sys.argv[3]) if len(sys.argv) > 3 else S_PADRAO,
                       int(sys.argv[4]) if len(sys.argv) > 4 else 28)
        Image.fromarray(rgba, 'RGBA').save(sys.argv[2])
