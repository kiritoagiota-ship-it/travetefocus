"""Memorias: cada lote de 30 e montado 8 por quadro (nenhum quadro trava) e a
lista fica parada no lugar enquanto o lote cresce embaixo."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'telas', 'memorias.py'), [
    ('''        cont  = self.ids.memorias_container
        for child in list(cont.children):
            Animation.cancel_all(child)
        cont.clear_widgets()''', '''        cont  = self.ids.memorias_container
        self._cancelar_lote()                 # lote de antes ainda montando
        for child in list(cont.children):
            Animation.cancel_all(child)
        cont.clear_widgets()'''),
    ("""PAGINA = 30          # turnos desenhados de cada vez (anos de dados abrem rapido)
""", """PAGINA = 30          # turnos desenhados de cada vez (anos de dados abrem rapido)
POR_QUADRO = 8       # ... montados aos poucos, alguns por quadro
"""),
    ("""        try:
            if hasattr(self, "_filtro_ev") and self._filtro_ev:
                self._filtro_ev.cancel()
                self._filtro_ev = None
        except Exception:
            pass

    def on_kv_post(self, *_):
        self._pendentes = []
        self._max_t = 0
        self._btn_mais = None
        self.ids.lista_scroll.bind(scroll_y=self._ao_rolar)
""", """        try:
            if hasattr(self, "_filtro_ev") and self._filtro_ev:
                self._filtro_ev.cancel()
                self._filtro_ev = None
        except Exception:
            pass
        self._cancelar_lote()

    def on_kv_post(self, *_):
        self._pendentes = []
        self._max_t = 0
        self._btn_mais = None
        self._lote_ev = None
        self._ancora = None
        self._carregando = False
        self.ids.lista_scroll.bind(scroll_y=self._ao_rolar)
        self.ids.memorias_container.bind(height=self._manter_ancora)
"""),
    ("""        # so os PAGINA mais recentes agora; o resto entra ao rolar ate o fim
        self._max_t = max_t
        self._pendentes = list(reversed(mems))
        self._btn_mais = None
        entrada_cascata(self._desenhar_lote())
        try:
            self.ids.lista_scroll.scroll_y = 1
        except Exception:
            pass
""", """        # so os PAGINA mais recentes agora; o resto entra ao rolar ate o fim
        self._max_t = max_t
        self._pendentes = list(reversed(mems))
        self._btn_mais = None
        self._desenhar_lote(ancora=0.0)       # comeca no topo
"""),
    ("""    def _desenhar_lote(self):
        \"\"\"Poe mais PAGINA turnos no fim da lista (e o botao 'mais' se sobrar).\"\"\"
        cont = self.ids.memorias_container
        if self._btn_mais is not None:
            cont.remove_widget(self._btn_mais)
            self._btn_mais = None
        lote, self._pendentes = self._pendentes[:PAGINA], self._pendentes[PAGINA:]
        novos = [self._item(m) for m in lote]
        for b in novos:
            cont.add_widget(b)
        if self._pendentes:
            n = len(self._pendentes)
            b = BotaoAngular(text=f"MOSTRAR MAIS  ({n} {'turno' if n == 1 else 'turnos'})",
                             size_hint_y=None, height=dp(46), font_size="11sp")
            b.bind(on_release=lambda *_: self._carregar_mais())
            cont.add_widget(b)
            self._btn_mais = b
        return novos

    def _ao_rolar(self, sv, y):
        # chegou perto do fim da lista: carrega o proximo lote sozinho
        if y <= 0.04 and self._pendentes and not getattr(self, '_carregando', False):
            self._carregando = True
            Clock.schedule_once(lambda dt: self._carregar_mais(), 0)

    def _carregar_mais(self):
        sv, cont = self.ids.lista_scroll, self.ids.memorias_container
        try:
            if not self._pendentes:
                return
            # quantos pixels do topo a pessoa estava: continua no mesmo lugar
            ancora = (1.0 - sv.scroll_y) * max(0.0, cont.height - sv.height)
            novos = self._desenhar_lote()
            entrada_cascata(novos, atraso_max=0.25)

            def _manter(*_):
                cont.unbind(height=_manter)
                faixa = cont.height - sv.height
                if faixa > 0:
                    sv.scroll_y = max(0.0, min(1.0, 1.0 - ancora / faixa))
                self._carregando = False
            cont.bind(height=_manter)
        except Exception as e:
            print(f"[memorias] carregar mais: {e}")
            self._carregando = False
""", """    def _cancelar_lote(self):
        ev, self._lote_ev = getattr(self, '_lote_ev', None), None
        if ev is not None:
            ev.cancel()
        self._ancora = None
        self._carregando = False

    def _desenhar_lote(self, ancora):
        \"\"\"Poe mais PAGINA turnos no fim da lista, POR_QUADRO por quadro (e o
        botao 'mais' se sobrar). ancora: pixels do topo da lista ate a vista,
        mantidos enquanto a lista cresce embaixo.\"\"\"
        cont = self.ids.memorias_container
        self._cancelar_lote()
        self._carregando = True
        self._ancora = ancora
        if self._btn_mais is not None:
            cont.remove_widget(self._btn_mais)
            self._btn_mais = None
        lote, self._pendentes = self._pendentes[:PAGINA], self._pendentes[PAGINA:]
        fila, novos = list(lote), []

        def _passo(dt=0):
            try:
                parte, fila[:] = fila[:POR_QUADRO], fila[POR_QUADRO:]
                for m in parte:
                    b = self._item(m)
                    b.opacity = 0                  # a cascata acende no fim
                    cont.add_widget(b)
                    novos.append(b)
                if fila:
                    self._lote_ev = Clock.schedule_once(_passo, 0)
                    return
                self._lote_ev = None
                if self._pendentes:
                    n = len(self._pendentes)
                    b = BotaoAngular(text=f"MOSTRAR MAIS  ({n} {'turno' if n == 1 else 'turnos'})",
                                     size_hint_y=None, height=dp(46), font_size="11sp")
                    b.bind(on_release=lambda *_: self._carregar_mais())
                    cont.add_widget(b)
                    self._btn_mais = b
                entrada_cascata(novos, atraso_max=0.4)
                # solta a ancora depois que o layout assentar
                Clock.schedule_once(lambda dt: self._soltar_ancora(), 0.12)
            except Exception as e:
                print(f"[memorias] lote: {e}")
                self._soltar_ancora()
        _passo()

    def _manter_ancora(self, cont, h):
        if self._ancora is None:
            return
        sv = self.ids.lista_scroll
        faixa = h - sv.height
        sv.scroll_y = max(0.0, min(1.0, 1.0 - self._ancora / faixa)) if faixa > 0 else 1.0

    def _soltar_ancora(self):
        self._ancora = None
        self._carregando = False

    def _ao_rolar(self, sv, y):
        # chegou perto do fim da lista: carrega o proximo lote sozinho
        if y <= 0.04 and self._pendentes and not self._carregando:
            self._carregando = True
            Clock.schedule_once(lambda dt: self._carregar_mais(), 0)

    def _carregar_mais(self):
        sv, cont = self.ids.lista_scroll, self.ids.memorias_container
        try:
            if not self._pendentes:
                self._carregando = False
                return
            # quantos pixels do topo a pessoa estava: continua no mesmo lugar
            self._desenhar_lote(ancora=(1.0 - sv.scroll_y) * max(0.0, cont.height - sv.height))
        except Exception as e:
            print(f"[memorias] carregar mais: {e}")
            self._soltar_ancora()
"""),
])
print('ok')
