"""BAN-KAI como o do Ichigo (pedido de 29/09/2026):
ergue a katana e aponta para a frente; a espada azul vira luz e entra na
katana; a outra mao segura o braco; "BAN..." (borda de energia fervendo);
"KAI!!" (grito "Haaa!" gravado, quadro de impacto) - o reiatsu roxo explode,
cobre ele inteiro e sobe numa coluna ate o ceu, ferve, os olhos acendem la
dentro e ele se desfaz em fiapos revelando o Bankai (desenho da referencia
animado peca por peca). Sai o anel que subia pelo corpo (parecia scanner)."""
import os
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'cenas.py')
c = open(A, encoding='utf-8').read()

# ── 1) a sequencia do BAN-KAI ────────────────────────────────────────────
ini = c.index("        # ── BAN-KAI (como a primeira Bankai do Ichigo)")
fim = c.index("        def _acende_lamina():")
NOVO = '''        # ── BAN-KAI (igual ao Ichigo) ─────────────────────────────────
        # ERGUE a katana num arco e desce APONTANDO para a frente; a espada
        # azul vira luz e entra na katana; a outra mao SEGURA o braco.
        # "BAN..." - a borda de energia ferve em volta dele. "KAI!!" - estouro
        # de luz: o reiatsu roxo (miolo branco) cobre ele inteiro e sobe numa
        # coluna ate o ceu, ferve, os olhos acendem la dentro... e se desfaz
        # em fiapos revelando o Bankai.
        b_agacha = K.pose(pernas='base_larga', dy=-1, m1=(-2, 2), a1=200.0, m2=(-4, -2), a2=230.0, olhos='s')
        b_ergue = K.pose(pernas='base_larga', dx=1, m1=(3, 13), a1=88.0, m2=(-4, -3), a2=232.0, olhos='s')
        b_aponta = K.pose(pernas='base_larga', dx=1, m1=(9, 3), a1=2.0, m2=(-5, -3), a2=238.0, olhos='s')
        b_livre = K.pose(pernas='base_larga', dx=1, m1=(9, 3), a1=2.0, m2=(-4, -2), olhos='s')
        b_segura = K.pose(pernas='base_larga', dx=1, m1=(9, 3), a1=2.0, m2=(8.5, 2.5), olhos='s', agarra=True)
        b_grita = K.pose(pernas='base_larga', dx=1, dy=-1, m1=(9, 3), a1=2.0, m2=(8.5, 2.5), olhos='g',
                         agarra=True)
        mug = K._fund(pernas='base_larga', m1=(8, 1), a1=-28.0, olhos='l', evo=True, mugetsu=True)
        kk.precarregar([b_agacha, b_ergue, b_aponta, b_livre, b_segura, b_grita])
        try:
            K.clipes_dados()                                      # clipes do Bankai: le antes
        except Exception as _e:
            print(f"[cena] clipes do Bankai: {_e}")
        mug_b = _com(mug, cresce=1.0)          # a pose que os efeitos leem no Bankai (espada fundida)

        def _bk(nome, loop=True, on_fim=None, on_quadro=None, k=None, t0=0.0):
            """Toca o clipe `nome` do Bankai (desenho da referencia, peca por peca)."""
            (k or kk).mostrar_clipe(nome, loop=loop, on_fim=on_fim, on_quadro=on_quadro, base=mug_b, t0=t0)

        def _bk_idle(k=None):
            _bk('idle', k=k)

        def _ban():
            # pousa no meio da frase; agacha (antecipacao), ERGUE a katana num
            # arco para cima, segura um instante e desce APONTANDO para a
            # frente (passa um pouquinho do ponto e volta)
            _som('pouso')
            ax, ay = kk.ancora()
            poeira(ax, ay - kk.extensao()[1], n=8)
            cam[0].ir(1.05, foco=(ax, ay + alt * 0.35), dur=2.4)
            _fundo(tela, reator=0.22, barra=0.1, dur=0.8)       # o mundo escurece um pouco
            seq = K.sequencia([(3, _com(P['agacha'], olhos='s'), 'out'), (5, b_agacha, 'out'),
                               (6, b_ergue, 'segura'), (6, b_ergue, 'mola'), (1, b_aponta)])

            def _q(i):
                if i == 4:
                    _som('sacar')
                    kk.empurrar(cabelo=-6, lift=5)
                elif i == 15:
                    _som('corte2')
                    kk.empurrar(capa=-8, cabelo=-6)
                elif i == 18:
                    hx, hy = kk.ponta_espada(1)
                    faiscas.estourar(hx, hy, CIANO, n=8, forca=dp(90), tam=ps)
            kk.tocar(seq, on_quadro=_q, on_fim=_azul_vira_luz)

        def _azul_vira_luz():
            # a espada azul acende, vira luz e corre pelo ar ate a katana
            hx2, hy2 = kk.ponto_mao(2)
            tx2, ty2 = kk.ponta_espada(2)
            hx1, hy1 = kk.ponto_mao(1)
            kk.mostrar(b_livre)
            _som('fusao')
            mx, my = (hx2 + tx2) / 2.0, (hy2 + ty2) / 2.0
            faiscas.estourar(mx, my, AZUL, n=22, forca=dp(110), tam=ps)
            _estrela(camada, mx, my, ps, AZUL)
            u = te * 2

            def forma(t, p, uu):
                s = min(1.0, t / 0.3)
                e = s * s * (3 - 2 * s)
                for j in range(10):                   # cabeca clara e o rastro que esfria
                    ss = e - j * 0.04
                    if ss < 0:
                        break
                    x = mx + (hx1 - mx) * ss
                    y = my + (hy1 - my) * ss + math.sin(ss * math.pi) * alt * 0.12
                    nome = 'luz' if j < 2 else ('clara' if j < 5 else 'cor')
                    g = 2 if j < 3 else 1
                    p.setdefault(nome, []).append((math.floor(x / u) * u, math.floor(y / u) * u, g * u, g * u))
            camada.add_widget(_EfeitoPixel(_cores_efeito(AZUL), 0.36, forma))

            def _chega():
                _estrela(camada, hx1, hy1, ps, BRANCO)
                faiscas.estourar(hx1, hy1, AZUL, n=12, forca=dp(120), tam=ps)
                kk.impacto()
                _som('cristal')
            ag.depois(0.3, _chega)
            ag.depois(0.5, _segura)

        def _segura():
            # a outra mao vem e SEGURA o braco da espada; silencio
            seq = K.sequencia([(6, b_livre, 'out'), (1, b_segura)])
            kk.tocar(seq, on_fim=lambda: kk.tocar(K.poder(b_segura, n=36, forca=0.4, sobe=0.5, lift=1.0),
                                                   loop=True))
            ag.depois(0.18, lambda: _som('agarra'))
            ag.depois(0.6, _ban_fala)

        def _ban_fala():
            # "BAN..." - a borda de energia comeca a ferver em volta dele
            balao(camada, 'BAN...', kk, tipo='fala', dur=1.1)
            _som('carga')
            kk.borda_energia(0.35)
            ag.depois(0.3, lambda: kk.borda_energia(0.7))
            ag.depois(0.6, lambda: kk.borda_energia(1.0))
            _fundo(tela, reator=0.35, barra=0.1, dur=0.9)
            cam[0].ir(1.07, foco=kk.ancora(), dur=0.9)
            t = [0.0]

            def _sobe(dt):
                t[0] += dt
                if t[0] > 0.95:
                    return False
                kk.empurrar(lift=1.2, cabelo=0.8)
                if random.random() < 0.6:
                    ax2, ay2 = kk.ancora()
                    faiscas.estourar(ax2 + random.uniform(-1, 1) * 9 * ps, ay2 - 11 * ps, ROXO, n=1,
                                     forca=dp(30), tam=max(2, ps * 0.6), gravidade=-dp(300))
                return True
            ag.cada(0.05, _sobe)
            _tremer(4)
            ag.depois(1.0, _kai)

        def _kai():
            # "KAI!!" - grito, quadro de impacto e o ESTOURO de luz
            kk.borda_energia(0)
            kk.parar()
            kk.mostrar(b_grita)
            balao(camada, 'KAI!!', kk, tipo='grito', dur=1.3, font_size=sp(40))
            _som('kiai_kai')
            _som('golpe_final')
            ax, ay = kk.ancora()
            _quadro_impacto(camada, kk, (ax, ay + alt * 0.3))
            _tremer(34)
            cam[0].ir(1.0, dur=0.15)
            ag.depois(2.2 / 30.0, _estouro)

        def _estouro():
            # o reiatsu explode dele: raios, onda de choque no chao, e o casulo
            # cresce ate cobrir tudo; coberto, por baixo ele ja e o Bankai
            kr = K.KiritoPixel(ps=ps)
            kr.espelhar = kk.espelhar
            i = camada.children.index(kk) if kk in camada.children else 0
            camada.add_widget(kr, index=i)                       # na frente dele
            kr.ancorar(*kk.ancora())
            estado['kr'] = kr
            _som('absorve')
            _som('reiatsu')
            _fundo(tela, reator=0.5, barra=0.1, dur=0.2)
            _brilho_tela(camada, 0.55, 0.3, (0.92, 0.85, 1.0))

            def _q(i):
                if i == 4 and 'pilar' not in estado:
                    _pilar(kr)
                if i >= 6 and kk._desenho is None:
                    _bk('idle')                            # coberto: ja e o Bankai la dentro
                    chamas.alvo = 0.35
            kr.mostrar_clipe('rei_estouro', loop=False, on_quadro=_q, on_fim=_ferve)

        def _pilar(kr):
            # a coluna de luz sobe do topo do casulo ate o fim da tela
            cab = K.clipes_dados()
            qx, qy = cab['quadril']
            lx, ly = kr._local_desenho(qx + 2, 2)
            u = kr.ps / float(K.R)
            p = _PilarReiatsu(kr.x + lx, kr.y + ly - 2 * u, 20 * u, u)
            i = camada.children.index(kr) if kr in camada.children else 0
            camada.add_widget(p, index=i + 1)                    # atras do casulo
            estado['pilar'] = p

        def _ferve():
            # FERVENDO: ele sumiu dentro do reiatsu; no fim os olhos acendem
            kr = estado.get('kr')
            if kr is None:
                return _revela()
            kr.mostrar_clipe('rei_ferve', loop=True)
            _tremer(10)
            ag.depois(1.0, _olhos)
            ag.depois(1.5, _revela)

        def _olhos():
            kr = estado.get('kr')
            o = kk.olhos_desenho() if kk._desenho is not None else None
            if kr is None or o is None:
                return
            ol = _OlhosAcesos(o, kr.ps / float(K.R))
            camada.add_widget(ol)
            estado['olhos'] = ol
            _som('titulo')

        def _revela():
            # o reiatsu se desfaz em fiapos subindo: aparece o BANKAI, com o
            # cabelo e o sobretudo ainda levantados pelo vento de energia
            kr = estado.get('kr')
            p = estado.pop('pilar', None)
            if p is not None:
                p.sumir(0.45)
            ol = estado.pop('olhos', None)
            if ol is not None and ol.parent is not None:
                ol.parent.remove_widget(ol)
            _bk('revela', loop=False, on_fim=_bk_idle)
            chamas.alvo = 0.8
            aura.alvo = 0.5
            _som('transicao')
            ax, ay = kk.ancora()
            faiscas.estourar(ax, ay + alt * 0.4, ROXO, n=28, forca=dp(220), tam=te * 2, gravidade=-dp(90))

            def _fim_rei():
                k2 = estado.pop('kr', None)
                if k2 is not None and k2.parent is not None:
                    k2.parent.remove_widget(k2)
                ag.depois(0.25, _acende_lamina)
            if kr is not None:
                kr.mostrar_clipe('rei_dissipa', loop=False, on_fim=_fim_rei)
            else:
                _fim_rei()

'''
c = c[:ini] + NOVO + c[fim:]

# ── 2) efeitos novos: coluna de luz e olhos acesos ───────────────────────
EFEITOS = '''_CORES_PILAR = (('c0', (0.118, 0.039, 0.275, 1.0)), ('c1', (0.275, 0.102, 0.627, 1.0)),
                ('c2', (0.439, 0.196, 0.902, 1.0)), ('c3', (0.627, 0.408, 1.0, 1.0)),
                ('c4', (0.816, 0.667, 1.0, 1.0)), ('c5', (0.973, 0.941, 1.0, 1.0)))


class _PilarReiatsu(Widget):
    """A coluna de luz do BAN-KAI: sai do topo do reiatsu e sobe ate o fim da
    tela. Faixas roxas com o miolo branco (as mesmas cores do casulo), borda
    que ferve (troca 12 vezes por segundo) e riscos claros subindo. Abre de
    largura rapido e some afinando."""

    def __init__(self, cx, y0, meia, u, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.cx, self.y0, self.meia = float(cx), float(y0), float(meia)
        self.u = max(1.0, float(u))
        self.forca = 0.0
        self.alvo = 1.0
        self.vel = 1.0 / 0.18
        self.t = 0.0
        self._ult = -1
        self._lote = K.LotePixels(self.canvas, _CORES_PILAR)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def sumir(self, dur=0.4):
        self.alvo = 0.0
        self.vel = 1.0 / max(0.05, dur)

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            self.t += dt
            if self.forca < self.alvo:
                self.forca = min(self.alvo, self.forca + self.vel * dt)
            elif self.forca > self.alvo:
                self.forca = max(self.alvo, self.forca - self.vel * dt)
                if self.forca <= 0.0:
                    self.parent.remove_widget(self)
                    return self.parar()
            f = int(self.t * 12)
            if f != self._ult:
                self._ult = f
                self._desenha(f)
            return True
        except Exception as e:
            print(f"[pilar] {e}")
            return self.parar()

    def _desenha(self, f):
        u = self.u
        H = Window.size[1]
        passo = 2 * u
        meia = self.meia * self.forca
        cx = math.floor(self.cx / u) * u
        y = math.floor(self.y0 / u) * u
        rnd = random.Random(f * 7919 + 13)
        faixas = ((0.0, 'c0'), (0.14, 'c1'), (0.3, 'c2'), (0.48, 'c3'), (0.64, 'c4'), (0.8, 'c5'))
        pts = {}
        j = 0
        while y < H + passo:
            m = meia * (1.0 + 0.1 * math.sin(j * 0.55 - f * 1.3) + rnd.uniform(-0.07, 0.07))
            for fr, nome in faixas:
                n = int(round(m * (1.0 - fr) / u))
                if n < 1:
                    break
                pts.setdefault(nome, []).append((cx - n * u, y, 2 * n * u, passo))
            j += 1
            y += passo
        # riscos claros subindo pela coluna
        alto = max(1.0, H - self.y0)
        for k in range(9):
            yy = self.y0 + ((self.t * 900.0 + k * 211.0) % alto)
            xx = cx + ((k * 5) % 9 - 4) * u * max(0.2, self.forca) * (self.meia / (6 * u))
            pts.setdefault('c5', []).append((math.floor(xx / u) * u, math.floor(yy / u) * u, u, 6 * u))
        self._lote.desenhar(pts)

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


class _OlhosAcesos(Widget):
    """O olho do Bankai acendendo dentro do reiatsu: miolo branco com a
    borda escura (aparece em cima de qualquer cor) e uma cruz lilas que
    cresce e pisca (12 trocas por segundo)."""

    def __init__(self, pos, u, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.p = pos
        self.u = max(1.0, float(u))
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, (('borda', (0.12, 0.04, 0.27, 1.0)),
                                                ('halo', (0.63, 0.41, 1.0, 1.0)),
                                                ('luz', (0.97, 0.94, 1.0, 1.0))))
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            self.t += dt
            u = self.u
            cx = math.floor(self.p[0] / u) * u
            cy = math.floor(self.p[1] / u) * u
            f = int(self.t * 12)
            n = min(4, 1 + f // 2) - (f % 2 if f > 6 else 0)
            pts = {'borda': [(cx - 2 * u, cy - u, 5 * u, 3 * u)],
                   'luz': [(cx - u, cy, 3 * u, u)], 'halo': []}
            for k in range(2, 2 + n):
                for (dx, dy) in ((k, 0), (-k - 1, 0), (0, k), (0, -k)):
                    pts['halo'].append((cx + dx * u, cy + dy * u, u, u))
            self._lote.desenhar(pts)
            return True
        except Exception as e:
            print(f"[olhos] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


'''
marca = "_CORES_LUA = ("
assert c.count(marca) == 1
c = c.replace(marca, EFEITOS + marca)

# ── 3) sons novos pre-carregados e o cabecalho ──────────────────────────
a = "                'trevas', 'fusao', 'reiatsu',\n"
assert c.count(a) == 1
c = c.replace(a, "                'trevas', 'fusao', 'reiatsu', 'kiai_kai', 'agarra', 'cristal', 'transicao',\n")
a = """                                    silaba aparece por onde a luz de um corte
                                    passa), BAN-KAI em baloes de fala com a
                                    nuvem de reiatsu, Mugetsu, o corte final"""
assert c.count(a) == 1
c = c.replace(a, """                                    silaba aparece por onde a luz de um corte
                                    passa), BAN-KAI como o do Ichigo (aponta a
                                    espada, segura o braco, o reiatsu cobre e
                                    revela o Bankai), Mugetsu, o corte final""")
open(A, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
