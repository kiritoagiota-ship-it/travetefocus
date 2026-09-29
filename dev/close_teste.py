"""Mostra os 3 closes numa janela do tamanho do celular e captura quadros."""
import os, sys
LARG, ALT, SAIDA = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
os.makedirs(SAIDA, exist_ok=True)
os.environ['KIVY_METRICS_DENSITY'] = sys.argv[4]
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_LOG_MODE', 'PYTHON')
REPO = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
sys.path.insert(0, REPO); os.chdir(REPO)
from kivy.config import Config
Config.set('graphics', 'width', str(LARG)); Config.set('graphics', 'height', str(ALT)); Config.set('graphics', 'resizable', '0')
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
import som
som.tocar = lambda *a, **k: None
som.precarregar = lambda *a, **k: None
import cenas
cenas._som = lambda n: None
fotos = []
class T(App):
    def build(self):
        Window.clearcolor = (0.02, 0.02, 0.05, 1)
        return FloatLayout()
    def on_start(self):
        for i, tipo in enumerate(('normal', 'poder', 'mugetsu')):
            Clock.schedule_once(lambda dt, t=tipo: cenas.close_rosto(self.root, t, dur=0.85), 0.5 + i * 1.2)
            for j in range(0, 18):
                Clock.schedule_once(lambda dt, n=f'{tipo}_{j:02d}': Window.screenshot(name=os.path.join(SAIDA, n + '.png')),
                                    0.5 + i * 1.2 + j * 0.05)
        Clock.schedule_once(lambda dt: self.stop(), 4.5)
T().run()
