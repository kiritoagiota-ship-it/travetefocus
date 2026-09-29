"""Tocar na tela pula a abertura (a completa e a entrada rapida), com a
dica 'toque para pular' piscando embaixo."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'telas', 'loading.py'), [
    ("""        self._cena           = None
        self._kpin           = None
""", """        self._cena           = None
        self._kpin           = None
        self._fim_titulo     = None     # fecha a abertura (usado ao pular)
        self._pular_ok       = False
        self._dica_pular     = None
"""),
    ("""    def on_leave(self, *_):
        self._typing_ativo = False
        self._parar_particulas_dados()
""", """    def on_leave(self, *_):
        self._typing_ativo = False
        self._parar_particulas_dados()
        self._pular_ok = False
        self._fim_titulo = None
        self._tirar_dica_pular()
"""),
    ("""        def _fim():
            if feito[0] or not self._typing_ativo:
                return
            feito[0] = True
            try:""", """        def _fim():
            if feito[0] or not self._typing_ativo:
                return
            feito[0] = True
            self._pular_ok = False
            self._fim_titulo = None
            self._tirar_dica_pular()
            try:"""),
    ("""        except Exception as e:
            print(f"[loading] cena do titulo ignorada: {e}")
            t.text = "TRAVETE FOCUS"
            _fim()
""", """        except Exception as e:
            print(f"[loading] cena do titulo ignorada: {e}")
            t.text = "TRAVETE FOCUS"
            _fim()
            return
        if not feito[0]:
            # um toque na tela pula a abertura (liberado um instante depois,
            # para o toque do VERIFICAR nao pular sem querer)
            self._fim_titulo = _fim
            Clock.schedule_once(self._liberar_pulo, 0.8)

    # ── Pular a abertura ───────────────────────────────────────────────────

    def _liberar_pulo(self, dt=0):
        if self._cena is None or self._fim_titulo is None or not self._typing_ativo:
            return
        self._pular_ok = True
        try:
            dica = Label(
                text="toque para pular", font_name="rajdhani.ttf", font_size="14sp",
                color=(0.55, 0.85, 1, 1), size_hint=(None, None), size=(dp(220), dp(26)),
                halign="center", valign="middle", opacity=0)
            dica.text_size = dica.size
            dica.pos = ((self.width - dica.width) / 2.0, dp(22))
            self.add_widget(dica)
            self._dica_pular = dica
            pisca = (Animation(opacity=0.7, duration=0.7, transition='in_out_sine') +
                     Animation(opacity=0.3, duration=0.9, transition='in_out_sine'))
            pisca.repeat = True
            pisca.start(dica)
        except Exception as e:
            print(f"[loading] dica pular: {e}")

    def _tirar_dica_pular(self):
        dica, self._dica_pular = self._dica_pular, None
        if dica is None:
            return
        try:
            Animation.cancel_all(dica)
            if dica.parent is not None:
                dica.parent.remove_widget(dica)
        except Exception:
            pass

    def on_touch_down(self, touch):
        if self._pular_ok and self._cena is not None and self._fim_titulo is not None:
            self._pular_abertura()
            return True
        return super().on_touch_down(touch)

    def _pular_abertura(self):
        \"\"\"Corta a cena na hora: o titulo aparece pronto e segue para o menu.\"\"\"
        self._pular_ok = False
        fim, self._fim_titulo = self._fim_titulo, None
        try:
            from cenas import limpar_cena
            limpar_cena(self._cena)
        except Exception as e:
            print(f"[loading] pular: {e}")
        self._cena = None
        try:
            t = self.ids.titulo_label
            t.text = "TRAVETE FOCUS"
            t.opacity = 0
            Animation(opacity=1, duration=0.25, transition='out_quad').start(t)
        except Exception:
            pass
        tatil.botao()
        if fim is not None:
            fim()
"""),
])
print('ok')
