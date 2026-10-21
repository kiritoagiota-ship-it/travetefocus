"""telas/ganhos.py — TelaGanhos

Regra do calculo (por periodo: semanal, quinzenal ou mensal) - 3 FAIXAS, e o
valor da faixa atingida vale para TODAS as pecas do periodo (contas em metas.py):
  - abaixo da meta do meio (2.500): valor BASE (R$ 0,25);
  - da meta do meio ate a meta de cima - 1: valor do MEIO (R$ 0,27);
  - meta de cima (3.000) ou mais: valor BONUS (R$ 0,30).
  Ex: 2.499 = R$ 624,75 | 2.500 = R$ 675,00 | 3.000 = R$ 900,00.
Configs salvas antes da faixa do meio ganham os padroes (metas.completar_cfg).
Embaixo do periodo, a META DA SEMANA (seg a sab): quanto falta para cada
faixa e quanto por dia, contando tambem as pecas de hoje ainda nao finalizadas.
So entram os turnos ja finalizados (memorias). Um turno contado no
fechamento de um periodo nao entra de novo no periodo seguinte (mesmo que
os dois caiam no mesmo dia).
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from datetime import datetime

from efeitos import BotaoAngular, BotaoAngularAlerta, ListaItem, tremer_tela
import som
from animacoes_ui import entrada_cascata, contar, fmt_br
from helpers import aplicar_fundo_holografico, _make_popup, _abrir_popup, em, anexar_teclado, uma_vez
import tatil
import metas


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


NB = '\u00a0'      # espaco que nao quebra a linha ("R$" nunca fica sozinho no fim)


def _reais(v):
    return f"R${NB}{fmt_br(v, 2)}"


class TelaGanhos(Screen):

    def on_enter(self):
        try:
            self.ids.rolagem.scroll_y = 1            # sempre abre no topo
        except Exception:
            pass
        self.ids.barra_semana.ao_cruzar = self._passou_faixa
        self._atualizar_config_ui()
        self._atualizar_periodo_atual()
        self._atualizar_historico()
        try:
            from animacoes_ui import entrada_tela
            entrada_tela(self.ids.historico_container.parent, pular=(self.ids.historico_container,))
        except Exception as e:
            print(f"[ganhos] entrada: {e}")
        # Teclados customizados SAO nos campos de configuracao
        from kivy.clock import Clock as _Clk
        _Clk.schedule_once(self._anexar_teclados_ganhos, 0.4)

    def _anexar_teclados_ganhos(self, dt=None):
        """Conecta teclado numerico com decimal nos campos de valor."""
        try:
            anexar_teclado(self.ids.inp_valor_base,  'numeros', decimal=True)
            anexar_teclado(self.ids.inp_valor_bonus, 'numeros', decimal=True)
            anexar_teclado(self.ids.inp_meta_bonus,  'numeros', decimal=False)
            anexar_teclado(self.ids.inp_valor_meio,  'numeros', decimal=True)
            anexar_teclado(self.ids.inp_meta_meio,   'numeros', decimal=False)
            anexar_teclado(self.ids.inp_sabado,      'numeros', decimal=False)
        except Exception as e:
            print(f"[ganhos] teclado nao anexado: {e}")

    def _cfg(self):
        return metas.completar_cfg(App.get_running_app().config_ganhos)

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
    def _calcular_ganho(self, total_pecas):
        """O valor da faixa atingida vale para TODAS as pecas (metas.py)."""
        return metas.ganho(total_pecas, self._cfg())

    # ── tela ────────────────────────────────────────────────────────────
    @staticmethod
    def filtro_reais(texto, desfazendo=False):
        """So numeros e virgula nos campos de R$ (o ponto vira virgula)."""
        return ''.join(c for c in texto.replace('.', ',') if c.isdigit() or c == ',')

    def _atualizar_config_ui(self):
        cfg = self._cfg()
        self.ids.inp_valor_base.text  = f"{cfg['valor_base']:.2f}".replace('.', ',')
        self.ids.inp_valor_bonus.text = f"{cfg['valor_bonus']:.2f}".replace('.', ',')
        self.ids.inp_meta_bonus.text  = str(int(cfg['meta_bonus']))
        self.ids.inp_valor_meio.text  = f"{float(cfg['valor_meio']):.2f}".replace('.', ',')
        self.ids.inp_meta_meio.text   = str(int(cfg['meta_meio']))
        self.ids.inp_sabado.text      = str(int(cfg['pecas_sabado']))
        self.ids.spin_tipo.text       = cfg['tipo_periodo'].capitalize()

    def _atualizar_periodo_atual(self):
        app      = App.get_running_app()
        periodos = app.periodos_ganhos
        aberto   = next((p for p in reversed(periodos) if not p.get('data_fim')), None)

        if aberto is None:
            self.ids.lbl_periodo_status.text = "[color=#8c96aa]--  Nenhum período aberto  --[/color]"
            self.ids.lbl_periodo_pecas.text  = ""
            self.ids.lbl_periodo_ganho.text  = ""
            self.ids.lbl_periodo_bonus.text  = "[color=#8c96aa]Toque em ABRIR PERÍODO para acompanhar o pagamento[/color]"
            self._pecas_periodo = None
            self._mostrar_botao(self.ids.btn_abrir_periodo, True)
            self._mostrar_botao(self.ids.btn_fechar_periodo, False)
            self._atualizar_semana()
            return

        cfg      = self._cfg()
        pecas    = self._pecas_no_periodo(aberto['data_inicio'], excluir=self._ja_contadas(aberto))
        pecas   += self._lotes_nao_finalizados(aberto['data_inicio'])
        self._pecas_periodo = pecas
        ganho    = self._calcular_ganho(pecas)
        tipo     = aberto.get('tipo', 'período').capitalize()
        prox     = metas.proxima_faixa(pecas, cfg)
        valor_agora = metas.faixa_de(pecas, cfg)[2]

        self.ids.lbl_periodo_status.text = (
            f"[color=#00ff88]>> {tipo} aberto desde [b]{aberto['data_inicio']}[/b][/color]")
        contar(self.ids.lbl_periodo_pecas, pecas,
               lambda v: f"[color=#9aa6bd]Peças[/color]\n[color=#00e5ff][b]{fmt_br(v)}[/b][/color]")
        contar(self.ids.lbl_periodo_ganho, ganho,
               lambda v: f"[color=#9aa6bd]Projeção[/color]\n[color=#00ff88][b]R$ {fmt_br(v, 2)}[/b][/color]",
               inteiro=False)
        if prox is None and pecas > 0:
            extra = ganho - pecas * float(cfg['valor_base'])
            self.ids.lbl_periodo_bonus.text = (
                f"[color=#ffcc00]{em('🔥')} FAIXA MÁXIMA! Todas as peças valem {_reais(valor_agora)} "
                f"(+{_reais(extra)}{NB}de{NB}bônus)[/color]")
        else:
            agora = f"Valendo {_reais(valor_agora)}  ·  " if pecas > 0 else ""
            self.ids.lbl_periodo_bonus.text = (
                f"[color=#aab4c8]{agora}faltam [b]{fmt_br(prox['falta'])}[/b] para {_reais(prox['valor'])} "
                f"[color=#ffcc00](+{_reais(prox['a_mais'])})[/color][/color]")
        self._atualizar_semana()
        self._mostrar_botao(self.ids.btn_abrir_periodo, False)   # ja tem um aberto
        self._mostrar_botao(self.ids.btn_fechar_periodo, True)

    def _passou_faixa(self, k, x, y):
        """A barra da semana passou da marca de uma faixa: estoura em faiscas
        douradas e o valor da projecao da uma batida."""
        try:
            import kirito as K
            f = getattr(self, '_faiscas', None)
            if f is None or f.parent is None:
                f = self._faiscas = K.Faiscas(n_max=60)
                Window.add_widget(f)
            f.estourar(x, y, (1.0, 0.85, 0.2), n=26, forca=dp(300), tam=dp(3), gravidade=dp(300))
            f.estourar(x, y, (1.0, 1.0, 0.75), n=10, forca=dp(160), tam=dp(2), gravidade=dp(200))
            from animacoes_ui import pulso
            pulso(self.ids.lbl_periodo_ganho, 1.1, 0.3)
            import tatil
            tatil.tecla()
            som.tocar_add()
        except Exception as e:
            print(f"[ganhos] faixa: {e}")

    def on_leave(self, *_):
        f = getattr(self, '_faiscas', None)
        if f is not None and f.parent is not None:
            Clock.schedule_once(lambda dt: f.parent and f.parent.remove_widget(f), 1.0)

    @staticmethod
    def _lotes_nao_finalizados(inicio_str):
        """Pecas lancadas no Registro e ainda nao finalizadas, de `inicio_str`
        em diante (as sem dia sao de hoje): entram na projecao e no 'faltam'."""
        ini = _data_str_para_obj(inicio_str)
        if ini is None:
            return 0
        hoje = datetime.now()
        total = 0
        for r in App.get_running_app().registros:
            d = _data_str_para_obj(r[3]) if len(r) > 3 and r[3] else hoje
            if d is None or d.date() < ini.date():
                continue
            try:
                total += int(r[1])
            except (TypeError, ValueError, IndexError):
                pass
        return total

    def _atualizar_semana(self):
        """META DA SEMANA (seg a sab): a barra das faixas e quanto por dia falta
        para cada uma (conta tambem as pecas de hoje ainda nao finalizadas)."""
        try:
            app = App.get_running_app()
            cfg = self._cfg()
            hoje = datetime.now().date()
            sem, hj = metas.pecas_da_semana(app.memorias, app.registros, hoje)
            fx = metas.faixas(cfg)
            topo = fx[-1][0]
            prox = metas.proxima_faixa(sem, cfg)
            self.ids.barra_semana.definir(
                sem, maximo=topo * 1.12, cor=(1, 0.88, 0.1, 1) if prox is None else (0, 0.9, 1, 1),
                marcas=[(ini, f"R$ {fmt_br(v, 2)}", (1, 0.88, 0.1, 1) if k == len(fx) - 1
                         else (0, 1, 0.55, 1)) for k, (ini, v, _n) in enumerate(fx) if ini > 0])
            aberto = next((p for p in reversed(app.periodos_ganhos) if not p.get('data_fim')), None)
            if aberto is None:
                # sem periodo aberto: os numeros grandes mostram a semana
                contar(self.ids.lbl_periodo_pecas, sem,
                       lambda v: f"[color=#9aa6bd]Peças na semana[/color]\n[color=#00e5ff][b]{fmt_br(v)}[/b][/color]")
                contar(self.ids.lbl_periodo_ganho, metas.ganho(sem, cfg),
                       lambda v: f"[color=#9aa6bd]Projeção[/color]\n[color=#00ff88][b]R$ {fmt_br(v, 2)}[/b][/color]",
                       inteiro=False)
                self.ids.lbl_semana_pecas.text = ""
            elif getattr(self, '_pecas_periodo', None) != sem:
                self.ids.lbl_semana_pecas.text = (
                    f"[color=#9aa6bd]Esta semana (seg a sáb):[/color] [color=#00e5ff][b]{fmt_br(sem)}[/b][/color]"
                    f"[color=#9aa6bd] peças  ·  [/color][color=#00ff88]{_reais(metas.ganho(sem, cfg))}[/color]")
            else:
                self.ids.lbl_semana_pecas.text = ""
            linhas = []
            sab = int(cfg['pecas_sabado'])
            for ini, v, _n in fx:
                if ini <= 0 or sem >= ini:
                    continue
                md = metas.meta_diaria(ini, sem, hj, hoje, sab)
                if md['e_sabado']:
                    como = "tudo hoje (sábado)"
                elif md['por_dia'] > 0:
                    # o sabado e so uma PREVISAO (meio periodo, ajustavel): nao conta como feito
                    como = (f"[b]{fmt_br(md['por_dia'])}[/b] por dia [color=#7f8aa3](contando{NB}~{fmt_br(md['sabado'])}"
                            f"{NB}no{NB}sábado)[/color]")
                else:
                    como = f"cabe no sábado [color=#7f8aa3](previsão{NB}~{fmt_br(md['sabado'])})[/color]"
                linhas.append(f"[color=#c8d2e6]Faltam [b]{fmt_br(md['falta'])}[/b] para {_reais(v)} "
                              f"[color=#00e5ff]->[/color] {como}[/color]")
            periodo_no_topo = (aberto is not None and getattr(self, '_pecas_periodo', None) is not None
                               and metas.proxima_faixa(self._pecas_periodo, cfg) is None)
            if not linhas and not periodo_no_topo:
                linhas.append(f"[color=#ffcc00]{em('🔥')} Faixa máxima da semana! "
                              f"Todas as peças valem {_reais(fx[-1][1])}[/color]")
            if hoje.weekday() == 6:
                linhas.insert(0, "[color=#8c96aa]Domingo: a conta já é da semana que começa amanhã[/color]")
            self.ids.lbl_semana_metas.text = "\n".join(linhas[:3])
        except Exception as e:
            print(f"[ganhos] semana: {e}")

    @staticmethod
    def _mostrar_botao(btn, sim):
        """Mostra o botao ocupando a linha toda, ou some com ele (sem espaco)."""
        btn.opacity    = 1 if sim else 0
        btn.disabled   = not sim
        btn.size_hint_x = 1 if sim else None
        if not sim:
            btn.width = 0

    def _atualizar_historico(self):
        app  = App.get_running_app()
        cont = self.ids.historico_container
        cont.clear_widgets()

        fechados = [p for p in app.periodos_ganhos if p.get('data_fim')]
        if not fechados:
            vazio = Label(
                text="[ SEM PERÍODOS FECHADOS ]",
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
            meio_p = p.get('meta_meio')
            bonus_icon = (f"{em('🔥')} " if pecas >= meta_p and pecas > 0 else
                          (f"{em('⭐')} " if meio_p and pecas >= meio_p else ""))

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
                    tatil.forte()
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
                    text=(f"[color=#ff2244]!!  APAGAR PERÍODO?[/color]\n"
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
                bs.bind(on_release=uma_vez(lambda *_: (pop2.dismiss(), _confirmar_delete())))
                bn.bind(on_release=lambda *_: pop2.dismiss())
                _abrir_popup(cx2, pop2)

            btn_del.bind(on_release=lambda *_, f=_fazer_delete: f())
        entrada_cascata(linhas)

    def on_kv_post(self, *_):
        self._recolher_conteudo()

    def _recolher_conteudo(self, *_):
        """Fechado, o painel SAI da tela de verdade: com altura 0 o conteudo
        (a linha do SALVAR) ficava invisivel e desativado EXATAMENTE em cima do
        botao AJUSTES - e um botao desativado segura o toque, entao o AJUSTES
        nunca abria no celular."""
        bloco = self.ids.bloco_config
        if bloco.children:
            self._cfg_filhos = list(reversed(bloco.children))
            bloco.clear_widgets()

    def _devolver_conteudo(self):
        bloco = self.ids.bloco_config
        if not bloco.children:
            for w in getattr(self, '_cfg_filhos', []):
                bloco.add_widget(w)

    def alternar_ajustes(self, abrir=None):
        """Mostra/esconde as configuracoes do calculo (ficam recolhidas)."""
        bloco = self.ids.bloco_config
        abrir = (bloco.height < 1 or not bloco.children) if abrir is None else abrir
        Animation.cancel_all(bloco)
        if abrir:
            self._devolver_conteudo()
            bloco.disabled = False
            Animation(height=dp(220), opacity=1, duration=0.22, transition='out_quad').start(bloco)
            self.ids.btn_ajustes.text = "AJUSTES DO CÁLCULO   [color=#00e5ff88]^[/color]"
            som.tocar_click()
        else:
            bloco.disabled = True
            a = Animation(height=0, opacity=0, duration=0.18, transition='out_quad')
            a.bind(on_complete=self._recolher_conteudo)
            a.start(bloco)
            self.ids.btn_ajustes.text = "AJUSTES DO CÁLCULO   [color=#00e5ff88]v[/color]"
        tatil.botao()

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
        meio = _num(self.ids.inp_valor_meio.text)
        meta_meio = _num(self.ids.inp_meta_meio.text, inteiro=True, minimo=1)
        sabado = _num(self.ids.inp_sabado.text, inteiro=True, minimo=0)
        if base is not None:
            cfg['valor_base'] = base
        else:
            invalidos.append("BASE")
        if bonus is not None:
            cfg['valor_bonus'] = bonus
        else:
            invalidos.append("BÔNUS")
        if meta is not None:
            cfg['meta_bonus'] = meta
        else:
            invalidos.append("META")
        # a faixa do meio tem de ficar ENTRE a base e a de cima (valor e meta)
        if meio is not None and cfg['valor_base'] <= meio <= cfg['valor_bonus']:
            cfg['valor_meio'] = meio
        else:
            invalidos.append("R$ MEIO")
        if meta_meio is not None and meta_meio < int(cfg['meta_bonus']):
            cfg['meta_meio'] = meta_meio
        else:
            invalidos.append("META MEIO")
        if sabado is not None:
            cfg['pecas_sabado'] = sabado
        else:
            invalidos.append("SÁBADO")
        cfg['tipo_periodo'] = self.ids.spin_tipo.text.lower()
        App.get_running_app().salvar_dados()
        self._atualizar_config_ui()          # mostra o que ficou valendo
        self._atualizar_periodo_atual()
        if invalidos:
            som.tocar_erro()
            tatil.erro()
            self._aviso("VALOR INVÁLIDO: " + ", ".join(invalidos) + " (mantido o anterior)",
                        (1, 0.35, 0.35, 1))
        else:
            som.tocar_salvar()
            tatil.confirmar()
            tremer_tela(5)
            self._aviso("SALVO: " + _reais(cfg['valor_base']) + " / " + _reais(cfg['valor_meio']) + " a partir de "
                        + fmt_br(cfg['meta_meio']) + " / " + _reais(cfg['valor_bonus']) + " a partir de "
                        + fmt_br(cfg['meta_bonus']))

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
        tatil.confirmar()
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
        soltas = self._lotes_nao_finalizados(original['data_inicio'])
        if soltas > 0:
            # so os turnos finalizados entram no pagamento: avisa antes, para
            # nenhuma peca lancada ficar de fora sem querer
            from helpers import popup_aviso
            som.tocar_erro()
            tatil.erro()
            popup_aviso(f"Você tem {fmt_br(soltas)} peças no Registro\nainda não finalizadas.\n"
                        "Toque em FINALIZAR DIA no Registro\ne depois feche o período.",
                        titulo="FALTA FINALIZAR O DIA")
            return
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
        aberto['meta_meio']   = int(cfg['meta_meio'])
        aberto['valor_meio']  = float(cfg['valor_meio'])
        aberto['contadas']    = [_chave_turno(m) for m in turnos]
        periodos[idx_real]   = aberto
        app.periodos_ganhos  = periodos
        app.salvar_dados()
        som.tocar_fechar_periodo()
        tatil.vitoria()
        tremer_tela(15)
        self._atualizar_periodo_atual()
        self._atualizar_historico()
        self._popup_resultado(pecas, ganho, aberto)

    def _popup_resultado(self, pecas, ganho, periodo):
        pop, layout = _make_popup()
        h   = min(dp(362), int(Window.height * 0.72))
        caixa = BoxLayout(
            orientation='vertical',
            padding=[dp(24), dp(18), dp(24), dp(18)],
            spacing=dp(10), size_hint=(0.90, None), height=h)
        aplicar_fundo_holografico(caixa, (0, 0.9, 1, 0.9))
        cfg = self._cfg()
        i_fx, _ini, valor, _nome = metas.faixa_de(pecas, cfg)
        total = metas.ganho(pecas, cfg)
        n_bonus = pecas if i_fx > 0 else 0          # (o Yoru comemora se passou da base)

        caixa.add_widget(Label(
            text="[b][color=#00e5ff]>>  PERÍODO ENCERRADO  <<[/color][/b]",
            markup=True, font_name="orbitron.ttf", font_size="15sp",
            size_hint_y=None, height=dp(34), halign="center"))

        prox = metas.proxima_faixa(pecas, cfg)
        if n_bonus > 0:
            sem_meta = round(pecas * float(cfg['valor_base']), 2)
            icone = em('🔥') if prox is None else em('⭐')
            linha_base = (f"[color=#ffcc00]{icone} FAIXA DE {_reais(valor)}[/color]\n"
                          f"[color=#ffcc00]{fmt_br(pecas)}{NB}×{NB}{_reais(valor)}{NB}={NB}{_reais(total)}[/color]")
            linha_bonus = (f"[color=#8c96aa]na base seriam {_reais(sem_meta)} "
                           f"(+{_reais(total - sem_meta)}{NB}de{NB}bônus)[/color]")
        else:
            linha_base = (f"[color=#aab4c8]{fmt_br(pecas)}{NB}×{NB}{_reais(valor)}{NB}=[/color]"
                          f"{NB}[color=#00e5ff]{_reais(total)}[/color]")
            linha_bonus = ""
        if prox is not None:
            linha_bonus += (("\n" if linha_bonus else "") +
                            f"[color=#8c96aa]Faltaram {fmt_br(prox['falta'])} para {_reais(prox['valor'])} "
                            f"(+{_reais(prox['a_mais'])})[/color]")

        caixa.add_widget(Label(
            text=(f"[color=#aab4c8]Período[/color]   "
                  f"[color=#00e5ff]{periodo['data_inicio']} - {periodo['data_fim']}[/color]\n"
                  f"[color=#aab4c8]Total de peças[/color]   "
                  f"[color=#00e5ff][b]{fmt_br(pecas)} un.[/b][/color]\n\n"
                  f"{linha_base}\n{linha_bonus}\n\n"
                  f"[color=#aab4c8]Total a receber[/color]   "
                  f"[color=#00ff88][b]{_reais(total)}[/b][/color]"),
            markup=True, font_name="rajdhani.ttf", font_size="16sp",
            halign="center", valign="middle", size_hint_y=None, height=dp(210)))
        texto = caixa.children[0]
        texto.bind(size=lambda i, s: setattr(i, 'text_size', s))     # linha comprida quebra dentro da caixa

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
