"""
hooks.py — TraveteFocus
Executado pelo python-for-android antes de empacotar o APK.
Remove arquivos desnecessários do Kivy para reduzir tamanho e tempo de build.
"""
import shutil
import os


def before_apk_build(toolchain):
    """Remove testes e arquivos desnecessários do Kivy antes de gerar o APK."""
    ctx = toolchain.ctx

    try:
        site_packages = ctx.get_site_packages_dir()
    except Exception:
        print("[HOOK] Não foi possível obter site-packages, pulando limpeza.")
        return

    dirs_para_remover = [
        os.path.join(site_packages, 'kivy', 'tests'),
        os.path.join(site_packages, 'kivy', 'tools'),
        os.path.join(site_packages, 'kivy', 'data', 'tests'),
        os.path.join(site_packages, 'kivy', 'data', 'glsl_fragments'),
        os.path.join(site_packages, 'PIL', 'tests'),
        os.path.join(site_packages, 'pip'),
        os.path.join(site_packages, 'setuptools'),
        os.path.join(site_packages, 'pkg_resources'),
    ]

    padroes_para_remover = ['test_*.py', '*_test.py', '*.pyc', '*.pyo']

    total_removido = 0
    for d in dirs_para_remover:
        if os.path.exists(d):
            try:
                tamanho = sum(
                    os.path.getsize(os.path.join(dp, f))
                    for dp, dn, fns in os.walk(d)
                    for f in fns
                )
                shutil.rmtree(d)
                total_removido += tamanho
                print(f"[HOOK] Removido: {d} ({tamanho // 1024}KB)")
            except Exception as e:
                print(f"[HOOK] Erro ao remover {d}: {e}")

    # Remove arquivos de teste soltos
    if os.path.exists(site_packages):
        for root, dirs, files in os.walk(site_packages):
            for f in files:
                if f.startswith('test_') and f.endswith('.py'):
                    try:
                        caminho = os.path.join(root, f)
                        os.remove(caminho)
                        total_removido += 1024
                    except Exception:
                        pass

    print(f"[HOOK] Limpeza concluída — {total_removido // (1024*1024)}MB removidos")
