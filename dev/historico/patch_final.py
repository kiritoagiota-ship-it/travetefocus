import os
AQUI = os.path.dirname(__file__)
p = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(p, encoding='utf-8').read()

# widget das trevas antes da onda do getsuga
trevas = open(os.path.join(AQUI, 'trevas.txt'), encoding='utf-8').read()
assert c.count('class _OndaGetsuga(Widget):') == 1
c = c.replace('class _OndaGetsuga(Widget):', trevas + 'class _OndaGetsuga(Widget):')

a = c.index('        def _posiciona():')
b = c.index('        def _para():')
novo = '''        def _posiciona():
            # sobe para o meio da frase: dali a escuridao vai sair dele
            kk.espelhar = False
            poses_f = [M['evo_alto'], M['evo_carga'], M['evo_corte'], M['evo_fim']]
            x_ini, y_ini = quadro(cx_meio - th * 0.3, y_topo + alt * 0.45, poses_f)
            ax, ay = kk.ancora()
            alto_p = _com(M['evo_alto'], sobe=1.0, olhos='l')
            kk.parar()
            kk.mostrar(K.esticado(alto_p))
            _som('pulo')
            cam[0].ir(1.0, dur=0.35)
            h = _arco(ay, y_ini, th * 1.2, area[3] - m - _ext(kk, [K.esticado(alto_p)])[3])
            _mover(kk, (ax, ay), (x_ini, y_ini), 0.4, altura=h, fantasmas=4, on_fim=_trevas,
                   limite=(area, m),
                   on_passo=_voo(kk, K.esticado(alto_p), K.encolhido(alto_p), alto_p, (0.25, 0.65)))

        def _trevas():
            # MUGETSU: a escuridao sai dele e engole a tela inteira (a frase e
            # o infinito somem); so os olhos, o fogo e a espada brilham
            kk.tocar(K.poder(_com(M['evo_alto'], olhos='l'), n=36, de=0.8), loop=True)
            ax, ay = kk.ancora()
            tv = _Trevas(2 * ps / float(K.R))
            i = camada.children.index(titulo) if titulo in camada.children else len(camada.children)
            camada.add_widget(tv, index=i)
            estado['trevas'] = tv
            tv.crescer(ax, ay + alt * 0.3, dur=0.75)
            _som('reiatsu')
            aura.alvo = 1.0
            cam[0].ir(1.12, foco=(ax, ay + alt * 0.3), dur=1.4)
            kk.empurrar(capa=-6, cabelo=-5, lift=4)
            ag.depois(1.3, _ergue)

        def _ergue():
            # silencio: a lamina vai para tras e o fogo sobe
            kk.tocar(K.poder(_com(M['evo_carga'], olhos='l'), n=36, de=0.7), loop=True)
            _som('carga')
            kk.empurrar(capa=4, cabelo=4, lift=3)
            ag.depois(0.6, _golpe_final)

        def _golpe_final():
            # UM corte so: a lamina atravessa e um risco de luz corta a tela de
            # um lado ao outro na altura da frase... e tudo congela
            corte = _com(M['evo_corte'], sobe=1.0)
            meio = K.smear(K.misturar(M['evo_carga'], corte, 0.5, 0.5), P['evo_carga']['a1'])
            kk.impacto(forte=True)
            kk.tocar(K.sequencia([(1, meio, 'segura'), (1, K.smear(corte, P['evo_carga']['a1']), 'segura'),
                                  (6, corte, 'segura'), (1, corte)]))
            _, cy = titulo.x_do_trecho(0, len(texto))
            tv = estado.get('trevas')
            if tv is not None:
                tv.cortar(cy)
            _som('sacar_iai')
            cam[0].ir(1.0, dur=0.1)
            ag.depois(0.08, lambda: kk.pausar(0.55))
            ag.depois(0.7, _abre)

        def _abre():
            # a escuridao se abre no corte: a frase aparece gravada dentro dele
            tv = estado.get('trevas')
            if tv is not None:
                tv.abrir(0.6)
            _, cy = titulo.x_do_trecho(0, len(texto))
            i0, i1 = _TRECHOS[4]
            titulo.revelar(i0, i1, dur=0.05)
            for li, letra in enumerate(texto):
                if letra.strip():
                    ag.depois(0.015 * li, lambda li=li: titulo.gravar(li, li + 1))
            for j in range(9):
                xj = area[0] + (area[2] - area[0]) * (j + 0.5) / 9.0
                faiscas.estourar(xj, cy, random.choice((ROXO, BRANCO, (0.85, 0.72, 1.0))), n=5,
                                 forca=dp(240), tam=ps, gravidade=dp(160))
            _som('getsuga')
            _tremer(28)
            _brilho_tela(camada, 0.5, 0.35, (0.9, 0.82, 1.0))
            ag.depois(0.3, _para)

'''
c = c[:a] + novo + c[b:]
open(p, 'w', encoding='utf-8').write(c)
print('ok')
