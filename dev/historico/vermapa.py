"""Mostra mapas de caracteres ampliados lado a lado. uso: importar e chamar ver(lista, arquivo)"""
import os, sys
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app')
os.environ['KIVY_NO_ARGS'] = '1'; os.environ['KIVY_LOG_MODE'] = 'PYTHON'
import kirito as K
from PIL import Image, ImageDraw


def ver(mapas, arq, esc=12, fundo=(10, 10, 18)):
    larg = sum(len(m[0]) * esc + 20 for _, m in mapas)
    alt = max(len(m) for _, m in mapas) * esc + 24
    S = Image.new('RGB', (larg, alt), fundo)
    d = ImageDraw.Draw(S)
    ox = 0
    for nome, m in mapas:
        for y, l in enumerate(m):
            for x, ch in enumerate(l):
                if ch == '.':
                    continue
                r, g, b, a = K._PALETA[ch]
                d.rectangle([ox + x * esc, 20 + y * esc, ox + x * esc + esc - 1, 20 + y * esc + esc - 1],
                            fill=(int(r * 255), int(g * 255), int(b * 255)))
        d.text((ox + 2, 2), nome, fill='yellow')
        ox += len(m[0]) * esc + 20
    S.save(arq)
    return S.size
