"""telas/progresso.py — TelaProgresso"""
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.animation import Animation
from helpers import calcular_level, obter_titulo_level, em


class TelaProgresso(Screen):

    def on_leave(self, *_):
        try:
            self.ids.barra_circular.parar_animacoes()
        except Exception:
            pass

    def on_enter(self):
        app   = App.get_running_app()
        level, xp_atual, xp_necessario = calcular_level(app.total_xp)

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
