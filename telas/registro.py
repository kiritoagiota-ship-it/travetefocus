"""telas/registro.py — TelaRegistro com sons temáticos"""
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp
from efeitos import ListaItem, explodir_estilhacos, tremer_tela
from helpers import popup_pedir_xp, popup_delete_engracado, popup_resumo_dia, animar_ganho_xp
from datetime import datetime
import som


class TelaRegistro(Screen):

    def on_enter(self):
        self.atualizar()
        self._foco_ev = Clock.schedule_once(self._focar_nome, 0.35)

    def on_leave(self, *_):
        if hasattr(self, '_foco_ev') and self._foco_ev:
            self._foco_ev.cancel()
            self._foco_ev = None

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
        btn.valign  = 'middle' # texto centralizado verticalmente
        return btn

    def atualizar(self):
        self.ids.lista_container.clear_widgets()
        registros = App.get_running_app().registros
        es = self.ids.empty_state

        if registros:
            Animation(opacity=0, duration=0.15).start(es)
            Clock.schedule_once(lambda _: setattr(es, 'height', 0), 0.15)
        else:
            es.height  = 200
            es.opacity = 0
            Clock.schedule_once(
                lambda _: Animation(opacity=1, duration=0.4,
                                    transition='out_quad').start(es), 0.1)

        for i, r in enumerate(registros):
            nome = r[0][:18] + "…" if len(r[0]) > 18 else r[0]
            btn  = self._make_item(f"  {nome}   ·   {r[1]} un.   ·   +{r[2]} XP")
            btn.bind(on_release=lambda x, dado=r, w=btn: self.confirmar_delete(dado, w))
            btn.opacity = 0
            self.ids.lista_container.add_widget(btn)
            Clock.schedule_once(
                lambda dt, b=btn: Animation(
                    opacity=1, duration=0.25, transition='out_quad').start(b),
                i * 0.06)

    def adicionar_item(self):
        n = self.ids.nome_input.text.strip()
        q = self.ids.qtd_input.text.strip()
        if not n:
            self._shake_input(self.ids.nome_input)
        if not q or not q.isdigit() or int(q) <= 0:
            self._shake_input(self.ids.qtd_input)
        if not (n and q and q.isdigit() and int(q) > 0):
            som.tocar_erro()
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
        xp_total = xp * int(q)
        app.registros.append([n, q, xp_total])
        app.total_xp += xp_total
        app.salvar_dados()
        self.ids.nome_input.text = ""
        self.ids.qtd_input.text  = ""
        som.tocar_add()
        animar_ganho_xp(xp_total)
        self.ids.empty_state.opacity = 0
        self.ids.empty_state.height  = 0
        dado = app.registros[-1]
        nome_curto = n[:18] + "…" if len(n) > 18 else n
        btn = self._make_item(f"  {nome_curto}   ·   {q} un.   ·   +{xp_total} XP")
        btn.bind(on_release=lambda x, d=dado, w=btn: self.confirmar_delete(d, w))
        btn.opacity = 0
        self.ids.lista_container.add_widget(btn)
        Animation(opacity=1, duration=0.35, transition='out_quad').start(btn)
        Clock.schedule_once(lambda _: self._focar_nome(), 0.15)

    def confirmar_delete(self, dado, btn):
        def _fazer():
            som.tocar_delete()
            explodir_estilhacos(btn, lambda: self.deletar(dado))
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

    def finalizar_dia(self):
        app = App.get_running_app()
        if not app.registros:
            som.tocar_erro()
            return
        tot_pecas = sum(int(x[1]) for x in app.registros)
        tot_xp    = sum(int(x[2]) for x in app.registros)

        def _confirmar(data_str):
            app.memorias.append({
                "data":  data_str, "total": tot_pecas,
                "xp":    tot_xp,  "itens": list(app.registros)
            })
            app.total_geral += tot_pecas
            if tot_pecas > app.melhor_dia:
                app.melhor_dia = tot_pecas
            hoje_str = data_str.strip().split()[0].strip()
            if app.ultima_data:
                try:
                    from datetime import datetime as DT
                    d1   = DT.strptime(app.ultima_data, "%d/%m/%Y")
                    d2   = DT.strptime(hoje_str,        "%d/%m/%Y")
                    diff = (d2 - d1).days
                    if   diff == 1: app.streak += 1
                    elif diff == 0: pass
                    else:           app.streak  = 1
                except Exception:
                    app.streak = 1
            else:
                app.streak = 1
            app.ultima_data = hoje_str
            app.registros.clear()
            app.salvar_dados()
            som.tocar_finalizar()
            tremer_tela(12)
            self.atualizar()

        popup_resumo_dia(tot_pecas, tot_xp, _confirmar)
