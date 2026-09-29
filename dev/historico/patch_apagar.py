"""Golpes de apagar mais fluidos: preparacao, quadros de rastro, arco de
luz em pixel art (o mesmo da abertura) e acomodacao."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'cenas.py')

patch(A, [
    # _Mini: prepara e solta arcos de luz (mesmo corte da abertura)
    ("""    def no_quadro(self, x, y, poses):
        return _no_quadro(self.k, x, y, poses, self.area, dp(2))
""", """    def no_quadro(self, x, y, poses):
        return _no_quadro(self.k, x, y, poses, self.area, dp(2))

    def preparar_arco(self, chave, arco, pal='katana'):
        \"\"\"Desenha antes da hora a mancha do arco de luz de um golpe.\"\"\"
        if not hasattr(self, '_oficina'):
            self._oficina = OficinaCortes(self.te * max(1, int(round(2.4 / self.te))))
            self._arcos = {}
        self._arcos[chave] = arco
        self._oficina.pedir(chave, arco, pal)

    def soltar_arco(self, chave, dur=0.1, decai=0.2):
        \"\"\"O arco de luz corre pelo caminho da lamina (congela no hit-stop).\"\"\"
        try:
            mancha = self._oficina.obter(chave)
            if mancha is not None:
                self.cam.add_widget(CorteGravado(self._arcos[chave], mancha, dur=dur, decai=decai, k=self.k),
                                    index=len(self.cam.children))
        except Exception as e:
            print(f"[apagar] arco: {e}")
"""),

    # ── APAGAR LOTE (iai): preparacao, rastro, arco de luz atravessando ──
    ("""        k.ancorar(*ini)
        k.mostrar(pronto)
        k.precarregar([corte] + embainha)

        def _tensao():""", """        k.ancorar(*ini)
        k.mostrar(pronto)
        k.precarregar([corte] + embainha)
        corta1 = _com(P['corta1'], olhos='g')
        chaves, i_r = K.golpe(pronto, corta1, n_arma=1, prende=1, segue=2, volta=3,
                              lamina_recua=False, seg=corte)
        chaves = [(ch[0], _com(ch[1], s1=None, s2=None)) + tuple(ch[2:]) for ch in chaves]
        k.precarregar([c[1] for c in chaves])
        s.preparar_arco('iai', ArcoCorte.pelo_meio((s.cx, s.cy), 0 if esq else 180, s.rw + s.te * 18,
                                                   -0.08 if esq else 0.08, min(s.rh * 1.2, s.te * 26)))

        def _tensao():"""),
    ("""        def _saque():
            k.fantasma(cor=CIANO, alfa=0.7, duracao=0.3)
            k.mostrar(corte)
            _som('sacar_iai')
            _gemido()
            linha = _reta_pixels(s.rx - s.te * 2, s.cy, s.rx + s.rw + s.te * 2, s.cy, s.te)
            if not esq:
                linha.reverse()
            s.cam.add_widget(_PixelsLuz([linha], s.te, cresce=0.06, fica=0.5, some=0.2, grossura=1), index=0)
            _mover(k, k.ancora(), fim_p, 0.07, linear=True, fantasmas=4, on_fim=_parado)
            s.faiscas.estourar(s.cx, s.cy, CIANO, n=10, forca=dp(120), tam=s.ps * 0.8)
            _tremer(4)

        def _parado():
            k.impacto()
            k.pausar(0.08)
            Clock.schedule_once(lambda dt: _embainha(), 0.3)""", """        def _saque():
            # sai do cabo num estalo: prepara, os quadros de rastro e ele ja
            # passou - a luz da lamina atravessa o item
            def _q(i):
                if i == i_r - 2:
                    k.fantasma(cor=CIANO, alfa=0.6, duracao=0.3)
                    _som('sacar_iai')
                    _gemido()
                    s.soltar_arco('iai', dur=0.1, decai=0.28)
                    _mover(k, k.ancora(), fim_p, 0.1, ease='out', fantasmas=4)
                elif i == i_r:
                    k.impacto()
                    k.pausar(0.08)
                    s.faiscas.estourar(s.cx, s.cy, CIANO, n=12, forca=dp(140), tam=s.ps * 0.8)
                    _tremer(5)
            k.tocar(K.sequencia(chaves), on_quadro=_q,
                    on_fim=lambda: Clock.schedule_once(lambda dt: _embainha(), 0.18))"""),

    # ── APAGAR TURNO (estocada): recolhe o braco e crava com a luz reta ─
    ("""        k.ancorar(*ini)
        k.mostrar(arma)
        k.precarregar([crava, puxa, _com(P['pulo'], olhos='s')])

        def _mira():""", """        k.ancorar(*ini)
        k.mostrar(arma)
        recua = _com(arma, dx=arma['dx'] - 1, m1=(arma['m1'][0] - 2, arma['m1'][1]), incl=-1)
        k.precarregar([crava, puxa, recua, _com(P['pulo'], olhos='s')])
        tx0, ty0 = k.ponta_espada(1, arma)
        ang_e = math.degrees(math.atan2(s.cy - ty0, s.cx - tx0))
        s.preparar_arco('estocada', ArcoCorte.pelo_meio(((tx0 + s.cx) / 2.0, (ty0 + s.cy) / 2.0), ang_e,
                                                        math.hypot(s.cx - tx0, s.cy - ty0) + s.te * 10,
                                                        0.02, s.te * 9))

        def _mira():"""),
    ("""        def _lanca():
            k.mostrar(crava)
            _som('pulo')
            _gemido()
            _mover(k, k.ancora(), alvo_a, 0.1, linear=True, fantasmas=4, on_fim=_crava)""",
     """        def _lanca():
            # recolhe o braco (preparacao) e se lanca: a luz vai reta na frente
            def _vai():
                k.mostrar(K.smear(crava, arma['a1']))
                _som('pulo')
                _gemido()
                s.soltar_arco('estocada', dur=0.1, decai=0.22)
                _mover(k, k.ancora(), alvo_a, 0.1, linear=True, fantasmas=4,
                       on_fim=lambda: (k.mostrar(crava), _crava()))
            k.tocar(K.sequencia([(3, recua, 'in'), (1, recua)]), on_fim=_vai)"""),

    # ── APAGAR PERIODO (X): golpe com preparacao e duas luzes em X ──────
    ("""        k.ancorar(*ini)
        k.mostrar(arma)
        k.precarregar([corta])

        def _salta():""", """        k.ancorar(*ini)
        k.mostrar(arma)
        k.precarregar([corta])
        diag = math.hypot(s.rw, s.rh) + s.te * 14
        esp_x = min(s.rh * 0.9, s.te * 22)
        s.preparar_arco('x1', ArcoCorte.pelo_meio((s.cx, s.cy), -35 if esq else -145, diag, 0.1, esp_x))
        s.preparar_arco('x2', ArcoCorte.pelo_meio((s.cx, s.cy), 35 if esq else 145, diag, -0.1, esp_x * 0.85),
                        'azul')

        def _salta():"""),
    ("""        def _corta():
            seq = K.sequencia([(1, K.smear(corta, arma['a1'], arma['a2']), 'segura'), (5, corta, 'segura'),
                               (4, _com(P['dupla'], olhos='s'), 'out'), (1, _com(P['dupla'], olhos='s'))])
            k.tocar(seq)
            k.impacto()
            k.pausar(0.08)
            _som('corte2')
            _som('corte')
            _gemido()
            _tremer(9)
            m = s.te * 2
            d1 = _reta_pixels(s.rx - m, s.ry + s.rh + m, s.rx + s.rw + m, s.ry - m, s.te)
            d2 = _reta_pixels(s.rx + s.rw + m, s.ry + s.rh + m, s.rx - m, s.ry - m, s.te)
            s.cam.add_widget(_PixelsLuz([d1, d2], s.te, cresce=0.08, fica=0.35, some=0.15, grossura=2), index=0)
            _estrela(s.cam, s.cx, s.cy, s.ps, CIANO, raios=4, dur=0.16)""",
     """        def _corta():
            meio = K.smear(K.misturar(arma, corta, 0.5, 0.5), arma['a1'], arma['a2'])
            seq = K.sequencia([(1, meio, 'segura'), (1, K.smear(corta, arma['a1'], arma['a2']), 'segura'),
                               (4, corta, 'segura'), (4, _com(P['dupla'], olhos='s'), 'out'),
                               (1, _com(P['dupla'], olhos='s'))])
            k.tocar(seq)
            k.impacto()
            k.pausar(0.08)
            _som('corte2')
            _som('corte')
            _gemido()
            _tremer(9)
            s.soltar_arco('x1', dur=0.1, decai=0.26)
            Clock.schedule_once(lambda dt: s.soltar_arco('x2', dur=0.1, decai=0.26), 0.04)
            _estrela(s.cam, s.cx, s.cy, s.ps, CIANO, raios=4, dur=0.16)"""),
])
print('ok')
