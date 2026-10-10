"""
chefe.py - O CHEFE da abertura ("THE ABYSS WARDEN"), o vilao do Yoru.

O desenho e a animacao sao feitos no PC (dev/chefe_arte.py desenha as pecas,
dev/chefe_rig.py anima peca por peca e grava chefe/clipes.bin). Aqui o app
so TOCA os quadros prontos: cada desenho vira uma textura (pixel art, sem
suavizar) num retangulo; nada e montado na hora.
"""
import os
import json
import zlib
import random
from collections import OrderedDict

from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.graphics.stencil_instructions import StencilPush, StencilUse, StencilUnUse, StencilPop
from kivy.properties import NumericProperty, BooleanProperty

_DADOS = {}
_TEX = OrderedDict()
_TEX_MAX = 110             # ~250 KB cada: os clipes em uso cabem, os antigos saem


def dados():
    """Cabecalho de chefe/clipes.bin (le uma vez)."""
    if 'cab' in _DADOS:
        return _DADOS['cab']
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chefe', 'clipes.bin')
    with open(caminho, 'rb') as f:
        bruto = f.read()
    if bruto[:4] != b'BK01':
        raise ValueError('chefe/clipes.bin de outra versao')
    n = int.from_bytes(bruto[4:8], 'little')
    cab = json.loads(zlib.decompress(bruto[8:8 + n]).decode('utf-8'))
    _DADOS['base'] = 8 + n
    _DADOS['bruto'] = bruto
    tabs = [bytearray(256) for _ in range(4)]
    for i, c in enumerate(cab['paleta']):
        for k in range(4):
            tabs[k][i] = c[k]
    _DADOS['tab'] = [bytes(t) for t in tabs]
    sil = bytearray(256)
    for i in range(1, len(cab['paleta'])):
        sil[i] = 255
    _DADOS['sil'] = bytes(sil)
    _DADOS['cab'] = cab
    return cab


def quadro(nome, i, silhueta=False):
    """(textura, caixa (x0, y0, w, h) na tela do clipe, garra, ponta) do
    quadro i do clipe `nome`."""
    cab = dados()
    pos, tam, caixa, garra, ponta = cab['clipes'][nome]['quadros'][i]
    ch = (pos, silhueta)
    tex = _TEX.get(ch)
    if tex is None:
        ini = _DADOS['base'] + pos
        idx = zlib.decompress(_DADOS['bruto'][ini:ini + tam])
        buf = bytearray(len(idx) * 4)
        if silhueta:
            s = idx.translate(_DADOS['sil'])
            buf[0::4] = s
            buf[1::4] = s
            buf[2::4] = s
            buf[3::4] = s
        else:
            t = _DADOS['tab']
            buf[0::4] = idx.translate(t[0])
            buf[1::4] = idx.translate(t[1])
            buf[2::4] = idx.translate(t[2])
            buf[3::4] = idx.translate(t[3])
        tex = Texture.create(size=(caixa[2], caixa[3]), colorfmt='rgba')
        tex.mag_filter = tex.min_filter = 'nearest'
        tex.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
        tex.flip_vertical()                     # as linhas vem de cima para baixo
        _TEX[ch] = tex
        while len(_TEX) > _TEX_MAX:
            _TEX.popitem(last=False)
    else:
        _TEX.move_to_end(ch)
    return tex, caixa, garra, ponta


def aquecer(nomes, por_quadro=2, on_fim=None):
    """Cria antes as texturas dos clipes (`por_quadro` por quadro da tela),
    para nenhum desenho ser montado no meio do golpe."""
    try:
        cab = dados()
    except Exception as e:
        print(f"[chefe] aquecer: {e}")
        return
    fila, vistos = [], set()
    for nome in nomes:
        c = cab['clipes'].get(nome)
        for i, q in enumerate(c['quadros'] if c else ()):
            if q[0] not in vistos:
                vistos.add(q[0])
                fila.append((nome, i))

    def _passo(dt):
        try:
            for _ in range(por_quadro):
                if not fila:
                    if on_fim:
                        on_fim()
                    return False
                quadro(*fila.pop(0))
        except Exception as e:
            print(f"[chefe] aquecer: {e}")
            return False
    Clock.schedule_interval(_passo, 0)


def soltar_texturas():
    """Libera as texturas (depois da abertura o chefe nao aparece mais)."""
    _TEX.clear()


class ChefePixel(Widget):
    """O chefe na tela. `te` = px de tela por pixel do desenho (o mesmo do
    Yoru na cena). ancorar(x, y) poe os pes dele (o meio, no chao) nesse
    ponto. Olha para a ESQUERDA; espelhar=True vira para a direita.
    pos/size do widget acompanham o desenho (a explosao em cacos fotografa
    o widget)."""
    espelhar = BooleanProperty(False)
    clarao = NumericProperty(0.0)           # 0..1: silhueta branca por cima (quadro de impacto)

    def __init__(self, te=2.0, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self.te = float(te)
        self.ax, self.ay = 0.0, 0.0
        self.clipe = 'idle'
        self.t = 0.0
        self.loop = True
        self._fim = None
        self._cb = None
        self._ult = -1
        self._pausa = 0.0
        self._tremor = 0
        self._desvio = (0, 0)
        self._recorte = None
        self._flash = 0
        with self.canvas:
            self._cor = Color(1, 1, 1, 1)
            self._ret = Rectangle(pos=(0, 0), size=(0, 0))
            self._cor_cl = Color(1.0, 0.93, 0.86, 0)
            self._ret_cl = Rectangle(pos=(0, 0), size=(0, 0))
        self.bind(espelhar=lambda *_: self._desenhar(), clarao=lambda *_: self._desenhar())
        self._ev = Clock.schedule_interval(self._tique, 1 / 60.)
        self._desenhar()

    # ── controle ─────────────────────────────────────────────────────────
    def ancorar(self, x, y):
        self.ax, self.ay = float(x), float(y)
        self._desenhar()

    def tocar(self, nome, loop=False, on_fim=None, on_quadro=None, t0=0.0):
        """Toca o clipe (30 quadros/s). loop=False: para no ultimo quadro e
        chama on_fim. on_quadro(i) a cada quadro novo."""
        self.clipe = nome
        self.t = float(t0)
        self.loop = loop
        self._fim = on_fim
        self._cb = on_quadro
        self._ult = -1
        self._desenhar()

    def duracao(self, nome):
        cab = dados()
        return len(cab['clipes'][nome]['quadros']) / float(cab['fps'])

    def pausar(self, seg):
        """Hit-stop: congela o desenho por `seg` segundos."""
        self._pausa = max(self._pausa, seg)

    def impacto(self, quadros=3, tremor=5):
        """Levou um golpe: pisca branco (quadros de impacto) e treme."""
        self._flash = int(quadros)
        self._tremor = int(tremor)
        self.clarao = 1.0

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None

    def on_parent(self, inst, pai):
        if pai is None:                         # saiu da tela (a cena acabou ou foi pulada)
            self.parar()

    def recortar(self, y0=None, y1=None):
        """Mostra so a faixa de altura y0..y1 (coordenadas do pai; None = sem
        limite). recortar() tira o recorte."""
        if y0 is None and y1 is None:
            if self._recorte is not None:
                for grupo, ins in self._recorte[0]:
                    for i in ins:
                        try:
                            grupo.remove(i)
                        except Exception:
                            pass
                self._recorte = None
            return
        a = -100000.0 if y0 is None else float(y0)
        b = 100000.0 if y1 is None else float(y1)
        if self._recorte is None:
            r1 = Rectangle(pos=(-100000, a), size=(200000, b - a))
            r2 = Rectangle(pos=(-100000, a), size=(200000, b - a))
            antes = [StencilPush(), r1, StencilUse()]
            depois = [StencilUnUse(), r2, StencilPop()]
            for i in antes:
                self.canvas.before.add(i)
            for i in depois:
                self.canvas.after.add(i)
            self._recorte = ([(self.canvas.before, antes), (self.canvas.after, depois)], (r1, r2))
        for r in self._recorte[1]:
            r.pos = (-100000, a)
            r.size = (200000, max(0.0, b - a))

    # ── pontos (coordenadas do pai) ──────────────────────────────────────
    def _indice(self):
        cab = dados()
        n = len(cab['clipes'][self.clipe]['quadros'])
        i = int(self.t * cab['fps'])
        return (i % n) if self.loop else min(i, n - 1)

    def _para_pai(self, sx, sy):
        qx, qy = dados()['quadril']
        dx = (sx - qx) * self.te
        return (self.ax - dx if self.espelhar else self.ax + dx), self.ay + (qy - sy) * self.te

    def ponta(self):
        """Ponta da lamina do montante neste quadro."""
        return self._para_pai(*quadro(self.clipe, self._indice())[3])

    def garra(self):
        """Meio das unhas da garra neste quadro."""
        return self._para_pai(*quadro(self.clipe, self._indice())[2])

    def ponto(self, nome):
        """'olho', 'nucleo' ou 'cabeca' (na pose parada)."""
        return self._para_pai(*dados()[nome])

    def corpo(self):
        """(x0, y0, x1, y1) do corpo (sem montante nem capa), no pai."""
        x0, x1, y_topo, y_pe = dados()['corpo']
        xa, ya = self._para_pai(x0, y_pe)
        xb, yb = self._para_pai(x1, y_topo)
        return min(xa, xb), ya, max(xa, xb), yb

    # ── desenho ──────────────────────────────────────────────────────────
    def _tique(self, dt):
        try:
            # o branco do impacto e o tremor correm mesmo no hit-stop
            if self._flash > 0:
                self._flash -= 1
                if self._flash <= 0:
                    self.clarao = 0.0
            if self._tremor > 0:
                self._tremor -= 1
                a = max(1, int(round(self.te * 2)))
                self._desvio = (random.choice((-a, 0, a)), random.choice((-a, 0, a))) if self._tremor else (0, 0)
                self._desenhar()
            if self._pausa > 0:
                self._pausa -= dt
                return True
            self.t += dt
            i = self._indice()
            if i != self._ult:
                self._ult = i
                self._desenhar()
                if self._cb is not None:
                    try:
                        self._cb(i)
                    except Exception as e:
                        print(f"[chefe] quadro: {e}")
            if not self.loop and self._fim is not None:
                cab = dados()
                if int(self.t * cab['fps']) >= len(cab['clipes'][self.clipe]['quadros']):
                    cb, self._fim = self._fim, None
                    try:
                        cb()
                    except Exception as e:
                        print(f"[chefe] fim do clipe: {e}")
            return True
        except Exception as e:
            print(f"[chefe] {e}")
            return True

    def _desenhar(self):
        try:
            cab = dados()
            tex, (x0, y0, w, h), _g, _p = quadro(self.clipe, self._indice())
            te = self.te
            qx, qy = cab['quadril']
            if self.espelhar:
                esq = self.ax - (x0 + w - qx) * te
            else:
                esq = self.ax + (x0 - qx) * te
            topo = self.ay + (qy - y0) * te
            px, py = round(esq + self._desvio[0]), round(topo - h * te + self._desvio[1])
            tc = tex.tex_coords
            if self.espelhar:
                tc = (tc[2], tc[3], tc[0], tc[1], tc[6], tc[7], tc[4], tc[5])
            self._ret.texture = tex
            self._ret.tex_coords = tc
            self._ret.pos = (px, py)
            self._ret.size = (round(w * te), round(h * te))
            self.pos = (px, py)
            self.size = self._ret.size
            if self.clarao > 0:
                sil = quadro(self.clipe, self._indice(), silhueta=True)[0]
                tcs = sil.tex_coords
                if self.espelhar:
                    tcs = (tcs[2], tcs[3], tcs[0], tcs[1], tcs[6], tcs[7], tcs[4], tcs[5])
                self._ret_cl.texture = sil
                self._ret_cl.tex_coords = tcs
                self._ret_cl.pos = self._ret.pos
                self._ret_cl.size = self._ret.size
                self._cor_cl.a = self.clarao
            else:
                self._cor_cl.a = 0
                self._ret_cl.size = (0, 0)
        except Exception as e:
            print(f"[chefe] desenhar: {e}")
