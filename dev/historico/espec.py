import sys, math; sys.path.insert(0, 't')
import audio as A
import os
if os.environ.get('PASTA'): A.PASTA = os.environ['PASTA']
from PIL import Image, ImageDraw
nomes = sys.argv[2].split(',')
larg_s = float(sys.argv[3]) if len(sys.argv) > 3 else 1.2
cols = 3; W, H = 380, 150
S = Image.new('RGB', (W * cols, (H + 18) * ((len(nomes) + cols - 1) // cols)), (8, 8, 14)); d = ImageDraw.Draw(S)
for i, nome in enumerate(nomes):
    a = A.ler(nome) if not nome.startswith('/') else None
    X = A.espectro(a, 512, 128)
    ox, oy = (i % cols) * W, (i // cols) * (H + 18)
    cen = A.centroide(a)
    d.text((ox + 3, oy + 2), f"{nome} {A.dur(a):.2f}s pico@{A.pico_t(a):.2f} cent={cen/1000:.1f}k", fill='yellow')
    mx = max(max(c) for c in X) or 1
    px_t = W / (larg_s * A.TAXA / 128)
    for ci, c in enumerate(X):
        x = int(ox + ci * px_t)
        if x >= ox + W: break
        for b in range(0, 256, 2):
            v = (c[b] + c[b + 1]) / 2
            v = max(0.0, 1 + math.log10(v / mx + 1e-6) / 3.0)      # 60 dB
            y = oy + 18 + H - 1 - int(b / 256 * H)
            col = (int(255 * min(1, v * 1.6)), int(255 * v ** 1.5), int(255 * min(1, 0.3 + v)) if v > 0.02 else 14)
            d.rectangle([x, y - 1, x + max(1, int(px_t)), y], fill=col)
S.save(sys.argv[1]); print(S.size)
