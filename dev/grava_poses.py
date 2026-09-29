"""Roda a abertura e grava cada pose mostrada (com o tempo) + os passos."""
import sys, os, time, runpy, json
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'
REG = {'poses': [], 'passos': []}
T0 = [None]
PASSOS = set('''_surge _kamae _koiguchi _solta _golpe1 _saca2 _ataque_giro _ataque_mergulho
_ataque_salto _final _fundir _flash_fusao _estoura_casulo _sugar _absorveu _posiciona _trevas
_ergue _golpe_final _abre _para _separa _chiburi _explode _sai _acabou'''.split())


def agora():
    t = time.time()
    if T0[0] is None:
        T0[0] = t
    return round(t - T0[0], 3)


def prof(frame, ev, arg):
    if ev == 'call' and frame.f_code.co_name in PASSOS and frame.f_code.co_filename.endswith('cenas.py'):
        REG['passos'].append((agora(), frame.f_code.co_name))
sys.setprofile(prof)
import kirito as K
_orig = K.KiritoPixel.mostrar


def mostrar(self, p):
    _orig(self, p)
    if T0[0] is not None:
        REG['poses'].append((agora(), id(self), {k: (list(v) if isinstance(v, tuple) else v) for k, v in p.items()},
                             bool(self.espelhar), round(self.escala_x, 3), round(self.rotacao, 1)))
K.KiritoPixel.mostrar = mostrar
import atexit


@atexit.register
def fim():
    json.dump(REG, open(os.environ['POSES_SAIDA'], 'w'))
sys.argv = [os.path.join(os.path.dirname(__file__), 'tour.py')] + sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
