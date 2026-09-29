"""Transformacao em Mugetsu (~10 s em etapas) com a fita de fogo, closes e o
grito no corte; rastro roxo do olho no Mugetsu."""
pc = r'C:\Users\kirit\travetefocus\app\cenas.py'
pk = r'C:\Users\kirit\travetefocus\app\kirito.py'
c = open(pc, encoding='utf-8').read()
k = open(pk, encoding='utf-8').read()


def troca(s, a, b, n=1):
    assert s.count(a) == n, (a[:80], s.count(a))
    return s.replace(a, b)


# ── o fogo do Mugetsu vira a fita (atras e na frente dele)
c = troca(c, """        camada.add_widget(K.ChamasReiatsu(kk, linguas=34))   # fogo da Bankai (atras)
        camada.add_widget(aura)
        camada.add_widget(K.RastroLamina(kk, faiscas))
        camada.add_widget(kk)
        camada.add_widget(K.ChamasReiatsu(kk, linguas=12, frente=True))""",
          """        fita_tras, fita_frente = K.FitaFogo(kk), K.FitaFogo(kk, frente=True)
        estado['fitas'] = (fita_tras, fita_frente)
        camada.add_widget(fita_tras)                     # fita de fogo do Mugetsu (atras)
        camada.add_widget(aura)
        camada.add_widget(K.RastroLamina(kk, faiscas))
        camada.add_widget(kk)
        camada.add_widget(fita_frente)                   # ... e a parte que passa na frente""")
c = troca(c, """        K.preparar_chamas()                            # quadros do fogo, aos poucos""",
          """        K.preparar_fita()                              # quadros da fita de fogo, aos poucos""")

# ── etapas da transformacao
a = c.index("        def _flash_fusao():")
b = c.index("        def _posiciona():")
c = c[:a] + '''        def _fitas(alvo=None, aperto=None, vel=None):
            for f in estado.get('fitas', ()):
                if alvo is not None:
                    f.alvo = alvo
                if aperto is not None:
                    f.aperto = aperto
                if vel is not None:
                    f.vel = vel

        def _flash_fusao():
            hx2, hy2 = kk.ponto_mao(1)
            jx, jy = hx2, hy2 + 6 * ps                 # onde as laminas se encontram
            # as laminas se fundem (clarao na juncao) e ele segura a espada
            # fundida no alto, tremendo com o reiatsu
            kk.tocar(K.poder(_com(P['fund_alto'], olhos='s'), n=36, de=0.9), loop=True)
            faiscas.estourar(jx, jy, BRANCO, n=26, forca=dp(220), tam=ps)
            faiscas.estourar(jx, jy, AZUL, n=16, forca=dp(160), tam=ps)
            _anel(camada, (jx, jy), ps * 2, ps * 22, 0.45, CIANO, esp=dp(4))
            _brilho_tela(camada, 0.3, 0.2)
            _som('fusao')
            _tremer(10)
            kk.pausar(0.08)
            kk.empurrar(cabelo=8, lift=6)
            aura.alvo = 0.35
            nome = estado.get('nome')
            if nome is not None:
                nome.parte2()
                ag.depois(1.1, nome.sumir)
            # close: o olho dele acende em ciano
            ag.depois(0.3, lambda: close_rosto(camada, 'poder', dur=0.8, y_rel=0.8))
            ag.depois(1.2, _enrola)

        def _enrola():
            # a fita de fogo sobe do chao e se enrola nele, apertada como um
            # casulo que gira
            _fitas(alvo=0.55, aperto=0.42, vel=20.0)
            _som('fitas')
            ag.depois(0.35, lambda: _som('fogo'))
            t = [0.0]

            def _vento(dt):
                t[0] += dt
                if t[0] > 1.5:
                    return False
                kk.empurrar(lift=1.8, cabelo=1.5, capa=-1.2)
                if random.random() < 0.6:
                    ax2, ay2 = kk.ancora()
                    faiscas.estourar(ax2 + random.uniform(-1, 1) * 9 * ps, ay2 - 10 * ps, ROXO, n=1,
                                     forca=dp(30), tam=max(2, ps * 0.6), gravidade=-dp(260))
                return True
            ag.cada(0.06, _vento)
            ag.depois(1.45, lambda: _cresce(0, 0.1))

        ETAPAS = (0.34, 0.66, 1.0)

        def _cresce(i, antes):
            # o cabelo cresce em 3 pulsos (no primeiro o sobretudo rasga e ele
            # vira o Mugetsu): cada pulso abre um pouco mais a fita
            alvo_c = ETAPAS[i]
            base = _com(M['fund_alto'], olhos='s')
            rampa = []
            for f, q in enumerate(K.poder(base, n=9, de=0.9)):
                q = dict(q)
                q['cresce'] = round((antes + (alvo_c - antes) * min(1.0, (f + 1) / 8.0)) * 20) / 20.0
                rampa.append(q)
            parado = [dict(q, cresce=alvo_c) for q in K.poder(base, n=36, de=0.9)]
            kk.tocar(rampa, on_fim=lambda: kk.tocar(parado, loop=True))
            ax_m, ay_m = kk.ancora()
            _anel(camada, (ax_m, ay_m + alt * 0.25), ps * 3, ps * (18 + 8 * i), 0.4, ROXO, esp=dp(4))
            faiscas.estourar(ax_m, ay_m + alt * 0.3, ROXO, n=10 + 6 * i, forca=dp(160), tam=ps, gravidade=-dp(100))
            _tremer(8 + 4 * i)
            kk.empurrar(cabelo=10, lift=6, capa=-8)
            _fitas(alvo=0.6 + 0.12 * i, aperto=0.5 + 0.12 * i)
            if i == 0:
                # o sobretudo rasga: clarao e retalhos escuros voando
                kk.clarao = 0.9
                ag.depois(0.1, lambda: _clarao_boneco(kk, 0.35))
                faiscas.estourar(ax_m, ay_m, (0.18, 0.1, 0.3), n=26, forca=dp(220), tam=ps * 1.4,
                                 gravidade=dp(80))
                _som('vidro')
                _brilho_tela(camada, 0.35, 0.2, (0.85, 0.75, 1.0))
            _som('absorve' if i == 2 else 'carga')
            if i < 2:
                ag.depois(0.6, lambda: _cresce(i + 1, alvo_c))
            else:
                aura.alvo = 0.7                          # a espada acende: roxo e azul
                ag.depois(0.7, _sugar)

        def _sugar():
            reator = estado['reator']
            ponta = lambda: kk.ponta_espada(1)
            if reator is None or reator.parent is None:
                _absorveu()
                return
            _fundo(tela, reator=1.0, barra=0.1, dur=0.35)    # o infinito acende enquanto e puxado
            _som('reiatsu')
            aura.alvo = 0.7
            fluxo = _Fluxo(reator, ponta, dur=1.9, px_tam=ps)
            estado['fluxo'] = fluxo
            camada.add_widget(fluxo, index=1)
            reator.sugar(ponta, dur=1.9, on_fim=lambda: ag.depois(0.0, _absorveu))
            vento = [0.0]

            def _vento(dt):
                vento[0] += dt
                if vento[0] > 2.0:
                    return False
                kk.empurrar(lift=2.2, cabelo=-1.5, capa=-1.0)
                if int(vento[0] * 10) % 4 == 0:
                    _tremer(2)
                return True
            ag.cada(0.08, _vento)
            ag.depois(2.6, lambda: None if getattr(reator, '_absorvido', False) else _absorveu())

        def _absorveu():
            if estado.get('absorveu'):
                return
            estado['absorveu'] = True
            fl = estado.get('fluxo')
            if fl is not None:
                ag.depois(0.25, fl.parar)
            r = estado['reator']
            if r is not None:
                r._absorvido = True
            tx, ty = kk.ponta_espada(1)
            kk.tocar(K.poder(M['evo_alto'], n=36, de=1.0, olhos='s'), loop=True)
            _clarao_boneco(kk, 0.3, 0.8)
            _anel(camada, (tx, ty), ps * 2, max(W, H) * 0.35, 0.45, BRANCO, esp=dp(3))
            faiscas.estourar(tx, ty, CIANO, n=30, forca=dp(300), tam=ps)
            _som('absorve')
            _tremer(12)
            kk.pausar(0.1)
            # close: os olhos acendem roxos
            ag.depois(0.25, lambda: close_rosto(camada, 'mugetsu', dur=0.95, y_rel=0.8, on_fim=_revela))

        def _revela():
            # a fita abre inteira em volta dele: o Mugetsu aparece
            kk.tocar(K.poder(M['evo_alto'], n=36, de=1.0, olhos='l'), loop=True)
            tx, ty = kk.ponta_espada(1)
            ax, ay = kk.ancora()
            _fitas(alvo=1.0, aperto=1.0, vel=14.0)
            kk.clarao = 1.0
            ag.depois(0.1, lambda: _clarao_boneco(kk, 0.45))
            _brilho_tela(camada, 0.7, 0.4, (0.9, 0.8, 1.0))
            _anel(camada, (ax, ay + alt * 0.3), ps * 3, max(W, H) * 0.6, 0.6, ROXO, esp=dp(5))
            faiscas.estourar(ax, ay + alt * 0.3, ROXO, n=40, forca=dp(320), tam=ps)
            faiscas.estourar(tx, ty, BRANCO, n=20, forca=dp(240), tam=ps)
            _som('titulo')
            _tremer(22)
            kk.pausar(0.14)
            aura.alvo = 1.0
            cam[0].ir(1.2, foco=(ax, ay + alt * 0.4), dur=0.5)
            ag.depois(1.0, _posiciona)

''' + c[b:]
# ── golpe final: silencio, ele grita "MUGETSU" e o corte cai no fim da palavra
c = troca(c, """            tv.crescer(ax, ay + alt * 0.3, dur=0.75)
            _som('trevas')
            ag.depois(0.5, lambda: _som('fogo'))
            aura.alvo = 1.0""", """            tv.crescer(ax, ay + alt * 0.3, dur=0.75)
            _som('trevas')
            aura.alvo = 1.0""")
c = troca(c, """            kk.tocar(K.poder(_com(M['evo_carga'], olhos='l'), n=36, de=0.7), loop=True)
            _som('voz_mugetsu')
            kk.empurrar(capa=4, cabelo=4, lift=3)
            ag.depois(1.0, _golpe_final)""", """            kk.tocar(K.poder(_com(M['evo_carga'], olhos='g'), n=36, de=0.7), loop=True)
            _som('voz_mugetsu')
            kk.empurrar(capa=4, cabelo=4, lift=3)
            ag.depois(1.3, _golpe_final)              # o corte cai no fim do grito""")
# ao sair do Mugetsu a fita se desfaz
c = troca(c, """            hx2, hy2 = kk.ponto_mao(1)
            aura.alvo = 0.0
            dupla = _com(P['dupla'], olhos='s')""", """            hx2, hy2 = kk.ponto_mao(1)
            aura.alvo = 0.0
            _fitas(alvo=0.0)
            dupla = _com(P['dupla'], olhos='s')""")
c = troca(c, """        ag.depois(32.0, _seguranca)""", """        ag.depois(36.0, _seguranca)""")

# ── rastro do olho no Mugetsu: roxo
k = troca(k, """        self._lote_olho = LotePixels(self.canvas.after, (
            ('rb', (0.20, 0.70, 1.00, 0.16)), ('r2', (0.10, 0.50, 0.95, 0.6)),
            ('r1', (0.33, 0.85, 1.00, 0.9)), ('r0', (0.85, 1.00, 1.00, 1.0))))""", """        self._lote_olho = LotePixels(self.canvas.after, (
            ('rb', (0.20, 0.70, 1.00, 0.16)), ('r2', (0.10, 0.50, 0.95, 0.6)),
            ('r1', (0.33, 0.85, 1.00, 0.9)), ('r0', (0.85, 1.00, 1.00, 1.0)),
            ('mb', (0.62, 0.30, 1.00, 0.18)), ('m2', (0.40, 0.18, 0.75, 0.6)),
            ('m1', (0.70, 0.40, 1.00, 0.9)), ('m0', (0.95, 0.88, 1.00, 1.0))))""")
k = troca(k, """            if not self.rastro_olho or p.get('mugetsu') or self.parent is None:""",
          """            if not self.rastro_olho or self.parent is None:""")
k = troca(k, """                    gx, gy = math.floor(x / te) * te, math.floor(y / te) * te
                    pontos.setdefault(cor, []).append((gx - (lado - te) / 2, gy - (lado - te) / 2, lado))
                    if idade < 3:                        # brilho em volta do risco
                        pontos.setdefault('rb', []).append((gx - 1.5 * te, gy - 1.5 * te, 4 * te))""",
          """                    gx, gy = math.floor(x / te) * te, math.floor(y / te) * te
                    cc = ('m' + cor[1]) if p.get('mugetsu') else cor
                    pontos.setdefault(cc, []).append((gx - (lado - te) / 2, gy - (lado - te) / 2, lado))
                    if idade < 3:                        # brilho em volta do risco
                        pontos.setdefault('mb' if p.get('mugetsu') else 'rb', []).append(
                            (gx - 1.5 * te, gy - 1.5 * te, 4 * te))""")
open(pc, 'w', encoding='utf-8', newline='\n').write(c)
open(pk, 'w', encoding='utf-8', newline='\r\n').write(k)
print('ok')
