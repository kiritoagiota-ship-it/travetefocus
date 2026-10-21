"""
menu_hud.py — TraveteFocus
O menu no modelo HUD (1.10): cabecalho com a moldura HUD e o nome, painel
de 3 quadros (hoje / nivel / sequencia), SYSTEM LINK START com o
capacete NerveGear, cartoes 2x2 com cenas em pixel art animadas, botoes com
icone e o rodape com a versao.

A pixel art e feita em codigo (Px): cada quadro de cada animacao vira uma
textura pronta (guardada) e animar e so trocar a textura. Um relogio so
(30/s) anima tudo, e so o que esta na tela.
"""
import math
import random
import weakref

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Line, Mesh, PushMatrix, PopMatrix, Scale
from kivy.graphics.texture import Texture
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.metrics import dp, sp
from kivy.clock import Clock

from efeitos import BotaoAngular, BotaoAngularMenu, textura_mapa, _render_texto
import tatil


def _chanfro(x, y, w, h, c):
    return [x + c, y, x + w - c, y, x + w, y + c, x + w, y + h - c,
            x + w - c, y + h, x + c, y + h, x, y + h - c, x, y + c]


def _chanfro4(x, y, w, h, ce, cd, be, bd):
    """Chanfro com um corte diferente em cada canto (cima-esq, cima-dir,
    baixo-esq, baixo-dir)."""
    return [x + be, y, x + w - bd, y, x + w, y + bd, x + w, y + h - cd,
            x + w - cd, y + h, x + ce, y + h, x, y + h - ce, x, y + be]


def _leque(pts):
    vs = []
    for i in range(0, len(pts), 2):
        vs += [pts[i], pts[i + 1], 0, 0]
    return vs, list(range(len(pts) // 2))


# ═══════════════════════════════════════════════════════════
#  RELOGIO UNICO
# ═══════════════════════════════════════════════════════════
class _Relogio:
    """Chama tique(t) de quem se inscreveu, 30x/s, so de quem esta na tela."""

    def __init__(self):
        self.ws = []
        self.t = 0.0
        self.ev = None

    def add(self, w):
        self.ws.append(weakref.ref(w))
        if self.ev is None:
            self.ev = Clock.schedule_interval(self._tique, 1 / 30.)

    def _tique(self, dt):
        self.t += min(dt, 0.1)
        vivos = []
        for r in self.ws:
            w = r()
            if w is None:
                continue
            vivos.append(r)
            try:
                if w.get_root_window() is not None:
                    w.tique(self.t)
            except Exception as e:
                print(f"[menu_hud] tique: {e}")
        self.ws = vivos
        if not vivos:
            self.ev = None
            return False


RELOGIO = _Relogio()


# ═══════════════════════════════════════════════════════════
#  TEXTURAS DE APOIO (degrade e brilho redondo)
# ═══════════════════════════════════════════════════════════
_TEX = {}


def _tex_degrade():
    """64x1: opaco a esquerda -> transparente a direita."""
    t = _TEX.get('degrade')
    if t is None:
        n = 64
        buf = bytearray()
        for i in range(n):
            a = 1.0 - i / float(n - 1)
            a = a * a * (3 - 2 * a)
            buf += bytes((255, 255, 255, int(255 * a)))
        dados = bytes(buf)
        t = Texture.create(size=(n, 1), colorfmt='rgba')
        t.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
        t.add_reload_observer(lambda tx: tx.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte'))
        _TEX['degrade'] = t
    return t


# ═══════════════════════════════════════════════════════════
#  PIXEL ART EM CODIGO
# ═══════════════════════════════════════════════════════════
class Px:
    """Grade de pixel art (y=0 em cima) com formas simples e contorno."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [['.'] * w for _ in range(h)]

    def p(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[y][x] = c

    def get(self, x, y):
        return self.g[y][x] if (0 <= x < self.w and 0 <= y < self.h) else '.'

    def ret(self, x, y, w, h, c):
        for j in range(y, y + h):
            for i in range(x, x + w):
                self.p(i, j, c)

    def linha(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        e = dx + dy
        while True:
            self.p(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * e
            if e2 >= dy:
                e += dy
                x0 += sx
            if e2 <= dx:
                e += dx
                y0 += sy

    def circ(self, cx, cy, r, c):
        for j in range(int(cy - r), int(cy + r) + 1):
            for i in range(int(cx - r), int(cx + r) + 1):
                if (i - cx) ** 2 + (j - cy) ** 2 <= r * r + r * 0.6:
                    self.p(i, j, c)

    def contorno(self, c='K'):
        marca = []
        for y in range(self.h):
            for x in range(self.w):
                if self.g[y][x] != '.':
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    v = self.get(x + dx, y + dy)
                    if v not in '.' and v != c:
                        marca.append((x, y))
                        break
        for x, y in marca:
            self.g[y][x] = c

    def copia(self):
        n = Px(self.w, self.h)
        n.g = [list(r) for r in self.g]
        return n

    def mapa(self):
        return [''.join(r) for r in self.g]


def _brilho_mapas(mapa, vazios=8, larg=2, nao=('K', '.')):
    """Quadros de uma faixa de luz diagonal passando pelo desenho (e alguns
    quadros sem luz: a luz passa de tempos em tempos)."""
    h, w = len(mapa), len(mapa[0])
    quadros = [list(mapa)]
    for k in range(-larg, w + h, 2):
        q = []
        for j, linha in enumerate(mapa):
            s = list(linha)
            for i, ch in enumerate(s):
                if ch not in nao and k <= i + (h - 1 - j) < k + larg:
                    s[i] = 'W'
            q.append(''.join(s))
        quadros.append(q)
    quadros += [list(mapa)] * vazios
    return quadros


# paletas (letra -> cor)
_P_CIANO = {'K': (0.01, 0.04, 0.09), 'l': (0.55, 0.95, 1.0), 'c': (0.0, 0.8, 1.0),
            'd': (0.0, 0.42, 0.66), 'W': (1, 1, 1), 'w': (0.82, 0.95, 1.0), 'G': (0.25, 1.0, 0.45),
            'f': (0.62, 0.32, 1.0), 's': (0.02, 0.1, 0.2), 'r': (1.0, 0.25, 0.35), 'z': (0.75, 1.0, 1.0),
            'e': (0.0, 0.26, 0.4), 'k': (0.0, 0.18, 0.3)}
_P_ROXO = {'K': (0.04, 0.01, 0.09), 'l': (0.86, 0.72, 1.0), 'c': (0.66, 0.36, 1.0),
           'd': (0.38, 0.14, 0.72), 'W': (1, 1, 1), 'b': (0.62, 0.3, 1.0), 'B': (0.38, 0.12, 0.7),
           'z': (0.9, 0.8, 1.0), 'e': (0.25, 0.08, 0.45)}
_P_LARANJA = {'K': (0.1, 0.04, 0.0), 'c': (1.0, 0.55, 0.08), 'd': (0.62, 0.3, 0.0),
              'w': (1.0, 0.88, 0.7), 'k': (0.7, 0.55, 0.4), 'W': (1, 1, 1), 'o': (0.55, 0.3, 0.0),
              'V': (1.0, 0.72, 0.0), 'z': (1.0, 0.85, 0.5), 'e': (0.4, 0.2, 0.0)}
_P_VERDE = {'K': (0.0, 0.07, 0.03), 'g': (0.0, 0.75, 0.4), 'h': (0.0, 0.5, 0.28), 'd': (0.0, 0.33, 0.18),
            'n': (0.55, 1.0, 0.7), 'y': (1.0, 0.85, 0.2), 'W': (1, 1, 1), 'z': (0.6, 1.0, 0.75),
            'e': (0.0, 0.3, 0.15)}
_P_CINZA = {'K': (0.03, 0.03, 0.05), 'l': (0.55, 0.6, 0.68), 'c': (0.4, 0.44, 0.52), 'd': (0.25, 0.27, 0.33),
            'W': (0.8, 0.82, 0.88), 's': (0.08, 0.08, 0.12), 'r': (1.0, 0.25, 0.35), 'k': (0.2, 0.2, 0.26)}


# ── icones ───────────────────────────────────────────────────
def _m_pilha():
    return ["...KKKKKKKK...",
            "..KllllllllK..",
            ".KccccccccccK.",
            ".KddddddddddK.",
            "..KKKKKKKKKK..",
            ".KllllllllllK.",
            "KccccccccccccK",
            "KddddddddddddK",
            ".KKKKKKKKKKKK.",
            "KllllllllllllK",
            "KccccccccccccK",
            "KddddddddddddK",
            ".KKKKKKKKKKKK."]


def _q_nivel():
    base = [".....KK.....",
            "....KllK....",
            "...KlccdK...",
            "..KlcKKcdK..",
            ".KlcK..KcdK.",
            "KlcK.KK.KcdK",
            "KKK.KllK.KKK",
            "...KlccdK...",
            "..KlcKKcdK..",
            ".KlcK..KcdK.",
            ".KKK....KKK."]

    def acende(rows):
        q = []
        for j, ln in enumerate(base):
            if j in rows:
                ln = ln.replace('l', 'W').replace('c', 'l')
            q.append(ln)
        return q
    # a luz sobe: a seta de baixo acende, depois a de cima
    return [base, base, acende(range(6, 11)), acende(range(0, 6)), base, base]


_MAPA_CAL = ["..k.....k...",
             "KKkKKKKKkKKK",
             "KcccccccccdK",
             "KKKKKKKKKKKK",
             "KwwwwwwwwwwK",
             "KwKwwKwwKwwK",
             "KwwwwwwwwwwK",
             "KwKwwKwwKwwK",
             "KwwwwwwwwwwK",
             "KKKKKKKKKKKK"]


def _q_calendario():
    dias = [(2, 5), (5, 5), (8, 5), (2, 7), (5, 7), (8, 7)]
    quadros = []
    for i in range(len(dias)):
        q = [list(r) for r in _MAPA_CAL]
        x, y = dias[i]
        q[y][x] = 'c'
        quadros.append([''.join(r) for r in q])
    return quadros


def _q_setas(n=3, larg=2):
    """Chevrons >>> que acendem em sequencia ('z' aceso, 'e' apagado)."""
    w = n * 4 + 1
    base = []
    for j, dx in enumerate((0, 1, 2, 1, 0)):
        s = ['.'] * w
        for k in range(n):
            for d in range(larg):
                x = k * 4 + dx + d
                if x < w:
                    s[x] = str(k)
        base.append(s)
    quadros = []
    for aceso in list(range(n)) + [-1]:
        q = []
        for s in base:
            q.append(''.join(('z' if ch == str(aceso) else 'e') if ch.isdigit() else '.' for ch in s))
        quadros.append(q)
    return quadros


def _m_vibrar(ligado, onda=0):
    p = Px(16, 13)
    p.ret(5, 0, 6, 13, 'c')
    p.ret(6, 1, 4, 9, 's')
    p.p(7, 11, 'l')
    p.p(8, 11, 'l')
    if ligado:
        o = 1 if onda else 0
        p.linha(3 - o, 3, 3 - o, 9, 'l')
        p.linha(12 + o, 3, 12 + o, 9, 'l')
        if onda:
            p.linha(3, 5, 3, 7, 'l')
            p.linha(12, 5, 12, 7, 'l')
    p.contorno()
    if not ligado:
        p.linha(1, 12, 14, 0, 'r')
    return p.mapa()


def _m_sino(ligado, dx=0):
    p = Px(15, 14)
    p.ret(6, 0, 3, 1, 'c')
    linhas = [(5, 1, 5), (4, 2, 7), (4, 3, 7), (4, 4, 7), (4, 5, 7), (3, 6, 9), (3, 7, 9), (2, 8, 11), (1, 9, 13)]
    for x, y, w in linhas:
        d = dx if y >= 5 else 0
        p.ret(x + d, y, w, 1, 'c')
    p.ret(4 + dx, 2, 1, 5, 'l')
    p.ret(6 + dx * 2, 10, 3, 2, 'l')
    p.contorno()
    if not ligado:
        p.linha(1, 13, 14, 0, 'r')
    return p.mapa()


def _m_cadeado():
    p = Px(11, 13)
    p.ret(3, 0, 5, 1, 'l')
    p.ret(2, 1, 1, 5, 'l')
    p.ret(8, 1, 1, 5, 'l')
    p.ret(1, 5, 9, 8, 'c')
    p.ret(1, 5, 9, 1, 'l')
    p.ret(5, 8, 1, 3, 'k')
    p.p(5, 7, 'k')
    p.contorno()
    return p.mapa()


# ── cenas (fundo dos cartoes) ────────────────────────────────
W_CENA, H_CENA = 56, 32


def _q_cena_memorias():
    """Cidade a noite com o Yoru sentado no alto de um predio olhando a lua;
    as janelas acendem e apagam, as estrelas piscam."""
    rng = random.Random(7)
    base = Px(W_CENA, H_CENA)
    estrelas = [(rng.randrange(0, W_CENA), rng.randrange(0, 12)) for _ in range(14)]
    base.circ(46, 7, 4.2, 'm')
    base.circ(48, 6, 3.6, '.')
    predios, janelas = [], []
    x = 0
    while x < W_CENA:
        w = rng.randint(4, 8)
        h = rng.randint(9, 22)
        if 14 <= x <= 20:
            h = 24                                    # o predio do Yoru
        predios.append((x, w, h))
        x += w + rng.randint(0, 1)
    for (x, w, h) in predios:
        base.ret(x, H_CENA - h, w, h, 'b')
        base.ret(x + w - 1, H_CENA - h, 1, h, 'B')
        for wy in range(H_CENA - h + 2, H_CENA - 1, 3):
            for wx in range(x + 1, x + w - 1, 2):
                janelas.append((wx, wy))
    # o Yoru sentado na beira do predio alto (silhueta)
    alto = max(predios, key=lambda p: p[2])
    fx, fy = alto[0] + alto[1] - 3, H_CENA - alto[2] - 6
    base.ret(fx, fy, 3, 2, 'k')                       # cabeca
    base.p(fx - 1, fy, 'k')                           # cabelo
    base.p(fx + 1, fy + 1, 'm')                       # o olho aceso
    base.ret(fx - 1, fy + 2, 4, 4, 'k')               # corpo
    base.ret(fx + 3, fy + 5, 2, 1, 'k')               # perna na beira
    base.ret(fx + 4, fy + 6, 1, 2, 'k')
    quadros = []
    for f in range(6):
        q = base.copia()
        r2 = random.Random(100 + f)
        for (wx, wy) in janelas:
            q.p(wx, wy, 'w' if r2.random() < 0.38 else 'B')
        for i, (sx, sy) in enumerate(estrelas):
            if q.get(sx, sy) == '.' and (i + f) % 3:
                q.p(sx, sy, 's')
        quadros.append(q.mapa())
    return quadros


def _q_cena_progresso():
    """Montanhas com a bandeira no pico mais alto (balancando) e estrelas."""
    rng = random.Random(3)
    base = Px(W_CENA, H_CENA)
    estrelas = [(rng.randrange(0, W_CENA), rng.randrange(0, 14)) for _ in range(16)]
    for x in range(W_CENA):
        h1 = int(13 + 4 * math.sin(x * 0.21) + 3 * math.sin(x * 0.53 + 1))
        base.ret(x, H_CENA - h1, 1, h1, 'f')
    pico = 34
    for x in range(W_CENA):
        d = abs(x - pico)
        h2 = int(max(5, 25 - d * 1.15 + 2 * math.sin(x * 0.7)))
        if x < 14:
            h2 = int(max(h2, 12 - abs(x - 7) * 1.3))
        base.ret(x, H_CENA - h2, 1, h2, 'n')
        base.ret(x, H_CENA - h2, 1, 2 if d < 6 else 1, 'w' if d < 6 else 'N')
    topo = H_CENA - 25
    base.ret(pico, topo - 7, 1, 7, 'w')               # o mastro
    quadros = []
    for f in range(4):
        q = base.copia()
        if f % 2 == 0:
            q.ret(pico + 1, topo - 7, 4, 2, 'c')
            q.p(pico + 5, topo - 6, 'c')
        else:
            q.ret(pico + 1, topo - 7, 3, 2, 'c')
            q.ret(pico + 4, topo - 6, 2, 2, 'c')
        for i, (sx, sy) in enumerate(estrelas):
            if q.get(sx, sy) == '.' and (i + f) % 4:
                q.p(sx, sy, 's')
        quadros.append(q.mapa())
    return quadros


def _q_cena_ganhos():
    """Pilhas de moedas e uma nota, com um brilho passando pelas moedas."""
    base = Px(W_CENA, H_CENA)
    base.ret(4, 20, 16, 10, 'h')                       # a nota
    base.ret(5, 21, 14, 8, 'n')
    base.ret(10, 23, 4, 4, 'h')
    topos = []
    rng = random.Random(5)
    for x0, n in ((20, 5), (32, 8), (44, 6)):
        y = H_CENA - 2
        for c in range(n):
            dx = rng.choice((0, 0, 1, -1))
            base.ret(x0 + dx, y, 10, 1, 'd')              # a borda da moeda
            base.ret(x0 + dx + 1, y - 1, 8, 1, 'g')
            base.p(x0 + dx, y - 1, 'd')
            base.p(x0 + dx + 9, y - 1, 'd')
            y -= 2
        # a moeda de cima: a face oval com o brilho
        base.ret(x0 + 1, y, 8, 1, 'g')
        base.ret(x0, y - 1, 10, 1, 'Y')
        base.ret(x0 + 1, y - 2, 8, 1, 'Y')
        base.ret(x0 + 3, y - 1, 4, 1, 'n')
        base.p(x0, y, 'd')
        base.p(x0 + 9, y, 'd')
        topos.append((x0 + 5, y - 2))
    # uma moeda solta, de pe, na frente
    base.circ(14, H_CENA - 5, 3.2, 'd')
    base.circ(14, H_CENA - 5, 2.2, 'g')
    base.ret(13, H_CENA - 7, 2, 4, 'Y')
    base.ret(0, H_CENA - 1, W_CENA, 1, 'd')
    quadros = []
    for f in range(8):
        q = base.copia()
        if f < len(topos) * 2:
            tx, ty = topos[f // 2]
            r = 1 + (f % 2)
            q.p(tx, ty - 1, 'W')
            for d in range(1, r + 1):
                for vx, vy in ((d, 0), (-d, 0), (0, d), (0, -d)):
                    q.p(tx + vx, ty - 1 + vy, 'W' if d == 1 else 'n')
        quadros.append(q.mapa())
    return quadros


def _q_cena_calculadora():
    """A maquina de costura grande: a agulha sobe e desce e o tecido anda."""
    base = Px(W_CENA, H_CENA)
    base.ret(0, 28, W_CENA, 4, 't')
    base.ret(14, 23, 36, 5, 'm')
    base.ret(14, 23, 36, 1, 'l')
    base.ret(40, 8, 7, 15, 'm')
    base.ret(16, 7, 31, 6, 'm')
    base.ret(16, 7, 31, 1, 'l')
    base.ret(15, 7, 7, 13, 'm')
    base.ret(15, 7, 1, 13, 'l')
    base.circ(49, 11, 4, 'd')
    base.circ(49, 11, 1.2, 'l')
    base.ret(27, 3, 3, 4, 's')
    base.linha(28, 3, 18, 7, 's')
    quadros = []
    for f, ag in enumerate((1, 2, 4, 2)):
        q = base.copia()
        q.ret(18, 20, 1, ag, 'W')
        q.ret(2, 22, 30, 1, 'f')
        for x in range(2 + (f * 1) % 3, 32, 3):
            q.p(x, 22, 'F')
        quadros.append(q.mapa())
    return quadros


_P_CENA = {
    'memorias': {'b': (0.17, 0.07, 0.34), 'B': (0.1, 0.04, 0.21), 'w': (0.86, 0.62, 1.0), 'm': (0.92, 0.85, 1.0),
                 's': (0.8, 0.72, 1.0), 'k': (0.03, 0.01, 0.07)},
    'progresso': {'f': (0.08, 0.2, 0.42), 'n': (0.05, 0.11, 0.27), 'N': (0.12, 0.3, 0.55), 'w': (0.72, 0.88, 1.0),
                  'c': (0.0, 0.9, 1.0), 's': (0.7, 0.9, 1.0)},
    'ganhos': {'g': (0.12, 0.78, 0.42), 'd': (0.03, 0.36, 0.18), 'Y': (0.6, 1.0, 0.72), 'h': (0.04, 0.3, 0.16),
               'n': (0.15, 0.5, 0.28), 'W': (1, 1, 1)},
    'calculadora': {'t': (0.25, 0.11, 0.0), 'm': (0.72, 0.38, 0.04), 'l': (1.0, 0.66, 0.22), 'd': (0.45, 0.22, 0.02),
                    's': (1.0, 0.85, 0.5), 'f': (0.85, 0.5, 0.12), 'F': (1.0, 0.92, 0.65), 'W': (1, 1, 1)},
}

_QUADROS = {}


def quadros(nome):
    """Lista de texturas (os quadros) de cada desenho, feitas uma vez."""
    q = _QUADROS.get(nome)
    if q is not None:
        return q
    mapas, cores = None, None
    if nome == 'pilha':
        mapas, cores = _brilho_mapas(_m_pilha()), _P_CIANO
    elif nome == 'nivel':
        mapas, cores = _q_nivel(), _P_ROXO
    elif nome == 'calendario':
        mapas, cores = _q_calendario(), _P_LARANJA
    elif nome.startswith('setas2_'):
        cor = nome.split('_', 1)[1]
        pal = {'roxo': _P_ROXO, 'ciano': _P_CIANO, 'verde': _P_VERDE, 'laranja': _P_LARANJA}[cor]
        mapas, cores = _q_setas(2), pal
    elif nome == 'vibrar_sim':
        mapas, cores = [_m_vibrar(True, 0), _m_vibrar(True, 1)], _P_CIANO
    elif nome == 'vibrar_nao':
        mapas, cores = [_m_vibrar(False)], _P_CINZA
    elif nome == 'sino_sim':
        mapas, cores = [_m_sino(True, d) for d in (0, 1, 0, -1)] + [_m_sino(True, 0)] * 6, _P_CIANO
    elif nome == 'sino_nao':
        mapas, cores = [_m_sino(False, 0)], _P_CINZA
    elif nome == 'cadeado':
        mapas, cores = _brilho_mapas(_m_cadeado()), _P_CIANO
    elif nome.startswith('cena_'):
        qual = nome[5:]
        gerar = {'memorias': _q_cena_memorias, 'progresso': _q_cena_progresso,
                 'ganhos': _q_cena_ganhos, 'calculadora': _q_cena_calculadora}[qual]
        mapas, cores = gerar(), _P_CENA[qual]
    if mapas is None:
        return []
    q = [textura_mapa(m, cores, ('hud', nome, i)) for i, m in enumerate(mapas)]
    _QUADROS[nome] = q
    return q


# ═══════════════════════════════════════════════════════════
#  SPRITE (pixel art animada)
# ═══════════════════════════════════════════════════════════
class SpritePixel(Widget):
    """Desenho de pixel art com quadros trocados a `fps` pelo relogio unico.
    `u` = tamanho de cada pixel na tela (inteiro: fica nitido)."""

    def __init__(self, nome='', u=2, fps=6, alfa=1.0, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        super().__init__(**kwargs)
        self.u = max(1, int(u))
        self.fps = fps
        self._i = -1
        self._qs = []
        with self.canvas:
            self._cor = Color(1, 1, 1, alfa)
            self._r = Rectangle()
        self.bind(pos=self._mover)
        self.trocar(nome)
        RELOGIO.add(self)

    def trocar(self, nome):
        self._qs = quadros(nome) if nome else []
        self._i = -1
        if self._qs:
            tw, th = self._qs[0].size
            self.size = (tw * self.u, th * self.u)
            self._r.texture = self._qs[0]
            self._r.size = self.size
            self._i = 0
        self._mover()

    def mudar_u(self, u):
        u = max(1, int(u))
        if u != self.u:
            self.u = u
            if self._qs:
                tw, th = self._qs[0].size
                self.size = (tw * u, th * u)
                self._r.size = self.size
            self._mover()

    def _mover(self, *_):
        self._r.pos = (int(self.x), int(self.y))

    def tique(self, t):
        if len(self._qs) > 1 and self.fps > 0:
            i = int(t * self.fps) % len(self._qs)
            if i != self._i:
                self._i = i
                self._r.texture = self._qs[i]


# ═══════════════════════════════════════════════════════════
#  CABECALHO: moldura HUD
# ═══════════════════════════════════════════════════════════
class CabecalhoMenu(FloatLayout):
    """Moldura HUD do topo do menu (o nome do app e as frases ficam por cima,
    no interface.kv)."""
    FUNDO = (0.01, 0.03, 0.08)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*self.FUNDO, 0.88)
            self._m_fundo = Mesh(mode='triangle_fan')
        with self.canvas.after:
            Color(0.0, 0.85, 1.0, 0.12)
            self._l_halo = Line(width=dp(2.6), close=True)
            Color(0.0, 0.85, 1.0, 0.7)
            self._l_borda = Line(width=dp(1.2), close=True)
            Color(0.0, 0.85, 1.0, 0.25)
            self._l_dentro = Line(width=dp(1))
            Color(0.4, 0.95, 1.0, 0.95)
            self._marcas = [Rectangle() for _ in range(5)]
        # a luz que corre pela borda de baixo (luz_na_linha, instalada pelo menu)
        self.linha_luz = Widget(size_hint=(None, None))
        self.add_widget(self.linha_luz)
        self.bind(pos=self._arrumar, size=self._arrumar)

    def _arrumar(self, *_):
        x, y, w, h = self.x, self.y, self.width, self.height
        if w < 20 or h < 20:
            return
        pts = _chanfro4(x, y, w, h, dp(16), dp(6), dp(6), dp(16))
        self._m_fundo.vertices, self._m_fundo.indices = _leque(pts)
        self._l_borda.points = pts
        self._l_halo.points = pts
        d = dp(5)
        self._l_dentro.points = [x + d, y + h * 0.45, x + d, y + h - d - dp(12), x + d + dp(12), y + h - d,
                                 x + w * 0.42, y + h - d]
        # marcas acesas na borda de cima e de baixo
        for i, r in enumerate(self._marcas[:3]):
            r.pos, r.size = (x + w * (0.5 + 0.06 * i), y + h - dp(1.5)), (w * (0.035 if i else 0.08), dp(3))
        self._marcas[3].pos, self._marcas[3].size = (x + w * 0.08, y - dp(1.5)), (w * 0.12, dp(3))
        self._marcas[4].pos, self._marcas[4].size = (x + w * 0.22, y - dp(1.5)), (w * 0.03, dp(3))
        self.linha_luz.pos, self.linha_luz.size = (x + dp(16), y), (w - dp(32), dp(1))


# ═══════════════════════════════════════════════════════════
#  PAINEL DE STATUS: hoje / nivel / sequencia
# ═══════════════════════════════════════════════════════════
class PainelStatus(Widget):
    """Tres quadros: pecas de HOJE, o NIVEL (barra e XP) e a SEQUENCIA. Os
    numeros contam do valor de antes ate o de agora (na primeira vez, do
    zero) e o que mudou da uma batida. Toque: abre o Progresso."""
    CORES = ((0.0, 0.85, 1.0), (0.66, 0.38, 1.0), (1.0, 0.58, 0.12))
    frac_xp = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._vals = None
        self._xp = (0, 1)
        self._ev_toque = None
        with self.canvas.before:
            Color(0.0, 0.85, 1.0, 0.35)
            self._l_fora = Line(width=dp(1), close=True)
            self._caixas = []
            for r, g, b in self.CORES:
                Color(r * 0.08 + 0.01, g * 0.08 + 0.02, b * 0.08 + 0.05, 0.92)
                mf = Mesh(mode='triangle_fan')
                Color(r, g, b, 0.14)
                lh = Line(width=dp(2.4), close=True)
                Color(r, g, b, 0.85)
                lb = Line(width=dp(1.2), close=True)
                Color(r, g, b, 0.5)
                rt = Rectangle()
                self._caixas.append((mf, lh, lb, rt))
            Color(0.66, 0.38, 1.0, 0.18)
            self._m_barra_bg = Mesh(mode='triangle_fan')
            Color(0.66, 0.38, 1.0, 1.0)
            self._m_barra = Mesh(mode='triangle_fan')
            Color(0.9, 0.8, 1.0, 0.9)
            self._r_barra_luz = Rectangle()
            self._c_toque = Color(0.0, 0.9, 1.0, 0)
            self._m_toque = Mesh(mode='triangle_fan')
        self._icones = [SpritePixel('pilha', fps=10), SpritePixel('nivel', fps=4), SpritePixel('calendario', fps=1.5)]
        for s in self._icones:
            self.add_widget(s)

        def rot(txt, fs, cor, fonte='orbitron.ttf', bold=False):
            l = Label(text=txt, font_name=fonte, font_size=fs, bold=bold, markup=True, color=cor,
                      halign='center', valign='middle', size_hint=(None, None), shorten=True, max_lines=1)
            self.add_widget(l)
            return l
        c0, c1, c2 = self.CORES
        self._cap = [rot('HOJE', sp(9), (*c0, 0.95)), rot('NÍVEL', sp(9), (*c1, 0.95)),
                     rot('SEQUÊNCIA', sp(9), (*c2, 0.95))]
        self._val = [rot('-', sp(30), (*c0, 1), bold=True), rot('-', sp(26), (0.92, 0.85, 1.0, 1), bold=True),
                     rot('-', sp(30), (*c2, 1), bold=True)]
        self._uni = [rot('peças', sp(13), (0.75, 0.92, 1.0, 0.9), fonte='rajdhani.ttf'), None,
                     rot('dias', sp(13), (1.0, 0.85, 0.7, 0.9), fonte='rajdhani.ttf')]
        self._l_xp = rot('XP  0 / 0', sp(8.5), (0.85, 0.78, 1.0, 0.8))
        # a luz que corre pela borda de cima (luz_na_linha, instalada pelo menu)
        self.linha_topo = Widget(size_hint=(None, None))
        self.add_widget(self.linha_topo)
        self.bind(pos=self._arrumar, size=self._arrumar, frac_xp=self._arrumar_barra)

    def _arrumar(self, *_):
        x, y, w, h = self.x, self.y, self.width, self.height
        if w < 20 or h < 20:
            return
        self._l_fora.points = _chanfro(x, y, w, h, dp(10))
        pad, gap = dp(6), dp(6)
        cw = (w - 2 * pad - 2 * gap) / 3.0
        ch = h - 2 * pad
        self._geo = []
        for i, (mf, lh, lb, rt) in enumerate(self._caixas):
            bx, by = x + pad + i * (cw + gap), y + pad
            pts = _chanfro4(bx, by, cw, ch, dp(10) if i == 0 else dp(4), dp(10) if i == 2 else dp(4),
                            dp(4), dp(4))
            mf.vertices, mf.indices = _leque(pts)
            lh.points = pts
            lb.points = pts
            rt.pos, rt.size = (bx + cw * 0.3, by + ch - dp(1.5)), (cw * 0.4, dp(3))
            self._geo.append((bx, by, cw, ch))
            # de baixo para cima: unidade (ou XP e barra), numero, legenda, icone
            if i == 1:
                self._l_xp.size = (cw - dp(6), dp(14))
                self._l_xp.text_size = self._l_xp.size
                self._l_xp.pos = (bx + dp(3), by + dp(5))
                self._barra = (bx + cw * 0.12, self._l_xp.top + dp(3), cw * 0.76, dp(7))
                base = self._barra[1] + dp(7) + dp(1)
            else:
                un = self._uni[i]
                un.size = (cw - dp(6), dp(18))
                un.text_size = un.size
                un.pos = (bx + dp(3), by + dp(3))
                base = un.top - dp(6)
            val = self._val[i]
            val.size = (cw - dp(4), dp(36))
            val.text_size = val.size
            val.pos = (bx + dp(2), base)
            cap = self._cap[i]
            cap.size = (cw - dp(6), dp(14))
            cap.text_size = cap.size
            cap.pos = (bx + dp(3), val.top)
            ic = self._icones[i]
            livre = by + ch - cap.top                      # o icone no meio do que sobrou em cima
            if ic._qs:
                linhas = ic._qs[0].size[1]
                ic.mudar_u(max(1, int(min(dp(2.4), (livre - dp(6)) / float(linhas)))))
            ic.pos = (int(bx + (cw - ic.width) / 2.0), int(cap.top + max(0.0, (livre - ic.height) / 2.0)))
        self._arrumar_barra()
        tv, ti = _leque(_chanfro(x, y, w, h, dp(10)))
        self._m_toque.vertices, self._m_toque.indices = tv, ti
        self.linha_topo.pos, self.linha_topo.size = (x + dp(12), y + h - dp(1)), (w - dp(24), dp(1))

    def _arrumar_barra(self, *_):
        b = getattr(self, '_barra', None)
        if b is None:
            return
        bx, by, bw, bh = b
        c = bh / 2.0
        self._m_barra_bg.vertices, self._m_barra_bg.indices = _leque(_chanfro(bx, by, bw, bh, c))
        f = max(0.0, min(1.0, self.frac_xp))
        fw = max(bh, bw * f) if f > 0 else 0
        if fw > 0:
            self._m_barra.vertices, self._m_barra.indices = _leque(_chanfro(bx, by, fw, bh, c))
            self._r_barra_luz.pos, self._r_barra_luz.size = (bx + c, by + bh - dp(2)), (max(0, fw - 2 * c), dp(1))
        else:
            self._m_barra.vertices, self._m_barra.indices = [], []
            self._r_barra_luz.size = (0, 0)

    def definir(self, hoje, nivel, frac, seq, xp=None, atraso=0.25):
        from animacoes_ui import contar, pulso, fmt_br
        from kivy.animation import Animation
        novos = (int(hoje), int(nivel), int(seq))
        primeira = self._vals is None
        velhos = (0, 0, 0) if primeira else self._vals
        self._vals = novos
        pq = int(sp(14))
        montar = (
            lambda v: fmt_br(v),
            lambda v: f"[size={pq}]LV. [/size]{v}",
            lambda v: f"{v}",
        )
        self._uni[0].text = 'peça' if novos[0] == 1 else 'peças'
        self._uni[2].text = 'dia' if novos[2] == 1 else 'dias'
        if xp is not None:
            self._l_xp.text = f"XP  {fmt_br(xp[0])} / {fmt_br(xp[1])}"
        dur = 0.9
        for i in range(3):
            contar(self._val[i], novos[i], montar[i], de=velhos[i], duracao=dur, atraso=atraso + i * 0.08)
            if not primeira and novos[i] != velhos[i]:
                lbl = self._val[i]
                Clock.schedule_once(lambda dt, l=lbl: pulso(l, 1.18, 0.3), atraso + i * 0.08 + dur * 0.8)
        Animation.cancel_all(self, 'frac_xp')
        if primeira or novos[1] > velhos[1]:
            self.frac_xp = 0.0
        Clock.schedule_once(lambda dt: Animation(frac_xp=float(frac), duration=0.9,
                                                 transition='out_cubic').start(self), atraso + 0.1)

    # ── toque: acende e abre o Progresso ──
    def _apagar(self):
        if self._ev_toque is not None:
            self._ev_toque.cancel()

        def _f(dt):
            self._c_toque.a = max(0.0, self._c_toque.a - dt * 0.5)
            if self._c_toque.a <= 0:
                self._ev_toque = None
                return False
        self._ev_toque = Clock.schedule_interval(_f, 1 / 60.)

    def on_touch_down(self, touch):
        if self.opacity > 0.5 and self.collide_point(*touch.pos):
            touch.grab(self)
            if self._ev_toque is not None:
                self._ev_toque.cancel()
                self._ev_toque = None
            self._c_toque.a = 0.12
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super().on_touch_up(touch)
        touch.ungrab(self)
        self._apagar()
        if self.collide_point(*touch.pos):
            try:
                tatil.botao()
            except Exception:
                pass
            app = App.get_running_app()
            if app is not None and hasattr(app, 'mudar_tela'):
                app.mudar_tela('progresso')
        return True


# ═══════════════════════════════════════════════════════════
#  SYSTEM LINK START (o capacete NerveGear e as setas de sempre)
# ═══════════════════════════════════════════════════════════
class BotaoLinkStart(BotaoAngularMenu):
    """O botao principal (o capacete NerveGear e as setas de sempre sao
    postos pelo menu com icone_pixel)."""


# ═══════════════════════════════════════════════════════════
#  CARTOES DO MENU (grade 2x2)
# ═══════════════════════════════════════════════════════════
class CartaoMenu(BotaoAngularMenu):
    """Cartao do menu: icone, titulo, descricao e >> a esquerda; a cena em
    pixel art animada ao fundo, a direita, sumindo para o lado do texto.
    (`text` continua com o nome do cartao - so nao aparece.)"""
    titulo = StringProperty('')
    sub = StringProperty('')
    icone = StringProperty('')
    cena = StringProperty('')
    cor = ListProperty([0.0, 0.85, 1.0])
    nome_setas = StringProperty('setas2_ciano')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pronto = False
        self._txt = {}

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        r, g, b = self.cor[:3]
        self.cor_borda = [r, g, b, 0.95]
        self.cor_borda_kv = list(self.cor_borda)
        with self.canvas.before:
            PushMatrix()
            self._sc = Scale(1, 1, 1)
            self._c_halo = Color(r, g, b, 0.14)
            self._l_halo = Line(width=dp(3), close=True)
            self._c_fundo = Color(r * 0.1 + 0.01, g * 0.1 + 0.015, b * 0.1 + 0.04, 0.96)
            self._m_fundo = Mesh(mode='triangle_fan')
        self._cena = SpritePixel('cena_' + self.cena, fps=3, alfa=0.45)
        self.add_widget(self._cena)
        with self._cena.canvas.after:                       # a cena some para o lado do texto
            self._c_deg = Color(r * 0.1 + 0.01, g * 0.1 + 0.015, b * 0.1 + 0.04, 1)
            self._r_deg = Rectangle(texture=_tex_degrade())
        self._ic = None                                    # (o icone de sempre: posto no 1o layout)
        self._set = SpritePixel(self.nome_setas, fps=5)
        self.add_widget(self._set)
        with self.canvas.after:
            Color(r, g, b, 0.22)
            self._l_dentro = Line(width=dp(1), close=True)
            self._c_borda = Color(*self.cor_borda)
            self._l_borda = Line(width=dp(1.5), close=True)
            Color(min(1, r + 0.4), min(1, g + 0.4), min(1, b + 0.4), 1)
            self._l_canto1 = Line(width=dp(2))
            self._l_canto2 = Line(width=dp(2))
            Color(1, 1, 1, 1)
            self._r_tit = Rectangle()
            self._r_sub = Rectangle()
            PopMatrix()
        self._pronto = True
        self._textos()
        self.bind(pos=self._arrumar, size=self._arrumar, escala=self._escalar,
                  cor_borda=lambda *_: setattr(self._c_borda, 'rgba', self.cor_borda),
                  brilho=lambda *_: setattr(self._c_halo, 'a', 0.12 + 0.16 * self.brilho),
                  state=self._estado)
        self._arrumar()

    def _textos(self):
        r, g, b = self.cor[:3]
        escuro = (r * 0.1 + 0.01, g * 0.1 + 0.015, b * 0.1 + 0.04)       # contorno: le sobre a cena
        try:
            self._t_tit = _render_texto(self.titulo, 'orbitron.ttf', sp(15), (min(1, r + 0.15), min(1, g + 0.15),
                                                                          min(1, b + 0.15), 1), True,
                                        contorno=(dp(2), escuro))
            self._t_sub = _render_texto(self.sub, 'orbitron.ttf', sp(7.5), (min(1, r + 0.2), min(1, g + 0.2),
                                                                        min(1, b + 0.2), 0.9),
                                        contorno=(dp(1.5), escuro))
        except Exception as e:
            print(f"[cartao menu] texto: {e}")
            self._t_tit = self._t_sub = None

    def _estado(self, *_):
        r, g, b = self.cor[:3]
        k = 0.2 if self.state == 'down' else 0.1
        self._c_fundo.rgba = (r * k + 0.01, g * k + 0.015, b * k + 0.04, 0.96)

    def _escalar(self, *_):
        self._sc.x = self._sc.y = self.escala
        self._sc.origin = (self.x + self.width / 2.0, self.y + self.height / 2.0)

    def _arrumar(self, *_):
        if not self._pronto:
            return
        x, y, w, h = self.x, self.y, self.width, self.height
        if w < 20 or h < 20:
            return
        c1, c2 = dp(14), dp(5)
        pts = _chanfro4(x, y, w, h, c1, c2, c2, c1)
        self._m_fundo.vertices, self._m_fundo.indices = _leque(pts)
        self._l_halo.points = pts
        self._l_borda.points = pts
        d = dp(4)
        self._l_dentro.points = _chanfro4(x + d, y + d, w - 2 * d, h - 2 * d, c1 - d * 0.6, c2, c2, c1 - d * 0.6)
        L = dp(16)
        self._l_canto1.points = [x, y + h - c1 - L, x, y + h - c1, x + c1, y + h, x + c1 + L, y + h]
        self._l_canto2.points = [x + w, y + c1 + L, x + w, y + c1, x + w - c1, y, x + w - c1 - L, y]
        self._escalar()
        # cena: a direita, de baixo, o maior pixel inteiro que cabe
        cena = self._cena
        if cena._qs:
            tw, th = cena._qs[0].size
            u = max(1, int(min(w * 0.72 / tw, (h - dp(6)) / th)))
            cena.mudar_u(u)
            cena.pos = (int(x + w - dp(3) - cena.width), int(y + dp(3)))
            self._r_deg.pos = (cena.x, cena.y)
            self._r_deg.size = (cena.width * 0.5, cena.height)
        # icone em cima a esquerda: o MESMO icone animado de antes do menu novo
        # (cristal, estrela piscando, moeda girando, calculadora)
        ui = max(2, int(round(dp(2.2))))                   # (o mesmo tamanho do menu de antes)
        if self._ic is None and self.icone:
            from animacoes_ui import icone_pixel
            icone_pixel(self, self.icone, u=ui,
                        onde=lambda ic: (self.x + dp(14), self.top - dp(12) - ic.height))
            self._ic = True
        # setas embaixo a direita
        self._set.mudar_u(max(2, ui - 1))
        self._set.pos = (int(x + w - dp(12) - self._set.width), int(y + dp(12)))
        # titulo e descricao
        xt = x + dp(14)
        if self._t_tit is not None:
            tw, th = self._t_tit.size
            if tw > w - dp(22):                              # nao cabe: encolhe
                k = (w - dp(22)) / float(tw)
                tw, th = tw * k, th * k
            self._r_tit.texture = self._t_tit
            self._r_tit.size = (tw, th)
            self._r_tit.pos = (int(xt), int(y + h * 0.38))
        if self._t_sub is not None:
            sw, sh = self._t_sub.size
            if sw > w - dp(48):
                k = (w - dp(48)) / float(sw)
                sw, sh = sw * k, sh * k
            self._r_sub.texture = self._t_sub
            self._r_sub.size = (sw, sh)
            self._r_sub.pos = (int(xt), int(self._r_tit.pos[1] - dp(4) - sh))


# ═══════════════════════════════════════════════════════════
#  BOTOES DE BAIXO (com icone)
# ═══════════════════════════════════════════════════════════
class BotaoIcone(BotaoAngular):
    """Botao chanfrado com um icone pixel a esquerda e o texto ao lado."""
    icone = StringProperty('')

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self._ic = SpritePixel(self.icone, fps=6)
        self.add_widget(self._ic)
        self.bind(pos=self._arrumar, size=self._arrumar, icone=lambda *_: self._ic.trocar(self.icone))
        self._arrumar()

    def _arrumar(self, *_):
        u = max(2, int(min(dp(1.8), self.height / 18.0)))
        self._ic.mudar_u(u)
        self._ic.pos = (int(self.x + dp(15)), int(self.y + (self.height - self._ic.height) / 2.0))


# ═══════════════════════════════════════════════════════════
#  RODAPE
# ═══════════════════════════════════════════════════════════
class RodapeMenu(FloatLayout):
    """Faixa do rodape: o selo TF, o sistema e a VERSAO e a frase do app."""
    selo_area = ListProperty([0, 0, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.01, 0.03, 0.08, 0.85)
            self._m_fundo = Mesh(mode='triangle_fan')
            Color(0.0, 0.85, 1.0, 0.45)
            self._l_borda = Line(width=dp(1), close=True)
            Color(0.4, 0.95, 1.0, 0.9)
            self._marcas = [Rectangle() for _ in range(3)]
            # o selo TF
            Color(0.0, 0.2, 0.32, 0.9)
            self._m_selo = Mesh(mode='triangle_fan')
            Color(0.0, 0.85, 1.0, 0.85)
            self._l_selo = Line(width=dp(1.2), close=True)
        self.linha_luz = Widget(size_hint=(None, None))
        self.add_widget(self.linha_luz)
        self.bind(pos=self._arrumar, size=self._arrumar)

    def _arrumar(self, *_):
        x, y, w, h = self.x, self.y, self.width, self.height
        if w < 20 or h < 10:
            return
        pts = _chanfro4(x, y, w, h, dp(5), dp(12), dp(12), dp(5))
        self._m_fundo.vertices, self._m_fundo.indices = _leque(pts)
        self._l_borda.points = pts
        self._marcas[0].pos, self._marcas[0].size = (x + w * 0.3, y + h - dp(1.5)), (w * 0.14, dp(3))
        self._marcas[1].pos, self._marcas[1].size = (x + w * 0.47, y + h - dp(1.5)), (w * 0.04, dp(3))
        self._marcas[2].pos, self._marcas[2].size = (x + w * 0.62, y - dp(1.5)), (w * 0.18, dp(3))
        s = h - dp(12)
        sx, sy = x + dp(8), y + dp(6)
        ps = _chanfro(sx, sy, s, s, dp(6))
        self._m_selo.vertices, self._m_selo.indices = _leque(ps)
        self._l_selo.points = ps
        self.selo_area = [sx, sy, s, s]
        self.linha_luz.pos, self.linha_luz.size = (x + dp(14), y + h - dp(1)), (w - dp(28), dp(1))
