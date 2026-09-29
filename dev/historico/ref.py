import os, sys, pickle
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
import kirito as K
out = []
for n in ('fund_alto', 'evo_alto', 'evo_carga', 'guarda', 'dupla', 'corta1'):
    for luz in (0.0, 0.5, 1.0):
        for mug in (False, True):
            q = dict(K.POSE_A[n]); q['mugetsu'] = mug; q['sobe'] = 1.0 if mug else 0.0; q['luz'] = luz
            K._CACHE.clear()
            ch, item = K._gerar_imagem(q)
            out.append((K.montar(q), item[0], item[1], item[3]))
pickle.dump(out, open(sys.argv[1], 'wb'))
