"""Baloes de fala estilo MANGA CLASSICO (escolha do usuario, 29/09/2026):
- fala: balao branco oval com contorno preto grosso e liso, rabinho curvo
  ate a boca, fonte de quadrinho (Comic Neue Bold) com folga nas bordas;
- grito (BAN! / KAI!): explosao com pontas regulares, sombra deslocada,
  fonte Bangers inclinada e um tremor;
- entra com um "pop" (cresce passando do ponto e volta) e sai encolhendo.
Fontes livres (SIL OFL 1.1), licencas junto no APK."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

NOVO = '''class BalaoFala(Widget):
    """Balao de fala de manga (texto, sem voz) preso na cabeca do boneco `k`.
    tipo 'fala' = balao oval branco com contorno preto grosso e rabinho curvo
    ate a boca; 'grito' = explosao de pontas regulares com sombra (BAN!/KAI!).
    Entra num pop (cresce passando do ponto e volta), o grito treme, e some
    encolhendo depois de `dur`."""

    def __init__(self, texto, k, tipo='fala', dur=1.4, font_size=None, cor_texto=(0.05, 0.05, 0.10),
                 lado=None, on_fim=None, cor_sombra=None, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k, self.tipo, self.dur = k, tipo, dur
        self._on_fim = _Uma(on_fim)
        self.t = 0.0
        grito = tipo == 'grito'
        fs = font_size or (sp(40) if grito else sp(19))
        fonte = 'Bangers-Regular.ttf' if grito else 'ComicNeue-Bold.ttf'
        try:
            cl = CoreLabel(text=texto, font_name=fonte, font_size=fs)
            cl.refresh()
        except Exception:
            cl = CoreLabel(text=texto, font_name='rajdhani.ttf', font_size=fs, bold=True)
            cl.refresh()
        self._tex_txt = cl.texture
        tw, th_ = self._tex_txt.size
        px, py = _topo_cabeca(k)
        W = Window.width
        if lado is None:
            lado = -1 if px > W * 0.55 else 1
        self.lado = lado
        contorno = dp(3.2) if grito else dp(2.6)
        if grito:
            rx, ry = tw * 0.5 + dp(26), th_ * 0.5 + dp(22)
            pontos = self._explosao(rx, ry)
            cauda = None
        else:
            rx, ry = tw * 0.5 * 1.18 + dp(14), th_ * 0.5 * 1.25 + dp(9)
            pontos, cauda = self._oval_com_rabo(rx, ry, lado)
        # o corpo do balao fica acima e para o lado; a ponta do rabo (0, 0) na boca
        self._corpo = (lado * (rx * 0.35 + dp(6)), ry + dp(18) if not grito else ry + dp(10))
        ox, oy = self._corpo
        with self.canvas:
            PushMatrix()
            self._tr = Translate(0, 0)
            self._rot = Rotate(angle=0, origin=(0, 0))
            self._sc = Scale(1, 1, 1)
            if grito:                                              # sombra deslocada (manga)
                cs = cor_sombra or (0.10, 0.04, 0.18)
                self._c_sombra = Color(cs[0], cs[1], cs[2], 0.9)
                Mesh(vertices=self._leque(pontos, ox + dp(4), oy - dp(4)), indices=list(range(len(pontos) + 2)),
                     mode='triangle_fan')
            else:
                self._c_sombra = None
            self._c = Color(1, 1, 1, 1)
            Mesh(vertices=self._leque(pontos, ox, oy), indices=list(range(len(pontos) + 2)), mode='triangle_fan')
            self._cl = Color(0.04, 0.04, 0.08, 1)
            lin = []
            for (x, y) in pontos:
                lin += [ox + x, oy + y]
            SmoothLine(points=lin, width=contorno, close=True)
            self._ct = Color(cor_texto[0], cor_texto[1], cor_texto[2], 1)
            self._rt = Rectangle(texture=self._tex_txt, size=(tw, th_),
                                 pos=(ox - tw / 2.0, oy - th_ / 2.0 + (dp(1) if grito else dp(0.5))))
            PopMatrix()
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)
        self._tick(0)

    @staticmethod
    def _leque(pontos, ox, oy):
        """Vertices de um triangle_fan: o centro e a volta fechada."""
        vs = [ox, oy, 0, 0]
        for (x, y) in pontos + [pontos[0]]:
            vs += [ox + x, oy + y, 0, 0]
        return vs

    @staticmethod
    def _explosao(rx, ry, n=16):
        """Pontas regulares (com uma variacao pequena, sempre a mesma)."""
        rnd = random.Random(7)
        pts = []
        for i in range(2 * n):
            a = math.pi * i / n + math.pi / (2 * n)
            fora = i % 2 == 0
            k = (1.0 + rnd.uniform(-0.06, 0.1)) if fora else (0.72 + rnd.uniform(-0.03, 0.03))
            pts.append((math.cos(a) * rx * k, math.sin(a) * ry * k))
        return pts

    @staticmethod
    def _oval_com_rabo(rx, ry, lado, n=72):
        """Oval (um pouco quadrado, como no manga) com um rabinho curvo que
        sai da parte de baixo e aponta para a boca, embaixo. Pontos em volta
        do centro do corpo; a ponta do rabo fica em (-ox, -oy) do corpo."""
        pts = []
        a_base = -math.pi / 2 - lado * 0.42          # onde o rabo nasce (embaixo, do lado da boca)
        larg = 0.26                                  # meia-largura da base (radianos)
        for i in range(n):
            a = 2 * math.pi * i / n
            d = (a - a_base + math.pi) % (2 * math.pi) - math.pi
            if abs(d) < larg:
                continue
            c, s = math.cos(a), math.sin(a)
            # superelipse (expoente 2.4): mais cheia que uma elipse
            x = rx * math.copysign(abs(c) ** (2 / 2.4), c)
            y = ry * math.copysign(abs(s) ** (2 / 2.4), s)
            pts.append((a, x, y))
        pts.sort(key=lambda q: (q[0] - a_base - larg) % (2 * math.pi))
        volta = [(x, y) for _, x, y in pts]
        # rabinho: da borda (fim da volta) ate a ponta e de volta ao comeco, em curva
        x0, y0 = volta[-1]
        x1, y1 = volta[0]
        ponta = (-lado * (rx * 0.35 + dp(6)) - lado * dp(2), -(ry + dp(18)) + dp(2))
        cauda = []
        for j in range(1, 9):
            u = j / 9.0
            meio = ((x0 + ponta[0]) / 2 + lado * dp(6), (y0 + ponta[1]) / 2)
            bx = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * meio[0] + u * u * ponta[0]
            by = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * meio[1] + u * u * ponta[1]
            cauda.append((bx, by))
        cauda.append(ponta)
        for j in range(1, 9):
            u = j / 9.0
            meio = ((x1 + ponta[0]) / 2 + lado * dp(3), (y1 + ponta[1]) / 2 + dp(2))
            bx = (1 - u) ** 2 * ponta[0] + 2 * (1 - u) * u * meio[0] + u * u * x1
            by = (1 - u) ** 2 * ponta[1] + 2 * (1 - u) * u * meio[1] + u * u * y1
            cauda.append((bx, by))
        return volta + cauda, ponta

    def _tick(self, dt):
        try:
            self.t += dt
            t = self.t
            if t >= self.dur or self.k.parent is None:
                return self.parar()
            grito = self.tipo == 'grito'
            # pop: cresce passando do ponto, volta com uma molinha; sai encolhendo
            pico = 1.25 if grito else 1.12
            if t < 0.07:
                s = 0.3 + (pico - 0.3) * (t / 0.07)
            elif t < 0.13:
                s = pico - (pico - 0.94) * (t - 0.07) / 0.06
            elif t < 0.19:
                s = 0.94 + 0.06 * (t - 0.13) / 0.06
            elif t > self.dur - 0.13:
                s = max(0.05, 1.0 - (t - (self.dur - 0.13)) / 0.13)
            else:
                s = 1.0 + (0.02 * math.sin(t * 9.0) if not grito else 0.0)
            px, py = _topo_cabeca(self.k)
            treme = (0.0, 0.0)
            if grito and 0.1 < t < 0.45:
                treme = (random.choice((-1, 0, 1)) * dp(2.5), random.choice((-1, 0, 1)) * dp(2.5))
            self._tr.xy = (round(px + treme[0]), round(py + treme[1]))
            self._sc.x = self._sc.y = s
            self._rot.angle = (-6.0 * self.lado) if grito else 0.0
            a = 1.0 if t < self.dur - 0.13 else max(0.0, s)
            self._c.a = self._cl.a = self._ct.a = a
            if self._c_sombra is not None:
                self._c_sombra.a = 0.9 * a
            return True
        except Exception as e:
            print(f"[balao] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)
        self._on_fim()
        return False
'''

c = open(os.path.join(A, 'cenas.py'), encoding='utf-8').read()
i0 = c.index('class BalaoFala(Widget):')
i1 = c.index('def balao(camada, texto, k,')
velho = c[i0:i1].rstrip('\n')
patch(os.path.join(A, 'cenas.py'), [
    (velho, NOVO.rstrip('\n')),
])
print('ok')
# (aplicado a parte: import SmoothLine em cenas.py e 'txt' no include_exts do buildozer.spec,
#  para as licencas OFL das fontes irem junto no APK)
