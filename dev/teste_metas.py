"""Testa as contas das metas (metas.py): faixas, o que falta, meta diaria e ritmo.
uso: python dev/teste_metas.py   -> "N casos, 0 falhas" """
import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import metas as M  # noqa: E402

falhas = []
casos = [0]


def ok(cond, txt):
    casos[0] += 1
    print(('OK    ' if cond else 'FALHA ') + txt)
    if not cond:
        falhas.append(txt)


C = M.completar_cfg({'valor_base': 0.25, 'valor_bonus': 0.30, 'meta_bonus': 3000, 'tipo_periodo': 'semanal'})
ok(C['valor_meio'] == 0.27 and C['meta_meio'] == 2500 and C['pecas_sabado'] == 200,
   'config antiga ganha a faixa do meio 0,27 / 2.500 e o sabado 200')
ok(M.completar_cfg({'valor_meio': 0.28})['valor_meio'] == 0.28, 'config que ja tem o campo nao e trocada')

# faixas: o valor da faixa vale para TODAS as pecas
ok(M.ganho(2499, C) == 624.75, '2.499 pecas = R$ 624,75 (0,25)')
ok(M.ganho(2500, C) == 675.00, '2.500 pecas = R$ 675,00 (0,27 em todas)')
ok(M.ganho(2999, C) == 809.73, '2.999 pecas = R$ 809,73')
ok(M.ganho(3000, C) == 900.00, '3.000 pecas = R$ 900,00 (0,30 em todas)')
ok(M.ganho(0, C) == 0, 'zero pecas = zero')
p = M.proxima_faixa(2400, C)
ok(p['falta'] == 100 and p['valor'] == 0.27 and p['a_mais'] == 75.0, '2.400: faltam 100 para 0,27 e rende +R$ 75,00')
p = M.proxima_faixa(2700, C)
ok(p['falta'] == 300 and p['a_mais'] == 171.0, '2.700: faltam 300 para 0,30 e rende +R$ 171,00')
ok(M.proxima_faixa(3200, C) is None, '3.200: ja esta na ultima faixa')
ruim = dict(C, meta_meio=3500)
ok(len(M.faixas(ruim)) == 2, 'faixa do meio maior que a de cima e ignorada (sem conta maluca)')

# semana e meta diaria (13/10/2026 e uma terca)
ter = date(2026, 10, 13)
ok(M.segunda_da_semana(ter) == date(2026, 10, 12), 'a semana de uma terca comeca na segunda')
ok(M.segunda_da_semana(date(2026, 10, 18)) == date(2026, 10, 19), 'no domingo a conta ja e da semana seguinte')
mem = [{'data': '12/10/2026  17:00', 'total': 450}, {'data': '10/10/2026  12:00', 'total': 200},
       {'data': 'lixo', 'total': 'x'}]
reg = [['Camisa', '100', 300], ['Calca', '50', 150, '', 0], ['Short', '30', 90, '12/10/2026']]
sem, hj = M.pecas_da_semana(mem, reg, ter)
ok(sem == 630 and hj == 150, 'semana = 450 (seg) + 30 (colado de seg) + 150 (hoje); hoje = 150')
m = M.meta_diaria(3000, 1150, 0, date(2026, 10, 14), 200)          # quarta, nada feito ainda hoje
ok(m['falta'] == 1850 and m['por_dia'] == 550 and m['sabado'] == 200 and m['dias'] == 3,
   'quarta, 1.150 feitas: faltam 1.850 -> 550 por dia (qua a sex) + 200 no sabado')
m = M.meta_diaria(3000, 1150, 0, date(2026, 10, 12), 200)
ok(m['dias'] == 5 and m['por_dia'] == 330, 'segunda: 5 dias uteis')
m = M.meta_diaria(2500, 1300, 300, date(2026, 10, 14), 200)
ok(m['por_dia'] == 434 and m['hoje_falta'] == 134, 'quarta com 300 ja feitas hoje: (2.500 - 1.000 - 200) / 3 = meta 434, faltam 134 hoje')
m = M.meta_diaria(2500, 2400, 0, date(2026, 10, 17), 200)
ok(m['e_sabado'] and m['hoje_falta'] == 100, 'sabado: o que falta e tudo hoje')
m = M.meta_diaria(2500, 2600, 0, ter, 200)
ok(m['batida'] and m['por_dia'] == 0, 'faixa ja batida: nada por dia')
m = M.meta_diaria(2500, 2400, 0, ter, 200)
ok(m['por_dia'] == 0 and m['sabado'] == 100, 'faltam so 100: cabem no sabado')
m = M.meta_diaria(2500, 1000, 0, date(2026, 10, 18), 200)
ok(m['dias'] == 5 and m['falta'] == 2500, 'domingo: conta a semana nova inteira')

# ritmo
base = datetime(2026, 10, 13, 7, 0).timestamp()
lotes = [(base, 50), (base + 3600, 52), (base + 7200, 48)]
r = M.ritmo(lotes)
ok(r is not None and abs(r - 50) < 0.01, '3 lotes de hora em hora (52 e 48 depois do primeiro): 50/h')
ok(M.ritmo(lotes[:1]) is None, 'um lote so: ainda nao da para medir')
ok(M.ritmo([(base, 10), (base + 300, 10)]) is None, 'menos de 15 min: ainda nao mede')
almoco = [(base, 50), (base + 3600, 50), (base + 3600 * 3, 50), (base + 3600 * 4, 50)]
r = M.ritmo(almoco)
ok(r is not None and abs(r - 50) < 0.01, 'intervalo do almoco (2h para 50 pecas) nao derruba o ritmo')
reg = [['A', '50', 1, '', base], ['B', '52', 1, '', base + 3600], ['C', '10', 1], ['D', '5', 1, '', 'x'],
       ['E', '9', 1, '', (datetime(2026, 10, 12, 9)).timestamp()]]
ok(len(M.lotes_de_hoje(reg, ter)) == 2, 'lotes sem hora, com hora estragada ou de outro dia ficam de fora')
ok(M.tempo_txt(1.5) == '1h30' and M.tempo_txt(0.25) == '15 min', 'tempo escrito: 1h30 / 15 min')

# a sequencia de dias (domingo e folga)
d = lambda dd, mm: date(2026, mm, dd)
ok(M.sequencia({d(12, 10), d(13, 10), d(14, 10)}) == 3, 'seg-ter-qua seguidos: 3 dias')
ok(M.sequencia({d(9, 10), d(10, 10), d(12, 10), d(13, 10)}) == 4, 'sex-sab, (domingo de folga), seg-ter: 4 dias')
ok(M.sequencia({d(9, 10), d(12, 10)}) == 1, 'faltou o sabado: a sequencia recomeca')
ok(M.sequencia({d(10, 10), d(11, 10), d(12, 10)}) == 3, 'trabalhou no domingo (feriado ou extra): conta junto')
ok(M.sequencia(set()) == 0, 'sem turnos: 0')
ok(M.sequencia_vale(d(10, 10), d(12, 10)), 'na segunda, o turno de sabado ainda vale (domingo e folga)')
ok(not M.sequencia_vale(d(9, 10), d(12, 10)), 'na segunda, o ultimo turno na sexta: quebrou')
ok(M.sequencia_vale(d(13, 10), d(14, 10)) and not M.sequencia_vale(d(12, 10), d(14, 10)),
   'na quarta vale o de terca; o de segunda nao')

# L1: o lote esquecido fica no dia dele (14/11/2026 e um sabado, 16/11 a segunda)
sab14, seg16 = date(2026, 11, 14), date(2026, 11, 16)
ts_sab = datetime(2026, 11, 14, 9, 10).timestamp()
ts_seg = datetime(2026, 11, 16, 8, 0).timestamp()
ok(M.dia_do_lote(['A', '10', 1, '', ts_sab], seg16) == sab14, 'lote sem dia com hora de sabado e de sabado')
ok(M.dia_do_lote(['A', '10', 1, '13/11/2026', ts_sab], seg16) == date(2026, 11, 13), 'o dia gravado (WhatsApp) vale mais que a hora')
ok(M.dia_do_lote(['A', '10', 1], seg16) == seg16, 'lote antigo sem hora continua de hoje')
ok(M.dia_do_lote(['A', '10', 1, '', 0], seg16) == seg16 and M.dia_do_lote(['A', '10', 1, '', None], seg16) == seg16,
   'hora 0 ou vazia: hoje')
ok(M.dia_do_lote(['A', '10', 1, '', 'x'], seg16) == seg16, 'hora estragada: hoje (nao quebra)')
ok(M.dia_do_lote(['A', '10', 1, 'lixo'], seg16) is None, 'dia gravado estragado: fica de fora (como antes)')
esq = [['Camisa', '300', 900, '', ts_sab], ['Calca', '200', 600, '', ts_sab + 600]]
mem_sem = [{'data': '09/11/2026  17:00', 'total': 600}]
ok(M.pecas_da_semana(mem_sem, esq, sab14) == (1100, 500), 'no sabado: 600 + 500 na semana, 500 hoje')
ok(M.pecas_da_semana(mem_sem, esq, seg16) == (0, 0), 'na segunda: os lotes de sabado NAO viram de hoje nem da semana nova')
ok(M.pecas_da_semana([], esq + [['Short', '50', 1, '', ts_seg]], seg16) == (50, 50), 'segunda com lote novo: so ele conta')
ok(M.dias_pendentes(esq + [['Short', '50', 1, '', ts_seg]], seg16) == [sab14], 'lotes pendentes de outro dia: sabado')
ok(M.dias_pendentes([['Short', '50', 1, '', ts_seg], ['Velho', '5', 1]], seg16) == [], 'so lote de hoje: nada pendente')
ok(M.aviso_pendentes(esq, seg16) == 'Tem lotes de sábado sem finalizar', 'faixa do Registro: "Tem lotes de sábado sem finalizar"')
ok(M.aviso_pendentes(esq, date(2026, 11, 15)) == 'Tem lotes de ontem sem finalizar', 'no domingo: "de ontem"')
ok(M.aviso_pendentes(esq, date(2026, 11, 25)) == 'Tem lotes de 14/11 sem finalizar', 'mais de uma semana: a data')
dois = esq + [['X', '1', 1, '', datetime(2026, 11, 13, 9).timestamp()]]
ok(M.aviso_pendentes(dois, seg16) == 'Lotes de 2 dias sem finalizar', 'dois dias pendentes')
ok(M.aviso_pendentes([], seg16) is None, 'sem lotes: sem faixa')
ok(M.rotulo_dia(sab14) == 'sáb 14/11', 'cartao do lote: "sáb 14/11"')
# FINALIZAR DIA: os digitados de dias anteriores viram turnos separados
fixos, livres, dl = M.separar_lotes(esq, seg16)
ok(fixos == {} and len(livres) == 2 and dl == sab14, 'so lotes de sabado: a data do popup ja vem 14/11')
zap = ['Bermuda', '40', 1, '12/11/2026', None]
fixos, livres, dl = M.separar_lotes(esq + [['Short', '50', 1, '', ts_seg], zap, ['Velho', '5', 1]], seg16)
ok(set(fixos) == {'14/11/2026', '12/11/2026'} and len(fixos['14/11/2026']) == 2 and dl == seg16
   and [r[0] for r in livres] == ['Short', 'Velho'],
   'sabado esquecido + segunda: sabado vira turno separado, os de hoje (e o sem hora) vao para a data do popup')
ok(M.separar_lotes([zap], seg16) == ({'12/11/2026': [zap]}, [], None), 'so colados do WhatsApp: sem data para perguntar')

# L2: a semana certa e a faixa por semana
ok(M.fim_da_semana(date(2026, 11, 10)) == sab14 and M.fim_da_semana(sab14) == sab14, 'o fim da semana e o sabado')
ok(M.fim_da_semana(date(2026, 11, 15)) == date(2026, 11, 21), 'domingo: o sabado da semana seguinte')
ok(M.fim_do_periodo('semanal', date(2026, 11, 9), seg16) == sab14, 'semanal fechado na segunda: so ate o sabado')
ok(M.fim_do_periodo('semanal', date(2026, 11, 9), date(2026, 11, 12)) == date(2026, 11, 12),
   'semanal fechado na quinta: ate hoje')
ok(M.fim_do_periodo('quinzenal', date(2026, 11, 2), seg16) == seg16, 'quinzenal: ate hoje')
ok(M.fim_do_periodo('semanal', seg16, sab14) == seg16, 'periodo que ainda vai comecar: nao volta no tempo')
dias = {date(2026, 11, 9) + timedelta(days=i): 400 for i in range(6)}          # 2.400 na semana
ok(M.ganho_por_semanas(dias, C) == 600.0, 'uma semana de 2.400 = R$ 600,00')
duas = dict(dias)
duas.update({date(2026, 11, 16) + timedelta(days=i): 400 for i in range(6)})
ok(M.ganho_por_semanas(duas, C) == 1200.0, 'duas semanas de 2.400 = R$ 1.200,00 (e nao 4.800 a 0,30 = 1.440)')
s = M.semanas(duas, C)
ok(len(s) == 2 and s[0]['seg'] == date(2026, 11, 9) and s[0]['sab'] == sab14 and s[1]['pecas'] == 2400,
   'semanas: seg e sab de cada uma')
ok(M.ganho_por_semanas([(date(2026, 11, 9), 2400), (seg16, 600)], C) == 750.0,
   '2.400 + 600 da segunda seguinte = 600 + 150 (a segunda nao sobe a faixa da semana anterior)')
ok(M.ganho_por_semanas([(date(2026, 11, 10), 1500), (date(2026, 11, 10), 1500)], C) == 900.0,
   'o mesmo dia repetido soma (3.000 = R$ 900,00)')
ok(M.ganho_por_semanas([(date(2026, 11, 15), 100), (seg16, 2400)], C) == 675.0,
   'domingo conta na semana seguinte (100 + 2.400 = 2.500 a 0,27)')
ok(M.ganho_por_semanas([(None, 5), (seg16, 'x'), (seg16, 10)], C) == 2.5, 'dia ou pecas estragados ficam de fora')
ok(M.ganho_por_semanas({}, C) == 0, 'periodo vazio = zero')
ok(M.ganho_por_semanas([(date(2026, 11, 10), 2950)], C) == 796.5, '2.950 na semana = R$ 796,50')
# T4: o periodo seguinte comeca no dia depois do fim
ok(M.inicio_do_proximo(sab14) == sab14, 'fechou no sabado: o seguinte comeca no proprio sabado (turno atrasado nao se perde)')
ok(M.inicio_do_proximo(sab14, {date(2026, 11, 15)}) == sab14, 'fechou no sabado com turno no domingo: comeca no sabado')
ok(M.inicio_do_proximo(date(2026, 11, 13)) == sab14, 'fechou na sexta: comeca no sabado')
ok(M.inicio_do_proximo(date(2026, 11, 13) + timedelta(days=-0)) == sab14, 'fim na sexta -> sabado')
# periodo semanal aberto num SABADO conta a semana seguinte inteira (antes zerava)
ok(M.fim_do_periodo('semanal', sab14, date(2026, 11, 18)) == date(2026, 11, 18), 'aberto no sabado, hoje quarta: conta ate hoje')
ok(M.fim_do_periodo('semanal', sab14, date(2026, 11, 23)) == date(2026, 11, 21), 'aberto no sabado: vai ate o sabado SEGUINTE')
ok(M.fim_do_periodo('semanal', sab14, sab14) == sab14, 'aberto e fechado no mesmo sabado')
ok(M.inicio_do_proximo(date(2026, 11, 12)) == date(2026, 11, 13), 'fechou na quinta: comeca na sexta')
# L8: as faixas tem de fechar antes de gravar
ok(M.config_coerente(0.25, 0.27, 0.30, 2500, 3000) is None, 'ajustes padrao fecham')
ok(M.config_coerente(0.28, 0.27, 0.30, 2500, 3000) is not None, 'base 0,28 com meio 0,27: recusado')
ok(M.config_coerente(0.25, 0.31, 0.30, 2500, 3000) is not None, 'meio acima do bonus: recusado')
ok(M.config_coerente(0.32, 0.31, 0.30, 2500, 3000) is not None, 'base acima do bonus: recusado')
ok(M.config_coerente(0.25, 0.27, 0.30, 3000, 3000) is not None, 'meta do meio igual a de cima: recusado')
ok(M.config_coerente(0.27, 0.27, 0.27, 2500, 3000) is None, 'tudo igual (sem bonus) e permitido')

print('%d casos, %d falhas' % (casos[0], len(falhas)))
sys.exit(1 if falhas else 0)
