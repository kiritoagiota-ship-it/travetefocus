"""
animacoes_ui.py — TraveteFocus
Animacoes de interface usadas por todas as telas:
  entrada_cascata(widgets)       itens/cards entram um depois do outro
  contar(label, ate, montar)     numero sobe contando ate o valor
  fmt_br(valor, casas)           1.234,56 (padrao brasileiro)
  aplicar_brilho_toque(botao)    pulso no contorno + faixa de luz varrendo
  pulso(widget)                  "batida" curta de escala
  deslizar(widgets, dy)          os itens saem de dy e escorregam ate o lugar (fecha buracos)
  entrada_tela(layout, pular)    os blocos da tela entram em cascata (todas as telas iguais)
  voar(w, dy)                    o widget chega de longe crescendo (ex.: conta indo pro historico)
  faixa_aviso(titulo, sub)       faixa HUD que abre, brilha e fecha (meta batida, faixa nova)
  brilho_texto(label)            reflexo de luz atravessando as letras de tempos em tempos
  luz_na_linha(linha)            ponto de luz correndo pela linha decorativa
  decifrar(label, final)         digitos rolando ate parar no numero certo
  EfeitoBordaAcesa               rolagem sem quique: a borda acende no fim da lista
  expandir_de(origem, l, a)      o item cresce ate virar o detalhe (Memorias)
  chamas_em_volta(label)         chamas de pixel subindo (sequencia de 5+ dias)
  icone_pixel(botao, nome)       icone de pixel art animado no botao (menu)
  tunel_link_start(centro, ...)  o tunel de aneis do Link Start (entrar no Registro)
  pacotes_de_luz(botao)          pacotes de luz correndo por dentro do botao
  corte_parte_tela(cor, ...)     troca de tela: a espada corta e a tela se parte
  deslize_voltar(...)            Voltar: a tela escorrega e some (mais leve)

Regras: nada de .bind(...).start(...) encadeado (bind devolve None) e nenhum
callback de Clock/Animation deixa excecao escapar.
"""
import math
import random

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import (Color, Line, Mesh, PushMatrix, PopMatrix,
                           Translate, Scale, Rectangle)
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.widget import Widget


# ═══════════════════════════════════════════════════════════════════
#  CASCATA
# ═══════════════════════════════════════════════════════════════════
def _matriz(w):
    """Translate/Scale proprios do widget (so visual: nao briga com o layout,
    que continua mandando no pos real). Criados uma vez e reaproveitados."""
    m = getattr(w, '_anim_ui_matriz', None)
    if m is None:
        push = PushMatrix()
        tr = Translate(0, 0)
        sc = Scale(1, 1, 1)
        w.canvas.before.insert(0, sc)
        w.canvas.before.insert(0, tr)
        w.canvas.before.insert(0, push)
        w.canvas.after.add(PopMatrix())
        m = (tr, sc)
        w._anim_ui_matriz = m

        def _origem(*_):
            # x/y direto: center_x/center_y tem cache e podem estar velhos aqui
            sc.origin = (w.x + w.width / 2.0, w.y + w.height / 2.0)
        w.bind(pos=_origem, x=_origem, y=_origem, size=_origem)
        _origem()
    return m


def entrada_cascata(widgets, atraso=0.045, dy=None, duracao=0.38,
                    escala=True, atraso_max=0.55, inicio=0.0):
    """Opacidade 0->1, sobe `dy` e cresce levemente, um item depois do outro.
    O atraso total e limitado a `atraso_max` (listas longas nao demoram).
    `inicio`: espera antes do primeiro (ex.: a lista espera o topo da tela)."""
    try:
        ws = [w for w in widgets if w is not None]
    except Exception:
        return
    if not ws:
        return
    if dy is None:
        dy = dp(22)
    passo = atraso if len(ws) * atraso <= atraso_max else atraso_max / float(len(ws))
    for i, w in enumerate(ws):
        try:
            _entrar(w, inicio + i * passo, dy, duracao, escala)
        except Exception as e:
            print(f"[anim_ui] cascata item ignorado: {e}")
            w.opacity = 1


def _entrar(w, espera, dy, duracao, escala):
    tr, sc = _matriz(w)
    ev_ant = getattr(w, '_anim_ui_ev', None)
    if ev_ant is not None:
        ev_ant.cancel()
    Animation.cancel_all(w, 'opacity')
    w.opacity = 0
    tr.y = -dy
    s0 = 0.94 if escala else 1.0
    sc.x = sc.y = s0

    def _comecar(dt):
        try:
            w._anim_ui_ev = None
            t0 = [0.0]

            def _passo(dt2):
                try:
                    t0[0] += dt2
                    k = min(1.0, t0[0] / duracao)
                    e = 1 - (1 - k) ** 3                      # out_cubic
                    ov = 1 + 2.2 * (k - 1) ** 3 + 1.2 * (k - 1) ** 2   # out_back leve
                    tr.y = -dy * (1 - e)
                    s = s0 + (1 - s0) * ov
                    sc.x = sc.y = s
                    w.opacity = min(1.0, e * 1.4)
                    if k >= 1:
                        tr.y = 0
                        sc.x = sc.y = 1
                        w.opacity = 1
                        return False
                except Exception as ex:
                    print(f"[anim_ui] cascata frame: {ex}")
                    tr.y = 0
                    sc.x = sc.y = 1
                    w.opacity = 1
                    return False
            Clock.schedule_interval(_passo, 1 / 60.)
        except Exception as ex:
            print(f"[anim_ui] cascata: {ex}")
            w.opacity = 1

    w._anim_ui_ev = Clock.schedule_once(_comecar, espera)


# ═══════════════════════════════════════════════════════════════════
#  NUMEROS CONTANDO
# ═══════════════════════════════════════════════════════════════════
def fmt_br(valor, casas=0):
    """1234567.891 -> '1.234.567,89' (casas=2)."""
    try:
        s = f"{float(valor):,.{casas}f}"
    except (TypeError, ValueError):
        return str(valor)
    return s.replace(',', '#').replace('.', ',').replace('#', '.')


def contar(label, ate, montar, de=0, duracao=0.9, inteiro=True, atraso=0.0):
    """Anima um numero de `de` ate `ate`, escrevendo label.text = montar(v)
    a cada quadro. O texto final e SEMPRE montar(ate) (valor exato)."""
    ev_ant = getattr(label, '_anim_ui_contar', None)
    if ev_ant is not None:
        ev_ant.cancel()
        label._anim_ui_contar = None
    try:
        de = float(de)
        ate_f = float(ate)
    except (TypeError, ValueError):
        label.text = montar(ate)
        return
    if de == ate_f or duracao <= 0:
        label.text = montar(ate)
        return
    t = [-float(atraso)]

    def _passo(dt):
        try:
            t[0] += dt
            if t[0] < 0:
                return True
            k = min(1.0, t[0] / duracao)
            e = 1 - (1 - k) ** 4                               # out_quart
            v = de + (ate_f - de) * e
            if k >= 1:
                label.text = montar(ate)
                label._anim_ui_contar = None
                return False
            label.text = montar(int(round(v)) if inteiro else v)
        except Exception as ex:
            print(f"[anim_ui] contar: {ex}")
            try:
                label.text = montar(ate)
            except Exception:
                pass
            label._anim_ui_contar = None
            return False

    label.text = montar(int(de) if inteiro else de)
    label._anim_ui_contar = Clock.schedule_interval(_passo, 1 / 60.)


# ═══════════════════════════════════════════════════════════════════
#  BRILHO NOS BOTOES
# ═══════════════════════════════════════════════════════════════════
_TEX_FAIXA_LUZ = None


def _textura_faixa_luz():
    """Faixa horizontal: transparente nas bordas, clara no meio."""
    global _TEX_FAIXA_LUZ
    if _TEX_FAIXA_LUZ is None:
        n = 32
        buf = bytearray(n * 4 * 4)
        for x in range(n):
            u = x / (n - 1.0)
            a = max(0.0, 1 - abs(2 * u - 1))
            a = a * a * (3 - 2 * a)
            for y in range(4):
                i = (y * n + x) * 4
                buf[i] = buf[i + 1] = buf[i + 2] = 255
                buf[i + 3] = int(255 * a)
        dados = bytes(buf)
        tex = Texture.create(size=(n, 4), colorfmt='rgba')
        tex.wrap = 'clamp_to_edge'
        tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
        tex.add_reload_observer(
            lambda t: t.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte'))
        _TEX_FAIXA_LUZ = tex
    return _TEX_FAIXA_LUZ


def aplicar_brilho_toque(botao, cor=None):
    """Instala (uma vez) o brilho de toque: faixa de luz diagonal varrendo o
    botao da esquerda para a direita, recortada nos limites do botao, e um
    pulso no contorno que se expande e some. Disparado em on_press."""
    if getattr(botao, '_brilho_toque_ok', False):
        return
    botao._brilho_toque_ok = True
    try:
        with botao.canvas.after:
            c_faixa = Color(1, 1, 1, 0)
            m_faixa = Mesh(mode='triangle_fan', indices=[0, 1, 2, 3],
                           vertices=[0] * 16)
            c_pulso = Color(0, 0.9, 1, 0)
            l_pulso = Line(width=dp(1.4), close=True)
            c_pulso2 = Color(0, 0.9, 1, 0)
            l_pulso2 = Line(width=dp(1.1), close=True)
        try:
            m_faixa.texture = _textura_faixa_luz()
        except Exception as e:
            print(f"[anim_ui] textura do brilho: {e}")
    except Exception as e:
        print(f"[anim_ui] brilho nao instalado: {e}")
        return

    estado = {'ev': None, 't': 0.0}

    def _cor():
        if cor is not None:
            return cor
        cb = getattr(botao, 'cor_borda', None) or (0, 0.9, 1, 1)
        return (cb[0], cb[1], cb[2])

    def _frame(dt):
        try:
            estado['t'] += dt
            t = estado['t']
            x, y, w, h = botao.x, botao.y, botao.width, botao.height
            if w <= 0 or h <= 0:
                return True
            r, g, b = _cor()[:3]
            # faixa diagonal: dura 0.36s, atravessa de fora a fora
            k = min(1.0, t / 0.36)
            larg = max(dp(18), w * 0.22)
            incl = h * 0.45
            x0 = x - larg - incl + (w + 2 * larg + incl) * (1 - (1 - k) ** 2)

            def cx(v):                       # recorta nos limites do botao
                return min(max(v, x), x + w)
            vs = [cx(x0), y, 0, 0.5,
                  cx(x0 + larg), y, 1, 0.5,
                  cx(x0 + larg + incl), y + h, 1, 0.5,
                  cx(x0 + incl), y + h, 0, 0.5]
            m_faixa.vertices = vs
            c_faixa.rgba = (0.6 + 0.4 * r, 0.6 + 0.4 * g, 0.6 + 0.4 * b,
                            0.42 * math.sin(math.pi * k))
            # anel de luz no formato do botao (chanfrado): expande e some.
            # Nas teclas (calculadora, teclado) sao dois aneis, maiores.
            tecla = getattr(botao, 'tatil', '') == 'tecla'
            ch = min(dp(18), w / 3.0, h / 3.0)
            kp = min(1.0, t / 0.40)
            ex = (dp(12) if tecla else dp(7)) * (1 - (1 - kp) ** 3)
            l_pulso.points = _chanfro(x - ex, y - ex, w + 2 * ex, h + 2 * ex, ch + ex * 0.4)
            c_pulso.rgba = (min(1, r + 0.3), min(1, g + 0.3), min(1, b + 0.3), (0.8 if tecla else 0.55) * (1 - kp))
            kp2 = max(0.0, min(1.0, (t - 0.07) / 0.42)) if tecla else 1.0
            if tecla and 0 < kp2 < 1:
                ex2 = dp(20) * (1 - (1 - kp2) ** 3)
                l_pulso2.points = _chanfro(x - ex2, y - ex2, w + 2 * ex2, h + 2 * ex2, ch + ex2 * 0.4)
                c_pulso2.rgba = (r, g, b, 0.45 * (1 - kp2))
            else:
                c_pulso2.a = 0
            if k >= 1 and kp >= 1 and kp2 >= 1:
                c_faixa.a = 0
                c_pulso.a = 0
                c_pulso2.a = 0
                estado['ev'] = None
                return False
        except Exception as e:
            print(f"[anim_ui] brilho frame: {e}")
            c_faixa.a = 0
            c_pulso.a = 0
            c_pulso2.a = 0
            estado['ev'] = None
            return False

    def _disparar(*_):
        try:
            if estado['ev'] is not None:
                estado['ev'].cancel()
            estado['t'] = 0.0
            estado['ev'] = Clock.schedule_interval(_frame, 1 / 60.)
        except Exception as e:
            print(f"[anim_ui] brilho: {e}")
        return False              # nao consome o evento

    botao.fbind('on_press', _disparar)
    botao._brilho_disparar = _disparar

    def _parar(inst, parent):
        if parent is None and estado['ev'] is not None:
            estado['ev'].cancel()
            estado['ev'] = None
            c_faixa.a = 0
            c_pulso.a = 0
            c_pulso2.a = 0
    botao.fbind('parent', _parar)


def deslizar(widgets, dy, duracao=0.24):
    """Os widgets aparecem deslocados `dy` (o lugar de antes) e escorregam
    ate o lugar novo: a lista fecha o buraco de um item apagado em vez de
    pular (so visual: o layout ja esta no lugar certo)."""
    for w in widgets or ():
        try:
            tr, _sc = _matriz(w)
            ev = getattr(w, '_anim_ui_desliza', None)
            if ev is not None:
                ev.cancel()
            tr.y = dy
            t = [0.0]

            def _p(dt, tr=tr, w=w):
                try:
                    t[0] += dt
                    k = min(1.0, t[0] / duracao)
                    tr.y = dy * (1 - k) ** 3                  # out_cubic
                    if k >= 1:
                        tr.y = 0
                        w._anim_ui_desliza = None
                        return False
                except Exception:
                    tr.y = 0
                    return False
            w._anim_ui_desliza = Clock.schedule_interval(_p, 1 / 60.)
        except Exception as e:
            print(f"[anim_ui] deslizar: {e}")


def entrada_tela(layout, pular=()):
    """Os blocos de `layout` (de cima para baixo) entram em cascata curta
    quando a tela abre - o mesmo jeito em todas as telas. `pular` = widgets
    que tem a propria animacao (ex.: listas que ja entram item a item)."""
    try:
        blocos = [w for w in reversed(list(layout.children)) if w not in pular and w.opacity > 0]
        entrada_cascata(blocos, atraso=0.035, dy=dp(14), duracao=0.30, escala=False, atraso_max=0.28)
    except Exception as e:
        print(f"[anim_ui] entrada da tela: {e}")


# ═══════════════════════════════════════════════════════════════════
#  CARTAO QUE ABRE (Memorias: o item cresce ate virar o detalhe)
# ═══════════════════════════════════════════════════════════════════
def expandir_de(origem, larg, alt, on_fim=None, cor=(0.55, 0.1, 0.95), duracao=0.2):
    """Uma moldura chanfrada sai do retangulo de `origem` e cresce ate o
    tamanho (larg x alt) no meio da tela; ai chama on_fim (que abre o
    detalhe por cima) e some."""
    from kivy.core.window import Window
    from kivy.uix.widget import Widget
    feito = [False]

    def _fim():
        if not feito[0]:
            feito[0] = True
            if on_fim:
                try:
                    on_fim()
                except Exception as e:
                    print(f"[anim_ui] expandir fim: {e}")
    try:
        x0, y0 = origem.to_window(origem.x, origem.y)
        w0, h0 = origem.width, origem.height
        W, H = Window.size
        x1, y1 = (W - larg) / 2.0, (H - alt) / 2.0
        mold = Widget(size_hint=(None, None), size=(0, 0))
        with mold.canvas:
            c_f = Color(cor[0] * 0.12, cor[1] * 0.12, cor[2] * 0.12, 0.0)
            m_f = Mesh(mode='triangle_fan', indices=list(range(10)), vertices=[0] * 40)
            c_b = Color(cor[0], cor[1], cor[2], 1.0)
            l_b = Line(width=dp(1.4), close=True)
            c_l = Color(1, 1, 1, 0.0)
            l_l = Line(width=dp(1), close=True)
        Window.add_widget(mold)
    except Exception as e:
        print(f"[anim_ui] expandir: {e}")
        _fim()
        return
    t = [0.0]

    def _p(dt):
        try:
            t[0] += dt
            k = min(1.0, t[0] / duracao)
            e = 1 - (1 - k) ** 3
            x = x0 + (x1 - x0) * e
            y = y0 + (y1 - y0) * e
            w = w0 + (larg - w0) * e
            h = h0 + (alt - h0) * e
            c = dp(10) + dp(8) * e
            pts = _chanfro(x, y, w, h, c)
            vs = [x + w / 2.0, y + h / 2.0, 0, 0]
            for i in range(0, len(pts), 2):
                vs += [pts[i], pts[i + 1], 0, 0]
            vs += [pts[0], pts[1], 0, 0]
            m_f.vertices = vs
            c_f.a = 0.92 * e
            l_b.points = pts
            l_l.points = _chanfro(x + dp(4), y + dp(4), w - dp(8), h - dp(8), c - dp(3))
            c_l.a = 0.25 * e
            if k >= 1:
                _fim()
                # some por baixo do detalhe que ja abriu por cima
                Clock.schedule_once(lambda _d: Window.remove_widget(mold), 0.25)
                return False
        except Exception as ex:
            print(f"[anim_ui] expandir quadro: {ex}")
            try:
                Window.remove_widget(mold)
            except Exception:
                pass
            _fim()
            return False
    Clock.schedule_interval(_p, 1 / 60.)


# ═══════════════════════════════════════════════════════════════════
#  CHAMAS EM PIXEL (sequencia de 5+ dias no Progresso)
# ═══════════════════════════════════════════════════════════════════
def chamas_em_volta(alvo, forca=1.0):
    """Chamas de pixel subindo em volta de `alvo` (um Label) enquanto ele
    esta na tela: brasas que nascem embaixo, sobem tremendo e mudam de cor
    (amarelo -> laranja -> vermelho escuro) ate apagar. Devolve parar()."""
    import random
    from kivy.uix.widget import Widget
    cores = [(1.0, 0.95, 0.55), (1.0, 0.78, 0.2), (1.0, 0.5, 0.05), (0.85, 0.22, 0.04), (0.45, 0.08, 0.04)]
    w = Widget(size_hint=(None, None), size=(0, 0))
    grupos = []
    with w.canvas:
        for c in cores:
            cc = Color(c[0], c[1], c[2], 1)
            grupos.append((cc, []))
    pool = []
    estado = {'ev': None, 'acc': 0.0}
    u = max(2.0, round(dp(2.5)))

    def _quadro(dt):
        try:
            if alvo.get_root_window() is None:
                return True
            if w.parent is None:
                janela = alvo.get_root_window()
                janela.add_widget(w)
            x0, y0 = alvo.to_window(alvo.x, alvo.y)
            # largura do TEXTO (o label ocupa a linha toda): mede uma copia sem markup
            if estado.get('txt') != alvo.text:
                import re
                from kivy.core.text import Label as CoreLabel
                cl = CoreLabel(text=re.sub(r'\[/?[^\]]*\]', '', alvo.text), font_name=alvo.font_name,
                               font_size=alvo.font_size, bold=alvo.bold)
                cl.refresh()
                estado['txt'], estado['tam'] = alvo.text, tuple(cl.texture.size)
            tw, th = estado['tam']
            cx = x0 + alvo.width / 2.0
            base = y0 + (alvo.height - th) / 2.0                 # o pe das letras
            meia = tw / 2.0 + dp(6)
            estado['acc'] += dt * 55 * forca
            while estado['acc'] >= 1 and len(pool) < 70:
                estado['acc'] -= 1
                # mais brasas no meio do texto, menos nas pontas (forma de chama)
                dx = max(-meia, min(meia, random.gauss(0, meia * 0.5)))
                alta = 1.0 - abs(dx) / meia * 0.6
                # nasce no alto das letras e sobe (nao tapa o texto)
                pool.append([cx + dx, base + th * 0.85 + random.uniform(0, dp(3)),
                             random.uniform(dp(34), dp(70)) * alta, random.uniform(0.4, 0.9) * alta, 0.0,
                             random.uniform(0, 6.28)])
            vivos = []
            pontos = [[] for _ in cores]
            for p in pool:
                p[4] += dt
                if p[4] >= p[3]:
                    continue
                k = p[4] / p[3]
                p[1] += p[2] * dt
                xx = p[0] + math.sin(p[5] + p[4] * 9) * dp(2.5)
                ci = min(len(cores) - 1, int(k * len(cores)))
                tam = u * (2 if 0.15 < k < 0.4 else 1)
                pontos[ci].append((math.floor(xx / u) * u, math.floor(p[1] / u) * u, tam))
                vivos.append(p)
            pool[:] = vivos
            for (cc, rects), pts in zip(grupos, pontos):
                while len(rects) < len(pts):
                    r = Rectangle(pos=(0, 0), size=(0, 0))
                    w.canvas.insert(w.canvas.indexof(cc) + 1, r)
                    rects.append(r)
                for i, r in enumerate(rects):
                    if i < len(pts):
                        r.pos = (pts[i][0], pts[i][1])
                        r.size = (pts[i][2], pts[i][2])
                    else:
                        r.size = (0, 0)
        except Exception as e:
            print(f"[anim_ui] chamas: {e}")
            return False

    def parar():
        if estado['ev'] is not None:
            estado['ev'].cancel()
            estado['ev'] = None
        if w.parent is not None:
            w.parent.remove_widget(w)
    estado['ev'] = Clock.schedule_interval(_quadro, 1 / 60.)
    return parar


# ═══════════════════════════════════════════════════════════════════
#  ICONES EM PIXEL ANIMADOS (botoes do menu)
# ═══════════════════════════════════════════════════════════════════
_ICONES = {
    # cristal de memoria (roxo) com um reflexo descendo
    'memorias': [
        "....KK....",
        "...KbbK...",
        "..KbWbbK..",
        ".KbWbbbbK.",
        "KbWbbbbbBK",
        "KbbbbbbbBK",
        ".KbbbbbBK.",
        "..KbbbBK..",
        "...KbBK...",
        "....KK....",
    ],
    # estrela (ciano) que pisca
    'progresso': [
        "....KK....",
        "....KcK...",
        "...KccK...",
        "KKKKcWcKKK",
        "KccccWcccK",
        ".KcccccK..",
        "..KccccK..",
        ".KccKKccK.",
        ".KcK..KcK.",
        ".KK....KK.",
    ],
    # moeda (verde/ouro) - gira
    'ganhos': [
        "...KKKK...",
        "..KyyyyK..",
        ".KyYYYYyK.",
        "KyYYyyYYyK",
        "KyYyYYyYyK",
        "KyYyYYyYyK",
        "KyYYyyYYyK",
        ".KyYYYYyK.",
        "..KyyyyK..",
        "...KKKK...",
    ],
    # NerveGear (o capacete do Link Start): uma luz varre o visor
    'nervegear': [
        "...KKKKKK...",
        "..KmmmmmmK..",
        ".KmmnnnnmmK.",
        "KmmKKKKKKmmK",
        "KmKvvvvvvKmK",
        "KmKvvvvvvKmK",
        "KmmKKKKKKmmK",
        ".KnmmmmmmnK.",
        "..KKnnnnKK..",
        "....KKKK....",
    ],
    # >>> que acendem em sequencia
    'setas': [
        "v..v..v..",
        ".v..v..v.",
        "..v..v..v",
        ".v..v..v.",
        "v..v..v..",
    ],
    # calculadora (laranja) com o visor piscando
    'calculadora': [
        "KKKKKKKKK.",
        "KoooooooK.",
        "KoVVVVVoK.",
        "KoVVVVVoK.",
        "KoooooooK.",
        "KoWoWoWoK.",
        "KoooooooK.",
        "KoWoWoWoK.",
        "KoooooooK.",
        "KKKKKKKKK.",
    ],
}
_ICONE_CORES = {
    'K': (0.02, 0.02, 0.06), 'W': (1.0, 1.0, 1.0),
    'b': (0.62, 0.3, 1.0), 'B': (0.38, 0.12, 0.7),
    'c': (0.0, 0.88, 1.0),
    'y': (0.0, 0.62, 0.32), 'Y': (0.2, 1.0, 0.55),
    'o': (0.55, 0.3, 0.0), 'V': (1.0, 0.72, 0.0),
    'm': (0.52, 0.56, 0.7), 'n': (0.3, 0.32, 0.44), 'v': (0.0, 0.78, 1.0), 'z': (0.75, 1.0, 1.0),
    'e': (0.0, 0.26, 0.36),
}


def icone_pixel(botao, nome, u=None, margem=None, lado='esq', onde=None):
    """Um icone de pixel art animado no lado esquerdo (ou direito) do `botao`
    (30 quadros por segundo, so com o botao na tela). onde(ic) -> (x, y): um
    lugar proprio (ex.: o canto de cima dos cartoes do menu)."""
    from kivy.uix.widget import Widget
    mapa = _ICONES.get(nome)
    if mapa is None or getattr(botao, '_icone_ok_' + lado, False):
        return
    setattr(botao, '_icone_ok_' + lado, True)
    u = u or max(2.0, round(dp(2.2)))
    ic = Widget(size_hint=(None, None), size=(len(mapa[0]) * u, len(mapa) * u))
    grupos = {}
    with ic.canvas:
        for ch, c in _ICONE_CORES.items():
            grupos[ch] = (Color(c[0], c[1], c[2], 1), [])
        c_luz = Color(1, 1, 1, 0)
        r_luz = [Rectangle(pos=(0, 0), size=(0, 0)) for _ in range(3)]
    botao.add_widget(ic)
    estado = {'t': 0.0, 'q': -1}

    def _onde(*_):
        if onde is not None:
            x, y = onde(ic)
            ic.pos = (int(x), int(y))
            return
        m = margem if margem is not None else dp(26)
        x = botao.x + m if lado == 'esq' else botao.right - m - ic.width
        ic.pos = (int(x), int(botao.center_y - ic.height / 2.0))
    botao.bind(pos=_onde, size=_onde)
    _onde()

    def _pinta(pixels):
        usados = {ch: 0 for ch in grupos}
        for (gx, gy, ch, larg) in pixels:
            cc, rects = grupos[ch]
            i = usados[ch]
            if i >= len(rects):
                r = Rectangle(pos=(0, 0), size=(0, 0))
                ic.canvas.insert(ic.canvas.indexof(cc) + 1 + len(rects), r)
                rects.append(r)
            rects[i].pos = (ic.x + gx * u, ic.y + gy * u)
            rects[i].size = (u * larg, u)
            usados[ch] = i + 1
        for ch, (cc, rects) in grupos.items():
            for r in rects[usados[ch]:]:
                r.size = (0, 0)

    def _quadro(dt):
        try:
            if botao.get_root_window() is None:
                return True
            estado['t'] += dt
            t = estado['t']
            q = int(t * 30)
            if q == estado['q']:
                return True
            estado['q'] = q
            h = len(mapa)
            pix = []
            bob = 1 if (nome == 'memorias' and int(t * 2) % 2) else 0
            if nome == 'ganhos':
                # a moeda gira: a largura de cada linha encolhe e volta (|cos|)
                f = abs(math.cos(t * 2.6))
                f = max(0.18, round(f * 5) / 5.0)
                for j, linha in enumerate(mapa):
                    cheios = [i for i, ch in enumerate(linha) if ch != '.']
                    if not cheios:
                        continue
                    c0, c1 = cheios[0], cheios[-1]
                    meio = (c0 + c1 + 1) / 2.0
                    for i in range(c0, c1 + 1):
                        ch = linha[i]
                        if ch == '.':
                            continue
                        xi = int(round(meio + (i - meio) * f))
                        if f < 0.5 and ch not in 'Ky':
                            ch = 'y'                               # de lado: so a borda
                        pix.append((xi, h - 1 - j, ch, 1))
            else:
                for j, linha in enumerate(mapa):
                    for i, ch in enumerate(linha):
                        if ch == '.':
                            continue
                        if nome == 'calculadora' and ch == 'V' and int(t * 1.6) % 2:
                            ch = 'o' if (i + j) % 2 else 'V'       # o visor pisca
                        if nome == 'nervegear' and ch == 'v':
                            col = int(t * 14) % 18 - 2               # a luz varre o visor
                            if i in (col, col + 1):
                                ch = 'z'
                        if nome == 'setas' and ch == 'v':
                            if i // 3 != int(t * 7) % 4:             # uma seta acesa por vez
                                ch = 'e'
                        pix.append((i, h - 1 - j + bob, ch, 1))
            _pinta(pix)
            # brilho: uma faisca branca passa pelo icone a cada ~2,4 s
            ciclo = t % 2.4
            if ciclo < 0.3:
                k = ciclo / 0.3
                cx = ic.x + ic.width * k
                cy = ic.y + ic.height * (1 - k)
                c_luz.a = math.sin(math.pi * k)
                r_luz[0].pos, r_luz[0].size = (int(cx), int(cy)), (u, u)
                r_luz[1].pos, r_luz[1].size = (int(cx - u), int(cy)), (u, u)
                r_luz[2].pos, r_luz[2].size = (int(cx), int(cy + u)), (u, u)
                if nome == 'progresso':
                    c_luz.a = 1.0
            else:
                c_luz.a = 0
        except Exception as e:
            print(f"[anim_ui] icone {nome}: {e}")
            return False
    Clock.schedule_interval(_quadro, 1 / 60.)


# ═══════════════════════════════════════════════════════════════════
#  LINK START: o tunel de aneis coloridos (como no anime) ao entrar
# ═══════════════════════════════════════════════════════════════════
_CORES_TUNEL = [(0.0, 0.9, 1.0), (0.85, 0.25, 1.0), (1.0, 0.85, 0.2), (0.2, 1.0, 0.55),
                (0.3, 0.45, 1.0), (1.0, 0.38, 0.55), (0.75, 1.0, 1.0)]


def tunel_link_start(centro, on_meio=None, on_fim=None, dur=1.0):
    """Aneis coloridos nascem no botao e correm para fora cada vez mais rapido
    (perspectiva de tunel), riscos de velocidade passam pelas bordas, a tela
    vira um clarao branco - ai troca de tela (on_meio) - e o clarao se abre
    na tela nova. Segura o toque enquanto acontece."""
    from kivy.core.window import Window
    from kivy.uix.widget import Widget

    class _Tunel(Widget):
        def on_touch_down(self, touch):
            return True

        def on_touch_move(self, touch):
            return True

        def on_touch_up(self, touch):
            return True
    W, H = Window.size
    tn = _Tunel(size_hint=(None, None), size=(W, H), pos=(0, 0))
    n_aneis, n_riscos = 16, 36
    with tn.canvas:
        c_fundo = Color(0.0, 0.0, 0.04, 0)
        Rectangle(pos=(0, 0), size=(W, H))
        aneis = []
        for _ in range(n_aneis):
            c = Color(1, 1, 1, 0)
            l = Line(circle=(0, 0, 1), width=dp(1))
            aneis.append([c, l, -1.0, None])           # [cor, linha, nasceu_em, rgb]
        riscos = []
        for _ in range(n_riscos):
            c = Color(1, 1, 1, 0)
            l = Line(points=[0, 0, 0, 0], width=dp(1.2))
            riscos.append([c, l, random.uniform(0, 2 * math.pi), random.uniform(0.0, 1.0),
                           random.choice(_CORES_TUNEL)])
        c_flash = Color(1, 1, 1, 0)
        Rectangle(pos=(0, 0), size=(W, H))
    Window.add_widget(tn)
    estado = {'t': 0.0, 'prox': 0.0, 'cor': 0, 'meio': False}
    rmax = math.hypot(W, H) * 0.75
    T_FLASH0, T_MEIO, T_FLASH1 = 0.56, 0.68, 0.74
    try:
        import som
        som.tocar('transicao')
    except Exception:
        pass
    try:
        import tatil
        tatil.confirmar()
    except Exception:
        pass

    def _fim():
        try:
            Window.remove_widget(tn)
        except Exception:
            pass
        if on_fim:
            try:
                on_fim()
            except Exception as e:
                print(f"[anim_ui] tunel fim: {e}")

    def _q(dt):
        try:
            estado['t'] += dt
            t = estado['t']
            # o centro do tunel vai do botao para o meio da tela
            e = min(1.0, t / 0.45)
            e = e * e * (3 - 2 * e)
            cx = centro[0] + (W / 2.0 - centro[0]) * e
            cy = centro[1] + (H * 0.5 - centro[1]) * e
            c_fundo.a = 0.88 * min(1.0, t / 0.18) if t < T_FLASH1 else 0.88 * max(0.0, 1 - (t - T_FLASH1) / 0.2)
            # aneis: nascem a cada 40 ms com a proxima cor e aceleram para fora
            if t < T_FLASH0 and t >= estado['prox']:
                estado['prox'] = t + 0.04
                livre = next((a for a in aneis if a[2] < 0), None)
                if livre is not None:
                    livre[2] = t
                    livre[3] = _CORES_TUNEL[estado['cor'] % len(_CORES_TUNEL)]
                    estado['cor'] += 1
            for a in aneis:
                if a[2] < 0:
                    continue
                idade = t - a[2]
                r = dp(10) * math.exp(idade * 7.5)
                if r > rmax:
                    a[2] = -1.0
                    a[0].a = 0
                    continue
                rgb = a[3]
                fade = 1.0 if t < T_FLASH1 else max(0.0, 1 - (t - T_FLASH1) / 0.15)
                a[0].rgba = (rgb[0], rgb[1], rgb[2], min(1.0, idade * 8) * (1 - r / rmax) * fade)
                a[1].width = dp(1) + r * 0.035
                a[1].circle = (cx, cy, r)
            # riscos de velocidade nas bordas
            for rs in riscos:
                c, l, ang, fase, rgb = rs
                v = (t * 2.6 + fase) % 1.0
                r0 = rmax * (0.15 + 0.85 * v * v)
                r1 = r0 + rmax * 0.18 * v
                l.points = [cx + math.cos(ang) * r0, cy + math.sin(ang) * r0,
                            cx + math.cos(ang) * r1, cy + math.sin(ang) * r1]
                aa = 0.0 if t > T_FLASH1 else min(1.0, t / 0.2) * v * 0.85
                c.rgba = (rgb[0], rgb[1], rgb[2], aa)
            # o clarao branco: sobe, troca a tela no pico, abre na tela nova
            if t < T_FLASH0:
                c_flash.a = 0.0
            elif t < T_MEIO:
                c_flash.a = (t - T_FLASH0) / (T_MEIO - T_FLASH0)
            else:
                if not estado['meio']:
                    estado['meio'] = True
                    if on_meio:
                        try:
                            on_meio()
                        except Exception as ex:
                            print(f"[anim_ui] tunel meio: {ex}")
                c_flash.a = max(0.0, 1 - (t - T_MEIO) / (dur - T_MEIO))
            if t >= dur:
                _fim()
                return False
        except Exception as ex:
            print(f"[anim_ui] tunel: {ex}")
            if not estado['meio'] and on_meio:
                try:
                    on_meio()
                except Exception:
                    pass
            _fim()
            return False
    Clock.schedule_interval(_q, 1 / 60.)


def pacotes_de_luz(botao, cor=(0, 0.9, 1), periodo=2.4):
    """Pacotes de luz correndo pelas bordas de dentro do botao (dados passando)."""
    from kivy.uix.widget import Widget
    if getattr(botao, '_pacotes_ok', False):
        return
    botao._pacotes_ok = True
    linhas = []
    for k in range(2):
        w = Widget(size_hint=(None, None), size=(1, 1))
        botao.add_widget(w)
        linhas.append(w)

    def _onde(*_):
        m = dp(26)
        for k, w in enumerate(linhas):
            w.size = (max(dp(10), botao.width - 2 * m), 1)
            w.pos = (botao.x + m, botao.y + (dp(7) if k == 0 else botao.height - dp(7)))
    botao.bind(pos=_onde, size=_onde)
    _onde()
    luz_na_linha(linhas[0], cor, periodo=periodo, atraso=0.3, duracao=1.1, larg=dp(46))
    luz_na_linha(linhas[1], cor, periodo=periodo, atraso=0.3 + periodo / 2.0, duracao=1.1, larg=dp(46))


# ═══════════════════════════════════════════════════════════════════
#  TROCA DE TELA: O CORTE QUE PARTE A TELA (e o deslize do Voltar)
# ═══════════════════════════════════════════════════════════════════
def foto_da_tela():
    """(textura, fbo) com o que o app mostra agora (a tela inteira)."""
    from kivy.app import App
    from kivy.core.window import Window
    from kivy.graphics import Fbo, ClearColor, ClearBuffers
    root = App.get_running_app().root
    W, H = Window.size
    fbo = Fbo(size=(int(W), int(H)), with_stencilbuffer=True)
    with fbo:
        ClearColor(0.02, 0.02, 0.05, 1)
        ClearBuffers()
    # o canvas da tela sai do lugar so durante a foto e VOLTA para o mesmo
    # lugar (como o export_as_image do Kivy). Sem devolver, ele ficava sem
    # "pai": continuava sendo desenhado, mas mudancas nele nao pediam mais
    # redesenho - no celular a tela CONGELAVA (o PC de teste redesenha todo
    # quadro e escondia isso)
    pai = root.parent.canvas if root.parent is not None else Window.canvas
    idx = pai.indexof(root.canvas)
    if idx > -1:
        pai.remove(root.canvas)
    try:
        fbo.add(root.canvas)
        fbo.draw()
        fbo.remove(root.canvas)
    finally:
        if idx > -1 and pai.indexof(root.canvas) < 0:
            pai.insert(idx, root.canvas)
    return fbo.texture, fbo


def _poligono_textura(pts, W, H):
    """Vertices de um triangle_fan com a textura da tela cheia (uv = x/W, y/H)."""
    vs = []
    for x, y in pts:
        vs += [x, y, x / float(W), y / float(H)]
    return vs


def corte_parte_tela(cor=(0.0, 0.9, 1.0), sentido=1, on_meio=None, on_fim=None, dur=0.42):
    """A espada (em pixel) corta a tela numa diagonal; a tela antiga se parte
    na linha do corte e as duas metades escorregam para lados opostos,
    sumindo - a tela nova ja esta por baixo (on_meio troca no fim do corte)."""
    from kivy.core.window import Window
    from kivy.uix.widget import Widget

    class _Sobre(Widget):
        def on_touch_down(self, touch):
            return True

        def on_touch_move(self, touch):
            return True

        def on_touch_up(self, touch):
            return True
    estado = {'meio': False, 'fim': False, 'fbo': None}

    def _meio():
        if not estado['meio']:
            estado['meio'] = True
            if on_meio:
                try:
                    on_meio()
                except Exception as e:
                    print(f"[corte] meio: {e}")

    def _fim(ov=None):
        _meio()
        if not estado['fim']:
            estado['fim'] = True
            try:
                if ov is not None and ov.parent is not None:
                    Window.remove_widget(ov)
            except Exception:
                pass
            estado['fbo'] = None
            if on_fim:
                try:
                    on_fim()
                except Exception as e:
                    print(f"[corte] fim: {e}")
    try:
        tex, fbo = foto_da_tela()
        estado['fbo'] = fbo
        W, H = Window.size
        # a linha do corte: diagonal rasa de um lado ao outro da tela
        dy = W * 0.36 * (1 if sentido > 0 else -1)
        A = (0.0, H * 0.5 - dy / 2.0)
        B = (float(W), H * 0.5 + dy / 2.0)
        comp = math.hypot(B[0] - A[0], B[1] - A[1])
        tx, ty = (B[0] - A[0]) / comp, (B[1] - A[1]) / comp          # ao longo do corte
        nx, ny = -ty, tx                                              # para o lado de cima
        cima = [A, B, (float(W), float(H)), (0.0, float(H))]
        baixo = [(0.0, 0.0), (float(W), 0.0), B, A]
        ov = _Sobre(size_hint=(None, None), size=(W, H), pos=(0, 0))
        u = max(2, int(round(dp(3))))
        with ov.canvas:
            metades = []
            for pts in (cima, baixo):
                PushMatrix()
                trm = Translate(0, 0)
                Color(1, 1, 1, 1)
                m = Mesh(mode='triangle_fan', texture=tex, indices=list(range(len(pts))),
                         vertices=_poligono_textura(pts, W, H))
                c_beira = Color(cor[0], cor[1], cor[2], 0)
                l_beira = Line(points=[A[0], A[1], B[0], B[1]], width=dp(1.6))
                PopMatrix()
                metades.append((trm, m, c_beira, l_beira))
            # a espada: brilho colorido + nucleo branco em blocos de pixel
            c_brilho = Color(cor[0], cor[1], cor[2], 0)
            l_brilho = Line(points=[A[0], A[1], A[0], A[1]], width=dp(7))
            c_nucleo = Color(1, 1, 1, 0)
            blocos = [Rectangle(pos=(0, 0), size=(0, 0)) for _ in range(int(comp // (u * 2)) + 2)]
        Window.add_widget(ov)
    except Exception as e:
        print(f"[corte] {e}")
        _fim()
        return
    T_CORTE = 0.13           # a espada atravessa
    T_ABRE0 = 0.11           # as metades comecam a se separar
    t = [0.0]

    def _q(dt):
        try:
            t[0] += dt
            k = t[0]
            # a espada: um traco de blocos de pixel que nasce em A e corre ate B
            kc = min(1.0, k / T_CORTE)
            if k < T_CORTE + 0.14:
                ponta = comp * (1 - (1 - kc) ** 2)
                cauda = max(0.0, ponta - comp * 0.55) if kc < 1 else comp * min(1.0, (k - T_CORTE) / 0.14)
                n = 0
                s = cauda
                while s < ponta and n < len(blocos):
                    x = A[0] + tx * s
                    y = A[1] + ty * s
                    blocos[n].pos = (int(x // u) * u, int(y // u) * u)
                    blocos[n].size = (u * 2, u)
                    n += 1
                    s += u * 2
                for r in blocos[n:]:
                    r.size = (0, 0)
                l_brilho.points = [A[0] + tx * cauda, A[1] + ty * cauda, A[0] + tx * ponta, A[1] + ty * ponta]
                c_brilho.a = 0.55
                c_nucleo.a = 1.0
            else:
                c_brilho.a = 0
                c_nucleo.a = 0
                for r in blocos:
                    r.size = (0, 0)
            if k >= T_CORTE and not estado['meio']:
                _meio()                                     # a tela nova fica por baixo
            # as metades se separam: cada uma para o seu lado, acelerando, e somem
            ka = max(0.0, (k - T_ABRE0) / (dur - T_ABRE0))
            if ka > 0:
                d = (ka ** 1.7) * H * 0.55
                desliza = (ka ** 2) * W * 0.10
                alfa = 1.0 - max(0.0, (ka - 0.45) / 0.55)
                for i, (trm, m, c_beira, l_beira) in enumerate(metades):
                    sgn = 1 if i == 0 else -1
                    trm.x = nx * d * sgn + tx * desliza * sgn
                    trm.y = ny * d * sgn + ty * desliza * sgn
                    c_beira.a = 0.9 * alfa
                ov.opacity = alfa
            if k >= dur:
                _fim(ov)
                return False
        except Exception as ex:
            print(f"[corte] quadro: {ex}")
            _fim(ov)
            return False
    Clock.schedule_interval(_q, 1 / 60.)


def deslize_voltar(on_meio=None, on_fim=None, dur=0.24):
    """Voltar: a tela de agora escorrega para a direita e some (a do menu ja
    esta por baixo). Mais leve que o corte - e o caminho mais usado."""
    from kivy.core.window import Window
    from kivy.uix.widget import Widget

    class _Sobre(Widget):
        def on_touch_down(self, touch):
            return True

        def on_touch_up(self, touch):
            return True
    guarda = {}
    try:
        tex, fbo = foto_da_tela()
        guarda['fbo'] = fbo                               # a textura vive enquanto o deslize anda
        W, H = Window.size
        ov = _Sobre(size_hint=(None, None), size=(W, H), pos=(0, 0))
        with ov.canvas:
            PushMatrix()
            tr = Translate(0, 0)
            Color(1, 1, 1, 1)
            Rectangle(texture=tex, pos=(0, 0), size=(W, H))
            Color(0, 0.9, 1, 0.5)
            beira = Rectangle(pos=(-dp(2), 0), size=(dp(2), H))
            PopMatrix()
        Window.add_widget(ov)
    except Exception as e:
        print(f"[voltar] {e}")
        if on_meio:
            on_meio()
        if on_fim:
            on_fim()
        return
    if on_meio:
        try:
            on_meio()
        except Exception as e:
            print(f"[voltar] meio: {e}")
    t = [0.0]

    def _q(dt):
        try:
            t[0] += dt
            k = min(1.0, t[0] / dur)
            e = k * k * (3 - 2 * k)
            tr.x = W * 0.55 * e
            ov.opacity = 1.0 - k ** 1.5
            if k >= 1:
                Window.remove_widget(ov)
                guarda.clear()
                if on_fim:
                    on_fim()
                return False
        except Exception as ex:
            print(f"[voltar] quadro: {ex}")
            try:
                Window.remove_widget(ov)
            except Exception:
                pass
            if on_fim:
                on_fim()
            return False
    Clock.schedule_interval(_q, 1 / 60.)


def pulso(widget, fator=1.08, duracao=0.28):
    """Batida curta de escala (visual), ex: quando um numero chega ao valor."""
    try:
        _, sc = _matriz(widget)
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                k = min(1.0, t[0] / duracao)
                s = 1 + (fator - 1) * math.sin(math.pi * k)
                sc.x = sc.y = s
                if k >= 1:
                    sc.x = sc.y = 1
                    return False
            except Exception:
                sc.x = sc.y = 1
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[anim_ui] pulso: {e}")


def voar(w, dy, escala0=1.2, duracao=0.34):
    """O widget chega de `dy` (ex.: saindo do visor) ate o lugar, crescendo
    de `escala0` para 1 e acendendo (so visual)."""
    try:
        tr, sc = _matriz(w)
        tr.y = dy
        sc.x = sc.y = escala0
        w.opacity = 0.2
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                k = min(1.0, t[0] / duracao)
                e = 1 - (1 - k) ** 3
                ov = 1 + 1.6 * (k - 1) ** 3 + 0.6 * (k - 1) ** 2      # out_back leve
                tr.y = dy * (1 - ov)
                sc.x = sc.y = escala0 + (1 - escala0) * e
                w.opacity = 0.2 + 0.8 * e
                if k >= 1:
                    tr.y = 0
                    sc.x = sc.y = 1
                    w.opacity = 1
                    return False
            except Exception:
                tr.y = 0
                sc.x = sc.y = 1
                w.opacity = 1
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[anim_ui] voar: {e}")


# ═══════════════════════════════════════════════════════════════════
#  FAIXA DE AVISO (meta batida, faixa nova...)
# ═══════════════════════════════════════════════════════════════════
def _chanfro(x, y, w, h, c):
    return [x + c, y, x + w - c, y, x + w, y + c, x + w, y + h - c,
            x + w - c, y + h, x + c, y + h, x, y + h - c, x, y + c]


_FAIXA_ATUAL = [None]


def faixa_aviso(titulo, sub='', ancora=None, cor=(1, 0.88, 0.1), segura=2.4):
    """Uma faixa HUD que abre de dentro para fora logo abaixo de `ancora`,
    uma luz passa por ela, fica `segura` s e fecha. Tem fundo proprio (le
    por cima de qualquer coisa) e nao pega o toque. Uma de cada vez."""
    from kivy.core.window import Window
    from kivy.uix.label import Label
    velho = _FAIXA_ATUAL[0]
    if velho is not None:
        try:
            velho._faixa_fim()
        except Exception:
            pass
    try:
        r, g, b = cor[:3]
        larg = min(Window.width * 0.92, dp(520))
        alt = dp(66) if sub else dp(46)
        topo = Window.height * 0.80
        if ancora is not None and ancora.get_root_window() is not None:
            topo = ancora.to_window(ancora.x, ancora.y)[1] - dp(8)
        hexc = '%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
        txt = f"[b][color=#{hexc}]{titulo}[/color][/b]"
        if sub:
            txt += f"\n[font=rajdhani.ttf][size=15sp][color=#e3eaf5]{sub}[/color][/size][/font]"
        x0, y0 = (Window.width - larg) / 2.0, topo - alt
        lbl = Label(text=txt, markup=True, font_name='orbitron.ttf', font_size='15sp',
                    halign='center', valign='middle', size_hint=(None, None),
                    size=(larg, alt), pos=(x0, y0), opacity=0)
        lbl.text_size = (larg - dp(24), alt)
        c = dp(12)
        pts = _chanfro(x0, y0, larg, alt, c)
        cx, cy = x0 + larg / 2.0, y0 + alt / 2.0
        vs = [cx, cy, 0, 0]
        for i in range(0, len(pts), 2):
            vs += [pts[i], pts[i + 1], 0, 0]
        vs += [pts[0], pts[1], 0, 0]
        with lbl.canvas.before:
            Color(r * 0.10, g * 0.10, b * 0.10, 0.97)
            Mesh(mode='triangle_fan', vertices=vs, indices=list(range(len(vs) // 4)))
            c_luz = Color(1, 1, 1, 0)
            m_luz = Mesh(mode='triangle_fan', indices=[0, 1, 2, 3], vertices=[0] * 16)
            Color(r, g, b, 0.22)
            Line(points=_chanfro(x0 + dp(4), y0 + dp(4), larg - dp(8), alt - dp(8), c - dp(2)),
                 width=1, close=True)
            Color(r, g, b, 1)
            Line(points=pts, width=dp(1.1), close=True)
        try:
            m_luz.texture = _textura_faixa_luz()
        except Exception:
            pass
        tr, sc = _matriz(lbl)
        sc.x = 0.06
        Window.add_widget(lbl)
        _FAIXA_ATUAL[0] = lbl
    except Exception as e:
        print(f"[anim_ui] faixa de aviso: {e}")
        return

    T_ABRE, T_LUZ0, T_LUZ, T_SAI = 0.26, 0.24, 0.6, 0.22
    t_sai0 = T_ABRE + segura
    t = [0.0]
    ev = [None]

    def _fim(*_):
        if ev[0] is not None:
            ev[0].cancel()
            ev[0] = None
        try:
            Window.remove_widget(lbl)
        except Exception:
            pass
        if _FAIXA_ATUAL[0] is lbl:
            _FAIXA_ATUAL[0] = None
    lbl._faixa_fim = _fim

    def _q(dt):
        try:
            t[0] += dt
            k = t[0]
            if k < T_ABRE:
                e = 1 - (1 - k / T_ABRE) ** 3
                sc.x = 0.06 + 0.94 * e
                lbl.opacity = min(1.0, e * 1.8)
            elif k < t_sai0:
                sc.x = sc.y = 1
                lbl.opacity = 1
            elif k < t_sai0 + T_SAI:
                e = ((k - t_sai0) / T_SAI) ** 2
                sc.y = 1 - 0.9 * e
                tr.y = dp(8) * e
                lbl.opacity = 1 - e
            else:
                _fim()
                return False
            kl = (k - T_LUZ0) / T_LUZ
            if 0 <= kl <= 1:
                lw = max(dp(30), larg * 0.18)
                incl = alt * 0.5
                xa = x0 - lw - incl + (larg + 2 * lw + incl) * (1 - (1 - kl) ** 2)

                def cl(v):
                    return min(max(v, x0 + dp(2)), x0 + larg - dp(2))
                m_luz.vertices = [cl(xa), y0, 0, 0.5, cl(xa + lw), y0, 1, 0.5,
                                  cl(xa + lw + incl), y0 + alt, 1, 0.5, cl(xa + incl), y0 + alt, 0, 0.5]
                c_luz.rgba = (0.6 + 0.4 * r, 0.6 + 0.4 * g, 0.6 + 0.4 * b, 0.30 * math.sin(math.pi * kl))
            else:
                c_luz.a = 0
        except Exception as ex:
            print(f"[anim_ui] faixa frame: {ex}")
            _fim()
            return False
    ev[0] = Clock.schedule_interval(_q, 1 / 60.)


# ═══════════════════════════════════════════════════════════════════
#  VIDA CONTINUA (brilho no titulo, luz correndo nas linhas)
# ═══════════════════════════════════════════════════════════════════
def _repetir(widget, periodo, atraso, rodar):
    """Chama rodar() a cada `periodo` s, so enquanto o widget esta na tela
    (fora dela nao gasta nada alem do relogio). Um widget que ja apareceu e
    foi descartado (sem pai) para de repetir."""
    visto = [False]

    def _vez(dt):
        try:
            if widget.get_root_window() is not None:
                visto[0] = True
                rodar()
            elif visto[0] and widget.parent is None:
                return                                   # descartado: acabou
        except Exception as e:
            print(f"[anim_ui] repetir: {e}")
        Clock.schedule_once(_vez, periodo)
    Clock.schedule_once(_vez, atraso)


def brilho_texto(label, periodo=6.0, atraso=1.4, duracao=0.75, forca=0.75):
    """De tempos em tempos um reflexo de luz atravessa as letras do label
    (as proprias letras acendem em branco numa faixa inclinada)."""
    if getattr(label, '_brilho_texto_ok', False):
        return
    label._brilho_texto_ok = True
    try:
        with label.canvas.after:
            faixas = []
            for a, larg_rel in ((0.35, 0.16), (forca, 0.06)):     # halo largo + nucleo
                cor = Color(1, 1, 1, 0)
                m = Mesh(mode='triangle_fan', indices=[0, 1, 2, 3], vertices=[0] * 16)
                faixas.append((cor, m, a, larg_rel))
    except Exception as e:
        print(f"[anim_ui] brilho do texto: {e}")
        return
    estado = {'ev': None, 't': 0.0}

    def _quadro(dt):
        try:
            estado['t'] += dt
            k = min(1.0, estado['t'] / duracao)
            # copia propria das letras em branco (desenhar com a textura do
            # proprio Label nao aparece: ela e trocada por baixo a cada ajuste)
            chave = (label.text, label.font_name, float(label.font_size), bool(label.bold))
            if estado.get('chave') != chave:
                if getattr(label, 'markup', False):              # [b]...[/b] vira negrito, nao texto
                    from kivy.core.text.markup import MarkupLabel as CoreLabel
                else:
                    from kivy.core.text import Label as CoreLabel
                cl = CoreLabel(text=label.text, font_name=label.font_name,
                               font_size=label.font_size, bold=label.bold)
                cl.refresh()
                estado['tex'], estado['chave'] = cl.texture, chave
            tex = estado['tex']
            if tex is None:
                return True
            tw, th = tex.size
            tx = int(label.center_x - tw / 2.0)
            ty = int(label.center_y - th / 2.0)
            uv = tex.tex_coords
            incl = th * 0.6
            e = k * k * (3 - 2 * k)
            for cor, m, a, larg_rel in faixas:
                lw = max(dp(6), tw * larg_rel)
                xa = tx - lw - incl + (tw + 2 * lw + incl) * e

                def pt(x, y):
                    x = min(max(x, tx), tx + tw)
                    fx = (x - tx) / float(tw) if tw else 0
                    fy = (y - ty) / float(th) if th else 0
                    u = uv[0] + (uv[2] - uv[0]) * fx
                    v = uv[1] + (uv[7] - uv[1]) * fy
                    return [x, y, u, v]
                m.texture = tex
                m.vertices = (pt(xa, ty) + pt(xa + lw, ty) +
                              pt(xa + lw + incl, ty + th) + pt(xa + incl, ty + th))
                cor.a = a * math.sin(math.pi * k)
            if k >= 1:
                for cor, *_ in faixas:
                    cor.a = 0
                estado['ev'] = None
                return False
        except Exception as ex:
            print(f"[anim_ui] brilho do texto frame: {ex}")
            for cor, *_ in faixas:
                cor.a = 0
            estado['ev'] = None
            return False

    def _rodar():
        if estado['ev'] is None:
            estado['t'] = 0.0
            estado['ev'] = Clock.schedule_interval(_quadro, 1 / 60.)
    _repetir(label, periodo, atraso, _rodar)


def luz_na_linha(linha, cor=(0, 0.9, 1), periodo=4.0, atraso=0.8, duracao=1.3, larg=None):
    """Um ponto de luz corre pela linha decorativa, de ponta a ponta."""
    if getattr(linha, '_luz_linha_ok', False):
        return
    linha._luz_linha_ok = True
    try:
        with linha.canvas.after:
            c = Color(cor[0], cor[1], cor[2], 0)
            m = Mesh(mode='triangle_fan', indices=[0, 1, 2, 3], vertices=[0] * 16)
        m.texture = _textura_faixa_luz()
    except Exception as e:
        print(f"[anim_ui] luz na linha: {e}")
        return
    estado = {'ev': None, 't': 0.0}

    def _quadro(dt):
        try:
            estado['t'] += dt
            k = min(1.0, estado['t'] / duracao)
            lw = larg or max(dp(50), linha.width * 0.22)
            x, w = linha.x, linha.width
            h = dp(3)
            y = linha.center_y - h / 2.0
            xa = x - lw + (w + lw) * (k * k * (3 - 2 * k))
            xb = xa + lw
            ca, cb = max(xa, x), min(xb, x + w)
            if cb <= ca:
                c.a = 0
            else:
                ua, ub = (ca - xa) / lw, (cb - xa) / lw
                m.vertices = [ca, y, ua, 0.5, cb, y, ub, 0.5, cb, y + h, ub, 0.5, ca, y + h, ua, 0.5]
                c.a = 0.95 * math.sin(math.pi * k)
            if k >= 1:
                c.a = 0
                estado['ev'] = None
                return False
        except Exception as ex:
            print(f"[anim_ui] luz na linha frame: {ex}")
            c.a = 0
            estado['ev'] = None
            return False

    def _rodar():
        if estado['ev'] is None:
            estado['t'] = 0.0
            estado['ev'] = Clock.schedule_interval(_quadro, 1 / 60.)
    _repetir(linha, periodo, atraso, _rodar)


# ═══════════════════════════════════════════════════════════════════
#  DIGITOS DECIFRANDO (resultado da calculadora)
# ═══════════════════════════════════════════════════════════════════
def parar_decifrar(label):
    ev = getattr(label, '_anim_decifra', None)
    if ev is not None:
        ev.cancel()
        label._anim_decifra = None


def decifrar(label, final, duracao=0.34):
    """Os digitos rolam (numeros trocando) e vao parando da esquerda para a
    direita ate formar `final`. O resto (pontos, virgula, sinais) fica fixo."""
    import random
    parar_decifrar(label)
    pos = [i for i, ch in enumerate(final) if ch.isdigit()]
    if not pos:
        label.text = final
        return
    t = [0.0]
    acc = [1.0]

    def _p(dt):
        try:
            t[0] += dt
            acc[0] += dt
            k = min(1.0, t[0] / duracao)
            if k >= 1:
                label.text = final
                label._anim_decifra = None
                return False
            if acc[0] < 1 / 30.:                     # troca 30x por segundo
                return True
            acc[0] = 0.0
            fixos = int(len(pos) * k)
            s = list(final)
            for j, i in enumerate(pos):
                if j >= fixos:
                    s[i] = random.choice('0123456789')
            label.text = ''.join(s)
        except Exception:
            label.text = final
            label._anim_decifra = None
            return False
    label._anim_decifra = Clock.schedule_interval(_p, 1 / 60.)


# ═══════════════════════════════════════════════════════════════════
#  ROLAGEM: SEM QUIQUE, A BORDA ACENDE
# ═══════════════════════════════════════════════════════════════════
_TEX_BORDA = None


def _textura_borda():
    """Brilho da borda: forte na beira e no meio, some para dentro e nas pontas."""
    global _TEX_BORDA
    if _TEX_BORDA is None:
        nx, ny = 32, 16
        buf = bytearray(nx * ny * 4)
        for y in range(ny):
            fy = (1 - y / (ny - 1.0)) ** 1.6
            for x in range(nx):
                fx = math.sin(math.pi * x / (nx - 1.0))
                a = fy * (0.25 + 0.75 * fx)
                i = (y * nx + x) * 4
                buf[i] = buf[i + 1] = buf[i + 2] = 255
                buf[i + 3] = int(255 * a)
        dados = bytes(buf)
        tex = Texture.create(size=(nx, ny), colorfmt='rgba')
        tex.wrap = 'clamp_to_edge'
        tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
        tex.add_reload_observer(lambda t: t.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte'))
        _TEX_BORDA = tex
    return _TEX_BORDA


try:
    from kivy.effects.scroll import ScrollEffect as _ScrollEffect
except Exception:                                  # pragma: no cover
    _ScrollEffect = object


class EfeitoBordaAcesa(_ScrollEffect):
    """Rolagem das listas: no fim nao quica - a borda de cima ou de baixo
    acende, mais forte quanto mais o dedo puxa ou mais rapido a lista chega."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._luz = {'cima': 0.0, 'baixo': 0.0}
        self._inst = None
        self._ev = None

    def on_value(self, *args):
        try:
            lo, hi = sorted((self.min, self.max))
            v = self.value
            if v < lo or v > hi:
                forca = abs(v - (lo if v < lo else hi)) / dp(36)
                if not self.is_manual:
                    forca = max(forca, abs(self.velocity) / dp(2400))
                self._acender('baixo' if v > hi else 'cima', forca)
        except Exception as e:
            print(f"[rolagem] borda: {e}")
        return super().on_value(*args)

    def _rolagem(self):
        alvo = self.target_widget
        sv = getattr(alvo, 'parent', None) if alvo is not None else None
        if sv is None or getattr(sv, 'effect_y', None) is not self:
            return None                                  # so o eixo vertical acende
        return sv

    def _acender(self, lado, forca):
        sv = self._rolagem()
        if sv is None:
            return
        if self._inst is None or self._inst[0] is not sv:
            with sv.canvas.after:
                cc = Color(0, 0.9, 1, 0)
                rc = Rectangle(texture=_textura_borda())
                lc = Color(0.6, 1, 1, 0)
                lr = Rectangle()
                cb = Color(0, 0.9, 1, 0)
                rb = Rectangle(texture=_textura_borda())
                lcb = Color(0.6, 1, 1, 0)
                lrb = Rectangle()
            self._inst = (sv, (cc, rc, lc, lr), (cb, rb, lcb, lrb))
        self._luz[lado] = min(1.0, self._luz[lado] + min(forca, 1.0) * 0.6)
        self._desenhar()
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._apagar, 1 / 60.)

    def _desenhar(self):
        sv, cima, baixo = self._inst
        x, y, w, h = sv.x, sv.y, sv.width, sv.height
        alt = min(dp(40), h * 0.25)
        for lado, (c, r, lc, lr) in (('cima', cima), ('baixo', baixo)):
            a = self._luz[lado]
            alt_l = alt * (0.5 + 0.5 * a)
            if lado == 'cima':
                r.pos, r.size = (x, y + h - alt_l), (w, alt_l)
                r.tex_coords = (0, 1, 1, 1, 1, 0, 0, 0)       # beira em cima
                lr.pos, lr.size = (x + w * 0.1, y + h - dp(1.5)), (w * 0.8, dp(1.5))
            else:
                r.pos, r.size = (x, y), (w, alt_l)
                r.tex_coords = (0, 0, 1, 0, 1, 1, 0, 1)       # beira embaixo
                lr.pos, lr.size = (x + w * 0.1, y), (w * 0.8, dp(1.5))
            c.a = 0.55 * a
            lc.a = 0.9 * a

    def _apagar(self, dt):
        try:
            if self._inst is None:
                self._ev = None
                return False
            fator = math.exp(-dt * (2.2 if self.is_manual else 5.0))
            vivo = False
            for lado in self._luz:
                self._luz[lado] *= fator
                if self._luz[lado] < 0.01:
                    self._luz[lado] = 0.0
                else:
                    vivo = True
            self._desenhar()
            if not vivo:
                self._ev = None
                return False
        except Exception as e:
            print(f"[rolagem] apagar: {e}")
            self._ev = None
            return False
