"""Filma TODAS as aparicoes do Yoru no app de verdade (telas reais, dados de
exemplo), com o RELOGIO SIMULADO do filme.py (1/60 s por quadro exato).

CENA=app (padrao): senha ainda valendo -> entrada rapida -> menu -> +XP
  (carimbo), apagar peca (iai), finalizar turno (vitoria), subir de nivel
  (Progresso), bater a meta (Ganhos), apagar periodo (X), WhatsApp
  (pergaminho), apagar o dia (estocada), WIPE.
CENA=pin: sem sessao -> o Yoru espiando a caixa da senha, senha errada,
  senha certa (ate o comeco da abertura).
CENA=telas: uma foto parada de cada tela e de cada aviso do app
  (tela_NN-nome.png), para conferir se tem coisa fora do lugar. Usar CADA=0.
CENA=zap: COLAR DO WHATSAPP de ponta a ponta (texto de exemplo no lugar do
  que estaria copiado): lista do que achou, tirar uma peça, XP, a lista do
  registro, finalizar (um turno por dia) e as memorias. Confere os dados
  gravados e escreve o resultado em filme.json ('zap'). Usar CADA=0.

uso (Git Bash, em app/):
  CENA=app CADA=3 TOUR_PY=dev/filme_cenas.py bash dev/tour.sh 720 1560 SAIDA 1.75
Saida: fNNNNN.png (quadro absoluto), filme.json: fases [quadro, nome],
quadros [quadro, [yorus]], sons, erros."""
import os
import sys
import json
import time
import random

LARG, ALT, SAIDA = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
DENS = sys.argv[4] if len(sys.argv) > 4 else None
CENA = os.environ.get('CENA', 'app')
CADA = int(os.environ.get('CADA', '3'))
REPO = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
os.makedirs(SAIDA, exist_ok=True)
if DENS:
    os.environ['KIVY_METRICS_DENSITY'] = DENS
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_LOG_MODE', 'PYTHON')

# ── dados de exemplo ─────────────────────────────────────────────────
random.seed(7)
pasta_app = os.path.join(os.environ['APPDATA'], 'travete')
os.makedirs(pasta_app, exist_ok=True)
nomes = ['Camisa polo', 'Calca jeans', 'Vestido longo', 'Bermuda', 'Jaqueta corta-vento']
memorias = []
for i, d in enumerate(range(15, 25)):
    itens = [[random.choice(nomes), str(q), q * 3] for q in (random.randint(60, 200), random.randint(40, 150))]
    memorias.append({'data': f'{d:02d}/09/2026  17:{10 + i:02d}', 'total': sum(int(x[1]) for x in itens),
                     'xp': sum(x[2] for x in itens), 'itens': itens, 'ts': 1790000000 + i})
registros = [['Camisa polo', '180', 540], ['Calca jeans', '95', 380], ['Vestido longo', '60', 240]]
if CENA == 'meta':
    # METAS: semana com turnos de seg ate ontem e lotes de hoje com hora (ritmo ~52/h)
    import datetime as _dt
    _hoje = _dt.date.today()
    _seg = _hoje - _dt.timedelta(days=_hoje.weekday() if _hoje.weekday() < 6 else -1)
    memorias = []
    for _i in range((_hoje - _seg).days):
        _d = _seg + _dt.timedelta(days=_i)
        memorias.append({'data': _d.strftime('%d/%m/%Y') + '  17:30', 'total': 430, 'xp': 1290,
                         'itens': [['Camisa polo', '430', 1290]], 'ts': 1790000000 + _i})
    _t0 = _dt.datetime.combine(_hoje, _dt.time(7, 30)).timestamp()
    registros = [['Camisa polo', '60', 180, '', _t0], ['Camisa polo', '52', 156, '', _t0 + 3600],
                 ['Calca jeans', '50', 150, '', _t0 + 7200], ['Calca jeans', '54', 162, '', _t0 + 10800]]
if CENA == 'varre':
    # casos extremos: VARRE="turnos,itens do ultimo turno,pecas no registro"
    _nm, _ni, _nr = [int(v) for v in os.environ.get('VARRE', '1,0,1').split(',')]
    memorias = [{'data': f'{1 + i % 28:02d}/{1 + (i // 28) % 12:02d}/2026  17:00', 'total': 100, 'xp': 300,
                 'itens': [['Camisa polo', '100', 300]], 'ts': 1790000000 + i} for i in range(_nm)]
    if memorias:
        memorias[-1]['itens'] = [[nomes[j % len(nomes)] + ' %d' % j, '10', 30] for j in range(_ni)]
    registros = [[nomes[j % len(nomes)] + ' %d' % j, '10', 30] for j in range(_nr)]
dados = {
    'memorias': memorias, 'total_geral': sum(m['total'] for m in memorias), 'meta_geral': 10000,
    'total_xp': sum(m['xp'] for m in memorias) + sum(r[2] for r in registros),
    'registros': registros, 'streak': 10, 'melhor_dia': max([m['total'] for m in memorias] or [0]),
    'ultima_data': '24/09/2026',
    'periodos_ganhos': [
        {'tipo': 'semanal', 'data_inicio': '01/09/2026', 'data_fim': '07/09/2026',
         'total_pecas': 3320, 'total_ganho': 846.0},
        {'tipo': 'semanal', 'data_inicio': '14/09/2026', 'data_fim': None, 'total_pecas': 0,
         'total_ganho': 0.0}],
    'config_ganhos': {'valor_base': 0.25, 'valor_bonus': 0.30, 'meta_bonus': 400, 'tipo_periodo': 'semanal'},
}
if CENA == 'meta':                     # a regra real: 2.500 / 3.000 por semana
    dados['config_ganhos'] = {'valor_base': 0.25, 'valor_bonus': 0.30, 'meta_bonus': 3000, 'tipo_periodo': 'semanal'}
with open(os.path.join(pasta_app, 'dados.json'), 'w', encoding='utf-8') as f:
    json.dump(dados, f, ensure_ascii=False)
if CENA in ('app', 'telas', 'zap', 'varre', 'meta'):
    with open(os.path.join(pasta_app, '.tf_session'), 'w') as f:
        f.write(str(time.time()))

from kivy.config import Config  # noqa: E402
Config.set('graphics', 'width', str(LARG))
Config.set('graphics', 'height', str(ALT))
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'maxfps', '0')
sys.path.insert(0, REPO)
os.chdir(REPO)
import main  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.app import App  # noqa: E402
from kivy.uix.popup import Popup  # noqa: E402
from kivy.uix.textinput import TextInput  # noqa: E402
from kivy.graphics.opengl import glReadPixels, GL_RGBA, GL_UNSIGNED_BYTE  # noqa: E402
from PIL import Image  # noqa: E402
import som  # noqa: E402
import cenas  # noqa: E402
import kirito as K  # noqa: E402
import exportar  # noqa: E402

Window.size = (LARG, ALT)
exportar._copiar = lambda texto: True          # WhatsApp: nao mexe na area de transferencia

# ── relogio simulado ─────────────────────────────────────────────────
SIM = [None]
_tempo_real = Clock.time
Clock._max_fps = 0
Clock.time = lambda: SIM[0] if SIM[0] is not None else _tempo_real()
_pre = Clock.pre_idle


def _pre_idle():
    if SIM[0] is not None:
        SIM[0] += 1 / 60.
    _pre()


Clock.pre_idle = _pre_idle
LOG = {'quadros': [], 'sons': [], 'fases': [], 'erros': []}
Q = [0]
GRAVA = [False]
som.tocar = lambda acao, *a, **k: LOG['sons'].append([Q[0], acao])
LOG['na_hora'] = []                 # quadros em que um desenho do Yoru foi montado na hora
_rasteriza = K._rasteriza


def _conta_rasteriza(*a, **kw):
    LOG['na_hora'].append(Q[0])
    return _rasteriza(*a, **kw)


K._rasteriza = _conta_rasteriza
som.precarregar = lambda *a, **k: None
cenas._som = lambda nome: LOG['sons'].append([Q[0], nome])


def fase(nome):
    LOG['fases'].append([Q[0], nome])
    print(f'[cenas] q{Q[0]:6d} {nome}')


def _yorus():
    out = []
    for topo in Window.children:
        for w in topo.walk(restrict=False):
            if isinstance(w, K.KiritoPixel) and w.get_root_window() is not None:
                out.append(w)
    return out


FOTO = [None]


def foto(nome):
    """Tira a foto da tela no proximo quadro desenhado (pede um desenho
    novo: com a tela parada o Kivy nao redesenha sozinho)."""
    FOTO[0] = nome
    Window.canvas.ask_update()


def _quadro(*_):
    Q[0] += 1
    if FOTO[0]:
        nome, FOTO[0] = FOTO[0], None
        try:
            w, h = Window.size
            dados_px = glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)
            im = Image.frombytes('RGBA', (w, h), dados_px).transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
            im.save(os.path.join(SAIDA, f'tela_{nome}.png'), compress_level=3)
            print(f'[cenas] foto {nome}')
        except Exception as e:
            LOG['erros'].append(f'foto {nome}: {e}')
    if not GRAVA[0]:
        return
    reg = []
    for k in _yorus():
        try:
            ax, ay = k.ancora()
            reg.append({'i': id(k) % 100000, 'x': round(ax, 1), 'y': round(ay, 1),
                        'rot': round(k.rotacao, 1), 'esp': bool(k.espelhar), 'op': round(k.opacity, 2),
                        'des': hash(k._ult_chave) % 10 ** 9, 'ps': k.ps,
                        'clipe': k._desenho})
        except Exception as e:
            LOG['erros'].append(f'yoru: {e}')
    LOG['quadros'].append([Q[0], reg])
    if CADA and Q[0] % CADA == 0:
        try:
            w, h = Window.size
            dados_px = glReadPixels(0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE)
            im = Image.frombytes('RGBA', (w, h), dados_px).transpose(Image.FLIP_TOP_BOTTOM).convert('RGB')
            im.save(os.path.join(SAIDA, f'f{Q[0]:06d}.png'), compress_level=3)
        except Exception as e:
            LOG['erros'].append(f'foto: {e}')


Window.bind(on_flip=_quadro)


def fim(*_):
    with open(os.path.join(SAIDA, 'filme.json'), 'w', encoding='utf-8') as f:
        json.dump(LOG, f)
    print('[cenas] fim', len(LOG['quadros']), 'quadros', len(LOG['erros']), 'erros')
    fases = LOG['fases']
    for i, (q0, nome) in enumerate(fases):
        q1 = fases[i + 1][0] if i + 1 < len(fases) else 10 ** 9
        n = sum(1 for q in LOG['na_hora'] if q0 <= q < q1)
        if n:
            print(f'[cenas] desenhos na hora em "{nome}": {n}')
    App.get_running_app().stop()


# ── ajudantes ────────────────────────────────────────────────────────
def app():
    return App.get_running_app()


def tela():
    return app().root.ids.sm.current_screen


def achar(txt):
    """O botao (tem on_release) com esse texto, do popup de cima para baixo."""
    for topo in Window.children:
        for w in topo.walk():
            if (txt in str(getattr(w, 'text', '')) and w.get_root_window() is not None and w.opacity > 0.05
                    and hasattr(w, 'is_event_type') and w.is_event_type('on_release')):
                return w
    return None


def apertar(txt):
    w = achar(txt)
    if w is None:
        LOG['erros'].append('botao nao achado: ' + txt)
        return
    w.dispatch('on_release')


def popup():
    for w in Window.children:
        if isinstance(w, Popup):
            return w
    return None


def fechar_popups():
    for w in list(Window.children):
        if isinstance(w, Popup):
            w.dismiss()


def campo_do_popup():
    p = popup()
    for w in (p.walk() if p else []):
        if isinstance(w, TextInput):
            return w
    return None


def soltar_foco():
    for w in tela().walk():
        if isinstance(w, TextInput) and w.focus:
            w.focus = False


class Roteiro:
    def __init__(self, passos):
        self.passos = passos
        self.i = 0

    def rodar(self, *_):
        if self.i >= len(self.passos):
            return
        espera, fn = self.passos[self.i]
        self.i += 1

        def _x(dt):
            try:
                fn()
            except Exception as e:
                LOG['erros'].append(f'passo {self.i}: {e}')
                print('[cenas] ERRO', e)
            self.rodar()
        Clock.schedule_once(_x, espera)


# ── roteiros ─────────────────────────────────────────────────────────
def roteiro_app():
    passos = []

    def ir(nome):
        return lambda: app().mudar_tela(nome)

    # +XP (carimbo)
    passos += [(0.3, ir('registro')), (1.8, soltar_foco),
               (0.4, lambda: (setattr(tela().ids.nome_input, 'text', 'Blusa manga longa'),
                              setattr(tela().ids.qtd_input, 'text', '75'), soltar_foco(), tela().adicionar_item())),
               (0.7, lambda: setattr(campo_do_popup(), 'text', '3')),
               (0.3, lambda: (fase('carimbo'), apertar('CONFIRMAR'))),
               (3.6, lambda: fase('fim carimbo'))]
    # apagar peca (iai)

    def _apagar_peca():
        t = tela()
        itens = list(t.ids.lista_container.children)
        btn = itens[len(itens) // 2]
        dado = next((r for r in app().registros if r[0] in btn.text), app().registros[0])
        t.confirmar_delete(dado, btn)
    passos += [(0.4, soltar_foco), (0.3, _apagar_peca), (0.7, lambda: (fase('iai'), apertar('DESINTEGRAR'))),
               (3.4, lambda: fase('fim iai'))]
    # finalizar turno (vitoria)
    passos += [(0.4, soltar_foco), (0.2, lambda: tela().finalizar_dia()),
               (0.8, lambda: (fase('vitoria'), apertar('SALVAR TURNO'))),
               (5.8, lambda: fase('fim vitoria'))]

    # subir de nivel (Progresso)
    def _prepara_nivel():
        from helpers import calcular_level
        a = app()
        lvl, prog, nec = calcular_level(a.total_xp)
        a.xp_anterior = max(0, a.total_xp - prog - 40)
    passos += [(0.3, _prepara_nivel), (0.1, lambda: (fase('nivel'), app().mudar_tela('progresso'))),
               (5.5, lambda: fase('fim nivel'))]
    # bater a meta (Ganhos)
    passos += [(0.3, ir('ganhos')), (1.8, soltar_foco),
               (0.3, lambda: (fase('meta'), tela().fechar_periodo())),
               (4.5, lambda: (fase('fim meta'), fechar_popups()))]

    # apagar periodo (X)
    def _x_periodo():
        bs = [w for w in tela().walk() if w.get_root_window() and hasattr(w, 'is_event_type')
              and w.is_event_type('on_release') and str(getattr(w, 'text', '')).strip() in ('X', '✕')
              or (w.get_root_window() and '✕' in str(getattr(w, 'text', '')) and hasattr(w, 'is_event_type')
                  and w.is_event_type('on_release'))]
        if not bs:
            LOG['erros'].append('X do periodo nao achado')
            return
        bs[0].dispatch('on_release')
    passos += [(0.8, soltar_foco), (0.2, _x_periodo), (0.7, lambda: (fase('x'), apertar('APAGAR'))),
               (3.4, lambda: fase('fim x'))]
    # WhatsApp (pergaminho)
    passos += [(0.3, ir('memorias')), (1.8, lambda: tela().abrir_detalhes_memoria(app().memorias[-1])),
               (0.8, lambda: (fase('pergaminho'), apertar('WHATSAPP'))),
               (4.4, lambda: (fase('fim pergaminho'), fechar_popups()))]
    # apagar o dia (estocada)
    passos += [(0.8, lambda: tela().abrir_detalhes_memoria(app().memorias[-1])),
               (0.8, lambda: apertar('APAGAR')),
               (0.7, lambda: (fase('estocada'), apertar('APAGAR'))),
               (3.6, lambda: (fase('fim estocada'), fechar_popups()))]
    # WIPE
    passos += [(0.8, lambda: tela().confirmar_wipe()),
               (0.8, lambda: (fase('wipe'), apertar('FORMATAR'))),
               (10.5, lambda: fase('fim wipe')), (0.5, fim)]
    Roteiro(passos).rodar()


def roteiro_telas():
    """Uma foto parada de cada tela e de cada aviso."""
    def ir(nome):
        return lambda: app().mudar_tela(nome)

    def focar(nome_id):
        return lambda: setattr(tela().ids[nome_id], 'focus', True)

    def _apagar_peca():
        t = tela()
        itens = list(t.ids.lista_container.children)
        btn = itens[len(itens) // 2]
        dado = next((r for r in app().registros if r[0] in btn.text), app().registros[0])
        t.confirmar_delete(dado, btn)

    def _x_periodo():
        for w in tela().walk():
            if (w.get_root_window() and hasattr(w, 'is_event_type') and w.is_event_type('on_release')
                    and str(getattr(w, 'text', '')).strip() in ('X', '\u2715')):
                w.dispatch('on_release')
                return
        LOG['erros'].append('X do periodo nao achado')

    def _calc():
        t = tela()
        for ch in ('1', '2', '5', '0', '*', '3', '=', '8', '4', '6', '/', '3'):
            t.apertar(ch)

    passos = [
        (0.5, lambda: foto('01-menu')),
        (0.3, ir('registro')), (2.0, soltar_foco), (0.4, lambda: foto('02-registro')),
        (0.3, focar('nome_input')), (0.8, lambda: foto('03-registro-teclado-letras')),
        (0.2, lambda: setattr(tela().ids.nome_input, 'text', 'Blusa manga longa')),
        (0.3, focar('qtd_input')), (0.8, lambda: foto('04-registro-teclado-numeros')),
        (0.2, lambda: (setattr(tela().ids.qtd_input, 'text', '75'), soltar_foco(), tela().adicionar_item())),
        (0.8, lambda: foto('05-aviso-xp')),
        (0.2, lambda: setattr(campo_do_popup(), 'text', '3')), (0.3, lambda: apertar('CONFIRMAR')),
        (4.2, soltar_foco), (0.5, lambda: foto('06-registro-com-pecas')),
        (0.3, _apagar_peca), (0.8, lambda: foto('07-aviso-apagar-peca')), (0.2, lambda: apertar('CANCELAR')),
        (0.6, lambda: tela().finalizar_dia()), (0.9, lambda: foto('08-aviso-salvar-turno')),
        (0.2, lambda: apertar('SALVAR TURNO')), (5.5, lambda: foto('09-registro-vazio')),
        (0.3, ir('memorias')), (2.2, lambda: foto('10-memorias')),
        (0.3, lambda: tela().abrir_detalhes_memoria(app().memorias[-1])),
        (0.9, lambda: foto('11-memoria-do-dia')), (0.2, fechar_popups),
        (0.6, lambda: tela().confirmar_wipe()), (0.9, lambda: foto('12-aviso-wipe')),
        (0.2, lambda: apertar('CANCELAR')),
        (0.6, ir('progresso')), (3.2, lambda: foto('13-progresso')),
        (0.3, ir('ganhos')), (2.2, soltar_foco), (0.4, lambda: foto('14-ganhos')),
        (0.3, lambda: tela().fechar_periodo()), (5.5, lambda: foto('15-ganhos-resultado')),
        (0.2, fechar_popups), (0.9, lambda: foto('16-ganhos-fechado')),
        (0.3, _x_periodo), (0.9, lambda: foto('17-aviso-apagar-periodo')), (0.2, lambda: apertar('CANCELAR')),
        (0.6, ir('calculadora')), (1.6, _calc), (0.6, lambda: foto('18-calculadora')),
        (0.3, ir('menu')), (1.6, lambda: apertar('TROCAR SENHA')), (0.9, lambda: foto('19-aviso-trocar-senha')),
        (0.3, fechar_popups), (0.6, fim),
    ]
    Roteiro(passos).rodar()


TEXTO_ZAP = '''[05/10/2026, 17:32] Kirito: Camisa polo 180
[05/10/2026, 17:33] Kirito: Calça jeans 95
[05/10/2026, 17:40] Chefe: beleza, amanhã tem mais
[06/10/2026, 17:41] Kirito: 120 bermuda
[06/10/2026, 17:42] Kirito: vestido longo - 60 un
[07/10/2026, 17:30] Kirito: Jaqueta corta-vento 40
camisa 2 bolsos 150
[07/10/2026, 17:31] Kirito: total 190
[08/10/2026, 18:02] Kirito: 📋 *PRODUÇÃO DO DIA*
📅 08/10/2026 (quinta)

🧵 Regata — *210*
🧵 Short — *1.050*

✅ *TOTAL: 1.260 peças*
[09/10/2026, 17:45] Kirito: Camisa polo 200
[09/10/2026, 17:46] Kirito: chego 7 horas amanhã'''


def roteiro_zap():
    """COLAR DO WHATSAPP de ponta a ponta, conferindo os dados no fim."""
    import telas.registro as TR
    TR.ler_area_de_transferencia = lambda: TEXTO_ZAP
    antes = {'memorias': len(app().memorias), 'registros': len(app().registros), 'xp': app().total_xp}

    def _tirar_uma():
        for w in popup().walk():
            if 'Vestido longo' in str(getattr(w, 'text', '')) and hasattr(w, 'is_event_type')                     and w.is_event_type('on_release'):
                w.dispatch('on_release')
                return
        LOG['erros'].append('zap: peça para tirar nao achada')

    def _confere():
        a = app()
        novas = a.memorias[antes['memorias']:]
        LOG['zap'] = {
            'turnos_novos': [[m['data'].split()[0], m['total'], m['xp'], [list(i) for i in m['itens']]]
                             for m in novas],
            'registros_depois': len(a.registros), 'xp_ganho': a.total_xp - antes['xp'],
            'streak': a.streak, 'ultima_data': a.ultima_data}
        print('[cenas] zap', json.dumps(LOG['zap'], ensure_ascii=False))

    passos = [
        (0.3, lambda: app().mudar_tela('registro')), (2.0, soltar_foco),
        (0.4, lambda: foto('z1-registro-com-botao')),
        (0.3, lambda: tela().colar_whatsapp()), (0.9, lambda: foto('z2-achado')),
        (0.2, _tirar_uma), (0.5, lambda: foto('z3-tirou-uma')),
        (0.2, lambda: apertar('CONTINUAR')), (1.0, lambda: setattr(campo_do_popup(), 'text', '3')),
        (0.4, lambda: foto('z4-xp')), (0.2, lambda: apertar('CONFIRMAR')),
        (1.6, soltar_foco), (0.5, lambda: foto('z5-lista')),
        (0.3, lambda: tela().finalizar_dia()), (0.9, lambda: foto('z6-resumo')),
        (0.2, lambda: apertar('SALVAR TURNO')), (5.5, _confere),
        (0.2, lambda: app().mudar_tela('memorias')), (2.4, lambda: foto('z7-memorias')),
        (0.4, fim),
    ]
    Roteiro(passos).rodar()


def roteiro_meta():
    """As telas das METAS: a faixa HOJE do registro, o painel da meta, um
    lote novo (com a festa se passar da meta) e a tela de ganhos."""
    def ir(nome):
        return lambda: app().mudar_tela(nome)

    def lote():
        t = tela()
        t.ids.nome_input.text = 'Short'
        t.ids.qtd_input.text = '40'
        soltar_foco()
        t.adicionar_item()
    passos = [(0.3, ir('registro')), (2.2, soltar_foco), (0.4, lambda: foto('m1-registro')),
              (0.3, lambda: tela().abrir_meta()), (1.4, lambda: foto('m2-painel-meta')), (0.3, fechar_popups),
              (0.8, lote), (0.8, lambda: setattr(campo_do_popup(), 'text', '3')),
              (0.3, lambda: apertar('CONFIRMAR')), (1.0, soltar_foco), (2.5, lambda: foto('m3-registro-depois')),
              (0.6, ir('ganhos')), (2.4, soltar_foco), (0.5, lambda: foto('m4-ganhos')),
              # fechar com pecas nao finalizadas: o aviso; finaliza o dia e ai fecha
              (0.3, lambda: tela().fechar_periodo()), (1.0, lambda: foto('m5-aviso-finalizar')),
              (0.3, fechar_popups), (0.4, ir('registro')), (2.0, lambda: tela().finalizar_dia()),
              (0.9, lambda: apertar('SALVAR TURNO')), (5.5, ir('ganhos')), (2.4, soltar_foco),
              (0.3, lambda: tela().fechar_periodo()), (5.0, lambda: foto('m6-ganhos-resultado')),
              (0.3, fechar_popups), (0.6, lambda: foto('m7-ganhos-fechado')), (0.4, fim)]
    Roteiro(passos).rodar()


def roteiro_varre():
    """Casos extremos das cenas novas (fotos): guardar o turno, a carta do
    WhatsApp e o WIPE com muita ou pouca coisa na tela."""
    def ir(nome):
        return lambda: app().mudar_tela(nome)

    def fotos(nome, n, cada=0.45):
        return [(cada, lambda i=i: foto('%s-%d' % (nome, i))) for i in range(n)]
    passos = [(0.3, ir('registro')), (1.8, soltar_foco), (0.3, lambda: foto('registro')),
              (0.3, lambda: tela().finalizar_dia()),
              (0.8, lambda: (fase('guardar'), apertar('SALVAR TURNO')))] + fotos('guardar', 12)
    passos += [(0.6, ir('memorias')), (1.8, lambda: foto('memorias')),
               (0.3, lambda: tela().abrir_detalhes_memoria(app().memorias[-2] if len(app().memorias) > 1
                                                           else app().memorias[-1])),
               (0.8, lambda: (fase('carta'), apertar('WHATSAPP')))] + fotos('carta', 9)
    passos += [(1.2, fechar_popups), (0.6, fechar_popups), (0.6, lambda: tela().confirmar_wipe()),
               (0.8, lambda: (fase('wipe'), apertar('FORMATAR')))] + fotos('wipe', 16) + \
              [(2.0, lambda: foto('depois-do-wipe')), (0.4, fim)]
    Roteiro(passos).rodar()


def esperar_menu(dt):
    if app().root.ids.sm.current != 'menu':
        Clock.schedule_once(esperar_menu, 0.05)
        return
    fase('menu')
    Clock.schedule_once(lambda dt: {'telas': roteiro_telas, 'zap': roteiro_zap, 'varre': roteiro_varre, 'meta': roteiro_meta}.get(CENA, roteiro_app)(), 1.0)


def roteiro_pin():
    fase('pin')

    def _digita(txt):
        c = None
        for topo in Window.children:
            for w in topo.walk():
                if isinstance(w, TextInput):
                    c = w
        if c is not None:
            c.text = txt
            c.dispatch('on_text_validate')
    passos = [(3.6, lambda: foto('20-senha')),
              (0.4, lambda: (fase('pin errado'), _digita('1111'))),
              (1.2, lambda: foto('21-senha-errada')),
              (2.3, lambda: (fase('pin certo'), _digita('2004'))),
              (3.0, lambda: fase('fim pin')), (0.3, fim)]
    Roteiro(passos).rodar()


def inicio(dt):
    SIM[0] = _tempo_real()
    GRAVA[0] = True
    if CENA == 'pin':
        Clock.schedule_once(lambda dt: roteiro_pin(), 0.5)
    else:
        fase('inicio')
        Clock.schedule_once(esperar_menu, 0.5)
    Clock.schedule_once(fim, 200)


Clock.schedule_once(inicio, 0.3)
main.TraveteApp().run()
