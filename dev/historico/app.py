"""Roda o app de verdade (desktop) numa pasta de dados isolada e segue um
roteiro: PIN (teclas, erro, acerto), cena do titulo, apagar item, WIPE.
Captura quadros (Window.screenshot), registra os sons tocados (sem tocar
nada no alto-falante) e confere se o Kirito sai do quadro.

uso: python -u app.py LARG ALT SAIDA [densidade]
"""
import os
import sys
import json
import math
import time

LARG, ALT, SAIDA = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
DENS = sys.argv[4] if len(sys.argv) > 4 else None
REPO = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')
os.makedirs(SAIDA, exist_ok=True)
if DENS:
    os.environ['KIVY_METRICS_DENSITY'] = DENS
os.environ['KIVY_NO_ARGS'] = '1'
os.environ.setdefault('KIVY_LOG_MODE', 'PYTHON')

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
import som  # noqa: E402
import kirito as K  # noqa: E402

Window.size = (LARG, ALT)
T0 = [None]
LOG = {'quadros': [], 'sons': [], 'fora': [], 'erros': [], 'tamanho': [LARG, ALT], 'dens': DENS}


def agora():
    return time.time() - T0[0] if T0[0] else 0.0


# ── sons: registra em vez de tocar ───────────────────────────────────
_tocar_orig = som.tocar


def _tocar(acao):
    fonte = 'gravado' if som._gravacao(acao) else ('sintese' if acao in som._RECEITAS else 'NENHUM')
    LOG['sons'].append([round(agora(), 3), acao, fonte])


_tocar.__name__ = 'tocar'
som.tocar = _tocar
for _n in dir(som):
    if _n.startswith('tocar_'):
        acao = _n[len('tocar_'):]
        setattr(som, _n, (lambda a: (lambda: _tocar(a)))(acao))
som.precarregar = lambda acoes: None

# confere que o SoundLoader carrega cada gravacao (sem tocar)
from kivy.core.audio import SoundLoader  # noqa: E402
for f in sorted(os.listdir(os.path.join(REPO, 'sons'))):
    if f.endswith('.wav'):
        s = SoundLoader.load(os.path.join(REPO, 'sons', f))
        LOG.setdefault('carrega', []).append([f, bool(s), round(s.length, 3) if s else 0])
        if s:
            s.unload()


# ── capturas ─────────────────────────────────────────────────────────
def foto(rotulo):
    try:
        caminho = Window.screenshot(name=os.path.join(SAIDA, 'q.png'))
        LOG['quadros'].append([round(agora(), 3), rotulo, os.path.basename(caminho)])
    except Exception as e:
        LOG['erros'].append(f'foto {rotulo}: {e}')


def rajada(rotulo, dur, passo):
    n = int(dur / passo)
    for i in range(n):
        Clock.schedule_once(lambda dt, i=i: foto(f'{rotulo} {i * passo:.2f}s'), i * passo)


# ── o boneco saiu do quadro? ─────────────────────────────────────────
def _kiritos(w, out):
    for c in w.children:
        if isinstance(c, K.KiritoPixel):
            out.append(c)
        _kiritos(c, out)
    return out


def _caixa_janela(k):
    x0, y0, x1, y1 = K.caixa(k._pose)
    ps = k.ps
    if k.espelhar:
        x0, x1 = K.GW - 1 - x1, K.GW - 1 - x0
    cantos = [(x0 * ps, y0 * ps), ((x1 + 1) * ps, y0 * ps), (x0 * ps, (y1 + 1) * ps), ((x1 + 1) * ps, (y1 + 1) * ps)]
    ox, oy = k.pivo if k.pivo is not None else k.ancora_local()
    a = math.radians(k.rotacao)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for (lx, ly) in cantos:
        dx, dy = lx - ox, ly - oy
        rx, ry = ox + dx * ca - dy * sa, oy + dx * sa + dy * ca
        wx, wy = k.parent.to_window(k.x + rx, k.y + ry) if k.parent else (k.x + rx, k.y + ry)
        pts.append((wx, wy))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


VIGIAR = {'ativo': False, 'nome': ''}


def _vigia(dt):
    if not VIGIAR['ativo']:
        return
    try:
        for k in _kiritos(Window, []):
            if k.opacity < 0.05 or k.parent is None:
                continue
            x0, y0, x1, y1 = _caixa_janela(k)
            fora = max(0.0, -x0, x1 - Window.width, -y0, y1 - Window.height)
            if k.pivo is not None and fora == y1 - Window.height and fora <= 2.2 * k.ps:
                continue            # pendurado: a mao segura a borda de cima (de proposito)
            if fora > 1.5:
                LOG['fora'].append([round(agora(), 3), VIGIAR['nome'], round(fora, 1),
                                    [round(x0), round(y0), round(x1), round(y1)],
                                    k._base.get('pernas'), round(k.rotacao, 1)])
    except Exception as e:
        LOG['erros'].append(f'vigia: {e}')


# ── roteiro ──────────────────────────────────────────────────────────
def _campo_pin():
    for w in Window.children:
        if isinstance(w, Popup):
            for x in w.walk():
                if isinstance(x, TextInput):
                    return x
    return None


def _digitar(txt, cada=0.35, depois=None):
    for i, ch in enumerate(txt):
        def _d(dt, ch=ch):
            inp = _campo_pin()
            if inp is not None:
                inp.text = inp.text + ch
        Clock.schedule_once(_d, i * cada)
    if depois:
        Clock.schedule_once(lambda dt: depois(), len(txt) * cada + 0.05)


def _enviar():
    inp = _campo_pin()
    if inp is not None:
        inp.dispatch('on_text_validate')


def passo_pin(dt):
    if _campo_pin() is None:
        Clock.schedule_once(passo_pin, 0.1)
        return
    LOG['t_popup'] = round(agora(), 3)
    VIGIAR.update(ativo=True, nome='pin')
    rajada('pin-entra', 1.9, 0.1)
    if os.environ.get('TECLADO'):
        # toca no campo: abre o teclado SAO e a caixa sobe (o Kirito tem que ir junto)
        def _foco(dt):
            inp = _campo_pin()
            if inp is not None:
                inp.focus = True
        Clock.schedule_once(_foco, 1.3)
    Clock.schedule_once(lambda dt: rajada('pin-tecla', 1.6, 0.08), 2.0)
    Clock.schedule_once(lambda dt: _digitar('12'), 2.05)
    Clock.schedule_once(lambda dt: _digitar('99', cada=0.1, depois=_enviar), 3.4)
    Clock.schedule_once(lambda dt: rajada('pin-erro', 2.2, 0.08), 3.6)
    if os.environ.get('BLOQUEIO'):
        # mais dois erros: bloqueio (o Kirito balanca a cabeca e afunda)
        Clock.schedule_once(lambda dt: _digitar('11', cada=0.1, depois=_enviar), 6.2)
        Clock.schedule_once(lambda dt: _digitar('33', cada=0.1, depois=_enviar), 7.6)
        Clock.schedule_once(lambda dt: rajada('pin-bloq', 2.8, 0.08), 7.7)
        Clock.schedule_once(fim, 11.5)
        return
    Clock.schedule_once(lambda dt: _digitar('2004', cada=0.12, depois=_enviar), 6.2)
    Clock.schedule_once(lambda dt: rajada('pin-certo', 2.2, 0.08), 6.7)
    Clock.schedule_once(esperar_titulo, 8.0)


def esperar_titulo(dt):
    tela = Window.children[-1] if Window.children else None
    try:
        from kivy.app import App
        sm = App.get_running_app().root.ids.sm
        lt = sm.get_screen('loading')
        if getattr(lt, '_cena', None) is not None:
            LOG['t_titulo'] = round(agora(), 3)
            VIGIAR.update(ativo=True, nome='titulo')
            rajada('titulo', float(os.environ.get('DUR_TITULO', 17.5)), 0.1)
            Clock.schedule_once(esperar_menu, 3.0)
            return
    except Exception as e:
        LOG['erros'].append(f'titulo: {e}')
    Clock.schedule_once(esperar_titulo, 0.05)


def esperar_menu(dt):
    from kivy.app import App
    if App.get_running_app().root.ids.sm.current != 'menu':
        Clock.schedule_once(esperar_menu, 0.1)
        return
    LOG['t_menu'] = round(agora(), 3)
    Clock.schedule_once(ir_apagar, 1.5)


def ir_apagar(dt):
    VIGIAR.update(ativo=False, nome='')
    try:
        from cenas import kirito_fatiar
        from kivy.app import App
        sm = App.get_running_app().root.ids.sm
        # alvo: o primeiro botao visivel do menu
        from efeitos import BotaoAngular
        tela = sm.current_screen
        botoes = [w for w in tela.walk(restrict=True) if isinstance(w, BotaoAngular)]
        if botoes:
            LOG['t_fatiar'] = round(agora(), 3)
            alvo = botoes[len(botoes) // 2]
            kirito_fatiar(alvo, on_fim=lambda: LOG.__setitem__('fatiar_fim', round(agora(), 3)))
            rajada('fatiar', 1.4, 0.07)
    except Exception as e:
        LOG['erros'].append(f'fatiar: {e}')
    Clock.schedule_once(fim, 2.2)


_acabou = [False]


def fim(dt):
    if _acabou[0]:
        return
    _acabou[0] = True
    with open(os.path.join(SAIDA, 'log.json'), 'w', encoding='utf-8') as f:
        json.dump(LOG, f, ensure_ascii=False, indent=1)
    print('[harness] fim', len(LOG['quadros']), 'quadros,', len(LOG['fora']), 'fora do quadro,',
          len(LOG['erros']), 'erros')
    from kivy.app import App
    App.get_running_app().stop()


def inicio(dt):
    T0[0] = time.time()
    foto('descarte')                     # a 1a captura as vezes vem vazia
    Clock.schedule_interval(_vigia, 1 / 60.)
    Clock.schedule_once(passo_pin, 0.5)
    Clock.schedule_once(fim, 85.0)       # seguranca


Clock.schedule_once(inicio, 0.6)
main.TraveteApp().run()
