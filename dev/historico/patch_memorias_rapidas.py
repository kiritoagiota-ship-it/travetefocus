"""Memorias rapidas (30 por vez, carrega mais ao rolar) + data do turno com
barras automaticas / teclado de numeros + editar a data recalcula tudo."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'interface.kv'), [
    ("""        ScrollView:
            GridLayout:
                id:            memorias_container""",
     """        ScrollView:
            id:            lista_scroll
            GridLayout:
                id:            memorias_container"""),
])

patch(os.path.join(A, 'telas', 'memorias.py'), [
    ("""from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, vibrar, _bind_teclado
import tatil
""", """from helpers import (aplicar_fundo_holografico, _make_popup, _abrir_popup, vibrar, _bind_teclado,
                     anexar_teclado, formatar_data_digitada, ler_data, tremer_widget)
import tatil

PAGINA = 30          # turnos desenhados de cada vez (anos de dados abrem rapido)
"""),
    ("""    def on_enter(self):
        self.filtro_mes = "TODOS"   # nao herdar filtro de uma visita anterior""",
     """    def on_kv_post(self, *_):
        self._pendentes = []
        self._max_t = 0
        self._btn_mais = None
        self.ids.lista_scroll.bind(scroll_y=self._ao_rolar)

    def on_enter(self):
        self.filtro_mes = "TODOS"   # nao herdar filtro de uma visita anterior"""),
    ("""        novos = []
        for m in reversed(mems):
            is_rec = m['total'] == max_t and max_t > 0
            crown  = "[REC] " if is_rec else ""
            btn    = ListaItem(
                text=f"  {crown}{m['data']}   ·   {m['total']} un.   ·   +{m.get('xp', 0)} XP")
            btn.height = dp(52)
            btn.valign = 'middle'
            if is_rec:
                btn.cor_borda    = [1.0, 0.82, 0.0, 1.0]
                btn.cor_borda_kv = [1.0, 0.82, 0.0, 1.0]
                btn.cor_fundo    = [0.10, 0.08, 0.0, 0.92]
                btn.cor_texto    = [1.0, 0.88, 0.1, 1.0]
            btn.bind(on_release=lambda x, mem=m: self.abrir_detalhes_memoria(mem))
            cont.add_widget(btn)
            novos.append(btn)
        entrada_cascata(novos)
""", """        # so os PAGINA mais recentes agora; o resto entra ao rolar ate o fim
        self._max_t = max_t
        self._pendentes = list(reversed(mems))
        self._btn_mais = None
        entrada_cascata(self._desenhar_lote())
        try:
            self.ids.lista_scroll.scroll_y = 1
        except Exception:
            pass

    def _item(self, m):
        is_rec = m['total'] == self._max_t and self._max_t > 0
        crown  = "[REC] " if is_rec else ""
        btn    = ListaItem(
            text=f"  {crown}{m['data']}   ·   {m['total']} un.   ·   +{m.get('xp', 0)} XP")
        btn.height = dp(52)
        btn.valign = 'middle'
        if is_rec:
            btn.cor_borda    = [1.0, 0.82, 0.0, 1.0]
            btn.cor_borda_kv = [1.0, 0.82, 0.0, 1.0]
            btn.cor_fundo    = [0.10, 0.08, 0.0, 0.92]
            btn.cor_texto    = [1.0, 0.88, 0.1, 1.0]
        btn.bind(on_release=lambda x, mem=m: self.abrir_detalhes_memoria(mem))
        return btn

    def _desenhar_lote(self):
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
"""),
    ("""        data_atual = memoria['data'].strip().split()[0]
        inp_data = InputHolografico(
            text=data_atual,
            font_name="orbitron.ttf", font_size="13sp",
            foreground_color=(0, 0.9, 1, 1),
            cursor_color=(0, 0.9, 1, 1),
            halign="center",
            size_hint_x=0.50)          # mais largo para caber a data completa
""", """        data_atual = memoria['data'].strip().split()[0]
        inp_data = InputHolografico(
            text=data_atual,
            font_name="orbitron.ttf", font_size="13sp",
            foreground_color=(0, 0.9, 1, 1),
            cursor_color=(0, 0.9, 1, 1),
            halign="center",
            size_hint_x=0.50)          # mais largo para caber a data completa
        formatar_data_digitada(inp_data)
        anexar_teclado(inp_data, 'numeros')
"""),
    ("""        def _salvar_data(*_):
            raw = inp_data.text.strip()
            try:
                d = datetime.strptime(raw, "%d/%m/%Y")
                partes = memoria['data'].strip().split()
                hora   = partes[1] if len(partes) > 1 else datetime.now().strftime("%H:%M")
                memoria['data'] = f"{d.strftime('%d/%m/%Y')}  {hora}"
                som.tocar_salvar()
                tatil.confirmar()
                App.get_running_app().salvar_dados()
                self.atualizar_lista()
                self._atualizar_grafico()
            except ValueError:
                tatil.erro()
                Animation.cancel_all(inp_data, 'borda_color')
                (Animation(borda_color=[1, 0.1, 0.2, 1], duration=0.08) +
                 Animation(borda_color=[0.55, 0.05, 0.95, 1], duration=0.35)
                 ).start(inp_data)
""", """        def _salvar_data(*_):
            d, motivo = ler_data(inp_data.text)
            if d is None:
                tatil.erro()
                btn_salvar_data.text = motivo.split('.')[0].upper()
                Clock.schedule_once(lambda dt: setattr(btn_salvar_data, 'text', ">>  SALVAR DATA"), 2.2)
                tremer_widget(inp_data)
                Animation.cancel_all(inp_data, 'borda_color')
                (Animation(borda_color=[1, 0.1, 0.2, 1], duration=0.08) +
                 Animation(borda_color=[0.55, 0.05, 0.95, 1], duration=0.35)
                 ).start(inp_data)
                return
            partes = memoria['data'].strip().split()
            hora   = partes[1] if len(partes) > 1 else datetime.now().strftime("%H:%M")
            memoria['data'] = f"{d.strftime('%d/%m/%Y')}  {hora}"
            som.tocar_salvar()
            tatil.confirmar()
            app = App.get_running_app()
            app.recalcular_totais()          # melhor dia e sequencia mudam com a data
            app.salvar_dados()
            self._atualizar_filtros()
            self.atualizar_lista()
            self._atualizar_grafico()
"""),
    ("""        def _executar_delete():
            app = App.get_running_app()
            if memoria in app.memorias:
                app.memorias.remove(memoria)
                app.recalcular_totais()
                app.salvar_dados()
            self.atualizar_lista()""", """        def _executar_delete():
            app = App.get_running_app()
            if memoria in app.memorias:
                app.memorias.remove(memoria)
                app.recalcular_totais()
                app.salvar_dados()
            self._atualizar_filtros()
            self.atualizar_lista()"""),
])
print('ok')
