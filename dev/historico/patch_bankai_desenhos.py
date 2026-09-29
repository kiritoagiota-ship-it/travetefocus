"""Bankai da abertura com os 6 DESENHOS da referencia do usuario (copiados
pixel a pixel, bankai/pN.png) como quadros-chave, Yoru ~15% maior:
- o anel de energia sobe e por baixo dele ja e o desenho 1 (de lado, espada
  baixa);
- o fio roxo da espada acende da guarda ate a ponta;
- corta para o desenho 5 (de frente, lua negra atras) com o fogo rugindo;
- salto para o meio da frase no desenho 2 (no ar, cortando) - e ali que a
  escuridao sai dele;
- carga no desenho 4 ("Ukete miro! Ougi!");
- o corte final no desenho 6; para de costas no desenho 3;
- volta ao desenho 1 e o anel desce devolvendo o Yoru normal.
Entre um desenho e outro: rastro (fantasma) e quadro de impacto."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'cenas.py'), [
    # chamas em volta do desenho pronto: pela parte firme dele
    ("""        k = self.k
        ps = k.ps
        ax, ay = k.ancora()
        frente = -1 if k.espelhar else 1
        x0, x1 = sorted((ax - frente * 7 * ps, ax + frente * 5 * ps))""",
     """        k = self.k
        if getattr(k, '_desenho', None) is not None:
            return k.corpo_desenho()
        ps = k.ps
        ax, ay = k.ancora()
        frente = -1 if k.espelhar else 1
        x0, x1 = sorted((ax - frente * 7 * ps, ax + frente * 5 * ps))"""),
    # sem o cabelo crescendo por passos (o desenho ja tem o cabelao)
    ("""        estado['cresce'] = 0.08

        def _dono_bankai():
            return estado.get('kk2') or kk

        def _aplica_cresce(c):
            # o cabelo do Bankai cresce: a pose do boneco que ja e Bankai muda
            # (mesmo tremor, mesmo quadro do loop)
            estado['cresce'] = c
            k = _dono_bankai()
            if k._seq:
                i = k._i
                k._seq = [dict(q, cresce=c) if q.get('mugetsu') else q for q in k._seq]
                k._i = min(i, len(k._seq))

        def _cabelo_cresce():
            passos = [round(0.08 + 0.92 * (i + 1) / 18.0, 2) for i in range(18)]

            def _p():
                if passos:
                    _aplica_cresce(passos.pop(0))
                    if len(passos) % 6 == 0:
                        _dono_bankai().empurrar(cabelo=4, lift=2)
                    ag.depois(0.05, _p)
            _som('fitas')
            _p()

        def _queima():""", """        mug_b = _com(mug, cresce=1.0)          # a pose que os efeitos leem no Bankai (espada fundida)

        def _bk(nome):
            \"\"\"Mostra o desenho `nome` do Bankai (copiado da referencia).\"\"\"
            kk.mostrar_desenho(nome, base=mug_b)

        def _queima():"""),
    ("""            base_m = _com(kai_m, cresce=0.08)
            kk2 = K.KiritoPixel(ps=ps)
            kk2.espelhar = kk.espelhar
            i = camada.children.index(kk) + 1 if kk in camada.children else 0
            camada.add_widget(kk2, index=i)
            kk2.ancorar(*kk.ancora())
            kk2.tocar(K.poder(base_m, n=36, de=0.9, sobe=1.2, lift=2.2), loop=True)
            kk2._preso = dict(kk._preso)
            estado['kk2'] = kk2
            ax, ay = kk.ancora()
            esq, baixo, dir_, cima = kk.extensao(_com(kai, a1=None, a2=None))
            y0, y1 = ay - baixo - te * 3, ay + cima + te * 8
            cx_c = ax + (dir_ - esq) / 2.0
            larg = (esq + dir_) * 1.05
            passo = te * 2
            y_pesc = ay + cima * 0.45
            anel = _AnelEnergia(te * 2)""", """            kk2 = K.KiritoPixel(ps=ps)
            kk2.espelhar = kk.espelhar
            i = camada.children.index(kk) + 1 if kk in camada.children else 0
            camada.add_widget(kk2, index=i)
            kk2.ancorar(*kk.ancora())
            kk2.mostrar_desenho('p1', base=mug_b)
            estado['kk2'] = kk2
            ax, ay = kk.ancora()
            esq, baixo, dir_, cima = kk.extensao(_com(kai, a1=None, a2=None))
            e2 = kk2.extensao()
            y0, y1 = ay - max(baixo, e2[1]) - te * 3, ay + max(cima, e2[3]) + te * 4
            bx0, bx1, _, _ = kk2.corpo_desenho()
            cx_c = (ax + (dir_ - esq) / 2.0 + (bx0 + bx1) / 2.0) / 2.0
            larg = max((esq + dir_) * 1.05, (bx1 - bx0) * 1.3)
            passo = te * 2
            anel = _AnelEnergia(te * 2)"""),
    ("""            dur = 1.45
            t = [0.0]
            cresceu = [False]
            kk.recortar(y0, None)""", """            dur = 1.45
            t = [0.0]
            kk.recortar(y0, None)"""),
    ("""                if not cresceu[0] and yq >= y_pesc:
                    cresceu[0] = True
                    _cabelo_cresce()
                if s >= 1.0:
                    _fim_queima(anel)""", """                if s >= 1.0:
                    _fim_queima(anel)"""),
    ("""            kk.recortar()
            if kk2 is not None:
                kk.tocar(kk2._seq, loop=True)
                kk._i = kk2._i
                kk._preso = dict(kk2._preso)
                for a in ('_m_capa', '_m_cab', '_m_lift'):
                    getattr(kk, a).x = getattr(kk2, a).x
                    getattr(kk, a).v = getattr(kk2, a).v
                kk2.recortar()
                if kk2.parent is not None:
                    kk2.parent.remove_widget(kk2)
            ax, ay = kk.ancora()
            faiscas.estourar(ax, ay + alt * 0.55, ROXO, n=24, forca=dp(260), tam=te * 2, gravidade=-dp(60))
            _som('titulo')
            _tremer(8)
            ag.depois(0.5, _funde)

        def _funde():
            # as duas espadas se juntam na frente e viram uma so: clarao nas
            # maos, e o fio roxo acende da guarda ate a ponta
            c = estado.get('cresce', 1.0)
            k_m = _com(kai_m, cresce=c)
            u_m = _com(une_m, cresce=c)
            kk.tocar(K.sequencia([(2, k_m, 'segura'), (6, u_m, 'in'), (3, u_m, 'segura'), (1, u_m)]),
                     on_fim=_fundiu)
            _som('giro')
            aura.alvo = 0.6

        def _fundiu():
            c = estado.get('cresce', 1.0)
            fim_m = _com(mug, cresce=c)
            hx, hy = kk.ponto_mao(1)
            kk.impacto(forte=True)
            _estrela(camada, hx, hy, ps, BRANCO)
            _anel(camada, (hx, hy), ps * 2, ps * 12, 0.3, ROXO)
            faiscas.estourar(hx, hy, BRANCO, n=16, forca=dp(200), tam=ps)
            faiscas.estourar(hx, hy, ROXO, n=16, forca=dp(160), tam=ps)
            _som('fusao')
            _tremer(12)
            acende = [(2, _com(fim_m, brilho=b / 8.0), 'segura') for b in range(9)]
            kk.tocar(K.sequencia(acende + [(1, fim_m)]),
                     on_fim=lambda: kk.tocar(K.poder(fim_m, n=36, de=0.9), loop=True))
            ag.depois(0.55, _lua)

        def _lua():
            # a lua negra sobe atras dele e o fogo ruge
            ax, ay = kk.ancora()
            lua = _LuaNegra((ax + (-1 if kk.espelhar else 1) * alt * 0.05, ay + alt * 0.5), alt * 0.62,
                            te * 2, dur=0.55)
            camada.add_widget(lua, index=len(camada.children))      # atras de tudo
            estado['lua'] = lua
            chamas.alvo = 1.0
            aura.alvo = 1.0
            _som('trevas')
            _tremer(8)
            kk.empurrar(capa=-6, cabelo=-5, lift=6)
            cam[0].ir(1.15, foco=(ax, ay + alt * 0.4), dur=0.6)
            # close: os olhos acendem roxos; depois a escuridao
            ag.depois(0.9, lambda: close_rosto(camada, 'mugetsu', dur=0.95, y_rel=0.8, on_fim=_posiciona))""",
     """            kk.recortar()
            _bk('p1')
            if kk2 is not None:
                kk2.recortar()
                if kk2.parent is not None:
                    kk2.parent.remove_widget(kk2)
            ax, ay = kk.ancora()
            faiscas.estourar(ax, ay + alt * 0.55, ROXO, n=24, forca=dp(260), tam=te * 2, gravidade=-dp(60))
            _som('titulo')
            _tremer(8)
            ag.depois(0.35, _acende_lamina)

        def _acende_lamina():
            # o fio roxo da espada acende da guarda ate a ponta
            hx, hy = kk.ponto_mao(1)
            tx, ty = kk.ponta_espada(1)
            aura.alvo = 0.7
            kk.impacto()
            _estrela(camada, hx, hy, ps, BRANCO)
            faiscas.estourar(hx, hy, BRANCO, n=10, forca=dp(150), tam=te * 2)
            _som('fusao')

            def forma(t, p, u):
                s = min(1.0, t / 0.32)
                for j in range(9):                        # cabeca clara e um rastro que esfria
                    ss = s - j * 0.035
                    if ss < 0:
                        break
                    x = hx + (tx - hx) * ss
                    y = hy + (ty - hy) * ss
                    nome = 'luz' if j < 2 else ('clara' if j < 5 else 'cor')
                    g = 2 if j < 3 else 1
                    p.setdefault(nome, []).append((math.floor(x / u) * u - (g - 1) * u,
                                                   math.floor(y / u) * u - (g - 1) * u, g * u, g * u))
            camada.add_widget(_EfeitoPixel(_cores_efeito(ROXO), 0.5, forma))
            ag.depois(0.32, lambda: (faiscas.estourar(tx, ty, ROXO, n=14, forca=dp(170), tam=te * 2),
                                     _estrela(camada, tx, ty, ps, ROXO)))
            ag.depois(0.6, _lua)

        def _lua():
            # corta para ele DE FRENTE, com a lua negra atras (desenho 5) e o
            # fogo rugindo
            kk.fantasma()
            kk.impacto(forte=True)
            _bk('p5')
            ax, ay = kk.ancora()
            chamas.alvo = 1.0
            aura.alvo = 1.0
            _som('trevas')
            _tremer(12)
            _brilho_tela(camada, 0.35, 0.22, (0.8, 0.62, 1.0))
            faiscas.estourar(ax, ay + alt * 0.5, ROXO, n=26, forca=dp(230), tam=te * 2, gravidade=-dp(80))
            cam[0].ir(1.15, foco=(ax, ay + alt * 0.45), dur=0.6)
            # close: os olhos acendem roxos; depois a escuridao
            ag.depois(1.05, lambda: close_rosto(camada, 'mugetsu', dur=0.95, y_rel=0.8, on_fim=_posiciona))"""),
    ("""            kk.espelhar = False
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
                   on_passo=_voo(kk, K.esticado(alto_p), K.encolhido(alto_p), alto_p, (0.25, 0.65)))""",
     """            kk.espelhar = False
            kk.fantasma()
            _bk('p2')                                  # no ar, cortando
            x_ini, y_ini = _dentro_girado(kk, cx_meio - th * 0.3, y_topo + alt * 0.45, area, m)
            ax, ay = kk.ancora()
            _som('pulo')
            cam[0].ir(1.0, dur=0.35)
            h = _arco(ay, y_ini, th * 1.2, area[3] - m - kk.extensao()[3])
            _mover(kk, (ax, ay), (x_ini, y_ini), 0.4, altura=h, fantasmas=4, on_fim=_trevas,
                   limite=(area, m))"""),
    ("""            kk.tocar(K.poder(_com(M['evo_alto'], olhos='l'), n=36, de=0.8), loop=True)
            ax, ay = kk.ancora()
            tv = _Trevas(2 * ps / float(K.R))""", """            _bk('p2')
            ax, ay = kk.ancora()
            tv = _Trevas(2 * ps / float(K.R))"""),
    ("""            kk.tocar(K.poder(_com(M['evo_carga'], olhos='g'), n=36, de=0.7), loop=True)
            _som('fala_ougi')""", """            kk.fantasma()
            _bk('p4')                                  # agachado, carregando
            _som('fala_ougi')"""),
    ("""            corte = _com(M['evo_corte'], sobe=1.0)
            meio = K.smear(K.misturar(M['evo_carga'], corte, 0.5, 0.5), P['evo_carga']['a1'])
            kk.impacto(forte=True)
            kk.tocar(K.sequencia([(1, meio, 'segura'), (1, K.smear(corte, P['evo_carga']['a1']), 'segura'),
                                  (6, corte, 'segura'), (1, corte)]))""",
     """            kk.fantasma()
            kk.impacto(forte=True)
            _bk('p6')                                  # o corte"""),
    ("""            fim_p = M['evo_fim']
            seg = _com(fim_p, a1=fim_p['a1'] - 20, dx=fim_p['dx'] + 1, sobe=0.6)
            kk.tocar(K.sequencia([(2, _com(M['evo_corte'], sobe=1.0), 'out'), (6, seg, 'mola'),
                                  (6, fim_p, 'segura'), (1, fim_p)]))
            kk.pausar(0.12)""", """            kk.fantasma()
            _bk('p3')                                  # de costas para a frase
            kk.pausar(0.12)"""),
    ("""            hx2, hy2 = kk.ponto_mao(1)
            aura.alvo = 0.0
            chamas.alvo = 0.0
            dupla = _com(P['dupla'], olhos='s')
            dupla_m = _com(dupla, mugetsu=True)
            # a lamina se divide nas duas (ainda no Bankai): estalo nas maos
            kk.tocar(K.sequencia([(4, _com(dupla_m, dx=dupla['dx'] + 1, a1=dupla['a1'] + 12,
                                             a2=dupla['a2'] - 12), 'mola'), (1, dupla_m)]))
            kk.impacto()""", """            kk.fantasma()
            _bk('p1')
            hx2, hy2 = kk.ponto_mao(1)
            aura.alvo = 0.0
            chamas.alvo = 0.0
            dupla = _com(P['dupla'], olhos='s')
            dupla_m = None
            # a lamina se divide nas duas: estalo nas maos
            kk.impacto()"""),
    ("""            ax, ay = kk.ancora()
            esq, baixo, dir_, cima = kk.extensao(_com(dupla, a1=None, a2=None))
            y_alto, y_baixo = ay + cima + te * 10, ay - baixo - te * 3""",
     """            ax, ay = kk.ancora()
            esq, baixo, dir_, cima = kk.extensao(_com(dupla, a1=None, a2=None))
            eb = kk.extensao()                             # o desenho do Bankai e mais alto
            y_alto, y_baixo = ay + max(cima, eb[3]) + te * 6, ay - max(baixo, eb[1]) - te * 3"""),
])
print('ok')
