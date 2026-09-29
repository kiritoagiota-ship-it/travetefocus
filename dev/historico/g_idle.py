import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gif_yoru import Sim, salvar_gif, K
from PIL import Image
# idle (como o widget faz) + uma corrida curta para ver o vento
b = dict(K.POSE_A['guarda'])
idle = []
for f in range(90):
    t = f / 90.0 * 2 * math.pi
    q = dict(b); q['dy'] = b['dy'] - (1 if math.sin(t) < -0.35 else 0)
    if b['a1'] is not None: q['a1'] = b['a1'] + round(2.0 * math.sin(2 * t + 0.8))
    idle.append(q)
s = Sim(ps=9)
# 0-40 parado, 40-70 corre para a frente, 70-120 freia e para
seq = idle + idle[:60]
def cam(i):
    if i < 40: return (0, 0)
    if i < 70: return ((i - 40) ** 2 * 1.2, 0)
    return (30 ** 2 * 1.2, 0)
poses = s.rodar(seq, caminho=cam)
caixa = (10 * 3, 12 * 3, 50 * 3, 48 * 3)
ims = salvar_gif(sys.argv[1], poses, esc=4, caixa=caixa)
# folha com alguns quadros
sel = [0, 45, 60, 72, 80, 95, 110, 130]
W, H = ims[0].size
S = Image.new('RGB', (W * 4, H * 2))
for k, i in enumerate(sel):
    S.paste(ims[i], ((k % 4) * W, (k // 4) * H))
S.save(sys.argv[2]); print(len(poses), S.size)
