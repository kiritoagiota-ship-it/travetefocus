[app]

# ── IDENTIDADE ──────────────────────────────────────────────────────────────
title          = TraveteFocus
package.name   = travetefocus
package.domain = com.travetefocus

# ── CÓDIGO FONTE ─────────────────────────────────────────────────────────────
source.dir = .
source.include_exts = py,kv,ttf,json,wav,mp3,ogg,png,jpg
source.exclude_dirs = tests,bin,.buildozer,.git,__pycache__,.github

# ── VERSÃO ───────────────────────────────────────────────────────────────────
version = 1.0.1

# ── DEPENDÊNCIAS ─────────────────────────────────────────────────────────────
requirements = python3,kivy,sqlite3,plyer

# ── INTERFACE ────────────────────────────────────────────────────────────────
orientation = portrait
fullscreen   = 0

# Ícone do app — coloque icon.png na raiz do repositório (512×512 px ideal)
icon.filename = %(source.dir)s/icon.png

# ── PERMISSÕES ───────────────────────────────────────────────────────────────
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, VIBRATE

# ── APIs ANDROID ─────────────────────────────────────────────────────────────
# android.api     = versão alvo (Play Store exige 34+)
# android.minapi  = mínimo para instalar o app (Android 5.0+ = ~99% dos devices)
# android.ndk_api = API alvo do código nativo — DEVE ser igual ao minapi
#                   para evitar o erro "minsdk mismatch" do p4a master
android.api     = 34
android.minapi  = 21
android.ndk_api = 21

# ── NDK / SDK ────────────────────────────────────────────────────────────────
# NDK 27 (compilador) é capaz de compilar para qualquer alvo de API 21..34
android.ndk      = 27.3.13750724
android.ndk_path = /usr/local/lib/android/sdk/ndk/27.3.13750724
android.sdk_path = /usr/local/lib/android/sdk

# Não baixa SDK/NDK — usa o que já está instalado no runner do GitHub Actions
android.skip_update        = True
android.accept_sdk_license = True

# ── ARQUITETURAS ─────────────────────────────────────────────────────────────
android.archs = arm64-v8a, armeabi-v7a

# ── ARMAZENAMENTO ────────────────────────────────────────────────────────────
android.private_storage = True
android.allow_backup    = True

# ── PYTHON-FOR-ANDROID ───────────────────────────────────────────────────────
p4a.hook = hooks.py

[buildozer]
log_level    = 1
warn_on_root = 1
