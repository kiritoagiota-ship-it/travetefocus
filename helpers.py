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

import som
from efeitos import (
    InputHolografico, BotaoAngular, BotaoAngularAlerta,
    ListaItem, tremer_tela, explodir_estilhacos
)

# ─── Vibração Android ────────────────────────────────────────────────────────
def vibrar(duracao_ms=80):
    """Vibra o celular por `duracao_ms` (respeita o liga/desliga do app).
    Para as respostas curtinhas use tatil.tecla/confirmar/erro/forte."""
    try:
        import tatil
        tatil.pulso(duracao_ms)
    except Exception:
        pass


# ─── Sugestões de peças (teclado de letras do registro) ─────────────────────
def sugestoes_pecas(texto=''):
    """Nomes de peças já usadas (mais recentes primeiro, sem repetir),
    filtrados pelo que já foi digitado (sem ligar para acento/maiúscula):
    primeiro as que começam com o texto, depois as que o contêm."""
    from efeitos import _sem_acento
    app = App.get_running_app()
    fontes = [r[0] for r in reversed(list(getattr(app, 'registros', []))) if r]
    for m in reversed(list(getattr(app, 'memorias', []))):
        fontes += [it[0] for it in m.get('itens', []) if it]
    chave = _sem_acento(texto.strip())
    vistos, comeca, contem = set(), [], []
    for nome in fontes:
        nome = str(nome).strip()
        k = _sem_acento(nome)
        if not nome or k in vistos:
            continue
        vistos.add(k)
        if not chave:
            comeca.append(nome)
        elif k == chave:
            continue
        elif k.startswith(chave):
            comeca.append(nome)
        elif chave in k:
            contem.append(nome)
    return comeca + contem


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
    # sem a fonte de emoji: orbitron/rajdhani nao tem esses glifos e o
    # Kivy desenharia um quadradinho; usa um equivalente que as fontes tem
    return _EMOJI_TEXTO.get(emoji_char, emoji_char)


_EMOJI_TEXTO = {'🔥': '>>', '✕': 'X', '✓': 'OK', '★': '*'}


def _bind_teclado(caixa, pop):
    """
    Move o modal para cima quando o teclado Android aparecer.
    Guard contra duplicata: se ja foi chamado no mesmo popup, ignora.
    """
    if getattr(pop, '_bind_teclado_ok', False):
        return
    pop._bind_teclado_ok = True
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
    # chamado de novo (ex: caixa do PIN fica verde no acerto): so troca a cor,
    # sem empilhar outro fundo e outra borda por cima dos antigos
    if getattr(widget, '_bg_cor_borda', None) is not None:
        widget._bg_cor_borda.rgba = cor_borda
        return
    with widget.canvas.before:
        Color(0.03, 0.03, 0.09, 0.97)
        widget._bg_rr = RoundedRectangle(
            pos=widget.pos, size=widget.size, radius=[14])
        widget._bg_cor_borda = Color(*cor_borda)
        widget._bg_ln = Line(
            rounded_rectangle=[widget.x, widget.y, widget.width, widget.height, 14],
            width=1.6)

    def _upd(inst, *_):
        inst._bg_rr.pos  = inst.pos
        inst._bg_rr.size = inst.size
        inst._bg_ln.rounded_rectangle = [
            inst.x, inst.y, inst.width, inst.height, 14]

    widget.bind(pos=_upd, size=_upd)


_transicao = {'sentido': 1, 'ativa': False, 'destino': None}


def _soltar_foco(tela):
    """Tira o foco dos campos da tela que esta saindo: fecha o teclado SAO
    (senao ele fica aberto por cima da proxima tela)."""
    try:
        from kivy.uix.textinput import TextInput
        for w in tela.walk(restrict=True):
            if isinstance(w, TextInput) and w.focus:
                w.focus = False
    except Exception as e:
        print(f"[transicao] soltar foco: {e}")


def transicao_tela(app, destino):
    """Troca de tela com um corte de espada atravessando a janela
    (espadachim.golpe_tela). O sentido alterna entre ida e volta."""
    try:
        sm = app.root.ids.sm
    except Exception as e:
        print(f"[transicao_tela] sem ScreenManager: {e}")
        return
    if _transicao['ativa']:
        # toque durante o corte: so atualiza o destino (o ultimo pedido vale)
        _transicao['destino'] = destino
        return
    if sm.current == destino:
        return
    _transicao['destino'] = destino

    def _trocar():
        alvo = _transicao['destino']
        try:
            _soltar_foco(sm.current_screen)
            if alvo and sm.current != alvo:
                sm.current = alvo
        except Exception as e:
            print(f"[transicao] sm.current={alvo} falhou: {e}")

    def _fim():
        _transicao['ativa'] = False
        _trocar()          # pedido feito depois do pico do corte

    try:
        from espadachim import golpe_tela
        _transicao['ativa'] = True
        sentido = _transicao['sentido']
        _transicao['sentido'] = -sentido
        cor = (0.0, 0.9, 1.0) if sentido > 0 else (0.6, 0.25, 1.0)
        try:
            som.tocar('transicao')
        except Exception:
            pass
        golpe_tela(on_meio=_trocar, on_fim=_fim, cor=cor, sentido=sentido)
    except Exception as e:
        print(f"[transicao_tela] erro: {e}")
        _transicao['ativa'] = False
        _trocar()


def animar_ganho_xp(quantidade, origem=None):
    """'+N XP' subindo. Com `origem` (ex: o item recem-adicionado na lista),
    nasce em cima dele em vez de no meio da tela (onde cobria o botao)."""
    ww = Window.width
    wh = Window.height
    fs = min(int(wh * 0.055), 34)

    y_base = wh * 0.66
    if origem is not None:
        try:
            _, oy = origem.to_window(origem.x, origem.y)
            y_base = oy + origem.height / 2.0 - 30
        except Exception:
            pass
    y_alto  = y_base + 22
    y_saida = y_base + min(wh * 0.12, dp(90))

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


def largura_coluna():
    """Largura util do app: tela toda no celular, coluna central no PC."""
    return min(Window.width, dp(560))


def _abrir_popup(caixa, pop):
    # em janela larga (PC/tablet deitado) o popup nao estica na tela toda
    try:
        if caixa.size_hint_x is not None and Window.width > dp(640):
            frac = caixa.size_hint_x
            caixa.size_hint_x = None
            caixa.width = min(Window.width * frac, dp(520))
    except Exception:
        pass
    caixa.opacity  = 0
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.44}

    def _on_open(*_):
        Animation(opacity=1, duration=0.16,
                  transition='out_expo').start(caixa)
        Animation(pos_hint={'center_x': 0.5, 'center_y': 0.5},
                  duration=0.20, transition='out_back').start(caixa)

    pop.bind(on_open=_on_open)

    def _on_dismiss(*_):
        # fecha o teclado SAO dos campos do popup (senao ele ficava aberto
        # sobre a tela). Nao devolver nada: valor "verdadeiro" cancela o fechar.
        try:
            from kivy.uix.textinput import TextInput
            for w in caixa.walk(restrict=True):
                if isinstance(w, TextInput) and w.focus:
                    w.focus = False
        except Exception as e:
            print(f"[popup] soltar foco: {e}")
    pop.bind(on_dismiss=_on_dismiss)
    pop.open()



# ── Teclado customizado SAO ───────────────────────────────────────────────────

def _caixa_do_popup(inp):
    """Se `inp` esta num popup, devolve a caixa (filha do conteudo do Popup)."""
    for pop in list(Window.children):
        if not isinstance(pop, Popup):
            continue
        conteudo = pop.content
        w = inp
        while w is not None and w.parent is not None:
            if w.parent is conteudo:
                return w
            w = w.parent
    return None


def _desviar_do_teclado(inp, kb, estado):
    """O teclado SAO nao informa altura ao Kivy (Window.keyboard_height fica
    0), entao o proprio teclado sobe o que estiver atras dele: a caixa do
    popup ou, fora de popup, a tela inteira."""
    try:
        _, iy = inp.to_window(inp.x, inp.y)
        caixa = _caixa_do_popup(inp)
        if caixa is not None:
            _, cy0 = caixa.to_window(caixa.x, caixa.y)
            if caixa.height < Window.height - dp(18) - kb.top:
                iy = cy0                      # cabe inteira: sobe a caixa toda
        falta = (kb.top + dp(12)) - iy
        if falta <= 0:
            return
        if caixa is not None:
            _, cy = caixa.to_window(caixa.x, caixa.y)
            topo_max = Window.height - dp(6)
            novo_cy = cy + falta + caixa.height / 2.0
            novo_cy = min(novo_cy, topo_max - caixa.height / 2.0) if caixa.height < topo_max - kb.top else novo_cy
            estado['alvo'], estado['orig'] = caixa, dict(caixa.pos_hint)
            dica = dict(caixa.pos_hint)
            # pos_hint e relativo ao conteudo do popup (menor que a janela)
            pai = caixa.parent
            _, py = pai.to_window(pai.x, pai.y)
            dica['center_y'] = (novo_cy - py) / float(max(1, pai.height))
            Animation.cancel_all(caixa, 'pos_hint')
            Animation(pos_hint=dica, duration=0.18, transition='out_quad').start(caixa)
        else:
            sm = App.get_running_app().root.ids.sm
            estado['alvo'], estado['orig'] = sm, None
            Animation.cancel_all(sm, 'y')
            Animation(y=falta, duration=0.18, transition='out_quad').start(sm)
    except Exception as e:
        print(f"[teclado] desviar: {e}")


def _voltar_do_teclado(estado):
    alvo, orig = estado.get('alvo'), estado.get('orig')
    estado['alvo'] = estado['orig'] = None
    if alvo is None:
        return
    try:
        if orig is not None:
            Animation.cancel_all(alvo, 'pos_hint')
            Animation(pos_hint=orig, duration=0.16, transition='out_quad').start(alvo)
        else:
            Animation.cancel_all(alvo, 'y')
            Animation(y=0, duration=0.16, transition='out_quad').start(alvo)
    except Exception as e:
        print(f"[teclado] voltar: {e}")


def anexar_teclado(inp, tipo='letras', decimal=False, sugestoes=None):
    """
    Teclado customizado SAO.
    - Passa 'fechar' callback para _TecladoBase — OK fecha sem crash
    - Toque fora do teclado tambem fecha
    - Supressao do teclado Android via _bind_keyboard no InputHolografico
    - sugestoes(texto) -> nomes: linha de sugestoes no teclado de letras
    """
    if getattr(inp, '_teclado_custom_ok', False):
        return
    inp._teclado_custom_ok = True

    from efeitos import TecladoLetras, TecladoNumeros
    from kivy.animation import Animation as _Anim

    Kls = TecladoLetras if tipo == 'letras' else TecladoNumeros
    ref    = [None]
    _touch = [None]  # binding de toque fora
    desvio = {'alvo': None, 'orig': None}

    def _esconder():
        kb = ref[0]
        if not kb:
            return
        _voltar_do_teclado(desvio)
        # Remover listener de toque fora
        try:
            Window.unbind(on_touch_down=_touch[0])
        except Exception:
            pass
        _touch[0] = None

        def _rm(*_):
            try:
                Window.remove_widget(kb)
            except Exception:
                pass
            ref[0] = None

        # bind() devolve None: encadear .bind(...).start(...) derrubava o app
        # toda vez que o teclado fechava (OK, toque fora, popup fechando)
        anim = _Anim(opacity=0, duration=0.10, transition='in_expo')
        anim.bind(on_complete=_rm)
        anim.start(kb)

    def _toque_fora(win, touch):
        """Fecha o teclado se o toque for acima dele."""
        kb = ref[0]
        if kb and not kb.collide_point(*touch.pos):
            try:   # tocar no proprio campo nao fecha o teclado
                if inp.collide_point(*inp.to_widget(*touch.pos)):
                    return False
            except Exception:
                pass
            _esconder()
        return False   # nao consumir o toque

    def _mostrar(inst, focused):
        if focused:
            if ref[0]:
                return
            kb = (Kls(target=inst, fechar=_esconder, decimal=decimal)
                  if tipo == 'numeros'
                  else Kls(target=inst, fechar=_esconder, sugestoes=sugestoes))
            larg       = largura_coluna()
            kb.size    = (larg, kb.height)
            kb.pos     = ((Window.width - larg) / 2.0, 0)
            kb.opacity = 0
            Window.add_widget(kb)
            ref[0] = kb
            _Anim(opacity=1, duration=0.14, transition='out_expo').start(kb)
            Clock.schedule_once(lambda dt: _desviar_do_teclado(inst, kb, desvio), 0)

            # Registrar listener para fechar ao tocar fora
            _touch[0] = _toque_fora
            Window.bind(on_touch_down=_toque_fora)
        else:
            _esconder()

    inp.bind(focused=_mostrar)

    # OK fecha o teclado mas o campo continua focado: sem isto, tocar de novo
    # no mesmo campo (ex: 2a tentativa do PIN) nao reabria o teclado
    def _toque_campo(inst, touch):
        try:
            if inst.focus and ref[0] is None and inst.collide_point(*touch.pos):
                Clock.schedule_once(lambda dt: _mostrar(inst, True), 0)
        except Exception as e:
            print(f"[teclado] reabrir: {e}")
        return False
    inp.bind(on_touch_down=_toque_campo)


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

    for w in [lbl_info, inp, lbl_preview, btn]:  # o teclado sobe a caixa inteira
        caixa.add_widget(w)
    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    def _confirmar(*_):
        val = max(0, int(inp.text or 0))
        pop.dismiss()
        on_save(val)

    btn.bind(on_release=_confirmar)
    inp.bind(on_text_validate=_confirmar)
    anexar_teclado(inp, 'numeros')
    _abrir_popup(caixa, pop)
    _bind_teclado(caixa, pop)
    # teclado customizado SAO — sem teclado Android


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