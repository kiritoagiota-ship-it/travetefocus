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
if os.environ.get('MEMORIAS'):
    import datetime as _dt
    _n = int(os.environ['MEMORIAS'])
    _d0 = _dt.date(2026, 9, 27) - _dt.timedelta(days=_n)
    escolhidos = [((_d0 + _dt.timedelta(days=i)).day, (_d0 + _dt.timedelta(days=i)).month) for i in range(_n)]
    _anos = [(_d0 + _dt.timedelta(days=i)).year for i in range(_n)]
else:
    escolhidos = sorted(random.sample(dias, 10), key=lambda x: (x[1], x[0]))
    _anos = [2026] * len(escolhidos)
for (d, m), _ano in zip(escolhidos, _anos):
    itens = []
    for _ in range(random.randint(2, 4)):
        q = random.randint(60, 260)
        xp = random.choice((2, 3, 4)) * q
        itens.append([random.choice(nomes), str(q), xp])
    memorias.append({'data': f'{d:02d}/{m:02d}/{_ano}  {random.randint(14, 19)}:{random.randint(0, 59):02d}',
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
if os.environ.get('RAPIDA') == '1':          # senha ainda valendo: entrada rapida
    with open(os.path.join(pasta_app, '.tf_session'), 'w') as f:
        f.write(str(time.time()))

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
    LOG['montar'].append([round(agora(), 3), round((time.perf_counter() - t) * 1000, 3)])
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
    if os.environ.get('PIN_ERRADO') == '3':             # erra a senha 3 vezes
        fase('pin-3-erros')
        Clock.schedule_once(lambda dt: _digitar('1111', cada=0.1, depois=_enviar), 0.5)
        Clock.schedule_once(lambda dt: _digitar('2222', cada=0.1, depois=_enviar), 2.0)
        Clock.schedule_once(lambda dt: _digitar('3333', cada=0.1, depois=_enviar), 3.5)
        # a senha certa durante o bloqueio tem de ser ignorada
        Clock.schedule_once(lambda dt: _digitar('2004', cada=0.1, depois=_enviar), 5.5)
        Clock.schedule_once(lambda dt: foto('bloqueado'), 7.5)
        def _onde(dt):
            sm = App.get_running_app().root.ids.sm
            fase('tela depois de 3 erros: ' + sm.current)
            foto('depois-3-erros')
        Clock.schedule_once(_onde, 9.0)
        Clock.schedule_once(fim, 10.0)
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
    if os.environ.get('PULAR'):
        Clock.schedule_once(_teste_pular, 6.7)
        return
    Clock.schedule_once(lambda dt: roteiro_teste(), 8.0)


def tocar_tela(x, y):
    """Um toque de verdade (passa pela janela como o dedo)."""
    from kivy.input.motionevent import MotionEvent
    from kivy.base import EventLoop

    class _Toque(MotionEvent):
        def depack(self, args):
            self.sx, self.sy = args
            self.profile = ['pos']
            super().depack(args)
    t = _Toque('teste', 1, (x / float(Window.width), y / float(Window.height)),
               is_touch=True, type_id='touch')
    EventLoop.post_dispatch_input('begin', t)
    EventLoop.post_dispatch_input('end', t)


def _teste_pular(dt=0):
    """PULAR=s: espera a abertura liberar o pulo, toca na tela s segundos
    depois e confere se foi para o menu."""
    lt = App.get_running_app().root.ids.sm.get_screen('loading')
    if not getattr(lt, '_pular_ok', False):
        Clock.schedule_once(_teste_pular, 0.05)
        return
    fase('pular liberado')
    Clock.schedule_once(lambda dt: foto('dica-pular'), 0.6)

    def _toque(dt):
        fase('toque para pular')
        tocar_tela(Window.width / 2, Window.height / 2)
        rajada('pulou', 2.6, 0.1)
        Clock.schedule_once(lambda dt: fase('tela depois de pular: ' + App.get_running_app().root.ids.sm.current), 2.7)
        Clock.schedule_once(fim, 3.0)
    Clock.schedule_once(_toque, float(os.environ['PULAR']))


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
            t.add_texto(ch)
        foto('calc-digitado')
        t.calcular()
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




# ── roteiro de teste (calculadora, registro, teclados, menu) ─────────
def teclado_aberto():
    for w in Window.children:
        if w.__class__.__name__.startswith('Teclado'):
            return w
    return None


def teclar(txt):
    kb = teclado_aberto()
    if kb is None:
        LOG['erros'].append('teclado nao abriu')
        return
    for tk in txt.split('|'):
        kb._press(tk)


def roteiro_teste():
    import os as _os
    passos = []
    casos = _os.environ.get('CALC', '')
    passos.append((0.1, lambda: ir('calculadora')))
    for i, caso in enumerate(filter(None, casos.split(';'))):
        def _f(caso=caso, i=i):
            t = tela()
            t.apertar('C')
            for ch in caso.rstrip('='):
                t.apertar('()' if ch in '()' else ch)
            Clock.schedule_once(lambda dt: foto(f'calc{i} digitado {caso}'), 0.35)
            if caso.endswith('='):
                Clock.schedule_once(lambda dt: t.apertar('='), 0.5)
                Clock.schedule_once(lambda dt: foto(f'calc{i} resultado'), 1.1)
        passos.append((1.4, _f))
    if _os.environ.get('REGISTRO') == '1':
        passos.append((1.6, lambda: ir('registro')))
        passos.append((1.4, lambda: setattr(tela().ids.nome_input, 'focus', True)))
        passos.append((0.6, lambda: foto('registro-teclado-sugestoes')))
        passos.append((0.2, lambda: teclar('C|A')))
        passos.append((0.3, lambda: foto('registro-digitou-CA')))
        passos.append((0.2, lambda: teclar('L|C|ACENTO|A')))
        passos.append((0.3, lambda: foto('registro-CALCA-com-cedilha')))
        passos.append((0.2, lambda: teclar('CLR|B|L|U|S|A|ACENTO|O|ACENTO|ACENTO')))
        passos.append((0.3, lambda: foto('registro-acentos')))
        def _lote():
            t = tela()
            t.ids.qtd_input.text = '120'
            t.adicionar_item()
        passos.append((0.3, _lote))
        passos.append((0.9, lambda: foto('popup-xp')))
        def _foco_xp():
            p = popup_aberto()
            if p is None:
                LOG['erros'].append('popup xp nao abriu')
                return
            from kivy.uix.textinput import TextInput
            for w in p.walk():
                if isinstance(w, TextInput):
                    w.focus = True
        passos.append((0.2, _foco_xp))
        passos.append((0.8, lambda: foto('popup-xp-teclado')))
        passos.append((0.2, lambda: teclar('4')))
        passos.append((0.4, lambda: foto('popup-xp-digitado')))
    if _os.environ.get('ABRIR'):
        for tela_n in _os.environ['ABRIR'].split(','):
            passos.append((2.5, lambda tela_n=tela_n: ir(tela_n)))
            passos.append((2.5, lambda tela_n=tela_n: foto('aberta ' + tela_n)))
    if _os.environ.get('MENU') == '1':
        passos.append((1.0, lambda: ir('menu')))
        passos.append((1.5, lambda: foto('menu')))
        passos.append((0.2, lambda: App.get_running_app().alternar_vibracao()))
        passos.append((0.5, lambda: foto('menu-vibracao-desligada')))
        passos.append((0.2, lambda: App.get_running_app().alternar_vibracao()))
    if _os.environ.get('ROLAR') == '1':               # memorias: carrega mais ao rolar
        def _conta(rot):
            t = tela()
            fase(f'{rot}: {len(t.ids.memorias_container.children)} itens na lista, '
                 f'faltam {len(getattr(t, "_pendentes", []))}, scroll_y={t.ids.lista_scroll.scroll_y:.3f}')
        passos.append((0.2, lambda: _conta('abriu')))
        passos.append((0.2, lambda: setattr(tela().ids.lista_scroll, 'scroll_y', 0)))
        passos.append((0.8, lambda: _conta('rolou ate o fim')))
        passos.append((0.1, lambda: foto('memorias-carregou-mais')))
    if _os.environ.get('SENHA') == '1':               # trocar a senha pelo menu
        def _campos():
            from kivy.uix.textinput import TextInput
            p = popup_aberto()
            cs = [w for w in p.walk() if isinstance(w, TextInput)] if p else []
            return sorted(cs, key=lambda w: -w.to_window(w.x, w.y)[1])   # de cima para baixo
        def _botao(txt):
            p = popup_aberto()
            for w in (p.walk() if p else []):
                if getattr(w, 'text', None) == txt:
                    w.dispatch('on_release')
                    return
            LOG['erros'].append('botao nao achado: ' + txt)
        def _preencher(a, n, c):
            cs = _campos()
            if len(cs) != 3:
                LOG['erros'].append(f'campos da senha: {len(cs)}')
                return
            for w, v in zip(cs, (a, n, c)):
                w.text = v
            _botao('SALVAR')
        passos.append((1.0, lambda: ir('menu')))
        passos.append((1.5, lambda: foto('menu')))
        passos.append((0.2, lambda: App.get_running_app().trocar_senha()))
        passos.append((0.8, lambda: foto('senha-popup')))
        passos.append((0.2, lambda: setattr(_campos()[0], 'focus', True)))
        passos.append((0.8, lambda: foto('senha-teclado')))
        passos.append((0.2, lambda: _preencher('1111', '5555', '5555')))
        passos.append((0.15, lambda: foto('senha-atual-errada')))
        passos.append((0.6, lambda: _preencher('2004', '55', '55')))
        passos.append((0.5, lambda: foto('senha-curta')))
        passos.append((0.2, lambda: _preencher('2004', '5555', '5556')))
        passos.append((0.5, lambda: foto('senha-diferente')))
        passos.append((0.2, lambda: _preencher('2004', '5555', '5555')))
        passos.append((0.5, lambda: foto('senha-trocada')))
        def _confere():
            import seguranca
            fase(f"senha nova vale: {seguranca.pin_confere('5555')}, antiga vale: {seguranca.pin_confere('2004')}")
        passos.append((1.2, _confere))
    if _os.environ.get('FINALIZAR') == '1':           # data do turno
        def _data():
            from kivy.uix.textinput import TextInput
            p = popup_aberto()
            for w in (p.walk() if p else []):
                if isinstance(w, TextInput):
                    return w
        def _salvar():
            p = popup_aberto()
            for w in (p.walk() if p else []):
                if 'SALVAR TURNO' in str(getattr(w, 'text', '')):
                    w.dispatch('on_release')
                    return
            LOG['erros'].append('botao salvar turno nao achado')
        passos.append((1.0, lambda: ir('registro')))
        passos.append((1.4, lambda: fase(f'antes: {len(App.get_running_app().memorias)} turnos, sequencia {App.get_running_app().streak}')))
        passos.append((0.1, lambda: tela().finalizar_dia()))
        passos.append((0.8, lambda: foto('finalizar-popup')))
        passos.append((0.2, lambda: setattr(_data(), 'focus', True)))
        passos.append((0.8, lambda: foto('finalizar-teclado')))
        passos.append((0.1, lambda: setattr(_data(), 'text', '')))
        passos.append((0.1, lambda: teclar('3|1|0|2|2|0|2|6')))
        passos.append((0.3, lambda: fase('digitado: ' + _data().text)))
        passos.append((0.1, lambda: _salvar()))
        passos.append((0.15, lambda: foto('finalizar-data-invalida')))
        passos.append((0.6, lambda: fase('popup ainda aberto: ' + str(popup_aberto() is not None))))
        passos.append((0.1, lambda: teclar('CLR|2|6|0|9|2|0|2|6')))
        passos.append((0.3, lambda: fase('digitado: ' + _data().text)))
        passos.append((0.1, lambda: teclar('OK')))
        passos.append((0.4, lambda: _salvar()))
        passos.append((2.5, lambda: fase(f'depois: {len(App.get_running_app().memorias)} turnos, '
                                         f'sequencia {App.get_running_app().streak}, '
                                         f'ultima {App.get_running_app().ultima_data}')))
        passos.append((0.1, lambda: foto('finalizar-salvo')))
    if _os.environ.get('VAZA') == '1':                # toque "vazando" do teclado para o que esta embaixo
        estado = {}
        # como no celular: o campo com o teclado do app nao liga o teclado do
        # sistema (no PC o Kivy tiraria o foco a cada toque fora do campo)
        import efeitos as _ef
        _orig_bind = _ef.InputHolografico._bind_keyboard

        def _bind_como_android(self):
            if getattr(self, '_teclado_custom_ok', False):
                return
            _orig_bind(self)
        _ef.InputHolografico._bind_keyboard = _bind_como_android

        def _ret(w):
            x, y = w.to_window(w.x, w.y)
            return (x, y, x + w.width, y + w.height)

        def _corta(a, b):
            r = (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))
            return r if r[2] > r[0] and r[3] > r[1] else None

        def _no_vao(kb, alvos):
            """Ponto dentro do teclado, fora de qualquer tecla, em cima de um alvo."""
            from efeitos import _BotaoTecla
            teclas = [_ret(b) for b in kb.walk() if isinstance(b, _BotaoTecla)]
            k = _ret(kb)
            for y in range(int(k[1]) + 1, int(k[3]) - 1, 2):
                for x in range(int(k[0]) + 1, int(k[2]) - 1, 2):
                    if any(r[0] <= x <= r[2] and r[1] <= y <= r[3] for r in teclas):
                        continue
                    for nome, r in alvos:
                        if r[0] + 2 <= x <= r[2] - 2 and r[1] + 2 <= y <= r[3] - 2:
                            return (x, y, nome)
            return None

        # A) adicionar peca: lista cheia de pecas embaixo do teclado de letras
        def _encher():
            app = App.get_running_app()
            for i in range(12):
                app.registros.append([f'Peca teste {i}', str(10 + i), 30])
        passos.append((0.5, _encher))
        passos.append((0.5, lambda: ir('registro')))
        passos.append((1.8, lambda: foto('vaza-registro-teclado')))

        def _testa_registro():
            kb = teclado_aberto()
            if kb is None:
                LOG['erros'].append('vaza: teclado nao abriu no registro')
                return
            t = tela()
            chamados = estado.setdefault('apagar', [])
            orig = t.confirmar_delete
            t.confirmar_delete = lambda d, w, orig=orig: (chamados.append(d[0]), orig(d, w))
            sv = t.ids.lista_container.parent
            visivel = _ret(sv)
            alvos = []
            for w in t.ids.lista_container.children:
                r = _corta(_ret(w), visivel)
                if r:
                    alvos.append((w.text.strip()[:18], r))
            p = _no_vao(kb, alvos)
            fase(f'vaza registro: {len(alvos)} pecas visiveis; ponto no vao do teclado em cima de peca: {p}')
            if p:
                tocar_tela(p[0], p[1])
        passos.append((0.2, _testa_registro))
        passos.append((0.6, lambda: fase(f"vaza registro RESULTADO: tentou apagar={estado.get('apagar')}, "
                                         f"aviso de apagar aberto={popup_aberto() is not None}")))
        passos.append((0.1, lambda: foto('vaza-registro-depois')))
        passos.append((0.3, lambda: popup_aberto() and popup_aberto().dismiss()))

        def _tecla_digita():
            # a tecla de verdade continua digitando (toque no meio da tecla Q)
            kb = teclado_aberto()
            if kb is None:
                fase('vaza registro: teclado fechou (o aviso de apagar tinha aberto)')
                return
            from efeitos import _BotaoTecla
            q = next((b for b in kb.walk() if isinstance(b, _BotaoTecla) and b.text == 'Q'), None)
            estado['antes'] = tela().ids.nome_input.text
            r = _ret(q)
            tocar_tela((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
        passos.append((0.3, _tecla_digita))
        passos.append((0.3, lambda: fase(f"vaza registro: tecla Q digitou? antes='{estado.get('antes')}' "
                                         f"depois='{tela().ids.nome_input.text}'")))

        # B) memorias: detalhe do dia, teclado de numeros da data por cima dos botoes
        passos.append((0.6, lambda: ir('memorias')))
        passos.append((1.5, lambda: tela().abrir_detalhes_memoria(App.get_running_app().memorias[-1])))

        def _foco_data():
            p = popup_aberto()
            for w in (p.walk() if p else []):
                if isinstance(w, TextInput):
                    w.focus = True
                    return
            LOG['erros'].append('vaza: campo da data nao achado')
        passos.append((0.9, _foco_data))
        passos.append((0.9, lambda: foto('vaza-memoria-teclado')))

        def _testa_mem():
            kb, p = teclado_aberto(), popup_aberto()
            if kb is None or p is None:
                LOG['erros'].append(f'vaza memoria: teclado={kb is not None} popup={p is not None}')
                return
            botoes = [(w.text.strip(), _ret(w)) for w in p.walk()
                      if any(s in str(getattr(w, 'text', '')) for s in ('APAGAR', 'FECHAR', 'WHATSAPP'))]
            estado['n_mem'] = len(App.get_running_app().memorias)
            fase('vaza memoria: botoes ' + ', '.join(f"{n} y={int(r[1])}-{int(r[3])}" for n, r in botoes) +
                 f"; teclado y={int(_ret(kb)[1])}-{int(_ret(kb)[3])}")
            ponto = _no_vao(kb, botoes)
            fase(f'vaza memoria: ponto no vao do teclado em cima de botao: {ponto}')
            if ponto:
                tocar_tela(ponto[0], ponto[1])
        passos.append((0.2, _testa_mem))
        passos.append((1.6, lambda: fase(f"vaza memoria RESULTADO: popup ainda aberto={popup_aberto() is not None}, "
                                         f"turnos antes={estado.get('n_mem')} depois={len(App.get_running_app().memorias)}")))
        passos.append((0.1, lambda: foto('vaza-memoria-depois')))

        # C) ganhos: campos de valor com teclado de numeros, botoes embaixo
        passos.append((0.3, lambda: popup_aberto() and popup_aberto().dismiss()))
        passos.append((0.6, lambda: ir('ganhos')))
        passos.append((1.5, lambda: setattr(tela().ids.inp_valor_base, 'focus', True)))
        passos.append((0.9, lambda: foto('vaza-ganhos-teclado')))

        def _testa_ganhos():
            kb = teclado_aberto()
            if kb is None:
                LOG['erros'].append('vaza ganhos: teclado nao abriu')
                return
            from kivy.uix.button import Button
            botoes = [(w.text.strip()[:24], _ret(w)) for w in tela().walk()
                      if isinstance(w, Button) and w.get_root_window() is not None and w.opacity > 0.05]
            ponto = _no_vao(kb, botoes)
            estado['per'] = [dict(p) for p in App.get_running_app().periodos_ganhos]
            fase(f'vaza ganhos: {len(botoes)} botoes na tela; ponto no vao do teclado em cima de botao: {ponto}')
            if ponto:
                tocar_tela(ponto[0], ponto[1])
        passos.append((0.2, _testa_ganhos))
        passos.append((0.8, lambda: fase(f"vaza ganhos RESULTADO: popup aberto={popup_aberto() is not None}, "
                                         f"periodos mudaram={estado.get('per') != [dict(p) for p in App.get_running_app().periodos_ganhos]}, "
                                         f"tela agora={App.get_running_app().root.ids.sm.current}")))
        passos.append((0.1, lambda: foto('vaza-ganhos-depois')))
    if _os.environ.get('DUPLO') == '1':               # dois toques rapidos nos botoes de confirmar
        est = {}

        def _achar(txt):
            for topo in Window.children:                 # de cima (popup) para baixo
                for w in topo.walk():
                    if txt in str(getattr(w, 'text', '')) and w.get_root_window() and w.opacity > 0.05:
                        return w
            return None

        def _toque_duplo(txt, intervalo=0.08):
            w = _achar(txt)
            if w is None:
                LOG['erros'].append('duplo: botao nao achado ' + txt)
                return
            x, y = w.to_window(w.center_x, w.center_y)
            tocar_tela(x, y)
            Clock.schedule_once(lambda dt: tocar_tela(x, y), intervalo)

        def _popups():
            return sum(1 for w in Window.children if isinstance(w, Popup))
        app_ = lambda: App.get_running_app()
        passos.append((0.5, lambda: ir('registro')))
        # A) Adicionar Lote duas vezes: quantos popups de XP abrem?
        def _prepara():
            t = tela()
            t.ids.nome_input.focus = False
            t.ids.nome_input.text = 'Teste duplo'
            t.ids.qtd_input.text = '10'
            est['reg0'] = len(app_().registros)
        passos.append((1.5, _prepara))
        passos.append((0.4, lambda: _toque_duplo('Adicionar Lote')))
        passos.append((0.8, lambda: fase(f'duplo A (Adicionar Lote 2x): popups de XP abertos = {_popups()}')))
        # B) CONFIRMAR o XP duas vezes: quantas pecas entram?
        def _xp():
            p = next((w for w in reversed(Window.children) if isinstance(w, Popup)), None)
            for w in (p.walk() if p else []):
                if isinstance(w, TextInput):
                    w.text = '3'
        passos.append((0.2, _xp))
        passos.append((0.3, lambda: _toque_duplo('CONFIRMAR')))
        passos.append((1.2, lambda: fase(f"duplo B (CONFIRMAR 2x): pecas novas = {len(app_().registros) - est['reg0']}, "
                                         f"popups ainda abertos = {_popups()}")))
        passos.append((0.2, lambda: [p.dismiss() for p in list(Window.children) if isinstance(p, Popup)]))
        # C) SALVAR TURNO duas vezes: quantos turnos entram?
        def _fin():
            est['mem0'] = len(app_().memorias)
            tela().finalizar_dia()
        passos.append((1.0, _fin))
        passos.append((0.9, lambda: _toque_duplo('SALVAR TURNO')))
        passos.append((1.5, lambda: fase(f"duplo C (SALVAR TURNO 2x): turnos novos = {len(app_().memorias) - est['mem0']}")))
        passos.append((0.2, lambda: foto('duplo-depois')))
        # D) APAGAR um dia nas memorias: agora pergunta antes
        passos.append((1.5, lambda: ir('memorias')))
        def _abre_dia():
            est['mem1'] = len(app_().memorias)
            tela().abrir_detalhes_memoria(app_().memorias[-1])
        passos.append((1.5, _abre_dia))
        passos.append((0.8, lambda: _toque_duplo('APAGAR')))
        passos.append((0.8, lambda: fase(f"D (APAGAR o dia): popups abertos = {_popups()}, "
                                         f"turnos apagados = {est['mem1'] - len(app_().memorias)}")))
        passos.append((0.1, lambda: foto('apagar-dia-pergunta')))
        passos.append((0.3, lambda: _toque_duplo('CANCELAR')))
        passos.append((0.8, lambda: fase(f"D depois de CANCELAR: turnos apagados = {est['mem1'] - len(app_().memorias)}, "
                                         f"popups = {_popups()}")))
        passos.append((0.3, lambda: _toque_duplo('APAGAR')))
        passos.append((0.8, lambda: _toque_duplo('APAGAR')))          # o APAGAR da pergunta (2 toques)
        passos.append((3.0, lambda: fase(f"D depois de confirmar: turnos apagados = {est['mem1'] - len(app_().memorias)}, "
                                         f"popups = {_popups()}")))
    if _os.environ.get('VOLTA') == '1':               # botao VOLTAR do Android (tecla 27)
        def _voltar():
            r = Window.dispatch('on_keyboard', 27, 41, None, [])
            return r

        def _estado(rot):
            from kivy.uix.popup import Popup as _P
            pops = sum(1 for w in Window.children if isinstance(w, _P))
            fase(f"volta {rot}: tela={App.get_running_app().root.ids.sm.current}, "
                 f"teclado aberto={teclado_aberto() is not None}, popups={pops}")
        passos.append((0.5, lambda: ir('registro')))
        passos.append((1.8, lambda: _estado('registro com teclado')))
        passos.append((0.1, _voltar))
        passos.append((0.5, lambda: _estado('1o VOLTAR (fecha o teclado)')))
        passos.append((0.1, lambda: tela().confirmar_delete(App.get_running_app().registros[0], None)))
        passos.append((0.6, lambda: _estado('aviso de apagar aberto')))
        passos.append((0.1, _voltar))
        passos.append((0.6, lambda: _estado('2o VOLTAR (fecha o popup)')))
        passos.append((0.1, _voltar))
        passos.append((1.5, lambda: _estado('3o VOLTAR (volta ao menu)')))
    passos.append((1.5, lambda: fim(0)))
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
    if os.environ.get('RAPIDA') == '1' and os.environ.get('PULAR'):
        fase('rapida')
        Clock.schedule_once(_teste_pular, 0.1)
        return
    if os.environ.get('RAPIDA') == '1':
        fase('rapida')
        rajada('rapida', float(os.environ.get('RAPIDA_DUR', '5.5')), float(os.environ.get('RAPIDA_PASSO', '0.05')))
        Clock.schedule_once(fim, float(os.environ.get('RAPIDA_DUR', '5.5')) + 2.0)
        return
    Clock.schedule_once(passo_pin, 0.5)
    Clock.schedule_once(fim, 170.0)


Clock.schedule_once(inicio, 0.6)
if os.environ.get('PROF') == '1':
    import cProfile
    cProfile.run('main.TraveteApp().run()', os.path.join(SAIDA, 'prof.out'))
else:
    main.TraveteApp().run()
