"""Testa a logica de Ganhos (telas/ganhos.py) com o codigo real, sem abrir a UI."""
import os, sys
os.environ['KIVY_NO_ARGS'] = '1'
os.environ['KIVY_LOG_MODE'] = 'PYTHON'
REPO = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
sys.path.insert(0, REPO)
os.chdir(REPO)
from kivy.app import App  # noqa: E402
import som  # noqa: E402
som.tocar = lambda *a, **k: None
for n in dir(som):
    if n.startswith('tocar_'):
        setattr(som, n, lambda *a, **k: None)
import telas.ganhos as G  # noqa: E402


class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


app = Obj(config_ganhos={'valor_base': 0.25, 'valor_bonus': 0.30, 'meta_bonus': 3000,
                         'tipo_periodo': 'semanal'},
          memorias=[], periodos_ganhos=[], salvos=0)
app.salvar_dados = lambda *a, **k: setattr(app, 'salvos', app.salvos + 1)
App.get_running_app = staticmethod(lambda: app)
tela = G.TelaGanhos.__new__(G.TelaGanhos)

print('== calculo (base 0,25 / bonus 0,30 / meta 3000) ==')
for pecas in (0, 1000, 2999, 3000, 3001, 3500, 6000):
    print(f'  {pecas:5d} pecas -> R$ {G.TelaGanhos._calcular_ganho(tela, pecas):8.2f}')

print('== pecas no periodo (datas inclusivas) ==')
app.memorias = [{'data': '13/09/2026  18:00', 'total': 100}, {'data': '14/09/2026  09:00', 'total': 200},
                {'data': '15/09/2026  18:00', 'total': 300}, {'data': '21/09/2026  18:00', 'total': 400}]
print('  de 14/09 aberto          :', G.TelaGanhos._pecas_no_periodo(tela, '14/09/2026'))
print('  de 14/09 ate 15/09       :', G.TelaGanhos._pecas_no_periodo(tela, '14/09/2026', '15/09/2026'))

print('== salvar configuracao com textos diferentes ==')


def cfg_com(base, bonus, meta):
    app.config_ganhos = {'valor_base': 0.25, 'valor_bonus': 0.30, 'meta_bonus': 3000, 'tipo_periodo': 'semanal'}
    ids = Obj(inp_valor_base=Obj(text=base), inp_valor_bonus=Obj(text=bonus),
              inp_meta_bonus=Obj(text=meta), spin_tipo=Obj(text='Semanal'))
    tela.__dict__['_ids_fake'] = ids
    G.TelaGanhos.ids = property(lambda self: self.__dict__['_ids_fake'])
    G.TelaGanhos._atualizar_periodo_atual = lambda self: None
    antes = app.salvos
    G.TelaGanhos.salvar_config(tela)
    c = app.config_ganhos
    print(f'  base={base!r:8} bonus={bonus!r:8} meta={meta!r:7} -> base {c["valor_base"]}, '
          f'bonus {c["valor_bonus"]}, meta {c["meta_bonus"]} (salvou: {app.salvos > antes})')


cfg_com('0.25', '0.35', '2500')
cfg_com('0,25', '0,35', '2500')
cfg_com('0.25', '', '2500')
cfg_com('0.25', '0.35', '')
