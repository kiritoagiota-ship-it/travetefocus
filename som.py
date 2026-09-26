"""
som.py — TraveteFocus
Sons criativos e temáticos para cada ação do app.
Windows: winsound em thread separada (não bloqueia UI)
Android: WAV sintético via SoundLoader
"""
import struct
import math
import tempfile
import os
import sys
import threading

_sons         = {}
_usa_winsound = False
_tmp_files    = []


def _wav(notas, taxa=44100):
    dados = []
    for freq, dur, vol in notas:
        frames = int(taxa * dur)
        for i in range(frames):
            t    = i / taxa
            fade = 1.0 - (i / frames) ** 0.5
            if freq == 0:
                amostra = 0
            else:
                amostra = math.sin(2 * math.pi * freq * t) * fade * vol
            dados.append(max(-32767, min(32767, int(amostra * 32767))))
    data_bytes = struct.pack(f'<{len(dados)}h', *dados)
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + len(data_bytes), b'WAVE',
        b'fmt ', 16, 1, 1, taxa, taxa * 2, 2, 16,
        b'data', len(data_bytes))
    return header + data_bytes


_RECEITAS = {
    # ── Sons existentes ───────────────────────────────────────────────
    'click':          [(880, 0.040, 0.35)],
    'add':            [(440, 0.060, 0.30), (554, 0.060, 0.35), (659, 0.100, 0.40)],
    'delete':         [(600, 0.040, 0.40), (400, 0.040, 0.40), (200, 0.080, 0.35), (100, 0.060, 0.25)],
    'salvar':         [(880, 0.035, 0.25), (1100, 0.060, 0.30)],
    'abrir_periodo':  [(220, 0.060, 0.30), (330, 0.060, 0.35), (440, 0.060, 0.35), (660, 0.120, 0.40)],
    'fechar_periodo': [(523, 0.070, 0.35), (659, 0.070, 0.40), (784, 0.070, 0.40), (1047, 0.070, 0.45), (1319, 0.200, 0.50)],
    'wipe':           [(440, 0.050, 0.40), (330, 0.050, 0.40), (220, 0.050, 0.40), (110, 0.150, 0.45)],

    # ── Sons novos ────────────────────────────────────────────────────

    # Barra de loading subindo — drone suave pulsante (máquina iniciando)
    'loading_drone':  [(80, 0.120, 0.20), (100, 0.120, 0.22), (120, 0.120, 0.24),
                       (80, 0.120, 0.22), (100, 0.120, 0.24), (120, 0.120, 0.26),
                       (80, 0.100, 0.24), (110, 0.100, 0.28), (140, 0.180, 0.30)],

    # Erro / firewall bloqueado — 3 beeps descendentes urgentes
    'erro_firewall':  [(500, 0.080, 0.50), (0, 0.025, 0.00),
                       (380, 0.080, 0.55), (0, 0.025, 0.00),
                       (220, 0.140, 0.60)],

    # Digitação do PIN — blip eletrônico curto por tecla
    'pin_tecla':      [(1200, 0.030, 0.28)],

    # PIN incorreto — buzz grave
    'pin_erro':       [(100, 0.080, 0.50), (80, 0.120, 0.55)],

    # Retomada após PIN correto — arpeggio ascendente "sistema voltando"
    'retomada':       [(220, 0.080, 0.30), (277, 0.080, 0.33), (330, 0.080, 0.36),
                       (440, 0.080, 0.38), (554, 0.080, 0.40), (659, 0.120, 0.42),
                       (880, 0.200, 0.45)],

    # Finalizar dia — fanfare game (missão completada)
    'finalizar':      [(523, 0.090, 0.35), (659, 0.090, 0.38), (784, 0.090, 0.40),
                       (1047, 0.090, 0.42), (0, 0.030, 0.00),
                       (784, 0.060, 0.38), (1047, 0.060, 0.42), (1319, 0.300, 0.50)],

    # XP subindo — sweep ascendente rápido (sensação de enchendo)
    'xp_subindo':     [(300, 0.050, 0.28), (380, 0.050, 0.30), (480, 0.050, 0.32),
                       (600, 0.050, 0.34), (760, 0.050, 0.36), (960, 0.050, 0.38),
                       (1200, 0.080, 0.40)],

    # Level up — fanfare RPG clássico (4 notas ascendentes + acorde final)
    'level_up':       [(262, 0.100, 0.35), (330, 0.100, 0.38), (392, 0.100, 0.40),
                       (523, 0.100, 0.42), (0, 0.040, 0.00),
                       (392, 0.080, 0.38), (494, 0.080, 0.40), (587, 0.080, 0.42),
                       (784, 0.380, 0.50)],

    # Calculadora resultado — ding metálico satisfatório
    'calc_resultado': [(1047, 0.060, 0.35), (1319, 0.060, 0.38), (1568, 0.180, 0.42)],

    # Erro genérico (campo vazio etc)
    'erro':           [(200, 0.060, 0.45), (0, 0.030, 0.00), (200, 0.060, 0.45)],

    # XP ganho (add lote)
    'xp':             [(784, 0.050, 0.30), (988, 0.050, 0.35), (1319, 0.100, 0.40)],

    # Corte de espada — swoosh descendente rapido + ressonancia metalica
    'corte':          [(2400, 0.018, 0.18), (1800, 0.018, 0.26), (1300, 0.020, 0.30),
                       (900, 0.024, 0.30), (600, 0.030, 0.26), (380, 0.040, 0.20),
                       (0, 0.010, 0.00), (3100, 0.070, 0.10)],

    # Sacar a segunda espada — "shing" metalico subindo
    'sacar':          [(1400, 0.020, 0.14), (2100, 0.025, 0.22), (2900, 0.040, 0.28),
                       (3400, 0.140, 0.16)],

    # Golpe final em X — impacto grave + brilho agudo longo
    'golpe_final':    [(160, 0.040, 0.45), (120, 0.050, 0.40), (0, 0.010, 0.00),
                       (2600, 0.050, 0.26), (1900, 0.080, 0.24), (1300, 0.220, 0.18)],
}

def tocar_loading_drone():  tocar('loading_drone')
def tocar_erro_firewall():  tocar('erro_firewall')
def tocar_pin_tecla():      tocar('pin_tecla')
def tocar_pin_erro():       tocar('pin_erro')
def tocar_retomada():       tocar('retomada')
def tocar_xp_subindo():     tocar('xp_subindo')
def tocar_level_up():       tocar('level_up')
def tocar_calc_resultado(): tocar('calc_resultado')
def tocar_corte():          tocar('corte')


_WINSOUND_MAP = {
    'click':           [(880, 45)],
    'add':             [(440, 60), (659, 100)],
    'finalizar':       [(523, 90), (659, 90), (784, 90), (1047, 90), (1319, 300)],
    'delete':          [(400, 60), (200, 80), (100, 60)],
    'salvar':          [(880, 35), (1100, 60)],
    'abrir_periodo':   [(330, 60), (660, 120)],
    'fechar_periodo':  [(523, 70), (784, 70), (1319, 200)],
    'erro':            [(200, 60), (200, 60)],
    'erro_firewall':   [(500, 80), (380, 80), (220, 140)],
    'xp':              [(784, 50), (1319, 100)],
    'xp_subindo':      [(300, 50), (600, 50), (1200, 80)],
    'level_up':        [(262, 100), (330, 100), (523, 100), (784, 380)],
    'calc_resultado':  [(1047, 60), (1319, 60), (1568, 180)],
    'loading_drone':   [(80, 120), (100, 120), (120, 180)],
    'retomada':        [(220, 80), (440, 80), (659, 80), (880, 200)],
    'pin_tecla':       [(1200, 30)],
    'pin_erro':        [(100, 80), (80, 120)],
    'wipe':            [(440, 50), (220, 50), (110, 150)],
    'corte':           [(1800, 20), (900, 25), (400, 40)],
    'sacar':           [(2100, 25), (3000, 40), (3400, 120)],
    'golpe_final':     [(160, 60), (2600, 50), (1300, 200)],
}


def inicializar():
    """
    No-op intencional: sons carregam lazy na primeira chamada.
    SoundLoader.load() DEVE rodar no main thread do Android.
    Chamar de thread background causa crash nativo silencioso.
    """
    pass  # lazy loading via _carregar() em tocar()


def _data_dir():
    """Retorna diretório para salvar WAV temporários."""
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app and hasattr(app, 'user_data_dir'):
            return app.user_data_dir
    except Exception:
        pass
    return tempfile.gettempdir()


_falhas = set()  # sons que falharam — nao tentar de novo


def _carregar(acao):
    """
    Gera WAV em Python puro e carrega com SoundLoader.
    Chamado no main thread na primeira vez que o som é pedido.
    """
    if acao in _falhas:
        return None
    notas = _RECEITAS.get(acao)
    if notas is None:
        _falhas.add(acao)
        return None
    try:
        from kivy.core.audio import SoundLoader
        wav  = _wav(notas)
        d    = _data_dir()
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, f'tf_{acao}.wav')
        with open(path, 'wb') as f:
            f.write(wav)
        som = SoundLoader.load(path)
        if som:
            som.volume = 0.60
            _sons[acao]  = som
            return som
        _falhas.add(acao)
        return None
    except Exception as ex:
        print(f"[SOM] falha ao carregar '{acao}': {ex}")
        _falhas.add(acao)
        return None



def tocar(acao: str):
    """Toca um som. Se ainda nao foi carregado, carrega agora (lazy)."""
    if _usa_winsound:
        seq = _WINSOUND_MAP.get(acao, [(880, 45)])
        def _beep():
            try:
                import winsound
                for freq, dur in seq:
                    if freq > 0:
                        winsound.Beep(freq, dur)
            except Exception:
                pass
        threading.Thread(target=_beep, daemon=True).start()
        return

    # Lazy load: carrega no main thread se ainda nao existe
    som_obj = _sons.get(acao)
    if som_obj is None and acao not in _falhas:
        som_obj = _carregar(acao)
    if som_obj:
        try:
            # Verificar estado antes de stop — evita glitch em alguns drivers
            if som_obj.state == 'play':
                som_obj.stop()
            som_obj.play()
        except Exception:
            pass



def tocar_click():         tocar('click')
def tocar_add():           tocar('add')
def tocar_finalizar():     tocar('finalizar')
def tocar_delete():        tocar('delete')
def tocar_salvar():        tocar('salvar')
def tocar_abrir_periodo(): tocar('abrir_periodo')
def tocar_fechar_periodo(): tocar('fechar_periodo')
def tocar_erro():          tocar('erro')
def tocar_xp():            tocar('xp')
def tocar_wipe():          tocar('wipe')


def limpar():
    for p in _tmp_files:
        try:
            if os.path.exists(p): os.unlink(p)
        except Exception: pass