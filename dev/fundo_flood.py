"""Mascara do fundo: pixels escuros ligados a borda da imagem (preenchimento
a partir das bordas), para fundos quase pretos iguais ao preto do cabelo."""
import numpy as np
from collections import deque


def mascara(nat, fundo=(2, 5, 13), tol=9.0):
    H, W = nat.shape[:2]
    perto = np.linalg.norm(nat - np.array(fundo, float), axis=2) < tol
    m = np.zeros((H, W), bool)
    fila = deque()
    for y in range(H):
        for x in (0, W - 1):
            if perto[y, x] and not m[y, x]:
                m[y, x] = True; fila.append((y, x))
    for x in range(W):
        for y in (0, H - 1):
            if perto[y, x] and not m[y, x]:
                m[y, x] = True; fila.append((y, x))
    while fila:
        y, x = fila.popleft()
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + a, x + b
            if 0 <= yy < H and 0 <= xx < W and perto[yy, xx] and not m[yy, xx]:
                m[yy, xx] = True; fila.append((yy, xx))
    return m
