import sys; sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
import os; os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito
nomes = sys.argv[2].split(',') if len(sys.argv) > 2 and sys.argv[2] else [n for n in kirito.POSE_A if n not in ('x_arma','x_corta','final_arma','final','pousa','guarda2','embainha')]
extra = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
ps = 5; W, H = kirito.GW * ps, kirito.GH * ps
cols = 6
S = Image.new('RGB', (W * cols, (H + 14) * ((len(nomes) + cols - 1) // cols)), (6, 6, 12)); d = ImageDraw.Draw(S)
for i, n in enumerate(nomes):
    p = dict(kirito.POSE_A[n]); p['capa'] += extra; p['cabelo'] += extra; p['fase'] = (i % 6) / 6.0
    px = kirito.montar(p); ox, oy = (i % cols) * W, (i // cols) * (H + 14)
    d.text((ox + 3, oy + 1), n, fill='yellow')
    for (x, y), c in px.items():
        if not (0 <= x < kirito.GW and 0 <= y < kirito.GH): continue
        r, g, b, a = kirito._PALETA[c]; bg = (6, 6, 12)
        col = tuple(int(255 * (v * a) + bgc * (1 - a)) for v, bgc in zip((r, g, b), bg))
        d.rectangle([ox + x * ps, oy + 14 + (kirito.GH - 1 - y) * ps, ox + x * ps + ps - 1, oy + 14 + (kirito.GH - 1 - y) * ps + ps - 1], fill=col)
S.save(sys.argv[1]); print(S.size)
