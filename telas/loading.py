"""telas/loading.py — TelaLoading otimizada (18s → ~12s)"""
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.animation import Animation
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
import random

from efeitos import tremer_tela
from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup


def _safe_treme(intensidade):
    """Wrapper seguro para tremer_tela — nunca deixa exceção vazar."""
    try:
        from efeitos import tremer_tela
        tremer_tela(intensidade)
    except Exception as e:
        print(f"[loading] tremer_tela ignorado: {e}")


def _safe_mudar_tela(destino):
    """Wrapper seguro para mudar_tela — nunca deixa exceção vazar."""
    try:
        app = App.get_running_app()
        if app:
            app.mudar_tela(destino)
    except Exception as e:
        print(f"[loading] mudar_tela({destino}) ignorado: {e}")


class TelaLoading(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typing_ativo = False

    def on_enter(self):
        Clock.schedule_once(self.preparar, 0.1)

    def on_leave(self, *_):
        self._typing_ativo = False

    def preparar(self, dt):
        self._typing_ativo = True
        try:
            self.ids.terminal_box.opacity    = 0
            self.ids.titulo_label.opacity    = 0
            self.ids.espada_esq.opacidade    = 0; self.ids.espada_esq.escala = 0
            self.ids.espada_dir.opacidade    = 0; self.ids.espada_dir.escala = 0
            self.reator                      = self.ids.reator_shader
            self.reator.build_progress       = 0.0
            self.reator.core_color           = [0, 0.89, 1]
            self.ids.barra_loading.progresso = 0
            self.ids.console_text.text       = ""
            # ↓ Reduzido de 0.3s para 0.1s
            Clock.schedule_once(self.start_anim, 0.1)
        except Exception as e:
            print(f"[LOADING] ids não prontos: {e}")
            Clock.schedule_once(
                lambda _: _safe_mudar_tela("menu"), 0.5)

    def printar_texto(self, texto, callback, vel=0.025):
        # vel padrão reduzido de 0.03 → 0.025
        buf   = self.ids.console_text.text
        c_idx = 0

        def tick(dt):
            nonlocal c_idx, buf
            if not self._typing_ativo:
                return
            if c_idx < len(texto):
                char = texto[c_idx]
                if char == '[':
                    end = texto.find(']', c_idx)
                    if end == -1:
                        buf += char; c_idx += 1
                    else:
                        buf += texto[c_idx:end + 1]; c_idx = end + 1
                else:
                    buf += char; c_idx += 1
                self.ids.console_text.text = buf + "_"
                Clock.schedule_once(tick, vel)
            else:
                self.ids.console_text.text = buf
                callback()

        Clock.schedule_once(tick, vel)

    def start_anim(self, dt):
        # Terminal fade: 1.0s → 0.5s
        Animation(opacity=1, duration=0.5).start(self.ids.terminal_box)
        self.ids.barra_loading.opacity = 1
        self.start_text()

    def start_text(self):
        def p1():
            # durations: 1.5s → 1.2s
            Animation(progresso=45, duration=1.2).start(self.ids.barra_loading)
            Animation(build_progress=0.6, duration=1.2).start(self.reator)
            Clock.schedule_once(self.etapa_erro, 1.2)
        self.printar_texto(">[SYSTEM] Conectando ao NerveGear...", p1)
        Animation(build_progress=0.35, duration=0.8).start(self.reator)

    def etapa_erro(self, dt):
        self.printar_texto(
            "\n[color=#ff0044]>[ERRO] FIREWALL ATIVO! BLOQUEIO.[/color]",
            # 0.6s → 0.4s
            lambda: Clock.schedule_once(self._popup_quem_e, 0.4), 0.02)
        self.ids.barra_loading.cor_linha = [1, 0, 0.2, 1]
        self.reator.core_color           = [1, 0, 0.2]
        Animation.cancel_all(self.reator)
        _safe_treme(15)

    def _popup_quem_e(self, dt):
        if not self._typing_ativo:
            return

        pop, layout = _make_popup()
        caixa = BoxLayout(
            orientation='vertical',
            padding=[dp(24), dp(20), dp(24), dp(20)],
            spacing=dp(10),
            size_hint=(0.90, None), height=dp(320))
        aplicar_fundo_holografico(caixa, (1.0, 0.08, 0.22, 0.9))

        lbl_titulo = Label(
            text="[b][color=#ff2244]⚠  ACESSO BLOQUEADO  ⚠[/color][/b]",
            markup=True, font_name="orbitron.ttf", font_size="13sp",
            size_hint_y=None, height=dp(28), halign="center", valign="middle")
        lbl_titulo.text_size = (Window.width * 0.82, None)

        lbl_scan = Label(
            text="[color=#ff8855]INICIANDO VERIFICAÇÃO BIOMÉTRICA...[/color]",
            markup=True, font_name="orbitron.ttf", font_size="10sp",
            size_hint_y=None, height=dp(20), halign="center", valign="middle")
        lbl_scan.text_size = (Window.width * 0.82, None)

        barra_scan = Widget(size_hint_y=None, height=dp(6))
        with barra_scan.canvas:
            Color(0.2, 0.2, 0.2, 0.6)
            RoundedRectangle(pos=barra_scan.pos, size=barra_scan.size, radius=[3])
            _scan_color = Color(1, 0.2, 0.2, 1)
            _scan_rect  = RoundedRectangle(pos=barra_scan.pos, size=(0, barra_scan.height), radius=[3])
        barra_scan.bind(pos=lambda i, v: setattr(_scan_rect, 'pos', v))

        lbl_nome = Label(
            text="[color=#ff4444]> ______[/color]",
            markup=True, font_name="orbitron.ttf", font_size="28sp",
            size_hint_y=None, height=dp(56), halign="center", valign="middle")
        lbl_nome.text_size = (Window.width * 0.82, None)

        lbl_status = Label(
            text="", markup=True, font_name="rajdhani.ttf", font_size="17sp",
            size_hint_y=None, height=dp(32), halign="center", valign="middle")
        lbl_status.text_size = (Window.width * 0.82, None)

        sep = Widget(size_hint_y=None, height=dp(1))
        with sep.canvas:
            Color(1, 0.2, 0.2, 0.4)
            sep._r = Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(pos=lambda i, v: setattr(i._r, 'pos', v),
                 size=lambda i, v: setattr(i._r, 'size', v))

        lbl_welcome = Label(
            text="", markup=True, font_name="orbitron.ttf", font_size="12sp",
            size_hint_y=None, height=dp(28), halign="center", valign="middle", opacity=0)
        lbl_welcome.text_size = (Window.width * 0.82, None)

        for w in [lbl_titulo, lbl_scan, barra_scan, lbl_nome, sep, lbl_status, lbl_welcome]:
            caixa.add_widget(w)

        layout.add_widget(caixa)
        caixa.pos_hint  = {'center_x': 0.5, 'center_y': 0.5}
        caixa.opacity   = 0
        caixa.size_hint = (0.01, None)
        (Animation(opacity=1, duration=0.25, transition='out_quad') &
         Animation(size_hint_x=0.90, duration=0.30, transition='out_back')).start(caixa)
        pop.open()

        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%!?"
        alvo  = "KIRITO"
        etapa = [0]

        def _animar_barra(prog):
            _scan_rect.size = (barra_scan.width * prog, barra_scan.height)

        def _scramble(dt):
            if not self._typing_ativo:
                pop.dismiss(); return
            _animar_barra(etapa[0] / 10.0)
            if etapa[0] < 10:
                s = "".join(random.choice(chars) for _ in range(len(alvo)))
                lbl_nome.text = f"[color=#ffaa00]> {s}[/color]"
                etapa[0] += 1
                Clock.schedule_once(_scramble, 0.07)
            else:
                _animar_barra(1.0)
                lbl_nome.text = "[color=#00ff88][b]> KIRITO[/b][/color]"
                lbl_scan.text = "[color=#00ff88]▸ IDENTIDADE CONFIRMADA[/color]"
                _scan_color.rgb = (0, 1, 0.55)
                Clock.schedule_once(_aprovado, 0.4)  # 0.6s → 0.4s

        def _aprovado(dt):
            if not self._typing_ativo:
                pop.dismiss(); return
            aplicar_fundo_holografico(caixa, (0, 1, 0.55, 0.9))
            lbl_titulo.text = "[b][color=#00ff88]◈  ACESSO CONCEDIDO  ◈[/color][/b]"
            lbl_status.text = "[color=#00e5ff]▸ SISTEMA DESBLOQUEADO[/color]"
            sep.canvas.before.clear()
            with sep.canvas.before:
                Color(0, 1, 0.55, 0.5)
                sep._r = Rectangle(pos=sep.pos, size=sep.size)
            lbl_welcome.text = "[color=#ffffff][b]BEM-VINDO, SENHOR.[/b][/color]"
            Animation(opacity=1, duration=0.4, transition='out_quad').start(lbl_welcome)
            _safe_treme(10)

            def _fechar(dt):
                anim_out = Animation(opacity=0, duration=0.35, transition='in_quad')
                anim_out.bind(on_complete=lambda *_: (
                    pop.dismiss(),
                    Clock.schedule_once(self.etapa_hack, 0.2)
                ))
                anim_out.start(caixa)

            # 1.8s → 1.1s
            Clock.schedule_once(_fechar, 1.1)

        Clock.schedule_once(_scramble, 0.4)  # 0.5s → 0.4s

    def etapa_hack(self, dt):
        if not self._typing_ativo:
            return
        self.printar_texto(
            "\n>[HACK] Forçando LIMIT BREAK...",
            lambda: Clock.schedule_once(self.etapa_sucesso, 0.7))  # 1.0s → 0.7s
        self.ids.barra_loading.cor_linha = [0.6, 0.1, 0.9, 1]
        self.reator.core_color           = [0.6, 0.1, 0.9]
        Animation(progresso=85, duration=1.2).start(self.ids.barra_loading)
        Animation(build_progress=0.9, duration=1.2).start(self.reator)

    def etapa_sucesso(self, dt):
        self.printar_texto(
            "\n[color=#00ff00]>[OK] Acesso Concedido. Sistema Online.[/color]",
            self.etapa_final, 0.02)
        self.ids.barra_loading.cor_linha = [0, 1, 0, 1]
        self.reator.core_color           = [0, 1, 0]
        Animation(progresso=100, duration=0.3).start(self.ids.barra_loading)

    def etapa_final(self):
        self.ids.barra_loading.progresso = 0
        self.ids.barra_loading.cor_linha = [0, 0.5, 1, 1]
        self.reator.core_color           = [0, 0.89, 1]
        Animation(build_progress=1.0, duration=0.8).start(self.reator)
        a = Animation(progresso=100, duration=0.8)
        a.bind(on_complete=self.ignicao)
        a.start(self.ids.barra_loading)

    def ignicao(self, *_):
        _safe_treme(30)
        self.ids.flash_overlay.opacity = 1
        Animation(opacity=0, duration=0.8).start(self.ids.flash_overlay)  # 1.2s → 0.8s
        self.ids.terminal_box.opacity  = 0
        self.animar_materializacao()

    def animar_materializacao(self):
        t     = self.ids.titulo_label
        v     = self.ids.version_label
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*!"
        alvo  = "TRAVETE FOCUS"

        Animation(opacidade=1, escala=1.0, duration=0.6,
                  transition='out_back').start(self.ids.espada_esq)
        Animation(opacidade=1, escala=1.0, duration=0.6,
                  transition='out_back').start(self.ids.espada_dir)
        t.opacity = 1

        # Partículas de dados flutuando durante o scramble
        self._iniciar_particulas_dados()

        ev = Clock.schedule_interval(
            lambda dt: setattr(t, 'text',
                "".join(random.choice(chars) for _ in range(len(alvo)))),
            0.05)

        def finish(*_):
            ev.cancel()
            t.text    = alvo
            v.opacity = 1
            self._parar_particulas_dados()
            # 3.0s → 1.5s
            Clock.schedule_once(
                lambda _: _safe_mudar_tela("menu"), 1.5)

        Clock.schedule_once(finish, 1.2)  # 1.5s → 1.2s

    # ── Partículas de dados flutuantes ─────────────────────
    def _iniciar_particulas_dados(self):
        """Exibe strings de dados holográficas flutuando durante o scramble."""
        self._part_ev  = None
        self._part_lbls = []
        frases = [
            "01001011 01001001",
            "LINK_START//",
            "AINCRAD.SYS",
            "NRV_GEAR_v6.0",
            "> CARREGANDO...",
            "FLOOR_001",
            "XP::[SYNC]",
        ]

        def _criar_particula(dt):
            if not self._typing_ativo:
                return
            try:
                from kivy.uix.label import Label as KLabel
                frase = random.choice(frases)
                x     = random.uniform(0.05, 0.85) * Window.width
                y_ini = random.uniform(0.15, 0.45) * Window.height
                lbl   = KLabel(
                    text=f"[color=#00e5ff44]{frase}[/color]",
                    markup=True,
                    font_name="orbitron.ttf",
                    font_size="9sp",
                    size_hint=(None, None),
                    size=(200, 20),
                    pos=(x, y_ini),
                    opacity=0)
                Window.add_widget(lbl)
                self._part_lbls.append(lbl)
                (Animation(opacity=1, y=y_ini + 30, duration=0.4, transition='out_quad') +
                 Animation(duration=0.5) +
                 Animation(opacity=0, y=y_ini + 70, duration=0.4, transition='in_quad')
                 ).bind(on_complete=lambda *_: self._remover_particula(lbl)).start(lbl)
            except Exception:
                pass

        self._part_ev = Clock.schedule_interval(_criar_particula, 0.25)

    def _remover_particula(self, lbl):
        try:
            Window.remove_widget(lbl)
            if lbl in self._part_lbls:
                self._part_lbls.remove(lbl)
        except Exception:
            pass

    def _parar_particulas_dados(self):
        if hasattr(self, '_part_ev') and self._part_ev:
            self._part_ev.cancel()
            self._part_ev = None
        for lbl in list(getattr(self, '_part_lbls', [])):
            try:
                Window.remove_widget(lbl)
            except Exception:
                pass
        self._part_lbls = []
