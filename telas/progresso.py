"""telas/progresso.py — TelaProgresso"""
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from helpers import calcular_level, obter_titulo_level, em
import som
from animacoes_ui import entrada_cascata, contar, fmt_br


class TelaProgresso(Screen):

    def _animar_xp_ganho(self, xp_ant, xp_novo, xp_max):
        """Som de XP subindo e fanfarra se subiu de level. O preenchimento do
        anel e feito uma unica vez no on_enter (antes eram duas animacoes
        brigando pelo mesmo anel, uma com os valores da visita anterior)."""
        if xp_ant is None:
            return

        level_ant, _, _ = calcular_level(xp_ant)
        level_nov, _, _ = calcular_level(xp_novo)
        houve_level_up = level_nov > level_ant

        def _start_anim(dt):
            try: som.tocar_xp_subindo()
            except Exception: pass
            if houve_level_up:
                Clock.schedule_once(_level_up_fanfare, 1.3)

        def _level_up_fanfare(dt):
            try: som.tocar_level_up()
            except Exception: pass
            # o Yoru comemora do lado do nivel
            try:
                from cenas import kirito_nivel
                kirito_nivel(self.ids.lbl_level_num)
            except Exception as e:
                print(f"[progresso] yoru: {e}")
            # Flash dourado no label de level
            lbl = self.ids.lbl_level_num
            (Animation(color=[1, 0.88, 0.1, 1], duration=0.15) +
             Animation(color=[1, 0.88, 0.1, 1], duration=0.40) +
             Animation(color=[0, 0.9, 1,   1], duration=0.35)).start(lbl)
            try:
                from efeitos import tremer_tela as _tremer
                _tremer(20)
            except Exception:
                pass

        Clock.schedule_once(_start_anim, 0.1)

    def on_leave(self, *_):
        try:
            self.ids.barra_circular.parar_animacoes()
        except Exception:
            pass

    def _cascata_cards(self):
        cards, vistos = [], set()
        for nome in ('lbl_level_num', 'lbl_titulo', 'lbl_streak', 'barra_circular',
                     'lbl_xp_fracao', 'lbl_total_xp', 'lbl_total_pecas', 'lbl_melhor_dia'):
            w = self.ids.get(nome)
            if w is None:
                continue
            # anima o card (pai) quando o label esta num BoxLayout pequeno proprio
            alvo = w.parent if (w.parent is not None and w.parent is not self
                                and len(w.parent.children) <= 3) else w
            if id(alvo) not in vistos:
                vistos.add(id(alvo))
                cards.append(alvo)
        entrada_cascata(cards, atraso=0.06)

    @staticmethod
    def _sequencia_valida(app):
        """A sequencia so vale se o ultimo turno finalizado foi hoje ou no
        ultimo dia de trabalho (na segunda, o sabado vale: domingo e folga);
        passou disso, ela quebrou (mostra 0 ate o proximo turno)."""
        try:
            import metas
            from datetime import datetime as DT
            ultima = DT.strptime(app.ultima_data, "%d/%m/%Y").date()
            if not metas.sequencia_vale(ultima, DT.now().date()):
                return 0
        except Exception:
            pass
        return int(app.streak or 0)

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
        contar(self.ids.lbl_xp_fracao, xp_atual,
               lambda v: f"{fmt_br(v)}  /  {fmt_br(xp_necessario)} XP", duracao=1.2, atraso=0.4)
        contar(self.ids.lbl_total_xp, app.total_xp,
               lambda v: f"XP TOTAL\n[color=#00e5ff]{fmt_br(v)}[/color]", atraso=0.15)
        contar(self.ids.lbl_total_pecas, app.total_geral,
               lambda v: f"PEÇAS TOTAL\n[color=#00e5ff]{fmt_br(v)}[/color]", atraso=0.22)
        contar(self.ids.lbl_melhor_dia, app.melhor_dia,
               lambda v: f"MELHOR DIA\n[color=#ffcc00]{fmt_br(v)} un.[/color]", atraso=0.29)
        self._cascata_cards()

        streak = self._sequencia_valida(app)
        barra  = self.ids.barra_circular
        # valores do anel antes de qualquer animacao (uma unica, sem estouro)
        barra.maximo = max(1, xp_necessario)
        barra.valor  = min(xp_atual, barra.maximo)
        barra.animar_progresso()

        if streak >= 5:
            barra.cor_anel = [1, 0.55, 0, 1]
            # em() renderiza o emoji com NotoEmoji se disponivel, senao usa texto
            self.ids.lbl_streak.text  = f"{em('🔥')}  STREAK  {streak}  {'DIA' if streak == 1 else 'DIAS'}"
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
            self.ids.lbl_streak.text  = f"STREAK  {streak}  {'DIA' if streak == 1 else 'DIAS'}"
            self.ids.lbl_streak.color = (0, 0.9, 1, 0.7)

