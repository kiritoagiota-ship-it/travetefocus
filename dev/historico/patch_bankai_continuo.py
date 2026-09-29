"""Abertura: o Bankai CONTINUO (boneco articulado da referencia), sem cortes:
- o anel sobe e por baixo dele o Bankai NASCE (o cabelo cresce da raiz, as
  caudas descem, a lamina nasce da guarda) e fica flutuando (idle);
- o fio da espada acende; a LUA NEGRA sobe atras dele, o fogo ruge; close;
- ele LEVITA devagar ate o meio da frase (sem pulo, o cabelo flutuando);
- carga (a lamina vai para tras e segura tremendo) com "Ukete miro! Ougi!";
- o corte sobe pela frente e, no quadro em que a lamina passa, a luz grava
  o CUS e a tela congela; depois volta devagar a flutuar;
- o anel desce e devolve o Yoru normal."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'cenas.py'), [
    # _mover: curva suave (levitar)
    ("""            if ease == 'linear':
                e = u
            elif ease == 'in':
                e = u * u
            else:
                e = 1 - (1 - u) ** 2""", """            if ease == 'linear':
                e = u
            elif ease == 'in':
                e = u * u
            elif ease == 'suave':
                e = u * u * (3 - 2 * u)
            else:
                e = 1 - (1 - u) ** 2"""),
    ("""        for _n in ('p1', 'p2', 'p3', 'p4', 'p5', 'p6'):          # desenhos do Bankai: carrega antes
            try:
                K.desenho_dados(_n)
            except Exception as _e:
                print(f"[cena] desenho {_n}: {_e}")""", """        try:
            K.clipes_dados()                                      # clipes do Bankai: le antes
        except Exception as _e:
            print(f"[cena] clipes do Bankai: {_e}")"""),
    ("""        def _bk(nome):
            \"\"\"Mostra o desenho `nome` do Bankai (copiado da referencia).\"\"\"
            kk.mostrar_desenho(nome, base=mug_b)
""", """        def _bk(nome, loop=True, on_fim=None, on_quadro=None, k=None, t0=0.0):
            \"\"\"Toca o clipe `nome` do Bankai (boneco articulado da referencia).\"\"\"
            (k or kk).mostrar_clipe(nome, loop=loop, on_fim=on_fim, on_quadro=on_quadro, base=mug_b, t0=t0)

        def _bk_idle(k=None):
            _bk('idle', k=k)
"""),
    ("""            kk2.mostrar_desenho('p1', base=mug_b)
            estado['kk2'] = kk2
            ax, ay = kk.ancora()
            esq, baixo, dir_, cima = kk.extensao(_com(kai, a1=None, a2=None))
            e2 = kk2.extensao()
            y0, y1 = ay - max(baixo, e2[1]) - te * 3, ay + max(cima, e2[3]) + te * 4
            bx0, bx1, _, _ = kk2.corpo_desenho()""", """            _bk('nasce', loop=False, on_fim=lambda: _bk_idle(kk2), k=kk2)
            estado['kk2'] = kk2
            ax, ay = kk.ancora()
            esq, baixo, dir_, cima = kk.extensao(_com(kai, a1=None, a2=None))
            bx0, bx1, by_pe, b_alt = kk2.corpo_desenho()
            y0, y1 = min(ay - baixo, by_pe) - te * 3, max(ay + cima, by_pe + b_alt) + te * 6"""),
    ("""            kk.recortar()
            _bk('p1')
            if kk2 is not None:
                kk2.recortar()""", """            kk.recortar()
            if kk2 is not None:
                if kk2._desenho == 'nasce' and kk2._clipe_fim is not None:
                    _bk('nasce', loop=False, on_fim=_bk_idle, t0=kk2._clipe_t)
                else:
                    _bk('idle', t0=kk2._clipe_t)
                kk2.recortar()"""),
    ("""        def _lua():
            # corta para ele DE FRENTE, com a lua negra atras (desenho 5) e o
            # fogo rugindo
            kk.fantasma()
            kk.impacto(forte=True)
            _bk('p5')
            ax, ay = kk.ancora()
            chamas.alvo = 1.0""", """        def _lua():
            # a lua negra sobe atras dele e o fogo ruge (ele continua flutuando)
            ax, ay = kk.ancora()
            lua = _LuaNegra((ax + (-1 if kk.espelhar else 1) * alt * 0.05, ay + alt * 0.62), alt * 0.7,
                            te * 2, dur=0.7)
            camada.add_widget(lua, index=len(camada.children))      # atras de tudo
            estado['lua'] = lua
            chamas.alvo = 1.0"""),
    ("""            ag.depois(1.05, lambda: close_rosto(camada, 'mugetsu', dur=0.95, y_rel=0.8, on_fim=_posiciona))

        def _posiciona():""", """            ag.depois(1.2, lambda: close_rosto(camada, 'mugetsu', dur=0.95, y_rel=0.8, on_fim=_posiciona))

        def _posiciona():"""),
    ("""            kk.espelhar = False
            kk.fantasma()
            _bk('p2')                                  # no ar, cortando
            x_ini, y_ini = _dentro_girado(kk, cx_meio - th * 0.3, y_topo + alt * 0.45, area, m)
            ax, ay = kk.ancora()
            _som('pulo')
            cam[0].ir(1.0, dur=0.35)
            h = _arco(ay, y_ini, th * 1.2, area[3] - m - kk.extensao()[3])
            _mover(kk, (ax, ay), (x_ini, y_ini), 0.4, altura=h, fantasmas=4, on_fim=_trevas,
                   limite=(area, m))""", """            kk.espelhar = False
            x_ini, y_ini = _dentro_girado(kk, cx_meio - th * 0.3, y_topo + alt * 0.45, area, m)
            ax, ay = kk.ancora()
            _som('reiatsu')
            cam[0].ir(1.0, dur=0.6)
            # levita: sobe devagar, o cabelo e o casaco flutuando
            _mover(kk, (ax, ay), (x_ini, y_ini), 1.0, altura=th * 0.25, fantasmas=0, on_fim=_trevas,
                   limite=(area, m), ease='suave')"""),
    ("""            # MUGETSU: a escuridao sai dele e engole a tela inteira (a frase e
            # o infinito somem); so os olhos, o fogo e a espada brilham
            _bk('p2')
            ax, ay = kk.ancora()""", """            # MUGETSU: a escuridao sai dele e engole a tela inteira (a frase e
            # o infinito somem); so os olhos, o fogo e a espada brilham
            ax, ay = kk.ancora()"""),
    ("""            # silencio: ele diz o nome do golpe, a lamina vai para tras e o fogo sobe
            kk.fantasma()
            _bk('p4')                                  # agachado, carregando
            _som('fala_ougi')
            kk.empurrar(capa=4, cabelo=4, lift=3)
            ag.depois(1.2, _golpe_final)              # o corte cai no "GI!" do grito""",
     """            # silencio: ele diz o nome do golpe, a lamina vai para tras (devagar)
            # e segura tremendo
            _bk('carga', loop=False, on_fim=lambda: _bk('carga_segura'))
            _som('fala_ougi')
            ag.depois(1.12, _golpe_final)             # o corte cai no "GI!" do grito"""),
    ("""            kk.fantasma()
            kk.impacto(forte=True)
            _bk('p6')                                  # o corte
            _, cy = titulo.x_do_trecho(0, len(texto))""", """            feito = [False]

            def _q(i):
                if i >= 5 and not feito[0]:           # a lamina passa pela frente: o golpe
                    feito[0] = True
                    _impacto_final()
            _bk('corte', loop=False, on_quadro=_q,
                on_fim=lambda: _bk('fim', loop=False, on_fim=_bk_idle))

        def _impacto_final():
            kk.impacto(forte=True)
            _, cy = titulo.x_do_trecho(0, len(texto))"""),
    ("""            kk.fantasma()
            _bk('p3')                                  # de costas para a frase
            kk.pausar(0.12)
            kk.empurrar(capa=-20, cabelo=-16)
            ag.depois(0.55, _separa)""", """            ag.depois(0.9, _separa)"""),
    ("""            kk.fantasma()
            _bk('p1')
            hx2, hy2 = kk.ponto_mao(1)""", """            hx2, hy2 = kk.ponto_mao(1)"""),
])
print('ok')
