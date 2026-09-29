"""Limpa o mapa da cabeca tirado da referencia -> r1/cab_final.txt"""
import os
AQUI = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.join(AQUI, '..', 'r1')
m = [list(l) for l in open(os.path.join(R1, 'cabN.txt')).read().split('\n') if l]
H, W = len(m), len(m[0])
CAB = set('NJHIhU')
# 1) cabo de cristal (espada das costas) e o que sobra abaixo da nuca
for r in range(H):
    for c in range(W):
        ch = m[r][c]
        if r >= 43 and c < 41:
            m[r][c] = '.'
        elif 37 <= r < 43 and 10 <= c <= 34 and ch in 'OU0hIk':
            m[r][c] = 'J'
        elif r >= 46 and c >= 51 and ch not in 'SstT':
            m[r][c] = '.'                      # gola (o tronco desenha)
# 2) linha de baixo: so pescoco (pele) e cabelo da nuca
for c in range(W):
    if m[H - 1][c] in CAB and c > 40:
        m[H - 1][c] = '.'
# 3) texel de cabelo sozinho (nenhum vizinho igual): vira o tom mais comum em volta
for _ in range(2):
    novo = [l[:] for l in m]
    for r in range(H):
        for c in range(W):
            if m[r][c] in 'JHIh':
                v = [m[r + a][c + b] for a in (-1, 0, 1) for b in (-1, 0, 1)
                     if (a or b) and 0 <= r + a < H and 0 <= c + b < W and m[r + a][c + b] in 'NJHIh']
                if v and m[r][c] not in v:
                    novo[r][c] = max(set(v), key=v.count)
    m = novo
open(os.path.join(R1, 'cab_final.txt'), 'w').write('\n'.join(''.join(l) for l in m) + '\n')
print(W, H)
