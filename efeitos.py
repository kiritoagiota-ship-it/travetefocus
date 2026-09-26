"""
efeitos.py — TraveteFocus v6.0 AINCRAD EDITION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGRA DE OURO:
  InputHolografico NUNCA sobrescreve insert_text, do_backspace,
  keyboard_on_key_down, nem qualquer método de buffer interno.
  Usa SOMENTE bind() passivo em propriedades já computadas (focus, text).
"""

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import (
    Color, Rectangle, RenderContext, Ellipse, Line,
    PushMatrix, PopMatrix, Rotate, Scale, Triangle, RoundedRectangle,
    Translate, Mesh
)
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import Label as CoreLabel
from kivy.animation import Animation
import math
import random

# Som de clique — importado do módulo independente
try:
    from som import tocar_click
except ImportError:
    def tocar_click(): pass

# ═══════════════════════════════════════════════════════════
#  SHADER GLSL — REATOR ARC
# ═══════════════════════════════════════════════════════════

_SHADER_FS = '''
#ifdef GL_ES
precision mediump float;
#endif
uniform float time;
uniform vec2  resolution;
uniform vec2  offset;
uniform float build_progress;
uniform vec3  core_color;

float rand(vec2 co){
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

void main(void){
    vec2 lp = gl_FragCoord.xy - offset;
    vec2 p  = (lp / resolution) * 2.0 - 1.0;
    float md = min(resolution.x, resolution.y);
    p.x *= resolution.x / md;
    p.y *= resolution.y / md;

    if(core_color.r > 0.8 && core_color.g < 0.2){
        p.x += sin(time * 60.0 + p.y * 25.0) * 0.04;
        if(rand(vec2(time, p.y)) > 0.85) p.x += 0.12;
    }

    float a  = atan(p.y, p.x);
    float r  = length(p);
    float n  = rand(floor(p * 45.0));
    float an = (a + 3.14159) / 6.28318;

    float mask = 0.0;
    if(build_progress > 0.0){
        float bs = build_progress * 1.5;
        if(an < bs && n < (bs - an + 0.4)) mask = 1.0;
    }

    float pulse = sin(time * 4.0) * 0.04;
    float e1    = sin(a * 12.0 + time * 8.0) * 0.05;
    float e2    = cos(a * 10.0 - time * 4.0) * 0.06;
    float gear  = abs(sin(a * 24.0)) * 0.015;

    if(build_progress > 0.98){
        mask  = 1.0;
        pulse = sin(time * 20.0) * 0.08;
        e1    = sin(a * 16.0 + time * 18.0) * 0.08;
        e2    = cos(a * 12.0 - time * 12.0) * 0.08;
        gear  = abs(sin(a * 24.0 + time * 8.0)) * 0.03;
    }

    float core = (0.1   / abs(r - 0.10 - pulse * 0.5)) * mask * (build_progress + 0.2);
    float r1   = (0.018 / abs(r - 0.45 - e1))          * mask;
    float r2   = (0.022 / abs(r - 0.65 - e2))          * mask;
    float r3   = (0.008 / abs(r - 0.85 - gear))        * mask;

    float sparks = 0.0;
    if(build_progress > 0.7 && rand(vec2(time * 10.0, a)) > 0.98)
        sparks = (0.03 / abs(r - rand(vec2(time)) * 0.9)) * mask;

    vec3 col  = core_color * 1.8 * core;
    col += vec3(core_color.r * 0.7, core_color.g * 0.9, core_color.b) * r1;
    col += vec3(core_color.r * 0.8, core_color.g * 0.3, core_color.b * 0.9) * r2;
    col += core_color * 0.5 * r3;
    col += vec3(1.0) * sparks;

    float alpha = clamp(1.4 - r, 0.0, 1.0);
    gl_FragColor = vec4(col, alpha);
}
'''


class ReatorArcShader(Widget):
    time           = NumericProperty(0.0)
    build_progress = NumericProperty(0.0)
    core_color     = ListProperty([0.0, 0.89, 1.0])
    _shader_ok     = False
    _is_android    = False

    def __init__(self, **kwargs):
        from kivy.utils import platform as _plat
        self._is_android = (_plat == 'android')
        self._anim_t = 0.0
        if not self._is_android:
            try:
                self.canvas = RenderContext(
                    use_parent_projection=True,
                    use_parent_modelview=True,
                    use_parent_frag_modelview=True)
            except Exception:
                pass
        super().__init__(**kwargs)
        if not self._is_android:
            try:
                self.canvas.shader.fs = _SHADER_FS
                self._shader_ok = True
            except Exception as e:
                print(f"[SHADER] indisponivel: {e}")
        with self.canvas:
            if self._is_android:
                self._fb_c1 = Color(0, 0.89, 1, 0.55)
                self._fb_a1 = Line(width=2.5)
                self._fb_c2 = Color(0, 0.89, 1, 0.30)
                self._fb_a2 = Line(width=1.5)
                self._fb_c3 = Color(0, 0.89, 1, 0.15)
                self._fb_a3 = Line(width=1.0)
            else:
                self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)
        self._clock_ev = None

    def on_parent(self, inst, parent):
        if parent is not None:
            if self._clock_ev is None:
                self._clock_ev = Clock.schedule_interval(self._tick, 1/60)
        else:
            if self._clock_ev is not None:
                self._clock_ev.cancel()
                self._clock_ev = None

    def _upd(self, *_):
        if not self._is_android and hasattr(self, 'rect'):
            self.rect.pos  = self.pos
            self.rect.size = self.size

    def _tick(self, dt):
        self._anim_t += dt
        t = self._anim_t
        if self._is_android:
            cx, cy = self.center
            r  = min(self.width, self.height) * 0.38
            cc = self.core_color[:3] if len(self.core_color) >= 3 else [0, 0.89, 1]
            a1 = (t * 100) % 360
            a2 = (-t * 70 + 180) % 360
            a3 = (t * 140 + 60) % 360
            self._fb_c1.rgba   = (*cc, 0.55)
            self._fb_a1.circle = (cx, cy, r, a1, a1 + 270)
            self._fb_c2.rgba   = (*cc, 0.30)
            self._fb_a2.circle = (cx, cy, r * 0.65, a2, a2 + 190)
            self._fb_c3.rgba   = (*cc, 0.18)
            self._fb_a3.circle = (cx, cy, r * 0.35, a3, a3 + 130)
            return
        if not self._shader_ok:
            return
        try:
            self.canvas['time']           = t
            self.canvas['resolution']     = (float(self.width), float(self.height))
            px, py = self.to_window(self.x, self.y)
            self.canvas['offset']         = (float(px), float(py))
            self.canvas['build_progress'] = float(self.build_progress)
            self.canvas['core_color']     = tuple(float(c) for c in self.core_color[:3])
            self.canvas.ask_update()
        except (TypeError, AttributeError) as e:
            print(f"[SHADER] desabilitado: {e}")
            self._shader_ok = False


class InputHolografico(TextInput):
    """
    CRÍTICO: esta classe NÃO sobrescreve NENHUM método de buffer do Kivy.
    Toda animação é feita via bind() passivo em propriedades já resolvidas.
    Isso garante que o teclado nativo tenha acesso irrestrito ao campo.
    """
    borda_color = ListProperty([0, 0.9, 1, 0.25])

    def __init__(self, **kwargs):
        kwargs.setdefault('multiline', False)
        super().__init__(**kwargs)
        self.bind(focus=self._ao_focar)

    def _bind_keyboard(self):
        """
        No Android: suprime teclado do sistema quando este campo
        tem teclado customizado anexado (_teclado_custom_ok=True).
        No desktop: comportamento normal do TextInput.
        """
        try:
            from kivy.utils import platform as _p
            if _p == 'android' and getattr(self, '_teclado_custom_ok', False):
                return   # teclado customizado SAO cuida deste campo
        except Exception:
            pass
        super()._bind_keyboard()
        self.bind(text=self._ao_digitar)

    def _ao_focar(self, inst, ativo):
        """Anima a borda ao ganhar/perder foco."""
        if ativo:
            Animation(borda_color=[0.55, 0.05, 0.95, 1.0],
                      duration=0.22, transition='out_quad').start(self)
        else:
            Animation(borda_color=[0, 0.9, 1, 0.25],
                      duration=0.28, transition='out_quad').start(self)

    def _ao_digitar(self, inst, valor):
        """
        Efeito hacking/digitalização a cada tecla.
        — foreground_color: flash branco puro -> ciano
        — borda_color: pulso de alta intensidade -> retorna ao estado de foco
        Tudo via bind passivo, sem tocar no buffer.
        """
        if not valor:
            return
        # Flash do texto: branco -> ciano (sensação de materialização)
        Animation.cancel_all(self, 'foreground_color')
        (Animation(foreground_color=(1.0, 1.0, 1.0, 1.0),
                   duration=0.04, transition='out_quad') +
         Animation(foreground_color=(0.0, 0.92, 1.0, 1.0),
                   duration=0.18, transition='out_quad')).start(self)

        # Pulso da borda: energia explode e retorna ao estado de foco (roxo)
        Animation.cancel_all(self, 'borda_color')
        (Animation(borda_color=[0.85, 0.15, 1.0, 1.0],
                   duration=0.04, transition='out_quad') +
         Animation(borda_color=[0.55, 0.05, 0.95, 1.0],
                   duration=0.22, transition='out_quad')).start(self)


# ═══════════════════════════════════════════════════════════
#  ESPADA HOLOGRÁFICA
# ═══════════════════════════════════════════════════════════

class EspadaHolografica(Widget):
    """Espada em holograma ao lado do titulo da loading.
    estilo 'katana' (Elucidator): lamina curva de um fio, hamon, tsuba oval
    e cabo trancado. estilo 'cristal' (Dark Repulser): lamina reta de
    cristal facetada, guarda com gema.
    Ao aparecer (opacidade 0 -> 1) a lamina cresce a partir da guarda; depois
    flutua, um brilho percorre a lamina, linhas de holograma sobem e
    faiscas saem dela. Desenho montado uma vez; a animacao so mexe em
    transformacoes e cores (leve)."""
    escala    = NumericProperty(0)
    opacidade = NumericProperty(0)
    cor       = ListProperty([0, 0.89, 1, 1])
    estilo    = StringProperty('katana')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._t = 0.0
        self._ev = None
        self._revelou = False
        self._flash = 0.0
        self._faiscas = []
        self._montar()
        self.bind(pos=self._posicionar, size=self._posicionar,
                  escala=self._ao_mudar, opacidade=self._ao_mudar,
                  cor=lambda *_: self._montar(), estilo=lambda *_: self._montar())

    # ── desenho (uma vez) ────────────────────────────────────────────
    def _montar(self, *_):
        self.canvas.clear()
        r, g, b = self.cor[0], self.cor[1], self.cor[2]
        L = dp(124)                         # comprimento total (ponta para cima)
        y0 = -L / 2.0                       # pomo
        y_guarda = y0 + dp(31)
        y_ponta = L / 2.0
        self._y_guarda, self._y_ponta = y_guarda, y_ponta
        katana = self.estilo != 'cristal'
        try:
            from infinito import textura_radial
            tex = textura_radial()
        except Exception:
            tex = None
        self._cores = []                    # (Color, alfa_base)

        def cor(a, clareia=0.0):
            c = Color(r + (1 - r) * clareia, g + (1 - g) * clareia, b + (1 - b) * clareia, 0)
            self._cores.append((c, a))
            return c

        # geometria da lamina (centro, largura) de baixo para cima
        n = 22
        esq, dirt, meio = [], [], []
        comp_l = y_ponta - (y_guarda + dp(3))
        for i in range(n + 1):
            t = i / float(n)
            y = y_guarda + dp(3) + comp_l * t
            if katana:
                x = -dp(4.5) * t * t                     # sori: a ponta volta para as costas
                w = dp(3.4) * (1 - 0.22 * t)
                if t > 0.88:                             # kissaki
                    w *= max(0.0, 1 - (t - 0.88) / 0.12)
                esq.append((x - w * 0.8, y))             # costas (mais fina)
                dirt.append((x + w, y))                  # fio
            else:
                x = 0.0
                w = dp(4.2) * (1 - 0.15 * t) if t < 0.86 else dp(4.2) * 0.87 * max(0.0, 1 - (t - 0.86) / 0.14)
                esq.append((x - w, y))
                dirt.append((x + w, y))
            meio.append((x, y))
        self._meio = meio

        with self.canvas:
            PushMatrix()
            self._tr = Translate(0, 0)
            self._rot = Rotate(angle=0, origin=(0, 0))
            self._sc = Scale(1, 1, 1)
            # aura
            cor(0.22)
            self._aura = Rectangle(texture=tex, pos=(-dp(26), y0 - dp(10)), size=(dp(52), L + dp(20)))
            # lamina (cresce a partir da guarda ao aparecer)
            PushMatrix()
            self._sc_lamina = Scale(1, 1, 1, origin=(0, y_guarda))
            idx = list(range(2 * (n + 1)))
            if katana:
                cor(0.30)
                Mesh(mode='triangle_strip', indices=idx,
                     vertices=[v for p, q in zip(esq, dirt) for v in (p[0], p[1], 0, 0, q[0], q[1], 0, 0)])
                cor(0.95, 0.55)
                Line(points=[v for p in dirt for v in p], width=dp(1.1))          # fio
                cor(0.55)
                Line(points=[v for p in esq for v in p], width=dp(0.9))           # costas
                hamon = []
                for i, (p, q) in enumerate(zip(meio, dirt)):
                    if 0 < i < n - 1:
                        k = 0.35 + 0.18 * math.sin(i * 1.9)
                        hamon.extend((p[0] + (q[0] - p[0]) * k, p[1]))
                cor(0.6, 0.35)
                Line(points=hamon, width=dp(0.8))                                   # hamon
            else:
                cor(0.40, 0.25)
                Mesh(mode='triangle_strip', indices=idx,
                     vertices=[v for p, q in zip(esq, meio) for v in (p[0], p[1], 0, 0, q[0], q[1], 0, 0)])
                cor(0.18)
                Mesh(mode='triangle_strip', indices=idx,
                     vertices=[v for p, q in zip(meio, dirt) for v in (p[0], p[1], 0, 0, q[0], q[1], 0, 0)])
                cor(0.95, 0.5)
                Line(points=[v for p in meio for v in p], width=dp(1.0))          # aresta central
                cor(0.8)
                Line(points=[v for p in esq for v in p] + [v for p in reversed(dirt) for v in p],
                     width=dp(0.9))
            # brilho percorrendo a lamina
            self._c_varre = cor(0.0, 0.8)
            self._varre = Line(points=[0, 0, 0, 0], width=dp(2.2), cap='round')
            # linhas de holograma
            self._c_scan = cor(0.0, 0.3)
            self._scan = [Line(points=[0, 0, 0, 0], width=dp(0.7)) for _ in range(9)]
            PopMatrix()
            # guarda, cabo e pomo
            if katana:
                cor(0.35)
                Ellipse(pos=(-dp(8), y_guarda - dp(2.4)), size=(dp(16), dp(4.8)))
                cor(0.95, 0.4)
                Line(ellipse=(-dp(8), y_guarda - dp(2.4), dp(16), dp(4.8)), width=dp(1.0))
                cor(0.9, 0.5)
                Rectangle(pos=(-dp(3), y_guarda + dp(2.4)), size=(dp(5), dp(2.4)))  # habaki
                cor(0.28)
                Rectangle(pos=(-dp(2.8), y0 + dp(4)), size=(dp(5.6), y_guarda - dp(2.4) - (y0 + dp(4))))
                ziguezague = []
                yy = y0 + dp(5)
                lado = -1
                while yy < y_guarda - dp(3):
                    ziguezague.extend((lado * dp(2.6), yy))
                    yy += dp(3.2)
                    lado = -lado
                cor(0.85, 0.3)
                Line(points=ziguezague, width=dp(0.9))                                # fita trancada
                cor(0.9, 0.3)
                Line(rounded_rectangle=(-dp(2.8), y0 + dp(4), dp(5.6),
                                        y_guarda - dp(2.4) - (y0 + dp(4)), dp(1.5)), width=dp(0.8))
                cor(0.9, 0.5)
                Ellipse(pos=(-dp(3.4), y0), size=(dp(6.8), dp(5)))                   # kashira
            else:
                gx = dp(12)
                cor(0.40)
                Mesh(mode='triangle_fan', indices=[0, 1, 2, 3, 4, 5],
                     vertices=[-gx, y_guarda, 0, 0, -gx + dp(3), y_guarda + dp(3), 0, 0,
                               gx - dp(3), y_guarda + dp(3), 0, 0, gx, y_guarda, 0, 0,
                               gx - dp(3), y_guarda - dp(3), 0, 0, -gx + dp(3), y_guarda - dp(3), 0, 0])
                cor(0.95, 0.4)
                Line(points=[-gx, y_guarda, -gx + dp(3), y_guarda + dp(3), gx - dp(3), y_guarda + dp(3),
                             gx, y_guarda, gx - dp(3), y_guarda - dp(3), -gx + dp(3), y_guarda - dp(3)],
                     close=True, width=dp(1.0))
                cor(1.0, 0.8)
                Mesh(mode='triangle_fan', indices=[0, 1, 2, 3],                        # gema
                     vertices=[0, y_guarda + dp(3), 0, 0, dp(2.6), y_guarda, 0, 0,
                               0, y_guarda - dp(3), 0, 0, -dp(2.6), y_guarda, 0, 0])
                cor(0.30)
                Rectangle(pos=(-dp(2.6), y0 + dp(5)), size=(dp(5.2), y_guarda - dp(3) - (y0 + dp(5))))
                yy = y0 + dp(7)
                while yy < y_guarda - dp(4):                                        # aneis do cabo
                    Line(points=[-dp(2.6), yy, dp(2.6), yy], width=dp(0.8))
                    yy += dp(4)
                cor(0.9, 0.3)
                Line(rectangle=(-dp(2.6), y0 + dp(5), dp(5.2), y_guarda - dp(3) - (y0 + dp(5))), width=dp(0.8))
                cor(0.95, 0.6)
                Mesh(mode='triangle_fan', indices=[0, 1, 2, 3],                        # pomo
                     vertices=[0, y0 + dp(6), 0, 0, dp(3.4), y0 + dp(2.5), 0, 0,
                               0, y0 - dp(1), 0, 0, -dp(3.4), y0 + dp(2.5), 0, 0])
            # clarao da ponta (quando termina de aparecer)
            self._c_ponta = cor(0.0, 0.9)
            self._r_ponta = Rectangle(texture=tex, size=(0, 0))
            # faiscas
            self._c_fx = []
            for _ in range(6):
                c = Color(r, g, b, 0)
                q = Rectangle(size=(0, 0))
                self._c_fx.append((c, q))
            PopMatrix()
        self._posicionar()
        self._aplicar()

    # ── animacao ─────────────────────────────────────────────────────
    def _posicionar(self, *_):
        self._cx = self.x + self.width / 2.0
        self._cy = self.y + self.height / 2.0
        self._aplicar()

    def _ao_mudar(self, *_):
        if self.opacidade > 0.01 and self._ev is None:
            self._ev = Clock.schedule_interval(self._tick, 1 / 45.)
        self._aplicar()

    def _aplicar(self):
        if not hasattr(self, '_tr'):
            return
        op = max(0.0, min(1.0, self.opacidade))
        bob = math.sin(self._t * 2.6) * dp(3)
        self._tr.xy = (self._cx, self._cy + bob)
        self._rot.angle = math.sin(self._t * 1.3) * 2.0
        e = max(0.0, self.escala)
        self._sc.x = self._sc.y = e
        self._sc_lamina.y = max(0.001, min(1.0, op * 1.15))
        pulso = 0.85 + 0.15 * math.sin(self._t * 3.1)
        for c, a in self._cores:
            c.a = a * op * pulso
        # brilho que percorre a lamina (a cada 2,4 s)
        ciclo = self._t % 2.4
        if op > 0.95 and ciclo < 0.55 and self._meio:
            u = ciclo / 0.55
            i = int(u * (len(self._meio) - 4))
            p0, p1 = self._meio[i], self._meio[min(len(self._meio) - 1, i + 3)]
            self._varre.points = [p0[0], p0[1], p1[0], p1[1]]
            self._c_varre.a = 0.9 * math.sin(math.pi * u)
        else:
            self._c_varre.a = 0
        # linhas de holograma subindo
        if self._meio:
            y_a, y_b = self._y_guarda + dp(3), self._y_ponta
            passo = (y_b - y_a) / len(self._scan)
            desl = (self._t * dp(14)) % passo
            for k, ln in enumerate(self._scan):
                y = y_a + k * passo + desl
                ln.points = [-dp(6), y, dp(6), y]
            self._c_scan.a = 0.22 * op
        # clarao na ponta quando acabou de aparecer
        if op >= 0.99 and not self._revelou:
            self._revelou = True
            self._flash = 1.0
        s = dp(30) * (0.5 + self._flash)
        self._r_ponta.pos = (-s / 2, self._y_ponta - s / 2)
        self._r_ponta.size = (s, s)
        self._c_ponta.a = self._flash * op

    def _tick(self, dt):
        try:
            if self.get_root_window() is None or self.opacidade <= 0.01:
                self._ev = None
                return False
            self._t += dt
            self._flash = max(0.0, self._flash - dt * 2.2)
            # faiscas saindo da lamina
            if random.random() < 0.25 and self.opacidade > 0.9:
                livres = [fx for fx in self._c_fx if fx[0].a <= 0.01]
                if livres:
                    c, q = livres[0]
                    y = random.uniform(self._y_guarda, self._y_ponta)
                    self._faiscas.append([c, q, random.uniform(-dp(5), dp(5)), y, random.uniform(0.5, 0.9), 0.0])
            vivas = []
            for f in self._faiscas:
                c, q, x, y, vida, t = f
                t += dt
                f[5] = t
                if t >= vida:
                    c.a = 0
                    q.size = (0, 0)
                    continue
                k = 1 - t / vida
                yy = y + t * dp(22)
                s = dp(2) * (0.5 + 0.5 * k)
                q.pos = (x - s / 2, yy - s / 2)
                q.size = (s, s)
                c.a = k * self.opacidade
                vivas.append(f)
            self._faiscas = vivas
            self._aplicar()
        except Exception as e:
            print(f"[espada holo] {e}")
            self._ev = None
            return False


# ═══════════════════════════════════════════════════════════
#  HUD PARALLAX
# ═══════════════════════════════════════════════════════════

class HUDParallax(FloatLayout):
    offset_x = NumericProperty(0)
    offset_y = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_parent(self, inst, parent):
        if parent is not None:
            Window.bind(mouse_pos=self._on_mouse)
        else:
            Window.unbind(mouse_pos=self._on_mouse)

    def _on_mouse(self, window, pos):
        cx, cy = Window.center
        dx = (pos[0] - cx) / max(cx, 1)
        dy = (pos[1] - cy) / max(cy, 1)
        Animation.cancel_all(self)
        Animation(offset_x=dx * 20, offset_y=dy * 20, duration=0.2).start(self)


# ═══════════════════════════════════════════════════════════
#  GRID HOLOGRÁFICO
# ═══════════════════════════════════════════════════════════

class GridHolografico(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(0, 0.9, 1, 0.04)
            for x in range(int(self.x), int(self.right), 44):
                Line(points=[x, self.y, x, self.top], width=1)
            for y in range(int(self.y), int(self.top), 44):
                Line(points=[self.x, y, self.right, y], width=1)


# ═══════════════════════════════════════════════════════════
#  BARRA NEON (loading)
# ═══════════════════════════════════════════════════════════

class BarraNeon(Widget):
    progresso = NumericProperty(0)
    cor_linha = ListProperty([0, 0.9, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._upd, size=self._upd,
                  progresso=self._upd, cor_linha=self._upd)

    def _upd(self, *_):
        self.canvas.clear()
        with self.canvas:
            Color(0.04, 0.04, 0.10, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[4])
            Color(*self.cor_linha)
            Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 4],
                 width=1.2)
            segs = 40; esp = 2
            if self.width > esp * (segs + 1):
                lw     = (self.width - esp * (segs + 1)) / segs
                ativos = int((self.progresso / 100.0) * segs)
                for i in range(segs):
                    c = (self.cor_linha if i < ativos
                         else (self.cor_linha[0], self.cor_linha[1],
                               self.cor_linha[2], 0.11))
                    Color(*c)
                    RoundedRectangle(
                        pos=(self.x + esp + i * (lw + esp), self.y + 3),
                        size=(lw, self.height - 6), radius=[2])


# ═══════════════════════════════════════════════════════════
#  BARRA CIRCULAR (XP ring)
# ═══════════════════════════════════════════════════════════

class BarraCircular(FloatLayout):
    valor                = NumericProperty(0)
    maximo               = NumericProperty(10000)
    angulo_preenchimento = NumericProperty(0)
    angulo_anel_externo  = NumericProperty(0)
    valor_display        = NumericProperty(0)
    cor_anel             = ListProperty([0, 0.9, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._anim_giro   = None
        self._anim_pulso  = None

    def parar_animacoes(self):
        """Cancela todas as animações repetidas — chamar no on_leave da tela."""
        Animation.cancel_all(self)
        if self._anim_giro:
            self._anim_giro.stop(self)
            self._anim_giro = None
        if self._anim_pulso:
            self._anim_pulso.stop(self)
            self._anim_pulso = None

    def animar_progresso(self):
        self.parar_animacoes()
        self.angulo_preenchimento = 0
        self.valor_display        = 0
        # limitado a 100% e sem 'out_elastic' (ele passava do alvo e voltava
        # quicando: o anel mostrava 113% e tremia antes de parar)
        valor = max(0, min(self.valor, self.maximo)) if self.maximo > 0 else 0
        alvo = (valor / self.maximo) * 360 if self.maximo > 0 else 0

        Animation(angulo_preenchimento=alvo, valor_display=valor,
                  duration=1.4, transition='out_cubic').start(self)

        self._anim_giro = Animation(angulo_anel_externo=360, duration=5)
        self._anim_giro.repeat = True
        self._anim_giro.start(self)

        if alvo >= 359.5:
            Clock.schedule_once(self._pulso_cheio, 1.7)

    def _pulso_cheio(self, dt):
        original = list(self.cor_anel)
        self._anim_pulso = (
            Animation(cor_anel=[1.0, 1.0, 1.0, 1.0],
                      duration=0.35, transition='out_sine') +
            Animation(cor_anel=original,
                      duration=0.55, transition='in_out_sine'))
        self._anim_pulso.repeat = True
        self._anim_pulso.start(self)


# ═══════════════════════════════════════════════════════════
#  BOTÕES ANGULARES SCI-FI
# ═══════════════════════════════════════════════════════════

class BotaoAngular(Button):
    """
    Botão chanfrado JARVIS/SAO.
    - Scale é APENAS visual (canvas). O touch dispatch usa collide_point normal.
    - on_press: dispara flash branco -> retorna ao ciano (novo requisito v6).
    """
    escala       = NumericProperty(1.0)
    brilho       = NumericProperty(0.0)
    cor_borda    = ListProperty([0.0, 0.85, 1.0, 0.9])
    cor_borda_kv = ListProperty([0.0, 0.85, 1.0, 0.9])   # cópia KV para reset
    cor_fundo    = ListProperty([0.04, 0.04, 0.15, 0.92])
    cor_texto    = ListProperty([0.0,  0.90, 1.0,  1.0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # faixa de luz + pulso no contorno a cada toque (todas as subclasses)
        try:
            from animacoes_ui import aplicar_brilho_toque
            aplicar_brilho_toque(self)
        except Exception as e:
            print(f"[BotaoAngular] brilho indisponivel: {e}")

    def on_kv_post(self, base_widget):
        # Salva cor original assim que o KV terminar de aplicar valores
        self.cor_borda_kv = list(self.cor_borda)

    def on_press(self):
        tocar_click()   # som de clique em todo botão
        Animation.cancel_all(self, 'escala', 'cor_borda')
        Animation(escala=0.93, duration=0.07, transition='out_quad').start(self)
        original = list(self.cor_borda_kv)
        (Animation(cor_borda=[1.0, 1.0, 1.0, 1.0], duration=0.06,
                   transition='out_quad') +
         Animation(cor_borda=original, duration=0.22,
                   transition='out_quad')).start(self)

    def on_release(self):
        Animation.cancel_all(self, 'escala')
        # out_quad em vez de out_elastic — sem overshoot visual
        Animation(escala=1.0, duration=0.18, transition='out_quad').start(self)


class BotaoAngularMenu(BotaoAngular):
    """Botão com respiração orgânica contínua (idle menu)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._breath_anim = None
        self._breath_ev   = None   # guarda ref do Clock para poder cancelar
        self._breath_ev   = Clock.schedule_once(
            self._start_breath, random.uniform(0.1, 2.0))

    def _start_breath(self, dt):
        self._breath_ev   = None
        self._breath_anim = (
            Animation(brilho=1.0, duration=2.0, transition='in_out_sine') +
            Animation(brilho=0.0, duration=2.0, transition='in_out_sine'))
        self._breath_anim.repeat = True
        self._breath_anim.start(self)

    def on_parent(self, inst, parent):
        if parent is None:
            # Cancela o clock pendente se ainda não disparou
            if self._breath_ev is not None:
                self._breath_ev.cancel()
                self._breath_ev = None
            # Para a animação se já estiver rodando
            if self._breath_anim is not None:
                self._breath_anim.stop(self)
                self._breath_anim = None
                self.brilho = 0.0


class BotaoAngularAlerta(BotaoAngular):
    pass   # cor definida no KV


class BotaoAngularOperador(BotaoAngular):
    pass   # cor definida no KV


# Aliases de retrocompatibilidade
BotaoNeon   = BotaoAngular
BotaoAlerta = BotaoAngularAlerta


# ═══════════════════════════════════════════════════════════
#  LISTA ITEM ANGULAR
# ═══════════════════════════════════════════════════════════

class ListaItem(BotaoAngular):
    cor_borda    = ListProperty([0.0, 0.85, 1.0, 0.85])
    cor_borda_kv = ListProperty([0.0, 0.85, 1.0, 0.85])
    cor_fundo    = ListProperty([0.04, 0.04, 0.18, 0.88])
    cor_texto    = ListProperty([0.0,  0.90, 1.0,  1.0])


# ═══════════════════════════════════════════════════════════
#  GRÁFICO DE BARRAS HOLOGRÁFICO
# ═══════════════════════════════════════════════════════════

class GraficoBarras(Widget):
    dados = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tex_cache = {}   # {(text, size, cor): texture}
        self.bind(pos=self._draw, size=self._draw, dados=self._draw_reset)

    def _draw_reset(self, *_):
        """Invalida o cache ao mudar dados e redesenha."""
        self._tex_cache.clear()
        self._draw()

    def _get_tex(self, text, size, cor):
        """Retorna textura cacheada — cria apenas na primeira chamada."""
        key = (str(text), size, cor)
        if key not in self._tex_cache:
            try:
                from kivy.core.text import Label as CoreLabel
                lbl = CoreLabel(text=str(text), font_size=size, color=cor)
                lbl.refresh()
                self._tex_cache[key] = lbl.texture
            except Exception:
                self._tex_cache[key] = None
        return self._tex_cache[key]

    def _txt(self, text, cx, y, cor, size=10):
        tex = self._get_tex(text, size, cor)
        if tex:
            tw, th = tex.size
            Color(*cor)
            Rectangle(texture=tex, pos=(cx - tw / 2, y), size=(tw, th))

    def _draw(self, *_):
        self.canvas.clear()
        if self.width <= 10 or self.height <= 10:
            return
        with self.canvas:
            Color(0.03, 0.03, 0.09, 0.96)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
            Color(0, 0.9, 1, 0.12)
            Line(rounded_rectangle=[self.x, self.y, self.width, self.height, 8],
                 width=1)

            if not self.dados:
                self._txt('SEM DADOS', self.center_x, self.center_y - 8,
                          (0.4, 0.4, 0.6, 0.7), 12)
                return

            n      = len(self.dados)
            maximo = max(d.get('valor', 0) for d in self.dados) or 1
            px, pb, pt, esp = 14, 28, 20, 7
            wu   = self.width - px * 2
            larg = (wu - esp * (n - 1)) / max(n, 1)
            hmax = self.height - pb - pt

            self._txt('PRODUÇÃO · ÚLTIMOS DIAS',
                      self.center_x, self.top - pt + 4, (0, 0.9, 1, 0.35), 9)
            Color(0, 0.9, 1, 0.12)
            Line(points=[self.x + px, self.y + pb - 1,
                         self.right - px, self.y + pb - 1], width=1)

            for i, item in enumerate(self.dados):
                bx   = self.x + px + i * (larg + esp)
                prop = item.get('valor', 0) / maximo
                # Limita altura máxima a 90% para a barra recorde não dominar toda a área
                alt  = max(prop * hmax * 0.90, 2)
                by   = self.y + pb
                cx   = bx + larg / 2

                if item.get('record'):
                    fc = (0.65, 0.48, 0.0, 0.45)   # dourado mais suave
                    bc = (1.0,  0.80, 0.1, 0.85)
                elif item.get('hoje'):
                    fc = (0.0, 0.65, 1.0, 0.52)
                    bc = (0.0, 0.88, 1.0, 0.95)
                else:
                    fc = (0.22, 0.04, 0.48, 0.38)
                    bc = (0.38, 0.08, 0.70, 0.72)

                Color(*fc)
                Rectangle(pos=(bx, by), size=(larg, alt))
                Color(fc[0] + 0.15, fc[1] + 0.15, fc[2] + 0.15, fc[3] * 0.55)
                Rectangle(pos=(bx, by + alt * 0.8), size=(larg, alt * 0.2))
                Color(*bc)
                Line(rectangle=[bx, by, larg, alt], width=1)
                Color(1, 1, 1, 0.28)
                Line(points=[bx + 1, by + alt, bx + larg - 1, by + alt], width=2)

                val = item.get('valor', 0)
                if val > 0:
                    self._txt(str(val), cx, by + alt + 3, (1, 1, 1, 0.9), 10)
                if item.get('record'):
                    self._txt('*', cx, by + alt + 14, (1, 0.88, 0, 1), 11)
                lbl = item.get('label', '')
                if lbl:
                    self._txt(lbl, cx, self.y + 5, (0.5, 0.5, 0.78, 0.88), 9)


# ═══════════════════════════════════════════════════════════
#  TREMOR DE TELA
# ═══════════════════════════════════════════════════════════

def tremer_tela(intensidade=20):
    try:
        app = App.get_running_app()
        if not app or not app.root:
            return
        sm = app.root.ids.sm
        ox, oy = sm.pos
        (Animation(x=ox + intensidade,   y=oy - intensidade,   duration=0.025) +
         Animation(x=ox - intensidade,   y=oy + intensidade,   duration=0.025) +
         Animation(x=ox + intensidade/2, y=oy - intensidade/2, duration=0.025) +
         Animation(x=ox,                y=oy,                  duration=0.025)
         ).start(sm)
    except Exception as e:
        print(f"[tremer_tela] ignorado: {e}")



# ═══════════════════════════════════════════════════════════
#  PARTÍCULAS DE FUNDO
# ═══════════════════════════════════════════════════════════

class ParticulaFundo(Widget):
    """
    Partícula circular com glow suave.
    Glow é centralizado em relação ao core — sem artefato de quadradinho.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        t = random.randint(2, 4)          # menor: 2-4px (era 2-5px)
        self.size    = (t, t)
        self.pos     = (random.randint(0, Window.width), random.randint(0, Window.height))
        self.opacity = 0
        if random.random() > 0.5:
            r, g, b = 0.0, 0.88, 1.0    # ciano
        else:
            r, g, b = 0.55, 0.10, 0.95  # roxo
        self._r = r; self._g = g; self._b = b; self._t = t
        with self.canvas:
            # Glow: elipse grande, opacidade baixa, corretamente centrada
            self._cg = Color(r, g, b, 0)
            gw = t * 6
            self._gl = Ellipse(
                pos=(self.x - gw/2 + t/2, self.y - gw/2 + t/2),
                size=(gw, gw))
            # Core: ponto sólido
            self._cc = Color(min(r + 0.2, 1), min(g + 0.1, 1), b, 0)
            self._cr = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, opacity=self._upd)

    def _upd(self, *_):
        t  = self._t
        gw = t * 6
        # Glow centrado no mesmo ponto que o core
        self._gl.pos  = (self.x - gw/2 + t/2, self.y - gw/2 + t/2)
        self._cr.pos  = self.pos
        self._cg.a    = self.opacity * 0.20   # glow mais sutil
        self._cc.a    = self.opacity


class FundoAnimado(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._init, 0.1)

    def _init(self, dt):
        # 40 partículas ao invés de 25
        for _ in range(22):    # 40 -> 22: menos carga no Android
            p = ParticulaFundo()
            self.add_widget(p)
            self._anim(p)

    def _anim(self, p):
        d    = random.uniform(6, 14)
        p.y  = random.randint(-50, Window.height - 80)
        p.x  = random.randint(0, Window.width)
        alvo = p.y + random.randint(100, 300)
        # Opacidade mais alta para partículas maiores
        op_max = random.uniform(0.65, 1.0) if p.size[0] >= 4 else random.uniform(0.45, 0.80)
        anim = (Animation(opacity=op_max,          duration=d * 0.25) +
                Animation(opacity=op_max * 0.7,    duration=d * 0.50) +
                Animation(opacity=0,               duration=d * 0.25))
        Animation(y=alvo, duration=d).start(p)
        anim.bind(on_complete=lambda *_: self._anim(p))
        anim.start(p)


# ═══════════════════════════════════════════════════════════
#  EXPLOSÃO SAO — coordenadas globais (Window space)
# ═══════════════════════════════════════════════════════════

class FlashExplosao(Widget):
    """Clarao do item sendo desintegrado: um brilho suave (borda esfumada,
    nucleo branco) que cresce e some - antes era um retangulo chapado."""
    escala = NumericProperty(1.0)

    def __init__(self, pos, size, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = size
        self.pos  = pos
        try:
            from infinito import textura_radial
            tex = textura_radial()
        except Exception:
            tex = None
        with self.canvas:
            PushMatrix()
            self._sc = Scale(1, 1, 1)
            self._c_glow = Color(0.2, 0.9, 1.0, 1)
            self._r_glow = Rectangle(texture=tex)
            self._c_nuc = Color(0.9, 1.0, 1.0, 1)
            self._r_nuc = Rectangle(texture=tex)
            PopMatrix()
        self.bind(pos=self._upd, size=self._upd, escala=self._upd, opacity=self._upd)
        self._upd()

    def _upd(self, *_):
        x, y = self.pos
        w, h = self.size
        cx, cy = x + w / 2.0, y + h / 2.0
        self._sc.origin = (cx, cy)
        self._sc.x = self._sc.y = self.escala
        # glow largo (passa das bordas do item) e nucleo mais estreito
        gw, gh = w * 1.35, h * 2.2
        self._r_glow.pos, self._r_glow.size = (cx - gw / 2, cy - gh / 2), (gw, gh)
        nw, nh = w * 1.05, h * 1.1
        self._r_nuc.pos, self._r_nuc.size = (cx - nw / 2, cy - nh / 2), (nw, nh)
        self._c_glow.a = 0.55
        self._c_nuc.a = 0.85


class CacoSAO(Widget):
    angulo = NumericProperty(0)
    escala = NumericProperty(1.0)

    def __init__(self, gx, gy, max_w, max_h, **kwargs):
        """
        gx, gy  — coordenada global (Window space) de origem
        max_w/h — dimensões do widget explodido
        """
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (random.randint(14, 28), random.randint(14, 28))
        # posição inicial: dentro da bbox global do widget
        self.pos = (gx + random.randint(0, int(max_w)),
                    gy + random.randint(0, int(max_h)))
        with self.canvas.before:
            PushMatrix()
            self._rot = Rotate(angle=self.angulo, origin=self.center)
            self._scl = Scale(self.escala, origin=self.center)
            Color(0, 0.8, 1, 1)
            self._tri = Triangle(points=[
                self.x, self.y,
                self.x + self.width, self.y,
                self.x + self.width / 2, self.y + self.height
            ])
        with self.canvas.after:
            PopMatrix()
        self.bind(pos=self._upd, angulo=self._upd, escala=self._upd)

    def _upd(self, *_):
        self._rot.angle  = self.angulo
        self._scl.xyz    = (self.escala, self.escala, 1)
        self._tri.points = [
            self.x, self.y,
            self.x + self.width, self.y,
            self.x + self.width / 2, self.y + self.height
        ]


class PoeiraDigital(Widget):
    def __init__(self, gx, gy, max_w, max_h, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (4, 4)
        self.pos  = (gx + random.randint(0, int(max_w)),
                     gy + random.randint(0, int(max_h)))
        with self.canvas:
            Color(0, 1, 1, 1)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda i, v: setattr(i._rect, 'pos', v))


def explodir_estilhacos(widget_alvo, callback_final):
    """
    Estilhacos no estilo SAO: o item se parte em poligonos com a imagem real
    dele; os cacos voam girando, viram cristal ciano e se desfazem em
    pontinhos de luz que sobem. Coordenadas da janela; tudo num unico
    Clock (leve mesmo com varios itens de uma vez, como no WIPE).
    """
    tremer_tela(14)
    fim = [False]

    def _acabar(*_):
        if fim[0]:
            return
        fim[0] = True
        try:
            if camada.parent:
                Window.remove_widget(camada)
        except Exception:
            pass
        try:
            callback_final()
        except Exception as e:
            print(f"[estilhacos] callback: {e}")

    camada = Widget(size_hint=(None, None), size=Window.size, pos=(0, 0))
    try:
        if widget_alvo.parent:
            gx, gy = widget_alvo.parent.to_window(widget_alvo.x, widget_alvo.y)
        else:
            gx, gy = widget_alvo.to_window(0, 0)
        gw, gh = max(1.0, widget_alvo.width), max(1.0, widget_alvo.height)
        # foto do item (com ele visivel), depois some
        tex = None
        try:
            op = widget_alvo.opacity
            widget_alvo.opacity = 1
            tex = widget_alvo.export_as_image().texture
            widget_alvo.opacity = op
        except Exception as e:
            print(f"[estilhacos] sem foto do item: {e}")
        widget_alvo.opacity = 0
        Window.add_widget(camada)

        flash = FlashExplosao((gx, gy), (gw, gh))
        camada.add_widget(flash)
        Animation(opacity=0, escala=1.5, duration=0.22).start(flash)

        # malha triangular com pontos internos deslocados (cacos irregulares)
        cols = max(3, min(8, int(gw / dp(46)) + 1))
        linhas = max(2, min(5, int(gh / dp(24)) + 1))
        pts = []
        for j in range(linhas + 1):
            fila = []
            for i in range(cols + 1):
                x = gx + gw * i / cols
                y = gy + gh * j / linhas
                if 0 < i < cols:
                    x += random.uniform(-0.32, 0.32) * gw / cols
                if 0 < j < linhas:
                    y += random.uniform(-0.32, 0.32) * gh / linhas
                fila.append((x, y))
            pts.append(fila)
        tris = []
        for j in range(linhas):
            for i in range(cols):
                a, b = pts[j][i], pts[j][i + 1]
                c, d = pts[j + 1][i + 1], pts[j + 1][i]
                if random.random() < 0.5:
                    tris += [(a, b, c), (a, c, d)]
                else:
                    tris += [(a, b, d), (b, c, d)]

        ccx, ccy = gx + gw / 2.0, gy + gh / 2.0
        cacos = []
        with camada.canvas:
            for tri in tris:
                mx = sum(p[0] for p in tri) / 3.0
                my = sum(p[1] for p in tri) / 3.0
                vs = []
                for (x, y) in tri:
                    vs.extend((x, y, (x - gx) / gw, 1.0 - (y - gy) / gh))
                PushMatrix()
                tr = Translate(0, 0)
                rot = Rotate(angle=0, origin=(mx, my))
                cor = Color(1, 1, 1, 1)
                m = Mesh(mode='triangle_fan', indices=[0, 1, 2], vertices=vs)
                if tex is not None:
                    m.texture = tex
                else:
                    cor.rgba = (0.05, 0.25, 0.4, 0.95)
                # brilho de cristal por cima da foto (acende no estalo e cresce no voo)
                cor_brilho = Color(0.55, 0.95, 1.0, 0)
                Mesh(mode='triangle_fan', indices=[0, 1, 2],
                     vertices=[v for p in tri for v in (p[0], p[1], 0, 0)])
                cor_borda = Color(0.55, 1.0, 1.0, 0.9)
                Line(points=[v for p in tri for v in p], close=True, width=1.1)
                PopMatrix()
                # voa para fora do centro do item, com um empurrao para cima
                dx, dy = mx - ccx, my - ccy
                ang = math.atan2(dy + random.uniform(-0.2, 0.2) * gh, dx + random.uniform(-0.3, 0.3) * gw)
                v = dp(random.uniform(140, 420))
                cacos.append({
                    'tr': tr, 'rot': rot, 'cor': cor, 'borda': cor_borda, 'brilho': cor_brilho,
                    'x': 0.0, 'y': 0.0,
                    'vx': math.cos(ang) * v, 'vy': math.sin(ang) * v * 0.7 + dp(random.uniform(120, 260)),
                    'va': random.uniform(-540, 540), 'a': 0.0, 'mx': mx, 'my': my,
                    'vida': random.uniform(0.7, 1.0), 'soltou': False, 'tem_tex': tex is not None})
            # pontinhos de luz (os cacos viram luz no fim)
            luzes = []
            for _ in range(min(90, len(cacos) * 3)):
                c = Color(0.7, 1.0, 1.0, 0)
                r = Rectangle(size=(0, 0))
                luzes.append([c, r, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        livres = list(range(len(luzes)))
        vivas = []
        t = [0.0]
        grav = dp(1100)

        def _passo(dt):
            try:
                dt = min(dt, 1 / 30.)
                t[0] += dt
                for k in cacos:
                    u = t[0] / k['vida']
                    if u >= 1:
                        if k['cor'].a:
                            k['cor'].a = 0
                            k['borda'].a = 0
                            k['brilho'].a = 0
                        continue
                    k['vy'] -= grav * dt
                    k['vx'] *= 0.985
                    k['x'] += k['vx'] * dt
                    k['y'] += k['vy'] * dt
                    k['a'] += k['va'] * dt
                    k['tr'].xy = (k['x'], k['y'])
                    k['rot'].origin = (k['mx'], k['my'])
                    k['rot'].angle = k['a']
                    # vira cristal: a foto vai clareando para o ciano e some
                    cristal = min(1.0, u * 1.6)
                    alfa = 1.0 if u < 0.55 else max(0.0, 1 - (u - 0.55) / 0.45)
                    if k['tem_tex']:
                        k['cor'].rgba = (1 - 0.45 * cristal, 1.0, 1.0, alfa)
                    else:
                        k['cor'].a = 0.95 * alfa
                    estalo = max(0.0, 1 - t[0] / 0.1)
                    k['brilho'].a = alfa * min(0.85, 0.7 * estalo + 0.4 * cristal)
                    k['borda'].a = 0.9 * alfa * (0.6 + 0.4 * math.sin(t[0] * 30 + k['mx']))
                    if u > 0.6 and not k['soltou']:
                        k['soltou'] = True
                        for _ in range(3):
                            if not livres:
                                break
                            i = livres.pop()
                            L = luzes[i]
                            L[2] = k['mx'] + k['x'] + random.uniform(-dp(6), dp(6))
                            L[3] = k['my'] + k['y'] + random.uniform(-dp(6), dp(6))
                            L[4] = random.uniform(-dp(30), dp(30))
                            L[5] = dp(random.uniform(60, 150))
                            L[6] = L[7] = random.uniform(0.35, 0.6)
                            vivas.append(i)
                for i in list(vivas):
                    L = luzes[i]
                    L[6] -= dt
                    if L[6] <= 0:
                        L[0].a = 0
                        L[1].size = (0, 0)
                        vivas.remove(i)
                        livres.append(i)
                        continue
                    L[2] += L[4] * dt
                    L[3] += L[5] * dt
                    kk = L[6] / L[7]
                    s = dp(2.6) * (0.5 + 0.5 * kk)
                    L[1].pos = (L[2] - s / 2, L[3] - s / 2)
                    L[1].size = (s, s)
                    L[0].a = kk
                if t[0] >= 1.15:
                    _acabar()
                    return False
            except Exception as e:
                print(f"[estilhacos] {e}")
                _acabar()
                return False
        Clock.schedule_interval(_passo, 1 / 60.)
        Clock.schedule_once(_acabar, 2.0)          # seguranca
    except Exception as e:
        print(f"[estilhacos] ignorado: {e}")
        widget_alvo.opacity = 0
        _acabar()


# ══════════════════════════════════════════════════════════════════════
#  TECLADOS CUSTOMIZADOS SAO — substitui teclado Android
# ══════════════════════════════════════════════════════════════════════

_LINHAS_LETRAS = ['QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM']


class _BotaoTecla(Button):
    """Botão compacto para teclado SAO — mais legível que BotaoAngular em espaço pequeno."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal  = ''
        self.background_color   = [0, 0, 0, 0]
        self.color              = [0, 0.9, 1, 1]
        self.font_name          = 'orbitron.ttf'
        radius = [dp(5)]
        with self.canvas.before:
            # RoundedRectangle para fundo + Line para borda
            # Mais eficiente que Line.rounded_rectangle que recalcula todos os pontos
            Color(0.04, 0.06, 0.15, 0.96)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=radius)
            Color(0, 0.75, 1, 0.55)
            self._bd = RoundedRectangle(
                pos=(self.x+1, self.y+1),
                size=(self.width-2, self.height-2),
                radius=radius)
            Color(0.04, 0.06, 0.15, 0.96)  # inner fill cobre o centro
            self._bi = RoundedRectangle(
                pos=(self.x+2, self.y+2),
                size=(self.width-4, self.height-4),
                radius=radius)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._bg.pos  = self.pos
        self._bg.size = self.size
        self._bd.pos  = (self.x + 1, self.y + 1)
        self._bd.size = (self.width - 2, self.height - 2)
        self._bi.pos  = (self.x + 2, self.y + 2)
        self._bi.size = (self.width - 4, self.height - 4)


class _TecladoBase(BoxLayout):
    """
    Base dos teclados SAO.
    fechar: callable — chamado pelo botao OK e pelo toque fora do teclado.
    Nao usa t.focus=False para fechar (causa crash Android).
    """

    def __init__(self, target, fechar=None, **kwargs):
        kwargs.setdefault('orientation', 'vertical')
        kwargs.setdefault('size_hint', (1, None))
        super().__init__(**kwargs)
        self.target  = target
        self._fechar = fechar
        self.spacing = dp(3)
        self.padding = [dp(5), dp(6), dp(5), dp(5)]

        with self.canvas.before:
            Color(0.02, 0.04, 0.10, 0.97)
            self._bg  = Rectangle(pos=self.pos, size=self.size)
            Color(0, 0.8, 1, 0.45)
            self._top = Line(points=[self.x, self.top, self.right, self.top], width=1.5)
        self.bind(pos=self._upd_bg, size=self._upd_bg)

    def _upd_bg(self, *_):
        self._bg.pos    = self.pos
        self._bg.size   = self.size
        self._top.points = [self.x, self.top, self.right, self.top]

    def _press(self, char):
        t = self.target
        if not t:
            return
        if char == 'OK':
            if self._fechar:
                self._fechar()
            return
        if char == 'DEL':
            if t.text:
                t.text = t.text[:-1]
        elif char == 'CLR':
            t.text = ''
        elif char == ' ':
            t.text += ' '
        else:
            t.text += char

    def _press_com_feedback(self, btn, char):
        """Feedback visual ao pressionar tecla — flash cyan rapido."""
        self._press(char)
        # Flash na cor do botao: cyan -> escuro -> cyan
        try:
            Animation.cancel_all(btn, 'color')
            (Animation(color=[1, 1, 1, 1], duration=0.04, transition='out_expo') +
             Animation(color=[0, 0.9, 1, 1], duration=0.10, transition='in_expo')
             ).start(btn)
        except Exception:
            pass

    def _key(self, char, font_size='18sp', **kw):
        btn = _BotaoTecla(text=char, font_size=font_size, **kw)
        btn.bind(on_press=lambda b: self._press_com_feedback(b, char))
        return btn


class TecladoLetras(_TecladoBase):
    """
    Teclado SAO apenas com letras A-Z.
    Font 18sp — legivel nos botoes ~36dp da linha QWERTY.
    """

    def __init__(self, target, fechar=None, **kwargs):
        kwargs['height'] = dp(252)
        super().__init__(target, fechar=fechar, **kwargs)

        for linha in _LINHAS_LETRAS:
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(3))
            for c in linha:
                row.add_widget(self._key(c, font_size='18sp'))
            self.add_widget(row)

        # Linha especial: CLR | espaço | DEL | OK
        spc = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        spc.add_widget(self._key('CLR', font_size='12sp', size_hint_x=0.18))
        spc.add_widget(self._key(' ',   font_size='12sp', size_hint_x=0.44))
        spc.add_widget(self._key('DEL', font_size='12sp', size_hint_x=0.18))
        spc.add_widget(self._key('OK',  font_size='14sp', size_hint_x=0.20))
        self.add_widget(spc)


class TecladoNumeros(_TecladoBase):
    """
    Teclado SAO apenas com numeros 0-9.
    decimal=True inclui ponto para campos R$.
    Font 26sp — confortavel nos botoes maiores.
    """

    def __init__(self, target, fechar=None, decimal=False, **kwargs):
        kwargs['height'] = dp(252)
        super().__init__(target, fechar=fechar, **kwargs)
        self._decimal = decimal

        for linha in [['7', '8', '9'], ['4', '5', '6'], ['1', '2', '3']]:
            row = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(5))
            for c in linha:
                row.add_widget(self._key(c, font_size='26sp'))
            self.add_widget(row)

        last = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(5))
        if decimal:
            last.add_widget(self._key('.',   font_size='22sp', size_hint_x=0.25))
            last.add_widget(self._key('0',   font_size='26sp', size_hint_x=0.25))
            last.add_widget(self._key('DEL', font_size='12sp', size_hint_x=0.25))
            last.add_widget(self._key('OK',  font_size='14sp', size_hint_x=0.25))
        else:
            last.add_widget(self._key('CLR', font_size='12sp', size_hint_x=0.25))
            last.add_widget(self._key('0',   font_size='26sp', size_hint_x=0.25))
            last.add_widget(self._key('DEL', font_size='12sp', size_hint_x=0.25))
            last.add_widget(self._key('OK',  font_size='14sp', size_hint_x=0.25))
        self.add_widget(last)
