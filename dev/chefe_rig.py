"""O CHEFE em PECAS: as pecas recortadas do MODELO FINAL do usuario
(chefe_ref.py) viram um boneco articulado.

As poses e os movimentos ficam em app/chefe_poses.py (o app monta as pecas
NA HORA com essas contas - chefe.py). Aqui:
  exportar   grava app/chefe/rig.bin: a paleta, cada PECA (indices, recortada)
             e a CAPA e o TABARDO ja balancando (alguns desenhos de cada
             jeito de vento: calmo, vento, alto) - o pano e cortado em TIRAS
             e cada pixel so anda em passos inteiros;
  gif/folha  previas feitas com as MESMAS contas do app (para conferir no PC).
(O chefe_arte.py e o chefe antigo, desenhado sem referencia: so historico.
Antes cada desenho do chefe ia pronto para o app: com o chefe novo, maior,
isso dava 22 MB; em pecas da ~1 MB e cabe qualquer movimento novo.)

uso: python dev/chefe_rig.py exportar
     python dev/chefe_rig.py gif [clipes] SAIDA.gif
     python dev/chefe_rig.py folha CLIPE SAIDA.png"""
import os
import sys
import json
import zlib
import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.dirname(AQUI))
import chefe_ref as A                                                   # noqa: E402
import chefe_poses as CP                                                # noqa: E402
from bankai_rig import desenha_peca, Mecha, _reamostra, _dist_seg       # noqa: E402

APP = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
SAIDA_TESTE = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'ferramentas', 'saida_testes', 'chefe')
FPS = 30
CW, CH = A.CW, A.CH
P = A.P
P_IDLE = CP.P_IDLE
PTS = {n: P(*v) for n, v in A.PT.items()}        # os pontos do boneco na tela de trabalho

# tiras da capa (da raiz, nos ombros, ate a barra) e do tabardo - em px do MODELO
TIRAS_CAPA = [
    [(330, 400), (285, 700), (262, 1000), (245, 1260)],
    [(480, 400), (470, 750), (485, 1000), (525, 1160)],
    [(700, 420), (760, 760), (800, 1050), (830, 1280)],
    [(880, 430), (930, 700), (962, 1000), (985, 1280)],
    [(950, 440), (1040, 650), (1082, 950), (1092, 1280)],
    [(985, 470), (1120, 600), (1160, 900), (1172, 1280)],
]
TIRAS_TAB = [
    [(490, 660), (480, 860), (470, 1045)],
    [(540, 660), (540, 880), (545, 1062)],
    [(600, 660), (612, 860), (642, 1045)],
]
RAIZ_CAPA, RAIZ_TAB = (700, 420), (540, 660)
# jeitos de vento do pano: (vento, quantos desenhos, desenhos por segundo)
VENTOS = {
    'calmo': (dict(onda=5.0, per=2.4, sobe=0.0, x=0.0), 24, 10),
    'vento': (dict(onda=10.0, per=0.8, sobe=0.04, x=-10.0), 12, 15),
    'alto': (dict(onda=9.0, per=0.8, sobe=0.26, x=-4.0), 12, 15),
}
G = [A.G0, A.G1, A.G2, A.G3, A.G4]


def _np(m):
    return np.array([[m[0], m[1], m[2]], [m[3], m[4], m[5]], [0, 0, 1.0]])


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
        self.miolo_capa = A.erode(self.pc['capa'].masc, 3)
        self.miolo_tab = A.erode(self.pc['tabardo'].masc, 2)
        self.lut = []
        for nivel in (0, 1, 2):
            t = np.arange(256, dtype=np.uint8)
            if nivel == 0:
                t[G[4]], t[G[3]], t[G[2]], t[G[1]] = G[3], G[2], G[1], G[0]
            elif nivel == 2:
                t[G[1]], t[G[2]], t[G[3]] = G[2], G[3], G[4]
            self.lut.append(t)
        self._panos = {}

    def pano(self, qual, modo, i):
        """O desenho i da capa/tabardo no jeito de vento `modo` (parado no lugar)."""
        ch = (qual, modo, i)
        if ch not in self._panos:
            vento, n, por_s = VENTOS[modo]
            t = i / float(por_s)
            img = np.zeros((CH, CW), np.uint8)
            miolo, lista = (self.miolo_capa, self.capa) if qual == 'capa' else (self.miolo_tab, self.tab)
            img[miolo] = A.C0
            for mc in lista:
                if len(mc.ys) == 0:
                    continue
                ddx, ddy = mc.deslocamento(t, vento)
                yy, xx = mc.ys + ddy, mc.xs + ddx
                ok = (yy >= 0) & (yy < CH) & (xx >= 0) & (xx < CW)
                img[yy[ok], xx[ok]] = mc.cores[ok]
            self._panos[ch] = img
        return self._panos[ch]

    def quadro(self, q, tc, vento):
        """Previa de uma pose, com as mesmas contas do app -> (indices, garra, ponta)."""
        M, pontos = CP.matrizes(q, PTS)
        modo = CP.modo_capa(vento)
        _v, n, por_s = VENTOS[modo]
        i = int(tc * por_s) % n
        img = np.zeros((CH, CW), np.int32)
        for nome in A.ORDEM:
            if nome == 'capa':
                f = self.pano('capa', modo, i)
            elif nome == 'tabardo':
                mt = 'calmo' if modo == 'calmo' else 'vento'
                f = self.pano('tabardo', mt, int(tc * VENTOS[mt][2]) % VENTOS[mt][1])
            else:
                f = self.pc[nome].img
            m = M[nome]
            if abs(m[1]) < 1e-9 and abs(m[3]) < 1e-9:           # so desloca: passos inteiros
                m = (1.0, 0.0, round(m[2]), 0.0, 1.0, round(m[5]))
            desenha_peca(img, f, f > 0, _np(m))
        if not q.get('ar'):
            img[int(PTS['PES'][1]) + 3:, :] = 0
        img = A.aro(img.astype(np.uint8))
        nivel = int(q.get('brilho', 1))
        if nivel != 1:
            img = self.lut[nivel][img]
        return img.astype(np.uint8), pontos['garra'], pontos['ponta']


def gerar_quadros(nomes=None):
    che = Chefe()
    saida = {}
    for nome, (fn, dur, loop) in CP.clipes().items():
        if nomes and nome not in nomes:
            continue
        quadros = []
        cache = {}
        n = int(round(dur * FPS))
        for f in range(n):
            q, tc, vento = fn(f / float(FPS))
            chave = json.dumps([sorted((k, (round(v, 2) if isinstance(v, float) else v)) for k, v in q.items()
                                       if not isinstance(v, tuple)), round(tc % P_IDLE, 4), CP.modo_capa(vento)])
            if chave not in cache:
                cache[chave] = che.quadro(q, tc, vento)
            quadros.append(cache[chave])
        saida[nome] = (quadros, loop)
        print(nome, n, 'quadros,', len({id(x) for x in quadros}), 'desenhos')
    return che, saida


def exportar():
    """app/chefe/rig.bin: b'CR01' + tamanho + cabecalho json (zlib) + os desenhos (zlib cada)."""
    che = Chefe()
    blocos = []
    pos = [0]

    def guarda(img):
        ys, xs = np.nonzero(img)
        x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
        dados = zlib.compress(img[y0:y1, x0:x1].tobytes(), 9)
        blocos.append(dados)
        item = [pos[0], len(dados), [x0, y0, x1 - x0, y1 - y0]]
        pos[0] += len(dados)
        return item

    cab = {'paleta': che.pal, 'tela': [CW, CH], 'pes': list(PTS['PES']), 'pontos': {k: list(v) for k, v in PTS.items()},
           'ordem': list(A.ORDEM), 'lava': G, 'fecho': A.FECHO,
           'corpo': [P(350, 0)[0], P(800, 0)[0], P(0, 90)[1], PTS['PES'][1]],
           'raiz_capa': list(P(*RAIZ_CAPA)), 'raiz_tab': list(P(*RAIZ_TAB)),
           'pecas': {}, 'panos': {'capa': {}, 'tabardo': {}}}
    for nome in A.ORDEM:
        if nome in ('capa', 'tabardo'):
            continue
        cab['pecas'][nome] = guarda(che.pc[nome].img)
    for qual in ('capa', 'tabardo'):
        for modo, (_v, n, por_s) in VENTOS.items():
            if qual == 'tabardo' and modo == 'alto':
                continue
            cab['panos'][qual][modo] = {'por_s': por_s, 'quadros': [guarda(che.pano(qual, modo, i)) for i in range(n)]}
    cz = zlib.compress(json.dumps(cab).encode('utf-8'), 9)
    os.makedirs(os.path.join(APP, 'chefe'), exist_ok=True)
    caminho = os.path.join(APP, 'chefe', 'rig.bin')
    with open(caminho, 'wb') as fp:
        fp.write(b'CR01')
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
    return max(0, x0 - 6), max(0, y0 - 6), min(CW, x1 + 7), min(CH, y1 + 7)


def gif(saida, ordem, caminho, z=1, pula=2, larg=None, cores=72):
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    x0, y0, x1, y1 = _caixa(saida, ordem)
    frames = []
    for nome in ordem:
        for idx, _, _ in saida[nome][0][::pula]:
            im = Image.fromarray(A.rgba(idx, (4, 4, 9))[y0:y1, x0:x1][..., :3])
            if larg:
                im = im.resize((larg, int(im.height * larg / im.width)), Image.LANCZOS)
            elif z != 1:
                im = im.resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST)
            frames.append(im.quantize(colors=cores, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    frames[0].save(caminho, save_all=True, append_images=frames[1:], duration=33 * pula, loop=0, optimize=True)
    print(caminho, frames[0].size, len(frames), 'quadros', os.path.getsize(caminho) // 1024, 'KB')


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
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    S.save(caminho)
    print(caminho, S.size, len(unicos), 'desenhos')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'exportar':
        exportar()
    elif cmd == 'folha':
        che, saida = gerar_quadros([sys.argv[2]])
        folha(saida, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else os.path.join(SAIDA_TESTE, sys.argv[2] + '.png'))
    else:
        nomes = sys.argv[2].split(',') if len(sys.argv) > 2 and sys.argv[2] not in ('', 'todos') else None
        che, saida = gerar_quadros(nomes)
        gif(saida, nomes or list(saida), sys.argv[3] if len(sys.argv) > 3 else os.path.join(SAIDA_TESTE, 'chefe.gif'))
