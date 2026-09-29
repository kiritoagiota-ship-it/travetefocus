"""Forma Bankai igual a referencia do usuario: cabelo preto com mechas roxas
e pontas que queimam em chamas roxas, sobretudo rasgado com chamas roxas
mais altas nas pontas, espada grande ESCURA com fio roxo aceso dos dois
lados e ponta afiada (sem o xadrez), guarda do infinito roxa. E o recorte
do boneco (para a transformacao aparecer por faixas, pixel a pixel)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'kirito.py'), [
    ("""from kivy.graphics import (Color, Rectangle, Mesh, PushMatrix, PopMatrix,
                           Translate, Rotate, Scale)""",
     """from kivy.graphics import (Color, Rectangle, Mesh, PushMatrix, PopMatrix,
                           Translate, Rotate, Scale)
from kivy.graphics.stencil_instructions import StencilPush, StencilUse, StencilUnUse, StencilPop"""),
    # cabelo preto com brilho roxo
    ("""           '3': 'V', 'm': 'L', 'i': 'd', 'U': 'o', '%': 'd', '9': 'L', 'x': '<', 'X': '>'}""",
     """           '3': 'V', 'm': 'L', 'i': 'd', 'U': 'o', '%': 'd', '9': 'L', 'x': '<', 'X': '>',
           'h': 'd', 'I': '&'}                      # cabelo: o brilho vira roxo"""),
    # pontas do cabelao queimando
    ("""            if u > fim:                                    # ponta em fumaca e brasa
                if (q[0] * 3 + q[1] + f6) % 3:
                    continue
                ch = 'o' if ((q[0] * 7 + q[1] * 3 + f6) % 9 == 0) else ('&' if u > fim + 0.06 else 'J')""",
     """            if u > fim:                                    # a ponta queima em chama roxa
                h = (q[0] * 3 + q[1] * 5 + f6 * 2) % 7
                if u > fim + 0.09 and h > 2:
                    continue                               # lingua de fogo solta na ponta
                ch = 'L' if h == 0 else ('V' if h < 3 else ('F' if h < 5 else 'o'))"""),
    # chamas mais altas nas pontas do sobretudo
    ("""        if not mug or u < fim_u - 0.12:
            return ch
        k2 = (fim_u - u) / 0.12                        # 1 longe da ponta .. 0 na ponta""",
     """        if not mug or u < fim_u - 0.2:
            return ch
        k2 = (fim_u - u) / 0.2                         # 1 longe da ponta .. 0 na ponta"""),
    # espada do Bankai: lamina escura, fio roxo aceso, ponta afiada
    ("""        if evo and k < ini:
            return None
        corta = max(0.0, k - (L - 9))""", """        if evo and k < ini:
            return None
        if evo:                                            # lamina do Bankai (referencia)
            w = 6.5 if k < L - 16 else 6.5 * max(0.0, (L + 2 - k) / 18.0)
            if abs(j) > w + 0.01:
                return None
            borda = w - abs(j)
            if borda < 1.0:
                return 'L' if j > 0 else 'V'                  # fio aceso (lado da luz mais claro)
            if borda < 2.0:
                return 'V' if j > 0 else 'F'
            if borda < 3.0:
                return 'F' if j > 0 else 'd'
            if jn == 0:
                return 'o' if (kk + mv) % 11 < 2 else 'K'    # sulco central com runas correndo
            return 'W' if jn > 0 else 'D'
        corta = max(0.0, k - (L - 9))"""),
    ("""        for (cx, cy) in _INF:                                  # guarda: o infinito
            for dj in (-0.5, 0.0, 0.5):
                pp(4.0 + cy * 6.0, cx * 10.5 + dj, 'Y')
        for (cx, cy) in _INF[::4]:
            pp(4.0 + cy * 6.0 * 0.82, cx * 10.5 * 0.9, 'F')
        for j in (-6, 6):
            pp(4.0, j, '9')
        pp(4.0, 0, '!')
        pp(L + 2, 6, fio)
        pp(L + 3, 6, fio)""", """        for (cx, cy) in _INF:                                  # guarda: o infinito (roxo)
            for dj in (-0.5, 0.0, 0.5):
                pp(4.0 + cy * 6.0, cx * 10.5 + dj, 'V')
        for (cx, cy) in _INF[::4]:
            pp(4.0 + cy * 6.0 * 0.82, cx * 10.5 * 0.9, 'L')
        for j in (-6, 6):
            pp(4.0, j, 'L')
        pp(4.0, 0, '!')"""),
    # rastro mais escuro (nao cobre o boneco com uma mancha clara)
    ("""        if cor is None:
            cor = (0.66, 0.36, 1.0) if self._base.get('mugetsu') else (0.0, 0.78, 1.0)""",
     """        if cor is None:
            cor = (0.42, 0.18, 0.78) if self._base.get('mugetsu') else (0.0, 0.5, 0.82)"""),
    ("""    def fantasma(self, cor=None, alfa=0.5, duracao=0.12):""",
     """    def fantasma(self, cor=None, alfa=0.42, duracao=0.12):"""),
    # recorte (stencil) do boneco
    ("""    def _virou(self, *_):""", """    def recortar(self, y0=None, y1=None):
        \"\"\"Mostra so a faixa de altura y0..y1 do boneco (coordenadas do pai;
        None = sem limite). recortar() tira o recorte. Na transformacao: o
        Yoru normal por cima da linha de energia e o Bankai por baixo.\"\"\"
        if y0 is None and y1 is None:
            if getattr(self, '_recorte', None) is not None:
                for grupo, ins in self._recorte:
                    for i in ins:
                        try:
                            grupo.remove(i)
                        except Exception:
                            pass
                self._recorte = None
            return
        a = -100000.0 if y0 is None else float(y0)
        b = 100000.0 if y1 is None else float(y1)
        if getattr(self, '_recorte', None) is None:
            r1 = Rectangle(pos=(-100000, a), size=(200000, b - a))
            r2 = Rectangle(pos=(-100000, a), size=(200000, b - a))
            antes = [StencilPush(), r1, StencilUse()]
            depois = [StencilUnUse(), r2, StencilPop()]
            for i in antes:
                self.canvas.before.add(i)
            for i in depois:
                self.canvas.after.add(i)
            self._recorte = [(self.canvas.before, antes), (self.canvas.after, depois)]
            self._rec_rects = (r1, r2)
        for r in self._rec_rects:
            r.pos = (-100000, a)
            r.size = (200000, max(0.0, b - a))

    def _virou(self, *_):"""),
])
print('ok')
