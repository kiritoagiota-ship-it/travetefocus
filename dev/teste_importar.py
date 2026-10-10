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

falhas = 0
for nome, texto, esperado in CASOS:
    r = Z.ler(texto, hoje=HOJE)
    achado = [(i['dia'], i['nome'], i['qtd']) for i in r['itens']]
    ok = achado == esperado
    falhas += 0 if ok else 1
    print(('OK   ' if ok else 'FALHA') + ' ' + nome)
    if not ok:
        print('   esperado:', esperado)
        print('   achado:  ', achado)
print('%d casos, %d falhas' % (len(CASOS), falhas))
sys.exit(1 if falhas else 0)
