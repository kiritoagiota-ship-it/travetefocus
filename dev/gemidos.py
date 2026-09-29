"""Gemidinhos dos golpes (kiai curtos) -> app/sons/gemido_*.wav"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import audio as A
import voz_jp as V            # usa a mesma cadeia da voz do Yoru
ORIG = r'C:\Users\kirit\travetefocus\ferramentas\voz\saida'
SONS = r'C:\Users\kirit\travetefocus\app\sons'
escolhas = {
    'gemido_ha': ('gem_ha.wav', 0.98, 1.35),
    'gemido_hun': ('gem_hun.wav', 0.96, 1.25),
    'gemido_ya': ('gem_ya.wav', 0.98, 1.35),
    'gemido_yaa': ('gem_yaa.wav', 0.97, 1.3),
    'gemido_to': ('gem_to.wav', 0.97, 1.3),
    'gemido_fun': ('gem_hmph.wav', 0.95, 1.2),
}
for nome, (arq, fator, sat) in escolhas.items():
    a = V.voz(A.ler_arquivo(os.path.join(ORIG, arq)), fator=fator, sat=sat, ganho=2.0,
              eco=(0.12, 0.05, 0.0), dobra=0.25)
    a = A.ganho(a, 0.8)                      # um pouco abaixo das falas grandes
    A.escrever(os.path.join(SONS, nome + '.wav'), a)
    print(nome, round(A.dur(a), 2), 's')
