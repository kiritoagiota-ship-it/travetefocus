"""Acentos nos textos que aparecem na tela (so textos: chaves e valores
salvos como 'semanal', 'TODOS', 'tipo_periodo' ficam iguais) + detalhes:
'Abrir periodo' so quando da para abrir, titulo do Progresso legivel."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch as _patch


def patch(caminho, reps):
    # pode rodar de novo: pula o que ja foi trocado
    txt = open(caminho, encoding='utf-8').read()     # modo texto: fim de linha vira so LF
    _patch(caminho, [(a, b) for a, b in reps if not (a not in txt and b in txt)])


A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
J = lambda *p: os.path.join(A, *p)

patch(J('interface.kv'), [
    ('text:         ">>  MEMORIAS"', 'text:         ">>  MEMÓRIAS"'),
    ('"[color=#444444]--  Nenhum periodo aberto  --[/color]"', '"[color=#444444]--  Nenhum período aberto  --[/color]"'),
    ("""            BoxLayout:
                size_hint_y: None
                height:      dp(46)
                spacing:     dp(10)
                BotaoAngular:
                    text:         ">>  ABRIR PERIODO\"""", """            BoxLayout:
                size_hint_y: None
                height:      dp(46)
                spacing:     0              # so um dos dois aparece de cada vez
                BotaoAngular:
                    id:           btn_abrir_periodo
                    text:         ">>  ABRIR PERÍODO\""""),
    ("""        Label:
            text:        "SISTEMA DE PROGRESSO"
            font_name:   "orbitron.ttf"
            font_size:   "14sp"
            color:       rgba("#00e5ff44")
            size_hint_y: None
            height:      dp(24)""", """        Label:
            text:        "SISTEMA DE PROGRESSO"
            font_name:   "orbitron.ttf"
            font_size:   "17sp"
            color:       rgba("#00e5ff")
            bold:        True
            size_hint_y: None
            height:      dp(30)"""),
])

patch(J('helpers.py'), [
    ('"[color=#ff2244]!!  ATENCAO[/color]\\n"', '"[color=#ff2244]!!  ATENÇÃO[/color]\\n"'),
])

patch(J('exportar.py'), [
    ("'*RELATORIO TRAVETEFOCUS*'", "'*RELATÓRIO TRAVETEFOCUS*'"),
    ("f'Total de pecas:  {total_pecas}'", "f'Total de peças:  {total_pecas}'"),
    ("{melhor.get(\"total\", 0)} pecas (", "{melhor.get(\"total\", 0)} peças ("),
    ("'*ULTIMOS 10 TURNOS:*'", "'*ÚLTIMOS 10 TURNOS:*'"),
    ('"Nao consegui abrir o WhatsApp.\\nA mensagem foi copiada: cole no grupo."',
     '"Não consegui abrir o WhatsApp.\\nA mensagem foi copiada: cole no grupo."'),
    ('"Nao consegui abrir o WhatsApp."\n', '"Não consegui abrir o WhatsApp."\n'),
    ('"Nao consegui copiar a mensagem."', '"Não consegui copiar a mensagem."'),
    ('"Nao foi possivel gerar o relatorio (dados inconsistentes)."',
     '"Não foi possível gerar o relatório (dados inconsistentes)."'),
])

patch(J('telas', 'ganhos.py'), [
    ("""            self.ids.lbl_periodo_status.text = "[color=#8c96aa]--  Nenhum periodo aberto  --[/color]"
            self.ids.lbl_periodo_pecas.text  = ""
            self.ids.lbl_periodo_ganho.text  = ""
            self.ids.lbl_periodo_bonus.text  = "[color=#8c96aa]Configure abaixo e toque em ABRIR PERIODO[/color]"
            self.ids.btn_fechar_periodo.opacity  = 0
            self.ids.btn_fechar_periodo.disabled = True
            return
""", """            self.ids.lbl_periodo_status.text = "[color=#8c96aa]--  Nenhum período aberto  --[/color]"
            self.ids.lbl_periodo_pecas.text  = ""
            self.ids.lbl_periodo_ganho.text  = ""
            self.ids.lbl_periodo_bonus.text  = "[color=#8c96aa]Configure abaixo e toque em ABRIR PERÍODO[/color]"
            self._mostrar_botao(self.ids.btn_abrir_periodo, True)
            self._mostrar_botao(self.ids.btn_fechar_periodo, False)
            return
"""),
    ("tipo     = aberto.get('tipo', 'periodo').capitalize()", "tipo     = aberto.get('tipo', 'período').capitalize()"),
    ('f"[color=#9aa6bd]Pecas[/color]', 'f"[color=#9aa6bd]Peças[/color]'),
    ('f"[color=#9aa6bd]Projecao[/color]', 'f"[color=#9aa6bd]Projeção[/color]'),
    ("META BATIDA! Todas as pecas valem {bonus_rs} \"\n                f\"(+{_reais(extra)} de bonus)",
     "META BATIDA! Todas as peças valem {bonus_rs} \"\n                f\"(+{_reais(extra)} de bônus)"),
    ("{fmt_br(faltam)} pecas para a meta", "{fmt_br(faltam)} peças para a meta"),
    ("""        self.ids.btn_fechar_periodo.opacity  = 1
        self.ids.btn_fechar_periodo.disabled = False
""", """        self._mostrar_botao(self.ids.btn_abrir_periodo, False)   # ja tem um aberto
        self._mostrar_botao(self.ids.btn_fechar_periodo, True)

    @staticmethod
    def _mostrar_botao(btn, sim):
        \"\"\"Mostra o botao ocupando a linha toda, ou some com ele (sem espaco).\"\"\"
        btn.opacity    = 1 if sim else 0
        btn.disabled   = not sim
        btn.size_hint_x = 1 if sim else None
        if not sim:
            btn.width = 0
"""),
    ('text="[ SEM PERIODOS FECHADOS ]"', 'text="[ SEM PERÍODOS FECHADOS ]"'),
    ('"[color=#ff2244]!!  APAGAR PERIODO?[/color]\\n"', '"[color=#ff2244]!!  APAGAR PERÍODO?[/color]\\n"'),
    ('invalidos.append("BONUS")', 'invalidos.append("BÔNUS")'),
    ('"VALOR INVALIDO: "', '"VALOR INVÁLIDO: "'),
    ('"CALCULO SALVO: base " + _reais(cfg[\'valor_base\']) + " / bonus "',
     '"CÁLCULO SALVO: base " + _reais(cfg[\'valor_base\']) + " / bônus "'),
    ('>>  PERIODO ENCERRADO  <<', '>>  PERÍODO ENCERRADO  <<'),
    ('(+{_reais(v_bonus - sem_meta)} de bonus)', '(+{_reais(v_bonus - sem_meta)} de bônus)'),
    ("{fmt_br(cfg['meta_bonus'])} nao batida", "{fmt_br(cfg['meta_bonus'])} não batida"),
    ('f"[color=#aab4c8]Periodo[/color]   "', 'f"[color=#aab4c8]Período[/color]   "'),
    ('f"[color=#aab4c8]Total de pecas[/color]   "', 'f"[color=#aab4c8]Total de peças[/color]   "'),
])

patch(J('telas', 'loading.py'), [
    ('"[color=#ff8855]VERIFICACAO DE IDENTIDADE NECESSARIA[/color]"',
     '"[color=#ff8855]VERIFICAÇÃO DE IDENTIDADE NECESSÁRIA[/color]"'),
    ('"[color=#888888]Insira o codigo de acesso:[/color]"', '"[color=#888888]Insira o código de acesso:[/color]"'),
    ('Forcando LIMIT BREAK', 'Forçando LIMIT BREAK'),
])

patch(J('telas', 'memorias.py'), [
    ("popular o banco de memorias.", "popular o banco de memórias."),
    ("Nenhum item detalhado disponivel.", "Nenhum item detalhado disponível."),
    ('"Nao consegui preparar a mensagem."', '"Não consegui preparar a mensagem."'),
    ('"Modulo exportar.py nao encontrado no repositorio."', '"Módulo exportar.py não encontrado no repositório."'),
    ("Apagar TODAS as memorias e XP?", "Apagar TODAS as memórias e XP?"),
])

patch(J('telas', 'progresso.py'), [
    ('f"PECAS TOTAL\\n', 'f"PEÇAS TOTAL\\n'),
])
print('ok')
