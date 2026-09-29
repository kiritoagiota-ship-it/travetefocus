"""Desenha as sequencias novas quadro a quadro (tiras), sem abrir janela.
uso: python seqs.py SAIDA_PREFIXO"""
import os
import sys
sys.path.insert(0, os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app'))
os.environ['KIVY_NO_ARGS'] = '1'
os.environ['KIVY_LOG_MODE'] = 'PYTHON'
from PIL import Image, ImageDraw
import kirito as K

P = K.POSE_A
_com = lambda p, **kw: dict(p, **kw)
saida = sys.argv[1]


def tira(nome, quadros, ps=5, x0=10, x1=60, y0=8, y1=62, cols=8, marca=None):
    W, H = (x1 - x0) * ps, (y1 - y0) * ps
    linhas = (len(quadros) + cols - 1) // cols
    S = Image.new('RGB', (W * cols, (H + 12) * linhas), (6, 6, 12))
    d = ImageDraw.Draw(S)
    for i, p in enumerate(quadros):
        px = K.montar(p)
        ox, oy = (i % cols) * W, (i // cols) * (H + 12)
        d.text((ox + 2, oy), f'{i}' + (' *' if marca is not None and i == marca else ''),
               fill='yellow' if i != marca else 'red')
        for (x, y), c in px.items():
            if not (x0 <= x < x1 and y0 <= y < y1):
                continue
            r, g, b, a = K._PALETA[c]
            bg = (6, 6, 12)
            col = tuple(int(255 * (v * a) + bgc * (1 - a)) for v, bgc in zip((r, g, b), bg))
            X = ox + (x - x0) * ps
            Y = oy + 12 + (y1 - 1 - y) * ps
            d.rectangle([X, Y, X + ps - 1, Y + ps - 1], fill=col)
        # linha do chao (sola da bota) para ver o peso
        d.line([ox, oy + 12 + (y1 - 1 - (K._PES - 1)) * ps, ox + W, oy + 12 + (y1 - 1 - (K._PES - 1)) * ps],
               fill=(40, 40, 70))
    S.save(f'{saida}_{nome}.png')
    print(nome, len(quadros), S.size)


# 1. TRA (iai)
ch, ir = K.golpe(P['saca0'], P['corta1'], n_arma=3, prende=3, segue=3, volta=6,
                 lamina_recua=False, seg=P['segue1'])
ch = [(2, _com(P['agacha'], olhos='s'), 'segura'), (3, _com(P['agacha'], olhos='s'), 'out')] + ch
tira('tra', K.sequencia(ch), marca=ir + 5)

# 2-4. combo
for nome, a, c in (('ve', 'sobe_arma', 'sobe_corta'), ('te', 'desce_arma', 'desce_corta'),
                   ('fo', 'x_arma', 'x_corta')):
    ch, ir = K.golpe(P[a], P[c], n_arma=2, prende=1, segue=3, volta=4)
    tira(nome, K.sequencia(ch), marca=ir)

# 5. fusao (54 quadros)
seq = K.sequencia([(3, _com(P['agacha'], olhos='s'), 'out'), (5, _com(P['dupla'], olhos='s'), 'out'),
                   (20, P['une_a'], 'suave'), (14, P['une_b'], 'segura'), (12, P['une_b'])])
for f, q in enumerate(seq):
    if f >= 8:
        u = min(1.0, (f - 8) / 30.0)
        q['sobe'] = u
        q['lift'] = q['lift'] + 1.4 * u
        if f >= 26:
            q['dx'] = q['dx'] + K._TREMOR[(f // 2) % len(K._TREMOR)]
tira('fusao', seq[::2], y1=70)

# 6. golpe final: meio + rastro + corte, para (continuidade)
corte = _com(P['evo_corte'], sobe=1.0)
meio = K.smear(K.misturar(P['evo_carga'], corte, 0.5, 0.5), P['evo_carga']['a1'])
fim_p = P['evo_fim']
seg = _com(fim_p, a1=fim_p['a1'] - 20, dx=fim_p['dx'] + 1, sobe=0.6)
q = K.poder(P['evo_carga'], n=6, de=0.7, olhos='l')
q += [meio, K.smear(corte, P['evo_carga']['a1']), corte]
q += K.sequencia([(2, corte, 'out'), (6, seg, 'mola'), (2, fim_p, 'segura'), (1, fim_p)])
tira('final', q, x1=72)

# 7. chiburi + embainhar
dupla = _com(P['dupla'], olhos='s')
seq = K.sequencia([(3, dupla, 'out'), (2, P['chiburi_a'], 'out'), (4, _com(P['chiburi'], olhos='s'), 'segura'),
                   (6, _com(P['chiburi'], olhos='s'), 'suave'), (8, P['embainha_a'], 'in'),
                   (2, P['embainha_b'], 'out'), (3, P['embainha_c'], 'mola'), (1, P['guardado'])])
tira('chiburi', seq)

# 8. saca2 (Dark Repulser)
seq = K.sequencia([(3, _com(P['segue1'], olhos='s')), (2, _com(P['pega2'], olhos='s'), 'segura'),
                   (2, _com(P['pega2'], olhos='s'), 'out'), (5, _com(P['saca2'], olhos='s'), 'mola'),
                   (3, _com(P['dupla'], olhos='s'), 'segura'), (1, _com(P['dupla'], olhos='s'))])
tira('saca2', seq)

# 9. pendurado: kamae
seq = K.sequencia([(2, P['pendurado_b']), (4, P['pendurado_b'], 'out'),
                   (2, _com(P['pendurado2'], olhos='s'), 'segura'), (1, _com(P['pendurado2'], olhos='s'))])
tira('kamae', seq, y1=70)
