"""Modelo 3/4 (referencia 2): limpa cabeca e tronco tirados da imagem e gera
tf_repo/yoru_mapas.py (cabecas com expressoes, tronco; mantem os RETRATOS)."""
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.join(AQUI, 'dados')
REPO = r'C:\Users\kirit\travetefocus\app'
sys.path.insert(0, AQUI)
import gera_mapas as G                      # blocos de olho e boca (mesmo desenho)

# ── cabeca: recorte nativo x 42..106, y 3..54
cab = [list(l) for l in open(os.path.join(R1, 'cab2N.txt')).read().split('\n') if l]
H, W = len(cab), len(cab[0])
for r in range(H):
    for c in range(W):
        ch = cab[r][c]
        if 35 <= r <= 48 and c <= 25 and ch in 'OU0hIkn':
            cab[r][c] = 'J' if r < 44 else '.'          # cabo da espada de cristal (atras do ombro)
        if r >= 45 and c < 30:
            cab[r][c] = '.'
        if r >= 46 and c >= 38 and ch not in 'SstT':
            cab[r][c] = '.'                              # gola (vem do tronco)
# pontinho solto de cabelo
for _ in range(2):
    novo = [l[:] for l in cab]
    for r in range(H):
        for c in range(W):
            if cab[r][c] in 'JHIh':
                v = [cab[r + a][c + b] for a in (-1, 0, 1) for b in (-1, 0, 1)
                     if (a or b) and 0 <= r + a < H and 0 <= c + b < W and cab[r + a][c + b] in 'NJHIh']
                if v and cab[r][c] not in v:
                    novo[r][c] = max(set(v), key=v.count)
    cab = novo

# ── tronco: recorte nativo x 54..112, y 48..100 -> fica x 58..104, y 49..87
src = [l for l in open(os.path.join(R1, 'tronco2_nat.txt')).read().split('\n') if l]
X0, Y0 = 54, 48
x0, x1, y0, y1 = 58, 105, 49, 88
tor = [list(src[y - Y0][x0 - X0:x1 - X0]) for y in range(y0, y1)]
TH, TWd = len(tor), len(tor[0])


def put(x, y, ch):
    if 0 <= y - y0 < TH and 0 <= x - x0 < TWd:
        tor[y - y0][x - x0] = ch


def pega(x, y):
    return tor[y - y0][x - x0]


for y in range(y0, y1):
    for x in range(x0, x1):
        ch = pega(x, y)
        if ch in 'SstT':
            put(x, y, '.')                                # pescoco e queixo: da cabeca
        # braco da frente (sai pela direita do peito)
        borda_d = 96 if y < 60 else (94 if y < 76 else 95)
        if y >= 56 and x > borda_d:
            put(x, y, '.')
        elif y >= 56 and x == borda_d:
            put(x, y, 'c' if y < 76 else 'A')
        # braco de tras (sai pela esquerda)
        borda_e = 62 if y < 76 else 61
        if y >= 58 and x < borda_e:
            put(x, y, '.')
        # cabo da espada de cristal perto do ombro de tras
        if y < 62 and x < 68 and ch in 'k+GOZ09al':
            put(x, y, 'C')
# o cinto passa inteiro de um lado ao outro
for y in range(70, 75):
    for x in range(62, 95):
        if pega(x, y) == '.':
            put(x, y, '2' if y in (70, 74) else 'P')
TRONCO = [''.join(l) for l in tor]

# ── expressoes (olho: bloco 9x8 a partir de (42, 35); boca: 7x4 a partir de (44, 42))
G.OLHO0, G.LIN0 = 42, 35
G.BOCA0, G.BLIN0 = 44, 42
G.cab = cab
partes = ['"""Mapas do Yoru na grade fina (5 texels por unidade), tirados da',
          'referencia oficial 2 (vista 3/4) e limpos a mao. Gerado por mapas2.py."""',
          '']
nomes = []
for k in G.OLHOS:
    nome = '_CAB5_' + k
    partes.append(G.lista(nome, G.expressao(k)))
    partes.append('')
    nomes.append((k, nome))
partes.append('CABECAS = {' + ', '.join("'%s': %s" % (k, n) for k, n in nomes) + '}')
partes.append('')
partes.append(G.lista('TRONCO', TRONCO))
partes.append('')
velho = open(os.path.join(REPO, 'yoru_mapas.py'), encoding='utf-8').read()
retratos = velho[velho.index('\nRETRATOS = {'):] if '\nRETRATOS = {' in velho else ''
open(os.path.join(REPO, 'yoru_mapas.py'), 'w', encoding='utf-8', newline='\r\n').write(
    '\n'.join(partes) + retratos)
print('cabeca', W, H, 'tronco', TWd, TH)
