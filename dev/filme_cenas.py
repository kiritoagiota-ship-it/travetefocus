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
if os.environ.get('MEMS'):              # so os ultimos N turnos (ex.: celular com 2 dias)
    memorias = memorias[-int(os.environ['MEMS']):]
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
if CENA in ('app', 'telas', 'zap', 'varre', 'meta', 'anim', 'vivo', 'novas', 'mem', 'link', 'ajustes', 'toques', 'trans', 'perfil', 'polir', 'avisos', 'fluidez'):
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


def _textos_cortados(nome):
    """CORTE=1: em cada foto, os textos que NAO cabem no espaco deles (linha
    que some por falta de altura, ou texto mais largo que o botao/caixa)."""
    from kivy.uix.label import Label

    def visivel(w):
        while w is not None and w is not Window:
            if getattr(w, 'opacity', 1) <= 0.01 or getattr(w, 'disabled', False) and w.opacity < 0.5:
                return False
            w = w.parent
        return True

    def todos(w):
        yield w
        for c in list(getattr(w, 'children', [])):
            yield from todos(c)
    achados = []
    for raiz in list(Window.children):
        for w in todos(raiz):
            if not isinstance(w, Label) or not (w.text or '').strip() or w.width < 4 or w.height < 4:
                continue
            if not visivel(w):
                continue
            x0, y0 = w.to_window(w.x, w.y)
            if x0 > Window.width or y0 > Window.height or x0 + w.width < 0 or y0 + w.height < 0:
                continue
            try:
                ts = w.text_size
                larg = ts[0] if ts and ts[0] else None
                t = Label(text=w.text, markup=w.markup, font_name=w.font_name, font_size=w.font_size,
                          line_height=w.line_height, padding=w.padding, halign=w.halign,
                          text_size=(larg, None), bold=w.bold, max_lines=w.max_lines or 0)
                t.texture_update()
                tw, th = t.texture_size
                pad_x = w.padding[0] + w.padding[2] if len(w.padding) == 4 else 2 * w.padding[0]
                txt = w.text.replace('\n', ' / ')[:60]
                n_tem = len(getattr(w._label, '_cached_lines', None) or [])
                n_quer = len(getattr(t._label, '_cached_lines', None) or [])
                if (ts and ts[1]) and n_tem < n_quer:
                    achados.append(f'LINHA SOME {nome}: "{txt}" tem {n_quer} linhas, aparecem {n_tem} '
                                   f'(precisa {th:.0f}px, tem {w.height:.0f}px)')
                elif larg is None and tw > w.width + 2 and not getattr(w, 'shorten', False):
                    achados.append(f'LARGURA {nome}: "{txt}" precisa {tw:.0f}px, tem {w.width:.0f}px '
                                   f'({type(w).__name__})')
            except Exception as e:
                achados.append(f'erro {nome}: {e}')
    with open(os.path.join(SAIDA, 'cortes.txt'), 'a', encoding='utf-8') as f:
        for a in achados:
            f.write(a + '\n')
    print(f'[cenas] cortes {nome}: {len(achados)}')


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
            if os.environ.get('CORTE') == '1':
                _textos_cortados(nome)
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
        (0.3, ir('menu')), (1.6, lambda: apertar('SENHA')), (0.9, lambda: foto('19-aviso-trocar-senha')),
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


def roteiro_anim():
    """As animacoes da interface, quadro a quadro: entrada das telas, o
    teclado subindo e descendo, um aviso abrindo e fechando, um lote entrando
    e um lote apagado (a lista fecha o buraco)."""
    def ir(nome):
        return lambda: app().mudar_tela(nome)

    def apaga_meio():
        t = tela()
        itens = list(t.ids.lista_container.children)
        btn = itens[len(itens) // 2]
        dado = next((r for r in app().registros if r[0] in btn.text), app().registros[0])
        t.confirmar_delete(dado, btn)
    passos = [(0.3, lambda: fase('entra registro')), (0.01, ir('registro')),
              (1.6, lambda: fase('teclado sobe')), (0.01, lambda: setattr(tela().ids.nome_input, 'focus', True)),
              (0.9, lambda: fase('teclado desce')), (0.01, soltar_foco),
              (0.8, lambda: fase('aviso abre')), (0.01, apaga_meio),
              (0.9, lambda: fase('aviso fecha')), (0.01, lambda: apertar('CANCELAR')),
              (0.8, lambda: fase('apaga lote')), (0.01, apaga_meio), (0.4, lambda: apertar('DESINTEGRAR')),
              (4.2, lambda: fase('entra ganhos')), (0.01, ir('ganhos')),
              (1.8, lambda: fase('ajustes')), (0.01, lambda: tela().alternar_ajustes(True)),
              (0.9, lambda: fase('entra calculadora')), (0.01, ir('calculadora')),
              (1.6, lambda: fase('entra memorias')), (0.01, ir('memorias')), (2.0, fim)]
    Roteiro(passos).rodar()


def roteiro_vivo():
    """As animacoes continuas e interativas, quadro a quadro: o menu parado
    (brilho no titulo, luz nas linhas), a faixa de aviso, o HOJE contando,
    a borda acesa no fim da lista, o grafico crescendo e trocando de mes,
    a barra de ganhos enchendo, o anel do progresso e a calculadora."""
    from kivy.metrics import dp

    def ir(nome):
        return lambda: app().mudar_tela(nome)

    def lote():
        t = tela()
        t.ids.nome_input.text = 'Short'
        t.ids.qtd_input.text = '40'
        soltar_foco()
        t.adicionar_item()

    def puxar(sv_id, para_cima):
        # o dedo puxa a lista alem do fim (o efeito recebe o arrasto)
        w = tela().ids[sv_id]
        sv = w if hasattr(w, 'effect_y') else w.parent
        e = sv.effect_y
        lo, hi = sorted((e.min, e.max))
        v0 = lo if para_cima else hi
        e.value = v0
        e.start(v0)
        for k in range(1, 9):
            e.update(v0 + (-1 if para_cima else 1) * dp(14) * k)
        e.stop(v0 + (-1 if para_cima else 1) * dp(14) * 8)

    def mes():
        for w in tela().ids.filtros_container.children:
            if '09/' in w.text:
                tela()._filtrar(w.text)
                return

    def calc(s):
        def _f():
            for ch in s:
                tela().apertar(ch)
        return _f
    passos = [(0.2, lambda: fase('menu parado')), (7.5, lambda: fase('registro')), (0.01, ir('registro')),
              (2.0, lambda: fase('lote: HOJE conta')), (0.01, lote), (0.8, lambda: setattr(campo_do_popup(), 'text', '3')),
              (0.2, lambda: apertar('CONFIRMAR')), (0.8, soltar_foco),
              (2.4, lambda: fase('faixa de aviso')), (0.01, lambda: tela()._festa('FAIXA NOVA!', 'Todas as peças da semana valem R$ 0,30', True)),
              (3.6, lambda: fase('borda acesa embaixo')), (0.01, lambda: puxar('lista_container', False)),
              # um turno de outro mes, para o grafico ter o que transformar
              (0.01, lambda: (app().memorias.append({'data': '05/10/2026  17:00', 'total': 320, 'xp': 960}),
                              app().memorias.append({'data': '06/10/2026  17:00', 'total': 140, 'xp': 420}))),
              (1.2, lambda: fase('memorias: grafico cresce')), (0.01, ir('memorias')),
              (2.2, lambda: fase('borda acesa em cima')), (0.01, lambda: puxar('lista_scroll', True)),
              (1.2, lambda: fase('grafico troca de mes')), (0.01, mes),
              (1.6, lambda: fase('grafico volta TODOS')), (0.01, lambda: tela()._filtrar('TODOS')),
              (1.6, lambda: fase('ganhos: barra enche')), (0.01, ir('ganhos')),
              (6.0, lambda: fase('progresso: anel vivo')), (0.01, ir('progresso')),
              (5.5, lambda: fase('calculadora vazia')), (0.01, ir('calculadora')),
              (1.4, lambda: fase('conta 1')), (0.01, calc('125*3=')),
              (1.2, lambda: fase('conta 2')), (0.01, calc('846/3=')),
              (1.2, lambda: fase('digitando')), (0.01, calc('7')), (0.25, calc('5')), (0.25, calc('0')),
              (1.0, fim)]
    Roteiro(passos).rodar()


_DEDO = [100]


def _toque_cls():
    from kivy.input.motionevent import MotionEvent

    class _Toque(MotionEvent):
        def depack(self, args):
            self.sx, self.sy = args
            self.profile = ['pos']
            super().depack(args)
    return _Toque


def dedo_desce(x, y):
    """Um dedo de verdade encostando na tela (passa pela janela)."""
    from kivy.base import EventLoop
    _DEDO[0] += 1
    t = _toque_cls()('teste', _DEDO[0], (x / float(Window.width), y / float(Window.height)),
                     is_touch=True, type_id='touch')
    EventLoop.post_dispatch_input('begin', t)
    return t


def dedo_move(t, x, y):
    from kivy.base import EventLoop
    t.move((x / float(Window.width), y / float(Window.height)))
    EventLoop.post_dispatch_input('update', t)


def dedo_sobe(t):
    from kivy.base import EventLoop
    EventLoop.post_dispatch_input('end', t)


def no_meio(w):
    return w.to_window(*w.center)


def roteiro_novas():
    """As animacoes novas com toques de verdade: LEVEL UP (e o titulo novo
    a cada 10 niveis), segurar o lote para corrigir, arrastar o lote para
    apagar, o cartao das Memorias abrindo, a barra do grafico tocada, a barra
    de Ganhos passando de faixa, o anel de luz das teclas, o anel do
    Progresso tocado, as chamas da sequencia e os icones do menu."""
    from datetime import datetime
    from helpers import calcular_level
    est = {}

    def ir(nome):
        return lambda: app().mudar_tela(nome)

    def perto_do_nivel(alvo_nivel=None):
        a = app()
        if alvo_nivel is None:
            _lv, at, nec = calcular_level(a.total_xp)
            a.total_xp += nec - at - 10
        else:
            soma = sum(int(800 * (l ** 1.5)) for l in range(1, alvo_nivel))
            a.total_xp = soma - 10
        LOG.setdefault('xp_antes', []).append(a.total_xp)

    def lote():
        t = tela()
        t.ids.nome_input.text = 'Short'
        t.ids.qtd_input.text = '40'
        soltar_foco()
        t.adicionar_item()

    def item_registro(i=0):
        itens = list(reversed(tela().ids.lista_container.children))
        return itens[min(i, len(itens) - 1)]

    def segura_ini():
        est['w'] = item_registro(1)
        est['t'] = dedo_desce(*no_meio(est['w']))

    def segura_fim():
        dedo_sobe(est['t'])

    def arrasta_ini():
        est['w'] = item_registro(0)
        x, y = no_meio(est['w'])
        est['xy'] = (x, y)
        est['t'] = dedo_desce(x, y)

    def arrasta(k):
        def _f():
            x, y = est['xy']
            dedo_move(est['t'], x + est['w'].width * 0.42 * k, y + 2 * k)
        return _f

    def toca(w_fn, segura=0.08):
        def _f():
            w = w_fn()
            t = dedo_desce(*no_meio(w))
            Clock.schedule_once(lambda dt: dedo_sobe(t), segura)
        return _f

    def toca_xy(fn, segura=0.08):
        def _f():
            t = dedo_desce(*fn())
            Clock.schedule_once(lambda dt: dedo_sobe(t), segura)
        return _f

    def item_memoria():
        return list(reversed(tela().ids.memorias_container.children))[2]

    def barra_grafico():
        g = tela().ids.grafico_barras
        return g.to_window(g.centro_barra(2), g.y + g.height * 0.3)

    def tecla(txt):
        return lambda: next(w for w in tela().walk()
                            if hasattr(w, 'tatil') and str(getattr(w, 'text', '')).strip() == txt)

    def sequencia_longa():
        a = app()
        a.streak = 7
        a.ultima_data = datetime.now().strftime('%d/%m/%Y')

    passos = [(0.3, ir('registro')), (2.2, soltar_foco),
              (0.2, lambda: fase('level up')), (0.01, perto_do_nivel), (0.01, lote),
              (0.8, lambda: setattr(campo_do_popup(), 'text', '3')), (0.2, lambda: apertar('CONFIRMAR')),
              (0.9, soltar_foco), (2.0, lambda: foto('n1-level-up')), (3.0, lambda: fase('titulo novo')),
              (0.01, lambda: perto_do_nivel(11)), (0.01, lote),
              (0.8, lambda: setattr(campo_do_popup(), 'text', '3')), (0.2, lambda: apertar('CONFIRMAR')),
              (0.9, soltar_foco), (2.9, lambda: foto('n2-titulo-novo')), (4.5, lambda: fase('segurar lote')),
              (0.01, segura_ini), (0.4, lambda: foto('n3-segurando')), (0.5, segura_fim),
              (0.6, lambda: foto('n4-corrigir')), (0.1, lambda: setattr(campo_do_popup(), 'text', '55')),
              (0.2, lambda: apertar('CORRIGIR')), (1.2, soltar_foco),
              (0.4, lambda: fase('arrastar lote')), (0.01, arrasta_ini), (0.12, arrasta(0.1)), (0.12, arrasta(0.4)), (0.08, arrasta(0.7)),
              (0.08, arrasta(1.0)), (0.08, arrasta(1.2)), (0.03, lambda: foto('n5-arrastando')),
              (0.05, lambda: dedo_sobe(est['t'])), (0.7, lambda: foto('n6-apagar')), (0.2, lambda: apertar('CANCELAR')),
              (0.8, lambda: fase('memorias')), (0.01, ir('memorias')),
              (2.2, lambda: fase('abre o dia')), (0.01, toca(item_memoria)), (0.12, lambda: foto('n7-abrindo')),
              (0.9, lambda: foto('n8-dia')), (0.3, fechar_popups),
              (0.8, lambda: fase('barra do grafico')), (0.01, toca_xy(barra_grafico)), (0.5, lambda: foto('n9-balao')),
              (2.4, lambda: fase('ganhos')), (0.01, ir('ganhos')), (2.6, lambda: foto('n10-ganhos')),
              (0.6, lambda: fase('teclas')), (0.01, ir('calculadora')), (1.6, toca(tecla('7'))),
              (0.08, lambda: foto('n11-tecla')), (0.3, toca(tecla('8'))), (0.4, toca(tecla('='))),
              (0.6, lambda: fase('progresso')), (0.01, sequencia_longa), (0.01, ir('progresso')),
              (2.4, lambda: foto('n12-chamas')), (0.3, lambda: fase('toca o anel')),
              (0.01, toca(lambda: tela().ids.barra_circular)), (0.7, lambda: foto('n13-anel')),
              (3.0, lambda: fase('menu')), (0.01, ir('menu')), (3.2, lambda: foto('n14-menu')), (1.0, fim)]
    Roteiro(passos).rodar()


def roteiro_mem():
    """So a entrada nas Memorias (duas vezes), para ver quadro a quadro."""
    def ir(nome):
        return lambda: app().mudar_tela(nome)
    alvo = os.environ.get('MEM_TELA', 'memorias')              # MEM_TELA/MEM_SEG: outra tela, mais tempo nela
    passos = [(float(os.environ.get('MENU_SEG', '0.5')), lambda: fase('entra ' + alvo)),   # MENU_SEG: mais tempo no menu
              (0.01, ir(alvo)), (float(os.environ.get('MEM_SEG', '2.5')), lambda: fase('volta menu')),
              (0.01, ir('menu')), (1.5, lambda: fase('entra memorias 2')), (0.01, ir('memorias')), (2.5, fim)]
    Roteiro(passos).rodar()


def roteiro_link():
    """O botao SYSTEM LINK START (icone, setas, luz correndo e o tunel ao
    tocar) e os cartoes novos do Registro: toque, segurar, arrastar e um lote
    novo chegando - tudo com toques de verdade."""
    est = {}

    def cartao(i):
        itens = list(reversed(tela().ids.lista_container.children))
        return itens[min(i, len(itens) - 1)]

    def toca(w_fn, segura=0.1):
        def _f():
            t = dedo_desce(*no_meio(w_fn()))
            Clock.schedule_once(lambda dt: dedo_sobe(t), segura)
        return _f

    def segura_ini():
        est['t'] = dedo_desce(*no_meio(cartao(1)))

    def arrasta_ini():
        est['w'] = cartao(0)
        est['xy'] = no_meio(est['w'])
        est['t'] = dedo_desce(*est['xy'])

    def arrasta(k):
        def _f():
            x, y = est['xy']
            dedo_move(est['t'], x + est['w'].width * 0.42 * k, y + 2 * k)
        return _f

    def lote():
        t = tela()
        t.ids.nome_input.text = 'Vestido longo'
        t.ids.qtd_input.text = '35'
        soltar_foco()
        t.adicionar_item()

    passos = [(1.5, lambda: fase('menu')), (2.6, lambda: foto('l1-menu')),
              (0.2, lambda: fase('toque link start')), (0.01, toca(lambda: tela().ids.btn_link_start)),
              (0.3, lambda: foto('l2-tunel')), (0.25, lambda: foto('l3-tunel-clarao')),
              (1.6, soltar_foco), (0.6, lambda: foto('l4-cartoes')),
              (0.3, lambda: fase('toque no cartao')), (0.01, toca(lambda: cartao(2), 0.12)),
              (0.06, lambda: foto('l5-toque')), (0.6, fechar_popups),
              (0.6, lambda: fase('segurar cartao')), (0.01, segura_ini), (0.45, lambda: foto('l6-segurando')),
              (0.5, lambda: dedo_sobe(est['t'])), (0.6, lambda: foto('l7-corrigir')), (0.2, fechar_popups),
              (0.6, lambda: fase('arrastar cartao')), (0.01, arrasta_ini), (0.12, arrasta(0.1)),
              (0.12, arrasta(0.4)), (0.08, arrasta(0.8)), (0.08, arrasta(1.15)), (0.03, lambda: foto('l8-arrastando')),
              (0.05, lambda: dedo_sobe(est['t'])), (0.7, fechar_popups),
              (0.6, lambda: fase('lote novo')), (0.01, lote), (0.8, lambda: setattr(campo_do_popup(), 'text', '4')),
              (0.2, lambda: apertar('CONFIRMAR')), (0.6, soltar_foco), (0.5, lambda: foto('l9-lote-novo')),
              (3.5, fim)]
    Roteiro(passos).rodar()


def roteiro_ajustes():
    """Ganhos: o botao AJUSTES com toques de verdade (rapido, segurando e com o
    dedo tremendo um pouco, como no celular), abrindo e fechando."""
    est = {}

    def btn():
        return tela().ids.btn_ajustes

    esperado = {'antes': False, 'toque rapido': True, 'toque rapido de novo': False, 'toque segurando': True,
                'fechou?': False, 'toque tremendo': True}

    def estado(nome):
        def _f():
            b = tela().ids.bloco_config
            LOG.setdefault('ajustes', []).append([nome, round(b.height, 1), round(b.opacity, 2), b.disabled])
            if (b.height > 1) != esperado.get(nome, b.height > 1):
                LOG['erros'].append(f'ajustes: depois de "{nome}" o painel devia estar '
                                    f'{"aberto" if esperado[nome] else "fechado"} (altura {b.height:.0f})')
            fase(f'{nome}: altura={b.height:.0f} opacidade={b.opacity:.2f}')
        return _f

    def toque(segura=0.08, treme=0):
        def _f():
            x, y = no_meio(btn())
            t = est['t'] = dedo_desce(x, y)
            for k in range(treme):
                Clock.schedule_once(lambda dt, k=k: dedo_move(t, x + (k % 2) * 3, y + (k % 3) * 2), 0.02 * (k + 1))
            Clock.schedule_once(lambda dt: dedo_sobe(t), segura)
        return _f
    def espia():
        b = btn()
        b.bind(on_press=lambda *_: fase('DBG on_press'), on_release=lambda *_: fase('DBG on_release'))
        fase(f'DBG btn pos={b.to_window(*b.pos)} size={b.size} disabled={b.disabled} opac={b.opacity}')
        fase(f'DBG janela: {[type(w).__name__ for w in Window.children]}')
        x, y = no_meio(b)
        for w in tela().walk(restrict=True):
            try:
                x0, y0 = w.to_window(w.x, w.y)
                if x0 <= x <= x0 + w.width and y0 <= y <= y0 + w.height:
                    fase(f'DBG sob o dedo: {type(w).__name__} id={getattr(w, "text", "")[:20]!r} '
                         f'disabled={w.disabled} rect=({x0:.0f},{y0:.0f},{w.width:.0f},{w.height:.0f})')
            except Exception:
                pass
        fase(f'DBG ponto {x:.0f},{y:.0f}')
    passos = [(0.3, lambda: app().mudar_tela('ganhos')), (2.4, estado('antes')),
              (0.2, toque(0.08)), (0.6, estado('toque rapido')), (0.1, lambda: foto('a1-rapido')),
              (0.4, toque(0.08)), (0.6, estado('toque rapido de novo')),
              (0.4, toque(0.35)), (0.7, estado('toque segurando')), (0.4, toque(0.35)), (0.7, estado('fechou?')),
              (0.4, toque(0.2, treme=6)), (0.7, estado('toque tremendo')), (0.1, lambda: foto('a2-tremendo')),
              (0.6, fim)]
    Roteiro(passos).rodar()


def roteiro_toques():
    """Em cada tela: algum botao visivel tem por cima dele (mais tarde na
    arvore = recebe o toque antes) um widget escondido ou desativado que
    seguraria o toque? (foi o que travou o AJUSTES de Ganhos.)"""
    def checa(nome):
        def _f():
            tl = tela()
            ws = list(tl.walk(restrict=True))
            ordem = {id(w): i for i, w in enumerate(ws)}
            def ret(w):
                x0, y0 = w.to_window(w.x, w.y)
                return x0, y0, x0 + w.width, y0 + w.height
            def visivel(w):
                p = w
                while p is not None and p is not tl:
                    if p.opacity < 0.05:
                        return False
                    p = p.parent
                return True
            botoes = [w for w in ws if hasattr(w, 'is_event_type') and w.is_event_type('on_release')
                      and not w.disabled and visivel(w) and w.width > 2 and w.height > 2]
            achados = 0
            for b in botoes:
                x0, y0, x1, y1 = ret(b)
                cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
                for w in ws:
                    if w is b or ordem[id(w)] <= ordem[id(b)] or w in b.walk():
                        continue
                    a = ret(w)
                    if not (a[0] <= cx <= a[2] and a[1] <= cy <= a[3]):
                        continue
                    if b in w.walk():
                        continue
                    pega = w.disabled or (not visivel(w) and hasattr(w, 'is_event_type') and w.is_event_type('on_release'))
                    if pega:
                        achados += 1
                        LOG['erros'].append(f'{nome}: {str(getattr(b, "text", ""))[:22]!r} coberto por '
                                            f'{type(w).__name__} {str(getattr(w, "text", ""))[:16]!r} '
                                            f'(desativado={w.disabled}, visivel={visivel(w)})')
            fase(f'toques {nome}: {len(botoes)} botoes, {achados} cobertos')
        return _f
    passos = [(0.5, checa('menu'))]
    for t in ('registro', 'memorias', 'progresso', 'ganhos', 'calculadora'):
        passos += [(0.3, lambda t=t: app().mudar_tela(t)), (2.6, checa(t))]
    passos += [(0.3, lambda: app().mudar_tela('ganhos')), (2.6, lambda: tela().alternar_ajustes(True)),
               (0.8, checa('ganhos com ajustes abertos')), (0.3, lambda: tela().alternar_ajustes(False)),
               (0.8, checa('ganhos com ajustes fechados')), (0.3, fim)]
    Roteiro(passos).rodar()


def roteiro_polir():
    """O polimento de 1.8 com toques de verdade: o painel vivo do menu (toque
    abre o Progresso; na volta os numeros contam do valor de antes), o aviso
    HUD abrindo do meio e fechando (SENHA -> CANCELAR) e o cartao do dia nas
    Memorias abrindo."""
    from kivy.uix.popup import Popup
    toque = {}

    def tocar_painel():
        p = app().root.ids.sm.get_screen('menu').ids.painel_menu
        toque['t'] = dedo_desce(*no_meio(p))

    def soltar():
        if 't' in toque:
            dedo_sobe(toque.pop('t'))

    def deve(nome):
        def _f():
            atual = app().root.ids.sm.current
            fase(f'tela agora: {atual}')
            if atual != nome:
                LOG['erros'].append(f'esperava a tela {nome}, esta em {atual}')
        return _f

    def popup_aberto(sim):
        def _f():
            n = sum(1 for w in Window.children if isinstance(w, Popup))
            fase(f'popups abertos: {n}')
            if (n > 0) != sim:
                LOG['erros'].append(f'popup {"nao abriu" if sim else "nao fechou"}')
        return _f

    def tocar_txt(txt):
        def _f():
            w = achar(txt)
            if w is None:
                LOG['erros'].append('botao nao achado: ' + txt)
                return
            toque['t'] = dedo_desce(*no_meio(w))
        return _f

    def tocar_cartao():
        from efeitos import CartaoMemoria
        cs = [w for w in tela().walk(restrict=True) if isinstance(w, CartaoMemoria)]
        if not cs:
            LOG['erros'].append('nenhum CartaoMemoria')
            return
        fase(f'{len(cs)} cartoes; recordes: {sum(1 for c in cs if c.recorde)}')
        c = max(cs, key=lambda w: w.to_window(*w.center)[1])   # o de cima da lista
        fase(f"toca no cartao {c._txt['data'].get('texto')} em {no_meio(c)}")
        toque['t'] = dedo_desce(*no_meio(c))

    def pecas_hoje(n):
        def _f():
            app().registros.append(['Camisa polo', str(n), n * 3, '', time.time()])
            fase(f'+{n} pecas hoje')
        return _f

    passos = [(1.6, lambda: fase('painel')), (0.01, tocar_painel), (0.12, soltar),
              (1.6, deve('progresso')),
              (0.2, pecas_hoje(40)), (0.01, lambda: app().mudar_tela('menu')), (2.2, deve('menu')),
              (0.2, lambda: fase('aviso senha')), (0.01, tocar_txt('SENHA')), (0.1, soltar),
              (0.9, popup_aberto(True)), (0.01, tocar_txt('CANCELAR')), (0.1, soltar),
              (0.6, popup_aberto(False)),
              (0.2, lambda: app().mudar_tela('memorias')), (2.6, lambda: fase('cartao')),
              (0.01, tocar_cartao), (0.1, soltar), (1.2, popup_aberto(True)),
              (0.01, tocar_txt('FECHAR')), (0.1, soltar), (0.8, popup_aberto(False)),
              (0.3, fim)]
    Roteiro(passos).rodar()


def roteiro_fluidez():
    """Em cada tela parada (depois da entrada): o tempo de Python por quadro
    (cProfile) e quantos desenhos a placa de video faz por quadro (as
    instrucoes que desenham no canvas da janela; Line conta a parte, porque
    cada Line grossa e um desenho proprio)."""
    import cProfile
    import pstats
    from kivy.graphics.instructions import InstructionGroup, VertexInstruction
    from kivy.graphics import Line
    est = {}

    def contar():
        n = {'desenhos': 0, 'linhas': 0}

        def anda(g):
            for ins in getattr(g, 'children', []):
                if isinstance(ins, VertexInstruction):
                    vazio = False                  # (sem geometria nao desenha: nao conta)
                    try:
                        if isinstance(ins, Line):
                            vazio = len(ins.points) < 4
                        elif hasattr(ins, 'indices') and hasattr(ins, 'vertices'):
                            vazio = len(ins.indices) == 0
                        elif hasattr(ins, 'size'):
                            vazio = ins.size[0] <= 0 or ins.size[1] <= 0
                    except Exception:
                        pass
                    if not vazio:
                        n['desenhos'] += 1
                        if isinstance(ins, Line):
                            n['linhas'] += 1
                if isinstance(ins, InstructionGroup):
                    anda(ins)
        anda(Window.canvas)
        return n

    def liga(nome):
        def _f():
            est['nome'] = nome
            est['q0'] = Q[0]
            est['t0'] = time.perf_counter()
            est['p'] = cProfile.Profile()
            est['p'].enable()
        return _f

    def desliga():
        p = est['p']
        p.disable()
        dur = time.perf_counter() - est['t0']
        quadros = max(1, Q[0] - est['q0'])
        st = pstats.Stats(p)
        tot = sum(v[2] for v in st.stats.values())
        n = contar()
        # quem desenha mais: os widgets da tela com mais instrucoes de desenho
        por = {}
        for w in Window.walk(restrict=False) if False else app().root.walk():
            k = 0
            for cv in (w.canvas.before, w.canvas, w.canvas.after):
                for ins in cv.children:
                    if isinstance(ins, VertexInstruction):
                        k += 1
                    elif isinstance(ins, InstructionGroup):
                        k += sum(1 for i2 in ins.children if isinstance(i2, VertexInstruction))
            if k:
                por[type(w).__name__] = por.get(type(w).__name__, 0) + k
        top = sorted(por.items(), key=lambda kv: -kv[1])[:8]
        fase('   ' + ', '.join(f'{a}={b}' for a, b in top))
        fase(f"FLUIDEZ {est['nome']}: python {tot * 1000 / quadros:.2f} ms/quadro, "
             f"{n['desenhos']} desenhos ({n['linhas']} linhas)")
        with open(os.path.join(SAIDA, f"fluidez_{est['nome']}.txt"), 'w', encoding='utf-8') as f:
            st.stream = f
            st.sort_stats('tottime').print_stats(18)

    def ir(nome):
        return lambda: app().mudar_tela(nome)
    passos = [(2.5, liga('menu')), (2.0, desliga)]
    for t in ('registro', 'memorias', 'progresso', 'ganhos', 'calculadora'):
        passos += [(0.3, ir(t)), (2.8, liga(t)), (2.0, desliga), (0.2, ir('menu')), (1.2, lambda: None)]
    passos.append((0.3, fim))
    Roteiro(passos).rodar()


def roteiro_avisos():
    """O painel do botao AVISOS com toques de verdade: abre, TESTAR AGORA,
    DESLIGAR (confere que desligou), LIGAR de novo, FECHAR."""
    from kivy.uix.popup import Popup
    toque = {}

    def tocar_txt(txt):
        def _f():
            w = achar(txt)
            if w is None:
                LOG['erros'].append('botao nao achado: ' + txt)
                return
            toque['t'] = dedo_desce(*no_meio(w))
        return _f

    def soltar():
        if 't' in toque:
            dedo_sobe(toque.pop('t'))

    def confere(nome, cond):
        def _f():
            ok = cond()
            fase(f'{nome}: {ok}')
            if not ok:
                LOG['erros'].append('falhou: ' + nome)
        return _f
    aberto = lambda: any(isinstance(w, Popup) for w in Window.children)
    passos = [(1.2, lambda: fase('abre avisos')), (0.01, tocar_txt('AVISOS')), (0.1, soltar),
              (0.9, confere('painel aberto', aberto)), (0.2, lambda: foto('avisos-painel')),
              (0.2, tocar_txt('TESTAR AGORA')), (0.1, soltar), (0.6, lambda: foto('avisos-testar')),
              (0.2, tocar_txt('DESLIGAR')), (0.1, soltar), (0.4, confere('desligou', lambda: not app().lembretes)),
              (0.2, lambda: foto('avisos-desligado')),
              (0.2, tocar_txt('LIGAR')), (0.1, soltar), (0.4, confere('ligou', lambda: app().lembretes)),
              (0.2, tocar_txt('FECHAR')), (0.1, soltar), (0.6, confere('fechou', lambda: not aberto())),
              (0.3, fim)]
    Roteiro(passos).rodar()


def roteiro_trans():
    """So as trocas de tela: o corte que parte a tela (ida, na cor de cada
    destino) e o deslize do Voltar."""
    def ir(nome):
        return lambda: app().mudar_tela(nome)
    def ligado(onde):
        # a tela continua sendo redesenhada sozinha? (o menu tem particulas
        # animando: em 0,5 s tem que haver varios quadros novos; se o canvas
        # da tela perdeu a ligacao com a janela, quase nenhum)
        def _f():
            q0 = Q[0]

            def _conta(dt):
                n = Q[0] - q0
                fase(f'quadros redesenhados em 0,5 s depois de {onde}: {n}')
                if n < 8 and not onde.startswith('ir para'):      # (o menu sempre anima)
                    LOG['erros'].append(f'TELA CONGELADA depois de {onde}: so {n} quadros em 0,5 s')
            Clock.schedule_once(_conta, 0.5)
        return _f
    passos = [(0.8, lambda: fase('menu')), (0.01, ligado('abrir'))]
    for t in ('memorias', 'ganhos', 'calculadora', 'progresso'):
        passos += [(0.6, lambda t=t: fase('vai ' + t)), (0.01, ir(t)), (1.0, ligado('ir para ' + t)),
                   (0.4, lambda t=t: fase('volta de ' + t)),
                   (0.01, ir('menu')), (0.9, ligado('voltar de ' + t))]
    passos.append((0.5, fim))
    Roteiro(passos).rodar()


def roteiro_perfil():
    """Onde vai o tempo do Python em cada momento (cProfile): o menu parado
    (animacoes continuas), uma troca de tela, o Registro com muitos lotes e o
    LEVEL UP. Grava perfil_*.txt na pasta de saida."""
    import cProfile
    import pstats
    import io
    from datetime import datetime as _dt
    est = {}

    def liga(nome):
        def _f():
            est['nome'] = nome
            est['q0'] = Q[0]
            est['t0'] = time.perf_counter()
            est['p'] = cProfile.Profile()
            est['p'].enable()
        return _f

    def desliga():
        p = est['p']
        p.disable()
        dur = time.perf_counter() - est['t0']
        quadros = max(1, Q[0] - est['q0'])
        s = io.StringIO()
        st = pstats.Stats(p, stream=s).sort_stats('tottime')
        st.print_stats(28)
        tot = sum(v[2] for v in st.stats.values())
        with open(os.path.join(SAIDA, f"perfil_{est['nome']}.txt"), 'w', encoding='utf-8') as f:
            f.write(f"{est['nome']}: {dur:.2f} s, {quadros} quadros, python {tot * 1000 / quadros:.2f} ms por quadro" + chr(10))
            f.write(s.getvalue())
        fase(f"PERFIL {est['nome']}: python {tot * 1000 / quadros:.2f} ms/quadro ({quadros} quadros em {dur:.1f} s)")

    def muitos_lotes():
        a = app()
        for i in range(25):
            a.registros.append([f'Peca {i}', str(20 + i), 60, '', _dt.now().timestamp()])

    def perto_nivel():
        from helpers import calcular_level
        a = app()
        _lv, at, nec = calcular_level(a.total_xp)
        a.total_xp += nec - at - 10

    def lote():
        t = tela()
        t.ids.nome_input.text = 'Short'
        t.ids.qtd_input.text = '40'
        soltar_foco()
        t.adicionar_item()

    def mede_atualizar():
        from telas.registro import TelaRegistro
        from telas.memorias import TelaMemorias
        from telas.ganhos import TelaGanhos
        from telas.calculadora import TelaCalculadora
        from telas.progresso import TelaProgresso
        import animacoes_ui as AU
        for cls in (TelaRegistro, TelaMemorias, TelaGanhos, TelaCalculadora, TelaProgresso, main.MenuPrincipal):
            o = cls.on_enter

            def _m(self, *a, _o=o, _n=cls.__name__, **k):
                t0 = time.perf_counter()
                if os.environ.get('PROF') == _n:            # PROF=TelaMemorias: tempo de cada metodo
                    import types
                    medidos = []
                    for nome in dir(self):
                        f = getattr(type(self), nome, None)
                        if not isinstance(f, types.FunctionType) or nome.startswith('__') or nome == 'on_enter':
                            continue

                        def _t(*aa, _f=f, _nm=nome, **kk):
                            t1 = time.perf_counter()
                            try:
                                return _f(*aa, **kk)
                            finally:
                                medidos.append((_nm, (time.perf_counter() - t1) * 1000))
                        setattr(self, nome, types.MethodType(_t, self))
                    r = _o(self, *a, **k)
                    for nome, _v in medidos:
                        self.__dict__.pop(nome, None)
                    fase('PROF ' + ', '.join(f'{nm} {v:.1f}' for nm, v in medidos))
                else:
                    r = _o(self, *a, **k)
                fase(f'PERFIL {_n}.on_enter: {(time.perf_counter() - t0) * 1000:.1f} ms')
                return r
            cls.on_enter = _m
        of = AU.foto_da_tela

        def _f(*a, **k):
            t0 = time.perf_counter()
            r = of(*a, **k)
            fase(f'PERFIL foto_da_tela: {(time.perf_counter() - t0) * 1000:.1f} ms')
            return r
        AU.foto_da_tela = _f
        orig = TelaRegistro.atualizar

        def _medido(self, *a, **k):
            t0 = time.perf_counter()
            r = orig(self, *a, **k)
            fase(f'PERFIL registro.atualizar: {(time.perf_counter() - t0) * 1000:.1f} ms '
                 f'({len(app().registros)} lotes, num quadro so)')
            return r
        TelaRegistro.atualizar = _medido
        # quanto custa cada cartao (montados 4 por quadro: 4x isso = o quadro)
        for cls, nome in ((TelaMemorias, '_item'), (TelaRegistro, '_make_item')):
            o = getattr(cls, nome)
            soma = {'n': 0, 't': 0.0, 'max': 0.0}

            def _c(self, *a, _o=o, _s=soma, _n=cls.__name__ + '.' + nome, **k):
                t0 = time.perf_counter()
                r = _o(self, *a, **k)
                d = time.perf_counter() - t0
                _s['n'] += 1
                _s['t'] += d
                _s['max'] = max(_s['max'], d)
                if _s['n'] % 10 == 0:
                    fase(f"PERFIL {_n}: {_s['t'] * 1000 / _s['n']:.2f} ms cada (max {_s['max'] * 1000:.2f}, {_s['n']} cartoes)")
                return r
            setattr(cls, nome, _c)
    passos = [(0.01, mede_atualizar), (0.3, lambda: app().mudar_tela('ganhos')), (1.5, lambda: app().mudar_tela('calculadora')),
              (1.5, lambda: app().mudar_tela('progresso')), (1.5, lambda: app().mudar_tela('menu')),
              (2.0, liga('menu_parado')), (4.0, desliga),
              (0.2, liga('troca_de_tela')), (0.01, lambda: app().mudar_tela('memorias')), (0.8, desliga),
              (0.5, muitos_lotes), (0.1, liga('entra_registro_30_lotes')), (0.01, lambda: app().mudar_tela('registro')),
              (1.4, desliga), (0.6, soltar_foco), (0.4, perto_nivel), (0.01, lote),
              (0.8, lambda: setattr(campo_do_popup(), 'text', '3')), (0.2, lambda: apertar('CONFIRMAR')),
              (0.6, soltar_foco), (1.5, liga('level_up')), (3.0, desliga), (0.5, fim)]
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
              # lote enorme (dedo escorregou): o app confere; CORRIGIR volta sem lancar
              (0.3, lambda: (setattr(tela().ids.nome_input, 'text', 'Short'), setattr(tela().ids.qtd_input, 'text', '1800'),
                             soltar_foco(), tela().adicionar_item())),
              (0.9, lambda: foto('m3b-confere-lote')), (0.3, lambda: apertar('CORRIGIR')),
              (0.8, lambda: LOG.setdefault('lotes_depois_corrigir', len(app().registros))),
              (0.6, ir('ganhos')), (2.4, soltar_foco), (0.5, lambda: foto('m4-ganhos')),
              (0.3, lambda: tela().alternar_ajustes(True)), (0.6, lambda: foto('m4b-ajustes-abertos')),
              (0.3, lambda: setattr(tela().ids.rolagem, 'scroll_y', 0)), (0.6, lambda: foto('m4c-rolou-ate-o-fim')),
              (0.3, lambda: tela().alternar_ajustes(False)), (0.3, lambda: setattr(tela().ids.rolagem, 'scroll_y', 1)),
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
    Clock.schedule_once(lambda dt: {'telas': roteiro_telas, 'zap': roteiro_zap, 'varre': roteiro_varre, 'meta': roteiro_meta,
              'anim': roteiro_anim, 'vivo': roteiro_vivo, 'novas': roteiro_novas,
              'mem': roteiro_mem, 'link': roteiro_link,
              'ajustes': roteiro_ajustes, 'toques': roteiro_toques, 'trans': roteiro_trans,
              'perfil': roteiro_perfil, 'polir': roteiro_polir,
              'avisos': roteiro_avisos, 'fluidez': roteiro_fluidez}.get(CENA, roteiro_app)(), 1.0)


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
