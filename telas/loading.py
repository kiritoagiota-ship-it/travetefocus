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
import tatil
from infinito import InfinitoLoader  # noqa: F401  (usado no kv: id reator_shader)
from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, _bind_teclado
import som
import seguranca

# ══════════════════════════════════════════════════════════════
#  CONFIGURACAO — altere aqui sem mexer em mais nada
# ══════════════════════════════════════════════════════════════
SESSION_HORAS  = 4
SESSION_SEG    = SESSION_HORAS * 3600
ARQUIVO_SESSAO = ".tf_session"
# a senha fica em seguranca.py (so a impressao digital; troca pelo menu)"
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
        self._cena           = None
        self._kpin           = None
        self._fim_titulo     = None     # fecha a abertura (usado ao pular)
        self._pular_ok       = False
        self._dica_pular     = None

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
        self._pular_ok = False
        self._fim_titulo = None
        self._tirar_dica_pular()
        if self._cena is not None:
            from cenas import limpar_cena
            limpar_cena(self._cena)
            self._cena = None
        if self._kpin is not None:
            self._kpin.remover()
            self._kpin = None
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
        Animation(build_progress=1.0, duration=0.6, transition='out_expo').start(self.reator)
        Animation(progresso=100, duration=0.6).start(self.ids.barra_loading)

        # senha ainda valendo: entrada rapida (a animacao inteira so depois do PIN)
        Clock.schedule_once(lambda dt: self.animar_materializacao(rapida=True), 0.45)

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
        pop.auto_dismiss = False          # nem o botao voltar fecha a senha
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
            text="[color=#ff8855]VERIFICAÇÃO DE IDENTIDADE NECESSÁRIA[/color]",
            markup=True, font_name="orbitron.ttf", font_size="9sp",
            size_hint_y=None, height=dp(20), halign="center", valign="middle")
        lbl_sub.text_size = (Window.width * 0.80, None)

        lbl_inst = Label(
            text="[color=#888888]Insira o código de acesso:[/color]",
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
        contagem = [None]
        # Kirito espiando por cima da caixa, num dos cantos, esperando o PIN
        try:
            from cenas import KiritoPin
            kpin = KiritoPin(caixa)
        except Exception as e:
            print(f"[loading] kirito do pin: {e}")
            kpin = None
        self._kpin = kpin

        def _k(metodo):
            try:
                if kpin is not None:
                    getattr(kpin, metodo)()
            except Exception as e:
                print(f"[loading] kirito {metodo}: {e}")

        def _bloquear(seg):
            """3 erros: fica bloqueado (contagem regressiva) - nunca abre o app."""
            btn.disabled = True
            inp_pin.text = ""
            inp_pin.disabled = True
            if contagem[0] is not None:
                contagem[0].cancel()

            def _tique(dt=0):
                falta = seguranca.bloqueio_restante()
                if falta <= 0:
                    contagem[0].cancel()
                    contagem[0] = None
                    btn.disabled = False
                    inp_pin.disabled = False
                    lbl_status.text = "[color=#ffaa55]Pode tentar de novo.[/color]"
                    _k('voltar')
                    return False
                lbl_status.text = (f"[color=#ff2222]BLOQUEADO POR ERROS — tente de novo em "
                                   f"{seguranca.tempo_legivel(falta)}[/color]")
                return True
            _tique()
            contagem[0] = Clock.schedule_interval(_tique, 1.0)
            pop.bind(on_dismiss=lambda *_: contagem[0] is not None and contagem[0].cancel() and None)

        def _verificar(*_):
            pin = inp_pin.text.strip()
            if seguranca.bloqueio_restante() > 0:
                return
            if seguranca.pin_confere(pin):
                seguranca.registrar_acerto()
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
                tatil.confirmar()
                self._salvar_sessao()
                # acesso liberado: o Kirito sobe na caixa, sorri e some num
                # teleporte (ele volta pendurado na cena do titulo)
                Clock.schedule_once(lambda dt: _k('sumir'), 0.35)

                def _fechar(dt2):
                    def _apos_fade(*_):
                        pop.dismiss()
                        Clock.schedule_once(self.etapa_hack, 0.2)
                    anim = Animation(opacity=0, duration=0.3, transition='in_expo')
                    anim.bind(on_complete=_apos_fade)
                    anim.start(caixa)

                Clock.schedule_once(_fechar, 1.1)
            else:
                sobram, espera = seguranca.registrar_erro()
                inp_pin.text = ""
                try: som.tocar_pin_erro()
                except Exception: pass
                tatil.erro()
                _k('susto')
                _safe_treme(12)
                if sobram > 0:
                    lbl_status.text = (
                        f"[color=#ff4444]CÓDIGO INVÁLIDO — "
                        f"{sobram} {'tentativa restante' if sobram == 1 else 'tentativas restantes'}.[/color]")
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
                    Clock.schedule_once(lambda dt: _k('bloqueado'), 0.35)
                    _bloquear(espera)

        btn.bind(on_release=_verificar)
        inp_pin.bind(on_text_validate=_verificar)
        # Som de tecla ao digitar o PIN
        def _pin_tecla(inst, val):
            if not val or val == "****":        # limpeza/mascara nao sao teclas
                return
            try: som.tocar_pin_tecla()
            except Exception: pass
            _k('reagir_tecla')
        inp_pin.bind(text=_pin_tecla)
        pop.bind(on_dismiss=lambda *_: inp_pin.unbind(text=_pin_tecla))
        def _ao_fechar(*_):
            # IMPORTANTE: nao devolver nada. Se um handler de on_dismiss devolve
            # algo "verdadeiro" (ex: o evento do Clock), o Kivy CANCELA o fechar
            # e o popup fica aberto e invisivel por cima do app.
            Clock.schedule_once(lambda dt: _k('remover'), 0.6)
        pop.bind(on_dismiss=_ao_fechar)
        _abrir_popup(caixa, pop)
        # depois da caixa abrir e subir com o teclado (ele acompanha a caixa)
        Clock.schedule_once(lambda dt: _k('aparecer'), 0.8)
        # ainda bloqueado de antes (fechar o app nao zera o bloqueio)
        if seguranca.bloqueio_restante() > 0:
            Clock.schedule_once(lambda dt: (_k('bloqueado'), None)[1], 1.6)
            _bloquear(seguranca.bloqueio_restante())
        _bind_teclado(caixa, pop)
        from helpers import anexar_teclado
        # teclado numerico com fechar via _verificar (OK no teclado = verificar PIN)
        Clock.schedule_once(lambda dt: anexar_teclado(inp_pin, 'numeros'), 0.4)

    # ── Sequencia pos-PIN ──────────────────────────────────────────────────

    def etapa_hack(self, dt):
        if not self._typing_ativo:
            return
        self.printar_texto(
            "\n>[HACK] Forçando LIMIT BREAK...",
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

    def animar_materializacao(self, rapida=False):
        """O Yoru escreve TRAVETE FOCUS com as espadas: a abertura inteira
        (cenas.cena_titulo) logo depois da senha; com a senha ainda valendo,
        a entrada rapida (cenas.cena_entrada_rapida). Depois: espadas
        holograficas, versao e menu. Se a cena falhar, o titulo aparece
        direto."""
        if not self._typing_ativo:
            return
        t = self.ids.titulo_label
        v = self.ids.version_label
        t.text = ""
        t.opacity = 1
        self._iniciar_particulas_dados()
        feito = [False]

        def _fim():
            if feito[0] or not self._typing_ativo:
                return
            feito[0] = True
            self._pular_ok = False
            self._fim_titulo = None
            self._tirar_dica_pular()
            try:
                Animation(opacidade=1, escala=1.0, duration=0.6,
                          transition='out_back').start(self.ids.espada_esq)
                Animation(opacidade=1, escala=1.0, duration=0.6,
                          transition='out_back').start(self.ids.espada_dir)
                Animation(opacity=1, duration=0.4, transition='out_expo').start(v)
            except Exception as e:
                print(f"[loading] final do titulo: {e}")
            self._parar_particulas_dados()
            Clock.schedule_once(lambda _: _safe_mudar_tela("menu"), 1.4)

        try:
            if rapida:
                from cenas import cena_entrada_rapida
                self._cena = cena_entrada_rapida(self, t, on_fim=_fim, texto="TRAVETE FOCUS")
            else:
                from cenas import cena_titulo
                self._cena = cena_titulo(self, t, on_fim=_fim, texto="TRAVETE FOCUS")
        except Exception as e:
            print(f"[loading] cena do titulo ignorada: {e}")
            t.text = "TRAVETE FOCUS"
            _fim()
            return
        if not feito[0]:
            # um toque na tela pula a abertura (liberado um instante depois,
            # para o toque do VERIFICAR nao pular sem querer)
            self._fim_titulo = _fim
            Clock.schedule_once(self._liberar_pulo, 0.8)

    # ── Pular a abertura ───────────────────────────────────────────────────

    def _liberar_pulo(self, dt=0):
        if self._cena is None or self._fim_titulo is None or not self._typing_ativo:
            return
        self._pular_ok = True
        try:
            dica = Label(
                text="toque para pular", font_name="rajdhani.ttf", font_size="14sp",
                color=(0.55, 0.85, 1, 1), size_hint=(None, None), size=(dp(220), dp(26)),
                halign="center", valign="middle", opacity=0)
            dica.text_size = dica.size
            dica.pos = ((self.width - dica.width) / 2.0, dp(22))
            self.add_widget(dica)
            self._dica_pular = dica
            pisca = (Animation(opacity=0.7, duration=0.7, transition='in_out_sine') +
                     Animation(opacity=0.3, duration=0.9, transition='in_out_sine'))
            pisca.repeat = True
            pisca.start(dica)
        except Exception as e:
            print(f"[loading] dica pular: {e}")

    def _tirar_dica_pular(self):
        dica, self._dica_pular = self._dica_pular, None
        if dica is None:
            return
        try:
            Animation.cancel_all(dica)
            if dica.parent is not None:
                dica.parent.remove_widget(dica)
        except Exception:
            pass

    def on_touch_down(self, touch):
        if self._pular_ok and self._cena is not None and self._fim_titulo is not None:
            self._pular_abertura()
            return True
        return super().on_touch_down(touch)

    def _pular_abertura(self):
        """Corta a cena na hora: o titulo aparece pronto e segue para o menu."""
        self._pular_ok = False
        fim, self._fim_titulo = self._fim_titulo, None
        try:
            from cenas import limpar_cena
            limpar_cena(self._cena)
        except Exception as e:
            print(f"[loading] pular: {e}")
        self._cena = None
        try:
            t = self.ids.titulo_label
            t.text = "TRAVETE FOCUS"
            t.opacity = 0
            Animation(opacity=1, duration=0.25, transition='out_quad').start(t)
        except Exception:
            pass
        tatil.botao()
        if fim is not None:
            fim()

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
                # parte de baixo da tela, por baixo da luta (o foco e o Kirito)
                x     = random.uniform(0.05, 0.75) * self.width
                y_ini = random.uniform(0.08, 0.34) * self.height
                lbl   = Label(
                    text=f"[color=#00e5ff26]{frase}[/color]",
                    markup=True, font_name="orbitron.ttf", font_size="9sp",
                    size_hint=(None, None), size=(200, 20),
                    pos=(x, y_ini), opacity=0)
                self.add_widget(lbl, index=max(0, len(self.children) - 1))
                self._part_lbls.append(lbl)
                anim = (Animation(opacity=1, y=y_ini + 30, duration=0.4, transition='out_quad') +
                        Animation(duration=0.5) +
                        Animation(opacity=0, y=y_ini + 70, duration=0.4, transition='in_quad'))
                anim.bind(on_complete=lambda *_: self._remover_particula(lbl))
                anim.start(lbl)
            except Exception:
                pass

        self._part_ev = Clock.schedule_interval(_criar, 0.45)

    def _remover_particula(self, lbl):
        try:
            if lbl.parent is not None:
                lbl.parent.remove_widget(lbl)
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
                if lbl.parent is not None:
                    lbl.parent.remove_widget(lbl)
            except Exception:
                pass
        self._part_lbls = []
