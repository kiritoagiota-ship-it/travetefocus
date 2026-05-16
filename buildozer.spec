[app]

# (str) Title of your application
title = Travete Focus

# (str) Package name
package.name = travetefocus

# (str) Package domain (needed for android packaging)
package.domain = org.kirito

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (extensions separated by commas)
source.include_exts = py,png,jpg,kv,ttf,json,mp3,wav

# (list) List of inclusions using pattern matching
source.include_patterns = telas/*

# (str) Application version
version = 1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy

# (str) Supported orientations (valid options are: landscape, portrait, all)
orientation = portrait

# (bool) Use fullscreen mode or not
fullscreen = 1

# =============================================================================
# Android specific configurations
# =============================================================================

# (int) Android API to use
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (bool) Automatically accept SDK license agreements.
# OBRIGATÓRIO ESTAR EM TRUE PARA O GITHUB ACTIONS FUNCIONAR!
android.accept_sdk_license = True

# (list) Android architectures to build for
android.archs = armeabi-v7a, arm64-v8a

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a symbolic link
p4a.hook = 

# (str) The directory in which python-for-android should look for brands
#p4a.local_recipes = 

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
