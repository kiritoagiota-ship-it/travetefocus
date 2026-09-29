import os, re
AQUI = os.path.dirname(__file__)
p = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(p, encoding='utf-8').read()


def troca(a, b, n=1):
    global c
    assert c.count(a) == n, (a[:80], c.count(a))
    c = c.replace(a, b)


bloco = open(os.path.join(AQUI, 'bcd.txt'), encoding='utf-8').read()
bloco = bloco.replace("""            k.mostrar(_com(P['saca0'] if pose.get('a1') is None else pose, pernas='avanco_baixo', olhos='s'))""",
                      """            k.mostrar(_com(pose, pernas='avanco_baixo', olhos='s'))""")
bloco = bloco.replace('''def _entrar(s, on_fim):''', '''def _entrar(s, on_fim, tipos=('teleporte', 'queda', 'corrida', 'sombra')):''')
bloco = bloco.replace('''    tipo = random.choice(('teleporte', 'queda', 'corrida', 'sombra'))''', '''    tipo = random.choice(tipos)''')
troca('''# um Yoru por vez: enquanto uma cena curta esta rodando, a proxima espera na''',
      bloco + '''# um Yoru por vez: enquanto uma cena curta esta rodando, a proxima espera na''')
# sombra e poeira no _Mini
troca('''        self.cam.add_widget(K.RastroLamina(self.k, self.faiscas))
        self.cam.add_widget(self.k)
        self.cam.add_widget(self.faiscas)
        self.area = _limites()''', '''        self.cam.add_widget(_Sombra(self.k))
        self.cam.add_widget(K.RastroLamina(self.k, self.faiscas))
        self.cam.add_widget(self.k)
        self.cam.add_widget(self.faiscas)
        self.area = _limites()''')
troca('''    def no_quadro(self, x, y, poses):
        return _no_quadro(self.k, x, y, poses, self.area, dp(2))''', '''    def no_quadro(self, x, y, poses):
        return _no_quadro(self.k, x, y, poses, self.area, dp(2))

    def poeira(self, lado=0):
        """Poeira nos pes (pouso, freada)."""
        ax, _ = self.k.ancora()
        y = self.k.y + K._PES * self.ps
        for sentido in ((-1, 1) if not lado else (lado,)):
            self.faiscas.estourar(ax + sentido * self.ps * 3, y, POEIRA, n=5, forca=dp(70),
                                  tam=self.te * 2, gravidade=dp(260))''')
# entradas sorteadas no lugar do teleporte fixo
n0 = c.count('_materializar(k, s.cam, s.faiscas, dur=')
c = re.sub(r"_materializar\(k, s\.cam, s\.faiscas, dur=[0-9.]+, on_fim=", "_entrar(s, ", c)
print('entradas trocadas:', n0)
# o corte em X comeca no ar: so teleporte ou corrida
troca('''        _entrar(s, lambda: Clock.schedule_once(lambda dt: _salta(), 0.12))''',
      '''        _entrar(s, lambda: Clock.schedule_once(lambda dt: _salta(), 0.12), tipos=('teleporte', 'corrida'))''')
# quadros de impacto de anime nos golpes grandes
troca('''        def _crava():
            k.impacto(forte=True)
            k.pausar(0.12)
            _som('golpe_final')''', '''        def _crava():
            k.impacto(forte=True)
            k.pausar(0.14)
            _quadro_impacto(s.cam, k, (s.cx, s.cy))
            _som('golpe_final')''')
troca('''            tv = estado.get('trevas')
            if tv is not None:
                tv.cortar(cy)
            _som('sacar_iai')''', '''            tv = estado.get('trevas')
            if tv is not None:
                tv.cortar(cy)
            ax_i, _ = kk.ancora()
            ag.depois(0.06, lambda: _quadro_impacto(camada, kk, (ax_i, cy)))
            _som('sacar_iai')''')
troca('''                        _som('titulo')
                        _tremer(28)
                        k.impacto(forte=True)
                        k.pausar(0.12)''', '''                        _som('titulo')
                        _tremer(28)
                        k.impacto(forte=True)
                        k.pausar(0.14)
                        _quadro_impacto(cam, k, (gcx, gcy))''')
open(p, 'w', encoding='utf-8').write(c)
print('ok')
