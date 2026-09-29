"""Close de anime pode olhar para a esquerda (quando o Yoru esta virado)."""
pc = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(pc, encoding='utf-8').read()
Q = '"' * 3
reps = [
    ("    acendem roxos no meio do close)." + Q + "\n\n    PW, PH = 104, 40\n\n"
     "    def __init__(self, tipo='normal', dur=0.8, on_fim=None, y_rel=0.56, som=True, **kwargs):",
     "    acendem roxos no meio do close). espelhar: ele olhando para a\n"
     "    esquerda (o retrato vira e entra pelo outro lado)." + Q + "\n\n    PW, PH = 104, 40\n\n"
     "    def __init__(self, tipo='normal', dur=0.8, on_fim=None, y_rel=0.56, som=True, espelhar=False,\n"
     "                 **kwargs):"),
    ("        self.tipo, self.dur, self.on_fim = tipo, dur, on_fim\n        W, H = Window.size",
     "        self.tipo, self.dur, self.on_fim = tipo, dur, on_fim\n        self.esp = espelhar\n"
     "        W, H = Window.size"),
    ("            x0 = (W - self.wr) / 2.0 + (1 - desl) * W * 0.18\n"
     "            self.r_ret.texture = self.tex[self._nome(t)]",
     "            x0 = (W - self.wr) / 2.0 + (1 - desl) * W * 0.18 * (-1 if self.esp else 1)\n"
     "            self.r_ret.texture = self.tex[self._nome(t)]\n"
     "            if self.esp:\n"
     "                self.r_ret.tex_coords = K._TC_ESPELHO"),
    ("            # linhas de velocidade correndo para a esquerda\n"
     "            vs, ids = [], []\n"
     "            for i, (fy, fl, vel, fase) in enumerate(self.linhas):\n"
     "                x = W * (1.2 - ((fase + t * vel) % 1.4))\n"
     "                y = y0 + hb * fy\n"
     "                w, h = W * fl, max(1.0, dp(1.2))",
     "            # linhas de velocidade correndo para tras dele\n"
     "            vs, ids = [], []\n"
     "            for i, (fy, fl, vel, fase) in enumerate(self.linhas):\n"
     "                x = W * (1.2 - ((fase + t * vel) % 1.4))\n"
     "                y = y0 + hb * fy\n"
     "                w, h = W * fl, max(1.0, dp(1.2))\n"
     "                if self.esp:\n"
     "                    x = W - x - w"),
    ("                cx, cy = x0 + 76.5 * u, y0 + 18.5 * u * k",
     "                cx, cy = x0 + ((self.PW - 76.5) if self.esp else 76.5) * u, y0 + 18.5 * u * k"),
    ("def close_rosto(camada, tipo='normal', dur=0.8, on_fim=None, y_rel=0.56):",
     "def close_rosto(camada, tipo='normal', dur=0.8, on_fim=None, y_rel=0.56, espelhar=False):"),
    ("        camada.add_widget(_CloseRosto(tipo=tipo, dur=dur, on_fim=on_fim, y_rel=y_rel))",
     "        camada.add_widget(_CloseRosto(tipo=tipo, dur=dur, on_fim=on_fim, y_rel=y_rel, espelhar=espelhar))"),
    ("            ag.depois(0.12, lambda: close_rosto(camada, 'normal', dur=0.72, y_rel=0.8,\n"
     "                                                on_fim=lambda: ag.depois(0.02, _tra)))",
     "            ag.depois(0.12, lambda: close_rosto(camada, 'normal', dur=0.72, y_rel=0.8,\n"
     "                                                espelhar=kk.espelhar,\n"
     "                                                on_fim=lambda: ag.depois(0.02, _tra)))"),
]
for a, b in reps:
    assert c.count(a) == 1, a[:70]
    c = c.replace(a, b)
open(pc, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
