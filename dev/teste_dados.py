"""Testa a gravacao e a leitura das anotacoes (main.py) numa pasta de teste
(nunca na pasta de dados de verdade):
  1) grava e le de volta: tudo igual (inclusive acentos e pecas do WhatsApp);
  2) dados.json estragado: le da copia de seguranca e guarda o estragado;
  3) varias gravacoes seguidas em paralelo: o arquivo final e valido;
  4) dados antigos (sem os campos novos) abrem sem erro;
  7) copias: backup1/2/3 guardam as versoes ANTERIORES e ha uma copia por dia
     (backups/dados-AAAAMMDD.json, as 14 mais novas), com a data simulada.
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


for nome in ('salvar_dados', '_salvar_bg', '_salvar_bg_impl', 'carregar_dados', 'recalcular_totais',
             '_normalizar_memorias', '_normalizar_registros'):
    setattr(Falso, nome, getattr(App, nome))
Falso._int = staticmethod(App._int)


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
    confere(not os.path.exists(os.path.join(pasta, 'dados.backup1.json')),
            '1) 1a gravacao (pasta vazia): nao ha versao anterior para copiar')
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
    confere(e.memorias[0]['total'] == 120 and e.memorias[0]['xp'] == 0,
            '4) total salvo como texto ("120") vira numero e o xp que faltava vira 0')

    # 5) registro antigo/estranho: quantidade com espaco, xp faltando, item quebrado
    with open(os.path.join(pasta, 'dados.json'), 'w', encoding='utf-8') as f:
        json.dump({'memorias': [{'data': '01/09/2026', 'total': 50, 'itens': 'x', 'meu_campo': 7}],
                   'registros': [['Saia', ' 10 ', 30], ['Short', '5'], ['quebrado'], 'lixo']}, f)
    g = Falso(pasta)
    g.carregar_dados()
    confere(g.registros == [['Saia', '10', 30], ['Short', '5', 0]], '5) registros estranhos ficam certos (e os quebrados saem)')
    confere(g.memorias[0]['itens'] == [] and g.memorias[0]['meu_campo'] == 7, '5) campo desconhecido continua la')

    # 6) um defeito na conferencia NAO pode trocar dados bons por copia/vazio
    a.salvar_dados(sincrono=True)
    bom = open(os.path.join(pasta, 'dados.json'), encoding='utf-8').read()
    h = Falso(pasta)
    h._normalizar_memorias = lambda lista: 1 / 0          # simula um erro na conferencia
    h.carregar_dados()
    confere(h.memorias == a.memorias and not os.path.exists(os.path.join(pasta, 'dados.json.corrompido2')),
            '6) erro na conferencia: os turnos continuam os do arquivo (nada de copia ou vazio)')
    confere(open(os.path.join(pasta, 'dados.json'), encoding='utf-8').read() == bom, '6) o arquivo nao foi mexido')

    # 7) copias: versoes anteriores e uma copia por dia, com a data simulada
    p7 = tempfile.mkdtemp(prefix='tf_copias_')
    hoje_real = main._hoje_copia
    try:
        k = Falso(p7)

        def gravar(n):
            k.registros = [['Lote %d' % n, str(n), n]]
            k.salvar_dados(sincrono=True)

        def lido(nome):
            with open(os.path.join(p7, nome), encoding='utf-8') as f:
                return json.load(f)['registros'][0][0]

        versao = 0
        for dia in range(1, 21):                      # 20 dias, 3 gravacoes por dia
            main._hoje_copia = lambda dia=dia: '202611%02d' % dia
            for _ in range(3):
                versao += 1
                gravar(versao)
            if dia == 1:
                confere(lido('backups/dados-20261101.json') == 'Lote 1',
                        '7) dia 1 (pasta nova): a copia sai na 2a gravacao (a 1a nao tinha arquivo antes)')
            elif dia == 2:
                confere(lido('backups/dados-20261102.json') == 'Lote 3',
                        '7) copia do dia 2 = como o arquivo estava no fim do dia 1')
        confere(lido('dados.json') == 'Lote 60', '7) dados.json = ultima gravacao')
        confere([lido('dados.backup%d.json' % i) for i in (1, 2, 3)] == ['Lote 59', 'Lote 58', 'Lote 57'],
                '7) backup1/2/3 = as 3 versoes ANTERIORES (nenhuma repete o dados.json)')
        copias = sorted(os.listdir(os.path.join(p7, 'backups')))
        confere(len(copias) == 14, '7) guarda so 14 copias do dia (tem %d)' % len(copias))
        confere(copias[0] == 'dados-20261107.json' and copias[-1] == 'dados-20261120.json',
                '7) ficam as 14 mais novas (07 a 20/11)')
        confere(lido('backups/dados-20261120.json') == 'Lote 57',
                '7) copia de hoje = o arquivo antes da 1a gravacao de hoje')
        confere(not [n for n in copias if n.endswith('.tmp')], '7) nao sobra .tmp na pasta das copias')
        # tudo estragado menos as copias do dia: le a copia mais nova
        for n in ('dados.json', 'dados.backup1.json', 'dados.backup2.json', 'dados.backup3.json'):
            with open(os.path.join(p7, n), 'w', encoding='utf-8') as f:
                f.write('{estragado')
        m = Falso(p7)
        m.carregar_dados()
        confere(m.registros and m.registros[0][0] == 'Lote 57', '7) tudo estragado: le a copia do dia mais nova')
        # a copia do dia nao pode travar a gravacao: pasta 'backups' que e um ARQUIVO
        p8 = tempfile.mkdtemp(prefix='tf_copias2_')
        try:
            n8 = Falso(p8)
            n8.salvar_dados(sincrono=True)
            open(os.path.join(p8, 'backups'), 'w').close()
            main._hoje_copia = lambda: '20261201'
            n8.registros = [['Depois', '1', 1]]
            n8.salvar_dados(sincrono=True)
            with open(os.path.join(p8, 'dados.json'), encoding='utf-8') as f:
                confere(json.load(f)['registros'][0][0] == 'Depois', '7) copia do dia falhando: grava assim mesmo')
        finally:
            shutil.rmtree(p8, ignore_errors=True)
        # tempo: a gravacao com copia do dia continua rapida
        import time as _t
        main._hoje_copia = lambda: '20261202'
        t0 = _t.perf_counter()
        gravar(999)
        dt = _t.perf_counter() - t0
        print('      (gravacao com copia do dia: %.1f ms)' % (dt * 1000))
    finally:
        main._hoje_copia = hoje_real
        shutil.rmtree(p7, ignore_errors=True)
finally:
    shutil.rmtree(pasta, ignore_errors=True)

# 8) exportar: ordem por data (como nas Memorias) e melhor dia somando os turnos do dia
import exportar  # noqa: E402
mems = [{'data': '13/11/2026  12:00', 'total': 400, 'xp': 1}, {'data': '13/11/2026  18:00', 'total': 300, 'xp': 1},
        {'data': '02/11/2026  18:00', 'total': 500, 'xp': 1},            # dia antigo lancado depois
        {'data': '10/11/2026', 'total': '650', 'xp': '2'}]               # versao antiga: texto e sem hora
rel = exportar.gerar_relatorio_whatsapp(mems)
confere('Melhor dia:      700 peças (13/11/2026)' in rel, '8) melhor dia soma os 2 turnos do 13/11 (700)')
ult = rel.split('ÚLTIMOS 10 TURNOS:*')[1].strip().splitlines()
confere([x.split()[0] for x in ult] == ['13/11/2026', '13/11/2026', '10/11/2026', '02/11/2026'],
        '8) ultimos turnos do mais novo para o mais velho (nao a ordem de gravacao)')
confere('Total de peças:  1850' in rel, '8) total aceita numero salvo como texto')
csv_l = exportar.gerar_csv_bytes(mems).decode('utf-8-sig').splitlines()[1:]
confere([x.split(',')[0] for x in csv_l] == ['13/11/2026  18:00', '13/11/2026  12:00', '10/11/2026',
                                             '02/11/2026  18:00'], '8) CSV na mesma ordem das Memorias')
confere(exportar.melhor_dia([]) == ('?', 0), '8) melhor dia sem turnos')
print('%d falhas' % len(falhas))
