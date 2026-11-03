"""
chefe.py - O CHEFE da abertura ("THE ABYSS WARDEN"), o vilao do Yoru.

O desenho vem do MODELO FINAL do usuario, recortado em PECAS no PC
(dev/chefe_ref.py -> dev/chefe_rig.py exportar -> chefe/rig.bin). Aqui o app
MONTA o boneco na hora: cada peca e uma textura (pixel art, sem suavizar) e
vai para o lugar que a pose manda (chefe_poses.py: juntas que giram, pernas
que dobram, capa balancando). Tudo e montado primeiro numa tela pequena do
tamanho do desenho (1 ponto = 1 pixel dela) e so depois ampliado: os pixels
ficam sempre na grade, mesmo com as pecas giradas.
"""
import os
import json
import zlib
import random

from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Fbo, ClearColor, ClearBuffers, PushMatrix, PopMatrix
from kivy.graphics.context_instructions import MatrixInstruction
from kivy.graphics.transformation import Matrix
from kivy.graphics.texture import Texture
from kivy.graphics.stencil_instructions import StencilPush, StencilUse, StencilUnUse, StencilPop
from kivy.properties import NumericProperty, BooleanProperty

import chefe_poses as CP

_DADOS = {}
_TEX = {}
FPS = 30
COR_CLARAO = (1.0, 0.93, 0.86)


def dados():
    """Cabecalho de chefe/rig.bin (le uma vez)."""
    if 'cab' in _DADOS:
        return _DADOS['cab']
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chefe', 'rig.bin')
    with open(caminho, 'rb') as f:
        bruto = f.read()
    if bruto[:4] != b'CR01':
        raise ValueError('chefe/rig.bin de outra versao')
    n = int.from_bytes(bruto[4:8], 'little')
    cab = json.loads(zlib.decompress(bruto[8:8 + n]).decode('utf-8'))
    _DADOS['base'] = 8 + n
    _DADOS['bruto'] = bruto
    pal = cab['paleta']
    g = cab['lava']
    # 3 niveis de brasa: 0 = apagando, 1 = normal, 2 = aceso (so os indices da lava mudam)
    trocas = ({g[4]: g[3], g[3]: g[2], g[2]: g[1], g[1]: g[0]}, {}, {g[1]: g[2], g[2]: g[3], g[3]: g[4]})
    tabs = []
    for tr in trocas:
        t4 = [bytearray(256) for _ in range(4)]
        for i, c in enumerate(pal):
            c = pal[tr.get(i, i)]
            for k in range(4):
                t4[k][i] = c[k]
        tabs.append([bytes(t) for t in t4])
    _DADOS['tabs'] = tabs
    sil = bytearray(256)
    for i in range(1, len(pal)):
        sil[i] = 255
    _DADOS['sil'] = bytes(sil)
    _DADOS['lava'] = bytes(g)
    _DADOS['pts'] = {k: tuple(v) for k, v in cab['pontos'].items()}
    _DADOS['clipes'] = CP.clipes()
    _DADOS['cab'] = cab
    return cab


def _item(nome, i=None):
    cab = dados()
    if i is None:
        return cab['pecas'][nome]
    qual, modo = nome
    return cab['panos'][qual][modo]['quadros'][i]


def textura(nome, i=None, nivel=1):
    """(textura, caixa (x0, y0, w, h) na tela de trabalho) de uma peca (nome)
    ou de um desenho de pano ((qual, modo), i). nivel: 0/1/2 = brasa
    apagando/normal/acesa; 's' = silhueta branca (quadro de impacto)."""
    pos, tam, caixa = _item(nome, i)
    ch = (pos, nivel)
    tex = _TEX.get(ch)
    if tex is None:
        ini = _DADOS['base'] + pos
        idx = zlib.decompress(_DADOS['bruto'][ini:ini + tam])
        if nivel != 's' and nivel != 1 and not any(b in idx for b in _DADOS['lava']):
            tex = textura(nome, i, 1)[0]                  # peca sem lava: um desenho so
            _TEX[ch] = tex
            return tex, caixa
        buf = bytearray(len(idx) * 4)
        if nivel == 's':
            s = idx.translate(_DADOS['sil'])
            buf[0::4] = s
            buf[1::4] = s
            buf[2::4] = s
            buf[3::4] = s
        else:
            t = _DADOS['tabs'][nivel]
            buf[0::4] = idx.translate(t[0])
            buf[1::4] = idx.translate(t[1])
            buf[2::4] = idx.translate(t[2])
            buf[3::4] = idx.translate(t[3])
        tex = Texture.create(size=(caixa[2], caixa[3]), colorfmt='rgba')
        tex.mag_filter = tex.min_filter = 'nearest'
        tex.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
        tex.flip_vertical()                             # as linhas vem de cima para baixo
        _TEX[ch] = tex
    return tex, caixa


def aquecer(nomes=None, por_quadro=2, on_fim=None):
    """Cria antes as texturas (pecas nos 3 niveis de brasa e os desenhos do
    pano), `por_quadro` por quadro da tela: nada e montado no meio da luta.
    (`nomes` ficou do chefe antigo, que aquecia clipe por clipe: e ignorado.)"""
    try:
        cab = dados()
    except Exception as e:
        print(f"[chefe] aquecer: {e}")
        return
    fila = []
    for nome in cab['ordem']:
        if nome in cab['pecas']:
            fila += [(nome, None, n) for n in (1, 2, 0, 's')]
    for qual, modos in cab['panos'].items():
        for modo, d in modos.items():
            fila += [((qual, modo), i, 1) for i in range(len(d['quadros']))]
    fila = [f for f in fila if (_item(f[0], f[1])[0], f[2]) not in _TEX]

    def _passo(dt):
        try:
            for _ in range(por_quadro):
                if not fila:
                    if on_fim:
                        on_fim()
                    return False
                textura(*fila.pop(0))
        except Exception as e:
            print(f"[chefe] aquecer: {e}")
            return False
    Clock.schedule_interval(_passo, 0)


def soltar_texturas():
    """Libera as texturas (depois da abertura o chefe nao aparece mais)."""
    _TEX.clear()


class ChefePixel(Widget):
    """O chefe na tela. `te` = px de tela por pixel do desenho. ancorar(x, y)
    poe os pes dele (o meio, no chao) nesse ponto. Olha para a ESQUERDA;
    espelhar=True vira para a direita. pos/size do widget acompanham o
    desenho (a explosao em cacos fotografa o widget)."""
    espelhar = BooleanProperty(False)
    clarao = NumericProperty(0.0)           # 0..1: silhueta clara por cima (quadro de impacto)

    def __init__(self, te=1.0, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        cab = dados()
        self.te = float(te)
        self.ax, self.ay = 0.0, 0.0
        self.clipe = 'idle'
        self.t = 0.0
        self.loop = True
        self.inclina_capa = 0.0             # graus a mais na capa (a cena usa nas arrancadas)
        self.cor_clarao = COR_CLARAO        # a tinta da silhueta do quadro de impacto
        # vida propria: molas que atrasam a capa, a cabeca e o braco conforme o corpo anda
        self._mola = {'capa': [0.0, 0.0], 'cab': [0.0, 0.0], 'braco': [0.0, 0.0]}
        self._x_ant = None
        self._rastro_esp = []               # onde a lamina estava nos ultimos desenhos (imagens-fantasma)
        self._fim = None
        self._cb = None
        self._ult = -1
        self._chave = None
        self._pausa = 0.0
        self._tremor = 0
        self._desvio = (0, 0)
        self._recorte = None
        self._flash = 0
        self._pontos = None
        self._caixa = (0, 0, 1, 1)
        self._no_ar = False
        self.CW, self.CH = cab['tela']
        with self.canvas:                       # a telinha tem de estar na arvore de desenho para se redesenhar
            self._fbo = Fbo(size=(self.CW, self.CH))
        self._fbo.texture.mag_filter = 'nearest'
        self._fbo.texture.min_filter = 'nearest'
        self._inst = {}
        self._fant = []
        with self._fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            self._cor_fbo = Color(1, 1, 1, 1)
            for nome in cab['ordem']:
                if nome == 'espada':            # atras da lamina: as imagens-fantasma dela (rastro do golpe)
                    for rgb in ((0.42, 0.07, 0.09), (0.78, 0.2, 0.16)):     # a propria lamina, tingida de brasa
                        cf = Color(rgb[0], rgb[1], rgb[2], 0)
                        PushMatrix()
                        mf = MatrixInstruction()
                        rf = Rectangle(pos=(0, 0), size=(0, 0))
                        PopMatrix()
                        self._fant.append((cf, mf, rf))
                    self._cor_fbo2 = Color(1, 1, 1, 1)
                PushMatrix()
                mi = MatrixInstruction()
                r = Rectangle(pos=(0, 0), size=(0, 0))
                PopMatrix()
                self._inst[nome] = (mi, r)
        with self.canvas:
            self._cor = Color(1, 1, 1, 1)
            self._ret = Rectangle(pos=(0, 0), size=(0, 0), texture=self._fbo.texture)
        self.bind(espelhar=lambda *_: self._desenhar(True), clarao=lambda *_: self._desenhar(True))
        self._ev = Clock.schedule_interval(self._tique, 1 / 60.)
        self._desenhar(True)

    # ── controle ─────────────────────────────────────────────────────────
    def ancorar(self, x, y):
        self.ax, self.ay = float(x), float(y)
        self._posicionar()

    def tocar(self, nome, loop=False, on_fim=None, on_quadro=None, t0=0.0):
        """Toca o movimento `nome` (chefe_poses.clipes). loop=False: para no
        fim e chama on_fim. on_quadro(i) a cada 1/30 s."""
        if nome not in _DADOS['clipes']:
            print(f"[chefe] clipe desconhecido: {nome}")
            nome = 'idle'
        self.clipe = nome
        self.t = float(t0)
        self.loop = loop
        self._fim = on_fim
        self._cb = on_quadro
        self._ult = -1
        self._desenhar()

    def duracao(self, nome):
        return _DADOS['clipes'][nome][1]

    def pausar(self, seg):
        """Hit-stop: congela o desenho por `seg` segundos."""
        self._pausa = max(self._pausa, seg)

    def impacto(self, quadros=3, tremor=5):
        """Levou um golpe: pisca claro (quadros de impacto) e treme."""
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
        dur = _DADOS['clipes'][self.clipe][1]
        n = max(1, int(round(dur * FPS)))
        i = int(self.t * FPS)
        return (i % n) if self.loop else min(i, n - 1)

    def _para_pai(self, sx, sy):
        qx, qy = dados()['pes']
        dx = (sx - qx) * self.te
        return (self.ax - dx if self.espelhar else self.ax + dx), self.ay + (qy - sy) * self.te

    def _ponto_agora(self, nome):
        if self._pontos is None:
            self._desenhar(True)
        return self._para_pai(*self._pontos[nome])

    def ponta(self):
        """Ponta da lamina do montante agora."""
        return self._ponto_agora('ponta')

    def garra(self):
        """Meio das unhas da garra agora."""
        return self._ponto_agora('garra')

    def mao(self):
        """A mao que segura o montante agora."""
        return self._ponto_agora('mao')

    def ponto(self, nome):
        """'olho', 'nucleo', 'cabeca', 'ombro' (onde estao agora)."""
        return self._ponto_agora(nome)

    def corpo(self):
        """(x0, y0, x1, y1) do corpo (sem montante nem capa), no pai."""
        x0, x1, y_topo, y_pe = dados()['corpo']
        xa, ya = self._para_pai(x0, y_pe)
        xb, yb = self._para_pai(x1, y_topo)
        return min(xa, xb), ya, max(xa, xb), yb

    # ── desenho ──────────────────────────────────────────────────────────
    def _tique(self, dt):
        try:
            # o claro do impacto e o tremor correm mesmo no hit-stop
            if self._flash > 0:
                self._flash -= 1
                if self._flash <= 0:
                    self.clarao = 0.0
            if self._tremor > 0:
                self._tremor -= 1
                a = max(1, int(round(self.te * 3)))
                self._desvio = (random.choice((-a, 0, a)), random.choice((-a, 0, a))) if self._tremor else (0, 0)
                self._posicionar()
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
                if self.t >= _DADOS['clipes'][self.clipe][1]:
                    cb, self._fim = self._fim, None
                    try:
                        cb()
                    except Exception as e:
                        print(f"[chefe] fim do clipe: {e}")
            return True
        except Exception as e:
            print(f"[chefe] {e}")
            return True

    def _desenhar(self, forcar=False):
        """Monta as pecas na pose de agora (so refaz quando a pose muda)."""
        try:
            cab = dados()
            fn, dur, _loop = _DADOS['clipes'][self.clipe]
            t = self._indice() / float(FPS)
            q, tc, vento = fn(t)
            modo = CP.modo_capa(vento)
            panos = cab['panos']
            dc = panos['capa'][modo]
            i_capa = int(tc * dc['por_s']) % len(dc['quadros'])
            mt = 'calmo' if modo == 'calmo' else 'vento'
            dt_ = panos['tabardo'][mt]
            i_tab = int(tc * dt_['por_s']) % len(dt_['quadros'])
            claro = self.clarao > 0
            nivel = 's' if claro else int(q.get('brilho', 1))
            chave = (tuple(sorted((k, round(v, 2) if isinstance(v, float) else v) for k, v in q.items()
                                  if not isinstance(v, tuple))), modo, i_capa, i_tab, nivel,
                     round(self.inclina_capa, 1), tuple(self.cor_clarao) if claro else None, self._ult)
            if chave == self._chave and not forcar:
                return
            self._chave = chave
            q = self._vivo(q)
            M, pontos = CP.matrizes(q, _DADOS['pts'])
            self._pontos = pontos
            self._no_ar = bool(q.get('ar'))
            inc = self.inclina_capa + self._mola['capa'][0]
            if abs(inc) > 0.4:
                M['capa'] = CP.mul(M['capa'], CP.rot(tuple(cab['raiz_capa']), round(inc)))
                M['tabardo'] = CP.mul(M['tabardo'], CP.rot(tuple(cab['raiz_tab']), round(inc * 0.6)))
            CH_ = self.CH
            x0 = y0 = 10 ** 9
            x1 = y1 = -10 ** 9
            for nome in cab['ordem']:
                mi, r = self._inst[nome]
                if nome == 'capa':
                    tex, (bx, by, bw, bh) = textura(('capa', modo), i_capa, 's' if claro else 1)
                elif nome == 'tabardo':
                    tex, (bx, by, bw, bh) = textura(('tabardo', mt), i_tab, 's' if claro else 1)
                else:
                    tex, (bx, by, bw, bh) = textura(nome, None, nivel)
                a, b, tx, c, d, ty = M[nome]
                if abs(b) < 1e-9 and abs(c) < 1e-9:           # so desloca: passos inteiros
                    tx, ty = round(tx), round(ty)
                # a tela de trabalho tem o y para baixo; a do Fbo, para cima
                m = Matrix()
                m.set(flat=[a, -c, 0, 0, -b, d, 0, 0, 0, 0, 1, 0, tx + b * CH_, CH_ * (1 - d) - ty, 0, 1])
                mi.matrix = m
                r.texture = tex
                r.pos = (bx, CH_ - by - bh)
                r.size = (bw, bh)
                for px, py in ((bx, by), (bx + bw, by), (bx, by + bh), (bx + bw, by + bh)):
                    X, Y = a * px + b * py + tx, c * px + d * py + ty
                    x0, x1, y0, y1 = min(x0, X), max(x1, X), min(y0, Y), max(y1, Y)
            self._cor_fbo.rgb = tuple(self.cor_clarao) if claro else (1, 1, 1)
            self._cor_fbo2.rgb = self._cor_fbo.rgb
            self._fantasmas(M['espada'], claro)
            chao = cab['pes'][1] + 3
            self._caixa = (max(0, int(x0) - 1), max(0, int(y0) - 1), min(self.CW, int(x1) + 2),
                           min(self.CH if self._no_ar else chao, int(y1) + 2))
            self._fbo.ask_update()
            self._posicionar()
        except Exception as e:
            print(f"[chefe] desenhar: {e}")

    def _vivo(self, q):
        """Atraso e balanco (uma vez por desenho): a capa e o tabardo ficam
        para tras quando o corpo arranca e passam do ponto quando ele para; a
        cabeca e o braco da garra chegam um instante depois do tronco."""
        try:
            x = (-self.ax if self.espelhar else self.ax) / self.te + (q.get('hx', 0) + q.get('dx', 0)) * CP.ESC \
                - q.get('giro', 0.0) * 2.2
            if self._x_ant is None or abs(x - self._x_ant) > 400:
                self._x_ant = x
            v = x - self._x_ant                          # pontos por desenho (para a esquerda = negativo)
            self._x_ant = x
            for nome, ganho, rig, amort, lim in (('capa', 0.55, 0.20, 0.72, 26.0), ('cab', -0.22, 0.34, 0.6, 9.0),
                                                 ('braco', 0.5, 0.26, 0.7, 20.0)):
                m = self._mola[nome]
                alvo = max(-lim, min(lim, v * ganho))
                m[1] = (m[1] + (alvo - m[0]) * rig) * amort
                m[0] = max(-lim, min(lim, m[0] + m[1]))
            q = dict(q)
            q['c'] = q.get('c', 0.0) + round(self._mola['cab'][0])
            q['a'] = q.get('a', 0.0) + round(self._mola['braco'][0])
            q['b'] = q.get('b', 0.0) + round(self._mola['braco'][0] * 0.5)
        except Exception as e:
            print(f"[chefe] vivo: {e}")
        return q

    def _fantasmas(self, Me, claro):
        """Imagens-fantasma da lamina: quando ela gira depressa, os dois ou
        tres desenhos anteriores ficam atras dela em tons de brasa (o rastro
        do golpe, desenhado com a propria lamina)."""
        try:
            import math
            ang = math.degrees(math.atan2(Me[3], Me[0]))
            hist = self._rastro_esp
            rapido = bool(hist) and abs((ang - hist[-1][0] + 180) % 360 - 180) > 13.0
            if not rapido:
                del hist[:]                              # so nos quadros em que a lamina voa
            tex, (bx, by, bw, bh) = textura('espada', None, 2)
            usados = hist[-2:]
            for i, (cf, mf, rf) in enumerate(self._fant):
                j = i - (2 - len(usados))
                if j < 0 or claro:
                    cf.a = 0
                    rf.size = (0, 0)
                    continue
                a, b, tx, c, d, ty = usados[j][1]
                m = Matrix()
                m.set(flat=[a, -c, 0, 0, -b, d, 0, 0, 0, 0, 1, 0, tx + b * self.CH, self.CH * (1 - d) - ty, 0, 1])
                mf.matrix = m
                rf.texture = tex
                rf.pos = (bx, self.CH - by - bh)
                rf.size = (bw, bh)
                cf.a = 1
            hist.append((ang, tuple(Me)))
            del hist[:-3]
        except Exception as e:
            print(f"[chefe] rastro: {e}")

    def _posicionar(self):
        """Poe na tela o pedaco da telinha onde esta o desenho."""
        try:
            x0, y0, x1, y1 = self._caixa
            te = self.te
            qx, qy = dados()['pes']
            w, h = x1 - x0, y1 - y0
            if self.espelhar:
                esq = self.ax - (x1 - qx) * te
            else:
                esq = self.ax + (x0 - qx) * te
            topo = self.ay + (qy - y0) * te
            px, py = round(esq + self._desvio[0]), round(topo - h * te + self._desvio[1])
            u0, u1 = x0 / float(self.CW), x1 / float(self.CW)
            v0, v1 = (self.CH - y1) / float(self.CH), (self.CH - y0) / float(self.CH)
            if self.espelhar:
                u0, u1 = u1, u0
            self._ret.tex_coords = (u0, v0, u1, v0, u1, v1, u0, v1)
            self._ret.pos = (px, py)
            self._ret.size = (round(w * te), round(h * te))
            self.pos = (px, py)
            self.size = self._ret.size
        except Exception as e:
            print(f"[chefe] posicionar: {e}")
