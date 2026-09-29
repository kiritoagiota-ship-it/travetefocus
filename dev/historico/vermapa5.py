"""Mostra um mapa de texto (paleta nova) ampliado com grade e numeros.
uso: python vermapa5.py mapa.txt c0 r0 c1 r1 z saida.png"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from paleta5 import P5
l = open(sys.argv[1]).read().split('\n')
l = [x for x in l if x]
c0, r0, c1, r1, z = (int(v) for v in sys.argv[2:7])
S = Image.new('RGB', ((c1 - c0) * z + 30, (r1 - r0) * z + 20), (31, 53, 80))
d = ImageDraw.Draw(S)
for r in range(r0, r1):
    for c in range(c0, c1):
        ch = l[r][c] if r < len(l) and c < len(l[r]) else '.'
        if ch != '.':
            X, Y = 30 + (c - c0) * z, 20 + (r - r0) * z
            d.rectangle([X, Y, X + z - 1, Y + z - 1], fill=P5.get(ch, (255, 0, 255)))
for i in range(c1 - c0 + 1):
    d.line([(30 + i * z, 20), (30 + i * z, S.height)], fill=(200, 200, 60) if (c0 + i) % 5 == 0 else (70, 80, 100))
    if (c0 + i) % 5 == 0:
        d.text((31 + i * z, 4), str(c0 + i), fill=(255, 255, 0))
for j in range(r1 - r0 + 1):
    d.line([(30, 20 + j * z), (S.width, 20 + j * z)], fill=(200, 200, 60) if (r0 + j) % 5 == 0 else (70, 80, 100))
    if (r0 + j) % 5 == 0:
        d.text((2, 21 + j * z), str(r0 + j), fill=(255, 255, 0))
S.save(sys.argv[7])
