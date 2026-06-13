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
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import (
    Color, Rectangle, RenderContext, Ellipse, Line,
    PushMatrix, PopMatrix, Rotate, Scale, Triangle, RoundedRectangle
)
from kivy.properties import NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import Label as CoreLabel
from kivy.animation import Animation
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
        # Garante multiline=False por padrão (linha única)
        kwargs.setdefault('multiline', False)
        super().__init__(**kwargs)
        # bind PASSIVO — apenas observa, nunca interfere
        self.bind(focus=self._ao_focar)
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
        — foreground_color: flash branco puro → ciano
        — borda_color: pulso de alta intensidade → retorna ao estado de foco
        Tudo via bind passivo, sem tocar no buffer.
        """
        if not valor:
            return
        # Flash do texto: branco → ciano (sensação de materialização)
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
    escala    = NumericProperty(0)
    opacidade = NumericProperty(0)
    cor       = ListProperty([0, 0.89, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw,
                  escala=self._draw, opacidade=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        with self.canvas:
            PushMatrix()
            Scale(self.escala, self.escala, 1, origin=self.center)
            cx, cy = self.center
            Color(self.cor[0], self.cor[1], self.cor[2], self.opacidade)
            Triangle(points=[cx - 4, cy - 25, cx + 4, cy - 25, cx, cy + 45])
            Color(self.cor[0], self.cor[1], self.cor[2], self.opacidade * 0.3)
            Line(points=[cx, cy - 25, cx, cy + 50], width=2.5)
            Color(self.cor[0] * 0.8, self.cor[1], self.cor[2], self.opacidade)
            Rectangle(pos=(cx - 12, cy - 27), size=(24, 5))
            Color(0.1, 0.1, 0.2, self.opacidade)
            Rectangle(pos=(cx - 2, cy - 45), size=(4, 18))
            PopMatrix()


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
        alvo = (self.valor / self.maximo) * 360 if self.maximo > 0 else 0

        Animation(angulo_preenchimento=alvo, valor_display=self.valor,
                  duration=1.6, transition='out_elastic').start(self)

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
    - on_press: dispara flash branco → retorna ao ciano (novo requisito v6).
    """
    escala       = NumericProperty(1.0)
    brilho       = NumericProperty(0.0)
    cor_borda    = ListProperty([0.0, 0.85, 1.0, 0.9])
    cor_borda_kv = ListProperty([0.0, 0.85, 1.0, 0.9])   # cópia KV para reset
    cor_fundo    = ListProperty([0.04, 0.04, 0.15, 0.92])
    cor_texto    = ListProperty([0.0,  0.90, 1.0,  1.0])

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
        for _ in range(22):    # 40 → 22: menos carga no Android
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
    escala = NumericProperty(1.0)

    def __init__(self, pos, size, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = size
        self.pos  = pos
        self.bind(pos=self._upd, size=self._upd, escala=self._upd, opacity=self._upd)

    def _upd(self, *_):
        self.canvas.clear()
        with self.canvas:
            PushMatrix()
            Scale(self.escala, self.escala, 1, origin=self.center)
            Color(0.8, 1, 1, self.opacity)
            Rectangle(pos=self.pos, size=self.size)
            PopMatrix()


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
    Explosão SAO com coordenadas globais (Window space).
    Reduzido para 12 cacos + 8 poeira = 20 widgets totais
    (vs 50 anterior) — reduz spike de frame em ~60%.
    """
    tremer_tela(14)

    if widget_alvo.parent:
        gx, gy = widget_alvo.parent.to_window(widget_alvo.x, widget_alvo.y)
    else:
        gx, gy = widget_alvo.to_window(0, 0)
    gw, gh = widget_alvo.size

    widget_alvo.opacity = 0

    camada = FloatLayout(size=Window.size)
    Window.add_widget(camada)

    flash = FlashExplosao((gx, gy), (gw, gh))
    camada.add_widget(flash)
    Animation(opacity=0, escala=1.6, duration=0.20).start(flash)

    # 12 cacos (era 28)
    for _ in range(12):
        c   = CacoSAO(gx, gy, gw, gh)
        camada.add_widget(c)
        nx  = c.x + random.randint(-260, 260)
        nyp = c.y + random.randint(60, 160)
        nyc = nyp - random.randint(200, 420)
        (Animation(x=nx, y=nyp, angulo=random.randint(360, 720),
                   duration=0.26, transition='out_circ') +
         Animation(y=nyc, opacity=0, escala=0,
                   duration=0.55, transition='in_quad')).start(c)

    # 8 pontos de poeira (era 22)
    for _ in range(8):
        p = PoeiraDigital(gx, gy, gw, gh)
        camada.add_widget(p)
        Animation(x=p.x + random.randint(-160, 160),
                  y=p.y + random.randint(60, 300),
                  opacity=0, duration=0.75).start(p)

    Clock.schedule_once(
        lambda dt: (Window.remove_widget(camada), callback_final()), 0.95)
