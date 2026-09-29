p = r'C:\Users\kirit\travetefocus\app\cenas.py'
s = open(p, encoding='utf-8').read()


def troca(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)


troca('''            self._c2 = Color(0.85, 1.0, 1.0, 0)
            self._r2 = Rectangle(texture=tex, size=(0, 0))
            PopMatrix()
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)''', '''            self._c2 = Color(0.85, 1.0, 1.0, 0)
            self._r2 = Rectangle(texture=tex, size=(0, 0))
            PopMatrix()
        # forma Mugetsu: nevoa de pixels azul e roxa subindo das bordas da lamina
        self._fios = []
        self._lote = K.LotePixels(self.canvas, (
            ('azul', (0.36, 0.56, 1.0, 0.95)), ('azul2', (0.60, 0.80, 1.0, 0.95)),
            ('roxo', (0.62, 0.32, 1.0, 0.95)), ('lilas', (0.84, 0.68, 1.0, 0.95)),
            ('fundo', (0.30, 0.14, 0.62, 0.8))))
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)''')
troca('''                self._c1.a = self._c2.a = 0
                k.luz = 0.0
                return''', '''                self._c1.a = self._c2.a = 0
                k.luz = 0.0
                if self._fios:
                    self._fios = []
                    self._lote.desenhar({})
                return''')
troca('''            l1, w1 = comp * 1.3, k.ps * (6 + 6 * f)
            self._r1.pos, self._r1.size = (cx - l1 / 2, cy - w1 / 2), (l1, w1)
            self._c1.a = 0.55 * f * tremor''', '''            l1, w1 = comp * 1.3, k.ps * ((8 + 7 * f) if mug else (6 + 6 * f))
            self._r1.pos, self._r1.size = (cx - l1 / 2, cy - w1 / 2), (l1, w1)
            self._c1.a = (0.75 if mug else 0.55) * f * tremor
            self._nevoa(dt, k, hx, hy, tx, ty, comp, f if mug else 0.0)''')
troca('''    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)


class _Fluxo(Widget):''', '''    def _nevoa(self, dt, k, hx, hy, tx, ty, comp, f):
        """Aura da espada na forma Mugetsu: fiapos curtos azuis e roxos,
        misturados, que nascem nas duas bordas da lamina e sobem ondulando
        (na grade de pixels do Yoru)."""
        if f < 0.05:
            if self._fios:
                self._fios = []
                self._lote.desenhar({})
            return
        te = k.ps / float(K.R)
        while len(self._fios) < int(30 * f):
            self._fios.append({'s': random.uniform(0.14, 1.02), 'lado': random.choice((-1, 1)), 't': 0.0,
                               'vida': random.uniform(0.25, 0.5), 'alt': random.uniform(4, 10),
                               'fase': random.uniform(0, 6.3),
                               'cor': random.choice(('azul', 'azul2', 'roxo', 'roxo', 'lilas'))})
        ux, uy = (tx - hx) / comp, (ty - hy) / comp
        nx, ny = -uy, ux
        pontos = {}
        vivos = []
        for w in self._fios:
            w['t'] += dt
            v = w['t'] / w['vida']
            if v >= 1.0:
                continue
            vivos.append(w)
            afasta = (7.5 + 2.0 * v) * te * w['lado']
            bx = hx + (tx - hx) * w['s'] + nx * afasta
            by = hy + (ty - hy) * w['s'] + ny * afasta
            alt = w['alt'] * math.sin(math.pi * v)
            n = int(alt) + 1
            for i in range(n):
                u = i / float(max(1, n))
                x = bx + math.sin(w['fase'] + self._t * 12.0 - u * 3.0) * 1.4 * te * u
                y = by + i * te
                X = k.x + math.floor((x - k.x) / te) * te
                Y = k.y + math.floor((y - k.y) / te) * te
                larg = 2 if u < 0.35 else 1
                pontos.setdefault(w['cor'] if u < 0.75 else 'fundo', []).append((X, Y, larg * te, te))
        self._fios = vivos
        self._lote.desenhar(pontos, min(1.0, f * 1.3))

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)


class _Fluxo(Widget):''')
s = s.replace('K.ChamasReiatsu(kk, n_max=900, linguas=42)', 'K.ChamasReiatsu(kk, linguas=52)')
s = s.replace('K.ChamasReiatsu(kk, n_max=240, linguas=24, frente=True)', 'K.ChamasReiatsu(kk, linguas=24, frente=True)')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
