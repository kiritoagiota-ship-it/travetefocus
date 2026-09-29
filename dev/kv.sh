#!/bin/bash
# uso: kv.sh LARG ALT SAIDA [densidade]
AQUI="$(cd "$(dirname "$0")" && pwd)"
ISO="/c/Users/kirit/travetefocus/ferramentas/saida_testes/iso_$1x$2"
rm -rf "$ISO"; mkdir -p "$ISO/appdata" "$ISO/home" "$ISO/kivy"
rm -rf "$3"; mkdir -p "$3"
APPDATA="$(cygpath -w "$ISO/appdata")" HOME="$(cygpath -w "$ISO/home")" KIVY_HOME="$(cygpath -w "$ISO/kivy")" \
PYTHONUSERBASE='C:\Users\kirit\AppData\Roaming\Python' \
timeout 150 python -u "$AQUI/app.py" "$1" "$2" "$(cygpath -w "$3")" $4 > "$3/saida.txt" 2>&1
echo "rc=$?"
tail -3 "$3/saida.txt"
