"""
importar_zap.py - Le o texto COPIADO DO WHATSAPP e acha as pecas.

Quando se copia mais de uma mensagem, o WhatsApp poe na frente de cada uma a
data, a hora e quem mandou:
    [06/10/2026, 17:32] Fulano: Camisa polo 180
    [17:32, 06/10/2026] Fulano: 95 calca jeans          (aparelhos antigos)
    06/10/2026 17:32 - Fulano: vestido - 60 un          (conversa exportada)
As linhas seguintes sem esse comeco continuam a mesma mensagem.

De cada linha saem so o NOME da peca e a QUANTIDADE; o dia vem da data da
mensagem (ou de uma linha de data dentro dela, como a "PRODUCAO DO DIA" que
o proprio app manda). Conversa, totais e titulos sao ignorados.

    ler(texto) -> {'itens': [{'dia', 'nome', 'qtd', 'quem'}], 'quem': [nomes],
                   'ignoradas': n}
"""
import re
import unicodedata
from datetime import datetime, date

_DATA = r'(\d{1,2})[/.\-](\d{1,2})(?:[/.\-](\d{2,4}))?'
_HORA = r'\d{1,2}:\d{2}(?::\d{2})?(?:\s*[apAP]\.?\s*[mM]\.?)?'
_CABECALHOS = (
    re.compile(r'^\W*\[?\s*' + _DATA + r'[,\s]+' + _HORA + r'\s*\]?\s*(?:-\s*)?([^:\n]{1,60}?):\s?(.*)$'),
    re.compile(r'^\W*\[?\s*' + _HORA + r'[,\s]+' + _DATA + r'\s*\]?\s*(?:-\s*)?([^:\n]{1,60}?):\s?(.*)$'),
)
_SO_DATA = re.compile(r'^\D{0,12}' + _DATA + r'(?:\s*\(?[a-zA-ZçÇáéíóúãõâêô\-]{3,13}\)?)?\s*$')
_NUM = re.compile(r'(?<![\d.,])(\d{1,3}(?:\.\d{3})+|\d+)(?![\d,])')
_UNIDADE = r'(?:un(?:id(?:ades?)?)?|und?s?|p[cç]s?|pe[cç]as?|x)\.?'
_IGNORAR = ('total', 'producao do dia', 'relatorio', 'exportado em', 'melhor dia', 'turnos', 'xp')
_SEPARA_ITENS = re.compile(r'\s*[;,+]\s*|\s+e\s+(?=\d)|(?<=\d)\s+e\s+')
_DIAS_SEMANA = ('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo')


def _sem_acento(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c)).lower()


def _limpar(linha):
    """Tira enfeites do WhatsApp (*negrito*, _italico_, emojis, marcadores)."""
    s = re.sub(r'[*_~`]', '', linha)
    s = ''.join(c if (c.isalnum() or c in ' .,;:/+-()%\'"º°') else ' '
                for c in s.replace('—', ' - ').replace('–', ' - ').replace('=', ' - '))
    return re.sub(r'\s+', ' ', s).strip()


def _dia(d, m, a, base):
    """'dd/mm/aaaa' ou None se a data nao existe. Sem ano: o de `base`."""
    try:
        d, m = int(d), int(m)
        if a is None:
            a = base.year
        else:
            a = int(a)
            if a < 100:
                a += 2000
        return date(a, m, d).strftime('%d/%m/%Y')
    except (TypeError, ValueError):
        return None


def _nome(txt):
    t = re.sub(r'^[\s\-:.,/()x]+|[\s\-:.,/(]+$', '', txt, flags=re.IGNORECASE).strip()
    t = re.sub(r'\s+', ' ', t)
    if len(re.sub(r'[^a-zA-ZÀ-ÿ]', '', t)) < 2:
        return None
    return t[0].upper() + t[1:]


def _item(pedaco):
    """(nome, qtd) de um pedaco de linha, ou None. A quantidade e o numero
    do comeco ("180 camisa polo") ou o ultimo ("camisa 2 bolsos - 180 un")."""
    p = pedaco.strip()
    if not p:
        return None
    nums = list(_NUM.finditer(p))
    if not nums:
        return None
    ini = nums[0] if nums[0].start() == 0 or not re.search(r'[a-zA-ZÀ-ÿ]', p[:nums[0].start()]) else None
    esc = ini or nums[-1]
    qtd = int(esc.group(1).replace('.', ''))
    if qtd <= 0 or qtd > 99999:
        return None
    depois = re.sub(r'^\s*' + _UNIDADE + r'(?![a-zA-ZÀ-ÿ])', ' ', p[esc.end():], flags=re.IGNORECASE)
    letras = re.compile(r'[a-zA-ZÀ-ÿ]')
    if letras.search(p[:esc.start()]) and letras.search(depois):
        return None                               # numero no meio da frase ("chego 7 horas"): e conversa
    resto = p[:esc.start()] + ' ' + depois
    resto = re.sub(r'(?<![a-zA-ZÀ-ÿ])' + _UNIDADE + r'\s*$', ' ', resto, flags=re.IGNORECASE)
    nome = _nome(resto)
    return (nome, qtd) if nome else None


def _itens_da_linha(linha):
    """[(nome, qtd)] de uma linha ja limpa (pode ter mais de uma peca)."""
    out = []
    for ped in _SEPARA_ITENS.split(linha):
        it = _item(ped)
        if it:
            out.append(it)
    if not out:                                   # a virgula podia ser parte do nome
        it = _item(linha)
        if it:
            out.append(it)
    return out


def ler(texto, hoje=None):
    """Acha as pecas no texto copiado. `hoje` = dia das linhas sem data."""
    base = hoje or datetime.now().date()
    dia_padrao = base.strftime('%d/%m/%Y')
    itens, quem, ignoradas = [], [], 0
    dia_msg, autor = dia_padrao, ''
    dia_atual = dia_padrao
    pendente = None                               # nome sozinho numa linha, esperando o numero
    for bruta in str(texto or '').replace('\r', '\n').split('\n'):
        linha = bruta.replace('‎', '').replace('‏', '').replace('‪', '').replace('‬', '').strip()
        if not linha:
            pendente = None
            continue
        cab = None
        for i, rx in enumerate(_CABECALHOS):
            m = rx.match(linha)
            if m:
                cab = m.groups()
                break
        if cab:
            d, mm, a, autor, linha = cab
            autor = autor.strip()
            dia_msg = _dia(d, mm, a, base) or dia_padrao
            dia_atual = dia_msg
            pendente = None
            if autor and autor not in quem:
                quem.append(autor)
        limpa = _limpar(linha)
        if not limpa:
            continue
        m = _SO_DATA.match(limpa)
        if m:                                     # "24/09/2026 (quinta)": o dia das proximas linhas
            dia_atual = _dia(m.group(1), m.group(2), m.group(3), base) or dia_atual
            pendente = None
            continue
        chave = _sem_acento(limpa)
        if any(p in chave for p in _IGNORAR):
            pendente = None
            continue
        achados = _itens_da_linha(limpa)
        if not achados:
            so_num = re.fullmatch(r'\s*(\d{1,3}(?:\.\d{3})+|\d+)\s*(?:' + _UNIDADE + r')?\s*', limpa, re.IGNORECASE)
            if so_num and pendente:               # "Camisa polo" numa linha, "180" na outra
                qtd = int(so_num.group(1).replace('.', ''))
                if 0 < qtd <= 99999:
                    itens.append({'dia': dia_atual, 'nome': pendente, 'qtd': qtd, 'quem': autor})
                pendente = None
                continue
            nome = _nome(limpa)
            palavras = len(limpa.split())
            if nome and not so_num and palavras <= 4 and _sem_acento(nome) not in _DIAS_SEMANA:
                pendente = nome                   # pode ser o nome; o numero vem na proxima linha
            else:
                pendente = None
            ignoradas += 1
            continue
        pendente = None
        for nome, qtd in achados:
            itens.append({'dia': dia_atual, 'nome': nome, 'qtd': qtd, 'quem': autor})
    return {'itens': itens, 'quem': quem, 'ignoradas': ignoradas}


def por_dia(itens):
    """[(dia, [itens])] em ordem de data."""
    grupos = {}
    for it in itens:
        grupos.setdefault(it['dia'], []).append(it)

    def chave(d):
        try:
            return datetime.strptime(d, '%d/%m/%Y')
        except ValueError:
            return datetime.max
    return [(d, grupos[d]) for d in sorted(grupos, key=chave)]
