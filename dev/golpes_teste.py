"""Testa as cenas curtas do Yoru numa tela falsa (itens de lista) e captura
quadros. uso: python -u golpes_teste.py LARG ALT SAIDA DENS cena1,cena2,..."""
import os, sys, json, time
LARG, ALT, SAIDA, DENS = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
CENAS = sys.argv[5].split(',')
os.makedirs(SAIDA, exist_ok=True)
os.environ['KIVY_METRICS_DENSITY'] = DENS
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_LOG_MODE', 'PYTHON')
REPO = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
sys.path.insert(0, REPO)
os.chdir(REPO)
from kivy.config import Config
Config.set('graphics', 'width', str(LARG))
Config.set('graphics', 'height', str(ALT))
Config.set('graphics', 'resizable', '0')
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.metrics import dp
import som
som.tocar = lambda *a, **k: None
som.precarregar = lambda *a, **k: None
import cenas
cenas._som = lambda nome: None

LOG = {'quadros': [], 'erros': []}
T0 = [time.time()]


def foto(rot):
    try:
        caminho = Window.screenshot(name=os.path.join(SAIDA, 'q.png'))
        LOG['quadros'].append([round(time.time() - T0[0], 3), rot, os.path.basename(caminho)])
    except Exception as e:
        LOG['erros'].append(str(e))


class T(App):
    def build(self):
        raiz = FloatLayout()
        self.itens = []
        for i in range(6):
            b = Button(text=f'  Item {i + 1}   ·   120 un.   ·   +360 XP', size_hint=(0.9, None), height=dp(46),
                       pos_hint={'center_x': 0.5, 'top': 0.8 - i * 0.09},
                       background_color=(0.1, 0.2, 0.35, 1))
            raiz.add_widget(b)
            self.itens.append(b)
        return raiz

    def on_start(self):
        Clock.schedule_once(lambda dt: self.roteiro(0), 1.0)

    def roteiro(self, i):
        if i >= len(CENAS):
            Clock.schedule_once(lambda dt: self.stop(), 1.0)
            return
        nome = CENAS[i]
        alvo = self.itens[1 + i % 4]
        alvo.opacity = 1
        T0[0] = time.time()
        passo = float(os.environ.get('PASSO_FOTO', '0.05'))
        for j in range(int(float(os.environ.get('DUR_FOTO', '3.0')) / passo)):
            Clock.schedule_once(lambda dt, j=j: foto(f'{nome} {j * passo:.2f}s'), j * passo)
        if nome in ('iai', 'estocada', 'x'):
            cenas.kirito_fatiar(alvo, lambda: None, tipo=nome)
        elif nome == 'carimbo':
            cenas.kirito_carimbo(alvo, lambda: None)
        elif nome == 'vitoria':
            cenas.kirito_vitoria(self.root)
        elif nome == 'pergaminho':
            cenas.kirito_pergaminho(alvo, lambda: None)
        elif nome == 'nivel':
            cenas.kirito_nivel(alvo)
        elif nome == 'meta':
            cenas.kirito_meta(alvo)
        Clock.schedule_once(lambda dt: self.roteiro(i + 1), float(os.environ.get('INTERVALO', '4.0')))

    def on_stop(self):
        json.dump(LOG, open(os.path.join(SAIDA, 'log.json'), 'w'), ensure_ascii=False)


T().run()
