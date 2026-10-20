"""BANKAI do Yoru: o DESENHO 1 da referencia do usuario (referencias/
2026-09-29_bankai_referencia.png, de lado, espada baixa), copiado pixel a pixel
(bankai_ref.extrair, s=3.0: do tamanho do Yoru normal), animado PECA POR PECA.

Versao 1 (erro): um campo de onda entortava o cabelo e o casaco inteiros de
uma vez - cada pixel ia para um lado, virava listras ("lona").
Agora:
  cabelo  - cortado em MECHAS que seguem os fios do proprio desenho (cada
            pixel vai para a mecha cuja espinha esta mais perto);
  casaco  - cortado em ABAS do mesmo jeito;
  cada mecha/aba se mexe INTEIRA: a espinha dobra (a onda sai da raiz e
            chega atrasada na ponta) e cada pixel so ANDA em passos de pixel
            inteiro, junto com o pedaco da mecha em que esta - o desenho nao
            e reamostrado, nenhum detalhe some;
  tronco, pernas, cabeca - firmes (o corpo sobe e desce 1 pixel);
  braco -> antebraco -> espada - giram no ombro/cotovelo/punho so nos
            golpes (girar e reamostrar; parado eles ficam como no desenho).
Os desenhos do Bankai trocam 24 vezes por segundo (anime "em 1s"; antes
10 a 15) e o reiatsu 30 vezes por segundo (cada clipe guarda o proprio ritmo
no clipes.bin: 'fps').

Os clipes vao para app/bankai/clipes.bin (quadros repetidos sao guardados
uma vez so); o app so toca os quadros.
uso: python dev/bankai_rig.py mechas SAIDA.png   (as mechas/abas coloridas)
     python dev/bankai_rig.py gerar             (clipes -> app/bankai/clipes.bin)
     python dev/bankai_rig.py gif [clipes]      (GIF de previa)"""
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
FPS = 30                          # linha do tempo do app (os avisos de quadro contam em 30/s)
FPS_CORPO = 24                    # desenhos do Bankai por segundo
FPS_REI = 30                      # desenhos do reiatsu por segundo
S_DESENHO = 3.0                   # px da referencia por pixel: do tamanho do Yoru normal
CW, CH = 320, 320                 # tela de cada quadro
OX, OY = 70, 110                  # onde o desenho (170x170) fica dentro dela

# ── pontos do desenho (pixels do desenho, y para baixo) ─────────────────
OMBRO = (84.0, 46.0)
COTOVELO = (86.6, 62.7)
MAO = (93.6, 79.5)
PONTA = (162.5, 159.0)
PESCOCO = (84.0, 41.5)
QUADRIL = (84.0, 109.5)           # vai na ancora do Yoru
CINTURA_Y = 95.4
CABECA = (87.4, 30.9, 11.5)       # centro e raio
# cores extras (rastro do golpe e brilho) + luz de fundo roxa na borda de
# fora (costas/topo) e o escuro que fecha os buraquinhos de dentro do desenho
EXTRAS = [(238, 222, 255, 255), (214, 150, 255, 255), (160, 76, 255, 255), (96, 40, 190, 255)]
ARO = (104, 54, 196, 255)
FECHO = (12, 7, 20, 255)

# ── espinhas das MECHAS do cabelo (seguem os fios do desenho, raiz -> ponta)
MECHAS = [
    [(72, 16), (55, 20), (40, 28), (25, 38), (12, 50), (5, 58)],
    [(74, 20), (58, 26), (42, 36), (28, 46), (17, 58), (10, 70), (8, 80)],
    [(76, 24), (60, 32), (46, 44), (35, 56), (26, 68), (20, 80), (16, 88)],
    [(77, 28), (64, 40), (52, 52), (42, 64), (34, 76), (28, 88), (24, 96)],
    [(78, 32), (68, 46), (58, 58), (50, 70), (44, 82), (40, 94)],
    [(79, 36), (72, 52), (64, 64), (58, 76), (54, 88), (50, 98)],
    [(80, 40), (76, 56), (72, 68), (68, 80), (66, 92)],
]
# ── espinhas das ABAS do sobretudo (da cintura para a barra)
ABAS = [
    [(72, 96), (55, 108), (40, 120), (25, 132), (10, 142)],
    [(74, 98), (60, 114), (47, 128), (35, 142), (22, 152)],
    [(76, 100), (66, 118), (57, 134), (48, 150), (42, 158)],
    [(78, 102), (72, 120), (66, 138), (62, 152)],
    [(80, 104), (76, 124), (73, 142), (71, 156)],
    [(97, 96), (101, 112), (104, 128), (106, 142)],
    [(101, 94), (107, 110), (111, 124)],
]


def _c(p):
    return (p[0] + OX, p[1] + OY)


def _dist_seg(xs, ys, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    L2 = float(vx * vx + vy * vy) or 1.0
    t = np.clip(((xs - ax) * vx + (ys - ay) * vy) / L2, 0.0, 1.0)
    return np.hypot(xs - (ax + t * vx), ys - (ay + t * vy)), t


def _reamostra(pts, n=14):
    """Espinha com n pontos igualmente espacados (suavizada)."""
    pts = np.asarray(pts, float)
    d = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0], np.cumsum(d)])
    alvo = np.linspace(0, s[-1], n)
    out = np.stack([np.interp(alvo, s, pts[:, 0]), np.interp(alvo, s, pts[:, 1])], axis=1)
    for _ in range(2):                               # suaviza os cotovelos da espinha
        out[1:-1] = 0.25 * out[:-2] + 0.5 * out[1:-1] + 0.25 * out[2:]
    return out


# ═════════════════════════════════════════════════════════════════════
#  DESENHO, PECAS E MECHAS
# ═════════════════════════════════════════════════════════════════════
def base():
    a = extrair(1, s=S_DESENHO)
    a[:, 152:, 3] = 0                                # pedaco do desenho vizinho
    tela = np.zeros((CH, CW, 4), np.uint8)
    tela[OY:OY + a.shape[0], OX:OX + a.shape[1]] = a
    return tela


def pecas(rgba):
    """Mascaras (bool, CHxCW) das pecas firmes; o resto (cabelo + casaco) e
    'mole' e vai ser dividido em mechas/abas."""
    tem = rgba[..., 3] > 0
    ys, xs = np.mgrid[0:CH, 0:CW]
    d_esp, t_esp = _dist_seg(xs, ys, _c(MAO), _c(PONTA))
    espada = tem & (((d_esp <= 4.9) & (t_esp > 0.02)) | ((d_esp <= 8.4) & (t_esp > 0.1)))
    d_b, _ = _dist_seg(xs, ys, _c(OMBRO), _c(COTOVELO))
    d_a, _ = _dist_seg(xs, ys, _c(COTOVELO), _c(MAO))
    braco = tem & (d_b <= 4.0) & ~espada
    antebraco = tem & (d_a <= 4.3) & ~espada & ~braco
    cx, cy, r = CABECA
    cabeca = tem & (np.hypot(xs - (cx + OX), ys - (cy + OY)) <= r) & ~braco
    X, Y = xs - OX, ys - OY
    frente = 74.2 + (Y - 35.3) * 0.05
    tronco = tem & (X >= frente) & (X <= 98.9) & (Y >= 38.9) & (Y < 100.7) & ~braco & ~antebraco & ~espada & ~cabeca
    pernas = tem & (X >= 73) & (X <= 100) & (Y >= 114) & ~espada
    mole = tem & ~(espada | braco | antebraco | cabeca | tronco | pernas)
    return dict(mole=mole, pernas=pernas, tronco=tronco, cabeca=cabeca, braco=braco,
                antebraco=antebraco, espada=espada)


def indexar(rgba):
    """RGBA -> (indices uint8, paleta [(r,g,b,a)]); 0 = vazio."""
    tem = rgba[..., 3] > 0
    cores = {}
    pal = [(0, 0, 0, 0)]
    idx = np.zeros(rgba.shape[:2], np.uint8)
    for c in EXTRAS + [ARO, FECHO]:
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


class Mecha:
    """Um pedaco mole (mecha de cabelo ou aba do casaco): os pixels do
    desenho que ficam mais perto desta espinha, cada um com o seu u
    (0 na raiz .. 1 na ponta)."""

    def __init__(self, espinha, ys, xs, cores, u, amp, fase, rigidez, aba):
        self.esp = espinha                            # (n, 2) na tela
        self.ys, self.xs, self.cores, self.u = ys, xs, cores, u
        self.amp, self.fase, self.rigidez, self.aba = amp, fase, rigidez, aba
        d = np.hypot(*np.diff(espinha, axis=0).T)
        self.s = np.concatenate([[0], np.cumsum(d)]) / max(1e-6, d.sum())

    def deslocamento(self, t, vento):
        """Quanto cada pixel anda (dx, dy inteiros) neste desenho."""
        e = self.esp
        n = len(e)
        per = vento.get('per', 2.4)
        onda = vento.get('onda', 7.0) * self.amp * (0.7 if self.aba else 1.0)
        sobe = vento.get('sobe', 0.0)
        vx = vento.get('x', 0.0)
        pts = [e[0].copy()]
        for k in range(n - 1):
            f = (k + 0.5) / (n - 1)
            g = max(0.0, f - self.rigidez) / (1.0 - self.rigidez)   # perto da raiz nao mexe
            th = onda * g ** 1.3 * math.sin(2 * math.pi * t / per - 2.6 * f + self.fase)
            th += 0.35 * onda * g ** 1.6 * math.sin(4 * math.pi * t / per - 4.1 * f + 2 * self.fase)
            th += (sobe * 38.0 * g ** 0.8) + vx * g
            r = math.radians(th)
            v = e[k + 1] - e[k]
            c, s = math.cos(r), math.sin(r)
            pts.append(pts[-1] + np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]]))
        D = np.array(pts) - e
        dx = np.interp(self.u, self.s, D[:, 0])
        dy = np.interp(self.u, self.s, D[:, 1])
        return np.rint(dx).astype(int), np.rint(dy).astype(int)


def _dilata(m, n):
    out = m.copy()
    for _ in range(n):
        v = out.copy()
        v[1:, :] |= out[:-1, :]
        v[:-1, :] |= out[1:, :]
        v[:, 1:] |= out[:, :-1]
        v[:, :-1] |= out[:, 1:]
        out = v
    return out


def _erode(m, n):
    return ~_dilata(~m, n)


def contorno(img, i_aro, i_fecho):
    """Fecha os buraquinhos de dentro do desenho (ficam escuros: a silhueta
    fica solida) e poe a luz de fundo roxa so na borda de FORA, do lado das
    costas e em cima - o Bankai destaca do fundo escuro do app."""
    cheio = img > 0
    solido = _erode(_dilata(cheio, 2), 2)
    out = img.copy()
    out[solido & ~cheio] = i_fecho
    s = solido
    viz_d = np.zeros_like(s)
    viz_b = np.zeros_like(s)
    viz_d[:, :-1] = s[:, 1:]                       # tem desenho a direita
    viz_b[:-1, :] = s[1:, :]                       # tem desenho embaixo
    luz = ~s & (viz_d | viz_b)
    out[luz] = i_aro
    return out


# ═════════════════════════════════════════════════════════════════════
#  GIRAR PECAS FIRMES (so braco/antebraco/espada nos golpes)
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
    """Desenha a peca (fonte[masc]) transformada por M em dest (indices).
    Sem giro: so copia deslocada (nenhum pixel muda). Com giro: 4x4 amostras
    por pixel e fica a cor mais comum (sem cor nova, estilo RotSprite)."""
    ys, xs = np.nonzero(masc)
    if len(ys) == 0:
        return
    if abs(M[0, 1]) < 1e-9 and abs(M[1, 0]) < 1e-9 and abs(M[0, 0] - 1) < 1e-9:
        dx, dy = int(round(M[0, 2])), int(round(M[1, 2]))
        yy, xx = ys + dy, xs + dx
        ok = (yy >= 0) & (yy < dest.shape[0]) & (xx >= 0) & (xx < dest.shape[1])
        dest[yy[ok], xx[ok]] = fonte[ys[ok], xs[ok]]
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
        moveis = m['braco'] | m['antebraco'] | m['espada']
        self.fundo = preencher(self.idx, moveis, corpo)       # corpo sem braco/espada
        ys, xs = np.mgrid[0:CH, 0:CW]
        self.xs, self.ys = xs, ys
        _, self.t_esp = _dist_seg(xs, ys, _c(MAO), _c(PONTA))
        self.claro = self.pal.index(EXTRAS[0])
        self.lilas = self.pal.index(EXTRAS[1])
        self.roxo = self.pal.index(EXTRAS[2])
        self.roxo_esc = self.pal.index(EXTRAS[3])
        self.i_aro = self.pal.index(ARO)
        self.i_fecho = self.pal.index(FECHO)
        # a parte mole (cabelo + casaco, ja sem o braco por cima) vira mechas
        mole = (self.fundo > 0) & ~(m['tronco'] | m['pernas'] | m['cabeca'])
        self.mole = mole
        esp_c = [_reamostra([_c(p) for p in e]) for e in MECHAS]
        esp_a = [_reamostra([_c(p) for p in e]) for e in ABAS]
        todas = esp_c + esp_a
        py, px = np.nonzero(mole)
        melhor = np.full(len(py), 1e9)
        dono = np.zeros(len(py), int)
        uu = np.zeros(len(py))
        for i, e in enumerate(todas):
            d = np.hypot(*np.diff(e, axis=0).T)
            acum = np.concatenate([[0], np.cumsum(d)]) / d.sum()
            for k in range(len(e) - 1):
                dist, t = _dist_seg(px + 0.5, py + 0.5, e[k], e[k + 1])
                # casaco nao pega cabelo muito acima da cintura e vice-versa
                if i >= len(esp_c):
                    dist = dist + np.where(py < _c((0, CINTURA_Y - 8))[1], 30.0, 0.0)
                melhor_k = dist < melhor
                melhor = np.where(melhor_k, dist, melhor)
                dono = np.where(melhor_k, i, dono)
                uu = np.where(melhor_k, acum[k] + t * (acum[k + 1] - acum[k]), uu)
        rnd = np.random.default_rng(3)
        self.mechas = []
        for i, e in enumerate(todas):
            sel = dono == i
            aba = i >= len(esp_c)
            f = i / float(len(esp_c) - 1) if not aba else (i - len(esp_c)) / float(len(esp_a) - 1)
            amp = (0.8 + 0.5 * f + rnd.uniform(-0.1, 0.1)) if not aba else (1.1 - 0.5 * f)
            fase = (2.4 * f + rnd.uniform(0, 0.5)) if not aba else (1.8 * f + 0.7)
            rig = 0.12 if not aba else 0.18
            self.mechas.append(Mecha(e, py[sel], px[sel], self.fundo[py[sel], px[sel]], uu[sel],
                                     amp, fase, rig, aba))
        self.dono = np.full((CH, CW), -1, int)
        self.dono[py, px] = dono
        # o que fica atras quando duas mechas se afastam: o proprio cabelo,
        # parado, so por dentro (a borda de fora e sempre das mechas)
        self.miolo = _erode(mole, 3)
        # olhos (para acender): o roxo dentro do rosto
        cx, cy, r = CABECA
        rosto = (np.hypot(xs - (cx + 3 + OX), ys - (cy + 4 + OY)) <= 7)
        cor = np.array(self.pal, np.int32)[self.idx]
        roxo = (cor[..., 2] > cor[..., 1] + 40) & (cor[..., 0] > 60) & (cor[..., 3] > 0)
        self.olhos = rosto & roxo & (self.idx > 0)

    def quadro(self, t, vento, b=0.0, a=0.0, e=0.0, bob=0, olhos='a', cresce_esp=1.0, rastro=None):
        """Um desenho. t = tempo do cabelo/casaco (ja em degraus); b/a/e =
        giro do braco/antebraco/espada (graus, + = horario); bob = o corpo
        inteiro sobe (-) ou desce (+) em pixels. -> (indices, mao, ponta)"""
        m = self.m
        img = np.zeros((CH, CW), np.int32)
        # 1) miolo parado (so aparece nos vaos entre mechas)
        img[self.miolo] = self.fundo[self.miolo]
        # 2) mechas e abas: cada uma inteira, em passos de pixel
        for mc in self.mechas:
            if len(mc.ys) == 0:
                continue
            dx, dy = mc.deslocamento(t, vento)
            yy, xx = mc.ys + dy, mc.xs + dx
            ok = (yy >= 0) & (yy < CH) & (xx >= 0) & (xx < CW)
            img[yy[ok], xx[ok]] = mc.cores[ok]
        # 3) corpo firme (pernas, tronco, cabeca como no desenho)
        firme = m['pernas'] | m['tronco'] | m['cabeca']
        img[firme] = self.fundo[firme]
        if olhos == 'l':
            img[self.olhos] = self.claro
        # 4) braco, espada, antebraco
        Mb = rot(_c(OMBRO), b)
        Ma = Mb @ rot(_c(COTOVELO), a)
        Me = Ma @ rot(_c(MAO), e)
        esp = m['espada']
        if cresce_esp < 1.0:
            esp = esp & (self.t_esp <= cresce_esp)
        if rastro is not None:
            self._rastro(img, Ma, rastro, e)
        desenha_peca(img, self.idx, m['braco'], Mb)
        desenha_peca(img, self.idx, esp, Me)
        desenha_peca(img, self.idx, m['antebraco'], Ma)
        mao = aplica(Ma, _c(MAO))
        ponta = aplica(Me, _c(PONTA))
        img = contorno(img, self.i_aro, self.i_fecho)
        if bob:
            img = np.roll(img, int(bob), axis=0)
            mao = (mao[0], mao[1] + bob)
            ponta = (ponta[0], ponta[1] + bob)
        return img.astype(np.uint8), mao, ponta

    def _rastro(self, img, Ma, e_antes, e_agora):
        """Rastro (smear) do golpe: meia-lua solida entre o angulo da lamina
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
        ang = np.where(ang < lo - 180, ang + 360, ang)
        ang = np.where(ang > hi + 180, ang - 360, ang)
        r = np.hypot(xs - cx, ys - cy) / L
        fr = np.clip((ang - lo) / max(1e-6, hi - lo), 0.0, 1.0)
        k = fr if a1 > a0 else 1 - fr
        r_fora = 1.02 - 0.18 * (1 - k)
        r_dentro = 0.5 + 0.42 * (1 - k) ** 1.4
        dentro = (ang >= lo) & (ang <= hi) & (r > r_dentro) & (r < r_fora)
        larg = np.maximum(1e-6, r_fora - r_dentro)
        pos = (r - r_dentro) / larg
        cor = np.where(pos > 0.82, self.claro, np.where(pos > 0.5, self.lilas,
                       np.where(k > 0.45, self.roxo, self.roxo_esc)))
        pinta = dentro & (img == 0)
        img[pinta] = cor[pinta]


# ═════════════════════════════════════════════════════════════════════
#  CLIPES: cada quadro (30/s) -> (pose, tempo do cabelo, vento). O desenho
#  so muda em degraus; entre eles o quadro repete (guardado uma vez so).
# ═════════════════════════════════════════════════════════════════════
REPOUSO = dict(b=0.0, a=0.0, e=0.0, bob=0)


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
        a = v0.get(ch, REPOUSO.get(ch, 0.0))
        b = v1.get(ch, REPOUSO.get(ch, 0.0))
        q[ch] = a + (b - a) * k if isinstance(a, (int, float)) and isinstance(b, (int, float)) else b
    return q


def degrau(t, por_s):
    return math.floor(t * por_s + 1e-6) / float(por_s)


P_IDLE = 2.5                      # ciclo do cabelo parado (s): 60 desenhos, o loop fecha certinho
# golpe (graus a partir do desenho, + = horario): carrega com a lamina baixa
# para tras e corta SUBINDO pela frente (o rosto fica sempre a vista)
CARGA = dict(b=46.0, a=10.0, e=70.0, bob=2)
MEIO = dict(b=-4.0, a=-5.0, e=0.0, bob=1)
CORTOU = dict(b=-74.0, a=-10.0, e=-10.0, bob=-1)
SEGUE = dict(b=-99.0, a=-12.0, e=-12.0, bob=-2)


def _vivo(q, tc, forca=1.0):
    """Respira: o corpo sobe e desce 1 pixel e o braco balanca de leve."""
    w = 2 * math.pi * tc / P_IDLE
    q = dict(q)
    q['bob'] = int(round(q.get('bob', 0) + forca * 1.2 * math.sin(w)))
    q['b'] = q.get('b', 0.0) + forca * 1.5 * math.sin(w + 0.6)
    q['a'] = q.get('a', 0.0) + forca * 1.2 * math.sin(w + 1.1)
    q['e'] = q.get('e', 0.0) + forca * 1.0 * math.sin(w + 1.6)
    return q


def clipes():
    """{nome: (funcao t -> (pose, t_cabelo, vento), duracao_s, loop)}"""
    CL = {}

    # PARADO flutuando (o braco fica como no desenho: sem girar)
    def idle(t):
        tc = degrau(t, FPS_CORPO)
        q = dict(REPOUSO)
        q['bob'] = int(round(1.2 * math.sin(2 * math.pi * tc / P_IDLE)))
        return q, tc, dict(onda=7.0, per=P_IDLE, sobe=0.05)
    CL['idle'] = (idle, P_IDLE, True)

    # REVELA: o reiatsu se desfaz e ele aparece com o cabelo e o casaco
    # levantados pelo vento de energia, que cai e assenta (passa um pouco do
    # ponto e volta); os olhos acesos apagam
    # (o tempo do cabelo termina em 0: o 'idle' continua dali sem pulo)
    D_REV = 1.4

    def revela(t):
        tc = degrau(t, FPS_CORPO)
        th = tc - D_REV
        s = 0.95 * math.exp(-tc / 0.32) * math.cos(tc * 7.5) + 0.05 * (1 - math.exp(-tc / 0.3))
        q = dict(REPOUSO)
        q['bob'] = int(round(1.2 * math.sin(2 * math.pi * th / P_IDLE)))
        q['olhos'] = 'l' if tc < 0.75 else 'a'
        return q, th, dict(onda=7.0 + 8.0 * math.exp(-tc / 0.4), per=P_IDLE, sobe=s)
    CL['revela'] = (revela, D_REV, False)

    # CARGA: ergue a espada devagar (antecipacao) e segura tremendo
    ch = [(0.0, dict(REPOUSO), 'in'), (0.2, dict(b=-6.0, a=-4.0, e=-6.0), 'suave'),
          (0.73, CARGA, 'out'), (0.9, dict(CARGA, b=CARGA['b'] + 4))]

    def carga(t):
        tc = degrau(t, FPS_CORPO)
        q = trilha(ch, tc)
        q['bob'] = int(round(q.get('bob', 0)))
        return q, tc, dict(onda=8.0, per=P_IDLE, sobe=0.08, x=-6.0 * min(1.0, tc / 0.7))
    CL['carga'] = (carga, 28 / 30.0, False)

    def carga_segura(t):
        tc = degrau(t, FPS_CORPO)
        q = dict(CARGA, b=CARGA['b'] + 4)
        q['bob'] = CARGA['bob'] + (1 if int(tc * 12 + 1e-6) % 2 else 0)
        q['e'] += 1.5 * math.sin(tc * 2 * math.pi / 0.25)
        # loop de 0,75 s (18 desenhos) = um ciclo inteiro do cabelo (volta sem pulo)
        return q, tc, dict(onda=11.0, per=0.75, sobe=0.12, x=-6.0)
    CL['carga_segura'] = (carga_segura, 0.75, True)

    # CORTE: acelera (rastro) -> passa pela frente -> segue -> acomoda. O
    # cabelo do corte e do 'fim' corre num tempo so, que termina em 0 no fim
    # do 'fim' (o 'idle' continua dali)
    ch2 = [(0.0, dict(CARGA, b=CARGA['b'] + 4), 'in'), (4 / 30., MEIO, 'out'),
           (7 / 30., CORTOU, 'out'), (11 / 30., SEGUE, 'mola'), (17 / 30., dict(SEGUE, b=-92.0), 'suave'),
           (18 / 30., dict(SEGUE, b=-92.0))]
    D_CORTE, D_FIM = 19 / 30.0, 27 / 30.0

    def vento_corte(tc):
        return 14.0 * math.exp(-max(0.0, tc - 0.15) / 0.25)

    def corte(t):
        tc = degrau(t, FPS_CORPO)
        q = trilha(ch2, tc)
        q['bob'] = int(round(q.get('bob', 0)))
        f = int(round(tc * 30))
        if 1 <= f <= 9:
            ant = trilha(ch2, max(0.0, tc - 2 / 30.))
            q['rastro'] = ant['b'] + ant['a'] + ant['e'] - q['b'] - q['a']
        return q, tc - D_CORTE - D_FIM, dict(onda=9.0, per=P_IDLE, sobe=0.1, x=vento_corte(tc))
    CL['corte'] = (corte, D_CORTE, False)

    # FIM: volta devagar ao repouso (o cabelo e o casaco ainda balancando)
    ch3 = [(0.0, dict(SEGUE, b=-92.0), 'suave'), (26 / 30., dict(REPOUSO))]

    def fim(t):
        tc = degrau(t, FPS_CORPO)
        q = trilha(ch3, tc)
        q['bob'] = int(round(q.get('bob', 0)))
        return q, tc - D_FIM, dict(onda=7.0 + 2.0 * math.exp(-tc / 0.3), per=P_IDLE,
                                   sobe=0.05 + 0.05 * math.exp(-tc / 0.3), x=vento_corte(D_CORTE + tc))
    CL['fim'] = (fim, D_FIM, False)
    return CL


def gerar_quadros(nomes=None):
    bon = Boneco()
    saida = {}
    cache = {}
    for nome, (fn, dur, loop) in clipes().items():
        if nomes and nome not in nomes:
            continue
        quadros = []
        n = int(round(dur * FPS_CORPO))
        for f in range(n):
            q, tc, vento = fn(f / float(FPS_CORPO))
            kw = {k: v for k, v in q.items() if k in ('b', 'a', 'e', 'bob', 'olhos', 'cresce_esp', 'rastro')}
            chave = json.dumps([sorted((k, round(v, 3) if isinstance(v, float) else v) for k, v in kw.items()),
                                round(tc, 4), sorted((k, round(v, 4)) for k, v in vento.items())])
            if chave not in cache:
                cache[chave] = bon.quadro(tc, vento, **kw)
            quadros.append(cache[chave])
        saida[nome] = (quadros, loop, FPS_CORPO)
        print(nome, n, 'quadros,', len({id(x) for x in quadros}), 'desenhos')
    # o REIATSU do BAN-KAI (desenhado por cima do boneco, mesma tela e quadril)
    rei_nomes = ('rei_estouro', 'rei_ferve', 'rei_dissipa')
    if not nomes or any(n in rei_nomes for n in nomes):
        from reiatsu import Reiatsu, CORES
        rei = Reiatsu(CW, CH, _c(QUADRIL), len(bon.pal))
        bon.pal.extend(CORES)
        assert len(bon.pal) <= 256
        nada = ((0.0, 0.0), (0.0, 0.0))

        def _em_quadros(imgs):
            """um desenho por quadro (o clipe toca a FPS_REI/s)"""
            return [(img,) + nada for img in imgs]
        saida['rei_estouro'] = (_em_quadros(rei.estouro(por_s=FPS_REI)), False, FPS_REI)
        saida['rei_ferve'] = (_em_quadros(rei.ferve(n=20, por_s=FPS_REI)), True, FPS_REI)
        # a energia sai primeiro de cima do corpo (a forma dele no 1o quadro da revelacao)
        fn_rev = clipes()['revela'][0]
        q0, tc0, v0 = fn_rev(0.0)
        kw0 = {k: v for k, v in q0.items() if k in ('b', 'a', 'e', 'bob', 'olhos')}
        corpo = bon.quadro(tc0, v0, **kw0)[0] > 0
        saida['rei_dissipa'] = (_em_quadros(rei.dissipa(n=32, por_s=FPS_REI, corpo=corpo)), False, FPS_REI)
        saida['rei_pilar'] = (_em_quadros(rei.pilar(n=20, por_s=FPS_REI)), True, FPS_REI)
        rei_nomes = rei_nomes + ('rei_pilar',)
        for n in rei_nomes:
            print(n, len(saida[n][0]), 'quadros')
    return bon, saida


def escrever(bon, saida):
    """app/bankai/clipes.bin: b'BK01' + tamanho do cabecalho + cabecalho json
    (zlib) + cada desenho em zlib (1 byte por pixel = cor da paleta),
    recortado na caixa do que aparece. Quadro repetido aponta para o mesmo
    desenho."""
    blocos = []
    cx, cy, r = CABECA
    corpo = [_c((72, 0))[0], _c((101, 0))[0], _c((0, cy - r - 2))[1], _c((0, 166))[1]]
    oy, ox = np.nonzero(bon.olhos)
    olhos = [round(float(ox.mean()) + 0.5, 1), round(float(oy.mean()) + 0.5, 1)] if len(ox) else None
    cab = {'paleta': bon.pal, 'tela': [CW, CH], 'quadril': list(_c(QUADRIL)), 'fps': FPS,
           'corpo': corpo, 'olhos': olhos, 'clipes': {}}
    pos = 0
    ja = {}
    for nome, (quadros, loop, fps_c) in saida.items():
        lst = []
        for item in quadros:
            img, mao, ponta = item
            if id(item) not in ja:
                ys, xs = np.nonzero(img)
                if len(xs):
                    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
                else:                                   # quadro vazio (fim da dissipacao)
                    x0, y0 = CW // 2, CH // 2
                    x1, y1 = x0 + 1, y0 + 1
                dados = zlib.compress(img[y0:y1, x0:x1].tobytes(), 9)
                blocos.append(dados)
                ja[id(item)] = [pos, len(dados), [x0, y0, x1 - x0, y1 - y0]]
                pos += len(dados)
            p, tam, caixa = ja[id(item)]
            lst.append([p, tam, caixa, [round(mao[0], 1), round(mao[1], 1)],
                        [round(ponta[0], 1), round(ponta[1], 1)]])
        cab['clipes'][nome] = {'loop': loop, 'quadros': lst, 'fps': fps_c}
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


def rgba(pal, idx, fundo=(8, 6, 16)):
    p = np.array(pal, np.uint8)
    r = p[idx]
    f = np.zeros_like(r)
    f[...] = (fundo[0], fundo[1], fundo[2], 255)
    return np.where(r[..., 3:4] > 0, r, f)


def gif(bon, saida, ordem, caminho, z=2):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    x0 = y0 = 10 ** 9
    x1 = y1 = -1
    for nome in ordem:
        for idx, _, _ in saida[nome][0]:
            ys, xs = np.nonzero(idx)
            x0, x1 = min(x0, xs.min()), max(x1, xs.max())
            y0, y1 = min(y0, ys.min()), max(y1, ys.max())
    x0, y0, x1, y1 = x0 - 6, y0 - 6, x1 + 7, y1 + 7
    frames = []
    for nome in ordem:
        for idx, _, _ in saida[nome][0]:
            im = Image.fromarray(rgba(bon.pal, idx)[y0:y1, x0:x1][..., :3]).resize(
                ((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST)
            frames.append(im.quantize(colors=255, method=Image.MEDIANCUT))
    frames[0].save(caminho, save_all=True, append_images=frames[1:], duration=33, loop=0)
    print(caminho, len(frames), 'quadros')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'mechas':
        bon = Boneco()
        cores = np.random.default_rng(1).integers(60, 255, (len(bon.mechas), 3))
        out = np.zeros((CH, CW, 3), np.uint8)
        for i, mc in enumerate(bon.mechas):
            out[mc.ys, mc.xs] = cores[i]
        firme = bon.m['pernas'] | bon.m['tronco'] | bon.m['cabeca']
        out[firme] = (90, 90, 90)
        out[bon.m['braco'] | bon.m['antebraco']] = (200, 200, 200)
        out[bon.m['espada']] = (255, 255, 255)
        ys, xs = np.nonzero(out.sum(axis=2))
        c = out[ys.min() - 3:ys.max() + 4, xs.min() - 3:xs.max() + 4]
        Image.fromarray(c).resize((c.shape[1] * 4, c.shape[0] * 4), Image.NEAREST).save(sys.argv[2])
        print('ok')
    elif cmd in ('gerar', 'gif'):
        nomes = sys.argv[2].split(',') if len(sys.argv) > 2 else None
        bon, saida = gerar_quadros(nomes)
        if cmd == 'gerar':
            escrever(bon, saida)
        ordem = nomes or ['revela', 'idle', 'carga', 'carga_segura', 'carga_segura', 'corte', 'fim', 'idle']
        gif(bon, saida, ordem, os.path.join(SAIDA_TESTE, 'rig.gif'))
