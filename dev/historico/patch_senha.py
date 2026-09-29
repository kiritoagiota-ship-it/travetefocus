"""Senha de verdade: 3 erros bloqueiam (com contagem) e nunca abrem o menu."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'telas', 'loading.py'), [
    ("""from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, _bind_teclado
import som
""", """from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, _bind_teclado
import som
import seguranca
"""),
    ("""SESSION_HORAS  = 4
SESSION_SEG    = SESSION_HORAS * 3600
PIN_CORRETO    = "2004"
ARQUIVO_SESSAO = ".tf_session\"""", """SESSION_HORAS  = 4
SESSION_SEG    = SESSION_HORAS * 3600
ARQUIVO_SESSAO = ".tf_session"
# a senha fica em seguranca.py (so a impressao digital; troca pelo menu)\""""),
    ("""        pop, layout = _make_popup()
        caixa = BoxLayout(
            orientation='vertical',
            padding=[dp(24), dp(20), dp(24), dp(20)],
            spacing=dp(10),
            size_hint=(0.88, None), height=dp(300))""", """        pop, layout = _make_popup()
        pop.auto_dismiss = False          # nem o botao voltar fecha a senha
        caixa = BoxLayout(
            orientation='vertical',
            padding=[dp(24), dp(20), dp(24), dp(20)],
            spacing=dp(10),
            size_hint=(0.88, None), height=dp(300))"""),
    ("""        layout.add_widget(caixa)
        caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        tentativas = [3]
""", """        layout.add_widget(caixa)
        caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        contagem = [None]
"""),
    ("""        def _verificar(*_):
            pin = inp_pin.text.strip()
            if pin == PIN_CORRETO:""", """        def _bloquear(seg):
            \"\"\"3 erros: fica bloqueado (contagem regressiva) - nunca abre o app.\"\"\"
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
                seguranca.registrar_acerto()"""),
    ("""            else:
                tentativas[0] -= 1
                inp_pin.text = ""
                try: som.tocar_pin_erro()
                except Exception: pass
                tatil.erro()
                _k('susto')
                _safe_treme(12)
                if tentativas[0] > 0:
                    lbl_status.text = (
                        f"[color=#ff4444]CODIGO INVALIDO — "
                        f"{tentativas[0]} tentativa(s) restante(s).[/color]")""",
     """            else:
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
                        f"{sobram} {'tentativa restante' if sobram == 1 else 'tentativas restantes'}.[/color]")"""),
    ("""                else:
                    lbl_status.text  = "[color=#ff2222]ACESSO NEGADO. BLOQUEIO ATIVADO.[/color]"
                    btn.disabled     = True
                    inp_pin.disabled = True
                    Clock.schedule_once(lambda dt: _k('bloqueado'), 0.35)
                    def _bloqueado(_dt):
                        _k('remover')
                        pop.dismiss()
                        _safe_mudar_tela("menu")
                    Clock.schedule_once(_bloqueado, 2.5)
""", """                else:
                    Clock.schedule_once(lambda dt: _k('bloqueado'), 0.35)
                    _bloquear(espera)
"""),
    ("""        _abrir_popup(caixa, pop)
        # depois da caixa abrir e subir com o teclado (ele acompanha a caixa)
        Clock.schedule_once(lambda dt: _k('aparecer'), 0.8)""", """        _abrir_popup(caixa, pop)
        # depois da caixa abrir e subir com o teclado (ele acompanha a caixa)
        Clock.schedule_once(lambda dt: _k('aparecer'), 0.8)
        # ainda bloqueado de antes (fechar o app nao zera o bloqueio)
        if seguranca.bloqueio_restante() > 0:
            Clock.schedule_once(lambda dt: (_k('bloqueado'), None)[1], 1.6)
            _bloquear(seguranca.bloqueio_restante())"""),
])

# o Yoru da senha volta a espiar quando o bloqueio acaba
patch(os.path.join(A, 'cenas.py'), [
    ("""    def sumir(self):
        \"\"\"Acesso liberado: sobe na caixa, sorri, faz que sim e some num""",
     """    def voltar(self):
        \"\"\"O bloqueio acabou: sobe de novo devagar e volta a espiar.\"\"\"
        try:
            if self.k is None or self._em_cima:
                return
            self._bloq = False
            self._escondido = False
            self.k.mostrar(_com(K.POSE_A['espia_baixo'], olhos='s'))
            self._animar_desc(0.0, 0.6, on_fim=self._esperar)
        except Exception as e:
            print(f"[kirito pin] voltar: {e}")

    def sumir(self):
        \"\"\"Acesso liberado: sobe na caixa, sorri, faz que sim e some num"""),
])
print('ok')
