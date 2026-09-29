"""Referencia -> mapa de caracteres na grade nova (cores classificadas a mao).
uso: python quant.py x0 y0 x1 y1 escala saida"""
import sys
from PIL import Image
import numpy as np
x0, y0, x1, y1 = (int(v) for v in sys.argv[1:5])
esc = float(sys.argv[5])
ref = Image.open('refs/yoru_ref.jpg').convert('RGB').crop((x0, y0, x1, y1))
w, h = round((x1 - x0) / esc), round((y1 - y0) / esc)
p = np.asarray(ref.resize((w, h), Image.BOX)).astype(float)
# cores de referencia (medidas na imagem) -> caractere da paleta do Yoru
REF = [
    ((31, 53, 80), '.'), ((36, 60, 90), '.'),
    ((10, 10, 20), 'J'), ((22, 22, 38), 'H'), ((38, 38, 62), 'I'), ((70, 70, 110), 'I'), ((110, 110, 160), 'h'),
    ((150, 150, 200), 'h'),
    ((40, 150, 230), 'O'), ((60, 190, 250), 'O'), ((30, 100, 170), 'O'),
    ((250, 222, 190), 'S'), ((235, 190, 160), 'S'), ((215, 150, 120), 's'), ((180, 100, 80), 't'), ((130, 70, 60), 't'),
    ((60, 80, 150), '3'), ((90, 110, 190), 'm'), ((200, 210, 240), 'n'), ((25, 30, 60), 'E'),
]
cores = np.array([c for c, _ in REF], float)
ch = [k for _, k in REF]
linhas = []
for r in range(h):
    l = ''
    for c in range(w):
        d = np.linalg.norm(cores - p[r, c], axis=1)
        l += ch[int(np.argmin(d))]
    linhas.append(l)
open(sys.argv[6], 'w').write('\n'.join(linhas) + '\n')
print(w, h)
print('   ' + ''.join(str(i // 10) for i in range(w)))
print('   ' + ''.join(str(i % 10) for i in range(w)))
for r, l in enumerate(linhas):
    print('%2d %s' % (r, l))
