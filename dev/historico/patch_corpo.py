"""Desenho do corpo com mais forma:
- braco afina do ombro ao cotovelo e do cotovelo ao pulso (deltoide cheio,
  punho da luva mais largo, vinco escuro na dobra do cotovelo) - chega de
  "tubo" da mesma grossura;
- tronco que ESTICA e ENCOLHE (pose['estica'] = -1 encolhe, +1 estica): o
  peito, os ombros, os bracos e a cabeca descem/sobem 3 texels juntos -
  compressao na preparacao e no pouso, esticada no golpe e no impulso."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'kirito.py'), [
    ("""                 pernas_b=None, pt=0.0, vista='lado', cresce=1.0,""",
     """                 pernas_b=None, pt=0.0, vista='lado', cresce=1.0, estica=0,"""),
    # deslocamento do tronco de cima
    ("""def olhos_texel(p):""", """def _ds(p):
    \"\"\"Quanto o tronco de cima sobe (estica) ou desce (encolhe), em texels.\"\"\"
    return int(round(p.get('estica', 0) or 0)) * 3


def olhos_texel(p):"""),
    ("""    cab_x = cx + _GOLA[0] - _CAB_PESCOCO[0] + 4 * incl + int(round(p.get('hx', 0) or 0))
    cab_ty = hy + _GOLA[1] + _CAB_PESCOCO[1] + int(round(p.get('hy', 0) or 0))
    return [(cab_x + _OLHO5[0], cab_ty - _OLHO5[1])]""",
     """    cab_x = cx + _GOLA[0] - _CAB_PESCOCO[0] + 4 * incl + int(round(p.get('hx', 0) or 0))
    cab_ty = hy + _GOLA[1] + _CAB_PESCOCO[1] + int(round(p.get('hy', 0) or 0)) + _ds(p)
    return [(cab_x + _OLHO5[0], cab_ty - _OLHO5[1])]"""),
    ("""    mx = ax + R * incl + R * m[0]
    my = hy + 5 * R + R * m[1]""", """    mx = ax + R * incl + R * m[0]
    my = hy + 5 * R + R * m[1] + _ds(p)"""),
    ("""    return (cx, hy + 6, cx + _GOLA[0] - _CAB_PESCOCO[0] + 4 * incl, hy + _GOLA[1] + _CAB_PESCOCO[1])""",
     """    return (cx, hy + 6, cx + _GOLA[0] - _CAB_PESCOCO[0] + 4 * incl,
            hy + _GOLA[1] + _CAB_PESCOCO[1] + _ds(p))"""),
    ("""    o1 = (cx + _OMBRO1[0] + li, hy + _OMBRO1[1])
    o2 = (cx + _OMBRO2[0] + li, hy + _OMBRO2[1])
    cab_x = cx + _GOLA[0] - _CAB_PESCOCO[0] + li + int(round(p.get('hx', 0) or 0))
    cab_ty = hy + _GOLA[1] + _CAB_PESCOCO[1] + int(round(p.get('hy', 0) or 0))
    boca = (cx + int(2.5 * R), hy + int(1.6 * R))          # boca da bainha (cinto)
    # as maos continuam medidas a partir do ombro antigo (as poses sao as mesmas)
    am1 = (cx + int(2.5 * R) + R * incl, hy + 5 * R)
    am2 = (cx - int(3.5 * R) + R * incl, hy + 5 * R)""",
     """    ds = _ds(p)                                            # tronco esticado/encolhido
    o1 = (cx + _OMBRO1[0] + li, hy + _OMBRO1[1] + ds)
    o2 = (cx + _OMBRO2[0] + li, hy + _OMBRO2[1] + ds)
    cab_x = cx + _GOLA[0] - _CAB_PESCOCO[0] + li + int(round(p.get('hx', 0) or 0))
    cab_ty = hy + _GOLA[1] + _CAB_PESCOCO[1] + int(round(p.get('hy', 0) or 0)) + ds
    boca = (cx + int(2.5 * R), hy + int(1.6 * R))          # boca da bainha (cinto)
    # as maos continuam medidas a partir do ombro antigo (as poses sao as mesmas)
    am1 = (cx + int(2.5 * R) + R * incl, hy + 5 * R + ds)
    am2 = (cx - int(3.5 * R) + R * incl, hy + 5 * R + ds)"""),
    ("""    qx, qy = _TOR_QUADRIL
    for r, linha in enumerate(_YM.TRONCO):
        desl = li if r < 12 else (li // 2 if r < 21 else 0)
        y = hy + qy - r
        for c, ch in enumerate(linha):
            if ch != '.':
                px[(cx - qx + c + desl, y)] = ch""",
     """    qx, qy = _TOR_QUADRIL
    CINTA = 20                                             # linha do mapa onde o tronco dobra
    for r in range(len(_YM.TRONCO) - 1, -1, -1):          # de baixo para cima: o peito por cima
        linha = _YM.TRONCO[r]
        desl = li if r < 12 else (li // 2 if r < 21 else 0)
        y = hy + qy - r + (ds if r < CINTA else 0)
        vezes = ds + 1 if (ds > 0 and r == CINTA) else 1   # esticado: a cintura repete no vao
        for k in range(vezes):
            for c, ch in enumerate(linha):
                if ch != '.':
                    px[(cx - qx + c + desl, y + k)] = ch"""),
    # ── braco que afina ─────────────────────────────────────────────
    ("""    def braco(j, t):
        return couro(j, t, la)

    def antebraco(j, t):
        if faixas and t < 0.84:""", """    def braco(j, t):
        # deltoide cheio no ombro, afina ate o cotovelo (lado da luz mais cheio)
        r = 6.4 - 1.3 * t + (0.5 if j > 0 and t < 0.35 else 0.0)
        if abs(j) > r:
            return None
        if j <= -r + 1.0:
            return sombra                          # borda de baixo sempre na sombra
        return couro(j, t, la)

    def antebraco(j, t):
        if luva and 0.64 < t < 0.76:
            r = 5.6                                # punho da luva mais largo
        elif luva and t >= 0.76:
            r = 4.6
        else:
            r = 5.2 - 0.9 * t
        if abs(j) > r:
            return None
        if t < 0.08 and j <= -1:
            return '2'                             # vinco na dobra do cotovelo
        if faixas and t < 0.84:"""),
    ("""    _tubo(meu, (sx, sy), (ex, ey), 6.0, braco)""", """    _tubo(meu, (sx, sy), (ex, ey), 7.0, braco)"""),
    ("""    _tubo(meu, (ex, ey), (hx, hy), 5.0, antebraco)""", """    _tubo(meu, (ex, ey), (hx, hy), 6.0, antebraco)"""),
])
print('ok')
