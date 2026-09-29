"""BONECO ARTICULADO do Bankai feito com o DESENHO 1 da referencia do usuario
(de lado, espada baixa), copiado pixel a pixel (bankai_ref.py).

O desenho e recortado em pecas com "ossos":
  cabelo/casaco - a massa de cabelo atras e as caudas do sobretudo: um campo
            de deformacao continuo (as mechas flutuam, a onda desce da raiz
            para as pontas; perto do corpo quase nao mexe);
  tronco, pernas - firmes (o tronco respira e inclina no quadril);
  cabeca  - gira um pouco no pescoco;
  braco -> antebraco -> espada - giram no ombro, no cotovelo e no punho.
Girar pixel art sem entortar: cada pixel de saida olha 4x4 pontos do desenho
girado e fica com a cor que MAIS aparece (estilo RotSprite, sem cor nova).
Onde o braco/espada cobriam o corpo, o buraco e preenchido com as cores
vizinhas (so por dentro do corpo; por fora vira vazio).

Cada CLIPE (idle, nasce, carga, corte, fim) e uma lista de quadros a 30/s
gerados aqui no PC; o app so toca os quadros (app/bankai/clipes.bin).
uso: python dev/bankai_rig.py previa     (pecas coloridas, para conferir o recorte)
     python dev/bankai_rig.py gerar      (gera os clipes e o arquivo do app)
     python dev/bankai_rig.py gif        (GIF de previa de todos os clipes)"""
import os
import sys
import math
import json
import zlib
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bankai_ref import extrair                                          # noqa: E402

APP = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
SAIDA_TESTE = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'ferramentas', 'saida_testes', 'rig')
FPS = 30
CW, CH = 330, 330                 # tela de cada quadro (sobra para a espada erguida)
OX, OY = 70, 100                  # onde o desenho 1 (193x193) fica dentro dela

# ── pontos do desenho 1 (pixels, y para baixo) ──────────────────────────
OMBRO = (95, 52)
COTOVELO = (98, 71)
MAO = (106, 90)
PONTA = (184, 180)
PESCOCO = (95, 47)
QUADRIL = (95, 124)               # vai na ancora do Yoru (pes no mesmo chao)
CINTURA_Y = 108
RAIZ_CABELO = (92, 34)
# cores extras (rastro do golpe e brilho da espada nascendo)
EXTRAS = [(238, 222, 255, 255), (214, 150, 255, 255), (160, 76, 255, 255), (96, 40, 190, 255)]


def _c(p):
    return (p[0] + OX, p[1] + OY)


def _dist_seg(xs, ys, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    L2 = float(vx * vx + vy * vy) or 1.0
    t = np.clip(((xs - ax) * vx + (ys - ay) * vy) / L2, 0.0, 1.0)
    return np.hypot(xs - (ax + t * vx), ys - (ay + t * vy)), t


# ═════════════════════════════════════════════════════════════════════
#  DESENHO E PECAS
# ═════════════════════════════════════════════════════════════════════
def base():
    a = extrair(1)
    a[:, 172:, 3] = 0
    tela = np.zeros((CH, CW, 4), np.uint8)
    tela[OY:OY + a.shape[0], OX:OX + a.shape[1]] = a
    return tela


def pecas(rgba):
    """Mascaras (bool, CHxCW) de cada peca."""
    h, w = rgba.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]
    tem = rgba[..., 3] > 0
    d_esp, t_esp = _dist_seg(xs, ys, _c(MAO), _c(PONTA))
    # a lamina e larga (miolo escuro + fio aceso dos dois lados)
    espada = tem & (((d_esp <= 5.5) & (t_esp > 0.02)) | ((d_esp <= 9.5) & (t_esp > 0.1)))
    d_b, _ = _dist_seg(xs, ys, _c(OMBRO), _c(COTOVELO))
    d_a, _ = _dist_seg(xs, ys, _c(COTOVELO), _c(MAO))
    braco = tem & (d_b <= 4.5) & ~espada
    antebraco = tem & (d_a <= 4.8) & ~espada & ~braco
    cabeca = tem & (np.hypot(xs - (99 + OX), ys - (35 + OY)) <= 13) & ~braco
    frente = 84 + OX + (ys - 40 - OY) * 0.05
    col = (xs >= frente) & (xs <= 112 + OX)
    tronco = tem & col & (ys >= 44 + OY) & (ys < CINTURA_Y + 6 + OY) & ~braco & ~antebraco & ~espada & ~cabeca
    pernas = tem & (xs >= 78 + OX) & (xs <= 115 + OX) & (ys >= 150 + OY) & ~espada
    casaco = tem & (ys >= CINTURA_Y + OY) & ~pernas & ~espada & ~braco & ~antebraco & ~tronco
    cabelo = tem & ~(espada | braco | antebraco | cabeca | tronco | pernas | casaco)
    return dict(cabelo=cabelo, casaco=casaco, pernas=pernas, tronco=tronco, cabeca=cabeca,
                braco=braco, antebraco=antebraco, espada=espada)


def indexar(rgba):
    """RGBA -> (indices uint8, paleta [(r,g,b,a)]); 0 = vazio."""
    tem = rgba[..., 3] > 0
    cores = {}
    pal = [(0, 0, 0, 0)]
    idx = np.zeros(rgba.shape[:2], np.uint8)
    for c in EXTRAS:
        cores[c] = len(pal)
        pal.append(c)
    ys, xs = np.nonzero(tem)
    for y, x in zip(ys, xs):
        c = (int(rgba[y, x, 0]), int(rgba[y, x, 1]), int(rgba[y, x, 2]), 255)
        i = cores.get(c)
        if i is None:
            i = cores[c] = len(pal)
            pal.append(c)
        idx[y, x] = i
    assert len(pal) <= 256, len(pal)
    return idx, pal


def _dilata(m, n):
    """Distancia (em passos de 4-vizinhos) ate a mascara m, ate n."""
    dist = np.full(m.shape, n + 1, np.int32)
    dist[m] = 0
    atual = m.copy()
    for k in range(1, n + 1):
        viz = atual.copy()
        viz[1:, :] |= atual[:-1, :]
        viz[:-1, :] |= atual[1:, :]
        viz[:, 1:] |= atual[:, :-1]
        viz[:, :-1] |= atual[:, 1:]
        novos = viz & ~atual
        dist[novos] = k
        atual = viz
    return dist


def preencher(idx, buraco, corpo):
    """Tapa o buraco (onde estavam braco/espada/cabeca) com a cor do vizinho,
    so por dentro do corpo (tem corpo dos dois lados na mesma linha)."""
    h, w = idx.shape
    out = idx.copy()
    out[buraco] = 0
    dentro = np.zeros_like(buraco)
    for y in range(h):
        linha = corpo[y] & ~buraco[y]
        if not buraco[y].any():
            continue
        xs_corpo = np.nonzero(linha)[0]
        if len(xs_corpo) == 0:
            continue
        for x in np.nonzero(buraco[y])[0]:
            esq = xs_corpo[(xs_corpo < x) & (xs_corpo >= x - 24)]
            dir_ = xs_corpo[(xs_corpo > x) & (xs_corpo <= x + 24)]
            if len(esq) and len(dir_):
                dentro[y, x] = True
    falta = dentro.copy()
    for passo in range(30):
        if not falta.any():
            break
        viz = np.zeros_like(out)
        vizs = ((0, 1), (0, -1), (1, 0), (-1, 0)) if passo % 2 else ((1, 0), (-1, 0), (0, -1), (0, 1))
        for dy, dx in vizs:
            sh = np.roll(np.roll(out, dy, axis=0), dx, axis=1)
            ok = (sh > 0) & (viz == 0)
            viz[ok] = sh[ok]
        pega = falta & (viz > 0)
        out[pega] = viz[pega]
        falta &= ~pega
    return out


# ═════════════════════════════════════════════════════════════════════
#  TRANSFORMACOES (matrizes 3x3, pixels da tela, y para baixo)
# ═════════════════════════════════════════════════════════════════════
def rot(pivo, graus):
    a = math.radians(graus)
    c, s = math.cos(a), math.sin(a)
    px, py = pivo
    return np.array([[c, -s, px - c * px + s * py], [s, c, py - s * px - c * py], [0, 0, 1.0]])


def mov(dx, dy):
    return np.array([[1, 0, dx], [0, 1, dy], [0, 0, 1.0]])


def aplica(M, p):
    v = M @ np.array([p[0], p[1], 1.0])
    return (v[0], v[1])


def desenha_peca(dest, fonte, masc, M, sub=4):
    """Desenha a peca (fonte[masc]) transformada por M em dest (indices),
    girando sem entortar: 4x4 amostras por pixel, fica a cor mais comum
    (vazio se a maioria for vazio)."""
    ys, xs = np.nonzero(masc)
    if len(ys) == 0:
        return
    cantos = np.array([[xs.min() - 1, ys.min() - 1], [xs.max() + 2, ys.min() - 1],
                       [xs.min() - 1, ys.max() + 2], [xs.max() + 2, ys.max() + 2]], float)
    tc = np.array([aplica(M, c) for c in cantos])
    x0, y0 = np.floor(tc.min(axis=0)).astype(int)
    x1, y1 = np.ceil(tc.max(axis=0)).astype(int)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(dest.shape[1], x1 + 1), min(dest.shape[0], y1 + 1)
    if x1 <= x0 or y1 <= y0:
        return
    Mi = np.linalg.inv(M)
    oy, ox = np.mgrid[y0:y1, x0:x1]
    h, w = oy.shape
    so = (np.arange(sub) + 0.5) / sub
    amostras = np.zeros((h, w, sub * sub), np.int32)
    fonte_m = np.where(masc, fonte, 0)
    k = 0
    for sy in so:
        for sx in so:
            X = ox + sx
            Y = oy + sy
            u = Mi[0, 0] * X + Mi[0, 1] * Y + Mi[0, 2]
            v = Mi[1, 0] * X + Mi[1, 1] * Y + Mi[1, 2]
            ui = np.floor(u).astype(int)
            vi = np.floor(v).astype(int)
            ok = (ui >= 0) & (vi >= 0) & (ui < fonte.shape[1]) & (vi < fonte.shape[0])
            val = np.zeros((h, w), np.int32)
            val[ok] = fonte_m[vi[ok], ui[ok]]
            amostras[..., k] = val
            k += 1
    cheios = (amostras > 0).sum(axis=2)
    visivel = cheios * 2 >= sub * sub
    # cor mais comum entre as amostras cheias
    moda = np.zeros((h, w), np.int32)
    melhor = np.zeros((h, w), np.int32)
    for j in range(sub * sub):
        c = amostras[..., j]
        cont = (amostras == c[..., None]).sum(axis=2)
        troca = (c > 0) & (cont > melhor)
        moda[troca] = c[troca]
        melhor[troca] = cont[troca]
    reg = dest[y0:y1, x0:x1]
    reg[visivel] = moda[visivel]


# ═════════════════════════════════════════════════════════════════════
#  O BONECO
# ═════════════════════════════════════════════════════════════════════
class Boneco:
    def __init__(self):
        rgba = base()
        self.m = pecas(rgba)
        self.idx, self.pal = indexar(rgba)
        m = self.m
        corpo = rgba[..., 3] > 0
        moveis = m['braco'] | m['antebraco'] | m['espada'] | m['cabeca']
        self.fundo = preencher(self.idx, moveis, corpo)
        # o fundo sem o que e firme (tronco e pernas vao por cima dele)
        self.mole = (self.fundo > 0) & ~(m['tronco'] | m['pernas'])
        firme = m['tronco'] | m['pernas'] | m['cabeca'] | m['braco'] | m['antebraco'] | m['espada']
        self.dist = _dilata(firme, 60).astype(float)            # distancia ao corpo firme
        ys, xs = np.mgrid[0:CH, 0:CW]
        self.ys, self.xs = ys, xs
        rx, ry = _c(RAIZ_CABELO)
        self.r_cab = np.hypot(xs - rx, ys - ry)
        self.r_cab /= max(1.0, self.r_cab[m['cabelo']].max())
        self.r_cas = np.clip((ys - (CINTURA_Y + OY)) / 80.0, 0, 1)
        _, self.t_esp = _dist_seg(xs, ys, _c(MAO), _c(PONTA))
        self.ruido = np.random.default_rng(5).random((CH, CW))
        self.claro = self.pal.index(EXTRAS[0])
        self.lilas = self.pal.index(EXTRAS[1])
        self.roxo = self.pal.index(EXTRAS[2])
        self.roxo_esc = self.pal.index(EXTRAS[3])

    # ── deformacao do cabelo e do casaco (flutuar) ──────────────────────
    def mole_deformado(self, t, amp=1.0, incl=0.0, bob=0.0, cresc_cab=1.0, cresc_cas=1.0):
        xs, ys = self.xs, self.ys
        A = np.clip(self.dist * 0.19, 0, 9.0) * amp
        s = self.dist / 22.0
        w = 2 * math.pi * t / 2.2
        dx = A * np.sin(w - s * 1.6) + 0.45 * A * np.sin(2 * w - s * 2.7 + 0.5)
        dy = 0.55 * A * np.sin(w - s * 1.6 + 1.3) - 0.25 * A          # flutua: sobe um pouco
        # o que esta acima do quadril vai junto com o tronco (inclina/respira)
        qx, qy = _c(QUADRIL)
        peso = np.clip((qy - ys) / 30.0, 0, 1)
        if incl:
            a = math.radians(incl)
            ux, uy = xs - qx, ys - qy
            dx = dx + peso * (math.cos(a) * ux - math.sin(a) * uy - ux)
            dy = dy + peso * (math.sin(a) * ux + math.cos(a) * uy - uy)
        dy = dy + peso * bob
        sx = np.clip(np.rint(xs - dx).astype(int), 0, CW - 1)
        sy = np.clip(np.rint(ys - dy).astype(int), 0, CH - 1)
        fonte = np.where(self.mole, self.fundo, 0)
        out = fonte[sy, sx]
        if cresc_cab < 1.0 or cresc_cas < 1.0:
            mc = self.m['cabelo'][sy, sx]
            mk = self.m['casaco'][sy, sx]
            rn = self.ruido[sy, sx] * 0.07
            esconde = (mc & (self.r_cab[sy, sx] > cresc_cab + rn)) | (mk & (self.r_cas[sy, sx] > cresc_cas + rn))
            out = np.where(esconde, 0, out)
        return out

    # ── um quadro ───────────────────────────────────────────────────────
    def quadro(self, t, b=0.0, a=0.0, e=0.0, cab=0.0, incl=0.0, bob=0.0, amp=1.0,
               cresc_cab=1.0, cresc_cas=1.0, cresc_esp=1.0, rastro=None):
        """Angulos em graus (+ = sentido horario na tela): b = braco no
        ombro, a = antebraco no cotovelo, e = espada no punho, cab = cabeca;
        incl = tronco inclinando no quadril; bob = tronco sobe/desce (px).
        rastro = (angulo_espada_antes) para o rastro do golpe."""
        m = self.m
        img = self.mole_deformado(t, amp, incl, bob, cresc_cab, cresc_cas)
        img = np.where(m['pernas'], self.idx, img).astype(np.int32)
        H = rot(_c(QUADRIL), incl) @ mov(0, bob)
        desenha_peca(img, self.idx, m['tronco'], H)
        desenha_peca(img, self.idx, m['cabeca'], H @ rot(_c(PESCOCO), cab))
        Mb = H @ rot(_c(OMBRO), b)
        Ma = Mb @ rot(_c(COTOVELO), a)
        Me = Ma @ rot(_c(MAO), e)
        esp = m['espada']
        if cresc_esp < 1.0:
            esp = esp & (self.t_esp <= cresc_esp)
        if rastro is not None:
            self._rastro(img, Ma, rastro, e)
        desenha_peca(img, self.idx, m['braco'], Mb)
        desenha_peca(img, self.idx, esp, Me)
        desenha_peca(img, self.idx, m['antebraco'], Ma)
        if cresc_esp < 1.0:                                   # a ponta que nasce brilha
            ponta = m['espada'] & (self.t_esp > cresc_esp - 0.05) & (self.t_esp <= cresc_esp)
            tmp = np.where(ponta, self.claro, 0).astype(np.int32)
            desenha_peca(img, tmp, ponta, Me)
        mao = aplica(Ma, _c(MAO))
        ponta_p = aplica(Me, _c(PONTA))
        return img.astype(np.uint8), mao, ponta_p

    def _rastro(self, img, Ma, e_antes, e_agora):
        """Rastro (smear) do golpe: a faixa que a lamina varreu entre o angulo
        de antes e o de agora, lilas perto do fio e roxo por dentro."""
        cx, cy = aplica(Ma, _c(MAO))
        L = math.hypot(PONTA[0] - MAO[0], PONTA[1] - MAO[1])
        base_ang = math.degrees(math.atan2(PONTA[1] - MAO[1], PONTA[0] - MAO[0]))
        ang_fixo = math.degrees(math.atan2(Ma[1, 0], Ma[0, 0]))
        a0 = base_ang + ang_fixo + e_antes
        a1 = base_ang + ang_fixo + e_agora
        lo, hi = min(a0, a1), max(a0, a1)
        if hi - lo < 4:
            return
        xs, ys = self.xs, self.ys
        ang = np.degrees(np.arctan2(ys - cy, xs - cx))
        # coloca o angulo perto do intervalo
        ang = np.where(ang < lo - 180, ang + 360, ang)
        ang = np.where(ang > hi + 180, ang - 360, ang)
        r = np.hypot(xs - cx, ys - cy) / L
        fr = (ang - lo) / max(1e-6, hi - lo)
        k = fr if a1 > a0 else 1 - fr                       # 1 junto da lamina atual, 0 na cauda
        # meia-lua solida: larga junto da lamina, afina ate a ponta na cauda
        r_fora = 1.02 - 0.18 * (1 - k)
        r_dentro = 0.5 + 0.42 * (1 - k) ** 1.4
        dentro = (ang >= lo) & (ang <= hi) & (r > r_dentro) & (r < r_fora)
        larg = np.maximum(1e-6, r_fora - r_dentro)
        pos = (r - r_dentro) / larg                          # 0 por dentro .. 1 no fio
        cor = np.where(pos > 0.82, self.claro, np.where(pos > 0.5, self.lilas,
                       np.where(k > 0.45, self.roxo, self.roxo_esc)))
        pinta = dentro & (img == 0)
        img[pinta] = cor[pinta]


# ═════════════════════════════════════════════════════════════════════
#  CLIPES (cada chave: tempo em quadros -> valores; tudo interpolado com
#  curvas de animacao; o que nao muda fica no valor de repouso)
# ═════════════════════════════════════════════════════════════════════
REPOUSO = dict(b=0.0, a=0.0, e=0.0, cab=0.0, incl=0.0, bob=0.0, amp=1.0)


def _suave(u):
    return u * u * (3 - 2 * u)


def _curva(nome, u):
    if nome == 'in':
        return u * u * u
    if nome == 'out':
        return 1 - (1 - u) ** 3
    if nome == 'mola':
        c1 = 1.5
        return 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2
    return _suave(u)


def trilha(chaves, n):
    """chaves: [(quadro, {valores}, curva_ate_a_proxima), ...] -> lista de n dicts."""
    out = []
    for f in range(n):
        ant = chaves[0]
        prox = chaves[-1]
        for i in range(len(chaves) - 1):
            if chaves[i][0] <= f <= chaves[i + 1][0]:
                ant, prox = chaves[i], chaves[i + 1]
                break
        f0, v0, cur = ant[0], ant[1], ant[2] if len(ant) > 2 else 'suave'
        f1, v1 = prox[0], prox[1]
        u = 0.0 if f1 == f0 else (f - f0) / float(f1 - f0)
        k = _curva(cur, max(0.0, min(1.0, u)))
        q = dict(REPOUSO)
        for chave in set(v0) | set(v1):
            a = v0.get(chave, REPOUSO.get(chave, 0.0))
            b = v1.get(chave, REPOUSO.get(chave, 0.0))
            q[chave] = a + (b - a) * k
        out.append(q)
    return out


def respira(q, t, forca=1.0):
    """O vivo em cima de qualquer pose: respira, o braco balanca de leve, a
    ponta da espada flutua, a cabeca acompanha."""
    w = 2 * math.pi * t / 2.2
    q = dict(q)
    q['bob'] = q.get('bob', 0.0) + forca * 1.2 * math.sin(w)
    q['b'] = q.get('b', 0.0) + forca * 2.5 * math.sin(w + 0.5)
    q['a'] = q.get('a', 0.0) + forca * 2.0 * math.sin(w + 1.0)
    q['e'] = q.get('e', 0.0) + forca * 1.5 * math.sin(w + 1.6)
    q['cab'] = q.get('cab', 0.0) + forca * 1.2 * math.sin(w + 0.3)
    return q


# golpe (graus a partir do desenho, + = horario): carrega com a lamina baixa
# para tras (como o desenho 4 da referencia) e corta SUBINDO pela frente -
# o braco passa na altura do peito, o rosto fica sempre a vista.
# direcao do braco = 74 + b; da lamina = 49 + b + a + e (graus na tela)
CARGA = dict(b=46.0, a=10.0, e=70.0, incl=6.0, bob=3.0, cab=2.0)      # lamina para tras, baixa
MEIO = dict(b=-4.0, a=-5.0, e=0.0, incl=2.0, bob=1.0)                  # passa embaixo, pela frente
CORTOU = dict(b=-74.0, a=-10.0, e=-10.0, incl=-4.0, cab=-3.0)          # lamina para cima e para a frente
SEGUE = dict(b=-99.0, a=-12.0, e=-12.0, incl=-6.0, cab=-4.0)


def clipes():
    """{nome: (lista de parametros por quadro, loop)}"""
    C = {}
    n = 66                                                       # 2,2 s: um ciclo inteiro
    C['idle'] = ([respira(dict(REPOUSO), f / FPS) for f in range(n)], True)
    # nasce: o cabelo cresce da raiz, as caudas descem, a lamina nasce da guarda
    n = 48
    lst = []
    for f in range(n):
        u = f / float(n - 1)
        q = respira(dict(REPOUSO), f / FPS, forca=0.6)
        q['cresc_cab'] = 0.12 + 0.88 * _curva('out', min(1.0, u / 0.7))
        q['cresc_cas'] = 0.15 + 0.85 * _curva('out', max(0.0, min(1.0, (u - 0.1) / 0.65)))
        q['cresc_esp'] = _curva('in', max(0.0, min(1.0, (u - 0.35) / 0.6)))
        q['amp'] = 0.4 + 0.6 * u
        lst.append(q)
    C['nasce'] = (lst, False)
    # carga: ergue a espada devagar (antecipacao) e segura tremendo
    lst = trilha([(0, dict(REPOUSO), 'in'), (6, dict(b=-6.0, a=-4.0, e=-6.0, incl=-2.0), 'suave'),
                  (22, CARGA, 'out'), (27, dict(CARGA, b=CARGA['b'] + 4), 'suave')], 28)
    lst = [respira(q, f / FPS, 0.4) for f, q in enumerate(lst)]
    C['carga'] = (lst, False)
    trem = []
    for f in range(12):                                         # segura a carga tremendo
        q = dict(CARGA, b=CARGA['b'] + 4)
        q['bob'] = CARGA['bob'] + (1.0 if f % 4 < 2 else -1.0) * 0.8
        q['e'] += 1.5 * math.sin(f * 2.1)
        q['amp'] = 1.3
        trem.append(q)
    C['carga_segura'] = (trem, True)
    # corte: acelera (rastro) -> impacto -> continua -> acomoda
    chaves = [(0, dict(CARGA, b=CARGA['b'] + 4), 'in'), (4, MEIO, 'out'),
              (7, CORTOU, 'out'), (11, SEGUE, 'mola'), (17, dict(SEGUE, b=-92.0), 'suave'),
              (18, dict(SEGUE, b=-92.0))]
    lst = trilha(chaves, 19)
    for f, q in enumerate(lst):
        q['amp'] = 1.2
        if 1 <= f <= 8:
            q['rastro'] = lst[f - 1]['b'] + lst[f - 1]['a'] + lst[f - 1]['e'] - q['b'] - q['a']
    C['corte'] = (lst, False)
    # fim: volta devagar ao repouso (o cabelo e o casaco ainda flutuando)
    lst = trilha([(0, dict(SEGUE, b=-92.0), 'suave'), (26, dict(REPOUSO))], 27)
    C['fim'] = ([respira(q, f / FPS, f / 24.0) for f, q in enumerate(lst)], False)
    return C


def gerar_quadros():
    bon = Boneco()
    saida = {}
    for nome, (lst, loop) in clipes().items():
        quadros = []
        t0 = 0.0
        for f, q in enumerate(lst):
            t = (t0 + f) / FPS
            kw = {k: v for k, v in q.items() if k in ('b', 'a', 'e', 'cab', 'incl', 'bob', 'amp', 'cresc_cab',
                                                       'cresc_cas', 'cresc_esp')}
            img, mao, ponta = bon.quadro(t, rastro=q.get('rastro'), **kw)
            quadros.append((img, mao, ponta))
        saida[nome] = (quadros, loop)
        print(nome, len(quadros), 'quadros')
    return bon, saida


def escrever(bon, saida):
    """app/bankai/clipes.bin: b'BK01' + tamanho do cabecalho + cabecalho json
    (zlib) + cada quadro em zlib (1 byte por pixel = cor da paleta), recortado
    na caixa do que aparece. E o app/bankai_desenhos.py com os pontos."""
    blocos = []
    cab = {'paleta': bon.pal, 'tela': [CW, CH], 'quadril': list(_c(QUADRIL)), 'fps': FPS, 'clipes': {}}
    pos = 0
    for nome, (quadros, loop) in saida.items():
        lst = []
        for img, mao, ponta in quadros:
            ys, xs = np.nonzero(img)
            x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
            dados = zlib.compress(img[y0:y1, x0:x1].tobytes(), 9)
            blocos.append(dados)
            lst.append([pos, len(dados), [x0, y0, x1 - x0, y1 - y0],
                        [round(mao[0], 1), round(mao[1], 1)], [round(ponta[0], 1), round(ponta[1], 1)]])
            pos += len(dados)
        cab['clipes'][nome] = {'loop': loop, 'quadros': lst}
    cz = zlib.compress(json.dumps(cab).encode('utf-8'), 9)
    os.makedirs(os.path.join(APP, 'bankai'), exist_ok=True)
    caminho = os.path.join(APP, 'bankai', 'clipes.bin')
    with open(caminho, 'wb') as fp:
        fp.write(b'BK01')
        fp.write(len(cz).to_bytes(4, 'little'))
        fp.write(cz)
        for b in blocos:
            fp.write(b)
    print(caminho, os.path.getsize(caminho) // 1024, 'KB')


def gif(bon, saida):
    os.makedirs(SAIDA_TESTE, exist_ok=True)
    pal = np.array(bon.pal, np.uint8)
    frames = []
    ordem = ['nasce', 'idle', 'carga', 'carga_segura', 'carga_segura', 'corte', 'fim', 'idle']
    for nome in ordem:
        for img, mao, ponta in saida[nome][0]:
            rgba = pal[img]
            fundo = np.zeros((CH, CW, 3), np.uint8) + np.array([8, 6, 16], np.uint8)
            a = rgba[..., 3:4] / 255.0
            rgb = (rgba[..., :3] * a + fundo * (1 - a)).astype(np.uint8)
            im = Image.fromarray(rgb).resize((CW * 2, CH * 2), Image.NEAREST)
            frames.append(im.quantize(colors=200))
    caminho = os.path.join(SAIDA_TESTE, 'rig.gif')
    frames[0].save(caminho, save_all=True, append_images=frames[1:], duration=33, loop=0)
    print(caminho, len(frames), 'quadros')


if __name__ == '__main__':
    if sys.argv[1] == 'previa':
        from PIL import Image as _I
        b = Boneco()
        pal = np.array(b.pal, np.uint8)
        _I.fromarray(pal[b.fundo]).resize((CW * 3, CH * 3), _I.NEAREST).save(os.path.join(SAIDA_TESTE, 'fundo.png'))
        print('ok')
    elif sys.argv[1] in ('gerar', 'gif'):
        bon, saida = gerar_quadros()
        escrever(bon, saida)
        gif(bon, saida)
