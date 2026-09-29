"""Gera os desenhos do Bankai que vao no APK (app/bankai/p1..p6.png) a partir
da referencia do usuario, copiada pixel a pixel (bankai_ref.py), e o
modulo app/bankai_desenhos.py com os pontos de cada pose.

Cada pose vira uma tira de QUADROS pixel art: o corpo e a espada ficam
firmes; o cabelo, as pontas do sobretudo e as chamas ondulam nos proprios
pixels (a onda desce da raiz para a ponta) e as chamas/brasas trocam de
brilho a cada quadro - o desenho da referencia, vivo.
uso: python dev/bankai_folhas.py"""
import os
import sys
import math
import json
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bankai_ref import extrair                                    # noqa: E402

APP = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
PASTA = os.path.join(APP, 'bankai')
N_QUADROS = 6
FPS = 12

# pontos de cada pose (pixels do desenho, y para BAIXO). quadril: fica na
# ancora do Yoru (os pes caem no mesmo chao: pes - 60 = quadril). corpo:
# (centro x, meia-largura) da parte firme. manter: (x0, y0, x1, y1) do que
# e da pose (o resto era do quadro vizinho da referencia).
POSES = {
    'p1': dict(nome='de lado, espada baixa', quadril=(95, 124), mao=(107, 92), ponta=(184, 180),
               olho=(100, 38), corpo=(95, 9), manter=(0, 0, 172, 193)),
    'p2': dict(nome='no ar, cortando', quadril=(98, 116), mao=(138, 112), ponta=(190, 158),
               olho=(122, 72), corpo=(112, 11), manter=(0, 0, 193, 193)),
    'p3': dict(nome='de costas, espada baixa', quadril=(118, 125), mao=(142, 88), ponta=(186, 178),
               olho=(126, 35), corpo=(122, 9), manter=(26, 0, 193, 193)),
    'p4': dict(nome='agachado, carregando', quadril=(104, 110), mao=(112, 90), ponta=(190, 157),
               olho=(105, 57), corpo=(102, 11), manter=(0, 0, 193, 193)),
    'p5': dict(nome='de frente, lua negra', quadril=(100, 120), mao=(77, 86), ponta=(37, 165),
               olho=(102, 43), corpo=(100, 11), manter=(10, 0, 193, 193)),
    'p6': dict(nome='corte avancando', quadril=(95, 112), mao=(113, 84), ponta=(186, 155),
               olho=(118, 65), corpo=(98, 11), manter=(0, 0, 193, 193)),
}


def _dist_segmento(x, y, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy or 1.0
    t = np.clip(((x - ax) * vx + (y - ay) * vy) / L2, 0.0, 1.0)
    return np.hypot(x - (ax + t * vx), y - (ay + t * vy))


def _ruido(x, y, f):
    """Ruido fixo por bloco de 3x3 e quadro (0..1)."""
    h = (x // 3) * 73856093 ^ (y // 3) * 19349663 ^ (f + 1) * 83492791
    return ((h & 0xFFFF) / 65535.0)


def quadros(rgba, meta):
    h, w = rgba.shape[:2]
    x0, y0, x1, y1 = meta['manter']
    rgba = rgba.copy()
    fora = np.ones((h, w), bool)
    fora[y0:y1, x0:x1] = False
    rgba[fora, 3] = 0
    ys, xs = np.mgrid[0:h, 0:w]
    # perto da borda do quadro (onde a referencia cortava os arcos e o
    # cabelo reto) o desenho se desfaz em lascas, sem linha reta
    borda = np.minimum.reduce([xs - x0, x1 - 1 - xs, ys - y0, y1 - 1 - ys]).astype(float)
    lasca = np.vectorize(lambda x, y: _ruido(x * 3, y * 3, 7))(xs // 2, ys // 2)
    rgba[(borda / 14.0) < lasca * 1.1, 3] = 0
    cx, meia = meta['corpo']
    qy = meta['quadril'][1]
    # firme: a espada (da mao a ponta) e o tronco
    espada = _dist_segmento(xs, ys, meta['mao'], meta['ponta']) < 4.5
    tronco = (np.abs(xs - cx) <= meia) & (ys > meta['olho'][1] - 14) & (ys < qy + 40)
    firme = espada | tronco
    # quanto balanca: longe do corpo (cabelo e caudas para os lados) e na barra
    lado = np.clip((np.abs(xs - cx) - meia - 2) / 26.0, 0, 1)
    barra = np.clip((ys - (qy + 30)) / 40.0, 0, 1)
    amp = np.where(firme, 0.0, np.clip(lado * 1.7 + barra * 0.9, 0, 1.8))
    rgb = rgba[..., :3].astype(float)
    brilho = rgb.max(axis=2)
    satur = brilho - rgb.min(axis=2)
    energia = (satur > 70) & (rgb[..., 2] > 110) & (rgba[..., 3] > 0) & ~espada
    out = []
    for f in range(N_QUADROS):
        fase = 2 * math.pi * f / N_QUADROS
        onda = np.sin(fase - ys * 0.11 - xs * 0.035)
        dx = np.rint(amp * onda).astype(int)
        dy = np.rint(amp * 0.45 * np.sin(fase * 1.0 - xs * 0.09 + 1.3)).astype(int)
        sx = np.clip(xs - dx, 0, w - 1)
        sy = np.clip(ys - dy, 0, h - 1)
        q = rgba[sy, sx].copy()
        # chamas e brasas: o brilho troca em degraus a cada quadro
        en = energia[sy, sx]
        ru = np.vectorize(_ruido)(xs, ys, f)
        fator = np.where(en, 0.78 + 0.44 * np.round(ru * 3) / 3.0, 1.0)
        q[..., :3] = np.clip(q[..., :3].astype(float) * fator[..., None], 0, 255).astype(np.uint8)
        solta = en & (amp > 0.6) & (ru < 0.18)             # brasa longe do corpo pisca
        q[solta, 3] = 0
        out.append(q)
    return out


def main():
    os.makedirs(PASTA, exist_ok=True)
    info = {}
    for nome, meta in POSES.items():
        rgba = extrair(int(nome[1]))
        qs = quadros(rgba, meta)
        h, w = rgba.shape[:2]
        folha = np.concatenate(qs, axis=1)
        Image.fromarray(folha, 'RGBA').save(os.path.join(PASTA, nome + '.png'), optimize=True)
        sil = folha.copy()                                  # silhueta branca (quadro de impacto)
        sil[..., :3] = 255
        Image.fromarray(sil, 'RGBA').save(os.path.join(PASTA, nome + '_sil.png'), optimize=True)
        a = qs[0][..., 3] > 0
        ys, xs = np.nonzero(a)
        info[nome] = dict(meta, tam=(w, h), n=N_QUADROS, caixa=(int(xs.min()), int(ys.min()),
                                                                  int(xs.max()), int(ys.max())))
        print(nome, meta['nome'], (w, h), os.path.getsize(os.path.join(PASTA, nome + '.png')) // 1024, 'KB')
    with open(os.path.join(APP, 'bankai_desenhos.py'), 'w', encoding='utf-8') as fp:
        fp.write('"""Desenhos do Bankai copiados pixel a pixel da referencia do usuario\n'
                 '(gerado por dev/bankai_folhas.py - nao editar a mao). Pontos em pixels do\n'
                 'desenho, y para BAIXO; cada PNG em bankai/ tem N quadros lado a lado."""\n')
        fp.write(f'FPS = {FPS}\n')
        fp.write('POSES = ' + json.dumps(info, ensure_ascii=False, indent=1)
                 .replace('true', 'True').replace('false', 'False') + '\n')
    print('ok')


if __name__ == '__main__':
    main()
