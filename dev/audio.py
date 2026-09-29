"""DSP minima em Python puro (sem numpy): ler/escrever WAV, cortar, mixar,
pitch por reamostragem, filtros de 1 polo, fades, normalizar, espectrograma."""
import math, cmath, struct, wave, os
TAXA = 44100
PASTA = os.path.join(os.path.dirname(__file__), '..', 'sons_dl', 'w44')

def ler(nome):
    w = wave.open(os.path.join(PASTA, nome + '.wav'))
    n = w.getnframes(); d = w.readframes(n)
    assert w.getsampwidth() == 2 and w.getnchannels() == 1 and w.getframerate() == TAXA
    return [v / 32768.0 for v in struct.unpack('<%dh' % n, d)]

def ler_arquivo(caminho):
    """Le um WAV mono 16 bits qualquer (ex: a voz sintetizada)."""
    w = wave.open(caminho)
    n = w.getnframes(); d = w.readframes(n)
    assert w.getsampwidth() == 2 and w.getnchannels() == 1
    a = [v / 32768.0 for v in struct.unpack('<%dh' % n, d)]
    if w.getframerate() != TAXA:
        a = reamostrar(a, w.getframerate() / float(TAXA))
    return a


def ler_saida(nome):
    """Le um efeito ja gerado em tf_repo/sons (para derivar outro dele)."""
    caminho = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'sons', nome + '.wav')
    w = wave.open(caminho)
    n = w.getnframes(); d = w.readframes(n)
    return [v / 32768.0 for v in struct.unpack('<%dh' % n, d)]


def escrever(caminho, a, taxa=TAXA):
    pico = max(1e-9, max(abs(v) for v in a))
    if pico > 1.0:
        a = [v / pico for v in a]
    dados = struct.pack('<%dh' % len(a), *[int(max(-1, min(1, v)) * 32767) for v in a])
    w = wave.open(caminho, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(taxa)
    w.writeframes(dados); w.close()

def dur(a): return len(a) / TAXA
def seg(a, t0=0.0, t1=None):
    i0 = int(t0 * TAXA); i1 = len(a) if t1 is None else int(t1 * TAXA)
    return a[i0:i1]
def ganho(a, g): return [v * g for v in a]
def db(x): return 10 ** (x / 20.0)

def fade(a, ini=0.0, fim=0.0, curva=2.0):
    a = list(a); n = len(a)
    ni, nf = int(ini * TAXA), int(fim * TAXA)
    for i in range(min(ni, n)):
        a[i] *= (i / ni) ** curva
    for i in range(min(nf, n)):
        a[n - 1 - i] *= (i / nf) ** curva
    return a

def envelope(a, pontos):
    """pontos: [(t, ganho), ...] interpolado linear."""
    a = list(a)
    for i in range(len(a)):
        t = i / TAXA
        if t <= pontos[0][0]:
            g = pontos[0][1]
        elif t >= pontos[-1][0]:
            g = pontos[-1][1]
        else:
            for (t0, g0), (t1, g1) in zip(pontos, pontos[1:]):
                if t0 <= t <= t1:
                    g = g0 + (g1 - g0) * (t - t0) / max(1e-9, t1 - t0); break
        a[i] *= g
    return a

def reamostrar(a, fator):
    """fator > 1: mais agudo e mais curto (como acelerar a fita)."""
    n = int(len(a) / fator)
    out = [0.0] * n
    for i in range(n):
        x = i * fator; j = int(x); f = x - j
        v0 = a[j] if j < len(a) else 0.0
        v1 = a[j + 1] if j + 1 < len(a) else 0.0
        out[i] = v0 + (v1 - v0) * f
    return out

def lp(a, fc):
    k = 1 - math.exp(-2 * math.pi * fc / TAXA); y = 0.0; out = []
    for v in a:
        y += k * (v - y); out.append(y)
    return out

def hp(a, fc):
    b = lp(a, fc)
    return [v - w for v, w in zip(a, b)]

def mix(*camadas):
    """camadas: (amostras, inicio_s, ganho)"""
    n = max(int(t * TAXA) + len(a) for a, t, g in camadas)
    out = [0.0] * n
    for a, t, g in camadas:
        i0 = int(t * TAXA)
        for i, v in enumerate(a):
            out[i0 + i] += v * g
    return out

def pico_t(a, janela=0.005):
    """instante (s) de maior energia."""
    j = max(1, int(janela * TAXA)); melhor, ti = -1, 0
    for i in range(0, len(a) - j, j):
        e = sum(v * v for v in a[i:i + j])
        if e > melhor:
            melhor, ti = e, i
    return ti / TAXA

def aparar(a, lim=0.004, antes=0.004, depois=0.02):
    i0 = next((i for i, v in enumerate(a) if abs(v) > lim), 0)
    i1 = len(a) - next((i for i, v in enumerate(reversed(a)) if abs(v) > lim), 0)
    i0 = max(0, i0 - int(antes * TAXA)); i1 = min(len(a), i1 + int(depois * TAXA))
    return a[i0:i1]

def normalizar(a, alvo_db=-1.0):
    p = max(1e-9, max(abs(v) for v in a))
    return [v * db(alvo_db) / p for v in a]

def saturar(a, k=1.2):
    t = math.tanh(k)
    return [math.tanh(k * v) / t for v in a]

def rms_db(a):
    return 20 * math.log10(max(1e-9, math.sqrt(sum(v * v for v in a) / max(1, len(a)))))

def ruido_rosa(n, seed=1):
    import random
    r = random.Random(seed); b = [0.0] * 3; out = []
    for _ in range(n):
        w = r.uniform(-1, 1)
        b[0] = 0.99765 * b[0] + w * 0.0990460
        b[1] = 0.96300 * b[1] + w * 0.2965164
        b[2] = 0.57000 * b[2] + w * 1.0526913
        out.append((b[0] + b[1] + b[2] + w * 0.1848) * 0.2)
    return out

def seno(f0, f1, d, vol=1.0, queda=3.0, atk=0.004):
    n = int(d * TAXA); out = []; fase = 0.0
    r = math.log(f1 / f0) if f1 != f0 else 0.0
    for i in range(n):
        u = i / n; f = f0 * math.exp(r * u)
        fase += 2 * math.pi * f / TAXA
        env = (i / (atk * TAXA)) if i < atk * TAXA else math.exp(-queda * u)
        out.append(math.sin(fase) * env * vol)
    return out

# ── espectrograma ────────────────────────────────────────────────────
def _fft(x):
    n = len(x); j = 0; x = list(x)
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit; bit >>= 1
        j |= bit
        if i < j:
            x[i], x[j] = x[j], x[i]
    m = 2
    while m <= n:
        w = cmath.exp(-2j * math.pi / m)
        for k in range(0, n, m):
            wk = 1
            for t in range(m // 2):
                u = x[k + t]; v = x[k + t + m // 2] * wk
                x[k + t] = u + v; x[k + t + m // 2] = u - v; wk *= w
        m <<= 1
    return x

def espectro(a, n=512, hop=256):
    jan = [0.5 - 0.5 * math.cos(2 * math.pi * i / n) for i in range(n)]
    col = []
    for i in range(0, max(1, len(a) - n), hop):
        X = _fft([a[i + k] * jan[k] for k in range(n)])
        col.append([abs(X[k]) for k in range(n // 2)])
    return col

def centroide(a, n=1024):
    X = espectro(a, n, n // 2)
    tot = num = 0.0
    for c in X:
        for k, m in enumerate(c):
            num += k * m; tot += m
    return (num / max(1e-9, tot)) * TAXA / n
