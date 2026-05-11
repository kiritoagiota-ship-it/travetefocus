[app]
title = Travete Focus
package.name = travetefocus
package.domain = org.travete

source.dir = .
source.include_exts = py,kv,ttf,json,png,jpg

# Inclui explicitamente as fontes e o arquivo de dados
source.include_patterns = orbitron.ttf,rajdhani.ttf,dados.json,som.py

version = 1.0

requirements = python3,kivy==2.3.0,kivymd

orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a

# Ícone (substitua pelo seu ícone se tiver)
# icon.filename = icon.png

[buildozer]
log_level = 2
warn_on_root = 1
