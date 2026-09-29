p = r'C:\Users\kirit\travetefocus\app\kirito.py'
c = open(p, encoding='utf-8').read()


def troca(a, b):
    global c
    assert c.count(a) == 1, (a[:70], c.count(a))
    c = c.replace(a, b)


troca("    _tubo(px, Q, J, 6.0, coxa)\n    _tubo(px, J, P, 5.3, canela)", "    _tubo(px, Q, J, 7.2, coxa)\n    _tubo(px, J, P, 6.2, canela)")
troca("return -(10.0 + 6.0 * max(0.0, saia - 0.6)) * u - vento * 48.0 * u ** 0.8",
      "return -(24.0 + 8.0 * max(0.0, saia - 0.6)) * u - vento * 44.0 * u ** 0.8")
troca("_cauda(px, cx - 11.0, top, -95.0, 62.0 * estica, curva_f,", "_cauda(px, cx - 10.0, top, -100.0, 64.0 * estica, curva_f,")
troca("lambda u: (6.0 + 5.0 * u, 6.5 + 2.0 * u),", "lambda u: (7.0 + 11.0 * u, 7.0 + 3.0 * u),")
troca("return 4.0 * u - vento * 38.0 * u ** 0.85 - ergue * 26.0 * u ** 0.95",
      "return -8.0 * u - vento * 38.0 * u ** 0.85 - ergue * 26.0 * u ** 0.95")
troca("_cauda(px, cx - 3.0, top, -88.0, 54.0 * estica, curva_d,", "_cauda(px, cx - 2.0, top, -92.0, 56.0 * estica, curva_d,")
troca("lambda u: (5.0 + 2.0 * u, 5.0 + 1.0 * u),", "lambda u: (6.0 + 4.0 * u, 6.0 + 2.0 * u),")
troca("        if k < -22.5:\n            return None\n        if k < -19.5:\n            return ('*' if j > 1 else '$') if abs(j) <= 3.2 else None",
      "        if k < -17.5:\n            return None\n        if k < -14.5:\n            return ('*' if j > 1 else '$') if abs(j) <= 3.2 else None")
troca("    _girado(px, hx, hy, ux, uy, -23.0, L + 0.5, -8.0, 8.0, cor)", "    _girado(px, hx, hy, ux, uy, -18.0, L + 0.5, -8.0, 8.0, cor)")
troca("        if k < -19.5:\n            return '*' if j > 1 else '$'\n        cruza", "        if k < -14.5:\n            return '*' if j > 1 else '$'\n        cruza")
troca("_girado(px, bx, by, math.cos(a), math.sin(a), -22.5, 2.5, -8.0, 8.0, cor)", "_girado(px, bx, by, math.cos(a), math.sin(a), -17.5, 2.5, -8.0, 8.0, cor)")
open(p, 'w', encoding='utf-8', newline='\r\n').write(c)
print('ok')
