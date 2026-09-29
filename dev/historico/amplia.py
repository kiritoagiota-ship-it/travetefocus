"""Amplia mapas de pixel art (caracteres) em 1,5x: Scale3x (AdvMAME3x) e
reducao 2:1 pegando o pixel central do bloco - mantem bordas e diagonais."""


def scale3x(m):
    H, W = len(m), len(m[0])

    def px(y, x):
        y = min(H - 1, max(0, y))
        x = min(W - 1, max(0, x))
        return m[y][x]
    out = [[None] * (W * 3) for _ in range(H * 3)]
    for y in range(H):
        for x in range(W):
            A, B, C = px(y - 1, x - 1), px(y - 1, x), px(y - 1, x + 1)
            D, E, F = px(y, x - 1), px(y, x), px(y, x + 1)
            G, Hh, I = px(y + 1, x - 1), px(y + 1, x), px(y + 1, x + 1)
            e = [E] * 9
            if B != Hh and D != F:
                e[0] = D if D == B else E
                e[1] = B if (D == B and E != C) or (B == F and E != A) else E
                e[2] = F if B == F else E
                e[3] = D if (D == B and E != G) or (D == Hh and E != A) else E
                e[5] = F if (B == F and E != I) or (Hh == F and E != C) else E
                e[6] = D if D == Hh else E
                e[7] = Hh if (D == Hh and E != I) or (Hh == F and E != G) else E
                e[8] = F if Hh == F else E
            for k in range(9):
                out[y * 3 + k // 3][x * 3 + k % 3] = e[k]
    return out


def amplia(mapa):
    """mapa (lista de strings) 1x -> 1,5x."""
    g = scale3x([list(l) for l in mapa])
    H, W = len(g), len(g[0])
    res = []
    for y in range(0, H - 1, 2):
        res.append(''.join(g[y + (1 if y % 4 == 0 else 0)][x + (1 if x % 4 == 0 else 0)]
                           for x in range(0, W - 1, 2)))
    return res
