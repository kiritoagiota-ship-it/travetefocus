"""Testa importar_zap.ler com textos como os que saem ao copiar varias
mensagens do WhatsApp (varios aparelhos, varios jeitos de escrever).
uso: python dev/teste_importar.py"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importar_zap as Z                                                # noqa: E402

HOJE = date(2026, 10, 10)
CASOS = []


def caso(nome, texto, esperado):
    CASOS.append((nome, texto, esperado))


caso('android: data, hora e nome antes de cada mensagem', '''[05/10/2026, 17:32] Kirito: Camisa polo 180
[05/10/2026, 17:33] Kirito: Calça jeans 95
[06/10/2026, 17:40] Kirito: Vestido longo 60
[06/10/2026, 17:41] Kirito: bermuda - 120 un''',
     [('05/10/2026', 'Camisa polo', 180), ('05/10/2026', 'Calça jeans', 95), ('06/10/2026', 'Vestido longo', 60),
      ('06/10/2026', 'Bermuda', 120)])

caso('iphone: hora antes da data', '''[17:32, 05/10/2026] Kirito: 180 camisa polo
[17:33, 05/10/2026] Kirito: 95 calça jeans''',
     [('05/10/2026', 'Camisa polo', 180), ('05/10/2026', 'Calça jeans', 95)])

caso('conversa exportada (traco) e mensagem de varias linhas', '''05/10/2026 17:32 - Kirito: Camisa polo 180
Calça jeans 95
Jaqueta corta-vento: 40
06/10/2026 18:01 - Kirito: vestido 60 pçs''',
     [('05/10/2026', 'Camisa polo', 180), ('05/10/2026', 'Calça jeans', 95),
      ('05/10/2026', 'Jaqueta corta-vento', 40), ('06/10/2026', 'Vestido', 60)])

caso('conversa no meio e total sao ignorados', '''[05/10/2026, 08:01] Chefe: bom dia, hoje tem que sair tudo
[05/10/2026, 17:32] Kirito: Camisa polo 180
[05/10/2026, 17:33] Kirito: total 180
[05/10/2026, 17:35] Chefe: ok obrigado
[05/10/2026, 17:36] Kirito: amanhã chego 7 horas''',
     [('05/10/2026', 'Camisa polo', 180)])

caso('a mensagem que o proprio app manda (PRODUCAO DO DIA)', '''[24/09/2026, 17:20] Kirito: \U0001F4CB *PRODUÇÃO DO DIA*
\U0001F4C5 24/09/2026 (quinta)

\U0001F9F5 Camisa polo — *180*
\U0001F9F5 Calça jeans — *1.250*

✅ *TOTAL: 1.430 peças*''',
     [('24/09/2026', 'Camisa polo', 180), ('24/09/2026', 'Calça jeans', 1250)])

caso('nome com numero dentro e varias pecas na mesma linha', '''[07/10/2026, 17:30] Kirito: camisa 2 bolsos - 150 un
[07/10/2026, 17:31] Kirito: 80 short, 45 regata e 30 calça''',
     [('07/10/2026', 'Camisa 2 bolsos', 150), ('07/10/2026', 'Short', 80), ('07/10/2026', 'Regata', 45),
      ('07/10/2026', 'Calça', 30)])

caso('nome numa linha e a quantidade na outra', '''[08/10/2026, 17:30] Kirito: Camisa polo
180
Calça jeans
95''',
     [('08/10/2026', 'Camisa polo', 180), ('08/10/2026', 'Calça jeans', 95)])

caso('sem cabecalho (uma mensagem so): vale o dia de hoje', '''Camisa polo 180
Calça jeans x95
60 vestido longo''',
     [('10/10/2026', 'Camisa polo', 180), ('10/10/2026', 'Calça jeans', 95), ('10/10/2026', 'Vestido longo', 60)])

caso('data escrita dentro da mensagem muda o dia', '''[09/10/2026, 20:00] Kirito: 05/10
camisa polo 180
06/10
calça jeans 95''',
     [('05/10/2026', 'Camisa polo', 180), ('06/10/2026', 'Calça jeans', 95)])

caso('ano com 2 digitos, AM/PM e marcas invisiveis', '''‎[5/10/26, 5:32 PM] Kirito: Camisa polo 180
‎[5/10/26, 5:33:10 PM] ~ Maria: Calça jeans 95''',
     [('05/10/2026', 'Camisa polo', 180), ('05/10/2026', 'Calça jeans', 95)])

caso('total/xp/turnos so como palavra inteira', '''Saia express 120
Bermuda expert 80
Body totalmente liso 70
Total do dia 300
+540 XP
Turnos: 3''',
     [('10/10/2026', 'Saia express', 120), ('10/10/2026', 'Bermuda expert', 80),
      ('10/10/2026', 'Body totalmente liso', 70)])

caso('50+30 soma no mesmo item', '''Calça 50+30
Short 20 + 10 + 5
40+60 regata''',
     [('10/10/2026', 'Calça', 80), ('10/10/2026', 'Short', 35), ('10/10/2026', 'Regata', 100)])

caso('numero seguido de palavra comeca item novo', '''Camisa polo 180 calça 95
180 bermuda 95 vestido
Camisa 180 pçs calça 95 short 40''',
     [('10/10/2026', 'Camisa polo', 180), ('10/10/2026', 'Calça', 95), ('10/10/2026', 'Bermuda', 180),
      ('10/10/2026', 'Vestido', 95), ('10/10/2026', 'Camisa', 180), ('10/10/2026', 'Calça', 95),
      ('10/10/2026', 'Short', 40)])

caso('nome com numero pequeno nao e dividido; mais + separando pecas', '''camisa 2 bolsos 150
regata 3 cores 200
camisa 50 + 30 calça
Camisa 100 + calça 50''',
     [('10/10/2026', 'Camisa 2 bolsos', 150), ('10/10/2026', 'Regata 3 cores', 200),
      ('10/10/2026', 'Camisa', 50), ('10/10/2026', 'Calça', 30), ('10/10/2026', 'Camisa', 100),
      ('10/10/2026', 'Calça', 50)])

caso('separa por " / " e hora no texto nao vira quantidade', '''camisa 100 / calça 50
Camisa 180 peças às 14:30
Saída às 17:30''',
     [('10/10/2026', 'Camisa', 100), ('10/10/2026', 'Calça', 50), ('10/10/2026', 'Camisa', 180)])

falhas = 0

# marcar_repetidos: o que ja foi lancado (lotes do Registro ou itens de um turno do mesmo dia)
registros = [['Camisa polo', '180', 540, '05/10/2026', 1.0],      # colado antes (com dia)
             ['Bermuda', '120', 360, ''],                       # digitado hoje (sem dia)
             ['Short', '40', 120]]                              # registro antigo (sem campo de dia)
memorias = [{'data': '06/10/2026  17:50', 'total': 155, 'xp': 0,
             'itens': [['Calça Jeans', '95', 0], ['Vestido', 60, 0]]},
            {'data': 'quebrada', 'itens': 'x'}]
colados = [{'dia': '05/10/2026', 'nome': 'camisa  polo', 'qtd': 180},   # repetido (espaco/minuscula)
           {'dia': '05/10/2026', 'nome': 'Camisa polo', 'qtd': 180},    # 2o igual: so 1 ja existia
           {'dia': '05/10/2026', 'nome': 'Camisa polo', 'qtd': 181},    # outra quantidade
           {'dia': '06/10/2026', 'nome': 'Calca jeans', 'qtd': 95},     # turno do dia, sem acento
           {'dia': '07/10/2026', 'nome': 'Vestido', 'qtd': 60},         # outro dia
           {'dia': '10/10/2026', 'nome': 'Bermuda', 'qtd': 120},        # lote de hoje sem dia
           {'dia': '10/10/2026', 'nome': 'short', 'qtd': 40}]           # registro sem o campo de dia
esperado = [True, False, False, True, False, True, True]
achado = Z.marcar_repetidos(colados, registros, memorias, hoje=HOJE)
ok = achado == esperado
falhas += 0 if ok else 1
print(('OK   ' if ok else 'FALHA') + ' marcar_repetidos: dia + nome sem acento + qtd (lotes e turnos)')
if not ok:
    print('   esperado:', esperado)
    print('   achado:  ', achado)
ok = Z.marcar_repetidos([], [], []) == [] and Z.marcar_repetidos(colados[:1], None, None) == [False]
falhas += 0 if ok else 1
print(('OK   ' if ok else 'FALHA') + ' marcar_repetidos: listas vazias/None')
# colar a mesma mensagem duas vezes: a 2a vez sai toda marcada
txt = CASOS[0][1]
primeira = Z.ler(txt, hoje=HOJE)['itens']
regs = [[i['nome'], str(i['qtd']), 0, i['dia'], i['ts']] for i in primeira]
ok = all(Z.marcar_repetidos(Z.ler(txt, hoje=HOJE)['itens'], regs, [], hoje=HOJE))
falhas += 0 if ok else 1
print(('OK   ' if ok else 'FALHA') + ' marcar_repetidos: a mesma mensagem colada 2 vezes sai toda marcada')

# tamanho e referencia NAO viram outra peca (o 40 de 'Calca 40 preta' e numeracao)
for texto, esperado in (('Calça 40 preta 200', ['Calça 40 preta 200']),
                        ('Short tam 42 bege 150', ['Short tam 42 bege 150']),
                        ('Blusa ref 123 azul 80', ['Blusa ref 123 azul 80']),
                        ('Bermuda nº 12 azul 90', ['Bermuda nº 12 azul 90']),
                        ('Camisa polo 180 calça 95', ['Camisa polo 180', 'calça 95'])):
    achado = Z._dividir_por_numero(texto)
    ok = achado == esperado
    falhas += 0 if ok else 1
    print(('OK   ' if ok else 'FALHA') + ' dividir: ' + texto)
    if not ok:
        print('   esperado:', esperado)
        print('   achado:  ', achado)

for nome, texto, esperado in CASOS:
    r = Z.ler(texto, hoje=HOJE)
    achado = [(i['dia'], i['nome'], i['qtd']) for i in r['itens']]
    ok = achado == esperado
    falhas += 0 if ok else 1
    print(('OK   ' if ok else 'FALHA') + ' ' + nome)
    if not ok:
        print('   esperado:', esperado)
        print('   achado:  ', achado)
print("%d casos (+3 de marcar_repetidos, +5 de tamanho), %d falhas" % (len(CASOS), falhas))
sys.exit(1 if falhas else 0)
