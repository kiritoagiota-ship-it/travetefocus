"""Yoru comico (anime chibi) fora do apagar: emotes, pulinhos, moeda na cabeca."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p import patch
T = os.path.dirname(os.path.abspath(__file__))
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'cenas.py')
emotes = open(os.path.join(T, 'emotes.txt'), encoding='utf-8').read()

ajudantes = '''def _pulinhos(k, pose, n=2, altura=None, dur=0.2, on_fim=None):
    """Pulinhos de alegria no lugar (chibi): no alto encolhe as pernas."""
    altura = altura or k.ps * 3
    base = k.ancora()
    no_ar = K.encolhido(pose)
    fim = _Uma(on_fim)
    cont = [0]

    def _um():
        if cont[0] >= n or k.parent is None:
            k.mostrar(pose)
            fim()
            return
        cont[0] += 1
        k.mostrar(no_ar)
        k.empurrar(lift=4, cabelo=3)
        _mover(k, base, base, dur, altura=altura, fantasmas=0,
               on_fim=lambda: (k.mostrar(pose), Clock.schedule_once(lambda dt: _um(), 0.05)))
    _um()


def _moeda_na_cabeca(camada, k, te, on_bate=None):
    """Uma moeda de luz cai do alto e bate na cabeca dele (tonc!)."""
    x, y_fim = _topo_cabeca(k)
    y_ini = y_fim + te * 40
    x = math.floor(x / te) * te
    moeda = ["..YYY..", ".YyYyY.", "YYyYyYY", "YYyYyYY", ".YyYyY.", "..YYY.."]
    bateu = _Uma(on_bate)
    dur = 0.28

    def forma(t, p, u):
        k_ = min(1.0, t / dur)
        if k_ >= 1:
            bateu()
            yy = y_fim + te * 6 * max(0.0, 1 - (t - dur) / 0.25)     # quica e some
            if t > dur + 0.25:
                return
        else:
            yy = y_ini + (y_fim - y_ini) * k_ * k_
        gy = math.floor(yy / u) * u
        for r, linha in enumerate(moeda):
            for c, ch in enumerate(linha):
                if ch != '.':
                    nome = 'luz' if ch == 'y' else 'cor'
                    p.setdefault(nome, []).append((x + (c - 3) * u, gy + (5 - r) * u, u, u))
    camada.add_widget(_EfeitoPixel(_cores_efeito((1.0, 0.8, 0.2)), dur + 0.3, forma))


'''

patch(A, [
    # emotes e ajudantes antes das cenas curtas
    ("class _Mini:\n", emotes + ajudantes + "class _Mini:\n"),

    # ── +XP: olhos brilhando, carimba e pulinhos com nota ────────────────
    ("""        def _corta():
            seq = K.sequencia([(2, arma, 'segura'), (1, K.smear(corta, arma['a1']), 'segura'),
                               (4, corta, 'segura'), (4, volta, 'out'), (1, volta)])
""", """        def _ve():
            # ve o lote novo: !! e olhos brilhando
            k.mostrar(_com(arma, olhos='e'))
            emote(s.cam, k, '!!', 0.5)
            emote(s.cam, k, 'brilho', 0.5)
            Clock.schedule_once(lambda dt: _corta(), 0.38)

        def _festa():
            feliz = _com(P['guarda'], olhos='e')
            emote(s.cam, k, 'nota', 0.9)
            _pulinhos(k, feliz, n=2, altura=s.ps * 3,
                      on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.1))

        def _corta():
            seq = K.sequencia([(2, arma, 'segura'), (1, K.smear(corta, arma['a1']), 'segura'),
                               (4, corta, 'segura'), (4, volta, 'out'), (1, volta)])
"""),
    ("""                    _som('corte')
                    k.impacto()
                    feito()
            k.tocar(seq, on_quadro=_q, on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.1))

        _entrar(s, _corta)""", """                    _som('corte')
                    _gemido()
                    k.impacto()
                    feito()
            k.tocar(seq, on_quadro=_q, on_fim=_festa)

        _entrar(s, _ve)"""),

    # ── FINALIZAR: ufa (gota), !! e pulinhos de vitoria corado ───────────
    ("""        def _cerimonia():
            vit = P['vitoria']
            seq = K.sequencia([(4, guarda, 'segura'), (3, passos[0], 'out'), (3, passos[1], 'segura'),
                               (6, passos[2], 'in'), (2, passos[3], 'out'), (3, passos[4], 'mola'),
                               (4, vit, 'out'), (10, vit, 'segura'), (8, _com(vit, emote='brilho'), 'segura'),
                               (1, vit)])

            def _q(q):
                if q == 7:
                    hx, hy = k.ponto_mao(1)
                    s.faiscas.estourar(hx, hy, BRANCO, n=6, forca=dp(90), tam=s.ps * 0.6, gravidade=dp(300))
                    _som('desliza')
                elif q == 18:
                    _som('embainhar')
                    ax, ay = k.ancora()
                    _anel(s.cam, (ax, ay), s.ps * 2, s.ps * 12, 0.35, CIANO, esp=dp(2))
                elif q == 30:
                    _som('habilidade')
            k.tocar(seq, on_quadro=_q, on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.2))

        _entrar(s, _cerimonia)""", """        def _cerimonia():
            # ufa! fim do turno: olhos fechados, gota de suor escorrendo
            k.mostrar(_com(P['guardado'], olhos='f'))
            emote(s.cam, k, 'gota', 0.85)
            Clock.schedule_once(lambda dt: _comemora(), 0.8)

        def _comemora():
            # ... e cai a ficha: !!, olhos brilhando, corado, pulinhos
            feliz = _com(P['vitoria'], olhos='e')
            emote(s.cam, k, '!!', 0.45)
            emote(s.cam, k, 'brilho', 1.2, atraso=0.08)
            emote(s.cam, k, 'rubor', 1.4, atraso=0.08)
            _som('habilidade')
            ax, ay = k.ancora()
            _anel(s.cam, (ax, ay), s.ps * 2, s.ps * 12, 0.35, CIANO, esp=dp(2))
            s.faiscas.estourar(ax, ay + s.ps * 10, OURO, n=10, forca=dp(120), tam=s.te * 2, gravidade=dp(260))
            _pulinhos(k, feliz, n=3, altura=s.ps * 4, on_fim=_convencido)

        def _convencido():
            k.mostrar(_com(P['vitoria'], olhos='v'))
            emote(s.cam, k, 'nota', 0.8)
            Clock.schedule_once(lambda dt: s.sair(), 0.75)

        _entrar(s, _cerimonia)"""),

    # ── WHATSAPP: joga forte demais - susto e gota ───────────────────────
    ("""            seq = K.sequencia([(5, arma, 'segura'), (2, joga, 'out'), (8, joga, 'segura'),
                               (4, _com(P['guardado'], olhos='v'), 'out'), (1, _com(P['guardado'], olhos='v'))])

            def _q(q):
                if q == 6:
                    W, H = Window.size
                    rolo.soltar((W + s.te * 20, H + s.te * 10), 0.5)
                    _som('papel')""", """            seq = K.sequencia([(5, arma, 'segura'), (2, joga, 'out'), (12, _com(joga, olhos='u'), 'segura'),
                               (4, _com(P['guardado'], olhos='v'), 'out'), (1, _com(P['guardado'], olhos='v'))])

            def _q(q):
                if q == 6:
                    W, H = Window.size
                    rolo.soltar((W + s.te * 20, H + s.te * 10), 0.5)
                    _som('papel')
                    _gemido()
                elif q == 9:
                    emote(s.cam, k, 'gota', 0.8)         # jogou forte demais...
                elif q == 19:
                    emote(s.cam, k, 'nota', 0.7)"""),

    # ── NIVEL: olhos brilhando, corado e pulinhos ────────────────────────
    ("""            seq = K.sequencia([(3, _com(P['agacha'], olhos='s'), 'in'), (4, ergue, 'out'), (14, ergue, 'segura'),
                               (4, vit, 'out'), (10, _com(vit, emote='brilho'), 'segura'), (1, vit)])
""", """            seq = K.sequencia([(3, _com(P['agacha'], olhos='s'), 'in'), (4, ergue, 'out'), (14, ergue, 'segura'),
                               (4, _com(vit, olhos='e'), 'out'), (1, _com(vit, olhos='e'))])

            def _festa():
                emote(s.cam, k, 'brilho', 1.0)
                emote(s.cam, k, 'rubor', 1.1)
                emote(s.cam, k, 'nota', 0.9, atraso=0.2)
                _pulinhos(k, _com(vit, olhos='e'), n=2, altura=s.ps * 4,
                          on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.25))
"""),
    ("""                    _som('habilidade')
                    k.empurrar(capa=-10, cabelo=-10, lift=4)
            k.tocar(seq, on_quadro=_q, on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.2))
        _entrar(s, _comemora, tipos=('teleporte', 'queda', 'sombra'))""", """                    _som('habilidade')
                    emote(s.cam, k, '!!', 0.5)
                    k.empurrar(capa=-10, cabelo=-10, lift=4)
            k.tocar(seq, on_quadro=_q, on_fim=_festa)
        _entrar(s, _comemora, tipos=('teleporte', 'queda', 'sombra'))"""),
    ("""        k.precarregar([ergue, vit, _com(vit, emote='brilho')])
""", """        k.precarregar([ergue, _com(vit, olhos='e'), K.encolhido(_com(vit, olhos='e'))])
"""),

    # ── META: gira, chove moeda... e uma cai na cabeca dele ─────────────
    ("""            seq = K.sequencia([(2, g1, 'segura'), (8, g1, 'segura'), (5, g1, 'mola'), (4, vit, 'out'),
                               (12, _com(vit, emote='brilho'), 'segura'), (1, vit)])""",
     """            seq = K.sequencia([(2, g1, 'segura'), (8, g1, 'segura'), (5, g1, 'mola'),
                               (4, _com(vit, olhos='e'), 'out'), (1, _com(vit, olhos='e'))])"""),
    ("""                    Clock.schedule_once(_chuva, 0.5)
            k.tocar(seq, on_quadro=_q, on_fim=lambda: Clock.schedule_once(lambda dt: s.sair(), 0.3))""",
     """                    Clock.schedule_once(_chuva, 0.5)
                elif q == 15:
                    emote(s.cam, k, 'brilho', 0.8)

            def _tonc():
                # uma moeda cai na cabeca dele: susto, ? e gota... e ri
                _som('moedas')
                k.mostrar(_com(vit, olhos='u'))
                k.empurrar(cabelo=10, lift=-6)
                emote(s.cam, k, '?', 0.7)
                emote(s.cam, k, 'gota', 0.9)
                Clock.schedule_once(lambda dt: (k.mostrar(_com(vit, olhos='e')),
                                                emote(s.cam, k, 'nota', 0.7)), 0.7)
                Clock.schedule_once(lambda dt: s.sair(), 1.35)
            k.tocar(seq, on_quadro=_q,
                    on_fim=lambda: _moeda_na_cabeca(s.cam, k, s.te, on_bate=_tonc))"""),
    ("""        k.precarregar([g1, P['giro_2'], P['giro_3'], vit, _com(vit, emote='brilho')])""",
     """        k.precarregar([g1, P['giro_2'], P['giro_3'], _com(vit, olhos='e'), _com(vit, olhos='u')])"""),

    # ── SENHA: emotes novos (os antigos saiam em blocos grossos) ─────────
    ("""            self.k.tocar(K.sequencia([(1, _com(P['espia'], olhos='u', dy=0, m1=(3, 4), m2=(-3, 4)), 'out'),
                                      (4, _com(P['espia_alto'], olhos='u', emote='!'), 'segura'),
                                      (1, _com(P['espia_alto'], olhos='u', emote='!')),
                                      (1, _com(P['espia_baixo'], olhos='u'))]))""",
     """            self.k.tocar(K.sequencia([(1, _com(P['espia'], olhos='u', dy=0, m1=(3, 4), m2=(-3, 4)), 'out'),
                                      (4, _com(P['espia_alto'], olhos='u'), 'segura'),
                                      (1, _com(P['espia_alto'], olhos='u')),
                                      (1, _com(P['espia_baixo'], olhos='u'))]))
            emote(self.clip, self.k, '!!', 0.45)"""),
    ("""                seq = K.sequencia([(14, _com(P['espia_baixo'], olhos='s'), 'in'),
                                   (22, _com(P['espia_olha'], olhos='s', emote='gota')),
                                   (1, _com(P['espia_olha'], olhos='s', emote='gota'))])
                self.k.tocar(seq, on_fim=self._esperar)""",
     """                seq = K.sequencia([(14, _com(P['espia_baixo'], olhos='s'), 'in'),
                                   (22, _com(P['espia_olha'], olhos='s')),
                                   (1, _com(P['espia_olha'], olhos='s'))])
                self.k.tocar(seq, on_fim=self._esperar)
                emote(self.clip, self.k, 'gota', 1.3, atraso=0.45)"""),
    ("""            base = _com(P['espia_olha'], olhos='f', emote='gota')""",
     """            base = _com(P['espia_olha'], olhos='f')
            emote(self.clip, self.k, 'gota', 1.5)"""),
    ("""                self.k.mostrar(_com(P['espia_baixo'], olhos='f', emote='...'))""",
     """                self.k.mostrar(_com(P['espia_baixo'], olhos='f'))"""),
    ("""                k.tocar(K.sequencia([(3, _com(P['espia_alto'], olhos='e', emote='brilho')),
                                     (4, _com(P['espia'], olhos='e', emote='brilho')),
                                     (1, _com(P['espia_alto'], olhos='e', emote='brilho'))]))""",
     """                k.tocar(K.sequencia([(3, _com(P['espia_alto'], olhos='e')),
                                     (4, _com(P['espia'], olhos='e')),
                                     (1, _com(P['espia_alto'], olhos='e'))]))
                emote(self.clip, k, 'brilho', 0.5)"""),
    ("""                feliz = _com(P['guardado'], olhos='e', emote='brilho')""",
     """                feliz = _com(P['guardado'], olhos='e')
                emote(self.clip, k, 'brilho', 0.9, atraso=0.15)
                emote(self.clip, k, 'rubor', 1.0, atraso=0.15)
                emote(self.clip, k, 'nota', 0.8, atraso=0.4)"""),

    # ── APAGAR: gemidinhos nos golpes ────────────────────────────────────
    ("""            k.mostrar(corte)
            _som('sacar_iai')
            linha = _reta_pixels(""", """            k.mostrar(corte)
            _som('sacar_iai')
            _gemido()
            linha = _reta_pixels("""),
    ("""            k.mostrar(crava)
            _som('pulo')
            _som('voz_teya')""", """            k.mostrar(crava)
            _som('pulo')
            _gemido()"""),
    ("""            _som('corte2')
            _som('corte')
            _som('voz_seiya')""", """            _som('corte2')
            _som('corte')
            _gemido()"""),
    ("""            _estrela(cam, ccx, ccy, ps)
            _som('corte')
            _tremer(8)""", """            _estrela(cam, ccx, ccy, ps)
            _som('corte')
            _gemido()
            _tremer(8)"""),
    ("""                           'desliza', 'embainhar', 'golpe_final', 'habilidade', 'voz_teya', 'voz_seiya',
                           'vidro', 'papel', 'giro', 'moedas', 'pouso'])""",
     """                           'desliza', 'embainhar', 'golpe_final', 'habilidade', 'vidro', 'papel', 'giro',
                           'moedas', 'pouso'] + _GEMIDOS)"""),
])
print('ok')
