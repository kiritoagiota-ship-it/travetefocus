"""Mede a CONTINUIDADE da animacao gravada pelo filme.py (CADA=1): para cada
quadro, quanto da area do Yoru mudou em relacao ao quadro anterior. Animacao
continua muda um pouco por quadro; um "pisca" (troca de pose seca, corte,
teleporte) muda muito de uma vez.
uso: python dev/continuidade.py PASTA [limite=0.35]
Saida: lista dos saltos e continuidade.png (grafico de mudanca por quadro)."""
import sys
import os
import json
import numpy as np
from PIL import Image, ImageDraw

pasta = sys.argv[1]
LIM = float(sys.argv[2]) if len(sys.argv) > 2 else 0.35
L = json.load(open(os.path.join(pasta, 'filme.json'), encoding='utf-8'))
Q = {rel: regs for rel, regs in L['quadros']}
sons = {}
ini = min((q for q, n in L['fases'] if n == 'cena comecou'), default=0)
for q, s in L['sons']:
    sons.setdefault(q - ini, []).append(s)
nomes = sorted(int(n[1:6]) for n in os.listdir(pasta) if n.startswith('f') and n.endswith('.png'))
W, H = Image.open(os.path.join(pasta, f'f{nomes[0]:05d}.png')).size
ant = None
serie = []
for q in nomes:
    vis = [r for r in Q.get(q, []) if r['op'] > 0.5]
    im = np.asarray(Image.open(os.path.join(pasta, f'f{q:05d}.png')).convert('RGB')).astype(int)
    if not vis:
        ant = None
        serie.append((q, None, ''))
        continue
    r = vis[0]
    ps = r['ps']
    cx, cy = r['x'], H - r['y']
    x0, x1 = int(max(0, cx - 16 * ps)), int(min(W, cx + 16 * ps))
    y0, y1 = int(max(0, cy - 26 * ps)), int(min(H, cy + 14 * ps))
    if ant is not None:
        a_im, a_r = ant
        caixa = (min(x0, a_r[0]), min(y0, a_r[1]), max(x1, a_r[2]), max(y1, a_r[3]))
        A = a_im[caixa[1]:caixa[3], caixa[0]:caixa[2]]
        B = im[caixa[1]:caixa[3], caixa[0]:caixa[2]]
        muda = (np.abs(A - B).max(axis=2) > 60)
        figura = (A.max(axis=2) > 35) | (B.max(axis=2) > 35)
        frac = muda.sum() / float(max(1, figura.sum()))
        motivo = []
        rp = [x for x in Q.get(q - 1, []) if x['op'] > 0.5]
        if rp:
            rp = rp[0]
            if r.get('des') != rp.get('des'):
                motivo.append('desenho')
            if abs(r['x'] - rp['x']) + abs(r['y'] - rp['y']) > 3 * ps:
                motivo.append('pulo de %d px' % (abs(r['x'] - rp['x']) + abs(r['y'] - rp['y'])))
            if abs(r['rot'] - rp['rot']) > 1:
                motivo.append('giro')
            if r['mug'] != rp['mug']:
                motivo.append('troca de forma')
        serie.append((q, frac, ','.join(motivo)))
    else:
        serie.append((q, None, ''))
    ant = (im, (x0, y0, x1, y1))

saltos = [(q, f, m) for q, f, m in serie if f is not None and f > LIM]
print(f'quadros: {len(serie)}  saltos (> {LIM:.0%} da figura num quadro so): {len(saltos)}')
for q, f, m in saltos:
    print(f'  {q / 60.0:6.2f}s  {f:5.0%}  {m}  {" ".join(sons.get(q, []))}')
vals = [f for _, f, _ in serie if f is not None]
print(f'mudanca media por quadro: {np.mean(vals):.1%}  mediana {np.median(vals):.1%}')

# grafico
Wg, Hg = 1400, 300
G = Image.new('RGB', (Wg, Hg + 40), (18, 18, 28))
d = ImageDraw.Draw(G)
n = len(serie)
for i, (q, f, m) in enumerate(serie):
    if f is None:
        continue
    x = int(i / n * Wg)
    h = int(min(1.0, f) * Hg)
    cor = (240, 70, 90) if f > LIM else ((240, 190, 70) if f > LIM * 0.6 else (80, 200, 255))
    d.line([(x, Hg), (x, Hg - h)], fill=cor)
ylim = Hg - int(LIM * Hg)
d.line([(0, ylim), (Wg, ylim)], fill=(120, 120, 120))
for s in range(0, int(serie[-1][0] / 60) + 1, 2):
    x = int(s * 60 / max(1, serie[-1][0]) * Wg)
    d.text((x + 2, Hg + 8), f'{s}s', fill=(200, 200, 200))
G.save(os.path.join(pasta, 'continuidade.png'))
