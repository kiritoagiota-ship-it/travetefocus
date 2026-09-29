"""Sons proprios dos golpes novos (44,1 kHz mono) em tf_repo/sons/.
Amostras CC0 da Kenney (Impact Sounds e RPG Audio) + sintese."""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(__file__))
import audio as A

ORIG = r'C:\Users\kirit\travetefocus\ferramentas\sons_cc0\wav'
SAIDA = r'C:\Users\kirit\travetefocus\app\sons'
T = A.TAXA


def L(n):
    return A.ler_arquivo(os.path.join(ORIG, n + '.wav'))


def final(nome, a, rms_alvo, lp=11000, hp=50, cauda=0.08):
    a = A.aparar(a, lim=0.002, antes=0.003, depois=0.05)
    if hp:
        a = A.hp(a, hp)
    if lp:
        a = A.lp(a, lp)
    a = A.fade(a, 0.002, cauda)
    a = A.normalizar(a, -1.0)
    g = A.db(rms_alvo - A.rms_db(a))
    if g > 1.0:
        a = A.normalizar(A.saturar(A.ganho(a, g), 1.0), -1.0)
    else:
        a = A.ganho(a, g)
    A.escrever(os.path.join(SAIDA, nome + '.wav'), a)
    print(f"{nome:10s} {A.dur(a):.2f}s pico@{A.pico_t(a):.3f} rms={A.rms_db(a):.1f}dB")


def ruido(d, seed=1):
    return A.ruido_rosa(int(d * T), seed)


def sopro(d, f0, f1, seed=3, vol=1.0):
    """Vento/whoosh: ruido que passa por uma faixa que varre de f0 a f1."""
    n = int(d * T)
    r = ruido(d, seed)
    out = []
    y = 0.0
    for i in range(n):
        u = i / float(n)
        fc = f0 * (f1 / f0) ** u
        a = min(0.99, 2 * math.pi * fc / T)
        y += a * (r[i] - y)
        env = math.sin(math.pi * u) ** 1.5
        out.append(y * env * vol)
    return A.hp(out, 120)


# vidro: estala, trinca e os cacos
vidro = A.mix((L('impactGlass_heavy_000'), 0.0, 1.0), (L('impactGlass_medium_002'), 0.07, 0.7),
              (L('impactGlass_light_003'), 0.16, 0.5), (A.seno(110, 50, 0.16, 0.6, queda=6.0), 0.0, 0.8))
final('vidro', vidro, -14, cauda=0.25)

# cristal trincando (a crisalida): 3 estalos pequenos subindo
cristal = A.mix((L('impactGlass_light_000'), 0.0, 0.8), (L('impactGlass_light_002'), 0.11, 0.9),
                (L('impactGlass_light_004'), 0.2, 1.0))
final('cristal', cristal, -17, cauda=0.2)

# moedas: mao cheia de moedas + brilho de sino
moedas = A.mix((L('handleCoins'), 0.0, 1.0), (L('handleCoins2'), 0.18, 0.8),
               (A.reamostrar(L('impactBell_heavy_002'), 0.5), 0.05, 0.25))
final('moedas', moedas, -16, cauda=0.3)

# papel: o pergaminho sai voando
papel = A.mix((L('bookFlip2'), 0.0, 0.9), (L('cloth2'), 0.03, 0.6), (sopro(0.45, 900, 3500, seed=5, vol=0.5), 0.05, 1.0))
final('papel', papel, -18, cauda=0.2)

# giro: dois "vuum" rapidos (as duas laminas)
giro = A.mix((sopro(0.28, 600, 3000, seed=7), 0.0, 1.0), (sopro(0.28, 500, 2600, seed=8), 0.13, 0.9),
             (A.seno(180, 90, 0.2, 0.3, queda=4.0), 0.02, 0.6))
final('giro', giro, -17, cauda=0.12)

# fitas subindo (casulo): brilho que sobe + vento
fitas = A.mix((sopro(1.1, 300, 5000, seed=11, vol=0.9), 0.0, 1.0),
              (A.seno(440, 880, 1.0, 0.25, queda=1.0, atk=0.3), 0.1, 0.5),
              (A.seno(660, 1320, 0.9, 0.2, queda=1.2, atk=0.3), 0.2, 0.4))
final('fitas', fitas, -18, cauda=0.3)

# trevas: a escuridao se espalhando - onda grave que cresce e some
n = int(1.6 * T)
grave = []
fase = 0.0
for i in range(n):
    u = i / float(n)
    f = 62 - 26 * u
    fase += 2 * math.pi * f / T
    env = min(1.0, u / 0.35) * (1 - max(0.0, (u - 0.6) / 0.4))
    grave.append(math.sin(fase) * env * 0.8)
rumor = A.lp(ruido(1.6, 21), 260)
rumor = [v * min(1.0, i / (0.5 * T)) * (1 - max(0.0, (i / float(len(rumor)) - 0.6) / 0.4)) for i, v in enumerate(rumor)]
trevas = A.mix((grave, 0.0, 1.0), (rumor, 0.0, 1.2), (sopro(1.4, 200, 900, seed=22, vol=0.5), 0.1, 1.0))
final('trevas', trevas, -15, lp=6000, hp=25, cauda=0.3)

# fogo: rumor + estalos aleatorios (crepitar), 3,5 s
d = 3.5
base = A.lp(ruido(d, 31), 700)
chiado = A.hp(A.lp(ruido(d, 32), 5000), 1500)
rnd = random.Random(33)
estalos = [0.0] * int(d * T)
t = 0.02
while t < d - 0.05:
    i0 = int(t * T)
    amp = rnd.uniform(0.3, 1.0)
    for j in range(int(0.004 * T)):
        if i0 + j < len(estalos):
            estalos[i0 + j] += rnd.uniform(-1, 1) * amp * (1 - j / (0.004 * T))
    t += rnd.expovariate(14.0)
estalos = A.hp(estalos, 900)
nn = int(d * T)
ondas = [0.75 + 0.25 * math.sin(2 * math.pi * 1.3 * i / T) * math.sin(2 * math.pi * 0.37 * i / T) for i in range(nn)]
fogo = A.mix(([v * o for v, o in zip(base, ondas)], 0.0, 1.0), (chiado, 0.0, 0.25), (estalos, 0.0, 0.6))
fogo = A.fade(fogo, 0.4, 0.8)
final('fogo', fogo, -20, lp=8000, hp=40, cauda=0.6)
