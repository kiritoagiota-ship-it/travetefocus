import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'kirito.py'), [
    ("        y = -70.0 + 115.0 * u + 9.0 * math.sin(t)\n",
     "        y = -70.0 + 88.0 * u + 9.0 * math.sin(t)           # para no peito (nao passa no rosto)\n"),
    ("            self._cor.a = min(1.0, self.forca * 1.4)\n",
     "            # a parte da frente e um pouco transparente: o corpo aparece atras\n"
     "            self._cor.a = min(1.0, self.forca * 1.4) * (0.78 if self.lado == 'frente' else 1.0)\n"),
])
patch(os.path.join(A, 'cenas.py'), [
    ("            ag.depois(1.3, _ergue)\n", "            ag.depois(0.8, _ergue)\n"),
])
print('ok')
