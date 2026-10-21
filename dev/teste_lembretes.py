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

# 1) terca 6h, nada lancado: lembrete hoje 7h; meta hoje 16h
p = plano(datetime(2026, 10, 20, 6, 0))
caso('lancar hoje 7h', p['lancar']['quando'] == datetime(2026, 10, 20, 7, 0), p['lancar']['quando'])
caso('meta hoje 16h', 'meta' in p and p['meta']['quando'] == datetime(2026, 10, 20, 16, 0))

# 2) terca 9h, ja lancou hoje: lembrete so amanha
p = plano(datetime(2026, 10, 20, 9, 0), registros=[['Camisa', '50', 150, '', datetime(2026, 10, 20, 8, 30).timestamp()]])
caso('ja lancou: lembrete amanha', p['lancar']['quando'] == datetime(2026, 10, 21, 7, 0), p['lancar']['quando'])
caso('ja lancou: meta conta o que saiu', 'meta' in p and 'Já saíram 50' in p['meta']['texto'], p.get('meta'))

# 3) terca 12h sem lote: passou da hora (7h) -> amanha
p = plano(datetime(2026, 10, 20, 12, 0))
caso('passou da hora: amanha', p['lancar']['quando'] == datetime(2026, 10, 21, 7, 0))

# 4) sabado 15h: o proximo lembrete e segunda (domingo e folga)
p = plano(datetime(2026, 10, 24, 15, 0))
caso('sabado tarde: lembrete na segunda', p['lancar']['quando'] == datetime(2026, 10, 26, 7, 0), p['lancar']['quando'])
caso('sabado tarde: sem resumo (ja passou)', 'resumo' not in p)
caso('sabado: sem aviso de meta do dia', 'meta' not in p)

# 5) domingo: lembrete na segunda; sem meta/faixa/resumo
p = plano(datetime(2026, 10, 25, 10, 0))
caso('domingo: lembrete segunda', p['lancar']['quando'] == datetime(2026, 10, 26, 7, 0))
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

# 12) sequencia: o dia so conta com o turno finalizado
# turnos qua 14 a seg 19 (o domingo 18 e folga): 5 dias seguidos ate ontem
SEQ5 = [turno(f'{d}/10/2026', 300) for d in (14, 15, 16, 17, 19)]
LOTE_HOJE = [['Camisa', '50', 150, '', datetime(2026, 10, 20, 8, 30).timestamp()]]
p = plano(datetime(2026, 10, 20, 9, 0), SEQ5)
caso('risco 17h', 'risco' in p and p['risco']['quando'] == datetime(2026, 10, 20, 17, 0), p.get('risco'))
caso('risco: texto com os dias', 'risco' in p and '5 dias' in p['risco']['titulo'], p.get('risco', {}).get('titulo'))
caso('risco: Yoru assustado', p.get('risco', {}).get('pose') == 'susto')
caso('risco: recorde (6 > 5)', 'risco' in p and 'bate o recorde: 6 dias' in p['risco']['texto']
     and p['risco']['semana'] == 'Recorde: 5 dias', p.get('risco'))
caso('risco: barra 5 de 6', p.get('risco', {}).get('prog') == 5 and p['risco']['prog_max'] == 6, p.get('risco'))
# lancou mas nao finalizou: o aviso vira "finaliza o turno"
p = plano(datetime(2026, 10, 20, 9, 0), SEQ5, LOTE_HOJE)
caso('lancou: finaliza o turno', 'seq_fim' in p and 'risco' not in p and '6 dias' in p['seq_fim']['titulo'], p.keys())
caso('lancou: texto com as pecas', 'seq_fim' in p and '50 peças' in p['seq_fim']['texto'], p.get('seq_fim', {}).get('texto'))
caso('lancou: mesmo id', p.get('seq_fim', {}).get('id') == lembretes.IDS['sequencia'])
# turno de hoje ja finalizado: nada
caso('finalizado: sem aviso', not ({'risco', 'seq_fim'} & set(plano(datetime(2026, 10, 20, 9, 0), SEQ5 + [turno(ter, 400)]))))
caso('sequencia curta nao avisa', not ({'risco', 'seq_fim'} & set(plano(datetime(2026, 10, 20, 9, 0), [turno(seg, 300)]))))
caso('sequencia quebrada nao avisa', not ({'risco', 'seq_fim'} & set(plano(datetime(2026, 10, 20, 9, 0),
                                                                     [turno(f'{d}/10/2026', 300) for d in (14, 15, 16)]))))
caso('passou das 17h nao avisa', 'risco' not in plano(datetime(2026, 10, 20, 17, 30), SEQ5))
caso('domingo nao avisa', 'risco' not in plano(datetime(2026, 10, 25, 9, 0), SEQ5 + [turno(f'{d}/10/2026', 300) for d in (20, 21, 22, 23, 24)]))
p = plano(datetime(2026, 10, 24, 9, 0), SEQ5 + [turno(f'{d}/10/2026', 300) for d in (20, 21, 22, 23)])
caso('sabado 11h30', 'risco' in p and p['risco']['quando'] == datetime(2026, 10, 24, 11, 30), p.get('risco'))
# recorde antigo maior: nao fala em recorde
velho = [turno(f'{d:02d}/09/2026', 300) for d in (1, 2, 3, 4, 5, 7, 8, 9, 10)]
p = plano(datetime(2026, 10, 20, 9, 0), velho + SEQ5)
caso('recorde antigo: sem "recorde" no texto', 'risco' in p and 'recorde' not in p['risco']['texto']
     and p['risco']['semana'] == 'Recorde: 9 dias', p.get('risco'))
caso('melhor sequencia pula o domingo', lembretes._melhor_seq(lembretes._dias_com_turno(velho)) == 9)

# 13) fechamento do dia: terca 13h com 600 hoje -> 20h; sabado -> 13h
mems = [turno(seg, 600)]
regs = [['Calca', '600', 1800, '', datetime(2026, 10, 20, 10, 0).timestamp()]]
p = plano(datetime(2026, 10, 20, 13, 0), mems, regs)
caso('fechamento 20h', 'fechamento' in p and p['fechamento']['quando'] == datetime(2026, 10, 20, 20, 0), p.get('fechamento'))
caso('fechamento: pecas e XP de hoje', 'fechamento' in p and '600 peças' in p['fechamento']['texto']
     and '+1.800 XP' in p['fechamento']['texto'], p.get('fechamento', {}).get('texto'))
caso('fechamento: barra da semana ate a faixa', p.get('fechamento', {}).get('prog') == 1200
     and p['fechamento']['prog_max'] == 2500, p.get('fechamento'))
caso('fechamento: lote pendente lembra de finalizar', 'FINALIZAR DIA' in p['fechamento']['texto'])
p2 = plano(datetime(2026, 10, 20, 13, 0), mems + [turno(ter, 500)])
caso('fechamento: turno salvo', 'fechamento' in p2 and 'Dia finalizado' in p2['fechamento']['texto'],
     p2.get('fechamento', {}).get('texto'))
caso('fechamento: sem lote nao avisa', 'fechamento' not in plano(datetime(2026, 10, 20, 13, 0), mems))
regs_sab = [['Calca', '150', 450, '', datetime(2026, 10, 24, 8, 0).timestamp()]]
p = plano(datetime(2026, 10, 24, 9, 0), mems, regs_sab)
caso('fechamento sabado 13h', 'fechamento' in p and p['fechamento']['quando'] == datetime(2026, 10, 24, 13, 0))

# 14) o card: todo aviso tem pose, fala e numeros coerentes
todos = lembretes.planejar(datetime(2026, 10, 20, 6, 0), SEQ5, [], CFG)
caso('todos com o card', all(x.get('pose') in ('guarda', 'meta', 'vitoria', 'susto') and x.get('fala')
                             and 0 <= x['prog'] and x['prog_max'] >= 0 for x in todos), todos)
caso('fala igual o dia todo', lembretes._fala('meta', datetime(2026, 10, 20).date())
     == lembretes._fala('meta', datetime(2026, 10, 20).date()))
p = plano(datetime(2026, 10, 20, 9, 0), [turno(seg, 300)], [['Camisa', '50', 150, '', datetime(2026, 10, 20, 8, 30).timestamp()]])
caso('meta: barra hoje/meta', p['meta']['prog'] == 50 and p['meta']['prog_max'] > 50, p.get('meta'))

# 15) faixa nova (na hora): passar de 2.500 avisa; continuar na mesma faixa nao
f = lembretes.aviso_faixa_nova(2450, 2530, CFG)
caso('faixa nova: aviso', f is not None and '0,27' in f['titulo'] and f['id'] == lembretes.ID_FAIXA_NOVA, f)
caso('faixa nova: barra ate a proxima', f is not None and f['prog_max'] == 3000 and f['prog'] == 2530, f)
caso('faixa nova: mesma faixa nao avisa', lembretes.aviso_faixa_nova(2510, 2600, CFG) is None)
f = lembretes.aviso_faixa_nova(2990, 3010, CFG)
caso('faixa nova: a maxima', f is not None and '0,30' in f['titulo'] and f['rotulo'] == 'Faixa máxima!', f)

print(f'{casos[0]} casos, {len(falhas)} falhas')
sys.exit(1 if falhas else 0)
