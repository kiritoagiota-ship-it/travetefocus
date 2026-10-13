"""
chefe_poses.py - as POSES e os MOVIMENTOS do chefe (so contas, sem Kivy).

O chefe e um boneco de PECAS (recortadas do modelo do usuario em
dev/chefe_ref.py). Aqui fica o que cada peca faz em cada instante:
  - poses (dicts com angulos e passos em pixel) e clipes (funcoes do tempo);
  - matrizes(q, pts): onde cada peca vai parar numa pose (giro em volta das
    juntas; as pernas dobram sozinhas no joelho para o pe ficar no lugar).
O app (chefe.py) monta as pecas na hora com essas matrizes; as ferramentas do
PC (dev/chefe_rig.py) usam as MESMAS contas para as previas.

Angulos em graus, + = horario na tela. Passos em pixel estao na escala do
chefe antigo e sao multiplicados por ESC.
"""
import math

ESC = 1.4                 # o chefe novo e 1,4x o antigo
P_IDLE = 2.4              # ciclo da respiracao/capa parada (s)


def _curva(nome, u):
    u = max(0.0, min(1.0, u))
    if nome == 'in':
        return u * u * u
    if nome == 'out':
        return 1 - (1 - u) ** 3
    if nome == 'mola':
        c1 = 1.5
        return 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2
    if nome == 'linear':
        return u
    return u * u * (3 - 2 * u)


def trilha(chaves, t):
    """chaves: [(tempo_s, {valores}, curva_ate_a_proxima), ...] -> valores no tempo t."""
    ant, prox = chaves[0], chaves[-1]
    for i in range(len(chaves) - 1):
        if chaves[i][0] <= t <= chaves[i + 1][0]:
            ant, prox = chaves[i], chaves[i + 1]
            break
    if t >= chaves[-1][0]:
        ant = prox = chaves[-1]
    t0, v0 = ant[0], ant[1]
    cur = ant[2] if len(ant) > 2 else 'suave'
    t1, v1 = prox[0], prox[1]
    k = 0.0 if t1 == t0 else _curva(cur, (t - t0) / float(t1 - t0))
    q = {}
    for ch in set(v0) | set(v1):
        a = v0.get(ch, 0.0)
        b = v1.get(ch, 0.0)
        if isinstance(a, bool) or isinstance(b, bool):
            q[ch] = a if k < 0.5 else b
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            q[ch] = a + (b - a) * k
        else:
            q[ch] = b
    return q


def degrau(t, por_s):
    return math.floor(t * por_s + 1e-6) / float(por_s)


# ── matrizes 2D (a, b, tx, c, d, ty): x' = a x + b y + tx ; y' = c x + d y + ty ──
ID = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)


def mov(dx, dy):
    return (1.0, 0.0, float(dx), 0.0, 1.0, float(dy))


def rot(pivo, graus):
    a = math.radians(graus)
    c, s = math.cos(a), math.sin(a)
    px, py = pivo
    return (c, -s, px - c * px + s * py, s, c, py - s * px - c * py)


def mul(m, n):
    """m depois de n (m @ n)."""
    return (m[0] * n[0] + m[1] * n[3], m[0] * n[1] + m[1] * n[4], m[0] * n[2] + m[1] * n[5] + m[2],
            m[3] * n[0] + m[4] * n[3], m[3] * n[1] + m[4] * n[4], m[3] * n[2] + m[4] * n[5] + m[5])


def aplica(m, p):
    return (m[0] * p[0] + m[1] * p[1] + m[2], m[3] * p[0] + m[4] * p[1] + m[5])


def _perna(a0, j0, t0, d_anca, d_pe):
    """Perna de dois ossos: a anca foi para a0 + d_anca e o tornozelo tem de
    ficar em t0 + d_pe -> (M da coxa, M da canela). O joelho dobra para a
    FRENTE (esquerda, para onde ele olha)."""
    ax, ay = a0[0] + d_anca[0], a0[1] + d_anca[1]
    vx, vy = t0[0] + d_pe[0] - ax, t0[1] + d_pe[1] - ay
    L1 = math.hypot(j0[0] - a0[0], j0[1] - a0[1])
    L2 = math.hypot(t0[0] - j0[0], t0[1] - j0[1])
    d = max(abs(L1 - L2) + 0.5, min(L1 + L2 - 0.5, math.hypot(vx, vy)))
    base = math.atan2(vy, vx)
    ab = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
    c1 = (ax + L1 * math.cos(base + ab), ay + L1 * math.sin(base + ab))
    c2 = (ax + L1 * math.cos(base - ab), ay + L1 * math.sin(base - ab))
    jx, jy = c1 if c1[0] <= c2[0] else c2
    px, py = ax + d * math.cos(base), ay + d * math.sin(base)
    th1 = math.degrees(math.atan2(jy - ay, jx - ax) - math.atan2(j0[1] - a0[1], j0[0] - a0[0]))
    th2 = math.degrees(math.atan2(py - jy, px - jx) - math.atan2(t0[1] - j0[1], t0[0] - j0[0]))
    return (mul(mov(ax - a0[0], ay - a0[1]), rot(a0, th1)), mul(mov(jx - j0[0], jy - j0[1]), rot(j0, th2)))


def matrizes(q, pts):
    """Onde cada peca vai parar na pose q. pts = pontos do boneco (na tela de
    trabalho): QUADRIL, PESCOCO, OMBRO, COTOVELO, OMBRO_T, COTOVELO_T, MAO_T,
    ANCA_T/JOELHO_T/TORNOZELO_T, ANCA_F/JOELHO_F/TORNOZELO_F, PONTA, GARRA, OLHO.
    -> ({peca: matriz}, {'ponta', 'garra', 'olho', 'mao'})"""
    g = q.get
    hx, ag = int(round(g('hx', 0) * ESC)), int(round(g('ag', 0) * ESC))
    dx, dy = int(round(g('dx', 0) * ESC)), int(round(g('dy', 0) * ESC))
    o = int(round(g('o', 0) * ESC))
    H = mov(hx, ag)
    T = mul(mov(hx + dx, ag + dy), rot(pts['QUADRIL'], g('giro', 0.0)))
    Mcab = mul(T, rot(pts['PESCOCO'], g('c', 0.0)))
    To = mul(T, mov(0, o))
    Mb = mul(To, rot(pts['OMBRO'], g('b', 0.0)))
    Ma = mul(Mb, rot(pts['COTOVELO'], g('a', 0.0)))
    F = ID if g('planta') else T
    Mbt = mul(F, rot(pts['OMBRO_T'], g('bt', 0.0)))
    Mat = mul(Mbt, rot(pts['COTOVELO_T'], g('at', 0.0)))
    Me = mul(Mat, rot(pts['MAO_T'], g('e', 0.0)))
    ar = (hx, ag) if g('ar') else (0, 0)
    Mct, Mnt = _perna(pts['ANCA_T'], pts['JOELHO_T'], pts['TORNOZELO_T'], (hx, ag),
                      (ar[0] + g('ptx', 0) * ESC, ar[1] + g('pty', 0) * ESC))
    Mcf, Mnf = _perna(pts['ANCA_F'], pts['JOELHO_F'], pts['TORNOZELO_F'], (hx, ag),
                      (ar[0] + g('pfx', 0) * ESC, ar[1] + g('pfy', 0) * ESC))
    M = {'capa': T, 'espada': Me, 'braco_tras': Mbt, 'antebraco_tras': Mat, 'ombreira_tras': T,
         'coxa_tras': Mct, 'canela_tras': Mnt, 'coxa_frente': Mcf, 'canela_frente': Mnf,
         'tabardo': H, 'tronco': T, 'saiote': H, 'cabeca': Mcab, 'braco': Mb, 'antebraco': Ma,
         'ombreira': To}
    pontos = {'ponta': aplica(Me, pts['PONTA']), 'garra': aplica(Ma, pts['GARRA']),
              'olho': aplica(Mcab, pts['OLHO']), 'mao': aplica(Mat, pts['MAO_T']),
              'ombro': aplica(Mb, pts['OMBRO']), 'nucleo': aplica(T, pts['NUCLEO']),
              'cabeca': aplica(Mcab, pts['CABECA'])}
    return M, pontos


def modo_capa(vento):
    """Qual jeito de balancar a capa serve para este vento: 'calmo', 'vento' ou 'alto'."""
    if abs(vento.get('sobe', 0.0)) > 0.12:
        return 'alto'
    if abs(vento.get('x', 0.0)) > 7.0 or vento.get('onda', 5.0) > 8.0:
        return 'vento'
    return 'calmo'


# ═════════════════════════════════════════════════════════════════════
#  POSES E CLIPES
# ═════════════════════════════════════════════════════════════════════
REP = dict(dx=0, dy=0, hx=0, ag=0, o=0, c=0.0, b=0.0, a=0.0, bt=0.0, at=0.0, e=0.0, brilho=1,
           giro=0.0, ptx=0.0, pty=0.0, pfx=0.0, pfy=0.0)
PARADO = dict(REP, planta=True)
# montante erguido atras da cabeca, pronto para descer
ERGUIDO = dict(REP, dx=3, dy=-2, c=-10.0, bt=148.0, at=24.0, e=30.0, b=-18.0, a=-12.0)
# desceu: lamina cravada na frente, corpo jogado para a frente
CRAVADO = dict(REP, dx=-8, dy=4, ag=12, c=16.0, bt=-40.0, at=10.0, e=61.0, b=22.0, a=16.0)
# garra armada atras e garra passando na frente
GARRA_ARMA = dict(REP, dx=4, dy=-1, c=-6.0, b=-78.0, a=-34.0, planta=True)
GARRA_CORTA = dict(REP, dx=-12, dy=2, hx=-4, ag=4, c=10.0, b=100.0, a=-8.0, planta=True)
AJOELHADO = dict(REP, hx=-8, ag=62, giro=16.0, c=26.0, b=12.0, a=22.0, pfx=26.0, brilho=0, planta=True)
RUGE = dict(REP, dx=4, dy=-4, c=-26.0, b=-42.0, a=-92.0, brilho=2, planta=True)
APANHA = dict(REP, dx=6, dy=-1, c=-16.0, b=-14.0, a=-10.0, brilho=0, planta=True)
NUM = ('dx', 'dy', 'hx', 'ag', 'o', 'c', 'b', 'a', 'bt', 'at', 'e', 'giro', 'ptx', 'pty', 'pfx', 'pfy')
# ── os golpes da folha do usuario ──
# investida: recolhe o montante na altura do quadril e estoca reto para a frente
INV_ARMA = dict(REP, hx=12, ag=12, giro=-8.0, c=6.0, bt=-34.0, at=24.0, e=97.0, b=-22.0, a=-20.0)
INV_FIM = dict(REP, hx=-44, ag=20, giro=20.0, c=-14.0, bt=70.0, at=-80.0, e=77.0, b=40.0, a=20.0)
# varrida (corte baixo/giratorio): o montante vem de tras, raspa o chao e sobe na frente
VARRE_ARMA = dict(REP, hx=10, ag=6, giro=-12.0, c=8.0, bt=-62.0, at=-18.0, e=-43.0, b=-30.0, a=-20.0)
VARRE_FIM = dict(REP, hx=-24, ag=12, giro=14.0, c=-8.0, bt=62.0, at=-40.0, e=87.0, b=34.0, a=14.0)
# salto: agacha, sobe encolhido com o montante atras da cabeca e desce esticando
SALTO_PREP = dict(REP, ag=44, giro=12.0, c=18.0, bt=-16.0, at=6.0, e=-8.0, b=20.0, a=24.0)
SALTO_AR = dict(REP, ar=True, giro=-10.0, c=-14.0, bt=150.0, at=26.0, e=32.0, b=-46.0, a=-30.0,
                ptx=14.0, pty=-64.0, pfx=10.0, pfy=-40.0)
SALTO_DESCE = dict(REP, ar=True, giro=10.0, c=10.0, bt=158.0, at=22.0, e=36.0, b=-20.0, a=-12.0,
                   ptx=-6.0, pty=-12.0, pfx=6.0, pfy=-26.0)
# aponta o montante para a frente (dispara o projetil de sangue)
APONTA = dict(REP, hx=4, ag=6, giro=4.0, c=-4.0, bt=70.0, at=-80.0, e=97.0, b=-10.0, a=-8.0, brilho=2)
# guarda: o montante atravessado na frente do corpo
DEFESA = dict(REP, hx=6, ag=10, giro=-6.0, c=8.0, bt=38.0, at=-30.0, e=178.0, b=14.0, a=10.0)


def _pose(ch, t):
    q = trilha(ch, t)
    for k in ('dx', 'dy', 'hx', 'ag', 'o', 'brilho'):
        q[k] = int(round(q.get(k, 0)))
    return q


def _respira(q, tc, forca=1.0):
    """O peito sobe e desce 1 pixel; a ombreira e a cabeca chegam atrasadas."""
    w = 2 * math.pi * tc / P_IDLE
    q = dict(q)
    q['dy'] = q.get('dy', 0) + int(round(forca * 1.2 * math.sin(w)))
    q['o'] = q.get('o', 0) + int(round(forca * 1.0 * math.sin(w - 0.9)))
    q['c'] = q.get('c', 0.0) + forca * 1.6 * math.sin(w - 0.5)
    q['b'] = q.get('b', 0.0) + forca * 1.4 * math.sin(w - 1.2)
    q['a'] = q.get('a', 0.0) + forca * 1.6 * math.sin(w - 1.8)
    return q


def _pulso(tc):
    return (1, 1, 2, 2, 1, 0)[int(tc / 0.4) % 6]


def clipes():
    """{nome: (funcao t -> (pose, t_pano, vento), duracao_s, loop)}"""
    CL = {}
    V0 = dict(onda=5.0, per=P_IDLE, sobe=0.0, x=0.0, fogo=1.0)

    def idle(t):
        tc = degrau(t, 10)
        q = _respira(PARADO, tc)
        q['brilho'] = _pulso(tc)
        return q, tc, dict(V0)
    CL['idle'] = (idle, P_IDLE, True)

    # RUGIDO: encolhe (antecipacao), joga a cabeca para tras com a garra
    # aberta, treme segurando e assenta. A capa abre com o sopro.
    ch_r = [(0.0, dict(PARADO), 'suave'), (0.3, dict(PARADO, dx=-4, dy=3, ag=4, c=16.0, b=12.0, a=10.0), 'in'),
            (0.47, RUGE, 'out'), (1.25, dict(RUGE, c=-20.0), 'suave'), (1.7, dict(PARADO))]
    D_RUG = 1.7

    def rugido(t):
        tc = degrau(t, 15)
        q = _pose(ch_r, tc)
        q['planta'] = True
        if 0.47 <= tc <= 1.25:                               # treme segurando o rugido
            q['dx'] += (1, 0, -1, 0)[int(tc * 30) % 4]
            q['c'] += 2.0 * math.sin(tc * 40)
            q['brilho'] = 2
        sopro = math.exp(-max(0.0, tc - 0.45) / 0.45) if tc >= 0.4 else 0.0
        return q, tc - D_RUG, dict(V0, onda=5.0 + 9.0 * sopro, sobe=0.12 * sopro, x=14.0 * sopro,
                                   fogo=1.0 + 0.6 * sopro)
    CL['rugido'] = (rugido, D_RUG, False)

    # GOLPE: arranca o montante do chao, ergue por cima da cabeca (segura um
    # instante), desce de uma vez na frente (rastro) e crava; depois volta.
    ch_g = [(0.0, dict(REP), 'in'), (0.12, dict(REP, dx=-2, dy=2, ag=2, bt=-8.0, e=-4.0), 'suave'),
            (0.52, ERGUIDO, 'out'), (0.66, dict(ERGUIDO, bt=154.0, e=34.0, dy=-3), 'in'),
            (0.73, dict(REP, dx=-3, dy=0, c=4.0, bt=70.0, at=4.0, e=6.0, b=6.0), 'linear'),
            (0.80, CRAVADO, 'out'), (1.15, dict(CRAVADO, dx=-6, dy=2), 'suave'), (1.75, dict(REP))]
    D_GOLPE = 1.75

    def golpe(t):
        tc = degrau(t, 15)
        q = _pose(ch_g, tc)
        if 0.67 <= tc <= 0.87:
            ant = _pose(ch_g, tc - 2 / 30.0)
            q['rastro'] = (ant['bt'] + ant['at'] + ant['e'], q['bt'] + q['at'] + q['e'])
        if 0.80 <= tc <= 0.95:
            q['dy'] += (1, -1)[int(tc * 30) % 2]              # tranco do impacto
        q['brilho'] = 2 if 0.5 <= tc <= 1.0 else 1
        vx = -16.0 * math.exp(-max(0.0, tc - 0.78) / 0.3) if tc >= 0.7 else 5.0 * min(1.0, tc / 0.5)
        return q, tc - D_GOLPE, dict(V0, onda=6.0 + 4.0 * abs(vx) / 16.0, x=vx,
                                     sobe=0.10 if 0.2 < tc < 0.7 else 0.0)
    CL['golpe'] = (golpe, D_GOLPE, False)

    # GARRA: arma o braco da frente para tras e rasga na frente
    ch_u = [(0.0, dict(PARADO), 'suave'), (0.34, GARRA_ARMA, 'out'), (0.44, dict(GARRA_ARMA, b=-84.0), 'in'),
            (0.54, GARRA_CORTA, 'out'), (0.8, dict(GARRA_CORTA, b=58.0), 'suave'), (1.2, dict(PARADO))]
    D_GARRA = 1.2

    def garra(t):
        tc = degrau(t, 15)
        q = _pose(ch_u, tc)
        q['planta'] = True
        if 0.45 <= tc <= 0.62:
            ant = _pose(ch_u, tc - 2 / 30.0)
            q['unhas'] = (ant['b'] + ant['a'], q['b'] + q['a'])
        vx = -9.0 * math.exp(-max(0.0, tc - 0.5) / 0.3) if tc >= 0.44 else 0.0
        return q, tc - D_GARRA, dict(V0, x=vx)
    CL['garra'] = (garra, D_GARRA, False)

    # APANHA: o tronco vai para tras, a cabeca estala, volta
    ch_a = [(0.0, dict(PARADO), 'out'), (0.07, APANHA, 'suave'), (0.36, dict(PARADO))]
    D_AP = 0.4

    def apanha(t):
        tc = degrau(t, 15)
        q = _pose(ch_a, tc)
        q['planta'] = True
        return q, tc - D_AP, dict(V0, x=10.0 * math.exp(-tc / 0.15))
    CL['apanha'] = (apanha, D_AP, False)

    # CAMBALEIA: perde a forca, cai de joelho apoiado no montante
    ch_c = [(0.0, dict(PARADO), 'out'), (0.12, dict(APANHA, dx=8, c=-22.0), 'suave'),
            (0.5, dict(PARADO, dx=-2, dy=2, ag=4, c=8.0), 'in'), (0.8, AJOELHADO, 'mola'), (1.1, dict(AJOELHADO))]
    D_CAMB = 1.1

    def cambaleia(t):
        tc = degrau(t, 15)
        q = _pose(ch_c, tc)
        q['planta'] = True
        q['brilho'] = 0 if tc > 0.3 else 1
        return q, tc - D_CAMB, dict(V0, x=6.0 * math.exp(-tc / 0.3), fogo=0.55)
    CL['cambaleia'] = (cambaleia, D_CAMB, False)

    def ajoelhado(t):
        tc = degrau(t, 10)
        q = _respira(AJOELHADO, tc, 1.6)                      # ofegante
        q['brilho'] = (0, 0, 1, 0, 0, 0)[int(tc / 0.4) % 6]
        return q, tc, dict(V0, onda=3.5, fogo=0.5)
    CL['ajoelhado'] = (ajoelhado, P_IDLE, True)

    # CARREGA: levanta de vez, ergue o montante com tudo aceso e segura tremendo
    ch_k = [(0.0, dict(AJOELHADO), 'in'), (0.3, dict(REP, dx=-3, dy=2, ag=3, c=10.0, bt=-10.0, e=-6.0), 'suave'),
            (0.85, ERGUIDO, 'out'), (1.0, dict(ERGUIDO, bt=152.0, e=33.0))]
    D_CARR = 1.0

    def carrega(t):
        tc = degrau(t, 15)
        q = _pose(ch_k, tc)
        q['brilho'] = 1 if tc < 0.3 else 2
        return q, tc - D_CARR, dict(V0, onda=8.0, sobe=0.10 * min(1.0, tc / 0.6), x=6.0 * min(1.0, tc / 0.8),
                                    fogo=1.0 + 0.8 * min(1.0, tc / 0.8))
    CL['carrega'] = (carrega, D_CARR, False)

    def carrega_segura(t):
        tc = degrau(t, 15)
        q = dict(ERGUIDO, bt=152.0, e=33.0 + 1.5 * math.sin(tc * 30), brilho=2)
        q['dx'] = ERGUIDO['dx'] + (1, 0, -1, 0)[int(tc * 15) % 4]
        q['dy'] = ERGUIDO['dy'] + (0, 1)[int(tc * 15) % 2]
        return q, tc, dict(V0, onda=11.0, per=0.8, sobe=0.10, x=6.0, fogo=1.8)
    CL['carrega_segura'] = (carrega_segura, 0.8, True)

    def _soma(q):
        return q['bt'] + q['at'] + q['e'] + q.get('giro', 0.0)

    # INVESTIDA: recolhe o montante apontado, segura um instante e estoca
    # (o app faz ele atravessar a tela nesse momento); freia e volta
    ch_i = [(0.0, dict(REP), 'suave'), (0.34, INV_ARMA, 'out'), (0.5, dict(INV_ARMA, hx=16, ag=14), 'in'),
            (0.58, INV_FIM, 'out'), (1.0, dict(INV_FIM, hx=-40, giro=17.0), 'suave'), (1.45, dict(REP))]
    D_INV = 1.45

    def investida(t):
        tc = degrau(t, 15)
        q = _pose(ch_i, tc)
        q['brilho'] = 2 if 0.3 <= tc <= 1.0 else 1
        if 0.58 <= tc <= 0.9:
            q['dx'] += (1, 0, -1, 0)[int(tc * 30) % 4]
        vx = 22.0 * math.exp(-max(0.0, tc - 0.56) / 0.35) if tc >= 0.5 else -4.0 * min(1.0, tc / 0.4)
        return q, tc - D_INV, dict(V0, onda=6.0 + 6.0 * abs(vx) / 22.0, x=vx, sobe=0.10 if tc > 0.5 else 0.0)
    CL['investida'] = (investida, D_INV, False)

    # VARRIDA: o montante vem de tras, raspa o chao e sobe na frente (rastro largo)
    ch_v = [(0.0, dict(REP), 'suave'), (0.36, VARRE_ARMA, 'out'), (0.5, dict(VARRE_ARMA, bt=-68.0, giro=-14.0), 'in'),
            (0.66, VARRE_FIM, 'out'), (1.0, dict(VARRE_FIM, bt=56.0), 'suave'), (1.5, dict(REP))]
    D_VAR = 1.5

    def varrida(t):
        tc = degrau(t, 15)
        q = _pose(ch_v, tc)
        if 0.5 < tc <= 0.72:
            ant = _pose(ch_v, tc - 2 / 30.0)
            q['rastro'] = (ant['bt'] + ant['at'] + ant['e'], q['bt'] + q['at'] + q['e'])
        q['brilho'] = 2 if 0.4 <= tc <= 0.9 else 1
        vx = -18.0 * math.exp(-max(0.0, tc - 0.6) / 0.3) if tc >= 0.5 else 6.0 * min(1.0, tc / 0.4)
        return q, tc - D_VAR, dict(V0, onda=6.0 + 5.0 * abs(vx) / 18.0, x=vx)
    CL['varrida'] = (varrida, D_VAR, False)

    # SALTO: agacha fundo (salto_prep), sobe encolhido (salto_ar, em loop: o app
    # leva ele pelo ceu), desce esticando (salto_desce, em loop) e crava no
    # chao (pouso)
    ch_sp = [(0.0, dict(REP), 'in'), (0.3, SALTO_PREP, 'out'), (0.42, dict(SALTO_PREP, ag=48))]

    def salto_prep(t):
        tc = degrau(t, 15)
        q = _pose(ch_sp, tc)
        q['brilho'] = 2 if tc > 0.2 else 1
        return q, tc, dict(V0, onda=4.0, sobe=-0.05)
    CL['salto_prep'] = (salto_prep, 0.42, False)

    def salto_ar(t):
        tc = degrau(t, 15)
        q = dict(SALTO_AR, brilho=2)
        q['e'] = SALTO_AR['e'] + 2.0 * math.sin(tc * 2 * math.pi / 0.4)
        return q, tc, dict(V0, onda=9.0, per=0.4, sobe=-0.22, x=-4.0, fogo=1.6)
    CL['salto_ar'] = (salto_ar, 0.4, True)

    def salto_desce(t):
        tc = degrau(t, 15)
        q = dict(SALTO_DESCE, brilho=2)
        q['e'] = SALTO_DESCE['e'] + 2.0 * math.sin(tc * 2 * math.pi / 0.4)
        return q, tc, dict(V0, onda=10.0, per=0.4, sobe=0.30, x=2.0, fogo=1.8)
    CL['salto_desce'] = (salto_desce, 0.4, True)

    ch_po = [(0.0, dict(SALTO_DESCE, ar=False, ptx=0.0, pty=0.0, pfx=0.0, pfy=0.0, ag=10), 'linear'),
             (0.07, dict(CRAVADO, ag=40, giro=14.0), 'out'), (0.5, dict(CRAVADO, ag=30, giro=10.0), 'suave'),
             (1.15, dict(REP))]
    D_POUSO = 1.15

    def pouso(t):
        tc = degrau(t, 15)
        q = _pose(ch_po, tc)
        q.pop('ar', None)
        if tc <= 0.1:
            ant = _pose(ch_po, max(0.0, tc - 2 / 30.0))
            q['rastro'] = (ant['bt'] + ant['at'] + ant['e'], q['bt'] + q['at'] + q['e'])
        if 0.07 <= tc <= 0.3:
            q['dy'] += (1, -1)[int(tc * 30) % 2]
        q['brilho'] = 2 if tc < 0.5 else 1
        return q, tc - D_POUSO, dict(V0, onda=6.0 + 6.0 * math.exp(-tc / 0.3), x=-12.0 * math.exp(-tc / 0.3),
                                     sobe=0.25 * math.exp(-tc / 0.2))
    CL['pouso'] = (pouso, D_POUSO, False)

    # APONTA: nivela o montante para a frente, o fio acende e ele dispara (coice)
    ch_ap = [(0.0, dict(REP), 'suave'), (0.32, APONTA, 'out'), (0.62, dict(APONTA, hx=2), 'in'),
             (0.68, dict(APONTA, hx=14, giro=-4.0, c=6.0), 'out'), (1.0, dict(APONTA), 'suave'), (1.4, dict(REP))]
    D_APO = 1.4

    def aponta(t):
        tc = degrau(t, 15)
        q = _pose(ch_ap, tc)
        q['brilho'] = 2 if 0.25 <= tc <= 1.05 else 1
        if 0.4 <= tc <= 0.62:
            q['e'] += 1.5 * math.sin(tc * 50)
        return q, tc - D_APO, dict(V0, onda=6.0, x=8.0 * math.exp(-max(0.0, tc - 0.66) / 0.25) if tc > 0.62 else 0.0,
                                   fogo=1.5)
    CL['aponta'] = (aponta, D_APO, False)

    # DEFESA: atravessa o montante na frente do corpo e aguenta
    ch_d = [(0.0, dict(REP), 'out'), (0.16, DEFESA, 'suave'), (0.75, dict(DEFESA, hx=8), 'suave'), (1.05, dict(REP))]
    D_DEF = 1.05

    def defesa(t):
        tc = degrau(t, 15)
        q = _pose(ch_d, tc)
        return q, tc - D_DEF, dict(V0, x=4.0)
    CL['defesa'] = (defesa, D_DEF, False)
    return CL
