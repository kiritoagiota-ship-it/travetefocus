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


_DIAS = ('segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo')


def _milhar(n):
    try:
        return f"{int(n):,}".replace(',', '.')
    except (TypeError, ValueError):
        return str(n)


def mensagem_turno(memoria):
    """Mensagem de um turno para o grupo do WhatsApp: cada lote na ordem em
    que foi lancado (so as pecas) e o total. No WhatsApp, *texto* = negrito."""
    raw = str(memoria.get('data', '')).strip()
    dia = raw.split()[0] if raw else ''
    try:
        d = datetime.strptime(dia, '%d/%m/%Y')
        data = f"{dia} ({_DIAS[d.weekday()]})"
    except ValueError:
        data = dia or '?'
    linhas = ['\U0001F4CB *PRODUÇÃO DO DIA*', f'\U0001F4C5 {data}', '']
    itens = memoria.get('itens') or []
    for it in itens:
        nome = str(it[0]).strip() if len(it) > 0 else '?'
        qtd = it[1] if len(it) > 1 else 0
        linhas.append(f'\U0001F9F5 {nome} — *{_milhar(qtd)}*')
    if not itens:
        linhas.append('(sem itens detalhados)')
    total = memoria.get('total', 0)
    try:
        n = int(total)
    except (TypeError, ValueError):
        n = 0
    palavra = 'peça' if n == 1 else 'peças'
    linhas += ['', f"✅ *TOTAL: {_milhar(total)} {palavra}*"]
    return '\n'.join(linhas)


def _copiar(texto):
    try:
        from kivy.core.clipboard import Clipboard
        Clipboard.copy(texto)
        return True
    except Exception as ex:
        print(f"[EXPORT] copiar falhou: {ex}")
        return False


def enviar_whatsapp(texto):
    """Abre o WhatsApp com a mensagem pronta (a pessoa escolhe o grupo e
    envia). Android: WhatsApp ou WhatsApp Business; sem eles, o menu de
    compartilhar. No PC: copia o texto.
    Devolve (ok, aviso): aviso = texto para mostrar na tela, ou None."""
    if _plat == 'android':
        if compartilhar_android(texto):
            return True, None
        if _copiar(texto):
            return False, "Nao consegui abrir o WhatsApp.\nA mensagem foi copiada: cole no grupo."
        return False, "Nao consegui abrir o WhatsApp."
    if _copiar(texto):
        return True, "Mensagem copiada!\nCole no grupo do WhatsApp."
    return False, "Nao consegui copiar a mensagem."


def _texto_java(texto):
    """String Java montada a partir de UTF-8: emojis passam inteiros pelo
    JNI em qualquer versao do pyjnius."""
    try:
        from jnius import autoclass
        JString = autoclass('java.lang.String')
        return JString(texto.encode('utf-8'), 'UTF-8')
    except Exception as ex:
        print(f"[EXPORT] texto java: {ex}")
        return texto


def compartilhar_android(texto, caminho_csv=None):
    """
    Compartilha via Intent Android.
    Tenta o WhatsApp (normal e Business); cai para o chooser geral.
    """
    try:
        from jnius import autoclass
        Intent  = autoclass('android.content.Intent')
        PA      = autoclass('org.kivy.android.PythonActivity')
        jtexto  = _texto_java(texto)

        def _intent(pkg=None):
            intent = Intent(Intent.ACTION_SEND)
            intent.setType('text/plain')
            intent.putExtra(Intent.EXTRA_TEXT, jtexto)
            if pkg:
                intent.setPackage(pkg)
            return intent

        for pkg in ('com.whatsapp', 'com.whatsapp.w4b'):
            try:
                PA.mActivity.startActivity(_intent(pkg))
                return True
            except Exception:
                pass                       # nao instalado: tenta o proximo
        chooser = Intent.createChooser(_intent(), 'Compartilhar')
        PA.mActivity.startActivity(chooser)
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

    try:
        relatorio = gerar_relatorio_whatsapp(memorias)
    except Exception as ex:
        print(f"[EXPORT] relatorio falhou: {ex}")
        if callback_erro:
            callback_erro("Nao foi possivel gerar o relatorio (dados inconsistentes).")
        return
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
