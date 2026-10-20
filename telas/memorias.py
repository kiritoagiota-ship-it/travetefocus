"""telas/memorias.py — TelaMemorias"""
import som
from animacoes_ui import entrada_cascata
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty
from datetime import datetime

from efeitos import (BotaoAngular, BotaoAngularAlerta, ListaItem,
                     InputHolografico, tremer_tela, explodir_estilhacos)
import som
from helpers import (aplicar_fundo_holografico, _make_popup, _abrir_popup, vibrar, _bind_teclado,
                     anexar_teclado, formatar_data_digitada, ler_data, tremer_widget,
                     popup_delete_engracado)
import tatil

PAGINA = 30          # turnos desenhados de cada vez (anos de dados abrem rapido)
POR_QUADRO = 8       # ... montados aos poucos, alguns por quadro


def _mes_de(data_str):
    """'20/10/2026  17:28' -> '10/2026'."""
    partes = str(data_str).strip().split('/')
    if len(partes) >= 3:
        return f"{partes[1].strip()}/{partes[2].strip()[:4]}"
    return ""


def _ordenadas(memorias):
    """Turnos em ordem de data (a data de um turno pode ser editada e um
    dia antigo pode ser lancado depois: a ordem de gravacao nao serve)."""
    def chave(par):
        i, m = par
        raw = str(m.get('data', '')).strip()
        for fmt in ("%d/%m/%Y  %H:%M", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
            try:
                return (datetime.strptime(raw, fmt), i)
            except ValueError:
                continue
        try:
            return (datetime.strptime(raw.split()[0], "%d/%m/%Y"), i)
        except Exception:
            return (datetime.min, i)
    return [m for _, m in sorted(enumerate(memorias), key=chave)]


class TelaMemorias(Screen):
    filtro_mes = StringProperty("TODOS")

    def on_leave(self, *_):
        """Cancela updates pendentes ao sair da tela."""
        try:
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

    def on_enter(self):
        self.filtro_mes = "TODOS"   # nao herdar filtro de uma visita anterior
        self._atualizar_filtros()
        self.atualizar_lista()
        self._atualizar_grafico()
        try:
            self.ids.grafico_barras.animar_entrada()       # as barras crescem do chao
        except Exception as e:
            print(f"[memorias] grafico: {e}")
        try:
            from animacoes_ui import entrada_tela
            sv = self.ids.lista_scroll                     # a lista ja entra item a item
            entrada_tela(sv.parent, pular=(sv,))
        except Exception as e:
            print(f"[memorias] entrada: {e}")

    def _atualizar_filtros(self):
        app  = App.get_running_app()
        cont = self.ids.filtros_container
        cont.clear_widgets()

        btn_todos = BotaoAngular(text="TODOS",
                                  size_hint=(None, None), size=(dp(80), dp(36)),
                                  font_size="12sp")
        btn_todos.bind(on_release=lambda *_: self._filtrar("TODOS"))
        cont.add_widget(btn_todos)

        vistos = set()
        for m in reversed(_ordenadas(app.memorias)):
            raw    = m.get('data', '')
            partes = raw.strip().split('/')
            if len(partes) >= 3:
                mk = f"{partes[1].strip()}/{partes[2].strip()[:4]}"
            else:
                continue
            if mk not in vistos:
                vistos.add(mk)
                b = BotaoAngular(text=mk, size_hint=(None, None),
                                  size=(dp(100), dp(36)), font_size="11sp")
                b.bind(on_release=lambda x, k=mk: self._filtrar(k))
                cont.add_widget(b)

    def _filtrar(self, mes):
        if mes == self.filtro_mes:
            return  # debounce: mesmo filtro, nao redesenhar
        self.filtro_mes = mes
        self._atualizar_grafico()          # as barras se transformam nas do mes
        # Cancelar qualquer update pendente
        if hasattr(self, '_filtro_ev') and self._filtro_ev:
            self._filtro_ev.cancel()
        cont = self.ids.memorias_container
        if cont.children:
            for child in list(cont.children):
                Animation.cancel_all(child)
                Animation(opacity=0, duration=0.08,
                          transition='out_quad').start(child)
            self._filtro_ev = Clock.schedule_once(
                lambda dt: self.atualizar_lista(), 0.10)
        else:
            self.atualizar_lista()

    def atualizar_lista(self):
        # Guard: evitar re-entrada se chamado em rapida sucessao
        if getattr(self, '_atualizando', False):
            return
        self._atualizando = True
        try:
            self._atualizar_lista_impl()
        finally:
            self._atualizando = False

    def _atualizar_lista_impl(self):
        app   = App.get_running_app()
        cont  = self.ids.memorias_container
        self._cancelar_lote()                 # lote de antes ainda montando
        for child in list(cont.children):
            Animation.cancel_all(child)
        cont.clear_widgets()
        max_t = max((m['total'] for m in app.memorias), default=0)

        def _mes_de(data_str):
            partes = data_str.strip().split('/')
            if len(partes) >= 3:
                return f"{partes[1].strip()}/{partes[2].strip()[:4]}"
            return ""

        todas = _ordenadas(app.memorias)
        mems = (todas if self.filtro_mes == "TODOS"
                else [m for m in todas
                      if _mes_de(m.get('data', '')) == self.filtro_mes])

        # Atualizar contador no header
        try:
            total_txt = f"TODOS ({len(mems)})" if self.filtro_mes == "TODOS" else f"{self.filtro_mes} ({len(mems)})"
            self.ids.lbl_filtro_ativo.text = f"[color=#00e5ff]{total_txt}[/color]"
        except Exception:
            pass

        if not mems:
            vazio = Label(
                text="[ SEM REGISTROS ]\n\nFinalize um turno para\npopular o banco de memórias.",
                font_name="orbitron.ttf", font_size="12sp",
                color=(0, 0.9, 1, 0), halign="center", valign="middle",
                size_hint_y=None, height=dp(160))
            vazio.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
            cont.add_widget(vazio)
            Animation(color=(0, 0.9, 1, 0.28), duration=0.35,
                      transition='out_expo').start(vazio)
            return

        # so os PAGINA mais recentes agora; o resto entra ao rolar ate o fim
        self._max_t = max_t
        self._pendentes = list(reversed(mems))
        self._btn_mais = None
        self._desenhar_lote(ancora=0.0)       # comeca no topo

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

    def _cancelar_lote(self):
        ev, self._lote_ev = getattr(self, '_lote_ev', None), None
        if ev is not None:
            ev.cancel()
        self._ancora = None
        self._carregando = False

    def _desenhar_lote(self, ancora):
        """Poe mais PAGINA turnos no fim da lista, POR_QUADRO por quadro (e o
        botao 'mais' se sobrar). ancora: pixels do topo da lista ate a vista,
        mantidos enquanto a lista cresce embaixo."""
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

    def _atualizar_grafico(self):
        app      = App.get_running_app()
        grafico  = self.ids.grafico_barras
        filtro   = getattr(self, 'filtro_mes', 'TODOS')
        todas    = _ordenadas(app.memorias) if app.memorias else []
        if filtro != "TODOS":
            todas = [m for m in todas if _mes_de(m.get('data', '')) == filtro]
        recentes = todas[-8:]
        grafico.titulo = ('PRODUÇÃO · ÚLTIMOS DIAS' if filtro == "TODOS"
                          else f'PRODUÇÃO · {filtro}')
        # Cache: nao redesenhar se dados nao mudaram
        novo_hash = str([(m.get("data"), m.get("total")) for m in recentes])
        if getattr(grafico, "_ultimo_hash", None) == novo_hash:
            return
        grafico._ultimo_hash = novo_hash
        max_t    = max((m['total'] for m in app.memorias), default=0)

        def _label_dia(data_str):
            partes = data_str.strip().split('/')
            if len(partes) >= 2:
                return f"{partes[0].strip()[:2]}/{partes[1].strip()[:2]}"
            return data_str[:5]

        hoje = datetime.now().strftime("%d/%m/%Y")
        grafico.dados = [
            {'label':  _label_dia(m['data']), 'valor': m['total'],
             'record': m['total'] == max_t and max_t > 0,
             'hoje':   m['data'].strip().split(' ')[0] == hoje}
            for m in recentes
        ]

    def abrir_detalhes_memoria(self, memoria):
        pop, layout = _make_popup()

        # Altura baseada em dp() — funciona em qualquer densidade de tela
        alt = min(int(dp(500)), int(Window.height * 0.82))
        caixa = BoxLayout(
            orientation='vertical',
            padding=[dp(18), dp(14), dp(18), dp(14)],
            spacing=dp(8),
            size_hint=(0.93, None), height=alt)
        aplicar_fundo_holografico(caixa, (0.5, 0.05, 0.9, 0.9))

        # ── Header: resumo + edição de data ─────────────────────────────
        header = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))

        lbl_info = Label(
            text=(f"[color=#8a2be2]TOTAL:[/color] "
                  f"[color=#00e5ff][b]{memoria['total']}[/b] un.[/color]\n"
                  f"[color=#8a2be2]XP:[/color] "
                  f"[color=#00ff88][b]+{memoria.get('xp', 0)}[/b][/color]"),
            markup=True, font_name="orbitron.ttf", font_size="11sp",
            halign="left", valign="middle",
            size_hint_x=0.50)
        lbl_info.bind(size=lambda i, v: setattr(i, 'text_size', (v[0], None)))

        data_atual = memoria['data'].strip().split()[0]
        inp_data = InputHolografico(
            text=data_atual,
            font_name="orbitron.ttf", font_size="13sp",
            foreground_color=(0, 0.9, 1, 1),
            cursor_color=(0, 0.9, 1, 1),
            halign="center",
            size_hint_x=0.50)          # mais largo para caber a data completa
        formatar_data_digitada(inp_data)
        anexar_teclado(inp_data, 'numeros')

        header.add_widget(lbl_info)
        header.add_widget(inp_data)
        caixa.add_widget(header)

        btn_salvar_data = BotaoAngular(
            text=">>  SALVAR DATA",
            size_hint_y=None, height=dp(38),
            font_size="12sp")
        caixa.add_widget(btn_salvar_data)

        # Separador visual
        from kivy.uix.widget import Widget
        from kivy.graphics import Color, Rectangle
        sep = Widget(size_hint_y=None, height=dp(1))
        with sep.canvas:
            Color(0.5, 0.05, 0.9, 0.5)
            sep._r = Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(pos=lambda i, v: setattr(i._r, 'pos', v),
                 size=lambda i, v: setattr(i._r, 'size', v))
        caixa.add_widget(sep)

        # ── Lista de itens com BoxLayout — padrão Kivy para scroll ──────
        # Usando BoxLayout + minimum_height em vez de Label + texture_size
        # pois o texture_size binding é assíncrono e não funciona bem no Android
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        items_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(2),
            padding=[0, dp(4), 0, dp(4)])
        items_box.bind(minimum_height=items_box.setter('height'))

        itens = memoria.get('itens', [])

        titulo = Label(
            text="[color=#00e5ff]ITENS DO TURNO[/color]",
            markup=True, font_name="orbitron.ttf", font_size="11sp",
            size_hint_y=None, height=dp(28),
            halign="left", valign="middle")
        titulo.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        items_box.add_widget(titulo)

        if itens:
            for item in itens:
                nome_item = str(item[0]) if len(item) > 0 else "?"
                qtd_item  = item[1] if len(item) > 1 else 0
                xp_item   = item[2] if len(item) > 2 else 0
                row = Label(
                    text=(f"  [b]{nome_item}[/b]"
                          f"   {qtd_item} un."
                          f"   [color=#00ff88]+{xp_item} XP[/color]"),
                    markup=True,
                    font_name="rajdhani.ttf", font_size="15sp",
                    size_hint_y=None, height=dp(34),
                    halign="left", valign="middle")
                row.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
                items_box.add_widget(row)
        else:
            sem = Label(
                text="[color=#555555]Nenhum item detalhado disponível.[/color]",
                markup=True, font_name="rajdhani.ttf", font_size="14sp",
                size_hint_y=None, height=dp(40),
                halign="center", valign="middle")
            items_box.add_widget(sem)

        scroll.add_widget(items_box)
        caixa.add_widget(scroll)

        # ── Enviar a producao do turno para o grupo do WhatsApp ──────────
        btn_zap = BotaoAngular(
            text=">>  ENVIAR NO WHATSAPP",
            size_hint_y=None, height=dp(44), font_size="12sp",
            cor_borda=[0.15, 0.85, 0.42, 0.9], cor_borda_kv=[0.15, 0.85, 0.42, 0.9],
            cor_fundo=[0.02, 0.13, 0.06, 0.95], cor_texto=[0.35, 1.0, 0.6, 1.0])
        caixa.add_widget(btn_zap)

        # ── Botões ───────────────────────────────────────────────────────
        botoes = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        btn_f  = BotaoAngular(text=">>  FECHAR",  size_hint_x=0.55)
        btn_a  = BotaoAngularAlerta(text="APAGAR", size_hint_x=0.45)
        botoes.add_widget(btn_f)
        botoes.add_widget(btn_a)
        caixa.add_widget(botoes)

        layout.add_widget(caixa)
        caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        # ── Handlers ─────────────────────────────────────────────────────
        def _salvar_data(*_):
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

        def _executar_delete():
            app = App.get_running_app()
            if memoria in app.memorias:
                app.memorias.remove(memoria)
                app.recalcular_totais()
                app.salvar_dados()
            self._atualizar_filtros()
            self.atualizar_lista()
            self._atualizar_grafico()
            pop.dismiss()

        def _deletar(*_):
            som.tocar_delete()
            tremer_tela(10)
            # o Yoru crava a estocada no cartao do turno
            from cenas import kirito_fatiar
            for b in (btn_a, btn_f, btn_zap, btn_salvar_data):
                b.disabled = True
            pop.auto_dismiss = False                 # nao fecha no meio do golpe
            kirito_fatiar(caixa, _executar_delete, tipo='estocada')

        def _enviar():
            try:
                from exportar import mensagem_turno, enviar_whatsapp
                ok, aviso = enviar_whatsapp(mensagem_turno(memoria))
            except Exception as e:
                print(f"[whatsapp] {e}")
                ok, aviso = False, "Não consegui preparar a mensagem."
            if aviso:
                self._aviso(aviso, ok)

        def _whatsapp(*_):
            tatil.confirmar()
            # as linhas do turno viram uma carta na mao do Yoru; ele corta e ela
            # sai voando - o WhatsApp abre quando ele sai de cena
            try:
                from cenas import kirito_carta
                sx, sy = scroll.to_window(scroll.x, scroll.y)
                kirito_carta(btn_zap, _enviar,
                             linhas=[w for w in items_box.children if w is not titulo][::-1],
                             area=(sx, sy, sx + scroll.width, sy + scroll.height))
            except Exception as e:
                print(f"[whatsapp] carta: {e}")
                _enviar()

        _bind_teclado(inp_data, pop)
        btn_zap.bind(on_release=_whatsapp)
        btn_salvar_data.bind(on_release=_salvar_data)
        btn_f.bind(on_release=lambda *_: pop.dismiss())

        def _perguntar_apagar(*_):
            # apagar o dia inteiro pede confirmacao (antes apagava direto:
            # um toque sem querer sumia com o turno)
            dia = memoria['data'].strip().split()[0]
            popup_delete_engracado(
                _deletar,
                pergunta=f"Apagar o turno de {dia}?\n{memoria['total']} peças  -  +{memoria.get('xp', 0)} XP",
                botao="APAGAR")
        btn_a.bind(on_release=_perguntar_apagar)
        _abrir_popup(caixa, pop)

    def _aviso(self, msg, ok=True):
        """Popup curto por cima de tudo (verde = deu certo, ciano = aviso)."""
        pop, layout = _make_popup()
        cor = '#5cff9a' if ok else '#00e5ff'
        cx = BoxLayout(orientation='vertical', padding=[dp(20), dp(18), dp(20), dp(18)],
                       spacing=dp(10), size_hint=(0.84, None), height=dp(170))
        aplicar_fundo_holografico(cx, (0.15, 0.85, 0.42, 0.9) if ok else (0, 0.9, 1, 0.9))
        cx.add_widget(Label(
            text=f"[color={cor}]{msg}[/color]",
            markup=True, font_name="rajdhani.ttf", font_size="15sp",
            halign="center", valign="middle", size_hint_y=None, height=dp(70)))
        btn = BotaoAngular(text=">>  OK", size_hint_y=None, height=dp(48))
        btn.bind(on_release=lambda *_: pop.dismiss())
        cx.add_widget(btn)
        layout.add_widget(cx)
        cx.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        _abrir_popup(cx, pop)

    def exportar_historico(self):
        """Exporta o histórico como CSV e compartilha via WhatsApp."""
        from kivy.app import App
        app = App.get_running_app()

        if not app.memorias:
            # Popup informativo
            pop, layout = _make_popup()
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.label import Label
            cx = BoxLayout(orientation='vertical', padding=[dp(24), dp(20), dp(24), dp(20)],
                          spacing=dp(12), size_hint=(0.84, None), height=dp(160))
            aplicar_fundo_holografico(cx, (0, 0.9, 1, 0.9))
            cx.add_widget(Label(
                text="[color=#00e5ff]Nenhum turno para exportar.[/color]",
                markup=True, font_name="orbitron.ttf", font_size="13sp",
                halign="center", size_hint_y=None, height=dp(50)))
            from efeitos import BotaoAngular
            btn = BotaoAngular(text=">>  OK", size_hint_y=None, height=dp(48))
            btn.bind(on_release=lambda *_: pop.dismiss())
            cx.add_widget(btn)
            layout.add_widget(cx)
            cx.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
            _abrir_popup(cx, pop)
            return

        def _on_erro(msg):
            pop2, layout2 = _make_popup()
            from kivy.uix.boxlayout import BoxLayout
            from kivy.uix.label import Label
            cx2 = BoxLayout(orientation='vertical', padding=[dp(20), dp(18), dp(20), dp(18)],
                           spacing=dp(10), size_hint=(0.88, None), height=dp(200))
            aplicar_fundo_holografico(cx2, (0, 0.9, 1, 0.9))
            cx2.add_widget(Label(
                text=f"[color=#00e5ff]{msg}[/color]",
                markup=True, font_name="rajdhani.ttf", font_size="14sp",
                halign="center", valign="middle", size_hint_y=None, height=dp(100)))
            from efeitos import BotaoAngular
            btn2 = BotaoAngular(text=">>  OK", size_hint_y=None, height=dp(48))
            btn2.bind(on_release=lambda *_: pop2.dismiss())
            cx2.add_widget(btn2)
            layout2.add_widget(cx2)
            cx2.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
            _abrir_popup(cx2, pop2)

        try:
            from exportar import exportar_e_compartilhar
        except ImportError:
            _on_erro("Módulo exportar.py não encontrado no repositório.")
            return
        exportar_e_compartilhar(app.memorias, app.user_data_dir, _on_erro)
        tatil.confirmar()

    def confirmar_wipe(self):
        pop, layout = _make_popup()
        caixa = BoxLayout(
            orientation='vertical',
            padding=[dp(26), dp(22), dp(26), dp(22)],
            spacing=dp(16),
            size_hint=(0.84, None), height=dp(220))
        aplicar_fundo_holografico(caixa, (1.0, 0.08, 0.22, 0.9))
        caixa.add_widget(Label(
            text=("[color=#ff2244]  WIPE TOTAL[/color]\n"
                  "[color=#cccccc]Apagar TODAS as memórias e XP?\nSem volta.[/color]"),
            markup=True, font_name="orbitron.ttf", font_size="13sp",
            halign="center", size_hint_y=None, height=dp(84)))
        botoes = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(14))
        btn_s  = BotaoAngularAlerta(text="FORMATAR TUDO")
        btn_n  = BotaoAngular(text="CANCELAR")
        botoes.add_widget(btn_s)
        botoes.add_widget(btn_n)
        caixa.add_widget(botoes)
        layout.add_widget(caixa)
        caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        def _confirmar(*_):
            # versao epica: o Kirito corta a lista inteira antes de apagar
            btn_s.disabled = True
            pop.dismiss()
            itens = list(self.ids.memorias_container.children)
            try:
                from cenas import kirito_wipe
                # so as memorias que aparecem na lista (dentro da rolagem)
                sv = self.ids.memorias_container.parent
                x0, y0 = sv.to_window(sv.x, sv.y)
                area = (x0, y0, x0 + sv.width, y0 + sv.height)
                kirito_wipe(itens, _apagar_tudo, grafico=self.ids.grafico_barras, area_lista=area,
                            extras=[b for b in self.ids.filtros_container.children
                                    if getattr(b, 'text', '') != "TODOS"])   # os meses somem junto
            except Exception as e:
                print(f"[memorias] wipe animado: {e}")
                _apagar_tudo()

        def _apagar_tudo():
            app = App.get_running_app()
            app.memorias.clear()
            app.registros.clear()
            app.recalcular_totais()
            app.streak = 0
            app.ultima_data = ""
            app.salvar_dados()
            self.filtro_mes = "TODOS"
            self._atualizar_filtros()
            self.atualizar_lista()
            self._atualizar_grafico()
            # o grafico foi fatiado no golpe final: volta vazio, acendendo
            g = self.ids.grafico_barras
            g.opacity = 0
            Animation(opacity=1, duration=0.6).start(g)
            som.tocar_wipe()
            vibrar(300)
            tremer_tela(25)

        btn_s.bind(on_release=_confirmar)
        btn_n.bind(on_release=lambda *_: pop.dismiss())
        _abrir_popup(caixa, pop)
