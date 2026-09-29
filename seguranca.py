"""
seguranca.py — TraveteFocus
A senha (PIN) do app.

- Guardada so como "impressao digital" (PBKDF2 com sal) no arquivo
  seguranca.json da pasta do app: nunca o numero em si.
- Enquanto ninguem troca, vale a senha padrao (PIN_PADRAO).
- Errar 3 vezes bloqueia por um tempo que cresce a cada rodada de erros
  (1 min, 5 min, 15 min, 1 h). Fechar o app nao zera o bloqueio; acertar zera.
"""
import hashlib
import hmac
import json
import os
import time

PIN_PADRAO = "2004"                  # so ate a senha ser trocada no app
TENTATIVAS = 3
ESPERAS = (60, 300, 900, 3600)       # segundos de bloqueio, rodada a rodada
_ARQUIVO = "seguranca.json"
_VOLTAS = 60000


def _caminho():
    try:
        from kivy.app import App
        return os.path.join(App.get_running_app().user_data_dir, _ARQUIVO)
    except Exception:
        return _ARQUIVO


def _ler():
    try:
        with open(_caminho(), encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _gravar(d):
    try:
        caminho = _caminho()
        tmp = caminho + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, caminho)
    except Exception as e:
        print(f"[seguranca] nao gravou: {e}")


def _impressao(pin, sal_hex):
    return hashlib.pbkdf2_hmac("sha256", str(pin).encode("utf-8"), bytes.fromhex(sal_hex), _VOLTAS).hex()


def pin_confere(pin):
    """True se `pin` e a senha do app."""
    d = _ler()
    if d.get("hash") and d.get("sal"):
        return hmac.compare_digest(_impressao(pin, d["sal"]), d["hash"])
    return hmac.compare_digest(str(pin), PIN_PADRAO)


def bloqueio_restante():
    """Segundos que faltam para poder tentar de novo (0 = liberado)."""
    return max(0, int(round(_ler().get("bloqueado_ate", 0) - time.time())))


def tentativas_restantes():
    return max(0, TENTATIVAS - int(_ler().get("erros", 0)))


def registrar_erro():
    """Anota um erro. Devolve (tentativas que sobram, segundos de bloqueio)."""
    d = _ler()
    d["erros"] = int(d.get("erros", 0)) + 1
    if d["erros"] < TENTATIVAS:
        _gravar(d)
        return TENTATIVAS - d["erros"], 0
    rodada = min(int(d.get("rodada", 0)), len(ESPERAS) - 1)
    espera = ESPERAS[rodada]
    d["bloqueado_ate"] = time.time() + espera
    d["rodada"] = rodada + 1
    d["erros"] = 0
    _gravar(d)
    return 0, espera


def registrar_acerto():
    d = _ler()
    d["erros"] = 0
    d["rodada"] = 0
    d["bloqueado_ate"] = 0
    _gravar(d)


def trocar_pin(atual, novo, confirma):
    """Troca a senha. Devolve (ok, mensagem)."""
    if bloqueio_restante() > 0:
        return False, "Senha bloqueada por erros. Espere o tempo acabar."
    if not pin_confere(atual):
        registrar_erro()
        return False, "A senha atual não confere."
    novo = str(novo).strip()
    if not (novo.isdigit() and 4 <= len(novo) <= 8):
        return False, "A senha nova precisa ter de 4 a 8 números."
    if novo != str(confirma).strip():
        return False, "A confirmação não é igual à senha nova."
    d = _ler()
    d["sal"] = os.urandom(16).hex()
    d["hash"] = _impressao(novo, d["sal"])
    d["erros"] = 0
    d["rodada"] = 0
    d["bloqueado_ate"] = 0
    _gravar(d)
    return True, "Senha trocada!"


def tempo_legivel(seg):
    m, s = divmod(max(0, int(seg)), 60)
    return f"{m:02d}:{s:02d}"
