"""
aberturas.py — TraveteFocus
A abertura SIMPLES depois da senha (escolha do usuario em 03/11/2026, no
lugar da luta contra o chefe, que ficou guardada em guardado/abertura_luta/).
Mesmo formato das cenas do cenas.py: abertura(tela, label, on_fim, texto) ->
camada (com _agenda, para o limpar_cena e o "toque para pular"). Calma: nada
de zoom, clarao ou tremida.

  abertura_chegada   o Yoru aparece em guarda em cima da frase (esmaecendo),
                     o titulo acende letra por letra, ele guarda a espada e
                     cumprimenta pela hora do dia (bom dia / boa tarde / boa noite)
"""
from datetime import datetime

from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle

import kirito as K
from cenas import (TituloLuz, _Agenda, _Uma, _som, _precarregar_sons, _ps_titulo, _com, _PX,
                   _no_quadro, balao)


def _saudacao():
    h = datetime.now().hour
    return "Bom dia!" if 5 <= h < 12 else ("Boa tarde!" if 12 <= h < 18 else "Boa noite!")


def _montar(tela, label, texto):
    """A camada, o titulo (apagado) no lugar do label e a agenda."""
    camada = Widget(size_hint=(None, None), size=tela.size, pos=(0, 0))
    ag = _Agenda()
    camada._agenda = ag
    tela.add_widget(camada)
    wx, wy = label.to_window(label.x, label.y)
    lx, ly = tela.to_widget(wx, wy)
    titulo = TituloLuz(texto, label.font_size, pos=(lx, ly), size=label.size)
    camada.add_widget(titulo)
    camada._titulo = titulo
    return camada, ag, titulo


def _acender(titulo, i, dur=0.35):
    """A letra i aparece esmaecendo (clara -> ciano do titulo), descendo um
    pouquinho - sem o risco de luz do corte da espada."""
    from kivy.clock import Clock
    ox, oy = titulo._origem()
    x0, x1 = titulo._larg[i], titulo._larg[i + 1]
    w = max(1.0, x1 - x0)
    c = Color(0.85, 1, 1, 0)
    r = Rectangle(texture=titulo._tex.get_region(x0, 0, w, titulo.th), pos=(ox + x0, oy + dp(4)),
                  size=(w, titulo.th))
    titulo._grupo.add(c)
    titulo._grupo.add(r)
    titulo._trechos.append({'i0': i, 'rect': r})
    cor = titulo.cor
    t = [0.0]

    def _p(dt):
        t[0] += dt
        u = min(1.0, t[0] / dur)
        e = u * u * (3 - 2 * u)
        ox2, oy2 = titulo._origem()
        r.pos = (ox2 + x0, oy2 + dp(4) * (1 - e))
        c.rgba = (0.85 + (cor[0] - 0.85) * e, 1 + (cor[1] - 1) * e, 1 + (cor[2] - 1) * e, e)
        return u < 1
    Clock.schedule_interval(_p, 1 / 60.)


def _brilho_suave(titulo, dur=1.0):
    """Um brilho lento passa pelo titulo inteiro (sem piscar)."""
    import math
    from kivy.clock import Clock
    cores = [ins for ins in titulo._grupo.children if isinstance(ins, Color)]
    cor = titulo.cor
    t = [0.0]

    def _p(dt):
        t[0] += dt
        k = 0.45 * math.sin(math.pi * min(1.0, t[0] / dur))
        for c in cores:
            c.rgba = (cor[0] + (1 - cor[0]) * k, cor[1] + (1 - cor[1]) * k, cor[2] + (1 - cor[2]) * k, c.a)
        return t[0] < dur
    Clock.schedule_interval(_p, 1 / 60.)


def _acender_letras(ag, titulo, texto, t0, passo=0.07, dur=0.35):
    """As letras acendem uma por uma, da esquerda para a direita."""
    k = 0
    for i, ch in enumerate(texto):
        if ch.strip():
            ag.depois(t0 + k * passo, lambda i=i: _acender(titulo, i, dur=dur))
            k += 1
    return t0 + k * passo + dur


def abertura_chegada(tela, label, on_fim=None, texto="TRAVETE FOCUS"):
    """O Yoru surge em guarda em cima da frase (esmaecendo, sem pulo), o
    titulo acende letra por letra, ele guarda a espada e cumprimenta."""
    fim = _Uma(on_fim)
    camada = None
    try:
        camada, ag, titulo = _montar(tela, label, texto)

        def encerrar():
            ag.parar()
            fim()
        W, H = tela.size
        area = (0.0, 0.0, float(W), float(H))
        ps = _ps_titulo(titulo.th, W, H)
        kk = K.KiritoPixel(ps=ps)
        ps = kk.ps
        _PX[0] = ps / float(K.R)
        kk.opacity = 0
        camada.add_widget(kk)
        _precarregar_sons(['titulo', 'embainhar'])
        P = K.POSE_A
        th = titulo.th
        ox_t, oy_t = titulo._origem()
        guarda = _com(P['guarda'], olhos='a')
        fim_p = _com(P['guardado'], olhos='v')
        kk.precarregar([guarda, fim_p, P['embainha1_a'], P['embainha1_b'], P['embainha1_c']])
        pe = kk.extensao(guarda)[1] - ps
        B = _no_quadro(kk, ox_t + titulo.tw * 0.5, oy_t + th * 0.82 + pe, [guarda, fim_p], area, max(dp(4), ps))
        kk.ancorar(*B)
        kk.idle(base=guarda)

        def _surge():
            t = [0.0]

            def _q(dt):
                t[0] += dt
                kk.opacity = min(1.0, t[0] / 0.45)
                return kk.opacity < 1.0
            ag.cada(1 / 60., _q)
        ag.depois(0.05, _surge)
        acabou = _acender_letras(ag, titulo, texto, 0.55)
        ag.depois(acabou, lambda: (_som('titulo'), _brilho_suave(titulo)))

        def _guarda_e_fala():
            seq = K.sequencia([(4, P['embainha1_a'], 'in'), (2, P['embainha1_b'], 'suave'),
                               (2, P['embainha1_c'], 'mola'), (1, fim_p)])

            def _q(q):
                if q == 6:
                    _som('embainhar')
                    balao(camada, _saudacao(), kk, dur=1.4)
            kk.tocar(seq, on_quadro=_q, on_fim=lambda: kk.idle(base=fim_p))
        ag.depois(acabou + 0.15, _guarda_e_fala)
        ag.depois(acabou + 1.9, encerrar)
        ag.depois(8.0, lambda: (titulo.completo(), encerrar()))
    except Exception as e:
        print(f"[abertura] chegada falhou, seguindo sem ela: {e}")
        fim()
    return camada
