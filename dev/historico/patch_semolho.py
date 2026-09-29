"""Tira o rastro de luz dos olhos e o fogo antigo (ChamasReiatsu, sem uso)."""
pk = r'C:\Users\kirit\travetefocus\app\kirito.py'
k = open(pk, encoding='utf-8').read()


def corta(ini, fim, incl_fim=False):
    global k
    a = k.index(ini)
    b = k.index(fim, a)
    if incl_fim:
        b += len(fim)
    k = k[:a] + k[b:]


corta("        # rastro de luz no olho: quando ele se mexe rapido, o olho risca o ar\n",
      "        self.bind(pos=self._mover")
corta("            self._rastro_do_olho()\n", "        except Exception as e:\n            print(f\"[kirito] fisica")
corta("    def _ponto_mundo(self, lx, ly):\n", "    def _camadas(self, dt, frente, cima):")
corta("# ── fogo em quadros (flip-book de pixel art, como nos jogos) ─────────────\n", "carregar_assado()\n")
corta("def bordas_pose(p):\n", "def _runs(p, espelhar=False):")
open(pk, 'w', encoding='utf-8', newline='\r\n').write(k)
print('ok')
