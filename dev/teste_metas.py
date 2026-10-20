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

print('%d casos, %d falhas' % (casos[0], len(falhas)))
