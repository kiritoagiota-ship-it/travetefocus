"""Troca o bloco PANO E MECHAS do kirito.py pelo pano.txt (idempotente)."""
import os
AQUI = os.path.dirname(os.path.abspath(__file__))
p = r'C:\Users\kirit\travetefocus\app\kirito.py'
c = open(p, encoding='utf-8').read()
ini = c.index('# ═══════════════════════════════════════════════════════════════════\n#  PANO E MECHAS')
fim = c.index('def _bainha_costas(px, x, y):')
c = c[:ini] + open(os.path.join(AQUI, 'pano.txt'), encoding='utf-8').read() + c[fim:]
open(p, 'w', encoding='utf-8', newline='\r\n').write(c)
print('ok')
