"""Corte que grava a frase: efeito, titulo e coreografia nova."""
import os
AQUI = os.path.dirname(os.path.abspath(__file__))
pc = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(pc, encoding='utf-8').read()


def troca(a, b, n=1):
    global c
    assert c.count(a) == n, (a[:90], c.count(a))
    c = c.replace(a, b)


def ler(n):
    return open(os.path.join(AQUI, n), encoding='utf-8').read()


# 1. efeito
sec = "# ═══════════════════════════════════════════════════════════════════\n#  TITULO ESCRITO PELA ESPADA\n"
troca(sec, ler('grava.txt') + sec)
# oficina para sozinha quando nao tem mais nada para fazer
troca("""        self._fila = []                 # [(chave, gerador)]
        self._prontos = {}              # chave -> (Texture, x0, y0, largura, altura) em px
        self._ev = Clock.schedule_interval(self._passo, 0)

    def pedir(self, chave, arco, pal='katana'):
        self._fila.append((chave, _desenho_corte(arco, _PAL_CORTE[pal], self.u)))
""", """        self._fila = []                 # [(chave, gerador)]
        self._prontos = {}              # chave -> (Texture, x0, y0, largura, altura) em px
        self._ev = None

    def pedir(self, chave, arco, pal='katana'):
        self._fila.append((chave, _desenho_corte(arco, _PAL_CORTE[pal], self.u)))
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._passo, 0)
""")
troca("""                if res is not None:
                    self._fila.pop(0)
                    self._fechar(chave, res)
            return True
        except Exception as e:
            print(f"[cortes] preparar: {e}")
            self._fila = []
            return True
""", """                if res is not None:
                    self._fila.pop(0)
                    self._fechar(chave, res)
            if not self._fila:
                self._ev = None
                return False
            return True
        except Exception as e:
            print(f"[cortes] preparar: {e}")
            self._fila = []
            self._ev = None
            return False
""")
# 2. titulo
troca("""        self._trechos = []
        with self.canvas:
            PushMatrix()
            self._sc_glow""", """        self._trechos = []
        self._gravados = set()                     # trechos que um corte ja completou
        with self.canvas:
            PushMatrix()
            self._sc_glow""")
troca("""    def clarao_final(self):
        \"\"\"Titulo inteiro pulsa""", ler('grava_titulo.txt') + """    def clarao_final(self):
        \"\"\"Titulo inteiro pulsa""")
# 3. danca
a = c.index("        # ── 1-5. DANCA CORTANTE")
b = c.index("        # ── 6. golpe final (estilo Bleach)")
c = c[:a] + ler('danca_nova.txt') + c[b:]
# 4. o deslocamento tambem congela no hit-stop
troca("""    def _p(dt):
        try:
            t[0] += dt
            u = min(1.0, t[0] / dur)
            if on_passo:
                on_passo(u)          # troca a pose antes de enquadrar (sem 1 quadro de atraso)""",
      """    def _p(dt):
        try:
            if getattr(k, '_pausa', 0) > 0:
                return True          # hit-stop: o corpo congela junto com a pose
            t[0] += dt
            u = min(1.0, t[0] / dur)
            if on_passo:
                on_passo(u)          # troca a pose antes de enquadrar (sem 1 quadro de atraso)""")
# 5. golpe final do Mugetsu grava o CUS
troca("""            tv = estado.get('trevas')
            if tv is not None:
                tv.cortar(cy)
            ax_i, _ = kk.ancora()""", """            tv = estado.get('trevas')
            if tv is not None:
                tv.cortar(cy)
            cortar('cus', 4, dur=0.18)               # a luz roxa atravessa a frase e grava o CUS
            ax_i, _ = kk.ancora()""")
troca("""            i0, i1 = _TRECHOS[4]
            titulo.revelar(i0, i1, dur=0.05)
            for li, letra""", """            for i0, i1 in _TRECHOS:
                titulo.garantir(i0, i1)
            for li, letra""")
# 6. final: guarda as duas espadas e fica em pose (sem teleporte)
a = c.index("        def _separa():")
b = c.index("        # rede de seguranca: a cena nunca prende o app")
c = c[:a] + ler('final_novo.txt') + c[b:]
open(pc, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
