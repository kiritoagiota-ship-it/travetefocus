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

import tatil

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
        # o fundo do campo vai na PRIMEIRA posicao do canvas.before: o Kivy
        # desenha o texto no canvas.before e, desenhado depois, o fundo cobria
        # o texto (os numeros ficavam apagados)
        from kivy.graphics import InstructionGroup
        g = InstructionGroup()
        g.add(Color(0.04, 0.04, 0.12, 1))
        self._fundo_rr = RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
        g.add(self._fundo_rr)
        self.canvas.before.insert(0, g)
        self.bind(pos=self._mover_fundo, size=self._mover_fundo)

    def _mover_fundo(self, *_):
        self._fundo_rr.pos = self.pos
        self._fundo_rr.size = self.size

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

_TEX_HALO = None


def _textura_halo():
    """Luz redonda e macia (forte no centro, some na borda)."""
    global _TEX_HALO
    if _TEX_HALO is None:
        from kivy.graphics.texture import Texture
        n = 32
        buf = bytearray(n * n * 4)
        for yy in range(n):
            for xx in range(n):
                d = math.hypot(xx - (n - 1) / 2.0, yy - (n - 1) / 2.0) / ((n - 1) / 2.0)
                a = max(0.0, 1 - d) ** 2
                i = (yy * n + xx) * 4
                buf[i] = buf[i + 1] = buf[i + 2] = 255
                buf[i + 3] = int(255 * a)
        dados = bytes(buf)
        tex = Texture.create(size=(n, n), colorfmt='rgba')
        tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
        tex.add_reload_observer(lambda t: t.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte'))
        _TEX_HALO = tex
    return _TEX_HALO


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
        self._vida_ev     = None
        self._vida_g      = None
        self._faiscas     = []          # [x, y, vx, vy, vida, vida_max, Color, Rectangle]
        self._t_vida      = 0.0
        self._t_faisca    = 0.0

    def parar_animacoes(self):
        """Cancela todas as animações repetidas — chamar no on_leave da tela."""
        Animation.cancel_all(self)
        if self._anim_giro:
            self._anim_giro.stop(self)
            self._anim_giro = None
        if self._anim_pulso:
            self._anim_pulso.stop(self)
            self._anim_pulso = None
        if self._vida_ev is not None:
            self._vida_ev.cancel()
            self._vida_ev = None
        if self._vida_g is not None:
            self.canvas.after.remove(self._vida_g)
            self._vida_g = None
        self._faiscas = []

    # ── vida do anel: a ponta acesa respira, solta faiscas e um pulso de luz
    #    percorre o que ja encheu ─────────────────────────────────────────
    def _ligar_vida(self):
        from kivy.graphics import InstructionGroup
        if self._vida_g is not None:
            self.canvas.after.remove(self._vida_g)
        g = InstructionGroup()
        self._c_pulso = Color(1, 1, 1, 0)
        self._l_pulso = Line(width=dp(7), cap='round')
        self._c_ponta = Color(1, 1, 1, 0)
        self._r_ponta = Rectangle(texture=_textura_halo())
        for ins in (self._c_pulso, self._l_pulso, self._c_ponta, self._r_ponta):
            g.add(ins)
        self.canvas.after.add(g)
        self._vida_g = g
        self._faiscas = []
        self._t_vida = 0.0
        self._vida_ev = Clock.schedule_interval(self._vida, 1 / 60.)

    def _vida(self, dt):
        try:
            if self.get_root_window() is None:
                return True
            self._t_vida += dt
            t = self._t_vida
            ang = self.angulo_preenchimento
            raio = min(self.width, self.height) / 2.55
            cx, cy = self.center_x, self.center_y
            r, g, b = self.cor_anel[:3]
            rad = math.radians(ang)
            px, py = cx + raio * math.sin(rad), cy + raio * math.cos(rad)
            if ang > 2:
                tam = dp(44) * (1 + 0.12 * math.sin(t * 4.2))
                self._r_ponta.pos = (px - tam / 2, py - tam / 2)
                self._r_ponta.size = (tam, tam)
                self._c_ponta.rgba = (r, g, b, 0.55 + 0.2 * math.sin(t * 4.2))
                # faiscas saindo da ponta
                self._t_faisca += dt
                while self._t_faisca > 0.07 and len(self._faiscas) < 26:
                    self._t_faisca -= 0.07
                    fora = random.uniform(dp(18), dp(55))
                    frente = random.uniform(dp(10), dp(40))
                    vx = math.sin(rad) * fora + math.cos(rad) * frente
                    vy = math.cos(rad) * fora - math.sin(rad) * frente
                    vmax = random.uniform(0.45, 0.9)
                    lado = random.choice((dp(2), dp(3)))
                    cf = Color(min(1, r + 0.4), min(1, g + 0.4), min(1, b + 0.4), 1)
                    rf = Rectangle(pos=(px, py), size=(lado, lado))
                    self._vida_g.add(cf)
                    self._vida_g.add(rf)
                    self._faiscas.append([px + random.uniform(-dp(5), dp(5)),
                                          py + random.uniform(-dp(5), dp(5)), vx, vy, vmax, vmax, cf, rf])
            else:
                self._c_ponta.a = 0
            vivas = []
            for fz in self._faiscas:
                fz[4] -= dt
                if fz[4] <= 0:
                    self._vida_g.remove(fz[6])
                    self._vida_g.remove(fz[7])
                    continue
                fz[0] += fz[2] * dt
                fz[1] += fz[3] * dt
                fz[7].pos = (int(fz[0]), int(fz[1]))          # pixel duro
                fz[6].a = fz[4] / fz[5]
                vivas.append(fz)
            self._faiscas = vivas
            # pulso de luz correndo do comeco ate a ponta, a cada 3,4 s
            ciclo = t % 3.4
            if ang > 25 and ciclo < 1.0:
                k = ciclo / 1.0
                fim = ang * (1 - (1 - k) ** 2)
                ini = max(0.0, fim - 26)
                self._l_pulso.circle = (cx, cy, raio, ini, fim)
                self._c_pulso.a = 0.55 * math.sin(math.pi * k)
            else:
                self._c_pulso.a = 0
        except Exception as e:
            print(f"[anel] vida: {e}")
            self._vida_ev = None
            return False

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

        # (o anel de fora gira devagar: 0 -> 360 sem parar)
        self.angulo_anel_externo = 0
        self._anim_giro = Animation(angulo_anel_externo=360, duration=18)
        self._anim_giro.repeat = True
        self._anim_giro.start(self)
        self._ligar_vida()

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
    tatil        = StringProperty('botao')   # vibracao ao tocar: 'botao', 'tecla' ou ''

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
        if self.tatil == 'tecla':
            tatil.tecla()
        elif self.tatil:
            tatil.botao()
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


class ItemGesto(ListaItem):
    """Item de lista com gestos (o toque normal continua igual):
      arrastar para o lado  -> ao_arrastar(item): o item segue o dedo, a
                               borda fica vermelha; passou do limite e soltou,
                               ele volta escorregando e chama a funcao;
      segurar o dedo        -> ao_segurar(item): uma linha de luz enche a base
                               do item em 0,55 s e ai chama a funcao."""
    SEGURAR = 0.55
    LIMITE = 0.30                  # fracao da largura para o arrasto valer

    def __init__(self, **kwargs):
        self.ao_arrastar = kwargs.pop('ao_arrastar', None)
        self.ao_segurar = kwargs.pop('ao_segurar', None)
        super().__init__(**kwargs)
        self._g = None
        with self.canvas.after:
            self._c_seg = Color(0.6, 1.0, 1.0, 0)
            self._r_seg = Rectangle(pos=(0, 0), size=(0, 0))
            self._c_lado = Color(1.0, 0.18, 0.28, 0)
            self._l_lado = Line(width=dp(1.6))

    def _solta_visual(self):
        """O botao 'afundado' do toque volta ao tamanho (o soltar normal nao vem)."""
        Animation.cancel_all(self, 'escala')
        Animation(escala=1.0, duration=0.18, transition='out_quad').start(self)

    def _matriz_x(self):
        from animacoes_ui import _matriz
        return _matriz(self)[0]

    def on_touch_down(self, touch):
        if self.disabled or not self.collide_point(*touch.pos) or (self.ao_arrastar is None
                                                                  and self.ao_segurar is None):
            return super().on_touch_down(touch)
        r = super().on_touch_down(touch)
        self._parar_seg()
        # a lista so repassa o toque depois de um instante: o arrasto e o
        # tempo de segurar contam de onde/quando o dedo encostou de verdade
        # (medido na tela inteira: sx/osx nao mudam com a rolagem da lista)
        try:
            ja = max(0.0, Clock.get_time() - touch.time_start)
        except Exception:
            ja = 0.0
        self._g = {'id': touch.uid, 'modo': None, 't': min(ja, 0.3), 'dx': 0.0,
                   'aviso': False, 'ev': Clock.schedule_interval(self._segurando, 1 / 60.)
                   if self.ao_segurar else None}
        return r

    def _parar_seg(self):
        g = self._g
        if g and g.get('ev') is not None:
            g['ev'].cancel()
            g['ev'] = None
        self._c_seg.a = 0
        self._r_seg.size = (0, 0)

    def _segurando(self, dt):
        try:
            g = self._g
            if g is None or g['modo'] is not None or self.parent is None:
                self._c_seg.a = 0
                return False
            g['t'] += dt
            k = min(1.0, g['t'] / self.SEGURAR)
            if g['t'] > 0.12:                           # (um toque rapido nao acende nada)
                self._r_seg.pos = (self.x + dp(4), self.y + dp(3))
                self._r_seg.size = ((self.width - dp(8)) * k, dp(3))
                self._c_seg.a = 0.9
            if k >= 1:
                g['modo'] = 'segurou'
                g['ev'] = None
                self._c_seg.a = 0
                self.state = 'normal'
                self._solta_visual()
                try:
                    import tatil
                    tatil.confirmar()
                except Exception:
                    pass
                from animacoes_ui import pulso
                pulso(self, 1.04, 0.22)
                fn = self.ao_segurar
                Clock.schedule_once(lambda _d: fn(self), 0.05)
                return False
        except Exception as e:
            print(f"[item] segurar: {e}")
            return False

    def on_touch_move(self, touch):
        g = self._g
        if g is None or touch.uid != g['id']:
            return super().on_touch_move(touch)
        dx = (touch.sx - touch.osx) * Window.width
        dy = (touch.sy - touch.osy) * Window.height
        if g['modo'] is None:
            if self.ao_arrastar and abs(dx) > dp(12) and abs(dx) > abs(dy) * 1.4:
                g['modo'] = 'arrasto'
                self._parar_seg()
                self.state = 'normal'
                self._solta_visual()
            elif abs(dy) > dp(10) or abs(dx) > dp(12):
                g['modo'] = 'nada'                       # rolando a lista: nada de segurar
                self._parar_seg()
        if g['modo'] == 'arrasto':
            lim = self.width * self.LIMITE
            d = dx if abs(dx) <= lim else (lim + (abs(dx) - lim) * 0.35) * (1 if dx > 0 else -1)
            g['dx'] = dx
            tr = self._matriz_x()
            tr.x = d
            k = min(1.0, abs(dx) / lim)
            self._c_lado.a = 0.25 + 0.75 * k
            self._l_lado.rectangle = (self.x + dp(2), self.y + dp(2), self.width - dp(4), self.height - dp(4))
            if k >= 1 and not g['aviso']:
                g['aviso'] = True                        # passou do limite: tremidinha
                try:
                    import tatil
                    tatil.tecla()
                except Exception:
                    pass
            elif k < 1:
                g['aviso'] = False
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        g = self._g
        if g is None or touch.uid != g['id']:
            return super().on_touch_up(touch)
        modo = g['modo']
        if modo not in ('arrasto', 'segurou'):
            self._parar_seg()
            self._g = None
            return super().on_touch_up(touch)
        self._g = None
        self._parar_seg()
        touch.ungrab(self)
        self.state = 'normal'
        if modo == 'arrasto':
            valeu = abs(g['dx']) >= self.width * self.LIMITE
            tr = self._matriz_x()
            x0 = tr.x
            t = [0.0]

            def _volta(dt):
                try:
                    t[0] += dt
                    k = min(1.0, t[0] / 0.24)
                    tr.x = x0 * (1 - k) ** 3
                    self._c_lado.a = (1 - k) * (1.0 if valeu else 0.5)
                    if k >= 1:
                        tr.x = 0
                        self._c_lado.a = 0
                        return False
                except Exception:
                    tr.x = 0
                    return False
            Clock.schedule_interval(_volta, 1 / 60.)
            if valeu and self.ao_arrastar:
                fn = self.ao_arrastar
                Clock.schedule_once(lambda _d: fn(self), 0.18)
        return True


# ═══════════════════════════════════════════════════════════
#  GRÁFICO DE BARRAS HOLOGRÁFICO
# ═══════════════════════════════════════════════════════════

class GraficoBarras(Widget):
    """Producao dos ultimos dias. Quando os dados mudam as barras crescem da
    base (uma depois da outra) ou se transformam da altura de antes na nova."""
    dados = ListProperty([])
    titulo = StringProperty('PRODUÇÃO · ÚLTIMOS DIAS')

    ATRASO, DURACAO = 0.05, 0.5          # cascata entre barras / subida de cada uma
    __events__ = ('on_barra',)

    def on_barra(self, i):
        """Tocaram na barra i (a tela decide o que mostrar)."""

    LARG_MAX = 46          # dp: com poucos dias a barra nao vira um blocao

    def _layout(self):
        """Medidas em dp (o celular tem pixels bem menores que o PC)."""
        n = max(1, len(self.dados))
        px, pb, pt, esp = dp(10), dp(20), dp(28), dp(8)
        wu = self.width - px * 2
        larg = min((wu - esp * (n - 1)) / float(n), dp(self.LARG_MAX))
        total = n * larg + (n - 1) * esp
        x0 = self.x + px + (wu - total) / 2.0
        return {'px': px, 'pb': pb, 'pt': pt, 'esp': esp, 'larg': larg, 'x0': x0,
                'hmax': self.height - pb - pt}

    def centro_barra(self, i):
        lo = self._layout()
        return lo['x0'] + i * (lo['larg'] + lo['esp']) + lo['larg'] / 2.0

    def _barra_em(self, x):
        n = len(self.dados)
        if n == 0:
            return None
        lo = self._layout()
        passo = lo['larg'] + lo['esp']
        rel = x - lo['x0'] + lo['esp'] / 2.0
        i = int(rel // passo) if rel >= 0 else -1
        return i if 0 <= i < n else None

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or not self.dados:
            return super().on_touch_down(touch)
        i = self._barra_em(touch.x)
        if i is None:
            return super().on_touch_down(touch)
        self._destaque = [i, 0.0]
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._passo, 1 / 60.)
        self.dispatch('on_barra', i)
        return True

    def __init__(self, **kwargs):
        self._destaque = None
        super().__init__(**kwargs)
        self._tex_cache = {}   # {(text, size, cor): texture}
        self._vistas = []      # altura (0..0.9 do espaco) desenhada de cada barra agora
        self._de = []          # alturas no comeco da animacao
        self._t = None         # tempo da animacao (None = parada)
        self._ev = None
        self.bind(pos=self._draw, size=self._draw, dados=self._draw_reset, titulo=self._draw)

    def _alvos(self):
        maximo = max((d.get('valor', 0) for d in self.dados), default=0) or 1
        return [d.get('valor', 0) / float(maximo) * 0.90 for d in self.dados]

    def _draw_reset(self, *_):
        """Dados novos: as barras saem da altura de antes ate a nova."""
        self._tex_cache.clear()
        self._animar(list(self._vistas))

    def animar_entrada(self):
        """Ao abrir a tela: todas as barras crescem do chao."""
        self._animar([])

    def _animar(self, de):
        self._de = de
        self._t = 0.0
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._passo, 1 / 60.)
        self._draw()

    def _passo(self, dt):
        try:
            if self._destaque is not None:
                self._destaque[1] += dt
                if self._destaque[1] >= 0.7:
                    self._destaque = None
            if self._t is not None:
                self._t += dt
                if self._t >= self.DURACAO + self.ATRASO * len(self.dados) + 0.05:
                    self._t = None
            self._draw()
            if self._t is None and self._destaque is None:
                self._ev = None
                return False
        except Exception as e:
            print(f"[grafico] animacao: {e}")
            self._t = None
            self._ev = None
            return False

    def _altura(self, i, alvo):
        """(altura agora, quanto ja andou 0..1) da barra i."""
        if self._t is None:
            return alvo, 1.0
        de = self._de[i] if i < len(self._de) else 0.0
        k = min(1.0, max(0.0, (self._t - i * self.ATRASO) / self.DURACAO))
        if de <= 0.0:
            e = 1 + 1.7 * (k - 1) ** 3 + 0.7 * (k - 1) ** 2    # cresce passando um pouco e assenta
        else:
            e = 1 - (1 - k) ** 3                                 # transforma sem passar
        return de + (alvo - de) * e, k

    def _get_tex(self, text, size, cor):
        """Retorna textura cacheada — cria apenas na primeira chamada."""
        key = (str(text), size, cor)
        if key not in self._tex_cache:
            try:
                from kivy.core.text import Label as CoreLabel
                from kivy.metrics import sp
                lbl = CoreLabel(text=str(text), font_size=sp(size), color=cor,
                                font_name='rajdhani.ttf', bold=size >= 11)
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
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
            Color(0, 0.9, 1, 0.12)
            Line(rounded_rectangle=[self.x, self.y, self.width, self.height, dp(6)],
                 width=dp(1))

            if not self.dados:
                self._txt('SEM DADOS', self.center_x, self.center_y - dp(8),
                          (0.4, 0.4, 0.6, 0.7), 12)
                return

            lo = self._layout()
            px, pb, pt, esp = lo['px'], lo['pb'], lo['pt'], lo['esp']
            larg, hmax = lo['larg'], lo['hmax']

            self._txt(self.titulo,
                      self.center_x, self.top - dp(15), (0, 0.9, 1, 0.45), 9)
            Color(0, 0.9, 1, 0.12)
            Line(points=[self.x + px, self.y + pb - 1,
                         self.right - px, self.y + pb - 1], width=dp(1))

            vistas = []
            for i, (item, alvo) in enumerate(zip(self.dados, self._alvos())):
                bx   = lo['x0'] + i * (larg + esp)
                # (a barra recorde vai ate 90% para nao dominar toda a area)
                h_rel, kb = self._altura(i, alvo)
                vistas.append(h_rel)
                alt  = max(h_rel * hmax, 2)
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
                Line(rectangle=[bx, by, larg, alt], width=dp(0.8))
                Color(1, 1, 1, 0.28)
                Line(points=[bx + 1, by + alt, bx + larg - 1, by + alt], width=dp(1.2))

                if self._destaque is not None and self._destaque[0] == i:
                    # a barra tocada acende e apaga
                    a = 1 - self._destaque[1] / 0.7
                    Color(1, 1, 1, 0.22 * a)
                    Rectangle(pos=(bx, by), size=(larg, alt))
                    Color(1, 1, 1, 0.95 * a)
                    Line(rectangle=[bx - dp(2), by - dp(2), larg + dp(4), alt + dp(4)], width=dp(1.2))
                if kb < 1:
                    # a ponta da barra subindo brilha
                    Color(bc[0], bc[1], bc[2], 0.5 * (1 - kb))
                    Rectangle(pos=(bx - 1, by + alt - dp(2)), size=(larg + 2, dp(4)))

                val = item.get('valor', 0)
                if val > 0 and kb > 0.35:
                    # (o recorde em dourado: o '*' de antes nao cabia sem tapar o titulo)
                    cor_v = (1, 0.86, 0.25, 1) if item.get('record') else (1, 1, 1, 0.92)
                    self._txt(str(val), cx, by + alt + dp(2), cor_v, 11)
                lbl = item.get('label', '')
                if lbl:
                    self._txt(lbl, cx, self.y + dp(4), (0.62, 0.62, 0.86, 0.95), 9.5)
            self._vistas = vistas


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



_CACO_LUZ = (200, 255, 255)        # borda de cima/esquerda (onde bate a luz)
_CACO_SOMBRA = (30, 130, 185)      # borda de baixo/direita
_CACO_CLARO = (235, 255, 255)
_CACO_CRISTAL = ((70, 200, 255), (150, 235, 255))
# paletas dos cacos: 'vidro' (itens da tela: cristal ciano) e 'brasa' (o chefe
# da abertura: pedra escura com a borda em brasa, que vira cinza quente)
_CACO_PALETAS = {
    'vidro': {'luz': _CACO_LUZ, 'sombra': _CACO_SOMBRA, 'claro': _CACO_CLARO, 'cristal': _CACO_CRISTAL,
              'veu': (3, 4, 10, 50, 64), 'reflexo': (45, 60, 60), 'estalo': (255, 255, 255),
              'talho': (0.55, 1.0, 1.0),
              'luzes': ((0.7, 1.0, 1.0, 1), (1.0, 1.0, 1.0, 1), (0.78, 0.6, 1.0, 1))},
    'brasa': {'luz': (255, 196, 96), 'sombra': (150, 40, 16), 'claro': (255, 226, 150),
              'cristal': ((214, 84, 30), (255, 150, 60)),
              'veu': (1, 1, 0, 0, 0), 'reflexo': (40, 18, 6), 'estalo': (255, 236, 200),
              'talho': (1.0, 0.62, 0.22),
              'luzes': ((1.0, 0.72, 0.3, 1), (1.0, 0.92, 0.7, 1), (1.0, 0.42, 0.14, 1))},
}
_CACO_MAX_CELULAS = 4000          # itens grandes ganham blocos maiores (o custo fica igual)
_CANTOS = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


def _textura_blocos(w, h, buf):
    """Textura pequena (1 texel por bloco) ampliada sem suavizar."""
    from kivy.graphics.texture import Texture
    tex = Texture.create(size=(w, h), colorfmt='rgba')
    tex.mag_filter = 'nearest'
    tex.min_filter = 'nearest'
    tex.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
    return tex


def _foto_em_blocos(widget_alvo, gw, gh, b):
    """A foto do item reduzida a blocos de b px: (nc, nr, cores) com as
    linhas de baixo para cima; bloco transparente = None (fica fora dos cacos).
    Cada bloco fica com o ponto mais claro de 2x2 amostras (o texto fino nao
    some)."""
    nc = max(1, int(math.ceil(gw / b)))
    nr = max(1, int(math.ceil(gh / b)))
    cel = [None] * (nc * nr)
    try:
        op = widget_alvo.opacity
        widget_alvo.opacity = 1
        tex = widget_alvo.export_as_image().texture
        widget_alvo.opacity = op
        px = tex.pixels
        tw, th = tex.size
        fr = (0.3, 0.7) if nc * nr <= 5000 else (0.5,)  # 2x2 pontos por bloco (item enorme: 1)
        colunas = [[min(tw - 1, int((i + f) * b / gw * tw)) * 4 for f in fr] for i in range(nc)]
        for j in range(nr):
            # a foto vem de cima para baixo (linha 0 = topo do item)
            bases = [min(th - 1, max(0, int((1.0 - (j + f) * b / gh) * th))) * tw * 4 for f in fr]
            for i in range(nc):
                melhor, lum = None, -1
                for base in bases:
                    for col in colunas[i]:
                        o = base + col
                        if px[o + 3] > 50:
                            v = px[o] + px[o + 1] + px[o + 2]
                            if v > lum:
                                melhor, lum = o, v
                if melhor is not None:
                    cel[j * nc + i] = (px[melhor], px[melhor + 1], px[melhor + 2])
    except Exception as e:
        print(f"[estilhacos] sem foto do item: {e}")
    if not any(cel):
        cel = [(12, 45, 75)] * (nc * nr)
    return nc, nr, cel


def _cacos_em_blocos(nc, nr, cel, n_alvo=24):
    """Divide os blocos em cacos (celulas de Voronoi com sementes numa grade
    tremida): devolve o dono de cada bloco (-1 = vazio) e o numero de cacos."""
    t = max(1.0, math.sqrt(nc * nr / float(n_alvo)))
    cols = max(1, min(8, int(round(nc / t))))
    linhas = max(1, min(8, int(round(nr / t))))
    lw, lh = nc / float(cols), nr / float(linhas)
    sementes = {}
    for tj in range(linhas):
        for ti in range(cols):
            sementes[(ti, tj)] = (len(sementes), (ti + random.uniform(0.2, 0.8)) * lw,
                                  (tj + random.uniform(0.2, 0.8)) * lh)
    dono = [-1] * (nc * nr)
    for j in range(nr):
        tj = min(linhas - 1, int(j / lh))
        cy = j + 0.5
        for i in range(nc):
            if cel[j * nc + i] is None:
                continue
            ti = min(cols - 1, int(i / lw))
            cx = i + 0.5
            melhor, bd = 0, 1e18
            for sj in (tj - 1, tj, tj + 1):
                for si in (ti - 1, ti, ti + 1):
                    s = sementes.get((si, sj))
                    if s is not None:
                        d = (cx - s[1]) ** 2 + ((cy - s[2]) * 1.3) ** 2
                        if d < bd:
                            bd, melhor = d, s[0]
            dono[j * nc + i] = melhor
    return dono, len(sementes)


def _texturas_caco(g, d, dono, cel, nc, nr, pal=None):
    """As 4 caras de um caco: foto (contorno ciano de 1 bloco), branco (o
    estalo), cristal e cristal ralado em xadrez (desfazendo)."""
    i0 = min(c % nc for c in g)
    i1 = max(c % nc for c in g)
    j0 = min(c // nc for c in g)
    j1 = max(c // nc for c in g)
    w, h = i1 - i0 + 1, j1 - j0 + 1
    pal = pal or _CACO_PALETAS['vidro']
    vn, vd, vr, vg, vb = pal['veu']
    rf = pal['reflexo']
    estalo = bytes(pal['estalo']) + bytes((255,))
    foto, bran, cris, ralo = (bytearray(w * h * 4) for _ in range(4))
    for c in g:
        i, j = c % nc, c // nc
        o = ((j - j0) * w + (i - i0)) * 4
        esq_ = i > 0 and dono[c - 1] == d
        dir_ = i < nc - 1 and dono[c + 1] == d
        baixo = j > 0 and dono[c - nc] == d
        cima = j < nr - 1 and dono[c + nc] == d
        dentro = esq_ and dir_ and baixo and cima
        reflexo = (i - j) % 11 == 0                    # risco de luz na diagonal (vidro)
        if dentro:
            r, gg, bb = cel[c]
            # a foto com um veu ciano (vidro) e o reflexo um pouco mais claro
            cf = (r * vn // vd + vr, gg * vn // vd + vg, bb * vn // vd + vb)
            if reflexo:
                cf = (min(255, cf[0] + rf[0]), min(255, cf[1] + rf[1]), min(255, cf[2] + rf[2]))
            cc = pal['cristal'][1] if reflexo else pal['cristal'][0]
        else:
            cf = pal['luz'] if (not cima or not esq_) else pal['sombra']
            cc = pal['claro']
        foto[o:o + 4] = bytes((cf[0], cf[1], cf[2], 255))
        bran[o:o + 4] = estalo
        cris[o:o + 4] = bytes((cc[0], cc[1], cc[2], 255))
        if (i + j) % 2:
            ralo[o:o + 4] = bytes((cc[0], cc[1], cc[2], 255))
    texs = tuple(_textura_blocos(w, h, buf) for buf in (foto, bran, cris, ralo))
    return texs, i0, j0, w, h


def explodir_estilhacos(widget_alvo, callback_final, corte=None, tremor=14, px=None, abaixo_de=None,
                        racha=None, ponto=None, adiar=False, max_celulas=None, n_cacos=24, paleta=None):
    """
    Estilhacos no estilo SAO, em pixel art: a foto do item vira blocos de
    `px` px de tela e se parte em cacos feitos desses blocos (contorno ciano
    de 1 bloco). Os cacos piscam brancos no estalo, voam em degraus de
    bloco (30 por segundo), giram de 90 em 90 graus, viram cristal ciano,
    se desfazem em xadrez e soltam faiscas quadradas que sobem.
    corte = angulo (graus) do golpe que acertou o item, ou dois angulos (o
    X): antes de voar ele racha ao longo de cada talho (uma fileira de
    blocos de luz acende e os pedacos se afastam um bloco de cada vez,
    durante `racha` s) e os cacos seguem o golpe.
    abaixo_de = camada (na Window) que continua por cima dos cacos - o Yoru
    nunca fica escondido atras deles.
    ponto = (x, y) na janela por onde o talho passa (padrao: o meio do item).
    adiar=True: so PREPARA (foto, cacos, texturas - a parte pesada) e devolve
    a funcao que solta a explosao; assim a conta pode ser feita num momento
    em que a cena esta congelada, e a explosao sai sem tranco.
    max_celulas / n_cacos: limite de blocos e quantos cacos (itens grandes).
    paleta: 'vidro' (padrao, cristal ciano) ou 'brasa' (pedra em brasa).
    """
    if tremor and not adiar:
        tremer_tela(tremor)
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

    def _falhou(*_):
        widget_alvo.opacity = 0
        _acabar()

    camada = Widget(size_hint=(None, None), size=Window.size, pos=(0, 0))
    try:
        if widget_alvo.parent:
            gx, gy = widget_alvo.parent.to_window(widget_alvo.x, widget_alvo.y)
        else:
            gx, gy = widget_alvo.to_window(0, 0)
        gw, gh = max(1.0, widget_alvo.width), max(1.0, widget_alvo.height)
        b = float(px or max(3, round(dp(3))))
        b = max(b, math.ceil(math.sqrt(gw * gh / float(max_celulas or _CACO_MAX_CELULAS))))
        nc, nr, cel = _foto_em_blocos(widget_alvo, gw, gh, b)
        dono, n = _cacos_em_blocos(nc, nr, cel, n_cacos)
        grupos = [[] for _ in range(n)]
        for c, d in enumerate(dono):
            if d >= 0:
                grupos[d].append(c)

        cortes = [] if corte is None else (list(corte) if isinstance(corte, (list, tuple)) else [corte])
        racha = (0.16 if racha is None else racha) if cortes else 0.0     # tempo rachando antes de voar
        dirs = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in cortes] or [(1.0, 0.0)]
        ux, uy = dirs[0]
        ccx, ccy = ponto if ponto is not None else (gx + gw / 2.0, gy + gh / 2.0)

        pal = _CACO_PALETAS.get(paleta or 'vidro', _CACO_PALETAS['vidro'])
        cacos = []
        talho, brilho_talho = [], []
        with camada.canvas:
            for d, g in enumerate(grupos):
                if not g:
                    continue
                texs, i0, j0, w, h = _texturas_caco(g, d, dono, cel, nc, nr, pal)
                cor = Color(1, 1, 1, 1)
                ret = Rectangle(texture=texs[0], pos=(gx + i0 * b, gy + j0 * b), size=(w * b, h * b))
                mx, my = gx + (i0 + w / 2.0) * b, gy + (j0 + h / 2.0) * b
                dx, dy = mx - ccx, my - ccy
                # para que lado de cada talho o caco ficou: e para la que ele se afasta
                sx = sy = 0.0
                for cx_, cy_ in dirs:
                    lado = 1.0 if dx * -cy_ + dy * cx_ >= 0 else -1.0
                    sx += -cy_ * lado
                    sy += cx_ * lado
                if not cortes:
                    # voa para fora do centro do item, com um empurrao para cima
                    ang = math.atan2(dy + random.uniform(-0.2, 0.2) * gh, dx + random.uniform(-0.3, 0.3) * gw)
                    v = dp(random.uniform(140, 420))
                    vx, vy = math.cos(ang) * v, math.sin(ang) * v * 0.7 + dp(random.uniform(120, 260))
                else:
                    # cada pedaco se afasta do talho e tudo segue o golpe
                    afasta = dp(random.uniform(90, 260))
                    segue = dp(random.uniform(160, 420)) / len(dirs)
                    vx = sx * afasta + ux * segue + random.uniform(-1, 1) * dp(60)
                    vy = sy * afasta + uy * segue + dp(random.uniform(60, 200))
                cacos.append({'ret': ret, 'cor': cor, 'texs': texs, 'w': w, 'h': h, 'mx': mx, 'my': my,
                              'x': 0.0, 'y': 0.0, 'vx': vx, 'vy': vy, 'sx': sx, 'sy': sy,
                              'giro': random.choice((0, 0, 1, -1, 1, -1)), 'per': random.uniform(0.07, 0.13),
                              'rq': 0, 'cara': 0, 'vida': random.uniform(0.7, 1.0), 'soltou': False})
            if cortes:
                # os talhos em blocos: miolo branco e brilho ciano do lado
                meia = math.hypot(gw, gh) / 2.0 + 2 * b
                vistos = set()
                brilhos = set()
                passos = int(meia / (b * 0.5))
                for cx_, cy_ in dirs:
                    ox, oy = (1, 0) if abs(cy_) >= abs(cx_) else (0, 1)
                    for s in range(-passos, passos + 1):
                        ci = math.floor((ccx + cx_ * s * b * 0.5 - gx) / b)
                        cj = math.floor((ccy + cy_ * s * b * 0.5 - gy) / b)
                        if not (-1 <= ci <= nc and -1 <= cj <= nr):
                            continue                  # o talho so risca o item (e 1 bloco em volta)
                        vistos.add((ci, cj))
                        for sg in (-1, 1):
                            brilhos.add((ci + sg * ox, cj + sg * oy))
                c_brilho = Color(pal['talho'][0], pal['talho'][1], pal['talho'][2], 0)
                for ci, cj in brilhos - vistos:
                    brilho_talho.append(Rectangle(pos=(gx + ci * b, gy + cj * b), size=(b, b)))
                c_talho = Color(1, 1, 1, 0)
                for ci, cj in vistos:
                    talho.append(Rectangle(pos=(gx + ci * b, gy + cj * b), size=(b, b)))
            # faiscas quadradas (os cacos viram luz no fim)
            luzes = []
            for _ in range(min(90, len(cacos) * 3)):
                c = Color(*random.choice(pal['luzes']))
                luzes.append([c, Rectangle(size=(0, 0)), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        def _poe(k):
            """Enquadra o caco na grade de blocos, girado de 90 em 90."""
            rq = k['rq'] % 4
            w, h = (k['w'], k['h']) if rq % 2 == 0 else (k['h'], k['w'])
            cx, cy = k['mx'] + k['x'], k['my'] + k['y']
            k['ret'].pos = (gx + round((cx - w * b / 2.0 - gx) / b) * b,
                            gy + round((cy - h * b / 2.0 - gy) / b) * b)
            k['ret'].size = (w * b, h * b)
            cantos = _CANTOS[-rq:] + _CANTOS[:-rq] if rq else _CANTOS
            k['ret'].tex_coords = tuple(v for p in cantos for v in p)

        livres = list(range(len(luzes)))
        vivas = []
        t = [0.0]
        degrau = [-1]
        grav = dp(1100)

        def _passo(dt):
            try:
                dt = min(dt, 1 / 30.)
                t[0] += dt
                d = int(t[0] * 30)
                novo = d != degrau[0]             # desenho em degraus de 1/30 s
                degrau[0] = d
                if racha and t[0] < racha:
                    # rachando: o talho acende e os pedacos se afastam bloco a bloco
                    if novo:
                        c_talho.a = 1
                        c_brilho.a = 1
                        passo = min(3, 1 + d // 2)
                        for k in cacos:
                            k['x'] = round(k['sx'] * passo) * b
                            k['y'] = round(k['sy'] * passo) * b
                            _poe(k)
                    return
                tv = t[0] - racha                 # tempo desde que os cacos soltaram
                if racha and novo:
                    c_talho.a = 1 if tv < 1 / 30. else 0
                    c_brilho.a = 1 if tv < 3 / 30. else 0
                for k in cacos:
                    u = tv / k['vida']
                    if k['cara'] == 4:
                        continue
                    k['vy'] -= grav * dt
                    k['vx'] *= 0.985
                    k['x'] += k['vx'] * dt
                    k['y'] += k['vy'] * dt
                    if not novo:
                        continue
                    cara = 1 if tv < 2 / 30. else (0 if u < 0.45 else (2 if u < 0.72 else (3 if u < 1 else 4)))
                    if cara != k['cara']:
                        k['cara'] = cara
                        if cara == 4:
                            k['ret'].size = (0, 0)
                            k['cor'].a = 0
                        else:
                            k['ret'].texture = k['texs'][cara]
                    if cara == 4:
                        continue
                    if k['giro']:
                        k['rq'] = k['giro'] * int(tv / k['per'])
                    _poe(k)
                    if u > 0.6 and not k['soltou']:
                        k['soltou'] = True
                        for _ in range(3):
                            if not livres:
                                break
                            i = livres.pop()
                            L = luzes[i]
                            L[2] = k['mx'] + k['x'] + random.uniform(-2, 2) * b
                            L[3] = k['my'] + k['y'] + random.uniform(-2, 2) * b
                            L[4] = random.uniform(-dp(30), dp(30))
                            L[5] = dp(random.uniform(60, 150))
                            L[6] = L[7] = random.uniform(0.35, 0.6)
                            vivas.append(i)
                for i in list(vivas):
                    L = luzes[i]
                    L[6] -= dt
                    if L[6] <= 0:
                        L[1].size = (0, 0)
                        vivas.remove(i)
                        livres.append(i)
                        continue
                    L[2] += L[4] * dt
                    L[3] += L[5] * dt
                    if novo:
                        s = b if L[6] > L[7] * 0.5 else max(1.0, round(b / 2.0))   # encolhe num degrau
                        L[1].pos = (round(L[2] / s) * s, round(L[3] / s) * s)
                        L[1].size = (s, s)
                if tv >= 1.15:
                    _acabar()
                    return False
            except Exception as e:
                print(f"[estilhacos] {e}")
                _acabar()
                return False
        def _soltar(*_):
            try:
                widget_alvo.opacity = 0
                Window.add_widget(camada)
                if abaixo_de is not None and abaixo_de.parent is Window:
                    Window.remove_widget(abaixo_de)            # o Yoru volta para cima dos cacos
                    Window.add_widget(abaixo_de)
                if tremor and adiar:
                    tremer_tela(tremor)
                Clock.schedule_interval(_passo, 1 / 60.)
                Clock.schedule_once(_acabar, 2.0 + racha)      # seguranca
            except Exception as e:
                print(f"[estilhacos] soltar: {e}")
                _falhou()
        if adiar:
            return _soltar
        _soltar()
    except Exception as e:
        print(f"[estilhacos] ignorado: {e}")
        if adiar:
            return _falhou
        _falhou()


# ══════════════════════════════════════════════════════════════════════
#  TECLADOS CUSTOMIZADOS SAO — substitui teclado Android
# ══════════════════════════════════════════════════════════════════════

_LINHAS_LETRAS = ['QWERTYUIOP', 'ASDFGHJKLÇ', 'ZXCVBNM']

# tecla de acento: troca a ultima letra pela proxima da roda (A -> Á -> Ã -> Â -> À -> A)
_RODAS_ACENTO = ['AÁÃÂÀ', 'EÉÊ', 'IÍ', 'OÓÕÔ', 'UÚ', 'CÇ']
_PROXIMO_ACENTO = {}
for _roda in _RODAS_ACENTO:
    for _i, _ch in enumerate(_roda):
        _prox = _roda[(_i + 1) % len(_roda)]
        _PROXIMO_ACENTO[_ch] = _prox
        _PROXIMO_ACENTO[_ch.lower()] = _prox.lower()


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
        self._ev_del = None
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

    # O teclado SEGURA todo toque que cai na area dele: nas teclas, nos vaos
    # entre elas, nas bordas e na linha de sugestoes. Antes, o toque num vao
    # "vazava" para o que estava embaixo (abria o aviso de apagar uma peca da
    # lista, apertava o Voltar escondido na tela de Ganhos, rolava a lista).
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            super().on_touch_down(touch)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            super().on_touch_move(touch)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            super().on_touch_up(touch)
            return True
        return super().on_touch_up(touch)

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
        elif char == 'ACENTO':
            ult = t.text[-1:]
            if ult in _PROXIMO_ACENTO:
                t.text = t.text[:-1] + _PROXIMO_ACENTO[ult]
        elif char == ' ':
            t.text += ' '
        elif char == ',':
            if ',' not in t.text and '.' not in t.text:      # uma virgula so
                t.text += ','
        else:
            t.text += char
        self._mudou()

    def _mudou(self):
        """O texto mudou (as subclasses atualizam as sugestoes)."""

    # segurar o DEL apaga uma letra atras da outra
    def _segurar_del(self, *_):
        self._soltar_del()
        self._ev_del = Clock.schedule_once(self._repetir_del, 0.42)

    def _repetir_del(self, dt):
        self._ev_del = None
        t = self.target
        if self.parent is None or not t or not t.text:
            return
        self._press('DEL')
        tatil.tecla()
        self._ev_del = Clock.schedule_once(self._repetir_del, 0.06)

    def _soltar_del(self, *_):
        if self._ev_del is not None:
            self._ev_del.cancel()
            self._ev_del = None

    def _press_com_feedback(self, btn, char):
        """Feedback ao pressionar tecla — vibracao curtinha e flash cyan."""
        tatil.tecla()
        self._press(char)
        # Flash na cor do botao: cyan -> escuro -> cyan
        try:
            Animation.cancel_all(btn, 'color')
            (Animation(color=[1, 1, 1, 1], duration=0.04, transition='out_expo') +
             Animation(color=[0, 0.9, 1, 1], duration=0.10, transition='in_expo')
             ).start(btn)
        except Exception:
            pass

    def _key(self, char, font_size='18sp', rotulo=None, **kw):
        btn = _BotaoTecla(text=rotulo or char, font_size=font_size, **kw)
        btn.bind(on_press=lambda b: self._press_com_feedback(b, char))
        if char == 'DEL':
            btn.bind(on_press=self._segurar_del, on_release=self._soltar_del)
        return btn


def _sem_acento(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c)).lower()


class _LinhaSugestoes(BoxLayout):
    """Pecas ja usadas, em cima do teclado de letras: um toque preenche o
    nome. fonte(texto) -> nomes (mais recentes primeiro)."""

    MAX = 3

    def __init__(self, fonte, ao_escolher, **kwargs):
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(42))
        super().__init__(**kwargs)
        self.spacing = dp(5)
        self.fonte = fonte
        self.ao_escolher = ao_escolher

    def atualizar(self, texto):
        try:
            nomes = list(self.fonte(texto or ''))[:self.MAX]
        except Exception as e:
            print(f"[teclado] sugestoes: {e}")
            nomes = []
        self.clear_widgets()
        for n in nomes:
            b = _BotaoTecla(text=n, font_size='15sp', shorten=True, halign='center', valign='middle')
            b.font_name = 'rajdhani.ttf'
            b.color = [0.75, 0.55, 1, 1]
            b.bind(size=lambda w, s: setattr(w, 'text_size', (max(1, s[0] - dp(10)), s[1])))
            b.bind(on_press=lambda w, n=n: self._escolher(w, n))
            self.add_widget(b)

    def _escolher(self, w, nome):
        tatil.tecla()
        self.ao_escolher(nome)


class TecladoLetras(_TecladoBase):
    """
    Teclado SAO com letras A-Z, Ç e a tecla de acento (´ ~: troca a ultima
    letra por A -> Á -> Ã -> Â -> À...). Font 18sp — legivel nos botoes
    ~36dp da linha QWERTY. sugestoes(texto) -> nomes: linha de pecas ja
    usadas em cima das letras.
    """

    def __init__(self, target, fechar=None, sugestoes=None, **kwargs):
        kwargs['height'] = dp(252) + (dp(46) if sugestoes else 0)
        super().__init__(target, fechar=fechar, **kwargs)
        self._sug = None
        if sugestoes:
            self._sug = _LinhaSugestoes(sugestoes, self._usar_sugestao)
            self.add_widget(self._sug)
            self._sug.atualizar(target.text if target else '')

        for linha in _LINHAS_LETRAS:
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(3))
            for c in linha:
                row.add_widget(self._key(c, font_size='18sp'))
            if linha == _LINHAS_LETRAS[-1]:
                row.add_widget(self._key('ACENTO', font_size='16sp', rotulo='´ ~', size_hint_x=1.6))
            self.add_widget(row)

        # Linha especial: CLR | espaço | DEL | OK
        spc = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        spc.add_widget(self._key('CLR', font_size='12sp', size_hint_x=0.18))
        spc.add_widget(self._key(' ',   font_size='12sp', size_hint_x=0.44))
        spc.add_widget(self._key('DEL', font_size='12sp', size_hint_x=0.18))
        spc.add_widget(self._key('OK',  font_size='14sp', size_hint_x=0.20))
        self.add_widget(spc)

    def _mudou(self):
        if self._sug is not None and self.target is not None:
            self._sug.atualizar(self.target.text)

    def _usar_sugestao(self, nome):
        if self.target is not None:
            self.target.text = nome
        self._mudou()


class TecladoNumeros(_TecladoBase):
    """
    Teclado SAO apenas com numeros 0-9.
    decimal=True inclui a virgula para campos R$.
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
            last.add_widget(self._key(',',   font_size='22sp', size_hint_x=0.25))
            last.add_widget(self._key('0',   font_size='26sp', size_hint_x=0.25))
            last.add_widget(self._key('DEL', font_size='12sp', size_hint_x=0.25))
            last.add_widget(self._key('OK',  font_size='14sp', size_hint_x=0.25))
        else:
            last.add_widget(self._key('CLR', font_size='12sp', size_hint_x=0.25))
            last.add_widget(self._key('0',   font_size='26sp', size_hint_x=0.25))
            last.add_widget(self._key('DEL', font_size='12sp', size_hint_x=0.25))
            last.add_widget(self._key('OK',  font_size='14sp', size_hint_x=0.25))
        self.add_widget(last)


# ══════════════════════════════════════════════════════════════════════
#  BARRA DE META (faixas de pagamento, meta do dia, ritmo por hora)
# ══════════════════════════════════════════════════════════════════════
class BarraMeta(Widget):
    """Barra holografica em BLOCOS (estilo HUD do SAO): o que ja foi feito
    acende bloco a bloco ate `valor` (de 0 a `maximo`); cada marca e um
    traco vertical com o nome em cima - ex.: as faixas 2.500 / 3.000, ou as
    referencias 60/h e 90/h. definir(valor) anima a subida."""
    valor = NumericProperty(0.0)
    maximo = NumericProperty(100.0)
    cor = ListProperty([0, 0.9, 1, 1])

    def __init__(self, **kwargs):
        self.marcas = []                         # [(valor, texto, (r, g, b, a))]
        self._tex = {}                           # textura do nome de cada marca
        self._flash = {}                         # marca -> brilho (1 -> 0) ao ser alcancada
        self._subindo = False
        self._varre = None                       # reflexo correndo pelo que ja encheu (0..1)
        self._ev = None
        self._ultimo = 0.0
        super().__init__(**kwargs)
        self.bind(pos=self._desenhar, size=self._desenhar, valor=self._ao_valor, maximo=self._desenhar,
                  cor=self._desenhar)
        Clock.schedule_once(self._desenhar, 0)
        self._ev_vida = Clock.schedule_interval(self._talvez_varrer, 4.2)

    def definir(self, valor, maximo=None, marcas=None, cor=None, animar=True):
        if maximo is not None:
            self.maximo = max(1.0, float(maximo))
        if marcas is not None:
            self.marcas = list(marcas)
        if cor is not None:
            self.cor = list(cor)
        Animation.cancel_all(self, 'valor')
        alvo = max(0.0, min(float(valor), self.maximo))
        if animar:
            self._flash = {}
            self.valor = 0.0
            self._ultimo = 0.0
            self._subindo = True
            a = Animation(valor=alvo, duration=1.1, transition='out_cubic')
            a.bind(on_complete=self._fim_subida)
            a.start(self)
        else:
            self.valor = alvo
            self._ultimo = alvo
        self._desenhar()

    def _fim_subida(self, *_):
        self._subindo = False
        self._desenhar()

    def _ao_valor(self, *_):
        # passou de uma marca agora: ela acende
        for k, (v, _txt, _rgba) in enumerate(self.marcas):
            if self._ultimo < v <= self.valor:
                self._flash[k] = 1.0
                self._ligar()
                fn = getattr(self, 'ao_cruzar', None)
                if fn is not None and self.get_root_window() is not None:
                    try:
                        mx = self.x + self.width * min(1.0, v / max(1.0, self.maximo))
                        fn(k, *self.to_window(mx, self.y + self.height * 0.4))
                    except Exception as e:
                        print(f"[barra meta] ao cruzar: {e}")
        self._ultimo = self.valor
        self._desenhar()

    def _talvez_varrer(self, dt):
        # de tempos em tempos um reflexo corre pelo que ja encheu (so na tela)
        try:
            if self.valor > 0 and not self._subindo and self.get_root_window() is not None:
                self._varre = 0.0
                self._ligar()
        except Exception:
            pass

    def _ligar(self):
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._quadro, 1 / 60.)

    def _quadro(self, dt):
        try:
            for k in list(self._flash):
                self._flash[k] -= dt / 0.7
                if self._flash[k] <= 0:
                    del self._flash[k]
            if self._varre is not None:
                self._varre += dt / 1.1
                if self._varre >= 1:
                    self._varre = None
            self._desenhar()
            if not self._flash and self._varre is None:
                self._ev = None
                return False
        except Exception as e:
            print(f"[barra meta] quadro: {e}")
            self._ev = None
            return False

    def _textura(self, txt):
        tex = self._tex.get(txt)
        if tex is None:
            cl = CoreLabel(text=txt, font_name='rajdhani.ttf', font_size=dp(11), bold=True)
            cl.refresh()
            tex = self._tex[txt] = cl.texture
        return tex

    def _desenhar(self, *_):
        c = self.canvas
        c.clear()
        if self.width < 10 or self.height < 6:
            return
        x, y, w = self.x, self.y, self.width
        topo_txt = dp(14)
        h = max(dp(8), self.height - topo_txt)
        bloco, vao = dp(5), dp(2)
        n = max(1, int((w + vao) // (bloco + vao)))
        f = n * self.valor / max(1.0, self.maximo)
        cheios = int(f)
        r, g, b, a = self.cor
        varre = None if self._varre is None else self._varre * (cheios + 6) - 3
        with c:
            Color(0.03, 0.04, 0.10, 0.9)
            Rectangle(pos=(x, y), size=(w, h))
            for i in range(n):
                bx = x + i * (bloco + vao)
                if i < cheios:
                    luz = 1.0 if i == cheios - 1 else 0.82       # a ponta acesa mais forte
                    br = 0.0
                    if self._subindo:
                        br = max(0.0, 1 - (f - i) / 5.0) * 0.75  # rastro claro atras da ponta
                    if varre is not None:
                        br = max(br, max(0.0, 1 - abs(i - varre) / 3.0) * 0.55)
                    cr = r * luz + (1 - luz) * 0.2
                    cg = g * luz + (1 - luz) * 0.2
                    cb = b * luz + (1 - luz) * 0.2
                    Color(cr + (1 - cr) * br, cg + (1 - cg) * br, cb + (1 - cb) * br, a)
                elif i == cheios and self._subindo:
                    Color(1, 1, 1, a * (f - cheios))              # o bloco que esta acendendo
                else:
                    Color(r, g, b, 0.10)
                Rectangle(pos=(bx, y + dp(2)), size=(bloco, h - dp(4)))
            if self._subindo and cheios > 0:
                px = x + min(f, n) * (bloco + vao)               # halo na ponta
                Color(r, g, b, 0.28)
                Rectangle(pos=(px - dp(9), y - dp(1)), size=(dp(14), h + dp(2)))
            Color(r, g, b, 0.55)
            Line(rectangle=(x, y, w, h), width=1.1)
            for k, (v, txt, rgba) in enumerate(self.marcas):
                mx = x + w * min(1.0, max(0.0, v / max(1.0, self.maximo)))
                fl = max(0.0, self._flash.get(k, 0.0))
                ja = self.valor >= v
                if fl > 0:
                    Color(rgba[0], rgba[1], rgba[2], 0.45 * fl)
                    Rectangle(pos=(mx - dp(5), y - dp(4)), size=(dp(10), h + dp(8)))
                cor_m = [rgba[0] + (1 - rgba[0]) * fl, rgba[1] + (1 - rgba[1]) * fl,
                         rgba[2] + (1 - rgba[2]) * fl, rgba[3] if ja else rgba[3] * 0.55]
                Color(*cor_m)
                Rectangle(pos=(mx - dp(1), y - dp(2)), size=(dp(2), h + dp(4)))
                if txt:
                    tex = self._textura(txt)
                    tx = max(x, min(x + w - tex.size[0], mx - tex.size[0] / 2.0))
                    Color(*cor_m)
                    Rectangle(texture=tex, pos=(tx, y + h + dp(1) + dp(2) * fl), size=tex.size)
