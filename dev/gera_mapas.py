"""Gera tf_repo/yoru_mapas.py: cabeca (com as expressoes) e tronco do Yoru
na grade fina, a partir dos mapas limpos da referencia."""
import os
AQUI = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.join(AQUI, 'dados')
REPO = r'C:\Users\kirit\travetefocus\app'

cab = [list(l) for l in open(os.path.join(R1, 'cab_final.txt')).read().split('\n') if l]
tor = [l for l in open(os.path.join(R1, 'tronco_final.txt')).read().split('\n') if l]

# olho: bloco colunas 54-62, linhas 33-40 (canto de cima/esquerda em (54, 33)).
# '.' = pele (o mapa volta para a pele do rosto)
OLHO0, LIN0 = 54, 33
PELE_OLHO = [
    "SSSSSSSSS",
    "SSSSSSSSS",
    "SSSSSSSSS",
    "SSSSSSSSS",
    "SSSSSSSSS",
    "SSSSSSSSS",
    "SSSSSSSSS",
    "SSSSSSSSS",
]
OLHOS = {
    # normal: cilio grosso, brilho branco alto, iris do escuro (cima) ao claro (baixo)
    'a': ["NNtSSSsSS",
          "NNNNNNNNN",
          "SNnnEeEsS",
          "SinneeesS",
          "Sin3e33sS",
          "SSi3mm3SS",
          "SSSsmmsSS",
          "SSSSSSSSS"],
    # piscando: so a linha do cilio, curvada
    'f': ["NNtSSSsSS",
          "SSSSSSSSS",
          "SNSSSSSSS",
          "SSNNNNNsS",
          "SSSsssSSS",
          "SSSSSSSSS",
          "SSSSSSSSS",
          "SSSSSSSSS"],
    # olhando para baixo: palpebra desce, iris embaixo
    'b': ["NNtSSSsSS",
          "SSSSSSSSS",
          "SNNNNNNNS",
          "SNnneEEsS",
          "Sin3ee3sS",
          "SSi3mm3SS",
          "SSSsmmsSS",
          "SSSSSSSSS"],
    # serio: sobrancelha baixa e olho estreito
    's': ["NNNNNNtSS",
          "NNNNNNNNN",
          "SNnnEEEEN",
          "Sin3ee3sS",
          "SSi3mm3SS",
          "SSSssssSS",
          "SSSSSSSSS",
          "SSSSSSSSS"],
    # gritando no golpe: serio (a boca abre, ver BOCAS)
    'g': ["NNNNNNtSS",
          "NNNNNNNNN",
          "SNnnEEEEN",
          "Sin3ee3sS",
          "SSi3mm3SS",
          "SSSssssSS",
          "SSSSSSSSS",
          "SSSSSSSSS"],
    # olhos acesos (reiatsu)
    'l': ["NNNNNNtSS",
          "NNNNNNNNN",
          "SN!!999NS",
          "S9!9999sS",
          "SS99999SS",
          "SSS999SSS",
          "SSSSSSSSS",
          "SSSSSSSSS"],
    # susto: olho grande com branco em volta
    'u': ["NNNNNNNSS",
          "NiiiiiiNS",
          "iinnEeiiS",
          "iinneeiiS",
          "Si3eee3iS",
          "SSimmmiSS",
          "SSSiiiSSS",
          "SSSSSSSSS"],
    # feliz: olho fechado em arco (^)
    'e': ["NNtSSSsSS",
          "SSSSSSSSS",
          "SSSNNNSSS",
          "SSNSSSNSS",
          "SNSSSSSNS",
          "SSSSSSSSS",
          "SSSSSSSSS",
          "SSSSSSSSS"],
    # vitoria: meio fechado, confiante
    'v': ["NNtSSSsSS",
          "SSSSSSSSS",
          "SNNNNNNNS",
          "SNnnEEEsS",
          "SSi3mm3SS",
          "SSSsssSSS",
          "SSSSSSSSS",
          "SSSSSSSSS"],
}
# boca: colunas 55-61, linhas 42-45
BOCA0, BLIN0 = 55, 42
BOCAS = {
    'a': ["SSSSSSS", "SSSssSS", "SSSSSSS", "SSSSSSS"],
    'g': ["SSSNNNS", "SSNTTTN", "SSNTTTN", "SSSNNSS"],       # gritando
    'u': ["SSSSSSS", "SSSNNSS", "SSSNNSS", "SSSSSSS"],       # "o" de susto
    'e': ["SSSSSSS", "SSNSSSN", "SSSNNNS", "SSSSSSS"],       # sorriso
    'v': ["SSSSSSS", "SSSSSSN", "SSSNNNS", "SSSSSSS"],       # meio sorriso de lado
}
BOCA_DE = {'g': 'g', 'u': 'u', 'e': 'e', 'v': 'v'}


def expressao(k):
    m = [l[:] for l in cab]
    olho = OLHOS[k]
    for r, linha in enumerate(olho):
        for c, ch in enumerate(linha):
            y, x = LIN0 + r, OLHO0 + c
            if m[y][x] in 'SstTEeNn3mi9!Uh' or r >= 1:
                if m[y][x] not in 'JHI' or r >= 1:
                    m[y][x] = ch
    boca = BOCAS[BOCA_DE.get(k, 'a')]
    for r, linha in enumerate(boca):
        for c, ch in enumerate(linha):
            y, x = BLIN0 + r, BOCA0 + c
            if m[y][x] in 'Sst':
                m[y][x] = ch
    return [''.join(l) for l in m]


def lista(nome, linhas):
    out = [nome + ' = [']
    for l in linhas:
        out.append('    "%s",' % l)
    out.append(']')
    return '\n'.join(out)


if __name__ == '__main__':
    partes = ['"""Mapas do Yoru na grade fina (5 texels por unidade), tirados da',
              'referencia oficial e limpos a mao. Gerado por gera_mapas.py."""',
              '']
    nomes = []
    for k in OLHOS:
        nome = '_CAB5_' + k
        partes.append(lista(nome, expressao(k)))
        partes.append('')
        nomes.append((k, nome))
    partes.append('CABECAS = {' + ', '.join("'%s': %s" % (k, n) for k, n in nomes) + '}')
    partes.append('')
    partes.append(lista('TRONCO', tor))
    partes.append('')
    open(os.path.join(REPO, 'yoru_mapas.py'), 'w', encoding='utf-8', newline='\r\n').write('\n'.join(partes) + '\n')
    print('ok', len(cab[0]), len(cab), len(tor[0]), len(tor))
