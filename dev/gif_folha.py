"""gif_folha.py GIF SAIDA ini qtd cols escala [x0,y0,x1,y1 recorte em px]"""
import sys
from PIL import Image, ImageSequence, ImageDraw
gif, saida = sys.argv[1], sys.argv[2]
ini, qtd, cols, esc = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), float(sys.argv[6])
rec = [int(v) for v in sys.argv[7].split(',')] if len(sys.argv) > 7 else None
im = Image.open(gif)
quadros = [f.convert('RGBA') for f in ImageSequence.Iterator(im)]
sel = quadros[ini:ini + qtd]
ims = []
for i, f in enumerate(sel):
    if rec:
        f = f.crop(rec)
    f = f.resize((int(f.width * esc), int(f.height * esc)), Image.NEAREST)
    ims.append((ini + i, f))
w, h = ims[0][1].size
linhas = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (cols * w, linhas * (h + 14)), (30, 30, 30))
d = ImageDraw.Draw(S)
for k, (n, f) in enumerate(ims):
    x, y = (k % cols) * w, (k // cols) * (h + 14)
    S.paste(f, (x, y + 14), f)
    d.text((x + 2, y + 1), str(n), fill='yellow')
S.save(saida)
print(S.size, len(ims))
