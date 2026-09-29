"""_mover em degraus (como desenho em 2s): o corpo anda 30 vezes por segundo,
cai sempre em pixel inteiro e o giro do mortal vai de 90 em 90 graus (os
pixels do boneco nunca ficam tortos). Rastro na cor da forma atual. Mortais
da abertura na pose de bola."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'cenas.py'), [
    ("""def _mover(k, de, para, dur, altura=0.0, rot=None, fantasmas=3,
           cor_fantasma=CIANO, on_fim=None, linear=False, cada=None, on_passo=None,
           ease=None, limite=None):
    \"\"\"Move a ancora do Kirito em arco (parabola de `altura`), girando de
    rot[0] a rot[1]. Deixa `fantasmas` copias nitidas espalhadas pelo
    caminho (uma por quadro embolava num rastro de fumaca).
    ease: 'out' (desacelera), 'in' (acelera, queda) ou 'linear'.
    limite=(area, folga): o boneco (girado como estiver) nunca sai da area.
    on_passo(u) e chamado a cada quadro com o progresso 0..1.\"\"\"
    t = [0.0]
    feito = [False]""", """_PASSO_MOVER = 1 / 30.0      # o corpo anda em degraus de 1/30 s (desenho em 2s a 60 fps)


def _mover(k, de, para, dur, altura=0.0, rot=None, fantasmas=3,
           cor_fantasma=None, on_fim=None, linear=False, cada=None, on_passo=None,
           ease=None, limite=None):
    \"\"\"Move a ancora do Kirito em arco (parabola de `altura`), girando de
    rot[0] a rot[1]. Deixa `fantasmas` copias nitidas espalhadas pelo
    caminho (uma por quadro embolava num rastro de fumaca).
    ease: 'out' (desacelera), 'in' (acelera, queda) ou 'linear'.
    limite=(area, folga): o boneco (girado como estiver) nunca sai da area.
    on_passo(u) e chamado a cada degrau com o progresso 0..1.
    Como numa animacao desenhada, o corpo anda em degraus (30 por segundo,
    sempre em pixel inteiro) e o giro vai de 90 em 90 graus - girar pixel
    art num angulo torto entorta os pixels.\"\"\"
    t = [0.0]
    degrau = [-1]
    feito = [False]"""),
    ("""            t[0] += dt
            u = min(1.0, t[0] / dur)
            if on_passo:
                on_passo(u)          # troca a pose antes de enquadrar (sem 1 quadro de atraso)""",
     """            t[0] += dt
            u = min(1.0, t[0] / dur)
            d = int(t[0] / _PASSO_MOVER)
            if d == degrau[0] and u < 1:
                return True          # entre dois degraus: o desenho fica onde esta
            degrau[0] = d
            if on_passo:
                on_passo(u)          # troca a pose antes de enquadrar (sem 1 quadro de atraso)"""),
    ("""            if rot is not None:
                k.rotacao = rot[0] + (rot[1] - rot[0]) * e
            if limite is not None:
                x, y = _dentro_girado(k, x, y, limite[0], limite[1])
            k.ancorar(x, y)""", """            if rot is not None:
                r = rot[0] + (rot[1] - rot[0]) * e
                k.rotacao = (round(r / 90.0) * 90.0) % 360.0     # de 90 em 90 graus
            if limite is not None:
                x, y = _dentro_girado(k, x, y, limite[0], limite[1])
            k.ancorar(x, y)
            k.pos = (round(k.x), round(k.y))                    # pixel inteiro"""),
    # mortal da entrada e do TE na pose de bola
    ("""            kk.tocar(_voo_seq(K.esticado(p_pulo), K.encolhido(p_pulo), K.esticado(p_pulo), 0.5))
            _som('pulo')
            kk.empurrar(capa=-8, cabelo=-6, lift=10)""",
     """            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), K.esticado(p_pulo), 0.5))
            _som('pulo')
            kk.empurrar(capa=-8, cabelo=-6, lift=10)"""),
    ("""            kk.tocar(_voo_seq(K.esticado(p_pulo), K.encolhido(p_pulo), K.esticado(prep_fo), 0.32))""",
     """            kk.tocar(_voo_seq(K.esticado(p_pulo), K.bola(p_pulo), K.esticado(prep_fo), 0.32))"""),
])
print('ok')
