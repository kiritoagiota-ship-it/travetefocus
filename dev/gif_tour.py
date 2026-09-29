"""GIF a partir dos quadros de um tour: gif_tour.py PASTA ini fim SAIDA x0,y0,x1,y1 escala
(duracao de cada quadro = tempo real entre as fotos)."""
import sys, os, json
from PIL import Image
pasta, a, b, saida = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
rec = [int(v) for v in sys.argv[5].split(',')]
esc = float(sys.argv[6])
L = json.load(open(os.path.join(pasta, 'log.json'), encoding='utf-8'))
tempo = {q[2]: q[0] for q in L['quadros']}
ims, durs = [], []
nomes = ['q%04d.png' % i for i in range(a, b + 1) if os.path.exists(os.path.join(pasta, 'q%04d.png' % i))]
for k, n in enumerate(nomes):
    im = Image.open(os.path.join(pasta, n)).convert('RGB').crop(rec)
    im = im.resize((int(im.width * esc), int(im.height * esc)), Image.LANCZOS)
    ims.append(im.quantize(colors=96, method=Image.Quantize.MEDIANCUT))
    if k + 1 < len(nomes):
        d = (tempo[nomes[k + 1]] - tempo[n]) * 1000
        durs.append(max(20, int(round(d / 10.0)) * 10) if d > 0 else 50)
    else:
        durs.append(1500)
ims[0].save(saida, save_all=True, append_images=ims[1:], duration=durs, loop=0, optimize=True)
print(saida, len(ims), os.path.getsize(saida) // 1024, 'KB')
