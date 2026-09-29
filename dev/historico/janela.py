"""janela.py PASTA T0 T1 SAIDA [cols] [escala] [recorte] : quadros entre T0 e T1 (s)"""
import sys, os, json, subprocess
pasta, t0, t1, saida = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
resto = sys.argv[5:]
L = json.load(open(os.path.join(pasta, 'log.json'), encoding='utf-8'))
sel = [q for q in L['quadros'] if t0 <= q[0] <= t1]
json.dump({'quadros': sel}, open(os.path.join(pasta, 'log_janela.json'), 'w', encoding='utf-8'))
env = dict(os.environ, LOG='log_janela.json')
subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'folha.py'), pasta, '', saida] + resto, env=env)
