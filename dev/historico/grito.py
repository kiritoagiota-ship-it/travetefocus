"""'Mugetsu' gritado: mais agudo e rapido, presenca, saturacao, dobra de
voz e eco curto. Gera tf_repo/sons/voz_mugetsu.wav a partir do original."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio as A
AQUI = os.path.dirname(os.path.abspath(__file__))
orig = A.ler_arquivo(os.path.join(AQUI, '..', 'sons_bak', 'voz_mugetsu.wav'))
orig = A.aparar(orig, lim=0.003, antes=0.01, depois=0.08)
print('original %.2fs rms %.1f' % (A.dur(orig), A.rms_db(orig)))
v = A.reamostrar(orig, 1.09)                       # mais agudo e rapido (tensao)
brilho = A.hp(A.lp(v, 5200), 1400)                 # presenca (a voz corta o barulho)
dobra = A.reamostrar(orig, 1.13)                   # segunda voz levemente acima (grito com forca)
base = A.mix((v, 0.0, 1.0), (brilho, 0.0, 0.7), (dobra, 0.012, 0.35))
base = A.saturar(A.ganho(A.normalizar(base, -1.0), 2.4), 2.2)   # aspereza do grito
eco = A.lp(base, 3500)
voz = A.mix((base, 0.0, 1.0), (eco, 0.085, 0.32), (eco, 0.17, 0.16), (eco, 0.26, 0.07))
voz = A.hp(voz, 110)
voz = A.fade(voz, 0.003, 0.18)
voz = A.normalizar(voz, -0.8)
A.escrever(os.path.join(r'C:\Users\kirit\travetefocus\app', 'sons', 'voz_mugetsu.wav'), voz)
print('grito %.2fs rms %.1f pico@%.2f' % (A.dur(voz), A.rms_db(voz), A.pico_t(voz)))
