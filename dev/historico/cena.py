"""Preview de composicao (PIL) imitando o KiritoPixel: pos, espelho, rotacao em torno de pivo."""
import sys, math; sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
import os; os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito as K

def sprite(p, ps, espelhar=False, sil=None):
    _, dados = K._bytes(p)
    im = Image.frombytes('RGBA', (K.GW, K.GH), dados)       # linha 0 = y 0 (embaixo)
    im = im.transpose(Image.FLIP_TOP_BOTTOM)                 # PIL: linha 0 = topo
    if espelhar:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im.resize((K.GW * ps, K.GH * ps), Image.NEAREST)

class Tela:
    def __init__(self, w, h, fundo=(6, 6, 14)):
        self.w, self.h = w, h
        self.im = Image.new('RGBA', (w, h), fundo + (255,))
        self.d = ImageDraw.Draw(self.im)
    def por(self, p, ps, x, y, rot=0.0, pivo=None, espelhar=False, clip=None):
        """x,y = canto inferior esquerdo do widget (coords Kivy, y para cima).
        pivo = coords locais (Kivy). clip = (x0,y0,x1,y1) Kivy."""
        sp = sprite(p, ps, espelhar)
        cam = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        cam.paste(sp, (int(round(x)), int(round(self.h - y - sp.size[1]))))
        if rot:
            if pivo is None:
                ax, ay = anc_local(ps, espelhar)
            else:
                ax, ay = pivo
            cx, cy = x + ax, self.h - (y + ay)
            cam = cam.rotate(rot, resample=Image.NEAREST, center=(cx, cy))
        if clip:
            m = Image.new('L', (self.w, self.h), 0)
            ImageDraw.Draw(m).rectangle([clip[0], self.h - clip[3], clip[2], self.h - clip[1]], fill=255)
            a = cam.getchannel('A')
            from PIL import ImageChops
            cam.putalpha(ImageChops.multiply(a, m))
        self.im.alpha_composite(cam)
    def ponto(self, x, y, cor=(255, 0, 0), r=3):
        self.d.ellipse([x - r, self.h - y - r, x + r, self.h - y + r], fill=cor)
    def ret(self, x0, y0, x1, y1, cor=(60, 60, 90), w=2):
        self.d.rectangle([x0, self.h - y1, x1, self.h - y0], outline=cor, width=w)
    def texto(self, x, y, t, cor=(255, 255, 0)):
        self.d.text((x, self.h - y), t, fill=cor)
    def salvar(self, f):
        self.im.convert('RGB').save(f)

def anc_local(ps, espelhar=False):
    cx = (K._X0 + 6) if not espelhar else (K.GW - 1 - (K._X0 + 6))
    return (cx + 0.5) * ps, (K._PES + 8) * ps

def mao_local(p, qual, ps, espelhar=False):
    pernas = K._PERNAS[p['pernas']]
    topo = K._PES + len(pernas) + len(K._TRONCO) - 1 + int(p['dy'])
    bx = K._X0 + int(p['dx'])
    if qual == 1:
        x, y = bx + 9 + p['m1'][0], topo - 2 + p['m1'][1]
    else:
        m2 = p['m2'] if p['m2'] is not None else (-1, -6)
        x, y = bx + 3 + m2[0], topo - 2 + m2[1]
    if espelhar:
        x = K.GW - 1 - x
    return (x + 0.5) * ps, (y + 0.5) * ps
