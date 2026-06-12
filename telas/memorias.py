import som
"""telas/memorias.py — TelaMemorias"""
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
from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup


class TelaMemorias(Screen):
    filtro_mes = StringProperty("TODOS")

    def on_enter(self):
        self._atualizar_filtros()
        self.atualizar_lista()
        self._atualizar_grafico()

    def _atualizar_filtros(self):
        app  = App.get_running_app()
        cont = self.ids.filtros_container
        cont.clear_widgets()

        btn_todos = BotaoAngular(text="TODOS",
                                  size_hint=(None, None), size=(90, 38),
                                  font_size="12sp")
        btn_todos.bind(on_release=lambda *_: self._filtrar("TODOS"))
        cont.add_widget(btn_todos)

        vistos = set()
        for m in reversed(app.memorias):
            raw    = m.get('data', '')
            partes = raw.strip().split('/')
            if len(partes) >= 3:
                mk = f"{partes[1].strip()}/{partes[2].strip()[:4]}"
            else:
                continue
            if mk not in vistos:
                vistos.add(mk)
                b = BotaoAngular(text=mk, size_hint=(None, None),
                                  size=(110, 38), font_size="11sp")
                b.bind(on_release=lambda x, k=mk: self._filtrar(k))
                cont.add_widget(b)

    def _filtrar(self, mes):
        self.filtro_mes = mes
        cont = self.ids.memorias_container
        if cont.children:
            for child in list(cont.children):
                Animation(opacity=0, duration=0.10,
                          transition='out_quad').start(child)
            Clock.schedule_once(lambda dt: self.atualizar_lista(), 0.12)
        else:
            self.atualizar_lista()

    def atualizar_lista(self):
        app   = App.get_running_app()
        cont  = self.ids.memorias_container
        cont.clear_widgets()
        max_t = max((m['total'] for m in app.memorias), default=0)

        def _mes_de(data_str):
            partes = data_str.strip().split('/')
            if len(partes) >= 3:
                return f"{partes[1].strip()}/{partes[2].strip()[:4]}"
            return ""

        mems = (app.memorias if self.filtro_mes == "TODOS"
                else [m for m in app.memorias
                      if _mes_de(m.get('data', '')) == self.filtro_mes])

        if not mems:
            vazio = Label(
                text="[ SEM REGISTROS ]\n\nFinalize um turno para\npopular o banco de memorias.",
                font_name="orbitron.ttf", font_size="12sp",
                color=(0, 0.9, 1, 0), halign="center", valign="middle",
                size_hint_y=None, height=160)
            vazio.text_size = (vazio.width, None)
            vazio.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
            cont.add_widget(vazio)
            Animation(color=(0, 0.9, 1, 0.28), duration=0.45,
                      transition='out_quad').start(vazio)
            return

        for i, m in enumerate(reversed(mems)):
            is_rec = m['total'] == max_t and max_t > 0
            crown  = "★ " if is_rec else ""
            btn    = ListaItem(
                text=f"  {crown}{m['data']}   ·   {m['total']} un.   ·   +{m.get('xp', 0)} XP")
            # Altura compacta e texto centralizado verticalmente
            btn.height = dp(52)
            btn.valign = 'middle'
            if is_rec:
                btn.cor_borda    = [1.0, 0.82, 0.0, 1.0]
                btn.cor_borda_kv = [1.0, 0.82, 0.0, 1.0]
                btn.cor_fundo    = [0.10, 0.08, 0.0, 0.92]
                btn.cor_texto    = [1.0, 0.88, 0.1, 1.0]
            btn.bind(on_release=lambda x, mem=m: self.abrir_detalhes_memoria(mem))
            btn.opacity = 0
            cont.add_widget(btn)
            Clock.schedule_once(
                lambda dt, b=btn: Animation(opacity=1, duration=0.18).start(b),
                i * 0.04)

    def _atualizar_grafico(self):
        app      = App.get_running_app()
        grafico  = self.ids.grafico_barras
        recentes = app.memorias[-8:] if app.memorias else []
        max_t    = max((m['total'] for m in app.memorias), default=0)

        def _label_dia(data_str):
            partes = data_str.strip().split('/')
            if len(partes) >= 2:
                return f"{partes[0].strip()[:2]}/{partes[1].strip()[:2]}"
            return data_str[:5]

        grafico.dados = [
            {'label':  _label_dia(m['data']), 'valor': m['total'],
             'record': m['total'] == max_t and max_t > 0,
             'hoje':   idx == len(recentes) - 1}
            for idx, m in enumerate(recentes)
        ]

    def abrir_detalhes_memoria(self, memoria):
        pop, layout = _make_popup()
        h = min(int(Window.height * 0.80), 520)
        caixa = BoxLayout(orientation='vertical', padding=[dp(20), dp(16), dp(20), dp(16)],
                          spacing=dp(8), size_hint=(0.93, None), height=h)
        aplicar_fundo_holografico(caixa, (0.5, 0.05, 0.9, 0.9))

        # ── Header: resumo + edição de data ─────────────────────────────
        header = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        lbl_info = Label(
            text=(f"[color=#8a2be2]TOTAL:[/color] "
                  f"[color=#00e5ff]{memoria['total']} un.[/color]   "
                  f"[color=#8a2be2]XP:[/color] "
                  f"[color=#00ff88]+{memoria.get('xp', 0)}[/color]"),
            markup=True, font_name="orbitron.ttf", font_size="11sp",
            halign="left", valign="middle", size_hint_x=0.58)
        lbl_info.bind(size=lambda i, v: setattr(i, 'text_size', (v[0], None)))

        data_atual = memoria['data'].strip().split()[0]
        inp_data = InputHolografico(
            text=data_atual, font_name="orbitron.ttf", font_size="14sp",
            foreground_color=(0, 0.9, 1, 1), cursor_color=(0, 0.9, 1, 1),
            halign="center", size_hint_x=0.42)
        header.add_widget(lbl_info)
        header.add_widget(inp_data)
        caixa.add_widget(header)

        btn_salvar_data = BotaoAngular(
            text="SALVAR DATA", size_hint_y=None, height=dp(40),
            font_size="12sp")
        caixa.add_widget(btn_salvar_data)

        # ── ScrollView com itens do turno ────────────────────────────────
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)

        itens = memoria.get('itens', [])
        if itens:
            texto = "[color=#00e5ff]ITENS DO TURNO[/color]\n\n"
            for item in itens:
                nome_item = item[0] if len(item) > 0 else "?"
                qtd_item  = item[1] if len(item) > 1 else 0
                xp_item   = item[2] if len(item) > 2 else 0
                texto += (f"  [color=#ffffff]  [b]{nome_item}[/b][/color]"
                          f"   {qtd_item} un."
                          f"   [color=#00ff88]+{xp_item} XP[/color]\n\n")
        else:
            texto = "[color=#555555]Nenhum item registrado neste turno.[/color]"

        # text_size com largura fixa — garante quebra de linha e altura correta
        content_w = Window.width * 0.88
        lbl = Label(
            text=texto, markup=True,
            halign="left", valign="top",
            font_name="rajdhani.ttf", font_size="16sp",
            size_hint_y=None,
            text_size=(content_w, None))
        # Apenas altura é ligada ao texture_size (não a largura)
        lbl.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        scroll.add_widget(lbl)
        caixa.add_widget(scroll)

        # ── Botões de ação ───────────────────────────────────────────────
        botoes = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(12))
        btn_f  = BotaoAngular(text="FECHAR",  size_hint_x=0.55)
        btn_a  = BotaoAngularAlerta(text="APAGAR", size_hint_x=0.45)
        botoes.add_widget(btn_f)
        botoes.add_widget(btn_a)
        caixa.add_widget(botoes)

        layout.add_widget(caixa)
        caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        def _salvar_data(*_):
            raw = inp_data.text.strip()
            try:
                d = datetime.strptime(raw, "%d/%m/%Y")
                partes = memoria['data'].strip().split()
                hora   = partes[1] if len(partes) > 1 else datetime.now().strftime("%H:%M")
                memoria['data'] = f"{d.strftime('%d/%m/%Y')}  {hora}"
                som.tocar_salvar()
                App.get_running_app().salvar_dados()
                self.atualizar_lista()
                self._atualizar_grafico()
            except ValueError:
                Animation.cancel_all(inp_data, 'borda_color')
                (Animation(borda_color=[1, 0.1, 0.2, 1], duration=0.08) +
                 Animation(borda_color=[0.55, 0.05, 0.95, 1], duration=0.35)
                 ).start(inp_data)

        def _executar_delete():
            app = App.get_running_app()
            if memoria in app.memorias:
                app.memorias.remove(memoria)
                app.recalcular_totais()
                app.salvar_dados()
            self.atualizar_lista()
            self._atualizar_grafico()
            pop.dismiss()

        def _deletar(*_):
            som.tocar_delete()
            tremer_tela(10)
            explodir_estilhacos(btn_a, _executar_delete)

        btn_salvar_data.bind(on_release=_salvar_data)
        btn_f.bind(on_release=lambda *_: pop.dismiss())
        btn_a.bind(on_release=_deletar)
        _abrir_popup(caixa, pop)

    def confirmar_wipe(self):
        pop, layout = _make_popup()
        caixa = BoxLayout(orientation='vertical', padding=[dp(26), dp(22), dp(26), dp(22)],
                          spacing=dp(16), size_hint=(0.84, None), height=dp(210))
        aplicar_fundo_holografico(caixa, (1.0, 0.08, 0.22, 0.9))
        caixa.add_widget(Label(
            text=("[color=#ff2244]  WIPE TOTAL[/color]\n"
                  "[color=#cccccc]Apagar TODAS as memorias e XP?\nSem volta.[/color]"),
            markup=True, font_name="orbitron.ttf", font_size="13sp",
            halign="center", size_hint_y=None, height=dp(82)))
        botoes = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(14))
        btn_s  = BotaoAngularAlerta(text="FORMATAR TUDO")
        btn_n  = BotaoAngular(text="CANCELAR")
        botoes.add_widget(btn_s)
        botoes.add_widget(btn_n)
        caixa.add_widget(botoes)
        layout.add_widget(caixa)
        caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        def _confirmar(*_):
            app = App.get_running_app()
            app.memorias.clear()
            app.registros.clear()
            app.recalcular_totais()
            app.streak = 0
            app.ultima_data = ""
            app.salvar_dados()
            self.atualizar_lista()
            self._atualizar_grafico()
            som.tocar_wipe()
            tremer_tela(25)
            pop.dismiss()

        btn_s.bind(on_release=_confirmar)
        btn_n.bind(on_release=lambda *_: pop.dismiss())
        _abrir_popup(caixa, pop)
