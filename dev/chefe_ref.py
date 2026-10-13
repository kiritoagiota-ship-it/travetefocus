"""O CHEFE copiado do MODELO FINAL do usuario
(referencias/2026-10-13_chefe_modelo_final.png) para pixel art do jogo,
ja cortado em PECAS para o chefe_rig.py animar (mesma ideia do Bankai):

1) separa a figura do fundo (GrabCut guiado por um contorno grosso);
2) reduz as cores a uma paleta curta (k-medias) + a rampa fixa da LAVA
   (as fendas e o fio da espada pulsam: precisam de indices proprios);
3) cada bloco de S px do modelo vira 1 pixel com a cor que mais aparece nele;
4) cada pixel vai para uma PECA (poligonos tracados em cima do modelo; o pano
   vermelho - capa e tabardo - e achado pela cor);
5) o que fica ESCONDIDO atras de outra peca (o peito atras da ombreira, a
   coxa atras do saiote...) e completado, para nao abrir buraco quando as
   pecas se mexem.

Tem a mesma "cara" do chefe_arte.py (CW, CH, CHAO, P, PAL, pontos, montar,
aro, erode...): o chefe_rig.py usa um ou outro.
uso: python dev/chefe_ref.py previa SAIDA.png [zoom]   (montado)
     python dev/chefe_ref.py pecas SAIDA.png           (cada peca de uma cor)
     python dev/chefe_ref.py folha SAIDA.png           (as pecas separadas)"""
import os
import sys
import numpy as np
from PIL import Image

REF = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'referencias',
                   '2026-10-13_chefe_modelo_final.png')
CACHE = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'ferramentas', 'chefe_ref_cache.npz')
S = 3.2                           # px do modelo por pixel do jogo (o chefe fica com ~405 de altura)
CW, CH = 960, 960                 # tela de trabalho (folga para o montante girar por cima da cabeca)
OX, OY = 300, 320                 # onde o canto do modelo cai na tela
CHAO = OY + int(round(1296 / S))  # y do chao


def P(x, y):
    """Ponto do MODELO (px da imagem de referencia) -> tela de trabalho."""
    return (OX + x / S, OY + y / S)


# ── paleta ───────────────────────────────────────────────────────────
PAL = [(0, 0, 0, 0)]


def _cor(*rgb):
    PAL.append((rgb[0], rgb[1], rgb[2], 255))
    return len(PAL) - 1


LINHA = _cor(8, 6, 14)
# lava (fendas, nucleo, fio do montante, olho): do escuro ao miolo quase branco
G0 = _cor(112, 10, 18)
G1 = _cor(188, 22, 22)
G2 = _cor(255, 56, 34)
G3 = _cor(255, 138, 66)
G4 = _cor(255, 228, 176)
# rastro dos golpes
R0 = _cor(132, 12, 20)
R1 = _cor(232, 40, 30)
R2 = _cor(255, 196, 140)
ARO = _cor(150, 20, 26)           # luz de brasa na borda de fora
FECHO = _cor(12, 9, 18)           # buraquinhos fechados
C0 = _cor(52, 6, 14)              # miolo escuro do pano (aparece entre as tiras)
N_FIXAS = len(PAL)
K_CORES = 150                     # cores tiradas do modelo

# ── as pecas: poligonos em px do MODELO ──────────────────────────────
# 'vis' = onde a peca APARECE (bordas certas so onde ela fica na frente de outra);
# 'oculto' = por onde ela continua escondida atras das pecas da frente.
ORDEM = ['capa', 'espada', 'braco_tras', 'antebraco_tras', 'ombreira_tras', 'coxa_tras', 'canela_tras',
         'coxa_frente', 'canela_frente', 'tabardo', 'tronco', 'saiote', 'cabeca', 'braco', 'antebraco',
         'ombreira']
PANO = ('capa', 'tabardo')
VIS = {
    'espada': [[(118, 240), (205, 240), (202, 330), (184, 348), (180, 404), (146, 404), (138, 342), (118, 322)],
               [(10, 520), (96, 508), (150, 516), (258, 542), (252, 602), (222, 622), (232, 800), (222, 1000),
                (196, 1100), (172, 1200), (136, 1312), (40, 1312), (0, 1200), (0, 640)]],
    'braco_tras': [[(296, 432), (350, 436), (362, 520), (345, 600), (292, 650), (268, 604), (300, 520)]],
    'antebraco_tras': [[(78, 396), (150, 398), (184, 402), (208, 414), (218, 446), (300, 452), (300, 520),
                        (268, 600), (232, 562), (206, 522), (150, 514), (78, 510)]],
    'ombreira_tras': [[(222, 205), (246, 210), (300, 288), (338, 284), (352, 300), (362, 350), (352, 400),
                       (358, 444), (300, 450), (214, 444), (198, 400), (204, 330), (240, 292)]],
    # as pernas dobram no joelho: coxa (quase toda atras do saiote) e canela (joelheira + bota)
    'coxa_tras': [[(300, 640), (470, 640), (470, 868), (330, 860), (290, 800)]],
    'canela_tras': [[(250, 800), (292, 800), (330, 862), (470, 870), (470, 1000), (456, 1100), (424, 1200),
                     (432, 1312), (138, 1312), (172, 1200), (238, 1150), (292, 1000), (252, 900)]],
    'coxa_frente': [[(600, 640), (790, 640), (800, 858), (640, 858), (620, 800)]],
    'canela_frente': [[(636, 860), (800, 860), (792, 990), (832, 1130), (900, 1260), (905, 1312),
                       (628, 1312), (640, 1180), (636, 1000), (622, 890)]],
    'tabardo': [[(455, 655), (628, 655), (642, 850), (664, 1000), (650, 1066), (450, 1066), (444, 900),
                 (460, 800)]],
    'tronco': [[(362, 350), (350, 400), (358, 470), (385, 502), (412, 522), (402, 598), (395, 625), (442, 615),
                (446, 636), (620, 634), (626, 598), (722, 605), (742, 560), (732, 400), (702, 300), (640, 240),
                (540, 220), (450, 260), (345, 300)]],
    'saiote': [[(392, 626), (360, 700), (316, 790), (314, 816), (392, 866), (456, 832), (468, 700), (462, 662),
                (495, 662), (505, 700), (522, 720), (540, 700), (558, 662), (598, 658), (612, 832),
                (712, 864), (780, 800), (772, 740), (736, 655), (722, 603), (626, 596), (620, 632),
                (446, 634), (442, 612)]],
    'cabeca': [[(225, 0), (670, 0), (670, 120), (650, 165), (610, 200), (565, 232), (558, 262), (522, 288),
                (468, 288), (455, 346), (348, 336), (335, 262), (322, 245), (262, 210), (225, 150)]],
    'braco': [[(672, 372), (700, 384), (780, 412), (895, 406), (950, 370), (962, 460), (935, 508),
               (870, 530), (800, 546), (700, 480)]],
    'antebraco': [[(800, 548), (870, 530), (935, 510), (960, 530), (1018, 512), (1016, 742), (946, 762),
                   (962, 790), (968, 962), (905, 990), (832, 982), (800, 962), (762, 940), (770, 905),
                   (748, 880), (732, 862), (745, 800), (790, 770), (808, 735), (805, 640)]],
    'ombreira': [[(620, 240), (660, 215), (682, 138), (702, 213), (760, 205), (836, 82), (876, 210),
                  (936, 236), (1018, 212), (962, 330), (952, 372), (895, 406), (780, 412), (700, 384),
                  (640, 352), (622, 295)]],
}
OCULTO = {
    'capa': [[(300, 330), (960, 330), (1180, 600), (1180, 1296), (640, 1296), (610, 1160), (500, 1160),
              (460, 1296), (250, 1296), (200, 700)]],
    'espada': [[(138, 330), (188, 330), (190, 560), (118, 560)]],
    'braco_tras': [[(296, 380), (360, 380), (372, 520), (350, 610), (292, 650), (268, 604), (300, 520)]],
    'antebraco_tras': [[(140, 400), (300, 430), (310, 530), (268, 600), (150, 520)]],
    'ombreira_tras': [[(240, 292), (370, 292), (372, 450), (214, 446)]],
    'coxa_tras': [[(318, 620), (476, 620), (476, 930), (300, 930)]],
    'canela_tras': [[(300, 820), (470, 820), (470, 900), (300, 900)]],
    'coxa_frente': [[(596, 620), (800, 620), (806, 930), (620, 930)]],
    'canela_frente': [[(630, 820), (800, 820), (800, 900), (630, 900)]],
    'tabardo': [[(455, 640), (628, 640), (640, 860), (455, 860)]],
    'tronco': [[(345, 290), (760, 240), (800, 420), (745, 640), (395, 650), (350, 480)]],
    'saiote': [[(392, 600), (740, 596), (780, 800), (712, 864), (392, 866), (314, 810)]],
    'cabeca': [[(340, 230), (560, 230), (560, 350), (345, 350)]],
    'braco': [[(700, 300), (900, 290), (962, 400), (950, 560), (800, 590), (700, 480)]],
    'antebraco': [[(800, 500), (960, 490), (1000, 600), (800, 640)]],
}
# juntas e pontos (px do modelo)
PT = dict(QUADRIL=(540, 640), PEITO=(535, 430), PESCOCO=(470, 300), CABECA=(450, 200),
          OMBRO=(800, 345), COTOVELO=(872, 548), MAO=(858, 790),
          OMBRO_T=(318, 392), COTOVELO_T=(300, 506), MAO_T=(150, 456),
          PONTA=(100, 1288), NUCLEO=(538, 440), OLHO=(402, 244), GUARDA=(150, 545), GARRA=(850, 940),
          PES=(520, 1296),
          ANCA_T=(400, 700), JOELHO_T=(350, 905), TORNOZELO_T=(300, 1170),
          ANCA_F=(690, 700), JOELHO_F=(712, 915), TORNOZELO_F=(742, 1175))
# contorno grosso da figura (para o recorte) e os buracos de fundo dentro dele
FORA = [(160, 255), (120, 300), (140, 360), (80, 400), (78, 505), (20, 545), (30, 620), (5, 900), (15, 1120),
        (55, 1260), (95, 1300), (300, 1312), (480, 1312), (500, 1230), (560, 1120), (610, 1180), (630, 1312),
        (900, 1312), (930, 1250), (1010, 1262), (1150, 1280), (1180, 1150), (1180, 590), (1020, 515),
        (950, 440), (960, 330), (1010, 220), (930, 240), (870, 215), (840, 90), (770, 200), (720, 205),
        (690, 150), (670, 215), (620, 240), (585, 195), (640, 160), (668, 90), (640, 20), (598, 0),
        (590, 20), (618, 60), (610, 120), (560, 150), (520, 150), (500, 105), (450, 88), (400, 150),
        (370, 190), (320, 190), (275, 140), (270, 80), (305, 15), (290, 8), (245, 60), (235, 130),
        (265, 195), (330, 232), (335, 280), (300, 290), (230, 215), (245, 290), (205, 330), (190, 395),
        (175, 320), (195, 300)]
BURACOS = [
    [(215, 600), (290, 640), (330, 800), (270, 830), (300, 900), (290, 1000), (300, 1110), (255, 1180),
     (170, 1240), (215, 1000), (210, 800)],
    [(505, 1120), (560, 1090), (625, 1130), (640, 1230), (628, 1300), (490, 1300), (470, 1210)],
    [(252, 215), (330, 240), (332, 282), (302, 286)],
]
Y_CHAO_MODELO = 1296              # abaixo disto e chao (pedras), nao e o chefe


def _poli(pts, shape):
    import cv2
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
    return m > 0


def _polis(lista, shape):
    m = np.zeros(shape, bool)
    for p in lista:
        m |= _poli(p, shape)
    return m


def _recorte(bgr):
    """Mascara da figura no modelo (True = chefe)."""
    import cv2
    h, w = bgr.shape[:2]
    fora = _poli(FORA, (h, w)).astype(np.uint8)
    k = lambda n: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (n, n))
    mask = np.full((h, w), cv2.GC_BGD, np.uint8)
    mask[cv2.dilate(fora, k(41)) > 0] = cv2.GC_PR_BGD
    mask[fora > 0] = cv2.GC_PR_FGD
    mask[cv2.erode(fora, k(61)) > 0] = cv2.GC_FGD
    for b in BURACOS:
        mb = _poli(b, (h, w)).astype(np.uint8)
        mask[mb > 0] = cv2.GC_PR_BGD
        mask[cv2.erode(mb, k(25)) > 0] = cv2.GC_BGD
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(bgr, mask, None, bg, fg, 8, cv2.GC_INIT_WITH_MASK)
    m = ((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD))
    m[Y_CHAO_MODELO:, :] = False
    # so o pedaco grande (tira ilhas de fundo)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
    if n > 2:
        maior = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        m = (lab == maior) | ((lab > 0) & (st[lab, cv2.CC_STAT_AREA] > 1500))
    return m


def _kmedias(px, k, iters=16, semente=3):
    rnd = np.random.default_rng(semente)
    am = px[rnd.choice(len(px), min(len(px), 60000), replace=False)].astype(float)
    ordem = np.argsort(am.sum(axis=1))
    c = am[ordem[np.linspace(0, len(ordem) - 1, k).astype(int)]].copy()
    for _ in range(iters):
        lab = np.empty(len(am), int)
        for i in range(0, len(am), 8000):
            d = ((am[i:i + 8000, None, :] - c[None, :, :]) ** 2).sum(axis=2)
            lab[i:i + 8000] = d.argmin(axis=1)
        for i in range(k):
            sel = am[lab == i]
            if len(sel):
                c[i] = sel.mean(axis=0)
    return c


def _mais_perto(rgb, cores):
    """Indice da cor mais perto para cada pixel de rgb (N, 3)."""
    out = np.empty(len(rgb), int)
    for i in range(0, len(rgb), 20000):
        d = ((rgb[i:i + 20000, None, :].astype(float) - cores[None, :, :]) ** 2).sum(axis=2)
        out[i:i + 20000] = d.argmin(axis=1)
    return out


def _moda_blocos(idx, h, w, n_classes, pesos=None):
    """Cada bloco de S px vira o valor que mais aparece nele."""
    out = np.zeros((h, w), int)
    for y in range(h):
        y0, y1 = int(y * S), max(int(y * S) + 1, int((y + 1) * S))
        for x in range(w):
            bl = idx[y0:y1, int(x * S):max(int(x * S) + 1, int((x + 1) * S))].ravel()
            c = np.bincount(bl, minlength=n_classes).astype(float)
            if pesos is not None:
                c = c * pesos
            out[y, x] = int(c.argmax())
    return out


class Peca:
    """Uma peca: imagem (indices da paleta) do tamanho da tela de trabalho."""

    def __init__(self, nome):
        self.nome = nome
        self.img = np.zeros((CH, CW), np.uint8)
        self.pts = {}

    @property
    def masc(self):
        return self.img > 0


def erode(m, n=1):
    import cv2
    return cv2.erode(m.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=n) > 0


def dilata(m, n=1):
    import cv2
    return cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=n) > 0


def _construir():
    import cv2
    bgr = cv2.imread(REF)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(int)
    Hm, Wm = rgb.shape[:2]
    fig = _recorte(bgr)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # pano vermelho: vermelho dominante em AREA grande (as fendas de lava sao finas e somem na abertura)
    # lava: vermelho/laranja bem aceso
    lava = (r > 170) & (r - b > 110) & ((g > 40) | (r > 215))
    ouro = (r > 120) & (g > 70) & (b < g) & (r - b > 50)
    # pano: avermelhado (claro ou escuro: a capa tem sombras quase pretas, mas
    # sempre puxando para o vermelho; a armadura escura puxa para o azul) em
    # AREA grande - as fendas de lava da armadura sao finas e somem na abertura
    verm = (r > b + 3) & (g < r * 0.5) & ~lava & ~ouro
    el = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    pano = cv2.morphologyEx(verm.astype(np.uint8), cv2.MORPH_OPEN, el) > 0
    pano = cv2.dilate(pano.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0
    pano &= verm

    def _fecha(m, lim):
        """Fecha frestas e buracos de uma peca de armadura (as fendas de
        lava e o brilho vermelho em volta delas sao da peca, nao da capa)."""
        f = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE,
                             cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
        cheio = f.copy()
        cont, _ = cv2.findContours(f, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        for c in cont:
            if cv2.contourArea(c) < 2600:                 # buraco pequeno: fecha
                cv2.drawContours(cheio, [c], -1, 1, -1)
        return (cheio > 0) & lim
    # dono de cada pixel do modelo
    dono = np.zeros((Hm, Wm), np.uint8)                     # 0 = fundo; i+1 = ORDEM[i]
    for i, nome in enumerate(ORDEM):
        if nome == 'capa':
            continue
        m = _polis(VIS[nome], (Hm, Wm)) & fig
        if nome == 'tabardo':
            m &= (pano | verm | ouro | lava)
        elif nome != 'espada':
            lim = m
            m = _fecha(m & ~pano, lim)                      # armadura nunca leva o pano da capa
        dono[m] = i + 1
    resto = fig & (dono == 0)
    # o resto: pano -> capa; armadura sem dono -> a peca mais perto
    capa_i = ORDEM.index('capa') + 1
    dono[resto & (pano | verm)] = capa_i
    falta = fig & (dono == 0)
    if falta.any():
        _, ids = cv2.distanceTransformWithLabels((dono == 0).astype(np.uint8), cv2.DIST_L2, 5,
                                                 labelType=cv2.DIST_LABEL_PIXEL)
        ys, xs = np.nonzero(dono > 0)
        # rotulo -> dono do pixel-semente
        mapa = np.zeros(ids.max() + 1, np.uint8)
        mapa[ids[ys, xs]] = dono[ys, xs]
        perto = mapa[ids]
        longe = cv2.distanceTransform((dono == 0).astype(np.uint8), cv2.DIST_L2, 5) > 26
        dono[falta & ~longe] = perto[falta & ~longe]
        dono[falta & longe] = capa_i
    # cores
    cores_m = _kmedias(rgb[fig & ~lava].reshape(-1, 3), K_CORES)
    fixas = np.array([c[:3] for c in PAL[1:N_FIXAS]], float)
    ramp = np.array([PAL[i][:3] for i in (G0, G1, G2, G3, G4)], float)
    idx = np.zeros((Hm, Wm), int)
    ys, xs = np.nonzero(fig & ~lava)
    idx[ys, xs] = N_FIXAS + _mais_perto(rgb[ys, xs], cores_m)
    ys, xs = np.nonzero(fig & lava)
    idx[ys, xs] = np.array([G0, G1, G2, G3, G4])[_mais_perto(rgb[ys, xs], ramp)]
    h, w = int(Hm / S), int(Wm / S)
    n_pal = N_FIXAS + K_CORES
    pesos = np.ones(n_pal)
    pesos[0] = 1.15                                        # na duvida a borda fica limpa
    for gi, pv in ((G2, 1.5), (G3, 1.9), (G4, 2.3), (G1, 1.15)):   # as fendas sao finas: nao podem sumir
        pesos[gi] = pv
    nat = _moda_blocos(idx, h, w, n_pal, pesos)
    dono_n = _moda_blocos(np.where(idx > 0, dono, 0), h, w, len(ORDEM) + 1)
    # pixel pintado sem dono (ou o contrario): acerta pelo vizinho
    sem = (nat > 0) & (dono_n == 0)
    if sem.any():
        _, ids = cv2.distanceTransformWithLabels((dono_n == 0).astype(np.uint8), cv2.DIST_L2, 3,
                                                 labelType=cv2.DIST_LABEL_PIXEL)
        ys, xs = np.nonzero(dono_n > 0)
        mapa = np.zeros(ids.max() + 1, np.uint8)
        mapa[ids[ys, xs]] = dono_n[ys, xs]
        dono_n[sem] = mapa[ids][sem]
    dono_n[nat == 0] = 0
    # partes escondidas: dentro do poligono 'oculto' (ou 'vis') da peca, onde hoje manda uma peca da FRENTE
    pal_rgb = np.array([c[:3] for c in PAL[:N_FIXAS]] + [tuple(int(round(v)) for v in c) for c in cores_m], float)
    img_rgb = pal_rgb[nat].astype(np.uint8)
    escond = {}
    sy, sx = np.mgrid[0:h, 0:w]
    for i, nome in enumerate(ORDEM):
        if nome not in OCULTO:
            continue
        pol = np.zeros((h, w), np.uint8)
        for p in OCULTO[nome] + VIS.get(nome, []):
            cv2.fillPoly(pol, [np.array([(x / S, y / S) for x, y in p], np.float32).round().astype(np.int32)], 1)
        meu = dono_n == i + 1
        frente = dono_n > i + 1
        falta = (pol > 0) & frente
        if not falta.any() or not meu.any():
            continue
        # completa copiando de dentro da propria peca (sem lava: escondido fica apagado)
        fonte = img_rgb.copy()
        fonte[~meu] = 0
        furo = (~meu).astype(np.uint8)
        cheio = cv2.inpaint(fonte, furo, 5, cv2.INPAINT_TELEA)
        cand = np.arange(N_FIXAS, n_pal)
        ys, xs = np.nonzero(falta)
        if nome == 'capa':
            escuro = (cheio[ys, xs].astype(float) * 0.82)
            ci = cand[_mais_perto(escuro, pal_rgb[cand])]
        else:
            # armadura escondida: chapa escura lisa com um xadrez de 2 tons (limpo, sem borrao)
            dois = cand[_mais_perto(np.array([(22.0, 19.0, 34.0), (34.0, 30.0, 50.0)]), pal_rgb[cand])]
            ci = np.where(((xs // 3 + ys // 3) % 2) == 0, dois[0], dois[1])
        e = np.zeros((h, w), int)
        e[ys, xs] = ci
        escond[nome] = e
    return dict(nat=nat, dono=dono_n, cores=cores_m, escond=escond, fig_frac=float(fig.mean()))


_DADOS = [None]


def dados(refazer=False):
    if _DADOS[0] is not None and not refazer:
        return _DADOS[0]
    if os.path.exists(CACHE) and not refazer:
        z = np.load(CACHE, allow_pickle=True)
        d = dict(nat=z['nat'], dono=z['dono'], cores=z['cores'], escond=z['escond'].item())
    else:
        d = _construir()
        np.savez_compressed(CACHE, nat=d['nat'], dono=d['dono'], cores=d['cores'],
                            escond=np.array(d['escond'], dtype=object))
    if len(PAL) == N_FIXAS:
        for c in d['cores']:
            _cor(*[int(round(v)) for v in c])
    _DADOS[0] = d
    return d


def montar():
    """{nome: Peca}: cada peca na pose do modelo, ja com a parte escondida."""
    d = dados()
    nat, dono = d['nat'], d['dono']
    h, w = nat.shape
    pcs = {}
    for i, nome in enumerate(ORDEM):
        pc = Peca(nome)
        m = dono == i + 1
        sub = np.where(m, nat, 0)
        e = d['escond'].get(nome)
        if e is not None:
            sub = np.where((sub == 0) & (e > 0), e, sub)
        pc.img[OY:OY + h, OX:OX + w] = sub.astype(np.uint8)
        pcs[nome] = pc
    return pcs


def aro(img):
    """Fecha buraquinhos (o modelo ja tem o seu proprio contorno)."""
    cheio = img > 0
    solido = erode(dilata(cheio, 1), 1)
    out = img.copy()
    out[solido & ~cheio] = FECHO
    return out


def compor(pecas, ordem=ORDEM):
    img = np.zeros((CH, CW), np.uint8)
    for n in ordem:
        m = pecas[n].masc
        img[m] = pecas[n].img[m]
    return aro(img)


def rgba(idx, fundo=(6, 6, 12)):
    p = np.array(PAL, np.uint8)
    r = p[idx]
    f = np.zeros_like(r)
    f[...] = (fundo[0], fundo[1], fundo[2], 255)
    return np.where(r[..., 3:4] > 0, r, f)


def salvar(arr_rgb, caminho, zoom=2):
    im = Image.fromarray(arr_rgb)
    if zoom != 1:
        im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    im.save(caminho)
    print(caminho, im.size)


def _caixa(idx, folga=6):
    ys, xs = np.nonzero(idx)
    return max(0, xs.min() - folga), max(0, ys.min() - folga), xs.max() + folga + 1, ys.max() + folga + 1


for _n, _p in PT.items():
    globals()[_n] = _p


def _u_lamina():
    """(direcao, normal, comprimento) da lamina, da guarda ate a ponta (tela de trabalho)."""
    a, b = np.array(P(*PT['GUARDA'])), np.array(P(*PT['PONTA']))
    v = b - a
    L = float(np.hypot(*v))
    u = v / L
    return u, np.array([-u[1], u[0]]), L


if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'previa'
    saida = sys.argv[2] if len(sys.argv) > 2 else 'chefe_ref.png'
    zoom = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    dados(refazer='refazer' in sys.argv)
    pcs = montar()
    if modo == 'previa':
        img = compor(pcs)
        x0, y0, x1, y1 = _caixa(img)
        salvar(rgba(img)[y0:y1, x0:x1, :3], saida, zoom)
    elif modo == 'pecas':
        rnd = np.random.default_rng(2)
        cores = rnd.integers(60, 255, (len(ORDEM), 3))
        out = np.zeros((CH, CW, 3), np.uint8)
        out[...] = (6, 6, 12)
        d = dados()
        h, w = d['dono'].shape
        for i, n in enumerate(ORDEM):
            m = np.zeros((CH, CW), bool)
            m[OY:OY + h, OX:OX + w] = d['dono'] == i + 1
            lum = rgba(pcs[n].img)[..., :3].mean(axis=2, keepdims=True) / 255.0
            out[m] = (cores[i] * (0.35 + 0.65 * lum[m])).astype(np.uint8)
        x0, y0, x1, y1 = _caixa(compor(pcs))
        salvar(out[y0:y1, x0:x1], saida, zoom)
        print({n: [int(c) for c in cores[i]] for i, n in enumerate(ORDEM)})
    elif modo == 'folha':
        tiles = []
        for n in ORDEM:
            if not pcs[n].masc.any():
                continue
            x0, y0, x1, y1 = _caixa(pcs[n].img, 3)
            tiles.append(rgba(pcs[n].img, (30, 34, 60))[y0:y1, x0:x1, :3])
        Hm = max(t.shape[0] for t in tiles)
        Wt = sum(t.shape[1] for t in tiles) + 4 * len(tiles)
        out = np.zeros((Hm, Wt, 3), np.uint8)
        x = 0
        for t in tiles:
            out[:t.shape[0], x:x + t.shape[1]] = t
            x += t.shape[1] + 4
        salvar(out, saida, 1)
