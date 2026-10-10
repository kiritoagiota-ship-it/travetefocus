"""O CHEFE animado PECA POR PECA (como o Bankai): as pecas desenhadas em
chefe_arte.py viram um boneco articulado.
  capa e tabardo - cortados em TIRAS (cada pixel vai para a tira cuja espinha
                   esta mais perto); a tira dobra com o vento e cada pixel so
                   anda em passos inteiros;
  tronco/cabeca/ombreiras - sobem e descem 1 pixel (respira), a cabeca gira
                   no pescoco;
  braco da frente (garra) - gira no ombro e no cotovelo;
  braco de tras + montante - giram no ombro, cotovelo e punho (os golpes);
  por cima: fendas e nucleo PULSANDO (3 niveis de brasa), linguas de fogo
                   subindo das bordas de cima, faiscas e a chama do olho.
Os desenhos trocam 10 (parado) a 15 (golpe) vezes por segundo.

Os clipes vao para app/chefe/clipes.bin (mesmo formato do Bankai); o app so
toca os quadros (chefe.py).
uso: python dev/chefe_rig.py gerar            (clipes -> app/chefe/clipes.bin)
     python dev/chefe_rig.py gif [clipes]     (GIF de previa)
     python dev/chefe_rig.py folha CLIPE      (folha com os desenhos do clipe)"""
import os
import sys
import math
import json
import zlib
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chefe_arte as A                                                  # noqa: E402
from bankai_rig import rot, mov, aplica, desenha_peca, Mecha, _reamostra, _dist_seg, trilha, degrau   # noqa: E402
from reiatsu import Ruido                                               # noqa: E402

APP = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
SAIDA_TESTE = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'ferramentas', 'saida_testes', 'chefe')
FPS = 30
CW, CH = A.CW, A.CH
P = A.P
ANCORA = (176.0, float(A.CHAO))              # pes no chao: vai na ancora do widget
P_IDLE = 2.4

# tiras da capa (da raiz, nos ombros, ate a barra) e do tabardo
TIRAS_CAPA = [
    [(158, 108), (156, 170), (158, 230), (162, 284)],
    [(178, 104), (182, 170), (190, 232), (198, 292)],
    [(200, 100), (210, 160), (222, 226), (234, 298)],
    [(218, 98), (238, 150), (256, 216), (268, 302)],
    [(230, 98), (260, 140), (284, 202), (298, 302)],
    [(238, 102), (272, 138), (302, 200), (316, 302)],
]
TIRAS_TAB = [
    [(172, 210), (170, 250), (168, 284)],
    [(184, 210), (184, 250), (186, 290)],
    [(196, 210), (198, 250), (202, 282)],
]
G = [A.G0, A.G1, A.G2, A.G3, A.G4]


def _tiras(peca, espinhas, amps, rigidez):
    """Divide os pixels da peca entre as espinhas -> [Mecha]."""
    esp = [_reamostra([P(*p) for p in e]) for e in espinhas]
    py, px = np.nonzero(peca.masc)
    melhor = np.full(len(py), 1e9)
    dono = np.zeros(len(py), int)
    uu = np.zeros(len(py))
    for i, e in enumerate(esp):
        d = np.hypot(*np.diff(e, axis=0).T)
        acum = np.concatenate([[0], np.cumsum(d)]) / d.sum()
        for k in range(len(e) - 1):
            dist, t = _dist_seg(px + 0.5, py + 0.5, e[k], e[k + 1])
            mk = dist < melhor
            melhor = np.where(mk, dist, melhor)
            dono = np.where(mk, i, dono)
            uu = np.where(mk, acum[k] + t * (acum[k + 1] - acum[k]), uu)
    out = []
    for i, e in enumerate(esp):
        sel = dono == i
        f = i / float(max(1, len(esp) - 1))
        out.append(Mecha(e, py[sel], px[sel], peca.img[py[sel], px[sel]], uu[sel], amps[0] + (amps[1] - amps[0]) * f,
                         1.9 * f + 0.4, rigidez, True))
    return out


class Chefe:
    def __init__(self):
        self.pc = A.montar()
        self.pal = list(A.PAL)
        self.capa = _tiras(self.pc['capa'], TIRAS_CAPA, (0.55, 1.15), 0.14)
        self.tab = _tiras(self.pc['tabardo'], TIRAS_TAB, (0.5, 0.7), 0.2)
        ys, xs = np.mgrid[0:CH, 0:CW]
        self.xs, self.ys = xs, ys
        self.n1 = Ruido(5, 5, 9, 72.0, CW, CH)
        self.n2 = Ruido(6, 3, 5, 72.0, CW, CH)
        rnd = np.random.default_rng(4)
        # faiscas: (x no desenho, y de onde nasce, quanto sobe, fase, balanco, tamanho)
        self.faiscas = [(rnd.uniform(70, 300), rnd.uniform(120, 310), rnd.uniform(60, 140), rnd.uniform(0, 1),
                         rnd.uniform(0, 6.28), int(rnd.integers(1, 3))) for _ in range(18)]
        u, n, L = A._u_lamina()
        self.L_lam = L
        self.ang_lam = math.degrees(math.atan2(u[1], u[0]))
        self.lut = []
        for nivel in (0, 1, 2):
            t = np.arange(256, dtype=np.uint8)
            if nivel == 0:
                t[G[4]], t[G[3]], t[G[2]], t[G[1]] = G[3], G[2], G[1], G[0]
            elif nivel == 2:
                t[G[1]], t[G[2]], t[G[3]] = G[2], G[3], G[4]
            self.lut.append(t)

    # ── um desenho ───────────────────────────────────────────────────────
    def quadro(self, q, tc, vento):
        """q = pose (dict), tc = tempo do pano/fogo (em degraus), vento = dict.
        -> (indices, garra, ponta)"""
        pc = self.pc
        img = np.zeros((CH, CW), np.int32)
        hx, ag = int(round(q.get('hx', 0))), int(round(q.get('ag', 0)))
        dx, dy = int(round(q.get('dx', 0))), int(round(q.get('dy', 0)))
        H = mov(hx, ag)                                       # quadril
        T = mov(hx + dx, ag + dy)                             # tronco
        o = int(round(q.get('o', 0)))                         # a ombreira chega atrasada
        Mcab = T @ rot(P(*A.PESCOCO), q.get('c', 0.0))
        Mb = T @ mov(0, o) @ rot(P(*A.OMBRO), q.get('b', 0.0))
        Ma = Mb @ rot(P(*A.COTOVELO), q.get('a', 0.0))
        F = np.eye(3) if q.get('planta') else T
        Mbt = F @ rot(P(*A.OMBRO_T), q.get('bt', 0.0))
        Mat = Mbt @ rot(P(*A.COTOVELO_T), q.get('at', 0.0))
        Me = Mat @ rot(P(*A.MAO_T), q.get('e', 0.0))

        def tiras(lista, M):
            ox, oy = int(round(M[0, 2])), int(round(M[1, 2]))
            for mc in lista:
                if len(mc.ys) == 0:
                    continue
                ddx, ddy = mc.deslocamento(tc, vento)
                yy, xx = mc.ys + ddy + oy, mc.xs + ddx + ox
                ok = (yy >= 0) & (yy < CH) & (xx >= 0) & (xx < CW)
                img[yy[ok], xx[ok]] = mc.cores[ok]

        def peca(nome, M):
            desenha_peca(img, pc[nome].img, pc[nome].masc, M)

        # miolo parado da capa (aparece nos vaos entre as tiras)
        miolo = A.erode(pc['capa'].masc, 3)
        desenha_peca(img, np.where(miolo, A.C0, 0).astype(np.uint8), miolo, T)
        tiras(self.capa, T)
        peca('espada', Me)
        peca('braco_tras', Mbt)
        peca('antebraco_tras', Mat)
        peca('ombreira_tras', T)
        peca('perna_tras', np.eye(3))
        peca('perna_frente', np.eye(3))
        mi_t = A.erode(pc['tabardo'].masc, 2)
        desenha_peca(img, np.where(mi_t, A.C0, 0).astype(np.uint8), mi_t, H)
        tiras(self.tab, H)
        peca('tronco', T)
        peca('saiote', H)
        peca('cabeca', Mcab)
        peca('braco', Mb)
        peca('antebraco', Ma)
        peca('ombreira', T @ mov(0, o))
        ponta = aplica(Me, P(*A.PONTA))
        mao_esp = aplica(Mat, P(*A.MAO_T))
        garra = aplica(Ma, P(A.MAO[0] - 2, A.MAO[1] + 34))
        olho = aplica(Mcab, P(*A.OLHO))
        # rastro do golpe (so onde esta vazio)
        if q.get('rastro') is not None:
            self._rastro(img, mao_esp, self.ang_lam + q['rastro'][0], self.ang_lam + q['rastro'][1], self.L_lam)
        if q.get('unhas') is not None:
            self._unhas(img, aplica(Mb, P(*A.OMBRO)), garra, q['unhas'])
        img = A.aro(img.astype(np.uint8)).astype(np.int32)
        nivel = int(q.get('brilho', 1))
        if nivel != 1:
            img = self.lut[nivel][img]
        self._fogo(img, tc, vento.get('fogo', 1.0))
        self._olho(img, olho, tc, nivel)
        self._faiscas(img, tc, T)
        return img.astype(np.uint8), garra, ponta

    def _rastro(self, img, centro, a0, a1, L):
        """Meia-lua solida entre o angulo da lamina de antes e o de agora."""
        cx, cy = centro
        lo, hi = min(a0, a1), max(a0, a1)
        if hi - lo < 5:
            return
        ang = np.degrees(np.arctan2(self.ys - cy, self.xs - cx))
        for volta in (-360, 360):
            ang = np.where((ang < lo - 180) & (volta > 0), ang + 360, ang)
            ang = np.where((ang > hi + 180) & (volta < 0), ang - 360, ang)
        r = np.hypot(self.xs - cx, self.ys - cy) / L
        fr = np.clip((ang - lo) / max(1e-6, hi - lo), 0.0, 1.0)
        k = fr if a1 > a0 else 1 - fr                        # 1 = perto da lamina agora
        r_fora = 1.03 - 0.16 * (1 - k)
        r_dentro = 0.42 + 0.5 * (1 - k) ** 1.3
        dentro = (ang >= lo) & (ang <= hi) & (r > r_dentro) & (r < r_fora)
        pos = (r - r_dentro) / np.maximum(1e-6, r_fora - r_dentro)
        cor = np.where(pos > 0.8, A.R2, np.where((pos > 0.45) | (k > 0.6), A.R1, A.R0))
        pinta = dentro & (img == 0)
        img[pinta] = cor[pinta]

    def _unhas(self, img, ombro, garra, angs):
        """Riscos das unhas no ar (arcos finos em volta do ombro)."""
        a0, a1 = angs
        cx, cy = ombro
        raio = math.hypot(garra[0] - cx, garra[1] - cy)
        base = math.degrees(math.atan2(garra[1] - cy, garra[0] - cx))
        lo, hi = sorted((base, base - (a1 - a0)))
        ang = np.degrees(np.arctan2(self.ys - cy, self.xs - cx))
        ang = np.where(ang < lo - 180, ang + 360, ang)
        ang = np.where(ang > hi + 180, ang - 360, ang)
        r = np.hypot(self.xs - cx, self.ys - cy)
        fr = np.clip((ang - lo) / max(1e-6, hi - lo), 0, 1)
        k = fr if a1 > a0 else 1 - fr                        # 1 = onde a garra esta agora
        for i, dr in enumerate((-14, -5, 4, 13)):
            esp = 1.2 + 2.2 * k
            m = (ang >= lo) & (ang <= hi) & (np.abs(r - (raio + dr)) < esp)      # por cima do corpo
            img[m & (k > 0.55)] = A.R2
            img[m & (k <= 0.55) & (k > 0.2)] = A.R1
            img[m & (k <= 0.2)] = A.R0

    def _fogo(self, img, t, forca):
        """Linguas de fogo subindo das bordas de cima (so no vazio)."""
        if forca <= 0:
            return
        s = img > 0
        sobe = t / P_IDLE * 72.0
        n = 0.6 * self.n1(self.xs, self.ys + sobe) + 0.4 * self.n2(self.xs, self.ys + sobe * 2.0)
        lims = (0.50, 0.57, 0.63, 0.69, 0.74, 0.79)
        cores = (G[2], G[1], G[1], G[0], G[0], G[0])
        embaixo = s.copy()
        acesa = np.ones_like(s)
        for k in range(1, int(4 + 2 * min(1.5, forca)) + 1):
            embaixo = np.roll(embaixo, -1, axis=0)             # tem desenho k px abaixo
            embaixo[-1, :] = False
            lim = lims[min(k - 1, len(lims) - 1)] + (1.0 - forca) * 0.12
            acesa = acesa & (n > lim)
            m = ~s & embaixo & acesa
            img[m] = cores[min(k - 1, len(cores) - 1)]

    def _olho(self, img, olho, t, nivel):
        """Chama do olho: um fiapo que sobe para tras e treme."""
        x, y = olho
        L = 6 + int(round(2.5 * math.sin(2 * math.pi * t / 0.6))) + (3 if nivel == 2 else 0)
        for i in range(L):
            bx = int(round(x + 4 + i * 1.1 + 1.2 * math.sin(t * 9 + i * 0.9)))
            by = int(round(y - 3 - i * 1.0))
            cor = G[4] if i < 2 else (G[3] if i < 4 else (G[2] if i < 6 else G[1]))
            for ddx in range(2 if i < 4 else 1):
                if 0 <= by < CH and 0 <= bx + ddx < CW:
                    img[by, bx + ddx] = cor

    def _faiscas(self, img, t, T):
        ox, oy = int(round(T[0, 2])), int(round(T[1, 2]))
        for (x0, y0, sobe, fase, bal, tam) in self.faiscas:
            f = (t / P_IDLE + fase) % 1.0
            if f > 0.9:
                continue
            x, y = P(x0 + 4 * math.sin(bal + f * 9.0), y0 - sobe * f)
            x, y = int(round(x)) + ox, int(round(y)) + oy
            cor = G[3] if f < 0.3 else (G[2] if f < 0.65 else G[1])
            if 0 <= y < CH - 1 and 0 <= x < CW - 1:
                img[y, x] = cor
                if tam > 1 and f < 0.5:
                    img[y, x + 1] = G[2]


# ═════════════════════════════════════════════════════════════════════
#  POSES E CLIPES
# ═════════════════════════════════════════════════════════════════════
REP = dict(dx=0, dy=0, hx=0, ag=0, o=0, c=0.0, b=0.0, a=0.0, bt=0.0, at=0.0, e=0.0, brilho=1)
PARADO = dict(REP, planta=True)
# montante erguido atras da cabeca, pronto para descer
ERGUIDO = dict(REP, dx=3, dy=-2, c=-10.0, bt=148.0, at=24.0, e=30.0, b=-18.0, a=-12.0)
# desceu: lamina cravada na frente, corpo jogado para a frente
CRAVADO = dict(REP, dx=-8, dy=4, ag=12, c=16.0, bt=-40.0, at=10.0, e=61.0, b=22.0, a=16.0)
# garra armada atras e garra passando na frente
GARRA_ARMA = dict(REP, dx=4, dy=-1, c=-6.0, b=-78.0, a=-34.0, planta=True)
GARRA_CORTA = dict(REP, dx=-12, dy=2, hx=-4, ag=4, c=10.0, b=100.0, a=-8.0, planta=True)
AJOELHADO = dict(REP, dx=-10, dy=5, ag=22, c=30.0, b=12.0, a=22.0, brilho=0, planta=True)
RUGE = dict(REP, dx=4, dy=-4, c=-26.0, b=-42.0, a=-92.0, brilho=2, planta=True)
APANHA = dict(REP, dx=6, dy=-1, c=-16.0, b=-14.0, a=-10.0, brilho=0, planta=True)
NUM = ('dx', 'dy', 'hx', 'ag', 'o', 'c', 'b', 'a', 'bt', 'at', 'e')


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
    return CL


CHAVES_Q = ('dx', 'dy', 'hx', 'ag', 'o', 'c', 'b', 'a', 'bt', 'at', 'e', 'brilho', 'planta', 'rastro', 'unhas')


def gerar_quadros(nomes=None):
    che = Chefe()
    saida = {}
    cache = {}
    for nome, (fn, dur, loop) in clipes().items():
        if nomes and nome not in nomes:
            continue
        quadros = []
        n = int(round(dur * FPS))
        for f in range(n):
            q, tc, vento = fn(f / float(FPS))
            kw = {k: q[k] for k in CHAVES_Q if k in q}
            chave = json.dumps([sorted((k, (round(v, 2) if isinstance(v, float) else v)) for k, v in kw.items()
                                       if not isinstance(v, tuple)),
                                [(k, [round(x, 2) for x in v]) for k, v in sorted(kw.items()) if isinstance(v, tuple)],
                                round(tc % P_IDLE, 4), sorted((k, round(v, 4)) for k, v in vento.items())])
            if chave not in cache:
                cache[chave] = che.quadro(kw, tc, vento)
            quadros.append(cache[chave])
        saida[nome] = (quadros, loop)
        print(nome, n, 'quadros,', len({id(x) for x in quadros}), 'desenhos')
    return che, saida


def escrever(che, saida):
    """app/chefe/clipes.bin: mesmo formato do Bankai (b'BK01' + cabecalho json
    em zlib + cada desenho em zlib, recortado; quadro repetido aponta para o
    mesmo desenho)."""
    blocos = []
    cab = {'paleta': che.pal, 'tela': [CW, CH], 'quadril': list(P(*ANCORA)), 'fps': FPS,
           'olho': list(P(*A.OLHO)), 'nucleo': list(P(*A.NUCLEO)), 'cabeca': list(P(*A.CABECA)),
           'corpo': [P(100, 0)[0], P(250, 0)[0], P(0, 56)[1], P(0, A.CHAO)[1]], 'clipes': {}}
    pos = 0
    ja = {}
    for nome, (quadros, loop) in saida.items():
        lst = []
        for item in quadros:
            img, mao, ponta = item
            if id(item) not in ja:
                ys, xs = np.nonzero(img)
                x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
                dados = zlib.compress(img[y0:y1, x0:x1].tobytes(), 9)
                blocos.append(dados)
                ja[id(item)] = [pos, len(dados), [x0, y0, x1 - x0, y1 - y0]]
                pos += len(dados)
            p, tam, caixa = ja[id(item)]
            lst.append([p, tam, caixa, [round(mao[0], 1), round(mao[1], 1)], [round(ponta[0], 1), round(ponta[1], 1)]])
        cab['clipes'][nome] = {'loop': loop, 'quadros': lst}
    cz = zlib.compress(json.dumps(cab).encode('utf-8'), 9)
    os.makedirs(os.path.join(APP, 'chefe'), exist_ok=True)
    caminho = os.path.join(APP, 'chefe', 'clipes.bin')
    with open(caminho, 'wb') as fp:
        fp.write(b'BK01')
        fp.write(len(cz).to_bytes(4, 'little'))
        fp.write(cz)
        for b in blocos:
            fp.write(b)
    print(caminho, os.path.getsize(caminho) // 1024, 'KB,', len(blocos), 'desenhos')


def _caixa(saida, ordem):
    x0 = y0 = 10 ** 9
    x1 = y1 = -1
    for nome in ordem:
        for idx, _, _ in saida[nome][0]:
            ys, xs = np.nonzero(idx)
            x0, x1 = min(x0, xs.min()), max(x1, xs.max())
            y0, y1 = min(y0, ys.min()), max(y1, ys.max())
    return x0 - 6, y0 - 6, x1 + 7, y1 + 7


def gif(saida, ordem, caminho, z=2):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    x0, y0, x1, y1 = _caixa(saida, ordem)
    frames = []
    for nome in ordem:
        for idx, _, _ in saida[nome][0]:
            im = Image.fromarray(A.rgba(idx)[y0:y1, x0:x1][..., :3]).resize(((x1 - x0) * z, (y1 - y0) * z),
                                                                           Image.NEAREST)
            frames.append(im.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.Dither.NONE))
    frames[0].save(caminho, save_all=True, append_images=frames[1:], duration=33, loop=0)
    print(caminho, len(frames), 'quadros', os.path.getsize(caminho) // 1024, 'KB')


def folha(saida, nome, caminho, z=1, cols=6):
    """Os desenhos diferentes de um clipe, lado a lado."""
    x0, y0, x1, y1 = _caixa(saida, [nome])
    unicos = []
    for it in saida[nome][0]:
        if not unicos or unicos[-1] is not it:
            unicos.append(it)
    w, h = (x1 - x0) * z, (y1 - y0) * z
    lin = (len(unicos) + cols - 1) // cols
    S = Image.new('RGB', (cols * (w + 3), lin * (h + 3)), (30, 30, 30))
    for i, (idx, _, _) in enumerate(unicos):
        im = Image.fromarray(A.rgba(idx)[y0:y1, x0:x1][..., :3]).resize((w, h), Image.NEAREST)
        S.paste(im, ((i % cols) * (w + 3), (i // cols) * (h + 3)))
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    S.save(caminho)
    print(caminho, S.size, len(unicos), 'desenhos')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'folha':
        che, saida = gerar_quadros([sys.argv[2]])
        folha(saida, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else os.path.join(SAIDA_TESTE, sys.argv[2] + '.png'))
    else:
        nomes = sys.argv[2].split(',') if len(sys.argv) > 2 and sys.argv[2] not in ('', 'todos') else None
        che, saida = gerar_quadros(nomes)
        if cmd == 'gerar':
            escrever(che, saida)
        else:
            ordem = nomes or ['idle', 'rugido', 'idle', 'golpe', 'garra', 'apanha', 'cambaleia', 'ajoelhado',
                              'carrega', 'carrega_segura', 'carrega_segura']
            gif(saida, ordem, sys.argv[3] if len(sys.argv) > 3 else os.path.join(SAIDA_TESTE, 'chefe.gif'))
