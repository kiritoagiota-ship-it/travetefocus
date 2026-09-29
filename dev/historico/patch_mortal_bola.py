import sys
sys.path.insert(0, r'C:\Users\kirit\travetefocus\app\dev')
from p import patch
patch(r'C:\Users\kirit\travetefocus\app\cenas.py', [
    ("""           cor_fantasma=None, on_fim=None, linear=False, cada=None, on_passo=None,
           ease=None, limite=None):""", """           cor_fantasma=None, on_fim=None, linear=False, cada=None, on_passo=None,
           ease=None, limite=None, rot_janela=(0.0, 1.0)):"""),
    ("""            if rot is not None:
                r = rot[0] + (rot[1] - rot[0]) * e""", """            if rot is not None:
                ja, jb = rot_janela            # o giro so acontece nessa parte do voo (na bola)
                g = max(0.0, min(1.0, (e - ja) / max(1e-6, jb - ja)))
                r = rot[0] + (rot[1] - rot[0]) * g"""),
    ("""            \"\"\"Poses de um salto com a duracao do voo: sai esticado, encolhe
            no alto e estica de novo para pousar - tudo interpolado.\"\"\"
            n = max(6, int(round(dur * K.FPS)))
            a = max(2, int(n * 0.35))
            b = max(2, n - a)
            return K.sequencia([(a, p_ini, 'out'), (b, p_ar, 'suave'), (1, p_fim)])""",
     """            \"\"\"Poses de um salto com a duracao do voo: sai esticado, fecha
            na bola (segura enquanto gira) e abre de novo para pousar.\"\"\"
            n = max(6, int(round(dur * K.FPS)))
            a = max(2, int(n * 0.22))
            c = max(2, int(n * 0.25))
            b = max(2, n - a - c)
            return K.sequencia([(a, p_ini, 'out'), (b, p_ar, 'segura'), (c, p_ar, 'out'), (1, p_fim)])"""),
    ("""            _mover(kk, ini, A0, 0.5, rot=(0, 360), fantasmas=4, ease='in', on_fim=_pousa)""",
     """            _mover(kk, ini, A0, 0.5, rot=(0, 360), fantasmas=4, ease='in', on_fim=_pousa,
                   rot_janela=(0.2, 0.75))"""),
    ("""            _mover(kk, (ax, ay), D0, 0.32, altura=h, rot=(0, -360), fantasmas=2, limite=(area, m),
                   on_fim=_chegou)""", """            _mover(kk, (ax, ay), D0, 0.32, altura=h, rot=(0, -360), fantasmas=2, limite=(area, m),
                   on_fim=_chegou, rot_janela=(0.2, 0.75))"""),
])
print('ok')
