"""telas/loading.py — TelaLoading com PIN, sessao inteligente e espadas pixel art"""
import time
import os
import random

from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.animation import Animation
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp

from efeitos import tremer_tela, InputHolografico, BotaoAngular
from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, _bind_teclado
from lembrete import verificar_e_notificar

# ══════════════════════════════════════════════════════════════
#  CONFIGURACAO — altere aqui sem mexer em mais nada
# ══════════════════════════════════════════════════════════════
SESSION_HORAS  = 4
SESSION_SEG    = SESSION_HORAS * 3600
PIN_CORRETO    = "2004"
ARQUIVO_SESSAO = ".tf_session"
# ══════════════════════════════════════════════════════════════


def _safe_treme(intensidade):
    try:
        tremer_tela(intensidade)
    except Exception as e:
        print(f"[loading] tremer ignorado: {e}")


def _safe_mudar_tela(destino):
    try:
        app = App.get_running_app()
        if app:
            app.mudar_tela(destino)
    except Exception as e:
        print(f"[loading] mudar_tela ignorado: {e}")


class TelaLoading(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._typing_ativo   = False
        self._espadas_widget = None

    # ── Sessao ─────────────────────────────────────────────────────────────

    def _session_path(self):
        try:
            return os.path.join(App.get_running_app().user_data_dir, ARQUIVO_SESSAO)
        except Exception:
            return ARQUIVO_SESSAO

    def _sessao_valida(self):
        try:
            path = self._session_path()
            if not os.path.exists(path):
                return False
            with open(path) as f:
                last = float(f.read().strip())
            elapsed = time.time() - last
            print(f"[SESSAO] {elapsed/3600:.2f}h desde ultima auth (limite: {SESSION_HORAS}h)")
            return elapsed < SESSION_SEG
        except Exception:
            return False

    def _salvar_sessao(self):
        try:
            with open(self._session_path(), 'w') as f:
                f.write(str(time.time()))
            print("[SESSAO] Sessao salva.")
        except Exception as e:
            print(f"[SESSAO] Nao salva: {e}")

    # ── Entrada ────────────────────────────────────────────────────────────

    def on_enter(self):
        Clock.schedule_once(self.preparar, 0.1)

    def on_leave(self, *_):
        self._typing_ativo = False
        self._parar_particulas_dados()

    def preparar(self, dt):
        self._typing_ativo = True
        try:
            self.ids.terminal_box.opacity    = 0
            self.ids.titulo_label.opacity    = 0
            self.ids.espada_esq.opacidade    = 0
            self.ids.espada_esq.escala       = 0
            self.ids.espada_dir.opacidade    = 0
            self.ids.espada_dir.escala       = 0
            self.reator                      = self.ids.reator_shader
            self.reator.build_progress       = 0.0
            self.reator.core_color           = [0, 0.89, 1]
            self.ids.barra_loading.progresso = 0
            self.ids.console_text.text       = ""
            self._add_pixel_swords()

            if self._sessao_valida():
                Clock.schedule_once(self._quick_load, 0.15)
            else:
                Clock.schedule_once(self.start_anim, 0.1)
        except Exception as e:
            print(f"[LOADING] ids nao prontos: {e}")
            Clock.schedule_once(lambda _: _safe_mudar_tela("menu"), 0.5)

    # ── Pixel Art Espadas ──────────────────────────────────────────────────

    def _add_pixel_swords(self):
        """
        Cria widget das espadas e agenda o draw para APOS o layout.
        O centro so fica disponivel depois que o widget e adicionado
        e o Kivy faz o primeiro calculo de layout (~1 frame).
        """
        if self._espadas_widget:
            try:
                self.remove_widget(self._espadas_widget)
            except Exception:
                pass

        w = Widget(size_hint=(None, None), size=(dp(100), dp(100)))
        self.add_widget(w)
        self._espadas_widget = w

        def _posicionar_e_desenhar(*_):
            try:
                reator = self.ids.reator_shader
                w.center = reator.center
                self._redesenhar_espadas(w)
            except Exception as e:
                print(f"[espadas] posicao nao disponivel: {e}")

        # Bind para acompanhar mudancas de posicao/tamanho
        try:
            self.ids.reator_shader.bind(center=_posicionar_e_desenhar)
            self.bind(size=_posicionar_e_desenhar)
        except Exception:
            pass

        # Aguarda layout + fade-in suave das espadas
        Clock.schedule_once(lambda dt: _posicionar_e_desenhar(), 0.05)
        def _fade_in_espadas(dt):
            _posicionar_e_desenhar()
            if self._espadas_widget:
                self._espadas_widget.opacity = 0
                Animation(opacity=1, duration=0.6,
                          transition='out_quad').start(self._espadas_widget)
        Clock.schedule_once(_fade_in_espadas, 0.30)

    def _redesenhar_espadas(self, widget):
        """Limpa e redesenha as espadas usando posicao real do widget."""
        if not widget.parent or widget.width <= 0:
            return

        BLADE  = (0.85, 0.92, 0.97, 0.95)
        GUARD  = (1.00, 0.80, 0.15, 1.00)
        HANDLE = (0.52, 0.30, 0.10, 0.90)
        POMMEL = (0.00, 0.88, 1.00, 1.00)
        GEM    = (0.00, 1.00, 0.88, 1.00)

        pixels = [
            (-6, 6, BLADE), (-5, 5, BLADE), (-4, 4, BLADE),
            (-3, 3, BLADE), (-2, 2, BLADE), (-1, 1, BLADE),
            ( 6, 6, BLADE), ( 5, 5, BLADE), ( 4, 4, BLADE),
            ( 3, 3, BLADE), ( 2, 2, BLADE), ( 1, 1, BLADE),
            (-2, 0, GUARD), (-1, 1, GUARD), (0, 2, GUARD),
            ( 2, 0, GUARD), ( 1, 1, GUARD),
            (0, 0, GEM),
            ( 1, -1, BLADE), ( 2, -2, BLADE), ( 3, -3, BLADE),
            (-1, -1, BLADE), (-2, -2, BLADE), (-3, -3, BLADE),
            ( 4, -4, HANDLE), ( 5, -5, HANDLE),
            (-4, -4, HANDLE), (-5, -5, HANDLE),
            ( 6, -6, POMMEL),
            (-6, -6, POMMEL),
        ]

        # canvas.clear() limpa instrucoes anteriores — evita acumulo
        widget.canvas.clear()
        ps = max(2, int(widget.width / 28))
        cx = widget.center_x   # correto apos o layout
        cy = widget.center_y

        with widget.canvas:
            for dx, dy, cor in pixels:
                Color(*cor)
                Rectangle(
                    pos=(cx + dx * ps - ps / 2, cy + dy * ps - ps / 2),
                    size=(ps, ps))

    # ── Quick Load ─────────────────────────────────────────────────────────

    def _quick_load(self, dt):
        if not self._typing_ativo:
            return
        self.ids.barra_loading.opacity = 0
        self.reator.core_color = [0, 0.89, 1]
        Animation(opacity=1, duration=0.3).start(self.ids.barra_loading)
        Animation(build_progress=1.0, duration=1.0).start(self.reator)
        Animation(progresso=100, duration=1.0).start(self.ids.barra_loading)

        t     = self.ids.titulo_label
        t.opacity = 1
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*!"
        alvo  = "TRAVETE FOCUS"
        ev = Clock.schedule_interval(
            lambda dt: setattr(t, 'text',
                ''.join(random.choice(chars) for _ in range(len(alvo)))),
            0.04)

        def _finish(dt2):
            ev.cancel()
            t.text = alvo
            Animation(opacity=1, duration=0.4).start(self.ids.version_label)
            # Verificar lembrete diário após carregar dados
            try:
                Clock.schedule_once(
                    lambda _: verificar_e_notificar(App.get_running_app()), 2.0)
            except Exception:
                pass
            Clock.schedule_once(lambda _: _safe_mudar_tela("menu"), 0.5)

        Clock.schedule_once(_finish, 0.8)

    # ── Full Load — texto ──────────────────────────────────────────────────

    def printar_texto(self, texto, callback, vel=0.025):
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
        Animation(opacity=1, duration=0.5).start(self.ids.terminal_box)
        self.ids.barra_loading.opacity = 1
        self.start_text()

    def start_text(self):
        def p1():
            Animation(progresso=45, duration=1.2).start(self.ids.barra_loading)
            Animation(build_progress=0.6, duration=1.2).start(self.reator)
            Clock.schedule_once(self.etapa_erro, 1.2)
        self.printar_texto(">[SYSTEM] Conectando ao NerveGear...", p1)
        Animation(build_progress=0.35, duration=0.8).start(self.reator)

    def etapa_erro(self, dt):
        self.printar_texto(
            "\n[color=#ff0044]>[ERRO] FIREWALL ATIVO! BLOQUEIO.[/color]",
            lambda: Clock.schedule_once(self._popup_pin, 0.4), 0.02)
        self.ids.barra_loading.cor_linha = [1, 0, 0.2, 1]
        self.reator.core_color           = [1, 0, 0.2]
        Animation.cancel_all(self.reator)
        _safe_treme(15)

    # ── Popup PIN ──────────────────────────────────────────────────────────

    def _popup_pin(self, dt):
        if not self._typing_ativo:
            return

        pop, layout = _make_popup()
        caixa = BoxLayout(
            orientation='vertical',
            padding=[dp(24), dp(20), dp(24), dp(20)],
            spacing=dp(10),
            size_hint=(0.88, None), height=dp(300))
        aplicar_fundo_holografico(caixa, (1.0, 0.08, 0.22, 0.9))

        lbl_titulo = Label(
            text="[b][color=#ff2244]!!  ACESSO BLOQUEADO  !![/color][/b]",
            markup=True, font_name="orbitron.ttf", font_size="13sp",
            size_hint_y=None, height=dp(28), halign="center", valign="middle")
        lbl_titulo.text_size = (Window.width * 0.80, None)

        lbl_sub = Label(
            text="[color=#ff8855]VERIFICACAO DE IDENTIDADE NECESSARIA[/color]",
            markup=True, font_name="orbitron.ttf", font_size="9sp",
            size_hint_y=None, height=dp(20), halign="center", valign="middle")
        lbl_sub.text_size = (Window.width * 0.80, None)

        lbl_inst = Label(
            text="[color=#888888]Insira o codigo de acesso:[/color]",
            markup=True, font_name="orbitron.ttf", font_size="10sp",
            size_hint_y=None, height=dp(22), halign="center", valign="middle")
        lbl_inst.text_size = (Window.width * 0.80, None)

        # Botao ANTES do input — teclado nao cobre o botao
        btn = BotaoAngular(
            text=">>  VERIFICAR  <<",
            size_hint_y=None, height=dp(50))

        inp_pin = InputHolografico(
            password=True,
            input_filter='int',
            font_name="orbitron.ttf", font_size="32sp",
            background_color=(0, 0, 0, 0),
            foreground_color=(1, 0.3, 0.3, 1),
            cursor_color=(1, 0.3, 0.3, 1),
            halign="center",
            size_hint_y=None, height=dp(68))

        lbl_status = Label(
            text="",
            markup=True, font_name="rajdhani.ttf", font_size="14sp",
            size_hint_y=None, height=dp(24), halign="center", valign="middle")
        lbl_status.text_size = (Window.width * 0.80, None)

        for w in [lbl_titulo, lbl_sub, lbl_inst, btn, inp_pin, lbl_status]:
            caixa.add_widget(w)

        layout.add_widget(caixa)
        caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        tentativas = [3]

        def _verificar(*_):
            pin = inp_pin.text.strip()
            if pin == PIN_CORRETO:
                lbl_titulo.text = "[b][color=#00ff88]>>  ACESSO CONCEDIDO  <<[/color][/b]"
                lbl_sub.text    = "[color=#00ff88]IDENTIDADE CONFIRMADA — BEM-VINDO, KIRITO[/color]"
                aplicar_fundo_holografico(caixa, (0, 1, 0.55, 0.9))
                inp_pin.foreground_color = [0, 1, 0.55, 1]
                inp_pin.text = "****"
                btn.disabled = True
                _safe_treme(10)
                self._salvar_sessao()

                def _fechar(dt2):
                    def _apos_fade(*_):
                        pop.dismiss()
                        Clock.schedule_once(self.etapa_hack, 0.2)
                    anim = Animation(opacity=0, duration=0.3)
                    anim.bind(on_complete=_apos_fade)
                    anim.start(caixa)

                Clock.schedule_once(_fechar, 1.1)
            else:
                tentativas[0] -= 1
                inp_pin.text = ""
                _safe_treme(12)
                if tentativas[0] > 0:
                    lbl_status.text = (
                        f"[color=#ff4444]CODIGO INVALIDO — "
                        f"{tentativas[0]} tentativa(s) restante(s).[/color]")
                    Animation.cancel_all(inp_pin, 'borda_color')
                    (Animation(borda_color=[1, 0.1, 0.2, 1],      duration=0.07) +
                     Animation(borda_color=[1, 0.1, 0.2, 0.4],    duration=0.07) +
                     Animation(borda_color=[1, 0.1, 0.2, 1],      duration=0.07) +
                     Animation(borda_color=[0.8, 0.05, 0.1, 0.9], duration=0.30)
                     ).start(inp_pin)
                    # Cooldown: desabilita btn por 0.6s após erro
                    btn.disabled = True
                    Clock.schedule_once(lambda _: setattr(btn, 'disabled', False), 0.6)
                else:
                    lbl_status.text  = "[color=#ff2222]ACESSO NEGADO. BLOQUEIO ATIVADO.[/color]"
                    btn.disabled     = True
                    inp_pin.disabled = True
                    def _bloqueado(_dt):
                        pop.dismiss()
                        _safe_mudar_tela("menu")
                    Clock.schedule_once(_bloqueado, 2.5)

        btn.bind(on_release=_verificar)
        inp_pin.bind(on_text_validate=_verificar)
        _abrir_popup(caixa, pop)
        _bind_teclado(caixa, pop)
        from helpers import anexar_teclado
        # teclado numerico com fechar via _verificar (OK no teclado = verificar PIN)
        Clock.schedule_once(lambda dt: anexar_teclado(inp_pin, 'numeros'), 0.4)

    # ── Sequencia pos-PIN ──────────────────────────────────────────────────

    def etapa_hack(self, dt):
        if not self._typing_ativo:
            return
        self.printar_texto(
            "\n>[HACK] Forcando LIMIT BREAK...",
            lambda: Clock.schedule_once(self.etapa_sucesso, 0.7))
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
        Animation(opacity=0, duration=0.8).start(self.ids.flash_overlay)
        self.ids.terminal_box.opacity  = 0
        # Verificar lembrete ao entrar via loading completo
        try:
            Clock.schedule_once(
                lambda _: verificar_e_notificar(App.get_running_app()), 3.0)
        except Exception:
            pass
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
            Clock.schedule_once(lambda _: _safe_mudar_tela("menu"), 1.5)

        Clock.schedule_once(finish, 1.2)

    # ── Particulas ─────────────────────────────────────────────────────────

    def _iniciar_particulas_dados(self):
        self._part_ev   = None
        self._part_lbls = []
        frases = [
            "01001011 01001001", "LINK_START//",
            "AINCRAD.SYS",       "NRV_GEAR_v6.0",
            "> CARREGANDO...",   "FLOOR_001",    "XP::[SYNC]",
        ]

        def _criar(dt):
            if not self._typing_ativo:
                return
            try:
                frase = random.choice(frases)
                x     = random.uniform(0.05, 0.85) * Window.width
                y_ini = random.uniform(0.15, 0.45) * Window.height
                lbl   = Label(
                    text=f"[color=#00e5ff44]{frase}[/color]",
                    markup=True, font_name="orbitron.ttf", font_size="9sp",
                    size_hint=(None, None), size=(200, 20),
                    pos=(x, y_ini), opacity=0)
                Window.add_widget(lbl)
                self._part_lbls.append(lbl)
                (Animation(opacity=1, y=y_ini + 30, duration=0.4, transition='out_quad') +
                 Animation(duration=0.5) +
                 Animation(opacity=0, y=y_ini + 70, duration=0.4, transition='in_quad')
                 ).bind(on_complete=lambda *_: self._remover_particula(lbl)).start(lbl)
            except Exception:
                pass

        self._part_ev = Clock.schedule_interval(_criar, 0.25)

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
