"""Le o filme.json do filme.py e mostra, trecho a trecho, se o Yoru esta
sendo ANIMADO (desenho novo) ou so MOVIDO pelo programa (deslizou, girou ou
esticou com o mesmo desenho).
uso: python dev/analisa_filme.py PASTA [trecho_em_quadros=15]"""
import sys
import os
import json
import math

pasta = sys.argv[1]
TR = int(sys.argv[2]) if len(sys.argv) > 2 else 15
L = json.load(open(os.path.join(pasta, 'filme.json'), encoding='utf-8'))
Q = L['quadros']
sons = {}
for q, s in L['sons']:
    sons.setdefault(q, []).append(s)
ini = min((q for q, _ in L['fases'] if _ == 'cena comecou'), default=0)

ant = {}
linhas = []
tot = {'quadros': 0, 'desenho': 0, 'desliza': 0, 'gira': 0, 'estica': 0, 'parado': 0, 'pausa': 0,
       'cauda': 0, 'corpo': 0, 'cabeca': 0}
bloco = None


def novo_bloco(q0):
    return {'q0': q0, 'n': 0, 'des': 0, 'unicos': set(), 'desl': 0, 'gira': 0, 'estica': 0,
            'passo_max': 0.0, 'rot_max': 0.0, 'yorus': set(), 'mug': False, 'sons': [],
            'segura_max': 0, 'pausa': 0}


seguido = {}
for rel, regs in Q:
    if bloco is None or rel - bloco['q0'] >= TR:
        if bloco is not None:
            linhas.append(bloco)
        bloco = novo_bloco(rel)
    bloco['n'] += 1
    bloco['sons'] += sons.get(rel + ini, [])
    vis = [r for r in regs if r['op'] > 0.05]
    for r in vis:
        bloco['yorus'].add(r['i'])
        bloco['mug'] |= r['mug']
        a = ant.get(r['i'])
        tot['quadros'] += 1
        if r['pausa'] > 0:
            bloco['pausa'] += 1
            tot['pausa'] += 1
        if a is None:
            ant[r['i']] = r
            seguido[r['i']] = 0
            continue
        passo = math.hypot(r['x'] - a['x'], r['y'] - a['y']) / r['ps'] * 3   # em texels do boneco
        for nome, v0, v1 in zip(('cauda', 'corpo', 'cabeca'), a.get('cam', []), r.get('cam', [])):
            if v0 != v1:
                tot[nome] += 1
                bloco[nome] = bloco.get(nome, 0) + 1
        mudou = r['des'] != a['des']
        girou = abs(r['rot'] - a['rot']) > 0.5
        esticou = abs(r['ex'] - a['ex']) > 0.01 or abs(r['ey'] - a['ey']) > 0.01
        if mudou:
            bloco['des'] += 1
            tot['desenho'] += 1
            seguido[r['i']] = 0
        else:
            seguido[r['i']] += 1
            bloco['segura_max'] = max(bloco['segura_max'], seguido[r['i']])
        bloco['unicos'].add(r['des'])
        if passo > 1.0 and not mudou:
            bloco['desl'] += 1
            tot['desliza'] += 1
        if girou:
            bloco['gira'] += 1
            tot['gira'] += 1
        if esticou:
            bloco['estica'] += 1
            tot['estica'] += 1
        if not mudou and passo <= 1.0 and not girou and not esticou:
            tot['parado'] += 1
        bloco['passo_max'] = max(bloco['passo_max'], passo)
        bloco['rot_max'] = max(bloco['rot_max'], abs(r['rot']))
        ant[r['i']] = r
if bloco is not None:
    linhas.append(bloco)

print(f"{'tempo':>6} {'yorus':>5} {'desenhos novos':>14} {'unicos':>6} {'segura':>6} "
      f"{'desliza':>7} {'gira':>4} {'estica':>6} {'passo max':>9}  sons")
for b in linhas:
    t = b['q0'] / 60.0
    print(f"{t:6.2f} {len(b['yorus']):5d} {b['des']:6d}/{b['n']:<7d} {len(b['unicos']):6d} "
          f"{b['segura_max']:6d} {b['desl']:7d} {b['gira']:4d} {b['estica']:6d} {b['passo_max']:9.1f}"
          f" c{b.get('corpo', 0):2d} p{b.get('cauda', 0):2d} h{b.get('cabeca', 0):2d}"
          f"{' M' if b['mug'] else '  '} {' '.join(b['sons'])}")
n = max(1, tot['quadros'])
print(f"\nTOTAL: {tot['quadros']} quadros-yoru | desenho novo {100 * tot['desenho'] / n:.0f}% | "
      f"deslizando com o mesmo desenho {100 * tot['desliza'] / n:.0f}% | girando o sprite "
      f"{100 * tot['gira'] / n:.0f}% | esticando {100 * tot['estica'] / n:.0f}% | parado {100 * tot['parado'] / n:.0f}% "
      f"| hit-stop {100 * tot['pausa'] / n:.0f}%")
seg = n / 60.0
print(f"desenhos por segundo: imagem inteira {tot['desenho'] / seg:.1f} | corpo {tot['corpo'] / seg:.1f} | "
      f"sobretudo {tot['cauda'] / seg:.1f} | cabeca {tot['cabeca'] / seg:.1f}")
