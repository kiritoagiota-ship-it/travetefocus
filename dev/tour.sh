#!/bin/bash
# uso: tour.sh LARG ALT SAIDA [densidade]   (FOTOS=0 para medir desempenho sem capturas)
AQUI="$(cd "$(dirname "$0")" && pwd)"
ISO="/c/Users/kirit/travetefocus/ferramentas/saida_testes/iso_tour_$1x$2"
rm -rf "$ISO"; mkdir -p "$ISO/appdata" "$ISO/home" "$ISO/kivy"
rm -rf "$3"; mkdir -p "$3"
APPDATA="$(cygpath -w "$ISO/appdata")" HOME="$(cygpath -w "$ISO/home")" KIVY_HOME="$(cygpath -w "$ISO/kivy")" \
PYTHONUSERBASE='C:\Users\kirit\AppData\Roaming\Python' \
timeout 230 python -u "${TOUR_PY:-$AQUI/tour.py}" "$1" "$2" "$(cygpath -w "$3")" $4 > "$3/saida.txt" 2>&1
echo "rc=$?"
grep "\[tour\]" "$3/saida.txt" | tail -40
