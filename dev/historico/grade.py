"""Mostra um pedaco de uma imagem pequena ampliado, com grade e numeros.
uso: python grade.py img.png c0 r0 c1 r1 z saida.png"""
import sys
from PIL import Image, ImageDraw
im = Image.open(sys.argv[1]).convert('RGB')
c0, r0, c1, r1, z = (int(v) for v in sys.argv[2:7])
c = im.crop((c0, r0, c1, r1)).resize(((c1 - c0) * z, (r1 - r0) * z), Image.NEAREST)
S = Image.new('RGB', (c.width + 30, c.height + 20), (0, 0, 0))
S.paste(c, (30, 20))
d = ImageDraw.Draw(S)
for i in range(c1 - c0 + 1):
    col = (90, 90, 90) if (c0 + i) % 5 else (200, 200, 60)
    d.line([(30 + i * z, 20), (30 + i * z, S.height)], fill=col)
    if (c0 + i) % 5 == 0:
        d.text((30 + i * z + 1, 4), str(c0 + i), fill=(255, 255, 0))
for j in range(r1 - r0 + 1):
    col = (90, 90, 90) if (r0 + j) % 5 else (200, 200, 60)
    d.line([(30, 20 + j * z), (S.width, 20 + j * z)], fill=col)
    if (r0 + j) % 5 == 0:
        d.text((2, 20 + j * z + 1), str(r0 + j), fill=(255, 255, 0))
S.save(sys.argv[7]); print(S.size)
