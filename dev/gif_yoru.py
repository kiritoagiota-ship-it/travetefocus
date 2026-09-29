"""GIF do Yoru com a fisica de verdade (molas do sobretudo, cabelo, cabeca e
laminas), sem abrir janela: usa os metodos do proprio KiritoPixel num
objeto falso. uso (como modulo):
    from gif_yoru import Sim, salvar_gif
    s = Sim(); quadros = s.rodar(seq, caminho=lambda i: (x, y)); salvar_gif(...)
"""
import os
import sys
import math
sys.path.insert(0, os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app'))
os.environ['KIVY_NO_ARGS'] = '1'
os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image
import kirito as K

BG = (10, 10, 18)


class Sim:
    def __init__(self, ps=9, M=None):
        M = M or K
        self.M = M
        KP = M.KiritoPixel
        self.ps = ps
        self.rotacao = 0.0
        self.espelhar = False
        self.fisica = True
        self._pausa = 0.0
        self._base = M.pose()
        self._ult_base = None
        self._m_capa = M._Mola(95, 9)
        self._m_cab = M._Mola(110, 10)
        self._m_lift = M._Mola(80, 8)
        self._m_hx = M._Mola(150, 13)
        self._m_hy = M._Mola(150, 11)
        self._m_a = {1: None, 2: None}
        self.luz = 0.0
        self._luz_imp = 0.0
        self._fase = 0.0
        self._t = 0.0
        self._ult = None
        self._vel = (0.0, 0.0)
        self.pos = (0.0, 0.0)
        self.saida = []
        self._vida_f = KP._vida
        self._camadas_f = KP._camadas
        self._composta_f = KP._composta

    # o que o _vida do widget usa
    def ancora(self):
        return self.pos

    def _camadas(self, dt, frente, cima):
        return self._camadas_f(self, dt, frente, cima)

    def _composta(self):
        return self._composta_f(self)

    def _desenhar(self, forcar=False):
        self.saida.append(self._composta())

    def empurrar(self, capa=0.0, cabelo=0.0, lift=0.0):
        self._m_capa.v += capa
        self._m_cab.v += cabelo
        self._m_lift.v += lift

    def rodar(self, seq, caminho=None, eventos=None, aquece=30):
        """seq: poses (1 por quadro a 30 fps). caminho(i) -> (x, y) da ancora
        em px de tela. eventos: {quadro: fn(sim)}. Devolve as poses compostas."""
        self.saida = []
        n = len(seq)
        for i in range(-aquece, n):
            j = max(0, i)
            self._base = seq[j]
            if caminho:
                self.pos = caminho(j)
            if eventos and i >= 0 and i in eventos:
                eventos[i](self)
            self._vida_f(self, 1 / 30.0)
        return self.saida[aquece:]


def imagem(p, esc=3, caixa=None, espelhar=False, M=None):
    M = M or K
    px = M.montar(p)
    if caixa is None:
        caixa = (0, 0, K.TW, K.TH)
    x0, y0, x1, y1 = caixa
    im = Image.new('RGB', ((x1 - x0) * esc, (y1 - y0) * esc), BG)
    pix = im.load()
    for (x, y), c in px.items():
        if espelhar:
            x = K.TW - 1 - x
        if not (x0 <= x < x1 and y0 <= y < y1):
            continue
        r, g, b, a = M._PALETA[c]
        col = tuple(int(255 * (v * a) + bgc * (1 - a)) for v, bgc in zip((r, g, b), BG))
        X, Y = (x - x0) * esc, (y1 - 1 - y) * esc
        for dx in range(esc):
            for dy in range(esc):
                pix[X + dx, Y + dy] = col
    return im


def salvar_gif(caminho, poses, esc=3, caixa=None, ms=33, desl=None):
    """desl(i) -> (dx, dy) em texels para deslocar o boneco no quadro."""
    ims = []
    for i, p in enumerate(poses):
        im = imagem(p, esc, caixa)
        if desl:
            dx, dy = desl(i)
            im2 = Image.new('RGB', im.size, BG)
            im2.paste(im, (int(dx * esc), int(-dy * esc)))
            im = im2
        ims.append(im)
    ims[0].save(caminho, save_all=True, append_images=ims[1:], duration=ms, loop=0, disposal=2)
    return ims
