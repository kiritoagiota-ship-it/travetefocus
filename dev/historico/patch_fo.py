pc = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(pc, encoding='utf-8').read()


def troca(a, b, n=1):
    global c
    assert c.count(a) == n, (a[:90], c.count(a))
    c = c.replace(a, b)


# posicionar: pode fixar o fim no chao (a altura do comeco se ajusta)
troca("""    def posicionar(chave, i, arma, corta, desl, bojo, esp, pal='katana', y_ini=None,
                       extra=None):""", """    def posicionar(chave, i, arma, corta, desl, bojo, esp, pal='katana', y_ini=None,
                       extra=None, y_fim=None):""")
troca("""            no golpe (em alturas de letra; x para a frente). y_ini: comeca
            no chao (a altura do pulo e que se ajusta). extra = (chave,""", """            no golpe (em alturas de letra; x para a frente). y_ini: comeca
            no chao (a altura do pulo e que se ajusta); y_fim: termina no
            chao (a altura de onde ele desce e que se ajusta). extra = (chave,""")
troca("""            a0 = (0.0, 0.0 if y_ini is None else y_ini)
            for _ in range(8):
                a1 = (a0[0] + dx, a0[1] + dy)
                mx, my = arco_do_golpe(arma, corta, a0, a1, 1, bojo, esp).ponto(0.5, -0.4 * esp)
                if y_ini is None:
                    a0 = (a0[0] + cx - mx, a0[1] + cy - my)
                    continue
                a0 = (a0[0] + cx - mx, y_ini)
                dy += (cy - my) * 1.6""", """            a0 = (0.0, y_ini if y_ini is not None else (y_fim - dy if y_fim is not None else 0.0))
            for _ in range(8):
                a1 = (a0[0] + dx, a0[1] + dy)
                mx, my = arco_do_golpe(arma, corta, a0, a1, 1, bojo, esp).ponto(0.5, -0.4 * esp)
                if y_ini is not None:
                    a0 = (a0[0] + cx - mx, y_ini)
                    dy += (cy - my) * 1.6
                elif y_fim is not None:
                    dy -= (cy - my) * 1.6
                    a0 = (a0[0] + cx - mx, y_fim - dy)
                else:
                    a0 = (a0[0] + cx - mx, a0[1] + cy - my)""")
# sem o rastro antigo desenhado no boneco: quem faz o rastro agora e a luz do corte
troca("""        def impacto_silaba(i, cor, forte=False):""", """        def sem_rastro(chaves):
            return [(ch[0], _com(ch[1], s1=None, s2=None)) + tuple(ch[2:]) for ch in chaves]

        def impacto_silaba(i, cor, forte=False):""")
for nome in ('_tra', '_ve_sobe', '_te', '_fo'):
    pass
c = c.replace("kk.tocar(K.sequencia(chaves), on_quadro=_q", "kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q")
# FO: X de cima para baixo (as duas no alto cruzadas, descem abrindo)
troca("""        arma_fo = _com(P['c3_arma'], olhos='s')
        corta_fo = _com(P['c3_corta'], olhos='g')""", """        arma_fo = K.encolhido(_com(P['c3_corta'], olhos='s'))      # as duas no alto, cruzadas
        corta_fo = _com(P['c3_arma'], olhos='g')                    # descem abrindo em X
        prep_fo = _com(P['agacha'], olhos='s', m1=(3, 2), a1=150.0, m2=(-3, 3), a2=60.0)""")
troca("""        D0, D1 = posicionar('fo', 3, arma_fo, corta_fo, (0.2, 0.9), 0.14, th * 0.9, y_ini=y_chao,
                            extra=('fo2', 2, 0.14, th * 0.85, 'azul'))""", """        Dm, D1 = posicionar('fo', 3, arma_fo, corta_fo, (0.6, -1.0), 0.14, th * 0.9, y_fim=y_chao,
                            extra=('fo2', 2, 0.14, th * 0.85, 'azul'))
        D0 = quadro(Dm[0] + th * 0.9 * (-1 if kk.espelhar else 1), y_chao, [prep_fo])""")
troca("""        kk.precarregar([pronto, agacha, corta_tra, arma_ve, corta_ve, fim_ve, pega_az, saca_az,
                        arma_te, corta_te, arma_fo, corta_fo])""", """        kk.precarregar([pronto, agacha, corta_tra, arma_ve, corta_ve, fim_ve, pega_az, saca_az,
                        arma_te, corta_te, arma_fo, corta_fo, prep_fo])""")
troca("""            kk.tocar(_voo_seq(K.esticado(p_pulo), K.encolhido(p_pulo), K.esticado(arma_fo), 0.32))""",
      """            kk.tocar(_voo_seq(K.esticado(p_pulo), K.encolhido(p_pulo), K.esticado(prep_fo), 0.32))""")
troca("""                baixo = _com(arma_fo, dy=arma_fo['dy'] - 2)       # amortece a queda
                kk.tocar(K.sequencia([(2, baixo, 'out'), (2, arma_fo, 'out'), (1, arma_fo)]), on_fim=_fo)""",
      """                baixo = _com(prep_fo, dy=prep_fo['dy'] - 1)       # amortece a queda
                kk.tocar(K.sequencia([(2, baixo, 'out'), (2, prep_fo, 'out'), (1, prep_fo)]), on_fim=_fo)""")
a = c.index("        def _fo():")
b = c.index("        # ── 6. golpe final (estilo Bleach)")
c = c[:a] + """        def _fo():
            # FO: salta cruzando as duas laminas no alto...
            kk.tocar(_voo_seq(K.esticado(prep_fo), arma_fo, arma_fo, 0.2))
            _som('pulo')
            kk.empurrar(capa=-10, lift=10)
            _mover(kk, kk.ancora(), Dm, 0.2, ease='out', fantasmas=2, limite=(area, m), on_fim=_fo_x)

        def _fo_x():
            # ... e desce abrindo as duas em X: as duas luzes se cruzam na silaba
            chaves, i_r = K.golpe(arma_fo, corta_fo, n_arma=1, prende=1, segue=2, volta=3)

            def _q(i):
                if i == i_r - 2:
                    _som('voz_seiya')
                    kk.empurrar(capa=10, cabelo=8, lift=6)
                    _mover(kk, kk.ancora(), D1, 0.16, ease='in', fantasmas=3, limite=(area, m),
                           on_fim=lambda: poeira(D1[0], D1[1] - kk.extensao()[1], n=8))
                    cortar('fo', 3, dur=0.13, on_meio=lambda: impacto_silaba(3, CIANO, forte=True))
                    ag.depois(0.03, lambda: cortar('fo2', 3, dur=0.13, som='corte2'))
            kk.tocar(K.sequencia(sem_rastro(chaves)), on_quadro=_q, on_fim=_final)

""" + c[b:]
open(pc, 'w', encoding='utf-8', newline='\n').write(c)
print(c.count('sem_rastro(chaves)'))
