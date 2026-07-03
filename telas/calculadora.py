"""telas/calculadora.py — TelaCalculadora"""
from kivy.uix.screenmanager import Screen
from kivy.animation import Animation
from kivy.clock import Clock
from efeitos import tremer_tela


class TelaCalculadora(Screen):
    _SAFE      = set('0123456789+-*/.() ')
    _historico = []   # ultimos 3 resultados

    def add_texto(self, t):
        lbl = self.ids.calc_display
        if lbl.text == "ERRO":
            lbl.text  = ""
            lbl.color = (1, 1, 1, 1)
        lbl.text += t
        Animation.cancel_all(lbl, 'color')
        (Animation(color=(0, 0.9, 1, 1), duration=0.05, transition='out_quad') +
         Animation(color=(1, 1, 1, 1),   duration=0.18, transition='out_quad')
         ).start(lbl)

    def backspace(self):
        lbl = self.ids.calc_display
        t   = lbl.text
        if not t or t == "ERRO":
            lbl.text  = ""
            lbl.color = (1, 1, 1, 1)
            return
        lbl.text = t[:-1]
        Animation.cancel_all(lbl, 'color')
        (Animation(color=(1, 0.55, 0, 1), duration=0.05, transition='out_quad') +
         Animation(color=(1, 1, 1, 1),    duration=0.18, transition='out_quad')
         ).start(lbl)

    def limpar(self):
        lbl = self.ids.calc_display
        if not lbl.text:
            return
        Animation.cancel_all(lbl, 'color')
        (Animation(color=(1, 0.1, 0.2, 1), duration=0.06, transition='out_quad') +
         Animation(color=(1, 1, 1, 1),     duration=0.25, transition='out_quad')
         ).start(lbl)
        Clock.schedule_once(lambda _: setattr(lbl, 'text', ''), 0.06)

    def calcular(self):
        # Normaliza: X -> *, DEL -> backspace, / vem direto do botao /
        raw = (self.ids.calc_display.text
               .replace('X', '*')
               .replace('x', '*'))
        lbl = self.ids.calc_display
        if not raw or not all(c in self._SAFE for c in raw):
            lbl.text = "ERRO"
            self._flash_erro(lbl)
            return
        try:
            result = eval(raw, {"__builtins__": {}})
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            lbl.text = str(result)
            # Guardar no historico (max 3)
            self._historico.append(str(result))
            if len(self._historico) > 3:
                self._historico.pop(0)
            tremer_tela(5)
            (Animation(color=(0, 1, 0.8, 1), duration=0.06, transition='out_expo') +
             Animation(color=(0, 0.9, 1, 1), duration=0.08, transition='out_expo') +
             Animation(color=(1, 1, 1, 1),   duration=0.28, transition='in_out_expo')).start(lbl)
        except Exception:
            lbl.text = "ERRO"
            self._flash_erro(lbl)

    def _flash_erro(self, lbl):
        tremer_tela(18)
        (Animation(color=(1, 0.15, 0.2, 1), duration=0.07) +
         Animation(color=(1, 1, 1, 1),      duration=0.45)).start(lbl)
