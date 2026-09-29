import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p import patch
T = os.path.dirname(os.path.abspath(__file__))
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'cenas.py')
nuvem = open(os.path.join(T, 'nuvem.txt'), encoding='utf-8').read()
bankai = open(os.path.join(T, 'bankai.txt'), encoding='utf-8').read()
patch(A, [
    # oficina: tambem prepara coisas que nao viram textura (os quadros da nuvem)
    ("""        self._fila = []                 # [(chave, gerador)]
        self._prontos = {}              # chave -> (Texture, x0, y0, largura, altura) em px
        self._ev = None
""", """        self._fila = []                 # [(chave, gerador)]
        self._prontos = {}              # chave -> (Texture, x0, y0, largura, altura) em px
        self._crus = set()              # chaves cujo resultado fica como veio do gerador
        self._ev = None

    def pedir_bruto(self, chave, gerador):
        \"\"\"Prepara um gerador qualquer (o ultimo valor dele e o resultado).\"\"\"
        self._crus.add(chave)
        self._fila.append((chave, gerador))
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._passo, 0)
"""),
    ("""    def _fechar(self, chave, res):
        dados, gx0, gy0, w, h = res""", """    def _fechar(self, chave, res):
        if chave in self._crus:
            self._prontos[chave] = res
            return
        dados, gx0, gy0, w, h = res"""),
    ("# ═══════════════════════════════════════════════════════════════════\n#  TITULO ESCRITO PELA ESPADA\n",
     nuvem + "# ═══════════════════════════════════════════════════════════════════\n#  TITULO ESCRITO PELA ESPADA\n"),
    ("""            _mover(kk, (ax, ay), alvo, 0.38, altura=h, on_fim=_fundir, limite=(area, m),""",
     """            _mover(kk, (ax, ay), alvo, 0.38, altura=h, on_fim=_ban, limite=(area, m),"""),
])
c = open(A, encoding='utf-8').read()
a = c.index("        def _fundir():")
b = c.index("        def _posiciona():")
seg = c[a:b]
assert "def _fitas(" in seg and "def _sugar" in seg
c = c[:a] + bankai + c[b:]
open(A, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
