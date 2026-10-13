"""Mostra o chefe (chefe.py) tocando os movimentos numa janela do tamanho do
celular e tira fotos: confere a montagem das pecas NO APP (a previa do PC,
chefe_rig.py gif, usa as mesmas contas mas outro desenhista).
uso: python dev/chefe_teste.py PASTA [clipe1,clipe2,...] [fotos_por_clipe=6]"""
import os
import sys

SAIDA = sys.argv[1]
os.makedirs(SAIDA, exist_ok=True)
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_LOG_MODE', 'PYTHON')
os.environ['KIVY_METRICS_DENSITY'] = '1.75'
from kivy.config import Config  # noqa: E402
Config.set('graphics', 'width', '720')
Config.set('graphics', 'height', '1560')
Config.set('graphics', 'resizable', '0')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(sys.path[0])
from kivy.app import App  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.uix.widget import Widget  # noqa: E402
from kivy.graphics import Color, Rectangle  # noqa: E402
import chefe as CH  # noqa: E402

CLIPES = sys.argv[2].split(',') if len(sys.argv) > 2 and sys.argv[2] else list(CH.CP.clipes())
N = int(sys.argv[3]) if len(sys.argv) > 3 else 6


class T(App):
    def build(self):
        raiz = Widget()
        with raiz.canvas:
            Color(0.03, 0.03, 0.06, 1)
            Rectangle(pos=(0, 0), size=(720, 1560))
            Color(0.25, 0.25, 0.35, 1)
            Rectangle(pos=(0, 499), size=(720, 1))
        self.b = CH.ChefePixel(te=1.0)
        self.b.ancorar(430, 500)
        raiz.add_widget(self.b)
        passos = []
        t = 0.6
        for nome in CLIPES:
            dur = self.b.duracao(nome)
            passos.append((t, lambda n=nome: self.b.tocar(n, loop=True)))
            for k in range(N):
                passos.append((t + dur * (k + 0.5) / N, lambda n=nome, k=k: self.foto('%s_%d' % (n, k))))
            t += dur + 0.1
        for quando, fn in passos:
            Clock.schedule_once(lambda dt, fn=fn: fn(), quando)
        Clock.schedule_once(lambda dt: self.stop(), t + 0.4)
        return raiz

    def foto(self, nome):
        Window.screenshot(name=os.path.join(SAIDA, nome + '.png'))


T().run()
