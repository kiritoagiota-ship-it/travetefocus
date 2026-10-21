"""Gera as imagens do Yoru para os cards de aviso (res_notif/yoru_*.png):
o busto do Yoru de verdade (KiritoPixel) em cada pose, fundo transparente.
uso: python dev/notif_yoru.py [pasta_previa]"""
import os
import sys
os.environ.setdefault('KIVY_LOG_MODE', 'PYTHON')
os.environ['KIVY_NO_ARGS'] = '1'
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
from kivy.config import Config  # noqa: E402
Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '300')
from kivy.app import App  # noqa: E402
from kivy.uix.floatlayout import FloatLayout  # noqa: E402
from kivy.uix.stencilview import StencilView  # noqa: E402
from kivy.clock import Clock  # noqa: E402
import kirito as K  # noqa: E402

LADO = 192
POSES = {'guarda': 'guarda', 'meta': 'salto_fim', 'vitoria': 'vitoria', 'susto': 'susto'}


class _A(App):
    def build(self):
        r = FloatLayout()
        self.caixas = {}
        for i, (nome, pose) in enumerate(POSES.items()):
            sv = StencilView(size_hint=(None, None), size=(LADO, LADO), pos=(10 + i * (LADO + 20), 50))
            r.add_widget(sv)
            k = K.KiritoPixel(ps=12)
            sv.add_widget(k)
            k.mostrar(dict(K.POSE_A[pose]))
            ol = K.olhos_texel(k._pose)[0]
            lx, ly = k._local_texel(*ol)
            k.pos = (int(sv.x + LADO * 0.5 - lx), int(sv.y + LADO * 0.6 - ly))
            self.caixas[nome] = sv
        Clock.schedule_once(self.gravar, 1.0)
        return r

    def gravar(self, dt):
        destino = os.path.join(RAIZ, 'res_notif')
        for nome, sv in self.caixas.items():
            sv.export_to_png(os.path.join(destino, f'yoru_{nome}.png'))
            print('ok', nome)
        self.stop()


_A().run()
