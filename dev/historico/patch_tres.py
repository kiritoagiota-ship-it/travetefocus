pc = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(pc, encoding='utf-8').read()


def troca(a, b):
    global c
    assert c.count(a) == 1, a[:80]
    c = c.replace(a, b)


a = c.index("class ArcoCorte:")
b = c.index("    def ponto(self, s, off=0.0):", a)
c = c[:a] + '''class ArcoCorte:
    """Caminho da ponta da lamina num corte: arco de circulo (centro, raio,
    angulo inicial e quanto gira). A mancha fica do lado de dentro (onde
    estao a mao e o corpo), com a grossura maxima `esp` (px)."""

    def __init__(self, cx, cy, R, a0, da, esp):
        self.cx, self.cy, self.R = cx, cy, R
        self.a0, self.da = a0, da
        self.esp = float(esp)
        self.comp = abs(da) * R

    @classmethod
    def por_bojo(cls, p0, p1, bojo, esp):
        """De p0 a p1 estufando para um lado (bojo = fracao da corda; > 0 =
        para a esquerda de quem vai de p0 a p1)."""
        (x0, y0), (x1, y1) = p0, p1
        c = math.hypot(x1 - x0, y1 - y0) or 1.0
        ux, uy = (x1 - x0) / c, (y1 - y0) / c
        nx, ny = -uy, ux
        b = bojo if abs(bojo) > 0.01 else 0.01
        h = b * c
        mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        return cls.por_tres(p0, (mx + nx * h, my + ny * h), p1, esp)

    @classmethod
    def por_tres(cls, p0, pm, p1, esp):
        """O arco que sai de p0, passa por pm e chega em p1."""
        (ax, ay), (bx, by), (qx, qy) = p0, pm, p1
        d = 2.0 * (ax * (by - qy) + bx * (qy - ay) + qx * (ay - by))
        if abs(d) < 1e-6:                               # alinhados: quase reto
            ux, uy = qx - ax, qy - ay
            c = math.hypot(ux, uy) or 1.0
            return cls.por_tres(p0, ((ax + qx) / 2.0 - uy / c * c * 0.01,
                                     (ay + qy) / 2.0 + ux / c * c * 0.01), p1, esp)
        a2, b2, q2 = ax * ax + ay * ay, bx * bx + by * by, qx * qx + qy * qy
        cx = (a2 * (by - qy) + b2 * (qy - ay) + q2 * (ay - by)) / d
        cy = (a2 * (qx - bx) + b2 * (ax - qx) + q2 * (bx - ax)) / d
        R = math.hypot(ax - cx, ay - cy)
        a0 = math.atan2(ay - cy, ax - cx)
        am = math.atan2(by - cy, bx - cx)
        a1 = math.atan2(qy - cy, qx - cx)
        dm = (am - a0) % (2 * math.pi)
        d1 = (a1 - a0) % (2 * math.pi)
        da = d1 if dm <= d1 else d1 - 2 * math.pi      # o lado que passa por pm
        return cls(cx, cy, R, a0, da, esp)

    @classmethod
    def pelo_meio(cls, centro, ang, comp, bojo, esp):
        """Arco cujo MEIO da mancha passa por `centro` (o meio da silaba),
        indo na direcao `ang` (graus), com a corda `comp`."""
        a = math.radians(ang)
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        sg = 1.0 if bojo > 0 else -1.0
        # o caminho da ponta fica por fora do meio da mancha (~0,4 da grossura)
        desl = -bojo * comp + sg * 0.4 * esp
        mx, my = centro[0] + nx * desl, centro[1] + ny * desl
        return cls.por_bojo((mx - dx * comp / 2.0, my - dy * comp / 2.0),
                            (mx + dx * comp / 2.0, my + dy * comp / 2.0), bojo, esp)

''' + c[b:]
# arco do golpe: pelas pontas da lamina no comeco, no meio e no fim
a = c.index("        def arco_do_golpe(arma, corta, a0, a1, qual, bojo, esp):")
b = c.index("        def posicionar(", a)
c = c[:a] + '''        def arco_do_golpe(arma, corta, a0, a1, qual, bojo, esp):
            """Arco da ponta da lamina `qual`: passa pela ponta na pose `arma`
            (ancora a0), no meio do golpe e na pose `corta` (ancora a1) - o
            mesmo caminho que a lamina do desenho faz."""
            meio = K.misturar(arma, corta, 0.5, 0.5)
            am = ((a0[0] + a1[0]) / 2.0, (a0[1] + a1[1]) / 2.0)
            return ArcoCorte.por_tres(ponta(arma, a0, qual), ponta(meio, am, qual),
                                      ponta(corta, a1, qual), esp)

''' + c[b:]
# pelos no-bojo antigos: posicionar ignora o bojo agora (fica no arco real)
troca("""        corta_ve = _com(P['salto'], olhos='g')
        fim_ve = _com(P['salto_fim'], olhos='s')""", """        corta_ve = _com(P['salto'], olhos='g', a1=P['salto']['a1'] + 360)   # sobe pela frente
        fim_ve = _com(P['salto_fim'], olhos='s', a1=_perto(P['salto_fim']['a1'], corta_ve['a1']))""")
troca("""        corta_fo = _com(P['c3_arma'], olhos='g')                    # descem abrindo em X""",
      """        corta_fo = _com(P['c3_arma'], olhos='g', a2=P['c3_arma']['a2'] - 360)   # descem abrindo em X""")
open(pc, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
