"""Leva o kirito.py para a grade fina (R=5) com o desenho novo."""
import os, re, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from paleta5 import P5
p = r'C:\Users\kirit\travetefocus\app\kirito.py'
c = open(p, encoding='utf-8').read()


def troca(a, b, n=1):
    global c
    assert c.count(a) == n, (a[:70], c.count(a))
    c = c.replace(a, b)


# 1) grade
troca("R = 3\nE = R / 2.0", "R = 5\nE = R / 2.0")

# 2) paleta: cor nova para cada caractere (mesmo papel) + os novos
for ch, (r, g, b) in P5.items():
    cor = '(%.2f, %.2f, %.2f, 1)' % (r / 255.0, g / 255.0, b / 255.0)
    padrao = re.compile(r"'%s': \([0-9.]+, [0-9.]+, [0-9.]+, [0-9.]+\)" % re.escape(ch))
    if padrao.search(c):
        c, n = padrao.subn("'%s': %s" % (ch, cor), c, count=1)
    else:
        troca("_SEM_CONTORNO = set('xX!1FfL<>')",
              "_PALETA['%s'] = %s\n_SEM_CONTORNO = set('xX!1FfL<>')" % (ch, cor))
# o contorno de luz ciano que ja vem desenhado no cabelo nao ganha outro contorno
troca("_SEM_CONTORNO = set('xX!1FfL<>')", "_SEM_CONTORNO = set('xX!1FfL<>O0')")
troca("""_SOMBRA = {'C': '&',""", """_SOMBRA = {'a': 'd', 'l': 'o', '$': 'd', '@': 'D', '*': 'o', 'O': 'o', '0': '8', 'C': '&',""")
troca("""_CORPO = set('CcAqGPBMSsHhE24JIen7tU3%bp~^')""", """_CORPO = set('CcAqGPBMSsHhE24JIen7tU3%bp~^alkZN')""")
troca("""_PANO = set('CcAq2Z')""", """_PANO = set('CcAq2Zal')""")

# 3) pernas mais longas (proporcao da referencia): alturas e pes x1,29
a = c.index('_PERNAS_P = {')
b = c.index('}\n_PERNAS = _PERNAS_P', a)
bloco = c[a:b]


def escala(m):
    v = float(m.group(1)) * 1.29
    return 'H=%.1f' % v


def escala_t(m):
    return '(%.1f, %.1f)' % (float(m.group(1)) * 1.29, float(m.group(2)) * 1.29)


bloco = re.sub(r'H=([0-9.]+)', escala, bloco)
bloco = re.sub(r'\((-?[0-9.]+), (-?[0-9.]+)\)', escala_t, bloco)
c = c[:a] + bloco + c[b:]
troca("_COXA, _CANELA = 6.3, 6.3", "_COXA, _CANELA = 8.1, 8.1")

# 4) espadas das costas e fundida: o desenho de sempre, ampliado
for nome in ('_repulser2', '_fundida2'):
    a = c.index('def %s(' % nome)
    b = c.index('\ndef ', a + 10)
    f = c[a:b]
    f = f.replace('    L = comp * R\n', '    L = comp * 3\n', 1)
    f = re.sub(r"_girado\(px, hx, hy, ux, uy, (-?[0-9.]+), (L \+ [0-9.]+), (-?[0-9.]+), (-?[0-9.]+), cor\)",
               r"_girado_esc(px, hx, hy, ux, uy, \1, \2, \3, \4, cor, F)", f)
    f = f.replace("px[(int(round(hx + ux * k + nx * j)), int(round(hy + uy * k + ny * j)))] = ch",
                  "px[(int(round(hx + (ux * k + nx * j) * F)), int(round(hy + (uy * k + ny * j) * F)))] = ch")
    assert '_girado_esc' in f, nome
    c = c[:a] + f + c[b:]
troca("""        if tipo == 1:
            _katana2(d, 0, 0, ux, uy, nx, ny, comp, b)""", """        if tipo == 1:
            _katana5(d, 0, 0, ux, uy, nx, ny, comp, b)""")

# 5) desenho novo: entra antes do montar antigo, que sai
novo = open(os.path.join(AQUI, 'yoru5.txt'), encoding='utf-8').read()
a = c.index('def montar(p, rapido=False):')
b = c.index('\ndef bordas(px):', a)
c = c[:a] + novo + c[b + 1:]

# 6) olhos (rastro de luz da forma Mugetsu) na cabeca nova
a = c.index('def olhos_texel(p):')
b = c.index('\ndef ', a + 10)
c = c[:a] + '''def olhos_texel(p):
    """Centro do olho (texels, sem espelho) na pose - para o brilho e o
    rastro de luz dos olhos na forma Mugetsu."""
    dx, dy = _meia(p['dx']), _meia(p['dy'])
    hip_y = _PES + _alt_pernas(p) + dy
    incl = int(round(p.get('incl', 0) or 0))
    cx = _t(_X0 + dx + 6.5)
    hy = _t(hip_y)
    cab_x = cx + 2 - 46 + 4 * incl + int(round(p.get('hx', 0) or 0))
    cab_ty = hy + 38 + 50 + int(round(p.get('hy', 0) or 0))
    return [(cab_x + 58, cab_ty - 37)]

''' + c[b + 1:]

# 7) tamanho do texel: multiplo de R mais perto (antes arredondava para baixo)
troca("        self.ps = max(R, int(ps) - int(ps) % R)      # texel = ps/R (pixels todos iguais)",
      "        self.ps = R * max(1, int(round(ps / float(R))))   # texel = ps/R (pixels todos iguais)")
open(p, 'w', encoding='utf-8', newline='\r\n').write(c)
print('ok')
