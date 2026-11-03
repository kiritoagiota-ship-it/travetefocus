"""
cenas_luta.py — a ABERTURA DA LUTA contra o chefe THE ABYSS WARDEN (guardada
em 03/11/2026, a pedido do usuario; no app entrou a abertura simples
aberturas.abertura_chegada). Estas sao as pecas que ficavam no cenas.py e so
a luta usava, com o texto igual. Elas usam o resto do cenas.py (TituloLuz,
_Agenda, efeitos...), por isso o jeito facil de ver a luta funcionando e o
git: `git checkout abertura-luta-chefe` (a versao 1.17 inteira).
Para trazer de volta: ver LEIA-ME.txt nesta pasta.
"""
from cenas import *          # noqa: F401,F403  (as pecas usam o resto do cenas.py)
from cenas import (_Agenda, _Uma, _som, _com, _PX, _no_quadro, _mover, _tremer,  # noqa: F401
                   _precarregar_sons, _ps_titulo)


# efeitos que as cenas tocam (pre-carregados no inicio de cada cena)
_SONS_TITULO = ['koiguchi', 'pulo', 'pouso', 'sacar_iai', 'corte', 'sacar', 'corte2',
                'absorve', 'carga', 'getsuga', 'separa', 'desliza', 'embainhar', 'titulo',
                'golpe_final', 'fala_ougi', 'fala_ikuzo', 'fala_kurae', 'kiai_seiya', 'giro', 'fitas',
                'trevas', 'fusao', 'reiatsu', 'kiai_kai', 'agarra', 'cristal', 'transicao',
                'kiai_ha1', 'kiai_ha2', 'kiai_sei1', 'kiai_sei2', 'kiai_sei3', 'kiai_fun', 'rugido', 'vidro']


def _fundo(tela, reator=None, barra=None, dur=0.6):
    """Escurece/acende o fundo da loading (infinito e barra): durante a luta
    o foco fica no Kirito e no titulo."""
    try:
        from kivy.animation import Animation
        ids = getattr(tela, 'ids', {})
        for nome, alvo in (('reator_shader', reator), ('barra_loading', barra)):
            w = ids.get(nome) if hasattr(ids, 'get') else None
            if w is not None and alvo is not None:
                Animation.cancel_all(w, 'opacity')
                Animation(opacity=alvo, duration=dur).start(w)
    except Exception as e:
        print(f"[cena] fundo: {e}")


def preparar_meialua(centro, raio, ang_ini, ang_fim, espessura, achat=1.0, rotacao=0.0):
    """Calcula antes (fora da hora do golpe) a forma de uma meia-lua grande."""
    rot = math.radians(rotacao)
    _geometria_meialua(centro, float(raio), math.radians(ang_ini), math.radians(ang_fim), float(espessura),
                       float(achat), math.cos(rot), math.sin(rot), max(1.0, _PX[0]))


# ═══════════════════════════════════════════════════════════════════
#  CENA DO TITULO
# ═══════════════════════════════════════════════════════════════════
_TRECHOS = [(0, 3), (3, 5), (5, 8), (8, 10), (10, 13)]      # TRA|VE|TE |FO|CUS


# ═══════════════════════════════════════════════════════════════════
#  EFEITOS DA TRANSFORMACAO (Bankai)
# ═══════════════════════════════════════════════════════════════════
_CORES_CHAMA = (('L', (0.93, 0.86, 1.0, 1.0)), ('V', (0.86, 0.58, 1.0, 1.0)),
                ('F', (0.62, 0.28, 1.0, 0.95)), ('o', (0.42, 0.18, 0.78, 0.9)),
                ('d', (0.24, 0.10, 0.42, 0.8)))


class _ChamasBankai(Widget):
    """Chamas roxas de pixel art em volta do Bankai: linguas de fogo (3 a 5
    blocos empilhados que afinam na ponta) nascem no chao e nas bordas do
    corpo, sobem balancando e escurecem em degraus antes de sumir. `alvo`
    0..1 = quantas nascem (a forca vai ate ele aos poucos)."""

    def __init__(self, k, u, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k = k
        self.u = max(1.0, float(u))
        self.forca = 0.0
        self.alvo = 0.0
        self._f = []
        self._acc = 0.0
        self._caixa = None
        self._n = 0
        self._lote = K.LotePixels(self.canvas, _CORES_CHAMA)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _corpo(self):
        """(x0, x1, y_pe, altura) do corpo, estimado pela ancora (quadril) e
        pelo tamanho da unidade - sem desenhar nada para medir."""
        k = self.k
        if getattr(k, '_desenho', None) is not None:
            return k.corpo_desenho()
        ps = k.ps
        ax, ay = k.ancora()
        frente = -1 if k.espelhar else 1
        x0, x1 = sorted((ax - frente * 7 * ps, ax + frente * 5 * ps))
        dy = (k._base.get('dy', 0) or 0) * ps
        return (x0, x1, ay - 12 * ps - dy, 30 * ps)

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            self.forca += (self.alvo - self.forca) * min(1.0, dt * 3.0)
            k = self.k
            u = self.u
            if k.parent is None or k.opacity < 0.05:
                self._lote.desenhar({})
                return True
            x0, x1, y_pe, alt = self._corpo()
            self._acc += self.forca * 95.0 * dt
            while self._acc >= 1.0:
                self._acc -= 1.0
                borda = random.random() < 0.7
                if borda:                                   # nas bordas do corpo (mais atras)
                    x = (x0 + random.uniform(-0.1, 0.25) * (x1 - x0)) if random.random() < 0.6 \
                        else (x1 - random.uniform(-0.1, 0.25) * (x1 - x0))
                else:
                    x = random.uniform(x0, x1)
                y = y_pe + alt * (random.random() ** 2.2) * 0.85
                vida = random.uniform(0.35, 0.75)
                self._f.append({'x': x, 'y': y, 'vy': alt * random.uniform(0.6, 1.1), 't': 0.0,
                                'vida': vida, 'n': random.choice((4, 5, 5, 6)),
                                'fb': random.uniform(7, 12), 'ph': random.uniform(0, 6.3)})
            pts = {}
            vivas = []
            for f in self._f:
                f['t'] += dt
                if f['t'] >= f['vida']:
                    continue
                vivas.append(f)
                f['y'] += f['vy'] * dt
                a = f['t'] / f['vida']
                bx = math.floor((f['x'] + math.sin(f['t'] * f['fb'] + f['ph']) * u * 1.4) / u) * u
                by = math.floor(f['y'] / u) * u
                n = max(1, int(round(f['n'] * (1.0 - 0.5 * a))))       # encurta enquanto sobe
                c = min(4, int(a * 2.6))
                for i in range(n):
                    if i == n - 1:
                        nome = ('L', 'V', 'F', 'o', 'd')[c]           # pontinha clara so quando nova
                    elif i == n - 2:
                        nome = ('V', 'F', 'o', 'd', 'd')[c]
                    else:
                        nome = ('F', 'F', 'o', 'd', 'd')[c]           # base roxa
                    larg = 3 if (i == 0 and a < 0.3) else (2 if (i < n - 2 and a < 0.6) else 1)
                    tremor = u if (i == n - 1 and int(f['t'] * 20 + f['ph']) % 2) else 0
                    pts.setdefault(nome, []).append((bx - (larg - 1) * u * 0.5 + tremor, by + i * u, larg * u, u))
            self._f = vivas[-160:]
            self._lote.desenhar(pts)
        except Exception as e:
            print(f"[chamas] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


class _PilarReiatsu(Widget):
    """A coluna de luz do BAN-KAI: continua o topo do casulo (widget `kr`,
    que toca os clipes do reiatsu) ate o fim da tela. E o bloco 'rei_pilar'
    do clipes.bin (mesmas cores e mesmo fogo subindo do casulo) empilhado -
    troca a textura 30 vezes por segundo, no MESMO passo do casulo (sem
    emenda). Nasce subindo como um raio ate o ceu e, no fim, descola de
    baixo para cima."""

    N_MAX = 16

    def __init__(self, kr, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.kr = kr
        self.t = 0.0
        self.sobe = 1.0 / 0.22            # o raio chega ao topo em 0,22 s
        self.alto = 0.0                   # 0..1 da base ate o fim da tela
        self.baixo = 0.0                  # 0..1: a base descolando
        self.vel_baixo = 0.0
        with self.canvas:
            Color(1, 1, 1, 1)
            self._rects = [Rectangle(pos=(0, 0), size=(0, 0)) for _ in range(self.N_MAX)]
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def sumir(self, dur=0.45):
        self.vel_baixo = 1.0 / max(0.05, dur)

    def _indice(self):
        """Desenho do bloco no mesmo passo do casulo."""
        kr = self.kr
        cab = K.clipes_dados()
        n = len(cab['clipes']['rei_pilar']['quadros'])
        nome = getattr(kr, '_desenho', None)
        t = getattr(kr, '_clipe_t', self.t)
        if nome == 'rei_estouro':          # o estouro termina 1 passo antes da fervura
            d = int(t * 30 + 1e-6)
            m = len(cab['clipes']['rei_estouro']['quadros'])
            return (min(d, m - 1) - m) % n
        if nome == 'rei_ferve':
            return int(t * 30 + 1e-6) % n
        return int(self.t * 30) % n

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            self.t += dt
            self.alto = min(1.0, self.alto + self.sobe * dt)
            if self.vel_baixo:
                self.baixo = min(1.0, self.baixo + self.vel_baixo * dt)
                if self.baixo >= 1.0:
                    self.parent.remove_widget(self)
                    return self.parar()
            kr = self.kr
            te = kr.te_clipe()
            tex, (x0, y0, w, h), _, _ = K.quadro_clipe('rei_pilar', self._indice())
            xa, yb = kr._local_desenho(x0, 0)                 # topo da tela do clipe = base da coluna
            x = kr.x + (xa - w * te if kr.espelhar else xa)
            base = kr.y + yb
            H = Window.size[1] / max(0.2, getattr(self.parent, 'scale', 1.0) or 1.0) + h * te
            topo_vis = base + (H - base) * self.alto
            topo_vis = math.floor(topo_vis / te) * te
            base_vis = base + (H - base) * self.baixo
            base_vis = math.floor(base_vis / te) * te
            bh = h * te
            tc = K._tc_espelhado(tex.tex_coords) if kr.espelhar else tex.tex_coords
            u0, v0, u1, _, _, v1, _, _ = tc[0], tc[1], tc[2], tc[3], tc[4], tc[5], tc[6], tc[7]
            for j, r in enumerate(self._rects):
                y_a = base + j * bh
                y_b = y_a + bh
                lo, hi = max(y_a, base_vis), min(y_b, topo_vis)
                if hi <= lo:
                    r.size = (0, 0)
                    continue
                fa, fb = (lo - y_a) / bh, (hi - y_a) / bh
                va, vb = v0 + (v1 - v0) * fa, v0 + (v1 - v0) * fb
                r.texture = tex
                r.pos = (x, lo)
                r.size = (w * te, hi - lo)
                r.tex_coords = (u0, va, u1, va, u1, vb, u0, vb)
            return True
        except Exception as e:
            print(f"[pilar] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


class _OlhosAcesos(Widget):
    """O olho do Bankai acendendo dentro do reiatsu: miolo branco com a
    borda escura (aparece em cima de qualquer cor) e uma cruz lilas que
    cresce (desenho novo todo quadro) e pisca."""

    def __init__(self, pos, u, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.p = pos
        self.u = max(1.0, float(u))
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, (('borda', (0.12, 0.04, 0.27, 1.0)),
                                                ('halo', (0.63, 0.41, 1.0, 1.0)),
                                                ('luz', (0.97, 0.94, 1.0, 1.0))))
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            self.t += dt
            u = self.u
            cx = math.floor(self.p[0] / u) * u
            cy = math.floor(self.p[1] / u) * u
            f = self.t * 12.0
            # o olho: miolo branco com borda escura e o risco de luz de anime
            # (abre para os lados e depois pisca)
            n = min(12, int(3 + 2 * f)) - (int(f) % 2 if f > 6 else 0)
            pts = {'borda': [(cx - 3 * u, cy - 2 * u, 7 * u, 4 * u), (cx - (n + 2) * u, cy - u, (2 * n + 5) * u, 3 * u)],
                   'halo': [(cx - (n + 1) * u, cy, (2 * n + 3) * u, u), (cx - 2 * u, cy - u, 5 * u, 3 * u)],
                   'luz': [(cx - u, cy - u, 3 * u, 2 * u), (cx - (n // 2 + 1) * u, cy, (n + 3) * u, u)]}
            for k in (3, 4):                                           # cruz curta em cima e embaixo
                pts['halo'].append((cx, cy + k * u, u, u))
                pts['halo'].append((cx, cy - k * u, u, u))
            self._lote.desenhar(pts)
            return True
        except Exception as e:
            print(f"[olhos] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


_CORES_LUA = (('halo', (0.40, 0.16, 0.72, 0.5)), ('fundo', (0.03, 0.01, 0.055, 0.95)),
              ('miolo', (0.07, 0.02, 0.12, 0.95)), ('borda', (0.62, 0.30, 1.0, 1.0)),
              ('claro', (0.93, 0.82, 1.0, 1.0)))


class _LuaNegra(Widget):
    """Lua negra atras do Bankai: disco escuro de pixels grandes com a borda
    roxa acesa (que tremula) e um halo pontilhado; cresce em degraus e
    some encolhendo."""

    def __init__(self, centro, raio, u, dur=0.5, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.c = centro
        self.u = max(2.0, float(u))
        self.r_alvo = float(raio)
        self.r = 0.0
        self.vel = raio / max(0.05, dur)
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, _CORES_LUA)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def sumir(self, dur=0.35):
        self.r_alvo = 0.0
        self.vel = max(self.r, 1.0) / max(0.05, dur)

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            self.t += dt
            if self.r < self.r_alvo:
                self.r = min(self.r_alvo, self.r + self.vel * dt)
            elif self.r > self.r_alvo:
                self.r = max(self.r_alvo, self.r - self.vel * dt)
                if self.r <= 0.0:
                    if self.parent is not None:
                        self.parent.remove_widget(self)
                    return self.parar()
            u = self.u
            n = int(self.r / u)
            cx = math.floor(self.c[0] / u) * u
            cy = math.floor(self.c[1] / u) * u
            pts = {}
            f = int(self.t * 30)
            for iy in range(-n - 2, n + 3):
                w_f = math.sqrt(max(0.0, (n - 0.5) ** 2 - iy * iy))
                if w_f > 0:
                    k0 = int(math.floor(-w_f))
                    pts.setdefault('fundo', []).append((cx + k0 * u, cy + iy * u, (2 * -k0 + 1) * u, u))
                    if abs(iy) < n * 0.55:                               # miolo um tiquinho mais claro
                        w_m = math.sqrt(max(0.0, (n * 0.55) ** 2 - iy * iy))
                        km = int(math.floor(-w_m))
                        pts.setdefault('miolo', []).append((cx + km * u, cy + iy * u, (2 * -km + 1) * u, u))
            if n >= 1:
                m = max(16, int(2 * math.pi * n))
                vistos = set()
                for i in range(m):
                    a = 2 * math.pi * i / m
                    for rr, nome in ((n, 'borda'), (n + 1.6, 'halo')):
                        gx, gy = int(round(math.cos(a) * rr)), int(round(math.sin(a) * rr))
                        if (gx, gy, nome) in vistos:
                            continue
                        vistos.add((gx, gy, nome))
                        h = (gx * 7 + gy * 13 + f) % 9
                        if nome == 'halo' and h > 3:
                            continue
                        nm = 'claro' if (nome == 'borda' and h == 0) else nome
                        pts.setdefault(nm, []).append((cx + gx * u, cy + gy * u, u, u))
            self._lote.desenhar(pts)
        except Exception as e:
            print(f"[lua] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


class _AnelEnergia(Widget):
    """A linha da transformacao: uma elipse achatada de pixels roxos e
    lilases em volta do corpo, na altura y (a frente mais clara que a parte
    de tras), tremulando."""

    def __init__(self, u, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.u = max(1.0, float(u))
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, _CORES_CHAMA)

    def pos_linha(self, cx, y, larg, dt=1 / 60.):
        self.t += dt
        u = self.u
        a = max(u * 3, larg / 2.0)
        b = u * 2.2
        n = max(16, int(2 * math.pi * a / u))
        pts = {}
        f = int(self.t * 24)
        for i in range(n):
            ang = 2 * math.pi * i / n
            x = math.floor((cx + math.cos(ang) * a) / u) * u
            yy = math.floor((y + math.sin(ang) * b) / u) * u
            frente = math.sin(ang) < 0
            h = (i * 5 + f) % 7
            if frente:
                nome = 'L' if h < 2 else 'V'
            else:
                if h > 4:
                    continue
                nome = 'F' if h < 3 else 'o'
            pts.setdefault(nome, []).append((x, yy, u, u))
            if frente and h == 0:                               # lingua de fogo subindo da frente
                pts.setdefault('F', []).append((x, yy + u, u, u))
        # a faixa de corte atravessando o corpo: linha clara com fogo roxo por cima
        k0 = math.floor((cx - a) / u)
        k1 = math.floor((cx + a) / u)
        yb = math.floor(y / u) * u
        for k in range(k0, k1 + 1):
            h = (k * 3 + f) % 5
            pts.setdefault('L' if h else 'V', []).append((k * u, yb, u, u))
            if h < 2:
                pts.setdefault('F', []).append((k * u, yb + u, u, u))
            if h == 0:
                pts.setdefault('o', []).append((k * u, yb + 2 * u, u, u))
        self._lote.desenhar(pts)


class _BarraChefe(Widget):
    """Nome e barra de vida do chefe (como os chefes de andar de SAO), em
    pixels: moldura, a vida em brasa e, em branco, o pedaco que ele acabou
    de perder - que encolhe um instante depois, em degraus."""

    def __init__(self, nome, cx, y, larg, u, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.u = max(2.0, float(round(u)))
        self.cx, self.y0, self.larg = cx, y, larg
        self.frac, self.lag = 1.0, 1.0
        self.abre, self._alvo = 0.0, 0.0
        self._espera = 0.0
        self._sai = False
        self._lote = K.LotePixels(self.canvas, (('f', (0.03, 0.02, 0.05, 1.0)), ('m', (0.60, 0.64, 0.76, 1.0)),
                                                ('e', (0.30, 0.04, 0.05, 1.0)), ('v', (0.84, 0.15, 0.10, 1.0)),
                                                ('c', (1.0, 0.56, 0.20, 1.0)), ('b', (1.0, 1.0, 1.0, 1.0))))
        from kivy.core.text import Label as CoreLabel
        cl = CoreLabel(text=nome, font_name='orbitron.ttf', font_size=max(sp(9), self.u * 3.2), bold=True)
        cl.refresh()
        self._tex = cl.texture
        with self.canvas:
            self._c_nome = Color(1.0, 0.84, 0.74, 0)
            self._r_nome = Rectangle(texture=self._tex, size=self._tex.size, pos=(0, 0))
        self._ev = Clock.schedule_interval(self._tique, 1 / 30.)

    def mostrar(self):
        self._alvo = 1.0

    def dano(self, frac):
        """A vida cai para `frac` (0..1) de uma vez; o branco some depois."""
        self.frac = max(0.0, min(self.frac, frac))
        self._espera = 0.3

    def sumir(self):
        self._alvo = 0.0
        self._sai = True

    def _tique(self, dt):
        try:
            if self.parent is None:
                return False
            if self.abre < self._alvo:
                self.abre = min(self._alvo, self.abre + 0.2)
            elif self.abre > self._alvo:
                self.abre = max(self._alvo, self.abre - 0.25)
            if self._espera > 0:
                self._espera -= dt
            elif self.lag > self.frac:
                self.lag = max(self.frac, self.lag - 0.05)
            u = self.u
            p = {}
            wb = math.floor(self.larg * self.abre / u) * u
            if wb >= 6 * u:
                x0 = math.floor((self.cx - wb / 2.0) / u) * u
                y = math.floor(self.y0 / u) * u
                h = 3 * u
                p['f'] = [(x0, y, wb, h)]
                p['m'] = [(x0, y + h, wb, u), (x0, y - u, wb, u), (x0 - u, y, u, h), (x0 + wb, y, u, h),
                          (x0 - 2 * u, y + u, u, u), (x0 + wb + u, y + u, u, u)]
                dentro = wb - 2 * u
                wv = math.floor(dentro * self.frac / u) * u
                wl = math.floor(dentro * self.lag / u) * u
                p['e'] = [(x0 + u, y, dentro, h)]
                if wl > wv:
                    p['b'] = [(x0 + u + wv, y, wl - wv, h)]
                if wv > 0:
                    p['v'] = [(x0 + u, y, wv, h)]
                    p['c'] = [(x0 + u, y + 2 * u, wv, u)]
                for k in range(1, 10):                          # marcas de 10 em 10
                    xm = x0 + u + math.floor(dentro * k / 10.0 / u) * u
                    p['f'].append((xm, y, u, u))
                self._r_nome.pos = (x0, y + h + 2 * u)
                self._c_nome.a = 1.0 if self.abre >= 1.0 else 0.0
            else:
                self._c_nome.a = 0.0
            self._lote.desenhar(p)
            if self._sai and self.abre <= 0:
                if self.parent is not None:
                    self.parent.remove_widget(self)
                return False
            return True
        except Exception as e:
            print(f"[cena] barra do chefe: {e}")
            return False


def _surgir_chefe(boss, camada, dur, on_fim=None, cor=BRASA):
    """O chefe se ergue do chao em faixas, de baixo para cima: silhueta em
    brasa escura que ganha cor em 3 degraus, com uma barra de luz na emenda
    (nada de transparencia)."""
    fim = _Uma(on_fim)
    antes = tuple(boss.cor_clarao)

    def _pronto():
        boss.recortar()
        boss.cor_clarao = antes
        boss.clarao = 0.0
        boss.opacity = 1
        fim()
    try:
        te = boss.te
        base, topo = boss.y - 2 * te, boss.top + 2 * te
        cx, larg = boss.center_x, boss.width * 0.86
        n = max(6, int(round(dur * 30)))
        boss.cor_clarao = (0.40, 0.05, 0.04)
        boss.opacity = 1
        boss.clarao = 1.0
        boss.recortar(None, base)

        def emenda(d):
            i = min(n, max(0, d + 1))
            return base + math.floor((topo - base) * i / float(n) / te) * te

        def forma(t, p, u):
            d = int(t * 30)
            if d >= n:
                return
            y = math.floor(emenda(d) / u) * u
            x0 = math.floor((cx - larg / 2.0) / u)
            x1 = math.floor((cx + larg / 2.0) / u)
            borda = max(1, (x1 - x0) // 6)
            for gx in range(x0, x1 + 1):
                ponta = gx - x0 < borda or x1 - gx < borda
                if ponta and (gx + d) % 2:
                    continue
                p.setdefault('cor' if ponta else 'luz', []).append((gx * u, y, u, u))
                if not ponta:
                    p.setdefault('clara', []).append((gx * u, y - u, u, u))
                    if (gx + d) % 3 == 0:
                        p.setdefault('cor', []).append((gx * u, y - 2 * u, u, u))
        camada.add_widget(_EfeitoPixel(_cores_efeito(cor), (n + 4) / 30.0, forma))
        passo = [-1]
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                d = int(t[0] * 30)
                if d == passo[0]:
                    return True
                passo[0] = d
                if d < n:
                    boss.recortar(None, emenda(d))
                elif d < n + 3:
                    boss.recortar()
                    boss.clarao = (2, 1, 0)[d - n] / 3.0
                else:
                    _pronto()
                    return False
                return True
            except Exception as e:
                print(f"[cena] chefe surge: {e}")
                _pronto()
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[cena] chefe surge ignorado: {e}")
        _pronto()


# ═══════════════════════════════════════════════════════════════════
#  A LUTA EM "CENA DE ANIME": cenario, faixas de cinema, linhas de
#  velocidade, close do chefe, raio de sangue, sombra no chao
# ═══════════════════════════════════════════════════════════════════
class _CenarioChefe(Widget):
    """O cenario da luta (chefe/cenario_*.png, feitos em dev/cenario_chefe.py
    a partir do desenho do usuario): ceu com a lua em eclipse, o castelo ao
    longe e o chao rachado em brasa. O horizonte fica na linha `chao`.
    abrir(): aparece a partir do horizonte (o ceu sobe, o chao desce);
    fechar(): some do mesmo jeito; tranco(): um solavanco (impactos grandes)."""

    def __init__(self, W, H, chao, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.W, self.H, self.chao = W, H, float(chao)
        self.f, self.alvo, self.vel = 0.0, 0.0, 1.0
        self._tr = 0
        self._passo = -1
        self._tex = {}
        try:
            from kivy.core.image import Image as CoreImage
            pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chefe')
            for n in ('ceu', 'longe', 'chao'):
                t = CoreImage(os.path.join(pasta, 'cenario_%s.png' % n)).texture
                t.mag_filter = t.min_filter = 'nearest'
                self._tex[n] = t
        except Exception as e:
            print(f"[cenario] {e}")
        self.u = W / 180.0                                   # as imagens tem 200 pontos de largura: sobra 10 de cada lado
        with self.canvas:
            self._c_topo = Color(7 / 255.0, 4 / 255.0, 9 / 255.0, 1)
            self._r_topo = Rectangle(pos=(0, 0), size=(0, 0))
            self._c_base = Color(4 / 255.0, 2 / 255.0, 5 / 255.0, 1)
            self._r_base = Rectangle(pos=(0, 0), size=(0, 0))
            Color(1, 1, 1, 1)
            self._r = {n: Rectangle(pos=(0, 0), size=(0, 0), texture=self._tex.get(n)) for n in ('ceu', 'longe', 'chao')}
        self._ev = Clock.schedule_interval(self._tique, 1 / 60.)

    def abrir(self, dur=0.7):
        self.alvo, self.vel = 1.0, 1.0 / max(0.05, dur)

    def fechar(self, dur=0.5):
        self.alvo, self.vel = 0.0, 1.0 / max(0.05, dur)

    def tranco(self):
        self._tr = 8

    def _tique(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            if self.f != self.alvo:
                d = self.vel * dt
                self.f = min(self.alvo, self.f + d) if self.alvo > self.f else max(self.alvo, self.f - d)
            dy = 0
            if self._tr > 0:
                self._tr -= 1
                dy = (self._tr % 2 * 2 - 1) * int(self.u) * (1 if self._tr > 3 else 0.5)
            passo = (int(self.f * 24), dy)
            if passo == self._passo:
                return True
            self._passo = passo
            f = int(self.f * 24) / 24.0
            u, W, H, ch = self.u, self.W, self.H, self.chao + dy
            if f <= 0 or not self._tex:
                for r in list(self._r.values()) + [self._r_topo, self._r_base]:
                    r.size = (0, 0)
                return True
            x0 = -10 * u
            # ceu: da linha do horizonte para cima, ate a fracao f
            tc, hc = self._tex['ceu'], self._tex['ceu'].height * u
            vis = min(hc, (H - ch)) * f
            self._r['ceu'].pos = (x0, ch)
            self._r['ceu'].size = (tc.width * u, vis)
            fr = vis / hc
            self._r['ceu'].tex_coords = (0, 1, 1, 1, 1, 1 - fr, 0, 1 - fr)
            if f >= 1 and ch + hc < H:
                self._r_topo.pos, self._r_topo.size = (0, ch + hc), (W, H - ch - hc)
            else:
                self._r_topo.size = (0, 0)
            tl, hl = self._tex['longe'], self._tex['longe'].height * u
            visl = min(hl, vis)
            frl = visl / hl
            self._r['longe'].pos = (x0, ch)
            self._r['longe'].size = (tl.width * u, visl)
            self._r['longe'].tex_coords = (0, 1, 1, 1, 1, 1 - frl, 0, 1 - frl)
            # chao: do horizonte para baixo
            tg, hg = self._tex['chao'], self._tex['chao'].height * u
            visg = min(hg, ch) * f
            frg = visg / hg
            self._r['chao'].pos = (x0, ch - visg)
            self._r['chao'].size = (tg.width * u, visg)
            self._r['chao'].tex_coords = (0, frg, 1, frg, 1, 0, 0, 0)
            if f >= 1 and ch - hg > 0:
                self._r_base.pos, self._r_base.size = (0, 0), (W, ch - hg)
            else:
                self._r_base.size = (0, 0)
            return True
        except Exception as e:
            print(f"[cenario] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


def _close_chefe(camada, boss, dur=0.75, y_rel=0.6, on_fim=None):
    """Close de anime do chefe: uma faixa atravessa a tela mostrando o elmo
    dele ampliado (os olhos e os dentes acesos), com riscos de velocidade."""
    fim = _Uma(on_fim)
    try:
        W, H = camada.size
        hb = round(H * 0.15)
        y = round(H * y_rel - hb / 2.0)
        z = 3.0
        w = Widget(size_hint=(None, None), size=(0, 0))
        fbo_tex = boss._fbo.texture
        ox, oy = boss._pontos['olho'] if boss._pontos else (0, 0)
        # a regiao da telinha do chefe em volta do olho (y da telinha para baixo)
        rw, rh = W / z, hb / z
        cx, cy = ox + rw * 0.08, oy + rh * 0.12
        u0, u1 = (cx - rw / 2.0) / boss.CW, (cx + rw / 2.0) / boss.CW
        v0, v1 = (boss.CH - (cy + rh / 2.0)) / boss.CH, (boss.CH - (cy - rh / 2.0)) / boss.CH
        borda = max(2.0, round(_PX[0] * 3))
        with w.canvas:
            Color(0.02, 0.0, 0.01, 1)
            fundo = Rectangle(pos=(0, y), size=(W, hb))
            Color(1, 1, 1, 1)
            img = Rectangle(pos=(0, y), size=(W, hb), texture=fbo_tex, tex_coords=(u0, v0, u1, v0, u1, v1, u0, v1))
            Color(1.0, 0.2, 0.14, 1)
            b1 = Rectangle(pos=(0, y + hb), size=(W, borda))
            b2 = Rectangle(pos=(0, y - borda), size=(W, borda))
        camada.add_widget(w)
        _som('koiguchi')
        t = [0.0]

        def _p(dt):
            t[0] += dt
            # entra deslizando da direita em 3 degraus e sai para a esquerda
            d = int(t[0] * 30)
            fora = int((dur - t[0]) * 30)
            dx = (W * (0.66, 0.3, 0.1)[d] if d < 3 else 0) - (W * (0.1, 0.3, 0.66)[2 - fora] if 0 <= fora < 3 else 0)
            for r in (fundo, img, b1, b2):
                r.pos = (dx, r.pos[1])
            if t[0] >= dur:
                if w.parent:
                    w.parent.remove_widget(w)
                fim()
                return False
            return True
        Clock.schedule_interval(_p, 1 / 60.)
        _linhas_velocidade(camada, dur, (1.0, 0.3, 0.2), y0=y, y1=y + hb, n=10)
    except Exception as e:
        print(f"[cena] close do chefe: {e}")
        fim()


def _projetil_sangue(camada, de, para, dur, te, on_chega=None, pequeno=False):
    """O raio de sangue do montante: uma lanca de luz vermelha com o miolo
    claro e um rastro em degraus, de `de` ate `para`."""
    chegou = _Uma(lambda: on_chega(para[0], para[1]) if on_chega else None)
    try:
        dx, dy = para[0] - de[0], para[1] - de[1]
        d = math.hypot(dx, dy) or 1.0
        ux, uy = dx / d, dy / d
        b = te * (4 if pequeno else 8)
        n = 7 if pequeno else 12

        def forma(t, p, u):
            k = min(1.0, t / dur)
            if k >= 1.0:
                chegou()
                return
            hx, hy = de[0] + dx * k, de[1] + dy * k
            for j in range(n):
                x, y = hx - ux * j * b * 1.1, hy - uy * j * b * 1.1
                if (x - de[0]) * ux + (y - de[1]) * uy < 0:
                    break
                g = max(1, (4 if pequeno else 6) - j // 2)          # afina para tras
                nome = 'luz' if j < 2 else ('clara' if j < 5 else 'cor')
                lado = g * b / 3.0
                for s in (-1, 0, 1) if g > 2 else (0,):
                    p.setdefault(nome if s == 0 else 'cor', []).append(
                        (math.floor((x - uy * s * lado) / u) * u, math.floor((y + ux * s * lado) / u) * u,
                         max(u, math.floor(lado / u) * u), max(u, math.floor(lado / u) * u)))
        camada.add_widget(_EfeitoPixel(_cores_efeito((1.0, 0.16, 0.12)), dur + 0.04, forma, on_fim=chegou))
    except Exception as e:
        print(f"[cena] projetil: {e}")
        chegou()


def _racha_chao(camada, x, chao, te, larg=320, n=7, atras=None):
    """O chao racha em brasa em volta de um impacto e fica aceso um tempo."""
    try:
        u = te * 2
        rach = _rachaduras(x, chao - 34 * te, x - larg * te / 2.0, chao - 70 * te, larg * te, 70 * te, u, n=n,
                           semente=int(x) % 97 + 3)
        w = _PixelsBrasa(rach, u, cresce=0.14, fica=1.7, some=0.7, grossura=1)
        i = camada.children.index(atras) + 1 if atras is not None and atras in camada.children else 0
        camada.add_widget(w, index=i)
    except Exception as e:
        print(f"[cena] racha: {e}")


def _talho_x(camada, x, y, te, tam=26, cls=None):
    """Um X de luz no ponto do acerto (dois riscos curtos que crescem e somem)."""
    try:
        u = te * 2
        d = tam * te
        linhas = [_reta_pixels(x - d, y - d * 0.6, x + d, y + d * 0.6, u), _reta_pixels(x - d, y + d * 0.6, x + d, y - d * 0.6, u)]
        camada.add_widget((cls or _PixelsLuz)(linhas, u, cresce=0.05, fica=0.08, some=0.12, grossura=1))
    except Exception as e:
        print(f"[cena] talho: {e}")


def _brasas_para_letras(camada, alvos, origem, dur, on_chega, on_fim=None):
    """As brasas do chefe viram a frase: de pontos espalhados dentro de
    `origem` (x0, y0, x1, y1) sai uma brasa para cada letra (alvos = [(i, x,
    y)]), em arco, uma depois da outra; on_chega(i) quando cada uma chega."""
    rnd = random.Random(7)
    x0, y0, x1, y1 = origem
    n = max(1, len(alvos))
    voo = dur * 0.55
    passo = (dur - voo) / n
    pts = [(rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(-1, 1)) for _ in alvos]
    chegou = [False] * n

    def forma(t, p, u):
        for k, (i, ax, ay) in enumerate(alvos):
            tl = t - k * passo
            if tl < 0:
                continue
            if tl >= voo:
                if not chegou[k]:
                    chegou[k] = True
                    on_chega(i)
                continue
            f = tl / voo
            sx, sy, lado = pts[k]
            for j, nome in enumerate(('luz', 'clara', 'cor', 'cor', 'brilho')):   # a ponta e a cauda
                fj = max(0.0, f - j * 0.06)
                e = fj * fj * (3 - 2 * fj)
                x = sx + (ax - sx) * e + math.sin(math.pi * fj) * lado * u * 26
                y = sy + (ay - sy) * e + math.sin(math.pi * fj) * u * 34
                g = u * (3 if j < 2 else 2)
                p.setdefault(nome, []).append((math.floor(x / u) * u, math.floor(y / u) * u, g, g))

    def _fim():
        for k, (i, _x, _y) in enumerate(alvos):
            if not chegou[k]:
                chegou[k] = True
                on_chega(i)
        if on_fim:
            on_fim()
    camada.add_widget(_EfeitoPixel(_cores_efeito((1.0, 0.3, 0.16)), dur + 0.05, forma, on_fim=_fim))


def _sombra_chao(camada, x, y, r0, r1, dur, u):
    """A sombra do chefe crescendo no chao enquanto ele cai do ceu (elipse
    achatada em xadrez, que escurece no fim)."""
    try:
        def forma(t, p, uu):
            k = min(1.0, t / dur)
            r = r0 + (r1 - r0) * k * k
            ry = max(u, r * 0.16)
            cheia = k > 0.7
            gx0, gx1 = int((x - r) / u), int((x + r) / u)
            for gy in range(int((y - ry) / u), int((y + ry) / u) + 1):
                yy = (gy + 0.5) * u - y
                for gx in range(gx0, gx1 + 1):
                    xx = (gx + 0.5) * u - x
                    if (xx / r) ** 2 + (yy / ry) ** 2 <= 1.0 and (cheia or (gx + gy) % 2 == 0):
                        p.setdefault('s', []).append((gx * u, gy * u, u, u))
        camada.add_widget(_EfeitoPixel((('s', (0.0, 0.0, 0.0, 0.85)),), dur, forma), index=len(camada.children) - 1)
    except Exception as e:
        print(f"[cena] sombra: {e}")


def cena_titulo(tela, label, on_fim=None, texto="TRAVETE FOCUS"):
    """A LUTA: o CHEFE (chefe.py, "THE ABYSS WARDEN") se ergue do chao e
    ruge; o Yoru cai do alto, espera o montante descer, passa por baixo dele
    num iai e emenda quatro golpes (subindo pelo peito, mergulhando com as
    duas espadas, fugindo da garra e voltando num X) - a barra de vida do
    chefe despenca. Ele cai de joelho... e se levanta em furia, jogando o
    Yoru para tras. BAN-KAI: a transformacao, a escuridao, e UM corte na
    altura da frase parte o chefe ao meio (ele vira cacos) e grava TRAVETE
    FOCUS. O Yoru volta ao normal, pousa na frase, guarda as espadas - a
    frase explode - e da as boas-vindas."""
    fim = _Uma(on_fim)
    camada = Widget(size_hint=(None, None), size=tela.size, pos=(0, 0))
    ag = _Agenda()
    camada._agenda = ag
    cam = [None]
    estado = {'reator': None, 'aura': None}

    def restaurar_fundo():
        try:
            if cam[0] is not None:
                cam[0].soltar()
            r = estado['reator']
            if r is not None and r.opacity < 0.99 and not getattr(r, '_absorvido', False):
                r.restaurar()
                _fundo(tela, reator=1.0, barra=1.0, dur=0.3)
        except Exception as e:
            print(f"[cena] restaurar fundo: {e}")

    camada._restaurar = restaurar_fundo

    def encerrar():
        ag.parar()
        K.definir_ambiente('')
        if cam[0] is not None:
            cam[0].soltar()
        try:
            r = estado.get('reator')
            if r is not None and estado.get('texto_reator'):
                r.texto = estado.pop('texto_reator')            # o LOADING volta com a tela de carga
        except Exception as e:
            print(f"[cena] texto do fundo: {e}")
        try:
            c = estado.get('chefe')
            if c is not None:
                c.parar()
            import chefe as _ch
            _ch.soltar_texturas()
        except Exception as e:
            print(f"[cena] soltar chefe: {e}")
        fim()

    try:
        tela.add_widget(camada)
        W, H = tela.size
        area = (0.0, 0.0, float(W), float(H))
        wx, wy = label.to_window(label.x, label.y)
        lx, ly = tela.to_widget(wx, wy)
        titulo = TituloLuz(texto, label.font_size, pos=(lx, ly), size=label.size)
        camada.add_widget(titulo)
        camada._titulo = titulo
        faiscas = K.Faiscas(n_max=140)
        fundo_fx = K.Faiscas(n_max=50)                 # particulas atras do Kirito
        ps = _ps_titulo(titulo.th, W, H)
        kk = K.KiritoPixel(ps=ps)
        ps = kk.ps
        _PX[0] = ps / float(K.R)
        kk.opacity = 0
        aura = _AuraEspada(kk, faiscas)
        aura.faiscas_fundo = fundo_fx
        estado['aura'] = aura
        camada.add_widget(fundo_fx)
        estado['fitas'] = ()
        chamas = _ChamasBankai(kk, 3 * ps / float(K.R))   # chamas roxas do Bankai (atras dele)
        estado['chamas'] = chamas
        camada.add_widget(chamas)
        camada.add_widget(aura)
        camada.add_widget(K.RastroLamina(kk, faiscas))
        camada.add_widget(kk)
        camada.add_widget(faiscas)
        cam[0] = _Camera(tela)
        try:
            estado['reator'] = tela.ids.get('reator_shader')
        except Exception:
            estado['reator'] = None
        try:
            # o "LOADING..." do fundo nao faz parte da luta: fica guardado ate o fim
            r0 = estado['reator']
            if r0 is not None and getattr(r0, 'texto', ''):
                estado['texto_reator'] = r0.texto
                r0.texto = ''
        except Exception as e:
            print(f"[cena] texto do fundo: {e}")
        alt = 24 * ps
        th = titulo.th
        m = max(dp(4), ps)                              # folga ate a borda do quadro
        P = K.POSE_A
        # Bankai (estilo Mugetsu): da fusao ate o golpe final ele fica na
        # sombra, envolto em chamas roxas e azuis, com o cabelo comprido
        M = {n: _com(P[n], mugetsu=True) for n in ('fund_alto', 'evo_alto', 'evo_carga',
                                                    'evo_corte', 'evo_fim')}
        K.definir_ambiente('brasa')                        # na luta ele reflete a lua e a brasa do chefe
        kk.precarregar([P[n] for n in P] + list(M.values()))
        _precarregar_sons(_SONS_TITULO)
        ox_t, oy_t = titulo._origem()
        pe = kk.extensao(P['guardado'])[1] - ps         # ancora -> sola da bota
        # a luta acontece EM CIMA das letras (elas ficam sempre a vista)
        y_topo = oy_t + th * 0.82 + pe

        def quadro(x, y, poses):
            return _no_quadro(kk, x, y, [P[n] if isinstance(n, str) else n for n in poses], area, m)

        def corte_trecho(i, cor, sentido=1, som_corte='corte', cor2=None, arco=None,
                         achat=0.42):
            i0, i1 = _TRECHOS[i]
            cx, cy = titulo.x_do_trecho(i0, i1)
            larg = max(titulo._larg[i1] - titulo._larg[i0], th)
            a0, a1 = arco or ((160, -150) if sentido > 0 else (20, 330))
            camada.add_widget(CorteMeiaLua(centro=(cx, cy), raio=larg * 0.95, ang_ini=a0,
                                           ang_fim=a1, espessura=th * 0.9, achat=achat, cor=cor))
            if cor2 is not None:           # a segunda lamina: meia-lua junto, um pouco defasada
                d = 22 if a1 > a0 else -22
                camada.add_widget(CorteMeiaLua(centro=(cx, cy - th * 0.08), raio=larg * 0.82,
                                               ang_ini=a0 - d, ang_fim=a1 - d,
                                               espessura=th * 0.7, achat=achat, cor=cor2))
                _som('corte2')
            titulo.revelar(i0, i1, cor=(1, 1, 1) if cor == CIANO else AZUL)
            faiscas.estourar(cx, cy, cor, n=18, forca=dp(170), tam=ps)
            _estrela(camada, cx, cy, ps, cor)
            _som(som_corte)
            _tremer(6)
            _brilho_tela(camada, 0.10, 0.12)
            kk.impacto()
            kk.pausar(0.07)                              # hit-stop
            kk.empurrar(capa=16, cabelo=14)

        def poeira(x, y, n=10):
            faiscas.estourar(x, y, POEIRA, n=n, forca=dp(90), tam=max(2, ps * 0.8), gravidade=dp(300))

        # ── 1-5. A LUTA CONTRA O CHEFE ───────────────────────────────
        kk.espelhar = False                                # o Yoru comeca olhando para a direita
        te = ps / float(K.R)
        oficina = OficinaCortes(te * max(1, int(round(2.4 / te))))
        estado['oficina'] = oficina
        VIS = [(0, 3), (3, 5), (5, 7), (8, 10), (10, 13)]      # letras de cada silaba (sem o espaco)

        def silaba(i):
            a, b = VIS[i]
            x0, x1 = ox_t + titulo._larg[a], ox_t + titulo._larg[b]
            return (x0 + x1) / 2.0, oy_t + th * 0.5, x1 - x0

        ARCOS = {}
        COR_PAL = {'katana': CIANO, 'azul': AZUL, 'mug': ROXO}

        def ponta(pose, anc, qual=1):
            """Ponta da lamina `qual` da pose com a ancora em `anc`."""
            tx, ty = kk._local_texel(*K.maos_texel(pose, qual)[1])
            ax, ay = kk.ancora_local()
            return anc[0] + tx - ax, anc[1] + ty - ay

        def arco_do_golpe(arma, corta, a0, a1, qual, esp):
            """Arco da ponta da lamina `qual`: passa pela ponta na pose `arma`
            (ancora a0), no meio do golpe e na pose `corta` (ancora a1) - o
            mesmo caminho que a lamina do desenho faz."""
            meio = K.misturar(arma, corta, 0.5, 0.5)
            am = ((a0[0] + a1[0]) / 2.0, (a0[1] + a1[1]) / 2.0)
            return ArcoCorte.por_tres(ponta(arma, a0, qual), ponta(meio, am, qual),
                                      ponta(corta, a1, qual), esp)

        def arco(chave, arma, corta, a0, a1, qual=1, esp=None, pal='katana'):
            """Prepara (antes da hora) a luz do golpe `chave`."""
            ARCOS[chave] = (arco_do_golpe(arma, corta, a0, a1, qual, esp or th), pal)
            oficina.pedir(chave, ARCOS[chave][0], pal)

        def golpear(chave, dur=0.16, on_meio=None, som=None):
            """Solta a luz do golpe `chave` pelo caminho da lamina (contra o chefe)."""
            a, pal = ARCOS[chave]
            cor = COR_PAL[pal]
            ult = [0.0]
            meio = [on_meio]

            def _passo(s):
                if s - ult[0] > 0.1 and s < 1.0:
                    ult[0] = s
                    x, y = a.ponto(s, -0.4 * a.esp)
                    faiscas.estourar(x, y, cor, n=2, forca=dp(120), tam=max(2, te * 2), gravidade=dp(200))
                if meio[0] is not None and s >= 0.5:
                    fn, meio[0] = meio[0], None
                    fn()
            if som:
                _som(som)
            mancha = oficina.obter(chave)
            if mancha is None:
                _passo(1.0)
                return
            camada.add_widget(CorteGravado(a, mancha, dur=dur, k=kk, on_passo=_passo))

        def cortar(chave, i, dur=0.12, on_meio=None, som=None, letras=False):
            """Solta o arco `chave` e grava a silaba i por onde ele passa.
            letras=True: cada letra ja escrita acende quando a luz passa."""
            a, pal = ARCOS[chave]
            i0, i1 = _TRECHOS[i]
            grava = titulo.gravar_arco(i0, i1, a, th * 0.95)
            cor = COR_PAL[pal]
            ult = [0.0]
            meio = [on_meio]
            acesas = set()

            def _passo(s):
                grava(s)
                if s - ult[0] > 0.1 and s < 1.0:
                    ult[0] = s
                    x, y = a.ponto(s, -0.4 * a.esp)
                    faiscas.estourar(x, y, cor, n=2, forca=dp(120), tam=max(2, te * 2),
                                     gravidade=dp(200))
                if meio[0] is not None and s >= 0.5:
                    fn, meio[0] = meio[0], None
                    fn()
                if letras:
                    hx = a.ponto(min(s, 1.0))[0]
                    for li in range(len(texto)):
                        if li not in acesas and texto[li].strip() and \
                                ox_t + (titulo._larg[li] + titulo._larg[li + 1]) / 2.0 <= hx:
                            acesas.add(li)
                            titulo.gravar(li, li + 1)
            if som:
                _som(som)
            mancha = oficina.obter(chave)
            if mancha is None:
                _passo(1.0)
                return
            camada.add_widget(CorteGravado(a, mancha, dur=dur, k=kk, on_passo=_passo))

        def sem_rastro(chaves):
            return [(ch[0], _com(ch[1], s1=None, s2=None)) + tuple(ch[2:]) for ch in chaves]

        pronto = _com(P['saca0'], olhos='s')
        agacha = _com(P['agacha'], olhos='s')
        corta_tra = _com(P['corta1'], olhos='g')
        arma_ve = _com(P['salto_arma'], olhos='s')
        corta_ve = _com(P['salto'], olhos='g', a1=P['salto']['a1'] + 360)   # sobe pela frente
        fim_ve = _com(P['salto_fim'], olhos='s', a1=_perto(P['salto_fim']['a1'], corta_ve['a1']))
        pega_az = K.encolhido(_com(P['pega2'], olhos='s'))
        saca_az = K.encolhido(_com(P['saca2'], olhos='s'))
        arma_te = _com(P['desce_arma'], olhos='s')
        corta_te = _com(P['desce_corta'], olhos='g')
        arma_fo = K.encolhido(_com(P['c3_corta'], olhos='s'))      # as duas no alto, cruzadas
        corta_fo = _com(P['c3_arma'], olhos='g', a2=P['c3_arma']['a2'] - 360)   # descem abrindo em X
        prep_fo = _com(P['agacha'], olhos='s', m1=(3, 2), a1=150.0, m2=(-3, 3), a2=60.0)
        guarda2 = _com(P['dupla'], olhos='s')

        # O CHEFE (o modelo do usuario, 405 pontos de altura): comeca do lado
        # direito, virado para o Yoru. O chao da luta fica 200 pontos ABAIXO da
        # frase (que so aparece no fim): ela passa na cintura dele - o corte do
        # Bankai, na altura das letras, parte o chefe ao meio. Sobra o ceu
        # inteiro em cima (o salto do chefe usa) e o chao em baixo.
        import chefe as CH
        CH.dados()
        CH.aquecer(por_quadro=3)
        _, cy_t, _ = silaba(0)
        chao = max(m + 6 * te, cy_t - 200 * te)
        y_luta = chao + pe
        bx = min(W - m - 215 * te, max(W * 0.66, W * 0.5 + 110 * te))
        bxl = max(m + 170 * te, W * 0.30)                  # onde ele cai do salto (do lado esquerdo)
        boss = CH.ChefePixel(te=te)
        boss.ancorar(bx, chao)
        boss.opacity = 0
        camada.add_widget(boss, index=camada.children.index(titulo))    # atras do Yoru e dos efeitos
        estado['chefe'] = boss
        frente = bx - 58 * te                              # onde comeca o corpo dele (do lado do Yoru)
        barra_c = _BarraChefe('THE ABYSS WARDEN', W / 2.0, min(H - m - 12 * te, chao + 470 * te),
                              min(W * 0.62, 260 * te), te * 2)
        camada.add_widget(barra_c)
        estado['barra_chefe'] = barra_c
        # o cenario do desenho dele (lua em eclipse, castelo, chao em brasa) atras de tudo
        cen = _CenarioChefe(W, H, chao)
        camada.add_widget(cen, index=len(camada.children))
        estado['cenario'] = cen
        cine = _FaixasCinema(W, H)                          # as faixas pretas de cinema
        camada.add_widget(cine)
        VIDA = {1: 0.88, 2: 0.76, 3: 0.58, 4: 0.53, 5: 0.48, 6: 0.43, 7: 0.38, 8: 0.22, 9: 0.06}
        brasas = K.Faiscas(n_max=110)                       # o fogo do chefe e as cinzas do chao (atras do Yoru)
        camada.add_widget(brasas, index=camada.children.index(boss))
        SANGUE = (1.0, 0.2, 0.12)

        def _vida_chefe(dt):
            try:
                if estado.get('chefe_morto'):
                    return False
                if cen.f > 0.9:                             # cinzas subindo das fendas do chao
                    brasas.estourar(random.uniform(0, W), chao - random.uniform(4, 150) * te,
                                    random.choice((BRASA, SANGUE)), n=1, forca=dp(14), tam=te * random.choice((2, 3, 4)),
                                    gravidade=-dp(random.uniform(40, 110)))
                if boss.opacity > 0 and boss._pontos is not None:
                    mx_, my_ = boss.mao()
                    px_, py_ = boss.ponta()
                    for _ in range(2):                      # o fio do montante solta fogo
                        f = random.uniform(0.15, 1.0)
                        brasas.estourar(mx_ + (px_ - mx_) * f, my_ + (py_ - my_) * f,
                                        random.choice((BRASA, SANGUE, (1.0, 0.6, 0.25))), n=1, forca=dp(40),
                                        tam=te * random.choice((2, 3, 3, 4)), gravidade=-dp(210))
                    ox_, oy_ = boss.ponto('olho')            # a chama do olho
                    brasas.estourar(ox_ + random.uniform(0, 5) * te, oy_ + random.uniform(0, 4) * te,
                                    random.choice((SANGUE, BRASA)), n=1, forca=dp(12), tam=te * 3,
                                    gravidade=-dp(170))
            except Exception as e:
                print(f"[cena] vida do chefe: {e}")
            return True
        ag.cada(0.05, _vida_chefe)
        # o BANKAI e desenhado maior que o Yoru normal (cada ponto do desenho da
        # referencia vira 2x2): da para ver cabelo, casaco e espada. Os pes
        # continuam no mesmo chao (a ancora sobe a diferenca).
        ESC_BK = 2.0
        sobe_bk = 56.5 * te * (ESC_BK - 1.0)

        def boss_idle():
            boss.tocar('idle', loop=True)

        arma_el = _com(P['arma1'], olhos='s')               # o corte de cima para baixo (no elmo)
        corta_el = _com(P['corta_desce'], olhos='g')
        # onde o Yoru fica em cada golpe
        A0 = quadro(max(m + 30 * te, bx - 330 * te), y_luta, [pronto])   # onde ele pousa
        J1 = (frente - 96 * te, y_luta + 300 * te)                       # por cima da varrida
        J2 = (frente - 62 * te, y_luta + 218 * te)                       # o corte desce no elmo
        K0 = quadro(frente - 170 * te, y_luta, [pronto])                 # de frente para ele, a distancia
        A1 = quadro(frente - 22 * te, y_luta, [corta_tra])               # colado no chefe
        B1 = (frente - 4 * te, y_luta + 250 * te)                        # sobe rente ao peito
        C0 = (frente - 50 * te, y_luta + 360 * te)                       # no alto, na cara dele
        C1 = quadro(frente - 14 * te, y_luta, [corta_te])                # desce rasgando o nucleo
        R0 = quadro(W - m - 70 * te, y_luta, [guarda2])                  # do lado direito (o chefe caiu no esquerdo)
        Xm = ((bxl + bx) / 2.0 + 20 * te, y_luta + 430 * te)             # por cima da investida
        X1 = (frente - 30 * te, y_luta + 150 * te)                       # o X desce nas costas dele
        E0 = quadro(max(m + 20 * te, A0[0] - 16 * te), y_luta, [guarda2])  # jogado para tras: daqui o BAN-KAI
        arco('h1', arma_el, corta_el, J1, J2, 1, th * 1.0)
        arco('dfl', pronto, corta_tra, K0, A1, 1, th * 1.0)
        arco('h2', arma_ve, corta_ve, A1, B1, 1, th * 0.95)
        arco('h3', arma_te, corta_te, C0, C1, 1, th * 0.95)
        arco('h3b', arma_te, corta_te, C0, C1, 2, th * 0.75, 'azul')
        arco('h4', arma_fo, corta_fo, Xm, X1, 1, th * 0.9)
        arco('h4b', arma_fo, corta_fo, Xm, X1, 2, th * 0.85, 'azul')
        # o do Bankai atravessa a frase inteira, de um lado ao outro da tela
        ARCOS['cus'] = (ArcoCorte.pelo_meio((ox_t + titulo.tw / 2.0, cy_t), 0, W * 1.02, -0.05,
                                            th * 1.35), 'mug')
        oficina.pedir('cus', ARCOS['cus'][0], 'mug')
        # o revide do Bankai (do alto, descendo na cabeca do chefe)
        ARCOS['ctr'] = (ArcoCorte.por_tres((E0[0] + 60 * te, chao + 480 * te), (frente - 90 * te, chao + 470 * te),
                                           (frente + 14 * te, chao + 330 * te), th * 1.25), 'mug')
        oficina.pedir('ctr', ARCOS['ctr'][0], 'mug')
        kk.precarregar([pronto, agacha, corta_tra, arma_ve, corta_ve, fim_ve, pega_az, saca_az,
                        arma_te, corta_te, arma_fo, corta_fo, prep_fo, guarda2, arma_el, corta_el])

        # golpes: prepara, segura, a lamina gira em quadros de rastro,
        # acompanha e volta com molinha
        G = dict(n_arma=3, prende=3, segue=3, volta=5, meios=(0.25, 0.5, 0.75))
        GIRO = len(G['meios'])                   # o corpo e a luz saem no 1o quadro de rastro

        def _voo_seq(p_ini, p_ar, p_fim, dur):
            """Poses de um salto com a duracao do voo: sai esticado, fecha
            na bola (segura enquanto gira) e abre de novo para pousar."""
            n = max(6, int(round(dur * K.FPS)))
            a = max(2, int(n * 0.22))
            c = max(2, int(n * 0.25))
            b = max(2, n - a - c)
            return K.sequencia([(a, p_ini, 'out'), (b, p_ar, 'segura'), (c, p_ar, 'out'), (1, p_fim)])

        def acerta(n, onde=None, forte=False, reage=True, leve=False, cor=CIANO):
            """Um golpe do Yoru pegou no chefe: quadros brancos, faiscas, a
            barra de vida cai e ele acusa o golpe. leve = golpe de uma rajada
            (sem congelar a cena)."""
            x, y = onde or boss.ponto('nucleo')
            boss.impacto(quadros=2 if leve else (5 if forte else 3), tremor=3 if leve else (8 if forte else 5))
            kk.impacto(forte=forte)
            if not leve:
                boss.pausar(0.11 if forte else 0.07)
                kk.pausar(0.09 if forte else 0.06)
                _som('corte')
                _brilho_tela(camada, 0.10, 0.1)
            _estrela(camada, x, y, ps, BRANCO, raios=4 if leve else (7 if forte else 5))
            _talho_x(camada, x, y, te, 16 if leve else (34 if forte else 24), _PixelsRoxo if cor == ROXO else None)
            if not leve:                                     # a lava espirra da ferida, para o lado do Yoru
                lado = -1 if kk.ancora()[0] < x else 1
                for _ in range(10 if forte else 6):
                    brasas.estourar(x + lado * random.uniform(0, 30) * te, y + random.uniform(-14, 14) * te,
                                    random.choice((SANGUE, BRASA)), n=1, forca=dp(60), tam=te * 3,
                                    gravidade=dp(520))
            faiscas.estourar(x, y, BRASA, n=8 if leve else (24 if forte else 14), forca=dp(220), tam=ps)
            faiscas.estourar(x, y, cor, n=5 if leve else 8, forca=dp(150), tam=ps)
            _tremer(5 if leve else (16 if forte else 8))
            barra_c.dano(VIDA[n])
            kk.empurrar(capa=14, cabelo=12)
            if reage:
                boss.tocar('apanha', on_fim=boss_idle)

        def _vida_yoru(dt):
            try:
                if kk.opacity <= 0 or estado.get('chefe_morto'):
                    return True
                ax_, ay_ = kk.ancora()
                ant = estado.get('yoru_ant', (ax_, ay_))
                estado['yoru_ant'] = (ax_, ay_)
                if math.hypot(ax_ - ant[0], ay_ - ant[1]) > te * 10:      # so quando ele esta voando
                    tx_, ty_ = kk.ponta_espada(1)
                    faiscas.estourar(tx_, ty_, ROXO if kk._desenho is not None else CIANO, n=2, forca=dp(40),
                                     tam=te * 2, gravidade=dp(60))
            except Exception as e:
                print(f"[cena] vida do yoru: {e}")
            return True
        ag.cada(0.04, _vida_yoru)

        def soco_camera(foco, zoom=1.1, volta=0.35):
            """A camera da um tranco para perto do golpe e volta."""
            cam[0].ir(1.0 + (zoom - 1.0) * 2.4, foco=foco, dur=0.07)
            ag.depois(0.16, lambda: cam[0].ir(1.0, dur=volta))

        def cam_em(zoom, foco=None, dur=0.4):
            cam[0].ir(zoom, foco=foco, dur=dur)

        def mover_chefe(de, para, dur, ease='linear', on_fim=None):
            """Leva os pes do chefe de `de` ate `para` (em passos de pixel, 30 por segundo)."""
            t = [0.0]
            fim_ = _Uma(on_fim)

            def _p(dt):
                t[0] += dt
                u = min(1.0, t[0] / max(0.01, dur))
                e = u * u if ease == 'in' else (1 - (1 - u) ** 2 if ease == 'out' else u)
                d = math.floor(u * dur * 30) / max(1.0, dur * 30) if u < 1 else 1.0
                e = d * d if ease == 'in' else (1 - (1 - d) ** 2 if ease == 'out' else d)
                boss.ancorar(round(de[0] + (para[0] - de[0]) * e), round(de[1] + (para[1] - de[1]) * e))
                if u >= 1.0:
                    fim_()
                    return False
                return True
            ag.cada(1 / 60., _p)

        # ── 1) o cenario abre do horizonte, o chefe se ergue do chao e ruge ──
        def _abre_cena():
            _fundo(tela, reator=0.0, barra=0.0, dur=0.3)
            cen.abrir(0.7)
            cine.entrar()
        ag.depois(0.15, _abre_cena)

        def _chefe_surge():
            boss_idle()
            _som('trevas')
            _tremer(12)
            faiscas.estourar(bx, chao, BRASA, n=22, forca=dp(190), tam=ps, gravidade=-dp(120))
            cam[0].ir(1.2, foco=(bx - 30 * te, chao + 300 * te), dur=1.4)       # a camera sobe pelo corpo dele
            _surgir_chefe(boss, camada, 0.9, on_fim=lambda: ag.depois(0.15, _ruge))
            ag.depois(0.7, barra_c.mostrar)
        ag.depois(0.95, _chefe_surge)

        def _berro(i):
            if i == 14:                                      # a cabeca foi para tras: o berro
                ox_, oy_ = boss.ponto('cabeca')
                _som('rugido')
                _tremer(26)
                cam[0].ir(1.0, dur=0.3)
                _anel(camada, (ox_ - 20 * te, oy_ - 8 * te), te * 10, te * 330, 0.55, BRASA, esp=dp(6), grao=3)
                _brilho_tela(camada, 0.22, 0.3, (1.0, 0.25, 0.16), atras=boss)
                faiscas.estourar(ox_ - 22 * te, oy_, BRASA, n=26, forca=dp(260), tam=ps)

        def _ruge():
            boss.tocar('rugido', on_quadro=_berro, on_fim=boss_idle)
            # close de anime: o elmo dele, os olhos e os dentes acesos
            ag.depois(0.95, lambda: _close_chefe(camada, boss, dur=0.75, y_rel=0.6))
            ag.depois(1.8, _entra)

        # ── 2) o Yoru despenca do alto da tela e pousa na frente dele ──
        def _entra():
            p_pulo = _com(P['pulo'], olhos='s')
            ini = (A0[0] - th * 1.2, H + alt * 0.6)
            kk.ancorar(*ini)
            kk.opacity = 1
            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), K.esticado(p_pulo), 0.75))
            _som('pulo')
            kk.empurrar(capa=-8, cabelo=-6, lift=10)
            _linhas_velocidade(camada, 0.7, CIANO, vertical=True, x0=A0[0] - 90 * te, x1=A0[0] + 90 * te, n=14)
            _mover(kk, ini, A0, 0.75, rot=(0, -360), fantasmas=4, ease='in', on_fim=_pousa,
                   rot_janela=(0.2, 0.75))

        def _pousa():
            kk.rotacao = 0
            _som('pouso')
            ax, ay = kk.ancora()
            poeira(ax, ay - kk.extensao()[1], n=14)
            _anel(camada, (ax, chao + te * 2), te * 4, te * 70, 0.3, CIANO, esp=dp(2), achat=0.3)
            _tremer(8)
            cine.sair()
            kk.empurrar(lift=-10, capa=-6)
            kk.tocar(K.sequencia(_de_agora(kk, 1) + [(2, _com(agacha, estica=-1), 'segura'),
                                                      (4, agacha, 'out'), (4, pronto, 'suave'),
                                                      (1, pronto)]))
            cam_em(1.55, foco=(ax + 40 * te, ay + 60 * te), dur=0.35)      # a camera vai ate ele
            ag.depois(0.95, lambda: cam_em(1.0, dur=0.3))
            # close de anime: o olho dele, com a mao no cabo
            ag.depois(0.1, lambda: _som('fala_ikuzo'))
            ag.depois(0.12, lambda: close_rosto(camada, 'normal', dur=0.7, y_rel=0.84,
                                                espelhar=kk.espelhar,
                                                on_fim=lambda: ag.depois(0.02, _luta1)))

        # ── 3) VARRIDA: o montante vem de tras raspando o chao; o Yoru salta
        #    por cima dela num mortal e desce cortando o elmo (golpe 1) ──
        def _luta1():
            def _q(i):
                if i == 12:
                    _salta_varrida()
                elif i == 17:                               # a lamina passa raspando o chao
                    mx_, my_ = boss.mao()
                    _som('corte2')
                    _tremer(14)
                    camada.add_widget(CorteMeiaLua(centro=(mx_, my_), raio=te * 250, ang_ini=300, ang_fim=165,
                                                   espessura=te * 60, achat=1.0, cor=BRASA,
                                                   dur_cheio=4 / 30.0, dur_decai=6 / 30.0))
                    _racha_chao(camada, frente - 130 * te, chao, te, larg=300, n=6, atras=boss)
                    for k_ in range(5):
                        poeira(frente - (40 + 50 * k_) * te, chao, n=4)
                    faiscas.estourar(frente - 120 * te, chao, BRASA, n=20, forca=dp(240), tam=ps)
            boss.tocar('varrida', on_quadro=_q, on_fim=boss_idle)

        def _salta_varrida():
            p_pulo = _com(P['pulo'], olhos='s')
            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), arma_el, 0.4))
            _som('pulo')
            kk.empurrar(capa=-8, lift=10)
            _mover(kk, kk.ancora(), J1, 0.4, altura=te * 60, rot=(0, -360), fantasmas=3, ease='out',
                   on_fim=_corta_elmo, rot_janela=(0.15, 0.8))

        def _corta_elmo():
            kk.rotacao = 0
            chaves, i_r = K.golpe(arma_el, corta_el, seg=P['segue_desce'], **dict(G, n_arma=1, prende=1, volta=3))

            def _q(i):
                if i == i_r - GIRO:
                    _gemido(forte=True)
                    kk.empurrar(capa=12, lift=6)
                    _mover(kk, kk.ancora(), J2, 0.14, ease='in', fantasmas=2)
                    cab_ = boss.ponto('cabeca')
                    golpear('h1', dur=0.16, on_meio=lambda: (acerta(1, cab_, forte=True), soco_camera(cab_, 1.12)))
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_cai_do_elmo)

        def _cai_do_elmo():
            p_pulo = _com(P['pulo'], olhos='s')
            kk.tocar(_voo_seq(K.esticado(p_pulo), K.encolhido(p_pulo), pronto, 0.36))

            def _chegou():
                _som('pouso')
                bx_, by_ = kk.ancora()
                poeira(bx_, by_ - kk.extensao()[1], n=8)
                kk.empurrar(lift=-8, capa=-6)
                kk.tocar(K.sequencia([(2, _com(agacha, estica=-1), 'out'), (3, pronto, 'out'), (1, pronto)]))
                ag.depois(0.22, _aparado)
            _mover(kk, kk.ancora(), K0, 0.36, altura=te * 30, fantasmas=1, on_fim=_chegou)

        # ── 3b) DEFESA: o Yoru emenda um avanco... e o chefe atravessa o
        #    montante na frente do corpo: a lamina bate e ele e jogado de volta ──
        def _aparado():
            boss.tocar('defesa', on_fim=boss_idle)
            perto = (frente - 64 * te, y_luta + 150 * te)       # salta: a lamina dele encontra o montante atravessado
            kk.tocar(K.sequencia([(2, pronto, 'segura'), (1, K.smear(corta_tra, pronto['a1']), 'segura'),
                                  (6, corta_tra, 'segura'), (1, corta_tra)]))
            _som('sacar_iai')
            _gemido()

            def _bateu():
                mx_, my_ = boss.mao()
                px_, py_ = mx_ - 8 * te, my_ + 34 * te
                kk.impacto(forte=True)
                kk.pausar(0.1)
                boss.pausar(0.1)
                _som('golpe_final')
                _som('koiguchi')
                _tremer(14)
                _estrela(camada, px_, py_, ps * 2, BRANCO, raios=8, dur=0.2)
                _anel(camada, (px_, py_), te * 6, te * 70, 0.25, BRANCO, esp=dp(2))
                faiscas.estourar(px_, py_, BRANCO, n=22, forca=dp(300), tam=ps)
                faiscas.estourar(px_, py_, BRASA, n=16, forca=dp(240), tam=ps)
                soco_camera((px_, py_), 1.1, 0.3)

                def _volta():
                    kk.tocar(K.sequencia([(3, _com(guarda2, pernas='recua', estica=-1), 'segura'),
                                          (5, _com(pronto, pernas='recua'), 'out'), (1, pronto)]))
                    _som('desliza')
                    _mover(kk, kk.ancora(), K0, 0.34, altura=te * 40, fantasmas=2,
                           on_fim=lambda: (poeira(K0[0], chao, n=8), _som('pouso'), ag.depois(0.25, _projetil)))
                ag.depois(0.14, _volta)
            _mover(kk, kk.ancora(), perto, 0.14, altura=te * 30, fantasmas=3, cor_fantasma=CIANO, on_fim=_bateu)

        # ── 4) PROJETIL: ele nivela o montante e dispara um raio de sangue; o
        #    Yoru corta o raio ao meio num iai e ja emenda: sobe cortando o
        #    peito (golpe 2), saca a azul no alto e mergulha no nucleo (golpe 3) ──
        def _projetil():
            cine.entrar()
            cam_em(1.25, foco=((K0[0] + bx) / 2.0, chao + 170 * te), dur=0.5)   # os dois no quadro, de perto
            ag.depois(0.95, lambda: cam_em(1.0, dur=0.25))

            def _q(i):
                if i == 12:
                    px_, py_ = boss.ponta()
                    _anel(camada, (px_, py_), te * 40, te * 6, 0.3, BRASA, esp=dp(3))     # junta energia na ponta
                elif i == 20:
                    _dispara()
            boss.tocar('aponta', on_quadro=_q, on_fim=boss_idle)

        def _dispara():
            px_, py_ = boss.ponta()
            alvo = (K0[0] + 34 * te, y_luta + 62 * te)
            _som('getsuga')
            _tremer(12)
            _estrela(camada, px_, py_, ps * 2, BRASA, raios=8, dur=0.2)
            _projetil_sangue(camada, (px_, py_), alvo, 0.3, te, on_chega=_rebate)
            chaves, i_r = K.golpe(pronto, corta_tra, lamina_recua=False, seg=P['segue1'],
                                  **dict(G, n_arma=2, prende=2))

            def _q(i):
                if i == i_r - GIRO:
                    _som('sacar_iai')
                    _gemido()
                    _mover(kk, kk.ancora(), A1, 0.24, ease='out', fantasmas=3, limite=(area, m))
                    golpear('dfl', dur=0.16)
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_sobe)

        def _rebate(x, y):
            # o raio se parte na lamina: duas metades voam para cima e para baixo
            kk.impacto(forte=True)
            kk.pausar(0.08)
            _som('vidro')
            _tremer(14)
            _brilho_tela(camada, 0.2, 0.15, (1.0, 0.4, 0.3))
            _estrela(camada, x, y, ps * 2, BRANCO, raios=8, dur=0.2)
            _anel(camada, (x, y), te * 6, te * 90, 0.3, BRASA, esp=dp(3))
            faiscas.estourar(x, y, BRASA, n=30, forca=dp(300), tam=ps)
            for sy in (1, -1):
                _projetil_sangue(camada, (x, y), (x - 210 * te, y + sy * 250 * te), 0.28, te, pequeno=True)

        def _sobe():
            chaves, i_r = K.golpe(arma_ve, corta_ve, seg=fim_ve, **dict(G, n_arma=2, prende=2, volta=4))

            def _q(i):
                if i == i_r - GIRO:
                    _som('pulo')
                    _gemido()
                    kk.empurrar(capa=-10, lift=10)
                    _mover(kk, kk.ancora(), B1, 0.3, ease='out', fantasmas=3)
                    golpear('h2', dur=0.18, on_meio=lambda: acerta(2))
            seq0 = K.sequencia(_de_agora(kk, 3, proxima=arma_ve) + [(4, arma_ve, 'out'), (1, arma_ve)])
            kk.tocar(seq0, on_fim=lambda: kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q,
                                                   on_fim=_saca_azul))
            kk.empurrar(capa=-10, cabelo=-6)

        def _saca_azul():
            seq = K.sequencia(_de_agora(kk, 2, proxima=pega_az) +
                              [(3, pega_az, 'out'), (3, saca_az, 'out'), (5, saca_az, 'segura'),
                               (4, arma_te, 'out'), (1, arma_te)])

            def _q(i):
                if i == 5:
                    hx2, hy2 = kk.ponta_espada(2)
                    faiscas.estourar(hx2, hy2, AZUL, n=16, forca=dp(130), tam=ps)
                    _anel(camada, kk.ponto_mao(2), ps, ps * 8, 0.3, AZUL, esp=dp(3))
                    _som('sacar')
                    kk.empurrar(cabelo=8, lift=4)
            _mover(kk, kk.ancora(), C0, 0.56, ease='suave', fantasmas=0)
            kk.tocar(seq, on_quadro=_q, on_fim=_te)

        def _te():
            chaves, i_r = K.golpe(arma_te, corta_te, seg=corta_te, **dict(G, n_arma=2, prende=2, volta=3))

            def _q(i):
                if i == i_r - GIRO:
                    _gemido(forte=True)
                    kk.empurrar(capa=12, lift=6)
                    _mover(kk, kk.ancora(), C1, 0.28, ease='in', fantasmas=4, limite=(area, m))
                    nuc = boss.ponto('nucleo')
                    golpear('h3', dur=0.2, on_meio=lambda: (acerta(3, forte=True), soco_camera(nuc, 1.14)))
                    ag.depois(0.05, lambda: golpear('h3b', dur=0.2, som='corte2'))
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_recua)

        def _recua():
            # mortal para tras: ele sente que vem coisa
            ax, ay = kk.ancora()
            p_pulo = _com(P['pulo'], olhos='s')
            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), guarda2, 0.44))
            _som('pulo')

            def _chegou():
                kk.rotacao = 0
                _som('pouso')
                bx_, by_ = kk.ancora()
                poeira(bx_, by_ - kk.extensao()[1], n=8)
                kk.mostrar(guarda2)
            _mover(kk, (ax, ay), K0, 0.44, altura=te * 90, rot=(0, 360), fantasmas=2, on_fim=_chegou,
                   rot_janela=(0.2, 0.75))
            cine.sair()
            ag.depois(0.25, _salto)

        # ── 5) SALTO: o chefe agacha, some no ceu... a sombra cresce no chao;
        #    o Yoru dispara por baixo e o chefe desaba do outro lado ──
        def _salto():
            boss.tocar('salto_prep', on_fim=_decola)
            _som('carga')

        def _decola():
            boss.tocar('salto_ar', loop=True)
            _som('pulo')
            _tremer(16)
            poeira(bx, chao, n=18)
            _anel(camada, (bx, chao + te * 2), te * 6, te * 120, 0.35, BRASA, esp=dp(3), achat=0.3)
            mover_chefe((bx, chao), (bx - 90 * te, H + 120 * te), 0.34, ease='out', on_fim=_no_ceu)
            cam[0].ir(1.06, foco=(W / 2.0, chao + 500 * te), dur=0.3)           # a camera olha para cima
            ag.depois(0.12, lambda: emote(camada, kk, '!!', 0.5))

        def _no_ceu():
            _sombra_chao(camada, bxl, chao, te * 24, te * 170, 0.62, te * 4)
            cam[0].ir(1.0, dur=0.45)
            ag.depois(0.3, _foge)
            ag.depois(0.6, _desaba)

        def _foge():
            # passa por baixo da sombra num risco, para o outro lado da tela
            kk.espelhar = False
            kk.mostrar(_com(guarda2, pernas='avanco_baixo'))
            _som('desliza')
            _linhas_velocidade(camada, 0.3, CIANO, y0=chao, y1=chao + 190 * te, n=12)

            def _freou():
                kk.espelhar = True                          # vira para onde ele vai cair
                kk.mostrar(guarda2)
                bx_, by_ = kk.ancora()
                poeira(bx_, by_ - kk.extensao()[1], n=8)
            _mover(kk, kk.ancora(), R0, 0.22, linear=True, fantasmas=5, cor_fantasma=CIANO, on_fim=_freou)

        def _desaba():
            boss.espelhar = True                            # agora olha para a direita, onde o Yoru esta
            boss.tocar('salto_desce', loop=True)
            mover_chefe((bxl, H + 120 * te), (bxl, chao), 0.2, ease='in', on_fim=_impacto_salto)

        def _impacto_salto():
            boss.tocar('pouso', on_fim=boss_idle)
            _som('golpe_final')
            _som('trevas')
            _tremer(36)
            _anel(camada, (bxl, chao + te * 4), te * 12, te * 340, 0.55, BRASA, esp=dp(6), achat=0.3, grao=3)
            _anel(camada, (bxl, chao + te * 4), te * 6, te * 200, 0.4, BRANCO, esp=dp(3), achat=0.3, grao=2)
            _brilho_tela(camada, 0.3, 0.25, (1.0, 0.3, 0.2), atras=boss)
            for k_ in range(-3, 6):
                poeira(bxl + k_ * 45 * te, chao, n=6)
            faiscas.estourar(bxl, chao, BRASA, n=44, forca=dp(360), tam=ps, gravidade=dp(300))
            _racha_chao(camada, bxl, chao, te, larg=460, n=11, atras=boss)
            cen.tranco()
            soco_camera((bxl, chao + 60 * te), 1.1, 0.5)
            # o chao joga o Yoru para cima um instante
            _pulinhos(kk, guarda2, n=1, altura=te * 26)
            ag.depois(0.55, lambda: _rajada(0))

        # ── 6) RAJADA: ele ainda esta se levantando - quatro golpes seguidos,
        #    alternando as espadas; o chefe revida com a garra e o Yoru sai num mortal ──
        RAJADA = [('sb1_a', 'sb1_b', 1, (150, -40)), ('sb2_a', 'sb2_b', 2, (215, 40)),
                  ('sb3_a', 'sb3_b', 1, (175, 0)), ('sb4_a', 'sb4_b', 2, (185, -5))]

        def _rajada(j):
            if j == 0:
                cam_em(1.45, foco=(bxl + 110 * te, chao + 150 * te), dur=0.2)   # a rajada de perto
            if j >= len(RAJADA):
                cam_em(1.0, dur=0.3)
                kk.tocar(K.sequencia(_de_agora(kk, 2, 'out') + [(3, guarda2, 'out'), (1, guarda2)]))
                return _garra()
            a, c_, qual, arc = RAJADA[j]
            arma, corta = P[a], P[c_]
            sm = K.smear(corta, arma['a1'] if qual == 1 else None, arma['a2'] if qual == 2 else None)
            cor = CIANO if qual == 1 else AZUL
            kk.espelhar = True

            def _q(q):
                if q != 1:
                    return
                nx, ny = boss.ponto('nucleo')
                px_ = nx + 26 * te + random.uniform(-10, 10) * te
                py_ = ny + random.uniform(-70, 40) * te
                camada.add_widget(CorteMeiaLua(centro=(px_, py_), raio=th * 1.7, ang_ini=180 - arc[0],
                                               ang_fim=180 - arc[1], espessura=th * 0.9, achat=0.4, cor=cor,
                                               dur_cheio=3 / 30.0, dur_decai=4 / 30.0))
                acerta(4 + j, (px_, py_), reage=False, leve=True, cor=cor)
                _som('corte2' if qual == 2 else 'corte')
                if j % 2 == 0:
                    _gemido()
                kk.empurrar(capa=8, cabelo=6)
            kk.parar()
            kk.mostrar(arma)
            perto = (bxl + (150 - j * 8) * te, y_luta)
            _mover(kk, kk.ancora(), perto, 0.07 if j else 0.16, linear=True, fantasmas=2 if not j else 1,
                   cor_fantasma=cor,
                   on_fim=lambda: kk.tocar(K.sequencia([(1, arma, 'segura'), (1, sm, 'segura'),
                                                        (2, corta, 'segura'), (1, corta)]),
                                           on_quadro=_q, on_fim=lambda: _rajada(j + 1)))

        def _garra():
            def _q(i):
                if i == 11:
                    _foge_garra()
                elif i == 16:
                    gx_, gy_ = boss.garra()
                    _som('corte2')
                    _tremer(10)
                    for k_ in range(3):
                        camada.add_widget(CorteMeiaLua(centro=boss.ponto('ombro'), raio=te * (150 + 22 * k_),
                                                       ang_ini=130, ang_fim=-50, espessura=te * 8, achat=1.0,
                                                       cor=BRASA, dur_cheio=3 / 30.0, dur_decai=5 / 30.0))
                    faiscas.estourar(gx_, gy_, BRASA, n=14, forca=dp(200), tam=ps)
            boss.tocar('garra', on_quadro=_q, on_fim=_gira)

        # ── 6b) CORTE GIRATORIO: a lamina da a volta inteira em volta dele (um
        #    anel de fogo varre a tela); o Yoru salta por cima do anel ──
        def _gira():
            def _q(i):
                if i == 12:
                    # salta reto para cima, num mortal, e cai no mesmo lugar
                    p_pulo = _com(P['pulo'], olhos='s')
                    kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), guarda2, 0.62))
                    _som('pulo')
                    a0 = kk.ancora()
                    _mover(kk, a0, a0, 0.62, altura=te * 300, rot=(0, -360), fantasmas=2,
                           rot_janela=(0.2, 0.8),
                           on_fim=lambda: (setattr(kk, 'rotacao', 0), kk.mostrar(guarda2), _som('pouso'),
                                           poeira(a0[0], chao, n=8)))
                elif i == 16:
                    boss.espelhar = not boss.espelhar            # de costas: a lamina passa por tras
                    _fogo_em_volta()
                elif i == 20:
                    boss.espelhar = not boss.espelhar
            boss.tocar('giratorio', on_quadro=_q, on_fim=_investe)

        def _fogo_em_volta():
            cx_, cy_ = boss.ax, chao + 120 * te
            _som('getsuga')
            _som('corte2')
            _tremer(22)
            cen.tranco()
            _brilho_tela(camada, 0.2, 0.2, (1.0, 0.3, 0.2), atras=boss)
            _racha_chao(camada, cx_, chao, te, larg=520, n=12, atras=boss)
            for r1, esp_, d_ in ((430, 9, 0.5), (330, 5, 0.42), (230, 3, 0.34)):
                _anel(camada, (cx_, cy_), te * 60, te * r1, d_, BRASA, esp=dp(esp_), achat=0.22, grao=3)
            _linhas_velocidade(camada, 0.35, BRASA, y0=chao + 60 * te, y1=chao + 190 * te, n=16, sentido=1)
            for k_ in range(-4, 7):
                poeira(cx_ + k_ * 50 * te, chao, n=4)
            faiscas.estourar(cx_, cy_, BRASA, n=40, forca=dp(380), tam=ps)

        def _foge_garra():
            ax, ay = kk.ancora()
            p_pulo = _com(P['pulo'], olhos='s')
            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), guarda2, 0.4))
            _som('pulo')

            def _chegou():
                kk.rotacao = 0
                _som('pouso')
                bx_, by_ = kk.ancora()
                poeira(bx_, by_ - kk.extensao()[1], n=8)
                kk.mostrar(guarda2)
            _mover(kk, (ax, ay), R0, 0.4, altura=te * 110, rot=(0, -360), fantasmas=2, on_fim=_chegou,
                   rot_janela=(0.2, 0.75))

        # ── 7) INVESTIDA: ele recolhe o montante e atravessa a tela numa estocada;
        #    o Yoru salta por cima e desce as duas laminas em X nas costas dele (golpe 8) ──
        def _investe():
            cine.entrar()

            def _q(i):
                if i == 13:
                    _salta_investida()
                elif i == 17:
                    _som('sacar_iai')
                    _som('rugido')
                    _tremer(18)
                    boss.inclina_capa = -16.0
                    _linhas_velocidade(camada, 0.45, BRASA, y0=chao + 20 * te, y1=chao + 330 * te, n=22,
                                       sentido=1)
                    for k_ in range(6):
                        ag.depois(0.03 * k_, lambda k_=k_: poeira(bxl + (60 + 45 * k_) * te, chao, n=5))
                    mover_chefe((bxl, chao), (bx, chao), 0.2, ease='out',
                                on_fim=lambda: setattr(boss, 'inclina_capa', 0.0))
            boss.tocar('investida', on_quadro=_q, on_fim=boss_idle)

        def _salta_investida():
            kk.espelhar = True
            kk.tocar(_voo_seq(K.esticado(_com(P['pulo'], olhos='s')), arma_fo, arma_fo, 0.34))
            _som('pulo')
            kk.empurrar(capa=-10, lift=10)
            _mover(kk, kk.ancora(), Xm, 0.34, ease='out', fantasmas=3, on_fim=_x_de_cima)

        def _x_de_cima():
            kk.espelhar = False                             # no alto ele ja esta virado para o chefe, que passou
            chaves, i_r = K.golpe(arma_fo, corta_fo, **dict(G, n_arma=2, prende=2, volta=4))

            def _q(i):
                if i == i_r - GIRO:
                    _som('fala_kurae')
                    kk.empurrar(capa=10, cabelo=8, lift=6)
                    _mover(kk, kk.ancora(), X1, 0.24, ease='in', fantasmas=4)
                    nuc = boss.ponto('nucleo')
                    golpear('h4', dur=0.2, on_meio=lambda: (acerta(8, (nuc[0], nuc[1] + 50 * te), forte=True,
                                                                   reage=False), soco_camera(nuc, 1.16, 0.5),
                                                            _virada()))
                    ag.depois(0.04, lambda: golpear('h4b', dur=0.2, som='corte2'))
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_cai_do_x)

        def _cai_do_x():
            def _chegou():
                _som('pouso')
                bx_, by_ = kk.ancora()
                poeira(bx_, by_ - kk.extensao()[1], n=8)
                kk.tocar(K.sequencia([(2, _com(guarda2, estica=-1), 'out'), (3, guarda2, 'out'), (1, guarda2)]))
            _mover(kk, kk.ancora(), (K0[0], y_luta), 0.3, altura=te * 20, fantasmas=1, on_fim=_chegou)

        # ── 8) o chefe cai de joelho, apoiado no montante... e se levanta em
        #    FURIA: ergue o montante, tudo aceso, e o sopro joga o Yoru longe ──
        def _virada():
            ag.depois(0.5, lambda: cam_em(1.3, foco=(bx - 40 * te, chao + 170 * te), dur=0.6))   # ele caido, de perto
            ag.depois(1.7, lambda: cam_em(1.0, dur=0.25))
            boss.espelhar = False                           # vira para o Yoru (o claro do golpe esconde a troca)
            boss.tocar('cambaleia', on_fim=lambda: boss.tocar('ajoelhado', loop=True))
            cine.sair()
            ag.depois(1.75, _furia)

        def _furia():
            _som('rugido')
            boss.tocar('carrega', on_fim=lambda: boss.tocar('carrega_segura', loop=True))
            ag.depois(0.34, _empurrao)

        def _empurrao():
            ox_, oy_ = boss.ponto('nucleo')
            _anel(camada, (ox_, oy_), te * 10, te * 330, 0.5, BRASA, esp=dp(6), grao=3)
            _tremer(22)
            cen.tranco()
            _brilho_tela(camada, 0.22, 0.25, (1.0, 0.25, 0.16), atras=boss)
            _som('carga')
            ax, ay = kk.ancora()
            kk.tocar(K.sequencia([(2, _com(guarda2, pernas='recua', estica=-1), 'segura'),
                                  (8, _com(guarda2, pernas='recua'), 'segura'), (1, guarda2)]))
            kk.empurrar(capa=-16, cabelo=-12, lift=4)
            _som('desliza')

            def _parou():
                bx_, by_ = kk.ancora()
                poeira(bx_, by_ - kk.extensao()[1], n=10)
                ag.depois(0.3, _ban)
            _mover(kk, (ax, ay), E0, 0.36, ease='out', fantasmas=2, limite=(area, m), on_fim=_parou)

        # ── 6. golpe final (estilo Bleach) ───────────────────────────
        cx_meio = ox_t + titulo.tw / 2.0

        def _fitas(alvo=None, aperto=None, vel=None):
            for f in estado.get('fitas', ()):
                if alvo is not None:
                    f.alvo = alvo
                if aperto is not None:
                    f.aperto = aperto
                if vel is not None:
                    f.vel = vel

        # ── BAN-KAI (igual ao Ichigo) ─────────────────────────────────
        # ERGUE a katana num arco e desce APONTANDO para a frente; a espada
        # azul vira luz e entra na katana; a outra mao SEGURA o braco.
        # "BAN..." - a borda de energia ferve em volta dele. "KAI!!" - estouro
        # de luz: o reiatsu roxo (miolo branco) cobre ele inteiro e sobe numa
        # coluna ate o ceu, ferve, os olhos acendem la dentro... e se desfaz
        # em fiapos revelando o Bankai.
        b_agacha = K.pose(pernas='base_larga', dy=-1, m1=(-2, 2), a1=200.0, m2=(-4, -2), a2=230.0, olhos='s')
        b_ergue = K.pose(pernas='base_larga', dx=1, m1=(3, 13), a1=88.0, m2=(-4, -3), a2=232.0, olhos='s')
        b_aponta = K.pose(pernas='base_larga', dx=1, m1=(9, 3), a1=2.0, m2=(-5, -3), a2=238.0, olhos='s')
        b_livre = K.pose(pernas='base_larga', dx=1, m1=(9, 3), a1=2.0, m2=(-4, -2), olhos='s')
        b_segura = K.pose(pernas='base_larga', dx=1, m1=(9, 3), a1=2.0, m2=(8.5, 2.5), olhos='s', agarra=True)
        b_grita = K.pose(pernas='base_larga', dx=1, dy=-1, m1=(9, 3), a1=2.0, m2=(8.5, 2.5), olhos='g',
                         agarra=True)
        mug = K._fund(pernas='base_larga', m1=(8, 1), a1=-28.0, olhos='l', evo=True, mugetsu=True)
        kk.precarregar([b_agacha, b_ergue, b_aponta, b_livre, b_segura, b_grita])
        try:
            K.clipes_dados()                                      # clipes do Bankai: le antes
            K.aquecer_clipes()                                    # e monta os desenhos aos poucos
        except Exception as _e:
            print(f"[cena] clipes do Bankai: {_e}")
        mug_b = _com(mug, cresce=1.0)          # a pose que os efeitos leem no Bankai (espada fundida)

        def _bk(nome, loop=True, on_fim=None, on_quadro=None, k=None, t0=0.0):
            """Toca o clipe `nome` do Bankai (desenho da referencia, peca por peca)."""
            (k or kk).mostrar_clipe(nome, loop=loop, on_fim=on_fim, on_quadro=on_quadro, base=mug_b, t0=t0)

        def _bk_idle(k=None):
            _bk('idle', k=k)

        def _ban():
            # de frente para o chefe em furia: agacha (antecipacao), ERGUE a
            # katana num arco para cima, segura um instante e desce APONTANDO
            # para ele (passa um pouquinho do ponto e volta)
            ax, ay = kk.ancora()
            cam[0].ir(1.05, foco=(ax, ay + alt * 0.35), dur=2.4)
            _fundo(tela, reator=0.22, barra=0.1, dur=0.8)       # o mundo escurece um pouco
            seq = K.sequencia([(3, _com(P['agacha'], olhos='s'), 'out'), (8, b_agacha, 'out'),
                               (6, b_ergue, 'segura'), (7, b_ergue, 'mola'), (1, b_aponta)])

            def _q(i):
                if i == 4:
                    _som('sacar')
                    kk.empurrar(cabelo=-6, lift=5)
                elif i == 18:
                    _som('corte2')
                    kk.empurrar(capa=-8, cabelo=-6)
                elif i == 22:
                    hx, hy = kk.ponta_espada(1)
                    faiscas.estourar(hx, hy, CIANO, n=8, forca=dp(90), tam=ps)
            kk.tocar(seq, on_quadro=_q, on_fim=_azul_vira_luz)

        def _azul_vira_luz():
            # a espada azul acende, vira luz e corre pelo ar ate a katana
            hx2, hy2 = kk.ponto_mao(2)
            tx2, ty2 = kk.ponta_espada(2)
            hx1, hy1 = kk.ponto_mao(1)
            kk.mostrar(b_livre)
            _som('fusao')
            mx, my = (hx2 + tx2) / 2.0, (hy2 + ty2) / 2.0
            faiscas.estourar(mx, my, AZUL, n=22, forca=dp(110), tam=ps)
            _estrela(camada, mx, my, ps, AZUL)
            u = te * 2

            def forma(t, p, uu):
                s = min(1.0, t / 0.3)
                e = s * s * (3 - 2 * s)
                for j in range(10):                   # cabeca clara e o rastro que esfria
                    ss = e - j * 0.04
                    if ss < 0:
                        break
                    x = mx + (hx1 - mx) * ss
                    y = my + (hy1 - my) * ss + math.sin(ss * math.pi) * alt * 0.12
                    nome = 'luz' if j < 2 else ('clara' if j < 5 else 'cor')
                    g = 2 if j < 3 else 1
                    p.setdefault(nome, []).append((math.floor(x / u) * u, math.floor(y / u) * u, g * u, g * u))
            camada.add_widget(_EfeitoPixel(_cores_efeito(AZUL), 0.36, forma))

            def _chega():
                # a luz entra na katana: estrela e faiscas na mao (sem piscar o
                # corpo inteiro - isso fica para os golpes)
                _estrela(camada, hx1, hy1, ps, BRANCO)
                faiscas.estourar(hx1, hy1, AZUL, n=12, forca=dp(120), tam=ps)
                _som('cristal')
            ag.depois(0.3, _chega)
            ag.depois(0.5, _segura)

        def _segura():
            # a outra mao vem e SEGURA o braco da espada; silencio
            seq = K.sequencia([(6, b_livre, 'out'), (1, b_segura)])
            kk.tocar(seq, on_fim=lambda: kk.tocar(K.poder(b_segura, n=36, forca=0.4, sobe=0.5, lift=1.0),
                                                   loop=True))
            ag.depois(0.18, lambda: _som('agarra'))
            ag.depois(0.6, _ban_fala)

        def _ban_fala():
            # "BAN..." - a borda de energia comeca a ferver em volta dele
            balao(camada, 'BAN...', kk, tipo='fala', dur=1.1)
            _som('carga')
            CH.aquecer(['golpe', 'apanha', 'idle'], por_quadro=1)
            kk.borda_energia(0.35)
            chamas.alvo = 0.3                               # o reiatsu comeca a subir dele
            ag.depois(0.3, lambda: kk.borda_energia(0.7))
            ag.depois(0.6, lambda: kk.borda_energia(1.0))
            _fundo(tela, reator=0.35, barra=0.1, dur=0.9)
            cam[0].ir(1.07, foco=kk.ancora(), dur=0.9)
            t = [0.0]

            def _sobe(dt):
                t[0] += dt
                if t[0] > 0.95:
                    return False
                kk.empurrar(lift=1.2, cabelo=0.8)
                if random.random() < 0.6:
                    ax2, ay2 = kk.ancora()
                    faiscas.estourar(ax2 + random.uniform(-1, 1) * 9 * ps, ay2 - 11 * ps, ROXO, n=1,
                                     forca=dp(30), tam=max(2, ps * 0.6), gravidade=-dp(300))
                return True
            ag.cada(0.05, _sobe)
            _tremer(4)
            ag.depois(0.75, _kai)

        def _kai():
            # "KAI!!" - grito, quadro de impacto e o ESTOURO de luz
            kk.borda_energia(0)
            kk.parar()
            kk.mostrar(b_grita)
            balao(camada, 'KAI!!', kk, tipo='grito', dur=1.3, font_size=sp(40))
            _som('kiai_kai')
            _som('golpe_final')
            ax, ay = kk.ancora()
            _quadro_impacto(camada, kk, (ax, ay + alt * 0.3))
            _tremer(34)
            cam[0].ir(1.0, dur=0.15)
            ag.depois(2.2 / 30.0, _estouro)
            # o chefe nao espera: desce o montante em cima dele...
            boss.tocar('golpe', t0=0.62, on_fim=boss_idle)
            ag.depois(0.17, _repelido)

        def _repelido():
            # ... e a explosao de reiatsu joga a lamina (e ele) para tras
            px_, py_ = boss.ponta()
            boss.impacto(quadros=5, tremor=10)
            boss.tocar('apanha', on_fim=boss_idle)
            _estrela(camada, px_, py_, ps, BRANCO, raios=8, dur=0.2)
            faiscas.estourar(px_, py_, ROXO, n=22, forca=dp(260), tam=ps)
            faiscas.estourar(px_, py_, BRASA, n=14, forca=dp(220), tam=ps)
            _anel(camada, (px_, py_), te * 4, te * 60, 0.3, ROXO, esp=dp(3))
            _som('corte2')

        def _estouro():
            # o reiatsu explode dele: raios, onda de choque no chao, e o casulo
            # cresce ate cobrir tudo; coberto, por baixo ele ja e o Bankai
            kr = K.KiritoPixel(ps=ps)
            kr.espelhar = kk.espelhar
            kr.escala_clipe = ESC_BK
            i = camada.children.index(kk) if kk in camada.children else 0
            camada.add_widget(kr, index=i)                       # na frente dele
            ax_k, ay_k = kk.ancora()
            kr.ancorar(ax_k, ay_k + sobe_bk)
            estado['kr'] = kr
            _som('absorve')
            _som('reiatsu')
            _fundo(tela, reator=0.5, barra=0.1, dur=0.2)
            _brilho_tela(camada, 0.38, 0.27, (0.62, 0.42, 1.0), atras=kk)   # o ceu acende roxo atras dele

            def _q(i):
                if i == 4 and 'pilar' not in estado:
                    _pilar(kr)
                if i >= 6 and kk._desenho is None:
                    kk.escala_clipe = ESC_BK
                    kk.ancorar(ax_k, ay_k + sobe_bk)
                    _bk('idle')                            # coberto: ja e o Bankai la dentro
                    chamas.alvo = 0.35
            kr.mostrar_clipe('rei_estouro', loop=False, on_quadro=_q, on_fim=_ferve)

        def _pilar(kr):
            # a coluna de luz sobe do topo do casulo ate o fim da tela
            p = _PilarReiatsu(kr)
            i = camada.children.index(kr) if kr in camada.children else 0
            camada.add_widget(p, index=i + 1)                    # atras do casulo
            estado['pilar'] = p

        def _ferve():
            # FERVENDO: ele sumiu dentro do reiatsu; no fim os olhos acendem.
            # A dissipacao entra no fim de uma volta da fervura (o fogo continua
            # do mesmo ponto, sem pulo)
            kr = estado.get('kr')
            if kr is None:
                return _revela()
            kr.mostrar_clipe('rei_ferve', loop=True)
            _tremer(10)
            ag.depois(0.8, _olhos)

            def _no_fim_da_volta():
                k2 = estado.get('kr')
                if k2 is None:
                    return _revela()
                c_f = K.clipes_dados()['clipes']['rei_ferve']
                volta = len(c_f['quadros']) / float(c_f.get('fps', 30.0))
                resto = volta - (k2._clipe_t % volta)
                if resto > 1 / 30.0 and resto < volta - 1 / 60.0:
                    ag.depois(resto, _revela)
                else:
                    _revela()
            ag.depois(1.25, _no_fim_da_volta)

        def _olhos():
            # a silhueta escura dele aparece dentro da energia (em degraus) e o
            # olho acende por cima - o quadro classico antes da revelacao
            kr = estado.get('kr')
            o = kk.olhos_desenho() if kk._desenho is not None else None
            if kr is None or o is None:
                return
            try:
                tex = K.quadro_clipe(kk._desenho, kk._quadro_atual(), silhueta=True)[0]
                sil = Widget(size_hint=(None, None), size=(0, 0))
                with sil.canvas:
                    c_sil = Color(0.07, 0.02, 0.15, 0.0)
                    Rectangle(texture=tex, pos=(kk.x + kk._rect.pos[0], kk.y + kk._rect.pos[1]),
                              size=kk._rect.size, tex_coords=tuple(kk._rect.tex_coords))
                camada.add_widget(sil)
                estado['sombra'] = sil
                estado['cor_sombra'] = c_sil
                for j, a in enumerate((0.7, 0.92)):
                    ag.depois(0.08 * j, lambda a=a: setattr(c_sil, 'a', a))
            except Exception as e:
                print(f"[cena] sombra do Bankai: {e}")
            ol = _OlhosAcesos(o, kr.te_clipe())
            camada.add_widget(ol)
            estado['olhos'] = ol
            _som('titulo')

        def _revela():
            # o reiatsu se desfaz em fiapos subindo: aparece o BANKAI, com o
            # cabelo e o sobretudo ainda levantados pelo vento de energia
            kr = estado.get('kr')
            p = estado.pop('pilar', None)
            if p is not None:
                p.sumir(0.45)
            # a energia sai primeiro de cima do corpo: no mesmo quadro a silhueta
            # escura da lugar ao Bankai de verdade (com os olhos ainda acesos)
            estado.pop('cor_sombra', None)
            for chave in ('olhos', 'sombra'):
                w = estado.pop(chave, None)
                if w is not None and w.parent is not None:
                    w.parent.remove_widget(w)
            _bk('revela', loop=False, on_fim=_bk_idle)
            CH.aquecer(['golpe', 'apanha', 'idle'], por_quadro=1)
            chamas.alvo = 0.8
            aura.alvo = 0.5
            _som('transicao')
            ax, ay = kk.ancora()
            faiscas.estourar(ax, ay + alt * 0.4, ROXO, n=28, forca=dp(220), tam=te * 2, gravidade=-dp(90))

            def _fim_rei():
                k2 = estado.pop('kr', None)
                if k2 is not None and k2.parent is not None:
                    k2.parent.remove_widget(k2)
                ag.depois(0.25, _acende_lamina)
            if kr is not None:
                kr.mostrar_clipe('rei_dissipa', loop=False, on_fim=_fim_rei)
            else:
                _fim_rei()

        def _acende_lamina():
            # o fio roxo da espada acende da guarda ate a ponta
            hx, hy = kk.ponto_mao(1)
            tx, ty = kk.ponta_espada(1)
            aura.alvo = 0.7
            _estrela(camada, hx, hy, ps, BRANCO)
            faiscas.estourar(hx, hy, BRANCO, n=10, forca=dp(150), tam=te * 2)
            _som('fusao')

            def forma(t, p, u):
                s = min(1.0, t / 0.32)
                for j in range(9):                        # cabeca clara e um rastro que esfria
                    ss = s - j * 0.035
                    if ss < 0:
                        break
                    x = hx + (tx - hx) * ss
                    y = hy + (ty - hy) * ss
                    nome = 'luz' if j < 2 else ('clara' if j < 5 else 'cor')
                    g = 2 if j < 3 else 1
                    p.setdefault(nome, []).append((math.floor(x / u) * u - (g - 1) * u,
                                                   math.floor(y / u) * u - (g - 1) * u, g * u, g * u))
            camada.add_widget(_EfeitoPixel(_cores_efeito(ROXO), 0.5, forma))
            ag.depois(0.32, lambda: (faiscas.estourar(tx, ty, ROXO, n=14, forca=dp(170), tam=te * 2),
                                     _estrela(camada, tx, ty, ps, ROXO)))
            ag.depois(0.5, _duelo)

        def _duelo():
            # o chefe nao espera: desce o montante em cima do Bankai... que some
            # num passo (so ficam as sombras roxas) e reaparece no alto
            ax, ay = kk.ancora()
            alto = (ax - 14 * te, ay + 116 * te)          # (o Bankai e grande: cabelo e casaco podem sair do quadro)

            def _q(i):
                if i == 20:
                    _som('teleporte')
                    kk.empurrar(capa=-10, cabelo=-8, lift=8)
                    _mover(kk, (ax, ay), alto, 0.1, linear=True, fantasmas=5, cor_fantasma=ROXO)
                elif i == 24:                                # cravou no chao vazio
                    px_, _py = boss.ponta()
                    poeira(px_, chao, n=14)
                    faiscas.estourar(px_, chao, BRASA, n=18, forca=dp(230), tam=ps)
                    _anel(camada, (px_, chao + te * 2), te * 4, te * 80, 0.35, BRASA, esp=dp(3), achat=0.3)
                    _som('golpe_final')
                    _tremer(18)
                    ag.depois(0.1, _revida)
            boss.tocar('golpe', t0=0.3, on_quadro=_q, on_fim=boss_idle)

        def _revida():
            # ... ja cortando: a lamina negra desce na cabeca do chefe
            feito = [False]

            def _q(i):
                if i >= 5 and not feito[0]:
                    feito[0] = True
                    golpear('ctr', dur=0.16, som='corte2',
                            on_meio=lambda: acerta(9, boss.ponto('cabeca'), forte=True, cor=ROXO))
            _gemido(forte=True)
            _bk('corte', loop=False, on_quadro=_q, on_fim=lambda: _bk('fim', loop=False, on_fim=_bk_idle))
            ag.depois(0.6, _lua)

        def _lua():
            # a lua negra sobe atras dele e o fogo ruge (ele continua flutuando)
            ax, ay = kk.ancora()
            CH.aquecer(['rugido', 'carrega', 'carrega_segura'], por_quadro=1)
            lua = _LuaNegra((ax + (-1 if kk.espelhar else 1) * alt * 0.05, ay + alt * 0.55), alt * 1.05,
                            te * 2, dur=0.7)
            camada.add_widget(lua, index=len(camada.children))      # atras de tudo
            estado['lua'] = lua
            chamas.alvo = 1.0
            aura.alvo = 1.0
            _som('trevas')
            _tremer(12)
            _brilho_tela(camada, 0.35, 0.22, (0.8, 0.62, 1.0))
            faiscas.estourar(ax, ay + alt * 0.5, ROXO, n=26, forca=dp(230), tam=te * 2, gravidade=-dp(80))
            cam[0].ir(1.15, foco=(ax, ay + alt * 0.45), dur=0.6)
            # close: os olhos acendem roxos; depois a escuridao
            ag.depois(0.55, lambda: close_rosto(camada, 'mugetsu', dur=0.85, y_rel=0.84, on_fim=_posiciona))

        def _posiciona():
            # desce de volta para a frente do chefe, com a lamina na altura da
            # frase: dali a escuridao vai sair dele
            lua = estado.pop('lua', None)
            if lua is not None:
                lua.sumir(0.3)
            kk.espelhar = False
            x_ini, y_ini = min(E0[0] + th * 0.4, bx - 190 * te), y_luta + sobe_bk + 12 * te
            ax, ay = kk.ancora()
            _som('reiatsu')
            cam[0].ir(1.0, dur=0.6)
            boss.tocar('rugido', on_quadro=_berro,
                       on_fim=lambda: boss.tocar('carrega', t0=0.3,
                                                 on_fim=lambda: boss.tocar('carrega_segura', loop=True)))
            # levita: sobe devagar, o cabelo e o casaco flutuando
            _mover(kk, (ax, ay), (x_ini, y_ini), 0.8, altura=th * 0.25, fantasmas=0, on_fim=_trevas,
                   ease='suave')

        def _trevas():
            # MUGETSU: a escuridao sai dele e engole a tela inteira (a frase e
            # o infinito somem); so os olhos, o fogo e a espada brilham
            ax, ay = kk.ancora()
            cine.entrar()                                    # (a lua e o castelo ficam: o corte acontece no mundo dele)
            _brilho_tela(camada, 0.3, 0.3, (0.5, 0.3, 0.9), atras=boss)
            _som('trevas')
            aura.alvo = 1.0
            cam[0].ir(1.12, foco=(ax, ay + alt * 0.3), dur=1.4)
            kk.empurrar(capa=-6, cabelo=-5, lift=4)
            ag.depois(0.8, _ergue)

        def _ergue():
            # silencio: ele diz o nome do golpe, a lamina vai para tras (devagar)
            # e segura tremendo
            _bk('carga', loop=False, on_fim=lambda: _bk('carga_segura'))
            _som('fala_ougi')
            ag.depois(1.12, _golpe_final)             # o corte cai no "GI!" do grito

        def _golpe_final():
            # UM corte so: a lamina atravessa e um risco de luz corta a tela de
            # um lado ao outro na altura da frase... e tudo congela
            feito = [False]

            def _q(i):
                if i >= 5 and not feito[0]:           # a lamina passa pela frente: o golpe
                    feito[0] = True
                    _impacto_final()
            _bk('corte', loop=False, on_quadro=_q,
                on_fim=lambda: _bk('fim', loop=False, on_fim=_bk_idle))

        def _impacto_final():
            kk.impacto(forte=True)
            _, cy = titulo.x_do_trecho(0, len(texto))
            tv = estado.get('trevas')
            if tv is not None:
                tv.cortar(cy)
            golpear('cus', dur=0.18)                 # a luz roxa atravessa a tela na altura da frase
            if titulo.parent is camada:              # a frase vai nascer POR CIMA do chefe
                camada.remove_widget(titulo)
                camada.add_widget(titulo)
            # talhos atrasados (classico de anime): ele ja passou... e os cortes
            # vao aparecendo no corpo do chefe, um depois do outro
            cx0, cy0, cx1, cy1 = boss.corpo()
            rnd_t = random.Random(4)
            for n_ in range(6):
                def _talho(n_=n_):
                    a = math.radians(rnd_t.choice((-38, -20, 16, 34, 62, -64)))
                    mx_ = rnd_t.uniform(cx0, cx1)
                    my_ = rnd_t.uniform(cy0 + (cy1 - cy0) * 0.2, cy1 - (cy1 - cy0) * 0.12)
                    L = rnd_t.uniform(120, 200) * te
                    u2 = te * 2
                    linha = _reta_pixels(mx_ - math.cos(a) * L, my_ - math.sin(a) * L,
                                         mx_ + math.cos(a) * L, my_ + math.sin(a) * L, u2)
                    camada.add_widget(_PixelsRoxo([linha], u2, cresce=0.05, fica=0.5, some=0.1, grossura=1))
                    faiscas.estourar(mx_, my_, random.choice((ROXO, BRANCO)), n=5, forca=dp(170), tam=te * 2)
                    _som('corte' if n_ % 2 else 'corte2')
                    _tremer(5)
                ag.depois(0.16 + 0.07 * n_, _talho)
            # ... e ele vai junto: num passo so atravessa o chefe e para do outro
            # lado, de costas para ele
            ax0, ay0 = kk.ancora()
            alem = (min(W - m - 60 * te, bx + 64 * te), ay0)
            _mover(kk, (ax0, ay0), alem, 0.09, linear=True, fantasmas=6, cor_fantasma=ROXO)
            # ... e passa pela cintura do chefe: ele congela, branco
            boss.impacto(quadros=8, tremor=0)
            boss.pausar(3.0)
            barra_c.dano(0.0)

            def _prepara_cacos():
                # a conta pesada (foto do chefe em blocos, cacos) cai aqui, com
                # a cena congelada - a explosao depois sai sem tranco
                try:
                    from efeitos import explodir_estilhacos
                    bxw, byw = camada.to_window(bx, cy)
                    estado['cacos'] = explodir_estilhacos(boss, lambda: None, corte=0.0, tremor=0, px=te * 3,
                                                          racha=0.5, ponto=(bxw, byw), adiar=True,
                                                          max_celulas=12000, n_cacos=34, paleta='brasa')
                except Exception as e:
                    print(f"[cena] chefe em cacos: {e}")
            ag.depois(0.38, _prepara_cacos)
            ag.depois(0.1, lambda: _quadro_impacto(camada, kk, (bx, cy)))
            _som('sacar_iai')
            cam[0].ir(1.0, dur=0.1)
            ag.depois(0.12, lambda: kk.pausar(0.75))
            ag.depois(0.9, _abre)

        def _abre():
            # a escuridao se abre no corte: a frase aparece gravada dentro dele
            tv = estado.get('trevas')
            if tv is not None:
                tv.abrir(0.6)
            _, cy = titulo.x_do_trecho(0, len(texto))
            # A FRASE NASCE DO CHEFE: de dentro do corpo que se parte sai uma brasa
            # para cada letra; onde ela chega a letra acende em brasa (branco ->
            # brasa -> o ciano do app). As letras do meio, mais perto dele, primeiro.
            estado['chefe_morto'] = True
            alvos = [(li, ox_t + (titulo._larg[li] + titulo._larg[li + 1]) / 2.0, cy)
                     for li, letra in enumerate(texto) if letra.strip()]
            alvos.sort(key=lambda a_: abs(a_[1] - bx))

            def _acende(li):
                lx_ = ox_t + (titulo._larg[li] + titulo._larg[li + 1]) / 2.0
                titulo.revelar(li, li + 1, dur=0.5, cor=BRASA)
                _estrela(camada, lx_, cy, ps * 0.7, BRASA, raios=4, dur=0.14)
                faiscas.estourar(lx_, cy, BRASA, n=4, forca=dp(120), tam=te * 2, gravidade=dp(200))
                if li % 3 == 0:
                    _som('cristal')
            cb = boss.corpo()
            _brasas_para_letras(camada, alvos, (cb[0], cb[1] + (cb[3] - cb[1]) * 0.15, cb[2], cb[3] - (cb[3] - cb[1]) * 0.1),
                                0.95, _acende)
            ag.depois(1.25, lambda: [titulo.garantir(i0, i1) for i0, i1 in _TRECHOS])   # nenhuma letra fica para tras
            for j in range(9):
                xj = area[0] + (area[2] - area[0]) * (j + 0.5) / 9.0
                faiscas.estourar(xj, cy, random.choice((ROXO, BRANCO, (0.85, 0.72, 1.0))), n=5,
                                 forca=dp(240), tam=ps, gravidade=dp(160))
            _som('getsuga')
            _tremer(28)
            _brilho_tela(camada, 0.5, 0.35, (0.9, 0.82, 1.0))
            # o mundo do chefe se desfaz com ele: volta a tela do app
            cen.fechar(0.6)
            cine.sair()
            _fundo(tela, reator=0.5, barra=0.1, dur=0.8)
            # o chefe se parte no corte (as duas metades se afastam) e vira cacos
            soltar = estado.pop('cacos', None)
            if soltar is not None:
                soltar()
                _som('vidro')
            else:
                boss.opacity = 0
            barra_c.sumir()
            ag.depois(0.3, _para)

        def _para():
            # de costas para a frase que acende letra por letra... e o mundo segura a respiracao
            ag.depois(0.7, _separa)

        def _separa():
            # a espada evoluida se divide de novo nas duas e ele desce para
            # pousar em cima da frase
            hx2, hy2 = kk.ponto_mao(1)
            aura.alvo = 0.0
            chamas.alvo = 0.0
            K.definir_ambiente('')                           # o mundo do chefe acabou: ele volta para a luz do app
            dupla = _com(P['dupla'], olhos='s')
            dupla_m = None
            # a lamina se divide nas duas: estalo nas maos
            kk.impacto()
            faiscas.estourar(hx2, hy2, BRANCO, n=18, forca=dp(160), tam=ps)
            faiscas.estourar(hx2, hy2, AZUL, n=10, forca=dp(120), tam=ps)
            _anel(camada, (hx2, hy2), ps * 2, ps * 14, 0.35, CIANO)
            _som('separa')
            ag.depois(0.22, lambda: _desfaz(dupla, dupla_m))

        def _desfaz(dupla, dupla_m):
            # o anel desce da cabeca aos pes: por cima dele ele ja voltou ao
            # normal, por baixo ainda e o Bankai - as chamas se apagam
            kk2 = K.KiritoPixel(ps=ps)
            kk2.espelhar = kk.espelhar
            i = camada.children.index(kk) if kk in camada.children else 0
            camada.add_widget(kk2, index=i)                     # na frente (o de cima e o normal)
            kk2.ancorar(*kk.ancora())
            kk2.mostrar(dupla)
            kk2._preso = dict(kk._preso)
            ax, ay = kk.ancora()
            esq, baixo, dir_, cima = kk.extensao(_com(dupla, a1=None, a2=None))
            eb = kk.extensao()                             # o desenho do Bankai e mais alto
            y_alto, y_baixo = ay + max(cima, eb[3]) + te * 6, ay - max(baixo, eb[1]) - te * 3
            cx_c = ax + (dir_ - esq) / 2.0
            larg = (esq + dir_) * 1.05
            passo = te * 2
            anel = _AnelEnergia(te * 2)
            camada.add_widget(anel)
            _som('absorve')
            dur = 0.55
            t = [0.0]
            kk2.recortar(y_alto, None)
            kk.recortar(None, y_alto)

            def _p(dt):
                t[0] += dt
                s = min(1.0, t[0] / dur)
                y = y_alto + (y_baixo - y_alto) * s
                yq = math.floor(y / passo) * passo
                kk2.recortar(yq, None)
                kk.recortar(None, yq)
                anel.pos_linha(cx_c, yq, larg, dt)
                if int(t[0] * 60) % 3 == 0:
                    faiscas.estourar(cx_c + random.uniform(-0.5, 0.5) * larg, yq, ROXO, n=2,
                                     forca=dp(60), tam=te * 2, gravidade=-dp(200))
                if s >= 1.0:
                    kk.recortar()
                    kk.mostrar(dupla)
                    kk.parar()
                    kk._preso = dict(kk2._preso)
                    for w in (kk2, anel):
                        if w.parent is not None:
                            w.parent.remove_widget(w)
                    ag.depois(0.12, _desce)
                    return False
                return True
            ag.cada(1 / 60., _p)

        def _desce():
            ax, ay = kk.ancora()
            ax_t = min(max(ax, ox_t + titulo.tw * 0.14), ox_t + titulo.tw * 0.84)   # em cima das letras
            alvo = quadro(ax_t, y_topo, ['dupla', 'saca2', 'pega2', 'chiburi1_a', 'chiburi1', 'guardado'])
            dupla = _com(P['dupla'], olhos='s')
            kk.mostrar(K.esticado(dupla))

            def _pousou():
                _som('pouso')
                bx, by = kk.ancora()
                poeira(bx, by - kk.extensao()[1], n=8)
                kk.empurrar(lift=-8, capa=-6)
                kk.tocar(K.sequencia([(2, _com(dupla, dy=dupla['dy'] - 2, estica=-1), 'segura'),
                                      (4, dupla, 'out'), (1, dupla)]),
                         on_fim=lambda: ag.depois(0.15, _guarda_azul))
            _mover(kk, (ax, ay), alvo, 0.26, ease='in', fantasmas=0, limite=(area, m), on_fim=_pousou)

        def _guarda_azul():
            # guarda a espada azul nas costas: gira a lamina para cima por
            # cima do ombro e ela desce na bainha (o saque ao contrario)
            saca = _com(P['saca2'], olhos='s')
            pega = _com(P['pega2'], olhos='s')
            seq = K.sequencia(_de_agora(kk, 3, 'out', proxima=saca) +
                              [(4, saca, 'out'), (3, saca, 'segura'), (4, pega, 'in'),
                               (2, pega, 'segura'), (1, pega)])

            def _q(q):
                if q == 3:
                    _som('giro')
                elif q == 14:
                    _som('embainhar')
                    bx, by = kk.ponto_mao(2)
                    faiscas.estourar(bx, by, AZUL, n=6, forca=dp(50), tam=max(2, ps * 0.7), gravidade=0)
                    kk.empurrar(capa=4, cabelo=3)
            kk.tocar(seq, on_quadro=_q, on_fim=_chiburi)

        def _chiburi():
            # chiburi com a katana (ergue e sacode a lamina num estalo) e noto:
            # embainha devagar na cintura ate o clique
            seq = K.sequencia(_de_agora(kk, 3, 'out', proxima=P['chiburi1_a']) +
                              [(4, _com(P['chiburi1_a'], olhos='s'), 'in'), (2, _com(P['chiburi1'], olhos='s'), 'segura'),
                               (6, _com(P['chiburi1'], olhos='s'), 'suave'), (8, P['embainha1_a'], 'in'),
                               (4, P['embainha1_b'], 'suave'), (3, P['embainha1_c'], 'mola'),
                               (1, P['guardado'])])

            def _q(q):
                if q == 7:
                    _som('pulo')
                    kk.empurrar(capa=-6, cabelo=-4)
                elif q == 15:
                    _som('desliza')
                    _prepara_explosao(1)
                elif q == 20:
                    _prepara_explosao(-1)
                elif q == 29:
                    _som('embainhar')
                    bx, by = kk.ponto_mao(1)
                    faiscas.estourar(bx, by, BRANCO, n=6, forca=dp(50), tam=max(2, ps * 0.7),
                                     gravidade=0)
                    ag.depois(0.14, _explode)
            kk.tocar(seq, on_quadro=_q, on_fim=lambda: kk.idle(base=P['guardado']))

        # ── 7. so depois de embainhar: a frase explode ──────────────
        def _meialua_explosao(sent):
            cx, cy = titulo.x_do_trecho(0, len(texto))
            return dict(centro=(cx, cy), raio=titulo.tw * 0.62, ang_ini=160 if sent > 0 else 20,
                        ang_fim=-45 if sent > 0 else 225, espessura=th * 1.2,
                        achat=0.34, rotacao=12 * sent)

        def _prepara_explosao(sent):
            try:
                preparar_meialua(**_meialua_explosao(sent))
            except Exception as e:
                print(f"[cena] preparar explosao: {e}")

        def _explode():
            cx, cy = titulo.x_do_trecho(0, len(texto))
            for sent, cor in ((1, CIANO), (-1, AZUL)):
                camada.add_widget(CorteMeiaLua(cor=cor, dur_cheio=5 / 30.0, dur_decai=9 / 30.0, por_s=30,
                                               **_meialua_explosao(sent)))
            faiscas.estourar(cx, cy, CIANO, n=45, forca=dp(340), tam=ps)
            faiscas.estourar(cx, cy, AZUL, n=25, forca=dp(260), tam=ps)
            _som('titulo')
            _tremer(26)
            _brilho_tela(camada, 0.3, 0.3)
            titulo.clarao_final()
            # pose final: espadas guardadas, firme em cima da frase, a mao
            # perto do cabo; o sobretudo assenta com o vento da explosao
            fim_p = _com(P['guardado'], olhos='a')
            kk.tocar(K.sequencia(_de_agora(kk, 3, 'out') + [(10, _com(fim_p, olhos='s'), 'segura'),
                                                            (1, fim_p)]),
                     on_fim=lambda: kk.idle(base=fim_p))
            kk.empurrar(capa=-10, cabelo=-8, lift=4)
            aura.alvo = 0.0
            ag.depois(0.25, lambda: balao(camada, 'Bem-vindo!', kk, dur=1.0))
            ag.depois(1.25, encerrar)

        # rede de seguranca: a cena nunca prende o app
        def _seguranca():
            titulo.completo()
            restaurar_fundo()
            encerrar()
        ag.depois(64.0, _seguranca)
    except Exception as e:
        print(f"[cena] falhou, seguindo sem ela: {e}")
        restaurar_fundo()
        encerrar()
    return camada


class _PixelsBrasa(_PixelsLuz):
    """Riscos e rachaduras em BRASA (o chao que racha, os talhos no chefe)."""
    CORES = (('halo', (0.55, 0.06, 0.08, 0.7)), ('meio', (1.0, 0.25, 0.14, 1.0)), ('luz', (1.0, 0.85, 0.6, 1.0)))


class _PixelsRoxo(_PixelsLuz):
    """Os talhos do Bankai."""
    CORES = (('halo', (0.45, 0.2, 0.9, 0.6)), ('meio', (0.8, 0.62, 1.0, 1.0)), ('luz', (1.0, 1.0, 1.0, 1.0)))


class _CloseRosto(Widget):
    """Close de anime: uma faixa atravessa a tela com o olho do Yoru em pixel
    grande. A faixa abre, o retrato entra deslizando com linhas de
    velocidade, o olho abre e o brilho pisca; no fim a faixa fecha.
    tipo: 'normal', 'poder' (olho aceso ciano) ou 'mugetsu' (os olhos
    acendem roxos no meio do close). espelhar: ele olhando para a
    esquerda (o retrato vira e entra pelo outro lado)."""

    PW, PH = 104, 40

    def __init__(self, tipo='normal', dur=0.8, on_fim=None, y_rel=0.56, som=True, espelhar=False,
                 **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self.size = (0, 0)
        self.tipo, self.dur, self.on_fim = tipo, dur, on_fim
        self.esp = espelhar
        W, H = Window.size
        self.W, self.H = W, H
        hb = min(W * self.PH / float(self.PW), H * 0.26)
        self.z = hb / float(self.PH)
        self.hb, self.wr = hb, self.PW * self.z
        self.cy = H * y_rel
        R = K._YM.RETRATOS
        self.tex = {n: K.textura_mapa(m) for n, m in R.items()}
        roxo = tipo == 'mugetsu'
        cor = (0.66, 0.36, 1.0) if roxo else (0.33, 0.85, 1.0)
        rnd = random.Random(7)
        self.linhas = [(rnd.uniform(0.05, 0.95), rnd.uniform(0.15, 0.6), rnd.uniform(1.4, 3.2), rnd.random())
                       for _ in range(18)]
        with self.canvas:
            self.c_fundo = Color(0.015, 0.015, 0.04, 0.95)
            self.r_fundo = Rectangle(pos=(0, self.cy), size=(W, 0))
            self.c_lin = Color(cor[0], cor[1], cor[2], 0.30)
            self.m_lin = Mesh(mode='triangles')
            Color(1, 1, 1, 1)
            self.r_ret = Rectangle(pos=(0, self.cy), size=(0, 0))
            self.c_borda = Color(cor[0], cor[1], cor[2], 1.0)
            self.b_cima = Rectangle(pos=(0, 0), size=(0, 0))
            self.b_baixo = Rectangle(pos=(0, 0), size=(0, 0))
            self.c_flash = Color(1, 1, 1, 0)
            self.r_flash = Rectangle(pos=(0, self.cy), size=(W, 0))
            self.c_brilho = Color(1, 1, 1, 0)
            self.m_brilho = Mesh(mode='triangles')
        self.t = 0.0
        self._som = som
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)
        self._tick(0)

    def _nome(self, t):
        if self.tipo == 'mugetsu':
            if t < 0.16:
                return 'normal_meio'
            if t < 0.36:
                return 'normal'
            return 'mugetsu_meio' if t < 0.42 else 'mugetsu'
        if t < 0.16:
            return 'normal_meio'
        return 'poder' if self.tipo == 'poder' else 'normal'

    def _tick(self, dt):
        try:
            self.t += dt
            t, dur = self.t, self.dur
            W = self.W
            abre = min(1.0, t / 0.08)
            fecha = max(0.0, min(1.0, (dur - t) / 0.09))
            k = (1 - (1 - min(abre, fecha)) ** 3)
            hb = self.hb * k
            y0 = self.cy - hb / 2.0
            self.r_fundo.pos, self.r_fundo.size = (0, y0), (W, hb)
            desl = (1 - (1 - min(1.0, t / 0.12)) ** 3)
            x0 = (W - self.wr) / 2.0 + (1 - desl) * W * 0.18 * (-1 if self.esp else 1)
            self.r_ret.texture = self.tex[self._nome(t)]
            if self.esp:
                self.r_ret.tex_coords = K._TC_ESPELHO
            self.r_ret.pos, self.r_ret.size = (x0, y0), (self.wr, hb)
            lb = max(1.0, dp(1.5))
            self.b_cima.pos, self.b_cima.size = (0, y0 + hb), (W, lb * k)
            self.b_baixo.pos, self.b_baixo.size = (0, y0 - lb * k), (W, lb * k)
            # linhas de velocidade correndo para tras dele
            vs, ids = [], []
            for i, (fy, fl, vel, fase) in enumerate(self.linhas):
                x = W * (1.2 - ((fase + t * vel) % 1.4))
                y = y0 + hb * fy
                w, h = W * fl, max(1.0, dp(1.2))
                if self.esp:
                    x = W - x - w
                vs += [x, y, 0, 0, x + w, y, 0, 0, x + w, y + h, 0, 0, x, y + h, 0, 0]
                b = 4 * i
                ids += [b, b + 1, b + 2, b, b + 2, b + 3]
            self.m_lin.vertices, self.m_lin.indices = vs, ids
            # brilho no olho quando ele abre (estrela de 4 pontas em pixel)
            tb = t - (0.42 if self.tipo == 'mugetsu' else 0.18)
            if 0 <= tb < 0.2:
                if tb < dt + 0.001 and self._som:
                    _som('habilidade' if self.tipo != 'normal' else 'koiguchi')
                u = self.z
                cx, cy = x0 + ((self.PW - 76.5) if self.esp else 76.5) * u, y0 + 18.5 * u * k
                s = (1 - abs(tb / 0.1 - 1)) * 4.5
                vs, ids = [], []
                for i, (w, h) in enumerate(((u * (1 + 2 * s), u), (u, u * (1 + 2 * s)))):
                    vs += [cx - w / 2, cy - h / 2, 0, 0, cx + w / 2, cy - h / 2, 0, 0,
                           cx + w / 2, cy + h / 2, 0, 0, cx - w / 2, cy + h / 2, 0, 0]
                    b = 4 * i
                    ids += [b, b + 1, b + 2, b, b + 2, b + 3]
                self.m_brilho.vertices, self.m_brilho.indices = vs, ids
                self.c_brilho.a = 1.0
            else:
                self.c_brilho.a = 0.0
            # no Mugetsu, os olhos acendem com um clarao roxo na faixa
            if self.tipo == 'mugetsu' and 0.36 <= t < 0.5:
                self.c_flash.rgba = (0.8, 0.6, 1.0, 0.55 * (1 - (t - 0.36) / 0.14))
                self.r_flash.pos, self.r_flash.size = (0, y0), (W, hb)
            else:
                self.c_flash.a = 0.0
            if t >= dur:
                self._ev.cancel()
                if self.parent is not None:
                    self.parent.remove_widget(self)
                if self.on_fim:
                    cb, self.on_fim = self.on_fim, None
                    cb()
                return False
        except Exception as e:
            print(f"[cena] close: {e}")
            try:
                self._ev.cancel()
                if self.parent is not None:
                    self.parent.remove_widget(self)
            except Exception:
                pass
            if self.on_fim:
                cb, self.on_fim = self.on_fim, None
                try:
                    cb()
                except Exception:
                    pass
            return False


def close_rosto(camada, tipo='normal', dur=0.8, on_fim=None, y_rel=0.56, espelhar=False):
    """Poe o close de anime por cima de tudo na camada."""
    try:
        camada.add_widget(_CloseRosto(tipo=tipo, dur=dur, on_fim=on_fim, y_rel=y_rel, espelhar=espelhar))
    except Exception as e:
        print(f"[cena] close: {e}")
        if on_fim:
            on_fim()
