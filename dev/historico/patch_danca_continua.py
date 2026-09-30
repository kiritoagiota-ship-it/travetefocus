"""Danca da abertura CONTINUA (pedido de 29/09/2026): golpes com antecipacao,
4 quadros de giro da lamina (rastro), acompanhamento e volta; deslocamentos
mais lentos (o corpo anda no maximo ~15-20 px por quadro); desenhos do meio
a cada quadro (EM_DOIS = 1 no kirito.py)."""
import os
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'cenas.py')
c = open(A, encoding='utf-8').read()


def troca(a, b, n=1):
    global c
    assert c.count(a) == n, (a[:70], c.count(a))
    c = c.replace(a, b)


# jeito dos golpes da danca
troca("""        def _voo_seq(p_ini, p_ar, p_fim, dur):""",
      """        # golpes da danca: prepara, segura, a lamina gira em 4 quadros de
        # rastro, acompanha e volta com molinha (antes eram 2-3 quadros)
        G = dict(n_arma=3, prende=3, segue=3, volta=5, meios=(0.25, 0.5, 0.75))
        GIRO = len(G['meios'])                   # o corpo e a luz saem no 1o quadro de rastro

        def _voo_seq(p_ini, p_ar, p_fim, dur):""")
# entrada: mergulho um pouco mais longo
troca("""            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), K.esticado(p_pulo), 0.5))
            _som('pulo')
            kk.empurrar(capa=-8, cabelo=-6, lift=10)
            _mover(kk, ini, A0, 0.5, rot=(0, 360), fantasmas=4, ease='in', on_fim=_pousa,""",
      """            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), K.esticado(p_pulo), 0.7))
            _som('pulo')
            kk.empurrar(capa=-8, cabelo=-6, lift=10)
            _mover(kk, ini, A0, 0.7, rot=(0, 360), fantasmas=4, ease='in', on_fim=_pousa,""")
# TRA
troca("""            chaves, i_r = K.golpe(pronto, corta_tra, n_arma=1, prende=2, segue=3, volta=4,
                                  lamina_recua=False, seg=P['segue1'])

            def _q(i):
                if i == i_r - 2:
                    _som('sacar_iai')
                    _gemido()
                    _mover(kk, kk.ancora(), A1, 0.14, ease='out', fantasmas=3, limite=(area, m))
                    cortar('tra', 0, dur=0.13, on_meio=lambda: impacto_silaba(0, CIANO))""",
      """            chaves, i_r = K.golpe(pronto, corta_tra, lamina_recua=False, seg=P['segue1'], **G)

            def _q(i):
                if i == i_r - GIRO:
                    _som('sacar_iai')
                    _gemido()
                    _mover(kk, kk.ancora(), A1, 0.26, ease='out', fantasmas=3, limite=(area, m))
                    cortar('tra', 0, dur=0.18, on_meio=lambda: impacto_silaba(0, CIANO))""")
# VE: recua deslizando
troca("""            seq = K.sequencia(_de_agora(kk, 2, proxima=arma_ve) + [(3, arma_ve, 'out'), (1, arma_ve)])
            kk.tocar(seq)
            _som('desliza')
            kk.empurrar(capa=-10, cabelo=-6)
            _mover(kk, kk.ancora(), B0, 0.17, ease='out', fantasmas=2, limite=(area, m),
                   on_fim=_ve_sobe)""",
      """            seq = K.sequencia(_de_agora(kk, 3, proxima=arma_ve) + [(5, arma_ve, 'out'), (1, arma_ve)])
            kk.tocar(seq)
            _som('desliza')
            kk.empurrar(capa=-10, cabelo=-6)
            _mover(kk, kk.ancora(), B0, 0.3, ease='out', fantasmas=2, limite=(area, m),
                   on_fim=_ve_sobe)""")
troca("""            chaves, i_r = K.golpe(arma_ve, corta_ve, n_arma=1, prende=1, segue=2, volta=3, seg=fim_ve)

            def _q(i):
                if i == i_r - 2:
                    _som('pulo')
                    _gemido()
                    kk.empurrar(capa=-10, lift=10)
                    _mover(kk, kk.ancora(), B1, 0.17, ease='out', fantasmas=3, limite=(area, m))
                    cortar('ve', 1, dur=0.14, on_meio=lambda: impacto_silaba(1, CIANO))""",
      """            chaves, i_r = K.golpe(arma_ve, corta_ve, seg=fim_ve, **dict(G, n_arma=2, prende=2, volta=4))

            def _q(i):
                if i == i_r - GIRO:
                    _som('pulo')
                    _gemido()
                    kk.empurrar(capa=-10, lift=10)
                    _mover(kk, kk.ancora(), B1, 0.28, ease='out', fantasmas=3, limite=(area, m))
                    cortar('ve', 1, dur=0.18, on_meio=lambda: impacto_silaba(1, CIANO))""")
# TE
troca("""            chaves, i_r = K.golpe(arma_te, corta_te, n_arma=1, prende=1, segue=2, volta=2, seg=corta_te)

            def _q(i):
                if i == i_r - 2:
                    _gemido(forte=True)
                    kk.empurrar(capa=12, lift=6)
                    _mover(kk, kk.ancora(), C1, 0.15, ease='in', fantasmas=3, limite=(area, m))
                    cortar('te', 2, dur=0.13, on_meio=lambda: impacto_silaba(2, CIANO, forte=True))
                    ag.depois(0.04, lambda: cortar('te2', 2, dur=0.13, som='corte2'))""",
      """            chaves, i_r = K.golpe(arma_te, corta_te, seg=corta_te, **dict(G, n_arma=2, prende=2, volta=3))

            def _q(i):
                if i == i_r - GIRO:
                    _gemido(forte=True)
                    kk.empurrar(capa=12, lift=6)
                    _mover(kk, kk.ancora(), C1, 0.26, ease='in', fantasmas=3, limite=(area, m))
                    cortar('te', 2, dur=0.18, on_meio=lambda: impacto_silaba(2, CIANO, forte=True))
                    ag.depois(0.05, lambda: cortar('te2', 2, dur=0.18, som='corte2'))""")
# TE volta (mortal para tras)
troca("""            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), K.esticado(prep_fo), 0.32))""",
      """            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), K.esticado(prep_fo), 0.48))""")
troca("""            _mover(kk, (ax, ay), D0, 0.32, altura=h, rot=(0, -360), fantasmas=2, limite=(area, m),
                   on_fim=_chegou, rot_janela=(0.2, 0.75))""",
      """            _mover(kk, (ax, ay), D0, 0.48, altura=h, rot=(0, -360), fantasmas=2, limite=(area, m),
                   on_fim=_chegou, rot_janela=(0.2, 0.75))""")
# FO
troca("""            kk.tocar(_voo_seq(K.esticado(prep_fo), arma_fo, arma_fo, 0.2))
            _som('pulo')
            kk.empurrar(capa=-10, lift=10)
            _mover(kk, kk.ancora(), Dm, 0.2, ease='out', fantasmas=2, limite=(area, m), on_fim=_fo_x)""",
      """            kk.tocar(_voo_seq(K.esticado(prep_fo), arma_fo, arma_fo, 0.3))
            _som('pulo')
            kk.empurrar(capa=-10, lift=10)
            _mover(kk, kk.ancora(), Dm, 0.3, ease='out', fantasmas=2, limite=(area, m), on_fim=_fo_x)""")
troca("""            chaves, i_r = K.golpe(arma_fo, corta_fo, n_arma=1, prende=1, segue=2, volta=3)

            def _q(i):
                if i == i_r - 2:
                    _som('fala_kurae')
                    kk.empurrar(capa=10, cabelo=8, lift=6)
                    _mover(kk, kk.ancora(), D1, 0.16, ease='in', fantasmas=3, limite=(area, m),
                           on_fim=lambda: poeira(D1[0], D1[1] - kk.extensao()[1], n=8))
                    cortar('fo', 3, dur=0.13, on_meio=lambda: impacto_silaba(3, CIANO, forte=True))
                    ag.depois(0.03, lambda: cortar('fo2', 3, dur=0.13, som='corte2'))""",
      """            chaves, i_r = K.golpe(arma_fo, corta_fo, **dict(G, n_arma=2, prende=2, volta=4))

            def _q(i):
                if i == i_r - GIRO:
                    _som('fala_kurae')
                    kk.empurrar(capa=10, cabelo=8, lift=6)
                    _mover(kk, kk.ancora(), D1, 0.26, ease='in', fantasmas=3, limite=(area, m),
                           on_fim=lambda: poeira(D1[0], D1[1] - kk.extensao()[1], n=8))
                    cortar('fo', 3, dur=0.18, on_meio=lambda: impacto_silaba(3, CIANO, forte=True))
                    ag.depois(0.04, lambda: cortar('fo2', 3, dur=0.18, som='corte2'))""")
open(A, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
