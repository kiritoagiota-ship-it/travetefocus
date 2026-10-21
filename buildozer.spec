[app]

# ── IDENTIDADE ──────────────────────────────────────────────────────────────
title          = TraveteFocus
package.name   = travetefocus
package.domain = com.travetefocus

# ── CÓDIGO FONTE ─────────────────────────────────────────────────────────────
source.dir = .
source.include_exts = py,kv,ttf,json,wav,mp3,ogg,png,jpg,csv,bin,txt
source.exclude_dirs = tests,bin,.buildozer,.git,__pycache__,.github,dev,java,res_notif,res_layout,docs

# ── VERSÃO ───────────────────────────────────────────────────────────────────
version = 1.0.4

# ── DEPENDÊNCIAS ─────────────────────────────────────────────────────────────
requirements = python3,kivy,sqlite3,plyer

# ── INTERFACE ────────────────────────────────────────────────────────────────
orientation = portrait
fullscreen   = 0

# Ícone do app (dev/icone.py "usar NOME" grava os tres): icon.png e o icone
# inteiro (celulares antigos); nos novos o Android monta o icone adaptativo com
# o fundo e o desenho separados e corta no formato do aparelho (circulo etc.)
icon.filename = %(source.dir)s/icon.png
icon.adaptive_foreground.filename = %(source.dir)s/icone_frente.png
icon.adaptive_background.filename = %(source.dir)s/icone_fundo.png

# Tela de abertura (no lugar do "Loading..." padrao do Kivy)
presplash.filename    = %(source.dir)s/presplash.png
android.presplash_color = #020204

# ── PERMISSÕES ───────────────────────────────────────────────────────────────
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, VIBRATE, POST_NOTIFICATIONS, QUERY_ALL_PACKAGES, USE_EXACT_ALARM, SCHEDULE_EXACT_ALARM

# Lembretes na barra do celular, com o app fechado: lembretes.py agenda e o
# recebedor java/org/travetefocus/Lembrete.java mostra o aviso (o <receiver>
# entra no AndroidManifest pelo .github/manifest_lembrete.py, no build)
android.add_src = java
android.add_resources = res_notif:drawable, res_layout:layout

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
p4a.branch = v2026.05.09

[buildozer]
log_level    = 1
warn_on_root = 1
