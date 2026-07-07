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
}

def tocar_loading_drone():  tocar('loading_drone')
def tocar_erro_firewall():  tocar('erro_firewall')
def tocar_pin_tecla():      tocar('pin_tecla')
def tocar_pin_erro():       tocar('pin_erro')
def tocar_retomada():       tocar('retomada')
def tocar_xp_subindo():     tocar('xp_subindo')
def tocar_level_up():       tocar('level_up')
def tocar_calc_resultado(): tocar('calc_resultado')


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
}


def inicializar():
    """Inicia carregamento de sons em thread background — nao bloqueia o build()."""
    import threading
    t = threading.Thread(target=_inicializar_bg, daemon=True)
    t.start()


def _inicializar_bg():
    """Carrega todos os sons em background. Seguro chamar de qualquer momento."""
    global _usa_winsound
    if sys.platform == 'win32':
        try:
            import winsound
            _usa_winsound = True
            print("[SOM] OK winsound (Windows nativo)")
            return
        except ImportError:
            pass
    try:
        from kivy.core.audio import SoundLoader
        from kivy.utils import platform as _plat

        if _plat == 'android':
            try:
                from kivy.app import App
                from kivy.clock import Clock
                # Aguardar App estar pronto (max 5s)
                import time
                deadline = time.time() + 5
                _app = None
                while time.time() < deadline:
                    _app = App.get_running_app()
                    if _app and hasattr(_app, 'user_data_dir'):
                        break
                    time.sleep(0.1)
                base_dir = _app.user_data_dir if _app else tempfile.gettempdir()
            except Exception:
                base_dir = tempfile.gettempdir()
        else:
            base_dir = tempfile.gettempdir()

        carregados = 0
        for nome, notas in _RECEITAS.items():
            try:
                wav  = _wav(notas)
                path = os.path.join(base_dir, f'tf_{nome}.wav')
                with open(path, 'wb') as f:
                    f.write(wav)
                _tmp_files.append(path)
                s = SoundLoader.load(path)
                if s:
                    s.volume = 0.60
                    _sons[nome] = s
                    carregados += 1
            except Exception as ex:
                print(f"[SOM] falha em '{nome}': {ex}")
        print(f"[SOM] OK {carregados}/{len(_RECEITAS)} sons carregados")
    except Exception as ex:
        print(f"[SOM] indisponivel: {ex}")


def tocar(acao: str):
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
    s = _sons.get(acao)
    if s:
        try: s.stop(); s.play()
        except Exception: pass


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
