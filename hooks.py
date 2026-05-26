"""
hooks.py — TraveteFocus
Remove arquivos de teste do Kivy antes de empacotar o APK.
Usa busca recursiva em múltiplos caminhos para garantir que funcione.
"""
import shutil
import os
import glob


def before_apk_build(toolchain):
    """Chamado pelo p4a antes de gerar o APK."""

    # Caminhos possíveis onde os testes podem estar
    bases = [
        os.path.expanduser('~/.buildozer/android/platform'),
        os.path.expanduser('~/.buildozer'),
    ]

    # Tenta também o site-packages diretamente
    try:
        site = toolchain.ctx.get_site_packages_dir()
        if site and os.path.exists(site):
            bases.insert(0, site)
    except Exception:
        pass

    removidos = 0

    for base in bases:
        if not os.path.exists(base):
            continue

        # Remove pastas de testes do Kivy e PIL
        for padrao in ['**/kivy/tests', '**/kivy/tools', '**/PIL/tests']:
            for caminho in glob.glob(os.path.join(base, padrao), recursive=True):
                if os.path.isdir(caminho):
                    try:
                        shutil.rmtree(caminho, ignore_errors=True)
                        removidos += 1
                        print(f'[HOOK] Removido: {caminho}')
                    except Exception as e:
                        print(f'[HOOK] Erro: {caminho} — {e}')

        # Remove arquivos test_*.py soltos
        for padrao in ['**/test_*.py', '**/*_test.py']:
            for arquivo in glob.glob(os.path.join(base, padrao), recursive=True):
                if os.path.isfile(arquivo):
                    try:
                        os.remove(arquivo)
                        removidos += 1
                    except Exception:
                        pass

    print(f'[HOOK] Concluído — {removidos} itens removidos')
