"""Trata as vozes Piper para a vibe do Yoru (voz de golpe especial de anime):
tom levemente mais grave, corpo (dobra desafinada), presenca, compressao
suave e eco curto de 'ativacao de habilidade'.
uso: python voz_yoru.py VOZ [fator_tom] [pasta_saida]"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import audio as A

AQUI = os.path.dirname(os.path.dirname(__file__))
voz = sys.argv[1]
fator = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
saida = sys.argv[3] if len(sys.argv) > 3 else os.path.join(AQUI, 'voz_piper')


def tratar(a):
    a = A.aparar(a, lim=0.01, antes=0.005, depois=0.08)
    if fator != 1.0:
        a = A.reamostrar(a, fator)                    # tom (e timbre) um pouco mais grave
    a = A.hp(a, 90)
    a = A.lp(a, 9000)
    dobra = A.reamostrar(a, 1.012)                    # voz dobrada levemente desafinada: mais cheia
    a = A.mix((a, 0.0, 1.0), (dobra, 0.014, 0.32))
    a = A.saturar(A.ganho(a, 1.6), 1.1)               # compressao/saturacao suave: presenca
    a = A.normalizar(a, -1.0)
    eco = A.mix((a, 0.0, 1.0), (A.lp(a, 3200), 0.12, 0.24), (A.lp(a, 2400), 0.24, 0.12),
                (A.lp(a, 1600), 0.37, 0.05))
    return A.normalizar(A.fade(eco, 0.004, 0.25), -1.0)


for chave in ('starburst', 'stream', 'frase'):
    a = A.ler_arquivo(os.path.join(AQUI, 'voz_piper', f'{voz}_{chave}.wav'))
    b = tratar(a)
    nome = os.path.join(saida, f'{voz}_{chave}_tratada.wav')
    A.escrever(nome, b)
    print(nome, round(A.dur(b), 2), 's pico', round(A.pico_t(b), 3))
