"""REIATSU do BAN-KAI (como a Bankai do Ichigo): a energia roxa (miolo
branco) explode dele, cobre o corpo inteiro fervendo e depois se desfaz em
fiapos que sobem, revelando o Bankai.

Pixel art quadro a quadro, gerado aqui no PC (vai junto no clipes.bin):
  rei_estouro  - 6 desenhos: raios, onda de choque no chao, o casulo cresce
                 muito claro e assenta;
  rei_ferve    - 8 desenhos em loop (12/s): linguas de fogo subindo, borda
                 fervendo, faiscas;
  rei_dissipa  - 12 desenhos: o casulo quebra de baixo para cima em pedacos
                 que sobem, escurecem e somem.
O campo de energia e: formato de chama (gota apontando para cima) + ruido
esticado na vertical que SOBE com o tempo (repete certinho no loop); as
faixas de cor sao cortes desse campo (sem degrade liso) e cada faixa perde
os pixels soltos."""
import math
import numpy as np

# cores do reiatsu (de fora para dentro)
CORES = [
    (30, 10, 70, 255),        # contorno
    (70, 26, 160, 255),       # roxo escuro
    (112, 50, 230, 255),      # roxo
    (160, 104, 255, 255),     # violeta
    (208, 170, 255, 255),     # lilas
    (248, 240, 255, 255),     # miolo branco
]
LIMIARES = [0.02, 0.15, 0.31, 0.47, 0.63]     # campo -> faixa 1..5


class Ruido:
    """Ruido de valor com repeticao em y (periodo `py` texels) - o fogo sobe
    e o loop fecha sem emenda."""

    def __init__(self, semente, cx, cy, py, w, h):
        rnd = np.random.default_rng(semente)
        self.cx, self.cy = cx, cy                 # tamanho da celula
        self.ny = int(round(py / cy))
        self.nx = int(math.ceil(w / cx)) + 3
        self.g = rnd.random((self.ny, self.nx))

    def __call__(self, x, y):
        gx = x / self.cx
        gy = y / self.cy
        x0 = np.floor(gx).astype(int)
        y0 = np.floor(gy).astype(int)
        fx = gx - x0
        fy = gy - y0
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        xa = np.clip(x0, 0, self.nx - 1)
        xb = np.clip(x0 + 1, 0, self.nx - 1)
        ya = y0 % self.ny
        yb = (y0 + 1) % self.ny
        g = self.g
        a = g[ya, xa] * (1 - fx) + g[ya, xb] * fx
        b = g[yb, xa] * (1 - fx) + g[yb, xb] * fx
        return a * (1 - fy) + b * fy


def _limpa(faixa, passes=2):
    """Tira pixel solto: pixel sem nenhum vizinho (4) da mesma faixa vira a
    faixa mais comum em volta."""
    f = faixa.copy()
    for _ in range(passes):
        igual = np.zeros(f.shape, int)
        vizs = []
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            s = np.roll(np.roll(f, dy, 0), dx, 1)
            vizs.append(s)
            igual += (s == f)
        solto = (igual == 0) & (f > 0)
        if not solto.any():
            break
        pilha = np.stack(vizs, axis=0)
        # a faixa vizinha mais alta entre as menores diferencas: usa a mediana
        med = np.sort(pilha, axis=0)[1]
        f[solto] = med[solto]
    return f


class Reiatsu:
    def __init__(self, cw, ch, quadril, pal_base):
        """quadril = (x, y) na tela dos clipes; pal_base = indice onde as
        cores do reiatsu comecam na paleta."""
        self.cw, self.ch = cw, ch
        self.qx, self.qy = quadril
        self.pal = pal_base
        ys, xs = np.mgrid[0:ch, 0:cw]
        self.xs = xs.astype(float)
        self.ys = ys.astype(float)
        # centro e tamanho do casulo (cobre o Bankai inteiro: cabelo atras,
        # espada na frente, pes)
        self.cx = self.qx + 2
        self.cy = self.qy - 26
        self.rx = 90.0
        self.r_cima = 140.0
        self.r_baixo = 96.0
        self.P = 72.0                              # periodo vertical do ruido (loop)
        self.n1 = Ruido(1, 10, 36, self.P, cw, ch)
        self.n2 = Ruido(2, 5, 18, self.P, cw, ch)
        self.n3 = Ruido(3, 3, 9, self.P, cw, ch)
        self.meia_pilar = 24.0                          # meia largura da coluna que sobe
        self.buraco = Ruido(4, 18, 16, self.P, cw, ch)
        rnd = np.random.default_rng(9)
        self.faiscas = [(rnd.uniform(-1, 1), rnd.uniform(0, 1), rnd.integers(1, 3), rnd.uniform(0, 6.28))
                        for _ in range(30)]

    # ── campo de energia ────────────────────────────────────────────────
    def forma(self, escala=1.0):
        X = (self.xs - self.cx) / (self.rx * escala)
        dy = self.ys - self.cy
        ry = np.where(dy < 0, self.r_cima, self.r_baixo) * escala
        Y = dy / ry
        # chama: afina em cima (gota apontando para cima)
        X = X * (1 + 1.1 * np.clip(-Y, 0, 1) ** 1.4)
        f = 1 - np.sqrt(X * X + Y * Y)
        # a coluna de luz que sai do topo e sobe ate o fim da tela
        if escala >= 0.99:
            col = np.clip(1 - np.abs(self.xs - self.cx) / self.meia_pilar, 0, 1) * 0.5
            topo = self.cy - self.r_cima * 0.55
            col = col * np.clip(1 - (self.ys - topo) / 30.0, 0, 1)
            f = np.where(col > 0, np.maximum(f, col), f)
        return f

    def campo(self, sobe, escala=1.0, fervura=1.0):
        """sobe = quanto o ruido ja subiu (texels)."""
        base = self.forma(escala)
        y = self.ys + sobe
        x = self.xs
        n = 0.55 * self.n1(x, y) + 0.3 * self.n2(x + 17, y + 5) + 0.15 * self.n3(x + 3, y + 11)
        cima = np.clip((self.cy - self.ys) / self.r_cima, 0, 1)
        borda = (0.3 + 0.7 * np.clip(1 - base, 0, 1)) * (1 + 0.6 * cima)   # a borda (e o topo) ferve mais
        return base + fervura * 0.75 * (n - 0.5) * borda

    def faixas(self, F, clarear=0.0):
        f = np.zeros(F.shape, np.int32)
        for i, lim in enumerate(LIMIARES):
            f[F + clarear > lim] = i + 1
        return _limpa(f)

    def pintar(self, f, extra=None):
        """faixas (0 = nada, 1..5) -> indices da paleta, com contorno por fora."""
        img = np.zeros(f.shape, np.uint8)
        dentro = f > 0
        viz = np.zeros(f.shape, bool)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            viz |= np.roll(np.roll(dentro, dy, 0), dx, 1)
        img[viz & ~dentro] = self.pal + 0
        for i in range(1, 6):
            img[f == i] = self.pal + i
        if extra is not None:
            m = extra > 0
            img[m] = extra[m]
        return img

    def _faiscas(self, img, t, forca=1.0, so_fora=True):
        H = 230.0
        for (u, fase, tam, osc) in self.faiscas:
            v = H / (2 / 3.0)                          # uma volta por loop (0,67 s)
            s = (fase * H + v * t) % H
            x = int(round(self.cx + u * self.rx * 1.05 + 3 * math.sin(osc + t * 9)))
            y = int(round(self.cy + self.r_baixo * 0.9 - s))
            if not (1 <= x < self.cw - 2 and 1 <= y < self.ch - 2):
                continue
            if forca < 1.0 and (hash((u, fase)) % 100) / 100.0 > forca:
                continue
            cor = self.pal + (5 if tam > 1 else 4)
            for dy in range(tam):
                for dx in range(tam):
                    if not so_fora or img[y + dy, x + dx] == 0:
                        img[y + dy, x + dx] = cor

    # ── clipes ──────────────────────────────────────────────────────────
    def pilar(self, n=8, por_s=12.0):
        """A coluna de luz que continua o topo do casulo ate o fim da tela:
        um BLOCO de P texels de altura que se repete na vertical (o ruido
        repete com o mesmo periodo) - o app empilha o bloco. Mesmas faixas
        e mesma subida do casulo. Desenhado no alto da tela do clipe
        (linhas 0..P-1), centrado na coluna."""
        L = n / por_s
        out = []
        P = int(self.P)
        m = int(self.meia_pilar) + 8
        x0, x1 = int(self.cx) - m, int(self.cx) + m
        for i in range(n):
            t = i / por_s
            xs = self.xs[:P, x0:x1]
            ys = self.ys[:P, x0:x1]
            y = ys + self.P * t / L
            nz = 0.55 * self.n1(xs, y) + 0.3 * self.n2(xs + 17, y + 5) + 0.15 * self.n3(xs + 3, y + 11)
            col = np.clip(1 - np.abs(xs - self.cx) / self.meia_pilar, 0, 1) * 0.5
            # a mesma conta do topo do casulo (emenda sem degrau)
            F = col + 0.75 * (nz - 0.5) * (0.3 + 0.7 * (1 - col)) * 1.6
            F[col <= 0] = -9.0
            f = np.zeros(F.shape, np.int32)
            for k, lim in enumerate(LIMIARES):
                f[F > lim] = k + 1
            # sem limpar na vertical (o bloco tem que emendar em cima e embaixo)
            img = np.zeros((self.ch, self.cw), np.uint8)
            dentro = f > 0
            viz = np.zeros(f.shape, bool)
            viz[:, 1:] |= dentro[:, :-1]
            viz[:, :-1] |= dentro[:, 1:]
            bloco = np.zeros(f.shape, np.uint8)
            bloco[viz & ~dentro] = self.pal
            for k in range(1, 6):
                bloco[f == k] = self.pal + k
            img[:P, x0:x1] = bloco
            out.append(img)
        return out

    def ferve(self, n=8, por_s=12.0):
        L = n / por_s
        out = []
        for i in range(n):
            t = i / por_s
            F = self.campo(self.P * t / L)
            img = self.pintar(self.faixas(F))
            self._faiscas(img, t)
            out.append(img)
        return out

    def estouro(self):
        """6 desenhos (15/s): raios + anel no chao + casulo crescendo claro."""
        escalas = [0.3, 0.55, 0.8, 1.06, 1.03, 1.0]
        claro = [0.55, 0.45, 0.3, 0.16, 0.07, 0.0]
        out = []
        pe = (self.qx, self.qy + 58)
        L = 8 / 12.0
        for i, (s, c) in enumerate(zip(escalas, claro)):
            # o fogo ja vem subindo no mesmo passo da fervura: o ultimo desenho
            # do estouro e o que vem logo antes do primeiro da fervura
            t = (i - 5) / 15.0 - 1 / 12.0
            F = self.campo(self.P * t / L, escala=s, fervura=0.6 + 0.4 * i / 5.0)
            f = self.faixas(F, clarear=c)
            extra = np.zeros(f.shape, np.uint8)
            # raios saindo do centro (so nos primeiros)
            if i <= 2:
                comp = [70, 120, 150][i]
                for k in range(14):
                    a = 2 * math.pi * k / 14 + 0.2
                    larg = 3 if k % 2 == 0 else 2
                    for r in range(int(comp * 0.25), comp):
                        x = self.cx + r * math.cos(a)
                        y = self.cy + r * math.sin(a) * 1.1
                        cor = self.pal + (5 if r < comp * 0.6 else 4)
                        for w in range(-(larg // 2), larg - larg // 2):
                            xi = int(round(x - w * math.sin(a)))
                            yi = int(round(y + w * math.cos(a)))
                            if 0 <= xi < self.cw and 0 <= yi < self.ch:
                                extra[yi, xi] = cor
            # onda de choque no chao (elipse achatada)
            if i >= 1:
                rx = 30 + 36 * i
                ry = rx * 0.2
                esp = 3 if i < 4 else 2
                d = np.hypot((self.xs - pe[0]) / rx, (self.ys - pe[1]) / ry)
                anel = np.abs(d - 1) * rx < esp
                if i >= 4:          # o anel quebra em pedacos
                    anel &= (np.floor(np.degrees(np.arctan2(self.ys - pe[1], self.xs - pe[0])) / 14) % 3 != 0)
                cor = self.pal + (5 if i < 3 else (4 if i < 5 else 3))
                extra[anel & (f == 0)] = cor
            img = self.pintar(f, extra)
            self._faiscas(img, t)
            out.append(img)
        return out

    def dissipa(self, n=16, por_s=15.0, corpo=None):
        """O casulo se abre do meio para fora: a energia sai PRIMEIRO de cima
        do corpo dele (`corpo` = mascara do Bankai no 1o quadro da revelacao,
        engordada 2 pixels) - ele aparece inteiro logo no comeco - e depois a
        energia em volta sai pelas bordas, sobe, escurece e some em fiapos.
        Comeca onde a fervura para (o app troca no fim de uma volta)."""
        out = []
        L = 8 / 12.0
        tira_corpo = 0.0
        if corpo is not None:
            m = corpo.copy()
            for _ in range(2):
                v = m.copy()
                v[1:, :] |= m[:-1, :]
                v[:-1, :] |= m[1:, :]
                v[:, 1:] |= m[:, :-1]
                v[:, :-1] |= m[:, 1:]
                m = v
            tira_corpo = m.astype(float)
        for i in range(n):
            u = (i + 1) / float(n)
            t = (i + 1) / por_s
            sobe = self.P * t / L + 80 * u * u              # os pedacos vao subindo
            F = self.campo(sobe, fervura=1.0 + 0.8 * u)
            # abre do MEIO para fora (ele aparece primeiro, a energia sai
            # pelas bordas e sobe), com buracos irregulares
            W = self.buraco(self.xs, self.ys + sobe * 0.5)
            X = (self.xs - self.cx) / self.rx
            Y = (self.ys - self.cy) / np.where(self.ys < self.cy, self.r_cima, self.r_baixo)
            meio = np.clip(1 - np.sqrt(X * X + Y * Y), 0, 1)
            baixo = np.clip((self.ys - (self.cy - self.r_cima)) / (self.r_cima + self.r_baixo), 0, 1)
            # quanto cada ponto dura: pouco no meio e embaixo (ele aparece de
            # dentro para fora), mais nas bordas e no alto (a energia sai e sobe)
            vida = 0.5 * W + 0.8 * (1 - meio) ** 1.2 + 0.25 * (1 - baixo) - 1.2 * tira_corpo
            vivo = vida > u * 1.25
            f = self.faixas(F, clarear=-0.3 * u)            # esfria: o branco some primeiro
            f[~vivo] = 0
            f = _limpa(f)
            img = self.pintar(f)
            self._faiscas(img, t, forca=1.0 - u)
            out.append(img)
        return out
