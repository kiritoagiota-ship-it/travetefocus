#!/bin/bash
# grava so a abertura (720x1560) e assa: para testar a danca com a velocidade real
AQUI="$(cd "$(dirname "$0")" && pwd)"
SCR="/c/Users/kirit/travetefocus/ferramentas/saida_testes"
export YORU_GRAVA="$(cygpath -w "$SCR/gravados.json")" PYTHONIOENCODING=utf-8 KIVY_LOG_MODE=PYTHON
FOTOS=0 SO_TITULO=1 bash "$AQUI/tour.sh" 720 1560 "$SCR/gr_tit2" 1.75
unset YORU_GRAVA
python -u "$AQUI/assar.py" assar
