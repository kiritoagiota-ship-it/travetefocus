import som
"""telas/ganhos.py — TelaGanhos"""
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from datetime import datetime

from efeitos import (BotaoAngular, BotaoAngularAlerta, ListaItem,
                     tremer_tela, explodir_estilhacos)
import som
from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, vibrar, em


def _data_str_para_obj(data_str):
    try:
        data_limpa = data_str.strip().split()[0]
        return datetime.strptime(data_limpa, "%d/%m/%Y")
    except Exception:
        return None


class TelaGanhos(Screen):

    def on_enter(self):
        self._atualizar_config_ui()
        self._atualizar_periodo_atual()
        self._atualizar_historico()

    def _cfg(self):
        return App.get_running_app().config_ganhos

    def _pecas_no_periodo(self, inicio_str, fim_str=None):
        app    = App.get_running_app()
        inicio = _data_str_para_obj(inicio_str)
        fim    = _data_str_para_obj(fim_str) if fim_str else None
        if inicio is None:
            return 0
        total = 0
        for m in app.memorias:
            d = _data_str_para_obj(m.get('data', ''))
            if d is None:
                continue
            if fim:
                if inicio <= d <= fim:
                    total += int(m.get('total', 0))
            else:
                if d >= inicio:
                    total += int(m.get('total', 0))
        return total

    def _calcular_ganho(self, total_pecas):
        """
        Base R$0.25/peca para todas as pecas.
        Bonus R$0.30/peca só para as pecas ACIMA da meta.
        Ex: 3500 pecas, meta=3000 -> 3000x0.25 + 500x0.30 = R$900.
        """
        cfg = self._cfg()
        meta  = cfg['meta_bonus']
        base  = cfg['valor_base']
        bonus = cfg['valor_bonus']
        if total_pecas <= meta:
            return round(total_pecas * base, 2)
        return round(meta * base + (total_pecas - meta) * bonus, 2)

    def _atualizar_config_ui(self):
        cfg = self._cfg()
        self.ids.inp_valor_base.text  = f"{cfg['valor_base']:.2f}"
        self.ids.inp_valor_bonus.text = f"{cfg['valor_bonus']:.2f}"
        self.ids.inp_meta_bonus.text  = str(int(cfg['meta_bonus']))
        self.ids.spin_tipo.text       = cfg['tipo_periodo'].capitalize()

    def _atualizar_periodo_atual(self):
        app      = App.get_running_app()
        periodos = app.periodos_ganhos
        aberto   = next((p for p in reversed(periodos) if not p.get('data_fim')), None)

        if aberto is None:
            self.ids.lbl_periodo_status.text = "[color=#444444]--  Nenhum periodo aberto  --[/color]"
            self.ids.lbl_periodo_pecas.text  = ""
            self.ids.lbl_periodo_ganho.text  = ""
            self.ids.lbl_periodo_bonus.text  = "[color=#333333]Configure abaixo e clique em ABRIR PERIODO[/color]"
            self.ids.btn_fechar_periodo.opacity  = 0
            self.ids.btn_fechar_periodo.disabled = True
            return

        cfg      = self._cfg()
        pecas    = self._pecas_no_periodo(aberto['data_inicio'])
        ganho    = self._calcular_ganho(pecas)
        bonus_ok = pecas >= cfg['meta_bonus']
        faltam   = max(0, int(cfg['meta_bonus']) - pecas)
        tipo     = aberto.get('tipo', 'periodo').capitalize()

        self.ids.lbl_periodo_status.text = (
            f"[color=#00ff88]{em('●')} {tipo} aberto desde [b]{aberto['data_inicio']}[/b][/color]")
        self.ids.lbl_periodo_pecas.text = (
            f"[color=#888888]Pecas[/color]\n[color=#00e5ff][b]{pecas}[/b][/color]")
        self.ids.lbl_periodo_ganho.text = (
            f"[color=#888888]Projecao[/color]\n[color=#00ff88][b]R$ {ganho:.2f}[/b][/color]")
        self.ids.lbl_periodo_bonus.text = (
            f"[color=#ffcc00]{em('🔥')} BONUS ATIVO — R${cfg['valor_bonus']:.2f}/peca[/color]"
            if bonus_ok else
            f"[color=#555555]Faltam {faltam} pecas para bonus (R${cfg['valor_bonus']:.2f}/peca)[/color]")
        self.ids.btn_fechar_periodo.opacity  = 1
        self.ids.btn_fechar_periodo.disabled = False

    def _atualizar_historico(self):
        app  = App.get_running_app()
        cont = self.ids.historico_container
        cont.clear_widgets()

        fechados = [p for p in app.periodos_ganhos if p.get('data_fim')]
        if not fechados:
            vazio = Label(
                text="[ SEM PERIODOS FECHADOS ]",
                font_name="orbitron.ttf", font_size="11sp",
                color=(0, 0.9, 1, 0.22), halign="center", valign="middle",
                size_hint_y=None, height=dp(60))
            vazio.text_size = (Window.width * 0.85, None)
            cont.add_widget(vazio)
            return

        for i, p in enumerate(reversed(fechados)):
            tipo  = p.get('tipo', '?').capitalize()
            di    = p['data_inicio']
            df    = p['data_fim']
            pecas = p.get('total_pecas', 0)
            ganho = p.get('total_ganho', 0.0)
            # Usar em() para o emoji de fogo — fica lindo com markup=True no ListaItem
            bonus_icon = f"{em('🔥')} " if pecas >= self._cfg()['meta_bonus'] else ""

            row = BoxLayout(size_hint_y=None, height=dp(68), spacing=dp(6))
            lbl = ListaItem(
                text=(f"  {bonus_icon}{tipo}  {di} - {df}\n"
                      f"  {pecas} un.   [color=#00ff88]R$ {ganho:.2f}[/color]"),
                markup=True, size_hint_x=0.82)
            # Botão de deletar com emoji via em()
            btn_del = BotaoAngularAlerta(
                text=em('✕'), size_hint_x=0.18, font_size="18sp")
            row.add_widget(lbl)
            row.add_widget(btn_del)
            row.opacity = 0
            cont.add_widget(row)

            def _fazer_delete(periodo=p, widget=btn_del):
                def _executar():
                    periodos = list(app.periodos_ganhos)
                    if periodo in periodos:
                        periodos.remove(periodo)
                        app.periodos_ganhos = periodos
                        app.salvar_dados()
                    self._atualizar_historico()
                    self._atualizar_periodo_atual()

                def _confirmar_delete(*_):
                    som.tocar_delete()
                    vibrar(80)
                    explodir_estilhacos(widget, _executar)
                    tremer_tela(8)

                pop2, lay2 = _make_popup()
                cx2 = BoxLayout(
                    orientation='vertical', padding=[dp(22), dp(18), dp(22), dp(18)],
                    spacing=dp(12), size_hint=(0.82, None),
                    height=min(dp(180), int(Window.height * 0.32)))
                aplicar_fundo_holografico(cx2, (1.0, 0.08, 0.22, 0.9))
                cx2.add_widget(Label(
                    text=(f"[color=#ff2244]!!  APAGAR PERIODO?[/color]\n"
                          f"[color=#cccccc]{tipo}  {di} - {df}\nR$ {ganho:.2f}[/color]"),
                    markup=True, font_name="orbitron.ttf", font_size="12sp",
                    halign="center", size_hint_y=None, height=dp(80)))
                bts = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(12))
                bs  = BotaoAngularAlerta(text="APAGAR")
                bn  = BotaoAngular(text="CANCELAR")
                bts.add_widget(bs)
                bts.add_widget(bn)
                cx2.add_widget(bts)
                lay2.add_widget(cx2)
                cx2.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                bs.bind(on_release=lambda *_: (pop2.dismiss(), _confirmar_delete()))
                bn.bind(on_release=lambda *_: pop2.dismiss())
                _abrir_popup(cx2, pop2)

            btn_del.bind(on_release=lambda *_, f=_fazer_delete: f())
            Clock.schedule_once(
                lambda dt, r=row: Animation(opacity=1, duration=0.22).start(r),
                i * 0.06)

    def _ciclar_tipo(self):
        tipos  = ["Semanal", "Quinzenal", "Mensal"]
        atual  = self.ids.spin_tipo.text
        idx    = tipos.index(atual) if atual in tipos else 0
        self.ids.spin_tipo.text = tipos[(idx + 1) % len(tipos)]

    def salvar_config(self):
        cfg = self._cfg()
        try:
            cfg['valor_base']   = max(0.01, float(self.ids.inp_valor_base.text  or 0.25))
            cfg['valor_bonus']  = max(0.01, float(self.ids.inp_valor_bonus.text or 0.30))
            cfg['meta_bonus']   = max(1,    int(self.ids.inp_meta_bonus.text    or 3000))
            cfg['tipo_periodo'] = self.ids.spin_tipo.text.lower()
        except (ValueError, TypeError):
            pass
        App.get_running_app().salvar_dados()
        self._atualizar_periodo_atual()
        som.tocar_salvar()
        tremer_tela(5)

    def abrir_periodo(self):
        app      = App.get_running_app()
        periodos = list(app.periodos_ganhos)
        if any(not p.get('data_fim') for p in periodos):
            return
        periodos.append({
            "tipo":        self._cfg()['tipo_periodo'],
            "data_inicio": datetime.now().strftime("%d/%m/%Y"),
            "data_fim":    None, "total_pecas": 0, "total_ganho": 0.0
        })
        app.periodos_ganhos = periodos
        app.salvar_dados()
        som.tocar_abrir_periodo()
        vibrar(100)
        self._atualizar_periodo_atual()
        tremer_tela(8)

    def fechar_periodo(self):
        app      = App.get_running_app()
        periodos = list(app.periodos_ganhos)
        idx_aberto = next(
            (i for i, p in enumerate(reversed(periodos)) if not p.get('data_fim')), None)
        if idx_aberto is None:
            return
        idx_real = len(periodos) - 1 - idx_aberto
        aberto   = dict(periodos[idx_real])
        pecas    = self._pecas_no_periodo(aberto['data_inicio'])
        ganho    = self._calcular_ganho(pecas)
        aberto['data_fim']    = datetime.now().strftime("%d/%m/%Y")
        aberto['total_pecas'] = pecas
        aberto['total_ganho'] = round(ganho, 2)
        periodos[idx_real]   = aberto
        app.periodos_ganhos  = periodos
        app.salvar_dados()
        som.tocar_fechar_periodo()
        vibrar(200)
        tremer_tela(15)
        self._atualizar_periodo_atual()
        self._atualizar_historico()
        self._popup_resultado(pecas, ganho, aberto)

    def _popup_resultado(self, pecas, ganho, periodo):
        pop, layout = _make_popup()
        h   = min(dp(320), int(Window.height * 0.56))
        cfg = self._cfg()
        caixa = BoxLayout(
            orientation='vertical',
            padding=[dp(24), dp(18), dp(24), dp(18)],
            spacing=dp(10), size_hint=(0.90, None), height=h)
        aplicar_fundo_holografico(caixa, (0, 0.9, 1, 0.9))
        bonus_ok = pecas >= cfg['meta_bonus']
        taxa     = cfg['valor_bonus'] if bonus_ok else cfg['valor_base']

        caixa.add_widget(Label(
            text="[b][color=#00e5ff]>>  PERIODO ENCERRADO  <<[/color][/b]",
            markup=True, font_name="orbitron.ttf", font_size="15sp",
            size_hint_y=None, height=dp(34), halign="center"))

        bonus_line = (f"[color=#ffcc00]{em('🔥')} BONUS APLICADO R${taxa:.2f}/peca[/color]"
                      if bonus_ok else
                      f"[color=#888888]R$ {taxa:.2f}/peca (base)[/color]")

        caixa.add_widget(Label(
            text=(f"[color=#888888]Periodo[/color]   "
                  f"[color=#00e5ff]{periodo['data_inicio']} - {periodo['data_fim']}[/color]\n\n"
                  f"[color=#888888]Total de pecas[/color]   "
                  f"[color=#00e5ff][b]{pecas} un.[/b][/color]\n\n"
                  f"{bonus_line}\n\n"
                  f"[color=#888888]Total a receber[/color]   "
                  f"[color=#00ff88][b]R$ {ganho:.2f}[/b][/color]"),
            markup=True, font_name="rajdhani.ttf", font_size="16sp",
            halign="center", size_hint_y=None, height=dp(160)))

        btn = BotaoAngular(text=">>  OK", size_hint_y=None, height=dp(50))
        btn.bind(on_release=lambda *_: pop.dismiss())
        caixa.add_widget(btn)
        layout.add_widget(caixa)
        caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        _abrir_popup(caixa, pop)
