import sys, os, wave, struct, math
sys.path.insert(0, os.path.dirname(__file__))
def ler(p):
    w = wave.open(p); n = w.getnframes(); d = w.readframes(n); r = w.getframerate()
    return [v / 32768.0 for v in struct.unpack('<%dh' % n, d)], r
def f0s(a, r, jan=0.04):
    n = int(jan * r); out = []
    for i in range(0, len(a) - n, n // 2):
        seg = a[i:i + n]
        e = sum(v * v for v in seg) / n
        if e < 1e-3:
            continue
        best, lag_b = 0, 0
        for lag in range(int(r / 400), int(r / 70)):
            c = sum(seg[k] * seg[k + lag] for k in range(0, n - lag, 2))
            if c > best:
                best, lag_b = c, lag
        if lag_b:
            out.append(r / lag_b)
    return out
for f in sys.argv[1:]:
    a, r = ler(f)
    fs = sorted(f0s(a, r))
    med = fs[len(fs) // 2] if fs else 0
    ativo = [i for i, v in enumerate(a) if abs(v) > 0.02]
    print(os.path.basename(f), r, 'dur %.2fs' % (len(a) / r), 'fala %.2f-%.2fs' % (ativo[0] / r, ativo[-1] / r) if ativo else '', 'F0 mediana %.0f Hz' % med, 'faixa %.0f-%.0f' % (fs[len(fs)//10], fs[-len(fs)//10-1]) if len(fs) > 10 else '')
