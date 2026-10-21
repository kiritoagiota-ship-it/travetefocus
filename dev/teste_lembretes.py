"""Testa as contas dos avisos na barra do celular (lembretes.planejar).
uso: python dev/teste_lembretes.py   -> "N casos, 0 falhas" """
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import lembretes  # noqa: E402

CFG = {'valor_base': 0.25, 'valor_meio': 0.27, 'valor_bonus': 0.30, 'meta_meio': 2500,
       'meta_bonus': 3000, 'pecas_sabado': 200, 'tipo_periodo': 'semanal'}
falhas = []
casos = [0]


def caso(nome, cond, extra=''):
    casos[0] += 1
    if not cond:
        falhas.append(f'{nome} {extra}')
        print('FALHOU:', nome, extra)


def turno(data, total):
    return {'data': f'{data}  17:00', 'total': total, 'xp': total * 3}


def plano(agora, memorias=(), registros=()):
    return {p['tipo']: p for p in lembretes.planejar(agora, list(memorias), list(registros), CFG)}


# 20/10/2026 e terca-feira (segunda = 19/10, sabado = 24/10, domingo = 25/10)
seg, ter, sab, dom = '19/10/2026', '20/10/2026', '24/10/2026', '25/10/2026'

# 1) terca 9h, nada lancado: lembrete hoje 11h; meta hoje 16h
p = plano(datetime(2026, 10, 20, 9, 0))
caso('lancar hoje 11h', p['lancar']['quando'] == datetime(2026, 10, 20, 11, 0), p['lancar']['quando'])
caso('meta hoje 16h', 'meta' in p and p['meta']['quando'] == datetime(2026, 10, 20, 16, 0))

# 2) terca 9h, ja lancou hoje: lembrete so amanha
p = plano(datetime(2026, 10, 20, 9, 0), registros=[['Camisa', '50', 150, '', datetime(2026, 10, 20, 8, 30).timestamp()]])
caso('ja lancou: lembrete amanha', p['lancar']['quando'] == datetime(2026, 10, 21, 11, 0), p['lancar']['quando'])
caso('ja lancou: meta conta o que saiu', 'meta' in p and 'Já saíram 50' in p['meta']['texto'], p.get('meta'))

# 3) terca 12h sem lote: passou da hora -> amanha
p = plano(datetime(2026, 10, 20, 12, 0))
caso('passou da hora: amanha', p['lancar']['quando'] == datetime(2026, 10, 21, 11, 0))

# 4) sabado 15h: o proximo lembrete e segunda (domingo e folga)
p = plano(datetime(2026, 10, 24, 15, 0))
caso('sabado tarde: lembrete na segunda', p['lancar']['quando'] == datetime(2026, 10, 26, 11, 0), p['lancar']['quando'])
caso('sabado tarde: sem resumo (ja passou)', 'resumo' not in p)
caso('sabado: sem aviso de meta do dia', 'meta' not in p)

# 5) domingo: lembrete na segunda; sem meta/faixa/resumo
p = plano(datetime(2026, 10, 25, 10, 0))
caso('domingo: lembrete segunda', p['lancar']['quando'] == datetime(2026, 10, 26, 11, 0))
caso('domingo: nada mais', set(p) == {'lancar'}, set(p))

# 6) meta do dia batida: sem aviso da meta
mems = [turno(seg, 600)]
regs = [['Calca', '600', 1800, '', datetime(2026, 10, 20, 10, 0).timestamp()]]
p = plano(datetime(2026, 10, 20, 13, 0), mems, regs)
caso('meta batida: sem aviso', 'meta' not in p, p.get('meta'))

# 7) faixa ao alcance no sabado: 2.380 na semana (faltam 120 para 2.500)
mems = [turno('19/10/2026', 480), turno('20/10/2026', 480), turno('21/10/2026', 480),
        turno('22/10/2026', 470), turno('23/10/2026', 470)]
p = plano(datetime(2026, 10, 23, 20, 0), mems)
caso('faixa no sabado 8h', 'faixa' in p and p['faixa']['quando'] == datetime(2026, 10, 24, 8, 0), p.get('faixa'))
caso('faixa: texto com 120 e R$ 0,27', 'faixa' in p and '120' in p['faixa']['texto'] and '0,27' in p['faixa']['texto'],
     p.get('faixa', {}).get('texto'))
caso('resumo sabado 14h', 'resumo' in p and p['resumo']['quando'] == datetime(2026, 10, 24, 14, 0))
caso('resumo com pecas e R$', 'resumo' in p and '2.380' in p['resumo']['texto'] and 'R$ 595,00' in p['resumo']['texto'],
     p.get('resumo', {}).get('texto'))

# 8) faixa longe demais (faltam 1.000): sem aviso de faixa
mems = [turno('19/10/2026', 500), turno('20/10/2026', 500)]
p = plano(datetime(2026, 10, 21, 9, 0), mems)
caso('faixa longe: sem aviso', 'faixa' not in p, p.get('faixa'))

# 9) ja na faixa maxima: sem aviso de faixa, resumo com R$ 0,30
mems = [turno('19/10/2026', 1600), turno('20/10/2026', 1500)]
p = plano(datetime(2026, 10, 21, 9, 0), mems)
caso('faixa maxima: sem faixa', 'faixa' not in p)
caso('faixa maxima: resumo a 0,30', 'resumo' in p and '0,30' in p['resumo']['texto'], p.get('resumo', {}).get('texto'))

# 10) semana vazia: sem resumo
p = plano(datetime(2026, 10, 19, 9, 0))
caso('semana vazia: sem resumo', 'resumo' not in p)

# 11) ids fixos e sempre os mesmos
todos = lembretes.planejar(datetime(2026, 10, 23, 7, 0), [turno('19/10/2026', 2300)], [], CFG)
caso('ids conhecidos', all(x['id'] in lembretes.IDS.values() for x in todos))

print(f'{casos[0]} casos, {len(falhas)} falhas')
sys.exit(1 if falhas else 0)
