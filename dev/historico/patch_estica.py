"""Compressao e esticada nos golpes e saltos (squash & stretch)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
patch(os.path.join(A, 'kirito.py'), [
    ("""    ant['vista'] = 'costas'                          # torce o corpo: mostra as costas""",
     """    ant['vista'] = 'costas'                          # torce o corpo: mostra as costas
    ant['estica'] = -1                               # encolhe juntando forca"""),
    ("""    imp = dict(corta, olhos=olhos[1], incl=1, vista='frente')   # corta de frente, peso a frente""",
     """    imp = dict(corta, olhos=olhos[1], incl=1, vista='frente', estica=1)   # corta esticado, peso a frente"""),
    ("""        seg['dx'] = corta['dx'] + 1                  # inclina para a frente
        seg['incl'] = 1""", """        seg['dx'] = corta['dx'] + 1                  # inclina para a frente
        seg['incl'] = 1
        seg['estica'] = 0"""),
    ("""        seg = dict(seg, olhos=olhos[1], incl=1, vista='lado')""",
     """        seg = dict(seg, olhos=olhos[1], incl=1, vista='lado', estica=0)"""),
    ("""    q['incl'] = 1
    q['lift'] = max(q.get('lift', 0.0), 0.8)
    return q""", """    q['incl'] = 1
    q['estica'] = -1
    q['lift'] = max(q.get('lift', 0.0), 0.8)
    return q"""),
    ("""    q = dict(p)
    q['pernas'] = 'suspenso'
    q['pernas_b'] = None
    q['dy'] = 0
    return q""", """    q = dict(p)
    q['pernas'] = 'suspenso'
    q['pernas_b'] = None
    q['dy'] = 0
    q['estica'] = 1                                  # o corpo todo estica no impulso
    return q"""),
])
patch(os.path.join(A, 'cenas.py'), [
    # pouso da entrada: amortece encolhendo
    ("""            kk.tocar(K.sequencia(_de_agora(kk, 2) + [(3, agacha, 'out'), (3, pronto, 'suave'),
                                                      (1, pronto)]))""",
     """            kk.tocar(K.sequencia(_de_agora(kk, 1) + [(2, _com(agacha, estica=-1), 'segura'),
                                                      (4, agacha, 'out'), (4, pronto, 'suave'),
                                                      (1, pronto)]))"""),
    ("""                baixo = _com(prep_fo, dy=prep_fo['dy'] - 1)       # amortece a queda""",
     """                baixo = _com(prep_fo, dy=prep_fo['dy'] - 1, estica=-1)   # amortece a queda"""),
    ("""                kk.tocar(K.sequencia([(2, _com(dupla, dy=dupla['dy'] - 2), 'out'), (3, dupla, 'out'),
                                      (1, dupla)]), on_fim=lambda: ag.depois(0.15, _guarda_azul))""",
     """                kk.tocar(K.sequencia([(2, _com(dupla, dy=dupla['dy'] - 2, estica=-1), 'segura'),
                                      (4, dupla, 'out'), (1, dupla)]),
                         on_fim=lambda: ag.depois(0.15, _guarda_azul))"""),
])
print('ok')
