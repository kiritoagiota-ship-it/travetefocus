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

    ler(texto) -> {'itens': [{'dia', 'nome', 'qtd', 'quem', 'ts'}], 'quem': [nomes],
                   'ignoradas': n}
    ts = a hora da mensagem (segundos, como time.time()) ou None.
    marcar_repetidos(itens, registros, memorias) -> [True/False] (ja lancado?)
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
_NUM = re.compile(r'(?<![\d.,])(?<!\d:)(\d{1,3}(?:\.\d{3})+|\d+)(?![\d,])(?!:\d)')   # '14:30' e hora
_UNIDADE = r'(?:un(?:id(?:ades?)?)?|und?s?|p[cç]s?|pe[cç]as?|x)\.?'
# so PALAVRA inteira: 'Saia express 120' e 'Body totalmente liso' sao pecas
_IGNORAR = re.compile(r'\b(?:total|producao do dia|relatorio|exportado em|melhor dia|turnos|xp)\b')
# o separador fica na lista (grupo): depois de '+' um numero sozinho soma no item
_SEPARA_ITENS = re.compile(r'(\s*[;,+]\s*|\s+/\s+|\s+e\s+(?=\d)|(?<=\d)\s+e\s+)')
_SO_NUM = re.compile(r'\s*(\d{1,3}(?:\.\d{3})+|\d+)\s*(?:' + _UNIDADE + r')?\s*', re.IGNORECASE)
_HORA_NO_TEXTO = re.compile(r'\s*(?:\b[aà]s\s+)?(?<!\d)\d{1,2}:\d{2}(?::\d{2})?(?:\s*h\b)?', re.IGNORECASE)
_LETRA = re.compile(r'[a-zA-ZÀ-ÿ]')
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


def _hora_de(cabecalho):
    """'17:32' (ou '5:32 PM') do comeco da mensagem -> (h, m) ou None."""
    m = re.search(r'(\d{1,2}):(\d{2})(?::\d{2})?\s*([apAP])?\.?\s*[mM]?', cabecalho or '')
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if m.group(3):
        h = h % 12 + (12 if m.group(3).lower() == 'p' else 0)
    return (h, mi) if h < 24 and mi < 60 else None


def _ts(dia, hora):
    if not dia or not hora:
        return None
    try:
        d = datetime.strptime(dia, '%d/%m/%Y')
        return d.replace(hour=hora[0], minute=hora[1]).timestamp()
    except (ValueError, OverflowError, OSError):
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


_ANTES_DE_CODIGO = re.compile(r'(?:\btam(?:anho)?|\bref|\bn[º°o]?|\bnum|\bpedido|\blote|\bc[oó]d(?:igo)?)\.?\s*$',
                              re.IGNORECASE)


def _parece_tamanho(p, n, q):
    """O numero `n` (valor q) e tamanho/referencia e nao a quantidade de outra
    peca? Depois de 'tam', 'ref', 'nº', 'pedido', 'lote', 'cod' - ou um numero
    PAR de 30 a 60 (numeracao de roupa: 'Calça 40 preta 200')."""
    if _ANTES_DE_CODIGO.search(p[:n.start()]):
        return True
    return 30 <= q <= 60 and q % 2 == 0


def _dividir_por_numero(p):
    """'Camisa polo 180 calça 95' -> ['Camisa polo 180', 'calça 95'] e
    '180 camisa 95 calça' -> ['180 camisa', '95 calça']: numero seguido de
    palavra comeca peca nova. Nao divide 'nome - qtd' / 'nome: qtd' (o nome
    pode ter numero: 'camisa 2 bolsos - 150') nem em numero < 10 sem unidade
    ('2 bolsos')."""
    if re.search(r'\s-\s|(?<!\d):', p):
        return [p]
    nums = list(_NUM.finditer(p))
    if len(nums) < 2:
        return [p]
    nome_primeiro = bool(_LETRA.search(p[:nums[0].start()]))
    cortes, ini = [], 0
    for k, n in enumerate(nums):
        q = int(n.group(1).replace('.', ''))
        un = re.match(r'\s*' + _UNIDADE + r'(?![a-zA-ZÀ-ÿ])', p[n.end():], re.IGNORECASE)
        if q < 10 and not un:
            continue
        if not un and _parece_tamanho(p, n, q):
            continue                          # 'Calça 40 preta 200': o 40 e tamanho, nao outra peca
        if nome_primeiro:
            # corta DEPOIS deste numero: tem nome antes e outra peca com numero depois
            if k == len(nums) - 1:
                continue
            fim = n.end() + (un.end() if un else 0)
            if (_LETRA.search(p[ini:n.start()]) and re.match(r'\s+[a-zA-ZÀ-ÿ]', p[fim:])
                    and _NUM.search(p, fim)):
                cortes.append(fim)
                ini = fim
        elif k > 0:
            # corta ANTES deste numero: a peca de antes ja tem nome e este tem nome depois
            if _LETRA.search(p[ini:n.start()]) and re.match(r'\s*(?:' + _UNIDADE + r'\s+)?[a-zA-ZÀ-ÿ]',
                                                             p[n.end():], re.IGNORECASE):
                cortes.append(n.start())
                ini = n.start()
    if not cortes:
        return [p]
    pontos = [0] + cortes + [len(p)]
    return [p[a:b].strip() for a, b in zip(pontos, pontos[1:]) if p[a:b].strip()]


def _itens_da_linha(linha):
    """[(nome, qtd)] de uma linha ja limpa (pode ter mais de uma peca)."""
    out = []
    linha = _HORA_NO_TEXTO.sub(' ', linha).strip()   # 'as 14:30' nao e quantidade
    partes = _SEPARA_ITENS.split(linha)               # [pedaco, separador, pedaco, ...]
    somar = 0                                         # '50+30 calca': o 50 espera o item
    for k in range(0, len(partes), 2):
        ped = partes[k]
        antes = partes[k - 1] if k else ''
        depois = partes[k + 1] if k + 1 < len(partes) else ''
        so = _SO_NUM.fullmatch(ped)
        if so:
            q = int(so.group(1).replace('.', ''))
            if '+' in antes and out:                  # 'Calça 50+30' = 80
                nome, qtd = out[-1]
                if 0 < qtd + q <= 99999:
                    out[-1] = (nome, qtd + q)
                continue
            if '+' in depois:
                somar += q
                continue
        for sub in _dividir_por_numero(ped):
            it = _item(sub)
            if it:
                if somar and 0 < it[1] + somar <= 99999:
                    it = (it[0], it[1] + somar)
                somar = 0
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
    hora_msg = dia_msg = None
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
            d, mm, a, autor, linha_msg = cab
            hora_msg = _hora_de(linha[:len(linha) - len(linha_msg)])
            linha = linha_msg
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
        if _IGNORAR.search(chave):
            pendente = None
            continue
        achados = _itens_da_linha(limpa)
        if not achados:
            so_num = re.fullmatch(r'\s*(\d{1,3}(?:\.\d{3})+|\d+)\s*(?:' + _UNIDADE + r')?\s*', limpa, re.IGNORECASE)
            if so_num and pendente:               # "Camisa polo" numa linha, "180" na outra
                qtd = int(so_num.group(1).replace('.', ''))
                if 0 < qtd <= 99999:
                    itens.append({'dia': dia_atual, 'nome': pendente, 'qtd': qtd, 'quem': autor,
                                  'ts': _ts(dia_atual, hora_msg) if dia_atual == dia_msg else None})
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
            itens.append({'dia': dia_atual, 'nome': nome, 'qtd': qtd, 'quem': autor,
                          'ts': _ts(dia_atual, hora_msg) if dia_atual == dia_msg else None})
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


def _chave_nome(nome):
    return re.sub(r'\s+', ' ', _sem_acento(str(nome or ''))).strip()


def _qtd_int(v):
    try:
        return int(float(str(v).replace(',', '.')))
    except (TypeError, ValueError):
        return None


def marcar_repetidos(itens, registros, memorias, hoje=None):
    """[True/False] para cada item: True = o mesmo (dia, nome sem acento e
    minusculo, qtd) ja esta nos lotes do Registro ou nos itens de um turno
    daquele dia (colar a mesma mensagem duas vezes). Conta as vezes: um lote
    igual ja lancado marca so UM item igual colado. Lote do Registro sem dia
    ('') conta como de `hoje`."""
    dia_hoje = (hoje or datetime.now().date()).strftime('%d/%m/%Y')
    ja = {}

    def _somar(dia, nome, qtd):
        q = _qtd_int(qtd)
        if not dia or q is None:
            return
        k = (dia, _chave_nome(nome), q)
        ja[k] = ja.get(k, 0) + 1

    for r in registros or []:
        try:
            dia = str(r[3]) if len(r) > 3 and r[3] else dia_hoje
            if not (len(r) > 3 and r[3]) and len(r) > 4 and r[4]:
                try:                           # lote digitado sem dia: o dia da hora dele (como metas.dia_do_lote)
                    dia = datetime.fromtimestamp(float(r[4])).strftime('%d/%m/%Y')
                except (TypeError, ValueError, OSError, OverflowError):
                    pass
            _somar(dia, r[0], r[1])
        except (TypeError, IndexError):
            continue
    for m in memorias or []:
        try:
            dia = str(m.get('data', '')).strip().split(' ')[0]
            for it in m.get('itens') or []:
                if isinstance(it, (list, tuple)) and len(it) > 1:
                    _somar(dia, it[0], it[1])
        except (AttributeError, TypeError):
            continue
    out = []
    for it in itens:
        k = (it.get('dia'), _chave_nome(it.get('nome')), _qtd_int(it.get('qtd')))
        if ja.get(k, 0) > 0:
            ja[k] -= 1
            out.append(True)
        else:
            out.append(False)
    return out
