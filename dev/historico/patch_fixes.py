import os
R = r'C:\Users\kirit\travetefocus\app'


def troca(p, a, b, n=1):
    c = open(os.path.join(R, p), encoding='utf-8').read()
    assert c.count(a) == n, (p, a[:80], c.count(a))
    open(os.path.join(R, p), 'w', encoding='utf-8').write(c.replace(a, b))


# ── 1b. um Yoru por vez ─────────────────────────────────────────────
troca('cenas.py', '''class _Mini:
    """Base das cenas curtas do Yoru fora da abertura: camada por cima de
    tudo, o boneco no tamanho certo para o item, faiscas, rastro da lamina,
    a explosao do item, a saida (teleporte) e redes de seguranca."""''', '''# um Yoru por vez: enquanto uma cena curta esta rodando, a proxima espera na
# fila (ou, no carimbo e no WhatsApp, a acao acontece direto, sem ele)
_OCUPADO = {'ate': 0.0, 'fila': []}


def _yoru_livre():
    return time.time() >= _OCUPADO['ate']


def _yoru_ocupa(seg):
    _OCUPADO['ate'] = time.time() + seg


def _yoru_solta():
    _OCUPADO['ate'] = 0.0
    if _OCUPADO['fila']:
        prox = _OCUPADO['fila'].pop(0)
        Clock.schedule_once(lambda dt: prox(), 0.08)


def _na_fila(fn):
    """True se o Yoru esta ocupado (fn foi para a fila)."""
    if _yoru_livre():
        return False
    _OCUPADO['fila'].append(fn)
    return True


class _Mini:
    """Base das cenas curtas do Yoru fora da abertura: camada por cima de
    tudo, o boneco no tamanho certo para o item, faiscas, rastro da lamina,
    a explosao do item, a saida (teleporte) e redes de seguranca."""''')
troca('cenas.py', '''        if destruir:
            Clock.schedule_once(lambda dt: self.explodir(), seguranca)
        Clock.schedule_once(lambda dt: _remover_da_janela(self.cam), seguranca + 2.5)''', '''        if destruir:
            Clock.schedule_once(lambda dt: self.explodir(), seguranca)
        _yoru_ocupa(seguranca + 2.5)
        Clock.schedule_once(lambda dt: self._fim_camada(), seguranca + 2.5)''')
troca('cenas.py', '''    def _limpa(self):
        self.k.parar()
        Clock.schedule_once(lambda dt: _remover_da_janela(self.cam), 0.4)''', '''    def _limpa(self):
        self.k.parar()
        Clock.schedule_once(lambda dt: self._fim_camada(), 0.4)

    def _fim_camada(self):
        if self.cam.parent is not None or _OCUPADO['ate']:
            _remover_da_janela(self.cam)
            _yoru_solta()''')
# ── G. Yoru maior nas cenas curtas (arredonda para cima: 3 px por pixel no celular) ──
troca('cenas.py', '''        alt_boneco = max(dp(62), min(self.rh * 1.7, dp(96), H * 0.15))
        self.ps = K.ps_inteiro(alt_boneco * 1.12 / 31.0)
        self.te = self.ps / float(K.R)''', '''        alt_boneco = max(dp(62), min(self.rh * 1.7, dp(96), H * 0.15))
        self.ps = max(K.R, K.R * int(math.ceil(alt_boneco * 1.12 / 31.0 / K.R - 0.15)))
        self.te = self.ps / float(K.R)''')
troca('cenas.py', '''    if tipo == 'iai':
        return _apagar_iai(alvo, on_fim)''', '''    if tipo is not None and _na_fila(lambda: kirito_fatiar(alvo, on_fim, tipo)):
        return
    if tipo == 'iai':
        return _apagar_iai(alvo, on_fim)''')
troca('cenas.py', '''    feito = _Uma(on_impacto)
    try:
        s = _Mini(alvo, None, seguranca=3.0, destruir=False)
        Clock.schedule_once(lambda dt: feito(), 1.6)            # o +XP sai de qualquer jeito''', '''    feito = _Uma(on_impacto)
    if not _yoru_livre():
        feito()                                                 # ja tem um Yoru em cena: so o +XP
        return
    try:
        s = _Mini(alvo, None, seguranca=3.0, destruir=False)
        Clock.schedule_once(lambda dt: feito(), 1.6)            # o +XP sai de qualquer jeito''')
troca('cenas.py', '''    o brilho no olho; depois some."""
    try:
        s = _Mini(alvo, None, seguranca=5.0, destruir=False)''', '''    o brilho no olho; depois some."""
    if _na_fila(lambda: kirito_vitoria(alvo)):
        return
    try:
        s = _Mini(alvo, None, seguranca=5.0, destruir=False)''')
troca('cenas.py', '''    feito = _Uma(on_fim)
    try:
        s = _Mini(alvo, None, seguranca=3.5, destruir=False)
        Clock.schedule_once(lambda dt: feito(), 2.6)             # o WhatsApp abre de qualquer jeito''', '''    feito = _Uma(on_fim)
    if not _yoru_livre():
        feito()                                                  # ja tem um Yoru em cena: abre direto
        return
    try:
        s = _Mini(alvo, None, seguranca=3.5, destruir=False)
        Clock.schedule_once(lambda dt: feito(), 2.6)             # o WhatsApp abre de qualquer jeito''')
troca('cenas.py', '''    fim = _Uma(on_fim)
    camada = [None]
    try:
        W, H = Window.size
        y_min, y_max = (area_lista[1], area_lista[3]) if area_lista else (0.0, float(H))''', '''    if _na_fila(lambda: kirito_wipe(widgets, on_fim, grafico, area_lista)):
        return
    _yoru_ocupa(16.0)
    fim = _Uma(on_fim)
    camada = [None]
    try:
        W, H = Window.size
        y_min, y_max = (area_lista[1], area_lista[3]) if area_lista else (0.0, float(H))''')
troca('cenas.py', '''        def _acabou():
            k.parar()
            _remover_da_janela(cam)
            fim()

        _materializar(k, cam, faiscas, dur=0.32, on_fim=_saca)

        def _seguranca(dt):
            _remover_da_janela(cam)
            fim()''', '''        def _acabou():
            k.parar()
            _remover_da_janela(cam)
            _yoru_solta()
            fim()

        _materializar(k, cam, faiscas, dur=0.32, on_fim=_saca)

        def _seguranca(dt):
            _remover_da_janela(cam)
            if cam.parent is None and _OCUPADO['ate']:
                _yoru_solta()
            fim()''')
troca('cenas.py', '''    except Exception as e:
        print(f"[wipe] ignorado: {e}")
        _remover_da_janela(camada[0])
        fim()''', '''    except Exception as e:
        print(f"[wipe] ignorado: {e}")
        _remover_da_janela(camada[0])
        _yoru_solta()
        fim()''')

# ── 1a. voz do WIPE: "Sutabasuto..." inteiro antes do "Sutorimu!" ──
troca('cenas.py', '''                              (2, _com(P['dupla'], olhos='s'), 'segura'),
                               (8, _com(P['dupla'], olhos='l'), 'segura'),
                               (1, _com(P['dupla'], olhos='l'))])

            def _q(i):
                if i == 6:
                    mx, my = k.ponto_mao(2)
                    faiscas.estourar(mx, my, AZUL, n=16, forca=dp(120), tam=ps)
                    _som('sacar')
                elif i == 12:
                    _som('voz_stream')''', '''                              (2, _com(P['dupla'], olhos='s'), 'segura'),
                               (28, _com(P['dupla'], olhos='s'), 'segura'),
                               (9, _com(P['dupla'], olhos='l'), 'segura'),
                               (1, _com(P['dupla'], olhos='l'))])

            def _q(i):
                if i == 6:
                    mx, my = k.ponto_mao(2)
                    faiscas.estourar(mx, my, AZUL, n=16, forca=dp(120), tam=ps)
                    _som('sacar')
                elif i == 40:                        # a fala "Sutabasuto..." ja acabou
                    _som('voz_stream')
                    k.empurrar(capa=-8, cabelo=-6)''')

# ── 1c. estocada: o popup fica travado enquanto ele ataca ──
troca('telas/memorias.py', '''            from cenas import kirito_fatiar
            btn_a.disabled = True
            kirito_fatiar(caixa, _executar_delete, tipo='estocada')''', '''            from cenas import kirito_fatiar
            for b in (btn_a, btn_f, btn_zap, btn_salvar_data):
                b.disabled = True
            pop.auto_dismiss = False                 # nao fecha no meio do golpe
            kirito_fatiar(caixa, _executar_delete, tipo='estocada')''')

# ── 1d. carimbo: espera o item novo terminar de entrar na lista ──
troca('telas/registro.py', '''        Clock.schedule_once(_carimbo, 0.2)''', '''        Clock.schedule_once(_carimbo, 0.42)''')
print('ok')
