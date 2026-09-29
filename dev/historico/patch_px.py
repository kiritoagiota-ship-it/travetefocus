import os, re
AQUI = os.path.dirname(__file__)
p = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(p, encoding='utf-8').read()


def troca(a, b, n=1):
    global c
    assert c.count(a) == n, (a[:80], c.count(a))
    c = c.replace(a, b)


def bloco(ini, fim, novo):
    global c
    a = c.index(ini)
    b = c.index(fim, a + 1)
    c = c[:a] + novo + c[b:]


# a meia-lua agora e a versao em pixels definida aqui
troca('from espadachim import CorteMeiaLua\n', '')
bloco('def _anel(camada, centro, r0, r1, dur, cor=CIANO, esp=None, achat=1.0):', 'def _clarao_boneco(',
      open(os.path.join(AQUI, 'efeitos_px.txt'), encoding='utf-8').read())
# o _risco_luz antigo (liso) sai
a = c.index('def _risco_luz(camada, x0, x1, y, dur, cor=CIANO, espessura=None):\n    """Risco reto de luz que cresce')
m = re.search(r'\n(def |class )', c[a + 10:])
c = c[:a] + c[a + 10 + m.start() + 1:]
# teleporte e entrada em pixels
bloco('def _teleporte(k, camada, faiscas, on_fim=None, cor=CIANO, dur=0.55, teto=None):',
      '# ═══════════════════════════════════════════════════════════════════\n#  GOLPE FINAL',
      open(os.path.join(AQUI, 'teleporte_px.txt'), encoding='utf-8').read())
# o risco liso dentro das metades sai (os cortes ja desenham o risco em pixels)
troca('''            if tex:
                m.texture = tex
            Color(0.6, 0.95, 1, 0.9)
            Line(points=[rx, ya, rx + rw, yb], width=dp(1.4))
            PopMatrix()''', '''            if tex:
                m.texture = tex
            PopMatrix()''')
# tamanho do pixel dos efeitos = texel do Yoru de cada cena
troca('''        kk = K.KiritoPixel(ps=ps)
        ps = kk.ps
''', '''        kk = K.KiritoPixel(ps=ps)
        ps = kk.ps
        _PX[0] = ps / float(K.R)
''')
troca('''        self.te = self.ps / float(K.R)
        self.k = K.KiritoPixel(ps=self.ps)''', '''        self.te = self.ps / float(K.R)
        _PX[0] = self.te
        self.k = K.KiritoPixel(ps=self.ps)''')
troca('''        ps = _ps_para(W, H)
        k = K.KiritoPixel(ps=ps)
        faiscas = K.Faiscas(n_max=140)''', '''        ps = _ps_para(W, H)
        k = K.KiritoPixel(ps=ps)
        _PX[0] = k.ps / float(K.R)
        faiscas = K.Faiscas(n_max=140)''')
open(p, 'w', encoding='utf-8').write(c)
print('ok')
