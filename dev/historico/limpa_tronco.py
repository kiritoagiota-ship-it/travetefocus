"""Tronco: recorta da referencia (x 49-84, y 49-93), tira pescoco e braco
da frente, preenche o peito escondido com o casaco -> r1/tronco_final.txt"""
import os
AQUI = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.join(AQUI, '..', 'r1')
src = [l for l in open(os.path.join(R1, 'tronco_nat.txt')).read().split('\n') if l]
X0, Y0 = 46, 48                        # origem do tronco_nat na grade nativa
x0, x1, y0, y1 = 49, 85, 49, 94
m = [list(src[y - Y0][x0 - X0:x1 - X0]) for y in range(y0, y1)]
H, W = len(m), len(m[0])


def put(x, y, ch):
    if 0 <= y - y0 < H and 0 <= x - x0 < W:
        m[y - y0][x - x0] = ch


# pescoco e queixo: e da cabeca
for r in range(H):
    for c in range(W):
        if m[r][c] in 'SstT' and r < 8:
            m[r][c] = '.'
# o braco da frente cobre o peito (x >= 76): vira casaco. A frente do peito
# desce em curva do ombro (x 83, y 57) ate a cintura (x 80, y 84)
for y in range(y0, y1):
    frente = 83 if y < 62 else (82 if y < 72 else 81)
    for x in range(76, x1):
        if y < 55:
            continue
        if x > frente:
            put(x, y, '.')
        elif x == frente:
            put(x, y, 'c' if y < 80 else 'A')
        else:
            ch = m[y - y0][x - x0]
            if ch not in 'Z9Ok+':
                put(x, y, 'A' if (x + y) % 7 == 0 else 'C')
# cinto passa por baixo do braco ate a frente
for y in range(79, 84):
    for x in range(74, 82):
        put(x, y, '2' if y in (79, 83) else 'P')
# as costas: a bainha/cabo de cristal que aparece na borda (x 49-56) sai
for y in range(y0, 80):
    for x in range(49, 57):
        ch = m[y - y0][x - x0]
        if ch in 'k+GOZ09a':
            put(x, y, 'C')
open(os.path.join(R1, 'tronco_final.txt'), 'w').write('\n'.join(''.join(l) for l in m) + '\n')
print(W, H)
