import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gif_yoru import Sim, salvar_gif, K
from PIL import Image, ImageDraw
P = K.POSE_A
_com = lambda p, **kw: dict(p, **kw)
g = P['guarda']
arma = _com(P['arma1'], olhos='s')
corta = _com(P['corta_desce'], olhos='g')
# preparacao: junta forca (abaixa, a ponta da lamina afunda) e ergue a
# lamina por cima do ombro
junta = _com(g, a1=-58.0, m1=(1.5, -3.5), dy=-0.5, pernas='recua', dx=-0.5, olhos='s')
ergue1 = _com(arma, a1=40.0, m1=(3, 3), dy=-0.5)
carga = _com(arma, a1=138.0, m1=(-1, 10), dy=-1)
treme = _com(carga, a1=141.0)
# o corte: 3 quadros com rastro seguindo o arco da mao
c1 = K.smear(_com(arma, a1=78.0, m1=(4, 9), pernas='avanco', dx=0.5, olhos='g', incl=1), 138.0)
c2 = K.smear(_com(corta, a1=10.0, m1=(8, 4), incl=1), 78.0)
c3 = K.smear(_com(corta, a1=-40.0, incl=1), 10.0)
passa = _com(corta, a1=-58.0, m1=(6, -4), dx=3, incl=1)
fica = _com(corta, olhos='s')
chaves = [(20, g, 'segura'), (4, junta, 'in'), (5, ergue1, 'suave'), (4, carga, 'out'), (2, treme, 'segura'),
          (1, carga, 'segura'),
          (1, c1, 'segura'), (1, c2, 'segura'), (1, c3, 'segura'), (2, passa, 'out'), (3, passa, 'segura'),
          (10, fica, 'mola'), (6, fica, 'segura'), (12, _com(g, olhos='a'), 'suave'), (20, g, 'segura'), (1, g)]
seq = K.sequencia(chaves)
i_imp = sum(c[0] for c in chaves[:8])
s = Sim(ps=9)
ev = {i_imp: lambda sm: sm.empurrar(capa=14, cabelo=10)}
poses = s.rodar(seq, eventos=ev)
caixa = (4 * 3, 12 * 3, 62 * 3, 66 * 3)
ims = salvar_gif(sys.argv[1], poses, esc=3, caixa=caixa)
W, H = ims[0].size
ini = 20
sel = list(range(ini, ini + 40))
col = 8
S = Image.new('RGB', (W * col, (H + 14) * ((len(sel) + col - 1) // col)), (10, 10, 18))
d = ImageDraw.Draw(S)
for k, i in enumerate(sel):
    x, y = (k % col) * W, (k // col) * (H + 14)
    S.paste(ims[i], (x, y + 14)); d.text((x + 3, y + 1), str(i - ini), fill='yellow')
S.save(sys.argv[2]); print(len(poses), S.size, 'impacto', i_imp - ini)
