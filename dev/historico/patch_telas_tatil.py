"""Vibracao certa em cada envio / erro das telas."""
import sys
sys.path.insert(0, __file__.rsplit('\\', 1)[0])
from p import patch

R = r'C:\Users\kirit\travetefocus\app\telas' + '\\'

patch(R + 'registro.py', [
    ("from helpers import popup_pedir_xp, popup_delete_engracado, popup_resumo_dia, animar_ganho_xp, vibrar, anexar_teclado\n",
     "from helpers import (popup_pedir_xp, popup_delete_engracado, popup_resumo_dia, animar_ganho_xp,\n"
     "                     anexar_teclado, sugestoes_pecas)\n"),
    ("import som\nfrom animacoes_ui import entrada_cascata\n",
     "import som\nimport tatil\nfrom animacoes_ui import entrada_cascata\n"),
    ("            anexar_teclado(self.ids.nome_input, 'letras')\n",
     "            anexar_teclado(self.ids.nome_input, 'letras', sugestoes=sugestoes_pecas)\n"),
    ("""        if not (n and q and q.isdigit() and int(q) > 0):
            som.tocar_erro()
            return""", """        if not (n and q and q.isdigit() and int(q) > 0):
            som.tocar_erro()
            tatil.erro()
            return"""),
    ("""        som.tocar_add()
        vibrar(50)""", """        som.tocar_add()
        tatil.confirmar()"""),
    ("""            som.tocar_delete()
            vibrar(80)""", """            som.tocar_delete()
            tatil.forte()"""),
    ("""        if not app.registros:
            som.tocar_erro()
            return""", """        if not app.registros:
            som.tocar_erro()
            tatil.erro()
            return"""),
    ("""            som.tocar_finalizar()
            vibrar(200)""", """            som.tocar_finalizar()
            tatil.vitoria()"""),
])

patch(R + 'ganhos.py', [
    ("from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, vibrar, em, anexar_teclado\n",
     "from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, em, anexar_teclado\n"
     "import tatil\n"),
    ("""                    som.tocar_delete()
                    vibrar(80)""", """                    som.tocar_delete()
                    tatil.forte()"""),
    ("""        if invalidos:
            som.tocar_erro()""", """        if invalidos:
            som.tocar_erro()
            tatil.erro()"""),
    ("""        else:
            som.tocar_salvar()
            tremer_tela(5)""", """        else:
            som.tocar_salvar()
            tatil.confirmar()
            tremer_tela(5)"""),
    ("""        som.tocar_abrir_periodo()
        vibrar(100)""", """        som.tocar_abrir_periodo()
        tatil.confirmar()"""),
    ("""        som.tocar_fechar_periodo()
        vibrar(200)""", """        som.tocar_fechar_periodo()
        tatil.vitoria()"""),
])

patch(R + 'memorias.py', [
    ("from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, vibrar, _bind_teclado\n",
     "from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, vibrar, _bind_teclado\n"
     "import tatil\n"),
    ("""                som.tocar_salvar()
                App.get_running_app().salvar_dados()
                self.atualizar_lista()
                self._atualizar_grafico()
            except ValueError:""", """                som.tocar_salvar()
                tatil.confirmar()
                App.get_running_app().salvar_dados()
                self.atualizar_lista()
                self._atualizar_grafico()
            except ValueError:
                tatil.erro()"""),
    ("""        def _whatsapp(*_):
            vibrar(40)""", """        def _whatsapp(*_):
            tatil.confirmar()"""),
    ("""        exportar_e_compartilhar(app.memorias, app.user_data_dir, _on_erro)
        vibrar(80)""", """        exportar_e_compartilhar(app.memorias, app.user_data_dir, _on_erro)
        tatil.confirmar()"""),
])

patch(R + 'loading.py', [
    ("""                _safe_treme(10)
                try: som.tocar_retomada()
                except Exception: pass""", """                _safe_treme(10)
                try: som.tocar_retomada()
                except Exception: pass
                tatil.confirmar()"""),
    ("""                inp_pin.text = ""
                try: som.tocar_pin_erro()
                except Exception: pass""", """                inp_pin.text = ""
                try: som.tocar_pin_erro()
                except Exception: pass
                tatil.erro()"""),
    ("from efeitos import tremer_tela, InputHolografico, BotaoAngular\n",
     "from efeitos import tremer_tela, InputHolografico, BotaoAngular\nimport tatil\n"),
])
print('ok')
