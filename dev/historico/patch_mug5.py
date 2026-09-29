"""Forma Mugetsu na grade fina, em camadas: cabelao ate os joelhos (mechas
que crescem, pontas em fumaca), sobretudo longo rasgado com as pontas em
chamas, faixas nos bracos e no peito."""
pk = r'C:\Users\kirit\travetefocus\app\kirito.py'
k = open(pk, encoding='utf-8').read()


def troca(a, b, n=1):
    global k
    assert k.count(a) == n, (a[:80], k.count(a))
    k = k.replace(a, b)


# ── cabeca: o tufo some quando o cabelao cresce; o cabelao vem atras
troca('''def _cabeca5(px, olhos, cab_x, cab_ty, cb, sobe, fase):''', '''# mechas do cabelao do Mugetsu: (coluna, linha da raiz no mapa da cabeca,
# angulo, comprimento, meia-largura). As de tras primeiro.
_CABELAO = ((22, 30, -112.0, 118.0, 7.5), (18, 22, -118.0, 128.0, 8.0), (26, 16, -124.0, 124.0, 8.5),
            (30, 10, -130.0, 112.0, 8.0), (14, 34, -104.0, 104.0, 7.0), (34, 20, -110.0, 116.0, 7.5),
            (24, 40, -98.0, 92.0, 6.5))


def _cabelao(px, cb, sobe, fase, cresce):
    """Cabelao do Mugetsu (coordenadas do mapa da cabeca, y para cima):
    mechas longas que descem pelas costas ate os joelhos, com brilho em
    cima e sombra embaixo, balancando da raiz para a ponta; as pontas se
    desfazem em fumaca e brasa. cresce 0..1 = quanto ja cresceu."""
    cabelo = {}
    corre = max(0.0, min(2.5, cb)) * 0.35
    amp = 4.0 + 3.0 * min(2.0, abs(cb)) + 5.0 * sobe
    f6 = int(round(fase * 6)) % 6
    for i, (col, lin, ang, comp, larg) in enumerate(_CABELAO):
        cp = comp * max(0.08, min(1.0, cresce))
        if cp < 6:
            continue
        a0 = ang - corre * 38.0 + sobe * 18.0              # o vento joga para tras; o reiatsu levanta

        def curva(u, i=i):
            return -10.0 * u * u + amp * u * _onda(fase * 1.2, u, 0.9, i * 0.15)

        f = _fita(col, -lin, a0, cp, curva,
                  lambda u, w=larg: (w * (1.0 - 0.55 * u), w * (1.0 - 0.45 * u)), passo=0.6)
        fim = 0.8 if cresce > 0.95 else 0.9
        for q, (u, v, W) in f.items():
            vf = v / W if W else 0.5
            if u > fim:                                    # ponta em fumaca: pixels soltos
                if (q[0] + q[1] + f6) % 3:
                    continue
                ch = 'o' if ((q[0] * 7 + q[1] * 3 + f6) % 11 == 0) else ('d' if u < fim + 0.1 else '&')
            elif vf > 0.72:
                ch = 'J'
            elif vf < 0.28 and 0.05 < u < 0.55:
                ch = 'h' if (vf < 0.12 and 0.15 < u < 0.35 and i in (1, 2, 5)) else 'I'
            else:
                ch = 'H'
            if q in cabelo and cabelo[q] in 'JHIh' and ch in 'JHIh' and \\
                    any((q[0] + a, q[1] + b) not in f for (a, b) in _VIZ4):
                ch = 'J'
            cabelo[q] = ch
    px.update(cabelo)


def _cabeca5(px, olhos, cab_x, cab_ty, cb, sobe, fase, cresce=None):''')
troca('''    olhos = olhos if olhos in _YM.CABECAS else 'a'
    _parte(px, ('cab5', olhos, cb, sobe, round(fase, 3)), cab_x, cab_ty,
           lambda d: _cabeca5_desenho(d, olhos, cb, sobe, fase))


def _cabeca5_desenho(d, olhos, cb, sobe, fase):
    mapa = _YM.CABECAS[olhos]''', '''    olhos = olhos if olhos in _YM.CABECAS else 'a'
    cr = None if cresce is None else round(cresce, 2)
    _parte(px, ('cab5', olhos, cb, sobe, round(fase, 3), cr), cab_x, cab_ty,
           lambda d: _cabeca5_desenho(d, olhos, cb, sobe, fase, cr))


def _cabeca5_desenho(d, olhos, cb, sobe, fase, cresce=None):
    if cresce is not None:
        _cabelao(d, cb, sobe, fase, cresce)             # o cabelao fica atras da cabeca
    sem_tufo = cresce is not None and cresce >= 0.3
    mapa = _YM.CABECAS[olhos]''')
troca('''            if not _no_tufo(c, r):
                resto[(c, -r)] = ch
                continue''', '''            if not _no_tufo(c, r):
                resto[(c, -r)] = ch
                continue
            if sem_tufo:
                continue                                # o tufo virou o cabelao''')

# ── sobretudo do Mugetsu: longo, barra rasgada em pontas de fogo
troca('''def _casaco5(px, cx, top, chao, capa, lift, fase, saia, parte):
    """Sobretudo da referencia (na grade fina), guardado pronto."""
    q4 = lambda v: round(v * 4) / 4.0
    capa, lift, saia = q4(capa), q4(lift), q4(saia)
    _parte(px, ('casaco5', parte, capa, lift, round(fase, 3), saia, chao - top), cx, top,
           lambda d: _casaco5_desenho(d, 0, 0, chao - top, capa, lift, fase, saia, parte))''', '''def _casaco5(px, cx, top, chao, capa, lift, fase, saia, parte, mug=False):
    """Sobretudo da referencia (na grade fina), guardado pronto."""
    q4 = lambda v: round(v * 4) / 4.0
    capa, lift, saia = q4(capa), q4(lift), q4(saia)
    _parte(px, ('casaco5', parte, capa, lift, round(fase, 3), saia, chao - top, mug), cx, top,
           lambda d: _casaco5_desenho(d, 0, 0, chao - top, capa, lift, fase, saia, parte, mug))''')
troca('''def _casaco5_desenho(px, cx, top, chao, capa, lift, fase, saia, parte):''',
      '''def _casaco5_desenho(px, cx, top, chao, capa, lift, fase, saia, parte, mug=False):''')
troca('''    vento = max(-1.0, min(2.2, capa))
    ergue = max(-0.6, min(2.6, lift))
    amp = 5.0 + 4.0 * min(3.0, abs(capa)) + 2.5 * abs(ergue)
    estica = 1.0 + 0.2 * max(0.0, vento) + 0.1 * max(0.0, ergue)

    if parte == 'frente':''', '''    vento = max(-1.0, min(2.2, capa))
    ergue = max(-0.6, min(2.6, lift))
    amp = 5.0 + 4.0 * min(3.0, abs(capa)) + 2.5 * abs(ergue)
    estica = (1.0 + 0.2 * max(0.0, vento) + 0.1 * max(0.0, ergue)) * (1.3 if mug else 1.0)
    f6 = int(round(fase * 6)) % 6

    def rasga(vf, base):
        """Barra: no Mugetsu, rasgada em pontas longas e desiguais."""
        if not mug:
            return base
        return base - 0.05 - 0.13 * abs(math.sin(vf * 11.0 + 0.7)) - 0.06 * abs(math.sin(vf * 23.0))

    def em_chamas(ch, u, fim_u, q):
        """As pontas do sobretudo do Mugetsu viram fogo roxo."""
        if not mug or u < fim_u - 0.12:
            return ch
        k2 = (fim_u - u) / 0.12                        # 1 longe da ponta .. 0 na ponta
        h = (q[0] * 5 + q[1] * 3 + f6 * 2) % 7
        if k2 < 0.35:
            return 'L' if h < 2 else ('V' if h < 5 else None)
        if k2 < 0.7:
            return 'V' if h < 3 else 'o'
        return 'o' if h < 3 else ch

    if parte == 'frente':''')
# a cor final das caudas passa pela chama nas pontas
troca('''    f = _fita(x0, y0, ang0, comp, curva, larg)
    dentro = {}
    for q, (u, v, W) in f.items():
        if q[1] < chao:
            continue                              # o pano nao atravessa o chao
        if u <= ponta(v / W if W else 0.0):
            dentro[q] = (u, v, W)''', '''    f = _fita(x0, y0, ang0, comp, curva, larg)
    dentro = {}
    for q, (u, v, W) in f.items():
        if q[1] < chao:
            continue                              # o pano nao atravessa o chao
        if u <= ponta(v / W if W else 0.0):
            dentro[q] = (u, v, W)
    fogo = getattr(cor, 'fogo', None)''')
troca('''    for q, (u, v, W) in dentro.items():
        if u > 0.72 and fora(q, 1):
            ch = barra[1]
        elif u > 0.72 and fora(q, 2):
            ch = barra[0]
        else:
            ch = cor(u, v, W)
        if ch:
            px[q] = ch''', '''    for q, (u, v, W) in dentro.items():
        if u > 0.72 and fora(q, 1):
            ch = barra[1]
        elif u > 0.72 and fora(q, 2):
            ch = barra[0]
        else:
            ch = cor(u, v, W)
        if fogo is not None:
            ch = fogo(ch, u, ponta(v / W if W else 0.0), q)
        if ch:
            px[q] = ch''')
# caudas do Mugetsu: barra rasgada + chama (as funcoes de cor levam o fogo)
troca('''    _cauda(px, cx - 2.0, top, -92.0, 56.0 * estica, curva_d,
           lambda u: (6.0 + 4.0 * u, 6.0 + 2.0 * u),
           lambda vf: 1.0 - 0.08 * (1.0 - vf) - 0.05 * abs(math.sin(vf * 7.0)),
           cor_d, chao, barra=('a', 'q'))''', '''    cor_d.fogo = em_chamas if mug else None
    _cauda(px, cx - 2.0, top, -92.0, 56.0 * estica, curva_d,
           lambda u: (6.0 + 4.0 * u, 6.0 + 2.0 * u),
           lambda vf: rasga(vf, 1.0 - 0.08 * (1.0 - vf) - 0.05 * abs(math.sin(vf * 7.0))),
           cor_d, chao, barra=('a', 'q'))''')
troca('''    _cauda(px, cx - 10.0, top, -100.0, 64.0 * estica, curva_f,
           lambda u: (7.0 + 11.0 * u, 7.0 + 3.0 * u),
           lambda vf: 1.0 - 0.1 * vf - 0.07 * abs(math.sin(vf * 9.4)),
           cor_f, chao, barra=('l', 'q'))''', '''    cor_f.fogo = em_chamas if mug else None
    _cauda(px, cx - 10.0, top, -100.0, 64.0 * estica, curva_f,
           lambda u: (7.0 + (14.0 if mug else 11.0) * u, 7.0 + 3.0 * u),
           lambda vf: rasga(vf, 1.0 - 0.1 * vf - 0.07 * abs(math.sin(vf * 9.4))),
           cor_f, chao, barra=('l', 'q'))''')
troca('''        _cauda(px, cx + 15.0, top, -92.0, 30.0, curva,
               lambda u: (6.5 + 1.0 * u, 5.5 + 1.0 * u * saia),
               lambda vf: 1.0 - 0.05 * vf, cor, chao, barra=('a', '2'))''', '''        cor.fogo = em_chamas if mug else None
        _cauda(px, cx + 15.0, top, -92.0, 30.0 * (1.5 if mug else 1.0), curva,
               lambda u: (6.5 + 1.0 * u, 5.5 + 1.0 * u * saia),
               lambda vf: rasga(vf, 1.0 - 0.05 * vf), cor, chao, barra=('a', '2'))''')

# ── faixas nos bracos (Mugetsu): enroladas em diagonal
FAIXA_VELHA = (
    "        if faixas and t < 0.8:                     # faixas enroladas (forma Mugetsu)\n"
    "            if (int(t * lb) + j) % 5 == 0:\n"
    "                return 'W'\n"
    "            return 'g' if j >= 2 else 'u'")
FAIXA_NOVA = (
    "        if faixas and t < 0.84:                    # faixas enroladas na diagonal (Mugetsu)\n"
    "            d = (int(t * lb) + j) % 6\n"
    "            if d == 0:\n"
    "                return '&'                          # vao entre as voltas\n"
    "            if d == 1:\n"
    "                return 'o' if j >= 1 else 'd'       # beirada acesa de cada volta\n"
    "            return 'd' if j >= -1 else '&'")
troca(FAIXA_VELHA, FAIXA_NOVA)
open(pk, 'w', encoding='utf-8', newline='\r\n').write(k)
print('ok')
