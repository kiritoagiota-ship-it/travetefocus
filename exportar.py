"""
exportar.py — Exportação de histórico CSV e compartilhamento.
Funciona no Android (Intent share) e desktop (salva arquivo).
"""
import os
import csv
import io
from datetime import datetime
from kivy.utils import platform as _plat


def gerar_csv_bytes(memorias):
    """Gera conteúdo do CSV como bytes UTF-8-BOM (compatível com Excel e WhatsApp)."""
    buf = io.StringIO()
    w   = csv.writer(buf)
    w.writerow(['Data', 'Total_Pecas', 'XP_Ganho', 'Itens_do_Turno'])
    for mem in reversed(memorias):
        itens = ' | '.join(
            f"{it[0]} x{it[1]}"
            for it in mem.get('itens', [])
        )
        w.writerow([
            mem.get('data', ''),
            mem.get('total', 0),
            mem.get('xp', 0),
            itens,
        ])
    return buf.getvalue().encode('utf-8-sig')


def gerar_relatorio_whatsapp(memorias):
    """Gera relatório formatado para colar no WhatsApp."""
    if not memorias:
        return "TraveteFocus — nenhum turno registrado ainda."

    total_pecas = sum(m.get('total', 0) for m in memorias)
    total_xp    = sum(m.get('xp',    0) for m in memorias)
    melhor      = max(memorias, key=lambda m: m.get('total', 0))

    linhas = [
        '*RELATORIO TRAVETEFOCUS*',
        f'Exportado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}',
        '',
        f'Total de turnos: {len(memorias)}',
        f'Total de pecas:  {total_pecas}',
        f'Total de XP:     {total_xp}',
        f'Melhor dia:      {melhor.get("total", 0)} pecas ({melhor.get("data", "?")})',
        '',
        '*ULTIMOS 10 TURNOS:*',
    ]
    for mem in reversed(memorias[-10:]):
        data  = mem.get('data', '?').split()[0]  # só data, sem hora
        total = mem.get('total', 0)
        xp    = mem.get('xp', 0)
        linhas.append(f"  {data}  |  {total} pcs  |  +{xp} XP")

    return '\n'.join(linhas)


def salvar_csv(memorias, data_dir):
    """
    Salva o CSV no diretório do app e, no Android, também tenta em Downloads.
    Retorna o caminho do arquivo salvo.
    """
    nome    = f"travetefocus_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    conteudo = gerar_csv_bytes(memorias)

    # Destino 1: user_data_dir (sempre funciona)
    path_app = os.path.join(data_dir, nome)
    try:
        with open(path_app, 'wb') as f:
            f.write(conteudo)
    except Exception as ex:
        print(f"[EXPORT] Erro ao salvar em user_data_dir: {ex}")
        path_app = None

    # Destino 2: Downloads (Android — nem sempre disponível)
    path_downloads = None
    if _plat == 'android':
        try:
            downloads = '/sdcard/Download'
            if os.path.isdir(downloads):
                path_downloads = os.path.join(downloads, nome)
                with open(path_downloads, 'wb') as f:
                    f.write(conteudo)
        except Exception as ex:
            print(f"[EXPORT] Downloads indisponível: {ex}")
            path_downloads = None

    return path_downloads or path_app


def compartilhar_android(texto, caminho_csv=None):
    """
    Compartilha via Intent Android.
    Tenta primeiro o WhatsApp; cai para chooser geral.
    """
    try:
        from jnius import autoclass
        Intent  = autoclass('android.content.Intent')
        PA      = autoclass('org.kivy.android.PythonActivity')

        def _enviar(pkg=None):
            intent = Intent(Intent.ACTION_SEND)
            intent.setType('text/plain')
            intent.putExtra(Intent.EXTRA_TEXT, texto)
            if pkg:
                intent.setPackage(pkg)
                try:
                    PA.mActivity.startActivity(intent)
                    return True
                except Exception:
                    return False
            chooser = Intent.createChooser(intent, 'Compartilhar historico')
            PA.mActivity.startActivity(chooser)
            return True

        # 1ª tentativa: WhatsApp direto
        if not _enviar('com.whatsapp'):
            # 2ª tentativa: chooser geral
            _enviar()
        return True
    except Exception as ex:
        print(f"[EXPORT] compartilhar_android falhou: {ex}")
        return False


def exportar_e_compartilhar(memorias, data_dir, callback_erro=None):
    """
    Ponto de entrada principal.
    Gera relatório + CSV, compartilha no Android ou exibe caminho no desktop.
    callback_erro(msg): chamado se algo falhar, para exibir popup ao usuário.
    """
    if not memorias:
        if callback_erro:
            callback_erro("Nenhum turno registrado para exportar.")
        return

    relatorio = gerar_relatorio_whatsapp(memorias)
    caminho   = None
    try:
        caminho = salvar_csv(memorias, data_dir)
    except Exception as ex:
        print(f"[EXPORT] {ex}")

    if _plat == 'android':
        ok = compartilhar_android(relatorio, caminho)
        if not ok and callback_erro:
            callback_erro(
                f"Não foi possível compartilhar automaticamente.\n\n"
                f"Arquivo salvo em:\n{caminho or 'user_data_dir'}"
            )
    else:
        # Desktop: abrir pasta ou mostrar caminho
        print(f"[EXPORT] CSV salvo em: {caminho}")
        if callback_erro:
            callback_erro(f"CSV salvo em:\n{caminho}")
