"""Mao e ponta das laminas medidas na grade fina (como o montar desenha)."""
pk = r'C:\Users\kirit\travetefocus\app\kirito.py'
k = open(pk, encoding='utf-8').read()


def troca(a, b, n=1):
    global k
    assert k.count(a) == n, (a[:80], k.count(a))
    k = k.replace(a, b)


troca("""    return [(cab_x + _OLHO5[0], cab_ty - _OLHO5[1])]
""", """    return [(cab_x + _OLHO5[0], cab_ty - _OLHO5[1])]


def maos_texel(p, qual=1):
    \"\"\"((mao), (ponta da lamina)) da mao `qual` em texels (sem espelho),
    como o montar desenha. Sem lamina na mao, a ponta e a propria mao.\"\"\"
    dx, dy = _meia(p['dx']), _meia(p['dy'])
    hy = _t(_PES + _alt_pernas(p) + dy)
    incl = int(round(p.get('incl', 0) or 0))
    cx = _t(_X0 + dx + 6.5)
    if qual == 1:
        ax, m, ang, comp = cx + int(2.5 * R), p['m1'] or (1, -3), p['a1'], p['c1']
    else:
        ax, m, ang, comp = cx - int(3.5 * R), p['m2'] or (-1, -6), p['a2'], p['c2']
    mx = ax + R * incl + R * m[0]
    my = hy + 5 * R + R * m[1]
    if ang is None or (qual == 1 and p['m1'] is None) or (qual == 2 and p['m2'] is None):
        return (mx, my), (mx, my)
    a = math.radians(ang)
    L = comp * R + 3
    return (mx, my), (mx + math.cos(a) * L, my + math.sin(a) * L)
""")
a = k.index("    def mao_local(self, qual=1, p=None):")
b = k.index("    def extensao(self, p=None):", a)
k = k[:a] + '''    def _local_texel(self, x, y):
        """Texel do sprite -> px locais (com o espelho)."""
        te = self.ps / float(R)
        if self.espelhar:
            x = TW - 1 - x
        return (x + 0.5) * te, (y + 0.5) * te

    def mao_local(self, qual=1, p=None):
        return self._local_texel(*maos_texel(p or self._base, qual)[0])

    def ponto_mao(self, qual=1):
        """Posicao da mao (coords do pai), sem considerar rotacao."""
        lx, ly = self.mao_local(qual)
        return self.x + lx, self.y + ly

    def ponta_espada(self, qual=1, p=None):
        """(x, y) da ponta da lamina `qual` (coords do pai), sem rotacao."""
        lx, ly = self._local_texel(*maos_texel(p or self._base, qual)[1])
        return self.x + lx, self.y + ly

''' + k[b:]
open(pk, 'w', encoding='utf-8', newline='\r\n').write(k)
print('ok')
