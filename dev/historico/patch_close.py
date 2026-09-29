"""Close de anime (faixa com o olho do Yoru) e rastro de luz no olho."""
pk = r'C:\Users\kirit\travetefocus\app\kirito.py'
pc = r'C:\Users\kirit\travetefocus\app\cenas.py'
k = open(pk, encoding='utf-8').read()
c = open(pc, encoding='utf-8').read()


def troca(s, a, b):
    assert s.count(a) == 1, (a[:70], s.count(a))
    return s.replace(a, b)


# ── kirito: textura de um mapa de caracteres (retratos do close)
k = troca(k, '''def _bytes(p):''', '''_TEX_MAPA = {}


def textura_mapa(linhas):
    """Texture (pixel duro) de um mapa de caracteres da paleta (linha 0 em
    cima). Guardada."""
    chave = id(linhas)
    tex = _TEX_MAPA.get(chave)
    if tex is not None:
        return tex
    h, w = len(linhas), len(linhas[0])
    idx = bytearray(w * h)
    for r, l in enumerate(linhas):
        base = (h - 1 - r) * w
        for cc, ch in enumerate(l):
            if ch != '.':
                idx[base + cc] = _COD[ch]
    buf = bytearray(w * h * 4)
    for i in range(4):
        buf[i::4] = idx.translate(_TAB[i])
    dados = bytes(buf)
    tex = Texture.create(size=(w, h), colorfmt='rgba')
    tex.mag_filter = 'nearest'
    tex.min_filter = 'nearest'
    tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
    tex.add_reload_observer(lambda t, d=dados: t.blit_buffer(d, colorfmt='rgba', bufferfmt='ubyte'))
    _TEX_MAPA[chave] = tex
    return tex


def _bytes(p):''')

# ── kirito: rastro de luz no olho (a marca do Yoru)
k = troca(k, '''            self._rect_clarao_cab = Rectangle(pos=(0, 0), size=(0, 0))''', '''            self._rect_clarao_cab = Rectangle(pos=(0, 0), size=(0, 0))
            PopMatrix()
        # rastro de luz no olho: quando ele se mexe rapido, o olho risca o ar
        self.rastro_olho = True
        self._olho_hist = []
        self._lote_olho = LotePixels(self.canvas.after, (
            ('r2', (0.10, 0.50, 0.95, 0.55)), ('r1', (0.33, 0.85, 1.00, 0.85)), ('r0', (0.80, 1.00, 1.00, 1.0))))
        with self.canvas:
            PushMatrix()''')
k = troca(k, '''    def _camadas(self, dt, frente, cima):''', '''    def _ponto_mundo(self, lx, ly):
        """Ponto local do sprite (px) -> coords do pai, com a escala em volta
        da ancora e a rotacao em volta do pivo, como no canvas."""
        ax, ay = self.ancora_local()
        lx = ax + (lx - ax) * self.escala_x
        ly = ay + (ly - ay) * self.escala_y
        ox, oy = self.pivo if self.pivo is not None else (ax, ay)
        a = math.radians(self.rotacao)
        ca, sa = math.cos(a), math.sin(a)
        return (self.x + ox + (lx - ox) * ca - (ly - oy) * sa,
                self.y + oy + (lx - ox) * sa + (ly - oy) * ca)

    def _rastro_do_olho(self):
        """Risco de luz ciano deixado pelo olho quando ele se mexe rapido
        (na forma Mugetsu quem faz o risco e o fogo, em roxo)."""
        try:
            p = self._pose
            if not self.rastro_olho or p.get('mugetsu') or self.parent is None:
                if self._olho_hist:
                    self._olho_hist = []
                    self._lote_olho.desenhar({})
                return
            te = self.ps / float(R)
            ex, ey = olhos_texel(p)[0]
            if self.espelhar:
                ex = TW - 1 - ex
            self._olho_hist.append(self._ponto_mundo((ex + 0.5) * te, (ey + 0.5) * te))
            del self._olho_hist[:-7]
            h = self._olho_hist
            pontos = {}
            for i in range(len(h) - 1, 0, -1):
                idade = len(h) - 1 - i
                cor = 'r0' if idade < 1 else ('r1' if idade < 3 else 'r2')
                lado = te * (1.6 if idade < 1 else 1.0)
                (x0, y0), (x1, y1) = h[i], h[i - 1]
                d = math.hypot(x1 - x0, y1 - y0) / te
                if d < 1.4:
                    continue
                n = int(d) + 1
                for j in range(n):
                    u = j / float(n)
                    x = x0 + (x1 - x0) * u
                    y = y0 + (y1 - y0) * u
                    pontos.setdefault(cor, []).append((math.floor(x / te) * te, math.floor(y / te) * te, lado))
            self._lote_olho.desenhar(pontos)
        except Exception as e:
            print(f"[kirito] rastro do olho: {e}")

    def _camadas(self, dt, frente, cima):''')
k = troca(k, '''            self._camadas(dt, frente, cima)
            self._desenhar()''', '''            self._camadas(dt, frente, cima)
            self._desenhar()
            self._rastro_do_olho()''')

# ── cenas: o close de anime
c = troca(c, '''class _Sombra(Widget):''', '''class _CloseRosto(Widget):
    """Close de anime: uma faixa atravessa a tela com o olho do Yoru em pixel
    grande. A faixa abre, o retrato entra deslizando com linhas de
    velocidade, o olho abre e o brilho pisca; no fim a faixa fecha.
    tipo: 'normal', 'poder' (olho aceso ciano) ou 'mugetsu' (os olhos
    acendem roxos no meio do close)."""

    PW, PH = 104, 40

    def __init__(self, tipo='normal', dur=0.8, on_fim=None, y_rel=0.56, som=True, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self.size = (0, 0)
        self.tipo, self.dur, self.on_fim = tipo, dur, on_fim
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
            x0 = (W - self.wr) / 2.0 + (1 - desl) * W * 0.18
            self.r_ret.texture = self.tex[self._nome(t)]
            self.r_ret.pos, self.r_ret.size = (x0, y0), (self.wr, hb)
            lb = max(1.0, dp(1.5))
            self.b_cima.pos, self.b_cima.size = (0, y0 + hb), (W, lb * k)
            self.b_baixo.pos, self.b_baixo.size = (0, y0 - lb * k), (W, lb * k)
            # linhas de velocidade correndo para a esquerda
            vs, ids = [], []
            for i, (fy, fl, vel, fase) in enumerate(self.linhas):
                x = W * (1.2 - ((fase + t * vel) % 1.4))
                y = y0 + hb * fy
                w, h = W * fl, max(1.0, dp(1.2))
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
                cx, cy = x0 + 76.5 * u, y0 + 18.5 * u * k
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


def close_rosto(camada, tipo='normal', dur=0.8, on_fim=None, y_rel=0.56):
    """Poe o close de anime por cima de tudo na camada."""
    try:
        camada.add_widget(_CloseRosto(tipo=tipo, dur=dur, on_fim=on_fim, y_rel=y_rel))
    except Exception as e:
        print(f"[cena] close: {e}")
        if on_fim:
            on_fim()


class _Sombra(Widget):''')
open(pk, 'w', encoding='utf-8', newline='\r\n').write(k)
open(pc, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
