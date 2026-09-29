"""Roda so a abertura e anota quando cada passo da cena comeca."""
import sys, os, time, runpy, json
PASSOS = set('''_surge _kamae _koiguchi _solta _pula _golpe1 _saca2 _combo _ataque_giro _ataque_mergulho
_ataque_salto _blitz_para _final _fundir _flash_fusao _estoura_casulo _sugar _absorveu _posiciona _trevas
_ergue _golpe_final _abre _para _separa _chiburi _explode _sai _acabou'''.split())
T = []
t0 = [None]
def prof(frame, ev, arg):
    if ev == 'call' and frame.f_code.co_name in PASSOS and frame.f_code.co_filename.endswith('cenas.py'):
        now = time.time()
        if t0[0] is None:
            t0[0] = now
        T.append((round(now - t0[0], 2), frame.f_code.co_name))
import atexit
@atexit.register
def fim():
    json.dump(T, open(os.environ['LINHA_SAIDA'], 'w'))
sys.setprofile(prof)
import threading
threading.setprofile(prof)
sys.argv = [os.path.join(os.path.dirname(__file__), 'tour.py')] + sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
