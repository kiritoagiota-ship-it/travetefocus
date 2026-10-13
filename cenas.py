"""
cenas.py — TraveteFocus
Cenas com o Kirito pixel art (kirito.py) + cortes em meia-lua (espadachim.py):

  cena_titulo(tela, label, on_fim)  abertura inteira (so depois da senha): a
                                    LUTA contra o chefe (chefe.py) - golpes, a
                                    rajada com ele de joelho, BAN-KAI como o do
                                    Ichigo (o Bankai e desenhado em dobro), o
                                    chefe ataca o Bankai e leva o revide, e o
                                    corte final atravessa o chefe e grava
                                    "TRAVETE FOCUS"; guarda as espadas e fica em pose.
  cena_entrada_rapida(...)          senha ainda valendo: mergulho de um canto,
                                    um corte grava a frase e balao "Bem-vindo!".
  KiritoPin(caixa)                  espia por cima da caixa do PIN (comico:
                                    !!, gota de suor, olhos brilhando).
  kirito_fatiar(widget, on_fim)     APAGAR: golpes de verdade (iai, estocada, X)
                                    com o arco de luz e gemidinhos de voz.
  kirito_wipe(widgets, on_fim)      APAGAR TUDO: um golpe em cada coisa da tela.
  kirito_vitoria(tela, linhas)      FINALIZAR: as pecas viram um cartao do turno,
                                    ele embainha, carimba (salvo) e o cartao voa.
  kirito_carta(botao, on_fim, linhas)  WHATSAPP: as linhas do turno viram uma carta
                                    na mao dele; ele joga, corta e ela sai voando.
  kirito_carimbo / nivel / meta     o resto do app e comico (anime chibi):
                                    emotes (EmoteAnime), pulinhos, moeda na cabeca.

Tudo tolerante a falha: se algo der errado, on_fim ainda e chamado (a
historia do app nunca trava por causa de uma animacao).
"""
import os
import math
import random
import time
from collections import OrderedDict

from kivy.uix.widget import Widget
from kivy.uix.stencilview import StencilView
from kivy.graphics import (Color, Rectangle, Line, Mesh, PushMatrix, PopMatrix,
                           Scale, Translate, Rotate, InstructionGroup, SmoothLine)
from kivy.graphics.texture import Texture
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp, sp

import kirito as K

CIANO = (0.0, 0.9, 1.0)
AZUL = (0.35, 0.65, 1.0)        # rastro da Dark Repulser
POEIRA = (0.55, 0.62, 0.75)
BRANCO = (1.0, 1.0, 1.0)
ROXO = (0.66, 0.34, 1.0)        # chamas da forma Mugetsu

# efeitos que as cenas tocam (pre-carregados no inicio de cada cena)
_SONS_TITULO = ['koiguchi', 'pulo', 'pouso', 'sacar_iai', 'corte', 'sacar', 'corte2',
                'absorve', 'carga', 'getsuga', 'separa', 'desliza', 'embainhar', 'titulo',
                'golpe_final', 'fala_ougi', 'fala_ikuzo', 'fala_kurae', 'kiai_seiya', 'giro', 'fitas',
                'trevas', 'fusao', 'reiatsu', 'kiai_kai', 'agarra', 'cristal', 'transicao',
                'kiai_ha1', 'kiai_ha2', 'kiai_sei1', 'kiai_sei2', 'kiai_sei3', 'kiai_fun', 'rugido', 'vidro']
_SONS_PIN = ['agarra', 'susto', 'pulo', 'pouso', 'teleporte']


def _som(nome):
    try:
        import som
        som.tocar(nome)
    except Exception:
        pass


def _precarregar_sons(nomes):
    try:
        import som
        som.precarregar(nomes)
    except Exception:
        pass


def _tremer(n):
    try:
        from efeitos import tremer_tela
        tremer_tela(n)
    except Exception:
        pass


def _com(p, **kw):
    """Copia da pose com alguns campos trocados (ex: expressao, emote)."""
    q = dict(p)
    q.update(kw)
    return q


def _perto(a, alvo):
    """O mesmo angulo `a`, na volta mais proxima de `alvo` (a lamina vai pelo
    caminho curto em vez de dar uma volta inteira no ar)."""
    if a is None or alvo is None:
        return a
    while a - alvo > 180:
        a -= 360
    while alvo - a > 180:
        a += 360
    return a


def _de_agora(k, n=2, curva='suave', proxima=None):
    """Chave inicial = a pose que esta na tela: a sequencia seguinte parte
    dela (sem 'teletransportar' os bracos de uma pose para a outra).
    `proxima` = a pose seguinte (acerta a volta dos angulos das laminas)."""
    p = _com(k._base, s1=None, s2=None, emote=None)
    if proxima is not None:
        p['a1'] = _perto(p['a1'], proxima['a1'])
        p['a2'] = _perto(p['a2'], proxima['a2'])
    return [(n, p, curva)]


def _voo(k, sobe, topo, desce, cortes=(0.22, 0.72)):
    """on_passo para _mover: pernas esticadas no impulso, encolhidas no alto
    do pulo e esticadas de novo indo pousar."""
    atual = [None]

    def _f(u):
        p = sobe if u < cortes[0] else (topo if u < cortes[1] else desce)
        if p is not atual[0]:
            atual[0] = p
            k.mostrar(p)
    return _f


class _Uma:
    """Chama `fn` uma unica vez (protege on_fim de cenas)."""

    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *_):
        fn, self.fn = self.fn, None
        if fn:
            try:
                fn()
            except Exception as e:
                print(f"[cenas] on_fim: {e}")


_PASSO_MOVER = 1 / 30.0      # o corpo anda em degraus de 1/30 s (desenho em 2s a 60 fps)


def _mover(k, de, para, dur, altura=0.0, rot=None, fantasmas=3,
           cor_fantasma=None, on_fim=None, linear=False, cada=None, on_passo=None,
           ease=None, limite=None, rot_janela=(0.0, 1.0)):
    """Move a ancora do Kirito em arco (parabola de `altura`), girando de
    rot[0] a rot[1]. Deixa `fantasmas` copias nitidas espalhadas pelo
    caminho (uma por quadro embolava num rastro de fumaca).
    ease: 'out' (desacelera), 'in' (acelera, queda) ou 'linear'.
    limite=(area, folga): o boneco (girado como estiver) nunca sai da area.
    on_passo(u) e chamado a cada degrau com o progresso 0..1.
    Como numa animacao desenhada, o corpo anda em degraus (30 por segundo,
    sempre em pixel inteiro) e o giro vai de 90 em 90 graus - girar pixel
    art num angulo torto entorta os pixels."""
    t = [0.0]
    degrau = [-1]
    feito = [False]
    n_f = 3 if fantasmas is True else int(fantasmas or 0)
    marcas = [(i + 1) / float(n_f + 1) for i in range(n_f)]
    if ease is None:
        ease = 'linear' if linear else ('out' if altura >= 0 else 'in')

    # vida: nas arrancadas o corpo estica no sentido do movimento; chegando
    # de uma queda ele amassa e volta (so no Yoru; o giro em bola nao estica)
    vivo = hasattr(k, 'amassar')
    ddx, ddy = para[0] - de[0], para[1] - de[1]
    longe = math.hypot(ddx, ddy) > getattr(k, 'ps', 6) * 9
    estica = vivo and rot is None and longe and dur <= 0.32
    if estica:
        if abs(ddx) >= abs(ddy):
            k.escala_x, k.escala_y = 1.12, 0.93
        else:
            k.escala_x, k.escala_y = 0.93, 1.12

    def _acabar():
        if not feito[0]:
            feito[0] = True
            if vivo:
                if estica:
                    k.escala_x = k.escala_y = 1.0
                if longe and (ease == 'in' or altura > 0 or ddy < -getattr(k, 'ps', 6) * 6):
                    k.amassar(-0.13)                     # pousou: amassa e volta
                elif estica:
                    k.amassar(0.06, quadros=3)           # freou: da uma esticadinha de volta
            if on_fim:
                on_fim()

    def _p(dt):
        try:
            if getattr(k, '_pausa', 0) > 0:
                return True          # hit-stop: o corpo congela junto com a pose
            t[0] += dt
            u = min(1.0, t[0] / dur)
            d = int(t[0] / _PASSO_MOVER)
            if d == degrau[0] and u < 1:
                return True          # entre dois degraus: o desenho fica onde esta
            degrau[0] = d
            if on_passo:
                on_passo(u)          # troca a pose antes de enquadrar (sem 1 quadro de atraso)
            if ease == 'linear':
                e = u
            elif ease == 'in':
                e = u * u
            elif ease == 'suave':
                e = u * u * (3 - 2 * u)
            else:
                e = 1 - (1 - u) ** 2
            x = de[0] + (para[0] - de[0]) * e
            y = de[1] + (para[1] - de[1]) * e + altura * 4 * u * (1 - u)
            if rot is not None:
                ja, jb = rot_janela            # o giro so acontece nessa parte do voo (na bola)
                g = max(0.0, min(1.0, (e - ja) / max(1e-6, jb - ja)))
                r = rot[0] + (rot[1] - rot[0]) * g
                k.rotacao = (round(r / 90.0) * 90.0) % 360.0     # de 90 em 90 graus
            if limite is not None:
                x, y = _dentro_girado(k, x, y, limite[0], limite[1])
            k.ancorar(x, y)
            k.pos = (round(k.x), round(k.y))                    # pixel inteiro
            while marcas and u >= marcas[0]:
                marcas.pop(0)
                k.fantasma(cor=cor_fantasma)
            if u >= 1:
                _acabar()
                return False
        except Exception as ex:
            print(f"[cenas] mover: {ex}")
            _acabar()
            return False
    return Clock.schedule_interval(_p, 1 / 60.)


# ═══════════════════════════════════════════════════════════════════
#  ENQUADRAMENTO (o boneco, com as espadas, nunca sai do quadro)
# ═══════════════════════════════════════════════════════════════════
def _ext(k, poses):
    """Maior extensao (esq, baixo, dir, cima) das poses a partir da ancora,
    na orientacao atual do boneco (espelhado ou nao)."""
    e = [0.0, 0.0, 0.0, 0.0]
    for p in poses:
        for i, v in enumerate(k.extensao(p)):
            e[i] = max(e[i], v)
    return e


def _no_quadro(k, x, y, poses, area, m=0.0):
    """(x, y) da ancora ajustado para todas as `poses` caberem na area."""
    esq, baixo, dir_, cima = _ext(k, poses)
    x0, y0, x1, y1 = area
    lo, hi = x0 + m + esq, x1 - m - dir_
    x = (lo + hi) / 2.0 if lo > hi else min(hi, max(lo, x))
    lo, hi = y0 + m + baixo, y1 - m - cima
    y = (lo + hi) / 2.0 if lo > hi else min(hi, max(lo, y))
    return x, y


def _dentro_girado(k, x, y, area, m=0.0):
    """(x, y) da ancora ajustado para a pose atual, com o giro atual (em
    torno da ancora), caber na area."""
    esq, baixo, dir_, cima = k.extensao()
    a = math.radians(k.rotacao)
    ca, sa = math.cos(a), math.sin(a)
    xs, ys = [], []
    for dx, dy in ((-esq, -baixo), (dir_, -baixo), (-esq, cima), (dir_, cima)):
        xs.append(dx * ca - dy * sa)
        ys.append(dx * sa + dy * ca)
    x0, y0, x1, y1 = area
    lo, hi = x0 + m - min(xs), x1 - m - max(xs)
    x = (lo + hi) / 2.0 if lo > hi else min(hi, max(lo, x))
    lo, hi = y0 + m - min(ys), y1 - m - max(ys)
    y = (lo + hi) / 2.0 if lo > hi else min(hi, max(lo, y))
    return x, y


def _arco(y_de, y_para, altura, teto):
    """Altura do arco limitada para o ponto mais alto nao passar do teto."""
    return max(0.0, min(altura, teto - max(y_de, y_para)))


# ═══════════════════════════════════════════════════════════════════
#  EFEITOS DE CENA: camera, clarao, fundo, aneis, teleporte
# ═══════════════════════════════════════════════════════════════════
class _Camera:
    """Zoom da tela toda (infinito, titulo e Kirito juntos) em volta de um
    ponto: enquadramento de cinema nos momentos fortes."""

    def __init__(self, tela):
        self.tela = tela
        self._ev = None
        self.zoom = 1.0
        self.foco = (tela.width / 2.0, tela.height / 2.0)
        self._sc = Scale(1, 1, 1)
        try:
            tela.canvas.before.add(self._sc)       # depois do Translate da tela
        except Exception as e:
            print(f"[camera] {e}")
            self._sc = None

    def ir(self, zoom, foco=None, dur=0.6, foco_fn=None):
        if self._sc is None:
            return
        if self._ev is not None:
            self._ev.cancel()
        z0, f0 = self.zoom, self.foco
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur) if dur > 0 else 1.0
                e = u * u * (3 - 2 * u)
                alvo = foco_fn() if foco_fn else (foco or f0)
                self.zoom = z0 + (zoom - z0) * e
                self.foco = (f0[0] + (alvo[0] - f0[0]) * e, f0[1] + (alvo[1] - f0[1]) * e)
                if self._sc is not None:
                    self._sc.origin = self.foco
                    self._sc.x = self._sc.y = self.zoom
                if u >= 1:
                    self._ev = None
                    return False
            except Exception as ex:
                print(f"[camera] {ex}")
                return False
        self._ev = Clock.schedule_interval(_p, 1 / 60.)

    def soltar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self._sc is not None:
            try:
                self.tela.canvas.before.remove(self._sc)
            except Exception:
                pass
            self._sc = None


def _brilho_tela(camada, alfa=0.35, dur=0.18, cor=BRANCO, atras=None):
    """Clarao na tela inteira (impacto). Apaga em 3 DEGRAUS (forte, meio,
    fraco), como nos jogos de pixel - sem veu cinza sumindo devagar.
    atras = widget: o clarao fica atras dele (so o fundo acende)."""
    try:
        W, H = camada.size
        w = Widget(size_hint=(None, None), size=(0, 0))
        with w.canvas:
            c = Color(cor[0], cor[1], cor[2], alfa)
            Rectangle(pos=(-W, -H), size=(W * 3, H * 3))
        if atras is not None and atras in camada.children:
            camada.add_widget(w, index=camada.children.index(atras) + 1)
        else:
            camada.add_widget(w)
        t = [0.0]

        def _p(dt):
            t[0] += dt
            u = t[0] / dur
            c.a = alfa * (1.0 if u < 0.34 else (0.5 if u < 0.67 else 0.2))
            if t[0] >= dur:
                if w.parent:
                    w.parent.remove_widget(w)
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[cena] clarao: {e}")


def _fundo(tela, reator=None, barra=None, dur=0.6):
    """Escurece/acende o fundo da loading (infinito e barra): durante a luta
    o foco fica no Kirito e no titulo."""
    try:
        from kivy.animation import Animation
        ids = getattr(tela, 'ids', {})
        for nome, alvo in (('reator_shader', reator), ('barra_loading', barra)):
            w = ids.get(nome) if hasattr(ids, 'get') else None
            if w is not None and alvo is not None:
                Animation.cancel_all(w, 'opacity')
                Animation(opacity=alvo, duration=dur).start(w)
    except Exception as e:
        print(f"[cena] fundo: {e}")


# ═══════════════════════════════════════════════════════════════════
#  EFEITOS EM PIXEL ART (mesmo tamanho de pixel do Yoru em cena)
# ═══════════════════════════════════════════════════════════════════
_PX = [2.0]          # tamanho do pixel dos efeitos: o texel do Yoru da cena atual


def _cores_efeito(cor, brilho=0.5):
    """Paleta curta de um efeito: brilho (cor translucida), cor, claro e luz."""
    clara = tuple(c + (1 - c) * 0.55 for c in cor)
    return (('brilho', (cor[0], cor[1], cor[2], brilho)), ('cor', (cor[0], cor[1], cor[2], 1.0)),
            ('clara', (clara[0], clara[1], clara[2], 1.0)), ('luz', (1.0, 1.0, 1.0, 1.0)))


class _EfeitoPixel(Widget):
    """Efeito desenhado em pixels quadrados (poucas cores, um Mesh por cor).
    desenha(t, pontos, u) enche {cor: [(x, y, w, h)]} a cada quadro; some
    sozinho depois de `dur`."""

    def __init__(self, cores, dur, desenha, on_fim=None, por_s=30, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.u = max(1.0, _PX[0])
        self.dur = dur
        self.t = 0.0
        self._desenha = desenha
        self._on_fim = _Uma(on_fim)
        self._lote = K.LotePixels(self.canvas, cores)
        self._passo = -1
        self._por_s = por_s
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            self.t += dt
            if self.t >= self.dur or self.parent is None:
                return self.parar()
            # desenho novo 30 vezes por segundo (cada um fica 2 quadros, como
            # animacao desenhada): metade da conta e o mesmo movimento
            passo = int(self.t * self._por_s)
            if passo == self._passo:
                return
            self._passo = passo
            p = {}
            self._desenha(self.t, p, self.u)
            self._lote.desenhar(p)
        except Exception as e:
            print(f"[efeito] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)
        self._on_fim()
        return False


class CorteMeiaLua(_EfeitoPixel):
    """Meia-lua do corte em PIXEL ART (mesma forma e tempo da versao lisa):
    crescente grosso perto da ponta que avanca, borda de fora branca, corpo
    na cor do golpe e brilho em volta; depois recolhe para a ponta,
    ralando em xadrez."""

    def __init__(self, centro, raio, ang_ini, ang_fim, espessura, cor=CIANO, dur_cheio=4 / 30.0,
                 dur_decai=3 / 30.0, on_fim=None, achat=1.0, rotacao=0.0, **kwargs):
        self.c = centro
        self.r = float(raio)
        self.a0, self.a1 = math.radians(ang_ini), math.radians(ang_fim)
        self.e = float(espessura)
        self.achat = float(achat)
        rot = math.radians(rotacao)
        self.cr, self.sr = math.cos(rot), math.sin(rot)
        self.dc, self.dd = dur_cheio, dur_decai
        self._pre = None
        super().__init__(_cores_efeito(cor, 0.45), dur_cheio + dur_decai, self._forma, on_fim, **kwargs)

    def _prepara(self, u):
        self._pre = (u, _geometria_meialua(self.c, self.r, self.a0, self.a1, self.e, self.achat,
                                           self.cr, self.sr, u))

    def _forma(self, t, p, u):
        if t < self.dc:
            s0, s1, gros, rala = 0.0, min(1.0, t / (1.3 / 30.0)), 1.0, 0.0
        else:
            k = min(1.0, (t - self.dc) / self.dd)
            s0, s1, gros, rala = 0.15 + 0.55 * k, 1.0, (1 - k) ** 1.4, 0.75 * k
        if self._pre is None or self._pre[0] != u:
            self._prepara(u)
        listas = {}
        lim = u * 0.6
        for s, gmax, cel in self._pre[1]:
            if s < s0 or s > s1 or not cel:
                continue
            g = gmax * gros
            if g < lim:
                continue
            nr = int(g / u) + 2
            n5, n3 = max(1, nr // 5), max(2, nr // 3)
            for j, x, y, h in cel:
                if j >= nr:
                    break
                if rala and h < rala:
                    continue
                if j == 0 or j == nr - 1:
                    nome = 'brilho'
                elif j <= n5:
                    nome = 'luz'
                elif j <= n3:
                    nome = 'clara'
                else:
                    nome = 'cor' if s > 0.25 else 'brilho'
                lst = listas.get(nome)
                if lst is None:
                    lst = listas[nome] = p.setdefault(nome, [])
                lst.append((x, y, u, u))


_GEO_MEIALUA = OrderedDict()


def _geometria_meialua(c, r, a0, a1, e, achat, cr, sr, u):
    """A forma de uma meia-lua e sempre a mesma: calcula UMA vez onde cai
    cada pixel (ao longo do arco e de fora para dentro), ja sem os repetidos;
    cada desenho so escolhe quais aparecem (antes eram ~12 mil contas por
    desenho e a meia-lua gigante do final dava tranco no celular)."""
    chave = (round(c[0], 1), round(c[1], 1), round(r, 1), round(a0, 4), round(a1, 4), round(e, 1),
             round(achat, 3), round(cr, 4), round(sr, 4), round(u, 2))
    pre = _GEO_MEIALUA.get(chave)
    if pre is not None:
        return pre
    cx, cy = c
    arco = abs(a1 - a0) * r
    n = max(6, int(arco / u) + 1)
    vistos = set()
    pre = []
    for i in range(n + 1):
        s = i / float(n)
        gmax = e * (math.sin(math.pi * s) ** 0.75) * (0.45 + 0.55 * s)
        cel = []
        if gmax >= u * 0.6:
            a = a0 + (a1 - a0) * s
            ca, sa = math.cos(a), math.sin(a) * achat
            ext = r + gmax * 0.1 + u
            for j in range(int(gmax / u) + 2):
                rad = ext - j * u
                xe, ye = ca * rad, sa * rad
                gx = math.floor((cx + xe * cr - ye * sr) / u)
                gy = math.floor((cy + xe * sr + ye * cr) / u)
                k = gx * 100003 + gy
                if k in vistos:
                    continue
                vistos.add(k)
                cel.append((j, gx * u, gy * u, ((gx * 7 + gy * 13) % 10) / 10.0))
        pre.append((s, gmax, cel))
    _GEO_MEIALUA[chave] = pre
    while len(_GEO_MEIALUA) > 24:
        _GEO_MEIALUA.popitem(last=False)
    return pre


def preparar_meialua(centro, raio, ang_ini, ang_fim, espessura, achat=1.0, rotacao=0.0):
    """Calcula antes (fora da hora do golpe) a forma de uma meia-lua grande."""
    rot = math.radians(rotacao)
    _geometria_meialua(centro, float(raio), math.radians(ang_ini), math.radians(ang_fim), float(espessura),
                       float(achat), math.cos(rot), math.sin(rot), max(1.0, _PX[0]))


def _anel(camada, centro, r0, r1, dur, cor=CIANO, esp=None, achat=1.0, grao=1):
    """Onda de choque em pixels: anel que abre (desacelerando), afina e some
    ralando em xadrez. grao = pixel do anel em pixels do Yoru (anel grande
    com pixel mais grosso custa bem menos conta no celular)."""
    try:
        cx, cy = centro
        e0 = esp or dp(3)

        def forma(t, p, u):
            u = u * grao
            k = min(1.0, t / dur)
            e = 1 - (1 - k) ** 3
            r = r0 + (r1 - r0) * e
            g = max(u, e0 * 1.4 * (1 - k))
            # anel enorme: pixel um pouco maior (senao passa do limite de um desenho)
            u = u * max(1, int(math.ceil(math.sqrt(2 * math.pi * r * (g + u) / (u * u * 9000.0)))))
            g = max(u, g)
            n = max(12, int(2 * math.pi * r / u) + 1)
            vistos = set()
            for i in range(n):
                a = 2 * math.pi * i / n
                ca, sa = math.cos(a), math.sin(a) * achat
                for j in range(int(g / u) + 1):
                    rad = r - j * u
                    gx, gy = math.floor((cx + ca * rad) / u), math.floor((cy + sa * rad) / u)
                    if (gx, gy) in vistos:
                        continue
                    vistos.add((gx, gy))
                    if k > 0.5 and ((gx * 5 + gy * 11) % 10) / 10.0 < (k - 0.5) * 1.6:
                        continue
                    nome = ('luz' if k < 0.35 else 'clara') if j == 0 else 'cor'
                    p.setdefault(nome, []).append((gx * u, gy * u, u, u))
        camada.add_widget(_EfeitoPixel(_cores_efeito(cor), dur, forma))
    except Exception as e:
        print(f"[cena] anel: {e}")


_TEX_COLUNA = None


_TEX_BRILHO = None


def _textura_radial():
    """Brilho pixel art: miolo forte, aneis intermediarios e pixels de fora,
    tudo com borda definida (textura pequena ampliada sem suavizar)."""
    global _TEX_BRILHO
    if _TEX_BRILHO is None:
        # comprida (32 x 8) porque a aura acompanha a lamina: os "pixels" do
        # brilho ficam quase quadrados depois de esticados
        nw, nh = 32, 8
        buf = bytearray(nw * nh * 4)
        cx, cy = (nw - 1) / 2.0, (nh - 1) / 2.0
        for y in range(nh):
            for x in range(nw):
                d = math.hypot((x - cx) / (nw / 2.0), (y - cy) / (nh / 2.0))
                a = 255 if d < 0.34 else (150 if d < 0.62 else (60 if d < 0.9 else 0))
                if 0.62 <= d < 0.9 and (x + y) % 2:          # anel de fora pontilhado
                    a = 0
                i = (y * nw + x) * 4
                buf[i] = buf[i + 1] = buf[i + 2] = 255
                buf[i + 3] = a
        dados = bytes(buf)
        tex = Texture.create(size=(nw, nh), colorfmt='rgba')
        tex.mag_filter = 'nearest'
        tex.min_filter = 'nearest'
        tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
        tex.add_reload_observer(lambda t: t.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte'))
        _TEX_BRILHO = tex
    return _TEX_BRILHO


def _estrela(camada, x, y, u, cor=CIANO, raios=5, dur=0.14):
    """Estrela de impacto em pixels: miolo branco 2x2 e 4 raios (mais 4
    diagonais curtos) que crescem num instante e somem em degraus."""
    try:
        w = Widget(size_hint=(None, None), size=(0, 0))
        pecas = []
        with w.canvas:
            c_raio = Color(cor[0], cor[1], cor[2], 1)
            for dx, dy, n in ((1, 0, raios), (-1, 0, raios), (0, 1, raios), (0, -1, raios),
                              (1, 1, 2), (-1, 1, 2), (1, -1, 2), (-1, -1, 2)):
                for j in range(1, n + 1):
                    pecas.append((Rectangle(size=(0, 0)), dx, dy, j, n))
            c_miolo = Color(1, 1, 1, 1)
            miolo = Rectangle(pos=(round(x / u) * u - u, round(y / u) * u - u), size=(2 * u, 2 * u))
        camada.add_widget(w)
        x0, y0 = round(x / u) * u, round(y / u) * u
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                k = t[0] / dur
                alcance = min(1.0, k * 2.5)                  # cresce rapido
                for r, dx, dy, j, n in pecas:
                    if j <= int(round(alcance * n)) and j > int(k * n) - 1:
                        r.pos = (x0 + dx * j * u - u / 2, y0 + dy * j * u - u / 2)
                        r.size = (u, u)
                    else:
                        r.size = (0, 0)
                c_raio.a = 1.0 if k < 0.6 else 0.5
                c_miolo.a = 1.0 if k < 0.5 else 0.0
                if k >= 1:
                    if w.parent:
                        w.parent.remove_widget(w)
                    return False
            except Exception:
                if w.parent:
                    w.parent.remove_widget(w)
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[cena] estrela: {e}")


def _faixas(k, camada, dur, entrando, on_fim=None, cor=CIANO, escuro=False, barra=True):
    """Entrada e saida por quadros, sem transparencia e sem esticar o desenho:
    o boneco se monta (entrando) ou se desfaz (saindo) em faixas de 1 texel,
    de baixo para cima, 30 degraus por segundo, com uma barra de luz de
    pixels na emenda. Entrando ele nasce branco (ou escuro, saindo da
    sombra) e ganha cor em 3 degraus; saindo fica branco em 2 degraus antes
    de comecar a sumir."""
    fim = _Uma(on_fim)
    te = k.ps / float(K.R)
    antes = tuple(k._cor_clarao.rgb)

    def _pronto(visivel):
        k.recortar()
        k.clarao = 0.0
        k._cor_clarao.rgb = antes
        k.opacity = 1.0 if visivel else 0.0
        fim()
    try:
        ax, ay = k.ancora()
        esq, baixo, dir_, cima = k.extensao()
        base = ay - baixo - te
        topo = ay + cima + te
        larg = max(te * 8, (esq + dir_) * 0.8)
        n = max(4, int(round(dur * 30)))
        pre, pos = (0, 3) if entrando else (2, 0)
        total = pre + n + pos
        if escuro:
            k._cor_clarao.rgb = (0.05, 0.02, 0.1)

        def emenda(d):
            i = min(n, max(0, d - pre + 1))
            return base + math.floor((topo - base) * i / float(n) / te) * te

        if entrando:
            k.opacity = 1.0
            k.clarao = 1.0
            k.recortar(None, base)
        if barra:
            def forma(t, p, u):
                d = int(t * 30)
                if not (pre <= d < pre + n):
                    return
                y = math.floor(emenda(d) / u) * u
                x0 = math.floor((ax - larg / 2.0) / u)
                x1 = math.floor((ax + larg / 2.0) / u)
                borda = max(1, (x1 - x0) // 5)
                for gx in range(x0, x1 + 1):
                    ponta = gx - x0 < borda or x1 - gx < borda
                    if ponta and (gx + d) % 2:
                        continue                    # pontas da barra ralando em xadrez
                    p.setdefault('cor' if ponta else 'luz', []).append((gx * u, y, u, u))
                    if not ponta:
                        p.setdefault('clara', []).append((gx * u, y - u, u, u))
            camada.add_widget(_EfeitoPixel(_cores_efeito(cor), total / 30.0 + 0.05, forma))
        passo = [-1]
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                d = int(t[0] * 30)
                if d == passo[0]:
                    return True
                passo[0] = d
                if d >= total:
                    _pronto(entrando)
                    return False
                if d < pre:                                   # saindo: clareia em 2 degraus
                    k.clarao = 0.5 if d == 0 else 1.0
                elif d < pre + n:
                    e = emenda(d)
                    if entrando:
                        k.recortar(None, e)
                    else:
                        k.recortar(e, None)
                else:                                         # entrando: ganha cor em 3 degraus
                    k.recortar()
                    k.clarao = (2, 1, 0)[min(2, d - pre - n)] / 3.0
                return True
            except Exception as e:
                print(f"[cena] faixas: {e}")
                _pronto(entrando)
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[cena] faixas ignorado: {e}")
        _pronto(entrando)


def _teleporte(k, camada, faiscas, on_fim=None, cor=CIANO, dur=0.55, teto=None):
    """Como o cristal de teleporte de SAO, em pixel art: anel de luz nos pes,
    o boneco fica branco e se desfaz em faixas de baixo para cima dentro de
    uma coluna de luz de pixels, soltando faiscas. Nao sai do lugar, nao
    estica e nao fica transparente."""
    fim = _Uma(on_fim)
    try:
        ax, ay = k.ancora()
        esq, baixo, dir_, cima = k.extensao()
        base = ay - baixo
        alt = (baixo + cima) * 1.45
        if teto is not None:
            alt = max(dp(20), min(alt, teto - base))
        larg = max(dp(14), (esq + dir_) * 0.55)

        def forma(t, p, u):
            v = min(1.0, t / dur)
            # anel nos pes: elipse de pixels que abre e rala
            ra = larg * (0.6 + 1.2 * v)
            rb = dp(3) + v * dp(4)
            n = max(12, int(2 * math.pi * ra / u))
            for i in range(n):
                a = 2 * math.pi * i / n
                gx = math.floor((ax + math.cos(a) * ra) / u)
                gy = math.floor((base + math.sin(a) * rb) / u)
                if ((gx * 7 + gy * 3) % 10) / 10.0 < v:
                    continue
                p.setdefault('clara' if i % 3 else 'luz', []).append((gx * u, gy * u, u, u))
            # coluna de luz: miolo branco, corpo na cor, bordas em xadrez
            f = min(1.0, v / 0.15) * (1 - max(0.0, (v - 0.6) / 0.4))
            if f <= 0:
                return
            h = alt * min(1.0, v / 0.3)
            lw = larg * 0.7 * (1 - 0.6 * max(0.0, (v - 0.45) / 0.55))
            x0 = math.floor((ax - lw / 2.0) / u)
            x1 = math.floor((ax + lw / 2.0) / u)
            y0 = math.floor(base / u)
            yt = math.floor((base + h) / u)
            meio = (x0 + x1) / 2.0
            for gx in range(x0, x1 + 1):
                d = abs(gx - meio) / max(1.0, (x1 - x0) / 2.0)
                nome = 'luz' if d < 0.22 else ('clara' if d < 0.45 else 'cor')
                if nome == 'cor' or f < 0.7:
                    for gy in range(y0, yt + 1):       # borda (ou coluna sumindo) em xadrez
                        if (gx + gy) % 2 == 0 and ((gx * 5 + gy * 9) % 10) / 10.0 < f:
                            p.setdefault(nome, []).append((gx * u, gy * u, u, u))
                else:
                    p.setdefault(nome, []).append((gx * u, y0 * u, u, (yt - y0 + 1) * u))
        camada.add_widget(_EfeitoPixel(_cores_efeito(cor), dur, forma))
        _som('teleporte')
        t = [0.0]
        cont = [0]

        def _p(dt):
            try:
                t[0] += dt
                cont[0] += 1
                if cont[0] % 3 == 0 and t[0] < dur * 0.85:
                    faiscas.estourar(ax + random.uniform(-larg * 0.4, larg * 0.4),
                                     base + random.uniform(0, (baixo + cima) * 0.9),
                                     random.choice((cor, BRANCO)), n=2,
                                     forca=dp(30), tam=max(2, k.ps * 0.8), gravidade=-dp(260))
                return t[0] < dur
            except Exception:
                return False
        Clock.schedule_interval(_p, 1 / 60.)
        _faixas(k, camada, dur * 0.8, False, on_fim=fim, cor=cor, barra=False)
    except Exception as e:
        print(f"[cena] teleporte ignorado: {e}")
        k.opacity = 0
        fim()


def _materializar(k, camada, faiscas, dur=0.32, on_fim=None, cor=CIANO):
    """Entrada de teleporte (o contrario do _teleporte): um anel de pixels se
    fecha nos pes, faiscas caem para o boneco e ele se monta em faixas de
    baixo para cima, branco, ganhando cor em degraus."""
    fim = _Uma(on_fim)
    try:
        ax, ay = k.ancora()
        esq, baixo, dir_, cima = k.extensao()
        r = max(esq + dir_, baixo + cima) * 0.7
        _som('materializa')

        def forma(t, p, u):
            v = min(1.0, t / dur)
            rr = max(u, r * (1 - v))
            n = max(10, int(2 * math.pi * rr / u))
            for i in range(n):
                a = 2 * math.pi * i / n
                gx = math.floor((ax + math.cos(a) * rr) / u)
                gy = math.floor((ay + math.sin(a) * rr) / u)
                p.setdefault('luz' if v > 0.6 else 'clara', []).append((gx * u, gy * u, u, u))
                if v < 0.6 and i % 2 == 0:
                    gx2 = math.floor((ax + math.cos(a) * (rr + u)) / u)
                    gy2 = math.floor((ay + math.sin(a) * (rr + u)) / u)
                    p.setdefault('cor', []).append((gx2 * u, gy2 * u, u, u))
        camada.add_widget(_EfeitoPixel(_cores_efeito(cor), dur, forma))
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur)
                rr = max(1.0, r * (1 - u))
                if random.random() < 0.6:
                    ang = random.uniform(0, 2 * math.pi)
                    faiscas.estourar(ax + math.cos(ang) * rr, ay + math.sin(ang) * rr,
                                     random.choice((cor, BRANCO)), n=1, forca=dp(20),
                                     tam=max(2, k.ps * 0.7), gravidade=0)
                if u >= 1:
                    faiscas.estourar(ax, ay, cor, n=10, forca=dp(90), tam=max(2, k.ps * 0.8))
                    return False
                return True
            except Exception:
                return False
        Clock.schedule_interval(_p, 1 / 60.)
        _faixas(k, camada, dur, True, on_fim=fim, cor=cor)
    except Exception as e:
        print(f"[cena] materializar ignorado: {e}")
        k.opacity = 1.0
        k.clarao = 0.0
        fim()


# ═══════════════════════════════════════════════════════════════════
#  GOLPE FINAL: aura da espada, fluxo do infinito e onda de energia
# ═══════════════════════════════════════════════════════════════════
class _AuraEspada(Widget):
    """Brilho de reiatsu em volta da lamina da espada fundida: acompanha o
    Kirito a cada quadro e solta faiscas subindo. `alvo` 0..1 (forca)."""

    def __init__(self, k, faiscas, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k = k
        self.faiscas = faiscas
        self.faiscas_fundo = None        # particulas atras do boneco (profundidade)
        self.forca = 0.0
        self.alvo = 0.0
        self._t = 0.0
        tex = _textura_radial()
        with self.canvas:
            PushMatrix()
            self._rot = Rotate(angle=0, origin=(0, 0))
            self._c1 = Color(0.2, 0.85, 1.0, 0)
            self._r1 = Rectangle(texture=tex, size=(0, 0))
            self._c2 = Color(0.85, 1.0, 1.0, 0)
            self._r2 = Rectangle(texture=tex, size=(0, 0))
            PopMatrix()
        # forma Mugetsu: nevoa de pixels azul e roxa subindo das bordas da lamina
        self._fios = []
        self._lote = K.LotePixels(self.canvas, (
            ('azul', (0.36, 0.56, 1.0, 0.95)), ('azul2', (0.60, 0.80, 1.0, 0.95)),
            ('roxo', (0.62, 0.32, 1.0, 0.95)), ('lilas', (0.84, 0.68, 1.0, 0.95)),
            ('fundo', (0.30, 0.14, 0.62, 0.8))))
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            self._t += dt
            self.forca += (self.alvo - self.forca) * (1 - math.exp(-dt * 5))
            k = self.k
            p = k._base
            if (k.parent is None or k.opacity < 0.05 or p.get('a1') is None
                    or p.get('tipo1', 1) < 3 or self.forca < 0.01):
                self._c1.a = self._c2.a = 0
                k.luz = 0.0
                if self._fios:
                    self._fios = []
                    self._lote.desenhar({})
                return
            k.luz = self.forca                          # a energia ilumina o corpo
            if getattr(k, '_desenho', None) is not None:
                # Bankai (desenho da referencia): a lamina ja tem o fio roxo
                # aceso - nada do brilho esticado/girado (virava xadrez); so os
                # fiapos de energia na grade de pixels e as faiscas subindo
                self._c1.a = self._c2.a = 0
                hx, hy = k.ponto_mao(1)
                tx, ty = k.ponta_espada(1)
                f = self.forca
                self._nevoa(dt, k, hx, hy, tx, ty, math.hypot(tx - hx, ty - hy) or 1.0, f)
                if random.random() < f * 0.6:
                    s = random.random()
                    k_ps = k.ps
                    self.faiscas.estourar(hx + (tx - hx) * s, hy + (ty - hy) * s,
                                          random.choice((ROXO, (0.85, 0.75, 1.0))), n=1,
                                          forca=dp(28), tam=max(2, k_ps * 0.6), gravidade=-dp(240))
                return
            mug = p.get('mugetsu')
            if mug != getattr(self, '_mug', None):      # Mugetsu: aura roxa por fora, azul por dentro
                self._mug = mug
                self._c1.rgb = (0.52, 0.26, 1.0) if mug else (0.2, 0.85, 1.0)
                self._c2.rgb = (0.55, 0.72, 1.0) if mug else (0.85, 1.0, 1.0)
            hx, hy = k.ponto_mao(1)
            tx, ty = k.ponta_espada(1)
            comp = math.hypot(tx - hx, ty - hy) or 1.0
            ang = math.degrees(math.atan2(ty - hy, tx - hx))
            cx, cy = (hx + tx) / 2.0, (hy + ty) / 2.0
            f = self.forca
            tremor = 0.85 + 0.15 * math.sin(self._t * 23) + 0.05 * random.random()
            self._rot.origin = (cx, cy)
            self._rot.angle = ang
            l1, w1 = comp * 1.3, k.ps * ((8 + 7 * f) if mug else (6 + 6 * f))
            self._r1.pos, self._r1.size = (cx - l1 / 2, cy - w1 / 2), (l1, w1)
            self._c1.a = (0.75 if mug else 0.55) * f * tremor
            self._nevoa(dt, k, hx, hy, tx, ty, comp, f if mug else 0.0)
            l2, w2 = comp * 1.08, k.ps * (2 + 2 * f)
            self._r2.pos, self._r2.size = (cx - l2 / 2, cy - w2 / 2), (l2, w2)
            self._c2.a = 0.75 * f * tremor
            if random.random() < f * 0.8:          # reiatsu subindo da lamina
                s = random.random()
                atras = self.faiscas_fundo is not None and random.random() < 0.45
                alvo = self.faiscas_fundo if atras else self.faiscas
                if mug:
                    cor = (0.28, 0.12, 0.55) if atras else random.choice((ROXO, AZUL, (0.85, 0.75, 1.0)))
                else:
                    cor = (0.1, 0.3, 0.6) if atras else random.choice((CIANO, BRANCO, (0.12, 0.25, 0.6)))
                alvo.estourar(hx + (tx - hx) * s, hy + (ty - hy) * s, cor, n=1,
                              forca=dp(28), tam=max(2, k.ps * (0.5 if atras else 0.6)),
                              gravidade=-dp(170 if atras else 240))
        except Exception as e:
            print(f"[aura] {e}")
            self._c1.a = self._c2.a = 0

    def _nevoa(self, dt, k, hx, hy, tx, ty, comp, f):
        """Aura da espada na forma Mugetsu: fiapos curtos azuis e roxos,
        misturados, que nascem nas duas bordas da lamina e sobem ondulando
        (na grade de pixels do Yoru)."""
        if f < 0.05:
            if self._fios:
                self._fios = []
                self._lote.desenhar({})
            return
        te = k.ps / float(K.R)
        while len(self._fios) < int(30 * f):
            self._fios.append({'s': random.uniform(0.14, 1.02), 'lado': random.choice((-1, 1)), 't': 0.0,
                               'vida': random.uniform(0.25, 0.5), 'alt': random.uniform(4, 10),
                               'fase': random.uniform(0, 6.3),
                               'cor': random.choice(('azul', 'azul2', 'roxo', 'roxo', 'lilas'))})
        ux, uy = (tx - hx) / comp, (ty - hy) / comp
        nx, ny = -uy, ux
        pontos = {}
        vivos = []
        for w in self._fios:
            w['t'] += dt
            v = w['t'] / w['vida']
            if v >= 1.0:
                continue
            vivos.append(w)
            afasta = (7.5 + 2.0 * v) * te * w['lado']
            bx = hx + (tx - hx) * w['s'] + nx * afasta
            by = hy + (ty - hy) * w['s'] + ny * afasta
            alt = w['alt'] * math.sin(math.pi * v)
            n = int(alt) + 1
            for i in range(n):
                u = i / float(max(1, n))
                x = bx + math.sin(w['fase'] + self._t * 12.0 - u * 3.0) * 1.4 * te * u
                y = by + i * te
                X = k.x + math.floor((x - k.x) / te) * te
                Y = k.y + math.floor((y - k.y) / te) * te
                larg = 2 if u < 0.35 else 1
                pontos.setdefault(w['cor'] if u < 0.75 else 'fundo', []).append((X, Y, larg * te, te))
        self._fios = vivos
        self._lote.desenhar(pontos, min(1.0, f * 1.3))

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)


class _Trevas(Widget):
    """Golpe final Mugetsu: a escuridao sai dele e cobre a tela (circulo de
    blocos com a borda roxa rendilhada), fica tudo preto - so ele, o fogo e
    os olhos brilham -, o corte risca uma linha de luz de um lado ao outro
    na altura da frase e, depois de um instante congelado, a escuridao se
    abre nessa linha (a fenda cresce, as bordas racham em cacos e somem),
    revelando a frase gravada dentro do corte.
    crescer(x, y) -> cobrir; cortar(y) -> linha; abrir() -> fenda e some."""
    CORES = (('preto', (0.0, 0.0, 0.02, 1.0)), ('borda', (0.12, 0.03, 0.24, 1.0)),
             ('borda2', (0.34, 0.12, 0.62, 1.0)), ('brilho', (0.66, 0.40, 1.0, 0.9)),
             ('luz', (1.0, 0.97, 1.0, 1.0)))

    def __init__(self, bloco, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.b = max(2.0, bloco)
        self._lote = K.LotePixels(self.canvas, self.CORES)
        self.estado = None
        self.t = 0.0
        self.alfa = 1.0
        self._cacos = []
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def crescer(self, x, y, dur=0.7):
        self.estado, self.t, self.cx, self.cy, self.dur = 'cresce', 0.0, x, y, dur

    def cortar(self, y):
        self.linha_y = y
        self.estado, self.t = 'linha', 0.0

    def abrir(self, dur=0.55):
        self.estado, self.t, self.dur = 'abre', 0.0, dur
        W, H = Window.size
        b = self.b
        rnd = random.Random(3)
        for i in range(int(W / b) + 1):                    # cacos das bordas da fenda
            for lado in (1, -1):
                if rnd.random() < 0.55:
                    self._cacos.append({'x': i * b, 'lado': lado, 'vy': rnd.uniform(60, 260) * lado,
                                        'vx': rnd.uniform(-40, 40), 't0': rnd.uniform(0, 0.15),
                                        'tam': rnd.choice((1, 1, 2))})

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            if self.estado is None:
                return
            self.t += dt
            W, H = Window.size
            b = self.b
            p = {}

            def rt(cor, x, y, w, h):
                p.setdefault(cor, []).append((x, y, w, h))
            if self.estado == 'cresce':
                u = min(1.0, self.t / self.dur)
                u = u * u * (3 - 2 * u)
                rmax = max(math.hypot(self.cx - x, self.cy - y) for x in (0, W) for y in (0, H)) + b * 3
                r = rmax * u
                y = 0.0
                while y < H:
                    dy = abs(y + b / 2.0 - self.cy)
                    if dy < r:
                        meia = math.sqrt(r * r - dy * dy)
                        x0 = math.floor((self.cx - meia) / b) * b
                        x1 = math.ceil((self.cx + meia) / b) * b
                        rt('preto', x0, y, x1 - x0, b)
                        # borda: onda roxa acesa em volta do circulo (3 blocos) com
                        # blocos soltos na frente, piscando
                        for s in (-1, 1):
                            xb = x0 - b if s < 0 else x1
                            rt('borda', xb, y, b, b)
                            rt('borda2', xb + s * b, y, b, b)
                            if int((y / b) + self.t * 24) % 3:
                                rt('brilho', xb + s * 2 * b, y, b, b)
                            if int((y / b) * 7 + self.t * 30) % 5 == 0:
                                rt('borda2', xb + s * 4 * b, y, b, b)
                    y += b
                if u >= 1.0:
                    self.estado = 'cheio'
            elif self.estado in ('cheio', 'linha'):
                rt('preto', 0, 0, W, H)
                if self.estado == 'linha':
                    yl = math.floor(self.linha_y / b) * b
                    k = min(1.0, self.t / 0.06)                 # o risco atravessa a tela num piscar
                    rt('brilho', 0, yl - b, W * k, b * 3)
                    rt('luz', 0, yl, W * k, b)
            elif self.estado == 'abre':
                u = min(1.0, self.t / self.dur)
                e = 1 - (1 - u) ** 3
                yl = math.floor(self.linha_y / b) * b
                gap = e * H * 0.9
                topo_ini = yl + b + gap / 2.0
                base_fim = yl - gap / 2.0
                self.alfa = 1.0 if u < 0.55 else max(0.0, 1 - (u - 0.55) / 0.45)
                rt('preto', 0, topo_ini, W, H - topo_ini)
                rt('preto', 0, 0, W, max(0.0, base_fim))
                # bordas da fenda: dentes roxos e a luz que esfria
                for i in range(int(W / b) + 1):
                    x = i * b
                    dente = ((i * 7) % 5) * b * 0.5
                    rt('borda2', x, topo_ini - dente, b, dente + b)
                    rt('borda2', x, base_fim, b, dente + b)
                if u < 0.35:
                    rt('luz', 0, topo_ini - b, W, b)
                    rt('luz', 0, base_fim, W, b)
                for c in self._cacos:
                    tc = self.t - c['t0']
                    if tc <= 0:
                        continue
                    y = (topo_ini if c['lado'] > 0 else base_fim) + c['vy'] * tc - 200 * tc * tc
                    x = c['x'] + c['vx'] * tc
                    rt('borda' if c['tam'] == 2 else 'borda2', math.floor(x / b) * b, math.floor(y / b) * b,
                       b * c['tam'], b * c['tam'])
                if u >= 1.0:
                    return self.parar()
            self._lote.desenhar(p, self.alfa)
        except Exception as e:
            print(f"[trevas] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)
        return False


class _OndaGetsuga(Widget):
    """Onda de energia em meia-lua (miolo escuro, brilho ciano e borda
    branca) varrendo a frase: o ultimo golpe da espada evoluida."""

    def __init__(self, x0, x1, cy, altura, dur, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.x0, self.x1, self.cy = x0, x1, cy
        self.R = altura / 2.0
        self.dur = dur
        self._t = 0.0
        n = 26
        self._n = n
        idx = list(range(2 * (n + 1)))
        with self.canvas:
            self._c_glow = Color(0.2, 0.85, 1.0, 0)
            self._m_glow = Mesh(mode='triangle_strip', indices=idx, vertices=[0] * (8 * (n + 1)))
            self._c_corpo = Color(0.02, 0.03, 0.08, 0)
            self._m_corpo = Mesh(mode='triangle_strip', indices=idx, vertices=[0] * (8 * (n + 1)))
            self._c_borda = Color(0.85, 1.0, 1.0, 0)
            self._borda = Line(points=[0, 0, 0, 0], width=dp(2.2))
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _crescente(self, cx, escala, espessura):
        """Meia-lua virada para a direita: ")" grossa no meio, fina nas pontas."""
        R = self.R * escala
        a = R * 0.42
        vs, borda = [], []
        for i in range(self._n + 1):
            t = -math.pi / 2 + math.pi * i / self._n
            ex, ey = cx + math.cos(t) * a, self.cy + math.sin(t) * R
            w = espessura * math.cos(t)
            ix, iy = ex - w, self.cy + math.sin(t) * R * 0.94
            vs.extend((ex, ey, 0, 0, ix, iy, 0, 0))
            borda.extend((ex, ey))
        return vs, borda

    def _tick(self, dt):
        try:
            self._t += dt
            u = min(1.0, self._t / self.dur)
            e = u * u * (3 - 2 * u)
            cx = self.x0 + (self.x1 - self.x0) * e
            aparece = min(1.0, self._t / 0.06)
            some = 1.0 - max(0.0, (self._t - self.dur) / 0.25)
            a = aparece * max(0.0, some)
            esp = self.R * 0.55
            vg, _ = self._crescente(cx, 1.22, esp * 1.35)
            vc, borda = self._crescente(cx, 1.0, esp)
            self._m_glow.vertices = vg
            self._m_corpo.vertices = vc
            self._borda.points = borda
            self._c_glow.a = 0.45 * a
            self._c_corpo.a = 0.92 * a
            self._c_borda.a = (0.8 + 0.2 * math.sin(self._t * 40)) * a
            if some <= 0:
                self.parar()
                return False
        except Exception as ex:
            print(f"[getsuga] {ex}")
            self.parar()
            return False

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)


# ═══════════════════════════════════════════════════════════════════
#  CORTE QUE GRAVA: a lamina deixa um arco de luz em pixel art (como nos
#  golpes da referencia) e as letras aparecem por onde ele passa.
# ═══════════════════════════════════════════════════════════════════
# fio (por fora), claro, cor da lamina, escuro, fundo (o rabo) e brilho
_PAL_CORTE = {
    'katana': ((1.0, 1.0, 1.0), (0.62, 0.92, 1.0), (0.22, 0.62, 1.0), (0.16, 0.30, 0.90),
               (0.30, 0.16, 0.66), (0.30, 0.70, 1.0)),
    'azul': ((0.92, 0.95, 1.0), (0.58, 0.72, 1.0), (0.28, 0.40, 1.0), (0.22, 0.20, 0.82),
             (0.34, 0.12, 0.60), (0.35, 0.45, 1.0)),
    'mug': ((1.0, 0.94, 1.0), (0.84, 0.66, 1.0), (0.52, 0.24, 0.95), (0.24, 0.08, 0.45),
            (0.05, 0.02, 0.09), (0.62, 0.30, 1.0)),
}


class ArcoCorte:
    """Caminho da ponta da lamina num corte: arco de circulo (centro, raio,
    angulo inicial e quanto gira). A mancha fica do lado de dentro (onde
    estao a mao e o corpo), com a grossura maxima `esp` (px)."""

    def __init__(self, cx, cy, R, a0, da, esp):
        self.cx, self.cy, self.R = cx, cy, R
        self.a0, self.da = a0, da
        self.esp = float(esp)
        self.comp = abs(da) * R

    @classmethod
    def por_bojo(cls, p0, p1, bojo, esp):
        """De p0 a p1 estufando para um lado (bojo = fracao da corda; > 0 =
        para a esquerda de quem vai de p0 a p1)."""
        (x0, y0), (x1, y1) = p0, p1
        c = math.hypot(x1 - x0, y1 - y0) or 1.0
        ux, uy = (x1 - x0) / c, (y1 - y0) / c
        nx, ny = -uy, ux
        b = bojo if abs(bojo) > 0.01 else 0.01
        h = b * c
        mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        return cls.por_tres(p0, (mx + nx * h, my + ny * h), p1, esp)

    @classmethod
    def por_tres(cls, p0, pm, p1, esp):
        """O arco que sai de p0, passa por pm e chega em p1."""
        (ax, ay), (bx, by), (qx, qy) = p0, pm, p1
        d = 2.0 * (ax * (by - qy) + bx * (qy - ay) + qx * (ay - by))
        if abs(d) < 1e-6:                               # alinhados: quase reto
            ux, uy = qx - ax, qy - ay
            c = math.hypot(ux, uy) or 1.0
            return cls.por_tres(p0, ((ax + qx) / 2.0 - uy / c * c * 0.01,
                                     (ay + qy) / 2.0 + ux / c * c * 0.01), p1, esp)
        a2, b2, q2 = ax * ax + ay * ay, bx * bx + by * by, qx * qx + qy * qy
        cx = (a2 * (by - qy) + b2 * (qy - ay) + q2 * (ay - by)) / d
        cy = (a2 * (qx - bx) + b2 * (ax - qx) + q2 * (bx - ax)) / d
        R = math.hypot(ax - cx, ay - cy)
        a0 = math.atan2(ay - cy, ax - cx)
        am = math.atan2(by - cy, bx - cx)
        a1 = math.atan2(qy - cy, qx - cx)
        dm = (am - a0) % (2 * math.pi)
        d1 = (a1 - a0) % (2 * math.pi)
        da = d1 if dm <= d1 else d1 - 2 * math.pi      # o lado que passa por pm
        return cls(cx, cy, R, a0, da, esp)

    @classmethod
    def pelo_meio(cls, centro, ang, comp, bojo, esp):
        """Arco cujo MEIO da mancha passa por `centro` (o meio da silaba),
        indo na direcao `ang` (graus), com a corda `comp`."""
        a = math.radians(ang)
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        sg = 1.0 if bojo > 0 else -1.0
        # o caminho da ponta fica por fora do meio da mancha (~0,4 da grossura)
        desl = -bojo * comp + sg * 0.4 * esp
        mx, my = centro[0] + nx * desl, centro[1] + ny * desl
        return cls.por_bojo((mx - dx * comp / 2.0, my - dy * comp / 2.0),
                            (mx + dx * comp / 2.0, my + dy * comp / 2.0), bojo, esp)

    def ponto(self, s, off=0.0):
        """Ponto em s (0..1 ao longo do corte), `off` px para fora (+) ou para
        dentro (-) do caminho da ponta."""
        a = self.a0 + self.da * s
        r = self.R + off
        return self.cx + math.cos(a) * r, self.cy + math.sin(a) * r

    def grossura(self, s):
        """Meia-lua: fina nas duas pontas, mais grossa depois do meio."""
        if s <= 0.0 or s >= 1.0:
            return 0.0
        return self.esp * (math.sin(math.pi * s) ** 0.7) * (0.45 + 0.55 * s)

    def local(self, x, y):
        """(s, off) de um ponto da tela."""
        dx, dy = x - self.cx, y - self.cy
        a = math.atan2(dy, dx) - self.a0
        if self.da < 0:
            a = -a
        a %= 2 * math.pi
        if a > math.pi + abs(self.da) / 2.0:
            a -= 2 * math.pi
        return a / abs(self.da), math.hypot(dx, dy) - self.R


_BAYER = ((-0.045, 0.015), (0.045, -0.015))     # pontilhado 2x2 nas bordas das faixas


def _desenho_corte(arco, pal, u):
    """Gerador que monta a mancha do corte em pixel art (grade de u px) aos
    poucos; no fim entrega (bytes RGBA, gx0, gy0, w, h). Fio branco por fora,
    miolo claro, corpo na cor da lamina e rabo escuro que se desfaz em
    xadrez (mais ralo perto do comeco do corte)."""
    xs, ys = [], []
    for i in range(41):
        s = i / 40.0
        for off in (2.5 * u, -arco.grossura(s) - u):
            x, y = arco.ponto(s, off)
            xs.append(x)
            ys.append(y)
    gx0, gx1 = int(math.floor(min(xs) / u)) - 1, int(math.floor(max(xs) / u)) + 2
    gy0, gy1 = int(math.floor(min(ys) / u)) - 1, int(math.floor(max(ys) / u)) + 2
    w, h = gx1 - gx0, gy1 - gy0
    buf = bytearray(w * h * 4)
    luz, clara, cor, escura, funda, brilho = [bytes([int(v * 255) for v in c] + [255]) for c in pal]
    brilho = brilho[:3] + bytes([95])
    brilho2 = brilho[:3] + bytes([45])
    local, gross = arco.local, arco.grossura
    for j in range(h):
        y = (gy0 + j + 0.5) * u
        lin = j * w * 4
        for i in range(w):
            s, off = local((gx0 + i + 0.5) * u, y)
            if s <= 0.0 or s >= 1.0:
                continue
            g = gross(s)
            if g < u * 0.5:
                continue
            if off > 0:
                if off < 1.2 * u:
                    px = brilho
                elif off < 2.4 * u and (i + j) % 2 == 0:
                    px = brilho2
                else:
                    continue
            else:
                a = -off / g
                if a > 1.0:
                    continue
                if -off < max(u * 1.05, g * 0.09):
                    px = luz                                    # fio da lamina
                elif 0.40 < a < 0.47 and int(s * 38) % 5:
                    px = clara                                  # riscos de velocidade
                elif 0.68 < a < 0.73 and int(s * 29) % 4:
                    px = cor
                else:
                    a += max(0.0, 0.3 - s) * 1.3                # rabo: mais escuro
                    a += _BAYER[j & 1][i & 1]                   # degraus pontilhados
                    if a < 0.26:
                        px = clara
                    elif a < 0.56:
                        px = cor
                    elif a < 0.8:
                        px = escura
                    elif a < 1.0 and (i + j) % 2 == 0:
                        px = funda
                    else:
                        continue
                    if s < 0.18 and (i * 3 + j * 5) % 7 < (0.18 - s) * 30:
                        continue                                # comeco se desfazendo
            buf[lin + i * 4:lin + i * 4 + 4] = px
        if j % 6 == 5:
            yield None
    yield (bytes(buf), gx0, gy0, w, h)


class OficinaCortes:
    """Prepara as manchas dos cortes da cena antes da hora (alguns ms por
    quadro de tela), para nada travar no golpe."""

    def __init__(self, u):
        self.u = u
        self._fila = []                 # [(chave, gerador)]
        self._prontos = {}              # chave -> (Texture, x0, y0, largura, altura) em px
        self._crus = set()              # chaves cujo resultado fica como veio do gerador
        self._ev = None

    def pedir_bruto(self, chave, gerador):
        """Prepara um gerador qualquer (o ultimo valor dele e o resultado)."""
        self._crus.add(chave)
        self._fila.append((chave, gerador))
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._passo, 0)

    def pedir(self, chave, arco, pal='katana'):
        self._fila.append((chave, _desenho_corte(arco, _PAL_CORTE[pal], self.u)))
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._passo, 0)

    def _fechar(self, chave, res):
        if chave in self._crus:
            self._prontos[chave] = res
            return
        dados, gx0, gy0, w, h = res
        tex = Texture.create(size=(w, h), colorfmt='rgba')
        tex.mag_filter = 'nearest'
        tex.min_filter = 'nearest'
        tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
        tex.add_reload_observer(lambda t, d=dados: t.blit_buffer(d, colorfmt='rgba', bufferfmt='ubyte'))
        u = self.u
        self._prontos[chave] = (tex, gx0 * u, gy0 * u, w * u, h * u)

    def _passo(self, dt):
        try:
            t0 = time.time()
            while self._fila and time.time() - t0 < 0.005:
                chave, gen = self._fila[0]
                res = next(gen)
                if res is not None:
                    self._fila.pop(0)
                    self._fechar(chave, res)
            if not self._fila:
                self._ev = None
                return False
            return True
        except Exception as e:
            print(f"[cortes] preparar: {e}")
            self._fila = []
            self._ev = None
            return False

    def obter(self, chave):
        """A mancha pronta (termina na hora se ainda faltar)."""
        if chave not in self._prontos:
            for i, (ch, gen) in enumerate(self._fila):
                if ch == chave:
                    self._fila.pop(i)
                    for res in gen:
                        if res is not None:
                            self._fechar(chave, res)
                    break
        return self._prontos.get(chave)

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        self._fila = []


class CorteGravado(Widget):
    """O arco de luz do corte correndo pelo caminho da ponta da lamina: a
    cabeca avanca rapido (freando), segura um instante e o rabo recolhe para
    a ponta enquanto apaga em degraus. Congela junto com o hit-stop do
    boneco `k`. on_passo(s) = ate onde a cabeca chegou (0..1)."""

    def __init__(self, arco, mancha, dur=0.12, decai=0.24, k=None, on_passo=None,
                 on_fim=None, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.arco = arco
        self.tex, self.x0, self.y0, self.w, self.h = mancha
        self.dur, self.decai = dur, decai
        self.k = k
        self._on_passo = on_passo
        self._on_fim = _Uma(on_fim)
        self.t = 0.0
        self._n = max(10, min(64, int(arco.comp / dp(7))))
        self._fora = dp(5)                     # o brilho por fora do fio
        self._dentro = -(arco.esp + dp(4))
        with self.canvas:
            self._c = Color(1, 1, 1, 1)
            self._m = Mesh(mode='triangles', texture=self.tex)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)
        self._tick(0)

    def _uv(self, x, y):
        return (x - self.x0) / self.w, (y - self.y0) / self.h

    def _faixa(self, s0, s1):
        if s1 - s0 <= 1e-4:
            self._m.vertices = []
            self._m.indices = []
            return
        ns = [s0] + [i / float(self._n) for i in range(self._n + 1) if s0 < i / float(self._n) < s1] + [s1]
        vs, ids = [], []
        for i, s in enumerate(ns):
            for off in (self._fora, self._dentro):
                x, y = self.arco.ponto(s, off)
                u, v = self._uv(x, y)
                vs.extend((x, y, u, v))
            if i:
                b = 2 * (i - 1)
                ids.extend((b, b + 1, b + 3, b, b + 3, b + 2))
        self._m.vertices = vs
        self._m.indices = ids

    def _tick(self, dt):
        try:
            if self.parent is None and self.t > 0:
                return self.parar()
            k = self.k
            if not (k is not None and k._pausa > 0):
                self.t += dt
            t = self.t
            if t < self.dur:
                u = t / self.dur
                s1 = 1 - (1 - u) ** 2
                self._faixa(0.0, s1)
                if self._on_passo:
                    self._on_passo(s1)
                return True
            if self._on_passo:
                self._on_passo(1.0)
                self._on_passo = None
            td = t - self.dur - 0.05
            if td < 0:
                self._faixa(0.0, 1.0)
                return True
            kd = td / self.decai
            if kd >= 1:
                return self.parar()
            self._faixa(min(0.999, kd ** 1.4), 1.0)
            self._c.a = 1.0 if kd < 0.35 else (0.7 if kd < 0.7 else 0.4)
            return True
        except Exception as e:
            print(f"[cortes] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self._on_passo:
            try:
                self._on_passo(1.0)
            except Exception:
                pass
            self._on_passo = None
        if self.parent:
            self.parent.remove_widget(self)
        self._on_fim()
        return False


def _recorta(poly, x0, y0, x1, y1):
    """Poligono convexo [(x, y)] recortado no retangulo (Sutherland-Hodgman)."""
    for ei in range(4):
        if not poly:
            return poly
        out = []
        for i in range(len(poly)):
            a, b = poly[i - 1], poly[i]

            def dentro(p):
                return (p[0] >= x0, p[1] >= y0, p[0] <= x1, p[1] <= y1)[ei]

            def corte(p, q):
                if ei in (0, 2):
                    xc = x0 if ei == 0 else x1
                    t = (xc - p[0]) / ((q[0] - p[0]) or 1e-9)
                    return (xc, p[1] + (q[1] - p[1]) * t)
                yc = y0 if ei == 1 else y1
                t = (yc - p[1]) / ((q[1] - p[1]) or 1e-9)
                return (p[0] + (q[0] - p[0]) * t, yc)
            if dentro(b):
                if not dentro(a):
                    out.append(corte(a, b))
                out.append(b)
            elif dentro(a):
                out.append(corte(a, b))
        poly = out
    return poly


# ═══════════════════════════════════════════════════════════════════
#  BALAO DE FALA (anime, em pixel art) e GEMIDINHOS DOS GOLPES
# ═══════════════════════════════════════════════════════════════════
_GEMIDOS = ['kiai_ha1', 'kiai_ha2', 'kiai_sei1', 'kiai_sei2', 'kiai_sei3', 'kiai_fun']
_ult_gemido = [None]


def _gemido(forte=False):
    """Kiai do Yoru num golpe (gravado: 'Hah!', 'Sei!', 'Fun!'): varia e
    nunca repete o ultimo. forte=True: 'Seiya!' (golpe com as duas)."""
    if forte:
        _som('kiai_seiya')
        _ult_gemido[0] = 'kiai_seiya'
        return
    opcoes = [g for g in _GEMIDOS if g != _ult_gemido[0]]
    g = random.choice(opcoes)
    _ult_gemido[0] = g
    _som(g)


def _topo_cabeca(k):
    """Ponto (coords do pai) logo acima da cabeca do boneco `k`."""
    try:
        te = k.ps / float(K.R)
        ex, ey = K.olhos_texel(k._pose)[0]
        if k.espelhar:
            ex = K.TW - 1 - ex
        return k.x + (ex + 0.5) * te, k.y + (ey + 16) * te
    except Exception:
        ax, ay = k.ancora()
        return ax, ay + k.ps * 14


class BalaoFala(Widget):
    """Balao de fala de manga (texto, sem voz) preso na cabeca do boneco `k`.
    tipo 'fala' = balao oval branco com contorno preto grosso e rabinho curvo
    ate a boca; 'grito' = explosao de pontas regulares com sombra (BAN!/KAI!).
    Entra num pop (cresce passando do ponto e volta), o grito treme, e some
    encolhendo depois de `dur`."""

    def __init__(self, texto, k, tipo='fala', dur=1.4, font_size=None, cor_texto=(0.05, 0.05, 0.10),
                 lado=None, on_fim=None, cor_sombra=None, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k, self.tipo, self.dur = k, tipo, dur
        self._on_fim = _Uma(on_fim)
        self.t = 0.0
        grito = tipo == 'grito'
        fs = font_size or (sp(40) if grito else sp(19))
        fonte = 'Bangers-Regular.ttf' if grito else 'ComicNeue-Bold.ttf'
        try:
            cl = CoreLabel(text=texto, font_name=fonte, font_size=fs)
            cl.refresh()
        except Exception:
            cl = CoreLabel(text=texto, font_name='rajdhani.ttf', font_size=fs, bold=True)
            cl.refresh()
        self._tex_txt = cl.texture
        tw, th_ = self._tex_txt.size
        px, py = _topo_cabeca(k)
        W = Window.width
        if lado is None:
            lado = -1 if px > W * 0.55 else 1
        self.lado = lado
        contorno = dp(3.2) if grito else dp(2.6)
        if grito:
            rx, ry = tw * 0.5 + dp(26), th_ * 0.5 + dp(22)
            pontos = self._explosao(rx, ry)
            cauda = None
        else:
            rx, ry = tw * 0.5 * 1.18 + dp(14), th_ * 0.5 * 1.25 + dp(9)
            pontos, cauda = self._oval_com_rabo(rx, ry, lado)
        # o corpo do balao fica acima e para o lado; a ponta do rabo (0, 0) na boca
        self._corpo = (lado * (rx * 0.35 + dp(6)), ry + dp(18) if not grito else ry + dp(10))
        ox, oy = self._corpo
        with self.canvas:
            PushMatrix()
            self._tr = Translate(0, 0)
            self._rot = Rotate(angle=0, origin=(0, 0))
            self._sc = Scale(1, 1, 1)
            if grito:                                              # sombra deslocada (manga)
                cs = cor_sombra or (0.10, 0.04, 0.18)
                self._c_sombra = Color(cs[0], cs[1], cs[2], 0.9)
                Mesh(vertices=self._leque(pontos, ox + dp(4), oy - dp(4)), indices=list(range(len(pontos) + 2)),
                     mode='triangle_fan')
            else:
                self._c_sombra = None
            self._c = Color(1, 1, 1, 1)
            Mesh(vertices=self._leque(pontos, ox, oy), indices=list(range(len(pontos) + 2)), mode='triangle_fan')
            self._cl = Color(0.04, 0.04, 0.08, 1)
            lin = []
            for (x, y) in pontos:
                lin += [ox + x, oy + y]
            SmoothLine(points=lin, width=contorno, close=True)
            self._ct = Color(cor_texto[0], cor_texto[1], cor_texto[2], 1)
            self._rt = Rectangle(texture=self._tex_txt, size=(tw, th_),
                                 pos=(ox - tw / 2.0, oy - th_ / 2.0 + (dp(1) if grito else dp(0.5))))
            PopMatrix()
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)
        self._tick(0)

    @staticmethod
    def _leque(pontos, ox, oy):
        """Vertices de um triangle_fan: o centro e a volta fechada."""
        vs = [ox, oy, 0, 0]
        for (x, y) in pontos + [pontos[0]]:
            vs += [ox + x, oy + y, 0, 0]
        return vs

    @staticmethod
    def _explosao(rx, ry, n=16):
        """Pontas regulares (com uma variacao pequena, sempre a mesma)."""
        rnd = random.Random(7)
        pts = []
        for i in range(2 * n):
            a = math.pi * i / n + math.pi / (2 * n)
            fora = i % 2 == 0
            k = (1.0 + rnd.uniform(-0.06, 0.1)) if fora else (0.72 + rnd.uniform(-0.03, 0.03))
            pts.append((math.cos(a) * rx * k, math.sin(a) * ry * k))
        return pts

    @staticmethod
    def _oval_com_rabo(rx, ry, lado, n=72):
        """Oval (um pouco quadrado, como no manga) com um rabinho curvo que
        sai da parte de baixo e aponta para a boca, embaixo. Pontos em volta
        do centro do corpo; a ponta do rabo fica em (-ox, -oy) do corpo."""
        pts = []
        a_base = -math.pi / 2 - lado * 0.42          # onde o rabo nasce (embaixo, do lado da boca)
        larg = 0.26                                  # meia-largura da base (radianos)
        for i in range(n):
            a = 2 * math.pi * i / n
            d = (a - a_base + math.pi) % (2 * math.pi) - math.pi
            if abs(d) < larg:
                continue
            c, s = math.cos(a), math.sin(a)
            # superelipse (expoente 2.4): mais cheia que uma elipse
            x = rx * math.copysign(abs(c) ** (2 / 2.4), c)
            y = ry * math.copysign(abs(s) ** (2 / 2.4), s)
            pts.append((a, x, y))
        pts.sort(key=lambda q: (q[0] - a_base - larg) % (2 * math.pi))
        volta = [(x, y) for _, x, y in pts]
        # rabinho: da borda (fim da volta) ate a ponta e de volta ao comeco, em curva
        x0, y0 = volta[-1]
        x1, y1 = volta[0]
        ponta = (-lado * (rx * 0.35 + dp(6)) - lado * dp(2), -(ry + dp(18)) + dp(2))
        cauda = []
        for j in range(1, 9):
            u = j / 9.0
            meio = ((x0 + ponta[0]) / 2 + lado * dp(6), (y0 + ponta[1]) / 2)
            bx = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * meio[0] + u * u * ponta[0]
            by = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * meio[1] + u * u * ponta[1]
            cauda.append((bx, by))
        cauda.append(ponta)
        for j in range(1, 9):
            u = j / 9.0
            meio = ((x1 + ponta[0]) / 2 + lado * dp(3), (y1 + ponta[1]) / 2 + dp(2))
            bx = (1 - u) ** 2 * ponta[0] + 2 * (1 - u) * u * meio[0] + u * u * x1
            by = (1 - u) ** 2 * ponta[1] + 2 * (1 - u) * u * meio[1] + u * u * y1
            cauda.append((bx, by))
        return volta + cauda, ponta

    def _tick(self, dt):
        try:
            self.t += dt
            t = self.t
            if t >= self.dur or self.k.parent is None:
                return self.parar()
            grito = self.tipo == 'grito'
            # pop: cresce passando do ponto, volta com uma molinha; sai encolhendo
            pico = 1.25 if grito else 1.12
            if t < 0.07:
                s = 0.3 + (pico - 0.3) * (t / 0.07)
            elif t < 0.13:
                s = pico - (pico - 0.94) * (t - 0.07) / 0.06
            elif t < 0.19:
                s = 0.94 + 0.06 * (t - 0.13) / 0.06
            elif t > self.dur - 0.13:
                s = max(0.05, 1.0 - (t - (self.dur - 0.13)) / 0.13)
            else:
                s = 1.0 + (0.02 * math.sin(t * 9.0) if not grito else 0.0)
            px, py = _topo_cabeca(self.k)
            treme = (0.0, 0.0)
            if grito and 0.1 < t < 0.45:
                treme = (random.choice((-1, 0, 1)) * dp(2.5), random.choice((-1, 0, 1)) * dp(2.5))
            self._tr.xy = (round(px + treme[0]), round(py + treme[1]))
            self._sc.x = self._sc.y = s
            self._rot.angle = (-6.0 * self.lado) if grito else 0.0
            a = 1.0 if t < self.dur - 0.13 else max(0.0, s)
            self._c.a = self._cl.a = self._ct.a = a
            if self._c_sombra is not None:
                self._c_sombra.a = 0.9 * a
            return True
        except Exception as e:
            print(f"[balao] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)
        self._on_fim()
        return False


def balao(camada, texto, k, tipo='fala', dur=1.4, **kw):
    """Poe um balao de fala do Yoru na camada (nunca derruba a cena)."""
    try:
        b = BalaoFala(texto, k, tipo=tipo, dur=dur, **kw)
        camada.add_widget(b)
        return b
    except Exception as e:
        print(f"[balao] {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
#  NUVEM DE REIATSU (a explosao do BAN-KAI, em pixel art)
#  Bolhas de energia roxa que estouram em volta dele, cobrem tudo e depois
#  abrem do meio para fora (revelando a forma nova), se desfazendo em
#  pontilhado. Os quadros sao desenhados antes da hora, aos poucos.
# ═══════════════════════════════════════════════════════════════════
_COR_NUVEM = ((250, 236, 255), (205, 160, 255), (140, 70, 230), (72, 24, 128), (22, 8, 40))


# ═══════════════════════════════════════════════════════════════════
#  TITULO ESCRITO PELA ESPADA
# ═══════════════════════════════════════════════════════════════════
class TituloLuz(Widget):
    """Texto revelado por trechos (cada golpe escreve um trecho): o trecho
    nasce branco-quente com um risco de luz no corte e esfria para o ciano."""

    def __init__(self, texto, font_size, cor=(0.0, 0.9, 1.0), **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self.texto = texto
        self.cor = cor
        lbl = CoreLabel(text=texto, font_name="orbitron.ttf", font_size=font_size, bold=True)
        lbl.refresh()
        self._tex = lbl.texture
        self.tw, self.th = self._tex.size
        self._larg = []
        for i in range(len(texto) + 1):
            if i == 0:
                self._larg.append(0.0)
                continue
            c = CoreLabel(text=texto[:i], font_name="orbitron.ttf", font_size=font_size, bold=True)
            c.refresh()
            self._larg.append(float(c.texture.size[0]))
        self._larg[-1] = float(self.tw)
        self._trechos = []
        self._gravados = set()                     # trechos que um corte ja completou
        with self.canvas:
            PushMatrix()
            self._sc_glow = Scale(1, 1, 1)
            self._c_glow = Color(*cor, 0)
            self._r_glow = Rectangle(texture=self._tex, size=self._tex.size)
            PopMatrix()
        self._grupo = InstructionGroup()
        self.canvas.add(self._grupo)
        with self.canvas:
            self._c_risco = Color(1, 1, 1, 0)
            self._risco = Line(points=[0, 0, 0, 0], width=dp(1.6))
        self.bind(pos=self._reposicionar, x=self._reposicionar, y=self._reposicionar,
                  size=self._reposicionar)
        self._reposicionar()

    def _origem(self):
        return (self.x + (self.width - self.tw) / 2.0,
                self.y + (self.height - self.th) / 2.0)

    def _reposicionar(self, *_):
        ox, oy = self._origem()
        self._r_glow.pos = (ox, oy)
        cx, cy = ox + self.tw / 2.0, oy + self.th / 2.0
        self._sc_glow.origin = (cx, cy)
        for tr in self._trechos:
            x0 = self._larg[tr['i0']]
            tr['rect'].pos = (ox + x0, oy)

    def x_do_trecho(self, i0, i1):
        """Centro (x) do trecho [i0, i1) em coords do pai."""
        ox, oy = self._origem()
        return ox + (self._larg[i0] + self._larg[i1]) / 2.0, oy + self.th / 2.0

    def revelar(self, i0, i1, dur=0.09, cor=None):
        cor = cor or self.cor
        ox, oy = self._origem()
        x0, x1 = self._larg[i0], self._larg[i1]
        c = Color(1, 1, 1, 1)
        r = Rectangle(pos=(ox + x0, oy), size=(0, self.th))
        self._grupo.add(c)
        self._grupo.add(r)
        tr = {'i0': i0, 'rect': r}
        self._trechos.append(tr)
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur)
                w = (x1 - x0) * u
                r.texture = self._tex.get_region(x0, 0, max(1, w), self.th)
                r.size = (max(1, w), self.th)
                ox2, oy2 = self._origem()
                ex = ox2 + x0 + w
                inc = self.th * 0.35
                self._risco.points = [ex - inc, oy2 - dp(6), ex + inc, oy2 + self.th + dp(6)]
                self._c_risco.a = 1.0 if u < 1 else 0.0
                # esfria: branco -> cor do golpe -> ciano do titulo
                k = min(1.0, max(0.0, (t[0] - dur) / 0.5))
                cc = [1 + (cor[i] - 1) * min(1.0, k * 2) for i in range(3)]
                if k > 0.5:
                    kk = (k - 0.5) * 2
                    cc = [cor[i] + (self.cor[i] - cor[i]) * kk for i in range(3)]
                c.rgba = (cc[0], cc[1], cc[2], 1)
                if k >= 1:
                    c.rgba = (*self.cor, 1)
                    return False
            except Exception as e:
                print(f"[titulo] revelar: {e}")
                return False
        Clock.schedule_interval(_p, 1 / 60.)

    def gravar_arco(self, i0, i1, arco, meia, cor=None):
        """As letras [i0, i1) aparecem por onde o corte passa: uma faixa de
        meia largura `meia` em volta do meio da mancha do `arco` mostra o
        trecho ate onde a cabeca do corte chegou (as letras nascem brancas,
        quentes). Devolve atualizar(s); em s = 1 o trecho fica inteiro e
        esfria para a cor do titulo."""
        cor = cor or self.cor
        c = Color(1, 1, 1, 1)
        m = Mesh(mode='triangles', texture=self._tex)
        self._grupo.add(c)
        self._grupo.add(m)
        n = max(10, min(48, int(arco.comp / dp(8))))
        meio = -0.4 * arco.esp
        tc = self._tex.tex_coords
        feito = [False]

        def atualizar(s):
            if feito[0]:
                return
            try:
                if s >= 1.0:
                    feito[0] = True
                    self._fechar_gravura(i0, i1, c, m, cor)
                    return
                ox, oy = self._origem()
                rx0, rx1 = ox + self._larg[i0], ox + self._larg[i1]
                ry0, ry1 = oy, oy + self.th
                ns = [0.0] + [i / float(n) for i in range(1, n) if i / float(n) < s] + [max(0.0, s)]
                vs, ids = [], []
                for j in range(1, len(ns)):
                    sa, sb = ns[j - 1], ns[j]
                    pol = _recorta([arco.ponto(sa, meio - meia), arco.ponto(sb, meio - meia),
                                    arco.ponto(sb, meio + meia), arco.ponto(sa, meio + meia)],
                                   rx0, ry0, rx1, ry1)
                    if len(pol) < 3:
                        continue
                    b = len(vs) // 4
                    for (x, y) in pol:
                        fx, fy = (x - ox) / self.tw, (y - oy) / self.th
                        vs.extend((x, y, tc[0] + (tc[2] - tc[0]) * fx, tc[1] + (tc[7] - tc[1]) * fy))
                    for q in range(1, len(pol) - 1):
                        ids.extend((b, b + q, b + q + 1))
                m.vertices = vs
                m.indices = ids
            except Exception as e:
                print(f"[titulo] gravar: {e}")
                feito[0] = True
                self._fechar_gravura(i0, i1, c, m, cor)
        return atualizar

    def _fechar_gravura(self, i0, i1, c, m, cor):
        """O corte terminou: o trecho fica inteiro (um retangulo so) e esfria
        branco -> cor do golpe -> cor do titulo."""
        if (i0, i1) in self._gravados:            # outro corte ja completou o trecho
            for ins in (m, c):
                try:
                    self._grupo.remove(ins)
                except Exception:
                    pass
            return
        self._gravados.add((i0, i1))
        ox, oy = self._origem()
        x0, x1 = self._larg[i0], self._larg[i1]
        w = max(1.0, x1 - x0)
        r = Rectangle(texture=self._tex.get_region(x0, 0, w, self.th), pos=(ox + x0, oy), size=(w, self.th))
        try:                                       # no lugar da faixa, logo depois da cor dela
            i = self._grupo.children.index(m)
            self._grupo.remove(m)
            self._grupo.insert(i, r)
        except Exception:
            self._grupo.add(c)
            self._grupo.add(r)
        self._trechos.append({'i0': i0, 'rect': r})
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                k = min(1.0, t[0] / 0.55)
                cc = [1 + (cor[i] - 1) * min(1.0, k * 2) for i in range(3)]
                if k > 0.5:
                    kk = (k - 0.5) * 2
                    cc = [cor[i] + (self.cor[i] - cor[i]) * kk for i in range(3)]
                c.rgba = (cc[0], cc[1], cc[2], 1)
                return k < 1
            except Exception:
                return False
        Clock.schedule_interval(_p, 1 / 60.)

    def garantir(self, i0, i1):
        """Se o trecho ainda nao apareceu (algum corte falhou), aparece agora."""
        if (i0, i1) not in self._gravados and not any(tr['i0'] == i0 for tr in self._trechos):
            self._gravados.add((i0, i1))
            self.revelar(i0, i1, dur=0.12, cor=(1, 1, 1))

    def clarao_final(self):
        """Titulo inteiro pulsa branco e ganha um brilho que respira."""
        t = [0.0]
        cores = [ins for ins in self._grupo.children if isinstance(ins, Color)]

        def _p(dt):
            try:
                t[0] += dt
                u = t[0]
                k = max(0.0, 1 - u / 0.6)
                for c in cores:
                    c.rgba = (self.cor[0] + (1 - self.cor[0]) * k,
                              self.cor[1] + (1 - self.cor[1]) * k,
                              self.cor[2] + (1 - self.cor[2]) * k, 1)
                self._c_glow.a = 0.30 * min(1.0, u / 0.15) * (0.75 + 0.25 * math.sin(u * 3))
                s = 1.10 - 0.04 * min(1.0, u / 0.6)
                self._sc_glow.x = self._sc_glow.y = s
                return self.parent is not None
            except Exception as e:
                print(f"[titulo] clarao: {e}")
                return False
        Clock.schedule_interval(_p, 1 / 60.)

    def varrer(self, dur=0.14):
        """Faixa de luz atravessando o titulo da esquerda para a direita (o
        corte do golpe final passando pelas letras)."""
        try:
            from animacoes_ui import _textura_faixa_luz
            tex = _textura_faixa_luz()
        except Exception:
            tex = None
        ox, oy = self._origem()
        larg = self.th * 1.6
        with self.canvas.after:
            c = Color(1, 1, 1, 0)
            r = Rectangle(size=(larg, self.th * 1.5), texture=tex)
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = t[0] / dur
                if u <= 1:
                    x = ox - larg + (self.tw + 2 * larg) * u
                    r.pos = (x, oy - self.th * 0.25)
                    c.a = 0.95
                else:
                    c.a = max(0.0, 0.95 - (t[0] - dur) / 0.2)
                    if c.a <= 0:
                        self.canvas.after.remove(c)
                        self.canvas.after.remove(r)
                        return False
            except Exception as e:
                print(f"[titulo] varrer: {e}")
                return False
        Clock.schedule_interval(_p, 1 / 60.)

    def gravar(self, i0, i1, cor=(0.78, 0.55, 1.0), dur=0.45):
        """O corte do golpe final passa por estas letras: elas saltam um
        pouco e acendem branco, puxam para o roxo e voltam ao normal (a
        lamina 'grava' a frase)."""
        try:
            ox, oy = self._origem()
            x0, x1 = self._larg[i0], self._larg[i1]
            w = max(1.0, x1 - x0)
            with self.canvas.after:
                c = Color(1, 1, 1, 1)
                r = Rectangle(texture=self._tex.get_region(x0, 0, w, self.th), size=(w, self.th))
        except Exception:
            return
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur)
                esc = 1.0 + 0.15 * (1 - u) ** 2              # salta e assenta
                ox2, oy2 = self._origem()
                cxl, cyl = ox2 + x0 + w / 2.0, oy2 + self.th / 2.0
                r.size = (w * esc, self.th * esc)
                r.pos = (cxl - w * esc / 2.0, cyl - self.th * esc / 2.0)
                k = min(1.0, u * 2.5)
                c.rgba = (1 + (cor[0] - 1) * k, 1 + (cor[1] - 1) * k, 1 + (cor[2] - 1) * k,
                          1.0 if u < 0.5 else max(0.0, (1 - u) * 2))
                if u >= 1:
                    self.canvas.after.remove(c)
                    self.canvas.after.remove(r)
                    return False
            except Exception:
                return False
        Clock.schedule_interval(_p, 1 / 60.)

    def pulsar(self, dur=0.85):
        """So as letras ja escritas pulsam (brancas) enquanto o golpe final
        carrega. O brilho da textura inteira revelaria o trecho que falta."""
        t = [0.0]
        cores = [ins for ins in self._grupo.children if isinstance(ins, Color)]

        def _p(dt):
            try:
                t[0] += dt
                if t[0] >= dur:
                    for c in cores:
                        c.rgba = (*self.cor, 1)
                    return False
                k = (0.15 + 0.55 * t[0] / dur) * (0.5 + 0.5 * math.sin(t[0] * 26))
                for c in cores:
                    c.rgba = (self.cor[0] + (1 - self.cor[0]) * k,
                              self.cor[1] + (1 - self.cor[1]) * k,
                              self.cor[2] + (1 - self.cor[2]) * k, 1)
            except Exception:
                return False
        Clock.schedule_interval(_p, 1 / 60.)

    def completo(self):
        """Mostra o titulo inteiro de uma vez (fallback)."""
        feitos = {tr['i0'] for tr in self._trechos}
        if 0 not in feitos:
            self.revelar(0, len(self.texto), dur=0.2)


# ═══════════════════════════════════════════════════════════════════
#  CENA DO TITULO
# ═══════════════════════════════════════════════════════════════════
_TRECHOS = [(0, 3), (3, 5), (5, 8), (8, 10), (10, 13)]      # TRA|VE|TE |FO|CUS


def _ps_titulo(th, largura, altura):
    """Abertura: o Yoru tem a altura de ~2 letras do logo (+12%) - a espada
    passa por uma silaba de cada vez, como se ele esculpisse a frase
    (multiplo de K.R: os pixels do boneco ficam todos do mesmo tamanho)."""
    alvo = min(th * 2.2 * 1.12, largura * 0.38, altura * 0.2)
    return K.ps_inteiro(alvo / 31.0)


def _ps_para(largura, altura, extra=1.0):
    alvo = min(dp(150), largura * 0.37, altura * 0.18) * extra  # altura do boneco (ver os detalhes)
    return K.ps_inteiro(alvo / 31.0)


class _Agenda:
    """schedule_once que so dispara enquanto a cena esta viva e nunca deixa
    excecao escapar (no Android uma excecao num callback fecha o app)."""

    def __init__(self):
        self.evs = []
        self.vivo = True

    def depois(self, t, fn):
        def _x(dt):
            if not self.vivo:
                return
            try:
                fn()
            except Exception as e:
                print(f"[cena] passo ignorado: {e}")
        self.evs.append(Clock.schedule_once(_x, t))

    def cada(self, t, fn):
        """Repete fn a cada t s enquanto a cena viver e fn nao devolver False."""
        def _x(dt):
            if not self.vivo:
                return False
            try:
                return fn(dt)
            except Exception as e:
                print(f"[cena] passo ignorado: {e}")
                return False
        self.evs.append(Clock.schedule_interval(_x, t))

    def parar(self):
        self.vivo = False
        for ev in self.evs:
            ev.cancel()
        self.evs = []


# ═══════════════════════════════════════════════════════════════════
#  EFEITOS DA TRANSFORMACAO (Bankai)
# ═══════════════════════════════════════════════════════════════════
_CORES_CHAMA = (('L', (0.93, 0.86, 1.0, 1.0)), ('V', (0.86, 0.58, 1.0, 1.0)),
                ('F', (0.62, 0.28, 1.0, 0.95)), ('o', (0.42, 0.18, 0.78, 0.9)),
                ('d', (0.24, 0.10, 0.42, 0.8)))


class _ChamasBankai(Widget):
    """Chamas roxas de pixel art em volta do Bankai: linguas de fogo (3 a 5
    blocos empilhados que afinam na ponta) nascem no chao e nas bordas do
    corpo, sobem balancando e escurecem em degraus antes de sumir. `alvo`
    0..1 = quantas nascem (a forca vai ate ele aos poucos)."""

    def __init__(self, k, u, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k = k
        self.u = max(1.0, float(u))
        self.forca = 0.0
        self.alvo = 0.0
        self._f = []
        self._acc = 0.0
        self._caixa = None
        self._n = 0
        self._lote = K.LotePixels(self.canvas, _CORES_CHAMA)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _corpo(self):
        """(x0, x1, y_pe, altura) do corpo, estimado pela ancora (quadril) e
        pelo tamanho da unidade - sem desenhar nada para medir."""
        k = self.k
        if getattr(k, '_desenho', None) is not None:
            return k.corpo_desenho()
        ps = k.ps
        ax, ay = k.ancora()
        frente = -1 if k.espelhar else 1
        x0, x1 = sorted((ax - frente * 7 * ps, ax + frente * 5 * ps))
        dy = (k._base.get('dy', 0) or 0) * ps
        return (x0, x1, ay - 12 * ps - dy, 30 * ps)

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            self.forca += (self.alvo - self.forca) * min(1.0, dt * 3.0)
            k = self.k
            u = self.u
            if k.parent is None or k.opacity < 0.05:
                self._lote.desenhar({})
                return True
            x0, x1, y_pe, alt = self._corpo()
            self._acc += self.forca * 95.0 * dt
            while self._acc >= 1.0:
                self._acc -= 1.0
                borda = random.random() < 0.7
                if borda:                                   # nas bordas do corpo (mais atras)
                    x = (x0 + random.uniform(-0.1, 0.25) * (x1 - x0)) if random.random() < 0.6 \
                        else (x1 - random.uniform(-0.1, 0.25) * (x1 - x0))
                else:
                    x = random.uniform(x0, x1)
                y = y_pe + alt * (random.random() ** 2.2) * 0.85
                vida = random.uniform(0.35, 0.75)
                self._f.append({'x': x, 'y': y, 'vy': alt * random.uniform(0.6, 1.1), 't': 0.0,
                                'vida': vida, 'n': random.choice((4, 5, 5, 6)),
                                'fb': random.uniform(7, 12), 'ph': random.uniform(0, 6.3)})
            pts = {}
            vivas = []
            for f in self._f:
                f['t'] += dt
                if f['t'] >= f['vida']:
                    continue
                vivas.append(f)
                f['y'] += f['vy'] * dt
                a = f['t'] / f['vida']
                bx = math.floor((f['x'] + math.sin(f['t'] * f['fb'] + f['ph']) * u * 1.4) / u) * u
                by = math.floor(f['y'] / u) * u
                n = max(1, int(round(f['n'] * (1.0 - 0.5 * a))))       # encurta enquanto sobe
                c = min(4, int(a * 2.6))
                for i in range(n):
                    if i == n - 1:
                        nome = ('L', 'V', 'F', 'o', 'd')[c]           # pontinha clara so quando nova
                    elif i == n - 2:
                        nome = ('V', 'F', 'o', 'd', 'd')[c]
                    else:
                        nome = ('F', 'F', 'o', 'd', 'd')[c]           # base roxa
                    larg = 3 if (i == 0 and a < 0.3) else (2 if (i < n - 2 and a < 0.6) else 1)
                    tremor = u if (i == n - 1 and int(f['t'] * 20 + f['ph']) % 2) else 0
                    pts.setdefault(nome, []).append((bx - (larg - 1) * u * 0.5 + tremor, by + i * u, larg * u, u))
            self._f = vivas[-160:]
            self._lote.desenhar(pts)
        except Exception as e:
            print(f"[chamas] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


class _PilarReiatsu(Widget):
    """A coluna de luz do BAN-KAI: continua o topo do casulo (widget `kr`,
    que toca os clipes do reiatsu) ate o fim da tela. E o bloco 'rei_pilar'
    do clipes.bin (mesmas cores e mesmo fogo subindo do casulo) empilhado -
    so troca a textura 12 vezes por segundo, no MESMO passo do casulo (sem
    emenda). Nasce subindo como um raio ate o ceu e, no fim, descola de
    baixo para cima."""

    N_MAX = 16

    def __init__(self, kr, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.kr = kr
        self.t = 0.0
        self.sobe = 1.0 / 0.22            # o raio chega ao topo em 0,22 s
        self.alto = 0.0                   # 0..1 da base ate o fim da tela
        self.baixo = 0.0                  # 0..1: a base descolando
        self.vel_baixo = 0.0
        with self.canvas:
            Color(1, 1, 1, 1)
            self._rects = [Rectangle(pos=(0, 0), size=(0, 0)) for _ in range(self.N_MAX)]
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def sumir(self, dur=0.45):
        self.vel_baixo = 1.0 / max(0.05, dur)

    def _indice(self):
        """Desenho do bloco no mesmo passo do casulo."""
        kr = self.kr
        cab = K.clipes_dados()
        n = len(cab['clipes']['rei_pilar']['quadros'])
        nome = getattr(kr, '_desenho', None)
        t = getattr(kr, '_clipe_t', self.t)
        if nome == 'rei_estouro':          # o estouro termina 1 passo antes da fervura
            d = int(t * 15)
            passo = int(round(((d - 5) / 15.0 - 1 / 12.0) * 12))
            return (passo % 8) * n // 8
        if nome == 'rei_ferve':
            return int(t * 30) % n
        return int(self.t * 30) % n

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            self.t += dt
            self.alto = min(1.0, self.alto + self.sobe * dt)
            if self.vel_baixo:
                self.baixo = min(1.0, self.baixo + self.vel_baixo * dt)
                if self.baixo >= 1.0:
                    self.parent.remove_widget(self)
                    return self.parar()
            kr = self.kr
            te = kr.te_clipe()
            tex, (x0, y0, w, h), _, _ = K.quadro_clipe('rei_pilar', self._indice())
            xa, yb = kr._local_desenho(x0, 0)                 # topo da tela do clipe = base da coluna
            x = kr.x + (xa - w * te if kr.espelhar else xa)
            base = kr.y + yb
            H = Window.size[1] / max(0.2, getattr(self.parent, 'scale', 1.0) or 1.0) + h * te
            topo_vis = base + (H - base) * self.alto
            topo_vis = math.floor(topo_vis / te) * te
            base_vis = base + (H - base) * self.baixo
            base_vis = math.floor(base_vis / te) * te
            bh = h * te
            tc = K._tc_espelhado(tex.tex_coords) if kr.espelhar else tex.tex_coords
            u0, v0, u1, _, _, v1, _, _ = tc[0], tc[1], tc[2], tc[3], tc[4], tc[5], tc[6], tc[7]
            for j, r in enumerate(self._rects):
                y_a = base + j * bh
                y_b = y_a + bh
                lo, hi = max(y_a, base_vis), min(y_b, topo_vis)
                if hi <= lo:
                    r.size = (0, 0)
                    continue
                fa, fb = (lo - y_a) / bh, (hi - y_a) / bh
                va, vb = v0 + (v1 - v0) * fa, v0 + (v1 - v0) * fb
                r.texture = tex
                r.pos = (x, lo)
                r.size = (w * te, hi - lo)
                r.tex_coords = (u0, va, u1, va, u1, vb, u0, vb)
            return True
        except Exception as e:
            print(f"[pilar] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


class _OlhosAcesos(Widget):
    """O olho do Bankai acendendo dentro do reiatsu: miolo branco com a
    borda escura (aparece em cima de qualquer cor) e uma cruz lilas que
    cresce e pisca (12 trocas por segundo)."""

    def __init__(self, pos, u, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.p = pos
        self.u = max(1.0, float(u))
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, (('borda', (0.12, 0.04, 0.27, 1.0)),
                                                ('halo', (0.63, 0.41, 1.0, 1.0)),
                                                ('luz', (0.97, 0.94, 1.0, 1.0))))
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            self.t += dt
            u = self.u
            cx = math.floor(self.p[0] / u) * u
            cy = math.floor(self.p[1] / u) * u
            f = int(self.t * 12)
            # o olho: miolo branco com borda escura e o risco de luz de anime
            # (abre para os lados em degraus e depois pisca)
            n = min(12, 3 + 2 * f) - (f % 2 if f > 6 else 0)
            pts = {'borda': [(cx - 3 * u, cy - 2 * u, 7 * u, 4 * u), (cx - (n + 2) * u, cy - u, (2 * n + 5) * u, 3 * u)],
                   'halo': [(cx - (n + 1) * u, cy, (2 * n + 3) * u, u), (cx - 2 * u, cy - u, 5 * u, 3 * u)],
                   'luz': [(cx - u, cy - u, 3 * u, 2 * u), (cx - (n // 2 + 1) * u, cy, (n + 3) * u, u)]}
            for k in (3, 4):                                           # cruz curta em cima e embaixo
                pts['halo'].append((cx, cy + k * u, u, u))
                pts['halo'].append((cx, cy - k * u, u, u))
            self._lote.desenhar(pts)
            return True
        except Exception as e:
            print(f"[olhos] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


_CORES_LUA = (('halo', (0.40, 0.16, 0.72, 0.5)), ('fundo', (0.03, 0.01, 0.055, 0.95)),
              ('miolo', (0.07, 0.02, 0.12, 0.95)), ('borda', (0.62, 0.30, 1.0, 1.0)),
              ('claro', (0.93, 0.82, 1.0, 1.0)))


class _LuaNegra(Widget):
    """Lua negra atras do Bankai: disco escuro de pixels grandes com a borda
    roxa acesa (que tremula) e um halo pontilhado; cresce em degraus e
    some encolhendo."""

    def __init__(self, centro, raio, u, dur=0.5, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.c = centro
        self.u = max(2.0, float(u))
        self.r_alvo = float(raio)
        self.r = 0.0
        self.vel = raio / max(0.05, dur)
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, _CORES_LUA)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def sumir(self, dur=0.35):
        self.r_alvo = 0.0
        self.vel = max(self.r, 1.0) / max(0.05, dur)

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            self.t += dt
            if self.r < self.r_alvo:
                self.r = min(self.r_alvo, self.r + self.vel * dt)
            elif self.r > self.r_alvo:
                self.r = max(self.r_alvo, self.r - self.vel * dt)
                if self.r <= 0.0:
                    if self.parent is not None:
                        self.parent.remove_widget(self)
                    return self.parar()
            u = self.u
            n = int(self.r / u)
            cx = math.floor(self.c[0] / u) * u
            cy = math.floor(self.c[1] / u) * u
            pts = {}
            f = int(self.t * 12)
            for iy in range(-n - 2, n + 3):
                w_f = math.sqrt(max(0.0, (n - 0.5) ** 2 - iy * iy))
                if w_f > 0:
                    k0 = int(math.floor(-w_f))
                    pts.setdefault('fundo', []).append((cx + k0 * u, cy + iy * u, (2 * -k0 + 1) * u, u))
                    if abs(iy) < n * 0.55:                               # miolo um tiquinho mais claro
                        w_m = math.sqrt(max(0.0, (n * 0.55) ** 2 - iy * iy))
                        km = int(math.floor(-w_m))
                        pts.setdefault('miolo', []).append((cx + km * u, cy + iy * u, (2 * -km + 1) * u, u))
            if n >= 1:
                m = max(16, int(2 * math.pi * n))
                vistos = set()
                for i in range(m):
                    a = 2 * math.pi * i / m
                    for rr, nome in ((n, 'borda'), (n + 1.6, 'halo')):
                        gx, gy = int(round(math.cos(a) * rr)), int(round(math.sin(a) * rr))
                        if (gx, gy, nome) in vistos:
                            continue
                        vistos.add((gx, gy, nome))
                        h = (gx * 7 + gy * 13 + f) % 9
                        if nome == 'halo' and h > 3:
                            continue
                        nm = 'claro' if (nome == 'borda' and h == 0) else nome
                        pts.setdefault(nm, []).append((cx + gx * u, cy + gy * u, u, u))
            self._lote.desenhar(pts)
        except Exception as e:
            print(f"[lua] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


class _AnelEnergia(Widget):
    """A linha da transformacao: uma elipse achatada de pixels roxos e
    lilases em volta do corpo, na altura y (a frente mais clara que a parte
    de tras), tremulando."""

    def __init__(self, u, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.u = max(1.0, float(u))
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, _CORES_CHAMA)

    def pos_linha(self, cx, y, larg, dt=1 / 60.):
        self.t += dt
        u = self.u
        a = max(u * 3, larg / 2.0)
        b = u * 2.2
        n = max(16, int(2 * math.pi * a / u))
        pts = {}
        f = int(self.t * 24)
        for i in range(n):
            ang = 2 * math.pi * i / n
            x = math.floor((cx + math.cos(ang) * a) / u) * u
            yy = math.floor((y + math.sin(ang) * b) / u) * u
            frente = math.sin(ang) < 0
            h = (i * 5 + f) % 7
            if frente:
                nome = 'L' if h < 2 else 'V'
            else:
                if h > 4:
                    continue
                nome = 'F' if h < 3 else 'o'
            pts.setdefault(nome, []).append((x, yy, u, u))
            if frente and h == 0:                               # lingua de fogo subindo da frente
                pts.setdefault('F', []).append((x, yy + u, u, u))
        # a faixa de corte atravessando o corpo: linha clara com fogo roxo por cima
        k0 = math.floor((cx - a) / u)
        k1 = math.floor((cx + a) / u)
        yb = math.floor(y / u) * u
        for k in range(k0, k1 + 1):
            h = (k * 3 + f) % 5
            pts.setdefault('L' if h else 'V', []).append((k * u, yb, u, u))
            if h < 2:
                pts.setdefault('F', []).append((k * u, yb + u, u, u))
            if h == 0:
                pts.setdefault('o', []).append((k * u, yb + 2 * u, u, u))
        self._lote.desenhar(pts)


BRASA = (1.0, 0.42, 0.14)        # o fogo do chefe


class _BarraChefe(Widget):
    """Nome e barra de vida do chefe (como os chefes de andar de SAO), em
    pixels: moldura, a vida em brasa e, em branco, o pedaco que ele acabou
    de perder - que encolhe um instante depois, em degraus."""

    def __init__(self, nome, cx, y, larg, u, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.u = max(2.0, float(round(u)))
        self.cx, self.y0, self.larg = cx, y, larg
        self.frac, self.lag = 1.0, 1.0
        self.abre, self._alvo = 0.0, 0.0
        self._espera = 0.0
        self._sai = False
        self._lote = K.LotePixels(self.canvas, (('f', (0.03, 0.02, 0.05, 1.0)), ('m', (0.60, 0.64, 0.76, 1.0)),
                                                ('e', (0.30, 0.04, 0.05, 1.0)), ('v', (0.84, 0.15, 0.10, 1.0)),
                                                ('c', (1.0, 0.56, 0.20, 1.0)), ('b', (1.0, 1.0, 1.0, 1.0))))
        from kivy.core.text import Label as CoreLabel
        cl = CoreLabel(text=nome, font_name='orbitron.ttf', font_size=max(sp(9), self.u * 3.2), bold=True)
        cl.refresh()
        self._tex = cl.texture
        with self.canvas:
            self._c_nome = Color(1.0, 0.84, 0.74, 0)
            self._r_nome = Rectangle(texture=self._tex, size=self._tex.size, pos=(0, 0))
        self._ev = Clock.schedule_interval(self._tique, 1 / 30.)

    def mostrar(self):
        self._alvo = 1.0

    def dano(self, frac):
        """A vida cai para `frac` (0..1) de uma vez; o branco some depois."""
        self.frac = max(0.0, min(self.frac, frac))
        self._espera = 0.3

    def sumir(self):
        self._alvo = 0.0
        self._sai = True

    def _tique(self, dt):
        try:
            if self.parent is None:
                return False
            if self.abre < self._alvo:
                self.abre = min(self._alvo, self.abre + 0.2)
            elif self.abre > self._alvo:
                self.abre = max(self._alvo, self.abre - 0.25)
            if self._espera > 0:
                self._espera -= dt
            elif self.lag > self.frac:
                self.lag = max(self.frac, self.lag - 0.05)
            u = self.u
            p = {}
            wb = math.floor(self.larg * self.abre / u) * u
            if wb >= 6 * u:
                x0 = math.floor((self.cx - wb / 2.0) / u) * u
                y = math.floor(self.y0 / u) * u
                h = 3 * u
                p['f'] = [(x0, y, wb, h)]
                p['m'] = [(x0, y + h, wb, u), (x0, y - u, wb, u), (x0 - u, y, u, h), (x0 + wb, y, u, h),
                          (x0 - 2 * u, y + u, u, u), (x0 + wb + u, y + u, u, u)]
                dentro = wb - 2 * u
                wv = math.floor(dentro * self.frac / u) * u
                wl = math.floor(dentro * self.lag / u) * u
                p['e'] = [(x0 + u, y, dentro, h)]
                if wl > wv:
                    p['b'] = [(x0 + u + wv, y, wl - wv, h)]
                if wv > 0:
                    p['v'] = [(x0 + u, y, wv, h)]
                    p['c'] = [(x0 + u, y + 2 * u, wv, u)]
                for k in range(1, 10):                          # marcas de 10 em 10
                    xm = x0 + u + math.floor(dentro * k / 10.0 / u) * u
                    p['f'].append((xm, y, u, u))
                self._r_nome.pos = (x0, y + h + 2 * u)
                self._c_nome.a = 1.0 if self.abre >= 1.0 else 0.0
            else:
                self._c_nome.a = 0.0
            self._lote.desenhar(p)
            if self._sai and self.abre <= 0:
                if self.parent is not None:
                    self.parent.remove_widget(self)
                return False
            return True
        except Exception as e:
            print(f"[cena] barra do chefe: {e}")
            return False


def _surgir_chefe(boss, camada, dur, on_fim=None, cor=BRASA):
    """O chefe se ergue do chao em faixas, de baixo para cima: silhueta em
    brasa escura que ganha cor em 3 degraus, com uma barra de luz na emenda
    (nada de transparencia)."""
    fim = _Uma(on_fim)
    antes = tuple(boss.cor_clarao)

    def _pronto():
        boss.recortar()
        boss.cor_clarao = antes
        boss.clarao = 0.0
        boss.opacity = 1
        fim()
    try:
        te = boss.te
        base, topo = boss.y - 2 * te, boss.top + 2 * te
        cx, larg = boss.center_x, boss.width * 0.86
        n = max(6, int(round(dur * 30)))
        boss.cor_clarao = (0.40, 0.05, 0.04)
        boss.opacity = 1
        boss.clarao = 1.0
        boss.recortar(None, base)

        def emenda(d):
            i = min(n, max(0, d + 1))
            return base + math.floor((topo - base) * i / float(n) / te) * te

        def forma(t, p, u):
            d = int(t * 30)
            if d >= n:
                return
            y = math.floor(emenda(d) / u) * u
            x0 = math.floor((cx - larg / 2.0) / u)
            x1 = math.floor((cx + larg / 2.0) / u)
            borda = max(1, (x1 - x0) // 6)
            for gx in range(x0, x1 + 1):
                ponta = gx - x0 < borda or x1 - gx < borda
                if ponta and (gx + d) % 2:
                    continue
                p.setdefault('cor' if ponta else 'luz', []).append((gx * u, y, u, u))
                if not ponta:
                    p.setdefault('clara', []).append((gx * u, y - u, u, u))
                    if (gx + d) % 3 == 0:
                        p.setdefault('cor', []).append((gx * u, y - 2 * u, u, u))
        camada.add_widget(_EfeitoPixel(_cores_efeito(cor), (n + 4) / 30.0, forma))
        passo = [-1]
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                d = int(t[0] * 30)
                if d == passo[0]:
                    return True
                passo[0] = d
                if d < n:
                    boss.recortar(None, emenda(d))
                elif d < n + 3:
                    boss.recortar()
                    boss.clarao = (2, 1, 0)[d - n] / 3.0
                else:
                    _pronto()
                    return False
                return True
            except Exception as e:
                print(f"[cena] chefe surge: {e}")
                _pronto()
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[cena] chefe surge ignorado: {e}")
        _pronto()


# ═══════════════════════════════════════════════════════════════════
#  A LUTA EM "CENA DE ANIME": cenario, faixas de cinema, linhas de
#  velocidade, close do chefe, raio de sangue, sombra no chao
# ═══════════════════════════════════════════════════════════════════
class _CenarioChefe(Widget):
    """O cenario da luta (chefe/cenario_*.png, feitos em dev/cenario_chefe.py
    a partir do desenho do usuario): ceu com a lua em eclipse, o castelo ao
    longe e o chao rachado em brasa. O horizonte fica na linha `chao`.
    abrir(): aparece a partir do horizonte (o ceu sobe, o chao desce);
    fechar(): some do mesmo jeito; tranco(): um solavanco (impactos grandes)."""

    def __init__(self, W, H, chao, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.W, self.H, self.chao = W, H, float(chao)
        self.f, self.alvo, self.vel = 0.0, 0.0, 1.0
        self._tr = 0
        self._passo = -1
        self._tex = {}
        try:
            from kivy.core.image import Image as CoreImage
            pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chefe')
            for n in ('ceu', 'longe', 'chao'):
                t = CoreImage(os.path.join(pasta, 'cenario_%s.png' % n)).texture
                t.mag_filter = t.min_filter = 'nearest'
                self._tex[n] = t
        except Exception as e:
            print(f"[cenario] {e}")
        self.u = W / 180.0                                   # as imagens tem 200 pontos de largura: sobra 10 de cada lado
        with self.canvas:
            self._c_topo = Color(7 / 255.0, 4 / 255.0, 9 / 255.0, 1)
            self._r_topo = Rectangle(pos=(0, 0), size=(0, 0))
            self._c_base = Color(4 / 255.0, 2 / 255.0, 5 / 255.0, 1)
            self._r_base = Rectangle(pos=(0, 0), size=(0, 0))
            Color(1, 1, 1, 1)
            self._r = {n: Rectangle(pos=(0, 0), size=(0, 0), texture=self._tex.get(n)) for n in ('ceu', 'longe', 'chao')}
        self._ev = Clock.schedule_interval(self._tique, 1 / 60.)

    def abrir(self, dur=0.7):
        self.alvo, self.vel = 1.0, 1.0 / max(0.05, dur)

    def fechar(self, dur=0.5):
        self.alvo, self.vel = 0.0, 1.0 / max(0.05, dur)

    def tranco(self):
        self._tr = 8

    def _tique(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            if self.f != self.alvo:
                d = self.vel * dt
                self.f = min(self.alvo, self.f + d) if self.alvo > self.f else max(self.alvo, self.f - d)
            dy = 0
            if self._tr > 0:
                self._tr -= 1
                dy = (self._tr % 2 * 2 - 1) * int(self.u) * (1 if self._tr > 3 else 0.5)
            passo = (int(self.f * 24), dy)
            if passo == self._passo:
                return True
            self._passo = passo
            f = int(self.f * 24) / 24.0
            u, W, H, ch = self.u, self.W, self.H, self.chao + dy
            if f <= 0 or not self._tex:
                for r in list(self._r.values()) + [self._r_topo, self._r_base]:
                    r.size = (0, 0)
                return True
            x0 = -10 * u
            # ceu: da linha do horizonte para cima, ate a fracao f
            tc, hc = self._tex['ceu'], self._tex['ceu'].height * u
            vis = min(hc, (H - ch)) * f
            self._r['ceu'].pos = (x0, ch)
            self._r['ceu'].size = (tc.width * u, vis)
            fr = vis / hc
            self._r['ceu'].tex_coords = (0, 1, 1, 1, 1, 1 - fr, 0, 1 - fr)
            if f >= 1 and ch + hc < H:
                self._r_topo.pos, self._r_topo.size = (0, ch + hc), (W, H - ch - hc)
            else:
                self._r_topo.size = (0, 0)
            tl, hl = self._tex['longe'], self._tex['longe'].height * u
            visl = min(hl, vis)
            frl = visl / hl
            self._r['longe'].pos = (x0, ch)
            self._r['longe'].size = (tl.width * u, visl)
            self._r['longe'].tex_coords = (0, 1, 1, 1, 1, 1 - frl, 0, 1 - frl)
            # chao: do horizonte para baixo
            tg, hg = self._tex['chao'], self._tex['chao'].height * u
            visg = min(hg, ch) * f
            frg = visg / hg
            self._r['chao'].pos = (x0, ch - visg)
            self._r['chao'].size = (tg.width * u, visg)
            self._r['chao'].tex_coords = (0, frg, 1, frg, 1, 0, 0, 0)
            if f >= 1 and ch - hg > 0:
                self._r_base.pos, self._r_base.size = (0, 0), (W, ch - hg)
            else:
                self._r_base.size = (0, 0)
            return True
        except Exception as e:
            print(f"[cenario] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


class _FaixasCinema(Widget):
    """As duas faixas pretas de cinema (em cima e embaixo): entram e saem em
    degraus nos momentos fortes."""

    def __init__(self, W, H, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.W, self.H = W, H
        self.alt = H * 0.085
        self.f, self.alvo = 0.0, 0.0
        with self.canvas:
            Color(0, 0, 0, 1)
            self._a = Rectangle(pos=(0, 0), size=(0, 0))
            self._b = Rectangle(pos=(0, 0), size=(0, 0))
        self._ev = Clock.schedule_interval(self._tique, 1 / 30.)

    def entrar(self):
        self.alvo = 1.0

    def sair(self):
        self.alvo = 0.0

    def _tique(self, dt):
        if self.parent is None:
            self._ev.cancel()
            return False
        if self.f == self.alvo:
            return True
        self.f = min(1.0, self.f + 0.25) if self.alvo > self.f else max(0.0, self.f - 0.25)
        h = round(self.alt * self.f)
        self._a.pos, self._a.size = (-self.W, -self.H * 0.2), (self.W * 3, h + self.H * 0.2)
        self._b.pos, self._b.size = (-self.W, self.H - h), (self.W * 3, h + self.H * 0.2)
        return True


def _linhas_velocidade(camada, dur, cor=BRANCO, vertical=False, x0=None, x1=None, y0=None, y1=None, n=20,
                       sentido=-1):
    """Riscos de velocidade em pixel correndo pela tela (arrancadas e quedas).
    sentido: -1 = para a esquerda / para baixo; 1 = para a direita / para cima."""
    try:
        W, H = camada.size
        rnd = random.Random(int(dur * 1000) + n)
        a0, a1 = ((x0 if x0 is not None else 0), (x1 if x1 is not None else W)) if vertical \
            else ((y0 if y0 is not None else 0), (y1 if y1 is not None else H))
        L = H if vertical else W
        riscos = [(rnd.uniform(a0, a1), rnd.uniform(0, 1), rnd.uniform(0.12, 0.34) * L, rnd.uniform(1.6, 3.0),
                   rnd.choice((1, 1, 2))) for _ in range(n)]

        def forma(t, p, u):
            k = t / dur
            if k > 0.75 and int(t * 30) % 2:                  # some piscando
                return
            for a, fase, comp, vel, g in riscos:
                s = (fase + t * vel) % 1.3
                pos = (1.15 - s) * L if sentido < 0 else (s - 0.15) * L
                e = g * u * 2
                if vertical:
                    p.setdefault('clara' if g == 1 else 'luz', []).append(
                        (math.floor(a / u) * u, math.floor(pos / u) * u, e, math.floor(comp / u) * u))
                else:
                    p.setdefault('clara' if g == 1 else 'luz', []).append(
                        (math.floor(pos / u) * u, math.floor(a / u) * u, math.floor(comp / u) * u, e))
        camada.add_widget(_EfeitoPixel(_cores_efeito(cor), dur, forma))
    except Exception as e:
        print(f"[cena] linhas: {e}")


def _close_chefe(camada, boss, dur=0.75, y_rel=0.6, on_fim=None):
    """Close de anime do chefe: uma faixa atravessa a tela mostrando o elmo
    dele ampliado (os olhos e os dentes acesos), com riscos de velocidade."""
    fim = _Uma(on_fim)
    try:
        W, H = camada.size
        hb = round(H * 0.15)
        y = round(H * y_rel - hb / 2.0)
        z = 3.0
        w = Widget(size_hint=(None, None), size=(0, 0))
        fbo_tex = boss._fbo.texture
        ox, oy = boss._pontos['olho'] if boss._pontos else (0, 0)
        # a regiao da telinha do chefe em volta do olho (y da telinha para baixo)
        rw, rh = W / z, hb / z
        cx, cy = ox + rw * 0.08, oy + rh * 0.12
        u0, u1 = (cx - rw / 2.0) / boss.CW, (cx + rw / 2.0) / boss.CW
        v0, v1 = (boss.CH - (cy + rh / 2.0)) / boss.CH, (boss.CH - (cy - rh / 2.0)) / boss.CH
        borda = max(2.0, round(_PX[0] * 3))
        with w.canvas:
            Color(0.02, 0.0, 0.01, 1)
            fundo = Rectangle(pos=(0, y), size=(W, hb))
            Color(1, 1, 1, 1)
            img = Rectangle(pos=(0, y), size=(W, hb), texture=fbo_tex, tex_coords=(u0, v0, u1, v0, u1, v1, u0, v1))
            Color(1.0, 0.2, 0.14, 1)
            b1 = Rectangle(pos=(0, y + hb), size=(W, borda))
            b2 = Rectangle(pos=(0, y - borda), size=(W, borda))
        camada.add_widget(w)
        _som('koiguchi')
        t = [0.0]

        def _p(dt):
            t[0] += dt
            # entra deslizando da direita em 3 degraus e sai para a esquerda
            d = int(t[0] * 30)
            fora = int((dur - t[0]) * 30)
            dx = (W * (0.66, 0.3, 0.1)[d] if d < 3 else 0) - (W * (0.1, 0.3, 0.66)[2 - fora] if 0 <= fora < 3 else 0)
            for r in (fundo, img, b1, b2):
                r.pos = (dx, r.pos[1])
            if t[0] >= dur:
                if w.parent:
                    w.parent.remove_widget(w)
                fim()
                return False
            return True
        Clock.schedule_interval(_p, 1 / 60.)
        _linhas_velocidade(camada, dur, (1.0, 0.3, 0.2), y0=y, y1=y + hb, n=10)
    except Exception as e:
        print(f"[cena] close do chefe: {e}")
        fim()


def _projetil_sangue(camada, de, para, dur, te, on_chega=None, pequeno=False):
    """O raio de sangue do montante: uma lanca de luz vermelha com o miolo
    claro e um rastro em degraus, de `de` ate `para`."""
    chegou = _Uma(lambda: on_chega(para[0], para[1]) if on_chega else None)
    try:
        dx, dy = para[0] - de[0], para[1] - de[1]
        d = math.hypot(dx, dy) or 1.0
        ux, uy = dx / d, dy / d
        b = te * (4 if pequeno else 8)
        n = 7 if pequeno else 12

        def forma(t, p, u):
            k = min(1.0, t / dur)
            if k >= 1.0:
                chegou()
                return
            hx, hy = de[0] + dx * k, de[1] + dy * k
            for j in range(n):
                x, y = hx - ux * j * b * 1.1, hy - uy * j * b * 1.1
                if (x - de[0]) * ux + (y - de[1]) * uy < 0:
                    break
                g = max(1, (4 if pequeno else 6) - j // 2)          # afina para tras
                nome = 'luz' if j < 2 else ('clara' if j < 5 else 'cor')
                lado = g * b / 3.0
                for s in (-1, 0, 1) if g > 2 else (0,):
                    p.setdefault(nome if s == 0 else 'cor', []).append(
                        (math.floor((x - uy * s * lado) / u) * u, math.floor((y + ux * s * lado) / u) * u,
                         max(u, math.floor(lado / u) * u), max(u, math.floor(lado / u) * u)))
        camada.add_widget(_EfeitoPixel(_cores_efeito((1.0, 0.16, 0.12)), dur + 0.04, forma, on_fim=chegou))
    except Exception as e:
        print(f"[cena] projetil: {e}")
        chegou()


def _racha_chao(camada, x, chao, te, larg=320, n=7, atras=None):
    """O chao racha em brasa em volta de um impacto e fica aceso um tempo."""
    try:
        u = te * 2
        rach = _rachaduras(x, chao - 34 * te, x - larg * te / 2.0, chao - 70 * te, larg * te, 70 * te, u, n=n,
                           semente=int(x) % 97 + 3)
        w = _PixelsBrasa(rach, u, cresce=0.14, fica=1.7, some=0.7, grossura=1)
        i = camada.children.index(atras) + 1 if atras is not None and atras in camada.children else 0
        camada.add_widget(w, index=i)
    except Exception as e:
        print(f"[cena] racha: {e}")


def _talho_x(camada, x, y, te, tam=26, cls=None):
    """Um X de luz no ponto do acerto (dois riscos curtos que crescem e somem)."""
    try:
        u = te * 2
        d = tam * te
        linhas = [_reta_pixels(x - d, y - d * 0.6, x + d, y + d * 0.6, u), _reta_pixels(x - d, y + d * 0.6, x + d, y - d * 0.6, u)]
        camada.add_widget((cls or _PixelsLuz)(linhas, u, cresce=0.05, fica=0.08, some=0.12, grossura=1))
    except Exception as e:
        print(f"[cena] talho: {e}")


def _brasas_para_letras(camada, alvos, origem, dur, on_chega, on_fim=None):
    """As brasas do chefe viram a frase: de pontos espalhados dentro de
    `origem` (x0, y0, x1, y1) sai uma brasa para cada letra (alvos = [(i, x,
    y)]), em arco, uma depois da outra; on_chega(i) quando cada uma chega."""
    rnd = random.Random(7)
    x0, y0, x1, y1 = origem
    n = max(1, len(alvos))
    voo = dur * 0.55
    passo = (dur - voo) / n
    pts = [(rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(-1, 1)) for _ in alvos]
    chegou = [False] * n

    def forma(t, p, u):
        for k, (i, ax, ay) in enumerate(alvos):
            tl = t - k * passo
            if tl < 0:
                continue
            if tl >= voo:
                if not chegou[k]:
                    chegou[k] = True
                    on_chega(i)
                continue
            f = tl / voo
            sx, sy, lado = pts[k]
            for j, nome in enumerate(('luz', 'clara', 'cor', 'cor', 'brilho')):   # a ponta e a cauda
                fj = max(0.0, f - j * 0.06)
                e = fj * fj * (3 - 2 * fj)
                x = sx + (ax - sx) * e + math.sin(math.pi * fj) * lado * u * 26
                y = sy + (ay - sy) * e + math.sin(math.pi * fj) * u * 34
                g = u * (3 if j < 2 else 2)
                p.setdefault(nome, []).append((math.floor(x / u) * u, math.floor(y / u) * u, g, g))

    def _fim():
        for k, (i, _x, _y) in enumerate(alvos):
            if not chegou[k]:
                chegou[k] = True
                on_chega(i)
        if on_fim:
            on_fim()
    camada.add_widget(_EfeitoPixel(_cores_efeito((1.0, 0.3, 0.16)), dur + 0.05, forma, on_fim=_fim))


def _sombra_chao(camada, x, y, r0, r1, dur, u):
    """A sombra do chefe crescendo no chao enquanto ele cai do ceu (elipse
    achatada em xadrez, que escurece no fim)."""
    try:
        def forma(t, p, uu):
            k = min(1.0, t / dur)
            r = r0 + (r1 - r0) * k * k
            ry = max(u, r * 0.16)
            cheia = k > 0.7
            gx0, gx1 = int((x - r) / u), int((x + r) / u)
            for gy in range(int((y - ry) / u), int((y + ry) / u) + 1):
                yy = (gy + 0.5) * u - y
                for gx in range(gx0, gx1 + 1):
                    xx = (gx + 0.5) * u - x
                    if (xx / r) ** 2 + (yy / ry) ** 2 <= 1.0 and (cheia or (gx + gy) % 2 == 0):
                        p.setdefault('s', []).append((gx * u, gy * u, u, u))
        camada.add_widget(_EfeitoPixel((('s', (0.0, 0.0, 0.0, 0.85)),), dur, forma), index=len(camada.children) - 1)
    except Exception as e:
        print(f"[cena] sombra: {e}")


def cena_titulo(tela, label, on_fim=None, texto="TRAVETE FOCUS"):
    """A LUTA: o CHEFE (chefe.py, "THE ABYSS WARDEN") se ergue do chao e
    ruge; o Yoru cai do alto, espera o montante descer, passa por baixo dele
    num iai e emenda quatro golpes (subindo pelo peito, mergulhando com as
    duas espadas, fugindo da garra e voltando num X) - a barra de vida do
    chefe despenca. Ele cai de joelho... e se levanta em furia, jogando o
    Yoru para tras. BAN-KAI: a transformacao, a escuridao, e UM corte na
    altura da frase parte o chefe ao meio (ele vira cacos) e grava TRAVETE
    FOCUS. O Yoru volta ao normal, pousa na frase, guarda as espadas - a
    frase explode - e da as boas-vindas."""
    fim = _Uma(on_fim)
    camada = Widget(size_hint=(None, None), size=tela.size, pos=(0, 0))
    ag = _Agenda()
    camada._agenda = ag
    cam = [None]
    estado = {'reator': None, 'aura': None}

    def restaurar_fundo():
        try:
            if cam[0] is not None:
                cam[0].soltar()
            r = estado['reator']
            if r is not None and r.opacity < 0.99 and not getattr(r, '_absorvido', False):
                r.restaurar()
                _fundo(tela, reator=1.0, barra=1.0, dur=0.3)
        except Exception as e:
            print(f"[cena] restaurar fundo: {e}")

    camada._restaurar = restaurar_fundo

    def encerrar():
        ag.parar()
        K.definir_ambiente('')
        if cam[0] is not None:
            cam[0].soltar()
        try:
            r = estado.get('reator')
            if r is not None and estado.get('texto_reator'):
                r.texto = estado.pop('texto_reator')            # o LOADING volta com a tela de carga
        except Exception as e:
            print(f"[cena] texto do fundo: {e}")
        try:
            c = estado.get('chefe')
            if c is not None:
                c.parar()
            import chefe as _ch
            _ch.soltar_texturas()
        except Exception as e:
            print(f"[cena] soltar chefe: {e}")
        fim()

    try:
        tela.add_widget(camada)
        W, H = tela.size
        area = (0.0, 0.0, float(W), float(H))
        wx, wy = label.to_window(label.x, label.y)
        lx, ly = tela.to_widget(wx, wy)
        titulo = TituloLuz(texto, label.font_size, pos=(lx, ly), size=label.size)
        camada.add_widget(titulo)
        camada._titulo = titulo
        faiscas = K.Faiscas(n_max=140)
        fundo_fx = K.Faiscas(n_max=50)                 # particulas atras do Kirito
        ps = _ps_titulo(titulo.th, W, H)
        kk = K.KiritoPixel(ps=ps)
        ps = kk.ps
        _PX[0] = ps / float(K.R)
        kk.opacity = 0
        aura = _AuraEspada(kk, faiscas)
        aura.faiscas_fundo = fundo_fx
        estado['aura'] = aura
        camada.add_widget(fundo_fx)
        estado['fitas'] = ()
        chamas = _ChamasBankai(kk, 3 * ps / float(K.R))   # chamas roxas do Bankai (atras dele)
        estado['chamas'] = chamas
        camada.add_widget(chamas)
        camada.add_widget(aura)
        camada.add_widget(K.RastroLamina(kk, faiscas))
        camada.add_widget(kk)
        camada.add_widget(faiscas)
        cam[0] = _Camera(tela)
        try:
            estado['reator'] = tela.ids.get('reator_shader')
        except Exception:
            estado['reator'] = None
        try:
            # o "LOADING..." do fundo nao faz parte da luta: fica guardado ate o fim
            r0 = estado['reator']
            if r0 is not None and getattr(r0, 'texto', ''):
                estado['texto_reator'] = r0.texto
                r0.texto = ''
        except Exception as e:
            print(f"[cena] texto do fundo: {e}")
        alt = 24 * ps
        th = titulo.th
        m = max(dp(4), ps)                              # folga ate a borda do quadro
        P = K.POSE_A
        # Bankai (estilo Mugetsu): da fusao ate o golpe final ele fica na
        # sombra, envolto em chamas roxas e azuis, com o cabelo comprido
        M = {n: _com(P[n], mugetsu=True) for n in ('fund_alto', 'evo_alto', 'evo_carga',
                                                    'evo_corte', 'evo_fim')}
        K.definir_ambiente('brasa')                        # na luta ele reflete a lua e a brasa do chefe
        kk.precarregar([P[n] for n in P] + list(M.values()))
        _precarregar_sons(_SONS_TITULO)
        ox_t, oy_t = titulo._origem()
        pe = kk.extensao(P['guardado'])[1] - ps         # ancora -> sola da bota
        # a luta acontece EM CIMA das letras (elas ficam sempre a vista)
        y_topo = oy_t + th * 0.82 + pe

        def quadro(x, y, poses):
            return _no_quadro(kk, x, y, [P[n] if isinstance(n, str) else n for n in poses], area, m)

        def corte_trecho(i, cor, sentido=1, som_corte='corte', cor2=None, arco=None,
                         achat=0.42):
            i0, i1 = _TRECHOS[i]
            cx, cy = titulo.x_do_trecho(i0, i1)
            larg = max(titulo._larg[i1] - titulo._larg[i0], th)
            a0, a1 = arco or ((160, -150) if sentido > 0 else (20, 330))
            camada.add_widget(CorteMeiaLua(centro=(cx, cy), raio=larg * 0.95, ang_ini=a0,
                                           ang_fim=a1, espessura=th * 0.9, achat=achat, cor=cor))
            if cor2 is not None:           # a segunda lamina: meia-lua junto, um pouco defasada
                d = 22 if a1 > a0 else -22
                camada.add_widget(CorteMeiaLua(centro=(cx, cy - th * 0.08), raio=larg * 0.82,
                                               ang_ini=a0 - d, ang_fim=a1 - d,
                                               espessura=th * 0.7, achat=achat, cor=cor2))
                _som('corte2')
            titulo.revelar(i0, i1, cor=(1, 1, 1) if cor == CIANO else AZUL)
            faiscas.estourar(cx, cy, cor, n=18, forca=dp(170), tam=ps)
            _estrela(camada, cx, cy, ps, cor)
            _som(som_corte)
            _tremer(6)
            _brilho_tela(camada, 0.10, 0.12)
            kk.impacto()
            kk.pausar(0.07)                              # hit-stop
            kk.empurrar(capa=16, cabelo=14)

        def poeira(x, y, n=10):
            faiscas.estourar(x, y, POEIRA, n=n, forca=dp(90), tam=max(2, ps * 0.8), gravidade=dp(300))

        # ── 1-5. A LUTA CONTRA O CHEFE ───────────────────────────────
        kk.espelhar = False                                # o Yoru comeca olhando para a direita
        te = ps / float(K.R)
        oficina = OficinaCortes(te * max(1, int(round(2.4 / te))))
        estado['oficina'] = oficina
        VIS = [(0, 3), (3, 5), (5, 7), (8, 10), (10, 13)]      # letras de cada silaba (sem o espaco)

        def silaba(i):
            a, b = VIS[i]
            x0, x1 = ox_t + titulo._larg[a], ox_t + titulo._larg[b]
            return (x0 + x1) / 2.0, oy_t + th * 0.5, x1 - x0

        ARCOS = {}
        COR_PAL = {'katana': CIANO, 'azul': AZUL, 'mug': ROXO}

        def ponta(pose, anc, qual=1):
            """Ponta da lamina `qual` da pose com a ancora em `anc`."""
            tx, ty = kk._local_texel(*K.maos_texel(pose, qual)[1])
            ax, ay = kk.ancora_local()
            return anc[0] + tx - ax, anc[1] + ty - ay

        def arco_do_golpe(arma, corta, a0, a1, qual, esp):
            """Arco da ponta da lamina `qual`: passa pela ponta na pose `arma`
            (ancora a0), no meio do golpe e na pose `corta` (ancora a1) - o
            mesmo caminho que a lamina do desenho faz."""
            meio = K.misturar(arma, corta, 0.5, 0.5)
            am = ((a0[0] + a1[0]) / 2.0, (a0[1] + a1[1]) / 2.0)
            return ArcoCorte.por_tres(ponta(arma, a0, qual), ponta(meio, am, qual),
                                      ponta(corta, a1, qual), esp)

        def arco(chave, arma, corta, a0, a1, qual=1, esp=None, pal='katana'):
            """Prepara (antes da hora) a luz do golpe `chave`."""
            ARCOS[chave] = (arco_do_golpe(arma, corta, a0, a1, qual, esp or th), pal)
            oficina.pedir(chave, ARCOS[chave][0], pal)

        def golpear(chave, dur=0.16, on_meio=None, som=None):
            """Solta a luz do golpe `chave` pelo caminho da lamina (contra o chefe)."""
            a, pal = ARCOS[chave]
            cor = COR_PAL[pal]
            ult = [0.0]
            meio = [on_meio]

            def _passo(s):
                if s - ult[0] > 0.1 and s < 1.0:
                    ult[0] = s
                    x, y = a.ponto(s, -0.4 * a.esp)
                    faiscas.estourar(x, y, cor, n=2, forca=dp(120), tam=max(2, te * 2), gravidade=dp(200))
                if meio[0] is not None and s >= 0.5:
                    fn, meio[0] = meio[0], None
                    fn()
            if som:
                _som(som)
            mancha = oficina.obter(chave)
            if mancha is None:
                _passo(1.0)
                return
            camada.add_widget(CorteGravado(a, mancha, dur=dur, k=kk, on_passo=_passo))

        def cortar(chave, i, dur=0.12, on_meio=None, som=None, letras=False):
            """Solta o arco `chave` e grava a silaba i por onde ele passa.
            letras=True: cada letra ja escrita acende quando a luz passa."""
            a, pal = ARCOS[chave]
            i0, i1 = _TRECHOS[i]
            grava = titulo.gravar_arco(i0, i1, a, th * 0.95)
            cor = COR_PAL[pal]
            ult = [0.0]
            meio = [on_meio]
            acesas = set()

            def _passo(s):
                grava(s)
                if s - ult[0] > 0.1 and s < 1.0:
                    ult[0] = s
                    x, y = a.ponto(s, -0.4 * a.esp)
                    faiscas.estourar(x, y, cor, n=2, forca=dp(120), tam=max(2, te * 2),
                                     gravidade=dp(200))
                if meio[0] is not None and s >= 0.5:
                    fn, meio[0] = meio[0], None
                    fn()
                if letras:
                    hx = a.ponto(min(s, 1.0))[0]
                    for li in range(len(texto)):
                        if li not in acesas and texto[li].strip() and \
                                ox_t + (titulo._larg[li] + titulo._larg[li + 1]) / 2.0 <= hx:
                            acesas.add(li)
                            titulo.gravar(li, li + 1)
            if som:
                _som(som)
            mancha = oficina.obter(chave)
            if mancha is None:
                _passo(1.0)
                return
            camada.add_widget(CorteGravado(a, mancha, dur=dur, k=kk, on_passo=_passo))

        def sem_rastro(chaves):
            return [(ch[0], _com(ch[1], s1=None, s2=None)) + tuple(ch[2:]) for ch in chaves]

        pronto = _com(P['saca0'], olhos='s')
        agacha = _com(P['agacha'], olhos='s')
        corta_tra = _com(P['corta1'], olhos='g')
        arma_ve = _com(P['salto_arma'], olhos='s')
        corta_ve = _com(P['salto'], olhos='g', a1=P['salto']['a1'] + 360)   # sobe pela frente
        fim_ve = _com(P['salto_fim'], olhos='s', a1=_perto(P['salto_fim']['a1'], corta_ve['a1']))
        pega_az = K.encolhido(_com(P['pega2'], olhos='s'))
        saca_az = K.encolhido(_com(P['saca2'], olhos='s'))
        arma_te = _com(P['desce_arma'], olhos='s')
        corta_te = _com(P['desce_corta'], olhos='g')
        arma_fo = K.encolhido(_com(P['c3_corta'], olhos='s'))      # as duas no alto, cruzadas
        corta_fo = _com(P['c3_arma'], olhos='g', a2=P['c3_arma']['a2'] - 360)   # descem abrindo em X
        prep_fo = _com(P['agacha'], olhos='s', m1=(3, 2), a1=150.0, m2=(-3, 3), a2=60.0)
        guarda2 = _com(P['dupla'], olhos='s')

        # O CHEFE (o modelo do usuario, 405 pontos de altura): comeca do lado
        # direito, virado para o Yoru. O chao da luta fica 200 pontos ABAIXO da
        # frase (que so aparece no fim): ela passa na cintura dele - o corte do
        # Bankai, na altura das letras, parte o chefe ao meio. Sobra o ceu
        # inteiro em cima (o salto do chefe usa) e o chao em baixo.
        import chefe as CH
        CH.dados()
        CH.aquecer(por_quadro=3)
        _, cy_t, _ = silaba(0)
        chao = max(m + 6 * te, cy_t - 200 * te)
        y_luta = chao + pe
        bx = min(W - m - 215 * te, max(W * 0.66, W * 0.5 + 110 * te))
        bxl = max(m + 170 * te, W * 0.30)                  # onde ele cai do salto (do lado esquerdo)
        boss = CH.ChefePixel(te=te)
        boss.ancorar(bx, chao)
        boss.opacity = 0
        camada.add_widget(boss, index=camada.children.index(titulo))    # atras do Yoru e dos efeitos
        estado['chefe'] = boss
        frente = bx - 58 * te                              # onde comeca o corpo dele (do lado do Yoru)
        barra_c = _BarraChefe('THE ABYSS WARDEN', W / 2.0, min(H - m - 12 * te, chao + 470 * te),
                              min(W * 0.62, 260 * te), te * 2)
        camada.add_widget(barra_c)
        estado['barra_chefe'] = barra_c
        # o cenario do desenho dele (lua em eclipse, castelo, chao em brasa) atras de tudo
        cen = _CenarioChefe(W, H, chao)
        camada.add_widget(cen, index=len(camada.children))
        estado['cenario'] = cen
        cine = _FaixasCinema(W, H)                          # as faixas pretas de cinema
        camada.add_widget(cine)
        VIDA = {1: 0.88, 2: 0.76, 3: 0.58, 4: 0.53, 5: 0.48, 6: 0.43, 7: 0.38, 8: 0.22, 9: 0.06}
        brasas = K.Faiscas(n_max=110)                       # o fogo do chefe e as cinzas do chao (atras do Yoru)
        camada.add_widget(brasas, index=camada.children.index(boss))
        SANGUE = (1.0, 0.2, 0.12)

        def _vida_chefe(dt):
            try:
                if estado.get('chefe_morto'):
                    return False
                if cen.f > 0.9:                             # cinzas subindo das fendas do chao
                    brasas.estourar(random.uniform(0, W), chao - random.uniform(4, 150) * te,
                                    random.choice((BRASA, SANGUE)), n=1, forca=dp(14), tam=te * random.choice((2, 3, 4)),
                                    gravidade=-dp(random.uniform(40, 110)))
                if boss.opacity > 0 and boss._pontos is not None:
                    mx_, my_ = boss.mao()
                    px_, py_ = boss.ponta()
                    for _ in range(2):                      # o fio do montante solta fogo
                        f = random.uniform(0.15, 1.0)
                        brasas.estourar(mx_ + (px_ - mx_) * f, my_ + (py_ - my_) * f,
                                        random.choice((BRASA, SANGUE, (1.0, 0.6, 0.25))), n=1, forca=dp(40),
                                        tam=te * random.choice((2, 3, 3, 4)), gravidade=-dp(210))
                    ox_, oy_ = boss.ponto('olho')            # a chama do olho
                    brasas.estourar(ox_ + random.uniform(0, 5) * te, oy_ + random.uniform(0, 4) * te,
                                    random.choice((SANGUE, BRASA)), n=1, forca=dp(12), tam=te * 3,
                                    gravidade=-dp(170))
            except Exception as e:
                print(f"[cena] vida do chefe: {e}")
            return True
        ag.cada(0.05, _vida_chefe)
        # o BANKAI e desenhado maior que o Yoru normal (cada ponto do desenho da
        # referencia vira 2x2): da para ver cabelo, casaco e espada. Os pes
        # continuam no mesmo chao (a ancora sobe a diferenca).
        ESC_BK = 2.0
        sobe_bk = 56.5 * te * (ESC_BK - 1.0)

        def boss_idle():
            boss.tocar('idle', loop=True)

        arma_el = _com(P['arma1'], olhos='s')               # o corte de cima para baixo (no elmo)
        corta_el = _com(P['corta_desce'], olhos='g')
        # onde o Yoru fica em cada golpe
        A0 = quadro(max(m + 30 * te, bx - 330 * te), y_luta, [pronto])   # onde ele pousa
        J1 = (frente - 96 * te, y_luta + 300 * te)                       # por cima da varrida
        J2 = (frente - 62 * te, y_luta + 218 * te)                       # o corte desce no elmo
        K0 = quadro(frente - 170 * te, y_luta, [pronto])                 # de frente para ele, a distancia
        A1 = quadro(frente - 22 * te, y_luta, [corta_tra])               # colado no chefe
        B1 = (frente - 4 * te, y_luta + 250 * te)                        # sobe rente ao peito
        C0 = (frente - 50 * te, y_luta + 360 * te)                       # no alto, na cara dele
        C1 = quadro(frente - 14 * te, y_luta, [corta_te])                # desce rasgando o nucleo
        R0 = quadro(W - m - 70 * te, y_luta, [guarda2])                  # do lado direito (o chefe caiu no esquerdo)
        Xm = ((bxl + bx) / 2.0 + 20 * te, y_luta + 430 * te)             # por cima da investida
        X1 = (frente - 30 * te, y_luta + 150 * te)                       # o X desce nas costas dele
        E0 = quadro(max(m + 20 * te, A0[0] - 16 * te), y_luta, [guarda2])  # jogado para tras: daqui o BAN-KAI
        arco('h1', arma_el, corta_el, J1, J2, 1, th * 1.0)
        arco('dfl', pronto, corta_tra, K0, A1, 1, th * 1.0)
        arco('h2', arma_ve, corta_ve, A1, B1, 1, th * 0.95)
        arco('h3', arma_te, corta_te, C0, C1, 1, th * 0.95)
        arco('h3b', arma_te, corta_te, C0, C1, 2, th * 0.75, 'azul')
        arco('h4', arma_fo, corta_fo, Xm, X1, 1, th * 0.9)
        arco('h4b', arma_fo, corta_fo, Xm, X1, 2, th * 0.85, 'azul')
        # o do Bankai atravessa a frase inteira, de um lado ao outro da tela
        ARCOS['cus'] = (ArcoCorte.pelo_meio((ox_t + titulo.tw / 2.0, cy_t), 0, W * 1.02, -0.05,
                                            th * 1.35), 'mug')
        oficina.pedir('cus', ARCOS['cus'][0], 'mug')
        # o revide do Bankai (do alto, descendo na cabeca do chefe)
        ARCOS['ctr'] = (ArcoCorte.por_tres((E0[0] + 60 * te, chao + 480 * te), (frente - 90 * te, chao + 470 * te),
                                           (frente + 14 * te, chao + 330 * te), th * 1.25), 'mug')
        oficina.pedir('ctr', ARCOS['ctr'][0], 'mug')
        kk.precarregar([pronto, agacha, corta_tra, arma_ve, corta_ve, fim_ve, pega_az, saca_az,
                        arma_te, corta_te, arma_fo, corta_fo, prep_fo, guarda2, arma_el, corta_el])

        # golpes: prepara, segura, a lamina gira em quadros de rastro,
        # acompanha e volta com molinha
        G = dict(n_arma=3, prende=3, segue=3, volta=5, meios=(0.25, 0.5, 0.75))
        GIRO = len(G['meios'])                   # o corpo e a luz saem no 1o quadro de rastro

        def _voo_seq(p_ini, p_ar, p_fim, dur):
            """Poses de um salto com a duracao do voo: sai esticado, fecha
            na bola (segura enquanto gira) e abre de novo para pousar."""
            n = max(6, int(round(dur * K.FPS)))
            a = max(2, int(n * 0.22))
            c = max(2, int(n * 0.25))
            b = max(2, n - a - c)
            return K.sequencia([(a, p_ini, 'out'), (b, p_ar, 'segura'), (c, p_ar, 'out'), (1, p_fim)])

        def acerta(n, onde=None, forte=False, reage=True, leve=False, cor=CIANO):
            """Um golpe do Yoru pegou no chefe: quadros brancos, faiscas, a
            barra de vida cai e ele acusa o golpe. leve = golpe de uma rajada
            (sem congelar a cena)."""
            x, y = onde or boss.ponto('nucleo')
            boss.impacto(quadros=2 if leve else (5 if forte else 3), tremor=3 if leve else (8 if forte else 5))
            kk.impacto(forte=forte)
            if not leve:
                boss.pausar(0.11 if forte else 0.07)
                kk.pausar(0.09 if forte else 0.06)
                _som('corte')
                _brilho_tela(camada, 0.10, 0.1)
            _estrela(camada, x, y, ps, BRANCO, raios=4 if leve else (7 if forte else 5))
            _talho_x(camada, x, y, te, 16 if leve else (34 if forte else 24), _PixelsRoxo if cor == ROXO else None)
            if not leve:                                     # a lava espirra da ferida, para o lado do Yoru
                lado = -1 if kk.ancora()[0] < x else 1
                for _ in range(10 if forte else 6):
                    brasas.estourar(x + lado * random.uniform(0, 30) * te, y + random.uniform(-14, 14) * te,
                                    random.choice((SANGUE, BRASA)), n=1, forca=dp(60), tam=te * 3,
                                    gravidade=dp(520))
            faiscas.estourar(x, y, BRASA, n=8 if leve else (24 if forte else 14), forca=dp(220), tam=ps)
            faiscas.estourar(x, y, cor, n=5 if leve else 8, forca=dp(150), tam=ps)
            _tremer(5 if leve else (16 if forte else 8))
            barra_c.dano(VIDA[n])
            kk.empurrar(capa=14, cabelo=12)
            if reage:
                boss.tocar('apanha', on_fim=boss_idle)

        def _vida_yoru(dt):
            try:
                if kk.opacity <= 0 or estado.get('chefe_morto'):
                    return True
                ax_, ay_ = kk.ancora()
                ant = estado.get('yoru_ant', (ax_, ay_))
                estado['yoru_ant'] = (ax_, ay_)
                if math.hypot(ax_ - ant[0], ay_ - ant[1]) > te * 10:      # so quando ele esta voando
                    tx_, ty_ = kk.ponta_espada(1)
                    faiscas.estourar(tx_, ty_, ROXO if kk._desenho is not None else CIANO, n=2, forca=dp(40),
                                     tam=te * 2, gravidade=dp(60))
            except Exception as e:
                print(f"[cena] vida do yoru: {e}")
            return True
        ag.cada(0.04, _vida_yoru)

        def soco_camera(foco, zoom=1.1, volta=0.35):
            """A camera da um tranco para perto do golpe e volta."""
            cam[0].ir(1.0 + (zoom - 1.0) * 2.4, foco=foco, dur=0.07)
            ag.depois(0.16, lambda: cam[0].ir(1.0, dur=volta))

        def cam_em(zoom, foco=None, dur=0.4):
            cam[0].ir(zoom, foco=foco, dur=dur)

        def mover_chefe(de, para, dur, ease='linear', on_fim=None):
            """Leva os pes do chefe de `de` ate `para` (em passos de pixel, 30 por segundo)."""
            t = [0.0]
            fim_ = _Uma(on_fim)

            def _p(dt):
                t[0] += dt
                u = min(1.0, t[0] / max(0.01, dur))
                e = u * u if ease == 'in' else (1 - (1 - u) ** 2 if ease == 'out' else u)
                d = math.floor(u * dur * 30) / max(1.0, dur * 30) if u < 1 else 1.0
                e = d * d if ease == 'in' else (1 - (1 - d) ** 2 if ease == 'out' else d)
                boss.ancorar(round(de[0] + (para[0] - de[0]) * e), round(de[1] + (para[1] - de[1]) * e))
                if u >= 1.0:
                    fim_()
                    return False
                return True
            ag.cada(1 / 60., _p)

        # ── 1) o cenario abre do horizonte, o chefe se ergue do chao e ruge ──
        def _abre_cena():
            _fundo(tela, reator=0.0, barra=0.0, dur=0.3)
            cen.abrir(0.7)
            cine.entrar()
        ag.depois(0.15, _abre_cena)

        def _chefe_surge():
            boss_idle()
            _som('trevas')
            _tremer(12)
            faiscas.estourar(bx, chao, BRASA, n=22, forca=dp(190), tam=ps, gravidade=-dp(120))
            cam[0].ir(1.2, foco=(bx - 30 * te, chao + 300 * te), dur=1.4)       # a camera sobe pelo corpo dele
            _surgir_chefe(boss, camada, 0.9, on_fim=lambda: ag.depois(0.15, _ruge))
            ag.depois(0.7, barra_c.mostrar)
        ag.depois(0.95, _chefe_surge)

        def _berro(i):
            if i == 14:                                      # a cabeca foi para tras: o berro
                ox_, oy_ = boss.ponto('cabeca')
                _som('rugido')
                _tremer(26)
                cam[0].ir(1.0, dur=0.3)
                _anel(camada, (ox_ - 20 * te, oy_ - 8 * te), te * 10, te * 330, 0.55, BRASA, esp=dp(6), grao=3)
                _brilho_tela(camada, 0.22, 0.3, (1.0, 0.25, 0.16), atras=boss)
                faiscas.estourar(ox_ - 22 * te, oy_, BRASA, n=26, forca=dp(260), tam=ps)

        def _ruge():
            boss.tocar('rugido', on_quadro=_berro, on_fim=boss_idle)
            # close de anime: o elmo dele, os olhos e os dentes acesos
            ag.depois(0.95, lambda: _close_chefe(camada, boss, dur=0.75, y_rel=0.6))
            ag.depois(1.8, _entra)

        # ── 2) o Yoru despenca do alto da tela e pousa na frente dele ──
        def _entra():
            p_pulo = _com(P['pulo'], olhos='s')
            ini = (A0[0] - th * 1.2, H + alt * 0.6)
            kk.ancorar(*ini)
            kk.opacity = 1
            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), K.esticado(p_pulo), 0.75))
            _som('pulo')
            kk.empurrar(capa=-8, cabelo=-6, lift=10)
            _linhas_velocidade(camada, 0.7, CIANO, vertical=True, x0=A0[0] - 90 * te, x1=A0[0] + 90 * te, n=14)
            _mover(kk, ini, A0, 0.75, rot=(0, -360), fantasmas=4, ease='in', on_fim=_pousa,
                   rot_janela=(0.2, 0.75))

        def _pousa():
            kk.rotacao = 0
            _som('pouso')
            ax, ay = kk.ancora()
            poeira(ax, ay - kk.extensao()[1], n=14)
            _anel(camada, (ax, chao + te * 2), te * 4, te * 70, 0.3, CIANO, esp=dp(2), achat=0.3)
            _tremer(8)
            cine.sair()
            kk.empurrar(lift=-10, capa=-6)
            kk.tocar(K.sequencia(_de_agora(kk, 1) + [(2, _com(agacha, estica=-1), 'segura'),
                                                      (4, agacha, 'out'), (4, pronto, 'suave'),
                                                      (1, pronto)]))
            cam_em(1.55, foco=(ax + 40 * te, ay + 60 * te), dur=0.35)      # a camera vai ate ele
            ag.depois(0.95, lambda: cam_em(1.0, dur=0.3))
            # close de anime: o olho dele, com a mao no cabo
            ag.depois(0.1, lambda: _som('fala_ikuzo'))
            ag.depois(0.12, lambda: close_rosto(camada, 'normal', dur=0.7, y_rel=0.84,
                                                espelhar=kk.espelhar,
                                                on_fim=lambda: ag.depois(0.02, _luta1)))

        # ── 3) VARRIDA: o montante vem de tras raspando o chao; o Yoru salta
        #    por cima dela num mortal e desce cortando o elmo (golpe 1) ──
        def _luta1():
            def _q(i):
                if i == 12:
                    _salta_varrida()
                elif i == 17:                               # a lamina passa raspando o chao
                    mx_, my_ = boss.mao()
                    _som('corte2')
                    _tremer(14)
                    camada.add_widget(CorteMeiaLua(centro=(mx_, my_), raio=te * 250, ang_ini=300, ang_fim=165,
                                                   espessura=te * 60, achat=1.0, cor=BRASA,
                                                   dur_cheio=4 / 30.0, dur_decai=6 / 30.0))
                    _racha_chao(camada, frente - 130 * te, chao, te, larg=300, n=6, atras=boss)
                    for k_ in range(5):
                        poeira(frente - (40 + 50 * k_) * te, chao, n=4)
                    faiscas.estourar(frente - 120 * te, chao, BRASA, n=20, forca=dp(240), tam=ps)
            boss.tocar('varrida', on_quadro=_q, on_fim=boss_idle)

        def _salta_varrida():
            p_pulo = _com(P['pulo'], olhos='s')
            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), arma_el, 0.4))
            _som('pulo')
            kk.empurrar(capa=-8, lift=10)
            _mover(kk, kk.ancora(), J1, 0.4, altura=te * 60, rot=(0, -360), fantasmas=3, ease='out',
                   on_fim=_corta_elmo, rot_janela=(0.15, 0.8))

        def _corta_elmo():
            kk.rotacao = 0
            chaves, i_r = K.golpe(arma_el, corta_el, seg=P['segue_desce'], **dict(G, n_arma=1, prende=1, volta=3))

            def _q(i):
                if i == i_r - GIRO:
                    _gemido(forte=True)
                    kk.empurrar(capa=12, lift=6)
                    _mover(kk, kk.ancora(), J2, 0.14, ease='in', fantasmas=2)
                    cab_ = boss.ponto('cabeca')
                    golpear('h1', dur=0.16, on_meio=lambda: (acerta(1, cab_, forte=True), soco_camera(cab_, 1.12)))
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_cai_do_elmo)

        def _cai_do_elmo():
            p_pulo = _com(P['pulo'], olhos='s')
            kk.tocar(_voo_seq(K.esticado(p_pulo), K.encolhido(p_pulo), pronto, 0.36))

            def _chegou():
                _som('pouso')
                bx_, by_ = kk.ancora()
                poeira(bx_, by_ - kk.extensao()[1], n=8)
                kk.empurrar(lift=-8, capa=-6)
                kk.tocar(K.sequencia([(2, _com(agacha, estica=-1), 'out'), (3, pronto, 'out'), (1, pronto)]))
                ag.depois(0.22, _aparado)
            _mover(kk, kk.ancora(), K0, 0.36, altura=te * 30, fantasmas=1, on_fim=_chegou)

        # ── 3b) DEFESA: o Yoru emenda um avanco... e o chefe atravessa o
        #    montante na frente do corpo: a lamina bate e ele e jogado de volta ──
        def _aparado():
            boss.tocar('defesa', on_fim=boss_idle)
            perto = (frente - 64 * te, y_luta + 150 * te)       # salta: a lamina dele encontra o montante atravessado
            kk.tocar(K.sequencia([(2, pronto, 'segura'), (1, K.smear(corta_tra, pronto['a1']), 'segura'),
                                  (6, corta_tra, 'segura'), (1, corta_tra)]))
            _som('sacar_iai')
            _gemido()

            def _bateu():
                mx_, my_ = boss.mao()
                px_, py_ = mx_ - 8 * te, my_ + 34 * te
                kk.impacto(forte=True)
                kk.pausar(0.1)
                boss.pausar(0.1)
                _som('golpe_final')
                _som('koiguchi')
                _tremer(14)
                _estrela(camada, px_, py_, ps * 2, BRANCO, raios=8, dur=0.2)
                _anel(camada, (px_, py_), te * 6, te * 70, 0.25, BRANCO, esp=dp(2))
                faiscas.estourar(px_, py_, BRANCO, n=22, forca=dp(300), tam=ps)
                faiscas.estourar(px_, py_, BRASA, n=16, forca=dp(240), tam=ps)
                soco_camera((px_, py_), 1.1, 0.3)

                def _volta():
                    kk.tocar(K.sequencia([(3, _com(guarda2, pernas='recua', estica=-1), 'segura'),
                                          (5, _com(pronto, pernas='recua'), 'out'), (1, pronto)]))
                    _som('desliza')
                    _mover(kk, kk.ancora(), K0, 0.34, altura=te * 40, fantasmas=2,
                           on_fim=lambda: (poeira(K0[0], chao, n=8), _som('pouso'), ag.depois(0.25, _projetil)))
                ag.depois(0.14, _volta)
            _mover(kk, kk.ancora(), perto, 0.14, altura=te * 30, fantasmas=3, cor_fantasma=CIANO, on_fim=_bateu)

        # ── 4) PROJETIL: ele nivela o montante e dispara um raio de sangue; o
        #    Yoru corta o raio ao meio num iai e ja emenda: sobe cortando o
        #    peito (golpe 2), saca a azul no alto e mergulha no nucleo (golpe 3) ──
        def _projetil():
            cine.entrar()
            cam_em(1.25, foco=((K0[0] + bx) / 2.0, chao + 170 * te), dur=0.5)   # os dois no quadro, de perto
            ag.depois(0.95, lambda: cam_em(1.0, dur=0.25))

            def _q(i):
                if i == 12:
                    px_, py_ = boss.ponta()
                    _anel(camada, (px_, py_), te * 40, te * 6, 0.3, BRASA, esp=dp(3))     # junta energia na ponta
                elif i == 20:
                    _dispara()
            boss.tocar('aponta', on_quadro=_q, on_fim=boss_idle)

        def _dispara():
            px_, py_ = boss.ponta()
            alvo = (K0[0] + 34 * te, y_luta + 62 * te)
            _som('getsuga')
            _tremer(12)
            _estrela(camada, px_, py_, ps * 2, BRASA, raios=8, dur=0.2)
            _projetil_sangue(camada, (px_, py_), alvo, 0.3, te, on_chega=_rebate)
            chaves, i_r = K.golpe(pronto, corta_tra, lamina_recua=False, seg=P['segue1'],
                                  **dict(G, n_arma=2, prende=2))

            def _q(i):
                if i == i_r - GIRO:
                    _som('sacar_iai')
                    _gemido()
                    _mover(kk, kk.ancora(), A1, 0.24, ease='out', fantasmas=3, limite=(area, m))
                    golpear('dfl', dur=0.16)
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_sobe)

        def _rebate(x, y):
            # o raio se parte na lamina: duas metades voam para cima e para baixo
            kk.impacto(forte=True)
            kk.pausar(0.08)
            _som('vidro')
            _tremer(14)
            _brilho_tela(camada, 0.2, 0.15, (1.0, 0.4, 0.3))
            _estrela(camada, x, y, ps * 2, BRANCO, raios=8, dur=0.2)
            _anel(camada, (x, y), te * 6, te * 90, 0.3, BRASA, esp=dp(3))
            faiscas.estourar(x, y, BRASA, n=30, forca=dp(300), tam=ps)
            for sy in (1, -1):
                _projetil_sangue(camada, (x, y), (x - 210 * te, y + sy * 250 * te), 0.28, te, pequeno=True)

        def _sobe():
            chaves, i_r = K.golpe(arma_ve, corta_ve, seg=fim_ve, **dict(G, n_arma=2, prende=2, volta=4))

            def _q(i):
                if i == i_r - GIRO:
                    _som('pulo')
                    _gemido()
                    kk.empurrar(capa=-10, lift=10)
                    _mover(kk, kk.ancora(), B1, 0.3, ease='out', fantasmas=3)
                    golpear('h2', dur=0.18, on_meio=lambda: acerta(2))
            seq0 = K.sequencia(_de_agora(kk, 3, proxima=arma_ve) + [(4, arma_ve, 'out'), (1, arma_ve)])
            kk.tocar(seq0, on_fim=lambda: kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q,
                                                   on_fim=_saca_azul))
            kk.empurrar(capa=-10, cabelo=-6)

        def _saca_azul():
            seq = K.sequencia(_de_agora(kk, 2, proxima=pega_az) +
                              [(3, pega_az, 'out'), (3, saca_az, 'out'), (5, saca_az, 'segura'),
                               (4, arma_te, 'out'), (1, arma_te)])

            def _q(i):
                if i == 5:
                    hx2, hy2 = kk.ponta_espada(2)
                    faiscas.estourar(hx2, hy2, AZUL, n=16, forca=dp(130), tam=ps)
                    _anel(camada, kk.ponto_mao(2), ps, ps * 8, 0.3, AZUL, esp=dp(3))
                    _som('sacar')
                    kk.empurrar(cabelo=8, lift=4)
            _mover(kk, kk.ancora(), C0, 0.56, ease='suave', fantasmas=0)
            kk.tocar(seq, on_quadro=_q, on_fim=_te)

        def _te():
            chaves, i_r = K.golpe(arma_te, corta_te, seg=corta_te, **dict(G, n_arma=2, prende=2, volta=3))

            def _q(i):
                if i == i_r - GIRO:
                    _gemido(forte=True)
                    kk.empurrar(capa=12, lift=6)
                    _mover(kk, kk.ancora(), C1, 0.28, ease='in', fantasmas=4, limite=(area, m))
                    nuc = boss.ponto('nucleo')
                    golpear('h3', dur=0.2, on_meio=lambda: (acerta(3, forte=True), soco_camera(nuc, 1.14)))
                    ag.depois(0.05, lambda: golpear('h3b', dur=0.2, som='corte2'))
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_recua)

        def _recua():
            # mortal para tras: ele sente que vem coisa
            ax, ay = kk.ancora()
            p_pulo = _com(P['pulo'], olhos='s')
            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), guarda2, 0.44))
            _som('pulo')

            def _chegou():
                kk.rotacao = 0
                _som('pouso')
                bx_, by_ = kk.ancora()
                poeira(bx_, by_ - kk.extensao()[1], n=8)
                kk.mostrar(guarda2)
            _mover(kk, (ax, ay), K0, 0.44, altura=te * 90, rot=(0, 360), fantasmas=2, on_fim=_chegou,
                   rot_janela=(0.2, 0.75))
            cine.sair()
            ag.depois(0.25, _salto)

        # ── 5) SALTO: o chefe agacha, some no ceu... a sombra cresce no chao;
        #    o Yoru dispara por baixo e o chefe desaba do outro lado ──
        def _salto():
            boss.tocar('salto_prep', on_fim=_decola)
            _som('carga')

        def _decola():
            boss.tocar('salto_ar', loop=True)
            _som('pulo')
            _tremer(16)
            poeira(bx, chao, n=18)
            _anel(camada, (bx, chao + te * 2), te * 6, te * 120, 0.35, BRASA, esp=dp(3), achat=0.3)
            mover_chefe((bx, chao), (bx - 90 * te, H + 120 * te), 0.34, ease='out', on_fim=_no_ceu)
            cam[0].ir(1.06, foco=(W / 2.0, chao + 500 * te), dur=0.3)           # a camera olha para cima
            ag.depois(0.12, lambda: emote(camada, kk, '!!', 0.5))

        def _no_ceu():
            _sombra_chao(camada, bxl, chao, te * 24, te * 170, 0.62, te * 4)
            cam[0].ir(1.0, dur=0.45)
            ag.depois(0.3, _foge)
            ag.depois(0.6, _desaba)

        def _foge():
            # passa por baixo da sombra num risco, para o outro lado da tela
            kk.espelhar = False
            kk.mostrar(_com(guarda2, pernas='avanco_baixo'))
            _som('desliza')
            _linhas_velocidade(camada, 0.3, CIANO, y0=chao, y1=chao + 190 * te, n=12)

            def _freou():
                kk.espelhar = True                          # vira para onde ele vai cair
                kk.mostrar(guarda2)
                bx_, by_ = kk.ancora()
                poeira(bx_, by_ - kk.extensao()[1], n=8)
            _mover(kk, kk.ancora(), R0, 0.22, linear=True, fantasmas=5, cor_fantasma=CIANO, on_fim=_freou)

        def _desaba():
            boss.espelhar = True                            # agora olha para a direita, onde o Yoru esta
            boss.tocar('salto_desce', loop=True)
            mover_chefe((bxl, H + 120 * te), (bxl, chao), 0.2, ease='in', on_fim=_impacto_salto)

        def _impacto_salto():
            boss.tocar('pouso', on_fim=boss_idle)
            _som('golpe_final')
            _som('trevas')
            _tremer(36)
            _anel(camada, (bxl, chao + te * 4), te * 12, te * 340, 0.55, BRASA, esp=dp(6), achat=0.3, grao=3)
            _anel(camada, (bxl, chao + te * 4), te * 6, te * 200, 0.4, BRANCO, esp=dp(3), achat=0.3, grao=2)
            _brilho_tela(camada, 0.3, 0.25, (1.0, 0.3, 0.2), atras=boss)
            for k_ in range(-3, 6):
                poeira(bxl + k_ * 45 * te, chao, n=6)
            faiscas.estourar(bxl, chao, BRASA, n=44, forca=dp(360), tam=ps, gravidade=dp(300))
            _racha_chao(camada, bxl, chao, te, larg=460, n=11, atras=boss)
            cen.tranco()
            soco_camera((bxl, chao + 60 * te), 1.1, 0.5)
            # o chao joga o Yoru para cima um instante
            _pulinhos(kk, guarda2, n=1, altura=te * 26)
            ag.depois(0.55, lambda: _rajada(0))

        # ── 6) RAJADA: ele ainda esta se levantando - quatro golpes seguidos,
        #    alternando as espadas; o chefe revida com a garra e o Yoru sai num mortal ──
        RAJADA = [('sb1_a', 'sb1_b', 1, (150, -40)), ('sb2_a', 'sb2_b', 2, (215, 40)),
                  ('sb3_a', 'sb3_b', 1, (175, 0)), ('sb4_a', 'sb4_b', 2, (185, -5))]

        def _rajada(j):
            if j == 0:
                cam_em(1.45, foco=(bxl + 110 * te, chao + 150 * te), dur=0.2)   # a rajada de perto
            if j >= len(RAJADA):
                cam_em(1.0, dur=0.3)
                kk.tocar(K.sequencia(_de_agora(kk, 2, 'out') + [(3, guarda2, 'out'), (1, guarda2)]))
                return _garra()
            a, c_, qual, arc = RAJADA[j]
            arma, corta = P[a], P[c_]
            sm = K.smear(corta, arma['a1'] if qual == 1 else None, arma['a2'] if qual == 2 else None)
            cor = CIANO if qual == 1 else AZUL
            kk.espelhar = True

            def _q(q):
                if q != 1:
                    return
                nx, ny = boss.ponto('nucleo')
                px_ = nx + 26 * te + random.uniform(-10, 10) * te
                py_ = ny + random.uniform(-70, 40) * te
                camada.add_widget(CorteMeiaLua(centro=(px_, py_), raio=th * 1.7, ang_ini=180 - arc[0],
                                               ang_fim=180 - arc[1], espessura=th * 0.9, achat=0.4, cor=cor,
                                               dur_cheio=3 / 30.0, dur_decai=4 / 30.0))
                acerta(4 + j, (px_, py_), reage=False, leve=True, cor=cor)
                _som('corte2' if qual == 2 else 'corte')
                if j % 2 == 0:
                    _gemido()
                kk.empurrar(capa=8, cabelo=6)
            kk.parar()
            kk.mostrar(arma)
            perto = (bxl + (150 - j * 8) * te, y_luta)
            _mover(kk, kk.ancora(), perto, 0.07 if j else 0.16, linear=True, fantasmas=2 if not j else 1,
                   cor_fantasma=cor,
                   on_fim=lambda: kk.tocar(K.sequencia([(1, arma, 'segura'), (1, sm, 'segura'),
                                                        (2, corta, 'segura'), (1, corta)]),
                                           on_quadro=_q, on_fim=lambda: _rajada(j + 1)))

        def _garra():
            def _q(i):
                if i == 11:
                    _foge_garra()
                elif i == 16:
                    gx_, gy_ = boss.garra()
                    _som('corte2')
                    _tremer(10)
                    for k_ in range(3):
                        camada.add_widget(CorteMeiaLua(centro=boss.ponto('ombro'), raio=te * (150 + 22 * k_),
                                                       ang_ini=130, ang_fim=-50, espessura=te * 8, achat=1.0,
                                                       cor=BRASA, dur_cheio=3 / 30.0, dur_decai=5 / 30.0))
                    faiscas.estourar(gx_, gy_, BRASA, n=14, forca=dp(200), tam=ps)
            boss.tocar('garra', on_quadro=_q, on_fim=_gira)

        # ── 6b) CORTE GIRATORIO: a lamina da a volta inteira em volta dele (um
        #    anel de fogo varre a tela); o Yoru salta por cima do anel ──
        def _gira():
            def _q(i):
                if i == 12:
                    # salta reto para cima, num mortal, e cai no mesmo lugar
                    p_pulo = _com(P['pulo'], olhos='s')
                    kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), guarda2, 0.62))
                    _som('pulo')
                    a0 = kk.ancora()
                    _mover(kk, a0, a0, 0.62, altura=te * 300, rot=(0, -360), fantasmas=2,
                           rot_janela=(0.2, 0.8),
                           on_fim=lambda: (setattr(kk, 'rotacao', 0), kk.mostrar(guarda2), _som('pouso'),
                                           poeira(a0[0], chao, n=8)))
                elif i == 16:
                    boss.espelhar = not boss.espelhar            # de costas: a lamina passa por tras
                    _fogo_em_volta()
                elif i == 20:
                    boss.espelhar = not boss.espelhar
            boss.tocar('giratorio', on_quadro=_q, on_fim=_investe)

        def _fogo_em_volta():
            cx_, cy_ = boss.ax, chao + 120 * te
            _som('getsuga')
            _som('corte2')
            _tremer(22)
            cen.tranco()
            _brilho_tela(camada, 0.2, 0.2, (1.0, 0.3, 0.2), atras=boss)
            _racha_chao(camada, cx_, chao, te, larg=520, n=12, atras=boss)
            for r1, esp_, d_ in ((430, 9, 0.5), (330, 5, 0.42), (230, 3, 0.34)):
                _anel(camada, (cx_, cy_), te * 60, te * r1, d_, BRASA, esp=dp(esp_), achat=0.22, grao=3)
            _linhas_velocidade(camada, 0.35, BRASA, y0=chao + 60 * te, y1=chao + 190 * te, n=16, sentido=1)
            for k_ in range(-4, 7):
                poeira(cx_ + k_ * 50 * te, chao, n=4)
            faiscas.estourar(cx_, cy_, BRASA, n=40, forca=dp(380), tam=ps)

        def _foge_garra():
            ax, ay = kk.ancora()
            p_pulo = _com(P['pulo'], olhos='s')
            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), guarda2, 0.4))
            _som('pulo')

            def _chegou():
                kk.rotacao = 0
                _som('pouso')
                bx_, by_ = kk.ancora()
                poeira(bx_, by_ - kk.extensao()[1], n=8)
                kk.mostrar(guarda2)
            _mover(kk, (ax, ay), R0, 0.4, altura=te * 110, rot=(0, -360), fantasmas=2, on_fim=_chegou,
                   rot_janela=(0.2, 0.75))

        # ── 7) INVESTIDA: ele recolhe o montante e atravessa a tela numa estocada;
        #    o Yoru salta por cima e desce as duas laminas em X nas costas dele (golpe 8) ──
        def _investe():
            cine.entrar()

            def _q(i):
                if i == 13:
                    _salta_investida()
                elif i == 17:
                    _som('sacar_iai')
                    _som('rugido')
                    _tremer(18)
                    boss.inclina_capa = -16.0
                    _linhas_velocidade(camada, 0.45, BRASA, y0=chao + 20 * te, y1=chao + 330 * te, n=22,
                                       sentido=1)
                    for k_ in range(6):
                        ag.depois(0.03 * k_, lambda k_=k_: poeira(bxl + (60 + 45 * k_) * te, chao, n=5))
                    mover_chefe((bxl, chao), (bx, chao), 0.2, ease='out',
                                on_fim=lambda: setattr(boss, 'inclina_capa', 0.0))
            boss.tocar('investida', on_quadro=_q, on_fim=boss_idle)

        def _salta_investida():
            kk.espelhar = True
            kk.tocar(_voo_seq(K.esticado(_com(P['pulo'], olhos='s')), arma_fo, arma_fo, 0.34))
            _som('pulo')
            kk.empurrar(capa=-10, lift=10)
            _mover(kk, kk.ancora(), Xm, 0.34, ease='out', fantasmas=3, on_fim=_x_de_cima)

        def _x_de_cima():
            kk.espelhar = False                             # no alto ele ja esta virado para o chefe, que passou
            chaves, i_r = K.golpe(arma_fo, corta_fo, **dict(G, n_arma=2, prende=2, volta=4))

            def _q(i):
                if i == i_r - GIRO:
                    _som('fala_kurae')
                    kk.empurrar(capa=10, cabelo=8, lift=6)
                    _mover(kk, kk.ancora(), X1, 0.24, ease='in', fantasmas=4)
                    nuc = boss.ponto('nucleo')
                    golpear('h4', dur=0.2, on_meio=lambda: (acerta(8, (nuc[0], nuc[1] + 50 * te), forte=True,
                                                                   reage=False), soco_camera(nuc, 1.16, 0.5),
                                                            _virada()))
                    ag.depois(0.04, lambda: golpear('h4b', dur=0.2, som='corte2'))
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_cai_do_x)

        def _cai_do_x():
            def _chegou():
                _som('pouso')
                bx_, by_ = kk.ancora()
                poeira(bx_, by_ - kk.extensao()[1], n=8)
                kk.tocar(K.sequencia([(2, _com(guarda2, estica=-1), 'out'), (3, guarda2, 'out'), (1, guarda2)]))
            _mover(kk, kk.ancora(), (K0[0], y_luta), 0.3, altura=te * 20, fantasmas=1, on_fim=_chegou)

        # ── 8) o chefe cai de joelho, apoiado no montante... e se levanta em
        #    FURIA: ergue o montante, tudo aceso, e o sopro joga o Yoru longe ──
        def _virada():
            ag.depois(0.5, lambda: cam_em(1.3, foco=(bx - 40 * te, chao + 170 * te), dur=0.6))   # ele caido, de perto
            ag.depois(1.7, lambda: cam_em(1.0, dur=0.25))
            boss.espelhar = False                           # vira para o Yoru (o claro do golpe esconde a troca)
            boss.tocar('cambaleia', on_fim=lambda: boss.tocar('ajoelhado', loop=True))
            cine.sair()
            ag.depois(1.75, _furia)

        def _furia():
            _som('rugido')
            boss.tocar('carrega', on_fim=lambda: boss.tocar('carrega_segura', loop=True))
            ag.depois(0.34, _empurrao)

        def _empurrao():
            ox_, oy_ = boss.ponto('nucleo')
            _anel(camada, (ox_, oy_), te * 10, te * 330, 0.5, BRASA, esp=dp(6), grao=3)
            _tremer(22)
            cen.tranco()
            _brilho_tela(camada, 0.22, 0.25, (1.0, 0.25, 0.16), atras=boss)
            _som('carga')
            ax, ay = kk.ancora()
            kk.tocar(K.sequencia([(2, _com(guarda2, pernas='recua', estica=-1), 'segura'),
                                  (8, _com(guarda2, pernas='recua'), 'segura'), (1, guarda2)]))
            kk.empurrar(capa=-16, cabelo=-12, lift=4)
            _som('desliza')

            def _parou():
                bx_, by_ = kk.ancora()
                poeira(bx_, by_ - kk.extensao()[1], n=10)
                ag.depois(0.3, _ban)
            _mover(kk, (ax, ay), E0, 0.36, ease='out', fantasmas=2, limite=(area, m), on_fim=_parou)

        # ── 6. golpe final (estilo Bleach) ───────────────────────────
        cx_meio = ox_t + titulo.tw / 2.0

        def _fitas(alvo=None, aperto=None, vel=None):
            for f in estado.get('fitas', ()):
                if alvo is not None:
                    f.alvo = alvo
                if aperto is not None:
                    f.aperto = aperto
                if vel is not None:
                    f.vel = vel

        # ── BAN-KAI (igual ao Ichigo) ─────────────────────────────────
        # ERGUE a katana num arco e desce APONTANDO para a frente; a espada
        # azul vira luz e entra na katana; a outra mao SEGURA o braco.
        # "BAN..." - a borda de energia ferve em volta dele. "KAI!!" - estouro
        # de luz: o reiatsu roxo (miolo branco) cobre ele inteiro e sobe numa
        # coluna ate o ceu, ferve, os olhos acendem la dentro... e se desfaz
        # em fiapos revelando o Bankai.
        b_agacha = K.pose(pernas='base_larga', dy=-1, m1=(-2, 2), a1=200.0, m2=(-4, -2), a2=230.0, olhos='s')
        b_ergue = K.pose(pernas='base_larga', dx=1, m1=(3, 13), a1=88.0, m2=(-4, -3), a2=232.0, olhos='s')
        b_aponta = K.pose(pernas='base_larga', dx=1, m1=(9, 3), a1=2.0, m2=(-5, -3), a2=238.0, olhos='s')
        b_livre = K.pose(pernas='base_larga', dx=1, m1=(9, 3), a1=2.0, m2=(-4, -2), olhos='s')
        b_segura = K.pose(pernas='base_larga', dx=1, m1=(9, 3), a1=2.0, m2=(8.5, 2.5), olhos='s', agarra=True)
        b_grita = K.pose(pernas='base_larga', dx=1, dy=-1, m1=(9, 3), a1=2.0, m2=(8.5, 2.5), olhos='g',
                         agarra=True)
        mug = K._fund(pernas='base_larga', m1=(8, 1), a1=-28.0, olhos='l', evo=True, mugetsu=True)
        kk.precarregar([b_agacha, b_ergue, b_aponta, b_livre, b_segura, b_grita])
        try:
            K.clipes_dados()                                      # clipes do Bankai: le antes
            K.aquecer_clipes()                                    # e monta os desenhos aos poucos
        except Exception as _e:
            print(f"[cena] clipes do Bankai: {_e}")
        mug_b = _com(mug, cresce=1.0)          # a pose que os efeitos leem no Bankai (espada fundida)

        def _bk(nome, loop=True, on_fim=None, on_quadro=None, k=None, t0=0.0):
            """Toca o clipe `nome` do Bankai (desenho da referencia, peca por peca)."""
            (k or kk).mostrar_clipe(nome, loop=loop, on_fim=on_fim, on_quadro=on_quadro, base=mug_b, t0=t0)

        def _bk_idle(k=None):
            _bk('idle', k=k)

        def _ban():
            # de frente para o chefe em furia: agacha (antecipacao), ERGUE a
            # katana num arco para cima, segura um instante e desce APONTANDO
            # para ele (passa um pouquinho do ponto e volta)
            ax, ay = kk.ancora()
            cam[0].ir(1.05, foco=(ax, ay + alt * 0.35), dur=2.4)
            _fundo(tela, reator=0.22, barra=0.1, dur=0.8)       # o mundo escurece um pouco
            seq = K.sequencia([(3, _com(P['agacha'], olhos='s'), 'out'), (8, b_agacha, 'out'),
                               (6, b_ergue, 'segura'), (7, b_ergue, 'mola'), (1, b_aponta)])

            def _q(i):
                if i == 4:
                    _som('sacar')
                    kk.empurrar(cabelo=-6, lift=5)
                elif i == 18:
                    _som('corte2')
                    kk.empurrar(capa=-8, cabelo=-6)
                elif i == 22:
                    hx, hy = kk.ponta_espada(1)
                    faiscas.estourar(hx, hy, CIANO, n=8, forca=dp(90), tam=ps)
            kk.tocar(seq, on_quadro=_q, on_fim=_azul_vira_luz)

        def _azul_vira_luz():
            # a espada azul acende, vira luz e corre pelo ar ate a katana
            hx2, hy2 = kk.ponto_mao(2)
            tx2, ty2 = kk.ponta_espada(2)
            hx1, hy1 = kk.ponto_mao(1)
            kk.mostrar(b_livre)
            _som('fusao')
            mx, my = (hx2 + tx2) / 2.0, (hy2 + ty2) / 2.0
            faiscas.estourar(mx, my, AZUL, n=22, forca=dp(110), tam=ps)
            _estrela(camada, mx, my, ps, AZUL)
            u = te * 2

            def forma(t, p, uu):
                s = min(1.0, t / 0.3)
                e = s * s * (3 - 2 * s)
                for j in range(10):                   # cabeca clara e o rastro que esfria
                    ss = e - j * 0.04
                    if ss < 0:
                        break
                    x = mx + (hx1 - mx) * ss
                    y = my + (hy1 - my) * ss + math.sin(ss * math.pi) * alt * 0.12
                    nome = 'luz' if j < 2 else ('clara' if j < 5 else 'cor')
                    g = 2 if j < 3 else 1
                    p.setdefault(nome, []).append((math.floor(x / u) * u, math.floor(y / u) * u, g * u, g * u))
            camada.add_widget(_EfeitoPixel(_cores_efeito(AZUL), 0.36, forma))

            def _chega():
                # a luz entra na katana: estrela e faiscas na mao (sem piscar o
                # corpo inteiro - isso fica para os golpes)
                _estrela(camada, hx1, hy1, ps, BRANCO)
                faiscas.estourar(hx1, hy1, AZUL, n=12, forca=dp(120), tam=ps)
                _som('cristal')
            ag.depois(0.3, _chega)
            ag.depois(0.5, _segura)

        def _segura():
            # a outra mao vem e SEGURA o braco da espada; silencio
            seq = K.sequencia([(6, b_livre, 'out'), (1, b_segura)])
            kk.tocar(seq, on_fim=lambda: kk.tocar(K.poder(b_segura, n=36, forca=0.4, sobe=0.5, lift=1.0),
                                                   loop=True))
            ag.depois(0.18, lambda: _som('agarra'))
            ag.depois(0.6, _ban_fala)

        def _ban_fala():
            # "BAN..." - a borda de energia comeca a ferver em volta dele
            balao(camada, 'BAN...', kk, tipo='fala', dur=1.1)
            _som('carga')
            CH.aquecer(['golpe', 'apanha', 'idle'], por_quadro=1)
            kk.borda_energia(0.35)
            chamas.alvo = 0.3                               # o reiatsu comeca a subir dele
            ag.depois(0.3, lambda: kk.borda_energia(0.7))
            ag.depois(0.6, lambda: kk.borda_energia(1.0))
            _fundo(tela, reator=0.35, barra=0.1, dur=0.9)
            cam[0].ir(1.07, foco=kk.ancora(), dur=0.9)
            t = [0.0]

            def _sobe(dt):
                t[0] += dt
                if t[0] > 0.95:
                    return False
                kk.empurrar(lift=1.2, cabelo=0.8)
                if random.random() < 0.6:
                    ax2, ay2 = kk.ancora()
                    faiscas.estourar(ax2 + random.uniform(-1, 1) * 9 * ps, ay2 - 11 * ps, ROXO, n=1,
                                     forca=dp(30), tam=max(2, ps * 0.6), gravidade=-dp(300))
                return True
            ag.cada(0.05, _sobe)
            _tremer(4)
            ag.depois(0.75, _kai)

        def _kai():
            # "KAI!!" - grito, quadro de impacto e o ESTOURO de luz
            kk.borda_energia(0)
            kk.parar()
            kk.mostrar(b_grita)
            balao(camada, 'KAI!!', kk, tipo='grito', dur=1.3, font_size=sp(40))
            _som('kiai_kai')
            _som('golpe_final')
            ax, ay = kk.ancora()
            _quadro_impacto(camada, kk, (ax, ay + alt * 0.3))
            _tremer(34)
            cam[0].ir(1.0, dur=0.15)
            ag.depois(2.2 / 30.0, _estouro)
            # o chefe nao espera: desce o montante em cima dele...
            boss.tocar('golpe', t0=0.62, on_fim=boss_idle)
            ag.depois(0.17, _repelido)

        def _repelido():
            # ... e a explosao de reiatsu joga a lamina (e ele) para tras
            px_, py_ = boss.ponta()
            boss.impacto(quadros=5, tremor=10)
            boss.tocar('apanha', on_fim=boss_idle)
            _estrela(camada, px_, py_, ps, BRANCO, raios=8, dur=0.2)
            faiscas.estourar(px_, py_, ROXO, n=22, forca=dp(260), tam=ps)
            faiscas.estourar(px_, py_, BRASA, n=14, forca=dp(220), tam=ps)
            _anel(camada, (px_, py_), te * 4, te * 60, 0.3, ROXO, esp=dp(3))
            _som('corte2')

        def _estouro():
            # o reiatsu explode dele: raios, onda de choque no chao, e o casulo
            # cresce ate cobrir tudo; coberto, por baixo ele ja e o Bankai
            kr = K.KiritoPixel(ps=ps)
            kr.espelhar = kk.espelhar
            kr.escala_clipe = ESC_BK
            i = camada.children.index(kk) if kk in camada.children else 0
            camada.add_widget(kr, index=i)                       # na frente dele
            ax_k, ay_k = kk.ancora()
            kr.ancorar(ax_k, ay_k + sobe_bk)
            estado['kr'] = kr
            _som('absorve')
            _som('reiatsu')
            _fundo(tela, reator=0.5, barra=0.1, dur=0.2)
            _brilho_tela(camada, 0.38, 0.27, (0.62, 0.42, 1.0), atras=kk)   # o ceu acende roxo atras dele

            def _q(i):
                if i == 4 and 'pilar' not in estado:
                    _pilar(kr)
                if i >= 6 and kk._desenho is None:
                    kk.escala_clipe = ESC_BK
                    kk.ancorar(ax_k, ay_k + sobe_bk)
                    _bk('idle')                            # coberto: ja e o Bankai la dentro
                    chamas.alvo = 0.35
            kr.mostrar_clipe('rei_estouro', loop=False, on_quadro=_q, on_fim=_ferve)

        def _pilar(kr):
            # a coluna de luz sobe do topo do casulo ate o fim da tela
            p = _PilarReiatsu(kr)
            i = camada.children.index(kr) if kr in camada.children else 0
            camada.add_widget(p, index=i + 1)                    # atras do casulo
            estado['pilar'] = p

        def _ferve():
            # FERVENDO: ele sumiu dentro do reiatsu; no fim os olhos acendem.
            # A dissipacao entra no fim de uma volta da fervura (o fogo continua
            # do mesmo ponto, sem pulo)
            kr = estado.get('kr')
            if kr is None:
                return _revela()
            kr.mostrar_clipe('rei_ferve', loop=True)
            _tremer(10)
            ag.depois(0.8, _olhos)

            def _no_fim_da_volta():
                k2 = estado.get('kr')
                if k2 is None:
                    return _revela()
                volta = len(K.clipes_dados()['clipes']['rei_ferve']['quadros']) / 30.0
                resto = volta - (k2._clipe_t % volta)
                if resto > 1 / 30.0 and resto < volta - 1 / 60.0:
                    ag.depois(resto, _revela)
                else:
                    _revela()
            ag.depois(1.25, _no_fim_da_volta)

        def _olhos():
            # a silhueta escura dele aparece dentro da energia (em degraus) e o
            # olho acende por cima - o quadro classico antes da revelacao
            kr = estado.get('kr')
            o = kk.olhos_desenho() if kk._desenho is not None else None
            if kr is None or o is None:
                return
            try:
                tex = K.quadro_clipe(kk._desenho, kk._quadro_atual(), silhueta=True)[0]
                sil = Widget(size_hint=(None, None), size=(0, 0))
                with sil.canvas:
                    c_sil = Color(0.07, 0.02, 0.15, 0.0)
                    Rectangle(texture=tex, pos=(kk.x + kk._rect.pos[0], kk.y + kk._rect.pos[1]),
                              size=kk._rect.size, tex_coords=tuple(kk._rect.tex_coords))
                camada.add_widget(sil)
                estado['sombra'] = sil
                estado['cor_sombra'] = c_sil
                for j, a in enumerate((0.7, 0.92)):
                    ag.depois(0.08 * j, lambda a=a: setattr(c_sil, 'a', a))
            except Exception as e:
                print(f"[cena] sombra do Bankai: {e}")
            ol = _OlhosAcesos(o, kr.te_clipe())
            camada.add_widget(ol)
            estado['olhos'] = ol
            _som('titulo')

        def _revela():
            # o reiatsu se desfaz em fiapos subindo: aparece o BANKAI, com o
            # cabelo e o sobretudo ainda levantados pelo vento de energia
            kr = estado.get('kr')
            p = estado.pop('pilar', None)
            if p is not None:
                p.sumir(0.45)
            # a energia sai primeiro de cima do corpo: no mesmo quadro a silhueta
            # escura da lugar ao Bankai de verdade (com os olhos ainda acesos)
            estado.pop('cor_sombra', None)
            for chave in ('olhos', 'sombra'):
                w = estado.pop(chave, None)
                if w is not None and w.parent is not None:
                    w.parent.remove_widget(w)
            _bk('revela', loop=False, on_fim=_bk_idle)
            CH.aquecer(['golpe', 'apanha', 'idle'], por_quadro=1)
            chamas.alvo = 0.8
            aura.alvo = 0.5
            _som('transicao')
            ax, ay = kk.ancora()
            faiscas.estourar(ax, ay + alt * 0.4, ROXO, n=28, forca=dp(220), tam=te * 2, gravidade=-dp(90))

            def _fim_rei():
                k2 = estado.pop('kr', None)
                if k2 is not None and k2.parent is not None:
                    k2.parent.remove_widget(k2)
                ag.depois(0.25, _acende_lamina)
            if kr is not None:
                kr.mostrar_clipe('rei_dissipa', loop=False, on_fim=_fim_rei)
            else:
                _fim_rei()

        def _acende_lamina():
            # o fio roxo da espada acende da guarda ate a ponta
            hx, hy = kk.ponto_mao(1)
            tx, ty = kk.ponta_espada(1)
            aura.alvo = 0.7
            _estrela(camada, hx, hy, ps, BRANCO)
            faiscas.estourar(hx, hy, BRANCO, n=10, forca=dp(150), tam=te * 2)
            _som('fusao')

            def forma(t, p, u):
                s = min(1.0, t / 0.32)
                for j in range(9):                        # cabeca clara e um rastro que esfria
                    ss = s - j * 0.035
                    if ss < 0:
                        break
                    x = hx + (tx - hx) * ss
                    y = hy + (ty - hy) * ss
                    nome = 'luz' if j < 2 else ('clara' if j < 5 else 'cor')
                    g = 2 if j < 3 else 1
                    p.setdefault(nome, []).append((math.floor(x / u) * u - (g - 1) * u,
                                                   math.floor(y / u) * u - (g - 1) * u, g * u, g * u))
            camada.add_widget(_EfeitoPixel(_cores_efeito(ROXO), 0.5, forma))
            ag.depois(0.32, lambda: (faiscas.estourar(tx, ty, ROXO, n=14, forca=dp(170), tam=te * 2),
                                     _estrela(camada, tx, ty, ps, ROXO)))
            ag.depois(0.5, _duelo)

        def _duelo():
            # o chefe nao espera: desce o montante em cima do Bankai... que some
            # num passo (so ficam as sombras roxas) e reaparece no alto
            ax, ay = kk.ancora()
            alto = (ax - 14 * te, ay + 116 * te)          # (o Bankai e grande: cabelo e casaco podem sair do quadro)

            def _q(i):
                if i == 20:
                    _som('teleporte')
                    kk.empurrar(capa=-10, cabelo=-8, lift=8)
                    _mover(kk, (ax, ay), alto, 0.1, linear=True, fantasmas=5, cor_fantasma=ROXO)
                elif i == 24:                                # cravou no chao vazio
                    px_, _py = boss.ponta()
                    poeira(px_, chao, n=14)
                    faiscas.estourar(px_, chao, BRASA, n=18, forca=dp(230), tam=ps)
                    _anel(camada, (px_, chao + te * 2), te * 4, te * 80, 0.35, BRASA, esp=dp(3), achat=0.3)
                    _som('golpe_final')
                    _tremer(18)
                    ag.depois(0.1, _revida)
            boss.tocar('golpe', t0=0.3, on_quadro=_q, on_fim=boss_idle)

        def _revida():
            # ... ja cortando: a lamina negra desce na cabeca do chefe
            feito = [False]

            def _q(i):
                if i >= 5 and not feito[0]:
                    feito[0] = True
                    golpear('ctr', dur=0.16, som='corte2',
                            on_meio=lambda: acerta(9, boss.ponto('cabeca'), forte=True, cor=ROXO))
            _gemido(forte=True)
            _bk('corte', loop=False, on_quadro=_q, on_fim=lambda: _bk('fim', loop=False, on_fim=_bk_idle))
            ag.depois(0.6, _lua)

        def _lua():
            # a lua negra sobe atras dele e o fogo ruge (ele continua flutuando)
            ax, ay = kk.ancora()
            CH.aquecer(['rugido', 'carrega', 'carrega_segura'], por_quadro=1)
            lua = _LuaNegra((ax + (-1 if kk.espelhar else 1) * alt * 0.05, ay + alt * 0.55), alt * 1.05,
                            te * 2, dur=0.7)
            camada.add_widget(lua, index=len(camada.children))      # atras de tudo
            estado['lua'] = lua
            chamas.alvo = 1.0
            aura.alvo = 1.0
            _som('trevas')
            _tremer(12)
            _brilho_tela(camada, 0.35, 0.22, (0.8, 0.62, 1.0))
            faiscas.estourar(ax, ay + alt * 0.5, ROXO, n=26, forca=dp(230), tam=te * 2, gravidade=-dp(80))
            cam[0].ir(1.15, foco=(ax, ay + alt * 0.45), dur=0.6)
            # close: os olhos acendem roxos; depois a escuridao
            ag.depois(0.55, lambda: close_rosto(camada, 'mugetsu', dur=0.85, y_rel=0.84, on_fim=_posiciona))

        def _posiciona():
            # desce de volta para a frente do chefe, com a lamina na altura da
            # frase: dali a escuridao vai sair dele
            lua = estado.pop('lua', None)
            if lua is not None:
                lua.sumir(0.3)
            kk.espelhar = False
            x_ini, y_ini = min(E0[0] + th * 0.4, bx - 190 * te), y_luta + sobe_bk + 12 * te
            ax, ay = kk.ancora()
            _som('reiatsu')
            cam[0].ir(1.0, dur=0.6)
            boss.tocar('rugido', on_quadro=_berro,
                       on_fim=lambda: boss.tocar('carrega', t0=0.3,
                                                 on_fim=lambda: boss.tocar('carrega_segura', loop=True)))
            # levita: sobe devagar, o cabelo e o casaco flutuando
            _mover(kk, (ax, ay), (x_ini, y_ini), 0.8, altura=th * 0.25, fantasmas=0, on_fim=_trevas,
                   ease='suave')

        def _trevas():
            # MUGETSU: a escuridao sai dele e engole a tela inteira (a frase e
            # o infinito somem); so os olhos, o fogo e a espada brilham
            ax, ay = kk.ancora()
            cine.entrar()                                    # (a lua e o castelo ficam: o corte acontece no mundo dele)
            _brilho_tela(camada, 0.3, 0.3, (0.5, 0.3, 0.9), atras=boss)
            _som('trevas')
            aura.alvo = 1.0
            cam[0].ir(1.12, foco=(ax, ay + alt * 0.3), dur=1.4)
            kk.empurrar(capa=-6, cabelo=-5, lift=4)
            ag.depois(0.8, _ergue)

        def _ergue():
            # silencio: ele diz o nome do golpe, a lamina vai para tras (devagar)
            # e segura tremendo
            _bk('carga', loop=False, on_fim=lambda: _bk('carga_segura'))
            _som('fala_ougi')
            ag.depois(1.12, _golpe_final)             # o corte cai no "GI!" do grito

        def _golpe_final():
            # UM corte so: a lamina atravessa e um risco de luz corta a tela de
            # um lado ao outro na altura da frase... e tudo congela
            feito = [False]

            def _q(i):
                if i >= 5 and not feito[0]:           # a lamina passa pela frente: o golpe
                    feito[0] = True
                    _impacto_final()
            _bk('corte', loop=False, on_quadro=_q,
                on_fim=lambda: _bk('fim', loop=False, on_fim=_bk_idle))

        def _impacto_final():
            kk.impacto(forte=True)
            _, cy = titulo.x_do_trecho(0, len(texto))
            tv = estado.get('trevas')
            if tv is not None:
                tv.cortar(cy)
            golpear('cus', dur=0.18)                 # a luz roxa atravessa a tela na altura da frase
            if titulo.parent is camada:              # a frase vai nascer POR CIMA do chefe
                camada.remove_widget(titulo)
                camada.add_widget(titulo)
            # talhos atrasados (classico de anime): ele ja passou... e os cortes
            # vao aparecendo no corpo do chefe, um depois do outro
            cx0, cy0, cx1, cy1 = boss.corpo()
            rnd_t = random.Random(4)
            for n_ in range(6):
                def _talho(n_=n_):
                    a = math.radians(rnd_t.choice((-38, -20, 16, 34, 62, -64)))
                    mx_ = rnd_t.uniform(cx0, cx1)
                    my_ = rnd_t.uniform(cy0 + (cy1 - cy0) * 0.2, cy1 - (cy1 - cy0) * 0.12)
                    L = rnd_t.uniform(120, 200) * te
                    u2 = te * 2
                    linha = _reta_pixels(mx_ - math.cos(a) * L, my_ - math.sin(a) * L,
                                         mx_ + math.cos(a) * L, my_ + math.sin(a) * L, u2)
                    camada.add_widget(_PixelsRoxo([linha], u2, cresce=0.05, fica=0.5, some=0.1, grossura=1))
                    faiscas.estourar(mx_, my_, random.choice((ROXO, BRANCO)), n=5, forca=dp(170), tam=te * 2)
                    _som('corte' if n_ % 2 else 'corte2')
                    _tremer(5)
                ag.depois(0.16 + 0.07 * n_, _talho)
            # ... e ele vai junto: num passo so atravessa o chefe e para do outro
            # lado, de costas para ele
            ax0, ay0 = kk.ancora()
            alem = (min(W - m - 60 * te, bx + 64 * te), ay0)
            _mover(kk, (ax0, ay0), alem, 0.09, linear=True, fantasmas=6, cor_fantasma=ROXO)
            # ... e passa pela cintura do chefe: ele congela, branco
            boss.impacto(quadros=8, tremor=0)
            boss.pausar(3.0)
            barra_c.dano(0.0)

            def _prepara_cacos():
                # a conta pesada (foto do chefe em blocos, cacos) cai aqui, com
                # a cena congelada - a explosao depois sai sem tranco
                try:
                    from efeitos import explodir_estilhacos
                    bxw, byw = camada.to_window(bx, cy)
                    estado['cacos'] = explodir_estilhacos(boss, lambda: None, corte=0.0, tremor=0, px=te * 3,
                                                          racha=0.5, ponto=(bxw, byw), adiar=True,
                                                          max_celulas=12000, n_cacos=34, paleta='brasa')
                except Exception as e:
                    print(f"[cena] chefe em cacos: {e}")
            ag.depois(0.38, _prepara_cacos)
            ag.depois(0.1, lambda: _quadro_impacto(camada, kk, (bx, cy)))
            _som('sacar_iai')
            cam[0].ir(1.0, dur=0.1)
            ag.depois(0.12, lambda: kk.pausar(0.75))
            ag.depois(0.9, _abre)

        def _abre():
            # a escuridao se abre no corte: a frase aparece gravada dentro dele
            tv = estado.get('trevas')
            if tv is not None:
                tv.abrir(0.6)
            _, cy = titulo.x_do_trecho(0, len(texto))
            # A FRASE NASCE DO CHEFE: de dentro do corpo que se parte sai uma brasa
            # para cada letra; onde ela chega a letra acende em brasa (branco ->
            # brasa -> o ciano do app). As letras do meio, mais perto dele, primeiro.
            estado['chefe_morto'] = True
            alvos = [(li, ox_t + (titulo._larg[li] + titulo._larg[li + 1]) / 2.0, cy)
                     for li, letra in enumerate(texto) if letra.strip()]
            alvos.sort(key=lambda a_: abs(a_[1] - bx))

            def _acende(li):
                lx_ = ox_t + (titulo._larg[li] + titulo._larg[li + 1]) / 2.0
                titulo.revelar(li, li + 1, dur=0.5, cor=BRASA)
                _estrela(camada, lx_, cy, ps * 0.7, BRASA, raios=4, dur=0.14)
                faiscas.estourar(lx_, cy, BRASA, n=4, forca=dp(120), tam=te * 2, gravidade=dp(200))
                if li % 3 == 0:
                    _som('cristal')
            cb = boss.corpo()
            _brasas_para_letras(camada, alvos, (cb[0], cb[1] + (cb[3] - cb[1]) * 0.15, cb[2], cb[3] - (cb[3] - cb[1]) * 0.1),
                                0.95, _acende)
            ag.depois(1.25, lambda: [titulo.garantir(i0, i1) for i0, i1 in _TRECHOS])   # nenhuma letra fica para tras
            for j in range(9):
                xj = area[0] + (area[2] - area[0]) * (j + 0.5) / 9.0
                faiscas.estourar(xj, cy, random.choice((ROXO, BRANCO, (0.85, 0.72, 1.0))), n=5,
                                 forca=dp(240), tam=ps, gravidade=dp(160))
            _som('getsuga')
            _tremer(28)
            _brilho_tela(camada, 0.5, 0.35, (0.9, 0.82, 1.0))
            # o mundo do chefe se desfaz com ele: volta a tela do app
            cen.fechar(0.6)
            cine.sair()
            _fundo(tela, reator=0.5, barra=0.1, dur=0.8)
            # o chefe se parte no corte (as duas metades se afastam) e vira cacos
            soltar = estado.pop('cacos', None)
            if soltar is not None:
                soltar()
                _som('vidro')
            else:
                boss.opacity = 0
            barra_c.sumir()
            ag.depois(0.3, _para)

        def _para():
            # de costas para a frase que acende letra por letra... e o mundo segura a respiracao
            ag.depois(0.7, _separa)

        def _separa():
            # a espada evoluida se divide de novo nas duas e ele desce para
            # pousar em cima da frase
            hx2, hy2 = kk.ponto_mao(1)
            aura.alvo = 0.0
            chamas.alvo = 0.0
            K.definir_ambiente('')                           # o mundo do chefe acabou: ele volta para a luz do app
            dupla = _com(P['dupla'], olhos='s')
            dupla_m = None
            # a lamina se divide nas duas: estalo nas maos
            kk.impacto()
            faiscas.estourar(hx2, hy2, BRANCO, n=18, forca=dp(160), tam=ps)
            faiscas.estourar(hx2, hy2, AZUL, n=10, forca=dp(120), tam=ps)
            _anel(camada, (hx2, hy2), ps * 2, ps * 14, 0.35, CIANO)
            _som('separa')
            ag.depois(0.22, lambda: _desfaz(dupla, dupla_m))

        def _desfaz(dupla, dupla_m):
            # o anel desce da cabeca aos pes: por cima dele ele ja voltou ao
            # normal, por baixo ainda e o Bankai - as chamas se apagam
            kk2 = K.KiritoPixel(ps=ps)
            kk2.espelhar = kk.espelhar
            i = camada.children.index(kk) if kk in camada.children else 0
            camada.add_widget(kk2, index=i)                     # na frente (o de cima e o normal)
            kk2.ancorar(*kk.ancora())
            kk2.mostrar(dupla)
            kk2._preso = dict(kk._preso)
            ax, ay = kk.ancora()
            esq, baixo, dir_, cima = kk.extensao(_com(dupla, a1=None, a2=None))
            eb = kk.extensao()                             # o desenho do Bankai e mais alto
            y_alto, y_baixo = ay + max(cima, eb[3]) + te * 6, ay - max(baixo, eb[1]) - te * 3
            cx_c = ax + (dir_ - esq) / 2.0
            larg = (esq + dir_) * 1.05
            passo = te * 2
            anel = _AnelEnergia(te * 2)
            camada.add_widget(anel)
            _som('absorve')
            dur = 0.55
            t = [0.0]
            kk2.recortar(y_alto, None)
            kk.recortar(None, y_alto)

            def _p(dt):
                t[0] += dt
                s = min(1.0, t[0] / dur)
                y = y_alto + (y_baixo - y_alto) * s
                yq = math.floor(y / passo) * passo
                kk2.recortar(yq, None)
                kk.recortar(None, yq)
                anel.pos_linha(cx_c, yq, larg, dt)
                if int(t[0] * 60) % 3 == 0:
                    faiscas.estourar(cx_c + random.uniform(-0.5, 0.5) * larg, yq, ROXO, n=2,
                                     forca=dp(60), tam=te * 2, gravidade=-dp(200))
                if s >= 1.0:
                    kk.recortar()
                    kk.mostrar(dupla)
                    kk.parar()
                    kk._preso = dict(kk2._preso)
                    for w in (kk2, anel):
                        if w.parent is not None:
                            w.parent.remove_widget(w)
                    ag.depois(0.12, _desce)
                    return False
                return True
            ag.cada(1 / 60., _p)

        def _desce():
            ax, ay = kk.ancora()
            ax_t = min(max(ax, ox_t + titulo.tw * 0.14), ox_t + titulo.tw * 0.84)   # em cima das letras
            alvo = quadro(ax_t, y_topo, ['dupla', 'saca2', 'pega2', 'chiburi1_a', 'chiburi1', 'guardado'])
            dupla = _com(P['dupla'], olhos='s')
            kk.mostrar(K.esticado(dupla))

            def _pousou():
                _som('pouso')
                bx, by = kk.ancora()
                poeira(bx, by - kk.extensao()[1], n=8)
                kk.empurrar(lift=-8, capa=-6)
                kk.tocar(K.sequencia([(2, _com(dupla, dy=dupla['dy'] - 2, estica=-1), 'segura'),
                                      (4, dupla, 'out'), (1, dupla)]),
                         on_fim=lambda: ag.depois(0.15, _guarda_azul))
            _mover(kk, (ax, ay), alvo, 0.26, ease='in', fantasmas=0, limite=(area, m), on_fim=_pousou)

        def _guarda_azul():
            # guarda a espada azul nas costas: gira a lamina para cima por
            # cima do ombro e ela desce na bainha (o saque ao contrario)
            saca = _com(P['saca2'], olhos='s')
            pega = _com(P['pega2'], olhos='s')
            seq = K.sequencia(_de_agora(kk, 3, 'out', proxima=saca) +
                              [(4, saca, 'out'), (3, saca, 'segura'), (4, pega, 'in'),
                               (2, pega, 'segura'), (1, pega)])

            def _q(q):
                if q == 3:
                    _som('giro')
                elif q == 14:
                    _som('embainhar')
                    bx, by = kk.ponto_mao(2)
                    faiscas.estourar(bx, by, AZUL, n=6, forca=dp(50), tam=max(2, ps * 0.7), gravidade=0)
                    kk.empurrar(capa=4, cabelo=3)
            kk.tocar(seq, on_quadro=_q, on_fim=_chiburi)

        def _chiburi():
            # chiburi com a katana (ergue e sacode a lamina num estalo) e noto:
            # embainha devagar na cintura ate o clique
            seq = K.sequencia(_de_agora(kk, 3, 'out', proxima=P['chiburi1_a']) +
                              [(4, _com(P['chiburi1_a'], olhos='s'), 'in'), (2, _com(P['chiburi1'], olhos='s'), 'segura'),
                               (6, _com(P['chiburi1'], olhos='s'), 'suave'), (8, P['embainha1_a'], 'in'),
                               (4, P['embainha1_b'], 'suave'), (3, P['embainha1_c'], 'mola'),
                               (1, P['guardado'])])

            def _q(q):
                if q == 7:
                    _som('pulo')
                    kk.empurrar(capa=-6, cabelo=-4)
                elif q == 15:
                    _som('desliza')
                    _prepara_explosao(1)
                elif q == 20:
                    _prepara_explosao(-1)
                elif q == 29:
                    _som('embainhar')
                    bx, by = kk.ponto_mao(1)
                    faiscas.estourar(bx, by, BRANCO, n=6, forca=dp(50), tam=max(2, ps * 0.7),
                                     gravidade=0)
                    ag.depois(0.14, _explode)
            kk.tocar(seq, on_quadro=_q, on_fim=lambda: kk.idle(base=P['guardado']))

        # ── 7. so depois de embainhar: a frase explode ──────────────
        def _meialua_explosao(sent):
            cx, cy = titulo.x_do_trecho(0, len(texto))
            return dict(centro=(cx, cy), raio=titulo.tw * 0.62, ang_ini=160 if sent > 0 else 20,
                        ang_fim=-45 if sent > 0 else 225, espessura=th * 1.2,
                        achat=0.34, rotacao=12 * sent)

        def _prepara_explosao(sent):
            try:
                preparar_meialua(**_meialua_explosao(sent))
            except Exception as e:
                print(f"[cena] preparar explosao: {e}")

        def _explode():
            cx, cy = titulo.x_do_trecho(0, len(texto))
            for sent, cor in ((1, CIANO), (-1, AZUL)):
                camada.add_widget(CorteMeiaLua(cor=cor, dur_cheio=5 / 30.0, dur_decai=9 / 30.0, por_s=15,
                                               **_meialua_explosao(sent)))
            faiscas.estourar(cx, cy, CIANO, n=45, forca=dp(340), tam=ps)
            faiscas.estourar(cx, cy, AZUL, n=25, forca=dp(260), tam=ps)
            _som('titulo')
            _tremer(26)
            _brilho_tela(camada, 0.3, 0.3)
            titulo.clarao_final()
            # pose final: espadas guardadas, firme em cima da frase, a mao
            # perto do cabo; o sobretudo assenta com o vento da explosao
            fim_p = _com(P['guardado'], olhos='a')
            kk.tocar(K.sequencia(_de_agora(kk, 3, 'out') + [(10, _com(fim_p, olhos='s'), 'segura'),
                                                            (1, fim_p)]),
                     on_fim=lambda: kk.idle(base=fim_p))
            kk.empurrar(capa=-10, cabelo=-8, lift=4)
            aura.alvo = 0.0
            ag.depois(0.25, lambda: balao(camada, 'Bem-vindo!', kk, dur=1.0))
            ag.depois(1.25, encerrar)

        # rede de seguranca: a cena nunca prende o app
        def _seguranca():
            titulo.completo()
            restaurar_fundo()
            encerrar()
        ag.depois(64.0, _seguranca)
    except Exception as e:
        print(f"[cena] falhou, seguindo sem ela: {e}")
        restaurar_fundo()
        encerrar()
    return camada


def cena_entrada_rapida(tela, label, on_fim=None, texto="TRAVETE FOCUS"):
    """Entrada rapida (a senha ainda esta valendo), em cena de anime: as
    faixas de cinema fecham, o Yoru despenca do alto num risco de luz, a
    camera aproxima... um instante parado com a mao no cabo (brilho no fio)
    e ele atravessa a frase num iai - quadro de impacto, a luz da katana
    grava TRAVETE FOCUS de ponta a ponta -, freia do outro lado, salta para
    cima da frase, embainha e um balao diz 'Bem-vindo!'. Uns 4 s."""
    fim = _Uma(on_fim)
    camada = Widget(size_hint=(None, None), size=tela.size, pos=(0, 0))
    ag = _Agenda()
    camada._agenda = ag

    def encerrar():
        ag.parar()
        rest = getattr(camada, '_restaurar', None)
        if rest is not None:
            rest()
        fim()

    try:
        tela.add_widget(camada)
        W, H = tela.size
        area = (0.0, 0.0, float(W), float(H))
        wx, wy = label.to_window(label.x, label.y)
        lx, ly = tela.to_widget(wx, wy)
        titulo = TituloLuz(texto, label.font_size, pos=(lx, ly), size=label.size)
        camada.add_widget(titulo)
        camada._titulo = titulo
        faiscas = K.Faiscas(n_max=100)
        ps = _ps_titulo(titulo.th, W, H)
        kk = K.KiritoPixel(ps=ps)
        ps = kk.ps
        _PX[0] = ps / float(K.R)
        te = ps / float(K.R)
        kk.opacity = 0
        kk.espelhar = False
        camada.add_widget(K.RastroLamina(kk, faiscas))
        camada.add_widget(kk)
        camada.add_widget(faiscas)
        cine = _FaixasCinema(W, H)
        camada.add_widget(cine)
        cam = _Camera(tela)
        camada._restaurar = cam.soltar
        _precarregar_sons(['pulo', 'sacar_iai', 'corte', 'embainhar', 'pouso', 'titulo', 'fala_tou', 'koiguchi',
                           'golpe_final'])
        P = K.POSE_A
        th = titulo.th
        ox_t, oy_t = titulo._origem()
        cy = oy_t + th * 0.5
        m = max(dp(4), ps)
        pronto = _com(P['saca0'], olhos='s')
        corta = _com(P['corta1'], olhos='g')
        segue = _com(P['segue1'], olhos='s')
        fim_p = _com(P['guardado'], olhos='v')
        kk.precarregar([pronto, corta, segue, fim_p, P['chiburi1'], P['embainha1_a'],
                        P['embainha1_b'], P['embainha1_c']])

        # o corpo passa na altura da frase (a mao da katana rente as letras)
        _, hy = kk._local_texel(*K.maos_texel(corta, 1)[0])
        _, ay_l = kk.ancora_local()
        y_corte = cy - (hy - ay_l)
        A0 = _no_quadro(kk, ox_t - th * 0.9, y_corte, [pronto, corta], area, m)
        A1 = _no_quadro(kk, ox_t + titulo.tw + kk.extensao(segue)[0] + th * 0.15, y_corte,
                        [segue, fim_p], area, m)
        # a luz do corte: rente a frase, de ponta a ponta (a cabeca da luz vai
        # junto com ele)
        te_c = te * max(1, int(round(2.4 / te)))
        oficina = OficinaCortes(te_c)
        arco = ArcoCorte.pelo_meio((ox_t + titulo.tw / 2.0, cy), 0, titulo.tw + th * 0.9, -0.05, th * 1.15)
        oficina.pedir('frase', arco, 'katana')

        def _mergulha():
            p_pulo = _com(P['pulo'], olhos='s')
            ini = (-kk.extensao(p_pulo)[2] - dp(10), H + ps * 10)
            kk.ancorar(*ini)
            kk.opacity = 1
            n = max(6, int(0.42 * K.FPS))
            bola = K.bola(p_pulo)
            kk.tocar(K.sequencia([(max(2, n // 4), K.esticado(p_pulo), 'out'),
                                  (n - n // 4 - 2, bola, 'segura'), (2, bola, 'out'),
                                  (1, _com(pronto, estica=1))]))
            _som('pulo')
            kk.empurrar(capa=-10, cabelo=-8, lift=10)
            cine.entrar()
            _linhas_velocidade(camada, 0.42, CIANO, vertical=True, x0=0, x1=A0[0] + 60 * te, n=12)
            _mover(kk, ini, A0, 0.42, rot=(0, -720), fantasmas=4, ease='in', on_fim=_pousa0,
                   rot_janela=(0.12, 0.85))
        ag.depois(0.05, _mergulha)

        def _pousa0():
            # pousa agachado, a mao no cabo: a camera aproxima, um brilho corre no fio... silencio
            kk.rotacao = 0
            ax, ay = kk.ancora()
            _som('pouso')
            _tremer(6)
            faiscas.estourar(ax, ay - kk.extensao()[1], POEIRA, n=10, forca=dp(110), tam=max(2, ps * 0.8),
                             gravidade=dp(300))
            _anel(camada, (ax, ay - kk.extensao()[1] + te * 2), te * 4, te * 60, 0.3, CIANO, esp=dp(2), achat=0.3)
            kk.tocar(K.sequencia([(2, _com(pronto, estica=-1), 'segura'), (4, pronto, 'out'), (1, pronto)]))
            kk.empurrar(lift=-10, capa=-8)
            cam.ir(1.22, foco=(ax + th * 0.6, ay + th * 0.4), dur=0.3)

            def _brilho():
                hx, hy = kk.ponto_mao(1)
                _estrela(camada, hx, hy, ps * 1.2, BRANCO, raios=4, dur=0.16)
                _som('koiguchi')
            ag.depois(0.26, _brilho)
            ag.depois(0.5, _corta)

        def _corta():
            # o iai: desliza de ponta a ponta da frase
            kk.rotacao = 0
            cam.ir(1.0, dur=0.12)
            _quadro_impacto(camada, kk, (ox_t + titulo.tw / 2.0, cy))
            _linhas_velocidade(camada, 0.3, BRANCO, y0=cy - th * 2.2, y1=cy + th * 2.2, n=16, sentido=1)
            _tremer(14)
            chaves = [(1, pronto, 'segura'), (1, K.misturar(pronto, corta, 0.5, 0.5), 'segura'),
                      (5, corta, 'out'), (4, segue, 'mola'), (1, segue)]
            kk.tocar(K.sequencia(chaves))
            _som('sacar_iai')
            _som('fala_tou')
            kk.empurrar(capa=16, cabelo=12)
            mancha = oficina.obter('frase')
            grava = titulo.gravar_arco(0, len(texto), arco, th * 0.95)
            acesas = set()
            dur = 0.2

            def _passo(s):
                grava(s)
                hx = arco.ponto(min(s, 1.0))[0]
                for li in range(len(texto)):
                    if li not in acesas and texto[li].strip() and \
                            ox_t + (titulo._larg[li] + titulo._larg[li + 1]) / 2.0 <= hx:
                        acesas.add(li)
                        titulo.gravar(li, li + 1)
                        if li % 3 == 0:
                            faiscas.estourar(hx, cy, CIANO, n=2, forca=dp(120), tam=max(2, te * 2),
                                             gravidade=dp(200))
            if mancha is not None:
                camada.add_widget(CorteGravado(arco, mancha, dur=dur, decai=0.3, k=kk, on_passo=_passo),
                                  index=len(camada.children) - 1)
            else:
                _passo(1.0)
            _mover(kk, kk.ancora(), A1, dur, ease='out', fantasmas=4, limite=(area, m), on_fim=_freia)

        # no fim ele sobe e pousa EM CIMA da frase (sem tapar as letras)
        pe = kk.extensao(P['guardado'])[1] - ps
        y_topo = oy_t + th * 0.82 + pe
        B = _no_quadro(kk, ox_t + titulo.tw - th * 0.75, y_topo, [fim_p, P['chiburi1']], area, m)

        def _freia():
            # freia do outro lado (o sobretudo passa do ponto) e ja salta
            _som('corte')
            _som('golpe_final')
            _tremer(12)
            kk.impacto()
            kk.pausar(0.05)
            kk.empurrar(capa=-18, cabelo=-14)
            cine.sair()
            for sent, cor_ in ((1, CIANO), (-1, AZUL)):          # a frase estala: duas meias-luas cruzadas
                camada.add_widget(CorteMeiaLua(centro=(ox_t + titulo.tw / 2.0, cy), raio=titulo.tw * 0.6,
                                               ang_ini=160 if sent > 0 else 20, ang_fim=-45 if sent > 0 else 225,
                                               espessura=th * 1.1, achat=0.34, rotacao=12 * sent, cor=cor_,
                                               dur_cheio=4 / 30.0, dur_decai=7 / 30.0, por_s=15))
            faiscas.estourar(ox_t + titulo.tw / 2.0, cy, CIANO, n=30, forca=dp(300), tam=ps)
            p_pulo = _com(P['pulo'], olhos='s')
            ax, ay = kk.ancora()
            kk.tocar(K.sequencia([(3, K.esticado(p_pulo), 'out'), (4, K.encolhido(p_pulo), 'suave'),
                                  (1, K.esticado(fim_p))]))
            h = _arco(ay, B[1], th * 0.9, area[3] - m - _ext(kk, [K.encolhido(p_pulo)])[3])
            ag.depois(0.06, lambda: _mover(kk, kk.ancora(), B, 0.26, altura=h, fantasmas=2,
                                           limite=(area, m), on_fim=_pousa))

        def _pousa():
            _som('pouso')
            ax, ay = kk.ancora()
            faiscas.estourar(ax, ay - kk.extensao()[1], POEIRA, n=8, forca=dp(90), tam=max(2, ps * 0.8),
                             gravidade=dp(300))
            kk.empurrar(lift=-8, capa=-6)
            kk.mostrar(_com(K.POSE_A['agacha'], olhos='s', estica=-1))      # amortece
            ag.depois(0.08, _embainha)

        def _embainha():
            seq = K.sequencia(_de_agora(kk, 2, 'out', proxima=P['chiburi1']) +
                              [(3, _com(P['chiburi1'], olhos='s'), 'out'), (2, _com(P['chiburi1'], olhos='s'), 'segura'),
                               (4, P['embainha1_a'], 'in'), (2, P['embainha1_b'], 'suave'),
                               (2, P['embainha1_c'], 'mola'), (1, fim_p)])

            def _q(q):
                if q == 13:
                    _som('embainhar')
                    titulo.clarao_final()
                    balao(camada, 'Bem-vindo!', kk, dur=1.5)
            kk.tocar(seq, on_quadro=_q, on_fim=lambda: kk.idle(base=fim_p))
            ag.depois(1.9, encerrar)

        def _seguranca():
            titulo.completo()
            encerrar()
        ag.depois(9.5, _seguranca)
    except Exception as e:
        print(f"[cena] entrada rapida falhou, seguindo sem ela: {e}")
        encerrar()
    return camada


def limpar_cena(camada):
    try:
        K.definir_ambiente('')
        ag = getattr(camada, '_agenda', None)
        if ag is not None:
            ag.parar()
        rest = getattr(camada, '_restaurar', None)
        if rest is not None:
            rest()
        for w in list(camada.children):
            if isinstance(w, K.KiritoPixel):
                w.parar()
            elif isinstance(w, (_AuraEspada, _OndaGetsuga)):
                w.parar()
        if camada.parent:
            camada.parent.remove_widget(camada)
    except Exception as e:
        print(f"[cena] limpar: {e}")


# ═══════════════════════════════════════════════════════════════════
#  KIRITO NA TELA DO PIN (espiando por cima da caixa)
# ═══════════════════════════════════════════════════════════════════
class KiritoPin:
    """Espia por cima da caixa do PIN, perto de um dos cantos: so a cabeca e
    as duas maos apoiadas na borda aparecem (o corpo fica atras da caixa,
    recortado por um StencilView na linha da borda). Olha o codigo sendo
    digitado, da um pulinho a cada tecla, leva um susto no erro (!) e volta
    desconfiado; no bloqueio balanca a cabeca e afunda; no acerto sobe na
    caixa, sorri e some num teleporte."""

    def __init__(self, caixa=None):
        self.caixa = caixa
        self.k = None
        self.clip = None
        self.faiscas = None
        self.lado = 1
        self._desc = 0.0            # px abaixo da posicao de espiar (esconder)
        self._em_cima = False       # pulando/em pe em cima da caixa (acesso liberado)
        self._pe = None             # distancia ancora -> pes, quando em pe na caixa
        self._escondido = False     # abaixado depois de um PIN errado
        self._bloq = False          # 3 erros: reacao final (nada mais interrompe)
        self._ocupado = False
        self._ev_desc = None
        self._evs = []

    # ── geometria ────────────────────────────────────────────────────
    def _borda(self):
        """(x0, topo, x1) da caixa em coords da janela."""
        c = self.caixa
        x0, y0 = c.to_window(c.x, c.y)
        return x0, y0 + c.height, x0 + c.width

    def _linha_local(self):
        """Altura (local do sprite) da borda: 2 linhas acima do topo do
        tronco da pose sem dy (as poses 'espia*' foram feitas para ela)."""
        topo = K._PES + K._PERNAS_P['repouso']['H'] + len(K._TRONCO) - 1
        return (topo + 2) * self.k.ps

    def _seguir(self, dt=0):
        """Acompanha a caixa (ela sobe com o teclado, anima ao abrir...)."""
        try:
            if self.k is None:
                return False
            W, H = Window.size
            x0, topo, x1 = self._borda()
            self.clip.pos = (0, topo)
            self.clip.size = (W, max(0, H - topo))
            ax_l, _ = self.k.ancora_local()
            recuo = max((x1 - x0) * 0.17, dp(42))
            cx = x0 + recuo if self.lado < 0 else x1 - recuo
            if self._em_cima:
                if self._pe is not None:        # em pe na caixa: acompanha a borda
                    ax, _ = self.k.ancora()
                    self.k.ancorar(ax, topo + self._pe)
                return True
            y = topo - self._linha_local() - self._desc
            # tela baixa (teclado aberto empurrou a caixa para cima): em vez de
            # a cabeca passar do topo da janela, ele se abaixa mais atras da caixa
            y1 = K.caixa(self.k._pose)[3]
            teto = y + (y1 + 1) * self.k.ps
            if teto > H:
                y -= teto - H
            self.k.pos = (cx - ax_l, y)
            return True
        except Exception as e:
            print(f"[kirito pin] seguir: {e}")
            return False

    def _depois(self, t, fn):
        def _x(dt):
            if self.k is None:
                return
            try:
                fn()
            except Exception as e:
                print(f"[kirito pin] passo: {e}")
        self._evs.append(Clock.schedule_once(_x, t))

    def _animar_desc(self, alvo, dur, on_fim=None, volta=0.0):
        """Anima o quanto ele esta abaixado atras da borda (volta = passa do
        ponto e volta, em px)."""
        if self._ev_desc is not None:
            self._ev_desc.cancel()
        de = self._desc
        t = [0.0]

        def _p(dt):
            try:
                if self.k is None or self._em_cima:
                    return False
                t[0] += dt
                u = min(1.0, t[0] / dur)
                e = 1 - (1 - u) ** 3
                extra = volta * math.sin(math.pi * u) if volta else 0.0
                self._desc = de + (alvo - de) * e - extra
                self._seguir()
                if u >= 1:
                    self._desc = alvo
                    self._seguir()
                    if on_fim:
                        on_fim()
                    return False
            except Exception as e:
                print(f"[kirito pin] desc: {e}")
                return False
        self._ev_desc = Clock.schedule_interval(_p, 1 / 60.)
        self._evs.append(self._ev_desc)

    # ── entrada ──────────────────────────────────────────────────────
    def aparecer(self):
        try:
            if self.k is not None or self.caixa is None:
                return
            W, H = Window.size
            x0, topo, x1 = self._borda()
            ps = _ps_para(x1 - x0, H, extra=1.08)
            espaco = H - topo
            ps = min(ps, int(espaco / 15.0))         # cabeca inteira acima da caixa
            if ps < K.R:
                return                               # sem espaco (tela muito baixa)
            self.lado = random.choice((-1, 1))       # -1 canto esquerdo, 1 direito
            self.clip = StencilView(size_hint=(None, None), size=(W, 0), pos=(0, topo))
            k = K.KiritoPixel(ps=ps)
            _PX[0] = k.ps / float(K.R)
            self.k = k
            k.ao_redesenhar = self._seguir          # pose mudou: reajusta na hora (sem atraso)
            k.espelhar = self.lado > 0              # olha para o centro da caixa
            k.precarregar([K.POSE_A[n] for n in ('espia', 'espia_olha', 'espia_alto', 'espia_baixo',
                                                   'pulo', 'agacha', 'guardado')])
            _precarregar_sons(_SONS_PIN)
            k.mostrar(K.POSE_A['espia_baixo'])
            self.clip.add_widget(k)
            Window.add_widget(self.clip)
            self.faiscas = K.Faiscas(n_max=40)
            Window.add_widget(self.faiscas)
            self._desc = 3 * ps                      # maos ainda abaixo da borda
            self._seguir()
            self._evs.append(Clock.schedule_interval(self._seguir, 1 / 30.))
            self._ocupado = True
            # 1) as maos agarram a borda  2) a cabeca sobe devagar e espia
            self._animar_desc(0.0, 0.12, on_fim=self._agarrou)
        except Exception as e:
            print(f"[kirito pin] aparecer: {e}")
            self.remover()

    def _agarrou(self):
        _som('agarra')
        for qual in (1, 2):
            try:
                mx, my = self.k.ponto_mao(qual)
                self.faiscas.estourar(mx, my + self.k.ps, CIANO, n=3, forca=dp(30),
                                      tam=max(2, self.k.ps * 0.6), gravidade=0)
            except Exception:
                pass
        # a cabeca sobe devagar e passa um tiquinho do ponto (curiosidade)
        self._depois(0.3, lambda: self.k.tocar(
            K.sequencia([(12, K.POSE_A['espia_baixo'], 'mola'), (1, K.POSE_A['espia_olha'])]),
            on_fim=self._esperar))

    def _esperar(self):
        """Parado espiando: olha o campo do PIN, as vezes levanta os olhos,
        pisca e respira (a cabeca sobe 1 px)."""
        if self.k is None:
            return
        self._ocupado = False
        base = K.POSE_A['espia']
        olha = K.POSE_A['espia_olha']
        quadros = []
        for f in range(100):
            q = dict(olha if 44 <= f < 66 else base)
            if 18 <= f < 24 or 76 <= f < 82:        # respira
                q['dy'] = q['dy'] + 1
                q['m1'] = (q['m1'][0], q['m1'][1] - 1)
                q['m2'] = (q['m2'][0], q['m2'][1] - 1)
            if f in (60, 61):
                q['olhos'] = 'f'
            quadros.append(q)
        self.k.tocar(quadros, loop=True)

    # ── reacoes ──────────────────────────────────────────────────────
    def reagir_tecla(self):
        """Pulinho de atencao a cada tecla."""
        try:
            if self.k is None or self._ocupado:
                return
            # pulinho: sobe rapido e desce com uma molinha
            seq = K.sequencia([(2, K.POSE_A['espia'], 'out'), (5, K.POSE_A['espia_alto'], 'mola'),
                               (1, K.POSE_A['espia'])])
            self.k.tocar(seq, on_fim=self._esperar)
        except Exception as e:
            print(f"[kirito pin] tecla: {e}")

    def susto(self):
        """PIN errado: leva um susto (!), se abaixa atras da caixa e depois
        volta a espiar devagar, desconfiado e suando."""
        try:
            if self.k is None or self._em_cima or self._escondido:
                return
            self._ocupado = True
            self._escondido = True
            _som('susto')
            ps = self.k.ps
            P = K.POSE_A
            self.k.empurrar(cabelo=18, lift=8)
            # encolhe um instante e salta de susto (!)
            self.k.tocar(K.sequencia([(1, _com(P['espia'], olhos='u', dy=0, m1=(3, 4), m2=(-3, 4)), 'out'),
                                      (4, _com(P['espia_alto'], olhos='u'), 'segura'),
                                      (1, _com(P['espia_alto'], olhos='u')),
                                      (1, _com(P['espia_baixo'], olhos='u'))]))
            emote(self.clip, self.k, '!!', 0.45)

            def _de_volta():
                if self._bloq:
                    return
                self._escondido = False
                seq = K.sequencia([(14, _com(P['espia_baixo'], olhos='s'), 'in'),
                                   (22, _com(P['espia_olha'], olhos='s')),
                                   (1, _com(P['espia_olha'], olhos='s'))])
                self.k.tocar(seq, on_fim=self._esperar)
                emote(self.clip, self.k, 'gota', 1.3, atraso=0.45)

            def _volta():
                if self._bloq:
                    return
                self.k.mostrar(_com(P['espia_baixo'], olhos='s'))
                self._animar_desc(0.0, 0.45, on_fim=_de_volta)
            self._depois(0.2, lambda: self._animar_desc(
                13 * ps, 0.12, on_fim=lambda: self._depois(0.7, _volta)))
        except Exception as e:
            print(f"[kirito pin] susto: {e}")

    def bloqueado(self):
        """3 erros: fecha os olhos, balanca a cabeca (nao, nao...) com uma
        gota de suor e afunda devagar atras da caixa."""
        try:
            if self.k is None or self._em_cima or self._bloq:
                return
            self._bloq = True
            self._ocupado = True
            self._escondido = True
            P = K.POSE_A
            base = _com(P['espia_olha'], olhos='f')
            emote(self.clip, self.k, 'gota', 1.5)
            quadros = []
            for dx in (0, -1, -1, 1, 1, -1, -1, 1, 1, 0, 0, 0):
                q = dict(base)
                q['dx'] = dx
                q['m1'] = (base['m1'][0] - dx, base['m1'][1])     # maos paradas na borda
                q['m2'] = (base['m2'][0] - dx, base['m2'][1])
                quadros.extend([q, q])
            ps = self.k.ps

            def _afunda():
                self.k.mostrar(_com(P['espia_baixo'], olhos='f'))
                self._animar_desc(13 * ps, 0.9)
            # se estava escondido (susto do erro), volta para a borda antes
            self.k.mostrar(base)
            self._animar_desc(0.0, 0.15, on_fim=lambda: self.k.tocar(quadros, on_fim=_afunda))
        except Exception as e:
            print(f"[kirito pin] bloqueado: {e}")

    def voltar(self):
        """O bloqueio acabou: sobe de novo devagar e volta a espiar."""
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
        """Acesso liberado: sobe na caixa, sorri, faz que sim e some num
        teleporte (ele volta pendurado na cena do titulo)."""
        try:
            if self.k is None:
                return
            k = self.k
            self._ocupado = True
            P = K.POSE_A
            W, H = Window.size
            x0, topo, x1 = self._borda()
            ps = k.ps
            if H - topo < 30 * ps:
                # sem espaco para ficar em pe na caixa: some dali mesmo
                k.tocar(K.sequencia([(3, _com(P['espia_alto'], olhos='e')),
                                     (4, _com(P['espia'], olhos='e')),
                                     (1, _com(P['espia_alto'], olhos='e'))]))
                emote(self.clip, k, 'brilho', 0.5)
                self._depois(0.35, lambda: _teleporte(k, self.clip, self.faiscas, on_fim=self.remover))
                return
            # prepara o pulo: a cabeca afunda um pouco (impulso) e sobe
            k.tocar(K.sequencia([(2, P['espia'], 'out'),
                                 (3, _com(P['espia'], dy=-1, m1=(3, 5), m2=(-3, 5)), 'segura'),
                                 (1, P['espia_alto'])]))

            def _pula():
                ax, ay = k.ancora()
                self._em_cima = True
                pulo = P['pulo']
                k.mostrar(K.esticado(pulo))
                _som('pulo')
                k.empurrar(capa=-8, lift=10)
                base = k.extensao(P['guardado'])[1]
                _, topo2, _ = self._borda()
                alvo = (ax - self.lado * dp(18), topo2 + base)
                _mover(k, (ax, ay), alvo, 0.32, altura=4 * ps, fantasmas=False,
                       on_fim=lambda: _pousa(base),
                       on_passo=_voo(k, K.esticado(pulo), pulo, K.esticado(pulo), (0.25, 0.7)))

            def _pousa(base):
                self._pe = base
                _som('pouso')
                ax, ay = k.ancora()
                self.faiscas.estourar(ax, ay - base, POEIRA, n=8, forca=dp(60),
                                      tam=max(2, ps * 0.7), gravidade=dp(250))
                feliz = _com(P['guardado'], olhos='e')
                emote(self.clip, k, 'brilho', 0.9, atraso=0.15)
                emote(self.clip, k, 'rubor', 1.0, atraso=0.15)
                emote(self.clip, k, 'nota', 0.8, atraso=0.4)
                # amortece o pouso, levanta com uma molinha e faz que sim
                k.tocar(K.sequencia([(2, P['agacha'], 'segura'), (4, P['agacha'], 'out'),
                                     (4, feliz, 'suave'), (3, _com(feliz, dy=-1), 'mola'),
                                     (4, feliz, 'segura'), (1, feliz)]),
                        on_fim=lambda: _teleporte(k, self.clip, self.faiscas, on_fim=self.remover))
            self._depois(0.2, _pula)
        except Exception as e:
            print(f"[kirito pin] sumir: {e}")
            self.remover()

    def remover(self, *_):
        for ev in self._evs:
            try:
                ev.cancel()
            except Exception:
                pass
        self._evs = []
        k, self.k = self.k, None
        if k is not None:
            try:
                k.parar()
            except Exception:
                pass
        for w in (self.clip, self.faiscas):
            _remover_da_janela(w)
        self.clip = self.faiscas = None


# ═══════════════════════════════════════════════════════════════════
#  MINI KIRITO FATIANDO O QUE SERA APAGADO
# ═══════════════════════════════════════════════════════════════════
def _limites():
    """(x0, y0, x1, y1) da area do app na janela: no PC em janela larga o app
    fica numa coluna central, e o Kirito deve usar as bordas dela."""
    W, H = Window.size
    try:
        from kivy.app import App
        sm = App.get_running_app().root.ids.sm
        x0, y0 = sm.to_window(sm.x, sm.y)
        return x0, y0, x0 + sm.width, y0 + sm.height
    except Exception:
        return 0.0, 0.0, float(W), float(H)


def _ret_janela(w):
    """(x, y, larg, alt) do widget em coordenadas da janela."""
    x, y = w.to_window(w.x, w.y)
    return x, y, w.width, w.height


def _remover_da_janela(w):
    try:
        if w is not None and w.parent is not None:
            Window.remove_widget(w)
    except Exception:
        pass


class _PixelsLuz(Widget):
    """Riscos e rachaduras de luz em pixels (do tamanho dos do Yoru), que
    crescem do comeco ate a ponta e depois somem. caminhos = listas de
    pontos (x, y) na tela, um ponto por pixel."""
    CORES = (('halo', (0.35, 0.80, 1.0, 0.55)), ('meio', (0.70, 0.95, 1.0, 0.95)),
             ('luz', (1.0, 1.0, 1.0, 1.0)))

    def __init__(self, caminhos, te, cresce=0.2, fica=0.3, some=0.25, grossura=1, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.caminhos = caminhos
        self.te = te
        self.cresce, self.fica, self.some = cresce, fica, some
        self.g = grossura
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, self.CORES)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            self.t += dt
            p = min(1.0, self.t / max(0.01, self.cresce))
            alfa = 1.0 - max(0.0, (self.t - self.cresce - self.fica) / max(0.01, self.some))
            if alfa <= 0 or self.parent is None:
                return self.parar()
            te, g = self.te, self.g
            pts = {}
            for c in self.caminhos:
                for (x, y) in c[:max(1, int(len(c) * p))]:
                    pts.setdefault('halo', []).append((x - te, y - te, te * (g + 2), te * (g + 2)))
                    pts.setdefault('meio', []).append((x, y, te * g, te * g))
                    if g > 1:
                        pts.setdefault('luz', []).append((x + te * 0.5 * (g - 1), y + te * 0.5 * (g - 1), te, te))
            self._lote.desenhar(pts, alfa)
        except Exception as e:
            print(f"[luz] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)
        return False


def _reta_pixels(x0, y0, x1, y1, te):
    """Pontos de uma reta na grade de pixels (um por pixel)."""
    n = int(max(abs(x1 - x0), abs(y1 - y0)) / te) + 1
    out = []
    for i in range(n + 1):
        u = i / float(n)
        out.append((math.floor((x0 + (x1 - x0) * u) / te) * te, math.floor((y0 + (y1 - y0) * u) / te) * te))
    return out


def _rachaduras(cx, cy, rx, ry, rw, rh, te, n=9, semente=5):
    """Rachaduras de vidro saindo de (cx, cy): riscos retos em estrela, com
    uma quina de vez em quando e um ou outro galho, ate a borda do
    retangulo (vidro trincado - nada de linha enrolada)."""
    rnd = random.Random(semente)
    fila = [(cx, cy, 2 * math.pi * i / n + rnd.uniform(-0.25, 0.25)) for i in range(n)]
    caminhos = []
    while fila and len(caminhos) < n * 2:
        x, y, a0 = fila.pop(0)
        c = []
        a, lado = a0, rnd.choice((-1, 1))
        quina = rnd.randint(14, 30)
        for _ in range(900):
            quina -= 1
            if quina <= 0:                              # quina: zigue-zague em volta do rumo
                lado = -lado
                a = a0 + lado * rnd.uniform(0.12, 0.38)
                quina = rnd.randint(16, 40)
            x += math.cos(a) * te
            y += math.sin(a) * te
            if not (rx <= x <= rx + rw and ry <= y <= ry + rh):
                break
            q = (math.floor(x / te) * te, math.floor(y / te) * te)
            if not c or c[-1] != q:
                c.append(q)
            if len(c) in (26, 70) and rnd.random() < 0.5:
                fila.append((x, y, a0 + rnd.choice((-0.6, 0.6))))
        if c:
            caminhos.append(c)
    return caminhos


class _PixelsBrasa(_PixelsLuz):
    """Riscos e rachaduras em BRASA (o chao que racha, os talhos no chefe)."""
    CORES = (('halo', (0.55, 0.06, 0.08, 0.7)), ('meio', (1.0, 0.25, 0.14, 1.0)), ('luz', (1.0, 0.85, 0.6, 1.0)))


class _PixelsRoxo(_PixelsLuz):
    """Os talhos do Bankai."""
    CORES = (('halo', (0.45, 0.2, 0.9, 0.6)), ('meio', (0.8, 0.62, 1.0, 1.0)), ('luz', (1.0, 1.0, 1.0, 1.0)))


def _quadro_impacto(camada, k, centro=None):
    """Quadro de impacto de anime nos golpes grandes: 1 quadro com a tela
    preta e o Yoru em silhueta branca, 1 quadro com a tela branca e ele em
    silhueta preta - com linhas de foco (pixels grossos) vindo das bordas
    para o ponto do golpe. Depois tudo volta ao normal."""
    try:
        W, H = Window.size
        cx, cy = centro or k.ancora()
        fundo = Widget(size_hint=(None, None), size=(0, 0))
        with fundo.canvas:
            c_fundo = Color(0, 0, 0, 1)
            Rectangle(pos=(0, 0), size=(W, H))
        i = camada.children.index(k) + 1 if k in camada.children else len(camada.children)
        camada.add_widget(fundo, index=i)
        rnd = random.Random(int(cx) * 31 + int(cy))
        raios = [(rnd.uniform(0, 2 * math.pi), rnd.uniform(0.14, 0.26), rnd.choice((1, 1, 2)))
                 for _ in range(22)]
        R = math.hypot(W, H)

        antes = tuple(k._cor_clarao.rgb)
        k.clarao_preso = True
        k._cor_clarao.rgb = (1, 1, 1)
        k.clarao = 1.0
        virou = [False]

        def forma(t, p, u):
            # um relogio so: no 2o quadro a tela fica branca e ele preto
            if t >= 1 / 30.0 and not virou[0]:
                virou[0] = True
                c_fundo.rgb = (1, 1, 1)
                k._cor_clarao.rgb = (0, 0, 0.02)
                k._desenhar(forcar=True)
            u = u * 3
            nome = 'escuro' if virou[0] else 'claro'
            for a, ini, g in raios:
                ca, sa = math.cos(a), math.sin(a)
                n = int(R * (0.75 - ini) / u)
                for j in range(n):
                    d = R * 0.75 - j * u
                    gg = g if j < n * 0.6 else 1
                    x = math.floor((cx + ca * d) / u) * u
                    y = math.floor((cy + sa * d) / u) * u
                    p.setdefault(nome, []).append((x, y, u * gg, u * gg))

        def _fim():
            k._cor_clarao.rgb = antes
            k.clarao_preso = False
            k.clarao = 0.0
            if fundo.parent:
                fundo.parent.remove_widget(fundo)
        camada.add_widget(_EfeitoPixel((('escuro', (0.0, 0.0, 0.02, 1.0)), ('claro', (1.0, 1.0, 1.0, 1.0))),
                                       2.2 / 30.0, forma, on_fim=_fim))
    except Exception as e:
        print(f"[cena] impacto: {e}")


class _CloseRosto(Widget):
    """Close de anime: uma faixa atravessa a tela com o olho do Yoru em pixel
    grande. A faixa abre, o retrato entra deslizando com linhas de
    velocidade, o olho abre e o brilho pisca; no fim a faixa fecha.
    tipo: 'normal', 'poder' (olho aceso ciano) ou 'mugetsu' (os olhos
    acendem roxos no meio do close). espelhar: ele olhando para a
    esquerda (o retrato vira e entra pelo outro lado)."""

    PW, PH = 104, 40

    def __init__(self, tipo='normal', dur=0.8, on_fim=None, y_rel=0.56, som=True, espelhar=False,
                 **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self.size = (0, 0)
        self.tipo, self.dur, self.on_fim = tipo, dur, on_fim
        self.esp = espelhar
        W, H = Window.size
        self.W, self.H = W, H
        hb = min(W * self.PH / float(self.PW), H * 0.26)
        self.z = hb / float(self.PH)
        self.hb, self.wr = hb, self.PW * self.z
        self.cy = H * y_rel
        R = K._YM.RETRATOS
        self.tex = {n: K.textura_mapa(m) for n, m in R.items()}
        roxo = tipo == 'mugetsu'
        cor = (0.66, 0.36, 1.0) if roxo else (0.33, 0.85, 1.0)
        rnd = random.Random(7)
        self.linhas = [(rnd.uniform(0.05, 0.95), rnd.uniform(0.15, 0.6), rnd.uniform(1.4, 3.2), rnd.random())
                       for _ in range(18)]
        with self.canvas:
            self.c_fundo = Color(0.015, 0.015, 0.04, 0.95)
            self.r_fundo = Rectangle(pos=(0, self.cy), size=(W, 0))
            self.c_lin = Color(cor[0], cor[1], cor[2], 0.30)
            self.m_lin = Mesh(mode='triangles')
            Color(1, 1, 1, 1)
            self.r_ret = Rectangle(pos=(0, self.cy), size=(0, 0))
            self.c_borda = Color(cor[0], cor[1], cor[2], 1.0)
            self.b_cima = Rectangle(pos=(0, 0), size=(0, 0))
            self.b_baixo = Rectangle(pos=(0, 0), size=(0, 0))
            self.c_flash = Color(1, 1, 1, 0)
            self.r_flash = Rectangle(pos=(0, self.cy), size=(W, 0))
            self.c_brilho = Color(1, 1, 1, 0)
            self.m_brilho = Mesh(mode='triangles')
        self.t = 0.0
        self._som = som
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)
        self._tick(0)

    def _nome(self, t):
        if self.tipo == 'mugetsu':
            if t < 0.16:
                return 'normal_meio'
            if t < 0.36:
                return 'normal'
            return 'mugetsu_meio' if t < 0.42 else 'mugetsu'
        if t < 0.16:
            return 'normal_meio'
        return 'poder' if self.tipo == 'poder' else 'normal'

    def _tick(self, dt):
        try:
            self.t += dt
            t, dur = self.t, self.dur
            W = self.W
            abre = min(1.0, t / 0.08)
            fecha = max(0.0, min(1.0, (dur - t) / 0.09))
            k = (1 - (1 - min(abre, fecha)) ** 3)
            hb = self.hb * k
            y0 = self.cy - hb / 2.0
            self.r_fundo.pos, self.r_fundo.size = (0, y0), (W, hb)
            desl = (1 - (1 - min(1.0, t / 0.12)) ** 3)
            x0 = (W - self.wr) / 2.0 + (1 - desl) * W * 0.18 * (-1 if self.esp else 1)
            self.r_ret.texture = self.tex[self._nome(t)]
            if self.esp:
                self.r_ret.tex_coords = K._TC_ESPELHO
            self.r_ret.pos, self.r_ret.size = (x0, y0), (self.wr, hb)
            lb = max(1.0, dp(1.5))
            self.b_cima.pos, self.b_cima.size = (0, y0 + hb), (W, lb * k)
            self.b_baixo.pos, self.b_baixo.size = (0, y0 - lb * k), (W, lb * k)
            # linhas de velocidade correndo para tras dele
            vs, ids = [], []
            for i, (fy, fl, vel, fase) in enumerate(self.linhas):
                x = W * (1.2 - ((fase + t * vel) % 1.4))
                y = y0 + hb * fy
                w, h = W * fl, max(1.0, dp(1.2))
                if self.esp:
                    x = W - x - w
                vs += [x, y, 0, 0, x + w, y, 0, 0, x + w, y + h, 0, 0, x, y + h, 0, 0]
                b = 4 * i
                ids += [b, b + 1, b + 2, b, b + 2, b + 3]
            self.m_lin.vertices, self.m_lin.indices = vs, ids
            # brilho no olho quando ele abre (estrela de 4 pontas em pixel)
            tb = t - (0.42 if self.tipo == 'mugetsu' else 0.18)
            if 0 <= tb < 0.2:
                if tb < dt + 0.001 and self._som:
                    _som('habilidade' if self.tipo != 'normal' else 'koiguchi')
                u = self.z
                cx, cy = x0 + ((self.PW - 76.5) if self.esp else 76.5) * u, y0 + 18.5 * u * k
                s = (1 - abs(tb / 0.1 - 1)) * 4.5
                vs, ids = [], []
                for i, (w, h) in enumerate(((u * (1 + 2 * s), u), (u, u * (1 + 2 * s)))):
                    vs += [cx - w / 2, cy - h / 2, 0, 0, cx + w / 2, cy - h / 2, 0, 0,
                           cx + w / 2, cy + h / 2, 0, 0, cx - w / 2, cy + h / 2, 0, 0]
                    b = 4 * i
                    ids += [b, b + 1, b + 2, b, b + 2, b + 3]
                self.m_brilho.vertices, self.m_brilho.indices = vs, ids
                self.c_brilho.a = 1.0
            else:
                self.c_brilho.a = 0.0
            # no Mugetsu, os olhos acendem com um clarao roxo na faixa
            if self.tipo == 'mugetsu' and 0.36 <= t < 0.5:
                self.c_flash.rgba = (0.8, 0.6, 1.0, 0.55 * (1 - (t - 0.36) / 0.14))
                self.r_flash.pos, self.r_flash.size = (0, y0), (W, hb)
            else:
                self.c_flash.a = 0.0
            if t >= dur:
                self._ev.cancel()
                if self.parent is not None:
                    self.parent.remove_widget(self)
                if self.on_fim:
                    cb, self.on_fim = self.on_fim, None
                    cb()
                return False
        except Exception as e:
            print(f"[cena] close: {e}")
            try:
                self._ev.cancel()
                if self.parent is not None:
                    self.parent.remove_widget(self)
            except Exception:
                pass
            if self.on_fim:
                cb, self.on_fim = self.on_fim, None
                try:
                    cb()
                except Exception:
                    pass
            return False


def close_rosto(camada, tipo='normal', dur=0.8, on_fim=None, y_rel=0.56, espelhar=False):
    """Poe o close de anime por cima de tudo na camada."""
    try:
        camada.add_widget(_CloseRosto(tipo=tipo, dur=dur, on_fim=on_fim, y_rel=y_rel, espelhar=espelhar))
    except Exception as e:
        print(f"[cena] close: {e}")
        if on_fim:
            on_fim()


class _Sombra(Widget):
    """Sombra de pixels no chao embaixo do Yoru (nas cenas curtas): elipse
    escura com o miolo mais forte; quando ele esta no ar ela encolhe e
    clareia."""

    def __init__(self, k, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k = k
        self._lote = K.LotePixels(self.canvas, (('s1', (0.0, 0.0, 0.05, 0.22)), ('s2', (0.0, 0.0, 0.05, 0.4))))
        self._ev = Clock.schedule_interval(self._tick, 1 / 30.)

    def _tick(self, dt):
        try:
            k = self.k
            if self.parent is None or k.parent is None:
                return self.parar()
            if k.opacity < 0.15 or k.rotacao:
                self._lote.desenhar({})
                return
            te = k.ps / float(K.R)
            ax = k.ancora()[0]
            y = k.y + K._PES * k.ps - te
            no_ar = K._PERNAS_P.get(k._base.get('pernas'), {}).get('ar', False)
            rx = 6.0 * k.ps * (0.6 if no_ar else 1.0)
            p = {}
            for dy, frac, nome in ((0, 1.0, 's1'), (0, 0.6, 's2'), (-1, 0.75, 's1'), (1, 0.55, 's1')):
                w = math.floor(rx * frac / te) * te
                if no_ar and nome == 's2':
                    continue
                p.setdefault(nome, []).append((math.floor((ax - w) / te) * te, math.floor(y / te) * te + dy * te,
                                               2 * w, te))
            self._lote.desenhar(p)
        except Exception as e:
            print(f"[sombra] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)
        return False


def _entrar(s, on_fim, tipos=('teleporte', 'queda', 'corrida', 'sombra')):
    """Entrada sorteada nas cenas curtas (o boneco ja esta no lugar e na pose
    da cena): teleporte, queda do alto com poeira, corrida pela lateral
    freando, ou surgindo de uma poca de sombra."""
    k, P = s.k, K.POSE_A
    fim = _Uma(on_fim)
    alvo = k.ancora()
    pose = k._base
    tipo = random.choice(tipos)
    try:
        if tipo == 'teleporte':
            _materializar(k, s.cam, s.faiscas, dur=0.26, on_fim=fim)
        elif tipo == 'queda':
            topo = (alvo[0], s.H + k.extensao()[1] + dp(30))
            k.mostrar(K.esticado(_com(P['pulo'], olhos='s')))
            k.ancorar(*topo)
            _som('pulo')

            def _pousa():
                k.mostrar(_com(P['agacha'], olhos='s'))
                s.poeira()
                _som('pouso')
                k.impacto()
                k.empurrar(capa=-10, cabelo=-8)
                Clock.schedule_once(lambda dt: (k.mostrar(pose), fim()), 0.14)
            _mover(k, topo, alvo, 0.26, ease='in', fantasmas=2, on_fim=_pousa)
        elif tipo == 'corrida':
            esq, _b, dir_, _c = k.extensao()
            if k.espelhar:                        # olha para a esquerda: vem da direita
                ini = (s.area[2] + esq + dp(30), alvo[1])
            else:
                ini = (s.area[0] - dir_ - dp(30), alvo[1])
            k.mostrar(_com(pose, pernas='avanco_baixo', olhos='s'))
            k.ancorar(*ini)
            _som('desliza')

            def _freia():
                k.mostrar(_com(pose, pernas='recua', olhos='s'))
                s.poeira(lado=-1 if k.espelhar else 1)
                k.empurrar(capa=12, cabelo=10)
                Clock.schedule_once(lambda dt: (k.mostrar(pose), fim()), 0.14)
            _mover(k, ini, alvo, 0.17, linear=True, fantasmas=3, on_fim=_freia)
        else:
            # poca de sombra no chao; ele sobe dela em faixas, escuro, e ganha cor
            te = s.te
            ax = alvo[0]
            y = k.y + K._PES * k.ps - te
            rx = 7.0 * k.ps
            _poca_sombra(s.cam, ax, y, rx, te, 0.55)
            k.opacity = 0
            _som('materializa')

            def _sobe(dt):
                for _ in range(6):
                    s.faiscas.estourar(ax + random.uniform(-rx, rx) * 0.6, y, ROXO_SOMBRA, n=1,
                                       forca=dp(25), tam=te * 2, gravidade=-dp(160))
                _faixas(k, s.cam, 0.4, True, on_fim=fim, cor=ROXO_SOMBRA, escuro=True, barra=False)
            Clock.schedule_once(_sobe, 0.12)
    except Exception as e:
        print(f"[entrada] {e}")
        k.opacity = 1
        fim()


ROXO_SOMBRA = (0.55, 0.25, 0.95)


def _poca_sombra(camada, ax, y, rx, te, dur):
    """Poca de sombra em pixels no chao (abre, fica e fecha em `dur`)."""
    def forma(t, p, u):
        v = min(1.0, t / dur)
        abre = min(1.0, v / 0.25) * (1 - max(0.0, (v - 0.7) / 0.3))
        w = rx * abre
        for dy, frac, nome in ((0, 1.0, 'b'), (0, 0.7, 'a'), (1, 0.8, 'b'), (-1, 0.6, 'b')):
            ww = math.floor(w * frac / te) * te
            if ww > 0:
                p.setdefault(nome, []).append((math.floor((ax - ww) / te) * te,
                                               math.floor(y / te) * te + dy * te, 2 * ww, te))
    camada.add_widget(_EfeitoPixel((('b', (0.20, 0.05, 0.36, 1.0)), ('a', (0.03, 0.0, 0.06, 1.0))),
                                  dur, forma), index=len(camada.children))


def _sair(s, on_fim, tipos=('teleporte', 'salto', 'sombra', 'corrida')):
    """Saida sorteada nas cenas curtas (como a entrada): teleporte em faixas
    de luz, salto para fora da tela, afundando numa poca de sombra ou
    correndo para o lado mais perto. Nada estica nem fica transparente."""
    k, P = s.k, K.POSE_A
    fim = _Uma(on_fim)

    def _sumiu():
        k.opacity = 0
        fim()
    tipo = random.choice(tipos)
    try:
        if tipo == 'salto':
            k.mostrar(_com(P['agacha'], olhos='s'))
            s.poeira()
            k.empurrar(capa=-8, cabelo=-6)

            def _vai(dt):
                k.mostrar(K.esticado(_com(P['pulo'], olhos='s')))
                _som('pulo')
                ax, ay = k.ancora()
                _mover(k, (ax, ay), (ax, s.H + k.extensao()[1] + dp(40)), 0.22, linear=True,
                       fantasmas=2, on_fim=_sumiu)
            Clock.schedule_once(_vai, 0.1)
        elif tipo == 'corrida':
            vai_esq = k.ancora()[0] < s.W / 2.0
            k.espelhar = vai_esq                       # vira para o lado da saida
            k.mostrar(_com(P['guarda'], pernas='avanco_baixo', olhos='s'))
            ax, ay = k.ancora()
            esq, _b, dir_, _c = k.extensao()
            destino = (-dir_ - dp(30), ay) if vai_esq else (s.W + esq + dp(30), ay)
            s.poeira(lado=1 if vai_esq else -1)
            _som('desliza')
            _mover(k, (ax, ay), destino, 0.2, linear=True, fantasmas=3, on_fim=_sumiu)
        elif tipo == 'sombra':
            _afunda(s, fim)
        else:
            _teleporte(k, s.cam, s.faiscas, on_fim=fim, dur=0.45, teto=s.area[3] - dp(2))
    except Exception as e:
        print(f"[saida] {e}")
        _sumiu()


def _afunda(s, on_fim):
    """Saida pela sombra: a poca abre nos pes e ele afunda nela (cortado
    na linha do chao, descendo em degraus de texel), escurecendo."""
    k, te = s.k, s.te
    fim = _Uma(on_fim)
    antes = tuple(k._cor_clarao.rgb)

    def _pronto():
        k.recortar()
        k.opacity = 0
        k.clarao = 0.0
        k._cor_clarao.rgb = antes
        fim()
    try:
        ax, ay = k.ancora()
        esq, baixo, dir_, cima = k.extensao()
        y = k.y + K._PES * k.ps - te
        _poca_sombra(s.cam, ax, y, 7.0 * k.ps, te, 0.75)
        _som('materializa')
        alt = baixo + cima + 2 * te
        n = 12
        k._cor_clarao.rgb = (0.05, 0.02, 0.1)
        passo = [-1]
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                d = int((t[0] - 0.12) * 30)                # a poca abre antes
                if d < 0 or d == passo[0]:
                    return True
                passo[0] = d
                if d > n:
                    _pronto()
                    return False
                k.recortar(y, None)
                k.clarao = min(0.66, d * 0.22)
                k.ancorar(ax, ay - math.floor(alt * d / float(n) / te) * te)
                if d % 3 == 0:
                    s.faiscas.estourar(ax + random.uniform(-dir_, esq) * 0.5, y, ROXO_SOMBRA, n=2,
                                       forca=dp(25), tam=te * 2, gravidade=-dp(160))
                return True
            except Exception as e:
                print(f"[saida] sombra: {e}")
                _pronto()
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[saida] sombra ignorada: {e}")
        _pronto()


# um Yoru por vez: enquanto uma cena curta esta rodando, a proxima espera na
# fila (ou, no carimbo e no WhatsApp, a acao acontece direto, sem ele)
_OCUPADO = {'ate': 0.0, 'fila': []}


def _yoru_livre():
    return time.time() >= _OCUPADO['ate']


def _yoru_ocupa(seg):
    _OCUPADO['ate'] = time.time() + seg


def _yoru_solta():
    _OCUPADO['ate'] = 0.0
    if _OCUPADO['fila']:
        prox = _OCUPADO['fila'].pop(0)
        Clock.schedule_once(lambda dt: prox(), 0.08)


def _na_fila(fn):
    """True se o Yoru esta ocupado (fn foi para a fila)."""
    if _yoru_livre():
        return False
    _OCUPADO['fila'].append(fn)
    return True


# ═══════════════════════════════════════════════════════════════════
#  EMOTES DE ANIME (chibi): gota de suor, !!, ?, nota, brilho nos olhos e
#  bochecha vermelha - pixel art por cima do Yoru, presos na cabeca dele
# ═══════════════════════════════════════════════════════════════════
_EMOTE_CORES = (('K', (0.03, 0.03, 0.08, 1.0)), ('W', (1.0, 1.0, 1.0, 1.0)), ('b', (0.55, 0.85, 1.0, 1.0)),
                ('B', (0.25, 0.55, 1.0, 1.0)), ('Y', (1.0, 0.86, 0.25, 1.0)), ('y', (0.95, 0.6, 0.1, 1.0)),
                ('R', (1.0, 0.42, 0.55, 0.85)), ('r', (1.0, 0.7, 0.78, 0.85)))
_EMOTE_MAPAS = {
    'gota': [".K...", "KbK..", "KbK..", "KbbK.", "KWbbK", "KbbbK", ".KKK."],
    '!!': ["KKK.KKK", "KYK.KYK", "KYK.KYK", "KYK.KYK", "KyK.KyK", "KKK.KKK", "KKK.KKK", "KYK.KYK",
           "KKK.KKK"],
    '?': [".KKKK.", "KYYYYK", "KYKKYK", "KKK.YK", "..KYYK", "..KYK.", "..KKK.", "..KYK.", "..KKK."],
    'nota': ["..KKKKK", "..KYYYK", "..KYKKK", "..KYK..", ".KKYK..", "KYYYK..", "KYYYK..", ".KKK..."],
    'brilho': ["..W..", "..W..", "WWbWW", "..W..", "..W.."],
    'rubor': [".RrRrR.", "RrRrRrR", ".RrRrR."],
}


class EmoteAnime(Widget):
    """Um emote preso na cabeca do boneco `k` por `dur` segundos. Entra
    num pulinho; a gota escorre, o ? balanca, a nota sobe, o brilho pisca."""

    def __init__(self, k, tipo, dur=0.9, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k, self.tipo, self.dur = k, tipo, dur
        self.mapa = _EMOTE_MAPAS[tipo]
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, _EMOTE_CORES)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)
        self._tick(0)

    def _pontos(self):
        """(x, y) do canto de baixo/esquerda do desenho e o tamanho do pixel."""
        k = self.k
        te = k.ps / float(K.R)
        frente = -1 if k.espelhar else 1
        ex, ey = K.olhos_texel(k._pose)[0]
        if k.espelhar:
            ex = K.TW - 1 - ex
        olho = (k.x + (ex + 0.5) * te, k.y + (ey + 0.5) * te)
        u = max(3.0, round(te * 3.4))         # grande o bastante para ler no celular
        h = len(self.mapa)
        w = len(self.mapa[0])
        if self.tipo == 'gota':               # do lado da testa, na frente do rosto
            return olho[0] + frente * te * 13 - w * u / 2.0, olho[1] + te * 2, u
        if self.tipo == 'brilho':             # em cima do olho
            u = max(1.0, round(te * 1.6))
            return olho[0] - w * u / 2.0, olho[1] - h * u / 2.0 + te, u
        if self.tipo == 'rubor':              # na bochecha, embaixo do olho
            u = max(1.0, round(te * 1.3))
            return olho[0] - frente * te * 2 - w * u / 2.0, olho[1] - te * 8, u
        # !!, ?, nota: acima da cabeca, um pouco para tras
        return olho[0] - frente * te * 11 - w * u / 2.0, olho[1] + te * 31, u

    def _tick(self, dt):
        try:
            self.t += dt
            t = self.t
            if t >= self.dur or self.k.parent is None:
                return self.parar()
            x, y, u = self._pontos()
            s = 1.0
            if t < 0.07:
                s = 0.3 + 1.0 * t / 0.07                 # pop: estoura maior...
            elif t < 0.13:
                s = 1.3 - 0.42 * (t - 0.07) / 0.06       # ... encolhe passando do ponto ...
            elif t < 0.19:
                s = 0.88 + 0.12 * (t - 0.13) / 0.06      # ... e assenta
            dy = 0.0
            if self.tipo == 'gota':
                dy = -round(t / self.dur * 4) * u        # escorre
            elif self.tipo == '?':
                x += round(math.sin(t * 9) * 1.2) * u    # balanca
            elif self.tipo == 'nota':
                dy = round(t * 14) * u * 0.5             # sobe
                x += round(math.sin(t * 7)) * u
            elif self.tipo == '!!':
                dy = (u if t < 0.25 and int(t * 20) % 2 else 0)
            if self.tipo == 'brilho' and int(t * 12) % 3 == 2:
                self._lote.desenhar({})
                return True
            uu = max(1.0, round(u * s))
            h = len(self.mapa)
            w = len(self.mapa[0])
            x0 = math.floor((x + (w * u - w * uu) / 2.0) / u) * u
            y0 = math.floor((y + dy) / u) * u
            p = {}
            for r, linha in enumerate(self.mapa):
                for c, ch in enumerate(linha):
                    if ch != '.':
                        p.setdefault(ch, []).append((x0 + c * uu, y0 + (h - 1 - r) * uu, uu))
            some = 1.0 if t < self.dur - 0.15 else max(0.0, (self.dur - t) / 0.15)
            self._lote.desenhar(p, alfa=some)
            return True
        except Exception as e:
            print(f"[emote] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)
        return False


def emote(camada, k, tipo, dur=0.9, atraso=0.0):
    """Poe um emote de anime no Yoru (nunca derruba a cena)."""
    def _poe(*_):
        try:
            if k.parent is not None:
                camada.add_widget(EmoteAnime(k, tipo, dur))
        except Exception as e:
            print(f"[emote] {e}")
    if atraso > 0:
        Clock.schedule_once(_poe, atraso)
    else:
        _poe()


def _pulinhos(k, pose, n=2, altura=None, dur=0.2, on_fim=None):
    """Pulinhos de alegria no lugar (chibi): no alto encolhe as pernas."""
    altura = altura or k.ps * 3
    base = k.ancora()
    no_ar = K.encolhido(pose)
    fim = _Uma(on_fim)
    cont = [0]

    def _pousa():
        k.mostrar(_com(pose, estica=-1))           # amortece o pouso
        Clock.schedule_once(lambda dt: (k.mostrar(pose), Clock.schedule_once(lambda dt2: _um(), 0.04)), 0.07)

    def _sobe():
        k.mostrar(K.esticado(pose))                  # impulso: o corpo todo estica
        k.empurrar(lift=4, cabelo=3)
        Clock.schedule_once(lambda dt: k.mostrar(no_ar), 0.05)
        _mover(k, base, base, dur, altura=altura, fantasmas=0, on_fim=_pousa)

    def _um():
        if cont[0] >= n or k.parent is None:
            k.mostrar(pose)
            fim()
            return
        cont[0] += 1
        k.mostrar(_com(pose, estica=-1))             # prepara: encolhe
        Clock.schedule_once(lambda dt: _sobe(), 0.07)
    _um()


def _moeda_na_cabeca(camada, k, te, on_bate=None):
    """Uma moeda de luz cai do alto e bate na cabeca dele (tonc!)."""
    x, y_fim = _topo_cabeca(k)
    y_ini = y_fim + te * 70
    x = math.floor(x / te) * te
    # moeda grande (cada pixel = 2x2 texels) com contorno escuro: da para ler no celular
    moeda = ["..KKK..", ".KYYYK.", "KYyYyYK", "KYyYyYK", "KYyYyYK", ".KYYYK.", "..KKK.."]
    cores = (('K', (0.30, 0.16, 0.02, 1.0)), ('Y', (1.0, 0.8, 0.2, 1.0)), ('y', (1.0, 0.96, 0.62, 1.0)))
    bateu = _Uma(on_bate)
    dur = 0.5

    def forma(t, p, u):
        b = u * 2
        k_ = min(1.0, t / dur)
        if k_ >= 1:
            bateu()
            yy = y_fim + te * 8 * max(0.0, 1 - (t - dur) / 0.25)     # quica e some
            if t > dur + 0.25:
                return
        else:
            yy = y_ini + (y_fim - y_ini) * k_ * k_
        gy = math.floor(yy / u) * u
        for r, linha in enumerate(moeda):
            for c, ch in enumerate(linha):
                if ch != '.':
                    p.setdefault(ch, []).append((x + (c - 3) * b, gy + (6 - r) * b, b, b))
    camada.add_widget(_EfeitoPixel(cores, dur + 0.3, forma))


def _textos_tela():
    """Retangulos (x0, y0, x1, y1 na janela) dos textos que estao na tela
    agora - o Yoru e os emotes nao devem ficar em cima deles. Com um popup
    aberto contam so os de dentro dele (o resto esta escurecido)."""
    from kivy.uix.label import Label
    from kivy.uix.modalview import ModalView
    topos = [w for w in Window.children if not getattr(w, '_do_yoru', False)]
    modais = [w for w in topos if isinstance(w, ModalView)]
    if modais:
        topos = modais[:1]                      # o de cima
    rects = []
    for topo in topos:
        for w in topo.walk(restrict=True):
            if not isinstance(w, Label) or not str(w.text or '').strip() or w.opacity < 0.1:
                continue
            try:
                x, y, ww, hh = _ret_janela(w)
                tw, th = w.texture_size
                cl = getattr(w, '_label', None)
                if cl is not None and getattr(cl, 'content_width', 0):
                    tw = cl.content_width               # o texto de verdade (sem a caixa)
                tw, th = min(tw, ww), min(th, hh)
                if tw < 2 or th < 2:
                    continue
                pad = w.padding[0] if isinstance(w.padding, (list, tuple)) else 0
                if w.text_size[0] and w.halign == 'left':
                    cx = x + pad + tw / 2.0
                elif w.text_size[0] and w.halign == 'right':
                    cx = x + ww - pad - tw / 2.0
                else:
                    cx = x + ww / 2.0
                cy = y + hh / 2.0
                rects.append((cx - tw / 2.0, cy - th / 2.0, cx + tw / 2.0, cy + th / 2.0))
            except Exception:
                continue
    return rects


class _Mini:
    """Base das cenas curtas do Yoru fora da abertura: camada por cima de
    tudo, o boneco no tamanho certo para o item, faiscas, rastro da lamina,
    a explosao do item, a saida (teleporte) e redes de seguranca."""

    def __init__(self, alvo, on_fim, seguranca=4.5, destruir=True):
        self.fim = _Uma(on_fim)
        self.alvo = alvo
        self.explodiu = False
        self._solto = False
        W, H = Window.size
        self.W, self.H = W, H
        self.rx, self.ry, self.rw, self.rh = _ret_janela(alvo)
        self.cx, self.cy = self.rx + self.rw / 2.0, self.ry + self.rh / 2.0
        self.cam = Widget(size_hint=(None, None), size=(W, H), pos=(0, 0))
        self.cam._do_yoru = True
        Window.add_widget(self.cam)
        alt_boneco = max(dp(62), min(self.rh * 1.7, dp(96), H * 0.15))
        self.ps = max(K.R, int(round(3 * int(math.ceil(alt_boneco * 1.12 / 31.0 / 3 - 0.15)) * K.TAMANHO)))
        self.te = self.ps / float(K.R)
        _PX[0] = self.te
        self.k = K.KiritoPixel(ps=self.ps)
        P = K.POSE_A
        self.k.precarregar([_com(P['agacha'], olhos='s'), K.esticado(_com(P['pulo'], olhos='s')),
                            _com(P['guarda'], pernas='avanco_baixo', olhos='s')])      # poses das saidas
        self._apos_sair = None
        self.faiscas = K.Faiscas()
        self.cam.add_widget(_Sombra(self.k))
        self.cam.add_widget(K.RastroLamina(self.k, self.faiscas))
        self.cam.add_widget(self.k)
        self.cam.add_widget(self.faiscas)
        self.area = _limites()
        if destruir:
            Clock.schedule_once(lambda dt: self.explodir(), seguranca)
        _yoru_ocupa(seguranca + 2.5)
        Clock.schedule_once(lambda dt: self._fim_camada(), seguranca + 2.5)
        _precarregar_sons(['materializa', 'teleporte', 'corte', 'corte2', 'pulo', 'koiguchi', 'sacar_iai',
                           'desliza', 'embainhar', 'golpe_final', 'habilidade', 'vidro', 'papel', 'giro',
                           'moedas', 'pouso', 'fala_yatta'] + _GEMIDOS)

    def no_quadro(self, x, y, poses):
        return _no_quadro(self.k, x, y, poses, self.area, dp(2))

    def lugar_livre(self, x, y, poses, xs=None, ys=None, emotes=True):
        """Ancora perto de (x, y) onde o corpo do Yoru (e o espaco dos emotes
        em cima da cabeca) cobre menos texto da tela. Cada texto coberto
        pesa mais que andar um pouco; sem texto por perto fica em (x, y)."""
        try:
            textos = _textos_tela()
            if not textos:
                return self.no_quadro(x, y, poses)
            k, te = self.k, self.te
            _e, baixo, _d, _c = _ext(k, poses)
            ax0, ay0 = k.ancora()
            hx, hy = _topo_cabeca(k)
            hx, hy = hx - ax0, hy - ay0
            x0, y0, x1, y1 = self.area
            xs = list(xs) if xs else [x] + [x0 + (x1 - x0) * f for f in (0.1, 0.25, 0.4, 0.6, 0.75, 0.9)]
            ys = list(ys) if ys else [y] + [y0 + (y1 - y0) * f for f in (0.15, 0.3, 0.45, 0.6, 0.75, 0.9)]
            melhor, nota = None, None
            for cx in xs:
                for cy in ys:
                    px, py = self.no_quadro(cx, cy, poses)
                    caixas = [(px - te * 12, py - baixo, px + te * 12, py + hy, 1.0)]
                    if emotes:                          # !!, ? e nota ficam acima da cabeca
                        caixas.append((px + hx - te * 23, py + hy + te * 12, px + hx + te * 23,
                                       py + hy + te * 46, 0.7))
                    cobre = 0.0
                    for a0, b0, a1, b1, peso in caixas:
                        for t0, u0, t1, u1 in textos:
                            w = min(a1, t1) - max(a0, t0)
                            h = min(b1, u1) - max(b0, u0)
                            if w > 0 and h > 0:
                                cobre += w * h * peso
                    n = cobre + math.hypot(px - x, py - y) * te * 6
                    if nota is None or n < nota:
                        melhor, nota = (px, py), n
            return melhor
        except Exception as e:
            print(f"[lugar] {e}")
            return self.no_quadro(x, y, poses)

    def preparar_arco(self, chave, arco, pal='katana'):
        """Desenha antes da hora a mancha do arco de luz de um golpe."""
        if not hasattr(self, '_oficina'):
            self._oficina = OficinaCortes(self.te * max(1, int(round(2.4 / self.te))))
            self._arcos = {}
        self._arcos[chave] = arco
        self._oficina.pedir(chave, arco, pal)

    def soltar_arco(self, chave, dur=0.1, decai=0.2):
        """O arco de luz corre pelo caminho da lamina (congela no hit-stop)."""
        try:
            mancha = self._oficina.obter(chave)
            if mancha is not None:
                self.cam.add_widget(CorteGravado(self._arcos[chave], mancha, dur=dur, decai=decai, k=self.k),
                                    index=len(self.cam.children))
        except Exception as e:
            print(f"[apagar] arco: {e}")

    def poeira(self, lado=0):
        """Poeira nos pes (pouso, freada)."""
        ax, _ = self.k.ancora()
        y = self.k.y + K._PES * self.ps
        for sentido in ((-1, 1) if not lado else (lado,)):
            self.faiscas.estourar(ax + sentido * self.ps * 3, y, POEIRA, n=5, forca=dp(70),
                                  tam=self.te * 2, gravidade=dp(260))

    def preparar_cacos(self, corte=None, racha=None, max_celulas=None, n_cacos=24):
        """Faz antes (num quadro congelado) a conta pesada dos cacos de um
        item grande; o explodir() seguinte so solta."""
        try:
            from efeitos import explodir_estilhacos
            self._cacos = explodir_estilhacos(self.alvo, self.fim, corte=corte, px=self.te * 2,
                                              abaixo_de=self.cam, racha=racha, adiar=True,
                                              max_celulas=max_celulas, n_cacos=n_cacos)
        except Exception as e:
            print(f"[apagar] cacos: {e}")

    def explodir(self, corte=None, racha=None):
        if self.explodiu:
            return
        self.explodiu = True
        try:
            pronto = getattr(self, '_cacos', None)
            if pronto is not None:
                self._cacos = None
                return pronto()
            self.alvo.opacity = 0
            from efeitos import explodir_estilhacos
            explodir_estilhacos(self.alvo, self.fim, corte=corte, px=self.te * 2, abaixo_de=self.cam,
                                racha=racha)
        except Exception as e:
            print(f"[apagar] explosao: {e}")
            self.fim()

    def sair(self, on_fim=None):
        """Sai de cena (saida sorteada); on_fim quando ele ja sumiu."""
        self._apos_sair = on_fim
        _sair(self, self._limpa)

    def _limpa(self):
        self.k.parar()
        depois, self._apos_sair = self._apos_sair, None
        if depois:
            _Uma(depois)()
        Clock.schedule_once(lambda dt: self._fim_camada(), 0.4)

    def _fim_camada(self):
        _remover_da_janela(self.cam)
        if not self._solto:                     # libera a vez uma vez so
            self._solto = True
            _yoru_solta()


def _apagar_iai(alvo, on_fim):
    """APAGAR LOTE - saque relampago: ele aparece do lado do item agachado,
    com a mao no cabo; um clarao e ele ja esta do outro lado com a lamina
    fora, e um risco fino fica atravessando o item. Um instante depois ele
    sacode a lamina (chiburi), embainha devagar e, no clique, o item cai em
    duas metades e vira cacos."""
    s = _Mini(alvo, on_fim)
    k, P = s.k, K.POSE_A
    try:
        esq = s.cx >= (s.area[0] + s.area[2]) / 2.0 if s.rw < (s.area[2] - s.area[0]) * 0.7 \
            else random.random() < 0.5
        k.espelhar = not esq
        pronto = _com(P['saca0'], olhos='s')
        corte = _com(P['segue1'], olhos='g')
        embainha = [_com(P['chiburi1_a'], olhos='s'), _com(P['chiburi1'], olhos='s'), P['embainha1_a'],
                    P['embainha1_b'], P['embainha1_c'], P['guardado']]
        y_pe = s.cy - s.rh * 0.15
        ini = s.no_quadro(s.rx - dp(6) if esq else s.rx + s.rw + dp(6), y_pe, [pronto])
        fim_p = s.no_quadro(s.rx + s.rw + dp(10) if esq else s.rx - dp(10), y_pe, [corte] + embainha)
        k.ancorar(*ini)
        k.mostrar(pronto)
        k.precarregar([corte] + embainha)
        corta1 = _com(P['corta1'], olhos='g')
        chaves, i_r = K.golpe(pronto, corta1, n_arma=1, prende=1, segue=2, volta=3,
                              lamina_recua=False, seg=corte)
        chaves = [(ch[0], _com(ch[1], s1=None, s2=None)) + tuple(ch[2:]) for ch in chaves]
        k.precarregar([c[1] for c in chaves])
        s.preparar_arco('iai', ArcoCorte.pelo_meio((s.cx, s.cy), 0 if esq else 180, s.rw + s.te * 18,
                                                   -0.08 if esq else 0.08, min(s.rh * 1.2, s.te * 26)))

        def _tensao():
            hx, hy = k.ponto_mao(1)
            _estrela(s.cam, hx, hy, s.ps * 0.6, BRANCO, raios=4, dur=0.12)
            _som('koiguchi')
            Clock.schedule_once(lambda dt: _saque(), 0.32)

        def _saque():
            # sai do cabo num estalo: prepara, os quadros de rastro e ele ja
            # passou - a luz da lamina atravessa o item
            def _q(i):
                if i == i_r - 2:
                    k.fantasma(cor=CIANO, alfa=0.6, duracao=0.3)
                    _som('sacar_iai')
                    _gemido()
                    s.soltar_arco('iai', dur=0.1, decai=0.28)
                    _mover(k, k.ancora(), fim_p, 0.1, ease='out', fantasmas=4)
                elif i == i_r:
                    k.impacto()
                    k.pausar(0.08)
                    s.faiscas.estourar(s.cx, s.cy, CIANO, n=12, forca=dp(140), tam=s.ps * 0.8)
                    _tremer(5)
            k.tocar(K.sequencia(chaves), on_quadro=_q,
                    on_fim=lambda: Clock.schedule_once(lambda dt: _embainha(), 0.18))

        def _embainha():
            seq = K.sequencia([(3, embainha[0], 'out'), (3, embainha[1], 'segura'), (6, embainha[2], 'in'),
                               (2, embainha[3], 'out'), (3, embainha[4], 'mola'), (1, embainha[5])])

            def _q(q):
                if q == 3:
                    _som('desliza')
                elif q == 14:
                    _som('embainhar')
                    _cai()
            k.tocar(seq, on_quadro=_q, on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.25))

        def _cai():
            # no clique da bainha o item racha no risco e as metades se soltam
            s.faiscas.estourar(s.cx, s.cy, BRANCO, n=12, forca=dp(140), tam=s.ps * 0.8)
            s.explodir(0.0, racha=0.3)

        _entrar(s, lambda: Clock.schedule_once(lambda dt: _tensao(), 0.08))
    except Exception as e:
        print(f"[apagar iai] {e}")
        _remover_da_janela(s.cam)
        s.explodir()


def _apagar_estocada(alvo, on_fim):
    """APAGAR TURNO - estocada: ele aparece de lado, recolhe a lamina ao
    lado do rosto mirando com a outra mao, se lanca e crava a ponta no meio
    do cartao; rachaduras de vidro correm a partir da ponta, ele puxa a
    lamina, da um mortal para tras e o cartao estoura em cacos."""
    s = _Mini(alvo, on_fim, seguranca=5.0)
    k, P = s.k, K.POSE_A
    try:
        esq = random.random() < 0.5
        k.espelhar = not esq
        arma = _com(P['estoca_arma'], olhos='s')
        crava = _com(P['estoca'], olhos='g')
        puxa = _com(P['estoca_puxa'], olhos='s')
        # a ponta da lamina no meio do cartao
        k.mostrar(crava)
        ax0, ay0 = k.ancora()
        tx, ty = k.ponta_espada(1, crava)
        alvo_a = (s.cx - (tx - ax0), s.cy - (ty - ay0))
        dist = max(s.rw * 0.5 + dp(24), dp(60))
        ini = s.no_quadro(alvo_a[0] - dist if esq else alvo_a[0] + dist, alvo_a[1], [arma])
        k.ancorar(*ini)
        k.mostrar(arma)
        recua = _com(arma, dx=arma['dx'] - 1, m1=(arma['m1'][0] - 2, arma['m1'][1]), incl=-1)
        k.precarregar([crava, puxa, recua, _com(P['pulo'], olhos='s'), K.bola(_com(P['pulo'], olhos='s'))])
        tx0, ty0 = k.ponta_espada(1, arma)
        ang_e = math.degrees(math.atan2(s.cy - ty0, s.cx - tx0))
        s.preparar_arco('estocada', ArcoCorte.pelo_meio(((tx0 + s.cx) / 2.0, (ty0 + s.cy) / 2.0), ang_e,
                                                        math.hypot(s.cx - tx0, s.cy - ty0) + s.te * 10,
                                                        0.02, s.te * 9))

        def _mira():
            tx2, ty2 = k.ponta_espada(1, arma)
            _estrela(s.cam, tx2, ty2, s.ps * 0.7, BRANCO, raios=4, dur=0.14)
            _som('koiguchi')
            k.empurrar(capa=-6, cabelo=-4)
            Clock.schedule_once(lambda dt: _lanca(), 0.34)

        def _lanca():
            # recolhe o braco (preparacao) e se lanca: a luz vai reta na frente
            def _vai():
                k.mostrar(K.smear(crava, arma['a1']))
                _som('pulo')
                _gemido()
                s.soltar_arco('estocada', dur=0.1, decai=0.22)
                _mover(k, k.ancora(), alvo_a, 0.1, linear=True, fantasmas=4,
                       on_fim=lambda: (k.mostrar(crava), _crava()))
            k.tocar(K.sequencia([(3, recua, 'in'), (1, recua)]), on_fim=_vai)

        def _crava():
            k.impacto(forte=True)
            k.pausar(0.14)
            s.preparar_cacos(max_celulas=12000, n_cacos=44)     # cartao grande: cacos miudos
            _som('golpe_final')
            _som('vidro')
            _tremer(10)
            _anel(s.cam, (s.cx, s.cy), s.ps, s.ps * 5, 0.25, BRANCO, esp=dp(2))
            s.faiscas.estourar(s.cx, s.cy, BRANCO, n=10, forca=dp(150), tam=s.ps * 0.7)
            rach = _rachaduras(s.cx, s.cy, s.rx, s.ry, s.rw, s.rh, s.te, n=9,
                               semente=random.randint(1, 9999))
            s.cam.add_widget(_PixelsLuz(rach, s.te, cresce=0.22, fica=0.5, some=0.1, grossura=1), index=0)
            Clock.schedule_once(lambda dt: _puxa(), 0.55)

        def _puxa():
            # puxa a lamina, o cartao estoura e ele salta para tras girando
            s.explodir(None)
            _som('corte2')
            k.mostrar(puxa)
            pulo = _com(P['pulo'], olhos='s')
            bola = K.bola(pulo)
            volta = s.no_quadro(ini[0], ini[1] + s.rh * 0.15, [pulo, puxa])
            _mover(k, k.ancora(), volta, 0.34, altura=dp(40), rot=(0, 360 if esq else -360), fantasmas=2,
                   on_fim=_pousa, rot_janela=(0.15, 0.85),
                   on_passo=lambda u: k.mostrar(bola if 0.15 < u < 0.85 else puxa))

        def _pousa():
            k.rotacao = 0
            k.mostrar(_com(P['guarda'], olhos='s'))
            Clock.schedule_once(lambda dt: s.sair(), 0.2)

        _entrar(s, lambda: Clock.schedule_once(lambda dt: _mira(), 0.06))
    except Exception as e:
        print(f"[apagar estocada] {e}")
        _remover_da_janela(s.cam)
        s.explodir()


def _apagar_x(alvo, on_fim):
    """APAGAR PERIODO - corte em X: ele aparece no alto com as duas laminas
    cruzadas atras da cabeca, salta sobre o item e desce as duas juntas em
    X; o X de luz fica marcado e o item se parte em quatro pedacos que voam
    para os lados antes de virar cacos."""
    s = _Mini(alvo, on_fim)
    k, P = s.k, K.POSE_A
    try:
        esq = s.cx >= (s.area[0] + s.area[2]) / 2.0 if s.rw < (s.area[2] - s.area[0]) * 0.7 \
            else random.random() < 0.5
        k.espelhar = not esq
        arma = _com(P['x_arma'], olhos='s')
        corta = _com(P['x_corta'], olhos='g')
        ini = s.no_quadro(s.rx - dp(10) if esq else s.rx + s.rw + dp(10), s.cy + s.rh * 1.2 + dp(20), [arma])
        alvo_a = s.no_quadro(s.cx - (dp(14) if esq else -dp(14)), s.cy + s.rh * 0.2, [arma, corta])
        k.ancorar(*ini)
        k.mostrar(arma)
        k.precarregar([corta])
        diag = math.hypot(s.rw, s.rh) + s.te * 14
        esp_x = min(s.rh * 0.9, s.te * 22)
        s.preparar_arco('x1', ArcoCorte.pelo_meio((s.cx, s.cy), -35 if esq else -145, diag, 0.1, esp_x))
        s.preparar_arco('x2', ArcoCorte.pelo_meio((s.cx, s.cy), 35 if esq else 145, diag, -0.1, esp_x * 0.85),
                        'azul')

        def _salta():
            _som('pulo')
            _mover(k, k.ancora(), alvo_a, 0.22, altura=dp(30), fantasmas=2, on_fim=_corta)

        def _corta():
            meio = K.smear(K.misturar(arma, corta, 0.5, 0.5), arma['a1'], arma['a2'])
            seq = K.sequencia([(1, meio, 'segura'), (1, K.smear(corta, arma['a1'], arma['a2']), 'segura'),
                               (4, corta, 'segura'), (4, _com(P['dupla'], olhos='s'), 'out'),
                               (1, _com(P['dupla'], olhos='s'))])
            k.tocar(seq)
            k.impacto()
            k.pausar(0.08)
            _som('corte2')
            _som('corte')
            _gemido()
            _tremer(9)
            s.soltar_arco('x1', dur=0.1, decai=0.26)
            Clock.schedule_once(lambda dt: s.soltar_arco('x2', dur=0.1, decai=0.26), 0.04)
            _estrela(s.cam, s.cx, s.cy, s.ps, CIANO, raios=4, dur=0.16)
            s.faiscas.estourar(s.cx, s.cy, CIANO, n=14, forca=dp(170), tam=s.ps * 0.8)
            s.faiscas.estourar(s.cx, s.cy, AZUL, n=10, forca=dp(140), tam=s.ps * 0.8)
            Clock.schedule_once(lambda dt: _parte(), 0.3)

        def _parte():
            s.explodir((35.0, -35.0), racha=0.3)
            Clock.schedule_once(lambda dt: s.sair(), 0.35)

        _entrar(s, lambda: Clock.schedule_once(lambda dt: _salta(), 0.12), tipos=('teleporte', 'corrida'))
    except Exception as e:
        print(f"[apagar x] {e}")
        _remover_da_janela(s.cam)
        s.explodir()


def kirito_fatiar(alvo, on_fim=None, tipo=None):
    """Apagar: o Yoru destroi o item com o golpe proprio de cada tela -
    'iai' (saque relampago: apagar lote), 'estocada' (apagar turno) ou 'x'
    (corte em X: apagar periodo). Sem tipo: o corte de cima para baixo
    (se materializa grudado na borda, pula, fatia em duas metades, os cacos
    explodem e ele some num teleporte)."""
    if tipo is not None and _na_fila(lambda: kirito_fatiar(alvo, on_fim, tipo)):
        return
    if tipo == 'iai':
        return _apagar_iai(alvo, on_fim)
    if tipo == 'estocada':
        return _apagar_estocada(alvo, on_fim)
    if tipo == 'x':
        return _apagar_x(alvo, on_fim)
    fim = _Uma(on_fim)
    camada = [None]
    explodiu = [False]

    def _explodir(corte=None):
        if explodiu[0]:
            return
        explodiu[0] = True
        try:
            alvo.opacity = 0
            from efeitos import explodir_estilhacos
            explodir_estilhacos(alvo, fim, corte=corte, px=_PX[0] * 2, abaixo_de=camada[0], racha=0.32)
        except Exception as e:
            print(f"[fatiar] explosao: {e}")
            fim()

    try:
        W, H = Window.size
        rx, ry, rw, rh = _ret_janela(alvo)
        cam = Widget(size_hint=(None, None), size=(W, H), pos=(0, 0))
        camada[0] = cam
        Window.add_widget(cam)
        alt_boneco = max(dp(62), min(rh * 1.7, dp(96), H * 0.15))
        ps = K.ps_inteiro(alt_boneco * 1.12 / 31.0)
        k = K.KiritoPixel(ps=ps)
        _PX[0] = k.ps / float(K.R)
        faiscas = K.Faiscas()
        cam.add_widget(K.RastroLamina(k, faiscas))
        cam.add_widget(k)
        cam.add_widget(faiscas)
        cy = ry + rh / 2.0
        bx0, by0, bx1, by1 = _limites()
        area = (bx0, by0, bx1, by1)
        meio = (bx0 + bx1) / 2.0
        esquerda = ((rx + rw / 2.0) < meio) if rw < (bx1 - bx0) * 0.7 else (random.random() < 0.5)
        pe = 8 * ps + dp(2)
        ini = (bx0 + pe, cy) if esquerda else (bx1 - pe, cy)
        k.rotacao = -90 if esquerda else 90
        k.espelhar = not esquerda
        k.ancorar(*ini)
        k.mostrar(_com(K.POSE_A['grudado'], olhos='s'))
        # corte de cima para baixo com preparacao e a lamina passando do ponto
        chaves, i_r = K.golpe(K.POSE_A['arma1'], K.POSE_A['corta_desce'], n_arma=2, prende=1,
                              segue=3, volta=4, seg=K.POSE_A['segue_desce'])
        golpe = K.sequencia(chaves)
        k.precarregar([K.POSE_A[n] for n in ('agacha', 'pulo')] + golpe)
        # ataca pelo canto do widget do lado de onde veio, inteiro no quadro
        ataque = _no_quadro(k, rx - dp(6) if esquerda else rx + rw + dp(6), cy + rh * 0.35,
                            golpe, area, dp(2))

        def _pula():
            # agacha na parede (mola comprimindo) e salta girando para o item
            k.tocar(K.sequencia([(2, _com(K.POSE_A['grudado'], olhos='s'), 'in'),
                                 (3, _com(K.POSE_A['agacha'], olhos='s'), 'segura'),
                                 (1, _com(K.POSE_A['agacha'], olhos='s'))]))
            arma = _com(K.POSE_A['arma1'], olhos='s')
            pulo = _com(K.POSE_A['pulo'], olhos='s')
            Clock.schedule_once(lambda dt: (k.parar(), _mover(
                k, k.ancora(), ataque, 0.28, altura=rh * 0.8 + dp(20),
                rot=(k.rotacao, 0), on_fim=_golpe,
                on_passo=_voo(k, K.esticado(pulo), pulo, arma, (0.2, 0.62)))), 0.2)

        def _golpe():
            k.rotacao = 0
            k.espelhar = not esquerda
            k.tocar(K.sequencia(chaves), on_quadro=lambda i: i == i_r and _impacto(), on_fim=_sai)

        def _impacto():
            ccx, ccy = rx + rw / 2.0, ry + rh / 2.0
            cam.add_widget(CorteMeiaLua(
                centro=(ccx, ccy), raio=rw * 0.62, ang_ini=165 if esquerda else 15,
                ang_fim=-40 if esquerda else 220, espessura=max(dp(10), rh * 0.55),
                achat=0.35, rotacao=-8 if esquerda else 8))
            faiscas.estourar(ccx, ccy, CIANO, n=18, forca=dp(170), tam=ps)
            _estrela(cam, ccx, ccy, ps)
            _som('corte')
            _gemido()
            _tremer(8)
            k.impacto()
            k.pausar(0.07)                                   # hit-stop
            _explodir(-60.0 if esquerda else -120.0)         # racha no talho (em pixel) e vira cacos

        def _sai():
            _teleporte(k, cam, faiscas, on_fim=_limpa, dur=0.45, teto=by1 - dp(2))

        def _limpa():
            k.parar()
            Clock.schedule_once(lambda dt: _remover_da_janela(cam), 0.4)

        _materializar(k, cam, faiscas, dur=0.26, on_fim=lambda: Clock.schedule_once(lambda dt: _pula(), 0.08))
        # seguranca: se algo travar, apaga mesmo assim e limpa a camada
        Clock.schedule_once(lambda dt: _explodir(), 3.5)
        Clock.schedule_once(lambda dt: _remover_da_janela(cam), 6.0)
    except Exception as e:
        print(f"[fatiar] ignorado: {e}")
        _remover_da_janela(camada[0])
        _explodir()


def kirito_carimbo(alvo, on_impacto=None):
    """ADICIONAR LOTE: o Yoru aparece ao lado do item novo com a lamina
    erguida por cima do ombro, da um corte curto e rapido na horizontal que
    'carimba' o +XP (o numero nasce no corte) e some."""
    feito = _Uma(on_impacto)
    if not _yoru_livre():
        feito()                                                 # ja tem um Yoru em cena: so o +XP
        return
    try:
        s = _Mini(alvo, None, seguranca=3.0, destruir=False)
        Clock.schedule_once(lambda dt: feito(), 1.6)            # o +XP sai de qualquer jeito
    except Exception as e:
        print(f"[carimbo] {e}")
        feito()
        return
    k, P = s.k, K.POSE_A
    try:
        arma = _com(P['carimbo_arma'], olhos='s')
        corta = _com(P['carimbo'], olhos='g')
        volta = _com(P['guarda'], olhos='s')
        # na ponta do item que nao tem texto: o +XP nasce ali e ele nao tapa a lista
        pos = s.lugar_livre(s.rx + s.rw * 0.88, s.cy, [arma, corta],
                            xs=[s.rx + s.rw * f for f in (0.08, 0.2, 0.35, 0.5, 0.65, 0.8, 0.92)],
                            ys=[s.cy, s.cy + s.rh * 0.5, s.cy - s.rh * 0.5])
        esq = pos[0] < s.cx
        k.espelhar = not esq
        pos = s.no_quadro(pos[0], pos[1], [arma, corta])
        k.ancorar(*pos)
        k.mostrar(arma)
        # o corte do carimbo: um arco de luz curto atravessando o item (em
        # pixel, como os outros golpes) - antes era so uma linha de 1 pixel
        s.preparar_arco('carimbo', ArcoCorte.pelo_meio((s.cx, s.cy), 0 if esq else 180, s.rw * 0.84,
                                                       0.04, s.te * 8))

        def _ve():
            # ve o lote novo: !! e olhos brilhando
            k.mostrar(_com(arma, olhos='e'))
            emote(s.cam, k, '!!', 0.5)
            emote(s.cam, k, 'brilho', 0.5)
            Clock.schedule_once(lambda dt: _corta(), 0.38)

        def _festa():
            feliz = _com(P['guarda'], olhos='e')
            emote(s.cam, k, 'nota', 0.9)
            _pulinhos(k, feliz, n=2, altura=s.ps * 3,
                      on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.1))

        def _corta():
            seq = K.sequencia([(2, arma, 'segura'), (1, K.smear(corta, arma['a1']), 'segura'),
                               (4, corta, 'segura'), (4, volta, 'out'), (1, volta)])

            def _q(q):
                if q == 2:
                    linha = _reta_pixels(s.rx + s.rw * 0.08, s.cy, s.rx + s.rw * 0.92, s.cy, s.te)
                    if not esq:
                        linha.reverse()
                    s.cam.add_widget(_PixelsLuz([linha], s.te, cresce=0.05, fica=0.12, some=0.15), index=0)
                    s.soltar_arco('carimbo', dur=0.08, decai=0.2)
                    s.faiscas.estourar(s.cx, s.cy, CIANO, n=8, forca=dp(130), tam=s.ps * 0.7)
                    _som('corte')
                    _gemido()
                    k.impacto()
                    feito()
            k.tocar(seq, on_quadro=_q, on_fim=_festa)

        _entrar(s, _ve)
    except Exception as e:
        print(f"[carimbo] {e}")
        _remover_da_janela(s.cam)
        feito()


VERDE_ZAP = (0.25, 0.92, 0.48)

# objetos pequenos em pixel art (uma letra por pixel; '.' = vazio)
# a carta do WhatsApp: envelope claro com a dobra em V e o selo verde
_CARTA = [
    ".KKKKKKKKKKKKKK.",
    "KWwwwwwwwwwwwwWK",
    "KwWwwwwwwwwwwWwK",
    "KwwWwwwwwwwwWwwK",
    "KwwwWwwwwwwWwwwK",
    "KwwwwWwggwWwwwwK",
    "KwwwwwWggWwwwwwK",
    "KwwwwwwwwwwwwwwK",
    "KwwwwwwwwwwwwwwK",
    "KwwwwwwwwwwwwwwK",
    ".KKKKKKKKKKKKKK.",
]
_CARTA_CORES = (('K', (0.04, 0.30, 0.16, 1.0)), ('w', (0.93, 1.0, 0.94, 1.0)),
                ('W', (0.50, 0.78, 0.60, 1.0)), ('g', (0.16, 0.82, 0.40, 1.0)))
# o cartao do turno: moldura ciano, linhas das pecas e o XP em verde
_CARTAO = [
    "CCCCCCCCCCCCCCCCCC",
    "CddddddddddddddddC",
    "CdllllllldddddxxdC",
    "CddddddddddddddddC",
    "CdlllllddddddxxxdC",
    "CddddddddddddddddC",
    "CdllllllllddddxxdC",
    "CddddddddddddddddC",
    "CdlllldddddddxxxdC",
    "CddddddddddddddddC",
    "CddddddddddddddddC",
    "CCCCCCCCCCCCCCCCCC",
]
_CARTAO_CORES = (('C', (0.0, 0.9, 1.0, 1.0)), ('d', (0.03, 0.06, 0.16, 1.0)),
                 ('l', (0.45, 0.80, 0.95, 1.0)), ('x', (0.20, 1.0, 0.55, 1.0)))
# o carimbo de "salvo" (um visto) e os dois vistos de "enviado"
_VISTO = [
    ".......GG",
    "......GGg",
    "GG...GGg.",
    "gGG.GGg..",
    ".gGGGg...",
    "..gGg....",
]
_VISTO_CORES = (('G', (0.30, 1.0, 0.55, 1.0)), ('g', (0.05, 0.42, 0.20, 1.0)))


class _Sprite(Widget):
    """Um objeto pequeno em pixel art (carta, cartao, visto): cada letra do
    mapa e um bloco de `b` px. Fica onde `segue()` mandar, ou voa com
    voar(); aparece linha por linha (`linhas`) e pisca branco (`branco` s)."""

    def __init__(self, mapa, cores, b, te, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.mapa, self.b, self.te = mapa, b, te
        self.nc, self.nr = max(len(l) for l in mapa), len(mapa)
        self.cx = self.cy = 0.0
        self.visivel = True
        self.segue = None
        self.linhas = self.nr
        self.branco = 0.0
        self.girar = False
        self._voo = None
        self._teve_pai = False
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, tuple(cores) + (('#', (1.0, 1.0, 1.0, 1.0)),))
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def voar(self, para, dur, altura=0.0, ease='in', on_fim=None, girar=False, on_passo=None):
        self.segue = None
        self.girar = girar
        self._voo = [self.cx, self.cy, para, max(0.01, dur), altura, ease, _Uma(on_fim), 0.0, on_passo]

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar() if self._teve_pai else None    # ainda nao entrou em cena
            self._teve_pai = True
            self.t += dt
            if self.branco > 0:
                self.branco -= dt
            if self.segue is not None:
                self.cx, self.cy = self.segue()
            elif self._voo is not None:
                v = self._voo
                v[7] += dt
                u = min(1.0, v[7] / v[3])
                e = u * u if v[5] == 'in' else (1 - (1 - u) ** 2 if v[5] == 'out' else u)
                self.cx = v[0] + (v[2][0] - v[0]) * e
                self.cy = v[1] + (v[2][1] - v[1]) * e + math.sin(math.pi * u) * v[4]
                if v[8]:
                    v[8](u)
                if u >= 1.0:
                    self._voo = None
                    v[6]()
            p = {}
            if self.visivel and self.linhas > 0:
                b, te = self.b, self.te
                em_pe = self.girar and int(self.t * 14) % 2 == 1
                w, h = (self.nr, self.nc) if em_pe else (self.nc, self.nr)
                ox = math.floor((self.cx - w * b / 2.0) / te) * te
                oy = math.floor((self.cy - h * b / 2.0) / te) * te
                branco = self.branco > 0
                for r, linha in enumerate(self.mapa[:self.linhas]):
                    for c, ch in enumerate(linha):
                        if ch == '.':
                            continue
                        lx, ly = (r, c) if em_pe else (c, self.nr - 1 - r)
                        p.setdefault('#' if branco else ch, []).append((ox + lx * b, oy + ly * b, b))
            self._lote.desenhar(p)
        except Exception as ex:
            print(f"[sprite] {ex}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)
        return False


def _juntar(camada, origens, destino, cor, passo=0.07, on_chega=None, on_fim=None, voo=0.2):
    """As linhas de um texto 'viram luz' e vao para um ponto: debaixo de cada
    linha (x0, y, x1) um risco de luz acende da esquerda para a direita,
    encolhe para a ponta e voa em arco ate destino() - uma depois da outra.
    on_chega(i) quando cada uma chega."""
    acende = 0.12
    chegou = [False] * len(origens)
    dur = max(0.05, (len(origens) - 1) * passo + acende + voo + 0.06)

    def forma(t, p, u):
        dx, dy = destino()
        for i, (x0, y, x1) in enumerate(origens):
            tl = t - i * passo
            if tl < 0:
                continue
            if tl < acende:
                k = tl / acende
                xa = x0 + (x1 - x0) * k
                gx0, gy = math.floor(x0 / u) * u, math.floor(y / u) * u
                larg = max(u, math.floor((xa - x0) / u) * u)
                p.setdefault('cor', []).append((gx0, gy, larg, u * 2))
                p.setdefault('luz', []).append((gx0 + larg - u * 2, gy, u * 2, u * 2))
            elif tl < acende + voo:
                k = (tl - acende) / voo
                for j, nome in enumerate(('luz', 'clara', 'cor', 'cor')):   # a ponta e a cauda
                    kj = max(0.0, k - j * 0.07)
                    e = kj * kj
                    hx = x1 + (dx - x1) * e
                    hy = y + (dy - y) * e + math.sin(math.pi * kj) * u * 10
                    lado = u * (3 if j < 2 else 2)
                    p.setdefault(nome, []).append((math.floor(hx / u) * u, math.floor(hy / u) * u, lado, lado))
            elif not chegou[i]:
                chegou[i] = True
                if on_chega:
                    on_chega(i)

    def _fim():
        for i, c in enumerate(chegou):          # nenhuma fica sem chegar
            if not c and on_chega:
                on_chega(i)
        if on_fim:
            on_fim()
    camada.add_widget(_EfeitoPixel(_cores_efeito(cor), dur, forma, on_fim=_fim))


def _linhas_de(widgets, limite=6, area=None):
    """(x0, y, x1) do risco embaixo de cada widget de texto que esta na tela,
    de cima para baixo (no maximo `limite`)."""
    W, H = Window.size
    out = []
    for w in widgets or []:
        try:
            if isinstance(w, (tuple, list)):
                x, y, ww, hh = w
            else:
                x, y, ww, hh = _ret_janela(w)
            if ww <= 0 or hh <= 0 or y < 0 or y + hh > H:
                continue
            if area and not (area[1] <= y + hh / 2.0 <= area[3]):
                continue
            x0 = max(dp(4), x + dp(6))
            out.append((x0, y + hh * 0.12, min(W - dp(4), x0 + ww * 0.62)))
        except Exception:
            pass
    out.sort(key=lambda r: -r[1])
    return out[:limite]


def kirito_vitoria(alvo, linhas=None, area=None):
    """FINALIZAR TURNO - guardar o turno: o Yoru aparece com a lamina na
    mao; as pecas do dia (`linhas`: onde cada uma estava na lista) viram luz
    e se juntam num cartao do turno ao lado dele; ele sacode a lamina,
    embainha ate o clique, carimba o cartao com a mao (o visto verde de
    salvo), o cartao voa para as Memorias e ele comemora. Nenhum corte."""
    if _na_fila(lambda: kirito_vitoria(alvo, linhas, area)):
        return
    try:
        s = _Mini(alvo, None, seguranca=6.0, destruir=False)
    except Exception as e:
        print(f"[vitoria] {e}")
        return
    k, P = s.k, K.POSE_A
    try:
        te = s.te
        k.espelhar = False
        guarda = _com(P['guarda'], olhos='s')
        passos = [_com(P['chiburi1_a'], olhos='s'), _com(P['chiburi1'], olhos='s'), P['embainha1_a'],
                  P['embainha1_b'], P['embainha1_c'], P['guardado']]
        bate_a = _com(P['joga_arma'], olhos='s')
        bate = _com(P['joga'], olhos='g')
        riscos = _linhas_de(linhas, limite=7, area=area)      # so as pecas que estavam a vista
        b = te * 4
        lc, ac = len(_CARTAO[0]) * b, len(_CARTAO) * b
        # ele a esquerda, o cartao a direita, na altura de onde a lista estava
        y0 = (sum(r[1] for r in riscos) / len(riscos)) if riscos else s.cy
        x0 = s.area[0] + (s.area[2] - s.area[0]) * 0.34
        pos = s.no_quadro(x0, y0, [guarda, bate] + passos)
        k.ancorar(*pos)
        k.mostrar(bate)
        mx, my = k.ponto_mao(1)                         # onde a mao bate = a borda do cartao
        centro = (min(s.area[2] - lc / 2.0 - dp(4), mx + te * 3 + lc / 2.0), my)
        k.mostrar(guarda)
        k.precarregar(passos + [bate_a, bate, _com(P['vitoria'], olhos='e'), _com(P['vitoria'], olhos='v')])
        cartao = _Sprite(_CARTAO, _CARTAO_CORES, b, te)
        cartao.cx, cartao.cy = centro
        cartao.linhas = 0
        visto = _Sprite(_VISTO, _VISTO_CORES, b, te)
        visto.visivel = False
        visto.segue = lambda: (cartao.cx + b, cartao.cy - b)

        def _junta():
            s.cam.add_widget(cartao, index=len(s.cam.children))      # atras do Yoru
            s.cam.add_widget(visto, index=len(s.cam.children) - 1)
            n = max(1, len(riscos))

            def _chega(i):
                cartao.linhas = min(cartao.nr, int(math.ceil(cartao.nr * (i + 1) / float(n))))
                cartao.branco = 0.05
                s.faiscas.estourar(centro[0], centro[1], CIANO, n=3, forca=dp(70), tam=te * 2)
            if riscos:
                _som('desliza')
                _juntar(s.cam, riscos, lambda: centro, CIANO, on_chega=_chega,
                        on_fim=lambda: Clock.schedule_once(lambda dt: _embainha(), 0.1))
            else:
                _chega(0)
                Clock.schedule_once(lambda dt: _embainha(), 0.2)

        def _embainha():
            cartao.linhas = cartao.nr
            seq = K.sequencia([(2, passos[0], 'out'), (3, passos[1], 'segura'), (5, passos[2], 'in'),
                               (2, passos[3], 'out'), (3, passos[4], 'mola'), (1, passos[5])])

            def _q(q):
                if q == 13:
                    _som('embainhar')
            k.tocar(seq, on_quadro=_q, on_fim=_carimba)

        def _carimba():
            seq = K.sequencia([(4, bate_a, 'in'), (1, bate, 'segura'), (9, bate, 'segura'), (1, bate)])

            def _q(q):
                if q == 4:                                  # a mao bate no cartao: SALVO
                    visto.visivel = True
                    visto.branco = 0.07
                    cartao.branco = 0.05
                    k.impacto()
                    _som('golpe_final')
                    _tremer(5)
                    _anel(s.cam, centro, te * 6, lc * 0.75, 0.3, VERDE_ZAP, esp=dp(2), achat=0.55)
                    s.faiscas.estourar(centro[0], centro[1], VERDE_ZAP, n=12, forca=dp(150), tam=te * 2,
                                       gravidade=dp(260))
            k.tocar(seq, on_quadro=_q, on_fim=_guarda)

        def _guarda():
            # o cartao carimbado vai embora para as Memorias (sobe e sai pela direita)
            W, H = Window.size
            fora = (W + lc, min(H + ac, centro[1] + H * 0.45))

            def _rastro(u):
                if random.random() < 0.6:
                    s.faiscas.estourar(cartao.cx, cartao.cy, random.choice((CIANO, VERDE_ZAP)), n=1,
                                       forca=dp(30), tam=te * 2, gravidade=-dp(60))
            _som('papel')
            cartao.voar(fora, 0.42, altura=te * 14, ease='in', on_passo=_rastro,
                        on_fim=lambda: (cartao.parar(), visto.parar()))
            k.mostrar(_com(P['guardado'], olhos='f'))
            emote(s.cam, k, 'gota', 0.5)
            Clock.schedule_once(lambda dt: _comemora(), 0.5)

        def _comemora():
            # ... turno guardado: !!, olhos brilhando, corado, pulinhos
            feliz = _com(P['vitoria'], olhos='e')
            _som('fala_yatta')
            emote(s.cam, k, '!!', 0.45)
            emote(s.cam, k, 'brilho', 1.0, atraso=0.08)
            emote(s.cam, k, 'rubor', 1.2, atraso=0.08)
            _pulinhos(k, feliz, n=2, altura=s.ps * 4, on_fim=_convencido)

        def _convencido():
            k.mostrar(_com(P['vitoria'], olhos='v'))
            emote(s.cam, k, 'nota', 0.7)
            Clock.schedule_once(lambda dt: s.sair(), 0.6)

        _entrar(s, _junta)
    except Exception as e:
        print(f"[vitoria] {e}")
        _remover_da_janela(s.cam)


def _vistos(camada, x, y, te, cor=VERDE_ZAP):
    """Os dois vistos de 'enviado' em pixel: um, depois o outro; ficam um
    instante e somem ralando em xadrez."""
    b = te * 3

    def forma(t, p, u):
        for n in range(2):
            tl = t - n * 0.1
            if tl < 0:
                continue
            ox = math.floor((x + n * b * 5) / te) * te
            oy = math.floor(y / te) * te
            for r, linha in enumerate(_VISTO):
                for c, ch in enumerate(linha):
                    if ch == '.':
                        continue
                    if t > 0.6 and (r + c) % 2 == int((t - 0.6) / 0.07) % 2:
                        continue
                    nome = 'luz' if tl < 0.07 else ('cor' if ch == 'G' else 'sombra')
                    p.setdefault(nome, []).append((ox + c * b, oy + (len(_VISTO) - 1 - r) * b, b))
    cores = _cores_efeito(cor) + (('sombra', (cor[0] * 0.2, cor[1] * 0.45, cor[2] * 0.4, 1.0)),)
    camada.add_widget(_EfeitoPixel(cores, 0.8, forma))


def kirito_carta(alvo, on_fim=None, linhas=None, area=None):
    """ENVIAR PRO WHATSAPP: o Yoru aparece ao lado do botao com a mao
    estendida; as linhas do turno (`linhas`: os widgets de cada peca) acendem
    em verde e voam para a mao dele, onde viram uma carta; ele joga a carta
    para a frente, corta no ar e ela dispara para fora da tela, deixando os
    dois vistos de enviado - so entao o WhatsApp abre."""
    feito = _Uma(on_fim)
    if not _yoru_livre():
        feito()                                                  # ja tem um Yoru em cena: abre direto
        return
    try:
        s = _Mini(alvo, None, seguranca=4.6, destruir=False)
        Clock.schedule_once(lambda dt: feito(), 4.4)             # o WhatsApp abre de qualquer jeito
    except Exception as e:
        print(f"[carta] {e}")
        feito()
        return
    k, P = s.k, K.POSE_A
    try:
        te = s.te
        k.espelhar = False
        recebe = _com(P['joga'], pernas='base', dx=0, olhos='s')      # a mao estendida
        arma = _com(P['carimbo_arma'], olhos='s')
        corta = _com(P['carimbo'], olhos='g')
        fim_p = _com(P['guardado'], olhos='v')
        pos = s.lugar_livre(s.rx - dp(10), s.cy + s.rh * 0.6, [recebe, arma, corta])
        k.ancorar(*pos)
        k.mostrar(corta)                                # onde a lamina passa: e ali que a carta e cortada
        m0, p0 = k.ponto_mao(1), k.ponta_espada(1, corta)
        no_corte = (m0[0] + (p0[0] - m0[0]) * 0.72, m0[1] + (p0[1] - m0[1]) * 0.72)
        k.mostrar(recebe)
        k.precarregar([arma, corta, K.smear(corta, arma['a1']), fim_p])
        b = te * 5
        carta = _Sprite(_CARTA, _CARTA_CORES, b, te)
        carta.linhas = 0
        na_mao = lambda: (k.ponto_mao(1)[0] + b * 2, k.ponto_mao(1)[1] + b * 6)
        carta.segue = na_mao
        riscos = _linhas_de(linhas, limite=6, area=area)      # so as linhas que estao a vista

        def _junta():
            s.cam.add_widget(carta)
            n = max(1, len(riscos))

            def _chega(i):
                carta.linhas = min(carta.nr, int(math.ceil(carta.nr * (i + 1) / float(n))))
                carta.branco = 0.05
                cx, cy = na_mao()
                s.faiscas.estourar(cx, cy, VERDE_ZAP, n=3, forca=dp(70), tam=te * 2)
            if riscos:
                _som('desliza')
                _juntar(s.cam, riscos, na_mao, VERDE_ZAP, on_chega=_chega,
                        on_fim=lambda: Clock.schedule_once(lambda dt: _joga(), 0.12))
            else:
                _chega(0)
                Clock.schedule_once(lambda dt: _joga(), 0.25)

        def _joga():
            carta.linhas = carta.nr
            carta.cx, carta.cy = na_mao()
            _som('papel')
            carta.voar(no_corte, 0.36, altura=te * 26, ease='lin', girar=True)
            # enquanto a carta sobe ele ergue a lamina; corta quando ela desce na frente
            seq = K.sequencia([(7, arma, 'out'), (2, arma, 'segura'), (1, K.smear(corta, arma['a1']), 'segura'),
                               (5, corta, 'segura'), (4, fim_p, 'out'), (8, fim_p, 'segura'), (1, fim_p)])

            def _q(q):
                if q == 10:
                    W, H = Window.size
                    cx, cy = carta.cx, carta.cy
                    carta.girar = False
                    carta.branco = 0.07
                    k.impacto()
                    _som('corte')
                    _gemido()
                    _estrela(s.cam, cx, cy, s.ps * 0.8, VERDE_ZAP, raios=4, dur=0.16)
                    s.faiscas.estourar(cx, cy, VERDE_ZAP, n=10, forca=dp(150), tam=te * 2)

                    def _rastro(u):
                        s.faiscas.estourar(carta.cx, carta.cy, random.choice((VERDE_ZAP, (0.85, 1.0, 0.9))), n=1,
                                           forca=dp(30), tam=te * 2, gravidade=-dp(60))
                    # o corte ENVIA: a carta dispara para fora (cima, direita)
                    carta.voar((W + te * 40, cy + (W - cx) * 0.75), 0.3, ease='in', on_passo=_rastro,
                               on_fim=carta.parar)
                    _vistos(s.cam, cx - te * 14, cy + te * 8, te)
                elif q == 18:
                    emote(s.cam, k, 'nota', 0.6)
            # o WhatsApp (e o aviso de copiado) so abre depois que ele saiu
            k.tocar(seq, on_quadro=_q, on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(feito), 0.1))

        _entrar(s, _junta)
    except Exception as e:
        print(f"[carta] {e}")
        _remover_da_janela(s.cam)
        feito()


kirito_pergaminho = kirito_carta        # nome antigo (era um pergaminho)


OURO = (1.0, 0.84, 0.25)


def kirito_nivel(alvo):
    """SUBIU DE NIVEL: o Yoru aparece logo abaixo do nivel, abaixa e ergue a
    espada apontando para ele; o proprio NUMERO responde - um anel de luz
    dourada abre em volta dele, com estrelas e faiscas pela faixa toda; ele
    vira de frente com o meio sorriso (brilho no olho) e some."""
    if _na_fila(lambda: kirito_nivel(alvo)):
        return
    try:
        s = _Mini(alvo, None, seguranca=4.5, destruir=False)
    except Exception as e:
        print(f"[nivel] {e}")
        return
    k, P = s.k, K.POSE_A
    try:
        k.espelhar = random.random() < 0.5
        guarda = _com(P['guarda'], olhos='s')
        ergue = _com(P['salto_fim'], olhos='v')
        vit = P['vitoria']
        # logo abaixo do nivel, um pouco para o lado: a ponta da espada erguida
        # chega perto do numero sem tapar
        x = s.cx + (s.rw * 0.3 if k.espelhar else -s.rw * 0.3)
        k.ancorar(x, s.ry)
        k.mostrar(ergue)
        _tx, ty = k.ponta_espada(1, ergue)
        y = s.ry - (ty - s.ry) - dp(4)                  # a ponta para logo abaixo da faixa
        pos = s.lugar_livre(x, y, [guarda, ergue, vit], xs=[x, s.cx - s.rw * 0.3, s.cx + s.rw * 0.3],
                            ys=[y, y - dp(14), y - dp(28)])
        k.espelhar = pos[0] > s.cx                      # olhando para o nivel
        pos = s.no_quadro(pos[0], pos[1], [guarda, ergue, vit])
        k.ancorar(*pos)
        k.mostrar(guarda)
        k.precarregar([ergue, _com(vit, olhos='e'), K.encolhido(_com(vit, olhos='e'))])

        def _comemora():
            seq = K.sequencia([(3, _com(P['agacha'], olhos='s'), 'in'), (4, ergue, 'out'), (14, ergue, 'segura'),
                               (4, _com(vit, olhos='e'), 'out'), (1, _com(vit, olhos='e'))])

            def _festa():
                emote(s.cam, k, 'brilho', 1.0)
                emote(s.cam, k, 'rubor', 1.1)
                emote(s.cam, k, 'nota', 0.9, atraso=0.2)
                _pulinhos(k, _com(vit, olhos='e'), n=2, altura=s.ps * 4,
                          on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.25))

            def _q(q):
                if q == 4:
                    tx, ty = k.ponta_espada(1, ergue)
                    _estrela(s.cam, tx, ty, s.ps * 0.7, OURO, raios=5, dur=0.2)
                    # o numero responde: anel deitado em volta da faixa do nivel
                    r1 = min(s.rw * 0.52, s.cx - s.area[0] - dp(3), s.area[2] - s.cx - dp(3))
                    ach = max(0.2, min(0.5, (s.rh * 0.9) / max(1.0, r1)))
                    _anel(s.cam, (s.cx, s.cy), s.ps * 2, r1, 0.5, OURO, esp=dp(3), achat=ach)
                    _anel(s.cam, (s.cx, s.cy), s.ps, r1 * 0.6, 0.4, BRANCO, esp=dp(2), achat=ach)
                    for f in (-0.36, -0.18, 0.18, 0.36):
                        _estrela(s.cam, s.cx + s.rw * f, s.cy + s.rh * random.uniform(-0.3, 0.3), s.ps * 0.5,
                                 OURO, raios=4, dur=0.22)
                        s.faiscas.estourar(s.cx + s.rw * f, s.cy, OURO, n=5, forca=dp(150), tam=s.te * 2,
                                           gravidade=dp(260))
                    s.faiscas.estourar(s.cx, s.cy, BRANCO, n=8, forca=dp(140), tam=s.te * 2, gravidade=dp(200))
                    _som('habilidade')
                    emote(s.cam, k, '!!', 0.5)
                    k.empurrar(capa=-10, cabelo=-10, lift=4)
            k.tocar(seq, on_quadro=_q, on_fim=_festa)
        _entrar(s, _comemora, tipos=('teleporte', 'queda', 'sombra'))
    except Exception as e:
        print(f"[nivel] {e}")
        _remover_da_janela(s.cam)


def kirito_meta(alvo):
    """BATEU A META: o Yoru aparece de pe em cima da caixa do resultado (sem
    tapar o texto nem o botao OK), gira as duas espadas, e chovem moedas de
    luz douradas por cima do valor; termina de frente na pose de vitoria e
    some."""
    if _na_fila(lambda: kirito_meta(alvo)):
        return
    try:
        s = _Mini(alvo, None, seguranca=5.0, destruir=False)
    except Exception as e:
        print(f"[meta] {e}")
        return
    k, P = s.k, K.POSE_A
    try:
        k.espelhar = random.random() < 0.5
        g1 = _com(P['giro_1'], olhos='v')
        vit = P['vitoria']
        # de pe na borda de cima da caixa, perto de um canto
        poses_m = [g1, P['giro_2'], P['giro_3'], vit]
        k.mostrar(_com(P['dupla'], olhos='s'))
        x = s.rx + s.rw * (0.8 if k.espelhar else 0.2)
        k.ancorar(x, s.ry + s.rh)
        sobe = (s.ry + s.rh) - (k.y + K._PES * s.ps)     # os pes na borda
        pos = s.no_quadro(x, s.ry + s.rh + sobe, poses_m)
        k.espelhar = pos[0] > s.cx
        k.ancorar(*pos)
        g2 = _com(P['giro_2'], olhos='v')                  # de costas
        g3 = _com(P['giro_3'], olhos='v')                  # de frente
        k.precarregar([g1, g2, g3, _com(vit, olhos='e'), _com(vit, olhos='u')])

        def _chuva(dt):
            for i in range(10):
                x = s.rx + s.rw * random.uniform(0.1, 0.9)
                y = s.ry + s.rh * random.uniform(0.85, 1.05)
                s.faiscas.estourar(x, y, random.choice((OURO, OURO, BRANCO)), n=1, forca=dp(60),
                                   tam=s.te * 3, gravidade=dp(420))

        def _gira():
            # uma volta de verdade, desenhada: de lado -> de frente -> do outro
            # lado -> de costas -> de lado (nada de achatar o desenho)
            seq = K.sequencia([(2, g1, 'segura'), (2, g3, 'segura'), (2, g1, 'segura'), (2, g2, 'segura'),
                               (2, g1, 'segura'), (5, g1, 'mola'),
                               (4, _com(vit, olhos='e'), 'out'), (1, _com(vit, olhos='e'))])
            lado0 = k.espelhar

            def _q(q):
                if q == 4:
                    k.espelhar = not lado0
                elif q == 8:
                    k.espelhar = lado0
                if q == 2:
                    _som('giro')
                    ax, ay = k.ancora()
                    _anel(s.cam, (ax, ay), s.ps * 2, s.ps * 9, 0.35, OURO, esp=dp(2), achat=0.35)
                elif q == 7:
                    _som('moedas')
                    Clock.schedule_once(_chuva, 0.0)
                    Clock.schedule_once(_chuva, 0.25)
                    Clock.schedule_once(_chuva, 0.5)
                elif q == 15:
                    emote(s.cam, k, 'brilho', 0.8)

            def _tonc():
                # uma moeda cai na cabeca dele: TONC! ... e ele ri, todo feliz
                _som('moedas')
                k.mostrar(_com(vit, olhos='u'))
                k.empurrar(cabelo=10, lift=-6)
                hx, hy = _topo_cabeca(k)
                _estrela(s.cam, hx, hy, s.te * 2, OURO, raios=4, dur=0.2)
                balao(s.cam, 'TONC!', k, tipo='grito', dur=0.6, font_size=sp(24))
                Clock.schedule_once(lambda dt: (k.mostrar(_com(vit, olhos='e')),
                                                emote(s.cam, k, 'brilho', 0.8),
                                                emote(s.cam, k, 'nota', 0.7, atraso=0.1)), 0.55)
                Clock.schedule_once(lambda dt: s.sair(), 1.35)
            k.tocar(seq, on_quadro=_q,
                    on_fim=lambda: _moeda_na_cabeca(s.cam, k, s.te, on_bate=_tonc))
        _entrar(s, _gira, tipos=('teleporte', 'queda', 'corrida', 'sombra'))
    except Exception as e:
        print(f"[meta] {e}")
        _remover_da_janela(s.cam)


def kirito_wipe(widgets, on_fim=None, grafico=None, area_lista=None, extras=None):
    """WIPE - Starburst Stream: o Yoru se materializa, saca as duas espadas
    dizendo o nome do golpe e da UM golpe em cada coisa da tela, de cima para
    baixo, alternando as espadas: cada memoria racha no talho e vira cacos
    no proprio golpe; depois os filtros (extras) e, no golpe final, o
    grafico de barras do topo. Nenhum corte no vento, nenhum corte repetido."""
    if _na_fila(lambda: kirito_wipe(widgets, on_fim, grafico, area_lista, extras)):
        return
    _yoru_ocupa(16.0)
    fim = _Uma(on_fim)
    camada = [None]
    try:
        W, H = Window.size
        y_min, y_max = (area_lista[1], area_lista[3]) if area_lista else (0.0, float(H))
        vis = []
        for w in widgets:
            try:
                x, y, ww, hh = _ret_janela(w)
                if ww > 0 and hh > 0 and y_min <= y + hh / 2.0 <= y_max:
                    vis.append((w, x, y, ww, hh))
            except Exception:
                pass
        vis.sort(key=lambda t: -t[2])                 # de cima para baixo
        fora = []
        for w in (extras or []):                      # os filtros: da esquerda para a direita
            try:
                x, y, ww, hh = _ret_janela(w)
                if ww > 0 and hh > 0 and x + ww > 0 and x < W:
                    fora.append((w, x, y, ww, hh))
            except Exception:
                pass
        fora.sort(key=lambda t: t[1])
        vis += fora[:4]
        cam = Widget(size_hint=(None, None), size=(W, H), pos=(0, 0))
        camada[0] = cam
        Window.add_widget(cam)
        ps = _ps_para(W, H)
        k = K.KiritoPixel(ps=ps)
        _PX[0] = k.ps / float(K.R)
        faiscas = K.Faiscas(n_max=140)
        cam.add_widget(K.RastroLamina(k, faiscas))
        cam.add_widget(k)
        cam.add_widget(faiscas)
        bx0, by0, bx1, by1 = _limites()
        area = (bx0, by0, bx1, by1)
        cx = (bx0 + bx1) / 2.0
        P = K.POSE_A
        topo = max((y + hh for _, _, y, _, hh in vis), default=H * 0.6)
        k.mostrar(_com(P['guardado'], olhos='s'))
        ini = _no_quadro(k, cx, topo + dp(10), [P['guardado'], P['pega2'], P['saca2'], P['dupla']],
                         area, dp(4))
        k.ancorar(*ini)
        k.precarregar([P[n] for n in P])
        _precarregar_sons(['sacar', 'corte', 'corte2', 'titulo', 'pulo', 'teleporte', 'fala_ikuzo',
                           'fala_kurae', 'kiai_seiya'] + _GEMIDOS)
        # STARBURST STREAM: um golpe por coisa da tela, alternando as espadas
        # (so uma lamina se mexe por golpe); cada uma vira cacos no seu golpe
        # (preparo, corte, espada, arco do rastro, angulo do talho)
        padroes = [('sb1_a', 'sb1_b', 1, (150, -40), -40.0), ('sb2_a', 'sb2_b', 2, (215, 40), 40.0),
                   ('sb3_a', 'sb3_b', 1, (175, 0), 0.0), ('sb4_a', 'sb4_b', 2, (185, -5), 0.0)]
        n_vis = len(vis)

        def _angulo(j):
            talho = padroes[j % 4][4]
            return talho if j % 2 == 0 else 180 - talho

        # a conta pesada dos cacos (foto de cada item em blocos) e feita ANTES,
        # um item por quadro, enquanto ele saca as espadas: na hora do golpe os
        # cacos so soltam, sem tranco
        prontos = {}
        fila = [(w, _angulo(j)) for j, (w, _x, _y, _ww, _hh) in enumerate(vis)]
        if grafico is not None:
            fila.append((grafico, -25.0))

        def _prepara(dt):
            if not fila or camada[0] is None or camada[0].parent is None:
                return False
            w, ang = fila.pop(0)
            try:
                from efeitos import explodir_estilhacos
                prontos[w] = explodir_estilhacos(w, lambda: None, corte=ang, tremor=0, px=_PX[0] * 2,
                                                 abaixo_de=cam, adiar=True)
            except Exception as e:
                print(f"[wipe] preparar: {e}")
            return True
        Clock.schedule_interval(_prepara, 4 / 60.)

        def _desintegra(w, ang):
            from efeitos import explodir_estilhacos
            try:
                solta = prontos.pop(w, None)
                if solta is not None:
                    return solta()
                explodir_estilhacos(w, lambda: None, corte=ang, tremor=0, px=_PX[0] * 2, abaixo_de=cam)
            except Exception as e:
                print(f"[wipe] item: {e}")

        def _golpe(j):
            if j >= n_vis:
                _final()
                return
            w, x, y, ww, hh = vis[j]
            a, c_, qual, arco, talho = padroes[j % 4]
            lado = 1 if j % 2 == 0 else -1               # 1: ataca pela esquerda
            cor = CIANO if qual == 1 else AZUL
            arma, corta = P[a], P[c_]
            sm = K.smear(corta, arma['a1'] if qual == 1 else None, arma['a2'] if qual == 2 else None)
            cy = y + hh / 2.0
            k.espelhar = lado < 0
            alvo = _no_quadro(k, x + ww * (0.25 if lado > 0 else 0.75), cy, [arma, corta], area, dp(2))

            def _ataca():
                k.espelhar = lado < 0

                def _q(q):
                    if q != 1:
                        return
                    ccx = x + ww / 2.0
                    a0, a1 = arco if lado > 0 else (180 - arco[0], 180 - arco[1])
                    cam.add_widget(CorteMeiaLua(centro=(ccx, cy), raio=max(ww * 0.34, hh * 0.8), ang_ini=a0,
                                                ang_fim=a1, espessura=max(dp(18), hh * 0.9), achat=0.35, cor=cor,
                                                dur_cheio=3 / 30.0, dur_decai=4 / 30.0))
                    faiscas.estourar(ccx, cy, cor, n=7, forca=dp(170), tam=ps)
                    _som('corte2' if qual == 2 else 'corte')
                    if j % 3 == 0:
                        _gemido()                       # gemidinho a cada 3 golpes
                    k.impacto()
                    _estrela(cam, ccx, cy, ps, cor)
                    _tremer(6)
                    k.pausar(0.05)
                    _desintegra(w, talho if lado > 0 else 180 - talho)
                k.tocar(K.sequencia([(1, arma, 'segura'), (1, sm, 'segura'), (2, corta, 'segura'),
                                     (1, corta)]), on_quadro=_q, on_fim=lambda: _golpe(j + 1))
            k.parar()
            k.mostrar(arma)
            _mover(k, k.ancora(), alvo, 0.06, linear=True, fantasmas=1, cor_fantasma=cor, on_fim=_ataca)

        def _saca():
            _som('fala_ikuzo')
            seq = K.sequencia(_de_agora(k, 2, proxima=P['pega2']) +
                              [(2, _com(P['pega2'], olhos='s'), 'segura'),
                               (2, _com(P['pega2'], olhos='s'), 'out'),
                               (4, _com(P['saca2'], olhos='s'), 'mola'),
                               (2, _com(P['dupla'], olhos='s'), 'segura'),
                               (28, _com(P['dupla'], olhos='s'), 'segura'),
                               (9, _com(P['dupla'], olhos='l'), 'segura'),
                               (1, _com(P['dupla'], olhos='l'))])

            def _q(i):
                if i == 6:
                    mx, my = k.ponto_mao(2)
                    faiscas.estourar(mx, my, AZUL, n=16, forca=dp(120), tam=ps)
                    _som('sacar')
                elif i == 40:                        # a fala "Saa, iku zo!" ja acabou
                    _som('fala_kurae')
                    k.empurrar(capa=-8, cabelo=-6)
            k.tocar(seq, on_quadro=_q, on_fim=lambda: _golpe(0))

        def _final():
            # golpe final: o X gigante em cima do grafico de barras do topo
            k.espelhar = False
            if grafico is not None:
                gx, gy, gw, gh = _ret_janela(grafico)
            else:
                gx, gy, gw, gh = bx0, (by0 + by1) / 2.0, bx1 - bx0, dp(80)
            gcx, gcy = gx + gw / 2.0, gy + gh / 2.0
            chaves_f, i_f = K.golpe(P['final_arma'], P['final'], n_arma=3, prende=3,
                                    segue=4, volta=7, graus=20.0)
            poses_f = K.sequencia(chaves_f)
            alvo = _no_quadro(k, gx + gw * 0.18, gcy, poses_f, area, dp(2))

            def _ataca():
                k.espelhar = False

                def _q(q):
                    if q == i_f:
                        for sent, cor in ((1, CIANO), (-1, AZUL)):
                            cam.add_widget(CorteMeiaLua(
                                centro=(gcx, gcy), raio=gw * 0.55, ang_ini=160 if sent > 0 else 20,
                                ang_fim=-45 if sent > 0 else 225, espessura=max(dp(50), gh * 0.9),
                                achat=0.5, rotacao=35 * sent, cor=cor, dur_cheio=5 / 30.0,
                                dur_decai=9 / 30.0))
                        faiscas.estourar(gcx, gcy, CIANO, n=60, forca=dp(380), tam=ps)
                        faiscas.estourar(gcx, gcy, BRANCO, n=24, forca=dp(260), tam=ps)
                        _estrela(cam, gcx, gcy, ps, CIANO, raios=8, dur=0.2)
                        _som('titulo')
                        _gemido()
                        _tremer(28)
                        k.impacto(forte=True)
                        k.pausar(0.14)
                        _quadro_impacto(cam, k, (gcx, gcy))
                        _brilho_tela(cam, 0.35, 0.3)
                        if grafico is not None:
                            _desintegra(grafico, -25.0)
                k.tocar(K.sequencia(chaves_f), on_quadro=_q, on_fim=_sai)
            k.parar()
            arma_f = poses_f[0]
            _mover(k, k.ancora(), alvo, 0.26, altura=dp(50), on_fim=_ataca,
                   on_passo=_voo(k, K.esticado(arma_f), K.encolhido(arma_f), arma_f, (0.2, 0.65)))

        def _sai():
            _teleporte(k, cam, faiscas, on_fim=_acabou, teto=by1 - dp(2))

        solto = [False]

        def _solta():
            if not solto[0]:
                solto[0] = True
                _yoru_solta()

        def _acabou():
            k.parar()
            _remover_da_janela(cam)
            _solta()
            fim()

        _materializar(k, cam, faiscas, dur=0.32, on_fim=_saca)

        def _seguranca(dt):
            _remover_da_janela(cam)
            _solta()
            fim()
        Clock.schedule_once(_seguranca, 14.0)
    except Exception as e:
        print(f"[wipe] ignorado: {e}")
        _remover_da_janela(camada[0])
        _yoru_solta()
        fim()
