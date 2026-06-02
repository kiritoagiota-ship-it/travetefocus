[app]

# ── IDENTIDADE ──────────────────────────────────────────────────────────────
title          = TraveteFocus
package.name   = travetefocus
package.domain = com.travetefocus

# ── CÓDIGO FONTE ─────────────────────────────────────────────────────────────
# Raiz do projeto (onde fica o main.py)
source.dir = .

# Todos os tipos de arquivo que serão empacotados no APK.
# py   → seus módulos Python (main, helpers, efeitos, som, telas/*)
# kv   → interface.kv
# ttf  → orbitron.ttf e rajdhani.ttf
# json → arquivos de dados, se houver
# wav/mp3/ogg → áudios usados por som.py, se houver
source.include_exts = py,kv,ttf,json,wav,mp3,ogg,png,jpg

# Pastas que NÃO entram no APK
source.exclude_dirs = tests,bin,.buildozer,.git,__pycache__,.github

# ── VERSÃO ───────────────────────────────────────────────────────────────────
version = 1.0.0

# ── DEPENDÊNCIAS ─────────────────────────────────────────────────────────────
# kivy    → framework de interface (telas, widgets, animações, efeitos)
# sqlite3 → armazenamento local de dados (tela memorias.py)
# (kivy já inclui suporte a áudio/SDL2 — som.py está coberto)
requirements = python3,kivy,sqlite3

# ── INTERFACE ────────────────────────────────────────────────────────────────
orientation = portrait
fullscreen  = 0

# ── PERMISSÕES ANDROID ───────────────────────────────────────────────────────
# Necessário para gravar/ler o banco de dados sqlite localmente no dispositivo
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# ── APIs ANDROID ─────────────────────────────────────────────────────────────
android.api    = 33
android.minapi = 21

# ── NDK — usa o NDK 27 já instalado no runner do GitHub Actions ───────────────
android.ndk         = 27.3.13750724
android.ndk_api     = 27
android.ndk_path    = /usr/local/lib/android/sdk/ndk/27.3.13750724

# ── SDK — usa o SDK já instalado no runner do GitHub Actions ─────────────────
android.sdk_path    = /usr/local/lib/android/sdk

# Não tenta baixar/atualizar nada — usa o que já está no runner
android.skip_update = True

# Aceita licenças automaticamente (obrigatório em CI sem interação manual)
android.accept_sdk_license = True

# ── ARQUITETURAS ─────────────────────────────────────────────────────────────
# arm64-v8a  → celulares modernos (64-bit)
# armeabi-v7a → celulares mais antigos (32-bit)
android.archs = arm64-v8a, armeabi-v7a

# ── ARMAZENAMENTO ────────────────────────────────────────────────────────────
android.private_storage = True
android.allow_backup    = True

# ── HOOK PERSONALIZADO ───────────────────────────────────────────────────────
# Remove kivy/tests antes de empacotar — reduz APK e evita erros de build
p4a.hook = hooks.py


[buildozer]

# 1 = info (equilibrado para CI — não estoura o buffer do GitHub Actions)
log_level = 1

warn_on_root = 1
