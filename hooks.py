"""
hooks.py — Hook customizado para o python-for-android (p4a)
Referenciado em buildozer.spec como:  p4a.hook = hooks.py

A função before_apk_build() é chamada automaticamente pelo p4a
logo antes de empacotar o APK.  Aqui ela varre a pasta de build
e remove todos os diretórios kivy/tests encontrados, evitando:
  - Inchaço desnecessário no APK
  - Falhas de empacotamento causadas pelos fixtures de teste do Kivy
"""

import os
import shutil


def before_apk_build(*args, **kwargs):
    """Remove os diretórios de testes do Kivy antes de gerar o APK."""

    print("[hooks.py] ── Iniciando limpeza de testes do Kivy ──")

    # Raiz onde o buildozer armazena os builds intermediários
    build_base = os.path.join(".buildozer", "android", "platform")

    if not os.path.isdir(build_base):
        print(f"[hooks.py] Diretório '{build_base}' não encontrado — nada a fazer.")
        return

    removed_count = 0

    for dirpath, dirnames, _ in os.walk(build_base, topdown=True):
        # Itera sobre uma cópia para poder modificar a lista durante o loop
        for dirname in list(dirnames):
            if dirname == "tests" and "kivy" in dirpath.lower():
                full_path = os.path.join(dirpath, dirname)
                try:
                    shutil.rmtree(full_path)
                    dirnames.remove(dirname)   # impede os.walk de descer na pasta removida
                    print(f"[hooks.py] Removido: {full_path}")
                    removed_count += 1
                except OSError as exc:
                    print(f"[hooks.py] AVISO — não foi possível remover '{full_path}': {exc}")

    if removed_count == 0:
        print("[hooks.py] Nenhum diretório kivy/tests encontrado.")
    else:
        print(f"[hooks.py] ✓ {removed_count} diretório(s) de testes removido(s).")

    print("[hooks.py] ── Limpeza concluída ──")
