"""Motor da animacao com cara de pixel art desenhada quadro a quadro:
- poses do meio "em 2s" (cada desenho fica 2 quadros: ~15 desenhos/s);
- a mao gira em ARCO em volta do ombro (nao anda em linha reta);
- cabelo e sobretudo chegam DEPOIS do corpo, cada um no seu tempo;
- rastro (afterimage) com a pose de verdade em cor chapada, em degraus;
- quadro de impacto nitido (branco inteiro, 2 quadros), nada de cinza;
- pose de bola (mortal) para girar de 90 em 90 graus."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'kirito.py'), [
    # ── mao em arco ─────────────────────────────────────────────────
    ("""def misturar(p0, p1, t, tl=None):""", """def _mao_arco(a, b, t):
    \"\"\"Mao de a para b girando no OMBRO (m1/m2 ja sao medidos a partir
    dele): o braco varre um arco, como numa animacao desenhada, em vez de a
    mao andar em linha reta pelo meio do corpo.\"\"\"
    ra, rb = math.hypot(a[0], a[1]), math.hypot(b[0], b[1])
    if ra < 1.0 or rb < 1.0:
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    aa, ab = math.atan2(a[1], a[0]), math.atan2(b[1], b[0])
    d = (ab - aa + math.pi) % (2 * math.pi) - math.pi
    if abs(abs(d) - math.pi) < 0.15:               # meia volta exata: vai por cima
        d = abs(d)
    ang = aa + d * t
    r = ra + (rb - ra) * t
    return (r * math.cos(ang), r * math.sin(ang))


def misturar(p0, p1, t, tl=None):"""),
    ("""    for k in ('m1', 'm2'):
        a, b = p0[k], p1[k]
        if a is not None and b is not None:
            q[k] = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    l0, l1 = p0['pernas'], p1['pernas']""", """    for k in ('m1', 'm2'):
        a, b = p0[k], p1[k]
        if a is not None and b is not None:
            q[k] = _mao_arco(a, b, t)
    l0, l1 = p0['pernas'], p1['pernas']"""),
    # ── poses do meio em 2s ─────────────────────────────────────────
    ("""def sequencia(chaves):
    \"\"\"chaves: [(quadros, pose) ou (quadros, pose, curva), ...] -> lista de
    poses (1 por quadro). `quadros` = duracao do trecho ate a proxima chave;
    `curva` = como o tempo corre nele (ver _facil; padrao 'suave'). Campos
    numericos e maos interpolam; as pernas passam por um quadro do meio.\"\"\"
    out = []
    for i, ch in enumerate(chaves):
        n, p0 = ch[0], ch[1]
        curva = ch[2] if len(ch) > 2 else 'suave'
        p1 = chaves[i + 1][1] if i + 1 < len(chaves) else p0
        n = max(1, int(n))
        for f in range(n):
            tl = f / float(n)
            if p1 is p0 or curva == 'segura' or f == 0:
                out.append(dict(p0))
            else:
                out.append(misturar(p0, p1, _facil(curva, tl), tl))
    return out""", """EM_DOIS = 2        # desenhos do meio "em 2s": cada um fica 2 quadros (15 por segundo)


def sequencia(chaves, passo=None):
    \"\"\"chaves: [(quadros, pose) ou (quadros, pose, curva), ...] -> lista de
    poses (1 por quadro, 30 por segundo). `quadros` = duracao do trecho ate
    a proxima chave; `curva` = como o tempo corre nele (ver _facil; padrao
    'suave'). Como numa animacao desenhada, os desenhos do meio ficam 2
    quadros cada (`passo`): a chave segura e o movimento anda em degraus
    (trechos de 3 quadros ou menos - o golpe rapido - vao de 1 em 1).
    Numeros interpolam, as maos giram no ombro e as pernas passam por um
    quadro do meio.\"\"\"
    passo = EM_DOIS if passo is None else max(1, int(passo))
    out = []
    for i, ch in enumerate(chaves):
        n, p0 = ch[0], ch[1]
        curva = ch[2] if len(ch) > 2 else 'suave'
        p1 = chaves[i + 1][1] if i + 1 < len(chaves) else p0
        n = max(1, int(n))
        pa = passo if n > 3 else 1
        ult = None
        for f in range(n):
            fs = f - (f % pa)
            if p1 is p0 or curva == 'segura' or fs == 0:
                out.append(dict(p0))
            elif fs == ult:
                out.append(dict(out[-1]))
            else:
                tl = fs / float(n)
                out.append(misturar(p0, p1, _facil(curva, tl), tl))
            ult = fs
    return out"""),
    # ── cabeca com fase propria (o cabelo anda no tempo dele) ───────
    ("""    cabeca = None if _cabeca_no_corpo(q) else (
        'cabeca', q['olhos'], q4(q['cabelo']), q4(q.get('sobe', 0.0)), round(q.get('fase', 0.0) or 0.0, 3),
        mug, round(q.get('cresce', 1.0) or 0.0, 2) if mug else None)""",
     """    fcab = q.get('fase_cab', q.get('fase', 0.0))
    cabeca = None if _cabeca_no_corpo(q) else (
        'cabeca', q['olhos'], q4(q['cabelo']), q4(q.get('sobe', 0.0)), round(fcab or 0.0, 3),
        mug, round(q.get('cresce', 1.0) or 0.0, 2) if mug else None)"""),
    ("""    if camada == 'cabeca':
        _cabeca5(px, p['olhos'], 0, 0, cb, sobe, fase, cresce)""",
     """    if camada == 'cabeca':
        fase = p.get('fase_cab', fase) or 0.0
        _cabeca5(px, p['olhos'], 0, 0, cb, sobe, fase, cresce)"""),
    # ── fisica "travada" em batidas: cada camada no seu tempo ────────
    ("""        self._m_a = {1: None, 2: None}
        self._ult_base = None""", """        self._m_a = {1: None, 2: None}
        self._ult_base = None
        # o que a fisica mostra fica preso em batidas (como desenhos em 2s):
        # o sobretudo troca num tique, o cabelo no outro, a cabeca a cada 2 -
        # o corpo vai primeiro e o resto chega depois, cada um no seu tempo
        self._batida = 0
        self._preso = {'capa': 0.0, 'lift': 0.0, 'fase': 0.0, 'cabelo': 0.0, 'fase_cab': 0.0,
                       'hx': 0, 'hy': 0}"""),
    ("""        q = dict(b)
        q['capa'] = b['capa'] + self._m_capa.x
        q['cabelo'] = b['cabelo'] + self._m_cab.x
        q['lift'] = b['lift'] + self._m_lift.x
        q['fase'] = (int(self._fase * 6) % 6) / 6.0
        # cabeca: +-1 px de atraso
        q['hx'] = int(round(max(-1.0, min(1.0, self._m_hx.x))))
        q['hy'] = int(round(max(-1.0, min(1.0, self._m_hy.x))))""",
     """        q = dict(b)
        pr = self._preso
        q['capa'] = b['capa'] + pr['capa']
        q['cabelo'] = b['cabelo'] + pr['cabelo']
        q['lift'] = b['lift'] + pr['lift']
        q['fase'] = pr['fase']
        q['fase_cab'] = pr['fase_cab']
        # cabeca: +-1 px de atraso
        q['hx'] = pr['hx']
        q['hy'] = pr['hy']"""),
    ("""            vel = math.hypot(frente, cima)
            self._fase = (self._fase + dt * (1.6 + min(3.0, vel / 120.0))) % 1.0
            self._camadas(dt, frente, cima)
            self._desenhar()""", """            vel = math.hypot(frente, cima)
            self._fase = (self._fase + dt * (1.6 + min(3.0, vel / 120.0))) % 1.0
            self._camadas(dt, frente, cima)
            self._travar_batida()
            self._desenhar()"""),
    ("""    def _camadas(self, dt, frente, cima):""", """    def _travar_batida(self):
        \"\"\"Copia o estado das molas para o desenho so em algumas batidas
        (a fisica roda a 30/s): o sobretudo muda nas batidas pares, o cabelo
        nas impares (chega depois do corpo e do sobretudo), a cabeca a cada 2.\"\"\"
        self._batida = (self._batida + 1) % 6
        pr = self._preso
        f6 = (int(self._fase * 6) % 6) / 6.0
        if self._batida % 2 == 0:
            pr['capa'] = self._m_capa.x
            pr['lift'] = self._m_lift.x
            pr['fase'] = f6
        else:
            pr['cabelo'] = self._m_cab.x
            pr['fase_cab'] = f6
        if self._batida % 2 == 1:
            pr['hx'] = int(round(max(-1.0, min(1.0, self._m_hx.x))))
            pr['hy'] = int(round(max(-1.0, min(1.0, self._m_hy.x))))

    def _camadas(self, dt, frente, cima):"""),
    # ── impacto nitido ──────────────────────────────────────────────
    ("""        self._luz_imp = 1.0
        self.clarao = 0.9 if forte else 0.45
        t = [0.0]

        def _p(dt):
            t[0] += dt
            if getattr(self, 'clarao_preso', False):
                return False                        # um quadro de impacto esta usando a silhueta
            self.clarao = max(0.0, (0.9 if forte else 0.45) * (1 - t[0] / 0.07))
            return t[0] < 0.07
        Clock.schedule_interval(_p, 1 / 60.)""", """        self._luz_imp = 1.0
        if getattr(self, 'clarao_preso', False):
            return
        # quadro de impacto: o boneco inteiro branco e chapado por 2 quadros
        # (3 no forte) e volta de uma vez - nada de cinza meio transparente
        self.clarao = 1.0
        n = [3 if forte else 2]

        def _p(dt):
            if getattr(self, 'clarao_preso', False):
                return False                        # um quadro de impacto esta usando a silhueta
            n[0] -= 1
            if n[0] <= 0:
                self.clarao = 0.0
                return False
            return True
        Clock.schedule_interval(_p, 1 / 60.)"""),
    # ── rastro: pose de verdade, cor chapada, em degraus ────────────
    ("""    def fantasma(self, cor=(0.0, 0.85, 1.0), alfa=0.36, duracao=0.16):
        \"\"\"Afterimage: silhueta pontilhada (metade dos pixels) da pose atual,
        bem curta - so uma indicacao de velocidade.\"\"\"""",
     """    def fantasma(self, cor=None, alfa=0.5, duracao=0.12):
        \"\"\"Afterimage: a silhueta da pose atual em cor chapada, que some em
        3 degraus (sem pontilhado nem fade liso) - so uma indicacao de
        velocidade. Sem cor: ciano (roxo no Bankai).\"\"\"
        if cor is None:
            cor = (0.66, 0.36, 1.0) if self._base.get('mugetsu') else (0.0, 0.78, 1.0)""",),
    ("""                        tex, rec = textura_camada(self._pose, qual, ch, silhueta=True, xadrez=True)""",
     """                        tex, rec = textura_camada(self._pose, qual, ch, silhueta=True)"""),
    ("""            def _some(dt):
                try:
                    t[0] += dt
                    k = min(1.0, t[0] / duracao)
                    cor_sil.a = alfa * (1 - k)
                    if k >= 1:""", """            def _some(dt):
                try:
                    t[0] += dt
                    k = min(1.0, t[0] / duracao)
                    cor_sil.a = alfa * (1.0 if k < 0.34 else (0.55 if k < 0.67 else 0.25))
                    if k >= 1:"""),
    # ── pose de bola para o mortal ──────────────────────────────────
    ("""def esticado(p):""", """def bola(p):
    \"\"\"Mortal: todo encolhido (joelhos no peito, bracos junto das pernas,
    cabeca para a frente) - a pose que gira de 90 em 90 graus no ar.\"\"\"
    q = encolhido(p)
    q['m1'] = (3.0, -3.0)
    if q.get('m2') is not None:
        q['m2'] = (1.0, -3.5)
    q['incl'] = 1
    q['lift'] = max(q.get('lift', 0.0), 0.8)
    return q


def esticado(p):"""),
])
print('ok')
