import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'cenas.py')
patch(A, [("""        olho = (k.x + (ex + 0.5) * te, k.y + (ey + 0.5) * te)
        topo = _topo_cabeca(k)
        u = max(1.0, round(te * 1.5))
        h = len(self.mapa)
        w = len(self.mapa[0])
        if self.tipo == 'gota':               # do lado da cabeca, na frente
            return topo[0] + frente * te * 11 - w * u / 2.0, topo[1] - te * 16 - h * u, u
        if self.tipo == 'brilho':             # em cima do olho
            u = max(1.0, round(te))
            return olho[0] - w * u / 2.0, olho[1] - h * u / 2.0 + te, u
        if self.tipo == 'rubor':              # na bochecha, embaixo do olho
            u = max(1.0, round(te))
            return olho[0] - frente * te * 2 - w * u / 2.0, olho[1] - te * 6, u
        # !!, ?, nota: acima da cabeca, um pouco para tras
        return topo[0] - frente * te * 6 - w * u / 2.0, topo[1] + te * 2, u""",
"""        olho = (k.x + (ex + 0.5) * te, k.y + (ey + 0.5) * te)
        u = max(2.0, round(te * 2.2))         # grande o bastante para ler no celular
        h = len(self.mapa)
        w = len(self.mapa[0])
        if self.tipo == 'gota':               # do lado da testa, na frente do rosto
            return olho[0] + frente * te * 12 - w * u / 2.0, olho[1] + te * 3, u
        if self.tipo == 'brilho':             # em cima do olho
            u = max(1.0, round(te * 1.2))
            return olho[0] - w * u / 2.0, olho[1] - h * u / 2.0 + te, u
        if self.tipo == 'rubor':              # na bochecha, embaixo do olho
            u = max(1.0, round(te))
            return olho[0] - frente * te * 2 - w * u / 2.0, olho[1] - te * 7, u
        # !!, ?, nota: acima da cabeca, um pouco para tras
        return olho[0] - frente * te * 10 - w * u / 2.0, olho[1] + te * 30, u""")])
print('ok')
