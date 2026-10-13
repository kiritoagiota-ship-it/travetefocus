"""Assa os quadros do Yoru (desenha no PC o que as cenas usam; o celular so
abre o arquivo pronto).
uso:
  python assar.py gravar   roda as cenas (abertura, tour, cenas curtas) e anota o que pedem
  python assar.py assar    desenha tudo e escreve tf_repo/yoru_quadros.bin
"""
import os, sys, json, zlib, subprocess, time
AQUI = os.path.dirname(os.path.abspath(__file__))
SCR = r'C:\Users\kirit\travetefocus\ferramentas\saida_testes'            # o que os testes gravam fica fora do codigo
os.makedirs(SCR, exist_ok=True)
REPO = r'C:\Users\kirit\travetefocus\app'
GRAV = os.path.join(SCR, 'gravados.json')


def gravar():
    env = dict(os.environ, YORU_GRAVA=GRAV, PYTHONIOENCODING='utf-8', KIVY_LOG_MODE='PYTHON')
    bash = r'C:\Program Files\Git\bin\bash.exe'
    rodadas = [
        ('tour completo', [bash, os.path.join(AQUI, 'tour.sh'), '720', '1560', os.path.join(SCR, 'gr_tour1'), '1.75'],
         dict(FOTOS='0')),
        ('abertura 2', [bash, os.path.join(AQUI, 'tour.sh'), '720', '1560', os.path.join(SCR, 'gr_tit2'), '1.75'],
         dict(FOTOS='0', SO_TITULO='1')),
        ('abertura 3', [bash, os.path.join(AQUI, 'tour.sh'), '1080', '2340', os.path.join(SCR, 'gr_tit3'), '2.625'],
         dict(FOTOS='0', SO_TITULO='1')),
        ('entrada rapida', [bash, os.path.join(AQUI, 'tour.sh'), '720', '1560', os.path.join(SCR, 'gr_rap'), '1.75'],
         dict(FOTOS='0', RAPIDA='1', TOUR_PY=os.path.join(AQUI, 'tela_teste.py'))),
    ]
    for i in range(2):                    # o Yoru espiando a caixa da senha (senha errada e certa)
        rodadas.append(('senha %d' % (i + 1),
                        [bash, os.path.join(AQUI, 'tour.sh'), '720', '1560', os.path.join(SCR, 'gr_pin%d' % i), '1.75'],
                        dict(CENA='pin', CADA='0', TOUR_PY=os.path.join(AQUI, 'filme_cenas.py'))))
    # as cenas curtas dentro do app de verdade (o lugar e o tamanho mudam os desenhos pedidos)
    rodadas.append(('cenas no app', [bash, os.path.join(AQUI, 'tour.sh'), '720', '1560', os.path.join(SCR, 'gr_app'), '1.75'],
                    dict(CENA='app', CADA='0', TOUR_PY=os.path.join(AQUI, 'filme_cenas.py'))))
    for i, v in enumerate(('1,0,1', '40,30,14')):
        rodadas.append(('casos extremos %d' % (i + 1),
                        [bash, os.path.join(AQUI, 'tour.sh'), '720', '1560', os.path.join(SCR, 'gr_varre%d' % i), '1.75'],
                        dict(CENA='varre', VARRE=v, CADA='0', TOUR_PY=os.path.join(AQUI, 'filme_cenas.py'))))
    cenas = 'iai,estocada,x,carimbo,vitoria,pergaminho,nivel,meta'
    for i in range(3):
        rodadas.append(('cenas curtas %d' % (i + 1),
                        [sys.executable, '-u', os.path.join(AQUI, 'golpes_teste.py'), '720', '1560',
                         os.path.join(SCR, 'gr_mini%d' % i), '1.75', cenas], dict(PASSO_FOTO='1.0')))
    for nome, cmd, extra in rodadas:
        t = time.time()
        e = dict(env, **extra)
        r = subprocess.run(cmd, env=e, capture_output=True, text=True, encoding='utf-8', errors='replace')
        n = len(json.load(open(GRAV, encoding='utf-8'))) if os.path.exists(GRAV) else 0
        print(f'{nome}: rc={r.returncode} {time.time() - t:.0f}s  pedidos acumulados={n}')


def assar():
    sys.path.insert(0, REPO)
    os.environ['KIVY_NO_ARGS'] = '1'
    os.environ['KIVY_LOG_MODE'] = 'PYTHON'
    import kirito as K
    K._ASSADO.clear()                      # desenha tudo de verdade
    grav = json.load(open(GRAV, encoding='utf-8'))

    def pose(q):
        return {k: (tuple(v) if isinstance(v, list) else v) for k, v in q.items()}

    def indices(px):
        if not px:
            return b'\x00', (0, 0, 1, 1)
        xs = [p[0] for p in px]
        ys = [p[1] for p in px]
        X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)
        w, h = X1 - X0 + 1, Y1 - Y0 + 1
        idx = bytearray(w * h)
        for (x, y), c in px.items():
            idx[(y - Y0) * w + (x - X0)] = K._COD[c]
        return bytes(idx), (X0, Y0, w, h)

    itens, caixas, blobs = {}, {}, []
    pos = [0]

    def guarda(chave_txt, idx, rec, extra=None):
        z = zlib.compress(idx, 9)
        itens[chave_txt] = [pos[0], len(z), list(rec), extra]
        blobs.append(z)
        pos[0] += len(z)

    # estados vizinhos das caudas (o vento no celular nao sai igual ao do
    # PC): todas as fases da ondulacao e o vento um degrau a mais/a menos
    extra_caudas = []
    for ch, (qual, q) in grav.items():
        if qual == 'cauda':
            for f in range(6):
                for dc in (-0.25, 0.0, 0.25):
                    extra_caudas.append(dict(q, capa=q['capa'] + dc, fase=f / 6.0))
    # o mesmo para a cabeca (o cabelo balanca diferente a cada vez): todas as
    # fases e o vento no cabelo um degrau a mais/a menos
    extra_cabecas = []
    for ch, (qual, q) in grav.items():
        if qual == 'cabeca':
            for f in range(6):
                for dc in (-0.25, 0.0, 0.25):
                    extra_cabecas.append(dict(q, cabelo=q['cabelo'] + dc, fase=f / 6.0))
    t0 = time.time()
    feitos = 0
    tarefas = list(grav.items()) + [(None, ('cauda', q)) for q in extra_caudas] +         [(None, ('cabeca', q)) for q in extra_cabecas]
    for ch, (qual, q) in tarefas:
        q = pose(q)
        if qual in ('corpo', 'cauda', 'cabeca'):
            corpo, cauda, cabeca = K.chave_camadas(q)
            chave = {'corpo': corpo, 'cauda': cauda, 'cabeca': cabeca}[qual]
            if chave is None:
                continue
            txt = repr((qual, chave))
            if ch is not None and txt != ch:
                print('chave diferente!', ch[:80], txt[:80])
                continue
            if txt in itens:
                continue
            idx, rec = indices(K.montar(q, camada=qual))
            guarda(txt, idx, rec)
        elif qual == 'inteiro':
            chave = K._chave(q)
            txt = repr(('inteiro', chave))
            if txt in itens:
                continue
            px = K.montar(q)
            dentro = {p: c for p, c in px.items() if 0 <= p[0] < K.TW and 0 <= p[1] < K.TH}
            idx, rec = indices(dentro)
            corpo_px = [p for p, c in dentro.items() if c not in 'xX<>']
            if corpo_px:
                xs = [p[0] for p in corpo_px]
                ys = [p[1] for p in corpo_px]
                x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
                cx = (x0 / float(K.R), y0 / float(K.R), (x1 + 1) / float(K.R) - 1, (y1 + 1) / float(K.R) - 1)
            else:
                cx = (K._X0, K._PES, K._X0 + 12, K._PES + 26)
            bordas = K.bordas(px) if q.get('mugetsu') else None
            guarda(txt, idx, rec, {'caixa': list(cx), 'bordas': [list(b) for b in bordas] if bordas else None})
        elif qual == 'caixa':
            chave = K._chave(q)
            caixas[repr(chave)] = list(K.caixa(q))
        feitos += 1
        if feitos % 500 == 0:
            print(f'  {feitos} feitos, {time.time() - t0:.0f}s')
    # os 12 quadros da fita de fogo do Mugetsu
    for f in range(K._N_FITA):
        cam = K._quadro_fita(f)
        for lado in ('tras', 'frente'):
            idx = K._idx_fita(cam[lado])
            guarda(repr(('fita', f, lado)), idx, (K._FITA_X0, K._FITA_Y0, K._FITA_W, K._FITA_H))
    prova = K._digital(K._rasteriza(K.montar(K._pose_prova(), camada='corpo'))[0])
    cab = {'paleta': ''.join(sorted(K._PALETA)), 'R': K.R, 'prova': prova, 'itens': itens, 'caixas': caixas}
    cz = zlib.compress(json.dumps(cab).encode('utf-8'), 9)
    saida = os.path.join(REPO, 'yoru_quadros.bin')
    with open(saida, 'wb') as f:
        f.write(b'YQ01')
        f.write(len(cz).to_bytes(4, 'little'))
        f.write(cz)
        for b in blobs:
            f.write(b)
    tam = os.path.getsize(saida)
    print(f'{len(itens)} imagens, {len(caixas)} caixas, {tam / 1e6:.1f} MB, {time.time() - t0:.0f}s')


if __name__ == '__main__':
    {'gravar': gravar, 'assar': assar}[sys.argv[1]]()
