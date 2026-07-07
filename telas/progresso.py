"""telas/progresso.py — TelaProgresso"""
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from helpers import calcular_level, obter_titulo_level, em
import som


class TelaProgresso(Screen):

    def _animar_xp_ganho(self, xp_ant, xp_novo, xp_max):
        """Anima a barra de XP com som. Detecta level-up."""
        app   = App.get_running_app()
        barra = self.ids.barra_circular

        if xp_ant is None:
            # Sem XP novo — apenas mostrar estado atual
            barra.animar_progresso()
            return

        level_ant, _, _ = calcular_level(xp_ant)
        level_nov, xp_atual, xp_nec = calcular_level(xp_novo)
        houve_level_up = level_nov > level_ant

        # Iniciar barra do zero e animar até o novo valor
        barra.valor  = 0
        barra.maximo = max(1, xp_nec)

        def _start_anim(dt):
            try: som.tocar_xp_subindo()
            except Exception: pass
            Animation(valor=xp_atual, duration=1.2,
                      transition="out_expo").start(barra)
            if houve_level_up:
                Clock.schedule_once(_level_up_fanfare, 1.3)

        def _level_up_fanfare(dt):
            try: som.tocar_level_up()
            except Exception: pass
            # Flash dourado no label de level
            lbl = self.ids.lbl_level_num
            (Animation(color=[1, 0.88, 0.1, 1], duration=0.15) +
             Animation(color=[1, 0.88, 0.1, 1], duration=0.40) +
             Animation(color=[0, 0.9, 1,   1], duration=0.35)).start(lbl)
            tremer = getattr(__import__("efeitos"), "tremer_tela", None)
            if tremer:
                try: tremer(20)
                except Exception: pass

        Clock.schedule_once(_start_anim, 0.4)

    def on_leave(self, *_):
        try:
            self.ids.barra_circular.parar_animacoes()
        except Exception:
            pass

    def on_enter(self):
        app   = App.get_running_app()
        level, xp_atual, xp_necessario = calcular_level(app.total_xp)
        # Verificar se houve ganho de XP desde a última visita
        xp_ant = getattr(app, "xp_anterior", None)
        if xp_ant is not None and xp_ant != app.total_xp:
            app.xp_anterior = None   # consumir flag
            self._animar_xp_ganho(xp_ant, app.total_xp, xp_necessario)
        else:
            self._animar_xp_ganho(None, None, None)

        self.ids.lbl_level_num.text   = f"LVL  {level}"
        self.ids.lbl_titulo.text      = obter_titulo_level(level)
        self.ids.lbl_xp_fracao.text   = f"{xp_atual}  /  {xp_necessario} XP"
        self.ids.lbl_total_xp.text    = f"XP TOTAL\n[color=#00e5ff]{app.total_xp}[/color]"
        self.ids.lbl_total_pecas.text = f"PECAS TOTAL\n[color=#00e5ff]{app.total_geral}[/color]"
        self.ids.lbl_melhor_dia.text  = f"MELHOR DIA\n[color=#ffcc00]{app.melhor_dia} un.[/color]"

        streak = app.streak
        barra  = self.ids.barra_circular

        if streak >= 5:
            barra.cor_anel = [1, 0.55, 0, 1]
            # em() renderiza o emoji com NotoEmoji se disponivel, senao usa texto
            self.ids.lbl_streak.text  = f"{em('🔥')}  STREAK  {streak}  DIAS"
            self.ids.lbl_streak.color = (1, 0.5, 0, 1)
            fire = (Animation(cor_anel=[1, 0.42, 0, 1], duration=0.7,
                              transition='in_out_sine') +
                    Animation(cor_anel=[1, 0.88, 0.1, 1], duration=0.7,
                              transition='in_out_sine'))
            fire.repeat       = True
            barra._anim_pulso = fire
            fire.start(barra)
        else:
            barra.cor_anel = [0, 0.9, 1, 1]
            self.ids.lbl_streak.text  = f"STREAK  {streak}  DIAS"
            self.ids.lbl_streak.color = (0, 0.9, 1, 0.7)

        barra.valor  = xp_atual
        barra.maximo = max(1, xp_necessario)
        barra.animar_progresso()
