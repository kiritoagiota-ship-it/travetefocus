import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio as A
AQUI = os.path.dirname(os.path.abspath(__file__))
orig = A.aparar(A.ler_arquivo(os.path.join(r'C:\Users\kirit\travetefocus\ferramentas\voz\originais', 'voz_mugetsu.wav')), lim=0.003, antes=0.01, depois=0.08)
VAR = {
    'a': dict(vel=1.05, sat=(1.4, 1.2), dobra=0.18, brilho=0.5, eco=0.22),
    'b': dict(vel=1.06, sat=(1.8, 1.4), dobra=0.12, brilho=0.6, eco=0.2),
    'c': dict(vel=1.04, sat=(1.3, 1.0), dobra=0.0, brilho=0.8, eco=0.25),
    'd': dict(vel=1.08, sat=(2.0, 1.6), dobra=0.0, brilho=0.7, eco=0.18),
}
for n, c in VAR.items():
    v = A.reamostrar(orig, c['vel'])
    br = A.hp(A.lp(v, 5500), 1600)
    cam = [(v, 0.0, 1.0), (br, 0.0, c['brilho'])]
    if c['dobra']:
        cam.append((A.reamostrar(orig, c['vel'] * 1.04), 0.01, c['dobra']))
    base = A.mix(*cam)
    base = A.saturar(A.ganho(A.normalizar(base, -1.0), c['sat'][0]), c['sat'][1])
    eco = A.lp(base, 3500)
    voz = A.mix((base, 0.0, 1.0), (eco, 0.09, c['eco']), (eco, 0.18, c['eco'] * 0.45))
    voz = A.normalizar(A.fade(A.hp(voz, 110), 0.003, 0.18), -0.8)
    A.escrever(os.path.join(r'C:\Users\kirit\travetefocus\ferramentas\saida_testes', n + '.wav'), voz)
    print(n, 'rms %.1f' % A.rms_db(voz))
