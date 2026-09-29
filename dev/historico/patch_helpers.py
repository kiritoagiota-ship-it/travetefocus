import sys
sys.path.insert(0, __file__.rsplit('\\', 1)[0])
from p import patch

patch(r'C:\Users\kirit\travetefocus\app\helpers.py', [
    ("""# ─── Vibração Android ────────────────────────────────────────────────────────
def vibrar(duracao_ms=80):
    \"\"\"Vibra o celular no Android. No-op em outras plataformas.\"\"\"
    try:
        from kivy.utils import platform as _plat
        if _plat == 'android':
            from plyer import vibrator
            vibrator.vibrate(duracao_ms / 1000.0)
    except Exception:
        pass  # plyer não disponível ou permissão negada
""", """# ─── Vibração Android ────────────────────────────────────────────────────────
def vibrar(duracao_ms=80):
    \"\"\"Vibra o celular por `duracao_ms` (respeita o liga/desliga do app).
    Para as respostas curtinhas use tatil.tecla/confirmar/erro/forte.\"\"\"
    try:
        import tatil
        tatil.pulso(duracao_ms)
    except Exception:
        pass


# ─── Sugestões de peças (teclado de letras do registro) ─────────────────────
def sugestoes_pecas(texto=''):
    \"\"\"Nomes de peças já usadas (mais recentes primeiro, sem repetir),
    filtrados pelo que já foi digitado (sem ligar para acento/maiúscula):
    primeiro as que começam com o texto, depois as que o contêm.\"\"\"
    from efeitos import _sem_acento
    app = App.get_running_app()
    fontes = [r[0] for r in reversed(list(getattr(app, 'registros', []))) if r]
    for m in reversed(list(getattr(app, 'memorias', []))):
        fontes += [it[0] for it in m.get('itens', []) if it]
    chave = _sem_acento(texto.strip())
    vistos, comeca, contem = set(), [], []
    for nome in fontes:
        nome = str(nome).strip()
        k = _sem_acento(nome)
        if not nome or k in vistos:
            continue
        vistos.add(k)
        if not chave:
            comeca.append(nome)
        elif k == chave:
            continue
        elif k.startswith(chave):
            comeca.append(nome)
        elif chave in k:
            contem.append(nome)
    return comeca + contem
"""),
    # popup: sobe a caixa inteira acima do teclado quando couber (o botao
    # de confirmar fica embaixo do campo e continua a vista)
    ("""    try:
        _, iy = inp.to_window(inp.x, inp.y)
        falta = (kb.top + dp(12)) - iy
        if falta <= 0:
            return
        caixa = _caixa_do_popup(inp)
        if caixa is not None:""", """    try:
        _, iy = inp.to_window(inp.x, inp.y)
        caixa = _caixa_do_popup(inp)
        if caixa is not None:
            _, cy0 = caixa.to_window(caixa.x, caixa.y)
            if caixa.height < Window.height - dp(18) - kb.top:
                iy = cy0                      # cabe inteira: sobe a caixa toda
        falta = (kb.top + dp(12)) - iy
        if falta <= 0:
            return
        if caixa is not None:"""),
    ("""def anexar_teclado(inp, tipo='letras', decimal=False):
    \"\"\"
    Teclado customizado SAO.
    - Passa 'fechar' callback para _TecladoBase — OK fecha sem crash
    - Toque fora do teclado tambem fecha
    - Supressao do teclado Android via _bind_keyboard no InputHolografico
    \"\"\"""", """def anexar_teclado(inp, tipo='letras', decimal=False, sugestoes=None):
    \"\"\"
    Teclado customizado SAO.
    - Passa 'fechar' callback para _TecladoBase — OK fecha sem crash
    - Toque fora do teclado tambem fecha
    - Supressao do teclado Android via _bind_keyboard no InputHolografico
    - sugestoes(texto) -> nomes: linha de sugestoes no teclado de letras
    \"\"\""""),
    ("""            kb = (Kls(target=inst, fechar=_esconder, decimal=decimal)
                  if tipo == 'numeros'
                  else Kls(target=inst, fechar=_esconder))
            larg       = largura_coluna()
            kb.size    = (larg, dp(252))""", """            kb = (Kls(target=inst, fechar=_esconder, decimal=decimal)
                  if tipo == 'numeros'
                  else Kls(target=inst, fechar=_esconder, sugestoes=sugestoes))
            larg       = largura_coluna()
            kb.size    = (larg, kb.height)"""),
    # janela do XP: o campo primeiro, o botao embaixo
    ("""    for w in [lbl_info, btn, inp, lbl_preview]:  # btn antes do inp
        caixa.add_widget(w)""", """    for w in [lbl_info, inp, lbl_preview, btn]:  # o teclado sobe a caixa inteira
        caixa.add_widget(w)"""),
])
print('ok')
