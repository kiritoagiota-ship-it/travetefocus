import re
p = r'C:\Users\kirit\travetefocus\app\kirito.py'
s = open(p, 'rb').read().decode('utf-8').replace('\r\n', '\n')


def troca(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)


troca('from kivy.graphics import (Color, Rectangle, PushMatrix, PopMatrix,\n                           Translate, Rotate, Scale)',
      'from kivy.graphics import (Color, Rectangle, Mesh, PushMatrix, PopMatrix,\n                           Translate, Rotate, Scale)')

troca('class ChamasReiatsu(Widget):', '''class LotePixels:
    """Pixels quadrados de poucas cores, um Mesh por cor: bem mais leve no
    celular que um Rectangle por pixel. cores = ((nome, rgba), ...);
    desenhar({nome: [(x, y, lado), ...]})."""

    def __init__(self, canvas, cores):
        self.m = {}
        with canvas:
            for nome, rgba in cores:
                c = Color(*rgba)
                self.m[nome] = (c, rgba[3], Mesh(mode='triangles', vertices=[], indices=[]))

    def desenhar(self, pontos, alfa=1.0):
        for nome, (c, a0, mesh) in self.m.items():
            vs, ids = [], []
            for i, (x, y, t) in enumerate(pontos.get(nome, ())):
                vs.extend((x, y, 0, 0, x + t, y, 0, 0, x + t, y + t, 0, 0, x, y + t, 0, 0))
                b = 4 * i
                ids.extend((b, b + 1, b + 2, b, b + 2, b + 3))
            mesh.vertices = vs
            mesh.indices = ids
            c.a = a0 * alfa


class ChamasReiatsu(Widget):''')

troca('''        self.k = k
        self.frente = frente
        self.n_linguas = linguas
        self._linguas = []
        self._p = []
        self._ins = []
        with self.canvas:
            for _ in range(n_max):
                c = Color(1, 1, 1, 0)
                r = Rectangle(size=(0, 0))
                self._ins.append((c, r))
        self._livres = list(range(n_max))
        self._ev = Clock.schedule_interval(self._tick, 1 / 30.)''', '''        self.k = k
        self.frente = frente
        self.n_linguas = linguas
        self.n_max = n_max
        self._linguas = []
        self._p = []
        cores = [('r%d' % i, (c[0], c[1], c[2], a)) for i, (c, a) in enumerate(self.DEGRAUS)]
        cores += [('a%d' % i, (c[0], c[1], c[2], a)) for i, (c, a) in enumerate(self.DEGRAUS_AZUL)]
        self._lote = LotePixels(self.canvas, cores)
        self._ev = Clock.schedule_interval(self._tick, 1 / 30.)''')

troca("""                'f': random.uniform(8, 14), 'amp': random.uniform(1.5, 3.5) * E,
                'vy': random.uniform(30, 48) * E * (1.25 if alto else 1.0),
                'vida_p': random.uniform(0.32, 0.55) * (1.35 if alto else 1.0),""",
      """                'f': random.uniform(8, 14), 'amp': random.uniform(1.5, 3.5) * E,
                'vy': random.uniform(30, 48) * (1.25 if alto else 1.0),
                'vida_p': random.uniform(0.32, 0.55) * E * (1.35 if alto else 1.0),""")

troca('''                if self.frente and random.random() < 0.7:
                    continue
                if not self._livres:
                    continue
                i = self._livres.pop()
                vida = L['vida_p'] * (0.5 if self.frente else 1.0)
                self._p.append({'i': i, 'x': L['tx'] + random.uniform(-0.6, 0.6), 'y': float(L['ty']),''', '''                if self.frente and random.random() < 0.7:
                    continue
                if len(self._p) >= self.n_max:
                    continue
                vida = L['vida_p'] * (0.5 if self.frente else 1.0)
                self._p.append({'x': L['tx'] + random.uniform(-0.6, 0.6), 'y': float(L['ty']),''')

velho = s[s.index("            vivos = []\n            ox, oy = k.x, k.y\n            for f in self._p:"):s.index("            self._p = vivos\n")]
novo = '''            vivos = []
            ox, oy = k.x, k.y
            pontos = {}
            for f in self._p:
                f['vida'] -= dt
                if f['vida'] <= 0:
                    continue
                u = 1 - f['vida'] / f['v0']
                f['y'] += f['vy'] * dt
                f['vy'] *= 0.985
                # a lingua ondula (mais na ponta) e tomba para tras
                lx = f['x'] + math.sin(f['fase'] + u * f['f']) * f['amp'] * u - 5.0 * E * u
                tx = (TW - 1 - lx) if f['esp'] else lx
                d = min(4, int(u * 5))
                if self.frente:
                    tam = 1
                else:                                     # a lingua afina subindo
                    tam = 3 if u < 0.25 else (2 if u < 0.6 else 1)
                pontos.setdefault(('a%d' if f['azul'] else 'r%d') % d, []).append(
                    (ox + round(tx) * te, oy + round(f['y']) * te, tam * te))
                vivos.append(f)
'''
s = s.replace(velho, novo)
troca('''            self._p = vivos
        except Exception as e:
            print(f"[chamas] {e}")''', '''            self._p = vivos
            self._lote.desenhar(pontos, 0.8 if self.frente else 1.0)
        except Exception as e:
            print(f"[chamas] {e}")''')
open(p, 'wb').write(s.replace('\n', '\r\n').encode('utf-8'))

# ── cenas: usa o lote do kirito, casulo fecha de verdade, aura mais forte ──
p2 = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(p2, encoding='utf-8').read()
a = c.index('class _Lote:')
b = c.index('class _Casulo:')
c = c[:a] + c[b:]
c = c.replace('self.l_tras = _Lote(self.w_tras.canvas, self.CORES)', 'self.l_tras = K.LotePixels(self.w_tras.canvas, self.CORES)')
c = c.replace('self.l_frente = _Lote(self.w_frente.canvas, self.CORES)', 'self.l_frente = K.LotePixels(self.w_frente.canvas, self.CORES)')
c = c.replace("""                        cor = ('lilas' if pulso > 0.5 else 'roxo') if borda else ('meio' if lim < 0.5 else 'esc')""",
              """                        if borda:
                            cor = 'lilas' if pulso > 0.5 else 'roxo'
                        else:
                            cor = 'roxo' if (int((dx + dy) / passo) % 3 == 0) else 'meio'""")
c = c.replace("""            estado['casulo'] = _Casulo(kk, camada, t_sobe=0.8, t_fecha=0.45)""",
              """            estado['casulo'] = _Casulo(kk, camada, t_sobe=0.7, t_fecha=0.32)""")
c = c.replace("""            kk.empurrar(cabelo=12, lift=8, capa=-10)
            ag.depois(0.9, _sugar)""", """            kk.empurrar(cabelo=12, lift=8, capa=-10)
            aura.alvo = 0.7                              # a espada acende: roxo e azul
            ag.depois(0.9, _sugar)""")
assert 'K.LotePixels' in c and "aura.alvo = 0.7                              # a espada" in c
open(p2, 'w', encoding='utf-8').write(c)
print('ok')
