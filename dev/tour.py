"""Tour completo do app real (desktop) com dados de exemplo: PIN, titulo,
menu, registro (adicionar/apagar/finalizar), memorias (detalhe), progresso,
ganhos, calculadora e WIPE. Captura quadros (se FOTOS=1) e mede desempenho
(tempo de cada quadro, custo de montar as poses do Kirito).

uso: python -u tour.py LARG ALT SAIDA [densidade]
"""
import os
import sys
import json
import time
import random

LARG, ALT, SAIDA = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
DENS = sys.argv[4] if len(sys.argv) > 4 else None
FOTOS = os.environ.get('FOTOS', '1') == '1'
REPO = os.environ.get('TOUR_REPO') or os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
os.makedirs(SAIDA, exist_ok=True)
if DENS:
    os.environ['KIVY_METRICS_DENSITY'] = DENS
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_LOG_MODE', 'PYTHON')

# ── dados de exemplo (antes do app carregar) ─────────────────────────
random.seed(7)
pasta_app = os.path.join(os.environ['APPDATA'], 'travete')
os.makedirs(pasta_app, exist_ok=True)
nomes = ['Camisa polo', 'Calca jeans', 'Vestido longo', 'Bermuda', 'Jaqueta corta-vento',
         'Saia plissada', 'Blusa manga longa']
memorias = []
dias = [(d, m) for m, dd in ((8, range(18, 32)), (9, range(1, 25))) for d in dd]
escolhidos = sorted(random.sample(dias, 10), key=lambda x: (x[1], x[0]))
for (d, m) in escolhidos:
    itens = []
    for _ in range(random.randint(2, 4)):
        q = random.randint(60, 260)
        xp = random.choice((2, 3, 4)) * q
        itens.append([random.choice(nomes), str(q), xp])
    memorias.append({'data': f'{d:02d}/{m:02d}/2026  {random.randint(14, 19)}:{random.randint(0, 59):02d}',
                     'total': sum(int(i[1]) for i in itens), 'xp': sum(i[2] for i in itens),
                     'itens': itens})
registros = [['Camisa polo', '180', 540], ['Calca jeans', '95', 380], ['Vestido longo', '60', 240]]
dados = {
    'memorias': memorias, 'total_geral': sum(m['total'] for m in memorias), 'meta_geral': 10000,
    'total_xp': sum(m['xp'] for m in memorias) + sum(r[2] for r in registros),
    'registros': registros, 'streak': 6, 'melhor_dia': max(m['total'] for m in memorias),
    'ultima_data': '24/09/2026',
    'periodos_ganhos': [
        {'tipo': 'semanal', 'data_inicio': '01/09/2026', 'data_fim': '07/09/2026',
         'total_pecas': 3320, 'total_ganho': 846.0},
        {'tipo': 'semanal', 'data_inicio': '14/09/2026', 'data_fim': None,
         'total_pecas': 0, 'total_ganho': 0.0}],
    'config_ganhos': {'valor_base': 0.25, 'valor_bonus': 0.30, 'meta_bonus': 3000,
                      'tipo_periodo': 'semanal'},
}
with open(os.path.join(pasta_app, 'dados.json'), 'w', encoding='utf-8') as f:
    json.dump(dados, f, ensure_ascii=False)

from kivy.config import Config  # noqa: E402
Config.set('graphics', 'width', str(LARG))
Config.set('graphics', 'height', str(ALT))
Config.set('graphics', 'resizable', '0')
Config.set('input', 'mouse', 'mouse,disable_multitouch')

sys.path.insert(0, REPO)
os.chdir(REPO)
import main  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.uix.popup import Popup  # noqa: E402
from kivy.uix.textinput import TextInput  # noqa: E402
from kivy.app import App  # noqa: E402
import som  # noqa: E402
import kirito as K  # noqa: E402

Window.size = (LARG, ALT)
T0 = [None]
LOG = {'quadros': [], 'sons': [], 'erros': [], 'fases': [], 'dt': [], 'montar': [],
       'tamanho': [LARG, ALT], 'dens': DENS}

# WhatsApp: guarda a mensagem em vez de mexer na area de transferencia do PC
import exportar  # noqa: E402
LOG['whatsapp'] = []


def _copiar_falso(texto):
    LOG['whatsapp'].append(texto)
    return True


exportar._copiar = _copiar_falso


def agora():
    return time.time() - T0[0] if T0[0] else 0.0


def fase(nome):
    LOG['fases'].append([round(agora(), 3), nome])
    print(f'[tour] {agora():6.2f}s {nome}')


# ── sons: registra em vez de tocar ───────────────────────────────────
def _tocar(acao):
    fonte = 'gravado' if som._gravacao(acao) else ('sintese' if acao in som._RECEITAS else 'NENHUM')
    LOG['sons'].append([round(agora(), 3), acao, fonte])


_tocar.__name__ = 'tocar'
som.tocar = _tocar
for _n in dir(som):
    if _n.startswith('tocar_'):
        setattr(som, _n, (lambda a: (lambda: _tocar(a)))(_n[len('tocar_'):]))
som.precarregar = lambda acoes: None

# ── desempenho: custo de montar pose (Python puro) e tempo de quadro ─
_montar = K.montar


def _montar_medido(p, **kw):
    t = time.perf_counter()
    r = _montar(p, **kw)
    LOG['montar'].append([round(agora(), 3), round((time.perf_counter() - t) * 1000, 3),
                          1 if kw.get('rapido') else 0, str(kw.get('camada')),
                          repr(K._chave(p))[:400] if os.environ.get('MONTAR_CHAVE') else ''])
    return r


K.montar = _montar_medido
_ult = [None]


def _quadro(dt):
    t = time.perf_counter()
    if _ult[0] is not None:
        LOG['dt'].append([round(agora(), 3), round((t - _ult[0]) * 1000, 2)])
    _ult[0] = t


# ── capturas ─────────────────────────────────────────────────────────
def foto(rotulo):
    if not FOTOS:
        return
    try:
        caminho = Window.screenshot(name=os.path.join(SAIDA, 'q.png'))
        LOG['quadros'].append([round(agora(), 3), rotulo, os.path.basename(caminho)])
    except Exception as e:
        LOG['erros'].append(f'foto {rotulo}: {e}')


def rajada(rotulo, dur, passo):
    for i in range(int(dur / passo)):
        Clock.schedule_once(lambda dt, i=i: foto(f'{rotulo} {i * passo:.2f}s'), i * passo)


# ── utilidades de roteiro ────────────────────────────────────────────
def popup_aberto():
    for w in Window.children:
        if isinstance(w, Popup):
            return w
    return None


def campo(pop=None):
    pop = pop or popup_aberto()
    if pop is None:
        return None
    for x in pop.walk():
        if isinstance(x, TextInput):
            return x
    return None


def botao(texto, pop=None):
    pop = pop or popup_aberto()
    if pop is None:
        return None
    for x in pop.walk():
        if hasattr(x, 'text') and texto in str(getattr(x, 'text', '')) and hasattr(x, 'dispatch') \
                and x.__class__.__name__.startswith('Botao'):
            return x
    return None


def apertar(texto):
    b = botao(texto)
    if b is None:
        LOG['erros'].append(f'botao "{texto}" nao achado')
        return
    b.dispatch('on_press')
    b.dispatch('on_release')


def tela():
    return App.get_running_app().root.ids.sm.current_screen


def ir(destino):
    fase(f'-> {destino}')
    App.get_running_app().mudar_tela(destino)
    rajada(f'trans-{destino}', 0.9, 0.05)


class Roteiro:
    """Passos em sequencia com espera (s) entre eles."""

    def __init__(self, passos):
        self.passos = list(passos)

    def rodar(self, *_):
        if not self.passos:
            return
        espera, fn = self.passos.pop(0)

        def _x(dt):
            try:
                fn()
            except Exception as e:
                LOG['erros'].append(f'passo {getattr(fn, "__name__", fn)}: {e!r}')
                print('[tour] ERRO', e)
            self.rodar()
        Clock.schedule_once(_x, espera)


# ── PIN e titulo ─────────────────────────────────────────────────────
def _digitar(txt, cada=0.35, depois=None):
    for i, ch in enumerate(txt):
        def _d(dt, ch=ch):
            inp = campo()
            if inp is not None:
                inp.text = inp.text + ch
        Clock.schedule_once(_d, i * cada)
    if depois:
        Clock.schedule_once(lambda dt: depois(), len(txt) * cada + 0.05)


def _enviar():
    inp = campo()
    if inp is not None:
        inp.dispatch('on_text_validate')


def passo_pin(dt):
    if campo() is None:
        Clock.schedule_once(passo_pin, 0.1)
        return
    fase('pin')
    rajada('pin-entra', 1.9, 0.1)
    Clock.schedule_once(lambda dt: setattr(campo(), 'focus', True) if campo() else None, 1.3)
    Clock.schedule_once(lambda dt: _digitar('12'), 2.05)
    Clock.schedule_once(lambda dt: _digitar('99', cada=0.1, depois=_enviar), 3.4)
    Clock.schedule_once(lambda dt: fase('pin-erro'), 3.6)
    Clock.schedule_once(lambda dt: rajada('pin-erro', 2.2, 0.1), 3.6)
    Clock.schedule_once(lambda dt: _digitar('2004', cada=0.12, depois=_enviar), 6.2)
    Clock.schedule_once(lambda dt: fase('pin-certo'), 6.7)
    Clock.schedule_once(lambda dt: rajada('pin-certo', 1.8, 0.1), 6.7)
    Clock.schedule_once(esperar_titulo, 8.0)


def esperar_titulo(dt):
    try:
        lt = App.get_running_app().root.ids.sm.get_screen('loading')
        if getattr(lt, '_cena', None) is not None:
            fase('titulo')
            jan = os.environ.get('PROF_JANELA')        # "ini,fim": perfila so esse trecho do titulo
            if jan:
                import cProfile
                pr = cProfile.Profile()
                a, b = (float(v) for v in jan.split(','))
                Clock.schedule_once(lambda dt: pr.enable(), a)
                Clock.schedule_once(lambda dt: (pr.disable(), pr.dump_stats(os.path.join(SAIDA, 'janela.out'))), b)
            dens = os.environ.get('TITULO_DENSO')      # "ini,fim,passo": trecho com mais fotos
            if dens:
                a, b, c = (float(v) for v in dens.split(','))
                rajada('titulo', a, 0.25)
                Clock.schedule_once(lambda dt: rajada('tdenso', b - a, c), a)
                Clock.schedule_once(lambda dt: rajada('tfim', float(os.environ.get('TITULO_FIM', '22')) - b, 0.25), b)
            else:
                rajada('titulo', 19.5, 0.1)
            Clock.schedule_once(esperar_menu, 3.0)
            return
    except Exception as e:
        LOG['erros'].append(f'titulo: {e}')
    Clock.schedule_once(esperar_titulo, 0.05)


def esperar_menu(dt):
    if App.get_running_app().root.ids.sm.current != 'menu':
        Clock.schedule_once(esperar_menu, 0.05)
        return
    fase('menu')
    if os.environ.get('SO_TITULO') == '1':
        Clock.schedule_once(fim, 0.5)
        return
    rajada('menu', 1.2, 0.1)
    Clock.schedule_once(lambda dt: tour(), 2.0)


# ── tour pelas telas ─────────────────────────────────────────────────
def tour():
    app = App.get_running_app()
    estado = {}

    def reg_adicionar():
        fase('registro-add')
        t = tela()
        t.ids.nome_input.text = 'Jaqueta corta-vento'
        t.ids.qtd_input.text = '140'
        t.adicionar_item()

    def reg_xp():
        inp = campo()
        if inp is not None:
            inp.text = '3'
        foto('popup-xp')
        apertar('CONFIRMAR')
        rajada('registro-xp', 1.3, 0.1)

    def reg_apagar():
        fase('registro-apagar')
        t = tela()
        itens = list(t.ids.lista_container.children)
        alvo = itens[len(itens) // 2]
        dado = next((r for r in app.registros if r[0] in alvo.text), app.registros[0])
        t.confirmar_delete(dado, alvo)

    def reg_confirma():
        foto('popup-apagar')
        apertar('DESINTEGRAR')
        rajada('fatiar', 1.6, 0.05)

    def reg_finalizar():
        fase('registro-finalizar')
        tela().finalizar_dia()

    def reg_salvar_turno():
        foto('popup-turno')
        apertar('SALVAR TURNO')
        rajada('finalizado', 0.8, 0.1)

    def mem_detalhe():
        fase('memorias-detalhe')
        tela().abrir_detalhes_memoria(app.memorias[-1])
        rajada('mem-detalhe', 0.6, 0.1)

    def mem_zap():
        fase('whatsapp')
        apertar('WHATSAPP')

    def mem_fecha():
        apertar('FECHAR')

    def ganhos_config():
        fase('ganhos-config')
        t = tela()
        t.ids.inp_valor_bonus.text = '0,35'
        t.ids.inp_meta_bonus.text = '400'
        t.salvar_config()
        LOG['cfg_depois'] = dict(app.config_ganhos)

    def ganhos_fechar():
        fase('ganhos-fechar')
        tela().fechar_periodo()
        LOG['periodos'] = [dict(p) for p in app.periodos_ganhos]

    def calc():
        fase('calculadora-conta')
        t = tela()
        for ch in '1', '2', '*', '3', '5':
            t.apertar(ch)
        foto('calc-digitado')
        t.apertar('=')
        rajada('calc', 0.6, 0.1)

    def wipe():
        fase('wipe')
        tela().confirmar_wipe()

    def wipe_confirma():
        foto('popup-wipe')
        apertar('FORMATAR')
        rajada('wipe', 9.0, 0.08)

    passos = [
        (0.0, lambda: ir('registro')),
        (1.6, lambda: rajada('registro', 1.0, 0.1)),
        (1.4, reg_adicionar), (0.8, reg_xp),
        (1.8, reg_apagar), (0.6, reg_confirma),
        (3.0, reg_finalizar), (0.7, reg_salvar_turno),
        (1.5, lambda: ir('memorias')),
        (1.5, lambda: rajada('memorias', 1.2, 0.1)),
        (1.6, mem_detalhe), (1.0, mem_zap), (0.8, lambda: foto('whatsapp-aviso')),
        (0.6, lambda: apertar('OK')), (0.8, mem_fecha),
        (1.0, lambda: ir('progresso')),
        (1.2, lambda: rajada('progresso', 2.6, 0.1)),
        (3.0, lambda: ir('ganhos')),
        (1.2, lambda: rajada('ganhos', 1.4, 0.1)),
        (1.6, ganhos_config), (0.9, lambda: foto('ganhos-aviso')),
        (1.5, ganhos_fechar), (0.8, lambda: foto('ganhos-popup')), (0.4, lambda: apertar('OK')),
        (0.8, lambda: foto('ganhos-depois')),
        (2.0, lambda: ir('calculadora')),
        (1.3, calc),
        (1.5, lambda: ir('memorias')),
        (1.8, wipe), (0.7, wipe_confirma),
        (10.0, lambda: fim(0)),
    ]
    Roteiro(passos).rodar()


_acabou = [False]


def fim(dt):
    if _acabou[0]:
        return
    _acabou[0] = True
    with open(os.path.join(SAIDA, 'log.json'), 'w', encoding='utf-8') as f:
        json.dump(LOG, f, ensure_ascii=False)
    print('[tour] fim', len(LOG['quadros']), 'quadros,', len(LOG['erros']), 'erros')
    App.get_running_app().stop()


def inicio(dt):
    T0[0] = time.time()
    foto('descarte')
    Clock.schedule_interval(_quadro, 0)
    Clock.schedule_once(passo_pin, 0.5)
    Clock.schedule_once(fim, 170.0)


Clock.schedule_once(inicio, 0.6)
if os.environ.get('PROF') == '1':
    import cProfile
    cProfile.run('main.TraveteApp().run()', os.path.join(SAIDA, 'prof.out'))
else:
    main.TraveteApp().run()
