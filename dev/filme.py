"""Filma a abertura (ou a entrada rapida) quadro a quadro com o RELOGIO
SIMULADO: cada quadro vale 1/60 s exato, entao as fotos nao atrasam a
animacao. Anota em cada quadro o que cada Yoru na tela fez: desenho novo,
deslizou (andou sem mudar o desenho), girou, esticou...

uso (Git Bash, em app/):
  CENA=abertura SEG=22 CADA=2 TOUR_PY=dev/filme.py bash dev/tour.sh 720 1560 SAIDA 1.75
  CENA=rapida ...
CADA=N: guarda 1 foto a cada N quadros (0 = so o registro, sem fotos).
Saida: f00000.png..., filme.json (quadros, sons, yorus por quadro)."""
import os
import sys
import json
import time

LARG, ALT, SAIDA = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
DENS = sys.argv[4] if len(sys.argv) > 4 else None
CENA = os.environ.get('CENA', 'abertura')
SEG = float(os.environ.get('SEG', '22'))
CADA = int(os.environ.get('CADA', '2'))
REPO = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
os.makedirs(SAIDA, exist_ok=True)
if DENS:
    os.environ['KIVY_METRICS_DENSITY'] = DENS
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_LOG_MODE', 'PYTHON')

pasta_app = os.path.join(os.environ['APPDATA'], 'travete')
os.makedirs(pasta_app, exist_ok=True)
if CENA == 'rapida':
    with open(os.path.join(pasta_app, '.tf_session'), 'w') as f:
        f.write(str(time.time()))

from kivy.config import Config  # noqa: E402
Config.set('graphics', 'width', str(LARG))
Config.set('graphics', 'height', str(ALT))
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'maxfps', '0')

sys.path.insert(0, REPO)
os.chdir(REPO)
import main  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.app import App  # noqa: E402
from kivy.graphics.opengl import glReadPixels, GL_RGBA, GL_UNSIGNED_BYTE  # noqa: E402
from PIL import Image  # noqa: E402
import som  # noqa: E402
import cenas  # noqa: E402
import kirito as K  # noqa: E402

Window.size = (LARG, ALT)

# ── relogio simulado: 1/60 s por quadro, sempre ─────────────────────
SIM = [None]
_tempo_real = Clock.time
Clock._max_fps = 0
Clock.time = lambda: SIM[0] if SIM[0] is not None else _tempo_real()
_pre = Clock.pre_idle


def _pre_idle():
    if SIM[0] is not None:
        SIM[0] += 1 / 60.
    _pre()


Clock.pre_idle = _pre_idle

LOG = {'quadros': [], 'sons': [], 'fases': [], 'erros': []}
Q = [0]              # quadro atual
INI = [None]         # quadro em que a cena comecou


def fase(nome):
    LOG['fases'].append([Q[0], nome])
    print(f'[filme] q{Q[0]:5d} {nome}')


# sons: so anota (quando e qual)
som.tocar = lambda acao, *a, **k: LOG['sons'].append([Q[0], acao])
som.precarregar = lambda *a, **k: None
_som_cena = cenas._som
cenas._som = lambda nome: LOG['sons'].append([Q[0], nome])


def _yorus():
    lt = App.get_running_app().root.ids.sm.get_screen('loading')
    out = []
    for w in lt.walk(restrict=False):
        if isinstance(w, K.KiritoPixel):
            out.append(w)
    return out


def _quadro(*_):
    Q[0] += 1
    if INI[0] is None:
        return
    rel = Q[0] - INI[0]
    reg = []
    for i, k in enumerate(_yorus()):
        try:
            ax, ay = k.ancora()
            reg.append({'i': id(k) % 100000, 'x': round(ax, 1), 'y': round(ay, 1),
                        'rot': round(k.rotacao, 1), 'ex': round(k.escala_x, 3), 'ey': round(k.escala_y, 3),
                        'esp': bool(k.espelhar), 'op': round(k.opacity, 2),
                        'des': hash(k._ult_chave) % 10 ** 9, 'ps': k.ps,
                        'cam': [hash(c) % 10 ** 9 for c in (k._ult_chave[0] if k._ult_chave else ())],
                        'mug': bool(k._base.get('mugetsu')), 'pausa': round(k._pausa, 3)})
        except Exception as e:
            LOG['erros'].append(f'yoru: {e}')
    LOG['quadros'].append([rel, reg])
    if CADA and rel % CADA == 0:
        try:
            w, h = Window.size
            dados = glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)
            im = Image.frombytes('RGBA', (w, h), dados).transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
            im.save(os.path.join(SAIDA, f'f{rel:05d}.png'), compress_level=1)
        except Exception as e:
            LOG['erros'].append(f'foto: {e}')
    if rel >= SEG * 60:
        fim()


Window.bind(on_flip=_quadro)


def fim(*_):
    with open(os.path.join(SAIDA, 'filme.json'), 'w', encoding='utf-8') as f:
        json.dump(LOG, f)
    print('[filme] fim', len(LOG['quadros']), 'quadros', len(LOG['erros']), 'erros')
    App.get_running_app().stop()


def campo():
    from kivy.uix.popup import Popup
    from kivy.uix.textinput import TextInput
    for w in Window.children:
        if isinstance(w, Popup):
            for c in w.walk():
                if isinstance(c, TextInput):
                    return c
    return None


def esperar_cena(dt):
    lt = App.get_running_app().root.ids.sm.get_screen('loading')
    if getattr(lt, '_cena', None) is None:
        Clock.schedule_once(esperar_cena, 0)
        return
    INI[0] = Q[0]
    fase('cena comecou')


def pin(dt):
    c = campo()
    if c is None:
        Clock.schedule_once(pin, 0.1)
        return
    c.text = '2004'
    Clock.schedule_once(lambda dt: c.dispatch('on_text_validate'), 0.3)
    Clock.schedule_once(esperar_cena, 0.5)


def inicio(dt):
    SIM[0] = _tempo_real()
    if CENA == 'rapida':
        Clock.schedule_once(esperar_cena, 0)
    else:
        Clock.schedule_once(pin, 0.5)
    Clock.schedule_once(fim, 120)


Clock.schedule_once(inicio, 0.3)
main.TraveteApp().run()
