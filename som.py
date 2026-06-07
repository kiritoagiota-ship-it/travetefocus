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
    'click':          [(880, 0.040, 0.35)],
    'add':            [(440, 0.060, 0.30), (554, 0.060, 0.35), (659, 0.100, 0.40)],
    'finalizar':      [(523, 0.080, 0.35), (659, 0.080, 0.40), (784, 0.080, 0.40), (1047, 0.180, 0.45)],
    'delete':         [(600, 0.040, 0.40), (400, 0.040, 0.40), (200, 0.080, 0.35), (100, 0.060, 0.25)],
    'salvar':         [(880, 0.035, 0.25), (1100, 0.060, 0.30)],
    'abrir_periodo':  [(220, 0.060, 0.30), (330, 0.060, 0.35), (440, 0.060, 0.35), (660, 0.120, 0.40)],
    'fechar_periodo': [(523, 0.070, 0.35), (659, 0.070, 0.40), (784, 0.070, 0.40), (1047, 0.070, 0.45), (1319, 0.200, 0.50)],
    'erro':           [(200, 0.060, 0.45), (0, 0.030, 0.00), (200, 0.060, 0.45)],
    'xp':             [(784, 0.050, 0.30), (988, 0.050, 0.35), (1319, 0.100, 0.40)],
    'wipe':           [(440, 0.050, 0.40), (330, 0.050, 0.40), (220, 0.050, 0.40), (110, 0.150, 0.45)],
}

_WINSOUND_MAP = {
    'click':          [(880, 45)],
    'add':            [(440, 60), (659, 100)],
    'finalizar':      [(523, 80), (659, 80), (1047, 180)],
    'delete':         [(400, 60), (200, 80), (100, 60)],
    'salvar':         [(880, 35), (1100, 60)],
    'abrir_periodo':  [(330, 60), (660, 120)],
    'fechar_periodo': [(523, 70), (784, 70), (1319, 200)],
    'erro':           [(200, 60), (200, 60)],
    'xp':             [(784, 50), (1319, 100)],
    'wipe':           [(440, 50), (220, 50), (110, 150)],
}


def inicializar():
    global _usa_winsound
    if sys.platform == 'win32':
        try:
            import winsound
            _usa_winsound = True
            print("[SOM] ✓ winsound (Windows nativo)")
            return
        except ImportError:
            pass
    try:
        from kivy.core.audio import SoundLoader
        from kivy.utils import platform

        # No Android, /tmp pode ser inacessível ao MediaPlayer do sistema.
        # user_data_dir aponta para o diretório privado do app, sempre gravável.
        if platform == 'android':
            try:
                from kivy.app import App
                _app = App.get_running_app()
                base_dir = _app.user_data_dir if _app else tempfile.gettempdir()
            except Exception:
                base_dir = tempfile.gettempdir()
        else:
            base_dir = tempfile.gettempdir()

        for nome, notas in _RECEITAS.items():
            wav  = _wav(notas)
            path = os.path.join(base_dir, f'tf_{nome}.wav')
            with open(path, 'wb') as f:
                f.write(wav)
            _tmp_files.append(path)
            s = SoundLoader.load(path)
            if s:
                s.volume = 0.60
                _sons[nome] = s
        print(f"[SOM] ✓ {len(_sons)} sons carregados")
    except Exception as e:
        print(f"[SOM] indisponível: {e}")


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
