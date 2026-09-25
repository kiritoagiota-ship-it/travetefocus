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
from kivy.graphics import Color, Rectangle, InstructionGroup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp

from efeitos import tremer_tela, InputHolografico, BotaoAngular
from infinito import InfinitoLoader  # noqa: F401  (usado no kv: id reator_shader)
from espadachim import EspadachimPixel
from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, _bind_teclado
import som

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
        self._espadachim     = None

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
        self._remover_espadachim()
        # Limpar espadas ao sair — evita widget órfão na memória
        try:
            if self._espadas_widget and self._espadas_widget.parent:
                self.remove_widget(self._espadas_widget)
            self._espadas_widget = None
        except Exception:
            pass

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

            if self._sessao_valida():
                Clock.schedule_once(self._quick_load, 0.15)
            else:
                Clock.schedule_once(self.start_anim, 0.1)
        except Exception as e:
            print(f"[LOADING] ids nao prontos: {e}")
            Clock.schedule_once(lambda _: _safe_mudar_tela("menu"), 0.5)

    # ── Quick Load ─────────────────────────────────────────────────────────

    def _quick_load(self, dt):
        if not self._typing_ativo:
            return
        self.ids.barra_loading.opacity = 0
        self.reator.core_color = [0, 0.89, 1]
        Animation(opacity=1, duration=0.3, transition='out_expo').start(self.ids.barra_loading)
        Animation(build_progress=1.0, duration=1.0, transition='out_expo').start(self.reator)
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
            Animation(opacity=1, duration=0.4, transition='out_expo').start(self.ids.version_label)
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
        Animation(opacity=1, duration=0.5, transition='out_expo').start(self.ids.terminal_box)
        self.ids.barra_loading.opacity = 1
        self.start_text()

    def start_text(self):
        try: som.tocar_loading_drone()
        except Exception: pass
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
        try: som.tocar_erro_firewall()
        except Exception: pass
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
                # firewall vencido: o infinito sai do vermelho e volta a ciclar
                try:
                    self.reator.core_color = [0, 0.89, 1]
                    self.ids.barra_loading.cor_linha = [0, 0.9, 1, 1]
                except Exception:
                    pass
                _safe_treme(10)
                try: som.tocar_retomada()
                except Exception: pass
                self._salvar_sessao()

                def _fechar(dt2):
                    def _apos_fade(*_):
                        pop.dismiss()
                        # espadachim golpeia e so entao o "hack" continua
                        self._golpe_espadachim(
                            lambda: Clock.schedule_once(self.etapa_hack, 0.15))
                    anim = Animation(opacity=0, duration=0.3, transition='in_expo')
                    anim.bind(on_complete=_apos_fade)
                    anim.start(caixa)

                Clock.schedule_once(_fechar, 1.1)
            else:
                tentativas[0] -= 1
                inp_pin.text = ""
                try: som.tocar_pin_erro()
                except Exception: pass
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
        # Som de tecla ao digitar o PIN
        def _pin_tecla(inst, val):
            try: som.tocar_pin_tecla()
            except Exception: pass
        inp_pin.bind(text=_pin_tecla)
        pop.bind(on_dismiss=lambda *_: inp_pin.unbind(text=_pin_tecla))
        _abrir_popup(caixa, pop)
        _bind_teclado(caixa, pop)
        from helpers import anexar_teclado
        # teclado numerico com fechar via _verificar (OK no teclado = verificar PIN)
        Clock.schedule_once(lambda dt: anexar_teclado(inp_pin, 'numeros'), 0.4)

    # ── Espadachim (senha aceita) ──────────────────────────────────────────

    def _golpe_espadachim(self, continuar):
        """Espadachim pixel art entra, faz o combo de 2 cortes em meia-lua e
        sai. Qualquer falha aqui apenas segue a sequencia (nunca trava)."""
        seguiu = [False]

        def _seguir(*_):
            if seguiu[0]:
                return
            seguiu[0] = True
            try:
                continuar()
            except Exception as e:
                print(f"[loading] continuar: {e}")

        # rede de seguranca: a historia continua mesmo se algo travar
        Clock.schedule_once(_seguir, 4.0)
        if not self._typing_ativo:
            _seguir()
            return
        try:
            self._remover_espadachim()
            lado = min(Window.width * 0.86, dp(420))
            esp = EspadachimPixel(size_hint=(None, None), size=(lado, lado * 0.62),
                                  pos_hint={'center_x': 0.5, 'center_y': 0.49})
            esp.opacity = 0
            self.add_widget(esp)
            self._espadachim = esp
            esp.iniciar_idle()
            Animation(opacity=1, duration=0.25, transition='out_quad').start(esp)

            def _impacto(n):
                try: som.tocar_corte()
                except Exception: pass
                _safe_treme(10 + 6 * n)
                try:
                    fl = self.ids.flash_overlay
                    Animation.cancel_all(fl, 'opacity')
                    fl.opacity = 0.16
                    Animation(opacity=0, duration=0.22).start(fl)
                except Exception:
                    pass

            def _sair():
                anim = Animation(opacity=0, duration=0.3, transition='in_quad')
                anim.bind(on_complete=lambda *_: (self._remover_espadachim(), _seguir()))
                anim.start(esp)

            Clock.schedule_once(
                lambda dt: esp.atacar(combo=True, on_impacto=_impacto, on_fim=_sair), 0.45)
        except Exception as e:
            print(f"[loading] espadachim ignorado: {e}")
            self._remover_espadachim()
            _seguir()

    def _remover_espadachim(self):
        esp, self._espadachim = self._espadachim, None
        if esp is None:
            return
        try:
            esp.parar()
            if esp.parent:
                esp.parent.remove_widget(esp)
        except Exception as e:
            print(f"[loading] remover espadachim: {e}")

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
        Animation(build_progress=1.0, duration=0.8, transition='out_expo').start(self.reator)
        a = Animation(progresso=100, duration=0.8)
        a.bind(on_complete=self.ignicao)
        a.start(self.ids.barra_loading)

    def ignicao(self, *_):
        _safe_treme(30)
        self.ids.flash_overlay.opacity = 1
        Animation(opacity=0, duration=0.8).start(self.ids.flash_overlay)
        self.ids.terminal_box.opacity  = 0
        # (verificar_e_notificar / lembrete.py nao existe mais no projeto: a
        # chamada agendada aqui dava NameError 3s depois e derrubava o app)
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
        Animation(opacity=1, duration=0.3, transition='out_expo').start(t)
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
                anim = (Animation(opacity=1, y=y_ini + 30, duration=0.4, transition='out_quad') +
                        Animation(duration=0.5) +
                        Animation(opacity=0, y=y_ini + 70, duration=0.4, transition='in_quad'))
                anim.bind(on_complete=lambda *_: self._remover_particula(lbl))
                anim.start(lbl)
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
