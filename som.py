"""
som.py — TraveteFocus
Sintetizador de efeitos em Python puro (sem arquivos de audio no APK):
camadas de onda (seno, triangulo, quadrada, serra, sino metalico, ruido) com
deslize de frequencia, envelope, filtro, vibrato/tremolo e eco.

- Os WAV sao gerados numa thread em segundo plano e guardados em disco
  (nome com hash da receita): so no 1o uso de cada versao do app.
- SoundLoader.load() roda SEMPRE na thread principal (no Android, carregar
  audio fora dela derruba o app sem mensagem).
- Cada som tem ate 3 copias carregadas: golpes em sequencia (combo) nao se
  cortam.
"""
import hashlib
import math
import os
import random
import struct
import tempfile
import threading
import time
from array import array

TAXA = 22050
_sons = {}            # acao -> [Sound, ...]
_falhas = set()
_prontos = {}         # acao -> caminho do wav ja gerado
_trava = threading.Lock()
_dir = [None]
_tmp_files = []
_MAX_COPIAS = 3


# ═══════════════════════════════════════════════════════════════════
#  SINTETIZADOR
# ═══════════════════════════════════════════════════════════════════
def S(f, dur, vol, ini=0.0, f1=None, tipo='seno', harm=None, atk=0.004,
      queda=3.0, vib=None, trem=None, lp=None):
    """Camada tonal. f->f1 desliza (exponencial). harm=[(mult, amp)]."""
    return dict(tipo=tipo, f=f, f1=f1, dur=dur, vol=vol, ini=ini, harm=harm,
                atk=atk, queda=queda, vib=vib, trem=trem, lp=lp)


def R(dur, vol, ini=0.0, lp=(0.05, 0.4), hp=False, atk=0.01, queda=2.5, trem=None):
    """Camada de ruido filtrado (whoosh, impacto, raspado)."""
    return dict(tipo='ruido', dur=dur, vol=vol, ini=ini, lp=lp, hp=hp,
                atk=atk, queda=queda, trem=trem)


SINO = [(1, 1.0), (2.0, 0.35), (3.0, 0.16), (4.16, 0.08)]
METAL = [(1, 1.0), (2.76, 0.45), (5.4, 0.22), (8.93, 0.08)]
CRISTAL = [(1, 1.0), (2.01, 0.38), (3.0, 0.25), (4.2, 0.14), (5.43, 0.06)]


def _onda(tipo, fase):
    if tipo == 'tri':
        x = (fase / (2 * math.pi)) % 1.0
        return 4 * x - 1 if x < 0.5 else 3 - 4 * x
    if tipo == 'quad':
        return 0.6 if math.sin(fase) >= 0 else -0.6
    if tipo == 'serra':
        return ((fase / math.pi) % 2.0) - 1.0
    return math.sin(fase)


def _camada(buf, c, pausa):
    n0 = int(c['ini'] * TAXA)
    n = int(c['dur'] * TAXA)
    if n <= 0:
        return
    vol, atk = c['vol'], max(1, int(c['atk'] * TAXA))
    queda = c['queda']
    fim = min(len(buf), n0 + n)
    trem = c.get('trem')
    lp = c.get('lp')
    y = 0.0
    if c['tipo'] == 'ruido':
        hp = c.get('hp')
        rnd = random.random
        for i in range(n0, fim):
            k = i - n0
            u = k / n
            a = lp[0] + (lp[1] - lp[0]) * u
            x = rnd() * 2 - 1
            y += a * (x - y)
            s = (x - y) if hp else y
            env = k / atk if k < atk else math.exp(-queda * (k - atk) / n)
            if n - k < 110:
                env *= (n - k) / 110.0
            if trem:
                env *= 1 - trem[1] * (0.5 + 0.5 * math.sin(2 * math.pi * trem[0] * k / TAXA))
            buf[i] += s * env * vol * (2.2 if not hp else 1.0)
            if k & 4095 == 0:
                pausa()
        return
    f0 = c['f']
    f1 = c['f1'] or f0
    harm = c['harm'] or [(1, 1.0)]
    tot = sum(h[1] for h in harm)
    fases = [0.0] * len(harm)
    vib = c.get('vib')
    tipo = c['tipo']
    dois_pi = 2 * math.pi
    razao = math.log(f1 / f0) if f1 != f0 else 0.0
    for i in range(n0, fim):
        k = i - n0
        u = k / n
        f = f0 * math.exp(razao * u) if razao else f0
        if vib:
            f *= 2 ** (vib[1] * math.sin(dois_pi * vib[0] * k / TAXA) / 12.0)
        s = 0.0
        for j, (m, amp) in enumerate(harm):
            fases[j] += dois_pi * f * m / TAXA
            s += (_onda(tipo, fases[j]) if j == 0 else math.sin(fases[j])) * amp
        s /= tot
        if lp:
            a = lp[0] + (lp[1] - lp[0]) * u
            y += a * (s - y)
            s = y * 3.0
        env = k / atk if k < atk else math.exp(-queda * (k - atk) / n)
        if n - k < 110:
            env *= (n - k) / 110.0
        if trem:
            env *= 1 - trem[1] * (0.5 + 0.5 * math.sin(dois_pi * trem[0] * k / TAXA))
        buf[i] += s * env * vol
        if k & 4095 == 0:
            pausa()


def _renderizar(receita, pausa=lambda: None):
    if isinstance(receita, list):              # formato antigo: [(freq, dur, vol)]
        receita = _de_notas(receita)
    camadas = receita['camadas']
    eco = receita.get('eco')
    total = max(c['ini'] + c['dur'] for c in camadas)
    if eco:
        total += eco[0] * 6
    buf = [0.0] * (int(total * TAXA) + 1)
    for c in camadas:
        _camada(buf, c, pausa)
    if eco:
        d, fb = int(eco[0] * TAXA), eco[1]
        for i in range(d, len(buf)):
            buf[i] += buf[i - d] * fb
    ganho = receita.get('ganho', 1.0)
    saida = array('h', [0]) * len(buf)
    t1 = math.tanh(1.4)
    for i, v in enumerate(buf):              # saturacao suave (sem estalo)
        saida[i] = int(32000 * math.tanh(1.4 * v * ganho) / t1 * 0.92)
    # corta silencio do fim
    fim = len(saida)
    while fim > 1 and abs(saida[fim - 1]) < 40:
        fim -= 1
    dados = saida[:max(fim, 64)].tobytes()
    cab = struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', 36 + len(dados), b'WAVE',
                      b'fmt ', 16, 1, 1, TAXA, TAXA * 2, 2, 16, b'data', len(dados))
    return cab + dados


def _de_notas(notas, eco=(0.085, 0.22)):
    """Receita antiga (sequencia de notas) com timbre de sino e eco."""
    cam, t = [], 0.0
    for f, dur, vol in notas:
        if f > 0:
            cam.append(S(f, dur * 1.9 + 0.05, vol * 0.8, ini=t, harm=SINO, queda=3.6))
        t += dur
    return dict(camadas=cam or [S(440, 0.01, 0.0)], eco=eco)


# ═══════════════════════════════════════════════════════════════════
#  RECEITAS
# ═══════════════════════════════════════════════════════════════════
_NOTAS_TITULO = (659.3, 784.0, 880.0, 987.8, 1174.7)     # pentatonica de mi (sobe)

_RECEITAS = {
    # ── interface ────────────────────────────────────────────────────
    'click':          dict(camadas=[S(1650, 0.035, 0.24, f1=1250, queda=5),
                                    R(0.012, 0.10, lp=(0.6, 0.6), hp=True, queda=6)]),
    'pin_tecla':      dict(camadas=[S(1320, 0.06, 0.22, harm=[(1, 1), (2, 0.3)], queda=5),
                                    S(2640, 0.025, 0.06)]),
    'pin_erro':       dict(camadas=[S(150, 0.24, 0.30, f1=85, tipo='quad', queda=2),
                                    S(75, 0.22, 0.26, queda=2)]),
    'erro':           dict(camadas=[S(230, 0.08, 0.28, tipo='quad', queda=3),
                                    S(230, 0.08, 0.28, tipo='quad', ini=0.11, queda=3)]),
    'erro_firewall':  dict(camadas=[S(880, 0.13, 0.20, f1=620, tipo='quad', queda=1.5),
                                    S(880, 0.13, 0.20, f1=620, tipo='quad', ini=0.17, queda=1.5),
                                    S(520, 0.34, 0.26, f1=260, tipo='serra', ini=0.34, lp=(0.2, 0.05), queda=1.8),
                                    R(0.6, 0.10, lp=(0.02, 0.01), atk=0.02, queda=1.5)]),
    'loading_drone':  dict(camadas=[S(55, 1.6, 0.30, f1=110, tipo='serra', lp=(0.02, 0.09),
                                      atk=0.35, queda=1.1, trem=(6, 0.3)),
                                    S(110, 1.6, 0.12, f1=220, atk=0.45, queda=1.4),
                                    R(1.6, 0.07, lp=(0.01, 0.07), atk=0.5, queda=1.2)]),
    'retomada':       dict(camadas=[S(f, 0.55, 0.16, ini=0.07 * i, harm=SINO, queda=3.2)
                                    for i, f in enumerate((220, 277.2, 329.6, 440, 554.4, 659.3, 880))],
                           eco=(0.1, 0.25)),
    'delete':         dict(camadas=[S(600, 0.32, 0.22, f1=90, tipo='serra', lp=(0.3, 0.04), queda=2.5),
                                    R(0.26, 0.18, lp=(0.5, 0.04), queda=3)]),
    'wipe':           dict(camadas=[S(440, 0.65, 0.24, f1=50, tipo='serra', lp=(0.4, 0.03), queda=2.2),
                                    R(0.75, 0.32, lp=(0.6, 0.02), queda=2.5),
                                    S(55, 0.5, 0.3, queda=2.5)], eco=(0.12, 0.25)),
    'transicao':      dict(camadas=[R(0.2, 0.26, lp=(0.04, 0.35), atk=0.08, queda=3),
                                    S(1400, 0.28, 0.05, harm=SINO, ini=0.1, queda=5)]),

    # ── Kirito ───────────────────────────────────────────────────────
    # Elucidator: corte pesado (whoosh + baque + ressonancia de metal)
    'corte':          dict(camadas=[R(0.24, 0.55, lp=(0.03, 0.55), atk=0.07, queda=3.5),
                                    S(150, 0.12, 0.34, f1=55, ini=0.08, queda=4),
                                    S(1850, 0.55, 0.10, harm=METAL, ini=0.085, queda=4)],
                           eco=(0.07, 0.18)),
    # Dark Repulser: corte cristalino (mais agudo, brilho de cristal)
    'corte2':         dict(camadas=[R(0.18, 0.42, lp=(0.1, 0.8), hp=True, atk=0.05, queda=4),
                                    S(2637, 0.75, 0.12, harm=CRISTAL, ini=0.06, queda=3, vib=(7, 0.15)),
                                    S(1318, 0.4, 0.07, ini=0.06, queda=4)],
                           eco=(0.09, 0.25), ganho=1.3),
    # sacar a segunda espada: raspado + "shing" longo
    'sacar':          dict(camadas=[R(0.3, 0.24, lp=(0.3, 0.9), hp=True, atk=0.12, queda=2.5),
                                    S(2200, 0.95, 0.16, f1=2350, harm=CRISTAL, ini=0.18, queda=3, vib=(9, 0.1))],
                           eco=(0.11, 0.3), ganho=1.8),
    'pulo':           dict(camadas=[R(0.28, 0.26, lp=(0.02, 0.25), atk=0.1, queda=2.5)]),
    # polegar empurrando a guarda (koiguchi): estalo metalico antes do saque
    'koiguchi':       dict(camadas=[S(2200, 0.07, 0.22, harm=METAL, queda=6),
                                    R(0.03, 0.14, lp=(0.7, 0.7), hp=True, queda=5)], ganho=1.4),
    'pouso':          dict(camadas=[S(95, 0.14, 0.38, f1=45, queda=4),
                                    R(0.08, 0.2, lp=(0.1, 0.02), queda=4)]),
    'surge':          dict(camadas=[S(1760, 0.25, 0.08, harm=SINO, queda=5),
                                    S(2637, 0.3, 0.07, ini=0.06, harm=SINO, queda=5),
                                    R(0.05, 0.06, lp=(0.8, 0.8), hp=True, queda=4)], eco=(0.08, 0.2), ganho=2.4),
    'susto':          dict(camadas=[S(520, 0.13, 0.12, f1=820, queda=3),
                                    S(700, 0.1, 0.06, ini=0.05, f1=1000, queda=4)], ganho=1.6),
    # golpe final: carga (sobe e para seco) e o corte-atravessado
    'carga':          dict(camadas=[S(110, 0.9, 0.2, f1=440, tipo='serra', lp=(0.02, 0.25),
                                      atk=0.65, queda=0.15, trem=(14, 0.4)),
                                    R(0.9, 0.14, lp=(0.01, 0.5), atk=0.7, queda=0.15)]),
    'golpe_final':    dict(camadas=[R(0.35, 0.6, lp=(0.05, 0.7), atk=0.03, queda=3),
                                    S(2400, 0.9, 0.12, harm=METAL, ini=0.03, queda=3)],
                           eco=(0.1, 0.22)),
    'embainhar':      dict(camadas=[R(0.14, 0.2, lp=(0.5, 0.2), hp=True, atk=0.08, queda=3),
                                    S(2900, 0.05, 0.25, ini=0.14, queda=8),
                                    S(1450, 0.09, 0.2, ini=0.145, queda=7)]),
    # a frase explode depois do embainhar: baque + acorde brilhante
    'titulo':         dict(camadas=[S(60, 0.9, 0.5, f1=35, atk=0.005, queda=3),
                                    R(0.6, 0.45, lp=(0.6, 0.02), atk=0.002, queda=3),
                                    S(164.8, 1.8, 0.10, tipo='serra', lp=(0.05, 0.03), atk=0.1, queda=1.5)]
                           + [S(f, 2.0, 0.10, ini=0.02 + 0.03 * i, harm=SINO, queda=2.5)
                              for i, f in enumerate((659.3, 830.6, 987.8, 1318.5))],
                           eco=(0.13, 0.33)),

    # ── melodias antigas (agora com timbre de sino + eco) ─────────────
    'add':            [(440, 0.060, 0.30), (554, 0.060, 0.35), (659, 0.100, 0.40)],
    'salvar':         [(880, 0.035, 0.25), (1100, 0.060, 0.30)],
    'abrir_periodo':  [(220, 0.060, 0.30), (330, 0.060, 0.35), (440, 0.060, 0.35), (660, 0.120, 0.40)],
    'fechar_periodo': [(523, 0.070, 0.35), (659, 0.070, 0.40), (784, 0.070, 0.40), (1047, 0.070, 0.45), (1319, 0.200, 0.50)],
    'finalizar':      [(523, 0.090, 0.35), (659, 0.090, 0.38), (784, 0.090, 0.40),
                       (1047, 0.090, 0.42), (0, 0.030, 0.00),
                       (784, 0.060, 0.38), (1047, 0.060, 0.42), (1319, 0.300, 0.50)],
    'xp_subindo':     [(300, 0.050, 0.28), (380, 0.050, 0.30), (480, 0.050, 0.32),
                       (600, 0.050, 0.34), (760, 0.050, 0.36), (960, 0.050, 0.38),
                       (1200, 0.080, 0.40)],
    'level_up':       [(262, 0.100, 0.35), (330, 0.100, 0.38), (392, 0.100, 0.40),
                       (523, 0.100, 0.42), (0, 0.040, 0.00),
                       (392, 0.080, 0.38), (494, 0.080, 0.40), (587, 0.080, 0.42),
                       (784, 0.380, 0.50)],
    'calc_resultado': [(1047, 0.060, 0.35), (1319, 0.060, 0.38), (1568, 0.180, 0.42)],
    'xp':             [(784, 0.050, 0.30), (988, 0.050, 0.35), (1319, 0.100, 0.40)],
}
# uma nota por trecho da frase escrita pelo Kirito (sobe a escala)
for _i, _f in enumerate(_NOTAS_TITULO):
    _RECEITAS[f'nota{_i + 1}'] = dict(camadas=[S(_f, 1.1, 0.16, harm=SINO, queda=3.5),
                                               S(_f * 2, 0.4, 0.04, ini=0.01, queda=5)],
                                      eco=(0.12, 0.3), ganho=1.9)

# ordem de geracao: o que toca primeiro na abertura vem antes
_ORDEM = ['click', 'loading_drone', 'erro_firewall', 'pin_tecla', 'pin_erro', 'surge', 'koiguchi',
          'susto', 'retomada', 'pulo', 'corte', 'nota1', 'sacar', 'corte2', 'nota2',
          'nota3', 'nota4', 'carga', 'golpe_final', 'nota5', 'embainhar', 'titulo',
          'pouso', 'transicao']


def _nome_arquivo(acao):
    h = hashlib.md5((repr(_RECEITAS[acao]) + str(TAXA)).encode()).hexdigest()[:8]
    return f'tf2_{acao}_{h}.wav'


def _data_dir():
    if _dir[0]:
        return _dir[0]
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app and hasattr(app, 'user_data_dir'):
            return app.user_data_dir
    except Exception:
        pass
    return tempfile.gettempdir()


def _gerar(acao, pausa=lambda: None):
    """Gera (se preciso) o WAV da acao e devolve o caminho."""
    with _trava:
        if acao in _prontos:
            return _prontos[acao]
    d = _data_dir()
    caminho = os.path.join(d, _nome_arquivo(acao))
    if not os.path.exists(caminho):
        os.makedirs(d, exist_ok=True)
        dados = _renderizar(_RECEITAS[acao], pausa)
        tmp = caminho + f'.{threading.get_ident()}.tmp'
        with open(tmp, 'wb') as f:
            f.write(dados)
        os.replace(tmp, caminho)
    with _trava:
        _prontos[acao] = caminho
    return caminho


def _pre_gerar():
    """Thread de fundo: gera todos os WAV que faltam (pausas curtas deixam a
    interface respirar) e apaga os de versoes antigas das receitas."""
    try:
        d = _data_dir()
        atuais = {_nome_arquivo(a) for a in _RECEITAS}
        try:
            for f in os.listdir(d):
                if (f.startswith('tf2_') or f.startswith('tf_')) and f.endswith('.wav') and f not in atuais:
                    os.remove(os.path.join(d, f))
        except Exception:
            pass
        ordem = _ORDEM + [a for a in _RECEITAS if a not in _ORDEM]
        for acao in ordem:
            try:
                _gerar(acao, pausa=lambda: time.sleep(0.001))
            except Exception as e:
                print(f"[SOM] gerar '{acao}': {e}")
    except Exception as e:
        print(f"[SOM] pre-geracao: {e}")


def inicializar():
    """Chamado no build(): guarda a pasta de dados e comeca a gerar os sons
    em segundo plano (so geracao de bytes: o SoundLoader fica na thread
    principal, dentro de tocar())."""
    try:
        _dir[0] = _data_dir()
        threading.Thread(target=_pre_gerar, daemon=True).start()
    except Exception as e:
        print(f"[SOM] inicializar: {e}")


def _carregar(acao):
    """SoundLoader na thread principal (se o WAV ainda nao existe, gera agora)."""
    if acao in _falhas or acao not in _RECEITAS:
        _falhas.add(acao)
        return None
    try:
        from kivy.core.audio import SoundLoader
        caminho = _gerar(acao)
        s = SoundLoader.load(caminho)
        if s:
            s.volume = 0.7
            return s
    except Exception as ex:
        print(f"[SOM] falha ao carregar '{acao}': {ex}")
    _falhas.add(acao)
    return None


def tocar(acao: str):
    """Toca um som (ate 3 copias simultaneas do mesmo som)."""
    try:
        copias = _sons.setdefault(acao, [])
        livre = next((s for s in copias if s.state != 'play'), None)
        if livre is None:
            if len(copias) < _MAX_COPIAS and acao not in _falhas:
                livre = _carregar(acao)
                if livre:
                    copias.append(livre)
            if livre is None and copias:
                livre = copias.pop(0)            # reusa a mais antiga
                copias.append(livre)
                livre.stop()
        if livre:
            livre.play()
    except Exception as e:
        print(f"[SOM] tocar '{acao}': {e}")


def tocar_loading_drone():  tocar('loading_drone')
def tocar_erro_firewall():  tocar('erro_firewall')
def tocar_pin_tecla():      tocar('pin_tecla')
def tocar_pin_erro():       tocar('pin_erro')
def tocar_retomada():       tocar('retomada')
def tocar_xp_subindo():     tocar('xp_subindo')
def tocar_level_up():       tocar('level_up')
def tocar_calc_resultado(): tocar('calc_resultado')
def tocar_corte():          tocar('corte')
def tocar_click():          tocar('click')
def tocar_add():            tocar('add')
def tocar_finalizar():      tocar('finalizar')
def tocar_delete():         tocar('delete')
def tocar_salvar():         tocar('salvar')
def tocar_abrir_periodo():  tocar('abrir_periodo')
def tocar_fechar_periodo(): tocar('fechar_periodo')
def tocar_erro():           tocar('erro')
def tocar_xp():             tocar('xp')
def tocar_wipe():           tocar('wipe')


def limpar():
    for p in _tmp_files:
        try:
            if os.path.exists(p):
                os.unlink(p)
        except Exception:
            pass
