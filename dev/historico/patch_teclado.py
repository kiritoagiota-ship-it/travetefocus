"""Vibracao em botoes e teclas; teclado com Ç, acento, DEL segurando e
sugestoes de pecas."""
import sys
sys.path.insert(0, __file__.rsplit('\\', 1)[0])
from p import patch

patch(r'C:\Users\kirit\travetefocus\app\efeitos.py', [
    ("from kivy.properties import NumericProperty, ListProperty, StringProperty\n",
     "from kivy.properties import NumericProperty, ListProperty, StringProperty\n"),
    ("import math\nimport random\n\n# Som de clique",
     "import math\nimport random\n\nimport tatil\n\n# Som de clique"),
    # botoes: toque leve (ou toquezinho de tecla, na calculadora)
    ("""    cor_texto    = ListProperty([0.0,  0.90, 1.0,  1.0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # faixa de luz + pulso no contorno a cada toque (todas as subclasses)""",
     """    cor_texto    = ListProperty([0.0,  0.90, 1.0,  1.0])
    tatil        = StringProperty('botao')   # vibracao ao tocar: 'botao', 'tecla' ou ''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # faixa de luz + pulso no contorno a cada toque (todas as subclasses)"""),
    ("""    def on_press(self):
        tocar_click()   # som de clique em todo botão
        Animation.cancel_all(self, 'escala', 'cor_borda')""",
     """    def on_press(self):
        tocar_click()   # som de clique em todo botão
        if self.tatil == 'tecla':
            tatil.tecla()
        elif self.tatil:
            tatil.botao()
        Animation.cancel_all(self, 'escala', 'cor_borda')"""),
    # teclado
    ("""_LINHAS_LETRAS = ['QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM']
""", """_LINHAS_LETRAS = ['QWERTYUIOP', 'ASDFGHJKLÇ', 'ZXCVBNM']

# tecla de acento: troca a ultima letra pela proxima da roda (A -> Á -> Ã -> Â -> À -> A)
_RODAS_ACENTO = ['AÁÃÂÀ', 'EÉÊ', 'IÍ', 'OÓÕÔ', 'UÚ', 'CÇ']
_PROXIMO_ACENTO = {}
for _roda in _RODAS_ACENTO:
    for _i, _ch in enumerate(_roda):
        _prox = _roda[(_i + 1) % len(_roda)]
        _PROXIMO_ACENTO[_ch] = _prox
        _PROXIMO_ACENTO[_ch.lower()] = _prox.lower()
"""),
    ("""        self.target  = target
        self._fechar = fechar
        self.spacing = dp(3)""", """        self.target  = target
        self._fechar = fechar
        self._ev_del = None
        self.spacing = dp(3)"""),
    ("""        if char == 'DEL':
            if t.text:
                t.text = t.text[:-1]
        elif char == 'CLR':
            t.text = ''
        elif char == ' ':
            t.text += ' '
        else:
            t.text += char

    def _press_com_feedback(self, btn, char):
        \"\"\"Feedback visual ao pressionar tecla — flash cyan rapido.\"\"\"
        self._press(char)""", """        if char == 'DEL':
            if t.text:
                t.text = t.text[:-1]
        elif char == 'CLR':
            t.text = ''
        elif char == 'ACENTO':
            ult = t.text[-1:]
            if ult in _PROXIMO_ACENTO:
                t.text = t.text[:-1] + _PROXIMO_ACENTO[ult]
        elif char == ' ':
            t.text += ' '
        else:
            t.text += char
        self._mudou()

    def _mudou(self):
        \"\"\"O texto mudou (as subclasses atualizam as sugestoes).\"\"\"

    # segurar o DEL apaga uma letra atras da outra
    def _segurar_del(self, *_):
        self._soltar_del()
        self._ev_del = Clock.schedule_once(self._repetir_del, 0.42)

    def _repetir_del(self, dt):
        self._ev_del = None
        t = self.target
        if self.parent is None or not t or not t.text:
            return
        self._press('DEL')
        tatil.tecla()
        self._ev_del = Clock.schedule_once(self._repetir_del, 0.06)

    def _soltar_del(self, *_):
        if self._ev_del is not None:
            self._ev_del.cancel()
            self._ev_del = None

    def _press_com_feedback(self, btn, char):
        \"\"\"Feedback ao pressionar tecla — vibracao curtinha e flash cyan.\"\"\"
        tatil.tecla()
        self._press(char)"""),
    ("""    def _key(self, char, font_size='18sp', **kw):
        btn = _BotaoTecla(text=char, font_size=font_size, **kw)
        btn.bind(on_press=lambda b: self._press_com_feedback(b, char))
        return btn
""", """    def _key(self, char, font_size='18sp', rotulo=None, **kw):
        btn = _BotaoTecla(text=rotulo or char, font_size=font_size, **kw)
        btn.bind(on_press=lambda b: self._press_com_feedback(b, char))
        if char == 'DEL':
            btn.bind(on_press=self._segurar_del, on_release=self._soltar_del)
        return btn


def _sem_acento(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c)).lower()


class _LinhaSugestoes(BoxLayout):
    \"\"\"Pecas ja usadas, em cima do teclado de letras: um toque preenche o
    nome. fonte(texto) -> nomes (mais recentes primeiro).\"\"\"

    MAX = 3

    def __init__(self, fonte, ao_escolher, **kwargs):
        kwargs.setdefault('size_hint_y', None)
        kwargs.setdefault('height', dp(42))
        super().__init__(**kwargs)
        self.spacing = dp(5)
        self.fonte = fonte
        self.ao_escolher = ao_escolher

    def atualizar(self, texto):
        try:
            nomes = list(self.fonte(texto or ''))[:self.MAX]
        except Exception as e:
            print(f"[teclado] sugestoes: {e}")
            nomes = []
        self.clear_widgets()
        for n in nomes:
            b = _BotaoTecla(text=n, font_size='15sp', shorten=True, halign='center', valign='middle')
            b.font_name = 'rajdhani.ttf'
            b.color = [0.75, 0.55, 1, 1]
            b.bind(size=lambda w, s: setattr(w, 'text_size', (max(1, s[0] - dp(10)), s[1])))
            b.bind(on_press=lambda w, n=n: self._escolher(w, n))
            self.add_widget(b)

    def _escolher(self, w, nome):
        tatil.tecla()
        self.ao_escolher(nome)
"""),
    ("""class TecladoLetras(_TecladoBase):
    \"\"\"
    Teclado SAO apenas com letras A-Z.
    Font 18sp — legivel nos botoes ~36dp da linha QWERTY.
    \"\"\"

    def __init__(self, target, fechar=None, **kwargs):
        kwargs['height'] = dp(252)
        super().__init__(target, fechar=fechar, **kwargs)

        for linha in _LINHAS_LETRAS:
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(3))
            for c in linha:
                row.add_widget(self._key(c, font_size='18sp'))
            self.add_widget(row)

        # Linha especial: CLR | espaço | DEL | OK
        spc = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        spc.add_widget(self._key('CLR', font_size='12sp', size_hint_x=0.18))
        spc.add_widget(self._key(' ',   font_size='12sp', size_hint_x=0.44))
        spc.add_widget(self._key('DEL', font_size='12sp', size_hint_x=0.18))
        spc.add_widget(self._key('OK',  font_size='14sp', size_hint_x=0.20))
        self.add_widget(spc)
""", """class TecladoLetras(_TecladoBase):
    \"\"\"
    Teclado SAO com letras A-Z, Ç e a tecla de acento (´ ~: troca a ultima
    letra por A -> Á -> Ã -> Â -> À...). Font 18sp — legivel nos botoes
    ~36dp da linha QWERTY. sugestoes(texto) -> nomes: linha de pecas ja
    usadas em cima das letras.
    \"\"\"

    def __init__(self, target, fechar=None, sugestoes=None, **kwargs):
        kwargs['height'] = dp(252) + (dp(46) if sugestoes else 0)
        super().__init__(target, fechar=fechar, **kwargs)
        self._sug = None
        if sugestoes:
            self._sug = _LinhaSugestoes(sugestoes, self._usar_sugestao)
            self.add_widget(self._sug)
            self._sug.atualizar(target.text if target else '')

        for linha in _LINHAS_LETRAS:
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(3))
            for c in linha:
                row.add_widget(self._key(c, font_size='18sp'))
            if linha == _LINHAS_LETRAS[-1]:
                row.add_widget(self._key('ACENTO', font_size='16sp', rotulo='´ ~', size_hint_x=1.6))
            self.add_widget(row)

        # Linha especial: CLR | espaço | DEL | OK
        spc = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        spc.add_widget(self._key('CLR', font_size='12sp', size_hint_x=0.18))
        spc.add_widget(self._key(' ',   font_size='12sp', size_hint_x=0.44))
        spc.add_widget(self._key('DEL', font_size='12sp', size_hint_x=0.18))
        spc.add_widget(self._key('OK',  font_size='14sp', size_hint_x=0.20))
        self.add_widget(spc)

    def _mudou(self):
        if self._sug is not None and self.target is not None:
            self._sug.atualizar(self.target.text)

    def _usar_sugestao(self, nome):
        if self.target is not None:
            self.target.text = nome
        self._mudou()
"""),
])
print('ok')
