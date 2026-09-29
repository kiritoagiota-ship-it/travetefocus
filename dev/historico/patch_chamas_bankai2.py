"""Chamas do Bankai maiores (linguas de fogo de verdade, nao pingos), anel
da transformacao mais cheio e o estouro final em lascas pequenas que voam
para fora (nao blocos em cima do rosto)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'cenas.py'), [
    ("""        chamas = _ChamasBankai(kk, 2 * ps / float(K.R))   # chamas roxas do Bankai (atras dele)""",
     """        chamas = _ChamasBankai(kk, 3 * ps / float(K.R))   # chamas roxas do Bankai (atras dele)"""),
    ("""            self._acc += self.forca * 75.0 * dt""", """            self._acc += self.forca * 95.0 * dt"""),
    ("""                self._f.append({'x': x, 'y': y, 'vy': alt * random.uniform(0.7, 1.3), 't': 0.0,
                                'vida': vida, 'n': random.choice((3, 4, 4, 5)),""",
     """                self._f.append({'x': x, 'y': y, 'vy': alt * random.uniform(0.6, 1.1), 't': 0.0,
                                'vida': vida, 'n': random.choice((4, 5, 5, 6)),"""),
    ("""                    larg = 2 if (i < n - 2 and a < 0.45) else 1          # base mais larga, ponta fina""",
     """                    larg = 3 if (i == 0 and a < 0.3) else (2 if (i < n - 2 and a < 0.6) else 1)"""),
    ("""        # a faixa de corte, bem fina, atravessando o corpo
        k0 = math.floor((cx - a) / u)
        k1 = math.floor((cx + a) / u)
        for k in range(k0, k1 + 1):
            if (k + f) % 3:
                pts.setdefault('L', []).append((k * u, math.floor(y / u) * u, u, u))""",
     """        # a faixa de corte atravessando o corpo: linha clara com fogo roxo por cima
        k0 = math.floor((cx - a) / u)
        k1 = math.floor((cx + a) / u)
        yb = math.floor(y / u) * u
        for k in range(k0, k1 + 1):
            h = (k * 3 + f) % 5
            pts.setdefault('L' if h else 'V', []).append((k * u, yb, u, u))
            if h < 2:
                pts.setdefault('F', []).append((k * u, yb + u, u, u))
            if h == 0:
                pts.setdefault('o', []).append((k * u, yb + 2 * u, u, u))"""),
    ("""            ax, ay = kk.ancora()
            faiscas.estourar(ax, ay + alt * 0.55, ROXO, n=20, forca=dp(160), tam=ps, gravidade=-dp(100))
            _som('titulo')
            _tremer(8)
            ag.depois(0.5, _funde)""", """            ax, ay = kk.ancora()
            faiscas.estourar(ax, ay + alt * 0.55, ROXO, n=24, forca=dp(260), tam=te * 2, gravidade=-dp(60))
            _som('titulo')
            _tremer(8)
            ag.depois(0.5, _funde)"""),
])
print('ok')
