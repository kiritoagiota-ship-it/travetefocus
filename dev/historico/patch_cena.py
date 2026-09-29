import os
AQUI = os.path.dirname(__file__)
p = r'C:\Users\kirit\travetefocus\app\cenas.py'
s = open(p, encoding='utf-8').read()


def troca(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:90], s.count(a))
    s = s.replace(a, b)


# ── o casulo (antes da onda do getsuga) ──
casulo = open(os.path.join(AQUI, 'casulo.txt'), encoding='utf-8').read()
casulo = casulo.replace("                n_pts = int((alt * h + 2 * math.pi * voltas * rx * h) / te) + 2",
                        "                n_pts = int((alt * h + 2 * math.pi * voltas * rx * h) / passo * 1.3) + 2")
troca('class _OndaGetsuga(Widget):', casulo + 'class _OndaGetsuga(Widget):')

# ── fusao -> casulo -> estouro na forma Mugetsu ──
troca('''        def _flash_fusao():
            hx2, hy2 = kk.ponto_mao(1)
            jx, jy = hx2, hy2 + 6 * ps                 # onde as laminas se encontram
            # segura a espada fundida no alto, tremendo com o reiatsu (loop
            # ate absorver o infinito)
            # BANKAI: fica todo branco um instante e volta na forma Mugetsu
            kk.tocar(K.poder(_com(M['fund_alto'], olhos='s'), n=36, de=0.9), loop=True)
            kk.clarao = 1.0
            ag.depois(0.12, lambda: _clarao_boneco(kk, 0.5))
            ax_m, ay_m = kk.ancora()
            faiscas.estourar(ax_m, ay_m, ROXO, n=30, forca=dp(200), tam=ps, gravidade=-dp(120))
            _anel(camada, (ax_m, ay_m), ps * 3, ps * 30, 0.6, ROXO, esp=dp(5))
            faiscas.estourar(jx, jy, BRANCO, n=26, forca=dp(220), tam=ps)
            faiscas.estourar(jx, jy, AZUL, n=16, forca=dp(160), tam=ps)
            _anel(camada, (jx, jy), ps * 2, ps * 22, 0.45, CIANO, esp=dp(4))
            _brilho_tela(camada, 0.45, 0.25)
            _som('fusao')
            _tremer(12)
            kk.pausar(0.1)
            kk.empurrar(cabelo=10, lift=8)
            aura.alvo = 0.35
            nome = estado.get('nome')
            if nome is not None:
                nome.parte2()
                ag.depois(1.1, nome.sumir)
            ag.depois(0.7, _sugar)''', '''        def _flash_fusao():
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
            # o reiatsu roxo sobe do chao em fitas que giram em volta dele e
            # fecham um casulo
            estado['casulo'] = _Casulo(kk, camada, t_sobe=0.8, t_fecha=0.45)
            _som('carga')
            t = [0.0]

            def _vento(dt):
                t[0] += dt
                if t[0] > 1.25:
                    return False
                kk.empurrar(lift=1.8, cabelo=1.5, capa=-1.2)
                if random.random() < 0.5:
                    ax2, ay2 = kk.ancora()
                    faiscas.estourar(ax2 + random.uniform(-1, 1) * 9 * ps, ay2 - 10 * ps, ROXO, n=1,
                                     forca=dp(30), tam=max(2, ps * 0.6), gravidade=-dp(260))
                return True
            ag.cada(0.06, _vento)
            ag.depois(1.3, _estoura_casulo)

        def _estoura_casulo():
            # BANKAI: o casulo estoura em pedacos e ele aparece na forma
            # Mugetsu (sobretudo longo rasgado, ombreira, faixas e chamas
            # roxas), com o cabelo crescendo em etapas ate os joelhos
            c = estado.get('casulo')
            if c is not None:
                c.estourar()
            base = _com(M['fund_alto'], olhos='s')
            etapas = (0.12, 0.12, 0.12, 0.3, 0.3, 0.3, 0.48, 0.48, 0.48, 0.64, 0.64, 0.78, 0.78, 0.9, 1.0)
            seq = []
            for i, q in enumerate(K.poder(base, n=len(etapas), de=0.9)):
                q = dict(q)
                q['cresce'] = etapas[i]
                seq.append(q)
            kk.tocar(seq, on_fim=lambda: kk.tocar(K.poder(base, n=36, de=0.9), loop=True))
            kk.clarao = 1.0
            ag.depois(0.12, lambda: _clarao_boneco(kk, 0.5))
            ax_m, ay_m = kk.ancora()
            faiscas.estourar(ax_m, ay_m, ROXO, n=30, forca=dp(220), tam=ps, gravidade=-dp(120))
            faiscas.estourar(ax_m, ay_m + alt * 0.3, BRANCO, n=14, forca=dp(180), tam=ps)
            _anel(camada, (ax_m, ay_m), ps * 3, ps * 32, 0.6, ROXO, esp=dp(5))
            _brilho_tela(camada, 0.45, 0.25, (0.85, 0.75, 1.0))
            _som('absorve')
            _tremer(14)
            kk.pausar(0.1)
            kk.empurrar(cabelo=12, lift=8, capa=-10)
            ag.depois(0.9, _sugar)''')

# ── golpe final: a lamina grava cada letra da frase ao passar ──
troca('''            ag.depois(0.42 * frac, lambda: (titulo.revelar(i0, i1, dur=0.06),
                                            faiscas.estourar(cx5, cy, BRANCO, n=24, forca=dp(260), tam=ps)))''',
      '''            ag.depois(0.42 * frac, lambda: (titulo.revelar(i0, i1, dur=0.06),
                                            faiscas.estourar(cx5, cy, BRANCO, n=24, forca=dp(260), tam=ps)))
            # a lamina "grava" a frase: cada letra acende quando o corte passa
            # por ela (branco -> roxo) e solta faisquinhas
            ox_g, _ = titulo._origem()
            for li, letra in enumerate(texto):
                if not letra.strip():
                    continue
                xl = ox_g + (titulo._larg[li] + titulo._larg[li + 1]) / 2.0
                fr = max(0.0, min(1.0, (xl - xr0) / max(1.0, xr1 - xr0)))
                ag.depois(0.42 * fr + 0.02, lambda li=li, xl=xl: (
                    titulo.gravar(li, li + 1),
                    faiscas.estourar(xl, cy, random.choice((ROXO, BRANCO, AZUL)), n=4,
                                     forca=dp(120), tam=max(2, ps * 0.7), gravidade=dp(200))))''')

# ── TituloLuz.gravar ──
troca('''    def pulsar(self, dur=0.85):''', '''    def gravar(self, i0, i1, cor=(0.78, 0.55, 1.0), dur=0.45):
        """O corte do golpe final passa por estas letras: elas saltam um
        pouco e acendem branco, puxam para o roxo e voltam ao normal (a
        lamina 'grava' a frase)."""
        try:
            ox, oy = self._origem()
            x0, x1 = self._larg[i0], self._larg[i1]
            w = max(1.0, x1 - x0)
            with self.canvas.after:
                c = Color(1, 1, 1, 1)
                r = Rectangle(texture=self._tex.get_region(x0, 0, w, self.th), size=(w, self.th))
        except Exception:
            return
        t = [0.0]

        def _p(dt):
            try:
                t[0] += dt
                u = min(1.0, t[0] / dur)
                esc = 1.0 + 0.28 * (1 - u) ** 2              # salta e assenta
                ox2, oy2 = self._origem()
                cxl, cyl = ox2 + x0 + w / 2.0, oy2 + self.th / 2.0
                r.size = (w * esc, self.th * esc)
                r.pos = (cxl - w * esc / 2.0, cyl - self.th * esc / 2.0)
                k = min(1.0, u * 2.5)
                c.rgba = (1 + (cor[0] - 1) * k, 1 + (cor[1] - 1) * k, 1 + (cor[2] - 1) * k,
                          1.0 if u < 0.5 else max(0.0, (1 - u) * 2))
                if u >= 1:
                    self.canvas.after.remove(c)
                    self.canvas.after.remove(r)
                    return False
            except Exception:
                return False
        Clock.schedule_interval(_p, 1 / 60.)

    def pulsar(self, dur=0.85):''')

# ── aura da espada: azulada misturada com roxo na forma Mugetsu ──
troca('''            k.luz = self.forca                          # a energia ilumina o corpo''',
      '''            k.luz = self.forca                          # a energia ilumina o corpo
            mug = p.get('mugetsu')
            if mug != getattr(self, '_mug', None):      # Mugetsu: aura roxa por fora, azul por dentro
                self._mug = mug
                self._c1.rgb = (0.52, 0.26, 1.0) if mug else (0.2, 0.85, 1.0)
                self._c2.rgb = (0.55, 0.72, 1.0) if mug else (0.85, 1.0, 1.0)''')
troca('''                cor = (0.1, 0.3, 0.6) if atras else random.choice((CIANO, BRANCO, (0.12, 0.25, 0.6)))''',
      '''                if mug:
                    cor = (0.28, 0.12, 0.55) if atras else random.choice((ROXO, AZUL, (0.85, 0.75, 1.0)))
                else:
                    cor = (0.1, 0.3, 0.6) if atras else random.choice((CIANO, BRANCO, (0.12, 0.25, 0.6)))''')
open(p, 'w', encoding='utf-8').write(s)
print('ok')
