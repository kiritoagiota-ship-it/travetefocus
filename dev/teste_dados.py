"""Testa a gravacao e a leitura das anotacoes (main.py) numa pasta de teste
(nunca na pasta de dados de verdade):
  1) grava e le de volta: tudo igual (inclusive acentos e pecas do WhatsApp);
  2) dados.json estragado: le da copia de seguranca e guarda o estragado;
  3) varias gravacoes seguidas em paralelo: o arquivo final e valido;
  4) dados antigos (sem os campos novos) abrem sem erro.
uso: python dev/teste_dados.py"""
import os
import sys
import json
import shutil
import tempfile
import threading

os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_LOG_MODE', 'PYTHON')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402

App = main.TraveteApp
falhas = []


class Falso:
    """So o que salvar/carregar usam (sem abrir o app)."""
    _lock_salvar = threading.Lock()

    def __init__(self, pasta):
        self.user_data_dir = pasta
        self.memorias, self.registros = [], []
        self.total_geral = self.total_xp = self.streak = self.melhor_dia = 0
        self.meta_geral = 10000
        self.ultima_data = ''
        self.periodos_ganhos = []
        self.config_ganhos = {'valor_base': 0.25, 'valor_bonus': 0.30, 'meta_bonus': 400, 'tipo_periodo': 'semanal'}
        self.vibracao = True


for nome in ('salvar_dados', '_salvar_bg', '_salvar_bg_impl', 'carregar_dados', 'recalcular_totais'):
    setattr(Falso, nome, getattr(App, nome))


def confere(cond, txt):
    print(('OK    ' if cond else 'FALHA ') + txt)
    if not cond:
        falhas.append(txt)


pasta = tempfile.mkdtemp(prefix='tf_dados_')
try:
    a = Falso(pasta)
    a.memorias = [{'data': '14/10/2026  17:30', 'total': 180, 'xp': 540, 'itens': [['Calça jeans ção', '180', 540]],
                   'ts': 1.5}]
    a.registros = [['Camisa polo', '95', 285], ['Vestido', '60', 180, '13/10/2026']]
    a.recalcular_totais()
    a.salvar_dados(sincrono=True)
    b = Falso(pasta)
    b.carregar_dados()
    confere(b.memorias == a.memorias and b.registros == a.registros, '1) grava e le de volta igual')
    confere(os.path.exists(os.path.join(pasta, 'dados.backup1.json')), '1) copia de seguranca criada')

    # 2) dados.json estragado (gravacao cortada no meio)
    with open(os.path.join(pasta, 'dados.json'), 'w', encoding='utf-8') as f:
        f.write('{"memorias": [{"data": "14/10')
    c = Falso(pasta)
    c.carregar_dados()
    confere(c.memorias == a.memorias, '2) arquivo estragado: le da copia de seguranca')
    confere(os.path.exists(os.path.join(pasta, 'dados.json.corrompido')), '2) o estragado fica guardado')

    # 3) muitas gravacoes ao mesmo tempo (threads), mexendo nos dados no meio
    d = Falso(pasta)
    d.carregar_dados()
    for i in range(40):
        d.registros.append(['Peca %d' % i, str(i + 1), (i + 1) * 3])
        d.memorias[0]['total'] = i
        d.salvar_dados()
    import time
    time.sleep(1.5)
    d.salvar_dados(sincrono=True)
    with open(os.path.join(pasta, 'dados.json'), encoding='utf-8') as f:
        final = json.load(f)
    confere(len(final['registros']) == 42, '3) 40 gravacoes seguidas: o arquivo final esta completo')
    confere(not os.path.exists(os.path.join(pasta, 'dados.json.tmp')), '3) nao sobra arquivo temporario')

    # 4) dados de uma versao antiga do app
    with open(os.path.join(pasta, 'dados.json'), 'w', encoding='utf-8') as f:
        json.dump({'memorias': [{'data': '01/09/2026', 'total': '120', 'itens': [['Bermuda', '120']]}],
                   'registros': [['Saia', '10', 30]], 'streak': 3}, f)
    e = Falso(pasta)
    e.carregar_dados()
    confere(e.total_geral == 120 and len(e.registros) == 1, '4) dados antigos abrem e somam certo')
finally:
    shutil.rmtree(pasta, ignore_errors=True)
print('%d falhas' % len(falhas))
