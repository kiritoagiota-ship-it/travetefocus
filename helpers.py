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
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle, PushMatrix, PopMatrix, Translate
from kivy.metrics import dp
from datetime import datetime, timedelta
import math
import random

import som
from animacoes_ui import fmt_br, _matriz, _chanfro
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

def _hud_cores(widget, cor_borda, luz=0.0):
    """Pinta o painel HUD na cor `cor_borda` (`luz` 0..1 puxa para o branco:
    o clarao de quando o aviso abre)."""
    r, g, b = cor_borda[:3]
    a = cor_borda[3] if len(cor_borda) > 3 else 1.0

    def mis(k):
        return (r + (1 - r) * k, g + (1 - g) * k, b + (1 - b) * k)
    cb, ci, ca = widget._bg_cores
    cb.rgba = (*mis(luz * 0.6), min(1.0, a + luz * 0.3))
    ci.rgba = (r, g, b, 0.22 + 0.3 * luz)
    ca.rgba = (*mis(0.35 + 0.5 * luz), 1.0)


def aplicar_fundo_holografico(widget, cor_borda=None):
    """Fundo dos avisos: painel HUD de cantos chanfrados, borda na cor dada,
    uma linha fina por dentro, os quatro cantos acesos e uma aba no topo."""
    if cor_borda is None:
        cor_borda = (0, 0.9, 1, 0.85)
    # chamado de novo (ex: caixa do PIN fica verde no acerto): so troca a cor,
    # sem empilhar outro fundo e outra borda por cima dos antigos
    if getattr(widget, '_bg_cores', None) is not None:
        widget._bg_cor = tuple(cor_borda)
        _hud_cores(widget, cor_borda)
        return
    from kivy.graphics import Mesh
    with widget.canvas.before:
        Color(0.03, 0.03, 0.09, 0.97)
        widget._bg_mesh = Mesh(mode='triangle_fan')
        cb = Color()
        widget._bg_ln = Line(width=dp(1.2), close=True)
        ci = Color()
        widget._bg_in = Line(width=dp(1), close=True)
        ca = Color()
        widget._bg_cantos = [Line(width=dp(1.8)) for _ in range(4)]
        widget._bg_aba = Rectangle()
    widget._bg_cores = (cb, ci, ca)
    widget._bg_cor = tuple(cor_borda)
    _hud_cores(widget, cor_borda)

    def _upd(inst, *_):
        x, y, w, h = inst.x, inst.y, inst.width, inst.height
        c = min(dp(14), w * 0.2, h * 0.2)
        pts = _chanfro(x, y, w, h, c)
        vs = []
        for i in range(0, len(pts), 2):
            vs += [pts[i], pts[i + 1], 0, 0]
        inst._bg_mesh.vertices = vs
        inst._bg_mesh.indices = list(range(len(pts) // 2))
        inst._bg_ln.points = pts
        d = dp(5)
        inst._bg_in.points = _chanfro(x + d, y + d, w - 2 * d, h - 2 * d, max(1.0, c - d * 0.6))
        L = min(dp(16), w * 0.15, h * 0.15)
        x2, y2 = x + w, y + h
        inst._bg_cantos[0].points = [x, y2 - c - L, x, y2 - c, x + c, y2, x + c + L, y2]
        inst._bg_cantos[1].points = [x2 - c - L, y2, x2 - c, y2, x2, y2 - c, x2, y2 - c - L]
        inst._bg_cantos[2].points = [x2, y + c + L, x2, y + c, x2 - c, y, x2 - c - L, y]
        inst._bg_cantos[3].points = [x + c + L, y, x + c, y, x, y + c, x, y + c + L]
        la = min(dp(64), w * 0.26)
        inst._bg_aba.pos = (x + (w - la) / 2.0, y2 - dp(1.5))
        inst._bg_aba.size = (la, dp(3))

    widget.bind(pos=_upd, size=_upd)
    _upd(widget)


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


# cor do corte = cor do botao da tela de destino
_COR_DESTINO = {'registro': (0.0, 0.9, 1.0), 'memorias': (0.62, 0.3, 1.0), 'progresso': (0.2, 0.75, 1.0),
                'ganhos': (0.1, 1.0, 0.55), 'calculadora': (1.0, 0.62, 0.1)}


def transicao_tela(app, destino):
    """Troca de tela: a espada corta e a tela antiga se parte em duas metades
    que escorregam (na cor do botao do destino); Voltar ao menu e um deslize
    mais leve. Se algo falhar, cai no corte antigo (espadachim.golpe_tela)."""
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
            # so solta o foco quando a tela muda DE VERDADE: este _trocar roda de
            # novo no fim do corte e, ja na tela nova, derrubava o campo que ela
            # tinha acabado de focar (o teclado do Registro as vezes nao abria)
            if alvo and sm.current != alvo:
                _soltar_foco(sm.current_screen)
                sm.current = alvo
        except Exception as e:
            print(f"[transicao] sm.current={alvo} falhou: {e}")

    def _fim():
        _transicao['ativa'] = False
        _trocar()          # pedido feito depois do pico do corte

    _transicao['ativa'] = True
    sentido = _transicao['sentido']
    _transicao['sentido'] = -sentido
    try:
        som.tocar('transicao')
    except Exception:
        pass
    try:
        from animacoes_ui import corte_parte_tela, deslize_voltar
        if destino == 'menu':
            deslize_voltar(on_meio=_trocar, on_fim=_fim)
        else:
            corte_parte_tela(cor=_COR_DESTINO.get(destino, (0.0, 0.9, 1.0)), sentido=sentido,
                             on_meio=_trocar, on_fim=_fim)
        return
    except Exception as e:
        print(f"[transicao_tela] corte novo: {e}")
    try:
        from espadachim import golpe_tela
        cor = (0.0, 0.9, 1.0) if sentido > 0 else (0.6, 0.25, 1.0)
        golpe_tela(on_meio=_trocar, on_fim=_fim, cor=cor, sentido=sentido)
    except Exception as e:
        print(f"[transicao_tela] erro: {e}")
        _transicao['ativa'] = False
        _trocar()


def transicao_link_start(app, destino, centro):
    """Entrar pelo SYSTEM LINK START: a costura de luz (suave) no lugar do
    corte de espada; a tela troca no escuro, logo depois da costura."""
    try:
        sm = app.root.ids.sm
    except Exception as e:
        print(f"[link start] sem ScreenManager: {e}")
        return
    if _transicao['ativa'] or sm.current == destino:
        return
    _transicao['ativa'] = True

    def _meio():
        try:
            _soltar_foco(sm.current_screen)
            sm.current = destino
        except Exception as e:
            print(f"[link start] troca: {e}")

    def _fim():
        _transicao['ativa'] = False
    try:
        from animacoes_ui import entrada_costura
        entrada_costura(centro, on_meio=_meio, on_fim=_fim)
    except Exception as e:
        print(f"[link start] {e}")
        _transicao['ativa'] = False
        transicao_tela(app, destino)


def animar_ganho_xp(quantidade, origem=None):
    """'+N XP' saltando. Com `origem` (o item recem-adicionado na lista) nasce
    no item e salta para logo ACIMA dele (nao fica por cima do texto do item):
    cresce passando um pouco do tamanho, assenta, segura e sobe sumindo.
    Tamanhos em sp/dp (em pixel fixo ficava pequeno no celular)."""
    from kivy.metrics import sp
    ww, wh = Window.size
    alt = dp(46)
    y_ini = wh * 0.62
    y_alvo = y_ini + dp(18)
    if origem is not None:
        try:
            _, oy = origem.to_window(origem.x, origem.y)
            y_ini = oy + origem.height / 2.0 - alt / 2.0
            y_alvo = min(wh - alt - dp(8), oy + origem.height - dp(4))
        except Exception:
            pass
    verde = (0.2, 1.0, 0.6)
    lbl = Label(
        text=f"[b]+{fmt_br(quantidade)} XP[/b]",
        markup=True, color=(verde[0], verde[1], verde[2], 0.0),
        font_name="orbitron.ttf", font_size=sp(26),
        outline_width=max(1, int(dp(1.5))), outline_color=(0.0, 0.10, 0.05, 1),
        size_hint=(None, None), size=(ww * 0.8, alt),
        pos=(ww * 0.10, y_ini))
    Window.add_widget(lbl)
    try:
        from animacoes_ui import _matriz
        tr, sc = _matriz(lbl)
    except Exception:
        tr = sc = None
    t = [0.0]
    SALTO, SEGURA, SAI = 0.26, 0.5, 0.42
    sobe = min(wh * 0.08, dp(56))

    def _p(dt):
        try:
            t[0] += dt
            k = t[0]
            if k < SALTO:
                u = k / SALTO
                e = 1 - (1 - u) ** 3
                lbl.y = y_ini + (y_alvo - y_ini) * e
                ov = 1 + 2.4 * (u - 1) ** 3 + 1.4 * (u - 1) ** 2       # passa um pouco e assenta
                if sc is not None:
                    sc.x = sc.y = 0.55 + 0.45 * ov
                lbl.color = (verde[0], verde[1], verde[2], min(1.0, u * 2.5))
            elif k < SALTO + SEGURA:
                lbl.y = y_alvo
                if sc is not None:
                    sc.x = sc.y = 1.0
                lbl.color = (verde[0], verde[1], verde[2], 1.0)
            elif k < SALTO + SEGURA + SAI:
                u = (k - SALTO - SEGURA) / SAI
                lbl.y = y_alvo + sobe * u * u
                lbl.color = (verde[0], verde[1], verde[2], 1.0 - u)
            else:
                Window.remove_widget(lbl)
                return False
        except Exception:
            try:
                Window.remove_widget(lbl)
            except Exception:
                pass
            return False
    Clock.schedule_interval(_p, 1 / 60.)


# ═══════════════════════════════════════════════════════════
#  POPUPS
# ═══════════════════════════════════════════════════════════

def uma_vez(fn):
    """Botao de confirmar protegido contra TOQUE DUPLO: so o primeiro toque
    vale (o popup leva uma fracao de segundo fechando e um segundo toque
    rapido duplicava a peca ou o turno)."""
    feito = [False]

    def _f(*a, **k):
        if feito[0]:
            return None
        feito[0] = True
        return fn(*a, **k)
    return _f


def _make_popup():
    layout = FloatLayout()
    pop = Popup(
        title="", content=layout, size_hint=(1, 1), background="",
        background_color=(0, 0, 0, 0.82), separator_height=0)
    return pop, layout


def texto_que_cabe(lbl, caixa=None):
    """O rotulo cresce ate caber o texto todo e a `caixa` do aviso cresce
    junto. Com a letra grande do celular o Kivy APAGA a linha que nao cabe
    (nem que falte 1 pixel: o nome do lote sumia no LOTE DETECTADO) e o texto
    sem quebra passava da borda. A altura de antes vira o minimo; o texto
    fica no meio, como antes."""
    minimo = lbl.height
    lbl.size_hint_y = None

    def _largura(i, w):
        i.text_size = (max(1, w), None)

    def _altura(i, ts):
        novo = max(minimo, ts[1] + dp(2))
        if abs(novo - i.height) > 0.5:
            if caixa is not None:
                caixa.height += novo - i.height
            i.height = novo
    lbl.bind(width=_largura, texture_size=_altura)
    _largura(lbl, lbl.width)
    return lbl


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
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
    # abre do meio para os lados (como o LEVEL UP), com um clarao na borda
    tr, sc = _matriz(caixa)
    sc.x, sc.y = 0.06, 0.94
    anim = {'ev': None}

    def _parar():
        if anim['ev'] is not None:
            anim['ev'].cancel()
            anim['ev'] = None

    def _cor_hud(luz):
        if getattr(caixa, '_bg_cores', None) is not None:
            _hud_cores(caixa, caixa._bg_cor, luz)
    # recem-aberto, o toque no fundo escuro nao fecha (o 2o toque de um toque
    # duplo no botao que abriu o popup caia no fundo e fechava na hora)
    if pop.auto_dismiss:
        pop.auto_dismiss = False

        def _libera(dt):
            if pop.parent is not None:
                pop.auto_dismiss = True
        Clock.schedule_once(_libera, 0.35)

    def _abrir_ja():
        # comeca junto com o fundo escurecendo (o on_open do Popup so vem
        # depois do fade dele: ficava ~0,2 s de tela escura e vazia)
        _parar()
        t = [0.0]
        _cor_hud(1.0)

        def _abre(dt):
            try:
                t[0] += min(dt, 1 / 30.)
                k = min(1.0, t[0] / 0.24)
                e = 1 - (1 - k) ** 3
                sc.x = 0.06 + 0.94 * e
                sc.y = 0.94 + 0.06 * e
                caixa.opacity = min(1.0, 0.15 + e * 1.6)
                _cor_hud(max(0.0, 1.0 - t[0] / 0.42))       # o clarao dura um pouco mais
                if t[0] >= 0.42:
                    sc.x = sc.y = 1.0
                    _cor_hud(0.0)
                    anim['ev'] = None
                    return False
            except Exception:
                sc.x = sc.y = 1.0
                caixa.opacity = 1
                anim['ev'] = None
                return False
        anim['ev'] = Clock.schedule_interval(_abre, 1 / 60.)

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

    def _ao_fechar(*_):
        # a caixa se fecha numa linha (de cima e de baixo para o meio)
        # enquanto o fundo escuro some
        try:
            _parar()
            _cor_hud(0.0)
            Animation.cancel_all(caixa, 'opacity')
            t = [0.0]
            sx0 = sc.x

            def _fecha(dt):
                try:
                    t[0] += min(dt, 1 / 30.)
                    k = min(1.0, t[0] / 0.14)
                    e = k * k
                    sc.y = 1 - 0.92 * e
                    sc.x = sx0 + (1.0 - sx0) * e
                    caixa.opacity = 1 - e
                    if k >= 1:
                        anim['ev'] = None
                        return False
                except Exception:
                    anim['ev'] = None
                    return False
            anim['ev'] = Clock.schedule_interval(_fecha, 1 / 60.)
        except Exception as e:
            print(f"[popup] fechar: {e}")
    try:
        pop._anim_duration = 0.16
        pop.bind(on_pre_dismiss=_ao_fechar)
    except Exception as e:
        print(f"[popup] animacao de saida: {e}")
    pop.open()
    _abrir_ja()



# ── Teclado customizado SAO ───────────────────────────────────────────────────

def _caixa_do_popup(inp):
    """Se `inp` esta num popup, devolve a caixa (filha do conteudo do Popup)."""
    for pop in list(Window.children):
        if not isinstance(pop, Popup):
            continue
        conteudo = pop.content
        w = inp
        # para na janela e nunca passa de 60 niveis: a janela pode ser pai de
        # si mesma, e o laco antigo ficava preso para sempre (o app congelava
        # quando o teclado abria enquanto um aviso ainda fechava)
        for _ in range(60):
            pai = getattr(w, 'parent', None)
            if pai is None or pai is w or w is Window:
                break
            if pai is conteudo:
                return w
            w = pai
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
            if caixa.height < Window.height - dp(18) - kb.height:
                iy = cy0                      # cabe inteira: sobe a caixa toda
        topo_kb = kb.height                   # (ele termina com y = 0)
        falta = (topo_kb + dp(12)) - iy
        if falta <= 0:
            return
        if caixa is not None:
            _, cy = caixa.to_window(caixa.x, caixa.y)
            topo_max = Window.height - dp(6)
            novo_cy = cy + falta + caixa.height / 2.0
            novo_cy = min(novo_cy, topo_max - caixa.height / 2.0) if caixa.height < topo_max - kb.height else novo_cy
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
        ref[0] = None              # ja livre: tocar no campo durante a descida reabre na hora
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

        # bind() devolve None: encadear .bind(...).start(...) derrubava o app
        # toda vez que o teclado fechava (OK, toque fora, popup fechando)
        _Anim.cancel_all(kb)
        anim = _Anim(opacity=0, y=-kb.height * 0.35, duration=0.14, transition='in_cubic')
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
            kb.pos     = ((Window.width - larg) / 2.0, -kb.height * 0.5)
            kb.opacity = 0
            Window.add_widget(kb)
            ref[0] = kb
            _Anim(opacity=1, y=0, duration=0.20, transition='out_cubic').start(kb)
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


def popup_pedir_xp(nome: str, quantidade: int, on_save, titulo=">> LOTE DETECTADO",
                   pergunta="Valor de XP por peça:"):
    pop, layout = _make_popup()
    h = min(dp(318), int(Window.height * 0.6))
    caixa = BoxLayout(
        orientation='vertical', padding=[dp(24), dp(18), dp(24), dp(18)],
        spacing=dp(10), size_hint=(0.88, None), height=h)
    aplicar_fundo_holografico(caixa, (0.55, 0.05, 0.95, 0.9))

    lbl_titulo = Label(
        text=f"[b]{titulo}[/b]", markup=True, font_name="orbitron.ttf", font_size="13sp",
        color=(0.72, 0.45, 1.0, 1), halign="center", size_hint_y=None, height=dp(22))
    lbl_info = Label(
        text=(f"[color=#00e5ff][b]{nome}[/b][/color]  [color=#8c96aa]× {quantidade} un.[/color]\n"
              f"[size=14sp][color=#aab4c8]{pergunta}[/color][/size]"),
        markup=True, font_name="rajdhani.ttf", font_size="18sp", shorten=False,
        halign="center", valign="middle", size_hint_y=None, height=dp(52))
    texto_que_cabe(lbl_info, caixa)

    inp = InputHolografico(
        input_filter='int', font_name="orbitron.ttf", font_size="30sp",
        background_color=(0, 0, 0, 0), foreground_color=(0, 0.9, 1, 1),
        cursor_color=(0, 0.9, 1, 1), halign="center",
        hint_text="ex.: 3", hint_text_color=(0.0, 0.9, 1.0, 0.22),
        size_hint_y=None, height=dp(60))

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

    for w in [lbl_titulo, lbl_info, inp, lbl_preview, btn]:  # o teclado sobe a caixa inteira
        caixa.add_widget(w)
    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    @uma_vez
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


def popup_editar_qtd(nome, qtd, xp_un, on_save):
    """Corrigir a quantidade de um lote (segurou o dedo nele)."""
    pop, layout = _make_popup()
    h = min(dp(290), int(Window.height * 0.52))
    caixa = BoxLayout(
        orientation='vertical', padding=[dp(26), dp(20), dp(26), dp(20)],
        spacing=dp(10), size_hint=(0.88, None), height=h)
    aplicar_fundo_holografico(caixa, (0.0, 0.85, 1.0, 0.9))
    lbl_info = Label(
        text=(f"[color=#00e5ff]>> CORRIGIR LOTE[/color]\n"
              f"[color=#00e5ff][b]{nome}[/b][/color]   [color=#555555]era {qtd} un.[/color]\n"
              f"[color=#444444]Quantidade certa:[/color]"),
        markup=True, font_name="orbitron.ttf", font_size="12sp",
        halign="center", size_hint_y=None, height=dp(72))
    texto_que_cabe(lbl_info, caixa)
    inp = InputHolografico(
        input_filter='int', font_name="orbitron.ttf", font_size="30sp",
        background_color=(0, 0, 0, 0), foreground_color=(0, 0.9, 1, 1),
        cursor_color=(0, 0.9, 1, 1), halign="center", text=str(qtd),
        size_hint_y=None, height=dp(64))
    lbl_preview = Label(markup=True, font_name="rajdhani.ttf", font_size="16sp",
                        halign="center", size_hint_y=None, height=dp(32))

    def _preview(inst, valor):
        try:
            q = max(0, int(valor or 0))
        except ValueError:
            q = 0
        lbl_preview.text = (f"XP DO LOTE:  [color=#00ff88][b]{int(round(xp_un * q))} XP[/b][/color]"
                            f"   [color=#555555](era {int(round(xp_un * qtd))})[/color]")
    inp.bind(text=_preview)
    _preview(inp, inp.text)
    btn = BotaoAngular(text=">>  CORRIGIR  <<", size_hint_y=None, height=dp(52))
    for w in [lbl_info, inp, lbl_preview, btn]:
        caixa.add_widget(w)
    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    @uma_vez
    def _confirmar(*_):
        try:
            q = int(inp.text or 0)
        except ValueError:
            q = 0
        pop.dismiss()
        on_save(q)
    btn.bind(on_release=_confirmar)
    inp.bind(on_text_validate=_confirmar)
    anexar_teclado(inp, 'numeros')
    _abrir_popup(caixa, pop)
    _bind_teclado(caixa, pop)


def ler_area_de_transferencia():
    """O texto que esta copiado no celular ('' se nao der para ler)."""
    try:
        from kivy.core.clipboard import Clipboard
        return Clipboard.paste() or ''
    except Exception as e:
        print(f"[colar] {e}")
        return ''


_DIAS_CURTOS = ('seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom')


def dia_curto(dia):
    """'05/10/2026' -> '05/10 (seg)'"""
    try:
        d = datetime.strptime(dia, "%d/%m/%Y")
        return f"{d.strftime('%d/%m')} ({_DIAS_CURTOS[d.weekday()]})"
    except ValueError:
        return dia


def popup_importar_zap(itens, on_confirm):
    """O que foi achado no texto copiado do WhatsApp, separado por dia.
    Tocar numa peça tira (ou devolve) ela. on_confirm(itens que ficaram)."""
    import importar_zap
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.gridlayout import GridLayout
    pop, layout = _make_popup()
    alt = min(int(dp(610)), int(Window.height * 0.86))
    caixa = BoxLayout(orientation='vertical', padding=[dp(16), dp(14), dp(16), dp(14)], spacing=dp(8),
                      size_hint=(0.92, None), height=alt)
    aplicar_fundo_holografico(caixa, (0.15, 0.95, 0.5, 0.9))
    caixa.add_widget(Label(
        text="[b][color=#3dff8f]>>  COLADO DO WHATSAPP[/color][/b]", markup=True, font_name="orbitron.ttf",
        font_size="14sp", size_hint_y=None, height=dp(28), halign="center"))
    lbl_resumo = Label(markup=True, font_name="rajdhani.ttf", font_size="17sp", size_hint_y=None,
                       height=dp(26), halign="center", valign="middle")
    caixa.add_widget(lbl_resumo)
    caixa.add_widget(Label(
        text="[color=#6f7a92]Toque numa peça para tirar da lista.[/color]", markup=True,
        font_name="rajdhani.ttf", font_size="13sp", size_hint_y=None, height=dp(18), halign="center"))
    rolagem = ScrollView(bar_width=dp(3))
    grade = GridLayout(cols=1, size_hint_y=None, spacing=dp(5), padding=[0, dp(2), 0, dp(2)])
    grade.bind(minimum_height=grade.setter('height'))
    rolagem.add_widget(grade)
    caixa.add_widget(rolagem)
    ativos = [True] * len(itens)
    cabecas = []                                   # (label, [indices])
    varios = len({it.get('quem', '') for it in itens}) > 1

    def _resumo():
        vivos = [it for i, it in enumerate(itens) if ativos[i]]
        dias = len({it['dia'] for it in vivos})
        pecas = sum(it['qtd'] for it in vivos)
        lbl_resumo.text = (f"[color=#aab4c8]{len(vivos)} {'lote' if len(vivos) == 1 else 'lotes'} em "
                           f"{dias} {'dia' if dias == 1 else 'dias'}[/color]   "
                           f"[color=#00e5ff][b]{fmt_br(pecas)} un.[/b][/color]")
        for lbl, dia, idxs in cabecas:
            tot = sum(itens[i]['qtd'] for i in idxs if ativos[i])
            lbl.text = (f"[color=#3dff8f]{dia_curto(dia)}[/color]"
                        f"   [color=#6f7a92]{fmt_br(tot)} un.[/color]")

    def _texto(i):
        it = itens[i]
        quem = f"   [color=#6f7a92]{it['quem'][:12]}[/color]" if varios and it.get('quem') else ""
        nome = it['nome'] if len(it['nome']) <= 24 else it['nome'][:23] + "…"
        if ativos[i]:
            return f"  {nome}   [color=#00ff88]{fmt_br(it['qtd'])} un.[/color]{quem}"
        return f"  [color=#4a5068][s]{nome}   {fmt_br(it['qtd'])} un.[/s]   (fora)[/color]"

    def _alternar(btn, i):
        ativos[i] = not ativos[i]
        btn.text = _texto(i)
        btn.cor_borda = [0.0, 0.85, 1.0, 0.85] if ativos[i] else [0.25, 0.28, 0.4, 0.5]
        try:
            import tatil
            tatil.tecla()
        except Exception:
            pass
        _resumo()

    pos = {id(it): i for i, it in enumerate(itens)}
    for dia, grupo in importar_zap.por_dia(itens):
        idxs = [pos[id(it)] for it in grupo]
        cab = Label(markup=True, font_name="orbitron.ttf", font_size="11sp", size_hint_y=None, height=dp(24),
                    halign="left", valign="bottom")
        cab.bind(size=lambda i, s: setattr(i, 'text_size', s))
        grade.add_widget(cab)
        cabecas.append((cab, dia, idxs))
        for i in idxs:
            b = ListaItem(text=_texto(i), font_size="15sp")
            b.height = dp(42)
            b.bind(on_release=lambda inst, i=i: _alternar(inst, i))
            grade.add_widget(b)
    _resumo()

    botoes = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(12))
    btn_ok = BotaoAngular(text=">>  CONTINUAR", size_hint_x=0.6)
    btn_ok.cor_borda = btn_ok.cor_borda_kv = [0, 1, 0.55, 0.9]
    btn_ok.cor_texto = [0, 1, 0.55, 1]
    btn_nao = BotaoAngular(text="CANCELAR", size_hint_x=0.4)
    botoes.add_widget(btn_ok)
    botoes.add_widget(btn_nao)
    caixa.add_widget(botoes)
    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
    feito = [False]

    def _continuar(*_):
        vivos = [it for i, it in enumerate(itens) if ativos[i]]
        if not vivos:
            tremer_widget(btn_ok)
            return
        if feito[0]:
            return
        feito[0] = True
        pop.dismiss()
        on_confirm(vivos)

    btn_ok.bind(on_release=_continuar)
    btn_nao.bind(on_release=lambda *_: pop.dismiss())
    _abrir_popup(caixa, pop)


def popup_aviso(texto, cor='#00e5ff', titulo=None):
    """Aviso curto com um OK."""
    pop, layout = _make_popup()
    linhas = texto.count('\n') + 1
    caixa = BoxLayout(orientation='vertical', padding=[dp(22), dp(18), dp(22), dp(18)], spacing=dp(12),
                      size_hint=(0.86, None), height=dp(132) + dp(22) * linhas + (dp(26) if titulo else 0))
    aplicar_fundo_holografico(caixa, (0, 0.9, 1, 0.9))
    if titulo:
        caixa.add_widget(Label(text=f"[b][color={cor}]{titulo}[/color][/b]", markup=True,
                               font_name="orbitron.ttf", font_size="13sp", size_hint_y=None, height=dp(26),
                               halign="center"))
    lbl = Label(text=f"[color=#c8d2e6]{texto}[/color]", markup=True, font_name="rajdhani.ttf", font_size="16sp",
                halign="center", valign="middle")
    texto_que_cabe(lbl, caixa)
    caixa.add_widget(lbl)
    btn = BotaoAngular(text=">>  OK", size_hint_y=None, height=dp(50))
    btn.bind(on_release=lambda *_: pop.dismiss())
    caixa.add_widget(btn)
    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
    _abrir_popup(caixa, pop)


def _sem_emoji(t):
    """Tira o simbolo do comeco (as fontes do app nao tem os emojis)."""
    t = str(t).strip()
    while t and not t[0].isalnum():
        t = t[1:].strip()
    return t


def popup_avisos(app):
    """Painel do botao AVISOS do menu: liga/desliga, mostra o que pode estar
    impedindo os avisos NO PROPRIO CELULAR (permissao, notificacoes do app,
    o recebedor), os proximos avisos e um TESTE pelo mesmo caminho dos
    avisos de verdade (AlarmManager -> recebedor -> barra)."""
    import lembretes
    pop, layout = _make_popup()
    alt = min(dp(560), int(Window.height * 0.9))
    caixa = BoxLayout(orientation='vertical', padding=[dp(20), dp(16), dp(20), dp(16)], spacing=dp(8),
                      size_hint=(0.92, None), height=alt)
    aplicar_fundo_holografico(caixa, (0, 0.9, 1, 0.9))
    caixa.add_widget(Label(text="[b]>>  AVISOS NA BARRA  <<[/b]", markup=True, font_name="orbitron.ttf",
                           font_size="14sp", color=(0, 0.9, 1, 1), size_hint_y=None, height=dp(26),
                           halign="center"))

    def rotulo(tam, alt_, valign='top'):
        l = Label(text='', markup=True, font_name="rajdhani.ttf", font_size=tam, halign="left", valign=valign,
                  size_hint_y=None, height=alt_)
        l.bind(size=lambda i, s: setattr(i, 'text_size', s))
        caixa.add_widget(l)
        return l
    lbl_estado = rotulo("15sp", dp(122))
    caixa.add_widget(Label(text="[b]PRÓXIMOS AVISOS[/b]", markup=True, font_name="orbitron.ttf", font_size="10sp",
                           color=(0, 0.9, 1, 0.75), size_hint_y=None, height=dp(18), halign="left",
                           text_size=(Window.width * 0.8, None)))
    lbl_prox = rotulo("15sp", dp(70))
    lbl_teste = rotulo("14sp", dp(92), valign='middle')

    def ok(v, sim, nao, cinza="não deu para conferir"):
        if v is None:
            return f"[color=#7f8aa3]{cinza}[/color]"
        return f"[color=#00ff88]{sim}[/color]" if v else f"[color=#ff4466][b]{nao}[/b][/color]"

    def atualizar(*_):
        e = lembretes.estado()
        ligado = bool(getattr(app, 'lembretes', True))
        linhas = ["[color=#aab4c8]Avisos do app:[/color]  "
                  + ("[color=#00ff88]LIGADOS[/color]" if ligado else "[color=#ff4466][b]DESLIGADOS[/b][/color]")]
        if not e['android']:
            linhas.append("[color=#7f8aa3]No computador não há avisos: só no celular.[/color]")
        else:
            linhas.append("[color=#aab4c8]Permissão do Android:[/color]  " + ok(e['permissao'], "OK", "BLOQUEADA"))
            linhas.append("[color=#aab4c8]Notificações do app:[/color]  "
                          + ok(e['ativadas'], "ligadas", "DESLIGADAS"))
            linhas.append("[color=#aab4c8]Recebedor dos avisos:[/color]  "
                          + ok(e['recebedor'], "OK", "FALTANDO"))
            linhas.append("[color=#aab4c8]Horário exato:[/color]  "
                          + ok(e.get('exato'), "OK", "NÃO LIBERADO", "aproximado"))
            if e['erro']:
                linhas.append(f"[color=#7f8aa3]{e['erro']}[/color]")
        lbl_estado.text = "\n".join(linhas)
        prox = lembretes.proximos(app) if ligado else []
        if not ligado:
            lbl_prox.text = "[color=#7f8aa3]Desligados: nenhum aviso agendado.[/color]"
        elif not prox:
            lbl_prox.text = "[color=#7f8aa3]Nenhum agora (tudo em dia). O próximo entra quando houver.[/color]"
        else:
            lbl_prox.text = "\n".join(f"[color=#00e5ff][b]{q}[/b][/color]  [color=#c8d2e6]{_sem_emoji(t)}[/color]"
                                      for q, t in prox[:4])
        b_liga.text = ">>  DESLIGAR" if ligado else ">>  LIGAR"
        return e

    res = {'direto': None, 'agendado': None}

    def mostra_teste():
        def linha(n, nome, v):
            if v is None:
                return f"[color=#7f8aa3]{n}) {nome}: conferindo...[/color]"
            if v is True:
                return f"[color=#00ff88]{n}) {nome}: [b]apareceu[/b][/color]"
            return f"[color=#ff4466]{n}) {nome}: [b]não apareceu[/b][/color]"
        txt = linha(1, "Aviso direto", res['direto']) + "\n" + linha(2, "Aviso agendado", res['agendado'])
        if res['direto'] is False:
            txt += ("\n[color=#c8d2e6]O celular está escondendo os avisos do app: toque em CONFIGURAÇÕES "
                    "e ligue as notificações.[/color]")
        elif res['direto'] and res['agendado'] is False:
            txt += ("\n[color=#c8d2e6]O Android está segurando os agendados: em CONFIGURAÇÕES > Bateria, "
                    "deixe o app [b]Sem restrições[/b].[/color]")
        elif res['direto'] and res['agendado']:
            txt += "\n[color=#00ff88]Tudo certo: os lembretes vão chegar na hora.[/color]"
        lbl_teste.text = txt

    def testar(*_):
        lembretes.pedir_permissao()
        e1, e2 = lembretes.testar(5)
        if e1 and e2 and e1 == e2:
            lbl_teste.text = f"[color=#ffcc00]{e1}[/color]"
            return
        res['direto'] = False if e1 else None
        res['agendado'] = False if e2 else None
        mostra_teste()

        def confere_direto(dt):
            if res['direto'] is None:
                v = lembretes.apareceu(lembretes.ID_TESTE_DIRETO)
                res['direto'] = True if v is None else bool(v)
            atualizar()
            mostra_teste()

        def confere_agendado(dt):
            if res['agendado'] is None:
                v = lembretes.apareceu(lembretes.ID_TESTE)
                if v is None:
                    lbl_teste.text += "\n[color=#c8d2e6]Confira a barra: o teste 2 apareceu?[/color]"
                    return
                res['agendado'] = bool(v)
            mostra_teste()
        Clock.schedule_once(confere_direto, 2.0)
        Clock.schedule_once(confere_agendado, 14.0)

    def ligar(*_):
        app.alternar_lembretes()
        atualizar()

    l1 = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
    b_teste = BotaoAngular(text=">>  TESTAR AGORA", font_size="12sp", cor_borda=[0, 1, 0.55, 0.9],
                           cor_borda_kv=[0, 1, 0.55, 0.9], cor_texto=[0, 1, 0.55, 1])
    b_liga = BotaoAngular(text=">>  DESLIGAR", font_size="12sp")
    b_teste.bind(on_release=testar)
    b_liga.bind(on_release=ligar)
    l1.add_widget(b_teste)
    l1.add_widget(b_liga)
    l2 = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
    b_cfg = BotaoAngular(text="CONFIGURAÇÕES", font_size="12sp", cor_borda=[1, 0.8, 0, 0.9],
                         cor_borda_kv=[1, 0.8, 0, 0.9], cor_texto=[1, 0.85, 0.2, 1])
    b_fechar = BotaoAngular(text="FECHAR", font_size="12sp")
    b_cfg.bind(on_release=lambda *_: lembretes.abrir_config())
    b_fechar.bind(on_release=lambda *_: pop.dismiss())
    l2.add_widget(b_cfg)
    l2.add_widget(b_fechar)
    caixa.add_widget(Widget())
    caixa.add_widget(l1)
    caixa.add_widget(l2)
    lbl_teste.text = ("[color=#7f8aa3]TESTAR AGORA manda 2 avisos: um na hora (direto) e outro "
                      "agendado para 5 segundos depois.[/color]")
    atualizar()
    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
    _abrir_popup(caixa, pop)
    return pop


def popup_confirmar(pergunta, on_sim, sim=">>  SIM", nao="CORRIGIR", titulo="CONFERE?"):
    """Pergunta curta com dois botoes (no estilo do app): sim segue, nao volta."""
    pop, layout = _make_popup()
    caixa = BoxLayout(orientation='vertical', padding=[dp(22), dp(18), dp(22), dp(18)], spacing=dp(12),
                      size_hint=(0.86, None), height=dp(220))
    aplicar_fundo_holografico(caixa, (1, 0.8, 0, 0.9))
    caixa.add_widget(Label(text=f"[b][color=#ffcc00]{titulo}[/color][/b]", markup=True, font_name="orbitron.ttf",
                           font_size="13sp", size_hint_y=None, height=dp(26), halign="center"))
    lbl = Label(text=f"[color=#c8d2e6]{pergunta}[/color]", markup=True, font_name="rajdhani.ttf", font_size="17sp",
                halign="center", valign="middle")
    texto_que_cabe(lbl, caixa)
    caixa.add_widget(lbl)
    bts = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(12))
    b_nao = BotaoAngular(text=nao)
    b_sim = BotaoAngular(text=sim, cor_borda=[0, 1, 0.55, 0.9], cor_borda_kv=[0, 1, 0.55, 0.9],
                         cor_texto=[0, 1, 0.55, 1])
    b_nao.bind(on_release=lambda *_: pop.dismiss())
    b_sim.bind(on_release=uma_vez(lambda *_: (pop.dismiss(), on_sim())))
    bts.add_widget(b_nao)
    bts.add_widget(b_sim)
    caixa.add_widget(bts)
    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
    _abrir_popup(caixa, pop)


def popup_delete_engracado(on_confirm, pergunta="Desintegrar este registro?", botao="DESINTEGRAR"):
    pop, layout = _make_popup()
    linhas = pergunta.count('\n')
    h = min(dp(196) + dp(20) * linhas, int(Window.height * 0.42))
    caixa = BoxLayout(
        orientation='vertical', padding=[dp(26), dp(20), dp(26), dp(20)],
        spacing=dp(14), size_hint=(0.84, None), height=h)
    aplicar_fundo_holografico(caixa, (1.0, 0.08, 0.22, 0.9))

    caixa.add_widget(texto_que_cabe(Label(
        text=("[color=#ff2244]!!  ATENÇÃO[/color]\n"
              f"[color=#cccccc]{pergunta}\n"
              "Esta ação é irreversível.[/color]"),
        markup=True, font_name="orbitron.ttf", font_size="13sp",
        halign="center", size_hint_y=None, height=dp(74) + dp(20) * linhas), caixa))

    botoes  = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(14))
    btn_sim = BotaoAngularAlerta(text=botao)
    btn_nao = BotaoAngular(text="CANCELAR")
    botoes.add_widget(btn_sim)
    botoes.add_widget(btn_nao)
    caixa.add_widget(botoes)
    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    @uma_vez
    def _confirmar(*_):
        pop.dismiss()
        on_confirm()

    btn_sim.bind(on_release=_confirmar)
    btn_nao.bind(on_release=lambda *_: pop.dismiss())
    _abrir_popup(caixa, pop)


def tremer_widget(w, forca=None, dur=0.34):
    """Balanca so esse widget de um lado para o outro (campo com erro)."""
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
    """Campo de data com o teclado de numeros: as barras entram sozinhas
    (29092026 -> 29/09/2026) e o apagar tira um numero de cada vez."""
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
    """'dd/mm/aaaa' -> (datetime, None) ou (None, motivo em portugues)."""
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
    """Menu: troca a senha do app. So a 'impressao digital' fica guardada
    (seguranca.py); errar a senha atual conta como erro de senha."""
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
    texto_que_cabe(lbl_status, caixa)
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


def popup_resumo_dia(tot_pecas, tot_xp, on_confirm, dias=None, pede_data=True):
    """dias = [(dia 'dd/mm/aaaa', pecas)] das peças que ja tem dia (coladas do
    WhatsApp): cada dia vira um turno separado. pede_data=False: nenhuma
    peça sem dia, o campo da data some."""
    pop, layout = _make_popup()
    dias = list(dias or [])
    mostra = dias[:6]
    extra_h = (dp(26) + dp(21) * (len(mostra) + (1 if len(dias) > len(mostra) else 0))) if dias else 0
    # dp() garante tamanho correto em qualquer densidade de tela
    alt = min(int(dp(400) + extra_h - (0 if pede_data else dp(92))), int(Window.height * 0.86))
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
                    f"[color=#00e5ff][b]{fmt_br(tot_pecas)} un.[/b][/color]\n\n"
                    f"[color=#888888]Experiência Obtida[/color]   "
                    f"[color=#00ff88][b]+{fmt_br(tot_xp)} XP[/b][/color]"),
              markup=True, font_name="rajdhani.ttf", font_size="18sp",
              halign="center", size_hint_y=None, height=dp(88)),
    ]:
        caixa.add_widget(w)
    if dias:
        linhas = [f"[color=#3dff8f]{dia_curto(d)}[/color]   [color=#00e5ff]{fmt_br(p)} un.[/color]"
                  for d, p in mostra]
        if len(dias) > len(mostra):
            resto = dias[len(mostra):]
            linhas.append(f"[color=#6f7a92]e mais {len(resto)} "
                          f"{'dia' if len(resto) == 1 else 'dias'} "
                          f"({fmt_br(sum(p for _, p in resto))} un.)[/color]")
        caixa.add_widget(Label(
            text=f"[color=#555555]{len(dias)} {'TURNO SEPARADO' if len(dias) == 1 else 'TURNOS SEPARADOS'} "
                 f"POR DIA:[/color]",
            markup=True, font_name="orbitron.ttf", font_size="10sp", halign="center", size_hint_y=None,
            height=dp(22)))
        caixa.add_widget(Label(
            text="\n".join(linhas), markup=True, font_name="rajdhani.ttf", font_size="15sp", halign="center",
            valign="middle", size_hint_y=None, height=dp(21) * len(linhas)))
    if pede_data:
        caixa.add_widget(Label(
            text=("[color=#555555]Data das peças sem dia:[/color]" if dias
                  else "[color=#555555]Data do turno:[/color]"),
            markup=True, font_name="orbitron.ttf", font_size="11sp",
            halign="center", size_hint_y=None, height=dp(22)))

    inp_data = InputHolografico(
        text=hoje.strftime("%d/%m/%Y"),
        font_name="orbitron.ttf", font_size="22sp",
        foreground_color=(0, 0.9, 1, 1), cursor_color=(0, 0.9, 1, 1),
        halign="center", size_hint_y=None, height=dp(58))
    formatar_data_digitada(inp_data)
    anexar_teclado(inp_data, 'numeros')
    lbl_aviso = Label(
        text="", markup=True, font_name="rajdhani.ttf", font_size="14sp",
        size_hint_y=None, height=dp(22), halign="center", valign="middle")
    texto_que_cabe(lbl_aviso, caixa)
    btn = BotaoAngular(text=">>  SALVAR TURNO  <<", size_hint_y=None, height=dp(52))
    # o campo vem antes do botao: o teclado sobe a caixa inteira
    if pede_data:
        caixa.add_widget(inp_data)
    caixa.add_widget(lbl_aviso)
    caixa.add_widget(btn)

    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

    salvo = [False]

    def _confirmar(*_):
        if salvo[0]:                      # toque duplo: o turno ja foi salvo
            return
        d, motivo = ler_data(inp_data.text) if pede_data else (hoje, None)
        if d is None:                     # antes virava 'hoje' sem avisar
            lbl_aviso.text = f"[color=#ff4455]{motivo}[/color]"
            try:
                import tatil
                tatil.erro()
            except Exception:
                pass
            tremer_widget(inp_data)
            return
        salvo[0] = True
        data_str = f"{d.strftime('%d/%m/%Y')}  {hoje.strftime('%H:%M')}"
        pop.dismiss()
        on_confirm(data_str)

    inp_data.bind(text=lambda *_: setattr(lbl_aviso, 'text', ''))

    btn.bind(on_release=_confirmar)
    inp_data.bind(on_text_validate=_confirmar)
    _abrir_popup(caixa, pop)
    _bind_teclado(caixa, pop)
    # auto-focus removido — teclado sobe só quando usuario toca no campo)

def popup_meta_producao():
    """O painel da META DE PRODUCAO (aberto pela faixa HOJE do Registro):
    hoje x meta do dia, o ritmo comparado com 60/h e 90/h, quanto tempo falta
    e a semana com as faixas de pagamento."""
    import metas
    from efeitos import BarraMeta
    app = App.get_running_app()
    cfg = metas.completar_cfg(app.config_ganhos)
    hoje = datetime.now().date()
    sem, hj = metas.pecas_da_semana(app.memorias, app.registros, hoje)
    prox = metas.proxima_faixa(sem, cfg)
    alvo = prox['inicio'] if prox else int(cfg['meta_bonus'])
    md = metas.meta_diaria(alvo, sem, hj, hoje, cfg['pecas_sabado'])
    r = metas.ritmo(metas.lotes_de_hoje(app.registros, hoje))
    fx = metas.faixas(cfg)
    _i, _ini, valor_agora, _nm = metas.faixa_de(sem, cfg)

    pop, layout = _make_popup()
    caixa = BoxLayout(orientation='vertical', padding=[dp(20), dp(16), dp(20), dp(16)], spacing=dp(8),
                      size_hint=(0.92, None), height=min(dp(560), Window.height * 0.86))
    aplicar_fundo_holografico(caixa, (0, 0.9, 1, 0.9))

    def titulo(t, cor='#00e5ff'):
        caixa.add_widget(Label(text=f"[b][color={cor}]{t}[/color][/b]", markup=True, font_name="orbitron.ttf",
                               font_size="12sp", size_hint_y=None, height=dp(22), halign="center"))

    def texto(t, alt=dp(40), tam="15sp"):
        lbl = Label(text=t, markup=True, font_name="rajdhani.ttf", font_size=tam, halign="center",
                    valign="middle", size_hint_y=None, height=alt)
        texto_que_cabe(lbl, caixa)
        caixa.add_widget(lbl)
        return lbl

    caixa.add_widget(Label(text="[b][color=#00e5ff]>>  META DE PRODUÇÃO  <<[/color][/b]", markup=True,
                           font_name="orbitron.ttf", font_size="15sp", size_hint_y=None, height=dp(30),
                           halign="center"))
    # ── hoje ──
    titulo("HOJE")
    barra_h = BarraMeta(size_hint_y=None, height=dp(30))
    caixa.add_widget(barra_h)
    if hoje.weekday() == 6:
        texto("[color=#8c96aa]Domingo é folga. A conta da semana começa amanhã.[/color]")
    elif md['batida'] and prox is None:
        texto("[color=#ffcc00]Você já está na faixa mais alta da semana![/color]")
    else:
        if md['hoje_falta'] > 0:
            linha = (f"[color=#c8d2e6]Saíram [b]{fmt_br(hj)}[/b] de [b]{fmt_br(md['hoje_meta'])}[/b]  ·  "
                     f"faltam [color=#00e5ff][b]{fmt_br(md['hoje_falta'])}[/b][/color][/color]")
        else:
            linha = f"[color=#00ff88][b]{fmt_br(hj)}[/b] peças  ·  META DE HOJE BATIDA![/color]"
        texto(linha)
    meta_h = max(1, md['hoje_meta'], hj)
    barra_h.definir(hj, maximo=meta_h * 1.15,
                    marcas=[(md['hoje_meta'], f"META {fmt_br(md['hoje_meta'])}", (1, 0.88, 0.1, 1))]
                    if md['hoje_meta'] else [],
                    cor=(0, 1, 0.55, 1) if hj >= md['hoje_meta'] > 0 else (0, 0.9, 1, 1))
    # ── ritmo ──
    titulo("RITMO")
    barra_r = BarraMeta(size_hint_y=None, height=dp(30))
    caixa.add_widget(barra_r)
    if r:
        cor_r = (0, 1, 0.55, 1) if r >= metas.REF_REALISTA else ((1, 0.8, 0, 1) if r >= 45 else (1, 0.4, 0.4, 1))
        barra_r.definir(r, maximo=110, cor=cor_r,
                        marcas=[(metas.REF_REALISTA, "60/h  1 por min", (1, 0.88, 0.1, 1)),
                                (metas.REF_PADRAO, "90/h  padrão 40s", (1, 0.42, 0.3, 1))])
        lin = f"[color=#c8d2e6]Você está a [b]{int(round(r))} peças/h[/b][/color]"
        if md['hoje_falta'] > 0:
            f = md['hoje_falta']
            lin += (f"\n[color=#9aa6bd]Faltam {fmt_br(f)}: [b]~{metas.tempo_txt(f / r)}[/b] nesse ritmo  ·  "
                    f"{metas.tempo_txt(f / 60.0)} a 60/h  ·  {metas.tempo_txt(f / 90.0)} a 90/h[/color]")
        texto(lin, alt=dp(68), tam="14sp")
    else:
        barra_r.definir(0, maximo=110, marcas=[(60, "60/h", (1, 0.88, 0.1, 1)), (90, "90/h", (1, 0.42, 0.3, 1))],
                        animar=False)
        texto("[color=#8c96aa]Lance mais um lote (com uns 15 min de diferença)\npara medir o seu ritmo de hoje.[/color]",
              alt=dp(44), tam="14sp")
    # ── semana ──
    titulo("SEMANA  (seg a sáb)")
    barra_s = BarraMeta(size_hint_y=None, height=dp(30))
    caixa.add_widget(barra_s)
    topo = fx[-1][0]
    barra_s.definir(sem, maximo=topo * 1.12,
                    marcas=[(ini, f"R$ {fmt_br(v, 2)}", (1, 0.88, 0.1, 1) if k == len(fx) - 1 else (0, 1, 0.55, 1))
                            for k, (ini, v, _n) in enumerate(fx) if ini > 0],
                    cor=(1, 0.88, 0.1, 1) if prox is None else (0, 0.9, 1, 1))
    lin = (f"[color=#c8d2e6][b]{fmt_br(sem)}[/b] peças  ·  hoje valem [b]R$ {fmt_br(valor_agora, 2)}[/b]  ·  "
           f"[color=#00ff88]{'R$ ' + fmt_br(metas.ganho(sem, cfg), 2)}[/color][/color]")
    if prox:
        lin += (f"\n[color=#ffcc00]Faltam [b]{fmt_br(prox['falta'])}[/b] para os R$ {fmt_br(prox['valor'], 2)} "
                f"(+R$ {fmt_br(prox['a_mais'], 2)})[/color]")
        if md['e_sabado']:
            lin += "\n[color=#9aa6bd]É sábado: tudo isso hoje[/color]"
        elif md['por_dia'] > 0:
            # o sabado e so uma PREVISAO (meio periodo, ajustavel): nao conta como feito
            lin += (f"\n[color=#9aa6bd]{fmt_br(md['por_dia'])} por dia (contando ~{fmt_br(md['sabado'])} "
                    f"no sábado)[/color]")
        elif md['sabado'] > 0:
            lin += f"\n[color=#9aa6bd]Cabe no sábado (previsão ~{fmt_br(md['sabado'])})[/color]"
    texto(lin, alt=dp(70), tam="14sp")
    caixa.add_widget(Widget())
    btn = BotaoAngular(text=">>  OK", size_hint_y=None, height=dp(48))
    btn.bind(on_release=lambda *_: pop.dismiss())
    caixa.add_widget(btn)
    layout.add_widget(caixa)
    caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
    _abrir_popup(caixa, pop)
