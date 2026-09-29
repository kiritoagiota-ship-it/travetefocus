"""Mancha do corte (pixel art) fora do app: ver_arco.py SAIDA"""
import math, sys
from PIL import Image
src = open(r'C:\Users\kirit\travetefocus\app\cenas.py', encoding='utf-8').read()
a = src.index('_PAL_CORTE = {'); b = src.index('class OficinaCortes')
ns = {'math': math}
exec(src[a:b], ns)
Arco, des, PAL = ns['ArcoCorte'], ns['_desenho_corte'], ns['_PAL_CORTE']
th = 45.0
u = 2.8
casos = [
    (Arco.pelo_meio((200, 200), 0, 110 + th * 0.9, -0.16, th * 1.0), 'katana'),
    (Arco.pelo_meio((200, 200), 42, 75 + th * 1.3, -0.16, th * 0.95), 'katana'),
    (Arco.pelo_meio((200, 200), -40, 75 + th * 1.4, 0.15, th * 0.95), 'azul'),
    (Arco.pelo_meio((200, 200), 140, 80 + th * 1.2, -0.14, th * 0.9), 'katana'),
    (Arco.pelo_meio((200, 200), 0, 700, -0.05, th * 1.35), 'mug'),
]
ims = []
for arco, pal in casos:
    res = None
    for r in des(arco, PAL[pal], u):
        if r is not None:
            res = r
    dados, gx0, gy0, w, h = res
    im = Image.frombytes('RGBA', (w, h), dados).transpose(Image.FLIP_TOP_BOTTOM)
    fundo = Image.new('RGBA', (w, h), (5, 8, 16, 255))
    fundo.alpha_composite(im)
    ims.append(fundo.resize((w * 3, h * 3), Image.NEAREST))
W = max(i.width for i in ims); H = sum(i.height + 10 for i in ims)
S = Image.new('RGB', (W, H), (40, 40, 40)); y = 0
for i in ims:
    S.paste(i.convert('RGB'), (0, y)); y += i.height + 10
S.save(sys.argv[1]); print(S.size)
