pc = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(pc, encoding='utf-8').read()
a = c.index("        def posicionar(chave, i, arma, corta, desl, bojo, esp, pal='katana', y_ini=None,")
b = c.index("        def cortar(chave, i, dur=0.12, on_meio=None, som=None, letras=False):")
c = c[:a] + '''        def posicionar(chave, i, arma, corta, desl, bojo, esp, pal='katana', y_ini=None,
                       extra=None, alvo='meio'):
            """Acha onde ele comeca (a0) e termina (a1) o golpe para a luz do
            corte atravessar a silaba i. desl = quanto ele anda no golpe (em
            alturas de letra; x para a frente). alvo: 'meio' = o meio da luz
            cai no meio da silaba; 'cruza' = so anda de lado ate a luz cruzar
            a altura das letras no meio da silaba (y_ini = comeca no chao);
            'x' = as duas luzes se cruzam no meio da silaba. extra = (chave,
            qual, bojo, esp, pal) da segunda lamina, presa no mesmo corpo."""
            sx = -1.0 if kk.espelhar else 1.0
            dx, dy = desl[0] * th * sx, desl[1] * th
            cx, cy, _ = silaba(i)

            def arcos(a0, a1):
                a = arco_do_golpe(arma, corta, a0, a1, 1, bojo, esp)
                b = arco_do_golpe(arma, corta, a0, a1, extra[1], extra[2], extra[3]) if extra else None
                return a, b

            def ponto_alvo(a, b):
                if alvo == 'x' and b is not None:
                    melhor = None
                    for s in range(26):
                        p = a.ponto(s / 25.0, -0.4 * a.esp)
                        for r in range(26):
                            q = b.ponto(r / 25.0, -0.4 * b.esp)
                            d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
                            if melhor is None or d < melhor[0]:
                                melhor = (d, ((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0))
                    return melhor[1]
                if alvo == 'cruza':
                    s = min((abs(a.ponto(k / 40.0, -0.4 * esp)[1] - cy), k / 40.0) for k in range(4, 37))[1]
                    return a.ponto(s, -0.4 * esp)[0], cy
                return a.ponto(0.5, -0.4 * esp)
            a0 = (0.0, y_ini if y_ini is not None else 0.0)
            for _ in range(3):
                mx, my = ponto_alvo(*arcos(a0, (a0[0] + dx, a0[1] + dy)))
                a0 = (a0[0] + cx - mx, y_ini if y_ini is not None else a0[1] + cy - my)
            a1 = (a0[0] + dx, a0[1] + dy)
            # nunca sai do quadro (se precisar, o golpe todo anda junto)
            b1 = quadro(a1[0], a1[1], [corta])
            ddx, ddy = b1[0] - a1[0], b1[1] - a1[1]
            a0, a1 = (a0[0] + ddx, a0[1] + ddy), b1
            b0 = quadro(a0[0], a0[1], [arma])
            ARCOS[chave] = (arco_do_golpe(arma, corta, b0, a1, 1, bojo, esp), pal)
            oficina.pedir(chave, ARCOS[chave][0], pal)
            if extra:
                ch2, q2, bj2, es2, pal2 = extra
                ARCOS[ch2] = (arco_do_golpe(arma, corta, b0, a1, q2, bj2, es2), pal2)
                oficina.pedir(ch2, ARCOS[ch2][0], pal2)
            return b0, a1

''' + c[b:]


def troca(a, b):
    global c
    assert c.count(a) == 1, a[:80]
    c = c.replace(a, b)


troca("""        B0, B1 = posicionar('ve', 1, arma_ve, corta_ve, (0.5, 1.3), 0.16, th * 0.95, y_ini=y_chao)""",
      """        B0, B1 = posicionar('ve', 1, arma_ve, corta_ve, (0.5, 1.3), 0.16, th * 0.95, y_ini=y_chao,
                            alvo='cruza')""")
troca("""        Dm, D1 = posicionar('fo', 3, arma_fo, corta_fo, (0.6, -1.0), 0.14, th * 0.9, y_fim=y_chao,
                            extra=('fo2', 2, 0.14, th * 0.85, 'azul'))
        D0 = quadro(Dm[0] + th * 0.9 * (-1 if kk.espelhar else 1), y_chao, [prep_fo])""",
      """        Dm, D1 = posicionar('fo', 3, arma_fo, corta_fo, (0.5, -0.8), 0.14, th * 0.9, alvo='x',
                            extra=('fo2', 2, 0.14, th * 0.85, 'azul'))
        D0 = quadro(Dm[0] + th * 0.9 * (1 if kk.espelhar else -1), y_chao, [prep_fo])     # atras dele""")
open(pc, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
