"""
cenas.py — TraveteFocus
Cenas com o Kirito pixel art (kirito.py) + cortes em meia-lua (espadachim.py):

  cena_titulo(tela, label, on_fim)  o Yoru escreve "TRAVETE FOCUS" a golpes:
                                    cada silaba aparece por onde a luz de um
                                    corte passa (cada corte numa direcao). Vira
                                    Mugetsu, o corte final grava o CUS, guarda
                                    as duas espadas e fica em pose na frase.
  KiritoPin(caixa)                  espia por cima da caixa do PIN, com
                                    expressoes: pulinho nas teclas, susto no
                                    erro, balanca a cabeca no bloqueio e, no
                                    acerto, sobe na caixa e some num teleporte.
  kirito_fatiar(widget, on_fim)     mini Kirito se materializa, fatia o item
                                    que sera apagado e some num teleporte.
  kirito_wipe(widgets, on_fim)      versao epica: combo cortando a lista toda.

Tudo tolerante a falha: se algo der errado, on_fim ainda e chamado (a
historia do app nunca trava por causa de uma animacao).
"""
import math
import random
import time

from kivy.uix.widget import Widget
from kivy.uix.stencilview import StencilView
from kivy.graphics import (Color, Rectangle, Line, Mesh, PushMatrix, PopMatrix,
                           Scale, Translate, Rotate, InstructionGroup)
from kivy.graphics.texture import Texture
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import dp

import kirito as K

CIANO = (0.0, 0.9, 1.0)
AZUL = (0.35, 0.65, 1.0)        # rastro da Dark Repulser
POEIRA = (0.55, 0.62, 0.75)
BRANCO = (1.0, 1.0, 1.0)
ROXO = (0.66, 0.34, 1.0)        # chamas da forma Mugetsu

# efeitos que as cenas tocam (pre-carregados no inicio de cada cena)
_SONS_TITULO = ['agarra', 'koiguchi', 'pulo', 'pouso', 'sacar_iai', 'corte', 'sacar',
                'corte2', 'habilidade', 'voz_starburst', 'voz_stream', 'fusao', 'reiatsu',
                'absorve', 'carga', 'getsuga', 'separa', 'desliza', 'embainhar', 'titulo',
                'teleporte', 'golpe_final', 'voz_ha', 'voz_seiya', 'voz_teya', 'voz_mugetsu',
                'giro', 'fitas', 'cristal', 'vidro', 'fogo', 'trevas']
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


def _giro(k, a, b, fim, trocas=4):
    """on_passo para um giro no ar: alterna as duas poses de laminas abertas
    (parece uma roda de espadas girando) e abre na pose `fim` no final."""
    atual = [None]

    def _f(u):
        if u >= 0.8:
            p = fim
        else:
            p = a if int(u / 0.8 * trocas) % 2 == 0 else b
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


def _mover(k, de, para, dur, altura=0.0, rot=None, fantasmas=3,
           cor_fantasma=CIANO, on_fim=None, linear=False, cada=None, on_passo=None,
           ease=None, limite=None):
    """Move a ancora do Kirito em arco (parabola de `altura`), girando de
    rot[0] a rot[1]. Deixa `fantasmas` copias nitidas espalhadas pelo
    caminho (uma por quadro embolava num rastro de fumaca).
    ease: 'out' (desacelera), 'in' (acelera, queda) ou 'linear'.
    limite=(area, folga): o boneco (girado como estiver) nunca sai da area.
    on_passo(u) e chamado a cada quadro com o progresso 0..1."""
    t = [0.0]
    feito = [False]
    n_f = 3 if fantasmas is True else int(fantasmas or 0)
    marcas = [(i + 1) / float(n_f + 1) for i in range(n_f)]
    if ease is None:
        ease = 'linear' if linear else ('out' if altura >= 0 else 'in')

    def _acabar():
        if not feito[0]:
            feito[0] = True
            if on_fim:
                on_fim()

    def _p(dt):
        try:
            if getattr(k, '_pausa', 0) > 0:
                return True          # hit-stop: o corpo congela junto com a pose
            t[0] += dt
            u = min(1.0, t[0] / dur)
            if on_passo:
                on_passo(u)          # troca a pose antes de enquadrar (sem 1 quadro de atraso)
            if ease == 'linear':
                e = u
            elif ease == 'in':
                e = u * u
            else:
                e = 1 - (1 - u) ** 2
            x = de[0] + (para[0] - de[0]) * e
            y = de[1] + (para[1] - de[1]) * e + altura * 4 * u * (1 - u)
            if rot is not None:
                k.rotacao = rot[0] + (rot[1] - rot[0]) * e
            if limite is not None:
                x, y = _dentro_girado(k, x, y, limite[0], limite[1])
            k.ancorar(x, y)
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


def _raio(k, poses):
    """Maior distancia da ancora ate um canto das poses (para giros)."""
    r = 0.0
    for p in poses:
        esq, baixo, dir_, cima = k.extensao(p)
        r = max(r, math.hypot(max(esq, dir_), max(baixo, cima)))
    return r


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


def _brilho_tela(camada, alfa=0.35, dur=0.18, cor=BRANCO):
    """Clarao na tela inteira (impacto)."""
    try:
        W, H = camada.size
        w = Widget(size_hint=(None, None), size=(0, 0))
        with w.canvas:
            c = Color(cor[0], cor[1], cor[2], alfa)
            Rectangle(pos=(-W, -H), size=(W * 3, H * 3))
        camada.add_widget(w)
        t = [0.0]

        def _p(dt):
            t[0] += dt
            c.a = alfa * max(0.0, 1 - t[0] / dur)
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

    def __init__(self, cores, dur, desenha, on_fim=None, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.u = max(1.0, _PX[0])
        self.dur = dur
        self.t = 0.0
        self._desenha = desenha
        self._on_fim = _Uma(on_fim)
        self._lote = K.LotePixels(self.canvas, cores)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            self.t += dt
            if self.t >= self.dur or self.parent is None:
                return self.parar()
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
        super().__init__(_cores_efeito(cor, 0.45), dur_cheio + dur_decai, self._forma, on_fim, **kwargs)

    def _forma(self, t, p, u):
        if t < self.dc:
            s0, s1, gros, rala = 0.0, min(1.0, t / (1.3 / 30.0)), 1.0, 0.0
        else:
            k = min(1.0, (t - self.dc) / self.dd)
            s0, s1, gros, rala = 0.15 + 0.55 * k, 1.0, (1 - k) ** 1.4, 0.75 * k
        cx, cy = self.c
        arco = abs(self.a1 - self.a0) * self.r * (s1 - s0)
        n = max(6, int(arco / u) + 1)
        vistos = set()
        for i in range(n + 1):
            s = s0 + (s1 - s0) * i / float(n)
            g = self.e * (math.sin(math.pi * s) ** 0.75) * (0.45 + 0.55 * s) * gros
            if g < u * 0.6:
                continue
            a = self.a0 + (self.a1 - self.a0) * s
            ca, sa = math.cos(a), math.sin(a) * self.achat
            ext = self.r + g * 0.1 + u
            nr = int(g / u) + 2
            for j in range(nr):
                rad = ext - j * u
                xe, ye = ca * rad, sa * rad
                gx = math.floor((cx + xe * self.cr - ye * self.sr) / u)
                gy = math.floor((cy + xe * self.sr + ye * self.cr) / u)
                if (gx, gy) in vistos:
                    continue
                vistos.add((gx, gy))
                if rala and ((gx * 7 + gy * 13) % 10) / 10.0 < rala:
                    continue
                if j == 0 or j == nr - 1:
                    nome = 'brilho'
                elif j <= max(1, nr // 5):
                    nome = 'luz'
                elif j <= max(2, nr // 3):
                    nome = 'clara'
                else:
                    nome = 'cor' if s > 0.25 else 'brilho'
                p.setdefault(nome, []).append((gx * u, gy * u, u, u))


def _anel(camada, centro, r0, r1, dur, cor=CIANO, esp=None, achat=1.0):
    """Onda de choque em pixels: anel que abre (desacelerando), afina e some
    ralando em xadrez."""
    try:
        cx, cy = centro
        e0 = esp or dp(3)

        def forma(t, p, u):
            k = min(1.0, t / dur)
            e = 1 - (1 - k) ** 3
            r = r0 + (r1 - r0) * e
            g = max(u, e0 * 1.4 * (1 - k))
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


def _risco_luz(camada, x0, x1, y, dur, cor=CIANO, espessura=None):
    """Risco reto de luz em pixels que cresce de x0 ate x1 em `dur` e
    depois afina e some."""
    esp = espessura or dp(3)

    def forma(t, p, u):
        k = min(1.0, t / dur)
        xa = x0 + (x1 - x0) * k
        some = max(0.0, (t - dur) / 0.55)
        g = max(1, int(round(esp / u * (1 - some))))
        lo, hi = min(x0, xa), max(x0, xa)
        gy = math.floor(y / u) * u
        w = math.floor(hi / u) * u - math.floor(lo / u) * u + u
        xl = math.floor(lo / u) * u
        p.setdefault('brilho', []).append((xl, gy - (g + 1) * u, w, (2 * g + 3) * u))
        p.setdefault('luz', []).append((xl, gy - (g // 2) * u, w, g * u))
    camada.add_widget(_EfeitoPixel(_cores_efeito(cor, 0.45), dur + 0.55, forma))


def _clarao_boneco(k, dur=0.3, de=1.0):
    """O boneco fica branco e volta a cor (fusao das espadas)."""
    t = [0.0]

    def _p(dt):
        try:
            t[0] += dt
            k.clarao = de * max(0.0, 1 - t[0] / dur)
            return t[0] < dur
        except Exception:
            return False
    Clock.schedule_interval(_p, 1 / 60.)


_TEX_COLUNA = None


def _textura_coluna():
    """Coluna de luz: forte embaixo, somindo para cima e para os lados."""
    global _TEX_COLUNA
    if _TEX_COLUNA is None:
        w, h = 16, 64
        buf = bytearray(w * h * 4)
        for y in range(h):
            fy = (1 - y / (h - 1.0)) ** 1.4
            for x in range(w):
                fx = max(0.0, 1 - abs(x - (w - 1) / 2.0) / (w / 2.0)) ** 1.3
                i = (y * w + x) * 4
                buf[i] = buf[i + 1] = buf[i + 2] = 255
                a = fx * fy
                buf[i + 3] = 255 if a > 0.6 else (150 if a > 0.3 else (60 if a > 0.1 else 0))
        dados = bytes(buf)
        tex = Texture.create(size=(w, h), colorfmt='rgba')
        tex.mag_filter = 'nearest'
        tex.min_filter = 'nearest'
        tex.wrap = 'clamp_to_edge'
        tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
        tex.add_reload_observer(
            lambda t: t.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte'))
        _TEX_COLUNA = tex
    return _TEX_COLUNA


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


def _teleporte(k, camada, faiscas, on_fim=None, cor=CIANO, dur=0.55, teto=None):
    """Como o cristal de teleporte de SAO, em pixel art: anel de luz nos pes,
    o boneco fica branco, afina, se estica para cima e se desfaz em faiscas
    numa coluna de luz de pixels. Nao sai do lugar (fica dentro do quadro)."""
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
                nome = 'luz' if d < 0.22 else ('clara' if d < 0.45 else ('cor' if d < 0.7 else 'brilho'))
                if nome in ('brilho', 'cor') or f < 0.7:
                    for gy in range(y0, yt + 1):       # borda (ou coluna sumindo) em xadrez
                        if (gx + gy) % 2 == 0 and ((gx * 5 + gy * 9) % 10) / 10.0 < f:
                            p.setdefault(nome, []).append((gx * u, gy * u, u, u))
                else:
                    p.setdefault(nome, []).append((gx * u, y0 * u, u, (yt - y0 + 1) * u))
        camada.add_widget(_EfeitoPixel(_cores_efeito(cor, 0.5), dur, forma))
        _som('teleporte')
        t = [0.0]
        cont = [0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur)
                cont[0] += 1
                k.clarao = min(1.0, u / 0.25)
                if u > 0.25:
                    v = (u - 0.25) / 0.75
                    k.escala_x = max(0.04, 1 - v)
                    k.escala_y = 1 + 0.6 * v
                    k.opacity = max(0.0, 1 - v * 1.15)
                if cont[0] % 3 == 0 and u < 0.85:
                    faiscas.estourar(ax + random.uniform(-larg * 0.4, larg * 0.4),
                                     base + random.uniform(0, (baixo + cima) * 0.9),
                                     random.choice((cor, BRANCO)), n=2,
                                     forca=dp(30), tam=max(2, k.ps * 0.8), gravidade=-dp(260))
                if u >= 1:
                    k.opacity = 0
                    fim()
                    return False
            except Exception as e:
                print(f"[cena] teleporte: {e}")
                fim()
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[cena] teleporte ignorado: {e}")
        fim()


def _materializar(k, camada, faiscas, dur=0.32, on_fim=None, cor=CIANO):
    """Entrada de teleporte (o contrario do _teleporte): um anel de pixels se
    fecha, faiscas caem para o boneco e ele aparece branco, ganhando cor."""
    fim = _Uma(on_fim)
    try:
        ax, ay = k.ancora()
        esq, baixo, dir_, cima = k.extensao()
        r = max(esq + dir_, baixo + cima) * 0.7
        k.opacity = 0
        k.clarao = 1.0
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
                    p.setdefault('brilho', []).append((gx2 * u, gy2 * u, u, u))
        camada.add_widget(_EfeitoPixel(_cores_efeito(cor, 0.5), dur, forma))
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur)
                rr = max(1.0, r * (1 - u))
                k.opacity = min(1.0, u * 2.2)
                k.clarao = 1.0 - u
                if random.random() < 0.6:
                    ang = random.uniform(0, 2 * math.pi)
                    faiscas.estourar(ax + math.cos(ang) * rr, ay + math.sin(ang) * rr,
                                     random.choice((cor, BRANCO)), n=1, forca=dp(20),
                                     tam=max(2, k.ps * 0.7), gravidade=0)
                if u >= 1:
                    k.clarao = 0.0
                    k.opacity = 1.0
                    faiscas.estourar(ax, ay, cor, n=10, forca=dp(90), tam=max(2, k.ps * 0.8))
                    fim()
                    return False
            except Exception as e:
                print(f"[cena] materializar: {e}")
                k.opacity = 1.0
                k.clarao = 0.0
                fim()
                return False
        Clock.schedule_interval(_p, 1 / 60.)
    except Exception as e:
        print(f"[cena] materializar ignorado: {e}")
        k.opacity = 1.0
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


class _Fluxo(Widget):
    """Fios de luz arrancados do infinito e sugados em espiral para a ponta
    da espada (o reiatsu da tela)."""
    _N = 110

    def __init__(self, reator, alvo_fn, dur, px_tam=None, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        # fios na escala do Kirito (nao mais grossos que os pixels dele)
        self._larg = max(1.0, px_tam * 0.5) if px_tam else dp(1.5)
        self._comp_max = px_tam * 5 if px_tam else dp(30)
        self.reator = reator
        self.alvo_fn = alvo_fn
        self._dur = dur
        self._t = 0.0
        self._acum = 0.0
        self._p = []
        self._ins = []
        with self.canvas:
            for _ in range(self._N):
                c = Color(1, 1, 1, 0)
                ln = Line(points=[0, 0, 0, 0], width=self._larg, cap='none')
                self._ins.append((c, ln))
        self._livres = list(range(self._N))
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            self._t += dt
            u = self._t / self._dur
            ax, ay = self.alvo_fn()
            pts = getattr(self.reator, 'pontos_atuais', None) or []
            cor = tuple(getattr(self.reator, '_cor', CIANO))
            taxa = 90 * math.sin(math.pi * min(1.0, max(0.0, u)))
            self._acum += dt * taxa
            while self._acum >= 1 and self._livres and pts and u < 1:
                self._acum -= 1
                x, y = random.choice(pts)
                i = self._livres.pop()
                mistura = random.random() * 0.6
                c = tuple(cor[j] + (1 - cor[j]) * mistura for j in range(3))
                self._p.append([x, y, 0.0, 0.0, c, i, 0.0])
            vivas = []
            # o giro diminui com o tempo: a espiral fecha e tudo cai na ponta
            # (com giro constante alguns fios ficavam orbitando para sempre)
            giro = 0.45 * max(0.0, 1.0 - u)
            acc = dp(2400) * (1.0 if u < 1 else 3.0)
            for q in self._p:
                q[6] += dt
                dx, dy = ax - q[0], ay - q[1]
                d = math.hypot(dx, dy) or 1.0
                c, ln = self._ins[q[5]]
                if d < dp(10) or q[6] > 1.4 or u > 1.35:
                    c.a = 0
                    ln.points = [0, 0, 0, 0]
                    self._livres.append(q[5])
                    continue
                q[2] += (dx / d - dy / d * giro) * acc * dt
                q[3] += (dy / d + dx / d * giro) * acc * dt
                q[2] *= 0.93
                q[3] *= 0.93
                q[0] += q[2] * dt
                q[1] += q[3] * dt
                vn = math.hypot(q[2], q[3]) or 1.0
                comp = min(self._comp_max, vn * 0.035)
                ln.points = [q[0], q[1], q[0] - q[2] / vn * comp, q[1] - q[3] / vn * comp]
                c.rgba = (q[4][0], q[4][1], q[4][2], 0.9 * min(1.0, (1.4 - q[6]) / 0.3))
                vivas.append(q)
            self._p = vivas
            if u >= 1.0 and not vivas:
                self.parar()
                return False
        except Exception as e:
            print(f"[fluxo] {e}")
            self.parar()
            return False

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)


class _Crisalida:
    """Transformacao: crisalida de energia. Fitas roxas (borda escura, corpo
    roxo, linha clara no meio, cabeca branca) sobem em espiral de um anel no
    chao, apertam em volta dele (a silhueta e os olhos acesos aparecem por
    dentro), a casca endurece num cristal roxo escuro com facetas, rachaduras
    de luz se espalham a partir do peito e tudo estoura em cacos que se
    desfazem em fogo roxo. Pixels na grade do Yoru. Duas camadas (atras e
    na frente dele). on_estouro() e chamado no estouro."""
    CORES = (('fundo', (0.20, 0.07, 0.38, 0.85)), ('borda', (0.30, 0.10, 0.58, 0.95)),
             ('fita', (0.55, 0.25, 0.95, 0.95)), ('miolo', (0.86, 0.70, 1.0, 1.0)),
             ('ponta', (1.0, 0.97, 1.0, 1.0)), ('cristal', (0.11, 0.045, 0.20, 1.0)),
             ('faceta', (0.24, 0.11, 0.42, 1.0)), ('aresta', (0.60, 0.38, 0.94, 1.0)),
             ('halo', (0.66, 0.40, 1.0, 0.85)), ('racha', (0.99, 0.95, 1.0, 1.0)),
             ('olho2', (0.62, 0.30, 1.0, 0.75)), ('olho', (0.95, 0.80, 1.0, 1.0)))
    T_APERTA, T_CRISTAL, T_RACHA = 0.5, 0.95, 1.3

    def __init__(self, k, camada, faiscas, on_estouro=None):
        self.k = k
        self.faiscas = faiscas
        self.on_estouro = on_estouro
        self.t = 0.0
        self.pedacos = None
        self.t_voo = 0.0
        self._rachas = None
        self._facetas = None
        self.w_tras = Widget(size_hint=(None, None), size=(0, 0))
        self.w_frente = Widget(size_hint=(None, None), size=(0, 0))
        self.l_tras = K.LotePixels(self.w_tras.canvas, self.CORES)
        self.l_frente = K.LotePixels(self.w_frente.canvas, self.CORES)
        i = camada.children.index(k) if k in camada.children else 0
        camada.add_widget(self.w_frente, index=i)          # na frente dele
        camada.add_widget(self.w_tras, index=i + 2)        # atras dele
        self._ev = Clock.schedule_interval(self._tick, 1 / 30.)

    # ── geometria (em texels, relativa ao canto do quadro do Yoru) ──────
    def _geo(self):
        k = self.k
        te = k.ps / float(K.R)
        p = k._base
        cx = (k.ancora()[0] - k.x) / te
        yb = (K._PES - 0.5) * K.R
        yt = (K._PES + K.altura(p) + len(K._TRONCO) + len(K._CABECA) + 1.0) * K.R
        return te, cx, yb, yt, 9.2 * K.R

    @staticmethod
    def _raio(u, rx):
        u = min(1.0, max(0.0, u))
        return rx * (0.30 + 0.70 * math.sin(math.pi * u) ** 0.55)

    def _tick(self, dt):
        try:
            if self.w_frente.parent is None:
                return self.parar()
            self.t += dt
            te, cx, yb, yt, rx = self._geo()
            ox, oy = self.k.x, self.k.y
            frente, tras = {}, {}

            def rt(cor, x, y, w=1, h=1, alvo=frente):
                alvo.setdefault(cor, []).append((ox + x * te, oy + y * te, w * te, h * te))

            if self.pedacos is not None:
                self._voar(dt, rt, te)
                self.l_frente.desenhar(frente, max(0.0, 1.0 - max(0.0, self.t_voo - 0.35) / 0.4))
                self.l_tras.desenhar({})
                if self.t_voo > 0.8:
                    return self.parar()
                return
            t = self.t
            alt = yt - yb
            aperta = max(0.0, min(1.0, (t - self.T_APERTA * 0.9) / 0.45))
            aperta = aperta * aperta * (3 - 2 * aperta)
            casca = max(0.0, min(1.0, (t - self.T_APERTA) / (self.T_CRISTAL - self.T_APERTA)))
            # anel no chao de onde as fitas nascem
            if casca < 1.0:
                pulso = 0.5 + 0.5 * math.sin(t * 20)
                ra = rx * (1.35 - 0.2 * aperta)
                for i in range(int(ra * 2) + 1):
                    x = int(round(cx - ra + i))
                    v = (x - cx) / ra
                    dy = int(round(2.2 * math.sqrt(max(0.0, 1 - v * v))))
                    cor = 'miolo' if (i + int(t * 30)) % 7 == 0 else ('fita' if pulso > 0.3 else 'borda')
                    rt(cor, x, int(yb) + dy)
                    rt('borda', x, int(yb) - dy, alvo=tras)
            # fitas em espiral
            if t < self.T_CRISTAL + 0.12:
                n = 5
                voltas = 1.15 + 1.35 * aperta
                rm = 1.25 - 0.27 * aperta
                meia = 1 + int(round(aperta * 1.5))                   # a fita engrossa
                some = max(0.0, (t - self.T_CRISTAL + 0.1) / 0.22)   # entra na casca
                for i in range(n):
                    h = max(0.0, min(1.0, (t - 0.045 * i) / 0.42))
                    h = 1 - (1 - h) ** 2
                    if h <= 0:
                        continue
                    th0 = 2 * math.pi * i / n
                    arco = alt * h + 2 * math.pi * voltas * rx * rm * h
                    npts = int(arco / 1.5) + 2
                    vistos = set()
                    for s in range(npts):
                        u = h * s / float(npts - 1)
                        ang = th0 + 2 * math.pi * voltas * u + t * 6.0
                        prof = math.sin(ang)
                        x = int(round(cx + self._raio(u, rx) * rm * math.cos(ang)))
                        y = int(round(yb + alt * u))
                        if (x, y) in vistos:
                            continue
                        vistos.add((x, y))
                        if some > 0 and ((x * 7 + y * 3) % 10) / 10.0 < some:
                            continue
                        if prof <= 0:
                            rt('fundo', x, y - meia, 1, 2 * meia + 1, tras)
                            continue
                        if u > h - 0.035:
                            rt('ponta', x - 1, y - 1, 3, 3)
                            continue
                        rt('borda', x, y - meia, 1, 2 * meia + 1)
                        if meia >= 1:
                            rt('fita', x, y - meia + 1, 1, 2 * meia - 1)
                        rt('miolo' if prof > 0.35 else 'fita', x, y)
                    if h >= 1 and int(t * 30) % 4 == i % 4:          # faisca da cabeca da fita
                        ang = th0 + 2 * math.pi * voltas + t * 6.0
                        fx = ox + (cx + self._raio(1.0, rx) * rm * math.cos(ang)) * te
                        self.faiscas.estourar(fx, oy + yt * te, (0.85, 0.7, 1.0), n=1, forca=dp(30),
                                              tam=te * 2, gravidade=-dp(80))
            # casca de cristal: cresce de baixo para cima e endurece
            if casca > 0:
                topo_c = yb + alt * min(1.0, casca * 1.08)
                facetas = self._facetas_de(cx, yb, yt, rx)
                y = int(yb)
                while y <= int(topo_c):
                    u = (y - yb) / alt
                    r = self._raio(u, rx)
                    x0, x1 = int(round(cx - r)), int(round(cx + r))
                    rt('cristal', x0, y, x1 - x0 + 1, 1)
                    rt('aresta', x0, y)                              # luz do lado de tras
                    rt('faceta', x1, y)
                    y += 1
                for (x, y) in facetas:
                    if y <= topo_c:
                        rt('faceta', x, y)
                # brilho que desce pela casca enquanto ela endurece
                if casca >= 1.0 and t < self.T_CRISTAL + 0.25:
                    yv = yt - (t - self.T_CRISTAL) / 0.25 * alt
                    for d in range(-2, 3):
                        yy = int(yv + d)
                        u = (yy - yb) / alt
                        if 0 <= u <= 1:
                            r = self._raio(u, rx)
                            rt('aresta' if d else 'miolo', int(round(cx - r)) + 1, yy, int(2 * r) - 1, 1)
            # rachaduras de luz
            if t >= self.T_CRISTAL and not getattr(self, '_trincou', False):
                self._trincou = True
                _som('cristal')
            if t >= self.T_CRISTAL:
                p = min(1.0, (t - self.T_CRISTAL) / (self.T_RACHA - self.T_CRISTAL))
                for caminho in self._rachas_de(cx, yb, yt, rx):
                    m = int(len(caminho) * p)
                    for (x, y) in caminho[:m]:
                        rt('halo', x - 1, y, 3, 1)
                    for (x, y) in caminho[:m]:
                        rt('racha', x, y)
            # os olhos acesos aparecem por dentro
            if 0.3 < t:
                pisca = 0.6 + 0.4 * math.sin(t * 14)
                for (ex, ey) in K.olhos_texel(self.k._pose):
                    if self.k.espelhar:
                        ex = K.TW - 1 - ex
                    ex, ey = int(round(ex)), int(round(ey))
                    if pisca > 0.4:
                        rt('olho2', ex - 2, ey - 1, 5, 3)
                    rt('olho', ex - 1, ey, 3, 1)
            self.l_frente.desenhar(frente)
            self.l_tras.desenhar(tras)
            if t >= self.T_RACHA:
                self._estourar(cx, yb, yt, rx)
        except Exception as e:
            print(f"[crisalida] {e}")
            return self.parar()

    def _facetas_de(self, cx, yb, yt, rx):
        """Arestas do cristal: linhas que descem do topo em leque."""
        if self._facetas is None:
            pts = set()
            alt = yt - yb
            for a in (-0.75, -0.35, 0.05, 0.45, 0.8):
                for i in range(int(alt)):
                    y = yt - i
                    u = (y - yb) / alt
                    r = self._raio(u, rx)
                    x = cx + a * r * (0.4 + 0.6 * i / alt)
                    if abs(x - cx) < r - 1:
                        pts.add((int(round(x)), int(round(y))))
            self._facetas = list(pts)
        return self._facetas

    def _rachas_de(self, cx, yb, yt, rx):
        """Rachaduras: caminhos que saem do peito e andam para fora, se
        dividindo, ate a borda da casca."""
        if self._rachas is None:
            rnd = random.Random(7)
            alt = yt - yb
            y0 = yb + alt * 0.6
            caminhos = []
            fila = [(cx, y0, a) for a in [i * 2 * math.pi / 7 + rnd.uniform(-0.3, 0.3) for i in range(7)]]
            while fila and len(caminhos) < 14:
                x, y, a = fila.pop(0)
                c = []
                for _ in range(60):
                    a += rnd.uniform(-0.45, 0.45)
                    x += math.cos(a) * 1.4
                    y += math.sin(a) * 1.4
                    u = (y - yb) / alt
                    if not (0 <= u <= 1) or abs(x - cx) > self._raio(u, rx):
                        break
                    c.append((int(round(x)), int(round(y))))
                    if len(c) in (9, 20) and rnd.random() < 0.6:
                        fila.append((x, y, a + rnd.choice((-0.9, 0.9))))
                if c:
                    caminhos.append(c)
            self._rachas = caminhos
        return self._rachas

    def _estourar(self, cx, yb, yt, rx):
        """A casca estoura em cacos (setores em volta do peito) que voam e
        se desfazem em fogo."""
        alt = yt - yb
        y0 = yb + alt * 0.6
        grupos = {}
        for y in range(int(yb), int(yt) + 1):
            u = (y - yb) / alt
            r = self._raio(u, rx)
            if y % 2:
                continue
            for x in range(int(round(cx - r)), int(round(cx + r)) + 1, 2):
                a = math.atan2(y - y0, x - cx)
                d = math.hypot(x - cx, (y - y0) * 0.6)
                chave = (int((a + math.pi) / (2 * math.pi) * 10) % 10, 0 if d < rx * 0.55 else 1)
                grupos.setdefault(chave, []).append((x, y))
        self.pedacos = []
        for cel in grupos.values():
            mx = sum(c[0] for c in cel) / float(len(cel))
            my = sum(c[1] for c in cel) / float(len(cel))
            d = math.hypot(mx - cx, my - y0) or 1.0
            vel = random.uniform(70, 130)                            # texels por segundo
            self.pedacos.append({'cel': cel, 'x': 0.0, 'y': 0.0, 'vx': (mx - cx) / d * vel,
                                 'vy': (my - y0) / d * vel + 30, 'mx': mx, 'my': my})
        self.t_voo = 0.0
        if self.on_estouro is not None:
            try:
                self.on_estouro()
            except Exception as e:
                print(f"[crisalida] estouro: {e}")

    def _voar(self, dt, rt, te):
        """Cacos voando: primeiro cristal com a aresta acesa, depois viram
        roxo aceso e se desfazem em pontos de fogo."""
        self.t_voo += dt
        tv = self.t_voo
        for pd in self.pedacos:
            pd['x'] += pd['vx'] * dt
            pd['y'] += pd['vy'] * dt
            pd['vy'] -= 160 * dt
            pd['vx'] *= 0.97
            dx, dy = int(round(pd['x'])), int(round(pd['y']))
            queima = tv / 0.55                                       # 0..1: vira fogo
            for (x, y) in pd['cel']:
                h = ((x * 13 + y * 7) % 17) / 17.0
                if h < queima * 1.1 - 0.1:
                    continue                                          # ja se desfez
                if queima < 0.3:
                    cor = 'aresta' if h > 0.85 else 'cristal'
                elif queima < 0.6:
                    cor = 'fita' if h > 0.5 else 'faceta'
                else:
                    cor = 'miolo' if h > 0.8 else 'fita'
                rt(cor, x + dx, y + dy, 2, 2)
            if random.random() < 0.25 and tv < 0.5:
                k = self.k
                self.faiscas.estourar(k.x + (pd['mx'] + dx) * te, k.y + (pd['my'] + dy) * te,
                                      random.choice(((0.62, 0.30, 1.0), (0.86, 0.72, 1.0))), n=1,
                                      forca=dp(40), tam=te * 2, gravidade=-dp(120))

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        for w in (self.w_frente, self.w_tras):
            if w.parent is not None:
                w.parent.remove_widget(w)
        return False


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
        self._ev = None

    def pedir(self, chave, arco, pal='katana'):
        self._fila.append((chave, _desenho_corte(arco, _PAL_CORTE[pal], self.u)))
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._passo, 0)

    def _fechar(self, chave, res):
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


def _pendurado_idle(base, base_b, piscar=True):
    """Pernas balancando devagar: vao e voltam passando por um quadro do
    meio (solto, nao duro), com uma piscada."""
    meio = dict(base, pernas='solto_meio')
    quadros = []
    for f in range(64):
        if 18 <= f < 22 or 34 <= f < 38:
            q = dict(meio)
        elif 22 <= f < 34:
            q = dict(base_b)
        else:
            q = dict(base)
        if piscar and f in (50, 51):
            q['olhos'] = 'f'
        quadros.append(q)
    return quadros


class _NomeGolpe(Widget):
    """Nome da habilidade no estilo SAO: '- DUAL BLADES -' pequeno em cima e
    'STARBURST STREAM' grande, com brilho e linhas saindo dos lados.
    parte1(): 'STARBURST' aparece letra a letra; parte2(): 'STREAM' chega
    num impacto; sumir(): apaga tudo."""

    def __init__(self, cx, cy, largura_max, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        from kivy.metrics import sp
        # a Orbitron e larga: mede de verdade e encolhe ate caber (sobra
        # espaco nos lados para as linhas), senao corta em tela pequena
        fs = max(sp(12), min(sp(26), largura_max / 12.0))
        cabe = largura_max * 0.8
        for tentativa in range(3):
            t1 = CoreLabel(text="STARBURST", font_name="orbitron.ttf", font_size=fs, bold=True)
            t1.refresh()
            t2 = CoreLabel(text="STREAM", font_name="orbitron.ttf", font_size=fs, bold=True)
            t2.refresh()
            largura = t1.texture.width + fs * 0.55 + t2.texture.width
            if largura <= cabe or tentativa == 2:
                break
            fs = max(sp(9), fs * cabe / largura * 0.98)
        t0 = CoreLabel(text="-  DUAL BLADES  -", font_name="orbitron.ttf", font_size=max(sp(7), fs * 0.42))
        t0.refresh()
        self._tex1, self._tex2, self._tex0 = t1.texture, t2.texture, t0.texture
        w1, h1 = self._tex1.size
        w2, h2 = self._tex2.size
        esp = fs * 0.55
        total = w1 + esp + w2
        self._x1 = cx - total / 2.0
        self._x2 = self._x1 + w1 + esp
        self._y = cy - h1 / 2.0
        self._cx, self._cy, self._h = cx, cy, h1
        self._total = total
        with self.canvas:
            self._c_ln = Color(0.0, 0.9, 1.0, 0)
            self._ln_e = Line(points=[cx, cy, cx, cy], width=dp(1.3))
            self._ln_d = Line(points=[cx, cy, cx, cy], width=dp(1.3))
            self._c_sub = Color(0.6, 0.95, 1.0, 0)
            w0, h0 = self._tex0.size
            self._r_sub = Rectangle(texture=self._tex0, size=(w0, h0),
                                    pos=(cx - w0 / 2.0, self._y + h1 + dp(4)))
            # brilho (copia maior e ciano atras das letras)
            PushMatrix()
            self._sc_g = Scale(1.06, 1.18, 1, origin=(cx, cy))
            self._c_g1 = Color(0.0, 0.8, 1.0, 0)
            self._r_g1 = Rectangle(texture=self._tex1, size=(w1, h1), pos=(self._x1, self._y))
            self._c_g2 = Color(0.0, 0.8, 1.0, 0)
            self._r_g2 = Rectangle(texture=self._tex2, size=(w2, h2), pos=(self._x2, self._y))
            PopMatrix()
            self._c_1 = Color(1, 1, 1, 0)
            self._r_1 = Rectangle(texture=self._tex1, size=(0, h1), pos=(self._x1, self._y))
            PushMatrix()
            self._sc_2 = Scale(1, 1, 1, origin=(self._x2 + w2 / 2.0, cy))
            self._c_2 = Color(1, 1, 1, 0)
            self._r_2 = Rectangle(texture=self._tex2, size=(w2, h2), pos=(self._x2, self._y))
            PopMatrix()
        self._ev = None
        self._t1 = self._t2 = self._tsome = None
        self._t = 0.0

    def parte1(self):
        self._t1 = self._t
        self._ligar()

    def parte2(self):
        self._t2 = self._t
        self._ligar()

    def sumir(self):
        self._tsome = self._t
        self._ligar()

    def _ligar(self):
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            self._t += dt
            some = 1.0
            if self._tsome is not None:
                some = max(0.0, 1 - (self._t - self._tsome) / 0.45)
            w1, h1 = self._tex1.size
            if self._t1 is not None:
                u = min(1.0, (self._t - self._t1) / 0.55)
                w = max(1.0, w1 * u)
                self._r_1.texture = self._tex1.get_region(0, 0, w, h1)
                self._r_1.size = (w, h1)
                self._c_1.a = some
                self._c_g1.a = 0.35 * some * (0.8 + 0.2 * math.sin(self._t * 14))
                self._c_sub.a = 0.85 * min(1.0, u * 2) * some
                abre = min(1.0, (self._t - self._t1) / 0.35)
                meia = self._total / 2.0 + dp(10)
                alcance = meia + dp(34) * abre
                self._ln_e.points = [self._cx - meia, self._cy, self._cx - alcance, self._cy]
                self._ln_d.points = [self._cx + meia, self._cy, self._cx + alcance, self._cy]
                self._c_ln.a = 0.9 * abre * some
            if self._t2 is not None:
                u2 = min(1.0, (self._t - self._t2) / 0.16)
                s = 1.7 - 0.7 * (1 - (1 - u2) ** 3)
                self._sc_2.x = self._sc_2.y = s
                clarao = max(0.0, 1 - (self._t - self._t2) / 0.3)
                self._c_2.rgba = (1, 1, 1, min(1.0, u2 * 1.5) * some)
                self._c_g2.a = (0.35 + 0.5 * clarao) * some
                self._c_g1.a = (0.35 + 0.4 * clarao) * some
                self._sc_g.x = 1.06 + 0.08 * clarao
                self._sc_g.y = 1.18 + 0.25 * clarao
            if self._tsome is not None and some <= 0:
                self.parar()
                return False
        except Exception as e:
            print(f"[nome golpe] {e}")
            self.parar()
            return False

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)


def cena_titulo(tela, label, on_fim=None, texto="TRAVETE FOCUS"):
    """O Yoru entra num mortal e escreve a frase a golpes: a luz de cada
    corte atravessa uma silaba e as letras aparecem por onde ela passa (TRA
    na horizontal, VE subindo, TE descendo com as duas espadas, FO em X). No
    golpe final junta as duas espadas, suga o infinito da tela, vira o
    Mugetsu e um corte so grava o CUS. Separa as espadas, pousa na frase,
    guarda a azul nas costas e a katana na cintura - no clique da guarda a
    frase explode - e fica em pose (sem sair de cena)."""
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
        if cam[0] is not None:
            cam[0].soltar()
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
        fita_tras, fita_frente = K.FitaFogo(kk), K.FitaFogo(kk, frente=True)
        estado['fitas'] = (fita_tras, fita_frente)
        camada.add_widget(fita_tras)                     # fita de fogo do Mugetsu (atras)
        camada.add_widget(aura)
        camada.add_widget(K.RastroLamina(kk, faiscas))
        camada.add_widget(kk)
        camada.add_widget(fita_frente)                   # ... e a parte que passa na frente
        camada.add_widget(faiscas)
        cam[0] = _Camera(tela)
        try:
            estado['reator'] = tela.ids.get('reator_shader')
        except Exception:
            estado['reator'] = None
        alt = 24 * ps
        th = titulo.th
        m = max(dp(4), ps)                              # folga ate a borda do quadro
        P = K.POSE_A
        # Bankai (estilo Mugetsu): da fusao ate o golpe final ele fica na
        # sombra, envolto em chamas roxas e azuis, com o cabelo comprido
        M = {n: _com(P[n], mugetsu=True) for n in ('fund_alto', 'evo_alto', 'evo_carga',
                                                    'evo_corte', 'evo_fim')}
        kk.precarregar([P[n] for n in P] + list(M.values()))
        K.preparar_fita()                              # quadros da fita de fogo, aos poucos
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

        # ── 1-5. DANCA CORTANTE: O CORTE GRAVA A FRASE ──────────────
        # Cada silaba e escrita por UM corte, cada um numa direcao: a luz da
        # ponta da lamina atravessa as letras e elas aparecem exatamente por
        # onde ela passa. Ele fica virado para a frase, do lado das letras que
        # ainda nao existem, e recua um pouco a cada golpe (a frase vai
        # aparecendo da esquerda para a direita e nada fica escondido atras
        # dele). TRA (iai na horizontal) e VE (subindo na diagonal) so com a
        # katana; no alto do salto ele saca a espada azul das costas; TE
        # (descendo na diagonal, as duas laminas) e FO (tesoura em X). O CUS
        # fica para o corte do Mugetsu. Tudo numa corrente so, sem teleporte.
        ag.depois(0.25, lambda: _fundo(tela, reator=0.32, barra=0.2, dur=0.9))
        kk.espelhar = True
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

        def posicionar(chave, i, arma, corta, desl, esp, pal='katana', y_ini=None,
                       extra=None, alvo='meio'):
            """Acha onde ele comeca (a0) e termina (a1) o golpe para a luz do
            corte atravessar a silaba i. desl = quanto ele anda no golpe (em
            alturas de letra; x para a frente). alvo: 'meio' = o meio da luz
            cai no meio da silaba; 'cruza' = so anda de lado ate a luz cruzar
            a altura das letras no meio da silaba (y_ini = comeca no chao);
            'x' = as duas luzes se cruzam no meio da silaba. extra = (chave,
            qual, esp, pal) da segunda lamina, presa no mesmo corpo."""
            sx = -1.0 if kk.espelhar else 1.0
            dx, dy = desl[0] * th * sx, desl[1] * th
            cx, cy, _ = silaba(i)

            def arcos(a0, a1):
                a = arco_do_golpe(arma, corta, a0, a1, 1, esp)
                b = arco_do_golpe(arma, corta, a0, a1, extra[1], extra[2]) if extra else None
                return a, b

            def ponto_alvo(a, b):
                if alvo == 'x' and b is not None:
                    melhor = None
                    for s in range(26):
                        p = a.ponto(s / 25.0, -0.4 * a.esp)
                        for r in range(26):
                            q = b.ponto(r / 25.0, -0.4 * b.esp)
                            d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
                            if melhor is None or d < melhor[0]:
                                melhor = (d, ((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0))
                    return melhor[1]
                if alvo == 'cruza':
                    s = min((abs(a.ponto(k / 40.0, -0.4 * esp)[1] - cy), k / 40.0) for k in range(4, 37))[1]
                    return a.ponto(s, -0.4 * esp)[0], cy
                return a.ponto(0.5, -0.4 * esp)
            a0 = (0.0, y_ini if y_ini is not None else 0.0)
            for _ in range(3):
                mx, my = ponto_alvo(*arcos(a0, (a0[0] + dx, a0[1] + dy)))
                a0 = (a0[0] + cx - mx, y_ini if y_ini is not None else a0[1] + cy - my)
            a1 = (a0[0] + dx, a0[1] + dy)
            # nunca sai do quadro (se precisar, o golpe todo anda junto)
            b1 = quadro(a1[0], a1[1], [corta])
            ddx, ddy = b1[0] - a1[0], b1[1] - a1[1]
            a0, a1 = (a0[0] + ddx, a0[1] + ddy), b1
            b0 = quadro(a0[0], a0[1], [arma])
            ARCOS[chave] = (arco_do_golpe(arma, corta, b0, a1, 1, esp), pal)
            oficina.pedir(chave, ARCOS[chave][0], pal)
            if extra:
                ch2, q2, es2, pal2 = extra
                ARCOS[ch2] = (arco_do_golpe(arma, corta, b0, a1, q2, es2), pal2)
                oficina.pedir(ch2, ARCOS[ch2][0], pal2)
            return b0, a1

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

        def impacto_silaba(i, cor, forte=False):
            cx, cy, w = silaba(i)
            _estrela(camada, cx, cy, ps, cor)
            faiscas.estourar(cx, cy, cor, n=16 if forte else 10, forca=dp(180), tam=ps)
            _som('corte')
            _tremer(10 if forte else 6)
            _brilho_tela(camada, 0.10, 0.12)
            kk.impacto()
            kk.pausar(0.06)
            kk.empurrar(capa=14, cabelo=12)

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
        # onde ele fica em cada golpe (a luz de cada corte cruza a silaba)
        A0, A1 = posicionar('tra', 0, pronto, corta_tra, (1.1, 0.0), th * 1.0)
        y_chao = A0[1]                                   # o "chao" da danca, embaixo da frase
        B0, B1 = posicionar('ve', 1, arma_ve, corta_ve, (0.5, 1.3), th * 0.95, y_ini=y_chao,
                            alvo='cruza')
        C0, C1 = posicionar('te', 2, arma_te, corta_te, (0.9, -1.3), th * 0.95,
                            extra=('te2', 2, th * 0.75, 'azul'))
        Dm, D1 = posicionar('fo', 3, arma_fo, corta_fo, (0.5, -0.8), th * 0.9, alvo='x',
                            extra=('fo2', 2, th * 0.85, 'azul'))
        # depois do mergulho do TE ele continua embaixo: o FO e na altura em que o X termina
        D0 = quadro(Dm[0] + th * 0.9 * (1 if kk.espelhar else -1), D1[1], [prep_fo])     # atras dele
        # o do Mugetsu atravessa a frase inteira, de um lado ao outro da tela
        _, cy_t, _ = silaba(0)
        ARCOS['cus'] = (ArcoCorte.pelo_meio((ox_t + titulo.tw / 2.0, cy_t), 0, W * 1.02, -0.05,
                                            th * 1.35), 'mug')
        oficina.pedir('cus', ARCOS['cus'][0], 'mug')
        kk.precarregar([pronto, agacha, corta_tra, arma_ve, corta_ve, fim_ve, pega_az, saca_az,
                        arma_te, corta_te, arma_fo, corta_fo, prep_fo])

        def _voo_seq(p_ini, p_ar, p_fim, dur):
            """Poses de um salto com a duracao do voo: sai esticado, encolhe
            no alto e estica de novo para pousar - tudo interpolado."""
            n = max(6, int(round(dur * K.FPS)))
            a = max(2, int(n * 0.35))
            b = max(2, n - a)
            return K.sequencia([(a, p_ini, 'out'), (b, p_ar, 'suave'), (1, p_fim)])

        def _entra():
            # mergulho do canto de cima (do lado de la da frase) com um mortal
            p_pulo = _com(P['pulo'], olhos='s')
            ini = (A0[0] + th * 2.0, H + alt * 0.6)
            kk.ancorar(*ini)
            kk.opacity = 1
            kk.tocar(_voo_seq(K.esticado(p_pulo), K.encolhido(p_pulo), K.esticado(p_pulo), 0.5))
            _som('pulo')
            kk.empurrar(capa=-8, cabelo=-6, lift=10)
            _mover(kk, ini, A0, 0.5, rot=(0, 360), fantasmas=4, ease='in', on_fim=_pousa)
        ag.depois(0.15, _entra)

        def _pousa():
            kk.rotacao = 0
            _som('pouso')
            ax, ay = kk.ancora()
            poeira(ax, ay - kk.extensao()[1])
            _tremer(4)
            kk.empurrar(lift=-10, capa=-6)
            kk.tocar(K.sequencia(_de_agora(kk, 2) + [(3, agacha, 'out'), (3, pronto, 'suave'),
                                                      (1, pronto)]))
            # close de anime: o olho dele, com a mao no cabo, antes do iai
            ag.depois(0.12, lambda: close_rosto(camada, 'normal', dur=0.72, y_rel=0.8,
                                                espelhar=kk.espelhar,
                                                on_fim=lambda: ag.depois(0.02, _tra)))

        def _tra():
            # TRA: iai relampago - avanca sacando e a luz da katana atravessa
            # a silaba na horizontal
            chaves, i_r = K.golpe(pronto, corta_tra, n_arma=1, prende=2, segue=3, volta=4,
                                  lamina_recua=False, seg=P['segue1'])

            def _q(i):
                if i == i_r - 2:
                    _som('sacar_iai')
                    _mover(kk, kk.ancora(), A1, 0.14, ease='out', fantasmas=3, limite=(area, m))
                    cortar('tra', 0, dur=0.13, on_meio=lambda: impacto_silaba(0, CIANO))
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_ve)

        def _ve():
            # VE: recua deslizando e abaixa, com a lamina baixa para tras...
            seq = K.sequencia(_de_agora(kk, 2, proxima=arma_ve) + [(3, arma_ve, 'out'), (1, arma_ve)])
            kk.tocar(seq)
            _som('desliza')
            kk.empurrar(capa=-10, cabelo=-6)
            _mover(kk, kk.ancora(), B0, 0.17, ease='out', fantasmas=2, limite=(area, m),
                   on_fim=_ve_sobe)

        def _ve_sobe():
            # ... e salta cortando para cima: a luz sobe na diagonal pelas letras
            chaves, i_r = K.golpe(arma_ve, corta_ve, n_arma=1, prende=1, segue=2, volta=3, seg=fim_ve)

            def _q(i):
                if i == i_r - 2:
                    _som('pulo')
                    _som('voz_ha')
                    kk.empurrar(capa=-10, lift=10)
                    _mover(kk, kk.ancora(), B1, 0.17, ease='out', fantasmas=3, limite=(area, m))
                    cortar('ve', 1, dur=0.14, on_meio=lambda: impacto_silaba(1, CIANO))
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_saca_azul)

        def _saca_azul():
            # no alto do salto, pairando um instante: leva a mao as costas e
            # saca a espada azul num arco para cima (e ja se poe para o TE)
            seq = K.sequencia(_de_agora(kk, 2, proxima=pega_az) +
                              [(3, pega_az, 'out'), (2, saca_az, 'out'), (4, saca_az, 'segura'),
                               (3, arma_te, 'out'), (1, arma_te)])

            def _q(i):
                if i == 5:
                    hx2, hy2 = kk.ponta_espada(2)
                    faiscas.estourar(hx2, hy2, AZUL, n=16, forca=dp(130), tam=ps)
                    _anel(camada, kk.ponto_mao(2), ps, ps * 8, 0.3, AZUL, esp=dp(3))
                    _som('sacar')
                    kk.empurrar(cabelo=8, lift=4)
            _mover(kk, kk.ancora(), C0, 0.45, ease='out', fantasmas=0, limite=(area, m))
            kk.tocar(seq, on_quadro=_q, on_fim=_te)

        def _te():
            # TE: mergulha na diagonal com as duas laminas - duas luzes (a da
            # katana e a azul, um tiquinho atras) descem pelas letras
            chaves, i_r = K.golpe(arma_te, corta_te, n_arma=1, prende=1, segue=2, volta=2, seg=corta_te)

            def _q(i):
                if i == i_r - 2:
                    _som('voz_teya')
                    kk.empurrar(capa=12, lift=6)
                    _mover(kk, kk.ancora(), C1, 0.15, ease='in', fantasmas=3, limite=(area, m))
                    cortar('te', 2, dur=0.13, on_meio=lambda: impacto_silaba(2, CIANO, forte=True))
                    ag.depois(0.04, lambda: cortar('te2', 2, dur=0.13, som='corte2'))
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_te_volta)

        def _te_volta():
            # da um mortal para tras e cai agachado do lado de la do FO
            ax, ay = kk.ancora()
            p_pulo = _com(P['pulo'], olhos='s')
            kk.tocar(_voo_seq(K.esticado(p_pulo), K.encolhido(p_pulo), K.esticado(prep_fo), 0.32))
            _som('pulo')
            kk.empurrar(capa=8, lift=8)
            h = _arco(ay, D0[1], th * 0.9, area[3] - m - _ext(kk, [K.encolhido(p_pulo)])[3])

            def _chegou():
                kk.rotacao = 0
                _som('pouso')
                bx, by = kk.ancora()
                poeira(bx, by - kk.extensao()[1], n=8)
                kk.empurrar(lift=-8, capa=-6)
                baixo = _com(prep_fo, dy=prep_fo['dy'] - 1)       # amortece a queda
                kk.tocar(K.sequencia([(2, baixo, 'out'), (2, prep_fo, 'out'), (1, prep_fo)]), on_fim=_fo)
            _mover(kk, (ax, ay), D0, 0.32, altura=h, rot=(0, -360), fantasmas=2, limite=(area, m),
                   on_fim=_chegou)

        def _fo():
            # FO: salta cruzando as duas laminas no alto...
            kk.tocar(_voo_seq(K.esticado(prep_fo), arma_fo, arma_fo, 0.2))
            _som('pulo')
            kk.empurrar(capa=-10, lift=10)
            _mover(kk, kk.ancora(), Dm, 0.2, ease='out', fantasmas=2, limite=(area, m), on_fim=_fo_x)

        def _fo_x():
            # ... e desce abrindo as duas em X: as duas luzes se cruzam na silaba
            chaves, i_r = K.golpe(arma_fo, corta_fo, n_arma=1, prende=1, segue=2, volta=3)

            def _q(i):
                if i == i_r - 2:
                    _som('voz_seiya')
                    kk.empurrar(capa=10, cabelo=8, lift=6)
                    _mover(kk, kk.ancora(), D1, 0.16, ease='in', fantasmas=3, limite=(area, m),
                           on_fim=lambda: poeira(D1[0], D1[1] - kk.extensao()[1], n=8))
                    cortar('fo', 3, dur=0.13, on_meio=lambda: impacto_silaba(3, CIANO, forte=True))
                    ag.depois(0.03, lambda: cortar('fo2', 3, dur=0.13, som='corte2'))
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_final)

        # ── 6. golpe final (estilo Bleach) ───────────────────────────
        cx_meio = ox_t + titulo.tw / 2.0

        def _final():
            # sobe para o meio da frase, embaixo do infinito
            kk.espelhar = False
            alvo = quadro(cx_meio, y_topo, ['agacha', 'une_a', 'une_b', M['fund_alto'], M['evo_alto']])
            ax, ay = kk.ancora()
            p_pulo = _com(P['pulo'], olhos='s')
            kk.mostrar(K.esticado(p_pulo))
            _som('pulo')
            h = _arco(ay, alvo[1], th * 1.2, area[3] - m - _ext(kk, [K.esticado(p_pulo)])[3])
            _mover(kk, (ax, ay), alvo, 0.38, altura=h, on_fim=_fundir, limite=(area, m),
                   on_passo=_voo(kk, K.esticado(p_pulo), p_pulo, K.esticado(p_pulo)))

        def _fundir():
            _som('pouso')
            ax, ay = kk.ancora()
            poeira(ax, ay - kk.extensao()[1], n=8)
            cam[0].ir(1.12, foco=(ax, ay + alt * 0.35), dur=1.8)
            # nome da habilidade embaixo da frase (a acao e em cima dela)
            nome = _NomeGolpe(ox_t + titulo.tw / 2.0, oy_t - th * 1.5, W * 0.9)
            estado['nome'] = nome
            camada.add_widget(nome)
            # a pose: cruza as duas espadas no alto enquanto diz "Starburst...
            # Stream!" - o clarao da fusao cai no pico do "Stream".
            # (54 quadros: a voz e o clarao estao sincronizados com eles)
            seq = K.sequencia([(3, _com(P['agacha'], olhos='s'), 'out'), (5, _com(P['dupla'], olhos='s'), 'out'),
                               (20, P['une_a'], 'suave'), (14, P['une_b'], 'segura'), (12, P['une_b'])])
            # o reiatsu vai subindo: cabelo arrepia, sobretudo levanta e, com
            # as espadas se juntando, o tronco treme de tanta energia
            for f, q in enumerate(seq):
                if f >= 8:
                    u = min(1.0, (f - 8) / 30.0)
                    q['sobe'] = u
                    q['lift'] = q['lift'] + 1.4 * u
                    if f >= 26:
                        q['dx'] = q['dx'] + K._TREMOR[(f // 2) % len(K._TREMOR)]

            def _q(i):
                if i == 6:
                    _som('habilidade')
                    _som('voz_starburst')
                    nome.parte1()
                elif i == 8:
                    _som('pulo')                     # as duas sobem cruzadas
                elif i == 41:
                    _som('voz_stream')
            kk.tocar(seq, on_quadro=_q, on_fim=_flash_fusao)

        def _fitas(alvo=None, aperto=None, vel=None):
            for f in estado.get('fitas', ()):
                if alvo is not None:
                    f.alvo = alvo
                if aperto is not None:
                    f.aperto = aperto
                if vel is not None:
                    f.vel = vel

        def _flash_fusao():
            hx2, hy2 = kk.ponto_mao(1)
            jx, jy = hx2, hy2 + 6 * ps                 # onde as laminas se encontram
            # as laminas se fundem (clarao na juncao) e ele segura a espada
            # fundida no alto, tremendo com o reiatsu
            kk.tocar(K.poder(_com(P['fund_alto'], olhos='s'), n=36, de=0.9), loop=True)
            faiscas.estourar(jx, jy, BRANCO, n=26, forca=dp(220), tam=ps)
            faiscas.estourar(jx, jy, AZUL, n=16, forca=dp(160), tam=ps)
            _anel(camada, (jx, jy), ps * 2, ps * 22, 0.45, CIANO, esp=dp(4))
            _brilho_tela(camada, 0.3, 0.2)
            _som('fusao')
            _tremer(10)
            kk.pausar(0.08)
            kk.empurrar(cabelo=8, lift=6)
            aura.alvo = 0.35
            nome = estado.get('nome')
            if nome is not None:
                nome.parte2()
                ag.depois(1.1, nome.sumir)
            # close: o olho dele acende em ciano
            ag.depois(0.3, lambda: close_rosto(camada, 'poder', dur=0.8, y_rel=0.8))
            ag.depois(1.2, _enrola)

        def _enrola():
            # a fita de fogo sobe do chao e se enrola nele, apertada como um
            # casulo que gira
            _fitas(alvo=0.55, aperto=0.42, vel=20.0)
            _som('fitas')
            ag.depois(0.35, lambda: _som('fogo'))
            t = [0.0]

            def _vento(dt):
                t[0] += dt
                if t[0] > 1.5:
                    return False
                kk.empurrar(lift=1.8, cabelo=1.5, capa=-1.2)
                if random.random() < 0.6:
                    ax2, ay2 = kk.ancora()
                    faiscas.estourar(ax2 + random.uniform(-1, 1) * 9 * ps, ay2 - 10 * ps, ROXO, n=1,
                                     forca=dp(30), tam=max(2, ps * 0.6), gravidade=-dp(260))
                return True
            ag.cada(0.06, _vento)
            ag.depois(1.45, lambda: _cresce(0, 0.1))

        ETAPAS = (0.34, 0.66, 1.0)

        def _cresce(i, antes):
            # o cabelo cresce em 3 pulsos (no primeiro o sobretudo rasga e ele
            # vira o Mugetsu): cada pulso abre um pouco mais a fita
            alvo_c = ETAPAS[i]
            base = _com(M['fund_alto'], olhos='s')
            rampa = []
            for f, q in enumerate(K.poder(base, n=9, de=0.9)):
                q = dict(q)
                q['cresce'] = round((antes + (alvo_c - antes) * min(1.0, (f + 1) / 8.0)) * 20) / 20.0
                rampa.append(q)
            parado = [dict(q, cresce=alvo_c) for q in K.poder(base, n=36, de=0.9)]
            kk.tocar(rampa, on_fim=lambda: kk.tocar(parado, loop=True))
            ax_m, ay_m = kk.ancora()
            _anel(camada, (ax_m, ay_m + alt * 0.25), ps * 3, ps * (18 + 8 * i), 0.4, ROXO, esp=dp(4))
            faiscas.estourar(ax_m, ay_m + alt * 0.3, ROXO, n=10 + 6 * i, forca=dp(160), tam=ps, gravidade=-dp(100))
            _tremer(8 + 4 * i)
            kk.empurrar(cabelo=10, lift=6, capa=-8)
            _fitas(alvo=0.6 + 0.12 * i, aperto=0.5 + 0.12 * i)
            if i == 0:
                # o sobretudo rasga: clarao e retalhos escuros voando
                kk.clarao = 0.9
                ag.depois(0.1, lambda: _clarao_boneco(kk, 0.35))
                faiscas.estourar(ax_m, ay_m, (0.18, 0.1, 0.3), n=26, forca=dp(220), tam=ps * 1.4,
                                 gravidade=dp(80))
                _som('vidro')
                _brilho_tela(camada, 0.35, 0.2, (0.85, 0.75, 1.0))
            _som('absorve' if i == 2 else 'carga')
            if i < 2:
                ag.depois(0.6, lambda: _cresce(i + 1, alvo_c))
            else:
                aura.alvo = 0.7                          # a espada acende: roxo e azul
                ag.depois(0.7, _sugar)

        def _sugar():
            reator = estado['reator']
            ponta = lambda: kk.ponta_espada(1)
            if reator is None or reator.parent is None:
                _absorveu()
                return
            _fundo(tela, reator=1.0, barra=0.1, dur=0.35)    # o infinito acende enquanto e puxado
            _som('reiatsu')
            aura.alvo = 0.7
            fluxo = _Fluxo(reator, ponta, dur=1.9, px_tam=ps)
            estado['fluxo'] = fluxo
            camada.add_widget(fluxo, index=1)
            reator.sugar(ponta, dur=1.9, on_fim=lambda: ag.depois(0.0, _absorveu))
            vento = [0.0]

            def _vento(dt):
                vento[0] += dt
                if vento[0] > 2.0:
                    return False
                kk.empurrar(lift=2.2, cabelo=-1.5, capa=-1.0)
                if int(vento[0] * 10) % 4 == 0:
                    _tremer(2)
                return True
            ag.cada(0.08, _vento)
            ag.depois(2.6, lambda: None if getattr(reator, '_absorvido', False) else _absorveu())

        def _absorveu():
            if estado.get('absorveu'):
                return
            estado['absorveu'] = True
            fl = estado.get('fluxo')
            if fl is not None:
                ag.depois(0.25, fl.parar)
            r = estado['reator']
            if r is not None:
                r._absorvido = True
            tx, ty = kk.ponta_espada(1)
            kk.tocar(K.poder(M['evo_alto'], n=36, de=1.0, olhos='s'), loop=True)
            _clarao_boneco(kk, 0.3, 0.8)
            _anel(camada, (tx, ty), ps * 2, max(W, H) * 0.35, 0.45, BRANCO, esp=dp(3))
            faiscas.estourar(tx, ty, CIANO, n=30, forca=dp(300), tam=ps)
            _som('absorve')
            _tremer(12)
            kk.pausar(0.1)
            # close: os olhos acendem roxos
            ag.depois(0.25, lambda: close_rosto(camada, 'mugetsu', dur=0.95, y_rel=0.8, on_fim=_revela))

        def _revela():
            # a fita abre inteira em volta dele: o Mugetsu aparece
            kk.tocar(K.poder(M['evo_alto'], n=36, de=1.0, olhos='l'), loop=True)
            tx, ty = kk.ponta_espada(1)
            ax, ay = kk.ancora()
            _fitas(alvo=1.0, aperto=1.0, vel=14.0)
            kk.clarao = 1.0
            ag.depois(0.1, lambda: _clarao_boneco(kk, 0.45))
            _brilho_tela(camada, 0.7, 0.4, (0.9, 0.8, 1.0))
            _anel(camada, (ax, ay + alt * 0.3), ps * 3, max(W, H) * 0.6, 0.6, ROXO, esp=dp(5))
            faiscas.estourar(ax, ay + alt * 0.3, ROXO, n=40, forca=dp(320), tam=ps)
            faiscas.estourar(tx, ty, BRANCO, n=20, forca=dp(240), tam=ps)
            _som('titulo')
            _tremer(22)
            kk.pausar(0.14)
            aura.alvo = 1.0
            cam[0].ir(1.2, foco=(ax, ay + alt * 0.4), dur=0.5)
            ag.depois(1.0, _posiciona)

        def _posiciona():
            # sobe para o meio da frase: dali a escuridao vai sair dele
            kk.espelhar = False
            poses_f = [M['evo_alto'], M['evo_carga'], M['evo_corte'], M['evo_fim']]
            x_ini, y_ini = quadro(cx_meio - th * 0.3, y_topo + alt * 0.45, poses_f)
            ax, ay = kk.ancora()
            alto_p = _com(M['evo_alto'], sobe=1.0, olhos='l')
            kk.parar()
            kk.mostrar(K.esticado(alto_p))
            _som('pulo')
            cam[0].ir(1.0, dur=0.35)
            h = _arco(ay, y_ini, th * 1.2, area[3] - m - _ext(kk, [K.esticado(alto_p)])[3])
            _mover(kk, (ax, ay), (x_ini, y_ini), 0.4, altura=h, fantasmas=4, on_fim=_trevas,
                   limite=(area, m),
                   on_passo=_voo(kk, K.esticado(alto_p), K.encolhido(alto_p), alto_p, (0.25, 0.65)))

        def _trevas():
            # MUGETSU: a escuridao sai dele e engole a tela inteira (a frase e
            # o infinito somem); so os olhos, o fogo e a espada brilham
            kk.tocar(K.poder(_com(M['evo_alto'], olhos='l'), n=36, de=0.8), loop=True)
            ax, ay = kk.ancora()
            tv = _Trevas(2 * ps / float(K.R))
            i = camada.children.index(titulo) if titulo in camada.children else len(camada.children)
            camada.add_widget(tv, index=i)
            estado['trevas'] = tv
            tv.crescer(ax, ay + alt * 0.3, dur=0.75)
            _som('trevas')
            aura.alvo = 1.0
            cam[0].ir(1.12, foco=(ax, ay + alt * 0.3), dur=1.4)
            kk.empurrar(capa=-6, cabelo=-5, lift=4)
            ag.depois(1.3, _ergue)

        def _ergue():
            # silencio: ele diz o nome do golpe, a lamina vai para tras e o fogo sobe
            kk.tocar(K.poder(_com(M['evo_carga'], olhos='g'), n=36, de=0.7), loop=True)
            _som('voz_mugetsu')
            kk.empurrar(capa=4, cabelo=4, lift=3)
            ag.depois(0.85, _golpe_final)             # o corte cai no "TSU" do grito

        def _golpe_final():
            # UM corte so: a lamina atravessa e um risco de luz corta a tela de
            # um lado ao outro na altura da frase... e tudo congela
            corte = _com(M['evo_corte'], sobe=1.0)
            meio = K.smear(K.misturar(M['evo_carga'], corte, 0.5, 0.5), P['evo_carga']['a1'])
            kk.impacto(forte=True)
            kk.tocar(K.sequencia([(1, meio, 'segura'), (1, K.smear(corte, P['evo_carga']['a1']), 'segura'),
                                  (6, corte, 'segura'), (1, corte)]))
            _, cy = titulo.x_do_trecho(0, len(texto))
            tv = estado.get('trevas')
            if tv is not None:
                tv.cortar(cy)
            cortar('cus', 4, dur=0.18)               # a luz roxa atravessa a frase e grava o CUS
            ax_i, _ = kk.ancora()
            ag.depois(0.06, lambda: _quadro_impacto(camada, kk, (ax_i, cy)))
            _som('sacar_iai')
            cam[0].ir(1.0, dur=0.1)
            ag.depois(0.08, lambda: kk.pausar(0.55))
            ag.depois(0.7, _abre)

        def _abre():
            # a escuridao se abre no corte: a frase aparece gravada dentro dele
            tv = estado.get('trevas')
            if tv is not None:
                tv.abrir(0.6)
            _, cy = titulo.x_do_trecho(0, len(texto))
            for i0, i1 in _TRECHOS:
                titulo.garantir(i0, i1)
            for li, letra in enumerate(texto):
                if letra.strip():
                    ag.depois(0.015 * li, lambda li=li: titulo.gravar(li, li + 1))
            for j in range(9):
                xj = area[0] + (area[2] - area[0]) * (j + 0.5) / 9.0
                faiscas.estourar(xj, cy, random.choice((ROXO, BRANCO, (0.85, 0.72, 1.0))), n=5,
                                 forca=dp(240), tam=ps, gravidade=dp(160))
            _som('getsuga')
            _tremer(28)
            _brilho_tela(camada, 0.5, 0.35, (0.9, 0.82, 1.0))
            ag.depois(0.3, _para)

        def _para():
            # para de costas para a frase: a lamina passa do ponto, o corpo
            # vai junto e volta com uma molinha... e o mundo segura a respiracao
            fim_p = M['evo_fim']
            seg = _com(fim_p, a1=fim_p['a1'] - 20, dx=fim_p['dx'] + 1, sobe=0.6)
            kk.tocar(K.sequencia([(2, _com(M['evo_corte'], sobe=1.0), 'out'), (6, seg, 'mola'),
                                  (6, fim_p, 'segura'), (1, fim_p)]))
            kk.pausar(0.12)
            kk.empurrar(capa=-20, cabelo=-16)
            ag.depois(0.55, _separa)

        def _separa():
            # a espada evoluida se divide de novo nas duas e ele desce para
            # pousar em cima da frase
            hx2, hy2 = kk.ponto_mao(1)
            aura.alvo = 0.0
            _fitas(alvo=0.0)
            dupla = _com(P['dupla'], olhos='s')
            kk.tocar(K.sequencia([(4, _com(dupla, dx=dupla['dx'] + 1, a1=dupla['a1'] + 12,
                                           a2=dupla['a2'] - 12), 'mola'), (1, dupla)]))
            # sai da Bankai: clarao branco e as chamas se desfazem em brilhos
            kk.clarao = 1.0
            ag.depois(0.08, lambda: _clarao_boneco(kk, 0.4))
            ax_m, ay_m = kk.ancora()
            faiscas.estourar(ax_m, ay_m + alt * 0.3, ROXO, n=24, forca=dp(140), tam=ps, gravidade=-dp(200))
            faiscas.estourar(hx2, hy2, BRANCO, n=18, forca=dp(160), tam=ps)
            faiscas.estourar(hx2, hy2, AZUL, n=10, forca=dp(120), tam=ps)
            _anel(camada, (hx2, hy2), ps * 2, ps * 14, 0.35, CIANO)
            _som('separa')
            ag.depois(0.4, _desce)

        def _desce():
            ax, ay = kk.ancora()
            alvo = quadro(ax, y_topo, ['dupla', 'saca2', 'pega2', 'chiburi1_a', 'chiburi1', 'guardado'])
            dupla = _com(P['dupla'], olhos='s')
            kk.mostrar(K.esticado(dupla))

            def _pousou():
                _som('pouso')
                bx, by = kk.ancora()
                poeira(bx, by - kk.extensao()[1], n=8)
                kk.empurrar(lift=-8, capa=-6)
                kk.tocar(K.sequencia([(2, _com(dupla, dy=dupla['dy'] - 2), 'out'), (3, dupla, 'out'),
                                      (1, dupla)]), on_fim=lambda: ag.depois(0.15, _guarda_azul))
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
                elif q == 29:
                    _som('embainhar')
                    bx, by = kk.ponto_mao(1)
                    faiscas.estourar(bx, by, BRANCO, n=6, forca=dp(50), tam=max(2, ps * 0.7),
                                     gravidade=0)
                    ag.depois(0.14, _explode)
            kk.tocar(seq, on_quadro=_q, on_fim=lambda: kk.idle(base=P['guardado']))

        # ── 7. so depois de embainhar: a frase explode ──────────────
        def _explode():
            cx, cy = titulo.x_do_trecho(0, len(texto))
            for sent, cor in ((1, CIANO), (-1, AZUL)):
                camada.add_widget(CorteMeiaLua(
                    centro=(cx, cy), raio=titulo.tw * 0.62, ang_ini=160 if sent > 0 else 20,
                    ang_fim=-45 if sent > 0 else 225, espessura=th * 1.2,
                    achat=0.34, rotacao=12 * sent, cor=cor,
                    dur_cheio=5 / 30.0, dur_decai=9 / 30.0))
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
            ag.depois(1.2, encerrar)

        # rede de seguranca: a cena nunca prende o app
        def _seguranca():
            titulo.completo()
            restaurar_fundo()
            encerrar()
        ag.depois(36.0, _seguranca)
    except Exception as e:
        print(f"[cena] falhou, seguindo sem ela: {e}")
        restaurar_fundo()
        encerrar()
    return camada


def limpar_cena(camada):
    try:
        ag = getattr(camada, '_agenda', None)
        if ag is not None:
            ag.parar()
        rest = getattr(camada, '_restaurar', None)
        if rest is not None:
            rest()
        for w in list(camada.children):
            if isinstance(w, K.KiritoPixel):
                w.parar()
            elif isinstance(w, (_AuraEspada, _Fluxo, _OndaGetsuga, _NomeGolpe)):
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
                                      (4, _com(P['espia_alto'], olhos='u', emote='!'), 'segura'),
                                      (1, _com(P['espia_alto'], olhos='u', emote='!')),
                                      (1, _com(P['espia_baixo'], olhos='u'))]))

            def _de_volta():
                if self._bloq:
                    return
                self._escondido = False
                seq = K.sequencia([(14, _com(P['espia_baixo'], olhos='s'), 'in'),
                                   (22, _com(P['espia_olha'], olhos='s', emote='gota')),
                                   (1, _com(P['espia_olha'], olhos='s', emote='gota'))])
                self.k.tocar(seq, on_fim=self._esperar)

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
            base = _com(P['espia_olha'], olhos='f', emote='gota')
            quadros = []
            for dx in (0, -1, -1, 1, 1, -1, -1, 1, 1, 0, 0, 0):
                q = dict(base)
                q['dx'] = dx
                q['m1'] = (base['m1'][0] - dx, base['m1'][1])     # maos paradas na borda
                q['m2'] = (base['m2'][0] - dx, base['m2'][1])
                quadros.extend([q, q])
            ps = self.k.ps

            def _afunda():
                self.k.mostrar(_com(P['espia_baixo'], olhos='f', emote='...'))
                self._animar_desc(13 * ps, 0.9)
            # se estava escondido (susto do erro), volta para a borda antes
            self.k.mostrar(base)
            self._animar_desc(0.0, 0.15, on_fim=lambda: self.k.tocar(quadros, on_fim=_afunda))
        except Exception as e:
            print(f"[kirito pin] bloqueado: {e}")

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
                k.tocar(K.sequencia([(3, _com(P['espia_alto'], olhos='e', emote='brilho')),
                                     (4, _com(P['espia'], olhos='e', emote='brilho')),
                                     (1, _com(P['espia_alto'], olhos='e', emote='brilho'))]))
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
                feliz = _com(P['guardado'], olhos='e', emote='brilho')
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
    """Rachaduras de vidro saindo de (cx, cy): caminhos tortos que se
    dividem, ate a borda do retangulo."""
    rnd = random.Random(semente)
    fila = [(cx, cy, 2 * math.pi * i / n + rnd.uniform(-0.25, 0.25)) for i in range(n)]
    caminhos = []
    while fila and len(caminhos) < n * 2:
        x, y, a = fila.pop(0)
        c = []
        for _ in range(400):
            a += rnd.uniform(-0.35, 0.35)
            x += math.cos(a) * te
            y += math.sin(a) * te
            if not (rx <= x <= rx + rw and ry <= y <= ry + rh):
                break
            q = (math.floor(x / te) * te, math.floor(y / te) * te)
            if not c or c[-1] != q:
                c.append(q)
            if len(c) in (10, 26) and rnd.random() < 0.5:
                fila.append((x, y, a + rnd.choice((-0.8, 0.8))))
        if c:
            caminhos.append(c)
    return caminhos


def _metades(camada, alvo, rx, ry, rw, rh, corte=(0.68, 0.32)):
    """Duas metades (foto real do widget) separadas por um corte reto:
    corte = (altura do corte na esquerda, na direita), em fracoes."""
    try:
        tex = alvo.export_as_image().texture
    except Exception as e:
        print(f"[fatiar] sem foto do widget: {e}")
        tex = None
    ya, yb = ry + rh * corte[0], ry + rh * corte[1]  # linha do corte (esq -> dir)

    def quad(pts):
        vs = []
        for x, y in pts:
            # a textura do export_as_image vem invertida na vertical
            vs.extend((x, y, (x - rx) / rw, 1.0 - (y - ry) / rh))
        return vs
    cima = [(rx, ry + rh), (rx + rw, ry + rh), (rx + rw, yb), (rx, ya)]
    baixo = [(rx, ya), (rx + rw, yb), (rx + rw, ry), (rx, ry)]
    pecas = []
    for pts, sentido in ((cima, 1), (baixo, -1)):
        w = Widget(size_hint=(None, None), size=(0, 0))
        with w.canvas:
            PushMatrix()
            tr = Translate(0, 0)
            rot = Rotate(angle=0, origin=(rx + rw / 2.0, ry + rh / 2.0))
            c = Color(1, 1, 1, 1) if tex else Color(0.05, 0.1, 0.2, 0.95)
            m = Mesh(mode='triangle_fan', indices=list(range(len(pts))), vertices=quad(pts))
            if tex:
                m.texture = tex
            PopMatrix()
        camada.add_widget(w)
        pecas.append((w, tr, rot, c, sentido))
    return pecas


def _quartos(camada, alvo, rx, ry, rw, rh):
    """Quatro pedacos (foto real do widget) cortados pelas duas diagonais:
    o corte em X. Cada um e (widget, translate, rotate, color, (dx, dy))."""
    try:
        tex = alvo.export_as_image().texture
    except Exception as e:
        print(f"[fatiar] sem foto do widget: {e}")
        tex = None
    cx, cy = rx + rw / 2.0, ry + rh / 2.0
    cantos = [(rx, ry + rh), (rx + rw, ry + rh), (rx + rw, ry), (rx, ry)]
    pecas = []
    for i, dirc in enumerate(((0, 1), (1, 0), (0, -1), (-1, 0))):
        pts = [cantos[i], cantos[(i + 1) % 4], (cx, cy)]
        w = Widget(size_hint=(None, None), size=(0, 0))
        vs = []
        for x, y in pts:
            vs.extend((x, y, (x - rx) / rw, 1.0 - (y - ry) / rh))
        with w.canvas:
            PushMatrix()
            tr = Translate(0, 0)
            rot = Rotate(angle=0, origin=(cx, cy))
            c = Color(1, 1, 1, 1) if tex else Color(0.05, 0.1, 0.2, 0.95)
            m = Mesh(mode='triangle_fan', indices=[0, 1, 2], vertices=vs)
            if tex:
                m.texture = tex
            PopMatrix()
        camada.add_widget(w)
        pecas.append((w, tr, rot, c, dirc))
    return pecas


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
            # poca de sombra no chao; ele sobe dela escuro e ganha cor
            te = s.te
            ax = alvo[0]
            y = k.y + K._PES * k.ps - te
            rx = 7.0 * k.ps

            def forma(t, p, u):
                v = min(1.0, t / 0.55)
                abre = min(1.0, v / 0.25) * (1 - max(0.0, (v - 0.7) / 0.3))
                w = rx * abre
                for dy, frac, nome in ((0, 1.0, 'b'), (0, 0.7, 'a'), (1, 0.8, 'b'), (-1, 0.6, 'b')):
                    ww = math.floor(w * frac / te) * te
                    if ww > 0:
                        p.setdefault(nome, []).append((math.floor((ax - ww) / te) * te,
                                                       math.floor(y / te) * te + dy * te, 2 * ww, te))
            s.cam.add_widget(_EfeitoPixel((('b', (0.20, 0.05, 0.36, 0.85)), ('a', (0.03, 0.0, 0.06, 1.0))),
                                          0.55, forma), index=len(s.cam.children))
            antes = tuple(k._cor_clarao.rgb)
            k._cor_clarao.rgb = (0.05, 0.02, 0.1)
            k.opacity = 0
            k.clarao = 1.0
            _som('materializa')
            t = [0.0]

            def _p(dt):
                try:
                    t[0] += dt
                    v = min(1.0, t[0] / 0.45)
                    k.opacity = min(1.0, v * 2.5)
                    k.clarao = 1.0 - v
                    if random.random() < 0.5:
                        s.faiscas.estourar(ax + random.uniform(-rx, rx) * 0.6, y, (0.55, 0.25, 0.95), n=1,
                                           forca=dp(25), tam=te * 2, gravidade=-dp(160))
                    if v >= 1:
                        k._cor_clarao.rgb = antes
                        k.clarao = 0.0
                        fim()
                        return False
                except Exception:
                    k._cor_clarao.rgb = antes
                    k.opacity = 1
                    k.clarao = 0
                    fim()
                    return False
            Clock.schedule_once(lambda dt: Clock.schedule_interval(_p, 1 / 60.), 0.12)
    except Exception as e:
        print(f"[entrada] {e}")
        k.opacity = 1
        fim()


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
        Window.add_widget(self.cam)
        alt_boneco = max(dp(62), min(self.rh * 1.7, dp(96), H * 0.15))
        self.ps = max(K.R, int(round(3 * int(math.ceil(alt_boneco * 1.12 / 31.0 / 3 - 0.15)) * K.TAMANHO)))
        self.te = self.ps / float(K.R)
        _PX[0] = self.te
        self.k = K.KiritoPixel(ps=self.ps)
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
                           'desliza', 'embainhar', 'golpe_final', 'habilidade', 'voz_teya', 'voz_seiya',
                           'vidro', 'papel', 'giro', 'moedas', 'pouso'])

    def no_quadro(self, x, y, poses):
        return _no_quadro(self.k, x, y, poses, self.area, dp(2))

    def poeira(self, lado=0):
        """Poeira nos pes (pouso, freada)."""
        ax, _ = self.k.ancora()
        y = self.k.y + K._PES * self.ps
        for sentido in ((-1, 1) if not lado else (lado,)):
            self.faiscas.estourar(ax + sentido * self.ps * 3, y, POEIRA, n=5, forca=dp(70),
                                  tam=self.te * 2, gravidade=dp(260))

    def explodir(self, corte=None):
        if self.explodiu:
            return
        self.explodiu = True
        try:
            self.alvo.opacity = 0
            from efeitos import explodir_estilhacos
            explodir_estilhacos(self.alvo, self.fim, corte=corte)
        except Exception as e:
            print(f"[apagar] explosao: {e}")
            self.fim()

    def separar(self, pecas, dur, deslocar, on_fim):
        """Anima os pedacos se afastando; deslocar(sentido, e) -> (dx, dy, giro)."""
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur)
                e = 1 - (1 - u) ** 2
                for w, tr, rot, c, s in pecas:
                    dx, dy, giro = deslocar(s, e)
                    tr.xy = (dx, dy)
                    rot.angle = giro
                    c.a = 1 - 0.35 * e
                if u >= 1:
                    for w, *_ in pecas:
                        if w.parent:
                            w.parent.remove_widget(w)
                    on_fim()
                    return False
            except Exception as ex:
                print(f"[apagar] separar: {ex}")
                on_fim()
                return False
        Clock.schedule_interval(_p, 1 / 60.)

    def sair(self):
        _teleporte(self.k, self.cam, self.faiscas, on_fim=self._limpa, dur=0.45, teto=self.area[3] - dp(2))

    def _limpa(self):
        self.k.parar()
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

        def _tensao():
            hx, hy = k.ponto_mao(1)
            _estrela(s.cam, hx, hy, s.ps * 0.6, BRANCO, raios=4, dur=0.12)
            _som('koiguchi')
            Clock.schedule_once(lambda dt: _saque(), 0.32)

        def _saque():
            k.fantasma(cor=CIANO, alfa=0.7, duracao=0.3)
            k.mostrar(corte)
            _som('sacar_iai')
            linha = _reta_pixels(s.rx - s.te * 2, s.cy, s.rx + s.rw + s.te * 2, s.cy, s.te)
            if not esq:
                linha.reverse()
            s.cam.add_widget(_PixelsLuz([linha], s.te, cresce=0.06, fica=0.5, some=0.2, grossura=1), index=0)
            _mover(k, k.ancora(), fim_p, 0.07, linear=True, fantasmas=4, on_fim=_parado)
            s.faiscas.estourar(s.cx, s.cy, CIANO, n=10, forca=dp(120), tam=s.ps * 0.8)
            _tremer(4)

        def _parado():
            k.impacto()
            k.pausar(0.08)
            Clock.schedule_once(lambda dt: _embainha(), 0.3)

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
            # no clique da bainha o item cai em duas metades pelo risco
            pecas = _metades(s.cam, alvo, s.rx, s.ry, s.rw, s.rh, corte=(0.5, 0.5))
            alvo.opacity = 0
            s.faiscas.estourar(s.cx, s.cy, BRANCO, n=12, forca=dp(140), tam=s.ps * 0.8)
            s.separar(pecas, 0.3, lambda sen, e: (sen * dp(6) * e, sen * dp(10) * e - dp(8) * e, sen * 3 * e),
                      lambda: s.explodir(0.0))

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
        k.precarregar([crava, puxa, _com(P['pulo'], olhos='s')])

        def _mira():
            tx2, ty2 = k.ponta_espada(1, arma)
            _estrela(s.cam, tx2, ty2, s.ps * 0.7, BRANCO, raios=4, dur=0.14)
            _som('koiguchi')
            k.empurrar(capa=-6, cabelo=-4)
            Clock.schedule_once(lambda dt: _lanca(), 0.34)

        def _lanca():
            k.mostrar(crava)
            _som('pulo')
            _som('voz_teya')
            _mover(k, k.ancora(), alvo_a, 0.1, linear=True, fantasmas=4, on_fim=_crava)

        def _crava():
            k.impacto(forte=True)
            k.pausar(0.14)
            _quadro_impacto(s.cam, k, (s.cx, s.cy))
            _som('golpe_final')
            _som('vidro')
            _tremer(10)
            _anel(s.cam, (s.cx, s.cy), s.ps, s.ps * 5, 0.25, BRANCO, esp=dp(2))
            s.faiscas.estourar(s.cx, s.cy, BRANCO, n=10, forca=dp(150), tam=s.ps * 0.7)
            rach = _rachaduras(s.cx, s.cy, s.rx, s.ry, s.rw, s.rh, s.te, n=9)
            s.cam.add_widget(_PixelsLuz(rach, s.te, cresce=0.22, fica=0.5, some=0.1, grossura=1), index=0)
            Clock.schedule_once(lambda dt: _puxa(), 0.55)

        def _puxa():
            # puxa a lamina, o cartao estoura e ele salta para tras girando
            s.explodir(None)
            _som('corte2')
            k.mostrar(puxa)
            pulo = _com(P['pulo'], olhos='s')
            volta = s.no_quadro(ini[0], ini[1] + s.rh * 0.15, [pulo, puxa])
            _mover(k, k.ancora(), volta, 0.34, altura=dp(40), rot=(0, 360 if esq else -360), fantasmas=2,
                   on_fim=_pousa, on_passo=lambda u: k.mostrar(pulo if 0.15 < u < 0.85 else puxa))

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

        def _salta():
            _som('pulo')
            _mover(k, k.ancora(), alvo_a, 0.22, altura=dp(30), fantasmas=2, on_fim=_corta)

        def _corta():
            seq = K.sequencia([(1, K.smear(corta, arma['a1'], arma['a2']), 'segura'), (5, corta, 'segura'),
                               (4, _com(P['dupla'], olhos='s'), 'out'), (1, _com(P['dupla'], olhos='s'))])
            k.tocar(seq)
            k.impacto()
            k.pausar(0.08)
            _som('corte2')
            _som('corte')
            _som('voz_seiya')
            _tremer(9)
            m = s.te * 2
            d1 = _reta_pixels(s.rx - m, s.ry + s.rh + m, s.rx + s.rw + m, s.ry - m, s.te)
            d2 = _reta_pixels(s.rx + s.rw + m, s.ry + s.rh + m, s.rx - m, s.ry - m, s.te)
            s.cam.add_widget(_PixelsLuz([d1, d2], s.te, cresce=0.08, fica=0.35, some=0.15, grossura=2), index=0)
            _estrela(s.cam, s.cx, s.cy, s.ps, CIANO, raios=4, dur=0.16)
            s.faiscas.estourar(s.cx, s.cy, CIANO, n=14, forca=dp(170), tam=s.ps * 0.8)
            s.faiscas.estourar(s.cx, s.cy, AZUL, n=10, forca=dp(140), tam=s.ps * 0.8)
            Clock.schedule_once(lambda dt: _parte(), 0.3)

        def _parte():
            pecas = _quartos(s.cam, alvo, s.rx, s.ry, s.rw, s.rh)
            alvo.opacity = 0
            s.separar(pecas, 0.3, lambda d, e: (d[0] * dp(16) * e, d[1] * dp(12) * e, (d[0] - d[1]) * 6 * e),
                      lambda: s.explodir(None))
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

    def _explodir():
        if explodiu[0]:
            return
        explodiu[0] = True
        try:
            alvo.opacity = 0
            from efeitos import explodir_estilhacos
            explodir_estilhacos(alvo, fim)
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
            _tremer(8)
            k.impacto()
            k.pausar(0.07)                                   # hit-stop
            pecas = _metades(cam, alvo, rx, ry, rw, rh)
            alvo.opacity = 0
            t = [0.0]

            def _separa(dt):
                try:
                    t[0] += dt
                    u = min(1.0, t[0] / 0.32)
                    e = 1 - (1 - u) ** 2
                    for w, tr, rot, c, s in pecas:
                        tr.xy = (-s * dp(10) * e, s * dp(12) * e)
                        rot.angle = s * 5 * e
                        c.a = 1 - 0.35 * e
                    if u >= 1:
                        for w, *_ in pecas:
                            if w.parent:
                                w.parent.remove_widget(w)
                        _explodir()
                        return False
                except Exception as ex:
                    print(f"[fatiar] separar: {ex}")
                    _explodir()
                    return False
            Clock.schedule_interval(_separa, 1 / 60.)

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
        esq = random.random() < 0.5
        k.espelhar = not esq
        arma = _com(P['carimbo_arma'], olhos='s')
        corta = _com(P['carimbo'], olhos='g')
        volta = _com(P['guarda'], olhos='s')
        pos = s.no_quadro(s.rx + s.rw * 0.12 if esq else s.rx + s.rw * 0.88, s.cy, [arma, corta])
        k.ancorar(*pos)
        k.mostrar(arma)

        def _corta():
            seq = K.sequencia([(2, arma, 'segura'), (1, K.smear(corta, arma['a1']), 'segura'),
                               (4, corta, 'segura'), (4, volta, 'out'), (1, volta)])

            def _q(q):
                if q == 2:
                    linha = _reta_pixels(s.rx + s.rw * 0.08, s.cy, s.rx + s.rw * 0.92, s.cy, s.te)
                    if not esq:
                        linha.reverse()
                    s.cam.add_widget(_PixelsLuz([linha], s.te, cresce=0.05, fica=0.12, some=0.15), index=0)
                    s.faiscas.estourar(s.cx, s.cy, CIANO, n=8, forca=dp(130), tam=s.ps * 0.7)
                    _som('corte')
                    k.impacto()
                    feito()
            k.tocar(seq, on_quadro=_q, on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.1))

        _entrar(s, _corta)
    except Exception as e:
        print(f"[carimbo] {e}")
        _remover_da_janela(s.cam)
        feito()


def kirito_vitoria(alvo):
    """FINALIZAR TURNO: o Yoru aparece com a lamina na mao, sacode (chiburi),
    embainha devagar ate o clique e vira de frente na pose de vitoria, com
    o brilho no olho; depois some."""
    if _na_fila(lambda: kirito_vitoria(alvo)):
        return
    try:
        s = _Mini(alvo, None, seguranca=5.0, destruir=False)
    except Exception as e:
        print(f"[vitoria] {e}")
        return
    k, P = s.k, K.POSE_A
    try:
        k.espelhar = random.random() < 0.5
        guarda = _com(P['guarda'], olhos='s')
        passos = [_com(P['chiburi1_a'], olhos='s'), _com(P['chiburi1'], olhos='s'), P['embainha1_a'],
                  P['embainha1_b'], P['embainha1_c'], P['vitoria']]
        pos = s.no_quadro(s.cx, s.cy, [guarda] + passos)
        k.ancorar(*pos)
        k.mostrar(guarda)
        k.precarregar(passos)

        def _cerimonia():
            vit = P['vitoria']
            seq = K.sequencia([(4, guarda, 'segura'), (3, passos[0], 'out'), (3, passos[1], 'segura'),
                               (6, passos[2], 'in'), (2, passos[3], 'out'), (3, passos[4], 'mola'),
                               (4, vit, 'out'), (10, vit, 'segura'), (8, _com(vit, emote='brilho'), 'segura'),
                               (1, vit)])

            def _q(q):
                if q == 7:
                    hx, hy = k.ponto_mao(1)
                    s.faiscas.estourar(hx, hy, BRANCO, n=6, forca=dp(90), tam=s.ps * 0.6, gravidade=dp(300))
                    _som('desliza')
                elif q == 18:
                    _som('embainhar')
                    ax, ay = k.ancora()
                    _anel(s.cam, (ax, ay), s.ps * 2, s.ps * 12, 0.35, CIANO, esp=dp(2))
                elif q == 30:
                    _som('habilidade')
            k.tocar(seq, on_quadro=_q, on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.2))

        _entrar(s, _cerimonia)
    except Exception as e:
        print(f"[vitoria] {e}")
        _remover_da_janela(s.cam)


# pergaminho de luz (pixel art): rolo de papel com as pontas de madeira e o
# selo verde no meio; 2 quadros (deitado e em pe) para girar no ar
_PERGAMINHO = [
    "..MmmmmmmM..",
    ".MpppppppPm.",
    "MmpppgGpppPm",
    "MmppgGGgpPPm",
    ".MPPPggPPPm.",
    "..MmmmmmmM..",
]
_PERGAMINHO_CORES = (('m', (0.30, 0.17, 0.10, 1.0)), ('M', (0.55, 0.34, 0.18, 1.0)),
                     ('P', (0.80, 0.70, 0.54, 1.0)), ('p', (0.97, 0.91, 0.76, 1.0)),
                     ('g', (0.20, 0.78, 0.40, 1.0)), ('G', (0.72, 1.0, 0.78, 1.0)))


class _Pergaminho(Widget):
    """O pergaminho: primeiro preso na mao do Yoru; soltar() e ele sai
    voando, girando (deitado/em pe) com rastro de luz verde, ate fora da
    tela."""

    def __init__(self, k, te, faiscas, on_fim, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k, self.te = k, te
        self.faiscas = faiscas
        self.fim = _Uma(on_fim)
        self.voo = None
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, _PERGAMINHO_CORES)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def soltar(self, alvo_xy, dur):
        x, y = self.k.ponto_mao(1)
        self.voo = (x, y, alvo_xy, dur)
        self.t = 0.0

    def _tick(self, dt):
        try:
            te = self.te
            if self.voo is None:                                # na mao dele
                x, y = self.k.ponto_mao(1)
                em_pe, u = False, 0.0
            else:
                self.t += dt
                x0, y0, alvo, dur = self.voo
                u = min(1.0, self.t / dur)
                e = u * u
                x = x0 + (alvo[0] - x0) * e
                y = y0 + (alvo[1] - y0) * e + math.sin(math.pi * u) * te * 20
                em_pe = int(self.t * 16) % 2 == 1
                if random.random() < 0.7:
                    self.faiscas.estourar(x, y, random.choice(((0.35, 0.95, 0.5), (0.85, 1.0, 0.9))), n=1,
                                          forca=dp(30), tam=te * 2, gravidade=-dp(60))
            p = {}
            b = te * 2                                          # cada pixel do rolo = 2x2 texels
            ox = math.floor(x / te) * te - 6 * b
            oy = math.floor(y / te) * te + 3 * b
            for r, linha in enumerate(_PERGAMINHO):
                for c_, ch in enumerate(linha):
                    if ch == '.':
                        continue
                    lx, ly = (r + 3, -c_ + 3) if em_pe else (c_, -r)
                    p.setdefault(ch, []).append((ox + lx * b, oy + ly * b, b))
            self._lote.desenhar(p)
            if self.voo is not None and u >= 1.0:
                self.fim()
                return self.parar()
        except Exception as ex:
            print(f"[pergaminho] {ex}")
            self.fim()
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        if self.parent:
            self.parent.remove_widget(self)
        return False


def kirito_pergaminho(alvo, on_fim=None):
    """ENVIAR PRO WHATSAPP: o Yoru aparece ao lado do botao com um pergaminho
    de luz na mao, pega impulso e joga; o pergaminho sai girando pela
    tela com rastro verde - so entao o WhatsApp abre."""
    feito = _Uma(on_fim)
    if not _yoru_livre():
        feito()                                                  # ja tem um Yoru em cena: abre direto
        return
    try:
        s = _Mini(alvo, None, seguranca=3.5, destruir=False)
        Clock.schedule_once(lambda dt: feito(), 2.6)             # o WhatsApp abre de qualquer jeito
    except Exception as e:
        print(f"[pergaminho] {e}")
        feito()
        return
    k, P = s.k, K.POSE_A
    try:
        k.espelhar = False
        arma = _com(P['joga_arma'], olhos='s')
        joga = _com(P['joga'], olhos='g')
        pos = s.no_quadro(s.rx - dp(10), s.cy + s.rh * 0.6, [arma, joga])
        k.ancorar(*pos)
        k.mostrar(arma)
        rolo = _Pergaminho(k, s.te, s.faiscas, feito)

        def _joga():
            seq = K.sequencia([(5, arma, 'segura'), (2, joga, 'out'), (8, joga, 'segura'),
                               (4, _com(P['guardado'], olhos='v'), 'out'), (1, _com(P['guardado'], olhos='v'))])

            def _q(q):
                if q == 6:
                    W, H = Window.size
                    rolo.soltar((W + s.te * 20, H + s.te * 10), 0.5)
                    _som('papel')
            k.tocar(seq, on_quadro=_q, on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.15))

        _entrar(s, lambda: (s.cam.add_widget(rolo), _joga()))
    except Exception as e:
        print(f"[pergaminho] {e}")
        _remover_da_janela(s.cam)
        feito()


OURO = (1.0, 0.84, 0.25)


def kirito_nivel(alvo):
    """SUBIU DE NIVEL: o Yoru aparece do lado do nivel, abaixa e salta
    erguendo a espada; da ponta sai um anel de luz dourada com estrelas e
    faiscas; ele vira de frente com o meio sorriso (brilho no olho) e some."""
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
        x = s.rx - dp(14) if k.espelhar else s.rx + s.rw + dp(14)
        pos = s.no_quadro(x, s.cy - s.rh * 0.3, [guarda, ergue, vit])
        k.ancorar(*pos)
        k.mostrar(guarda)
        k.precarregar([ergue, vit, _com(vit, emote='brilho')])

        def _comemora():
            seq = K.sequencia([(3, _com(P['agacha'], olhos='s'), 'in'), (4, ergue, 'out'), (14, ergue, 'segura'),
                               (4, vit, 'out'), (10, _com(vit, emote='brilho'), 'segura'), (1, vit)])

            def _q(q):
                if q == 4:
                    tx, ty = k.ponta_espada(1, ergue)
                    _anel(s.cam, (tx, ty), s.ps, s.ps * 10, 0.5, OURO, esp=dp(3))
                    _estrela(s.cam, tx, ty, s.ps * 0.7, OURO, raios=5, dur=0.2)
                    s.faiscas.estourar(tx, ty, OURO, n=16, forca=dp(180), tam=s.te * 2, gravidade=dp(260))
                    s.faiscas.estourar(tx, ty, BRANCO, n=6, forca=dp(120), tam=s.te * 2, gravidade=dp(200))
                    _som('habilidade')
                    k.empurrar(capa=-10, cabelo=-10, lift=4)
            k.tocar(seq, on_quadro=_q, on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.2))
        _entrar(s, _comemora, tipos=('teleporte', 'queda', 'sombra'))
    except Exception as e:
        print(f"[nivel] {e}")
        _remover_da_janela(s.cam)


def kirito_meta(alvo):
    """BATEU A META: o Yoru aparece do lado do resultado, gira as duas
    espadas, e chovem moedas de luz douradas por cima do valor; termina de
    frente na pose de vitoria e some."""
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
        x = s.rx - dp(10) if k.espelhar else s.rx + s.rw + dp(10)
        pos = s.no_quadro(x, s.ry + s.rh * 0.25, [g1, P['giro_2'], P['giro_3'], vit])
        k.ancorar(*pos)
        k.mostrar(_com(P['dupla'], olhos='s'))
        k.precarregar([g1, P['giro_2'], P['giro_3'], vit, _com(vit, emote='brilho')])

        def _chuva(dt):
            for i in range(10):
                x = s.rx + s.rw * random.uniform(0.1, 0.9)
                y = s.ry + s.rh * random.uniform(0.85, 1.05)
                s.faiscas.estourar(x, y, random.choice((OURO, OURO, BRANCO)), n=1, forca=dp(60),
                                   tam=s.te * 3, gravidade=dp(420))

        def _gira():
            # uma volta de verdade em 8 quadros (achata de lado e vira no meio)
            seq = K.sequencia([(2, g1, 'segura'), (8, g1, 'segura'), (5, g1, 'mola'), (4, vit, 'out'),
                               (12, _com(vit, emote='brilho'), 'segura'), (1, vit)])
            lado0 = k.espelhar

            def _q(q):
                if 2 <= q < 10:
                    cs = math.cos(2 * math.pi * (q - 2) / 8.0)
                    k.escala_x = max(0.2, abs(cs))
                    k.espelhar = lado0 if cs >= 0 else (not lado0)
                elif q == 10:
                    k.escala_x = 1.0
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
            k.tocar(seq, on_quadro=_q, on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.3))
        _entrar(s, _gira, tipos=('teleporte', 'queda', 'corrida', 'sombra'))
    except Exception as e:
        print(f"[meta] {e}")
        _remover_da_janela(s.cam)


def kirito_wipe(widgets, on_fim=None, grafico=None, area_lista=None):
    """WIPE - Starburst Stream: o Yoru se materializa, saca as duas espadas
    dizendo o nome do golpe e da 16 golpes rapidos alternando as espadas,
    espalhados pelas memorias que estao na tela (cada uma racha no talho e
    vira cacos no ultimo golpe que leva). No golpe final ele fatia o
    grafico de barras do topo. Nenhum corte no vento."""
    if _na_fila(lambda: kirito_wipe(widgets, on_fim, grafico, area_lista)):
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
        _precarregar_sons(['sacar', 'corte', 'corte2', 'titulo', 'pulo', 'teleporte', 'voz_starburst',
                           'voz_stream'])
        # STARBURST STREAM: 16 golpes rapidos, alternando as espadas (so uma
        # lamina se mexe por golpe), espalhados pelas memorias da tela; cada
        # memoria vira cacos no ultimo golpe que leva
        # (preparo, corte, espada, arco do rastro, angulo do talho)
        padroes = [('sb1_a', 'sb1_b', 1, (150, -40), -40.0), ('sb2_a', 'sb2_b', 2, (215, 40), 40.0),
                   ('sb3_a', 'sb3_b', 1, (175, 0), 0.0), ('sb4_a', 'sb4_b', 2, (185, -5), 0.0)]
        n_vis = max(1, len(vis))
        ultimo = {}
        for j in range(16):
            ultimo[j % n_vis] = j

        def _desintegra(w, ang):
            from efeitos import explodir_estilhacos
            try:
                explodir_estilhacos(w, lambda: None, corte=ang, tremor=0)
            except Exception as e:
                print(f"[wipe] item: {e}")

        def _golpe(j):
            if j >= 16 or not vis:
                _final()
                return
            iv = j % n_vis
            w, x, y, ww, hh = vis[iv]
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
                    cam.add_widget(CorteMeiaLua(centro=(ccx, cy), raio=ww * 0.34, ang_ini=a0, ang_fim=a1,
                                                espessura=max(dp(18), hh * 0.9), achat=0.35, cor=cor,
                                                dur_cheio=3 / 30.0, dur_decai=4 / 30.0))
                    faiscas.estourar(ccx, cy, cor, n=7, forca=dp(170), tam=ps)
                    _som('corte2' if qual == 2 else 'corte')
                    k.impacto()
                    if ultimo.get(iv) == j:
                        _estrela(cam, ccx, cy, ps, cor)
                        _tremer(9)
                        k.pausar(0.05)
                        _desintegra(w, talho if lado > 0 else 180 - talho)
                    else:
                        _tremer(3)
                k.tocar(K.sequencia([(1, arma, 'segura'), (1, sm, 'segura'), (2, corta, 'segura'),
                                     (1, corta)]), on_quadro=_q, on_fim=lambda: _golpe(j + 1))
            k.parar()
            k.mostrar(arma)
            _mover(k, k.ancora(), alvo, 0.06, linear=True, fantasmas=1, cor_fantasma=cor, on_fim=_ataca)

        def _saca():
            _som('voz_starburst')
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
                elif i == 40:                        # a fala "Sutabasuto..." ja acabou
                    _som('voz_stream')
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
