[app]
title = Travete Focus
package.name = travetefocus
package.domain = org.travete

source.dir = .
source.include_exts = py,kv,ttf,json
source.include_patterns = orbitron.ttf,rajdhani.ttf,telas/__init__.py,telas/loading.py,telas/registro.py,telas/memorias.py,telas/progresso.py,telas/ganhos.py,telas/calculadora.py

source.exclude_dirs = tests,__pycache__,.git,.buildozer,bin
source.exclude_patterns = test_*.py,*_test.py,*.pyc,*.pyo

version = 1.0

requirements = python3,kivy==2.3.0,pillow,sdl2,sdl2_image,sdl2_mixer,sdl2_ttf

orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 26
android.ndk = 23b
android.ndk_api = 26
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True

p4a.hook = hooks.py

[buildozer]
log_level = 2
warn_on_root = 1
