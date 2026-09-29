import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'cenas.py'), [("""        def forma(t, p, u):
            k = min(1.0, t / dur)
            e = 1 - (1 - k) ** 3
            r = r0 + (r1 - r0) * e
            g = max(u, e0 * 1.4 * (1 - k))
            n = max(12, int(2 * math.pi * r / u) + 1)""", """        def forma(t, p, u):
            k = min(1.0, t / dur)
            e = 1 - (1 - k) ** 3
            r = r0 + (r1 - r0) * e
            g = max(u, e0 * 1.4 * (1 - k))
            # anel enorme: pixel um pouco maior (senao passa do limite de um desenho)
            u = u * max(1, int(math.ceil(math.sqrt(2 * math.pi * r * (g + u) / (u * u * 9000.0)))))
            g = max(u, g)
            n = max(12, int(2 * math.pi * r / u) + 1)""")])
patch(os.path.join(A, 'kirito.py'), [("""    def desenhar(self, pontos, alfa=1.0):
        for nome, (c, a0, mesh) in self.m.items():
            vs, ids = [], []
            for i, r in enumerate(pontos.get(nome, ())):""", """    def desenhar(self, pontos, alfa=1.0):
        for nome, (c, a0, mesh) in self.m.items():
            vs, ids = [], []
            # um Mesh aceita no maximo 65535 vertices (16383 quadradinhos)
            for i, r in enumerate(pontos.get(nome, ())[:16000]):""")])
print('ok')
