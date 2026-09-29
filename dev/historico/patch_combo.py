p = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(p, encoding='utf-8').read()
a = c.index('        def _combo(i):')
b = c.index('        # ── 6. golpe final')
novo = '''        def _atras_da_silaba(i):
            i0, i1 = _TRECHOS[i]
            cx, cy = titulo.x_do_trecho(i0, i1)
            larg = max(titulo._larg[i1] - titulo._larg[i0], th)
            return i0, i1, cx, cy, larg

        def _ataque_giro(on_fim):
            # VE: GIRO DE 360 - as duas laminas abertas na horizontal, ele gira
            # duas vezes na frente da silaba e um anel de luz corta tudo em volta
            i0, i1, cx, cy, larg = _atras_da_silaba(1)
            kk.espelhar = False
            g1 = _com(P['giro_1'], olhos='s')
            g2, g3 = P['giro_2'], P['giro_3']
            abaixa = _com(g1, dy=-1, pernas='dobra')
            alvo = quadro(cx - th * 0.05, cy - th * 0.15, [abaixa, g1, g2, g3])

            def _gira():
                kk.rotacao = 0
                seq = K.sequencia([(3, abaixa, 'segura'), (2, g2, 'linear'), (2, g3, 'linear'),
                                   (2, g1, 'linear'), (2, g2, 'linear'), (2, g3, 'linear'),
                                   (6, g1, 'mola'), (1, g1)])

                def _q(q):
                    if q in (3, 9):                    # uma volta de luz a cada giro
                        ax, ay = kk.ancora()
                        for cor, rr, d in ((CIANO, 1.0, 0), (AZUL, 0.82, 180)):
                            camada.add_widget(CorteMeiaLua(
                                centro=(ax, cy), raio=larg * 0.9 * rr, ang_ini=d, ang_fim=d + 360,
                                espessura=th * 0.55, achat=0.3, cor=cor, dur_cheio=5 / 30.0,
                                dur_decai=6 / 30.0))
                        _som('corte2' if q == 3 else 'corte')
                        kk.empurrar(capa=18, cabelo=12)
                        for j in range(8):
                            ang = j * math.pi / 4
                            faiscas.estourar(ax + math.cos(ang) * larg * 0.9, cy + math.sin(ang) * larg * 0.27,
                                             random.choice((CIANO, AZUL, BRANCO)), n=2,
                                             forca=dp(120), tam=ps)
                        if q == 3:
                            titulo.revelar(i0, i1, cor=(1, 1, 1))
                            _estrela(camada, cx, cy, ps, CIANO)
                            _tremer(6)
                            kk.impacto()
                            kk.pausar(0.05)
                kk.tocar(seq, on_quadro=_q, on_fim=on_fim)
            _blitz_para(alvo, g1, _gira)

        def _ataque_mergulho(on_fim):
            # TE: MERGULHO DO ALTO - aparece bem acima da silaba com a lamina
            # erguida, fica um instante no ar e desce de ponta: crava nas
            # letras, uma onda de choque corre pela linha e sobe entulho
            i0, i1, cx, cy, larg = _atras_da_silaba(2)
            kk.espelhar = False
            sobe = _com(P['mergulho_sobe'], olhos='s')
            desce = _com(P['mergulho'], olhos='g')
            crava = _com(P['mergulho_fim'], olhos='s')
            # onde a ancora fica para a ponta da lamina cravar no meio da silaba
            ax0, ay0 = kk.ancora()
            tx, ty = kk.ponta_espada(1, crava)
            dxp, dyp = tx - ax0, ty - ay0
            impacto = (cx - dxp, cy - dyp)
            alto = quadro(impacto[0], impacto[1] + th * 2.4, [sobe, desce])

            def _cai():
                kk.mostrar(desce)
                _som('pulo')
                _mover(kk, kk.ancora(), impacto, 0.12, ease='in', fantasmas=3, on_fim=_crava)

            def _crava():
                kk.tocar(K.sequencia([(1, crava, 'segura'), (8, crava, 'segura'), (4, _com(P['guarda'], olhos='s'), 'out'),
                                      (1, _com(P['guarda'], olhos='s'))]), on_fim=on_fim)
                titulo.revelar(i0, i1, cor=(1, 1, 1))
                _anel(camada, (cx, cy), ps * 2, larg * 1.5, 0.45, CIANO, esp=dp(4), achat=0.25)
                _anel(camada, (cx, cy), ps, larg * 0.9, 0.35, BRANCO, esp=dp(3), achat=0.25)
                _estrela(camada, cx, cy, ps, BRANCO)
                faiscas.estourar(cx, cy + th * 0.3, POEIRA, n=14, forca=dp(160), tam=ps, gravidade=dp(420))
                faiscas.estourar(cx, cy, CIANO, n=12, forca=dp(200), tam=ps)
                _som('golpe_final')
                _tremer(12)
                _brilho_tela(camada, 0.12, 0.14)
                kk.impacto()
                kk.pausar(0.09)
                kk.empurrar(capa=-14, cabelo=-10)

            def _no_alto():
                kk.mostrar(sobe)
                kk.empurrar(capa=10, cabelo=8)
                ag.depois(0.14, _cai)                  # um instante parado no ar
            _blitz_para(alto, sobe, _no_alto)

        def _ataque_salto(on_fim):
            # FO: GOLPE SUBINDO COM SALTO - agachado embaixo da silaba com a
            # lamina baixa para tras, corta subindo e o corpo sobe junto,
            # atravessando as letras de baixo para cima
            i0, i1, cx, cy, larg = _atras_da_silaba(3)
            kk.espelhar = False
            arma = _com(P['salto_arma'], olhos='s')
            corta = _com(P['salto'], olhos='g')
            fim_p = _com(P['salto_fim'], olhos='s')
            cima_p = _ext(kk, [arma])[3]
            baixo_alvo = quadro(cx - th * 0.45, oy_t - dp(4) - cima_p, [arma])

            def _sobe():
                kk.rotacao = 0
                seq = K.sequencia([(3, arma, 'segura'), (1, K.smear(corta, arma['a1']), 'segura'),
                                   (2, corta, 'out'), (6, fim_p, 'out'), (1, fim_p)])

                def _q(q):
                    if q == 3:
                        camada.add_widget(CorteMeiaLua(centro=(cx, cy), raio=larg * 0.95, ang_ini=250,
                                                       ang_fim=70, espessura=th * 0.9, achat=0.55, cor=CIANO))
                        titulo.revelar(i0, i1, cor=(1, 1, 1))
                        faiscas.estourar(cx, cy, CIANO, n=16, forca=dp(190), tam=ps, gravidade=-dp(160))
                        _estrela(camada, cx, cy, ps, CIANO)
                        _som('corte')
                        _tremer(8)
                        kk.impacto()
                        kk.empurrar(capa=-16, cabelo=-14, lift=6)
                        ax, ay = kk.ancora()
                        _mover(kk, (ax, ay), (ax + th * 0.3, ay + th * 1.9), 0.28, ease='out', fantasmas=2,
                               limite=(area, m))
                kk.tocar(seq, on_quadro=_q, on_fim=on_fim)
            _blitz_para(baixo_alvo, arma, _sobe)

        def _blitz_para(alvo, pose_fim, on_fim):
            ax, ay = kk.ancora()
            sinal = random.choice((-1, 1))
            guarda = _com(P['dupla'], olhos='s')
            meio = quadro((ax + alvo[0]) / 2.0 + dp(8) * sinal, (ay + alvo[1]) / 2.0 + th * 1.2 * sinal, [guarda])
            _blitz([meio, alvo], CIANO, on_fim, guarda, pose_fim)

        def _combo(i):
            if i > 3:
                _final()
                return
            (_ataque_giro, _ataque_mergulho, _ataque_salto)[i - 1](lambda: _combo(i + 1))

'''
c = c[:a] + novo + c[b:]
open(p, 'w', encoding='utf-8').write(c)
print('ok')
