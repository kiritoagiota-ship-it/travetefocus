"""
helpers.py — TraveteFocus
Funções utilitárias compartilhadas por todas as telas.
Importado por telas/*.py e main.py.
"""
from kivy.app import App
from kivy.animation import Animation
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.metrics import dp
from datetime import datetime
import random

from efeitos import (
    InputHolografico, BotaoAngular, BotaoAngularAlerta,
    ListaItem, tremer_tela, explodir_estilhacos
)

# ─── Vibração Android ────────────────────────────────────────────────────────
def vibrar(duracao_ms=80):
    """Vibra o celular no Android. No-op em outras plataformas."""
    try:
        from kivy.utils import platform as _plat
        if _plat == 'android':
            from plyer import vibrator
            vibrator.vibrate(duracao_ms / 1000.0)
    except Exception:
        pass  # plyer não disponível ou permissão negada


# ─── Suporte a Emoji com fonte dedicada ──────────────────────────────────────
# NotoEmoji-Regular.ttf deve estar na raiz do projeto.
# Permite usar emojis em qualquer widget com markup=True,
# mantendo a fonte Orbitron para o resto do texto.
EMOJI_FONT = "NotoEmoji-Regular.ttf"

def em(emoji_char):
    """
    Renderiza emoji com NotoEmoji se disponivel — fallback seguro.
    Sem NotoEmoji no APK: retorna o char diretamente, sem crash.
    """
    try:
        from kivy.resources import resource_find as _rf
        if _rf(EMOJI_FONT):
            return f'[font={EMOJI_FONT}]{emoji_char}[/font]'
    except Exception:
        pass
    return emoji_char


def _bind_teclado(caixa, pop):
    """
    Move o modal para cima quando o teclado Android aparecer,
    evitando que ele cubra o botão de confirmar.
    """
    def _on_kb(window, kb_height):
        if kb_height > 0:
            offset = kb_height + dp(12)
            cy = min((offset + caixa.height / 2) / Window.height, 0.94)
            caixa.pos_hint = {'center_x': 0.5, 'center_y': cy}
        else:
            caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
    Window.bind(keyboard_height=_on_kb)
    pop.bind(on_dismiss=lambda *_: Window.unbind(keyboard_height=_on_kb))



# ═══════════════════════════════════════════════════════════
#  SISTEMA DE LEVEL
# ═══════════════════════════════════════════════════════════

def calcular_level(total_xp):
    if total_xp <= 0:
        return 1, 0, int(800 * 1 ** 1.5)
    level = 1
    acumulado = 0
    while level <= 100:
        necessario = int(800 * (level ** 1.5))
        if acumulado + necessario > total_xp:
            return level, total_xp - acumulado, necessario
        acumulado += necessario
        level     += 1
    return 100, 0, 0


_RANKS = [
    (1,  10, "Novato da Cidade do Começo"),
    (11, 20, "Explorador de Andares"),
    (21, 30, "Estrategista de Linha de Frente"),
    (31, 40, "Membro da Guilda"),
    (41, 50, "Sobrevivente da Zona Segura"),
    (51, 60, "Cavaleiro do Sangue"),
    (61, 70, "Domador de Lotes"),
    (71, 80, "Lâmina Gêmea"),
    (81, 90, "Comandante da Vanguarda"),
    (91, 100, "Beater de Aincrad"),
]


def obter_titulo_level(level: int) -> str:
    level = max(1, min(level, 100))
    for inicio, fim, titulo in _RANKS:
        if inicio <= level <= fim:
            return titulo
    return "Beater de Aincrad"


# ═══════════════════════════════════════════════════════════
#  HELPERS VISUAIS
# ═══════════════════════════════════════════════════════════

def aplicar_fundo_holografico(widget, cor_borda=None):
    if cor_borda is None:
        cor_borda = (0, 0.9, 1, 0.85)
    with widget.canvas.before:
        Color(0.03, 0.03, 0.09, 0.97)
        widget._bg_rr = RoundedRectangle(
            pos=widget.pos, size=widget.size, radius=[14])
        Color(*cor_borda)
        widget._bg_ln = Line(
            rounded_rectangle=[widget.x, widget.y, widget.width, widget.height, 14],
            width=1.6)

    def _upd(inst, *_):
        inst._bg_rr.pos  = inst.pos
        inst._bg_rr.size = inst.size
        inst._bg_ln.rounded_rectangle = [
            inst.x, inst.y, inst.width, inst.height, 14]

    widget.bind(pos=_upd, size=_upd)


def transicao_tela(app, destino):
    try:
        sm = app.root.ids.sm
        overlay = Widget(size=Window.size, opacity=0)
        with overlay.canvas:
            Color(0, 0, 0, 1)
            Rectangle(pos=(0, 0), size=Window.size)

        scan = Widget(size=(Window.width, 2), pos=(0, Window.height))
        with scan.canvas:
            Color(0, 0.9, 1, 0.55)
            scan_rect = Rectangle(pos=scan.pos, size=scan.size)
        scan.bind(pos=lambda i, v: setattr(scan_rect, 'pos', v))

        overlay.add_widget(scan)
        Window.add_widget(overlay)

        def _fade_out(anim, widget):
            try:
                sm.current = destino
            except Exception as e:
                print(f"[transicao] sm.current={destino} falhou: {e}")
            anim_out = Animation(opacity=0, duration=0.08, transition='out_quad')
            anim_out.bind(on_complete=lambda a, w: Window.remove_widget(overlay))
            anim_out.start(overlay)

        anim_in = Animation(opacity=0.92, duration=0.06, transition='out_quad')
        anim_in.bind(on_complete=lambda a, w: Clock.schedule_once(
            lambda dt: _fade_out(a, w), 0.01))
        anim_in.start(overlay)
        Animation(y=-4, duration=0.12, transition='out_quad').start(scan)
    except Exception as e:
        print(f"[transicao_tela] erro: {e}")
        try:
            app.root.ids.sm.current = destino
        except Exception:
            pass


def animar_ganho_xp(quantidade):
    ww = Window.width
    wh = Window.height
    fs = min(int(wh * 0.07), 42)

    y_base  = wh * 0.66
    y_alto  = y_base + 22
    y_saida = y_base + wh * 0.20

    lbl = Label(
        text=f"[b]+{quantidade} XP[/b]",
        markup=True, color=(0.0, 1.0, 0.53, 0.0),
        font_name="orbitron.ttf", font_size=fs,
        size_hint=(None, None), size=(ww * 0.8, 60),
        pos=(ww * 0.10, y_base))

    Window.add_widget(lbl)
    anim = (
        Animation(color=(0.0, 1.0, 0.53, 1.0), y=y_alto,
                  duration=0.28, transition='out_quad') +
        Animation(duration=0.42) +
        Animation(color=(0.0, 1.0, 0.53, 0.0), y=y_saida,
                  duration=0.40, transition='in_quad')
    )
    anim.bind(on_complete=lambda *_: Window.remove_widget(lbl))
    anim.start(lbl)


# ═══════════════════════════════════════════════════════════
#  POPUPS
# ═══════════════════════════════════════════════════════════

def _make_popup():
    layout = FloatLayout()
    pop = Popup(
        title="", content=layout, size_hint=(1, 1), background="",
        background_color=(0, 0, 0, 0.82), separator_height=0)
    return pop, layout


def _abrir_popup(caixa, pop):
    caixa.opacity  = 0
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.44}

    def _on_open(*_):
        Animation(opacity=1, duration=0.22,
                  transition='out_quad').start(caixa)
        Animation(pos_hint={'center_x': 0.5, 'center_y': 0.5},
                  duration=0.26, transition='out_quad').start(caixa)

    pop.bind(on_open=_on_open)
    pop.open()


def popup_pedir_xp(nome: str, quantidade: int, on_save):
    pop, layout = _make_popup()
    h = min(dp(290), int(Window.height * 0.52))
    caixa = BoxLayout(
        orientation='vertical', padding=[dp(26), dp(20), dp(26), dp(20)],
        spacing=dp(10), size_hint=(0.88, None), height=h)
    aplicar_fundo_holografico(caixa, (0.55, 0.05, 0.95, 0.9))

    lbl_info = Label(
        text=(f"[color=#8a2be2]>> LOTE DETECTADO[/color]\n"
              f"[color=#00e5ff][b]{nome}[/b][/color]   "
              f"[color=#555555]× {quantidade} un.[/color]\n"
              f"[color=#444444]Valor de XP por peça:[/color]"),
        markup=True, font_name="orbitron.ttf", font_size="12sp",
        halign="center", size_hint_y=None, height=dp(72))

    inp = InputHolografico(
        input_filter='int', font_name="orbitron.ttf", font_size="30sp",
        background_color=(0, 0, 0, 0), foreground_color=(0, 0.9, 1, 1),
        cursor_color=(0, 0.9, 1, 1), halign="center",
        size_hint_y=None, height=dp(64))

    lbl_preview = Label(
        text="TOTAL DO LOTE:  [color=#00ff88][b]0 XP[/b][/color]",
        markup=True, font_name="rajdhani.ttf", font_size="16sp",
        halign="center", size_hint_y=None, height=dp(32))

    def _preview(inst, valor):
        try:
            xp_un = max(0, int(valor or 0))
        except ValueError:
            xp_un = 0
        lbl_preview.text = f"TOTAL DO LOTE:  [color=#00ff88][b]{xp_un * quantidade} XP[/b][/color]"

    inp.bind(text=_preview)
    btn = BotaoAngular(text=">>  CONFIRMAR  <<", size_hint_y=None, height=dp(52))

    for w in [lbl_info, inp, lbl_preview, btn]:
        caixa.add_widget(w)
    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    def _confirmar(*_):
        val = max(0, int(inp.text or 0))
        pop.dismiss()
        on_save(val)

    btn.bind(on_release=_confirmar)
    inp.bind(on_text_validate=_confirmar)
    _abrir_popup(caixa, pop)
    _bind_teclado(caixa, pop)
    # auto-focus removido — evita teclado cobrindo botão


def popup_delete_engracado(on_confirm):
    pop, layout = _make_popup()
    h = min(dp(196), int(Window.height * 0.38))
    caixa = BoxLayout(
        orientation='vertical', padding=[dp(26), dp(20), dp(26), dp(20)],
        spacing=dp(14), size_hint=(0.84, None), height=h)
    aplicar_fundo_holografico(caixa, (1.0, 0.08, 0.22, 0.9))

    caixa.add_widget(Label(
        text=("[color=#ff2244]!!  ATENCAO[/color]\n"
              "[color=#cccccc]Desintegrar este registro?\n"
              "Esta ação é irreversível.[/color]"),
        markup=True, font_name="orbitron.ttf", font_size="13sp",
        halign="center", size_hint_y=None, height=dp(74)))

    botoes  = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(14))
    btn_sim = BotaoAngularAlerta(text="DESINTEGRAR")
    btn_nao = BotaoAngular(text="CANCELAR")
    botoes.add_widget(btn_sim)
    botoes.add_widget(btn_nao)
    caixa.add_widget(botoes)
    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    def _confirmar(*_):
        pop.dismiss()
        on_confirm()

    btn_sim.bind(on_release=_confirmar)
    btn_nao.bind(on_release=lambda *_: pop.dismiss())
    _abrir_popup(caixa, pop)


def popup_resumo_dia(tot_pecas, tot_xp, on_confirm):
    pop, layout = _make_popup()
    # dp() garante tamanho correto em qualquer densidade de tela
    alt = min(int(dp(400)), int(Window.height * 0.68))
    caixa = BoxLayout(
        orientation='vertical',
        padding=[dp(26), dp(16), dp(26), dp(16)],
        spacing=dp(10),
        size_hint=(0.90, None), height=alt)
    aplicar_fundo_holografico(caixa, (0, 0.9, 1, 0.9))

    sep = Widget(size_hint_y=None, height=dp(1))
    with sep.canvas:
        Color(0, 0.9, 1, 0.22)
        sep._r = Rectangle(pos=sep.pos, size=sep.size)
    sep.bind(pos=lambda i, v: setattr(i._r, 'pos', v),
             size=lambda i, v: setattr(i._r, 'size', v))

    hoje = datetime.now()
    for w in [
        Label(text="[b][color=#00e5ff]  RESUMO DO TURNO  [/color][/b]",
              markup=True, font_name="orbitron.ttf", font_size="16sp",
              size_hint_y=None, height=dp(38), halign="center"),
        sep,
        Label(text=(f"[color=#888888]Total Produzido[/color]   "
                    f"[color=#00e5ff][b]{tot_pecas} un.[/b][/color]\n\n"
                    f"[color=#888888]Experiência Obtida[/color]   "
                    f"[color=#00ff88][b]+{tot_xp} XP[/b][/color]"),
              markup=True, font_name="rajdhani.ttf", font_size="18sp",
              halign="center", size_hint_y=None, height=dp(88)),
        Label(text="[color=#555555]Data do turno:[/color]",
              markup=True, font_name="orbitron.ttf", font_size="11sp",
              halign="center", size_hint_y=None, height=dp(22)),
    ]:
        caixa.add_widget(w)

    inp_data = InputHolografico(
        text=hoje.strftime("%d/%m/%Y"),
        font_name="orbitron.ttf", font_size="22sp",
        foreground_color=(0, 0.9, 1, 1), cursor_color=(0, 0.9, 1, 1),
        halign="center", size_hint_y=None, height=dp(58))
    btn = BotaoAngular(text=">>  SALVAR TURNO  <<", size_hint_y=None, height=dp(52))
    caixa.add_widget(btn)
    caixa.add_widget(inp_data)

    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    def _confirmar(*_):
        raw = inp_data.text.strip()
        try:
            d = datetime.strptime(raw, "%d/%m/%Y")
            data_str = f"{d.strftime('%d/%m/%Y')}  {hoje.strftime('%H:%M')}"
        except ValueError:
            data_str = hoje.strftime("%d/%m/%Y  %H:%M")
        pop.dismiss()
        on_confirm(data_str)

    btn.bind(on_release=_confirmar)
    inp_data.bind(on_text_validate=_confirmar)
    _abrir_popup(caixa, pop)
    _bind_teclado(caixa, pop)
    # auto-focus removido — teclado sobe só quando usuario toca no campo)
