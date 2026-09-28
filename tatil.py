"""
tatil.py — TraveteFocus
Resposta tatil (vibracao curtinha) no Android, com os efeitos prontos do
proprio sistema (os mesmos do teclado do celular):

  tecla()      toquezinho seco a cada tecla (teclado do app, calculadora)
  botao()      toque leve em qualquer botao
  confirmar()  "tum-tum" ao enviar / salvar
  erro()       tres toquinhos rapidos (faltou algo, conta invalida)
  forte()      um tranco (apagar)
  vitoria()    tres pulsos subindo (finalizar o dia, fechar periodo)
  pulso(ms)    uma vibracao de `ms` milissegundos

Respeita o liga/desliga do app (App.vibracao). Fora do Android nao faz nada.
Nunca levanta excecao (vibrar nao pode derrubar o app).
"""
from kivy.app import App
from kivy.utils import platform

_V = None            # (vibrador, VibrationEffect ou None, versao do Android); False = sem vibrador

# efeitos prontos do Android 10+ (VibrationEffect.EFFECT_*)
_CLICK, _DOUBLE_CLICK, _TICK, _HEAVY_CLICK = 0, 1, 2, 5


def _vibrador():
    global _V
    if _V is None:
        _V = False
        if platform != 'android':
            return None
        try:
            from jnius import autoclass, cast
            PA = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            sdk = autoclass('android.os.Build$VERSION').SDK_INT
            vib = cast('android.os.Vibrator',
                       PA.mActivity.getSystemService(Context.VIBRATOR_SERVICE))
            if vib is None or not vib.hasVibrator():
                return None
            VE = autoclass('android.os.VibrationEffect') if sdk >= 26 else None
            _V = (vib, VE, sdk)
        except Exception as e:
            print(f"[tatil] sem vibrador: {e}")
    return _V or None


def ligado():
    try:
        app = App.get_running_app()
        return bool(getattr(app, 'vibracao', True)) if app is not None else True
    except Exception:
        return True


def _tocar(pronto, ms, amplitude=255):
    """Efeito pronto do Android 10+ (`pronto`); nos mais antigos, um pulso
    de `ms` com a forca `amplitude` (1..255)."""
    if not ligado():
        return
    v = _vibrador()
    if v is None:
        return
    vib, VE, sdk = v
    try:
        if sdk >= 29 and pronto is not None:
            vib.vibrate(VE.createPredefined(pronto))
        elif sdk >= 26:
            vib.vibrate(VE.createOneShot(int(ms), int(amplitude)))
        else:
            vib.vibrate(int(ms))
    except Exception as e:
        print(f"[tatil] {e}")


def _padrao(tempos, forcas):
    """Sequencia de pulsos: tempos = [espera, liga, espera, liga, ...] (ms)."""
    if not ligado():
        return
    v = _vibrador()
    if v is None:
        return
    vib, VE, sdk = v
    try:
        if sdk >= 26:
            vib.vibrate(VE.createWaveform([int(t) for t in tempos], [int(f) for f in forcas], -1))
        else:
            vib.vibrate([int(t) for t in tempos], -1)
    except Exception as e:
        print(f"[tatil] {e}")


def tecla():
    _tocar(_CLICK, 12, 140)


def botao():
    _tocar(_TICK, 8, 90)


def confirmar():
    _tocar(_DOUBLE_CLICK, 18, 200) if _sdk() >= 29 else _padrao([0, 18, 70, 26], [0, 200, 0, 255])


def erro():
    _padrao([0, 22, 45, 22, 45, 22], [0, 230, 0, 230, 0, 230])


def forte():
    _tocar(_HEAVY_CLICK, 40, 255)


def vitoria():
    _padrao([0, 25, 55, 35, 55, 70], [0, 120, 0, 190, 0, 255])


def pulso(ms=80):
    _tocar(None, max(1, int(ms)), 255)


def _sdk():
    v = _vibrador()
    return v[2] if v else 0
