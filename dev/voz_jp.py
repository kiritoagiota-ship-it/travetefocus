"""Trata a voz japonesa (Kokoro jm_kumo) para o Yoru e grava em tf_repo/sons."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import audio as A
ORIG = r'C:\Users\kirit\travetefocus\ferramentas\voz\saida'
SONS = r'C:\Users\kirit\travetefocus\app\sons'


def ler(n):
    return A.ler_arquivo(os.path.join(ORIG, n))


def voz(a, fator=0.97, dobra=0.3, sat=1.1, ganho=1.6, eco=(0.24, 0.12, 0.05), lp=9000, eco_lp=3200):
    a = A.aparar(a, lim=0.01, antes=0.005, depois=0.08)
    if fator != 1.0:
        a = A.reamostrar(a, fator)
    a = A.hp(a, 90)
    a = A.lp(a, lp)
    d = A.reamostrar(a, 1.012)
    a = A.mix((a, 0.0, 1.0), (d, 0.014, dobra))
    a = A.saturar(A.ganho(a, ganho), sat)
    a = A.normalizar(a, -1.0)
    a = A.mix((a, 0.0, 1.0), (A.lp(a, eco_lp), 0.12, eco[0]), (A.lp(a, eco_lp * 0.75), 0.24, eco[1]),
              (A.lp(a, eco_lp * 0.5), 0.37, eco[2]))
    return A.normalizar(A.fade(a, 0.004, 0.2), -1.0)


if __name__ == '__main__':
    saidas = {
        'voz_starburst': voz(ler('jp_starburst_3.wav')),
        'voz_stream': voz(ler('jp_stream_3.wav'), fator=0.96, sat=1.25, ganho=2.0, eco=(0.3, 0.16, 0.08)),
        'voz_mugetsu': voz(ler('jp_mugetsu.wav'), fator=0.9, dobra=0.45, sat=1.05, ganho=1.3, lp=6000,
                           eco=(0.35, 0.25, 0.16), eco_lp=2200),
        'voz_ha': voz(ler('jp_ha.wav'), fator=0.97, sat=1.35, ganho=2.2, eco=(0.15, 0.06, 0.0)),
        'voz_seiya': voz(ler('jp_sei.wav'), fator=0.97, sat=1.3, ganho=2.0, eco=(0.15, 0.06, 0.0)),
        'voz_teya': voz(ler('jp_teya.wav'), fator=0.97, sat=1.35, ganho=2.2, eco=(0.15, 0.06, 0.0)),
    }
    for nome, a in saidas.items():
        A.escrever(os.path.join(SONS, nome + '.wav'), a)
        print(nome, round(A.dur(a), 2), 's  pico', round(A.pico_t(a), 3))
