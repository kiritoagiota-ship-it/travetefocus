"""Previa da etapa 1: GIFs antes x depois (parado e golpe) e folha do visual.
uso: python previa1.py PASTA_SAIDA"""
import sys, os, math
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, '..', 'velho'))
from gif_yoru import Sim, imagem, K, BG
import kirito_velho as KV
from PIL import Image, ImageDraw, ImageFont
FONTE = ImageFont.truetype('arialbd.ttf', 22)

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
ESC = 4
_com = lambda p, **kw: dict(p, **kw)


def lado_a_lado(quad_a, quad_b, caixa, nome, rot=('ANTES', 'DEPOIS')):
    n = max(len(quad_a), len(quad_b))
    quad_a = quad_a + [quad_a[-1]] * (n - len(quad_a))
    quad_b = quad_b + [quad_b[-1]] * (n - len(quad_b))
    ims = []
    for pa, pb in zip(quad_a, quad_b):
        a = imagem(pa, ESC, caixa, M=KV)
        b = imagem(pb, ESC, caixa, M=K)
        W, H = a.size
        S = Image.new('RGB', (W * 2 + 8, H + 30), BG)
        S.paste(a, (0, 30))
        S.paste(b, (W + 8, 30))
        d = ImageDraw.Draw(S)
        d.rectangle([W, 0, W + 7, H + 30], fill=(40, 40, 60))
        d.text((12, 3), rot[0], fill=(160, 160, 180), font=FONTE)
        d.text((W + 20, 3), rot[1], fill=(120, 230, 255), font=FONTE)
        ims.append(S.convert('P', palette=Image.ADAPTIVE, colors=128))
    dur = [30 if i % 3 else 40 for i in range(len(ims))]     # ~30 quadros por segundo
    ims[0].save(os.path.join(OUT, nome), save_all=True, append_images=ims[1:], duration=dur, loop=0,
                disposal=2, optimize=False)
    return ims


def parado(M):
    """Parado e respirando; da um passinho para a frente e para (o pano
    continua mexendo depois que ele para)."""
    b = dict(M.POSE_A['guarda'])
    quadros = []
    for f in range(150):
        t = f / 90.0 * 2 * math.pi
        q = dict(b)
        if M is K:                                # respiracao nova: texel a texel
            q['dy'] = b['dy'] - round(1.0 - math.cos(t)) / 3.0
            q['m1'] = (b['m1'][0], b['m1'][1] - round(1.0 - math.cos(t - 0.6)) / 3.0)
        else:
            q['dy'] = b['dy'] - (1 if math.sin(t) < -0.35 else 0)
            atras = math.sin(t - 0.6)
            q['m1'] = (b['m1'][0], b['m1'][1] - (1 if atras < -0.35 else 0))
        q['a1'] = b['a1'] + round(2.0 * math.sin(2 * t + 0.8))
        if 70 <= f <= 72 or 128 <= f <= 129 or 133 <= f <= 134:
            q['olhos'] = 'f'
        quadros.append(q)

    def cam(i):                                   # passinho entre 40 e 58
        if i < 40:
            return (0.0, 0.0)
        u = min(1.0, (i - 40) / 18.0)
        return (u * u * (3 - 2 * u) * 120.0, 0.0)
    s = Sim(ps=9, M=M)
    return s.rodar(quadros, caminho=cam)


def golpe_velho():
    P = KV.POSE_A
    chaves, i_r = KV.golpe(P['arma1'], P['corta_desce'])
    g = P['guarda']
    chaves = [(20, g, 'segura'), (5, g, 'suave')] + chaves[:-1] + [(8, chaves[-1][1], 'segura'),
                                                                   (12, g, 'suave'), (20, g, 'segura'), (1, g)]
    seq = KV.sequencia(chaves)
    s = Sim(ps=9, M=KV)
    return s.rodar(seq, eventos={i_r + 25: lambda sm: sm.empurrar(capa=14, cabelo=10)})


def golpe_novo():
    P = K.POSE_A
    g = P['guarda']
    arma = _com(P['arma1'], olhos='s')
    corta = _com(P['corta_desce'], olhos='g')
    junta = _com(g, a1=-58.0, m1=(1.5, -3.5), dy=-0.5, pernas='recua', dx=-0.5, olhos='s')
    ergue1 = _com(arma, a1=40.0, m1=(3, 3), dy=-0.5)
    carga = _com(arma, a1=138.0, m1=(-1, 10), dy=-1)
    treme = _com(carga, a1=141.0)
    c1 = K.smear(_com(arma, a1=78.0, m1=(4, 9), pernas='avanco', dx=0.5, olhos='g', incl=1), 138.0)
    c2 = K.smear(_com(corta, a1=10.0, m1=(8, 4), incl=1), 78.0)
    c3 = K.smear(_com(corta, a1=-40.0, incl=1), 10.0)
    passa = _com(corta, a1=-58.0, m1=(6, -4), dx=3, incl=1)
    fica = _com(corta, olhos='s')
    chaves = [(20, g, 'segura'), (4, junta, 'in'), (5, ergue1, 'suave'), (4, carga, 'out'), (2, treme, 'segura'),
              (1, carga, 'segura'), (1, c1, 'segura'), (1, c2, 'segura'), (1, c3, 'segura'),
              (2, passa, 'out'), (3, passa, 'segura'), (10, fica, 'mola'), (6, fica, 'segura'),
              (12, _com(g, olhos='a'), 'suave'), (20, g, 'segura'), (1, g)]
    seq = K.sequencia(chaves)
    i_imp = sum(c[0] for c in chaves[:8])
    s = Sim(ps=9, M=K)
    return s.rodar(seq, eventos={i_imp: lambda sm: sm.empurrar(capa=14, cabelo=10)})


def folha(nome):
    """Visual novo x antigo, grande, em 3 poses."""
    poses = [('guarda', {}), ('corta_desce', dict(capa=0.9, cabelo=1.2, fase=0.4)),
             ('guarda', dict(capa=1.8, cabelo=2.0, fase=0.3))]
    caixa = (10 * 3, 12 * 3, 50 * 3, 48 * 3)
    esc = 6
    cols = []
    for base, kw in poses:
        a = imagem(_com(KV.POSE_A[base], **kw), esc, caixa, M=KV)
        b = imagem(_com(K.POSE_A[base], **kw), esc, caixa, M=K)
        cols.append((a, b))
    W, H = cols[0][0].size
    S = Image.new('RGB', (W * len(cols), H * 2 + 60), BG)
    d = ImageDraw.Draw(S)
    for i, (a, b) in enumerate(cols):
        S.paste(a, (i * W, 30))
        S.paste(b, (i * W, H + 60))
    d.text((12, 2), 'ANTES', fill=(160, 160, 180), font=FONTE)
    d.text((12, H + 32), 'DEPOIS', fill=(120, 230, 255), font=FONTE)
    S.save(os.path.join(OUT, nome))
    return S.size


if __name__ == '__main__':
    print('folha', folha('yoru_visual.png'))
    caixa_p = (4 * 3, 12 * 3, 62 * 3, 50 * 3)
    ims = lado_a_lado(parado(KV), parado(K), caixa_p, 'yoru_parado.gif')
    print('parado', len(ims), ims[0].size)
    caixa_g = (2 * 3, 12 * 3, 64 * 3, 66 * 3)
    ims = lado_a_lado(golpe_velho(), golpe_novo(), caixa_g, 'yoru_golpe.gif')
    print('golpe', len(ims), ims[0].size)

