#!/bin/bash
# bateria CURTA (pedido do usuario): so os cenarios que mais pegam problema
cd /c/Users/kirit/travetefocus/app
S=/c/Users/kirit/travetefocus/ferramentas/saida_testes
export KIVY_LOG_MODE=PYTHON
r() {
  n=$1; L=$2; A=$3; D=$4; shift 4
  rm -rf $S/b_$n
  env "$@" timeout 420 bash dev/tour.sh $L $A $S/b_$n $D > $S/o_$n.txt 2>&1
  echo "=== $n: $(grep -a -h 'RESULTADO\|rolou\|\] fim' $S/o_$n.txt $S/b_$n/saida.txt 2>/dev/null | grep -v pin | tail -4 | cut -c1-120 | tr '\n' ' ')"
}
r tour 720 1560 1.75 FOTOS=1
r registro 720 1560 1.75 REGISTRO=1 TOUR_PY=dev/tela_teste.py
r vaza 720 1560 1.75 VAZA=1 TOUR_PY=dev/tela_teste.py
r duplo 720 1560 1.75 DUPLO=1 TOUR_PY=dev/tela_teste.py
r memrolar 720 1560 1.75 MEMORIAS=365 ABRIR=memorias ROLAR=1 TOUR_PY=dev/tela_teste.py
r app 720 1560 1.75 CENA=app CADA=0 TOUR_PY=dev/filme_cenas.py
r link 540 1158 1.3125 CENA=link CADA=0 TOUR_PY=dev/filme_cenas.py
r ajustes 540 1158 1.3125 CENA=ajustes CADA=0 TOUR_PY=dev/filme_cenas.py
r toques 540 1158 1.3125 CENA=toques CADA=0 TOUR_PY=dev/filme_cenas.py
r trans 540 1158 1.3125 CENA=trans CADA=0 TOUR_PY=dev/filme_cenas.py
r polir 540 1158 1.3125 CENA=polir CADA=0 TOUR_PY=dev/filme_cenas.py
r perf 720 1560 1.75 FOTOS=0
python dev/teste_metas.py 2>&1 | tail -1
python dev/teste_dados.py 2>&1 | tail -1
python dev/teste_lembretes.py 2>&1 | tail -1
for f in $S/b_*/filme.json $S/b_*/log.json; do python -c "
import json,sys;e=json.load(open(sys.argv[1],encoding='utf-8')).get('erros') or []
print('ERROS', sys.argv[1], e[:3]) if e else None" "$f"; done
python - <<'PY'
import json, statistics as st
d=json.load(open(r'C:\Users\kirit\travetefocus\ferramentas\saida_testes\b_perf\log.json'))
v=sorted(x[1] for x in d['dt']); print('fluidez: media %.1f ms, p99 %.1f ms'%(st.mean(v), v[int(len(v)*0.99)]))
PY
