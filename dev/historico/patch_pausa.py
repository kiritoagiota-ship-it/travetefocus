import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'kirito.py')
patch(A, [("""        try:
            if self._pausa > 0:
                return
            dt = min(dt, 1 / 15.)
            self._t += dt""", """        try:
            if self._pausa > 0:
                if self._ev is None:          # sem sequencia tocando, o hit-stop acaba sozinho
                    self._pausa = max(0.0, self._pausa - dt)
                return
            dt = min(dt, 1 / 15.)
            self._t += dt""")])
print('ok')
