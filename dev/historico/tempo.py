import os, sys, time
sys.path.insert(0, sys.argv[1])
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
import importlib
K = importlib.import_module(sys.argv[2])
poses = list(K.POSE_A.values())
t = time.time()
for p in poses:
    K.montar(p)
t1 = time.time() - t
t = time.time()
for p in poses:
    q = dict(p); q['mugetsu'] = True; q['sobe'] = 1.0; q['cabelo'] = 1.5
    K.bordas(K.montar(q))
t2 = time.time() - t
print(sys.argv[2], 'normal %.1f ms/pose' % (1000 * t1 / len(poses)), 'mugetsu %.1f ms/pose' % (1000 * t2 / len(poses)))
