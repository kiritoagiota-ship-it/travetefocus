pk = r'C:\Users\kirit\travetefocus\app\kirito.py'
pc = r'C:\Users\kirit\travetefocus\app\cenas.py'
k = open(pk, encoding='utf-8').read()
c = open(pc, encoding='utf-8').read()


def troca(s, a, b):
    assert s.count(a) == 1, (a[:70], s.count(a))
    return s.replace(a, b)


k = troca(k, '''def ps_inteiro(v):''', '''TAMANHO = 1.15             # o Yoru novo e 15% maior que o de antes


def ps_inteiro(v):
    """Tamanho da unidade (px de tela): o que o Yoru tinha antes (degraus de
    3 px) e 15% a mais, exato. Os texels podem ficar com 1 px de diferenca
    entre si (invisivel no celular)."""
    return max(R, int(round(3 * max(1, int(round(v / 3.0))) * TAMANHO)))


def _ps_inteiro_antigo(v):''')
k = troca(k, "        self.ps = R * max(1, int(round(ps / float(R))))   # texel = ps/R (pixels todos iguais)",
          "        self.ps = max(R, int(round(ps)))                  # texel = ps/R")
c = troca(c, "        self.ps = max(K.R, K.R * int(math.ceil(alt_boneco * 1.12 / 31.0 / K.R - 0.15)))",
          "        self.ps = max(K.R, int(round(3 * int(math.ceil(alt_boneco * 1.12 / 31.0 / 3 - 0.15)) * K.TAMANHO)))")
open(pk, 'w', encoding='utf-8', newline='\r\n').write(k)
open(pc, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
