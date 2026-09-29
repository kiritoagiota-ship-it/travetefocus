"""BANKAI COM A TRANSFORMACAO A MOSTRA (~5 s, como a referencia do usuario):
BAN! (katana apontada) -> KAI! (a azul cruza, estrondo) -> o reiatsu roxo
explode do chao, chamas sobem em volta e os olhos acendem -> um ANEL de
energia sobe dos pes a cabeca e por baixo dele ele ja e o Bankai (pixel a
pixel: o sobretudo rasgado em chamas aparece primeiro, depois o peito, os
bracos) -> o cabelo cresce em degraus -> as duas espadas se juntam e viram
a lamina escura com o fio roxo acendendo da guarda ate a ponta -> uma LUA
NEGRA sobe atras dele -> close nos olhos roxos. Sem a nuvem de bolinhas e
sem as fitas em espiral. Na volta ao normal, o anel desce da cabeca aos pes."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'kirito.py'), [
    # a pose pode pedir o brilho da lamina (o fio acendendo na fusao)
    ("""        ciclo = self._t % 2.6
        q['brilho'] = (round(ciclo / 0.45 * 6) / 6.0) if (ciclo < 0.45 and self._loop
                                                            and not b.get('mugetsu')) else None
        return q""", """        ciclo = self._t % 2.6
        if b.get('brilho') is not None:
            q['brilho'] = b['brilho']
        else:
            q['brilho'] = (round(ciclo / 0.45 * 6) / 6.0) if (ciclo < 0.45 and self._loop
                                                                and not b.get('mugetsu')) else None
        return q"""),
])

CLASSES = '''

# ═══════════════════════════════════════════════════════════════════
#  EFEITOS DA TRANSFORMACAO (Bankai)
# ═══════════════════════════════════════════════════════════════════
_CORES_CHAMA = (('L', (0.93, 0.86, 1.0, 1.0)), ('V', (0.86, 0.58, 1.0, 1.0)),
                ('F', (0.62, 0.28, 1.0, 0.95)), ('o', (0.42, 0.18, 0.78, 0.9)),
                ('d', (0.24, 0.10, 0.42, 0.8)))


class _ChamasBankai(Widget):
    """Chamas roxas de pixel art em volta do Bankai: linguas de fogo (3 a 5
    blocos empilhados que afinam na ponta) nascem no chao e nas bordas do
    corpo, sobem balancando e escurecem em degraus antes de sumir. `alvo`
    0..1 = quantas nascem (a forca vai ate ele aos poucos)."""

    def __init__(self, k, u, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k = k
        self.u = max(1.0, float(u))
        self.forca = 0.0
        self.alvo = 0.0
        self._f = []
        self._acc = 0.0
        self._caixa = None
        self._n = 0
        self._lote = K.LotePixels(self.canvas, _CORES_CHAMA)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def _corpo(self):
        """(x0, x1, y_pe, altura) do corpo (sem as espadas), a cada 10 quadros."""
        self._n += 1
        if self._caixa is None or self._n % 10 == 0:
            k = self.k
            b = k._base
            esq, baixo, dir_, cima = k.extensao(dict(b, a1=None, a2=None))
            ax, ay = k.ancora()
            self._caixa = (ax - esq, ax + dir_, ay - baixo, baixo + cima)
        return self._caixa

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            self.forca += (self.alvo - self.forca) * min(1.0, dt * 3.0)
            k = self.k
            u = self.u
            if k.parent is None or k.opacity < 0.05:
                self._lote.desenhar({})
                return True
            x0, x1, y_pe, alt = self._corpo()
            self._acc += self.forca * 75.0 * dt
            while self._acc >= 1.0:
                self._acc -= 1.0
                borda = random.random() < 0.7
                if borda:                                   # nas bordas do corpo (mais atras)
                    x = (x0 + random.uniform(-0.1, 0.25) * (x1 - x0)) if random.random() < 0.6 \\
                        else (x1 - random.uniform(-0.1, 0.25) * (x1 - x0))
                else:
                    x = random.uniform(x0, x1)
                y = y_pe + alt * (random.random() ** 2.2) * 0.85
                vida = random.uniform(0.35, 0.75)
                self._f.append({'x': x, 'y': y, 'vy': alt * random.uniform(0.7, 1.3), 't': 0.0,
                                'vida': vida, 'n': random.choice((3, 4, 4, 5)),
                                'fb': random.uniform(7, 12), 'ph': random.uniform(0, 6.3)})
            pts = {}
            vivas = []
            for f in self._f:
                f['t'] += dt
                if f['t'] >= f['vida']:
                    continue
                vivas.append(f)
                f['y'] += f['vy'] * dt
                a = f['t'] / f['vida']
                bx = math.floor((f['x'] + math.sin(f['t'] * f['fb'] + f['ph']) * u * 1.4) / u) * u
                by = math.floor(f['y'] / u) * u
                n = max(1, int(round(f['n'] * (1.0 - 0.5 * a))))       # encurta enquanto sobe
                for i in range(n):
                    c = min(4, int(a * 3.2) + (1 if i >= n - 1 else 0) + (1 if i == 0 and a > 0.5 else 0))
                    nome = ('L', 'V', 'F', 'o', 'd')[c]
                    larg = 2 if (i < n - 2 and a < 0.45) else 1          # base mais larga, ponta fina
                    tremor = u if (i == n - 1 and int(f['t'] * 20 + f['ph']) % 2) else 0
                    pts.setdefault(nome, []).append((bx - (larg - 1) * u * 0.5 + tremor, by + i * u, larg * u, u))
            self._f = vivas[-160:]
            self._lote.desenhar(pts)
        except Exception as e:
            print(f"[chamas] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


_CORES_LUA = (('halo', (0.40, 0.16, 0.72, 0.5)), ('fundo', (0.03, 0.01, 0.055, 0.95)),
              ('miolo', (0.07, 0.02, 0.12, 0.95)), ('borda', (0.62, 0.30, 1.0, 1.0)),
              ('claro', (0.93, 0.82, 1.0, 1.0)))


class _LuaNegra(Widget):
    """Lua negra atras do Bankai: disco escuro de pixels grandes com a borda
    roxa acesa (que tremula) e um halo pontilhado; cresce em degraus e
    some encolhendo."""

    def __init__(self, centro, raio, u, dur=0.5, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.c = centro
        self.u = max(2.0, float(u))
        self.r_alvo = float(raio)
        self.r = 0.0
        self.vel = raio / max(0.05, dur)
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, _CORES_LUA)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)

    def sumir(self, dur=0.35):
        self.r_alvo = 0.0
        self.vel = max(self.r, 1.0) / max(0.05, dur)

    def _tick(self, dt):
        try:
            if self.parent is None:
                return self.parar()
            self.t += dt
            if self.r < self.r_alvo:
                self.r = min(self.r_alvo, self.r + self.vel * dt)
            elif self.r > self.r_alvo:
                self.r = max(self.r_alvo, self.r - self.vel * dt)
                if self.r <= 0.0:
                    if self.parent is not None:
                        self.parent.remove_widget(self)
                    return self.parar()
            u = self.u
            n = int(self.r / u)
            cx = math.floor(self.c[0] / u) * u
            cy = math.floor(self.c[1] / u) * u
            pts = {}
            f = int(self.t * 12)
            for iy in range(-n - 2, n + 3):
                for d_ext, nome in ((n + 2.5, 'halo'), (n + 0.5, 'borda'), (n - 0.5, 'fundo')):
                    pass
                w_f = math.sqrt(max(0.0, (n - 0.5) ** 2 - iy * iy))
                if w_f > 0:
                    k0 = int(math.floor(-w_f))
                    pts.setdefault('fundo', []).append((cx + k0 * u, cy + iy * u, (2 * -k0 + 1) * u, u))
                    if abs(iy) < n * 0.55:                               # miolo um tiquinho mais claro
                        w_m = math.sqrt(max(0.0, (n * 0.55) ** 2 - iy * iy))
                        km = int(math.floor(-w_m))
                        pts.setdefault('miolo', []).append((cx + km * u, cy + iy * u, (2 * -km + 1) * u, u))
            if n >= 1:
                m = max(16, int(2 * math.pi * n))
                vistos = set()
                for i in range(m):
                    a = 2 * math.pi * i / m
                    for rr, nome in ((n, 'borda'), (n + 1.6, 'halo')):
                        gx, gy = int(round(math.cos(a) * rr)), int(round(math.sin(a) * rr))
                        if (gx, gy, nome) in vistos:
                            continue
                        vistos.add((gx, gy, nome))
                        h = (gx * 7 + gy * 13 + f) % 9
                        if nome == 'halo' and h > 3:
                            continue
                        nm = 'claro' if (nome == 'borda' and h == 0) else nome
                        pts.setdefault(nm, []).append((cx + gx * u, cy + gy * u, u, u))
            self._lote.desenhar(pts)
        except Exception as e:
            print(f"[lua] {e}")
            return self.parar()

    def parar(self):
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None
        return False


class _AnelEnergia(Widget):
    """A linha da transformacao: uma elipse achatada de pixels roxos e
    lilases em volta do corpo, na altura y (a frente mais clara que a parte
    de tras), tremulando."""

    def __init__(self, u, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.u = max(1.0, float(u))
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, _CORES_CHAMA)

    def pos_linha(self, cx, y, larg, dt=1 / 60.):
        self.t += dt
        u = self.u
        a = max(u * 3, larg / 2.0)
        b = u * 2.2
        n = max(16, int(2 * math.pi * a / u))
        pts = {}
        f = int(self.t * 24)
        for i in range(n):
            ang = 2 * math.pi * i / n
            x = math.floor((cx + math.cos(ang) * a) / u) * u
            yy = math.floor((y + math.sin(ang) * b) / u) * u
            frente = math.sin(ang) < 0
            h = (i * 5 + f) % 7
            if frente:
                nome = 'L' if h < 2 else 'V'
            else:
                if h > 4:
                    continue
                nome = 'F' if h < 3 else 'o'
            pts.setdefault(nome, []).append((x, yy, u, u))
            if frente and h == 0:                               # lingua de fogo subindo da frente
                pts.setdefault('F', []).append((x, yy + u, u, u))
        # a faixa de corte, bem fina, atravessando o corpo
        k0 = math.floor((cx - a) / u)
        k1 = math.floor((cx + a) / u)
        for k in range(k0, k1 + 1):
            if (k + f) % 3:
                pts.setdefault('L', []).append((k * u, math.floor(y / u) * u, u, u))
        self._lote.desenhar(pts)
'''

patch(os.path.join(A, 'cenas.py'), [
    ("""def _pendurado_idle(base, base_b, piscar=True):""", CLASSES.lstrip('\n') + """

def _pendurado_idle(base, base_b, piscar=True):"""),
    # sem as fitas em espiral; chamas de pixel no lugar
    ("""        fita_tras, fita_frente = K.FitaFogo(kk), K.FitaFogo(kk, frente=True)
        estado['fitas'] = (fita_tras, fita_frente)
        camada.add_widget(fita_tras)                     # fita de fogo do Mugetsu (atras)
        camada.add_widget(aura)
        camada.add_widget(K.RastroLamina(kk, faiscas))
        camada.add_widget(kk)
        camada.add_widget(fita_frente)                   # ... e a parte que passa na frente
        camada.add_widget(faiscas)""", """        estado['fitas'] = ()
        chamas = _ChamasBankai(kk, 2 * ps / float(K.R))   # chamas roxas do Bankai (atras dele)
        estado['chamas'] = chamas
        camada.add_widget(chamas)
        camada.add_widget(aura)
        camada.add_widget(K.RastroLamina(kk, faiscas))
        camada.add_widget(kk)
        camada.add_widget(faiscas)"""),
    ("""        kk.precarregar([P[n] for n in P] + list(M.values()))
        K.preparar_fita()                              # quadros da fita de fogo, aos poucos""",
     """        kk.precarregar([P[n] for n in P] + list(M.values()))"""),
    ("""        kk.precarregar([ban, ban_prep, kai, mug, _com(mug, cresce=0.4)])
        nuvem_u = te * 3
        oficina.pedir_bruto('nuvem', _desenho_nuvem(alt * 0.95, nuvem_u))""",
     """        kai_m = _com(kai, mugetsu=True, olhos='l')
        une_m = K.pose(pernas='base_larga', dx=1, dy=-1, m1=(8, 3), a1=4.0, m2=(7, 1), a2=-4.0, olhos='g',
                       mugetsu=True)
        kk.precarregar([ban, ban_prep, kai, mug, _com(kai, olhos='l'), _com(kai_m, cresce=0.08)])"""),
    # ── KAI! sem a nuvem: estrondo e o reiatsu sobe ─────────────────
    ("""            _fundo(tela, reator=0.5, barra=0.1, dur=0.2)
            quadros = oficina.obter('nuvem')
            if not quadros:
                _no_mugetsu()
                ag.depois(0.5, _revela)
                return
            nuvem = NuvemReiatsu(quadros, nuvem_u, (cx_n, cy_n), dur=1.35,
                                 on_coberto=_no_mugetsu, on_fim=_revela)
            camada.add_widget(nuvem)

        def _no_mugetsu():
            # escondido na nuvem: as espadas viram uma so e ele vira o Mugetsu
            kk.tocar(K.poder(_com(mug, cresce=0.4), n=36, de=0.9), loop=True)
            _fitas(alvo=0.7, aperto=0.6, vel=20.0)
            aura.alvo = 0.8
            _som('fitas')

        def _revela():
            # a nuvem abre do meio: o Mugetsu aparece e o cabelo termina de crescer
            rampa = []
            for f, q in enumerate(K.poder(mug, n=12, de=0.9)):
                rampa.append(dict(q, cresce=round((0.4 + 0.6 * min(1.0, (f + 1) / 10.0)) * 20) / 20.0))
            kk.tocar(rampa, on_fim=lambda: kk.tocar(K.poder(mug, n=36, de=0.9), loop=True))
            _fitas(alvo=1.0, aperto=1.0, vel=14.0)
            aura.alvo = 1.0
            kk.clarao = 0.8
            ag.depois(0.08, lambda: _clarao_boneco(kk, 0.35))
            ax, ay = kk.ancora()
            faiscas.estourar(ax, ay + alt * 0.3, ROXO, n=24, forca=dp(200), tam=ps, gravidade=-dp(120))
            _som('titulo')
            _tremer(12)
            cam[0].ir(1.2, foco=(ax, ay + alt * 0.4), dur=0.5)
            # close: os olhos acendem roxos; depois a escuridao
            ag.depois(0.55, lambda: close_rosto(camada, 'mugetsu', dur=0.95, y_rel=0.8, on_fim=_posiciona))""",
     """            _fundo(tela, reator=0.5, barra=0.1, dur=0.2)
            ag.depois(0.4, _chamas_sobem)

        def _chamas_sobem():
            # o reiatsu roxo explode do chao: chamas sobem em volta dele, o
            # vento levanta cabelo e sobretudo e os olhos acendem
            chamas.alvo = 0.55
            _som('reiatsu')
            kk.tocar(K.poder(_com(kai, olhos='l'), n=36, de=0.9, sobe=1.2, lift=2.2), loop=True)
            kk.empurrar(lift=10, cabelo=6)
            ax, ay = kk.ancora()
            y_pe = ay - kk.extensao()[1]
            faiscas.estourar(ax, y_pe, ROXO, n=30, forca=dp(220), tam=ps, gravidade=-dp(160))
            _anel(camada, (ax, y_pe), ps * 2, ps * 16, 0.4, ROXO, achat=0.3)
            _tremer(10)
            ag.depois(0.5, _queima)

        estado['cresce'] = 0.08

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

        def _queima():
            # a transformacao A MOSTRA: um anel de energia sobe dos pes a
            # cabeca - por cima dele ainda e o Yoru, por baixo ja e o Bankai
            # (o sobretudo rasgado em chamas aparece primeiro, depois o
            # peito, os bracos, a cabeca). O cabelo cresce quando o anel passa
            # do pescoco.
            base_m = _com(kai_m, cresce=0.08)
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
            anel = _AnelEnergia(te * 2)
            camada.add_widget(anel)
            chamas.alvo = 0.8
            _som('absorve')
            dur = 1.45
            t = [0.0]
            cresceu = [False]
            kk.recortar(y0, None)
            kk2.recortar(None, y0)

            def _p(dt):
                t[0] += dt
                s = min(1.0, t[0] / dur)
                e = s * s * (3 - 2 * s)
                y = y0 + (y1 - y0) * e
                yq = math.floor(y / passo) * passo                 # sobe de 2 em 2 pixels
                kk.recortar(yq, None)
                kk2.recortar(None, yq)
                anel.pos_linha(cx_c, yq, larg * (0.75 + 0.25 * math.sin(math.pi * e)), dt)
                if int(t[0] * 60) % 3 == 0:
                    faiscas.estourar(cx_c + random.uniform(-0.5, 0.5) * larg, yq, ROXO, n=2,
                                     forca=dp(70), tam=te * 2, gravidade=-dp(220))
                if not cresceu[0] and yq >= y_pesc:
                    cresceu[0] = True
                    _cabelo_cresce()
                if s >= 1.0:
                    _fim_queima(anel)
                    return False
                return True
            ag.cada(1 / 60., _p)

        def _fim_queima(anel):
            # o Bankai assume: o boneco de cima vira o de baixo
            kk2 = estado.pop('kk2', None)
            if anel.parent is not None:
                anel.parent.remove_widget(anel)
            kk.recortar()
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
            faiscas.estourar(ax, ay + alt * 0.55, ROXO, n=20, forca=dp(160), tam=ps, gravidade=-dp(100))
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
            ag.depois(0.9, lambda: close_rosto(camada, 'mugetsu', dur=0.95, y_rel=0.8, on_fim=_posiciona))"""),
    # a lua some quando ele salta para o meio da frase
    ("""        def _posiciona():
            # sobe para o meio da frase: dali a escuridao vai sair dele
            kk.espelhar = False""", """        def _posiciona():
            # sobe para o meio da frase: dali a escuridao vai sair dele
            lua = estado.pop('lua', None)
            if lua is not None:
                lua.sumir(0.3)
            kk.espelhar = False"""),
    # ── volta ao normal A MOSTRA ────────────────────────────────────
    ("""            hx2, hy2 = kk.ponto_mao(1)
            aura.alvo = 0.0
            _fitas(alvo=0.0)
            dupla = _com(P['dupla'], olhos='s')
            kk.tocar(K.sequencia([(4, _com(dupla, dx=dupla['dx'] + 1, a1=dupla['a1'] + 12,
                                           a2=dupla['a2'] - 12), 'mola'), (1, dupla)]))
            # sai da Bankai: clarao branco e as chamas se desfazem em brilhos
            kk.clarao = 1.0
            ag.depois(0.08, lambda: _clarao_boneco(kk, 0.4))
            ax_m, ay_m = kk.ancora()
            faiscas.estourar(ax_m, ay_m + alt * 0.3, ROXO, n=24, forca=dp(140), tam=ps, gravidade=-dp(200))
            faiscas.estourar(hx2, hy2, BRANCO, n=18, forca=dp(160), tam=ps)
            faiscas.estourar(hx2, hy2, AZUL, n=10, forca=dp(120), tam=ps)
            _anel(camada, (hx2, hy2), ps * 2, ps * 14, 0.35, CIANO)
            _som('separa')
            ag.depois(0.4, _desce)""", """            hx2, hy2 = kk.ponto_mao(1)
            aura.alvo = 0.0
            chamas.alvo = 0.0
            dupla = _com(P['dupla'], olhos='s')
            dupla_m = _com(dupla, mugetsu=True)
            # a lamina se divide nas duas (ainda no Bankai): estalo nas maos
            kk.tocar(K.sequencia([(4, _com(dupla_m, dx=dupla['dx'] + 1, a1=dupla['a1'] + 12,
                                             a2=dupla['a2'] - 12), 'mola'), (1, dupla_m)]))
            kk.impacto()
            faiscas.estourar(hx2, hy2, BRANCO, n=18, forca=dp(160), tam=ps)
            faiscas.estourar(hx2, hy2, AZUL, n=10, forca=dp(120), tam=ps)
            _anel(camada, (hx2, hy2), ps * 2, ps * 14, 0.35, CIANO)
            _som('separa')
            ag.depois(0.22, lambda: _desfaz(dupla, dupla_m))

        def _desfaz(dupla, dupla_m):
            # o anel desce da cabeca aos pes: por cima dele ele ja voltou ao
            # normal, por baixo ainda e o Bankai - as chamas se apagam
            kk2 = K.KiritoPixel(ps=ps)
            kk2.espelhar = kk.espelhar
            i = camada.children.index(kk) if kk in camada.children else 0
            camada.add_widget(kk2, index=i)                     # na frente (o de cima e o normal)
            kk2.ancorar(*kk.ancora())
            kk2.mostrar(dupla)
            kk2._preso = dict(kk._preso)
            ax, ay = kk.ancora()
            esq, baixo, dir_, cima = kk.extensao(_com(dupla, a1=None, a2=None))
            y_alto, y_baixo = ay + cima + te * 10, ay - baixo - te * 3
            cx_c = ax + (dir_ - esq) / 2.0
            larg = (esq + dir_) * 1.05
            passo = te * 2
            anel = _AnelEnergia(te * 2)
            camada.add_widget(anel)
            _som('absorve')
            dur = 0.55
            t = [0.0]
            kk2.recortar(y_alto, None)
            kk.recortar(None, y_alto)

            def _p(dt):
                t[0] += dt
                s = min(1.0, t[0] / dur)
                y = y_alto + (y_baixo - y_alto) * s
                yq = math.floor(y / passo) * passo
                kk2.recortar(yq, None)
                kk.recortar(None, yq)
                anel.pos_linha(cx_c, yq, larg, dt)
                if int(t[0] * 60) % 3 == 0:
                    faiscas.estourar(cx_c + random.uniform(-0.5, 0.5) * larg, yq, ROXO, n=2,
                                     forca=dp(60), tam=te * 2, gravidade=-dp(200))
                if s >= 1.0:
                    kk.recortar()
                    kk.mostrar(dupla)
                    kk.parar()
                    kk._preso = dict(kk2._preso)
                    for w in (kk2, anel):
                        if w.parent is not None:
                            w.parent.remove_widget(w)
                    ag.depois(0.12, _desce)
                    return False
                return True
            ag.cada(1 / 60., _p)"""),
])
print('ok')
