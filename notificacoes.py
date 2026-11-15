"""
notificacoes.py — TraveteFocus
LEVEL UP: quando o nivel sobe (lote novo, colado do WhatsApp, lote corrigido),
um painel dourado no estilo do app abre no meio da tela:
  - "LEVEL UP!" com um reflexo passando pelas letras;
  - LVL 4 -> 5 (os digitos rolam ate o nivel novo);
  - a barra de XP enche ate o fim e recomeca no nivel novo;
  - a cada 10 niveis o TITULO muda: painel maior com o titulo novo;
  - raios de luz girando atras, faiscas douradas, o Yoru comemorando,
    som de level up e vibracao de vitoria.
Fecha sozinho (3,6 s; titulo novo 4,8 s) ou com um toque. Um de cada vez.

Regras do app: nenhum callback de Clock deixa excecao escapar.
"""
import math

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Mesh, Line
from kivy.metrics import dp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

from animacoes_ui import _matriz, _chanfro, brilho_texto, decifrar, pulso, fmt_br

OURO = (1.0, 0.82, 0.18)
OURO_CLARO = (1.0, 0.93, 0.55)
ROXO = (0.72, 0.45, 1.0)

_FILA = []
_ATIVA = [None]


def conferir_level(xp_antes, xp_depois, atraso=0.0):
    """Se o XP passou de nivel, agenda o LEVEL UP (depois de `atraso` s, para
    o corte do +XP terminar). Devolve True se subiu."""
    try:
        from helpers import calcular_level, obter_titulo_level
        n0 = calcular_level(max(0, int(xp_antes)))[0]
        n1, xp_at, xp_nec = calcular_level(max(0, int(xp_depois)))
        if n1 <= n0:
            return False
        t0, t1 = obter_titulo_level(n0), obter_titulo_level(n1)
        titulo = t1 if t1 != t0 else None
        Clock.schedule_once(lambda dt: level_up(n0, n1, xp_at, xp_nec, titulo), atraso)
        return True
    except Exception as e:
        print(f"[level up] conferir: {e}")
        return False


def level_up(n0, n1, xp_atual=0, xp_necessario=1, titulo_novo=None):
    if _ATIVA[0] is not None:
        _FILA.append(lambda: level_up(n0, n1, xp_atual, xp_necessario, titulo_novo))
        return
    try:
        _LevelUp(n0, n1, xp_atual, xp_necessario, titulo_novo)
    except Exception as e:
        print(f"[level up] {e}")
        _proxima()


def _proxima():
    _ATIVA[0] = None
    if _FILA:
        fn = _FILA.pop(0)
        Clock.schedule_once(lambda dt: fn(), 0.3)


class _LevelUp(FloatLayout):
    T_ABRE = 0.30

    def __init__(self, n0, n1, xp_atual, xp_necessario, titulo_novo):
        super().__init__(size_hint=(None, None), size=Window.size, pos=(0, 0))
        _ATIVA[0] = self
        self.n0, self.n1 = n0, n1
        self.grande = titulo_novo is not None
        self.dur = 4.8 if self.grande else 3.6
        self.t = 0.0
        self._fechando = None
        self._quadro_raios = -1
        W, H = Window.size
        self.pw = min(W * 0.88, dp(470))
        self.ph = dp(300) if self.grande else dp(236)
        self.px = (W - self.pw) / 2.0
        self.py = H * 0.56 - self.ph / 2.0
        cx, cy = W / 2.0, self.py + self.ph / 2.0
        self.c = (cx, cy)

        # fundo escuro + raios de luz girando atras do painel
        with self.canvas.before:
            self._c_fundo = Color(0, 0, 0, 0)
            Rectangle(pos=(0, 0), size=(W, H))
            self._c_raios = Color(OURO[0], OURO[1], OURO[2], 0)
            n = 12 if self.grande else 8
            self._m_raios = Mesh(mode='triangles', vertices=[0.0] * (n * 12), indices=list(range(n * 3)))

        # o painel (chanfrado, dourado; titulo novo com faixa roxa)
        self.painel = FloatLayout(size_hint=(None, None), size=(self.pw, self.ph), pos=(self.px, self.py))
        c = dp(16)
        pts = _chanfro(self.px, self.py, self.pw, self.ph, c)
        vs = [cx, cy, 0, 0]
        for i in range(0, len(pts), 2):
            vs += [pts[i], pts[i + 1], 0, 0]
        vs += [pts[0], pts[1], 0, 0]
        with self.painel.canvas.before:
            Color(0.07, 0.055, 0.01, 0.97)
            Mesh(mode='triangle_fan', vertices=vs, indices=list(range(len(vs) // 4)))
            Color(OURO[0], OURO[1], OURO[2], 0.08)                        # faixas de varredura
            for k in range(1, 6):
                Rectangle(pos=(self.px + dp(10), self.py + self.ph * k / 6.0), size=(self.pw - dp(20), 1))
            Color(OURO[0], OURO[1], OURO[2], 0.25)
            Line(points=_chanfro(self.px + dp(5), self.py + dp(5), self.pw - dp(10), self.ph - dp(10), c - dp(3)),
                 width=1, close=True)
            Color(OURO[0], OURO[1], OURO[2], 1)
            Line(points=pts, width=dp(1.3), close=True)
            # cantos acesos (detalhe de HUD)
            self._c_cantos = Color(*OURO_CLARO, 0.75)
            for (ax, ay, sx, sy) in ((self.px, self.py + self.ph, 1, -1), (self.px + self.pw, self.py + self.ph, -1, -1),
                                     (self.px, self.py, 1, 1), (self.px + self.pw, self.py, -1, 1)):
                Line(points=[ax + sx * dp(4), ay + sy * (c + dp(10)), ax + sx * dp(4), ay + sy * (c + dp(2))],
                     width=dp(1.6))
            self._c_traços = Color(*OURO_CLARO, 0)
            self._linha_topo = Line(width=dp(1.5))
            self._linha_base = Line(width=dp(1.5))
            self._c_selo = Color(*ROXO, 0)
            if self.grande:
                y_selo = self.py + dp(66)
                sx0, sx1 = self.px + self.pw * 0.25, self.px + self.pw - dp(19)
                Line(points=[sx0, y_selo - dp(18), sx0, y_selo + dp(18), sx0 + dp(5), y_selo + dp(23)],
                     width=dp(1.4))
                Line(points=[sx1, y_selo + dp(18), sx1, y_selo - dp(18), sx1 - dp(5), y_selo - dp(23)],
                     width=dp(1.4))
        self.add_widget(self.painel)

        topo = self.py + self.ph
        def rotulo(texto, y, fs, cor, fonte='orbitron.ttf', alt=dp(40), lado=0.0):
            # lado > 0: o texto fica mais para a direita (o Yoru comemora no canto esquerdo)
            x = self.px + dp(15) + self.pw * lado
            l = Label(text=texto, markup=True, font_name=fonte, font_size=fs, color=cor,
                      halign='center', valign='middle', size_hint=(None, None),
                      size=(self.pw - dp(30) - self.pw * lado, alt), pos=(x, y - alt / 2.0))
            l.text_size = l.size
            l.opacity = 0
            self.painel.add_widget(l)
            return l
        self.l_sis = rotulo("SISTEMA  //  NOTIFICAÇÃO", topo - dp(24), '9sp', (OURO[0], OURO[1], OURO[2], 0.6))
        self.l_titulo = rotulo("[b]LEVEL UP![/b]", topo - dp(66), '32sp', (OURO_CLARO[0], OURO_CLARO[1], OURO_CLARO[2], 1),
                               alt=dp(54))
        self.l_nivel = rotulo(f"LVL  {n0}", topo - dp(116), '24sp', (1, 1, 1, 1), alt=dp(40))
        from efeitos import BarraMeta
        self.barra = BarraMeta(size_hint=(None, None), size=(self.pw * 0.72, dp(26)),
                               pos=(self.px + self.pw * 0.14, topo - dp(158)))
        self.barra.opacity = 0
        self.barra.definir(0, maximo=100, cor=(OURO[0], OURO[1], OURO[2], 1), animar=False)
        self.painel.add_widget(self.barra)
        self._xp = (xp_atual, max(1, xp_necessario))
        falta = max(0, xp_necessario - xp_atual)
        self.l_falta = rotulo(f"[color=#c8b780]próximo nível em [b]{fmt_br(falta)} XP[/b][/color]",
                              topo - dp(180), '14sp', (1, 1, 1, 1), fonte='rajdhani.ttf', alt=dp(24))
        self.l_rank = self.l_rank2 = None
        if self.grande:
            self.l_rank = rotulo("NOVO TÍTULO", topo - dp(214), '10sp', (ROXO[0], ROXO[1], ROXO[2], 1), lado=0.2)
            self.l_rank2 = rotulo(f"[b]{titulo_novo}[/b]", topo - dp(244), '18sp', (0.93, 0.86, 1.0, 1),
                                  fonte='rajdhani.ttf', lado=0.2)
        self.l_toque = rotulo("toque para continuar", self.py + dp(16), '9sp', (1, 1, 1, 0.3),
                              fonte='rajdhani.ttf', alt=dp(18))

        self._tr, self._sc = _matriz(self.painel)
        self._sc.x = 0.94
        self.painel.opacity = 0
        Window.add_widget(self)
        try:
            import kirito as K
            self.faiscas = K.Faiscas(n_max=90)
            Window.add_widget(self.faiscas)
        except Exception as e:
            print(f"[level up] faiscas: {e}")
            self.faiscas = None

        self._marcos = [(0.18, self._abriu), (0.75, self._sobe_numero), (1.0, self._enche),
                        (1.19, self._numero_chegou), (2.0, self._rank), (2.2, self._recomeca_xp)]
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    # ── momentos ────────────────────────────────────────────────────
    def _abriu(self):
        try:
            import som
            som.tocar_level_up()
        except Exception:
            pass
        try:
            import tatil
            tatil.vitoria()
        except Exception:
            pass
        from animacoes_ui import entrada_cascata
        itens = [self.l_sis, self.l_titulo, self.l_nivel, self.barra, self.l_falta, self.l_toque]
        entrada_cascata(itens, atraso=0.05, dy=dp(10), duracao=0.3, escala=False)
        brilho_texto(self.l_titulo, periodo=2.8, atraso=0.35, duracao=0.65, forca=0.70)
        desloc = self.pw * 0.34
        for lado in (-1, 1):
            self._estoura(self.c[0] + lado * desloc, self.c[1] + self.ph * 0.27, 14, dp(220))

    def _sobe_numero(self):
        decifrar(self.l_nivel, f"LVL  {self.n1}", duracao=0.42)

    def _numero_chegou(self):
        try:
            self.l_nivel.color = (OURO_CLARO[0], OURO_CLARO[1], OURO_CLARO[2], 1)
            pulso(self.l_nivel, 1.12, 0.36)
            x, y = self.l_nivel.center
            self._estoura(x, y, 18, dp(210))
            from cenas import kirito_nivel                 # o Yoru comemora apontando para o numero
            kirito_nivel(self.l_nivel)
        except Exception as e:
            print(f"[level up] numero: {e}")

    def _enche(self):
        # a barra do nivel de antes enche ate o fim... e recomeca no novo
        self.barra.definir(100, maximo=100, animar=True)

    def _recomeca_xp(self):
        at, nec = self._xp
        self.barra.definir(0, maximo=100, animar=False)
        self.barra.definir(100.0 * at / nec, maximo=100, animar=True)

    def _rank(self):
        if not self.grande:
            return
        from animacoes_ui import entrada_cascata
        entrada_cascata([self.l_rank, self.l_rank2], atraso=0.12, dy=dp(12), duracao=0.35)
        brilho_texto(self.l_rank2, periodo=9, atraso=0.3, duracao=0.7, forca=0.8)
        self._estoura(self.c[0], self.l_rank2.center_y, 24, dp(215), cor=ROXO)
        try:
            import som
            som.tocar('vidro')
        except Exception:
            pass

    def _estoura(self, x, y, n, forca, cor=OURO):
        if self.faiscas is not None:
            try:
                self.faiscas.estourar(x, y, cor, n=n, forca=forca, tam=dp(3), gravidade=dp(260))
            except Exception:
                pass

    # ── relogio ─────────────────────────────────────────────────────
    def _tick(self, dt):
        try:
            self.t += dt
            t = self.t
            while self._fechando is None and self._marcos and t >= self._marcos[0][0]:
                _, fn = self._marcos.pop(0)
                try:
                    fn()
                except Exception as e:
                    print(f"[level up] momento: {e}")
            if self._fechando is None and t >= self.dur:
                self._fechar()
            if self._fechando is not None:
                k = min(1.0, (t - self._fechando) / 0.26)
                e = k * k * (3 - 2 * k)
                self._sc.y = 1 - 0.08 * e
                self._tr.y = -dp(5) * e
                self.painel.opacity = 1 - e
                self._c_fundo.a = 0.62 * (1 - e)
                self._c_raios.a = 0.0
                if k >= 1:
                    self._remover()
                    return False
                return True
            # abrir: o fundo escurece e o painel abre de dentro para fora
            ka = min(1.0, t / self.T_ABRE)
            ea = 1 - (1 - ka) ** 3
            self._c_fundo.a = 0.62 * ea
            self._sc.x = 0.94 + 0.06 * ea
            self._tr.y = -dp(7) * (1 - ea)
            self.painel.opacity = min(1.0, ea * 1.6)
            self._raios(t, ea)
            self._detalhes(t, ea)
            return True
        except Exception as e:
            print(f"[level up] quadro: {e}")
            self._remover()
            return False

    def _raios(self, t, forca):
        """Geometria atualizada a 24 Hz, com a intensidade suavizada a cada quadro."""
        quadro = int(t * 24)
        if quadro != self._quadro_raios:
            self._quadro_raios = quadro
            n = 12 if self.grande else 8
            ox, oy = self.c
            r = max(self.width, self.height) * 0.75
            ri = self.ph * 0.48
            pontos = []
            for i in range(n):
                a = quadro * (0.22 / 24) + 2 * math.pi * i / n
                pontos += [ox + math.cos(a) * ri, oy + math.sin(a) * ri, 0, 0,
                           ox + math.cos(a - 0.022) * r, oy + math.sin(a - 0.022) * r, 0, 0,
                           ox + math.cos(a + 0.022) * r, oy + math.sin(a + 0.022) * r, 0, 0]
            self._m_raios.vertices = pontos
        self._c_raios.a = (0.068 if self.grande else 0.040) * forca * (0.9 + 0.1 * math.sin(t * 2.2))

    def _detalhes(self, t, forca):
        """Dois reflexos na moldura no início e quando o nível novo assenta."""
        fase = t if t < 1.18 else t - 1.18
        k = min(1.0, fase / 0.72)
        self._c_traços.a = 0.90 * math.sin(math.pi * k) * forca
        if k < 1:
            cx, _ = self.c
            d = self.pw * 0.36 * k
            ponta = min(dp(19), self.pw * 0.12) * k
            topo, base = self.py + self.ph - dp(5), self.py + dp(5)
            self._linha_topo.points = [cx + d - ponta, topo, cx + d, topo]
            self._linha_base.points = [cx - d + ponta, base, cx - d, base]
        self._c_cantos.a = forca * (0.67 + 0.28 * math.sin(math.pi * k))
        if self.grande:
            revela = min(1.0, max(0.0, (t - 2.0) / 0.36))
            self._c_selo.a = 0.65 * revela * (0.92 + 0.08 * math.sin(3 * t))

    def _fechar(self):
        if self._fechando is None:
            self._fechando = self.t

    def on_touch_down(self, touch):
        if self.t > 0.6:
            self._fechar()
        return True                                      # nada embaixo recebe o toque

    def on_touch_move(self, touch):
        return True

    def on_touch_up(self, touch):
        return True

    def _remover(self):
        try:
            if self._ev is not None:
                self._ev.cancel()
                self._ev = None
            Window.remove_widget(self)
            self.painel.clear_widgets()                  # os reflexos repetidos param junto
            if self.faiscas is not None:
                f = self.faiscas
                Clock.schedule_once(lambda dt: Window.remove_widget(f), 1.2)
        except Exception as e:
            print(f"[level up] remover: {e}")
        _proxima()
