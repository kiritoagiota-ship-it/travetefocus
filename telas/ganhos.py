"""telas/ganhos.py — TelaGanhos

Regra do calculo (por periodo: semanal, quinzenal ou mensal):
  - abaixo da meta, cada peca vale o valor BASE (padrao R$ 0,25);
  - bateu a meta, TODAS as pecas do periodo passam a valer o valor BONUS
    (padrao R$ 0,30).
  Ex: meta 3000 -> 2999 pecas = R$ 749,75 | 3000 = R$ 900,00 | 3500 = R$ 1.050,00.
So entram os turnos ja finalizados (memorias). Um turno contado no
fechamento de um periodo nao entra de novo no periodo seguinte (mesmo que
os dois caiam no mesmo dia).
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.metrics import dp
from datetime import datetime

from efeitos import BotaoAngular, BotaoAngularAlerta, ListaItem, tremer_tela
import som
from animacoes_ui import entrada_cascata, contar, fmt_br
from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, vibrar, em, anexar_teclado


def _data_str_para_obj(data_str):
    try:
        data_limpa = data_str.strip().split()[0]
        return datetime.strptime(data_limpa, "%d/%m/%Y")
    except Exception:
        return None


def _num(texto, inteiro=False, minimo=0.01):
    """Numero digitado no campo (aceita virgula). Vazio ou invalido = None."""
    t = (texto or '').strip().replace(',', '.')
    if not t:
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    if inteiro:
        v = int(v)
    return v if v >= minimo else None


def _chave_turno(m):
    """Identidade de um turno (memoria): o mesmo turno nunca conta em dois
    periodos. Turnos novos tem 'ts'; os antigos usam data + total."""
    ts = m.get('ts')
    return f"ts:{ts}" if ts is not None else f"{m.get('data', '')}|{m.get('total', 0)}"


def _reais(v):
    return f"R$ {fmt_br(v, 2)}"


class TelaGanhos(Screen):

    def on_enter(self):
        self._atualizar_config_ui()
        self._atualizar_periodo_atual()
        self._atualizar_historico()
        # Teclados customizados SAO nos campos de configuracao
        from kivy.clock import Clock as _Clk
        _Clk.schedule_once(self._anexar_teclados_ganhos, 0.4)

    def _anexar_teclados_ganhos(self, dt=None):
        """Conecta teclado numerico com decimal nos campos de valor."""
        try:
            anexar_teclado(self.ids.inp_valor_base,  'numeros', decimal=True)
            anexar_teclado(self.ids.inp_valor_bonus, 'numeros', decimal=True)
            anexar_teclado(self.ids.inp_meta_bonus,  'numeros', decimal=False)
        except Exception as e:
            print(f"[ganhos] teclado nao anexado: {e}")

    def _cfg(self):
        return App.get_running_app().config_ganhos

    # ── contagem de pecas ───────────────────────────────────────────────
    def _ja_contadas(self, periodo=None):
        """Turnos ja contados no fechamento de OUTROS periodos."""
        chaves = set()
        for p in App.get_running_app().periodos_ganhos:
            if p is periodo or not p.get('data_fim'):
                continue
            chaves.update(p.get('contadas', []))
        return chaves

    def _turnos_no_periodo(self, inicio_str, fim_str=None, excluir=()):
        app    = App.get_running_app()
        # (sem cache: a chave por len(memorias) ficava velha ao editar a data
        # de um turno e gravava total/ganho errado ao fechar o periodo)
        inicio = _data_str_para_obj(inicio_str)
        fim    = _data_str_para_obj(fim_str) if fim_str else None
        if inicio is None:
            return []
        turnos = []
        for m in app.memorias:
            d = _data_str_para_obj(m.get('data', ''))
            if d is None or d < inicio or (fim is not None and d > fim):
                continue
            if _chave_turno(m) in excluir:
                continue
            turnos.append(m)
        return turnos

    def _pecas_no_periodo(self, inicio_str, fim_str=None, excluir=()):
        total = 0
        for m in self._turnos_no_periodo(inicio_str, fim_str, excluir):
            try:
                total += int(m.get('total', 0))
            except (TypeError, ValueError):
                pass
        return total

    # ── dinheiro ────────────────────────────────────────────────────────
    def _detalhe_ganho(self, total_pecas):
        """(pecas_base, valor_base, pecas_bonus, valor_bonus, total).
        Bateu a meta: todas as pecas vao para o bonus (pecas_base = 0)."""
        cfg = self._cfg()
        meta  = int(cfg['meta_bonus'])
        base  = float(cfg['valor_base'])
        bonus = float(cfg['valor_bonus'])
        if total_pecas >= meta and total_pecas > 0:
            n_base, n_bonus = 0, total_pecas
        else:
            n_base, n_bonus = total_pecas, 0
        v_base = round(n_base * base, 2)
        v_bonus = round(n_bonus * bonus, 2)
        return n_base, v_base, n_bonus, v_bonus, round(v_base + v_bonus, 2)

    def _calcular_ganho(self, total_pecas):
        """
        Abaixo da meta: R$0.25 por peca. Bateu a meta: TODAS a R$0.30.
        Ex: meta=3000 -> 3000 pecas = R$900; 3500 pecas = R$1050.
        """
        return self._detalhe_ganho(total_pecas)[4]

    # ── tela ────────────────────────────────────────────────────────────
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
            self.ids.lbl_periodo_status.text = "[color=#8c96aa]--  Nenhum periodo aberto  --[/color]"
            self.ids.lbl_periodo_pecas.text  = ""
            self.ids.lbl_periodo_ganho.text  = ""
            self.ids.lbl_periodo_bonus.text  = "[color=#8c96aa]Configure abaixo e toque em ABRIR PERIODO[/color]"
            self.ids.btn_fechar_periodo.opacity  = 0
            self.ids.btn_fechar_periodo.disabled = True
            return

        cfg      = self._cfg()
        pecas    = self._pecas_no_periodo(aberto['data_inicio'], excluir=self._ja_contadas(aberto))
        ganho    = self._calcular_ganho(pecas)
        meta     = int(cfg['meta_bonus'])
        faltam   = max(0, meta - pecas)
        tipo     = aberto.get('tipo', 'periodo').capitalize()
        bonus_rs = _reais(cfg['valor_bonus'])

        self.ids.lbl_periodo_status.text = (
            f"[color=#00ff88]>> {tipo} aberto desde [b]{aberto['data_inicio']}[/b][/color]")
        contar(self.ids.lbl_periodo_pecas, pecas,
               lambda v: f"[color=#9aa6bd]Pecas[/color]\n[color=#00e5ff][b]{fmt_br(v)}[/b][/color]")
        contar(self.ids.lbl_periodo_ganho, ganho,
               lambda v: f"[color=#9aa6bd]Projecao[/color]\n[color=#00ff88][b]R$ {fmt_br(v, 2)}[/b][/color]",
               inteiro=False)
        if pecas >= meta and pecas > 0:
            extra = ganho - pecas * float(cfg['valor_base'])
            self.ids.lbl_periodo_bonus.text = (
                f"[color=#ffcc00]{em('🔥')} META BATIDA! Todas as pecas valem {bonus_rs} "
                f"(+{_reais(extra)} de bonus)[/color]")
        else:
            self.ids.lbl_periodo_bonus.text = (
                f"[color=#aab4c8]Faltam {fmt_br(faltam)} pecas para a meta de {fmt_br(meta)} - "
                f"batendo, TODAS passam a valer {bonus_rs}[/color]")
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
                color=(0, 0.9, 1, 0.45), halign="center", valign="middle",
                size_hint_y=None, height=dp(60))
            vazio.text_size = (Window.width * 0.85, None)
            cont.add_widget(vazio)
            return

        linhas = []
        for p in reversed(fechados):
            tipo  = p.get('tipo', '?').capitalize()
            di    = p['data_inicio']
            df    = p['data_fim']
            pecas = p.get('total_pecas', 0)
            ganho = p.get('total_ganho', 0.0)
            meta_p = p.get('meta', self._cfg()['meta_bonus'])
            bonus_icon = f"{em('🔥')} " if pecas >= meta_p and pecas > 0 else ""

            row = BoxLayout(size_hint_y=None, height=dp(68), spacing=dp(6))
            lbl = ListaItem(
                text=(f"  {bonus_icon}{tipo}  {di} - {df}\n"
                      f"  {fmt_br(pecas)} un.   [color=#00ff88]{_reais(ganho)}[/color]"),
                markup=True, size_hint_x=0.82)
            btn_del = BotaoAngularAlerta(
                text=em('✕'), size_hint_x=0.18, font_size="18sp")
            row.add_widget(lbl)
            row.add_widget(btn_del)
            cont.add_widget(row)
            linhas.append(row)

            def _fazer_delete(periodo=p, widget=row, tipo=tipo, di=di, df=df, ganho=ganho):
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
                    # o Yoru parte a linha do periodo com o corte em X
                    from cenas import kirito_fatiar
                    kirito_fatiar(widget, _executar, tipo='x')
                    tremer_tela(8)

                pop2, lay2 = _make_popup()
                cx2 = BoxLayout(
                    orientation='vertical', padding=[dp(22), dp(18), dp(22), dp(18)],
                    spacing=dp(12), size_hint=(0.82, None),
                    height=min(dp(180), int(Window.height * 0.32)))
                aplicar_fundo_holografico(cx2, (1.0, 0.08, 0.22, 0.9))
                cx2.add_widget(Label(
                    text=(f"[color=#ff2244]!!  APAGAR PERIODO?[/color]\n"
                          f"[color=#cccccc]{tipo}  {di} - {df}\n{_reais(ganho)}[/color]"),
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
        entrada_cascata(linhas)

    def _ciclar_tipo(self):
        tipos  = ["Semanal", "Quinzenal", "Mensal"]
        atual  = self.ids.spin_tipo.text
        idx    = tipos.index(atual) if atual in tipos else 0
        self.ids.spin_tipo.text = tipos[(idx + 1) % len(tipos)]

    def _aviso(self, texto, cor=(0, 1, 0.55, 1)):
        """Recado curto que sobe e some (confirma o que foi salvo ou o erro)."""
        try:
            lbl = Label(text=texto, markup=True, font_name="orbitron.ttf", font_size="12sp",
                        color=(cor[0], cor[1], cor[2], 0), halign="center", valign="middle",
                        size_hint=(None, None), size=(Window.width * 0.9, dp(40)),
                        pos=(Window.width * 0.05, Window.height * 0.12))
            lbl.text_size = lbl.size
            Window.add_widget(lbl)
            anim = (Animation(color=cor, y=lbl.y + dp(16), duration=0.25, transition='out_quad') +
                    Animation(duration=1.3) +
                    Animation(color=(cor[0], cor[1], cor[2], 0), y=lbl.y + dp(34),
                              duration=0.35, transition='in_quad'))
            anim.bind(on_complete=lambda *_: Window.remove_widget(lbl))
            anim.start(lbl)
        except Exception as e:
            print(f"[ganhos] aviso: {e}")

    def salvar_config(self):
        """Salva cada campo por conta propria (um valor invalido nao impede os
        outros) e avisa o que ficou de fora. Aceita virgula (0,30)."""
        cfg = self._cfg()
        invalidos = []
        base = _num(self.ids.inp_valor_base.text)
        bonus = _num(self.ids.inp_valor_bonus.text)
        meta = _num(self.ids.inp_meta_bonus.text, inteiro=True, minimo=1)
        if base is not None:
            cfg['valor_base'] = base
        else:
            invalidos.append("BASE")
        if bonus is not None:
            cfg['valor_bonus'] = bonus
        else:
            invalidos.append("BONUS")
        if meta is not None:
            cfg['meta_bonus'] = meta
        else:
            invalidos.append("META")
        cfg['tipo_periodo'] = self.ids.spin_tipo.text.lower()
        App.get_running_app().salvar_dados()
        self._atualizar_config_ui()          # mostra o que ficou valendo
        self._atualizar_periodo_atual()
        if invalidos:
            som.tocar_erro()
            self._aviso("VALOR INVALIDO: " + ", ".join(invalidos) + " (mantido o anterior)",
                        (1, 0.35, 0.35, 1))
        else:
            som.tocar_salvar()
            tremer_tela(5)
            self._aviso("CALCULO SALVO: base " + _reais(cfg['valor_base']) + " / bonus "
                        + _reais(cfg['valor_bonus']) + " ao bater " + fmt_br(cfg['meta_bonus']))

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
        tremer_tela(8)
        # Animação de abertura: piscar o status em verde
        self._atualizar_periodo_atual()
        try:
            st = self.ids.lbl_periodo_status
            (Animation(color=[0, 1, 0.55, 0], duration=0.09, transition='out_expo') +
             Animation(color=[0, 1, 0.55, 1], duration=0.09, transition='out_expo') +
             Animation(color=[0, 1, 0.55, 0], duration=0.09, transition='out_expo') +
             Animation(color=[1, 1, 1, 1],    duration=0.18, transition='out_expo')).start(st)
        except Exception:
            pass

    def fechar_periodo(self):
        app      = App.get_running_app()
        periodos = list(app.periodos_ganhos)
        idx_aberto = next(
            (i for i, p in enumerate(reversed(periodos)) if not p.get('data_fim')), None)
        if idx_aberto is None:
            return
        idx_real = len(periodos) - 1 - idx_aberto
        original = periodos[idx_real]
        aberto   = dict(original)
        turnos   = self._turnos_no_periodo(aberto['data_inicio'], excluir=self._ja_contadas(original))
        pecas    = sum(int(m.get('total', 0)) for m in turnos)
        ganho    = self._calcular_ganho(pecas)
        cfg      = self._cfg()
        aberto['data_fim']    = datetime.now().strftime("%d/%m/%Y")
        aberto['total_pecas'] = pecas
        aberto['total_ganho'] = round(ganho, 2)
        # guarda as regras usadas e os turnos contados (nao contam de novo)
        aberto['meta']        = int(cfg['meta_bonus'])
        aberto['valor_base']  = float(cfg['valor_base'])
        aberto['valor_bonus'] = float(cfg['valor_bonus'])
        aberto['contadas']    = [_chave_turno(m) for m in turnos]
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
        h   = min(dp(340), int(Window.height * 0.62))
        caixa = BoxLayout(
            orientation='vertical',
            padding=[dp(24), dp(18), dp(24), dp(18)],
            spacing=dp(10), size_hint=(0.90, None), height=h)
        aplicar_fundo_holografico(caixa, (0, 0.9, 1, 0.9))
        n_base, v_base, n_bonus, v_bonus, total = self._detalhe_ganho(pecas)
        cfg = self._cfg()

        caixa.add_widget(Label(
            text="[b][color=#00e5ff]>>  PERIODO ENCERRADO  <<[/color][/b]",
            markup=True, font_name="orbitron.ttf", font_size="15sp",
            size_hint_y=None, height=dp(34), halign="center"))

        if n_bonus > 0:
            sem_meta = round(n_bonus * float(cfg['valor_base']), 2)
            linha_base = (f"[color=#ffcc00]{em('🔥')} META BATIDA: {fmt_br(n_bonus)} x "
                          f"{_reais(cfg['valor_bonus'])}   {_reais(v_bonus)}[/color]")
            linha_bonus = (f"[color=#8c96aa]sem a meta seriam {_reais(sem_meta)} "
                           f"(+{_reais(v_bonus - sem_meta)} de bonus)[/color]")
        else:
            linha_base = (f"[color=#aab4c8]{fmt_br(n_base)} x {_reais(cfg['valor_base'])}[/color]"
                          f"   [color=#00e5ff]{_reais(v_base)}[/color]")
            linha_bonus = (f"[color=#8c96aa]Meta de {fmt_br(cfg['meta_bonus'])} nao batida "
                           f"(faltaram {fmt_br(int(cfg['meta_bonus']) - pecas)})[/color]")

        caixa.add_widget(Label(
            text=(f"[color=#aab4c8]Periodo[/color]   "
                  f"[color=#00e5ff]{periodo['data_inicio']} - {periodo['data_fim']}[/color]\n"
                  f"[color=#aab4c8]Total de pecas[/color]   "
                  f"[color=#00e5ff][b]{fmt_br(pecas)} un.[/b][/color]\n\n"
                  f"{linha_base}\n{linha_bonus}\n\n"
                  f"[color=#aab4c8]Total a receber[/color]   "
                  f"[color=#00ff88][b]{_reais(total)}[/b][/color]"),
            markup=True, font_name="rajdhani.ttf", font_size="16sp",
            halign="center", size_hint_y=None, height=dp(190)))

        btn = BotaoAngular(text=">>  OK", size_hint_y=None, height=dp(50))
        btn.bind(on_release=lambda *_: pop.dismiss())
        caixa.add_widget(btn)
        layout.add_widget(caixa)
        caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        _abrir_popup(caixa, pop)
        if n_bonus > 0:                          # bateu a meta: o Yoru comemora
            def _yoru(dt):
                try:
                    from cenas import kirito_meta
                    kirito_meta(caixa)
                except Exception as e:
                    print(f"[ganhos] yoru: {e}")
            from kivy.clock import Clock as _Clk2
            _Clk2.schedule_once(_yoru, 0.45)
