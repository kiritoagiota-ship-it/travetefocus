pc = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(pc, encoding='utf-8').read()


def troca(a, b):
    global c
    assert c.count(a) == 1, a[:80]
    c = c.replace(a, b)


troca("""    'katana': ((1.0, 1.0, 1.0), (0.72, 0.96, 1.0), (0.22, 0.78, 1.0), (0.10, 0.42, 0.92),
               (0.20, 0.16, 0.60), (0.30, 0.85, 1.0)),
    'azul': ((0.90, 0.97, 1.0), (0.55, 0.80, 1.0), (0.20, 0.47, 1.0), (0.10, 0.25, 0.80),
             (0.26, 0.14, 0.58), (0.25, 0.50, 1.0)),""",
      """    'katana': ((1.0, 1.0, 1.0), (0.62, 0.92, 1.0), (0.22, 0.62, 1.0), (0.16, 0.30, 0.90),
               (0.30, 0.16, 0.66), (0.30, 0.70, 1.0)),
    'azul': ((0.92, 0.95, 1.0), (0.58, 0.72, 1.0), (0.28, 0.40, 1.0), (0.22, 0.20, 0.82),
             (0.34, 0.12, 0.60), (0.35, 0.45, 1.0)),""")
troca("""                if -off < max(u * 1.05, g * 0.09):
                    px = luz                                    # fio da lamina
                else:
                    a += max(0.0, 0.3 - s) * 1.3                # rabo: mais escuro
                    if a < 0.3:
                        px = clara
                    elif a < 0.6:
                        px = cor
                    elif a < 0.82:
                        px = escura
                    elif a < 1.0 and (i + j) % 2 == 0:
                        px = funda
                    else:
                        continue""", """                if -off < max(u * 1.05, g * 0.09):
                    px = luz                                    # fio da lamina
                elif 0.40 < a < 0.47 and int(s * 38) % 5:
                    px = clara                                  # riscos de velocidade
                elif 0.68 < a < 0.73 and int(s * 29) % 4:
                    px = cor
                else:
                    a += max(0.0, 0.3 - s) * 1.3                # rabo: mais escuro
                    a += _BAYER[j & 1][i & 1]                   # degraus pontilhados
                    if a < 0.26:
                        px = clara
                    elif a < 0.56:
                        px = cor
                    elif a < 0.8:
                        px = escura
                    elif a < 1.0 and (i + j) % 2 == 0:
                        px = funda
                    else:
                        continue""")
troca("""def _desenho_corte(arco, pal, u):""", """_BAYER = ((-0.045, 0.015), (0.045, -0.015))     # pontilhado 2x2 nas bordas das faixas


def _desenho_corte(arco, pal, u):""")
open(pc, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
