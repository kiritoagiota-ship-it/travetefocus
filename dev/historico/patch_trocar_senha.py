"""Trocar a senha pelo menu + campo de data do Finalizar o dia (barras sozinhas,
data invalida avisa em vez de virar 'hoje', campo antes do botao)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'helpers.py'), [
    ("""from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.metrics import dp
from datetime import datetime
""", """from kivy.graphics import Color, Rectangle, Line, RoundedRectangle, PushMatrix, PopMatrix, Translate
from kivy.metrics import dp
from datetime import datetime, timedelta
import math
"""),
    ("""def popup_resumo_dia(tot_pecas, tot_xp, on_confirm):""",
     """def tremer_widget(w, forca=None, dur=0.34):
    \"\"\"Balanca so esse widget de um lado para o outro (campo com erro).\"\"\"
    try:
        forca = dp(9) if forca is None else forca
        tr = getattr(w, '_tremor', None)
        if tr is None:
            tr = Translate(0, 0)
            w.canvas.before.insert(0, tr)
            w.canvas.before.insert(0, PushMatrix())
            w.canvas.after.add(PopMatrix())
            w._tremor = tr
        ev = getattr(w, '_tremor_ev', None)
        if ev is not None:
            ev.cancel()
        t = [0.0]

        def _passo(dt):
            t[0] += dt
            if t[0] >= dur:
                tr.x = 0
                w._tremor_ev = None
                return False
            tr.x = forca * math.sin(t[0] * 55.0) * (1.0 - t[0] / dur)
        w._tremor_ev = Clock.schedule_interval(_passo, 0)
    except Exception as e:
        print(f"[tremer_widget] {e}")


def formatar_data_digitada(inp):
    \"\"\"Campo de data com o teclado de numeros: as barras entram sozinhas
    (29092026 -> 29/09/2026) e o apagar tira um numero de cada vez.\"\"\"
    trava = [False]

    def _fmt(inst, valor):
        if trava[0]:
            return
        d = ''.join(ch for ch in valor if ch.isdigit())[:8]
        novo = d[:2] + ('/' + d[2:4] if len(d) > 2 else '') + ('/' + d[4:] if len(d) > 4 else '')
        if novo != valor:
            trava[0] = True
            inst.text = novo
            trava[0] = False
        Clock.schedule_once(lambda dt: setattr(inst, 'cursor', (len(inst.text), 0)), 0)
    inp.bind(text=_fmt)


def ler_data(texto):
    \"\"\"'dd/mm/aaaa' -> (datetime, None) ou (None, motivo em portugues).\"\"\"
    try:
        d = datetime.strptime(texto.strip(), "%d/%m/%Y")
    except ValueError:
        return None, "Data inválida. Use dia/mês/ano (ex.: 29/09/2026)."
    if d.year < 2000:
        return None, "Data muito antiga. Confira o ano."
    if d.date() > (datetime.now() + timedelta(days=1)).date():
        return None, "Essa data ainda não chegou."
    return d, None


def popup_trocar_senha():
    \"\"\"Menu: troca a senha do app. So a 'impressao digital' fica guardada
    (seguranca.py); errar a senha atual conta como erro de senha.\"\"\"
    import seguranca
    import tatil
    pop, layout = _make_popup()
    caixa = BoxLayout(
        orientation='vertical', padding=[dp(24), dp(16), dp(24), dp(16)],
        spacing=dp(6), size_hint=(0.88, None), height=dp(438))
    aplicar_fundo_holografico(caixa, (0.0, 0.9, 1.0, 0.9))

    caixa.add_widget(Label(
        text="[b][color=#00e5ff]TROCAR SENHA[/color][/b]",
        markup=True, font_name="orbitron.ttf", font_size="15sp",
        size_hint_y=None, height=dp(32), halign="center"))
    caixa.add_widget(Label(
        text="[color=#8899aa]A senha nova tem de 4 a 8 números.[/color]",
        markup=True, font_name="rajdhani.ttf", font_size="14sp",
        size_hint_y=None, height=dp(20), halign="center"))

    campos = []
    for rotulo in ("Senha atual", "Senha nova", "Repita a senha nova"):
        caixa.add_widget(Label(
            text=f"[color=#9fb3c8]{rotulo}[/color]",
            markup=True, font_name="orbitron.ttf", font_size="10sp",
            size_hint_y=None, height=dp(20), halign="center"))
        inp = InputHolografico(
            password=True, input_filter='int',
            font_name="orbitron.ttf", font_size="22sp",
            background_color=(0, 0, 0, 0),
            foreground_color=(0, 0.9, 1, 1), cursor_color=(0, 0.9, 1, 1),
            halign="center", size_hint_y=None, height=dp(50))
        # no maximo 8 numeros (o teclado SAO escreve direto no texto)
        inp.bind(text=lambda i, v: setattr(i, 'text', v[:8]) if len(v) > 8 else None)
        anexar_teclado(inp, 'numeros')
        caixa.add_widget(inp)
        campos.append(inp)
    inp_atual, inp_nova, inp_conf = campos

    lbl_status = Label(
        text="", markup=True, font_name="rajdhani.ttf", font_size="14sp",
        size_hint_y=None, height=dp(24), halign="center", valign="middle")
    lbl_status.bind(size=lambda i, s: setattr(i, 'text_size', s))
    caixa.add_widget(lbl_status)

    botoes = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(12))
    btn_salvar = BotaoAngular(text="SALVAR")
    btn_cancelar = BotaoAngular(text="CANCELAR")
    btn_cancelar.cor_texto = [0.6, 0.66, 0.72, 1]
    botoes.add_widget(btn_salvar)
    botoes.add_widget(btn_cancelar)
    caixa.add_widget(botoes)

    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    def _salvar(*_):
        if btn_salvar.disabled:
            return
        ok, msg = seguranca.trocar_pin(inp_atual.text, inp_nova.text, inp_conf.text)
        if ok:
            tatil.confirmar()
            try: som.tocar_salvar()
            except Exception: pass
            lbl_status.text = f"[color=#00ff88]{msg}[/color]"
            btn_salvar.disabled = True
            for c in campos:
                c.focus = False
            Clock.schedule_once(lambda dt: pop.dismiss(), 1.1)
            return
        tatil.erro()
        try: som.tocar_erro()
        except Exception: pass
        falta = seguranca.bloqueio_restante()
        if falta > 0:
            msg = f"Errou 3 vezes: senha bloqueada por {seguranca.tempo_legivel(falta)}."
        lbl_status.text = f"[color=#ff4455]{msg}[/color]"
        if "atual" in msg or falta > 0:
            alvo = inp_atual
        elif "confirmação" in msg:
            alvo = inp_conf
        else:
            alvo = inp_nova
        alvo.text = ""
        tremer_widget(alvo)

    btn_salvar.bind(on_release=_salvar)
    btn_cancelar.bind(on_release=lambda *_: pop.dismiss())
    inp_atual.bind(on_text_validate=lambda *_: setattr(inp_nova, 'focus', True))
    inp_nova.bind(on_text_validate=lambda *_: setattr(inp_conf, 'focus', True))
    inp_conf.bind(on_text_validate=_salvar)
    _abrir_popup(caixa, pop)
    _bind_teclado(caixa, pop)
    return pop


def popup_resumo_dia(tot_pecas, tot_xp, on_confirm):"""),
    ("""    inp_data = InputHolografico(
        text=hoje.strftime("%d/%m/%Y"),
        font_name="orbitron.ttf", font_size="22sp",
        foreground_color=(0, 0.9, 1, 1), cursor_color=(0, 0.9, 1, 1),
        halign="center", size_hint_y=None, height=dp(58))
    btn = BotaoAngular(text=">>  SALVAR TURNO  <<", size_hint_y=None, height=dp(52))
    caixa.add_widget(btn)
    caixa.add_widget(inp_data)
""", """    inp_data = InputHolografico(
        text=hoje.strftime("%d/%m/%Y"),
        font_name="orbitron.ttf", font_size="22sp",
        foreground_color=(0, 0.9, 1, 1), cursor_color=(0, 0.9, 1, 1),
        halign="center", size_hint_y=None, height=dp(58))
    formatar_data_digitada(inp_data)
    anexar_teclado(inp_data, 'numeros')
    lbl_aviso = Label(
        text="", markup=True, font_name="rajdhani.ttf", font_size="14sp",
        size_hint_y=None, height=dp(22), halign="center", valign="middle")
    lbl_aviso.bind(size=lambda i, s: setattr(i, 'text_size', s))
    btn = BotaoAngular(text=">>  SALVAR TURNO  <<", size_hint_y=None, height=dp(52))
    # o campo vem antes do botao: o teclado sobe a caixa inteira
    caixa.add_widget(inp_data)
    caixa.add_widget(lbl_aviso)
    caixa.add_widget(btn)
"""),
    ("""    def _confirmar(*_):
        raw = inp_data.text.strip()
        try:
            d = datetime.strptime(raw, "%d/%m/%Y")
            data_str = f"{d.strftime('%d/%m/%Y')}  {hoje.strftime('%H:%M')}"
        except ValueError:
            data_str = hoje.strftime("%d/%m/%Y  %H:%M")
        pop.dismiss()
        on_confirm(data_str)
""", """    def _confirmar(*_):
        d, motivo = ler_data(inp_data.text)
        if d is None:                     # antes virava 'hoje' sem avisar
            lbl_aviso.text = f"[color=#ff4455]{motivo}[/color]"
            try:
                import tatil
                tatil.erro()
            except Exception:
                pass
            tremer_widget(inp_data)
            return
        data_str = f"{d.strftime('%d/%m/%Y')}  {hoje.strftime('%H:%M')}"
        pop.dismiss()
        on_confirm(data_str)

    inp_data.bind(text=lambda *_: setattr(lbl_aviso, 'text', ''))
"""),
])

patch(os.path.join(A, 'main.py'), [
    ("""    def recalcular_totais(self):""", """    def trocar_senha(self):
        \"\"\"Botao do menu: abre a janela de trocar a senha.\"\"\"
        from helpers import popup_trocar_senha
        popup_trocar_senha()

    def recalcular_totais(self):"""),
])

patch(os.path.join(A, 'interface.kv'), [
    ("""            # ── Liga/desliga a vibracao (resposta tatil) ──────
            BotaoAngular:
                text:        "VIBRAÇÃO:  LIGADA" if app.vibracao else "VIBRAÇÃO:  DESLIGADA"
                font_name:   "orbitron.ttf"
                font_size:   "11sp"
                pos_hint:    {"center_x": 0.5, "center_y": 0.14}
                size_hint:   (0.6, None)
                height:      dp(40)
                cor_texto:   [0.0, 0.9, 1.0, 1.0] if app.vibracao else [0.45, 0.5, 0.56, 1.0]
                on_release:  app.alternar_vibracao()
""", """            # ── Liga/desliga a vibracao + trocar a senha ─────
            BoxLayout:
                pos_hint:    {"center_x": 0.5, "center_y": 0.14}
                size_hint:   (0.88, None)
                height:      dp(40)
                spacing:     dp(10)
                BotaoAngular:
                    text:        "VIBRAÇÃO: LIGADA" if app.vibracao else "VIBRAÇÃO: DESLIGADA"
                    font_name:   "orbitron.ttf"
                    font_size:   "10sp"
                    size_hint_x: 0.56
                    cor_texto:   [0.0, 0.9, 1.0, 1.0] if app.vibracao else [0.45, 0.5, 0.56, 1.0]
                    on_release:  app.alternar_vibracao()
                BotaoAngular:
                    text:        "TROCAR SENHA"
                    font_name:   "orbitron.ttf"
                    font_size:   "10sp"
                    size_hint_x: 0.44
                    cor_texto:   [0.0, 0.9, 1.0, 1.0]
                    on_release:  app.trocar_senha()
"""),
])
print('ok')
