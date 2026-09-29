p = r'C:\Users\kirit\travetefocus\app\kirito.py'
s = open(p, 'rb').read().decode('utf-8').replace('\r\n', '\n')
a = s.index('class ChamasReiatsu(Widget):')
b = s.index('    def parar(self):', a)
novo = '''class ChamasReiatsu(Widget):
    """Fogo roxo da forma Mugetsu, com pixels do mesmo tamanho dos do Yoru.
    O fogo e feito de LINGUAS: cada uma nasce num ponto do contorno do
    corpo (mais na cabeca e nos ombros) e e desenhada inteira a cada quadro
    - uma coluna que sobe, ondula, tomba para tras com o vento, afina ate a
    ponta e esfria em degraus (branco -> lilas -> roxo -> roxo escuro); umas
    poucas puxam para o azul. Cada lingua cresce, balanca e se apaga, e
    outra nasce no lugar. Acompanha o corpo. Liga sozinho quando a pose
    esta na forma Mugetsu. `frente=True`: linguas finas por cima dele."""
    DEGRAUS = (((0.98, 0.94, 1.00), 1.0), ((0.82, 0.64, 1.00), 1.0), ((0.64, 0.34, 1.00), 0.95),
               ((0.46, 0.20, 0.86), 0.9), ((0.28, 0.10, 0.52), 0.72))
    DEGRAUS_AZUL = (((0.97, 0.93, 1.00), 1.0), ((0.55, 0.86, 1.00), 1.0), ((0.34, 0.55, 1.00), 0.95),
                    ((0.52, 0.30, 1.00), 0.9), ((0.30, 0.13, 0.58), 0.72))

    def __init__(self, k, n_max=520, linguas=30, frente=False, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k = k
        self.frente = frente
        self.n_linguas = linguas
        self._linguas = []
        cores = [('r%d' % i, (c[0], c[1], c[2], a)) for i, (c, a) in enumerate(self.DEGRAUS)]
        cores += [('a%d' % i, (c[0], c[1], c[2], a)) for i, (c, a) in enumerate(self.DEGRAUS_AZUL)]
        self._lote = LotePixels(self.canvas, cores)
        self._ev = Clock.schedule_interval(self._tick, 1 / 30.)

    def _nova_lingua(self, bordas):
        topo = max(y for _, y in bordas)
        a = random.choice(bordas)
        b = random.choice(bordas)
        tx, ty = a if a[1] >= b[1] else b            # prefere as bordas de cima
        alto = ty >= topo - 16 * E
        return {'tx': tx, 'ty': ty, 't': 0.0,
                'vida': random.uniform(0.4, 0.75) * (1.2 if alto else 1.0),
                'alt': random.uniform(12, 22) * E * (1.35 if alto else 1.0),
                'larg': random.uniform(0.8, 1.4) if self.frente else random.uniform(2.2, 4.2),
                'fase': random.uniform(0, 6.3), 'amp': random.uniform(1.0, 2.4) * E,
                'azul': random.random() < 0.18}

    def _tick(self, dt):
        try:
            k = self.k
            if k.parent is None or self.get_root_window() is None:
                return self.parar()
            te = k.ps / float(R)
            pose = k._pose
            ativo = pose.get('mugetsu') and k.opacity > 0.3
            bordas = bordas_pose(pose) if ativo else None
            if not bordas:
                self._linguas = []
                self._lote.desenhar({})
                return
            while len(self._linguas) < self.n_linguas:
                L = self._nova_lingua(bordas)
                L['t'] = random.uniform(0, L['vida'] * 0.8)    # nao nascem todas juntas
                self._linguas.append(L)
            ox, oy = k.x, k.y
            esp = k.espelhar
            pontos = {}
            vivas = []
            for L in self._linguas:
                L['t'] += dt
                v = L['t'] / L['vida']
                if v >= 1.0:
                    continue
                vivas.append(L)
                alt = L['alt'] * (0.35 + 0.65 * math.sin(math.pi * min(1.0, v * 1.3)))
                sobe = L['alt'] * 0.35 * v                  # a lingua toda sobe um pouco
                larg0 = L['larg'] * (1.0 - 0.6 * max(0.0, v - 0.55) / 0.45)
                pre = 'a' if L['azul'] else 'r'
                n = max(2, int(alt))
                for i in range(n):
                    u = i / float(n)
                    x = L['tx'] + math.sin(L['fase'] + L['t'] * 10.0 - u * 4.0) * L['amp'] * u - 0.3 * alt * u
                    y = L['ty'] + sobe + i
                    w = larg0 * (1.0 - u) ** 0.8
                    if w < 0.5 and i > 1:
                        w = 0.5 if (i % 2 == 0) else 0          # ponta fina, falhando
                    if w <= 0:
                        continue
                    lado = int(round(w * 2))                   # largura em texels
                    x0 = int(round(x - lado / 2.0))
                    if esp:
                        x0 = TW - x0 - lado
                    d = min(4, int(u * 4.2 + v * 1.4))
                    pontos.setdefault(pre + str(d), []).append(
                        (ox + x0 * te, oy + int(round(y)) * te, lado * te, te))
            self._linguas = vivas
            self._lote.desenhar(pontos, 0.8 if self.frente else 1.0)
        except Exception as e:
            print(f"[chamas] {e}")
            return self.parar()

'''
s = s[:a] + novo + s[b:]
# o lote aceita retangulos (x, y, largura, altura) alem de quadrados (x, y, lado)
velho = '''            for i, (x, y, t) in enumerate(pontos.get(nome, ())):
                vs.extend((x, y, 0, 0, x + t, y, 0, 0, x + t, y + t, 0, 0, x, y + t, 0, 0))'''
assert velho in s
s = s.replace(velho, '''            for i, r in enumerate(pontos.get(nome, ())):
                x, y, w = r[0], r[1], r[2]
                h = r[3] if len(r) > 3 else w
                vs.extend((x, y, 0, 0, x + w, y, 0, 0, x + w, y + h, 0, 0, x, y + h, 0, 0))''')
s = s.replace('''    desenhar({nome: [(x, y, lado), ...]})."""''', '''    desenhar({nome: [(x, y, lado) ou (x, y, largura, altura), ...]})."""''')
open(p, 'wb').write(s.replace('\n', '\r\n').encode('utf-8'))
print('ok')
