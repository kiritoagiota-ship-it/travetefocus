pc = r'C:\Users\kirit\travetefocus\app\cenas.py'
c = open(pc, encoding='utf-8').read()


def troca(a, b):
    global c
    assert c.count(a) == 1, a[:80]
    c = c.replace(a, b)


troca('''  cena_titulo(tela, label, on_fim)  Kirito pendurado por uma mao num canto de
                                    cima, solta, saca num iai e escreve
                                    "TRAVETE FOCUS" em cima das letras. No
                                    golpe final (estilo Bleach) junta as duas
                                    espadas numa so, a espada suga o infinito
                                    da tela como reiatsu, evolui e solta uma
                                    onda de energia que completa a frase.
                                    Sempre inteiro no quadro; sai num teleporte.''',
      '''  cena_titulo(tela, label, on_fim)  o Yoru escreve "TRAVETE FOCUS" a golpes:
                                    cada silaba aparece por onde a luz de um
                                    corte passa (cada corte numa direcao). Vira
                                    Mugetsu, o corte final grava o CUS, guarda
                                    as duas espadas e fica em pose na frase.''')
troca('''    """Kirito pendurado por uma mao num canto de cima, a outra no cabo da
    Elucidator: kamae, solta, iai na cintura; saca a Dark Repulser e segue o
    combo em cima das letras. No golpe final junta as duas espadas, suga o
    infinito da tela para a lamina, que evolui, e solta uma onda de energia
    que completa a frase. Pousa na frase, separa as espadas, embainha
    devagar - e so no clique da guarda a frase explode. Sai num teleporte,
    sem nunca deixar o quadro."""''',
      '''    """O Yoru entra num mortal e escreve a frase a golpes: a luz de cada
    corte atravessa uma silaba e as letras aparecem por onde ela passa (TRA
    na horizontal, VE subindo, TE descendo com as duas espadas, FO em X). No
    golpe final junta as duas espadas, suga o infinito da tela, vira o
    Mugetsu e um corte so grava o CUS. Separa as espadas, pousa na frase,
    guarda a azul nas costas e a katana na cintura - no clique da guarda a
    frase explode - e fica em pose (sem sair de cena)."""''')
open(pc, 'w', encoding='utf-8', newline='\n').write(c)
print('ok')
