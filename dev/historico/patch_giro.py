pc = r'C:\Users\kirit\travetefocus\app\cenas.py'
pk = r'C:\Users\kirit\travetefocus\app\kirito.py'
c = open(pc, encoding='utf-8').read()
k = open(pk, encoding='utf-8').read()


def troca(s, a, b):
    assert s.count(a) == 1, (a[:70], s.count(a))
    return s.replace(a, b)


c = troca(c, '''            def _gira():
                kk.rotacao = 0
                seq = K.sequencia([(3, abaixa, 'segura'), (2, g2, 'linear'), (2, g3, 'linear'),
                                   (2, g1, 'linear'), (2, g2, 'linear'), (2, g3, 'linear'),
                                   (6, g1, 'mola'), (1, g1)])

                def _q(q):
                    if q in (3, 9):                    # uma volta de luz a cada giro''', '''            def _gira():
                kk.rotacao = 0
                # giro de verdade: 2 voltas de 8 quadros cada. De lado ele
                # "achata" (escala |cos|) e vira no meio de cada meia-volta -
                # o sobretudo e o cabelo seguem pela fisica
                seq = K.sequencia([(3, abaixa, 'segura'), (16, g1, 'segura'), (6, g1, 'mola'), (1, g1)])
                lado0 = kk.espelhar

                def _q(q):
                    if 3 <= q < 19:
                        cs = math.cos(2 * math.pi * (q - 3) / 8.0)
                        kk.escala_x = max(0.2, abs(cs))
                        kk.espelhar = lado0 if cs >= 0 else (not lado0)
                    elif q == 19:
                        kk.escala_x = 1.0
                        kk.espelhar = lado0
                    if q in (3, 11):                   # uma volta de luz a cada giro''')
# golpe: 3 quadros de rastro no corte (em vez de 2)
k = troca(k, '''    if duplo:                                         # meio do golpe: 2 quadros de rastro
        meio = misturar(ant, imp, 0.5, 0.5)
        meio = smear(meio, ant['a1'] if s1 else None, ant['a2'] if s2 else None)
        chaves.append((1, meio, 'segura'))''', '''    if duplo:                                         # meio do golpe: 3 quadros de rastro
        for fr in (0.34, 0.68):
            meio = misturar(ant, imp, fr, fr)
            meio = smear(meio, ant['a1'] if s1 else None, ant['a2'] if s2 else None)
            chaves.append((1, meio, 'segura'))''')
open(pc, 'w', encoding='utf-8', newline='\n').write(c)
open(pk, 'w', encoding='utf-8', newline='\r\n').write(k)
print('ok')
