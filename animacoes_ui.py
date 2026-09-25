"""
animacoes_ui.py — TraveteFocus
Animacoes de interface usadas por todas as telas:
  entrada_cascata(widgets)       itens/cards entram um depois do outro
  contar(label, ate, montar)     numero sobe contando ate o valor
  fmt_br(valor, casas)           1.234,56 (padrao brasileiro)
  aplicar_brilho_toque(botao)    pulso no contorno + faixa de luz varrendo
  pulso(widget)                  "batida" curta de escala

Regras: nada de .bind(...).start(...) encadeado (bind devolve None) e nenhum
callback de Clock/Animation deixa excecao escapar.
"""
import math

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import (Color, Line, Mesh, PushMatrix, PopMatrix,
                           Translate, Scale)
from kivy.graphics.texture import Texture
from kivy.metrics import dp


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
                    escala=True, atraso_max=0.55):
    """Opacidade 0->1, sobe `dy` e cresce levemente, um item depois do outro.
    O atraso total e limitado a `atraso_max` (listas longas nao demoram)."""
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
            _entrar(w, i * passo, dy, duracao, escala)
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
            l_pulso = Line(width=dp(1.4))
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
            # pulso do contorno: expande dp(0 -> 7) e some em 0.4s
            kp = min(1.0, t / 0.40)
            ex = dp(7) * (1 - (1 - kp) ** 3)
            l_pulso.rectangle = (x - ex, y - ex, w + 2 * ex, h + 2 * ex)
            c_pulso.rgba = (r, g, b, 0.55 * (1 - kp))
            if k >= 1 and kp >= 1:
                c_faixa.a = 0
                c_pulso.a = 0
                estado['ev'] = None
                return False
        except Exception as e:
            print(f"[anim_ui] brilho frame: {e}")
            c_faixa.a = 0
            c_pulso.a = 0
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

    def _parar(inst, parent):
        if parent is None and estado['ev'] is not None:
            estado['ev'].cancel()
            estado['ev'] = None
            c_faixa.a = 0
            c_pulso.a = 0
    botao.fbind('parent', _parar)


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
