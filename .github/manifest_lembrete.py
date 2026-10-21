"""Poe o recebedor dos lembretes (org.travetefocus.Lembrete, em java/) no
molde do AndroidManifest do python-for-android, dentro de <application>.
O buildozer nao tem opcao para declarar um <receiver>; sem isso o Android
nao entrega os avisos agendados pelo app (lembretes.py).
uso: python manifest_lembrete.py PASTA   (procura os moldes dentro dela)"""
import os
import sys

LINHA = '        <receiver android:name="org.travetefocus.Lembrete" android:exported="false" />'
raiz = sys.argv[1] if len(sys.argv) > 1 else '.'
achados = 0
for base, _dirs, arquivos in os.walk(raiz):
    for nome in arquivos:
        if nome != 'AndroidManifest.tmpl.xml':
            continue
        p = os.path.join(base, nome)
        s = open(p, encoding='utf-8').read()
        if '</application>' not in s:
            continue
        achados += 1
        if 'org.travetefocus.Lembrete' in s:
            continue
        i = s.rindex('</application>')
        s = s[:i] + LINHA.strip() + '\n    ' + s[i:]
        open(p, 'w', encoding='utf-8').write(s)
        print('recebedor dos lembretes em', p)
print(achados, 'moldes conferidos')
