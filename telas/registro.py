"""telas/registro.py — TelaRegistro com sons temáticos"""
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from efeitos import ListaItem, explodir_estilhacos, tremer_tela
from helpers import (popup_pedir_xp, popup_delete_engracado, popup_resumo_dia, animar_ganho_xp,
                     anexar_teclado, sugestoes_pecas, popup_importar_zap, popup_aviso,
                     ler_area_de_transferencia)
from datetime import datetime
import som
import tatil
from animacoes_ui import entrada_cascata, fmt_br
import time
import metas


class TelaRegistro(Screen):

    def on_enter(self):
        self.atualizar()
        self.atualizar_meta()
        # Anexar teclados customizados SAO (so na primeira vez por widget)
        Clock.schedule_once(self._anexar_teclados, 0.3)
        self._foco_ev = Clock.schedule_once(self._focar_nome, 0.35)

    def on_leave(self, *_):
        if hasattr(self, '_foco_ev') and self._foco_ev:
            self._foco_ev.cancel()
            self._foco_ev = None

    def _anexar_teclados(self, dt=None):
        """Conecta teclados SAO nos campos de texto e numero."""
        try:
            anexar_teclado(self.ids.nome_input, 'letras', sugestoes=sugestoes_pecas)
            anexar_teclado(self.ids.qtd_input,  'numeros')
        except Exception as e:
            print(f"[registro] teclado nao anexado: {e}")

    def _focar_nome(self, dt=None):
        self._foco_ev = None
        try:
            self.ids.nome_input.focus = True
        except Exception:
            pass

    def _make_item(self, text):
        """Cria ListaItem com altura e alinhamento corretos."""
        btn = ListaItem(text=text)
        btn.height  = dp(52)   # mais compacto que dp(68)
        btn.valign = 'middle' # texto centralizado verticalmente
        return btn

    def atualizar(self):
        Animation.cancel_all(self.ids.empty_state)  # parar pulse antes de atualizar
        self.ids.lista_container.clear_widgets()
        registros = App.get_running_app().registros
        es = self.ids.empty_state

        if registros:
            Animation(opacity=0, duration=0.15).start(es)
            Clock.schedule_once(lambda _: setattr(es, 'height', 0), 0.15)
        else:
            es.height  = 200
            es.opacity = 0
            def _animar_empty(_):
                Animation(opacity=1, duration=0.4,
                          transition='out_quad').start(es)
                # Pulso suave continuo para nao parecer travado
                pulse = (Animation(opacity=0.55, duration=1.2, transition='in_out_sine') +
                         Animation(opacity=1.0,  duration=1.2, transition='in_out_sine'))
                pulse.repeat = True
                Clock.schedule_once(lambda _: pulse.start(es), 0.5)
            Clock.schedule_once(_animar_empty, 0.1)

        novos = []
        for r in registros:
            btn = self._make_item(self._texto_item(r))
            btn.bind(on_release=lambda x, dado=r, w=btn: self.confirmar_delete(dado, w))
            self.ids.lista_container.add_widget(btn)
            novos.append(btn)
        entrada_cascata(novos)

    @staticmethod
    def _dia_do_item(r):
        """Dia ('dd/mm/aaaa') de uma peça colada do WhatsApp; '' = sem dia."""
        return str(r[3]) if len(r) > 3 and r[3] else ''

    def _texto_item(self, r):
        dia = self._dia_do_item(r)
        if dia:                                   # veio do WhatsApp: mostra de que dia e
            nome = r[0][:13] + "…" if len(r[0]) > 13 else r[0]
            return (f"  [color=#3dff8f]{dia[:5]}[/color]  {nome}   ·   {r[1]} un.   ·   +{r[2]} XP")
        nome = r[0][:18] + "…" if len(r[0]) > 18 else r[0]
        return f"  {nome}   ·   {r[1]} un.   ·   +{r[2]} XP"

    # ── colar do WhatsApp ────────────────────────────────────────────────
    def colar_whatsapp(self):
        """Le o que esta copiado, acha as peças (nome e quantidade) de cada
        dia e, depois de conferir e dizer o XP, joga tudo na lista."""
        import importar_zap
        try:
            self.ids.nome_input.focus = False
            self.ids.qtd_input.focus = False
        except Exception:
            pass
        texto = ler_area_de_transferencia()
        achado = importar_zap.ler(texto) if texto.strip() else {'itens': []}
        if not achado['itens']:
            som.tocar_erro()
            tatil.erro()
            popup_aviso(("Não achei peças no texto copiado." if texto.strip() else "Não tem nada copiado.") +
                        "\nNo WhatsApp, segure uma mensagem,\nmarque as outras e toque em COPIAR.\n"
                        "Depois volte aqui e toque de novo.", titulo="COLAR DO WHATSAPP")
            return
        tatil.confirmar()
        popup_importar_zap(achado['itens'], self._pedir_xp_do_lote)

    def _pedir_xp_do_lote(self, itens):
        pecas = sum(it['qtd'] for it in itens)
        n = len(itens)
        Clock.schedule_once(lambda dt: popup_pedir_xp(
            f"{n} {'lote' if n == 1 else 'lotes'}", pecas, lambda xp: self._salvar_lote(itens, xp),
            titulo=">> COLADO DO WHATSAPP", pergunta="XP por peça (vale para todas):"), 0.25)

    def _salvar_lote(self, itens, xp):
        app = App.get_running_app()
        ganho = 0
        for it in itens:
            xp_total = max(0, int(xp)) * int(it['qtd'])
            app.registros.append([it['nome'], str(it['qtd']), xp_total, it['dia'], it.get('ts')])
            ganho += xp_total
        app.total_xp += ganho
        app.salvar_dados()
        som.tocar_add()
        tatil.confirmar()
        self.atualizar()
        self.atualizar_meta()
        if ganho:
            Clock.schedule_once(lambda dt: animar_ganho_xp(ganho), 0.3)

    def adicionar_item(self):
        n = self.ids.nome_input.text.strip()
        q = self.ids.qtd_input.text.strip()
        if not n:
            self._shake_input(self.ids.nome_input)
        if not q or not q.isdigit() or int(q) <= 0:
            self._shake_input(self.ids.qtd_input)
        if not (n and q and q.isdigit() and int(q) > 0):
            som.tocar_erro()
            tatil.erro()
            return
        popup_pedir_xp(n, int(q), lambda xp: self.salvar(n, q, xp))

    def _shake_input(self, inp):
        Animation.cancel_all(inp, 'borda_color')
        (Animation(borda_color=[1, 0.1, 0.2, 1],   duration=0.08) +
         Animation(borda_color=[1, 0.1, 0.2, 0.6], duration=0.08) +
         Animation(borda_color=[1, 0.1, 0.2, 1],   duration=0.08) +
         Animation(borda_color=[0, 0.9, 1, 0.25],  duration=0.35)).start(inp)

    def salvar(self, n, q, xp):
        app      = App.get_running_app()
        try:
            xp_total = xp * int(q)
        except (ValueError, TypeError):
            xp_total = 0
        antes = self._situacao()
        # [nome, qtd, xp, dia ('' = hoje), hora do lancamento] - a hora mede o ritmo
        app.registros.append([n, q, xp_total, '', round(time.time(), 1)])
        app.total_xp += xp_total
        app.salvar_dados()
        self.ids.nome_input.text = ""
        self.ids.qtd_input.text  = ""
        som.tocar_add()
        tatil.confirmar()
        self.ids.empty_state.opacity = 0
        self.ids.empty_state.height  = 0
        dado = app.registros[-1]
        btn = self._make_item(self._texto_item(dado))
        btn.bind(on_release=lambda x, d=dado, w=btn: self.confirmar_delete(d, w))
        self.ids.lista_container.add_widget(btn)
        entrada_cascata([btn], dy=dp(30))
        # o Yoru aparece e 'carimba' o +XP com um corte curto (o numero nasce
        # no corte); espera o item novo terminar de entrar na lista
        def _carimbo(dt):
            try:
                from cenas import kirito_carimbo
                kirito_carimbo(btn, lambda: animar_ganho_xp(xp_total, origem=btn))
            except Exception as e:
                print(f"[registro] carimbo: {e}")
                animar_ganho_xp(xp_total, origem=btn)
        Clock.schedule_once(_carimbo, 0.42)
        Clock.schedule_once(lambda _: self._focar_nome(), 0.15)
        self.atualizar_meta()
        self._comemorar(antes, self._situacao())

    # ── metas de producao ────────────────────────────────────────────────
    def _situacao(self):
        """(pecas na semana, pecas hoje, meta de hoje, faixa da semana)."""
        app = App.get_running_app()
        cfg = metas.completar_cfg(app.config_ganhos)
        hoje = datetime.now().date()
        sem, hj = metas.pecas_da_semana(app.memorias, app.registros, hoje)
        prox = metas.proxima_faixa(sem, cfg)
        alvo = prox['inicio'] if prox else int(cfg['meta_bonus'])
        md = metas.meta_diaria(alvo, sem, hj, hoje, cfg['pecas_sabado'])
        return sem, hj, md['hoje_meta'], metas.faixa_de(sem, cfg)[0]

    def atualizar_meta(self):
        """A faixa do topo: o que saiu hoje, a meta do dia, o ritmo e quanto falta."""
        try:
            app = App.get_running_app()
            cfg = metas.completar_cfg(app.config_ganhos)
            hoje = datetime.now().date()
            sem, hj = metas.pecas_da_semana(app.memorias, app.registros, hoje)
            prox = metas.proxima_faixa(sem, cfg)
            alvo = prox['inicio'] if prox else int(cfg['meta_bonus'])
            md = metas.meta_diaria(alvo, sem, hj, hoje, cfg['pecas_sabado'])
            r = metas.ritmo(metas.lotes_de_hoje(app.registros, hoje))
            partes = []
            if hoje.weekday() == 6:
                partes.append("[color=#8c96aa]DOMINGO  ·  folga[/color]")
            elif md['hoje_meta'] > 0:
                cor = '#00ff88' if hj >= md['hoje_meta'] else '#00e5ff'
                partes.append(f"[color=#9aa6bd]HOJE[/color] [color={cor}][b]{fmt_br(hj)}[/b][/color]"
                              f"[color=#9aa6bd]/{fmt_br(md['hoje_meta'])}[/color]")
            else:
                partes.append(f"[color=#9aa6bd]HOJE[/color] [color=#00ff88][b]{fmt_br(hj)}[/b][/color]")
            if r:
                cor_r = '#00ff88' if r >= metas.REF_REALISTA else ('#ffcc00' if r >= 45 else '#ff6a6a')
                partes.append(f"[color={cor_r}][b]{int(round(r))}[/b]/h[/color]")
                if md['hoje_falta'] > 0:
                    partes.append(f"[color=#9aa6bd]~{metas.tempo_txt(md['hoje_falta'] / r)}[/color]")
            if md['hoje_meta'] > 0 and hj >= md['hoje_meta']:
                partes.append("[color=#ffcc00]META BATIDA[/color]")
            self.ids.lbl_meta_hoje.text = "  ·  ".join(partes) + "   [color=#00e5ff88]>>[/color]"
        except Exception as e:
            print(f"[registro] meta: {e}")

    def _comemorar(self, antes, depois):
        """Passou da meta do dia ou de faixa da semana com este lote: festa."""
        try:
            sem0, hj0, meta0, fx0 = antes
            sem1, hj1, meta1, fx1 = depois
            if fx1 > fx0:
                cfg = metas.completar_cfg(App.get_running_app().config_ganhos)
                v = metas.faixas(cfg)[fx1][1]
                Clock.schedule_once(lambda dt: self._festa(
                    f"FAIXA NOVA!  Todas as peças da semana valem R$ {fmt_br(v, 2)}", True), 2.6)
            elif meta0 > 0 and hj0 < meta0 <= hj1:
                Clock.schedule_once(lambda dt: self._festa("META DE HOJE BATIDA!", False), 2.6)
        except Exception as e:
            print(f"[registro] comemorar: {e}")

    def _festa(self, texto, grande):
        try:
            som.tocar_level_up() if grande else som.tocar_finalizar()
            tatil.vitoria()
            tremer_tela(14 if grande else 8)
            from cenas import kirito_meta
            kirito_meta(self.ids.lbl_meta_hoje)
            lbl = self.ids.lbl_meta_hoje
            (Animation(color=[1, 0.88, 0.1, 1], duration=0.12) + Animation(duration=0.5) +
             Animation(color=[1, 1, 1, 1], duration=0.4)).start(lbl)
            self._aviso_subindo(texto)
        except Exception as e:
            print(f"[registro] festa: {e}")

    def _aviso_subindo(self, texto):
        from kivy.uix.label import Label
        from kivy.core.window import Window
        lbl = Label(text=f"[b]{texto}[/b]", markup=True, font_name="orbitron.ttf", font_size="13sp",
                    color=(1, 0.88, 0.1, 0), halign="center", valign="middle", size_hint=(None, None),
                    size=(Window.width * 0.92, dp(44)), pos=(Window.width * 0.04, Window.height * 0.62))
        lbl.text_size = lbl.size
        Window.add_widget(lbl)
        a = (Animation(color=(1, 0.88, 0.1, 1), y=lbl.y + dp(18), duration=0.25, transition='out_back') +
             Animation(duration=1.6) + Animation(color=(1, 0.88, 0.1, 0), y=lbl.y + dp(40), duration=0.4))
        a.bind(on_complete=lambda *_: Window.remove_widget(lbl))
        a.start(lbl)

    def abrir_meta(self):
        """Toque na faixa do topo: o painel da meta (hoje, ritmo, semana)."""
        som.tocar_click()
        tatil.botao()
        try:
            from helpers import popup_meta_producao
            popup_meta_producao()
        except Exception as e:
            print(f"[registro] painel da meta: {e}")

    def confirmar_delete(self, dado, btn):
        def _fazer():
            som.tocar_delete()
            tatil.forte()
            # o Yoru corta o lote com o saque relampago e depois vem a explosao de cacos
            from cenas import kirito_fatiar
            kirito_fatiar(btn, lambda: self.deletar(dado), tipo='iai')
        popup_delete_engracado(_fazer)

    def deletar(self, dado):
        app = App.get_running_app()
        try:
            app.registros.remove(dado)
            app.total_xp = max(0, app.total_xp - dado[2])
            app.salvar_dados()
        except ValueError:
            pass
        self.atualizar()
        self.atualizar_meta()

    def finalizar_dia(self):
        app = App.get_running_app()
        if not app.registros:
            som.tocar_erro()
            tatil.erro()
            return
        tot_pecas = sum(int(x[1]) for x in app.registros)
        tot_xp    = sum(int(x[2]) for x in app.registros)
        # peças coladas do WhatsApp ja tem dia: cada dia vira um turno separado
        por_dia = {}
        for r in app.registros:
            por_dia.setdefault(self._dia_do_item(r), []).append(r)
        sem_dia = por_dia.pop('', [])

        def _ordem(dia):
            try:
                return datetime.strptime(dia, "%d/%m/%Y")
            except ValueError:
                return datetime.max
        dias = sorted(por_dia, key=_ordem)

        def _confirmar(data_str):
            import time
            # Guardar XP anterior para animacao de progresso
            app.xp_anterior = getattr(app, "total_xp", 0)
            partes = data_str.strip().split()
            hora = partes[1] if len(partes) > 1 else datetime.now().strftime("%H:%M")
            grupos = {d: list(por_dia[d]) for d in dias}
            if sem_dia:                             # as digitadas vao para a data escolhida
                grupos.setdefault(partes[0], []).extend(sem_dia)
            agora = time.time()
            for k, dia in enumerate(sorted(grupos, key=_ordem)):
                itens = [[r[0], r[1], r[2]] for r in grupos[dia]]
                app.memorias.append({
                    "data":  f"{dia}  {hora}",
                    "total": sum(int(x[1]) for x in itens),
                    "xp":    sum(int(x[2]) for x in itens),
                    "itens": itens,
                    "ts":    round(agora + k * 0.001, 3),     # identidade do turno (ganhos)
                })
            app.registros.clear()
            app.recalcular_totais()                 # total, melhor dia e sequencia saem das datas
            app.salvar_dados()
            som.tocar_finalizar()
            tatil.vitoria()
            tremer_tela(12)
            self.atualizar_meta()
            # onde cada peca estava na lista: e dali que elas voam para o cartao do turno
            linhas, area = [], None
            try:
                sv = self.ids.lista_container.parent
                sx, sy = sv.to_window(sv.x, sv.y)
                area = (sx, sy, sx + sv.width, sy + sv.height)
            except Exception:
                pass
            for w in self.ids.lista_container.children:
                try:
                    x, y = w.to_window(w.x, w.y)
                    linhas.append((x, y, w.width, w.height))
                except Exception:
                    pass
            self.atualizar()
            # o Yoru guarda o turno: as pecas viram um cartao, ele embainha e carimba
            try:
                from cenas import kirito_vitoria
                Clock.schedule_once(lambda dt: kirito_vitoria(self, linhas, area), 0.35)
            except Exception as e:
                print(f"[registro] vitoria: {e}")

        popup_resumo_dia(tot_pecas, tot_xp, _confirmar,
                         dias=[(d, sum(int(x[1]) for x in por_dia[d])) for d in dias],
                         pede_data=bool(sem_dia) or not dias)
