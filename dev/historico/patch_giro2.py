pc = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(pc, encoding='utf-8').read()


def troca(s, a, b):
    assert s.count(a) == 1, (a[:70], s.count(a))
    return s.replace(a, b)


c = troca(c, '''        def _gira():
            seq = K.sequencia([(2, g1, 'segura'), (2, P['giro_2'], 'linear'), (2, P['giro_3'], 'linear'),
                               (2, g1, 'linear'), (5, g1, 'mola'), (4, vit, 'out'),
                               (12, _com(vit, emote='brilho'), 'segura'), (1, vit)])

            def _q(q):
                if q == 2:''', '''        def _gira():
            # uma volta de verdade em 8 quadros (achata de lado e vira no meio)
            seq = K.sequencia([(2, g1, 'segura'), (8, g1, 'segura'), (5, g1, 'mola'), (4, vit, 'out'),
                               (12, _com(vit, emote='brilho'), 'segura'), (1, vit)])
            lado0 = k.espelhar

            def _q(q):
                if 2 <= q < 10:
                    cs = math.cos(2 * math.pi * (q - 2) / 8.0)
                    k.escala_x = max(0.2, abs(cs))
                    k.espelhar = lado0 if cs >= 0 else (not lado0)
                elif q == 10:
                    k.escala_x = 1.0
                    k.espelhar = lado0
                if q == 2:''')
open(pc, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
