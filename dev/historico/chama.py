"""Rascunho das chamas em quadros (pixel art)."""
import math, random

N_QUADROS = 8


def quadro_chama(w, h, f, n=N_QUADROS, inclina=-0.3, semente=0):
    """Um quadro de uma lingua de fogo w x h texels (y=0 embaixo).
    Devolve {(x, y): nivel} com nivel 0 (borda escura) .. 3 (miolo claro).
    O ciclo de n quadros fecha (loop): a lingua balanca, se divide numa
    lambida do lado de vez em quando e a ponta se solta e sobe."""
    dois_pi = 2 * math.pi
    fs = f / float(n)
    rnd = random.Random(semente * 1000 + f)
    out = {}

    def perfil(u):
        # larga embaixo (bojo em ~25% da altura), afina ate a ponta
        return (1.0 - u) ** 1.15 * (1.0 - 0.55 * math.exp(-u * 8.0))

    alt = h * (0.8 + 0.12 * math.sin(dois_pi * (fs + semente * 0.21)))    # a lingua respira
    lado = 1 if (semente % 2) else -1
    lambida = 0.5 + 0.5 * math.sin(dois_pi * (fs * 2 + semente * 0.4))    # forca da lambida do lado
    solta_y = alt + (h - alt) * fs * 1.1 - 1
    solta_r = max(0.0, 1.2 - 1.3 * fs) * (w / 6.0)
    for y in range(h):
        u = y / max(1.0, alt)
        for x in range(w):
            melhor = None
            if u < 1.0:
                cx = (w - 1) / 2.0 + math.sin(dois_pi * (fs + u * 0.8 + semente * 0.37)) * u * w * 0.2 \
                    + inclina * u * alt * 0.3
                meia = (w / 2.0) * perfil(u) / 0.62
                d = abs(x - cx) / max(0.45, meia)
                melhor = (d, u)
                # lambida do lado: sai do bojo e sobe mais curta
                if lambida > 0.35:
                    u2 = (y - alt * 0.22) / max(1.0, alt * 0.55 * lambida)
                    if 0 <= u2 < 1:
                        cx2 = cx + lado * (1.2 + 2.2 * u2) * (w / 8.0)
                        m2 = (w / 4.2) * (1 - u2) ** 1.2
                        d2 = abs(x - cx2) / max(0.4, m2)
                        if d2 < d:
                            melhor = (d2 * 1.08 + 0.1, u + 0.12)
            if solta_r > 0.35:                                   # gota de fogo que se soltou
                bx = (w - 1) / 2.0 + inclina * alt * 0.3 + math.sin(dois_pi * fs) * 0.6
                db = math.hypot((x - bx) / max(0.6, solta_r), (y - solta_y) / max(0.8, solta_r * 1.6))
                if db <= 1.0 and (melhor is None or db < melhor[0]):
                    melhor = (db * 0.9 + 0.35, 0.9)
            if melhor is None:
                continue
            d, uu = melhor
            if d > 1.0 + rnd.uniform(-0.1, 0.04):
                continue
            if d < 0.3 and uu < 0.32:
                nivel = 3
            elif d < 0.58 and uu < 0.62:
                nivel = 2
            elif d < 0.82:
                nivel = 1
            else:
                nivel = 0
            if uu > 0.78:
                nivel = min(nivel, 1)
            out[(x, y)] = nivel
    return out
