p = r'C:\Users\kirit\travetefocus\app\kirito.py'
c = open(p, encoding='utf-8').read()


def troca(a, b):
    global c
    assert c.count(a) == 1, (a[:70], c.count(a))
    c = c.replace(a, b)


troca("_COXA, _CANELA = 8.1, 8.1", "_COXA, _CANELA = 7.5, 7.5")
# kashira escura (a ponta do cabo nao vira uma mancha dourada no braco)
troca("            return ('*' if j > 1 else '$') if abs(j) <= 3.2 else None         # kashira",
      "            return ('k' if j > 1 else 'K') if abs(j) <= 3.0 else None         # kashira")
troca("        if k < -14.5:\n            return '*' if j > 1 else '$'\n        cruza",
      "        if k < -14.5:\n            return 'k' if j > 1 else 'K'\n        cruza")
# ponteira da bainha menor e mais escura
troca("""        if k > L:
            return '*' if jn <= -2 else ('$' if jn <= 1 else '@')""",
      """        if k > L:
            return '$' if jn <= -2 else '@'""")
troca("_girado(px, bx, by, math.cos(a), math.sin(a), 0.0, L + 7.0, -3.4, 2.4, cor,",
      "_girado(px, bx, by, math.cos(a), math.sin(a), 0.0, L + 3.5, -3.4, 2.4, cor,")
troca("_BAINHA_COMP = 11", "_BAINHA_COMP = 13")
open(p, 'w', encoding='utf-8', newline='\r\n').write(c)
print('ok')
