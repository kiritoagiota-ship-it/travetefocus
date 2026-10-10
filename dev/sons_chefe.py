"""Som do CHEFE da abertura: o RUGIDO (sons/rugido.wav), todo sintetizado.
  rosnado  - onda cheia de harmonicos (dente de serra) descendo de 96 para
             52 Hz, com a "aspereza" de garganta (tremor de 31 Hz que acelera)
             e duas ressonancias de boca (formantes) que abrem e fecham;
  sopro    - ruido pela mesma boca (o ar do berro);
  peso     - um grave de 45 Hz por baixo.
uso: python dev/sons_chefe.py"""
import os
import sys
import math
import random

sys.path.insert(0, os.path.dirname(__file__))
import audio as A                                                       # noqa: E402

SAIDA = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'sons')
T = A.TAXA


def ressoa(a, fc, q):
    """Passa-faixa simples (ressonancia de boca)."""
    w = 2 * math.pi * fc / T
    alfa = math.sin(w) / (2 * q)
    b0, b2 = alfa, -alfa
    a0, a1, a2 = 1 + alfa, -2 * math.cos(w), 1 - alfa
    x1 = x2 = y1 = y2 = 0.0
    out = []
    for x in a:
        y = (b0 * x + b2 * x2 - a1 * y1 - a2 * y2) / a0
        x2, x1 = x1, x
        y2, y1 = y1, y
        out.append(y)
    return out


def rugido(d=1.55, semente=7):
    rnd = random.Random(semente)
    n = int(d * T)
    fase = 0.0
    garg = 0.0
    serra = []
    for i in range(n):
        u = i / float(n)
        f = 96.0 * (52.0 / 96.0) ** (u ** 0.8) * (1 + 0.035 * math.sin(2 * math.pi * 5.5 * u * d))
        f *= 1 + 0.02 * (rnd.random() - 0.5)                    # voz instavel
        fase += f / T
        s = 2.0 * (fase % 1.0) - 1.0
        garg += (31.0 + 22.0 * u) / T                           # aspereza da garganta
        rasp = 0.55 + 0.45 * (1.0 if (garg % 1.0) < 0.55 else -0.4)
        serra.append(s * rasp)
    ar = A.ruido_rosa(n, semente + 1)
    boca = []
    for i in range(n):
        boca.append(serra[i] * 0.8 + ar[i] * 0.55)
    # formantes: "RRROOOAAARRH" - a boca abre (o primeiro sobe) e fecha
    f1 = ressoa(boca, 420.0, 2.2)
    f1b = ressoa(boca, 760.0, 2.6)
    f2 = ressoa(boca, 1350.0, 3.5)
    f3 = ressoa(ar, 2600.0, 2.0)
    grave = A.seno(48.0, 40.0, d, 1.0, queda=1.2, atk=0.06)
    out = []
    for i in range(n):
        u = i / float(n)
        abre = math.sin(math.pi * min(1.0, u / 0.75)) ** 0.8
        env = min(1.0, u / 0.07) * (1.0 if u < 0.62 else max(0.0, 1 - (u - 0.62) / 0.38) ** 1.6)
        v = (f1[i] * (1.5 - 0.5 * abre) + f1b[i] * 1.4 * abre + f2[i] * 0.5 * abre + f3[i] * 0.12 * abre
             + serra[i] * 0.3)
        g = grave[i] if i < len(grave) else 0.0
        out.append((v * 1.6 + g * 0.9) * env)
    out = A.saturar(A.normalizar(out, -3.0), 2.2)
    out = A.lp(A.lp(A.hp(out, 38), 3400), 3400)
    out = A.fade(out, 0.004, 0.25)
    return A.normalizar(out, -1.5)


if __name__ == '__main__':
    a = rugido()
    A.escrever(os.path.join(SAIDA, 'rugido.wav'), a)
    print('rugido %.2fs rms=%.1f dB centroide=%.0f Hz' % (A.dur(a), A.rms_db(a), A.centroide(a)))
