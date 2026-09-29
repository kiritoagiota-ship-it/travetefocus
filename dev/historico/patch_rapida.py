import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
T = os.path.dirname(os.path.abspath(__file__))
balao = open(os.path.join(T, 'balao.txt'), encoding='utf-8').read()
rapida = open(os.path.join(T, 'entrada_rapida.txt'), encoding='utf-8').read()
patch(os.path.join(A, 'cenas.py'), [
    ("from kivy.metrics import dp\n", "from kivy.metrics import dp, sp\n"),
    ("# ═══════════════════════════════════════════════════════════════════\n#  TITULO ESCRITO PELA ESPADA\n",
     balao + "# ═══════════════════════════════════════════════════════════════════\n#  TITULO ESCRITO PELA ESPADA\n"),
    ("def limpar_cena(camada):\n", rapida + "def limpar_cena(camada):\n"),
])
patch(os.path.join(A, 'telas', 'loading.py'), [
    ("""        Animation(opacity=1, duration=0.3, transition='out_expo').start(self.ids.barra_loading)
        Animation(build_progress=1.0, duration=1.0, transition='out_expo').start(self.reator)
        Animation(progresso=100, duration=1.0).start(self.ids.barra_loading)

        Clock.schedule_once(lambda dt: self.animar_materializacao(), 0.9)""",
     """        Animation(opacity=1, duration=0.3, transition='out_expo').start(self.ids.barra_loading)
        Animation(build_progress=1.0, duration=0.6, transition='out_expo').start(self.reator)
        Animation(progresso=100, duration=0.6).start(self.ids.barra_loading)

        # senha ainda valendo: entrada rapida (a animacao inteira so depois do PIN)
        Clock.schedule_once(lambda dt: self.animar_materializacao(rapida=True), 0.45)"""),
    ("""    def animar_materializacao(self):
        \"\"\"O Kirito surge numa borda, pula e escreve TRAVETE FOCUS com o
        rastro das espadas (cenas.cena_titulo). Depois: espadas holograficas,
        versao e menu. Se a cena falhar, o titulo aparece direto.\"\"\"""",
     """    def animar_materializacao(self, rapida=False):
        \"\"\"O Yoru escreve TRAVETE FOCUS com as espadas: a abertura inteira
        (cenas.cena_titulo) logo depois da senha; com a senha ainda valendo,
        a entrada rapida (cenas.cena_entrada_rapida). Depois: espadas
        holograficas, versao e menu. Se a cena falhar, o titulo aparece
        direto.\"\"\""""),
    ("""        try:
            from cenas import cena_titulo
            self._cena = cena_titulo(self, t, on_fim=_fim, texto="TRAVETE FOCUS")""",
     """        try:
            if rapida:
                from cenas import cena_entrada_rapida
                self._cena = cena_entrada_rapida(self, t, on_fim=_fim, texto="TRAVETE FOCUS")
            else:
                from cenas import cena_titulo
                self._cena = cena_titulo(self, t, on_fim=_fim, texto="TRAVETE FOCUS")"""),
])
print('ok')
