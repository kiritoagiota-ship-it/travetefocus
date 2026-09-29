import os
AQUI = os.path.dirname(os.path.abspath(__file__))
p = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(p, encoding='utf-8').read()
a = c.index('        # ── 1. pendurado por uma mao num canto de cima')
b = c.index('        # ── 6. golpe final (estilo Bleach)')
c = c[:a] + open(os.path.join(AQUI, 'danca.txt'), encoding='utf-8').read() + c[b:]
open(p, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
