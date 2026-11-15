"""
metas.py - As contas das METAS DE PRODUCAO (so contas, sem tela: dev/teste_metas.py testa).

Como a travetista recebe (por semana, de segunda a sabado, pago no sabado):
  o valor da FAIXA atingida na semana vale para TODAS as pecas da semana:
    abaixo de meta_meio (2.500) ......... valor_base  (R$ 0,25)
    de meta_meio ate meta_bonus - 1 ..... valor_meio  (R$ 0,27)
    meta_bonus (3.000) ou mais .......... valor_bonus (R$ 0,30)
  Configs antigas (sem valor_meio/meta_meio) ganham os padroes - completar_cfg().

Meta diaria: o que falta para cada faixa, dividido pelos dias uteis que
sobram (segunda a sexta, contando hoje) depois de reservar o sabado (meio
periodo, `pecas_sabado`, padrao 200). Domingo nao se trabalha (no domingo a
conta ja e da semana que comeca amanha). Feriado conta como dia normal.

Ritmo: cada lote novo guarda a hora em que foi lancado (5a posicao do
registro: [nome, qtd, xp, dia, ts]). Peca por hora = pecas lancadas depois
do primeiro lote do dia / tempo entre o primeiro e o ultimo lancamento,
tirando os intervalos que claramente foram pausa (almoco): um intervalo em
que o ritmo ficou abaixo de 60% do ritmo normal do dia nao conta.
"""
import math
from datetime import datetime, timedelta

PADRAO = {'valor_base': 0.25, 'valor_meio': 0.27, 'valor_bonus': 0.30,
          'meta_meio': 2500, 'meta_bonus': 3000, 'pecas_sabado': 200}
REF_REALISTA = 60          # 1 peca por minuto
REF_PADRAO = 90            # o padrao da fabrica: 1 peca a cada 40 s
MIN_LOTES = 2
MIN_MINUTOS = 15


def completar_cfg(cfg):
    """Poe os campos novos que faltam numa config salva (nao mexe nos que existem)."""
    for k, v in PADRAO.items():
        cfg.setdefault(k, v)
    return cfg


def _n(cfg, k):
    try:
        return float(cfg.get(k, PADRAO[k]))
    except (TypeError, ValueError):
        return float(PADRAO[k])


def faixas(cfg):
    """[(a partir de quantas pecas, R$ por peca, nome)] em ordem."""
    meio, topo = int(_n(cfg, 'meta_meio')), int(_n(cfg, 'meta_bonus'))
    fx = [(0, _n(cfg, 'valor_base'), 'base')]
    if 0 < meio < topo:                                # faixa do meio so se fizer sentido
        fx.append((meio, _n(cfg, 'valor_meio'), 'meio'))
    fx.append((topo, _n(cfg, 'valor_bonus'), 'topo'))
    return fx


def faixa_de(pecas, cfg):
    """(indice, inicio, valor, nome) da faixa em que `pecas` cai."""
    fx = faixas(cfg)
    i = 0
    for k, (ini, _v, _n_) in enumerate(fx):
        if pecas >= ini and (ini > 0 or k == 0):
            i = k
    if pecas <= 0:
        i = 0
    ini, v, nome = fx[i]
    return i, ini, v, nome


def ganho(pecas, cfg):
    pecas = max(0, int(pecas))
    return round(pecas * faixa_de(pecas, cfg)[2], 2)


def proxima_faixa(pecas, cfg):
    """None (ja esta na ultima) ou dict: falta, inicio, valor, ganho_la, a_mais
    (quanto a mais em R$ chegar la renderia, comparado com o ganho de hoje)."""
    fx = faixas(cfg)
    i = faixa_de(pecas, cfg)[0]
    if i + 1 >= len(fx):
        return None
    ini, v, nome = fx[i + 1]
    falta = max(0, ini - int(pecas))
    la = round(ini * v, 2)
    return {'falta': falta, 'inicio': ini, 'valor': v, 'nome': nome, 'ganho_la': la,
            'a_mais': round(la - ganho(pecas, cfg), 2)}


# ── a semana (segunda a sabado) ─────────────────────────────────────────
def segunda_da_semana(hoje):
    """A segunda-feira da semana de pagamento de `hoje` (domingo: a de amanha)."""
    if hoje.weekday() == 6:
        return hoje + timedelta(days=1)
    return hoje - timedelta(days=hoje.weekday())


def _dia_de(texto):
    try:
        return datetime.strptime(str(texto).strip().split()[0], "%d/%m/%Y").date()
    except Exception:
        return None


def chave_turno(turno):
    if turno.get('id'):
        return f"id:{turno['id']}"
    ts = turno.get('ts')
    return f"ts:{ts}" if ts is not None else f"{turno.get('data', '')}|{turno.get('total', 0)}"


def producao_por_dia(turnos):
    producao = {}
    for turno in turnos:
        dia = _dia_de(turno.get('data'))
        if dia is None:
            continue
        try:
            pecas = int(turno.get('total', 0))
        except (TypeError, ValueError, OverflowError):
            continue
        producao[dia] = producao.get(dia, 0) + pecas
    return producao


def periodos_do_turno(turno, periodos):
    """Fechamentos que protegem o turno. Em históricos antigos, usa a janela salva."""
    chave = chave_turno(turno)
    dia = _dia_de(turno.get('data'))
    for p in periodos:
        if not p.get('data_fim'):
            continue
        if 'contadas' in p:
            if chave in p['contadas']:
                yield p
        else:
            inicio, fim = _dia_de(p.get('data_inicio')), _dia_de(p['data_fim'])
            if inicio and fim and dia and inicio <= dia <= fim:
                yield p


def dia_do_lote(r, hoje):
    """O dia de um lote do Registro: o dia gravado (r[3], colado do WhatsApp);
    senao o dia da hora em que foi lancado (r[4]); senao (lote antigo, sem
    hora) hoje. Dia gravado estragado = None (fica de fora, como antes)."""
    if len(r) > 3 and r[3]:
        return _dia_de(r[3])
    if len(r) > 4 and r[4]:
        try:
            return datetime.fromtimestamp(float(r[4])).date()
        except (TypeError, ValueError, OverflowError, OSError):
            pass
    return hoje


DIAS_CURTOS = ('seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom')
DIAS_NOMES = ('segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo')


def rotulo_dia(d):
    """date -> 'sáb 14/11' (o cartao do lote que nao e de hoje)."""
    return f"{DIAS_CURTOS[d.weekday()]} {d.strftime('%d/%m')}"


def nome_do_dia(d, hoje):
    """Como falar de um dia que passou: 'ontem', 'sábado' (ate 6 dias) ou '14/11'."""
    n = (hoje - d).days
    if n == 1:
        return 'ontem'
    if 1 < n < 7:
        return DIAS_NOMES[d.weekday()]
    return d.strftime('%d/%m')


def dias_pendentes(registros, hoje):
    """Os dias ANTES de hoje que tem lote ainda nao finalizado (em ordem)."""
    dias = set()
    for r in registros or ():
        d = dia_do_lote(r, hoje)
        if d is not None and d < hoje:
            dias.add(d)
    return sorted(dias)


def aviso_pendentes(registros, hoje):
    """O texto da faixa do Registro quando sobrou lote de outro dia: None
    (nao tem) ou 'Tem lotes de sábado sem finalizar'."""
    dias = dias_pendentes(registros, hoje)
    if not dias:
        return None
    if len(dias) == 1:
        return f"Tem lotes de {nome_do_dia(dias[0], hoje)} sem finalizar"
    return f"Lotes de {len(dias)} dias sem finalizar"         # (curto: cabe na faixa com letra grande)


def separar_lotes(registros, hoje):
    """Como o FINALIZAR DIA divide os lotes em turnos.
    -> (fixos {'dd/mm/aaaa': [lotes]}, livres [lotes], data_livre date|None)
    fixos: os colados do WhatsApp (tem dia) e os digitados em dias ANTERIORES ao
    dia mais novo dos digitados (cada dia vira um turno). livres: os digitados do
    dia mais novo (e os antigos sem hora, que sao de hoje): vao para a data que o
    popup pergunta, que ja vem com o dia deles (data_livre)."""
    fixos, digitados = {}, {}
    for r in registros or ():
        if len(r) > 3 and r[3]:
            fixos.setdefault(str(r[3]), []).append(r)
        else:
            digitados.setdefault(dia_do_lote(r, hoje), []).append(r)
    if not digitados:
        return fixos, [], None
    data_livre = max(digitados)
    livres = digitados.pop(data_livre)
    for d in sorted(digitados):
        fixos.setdefault(d.strftime('%d/%m/%Y'), []).extend(digitados[d])
    return fixos, livres, data_livre


def pecas_da_semana(memorias, registros, hoje):
    """(pecas na semana, pecas de hoje): turnos finalizados + lotes ainda nao
    finalizados (cada lote no dia dele: metas.dia_do_lote)."""
    seg = segunda_da_semana(hoje)
    sab = seg + timedelta(days=5)
    semana = hoje_n = 0
    for m in memorias or ():
        d = _dia_de(m.get('data', ''))
        if d is None or not (seg <= d <= sab):
            continue
        try:
            t = int(m.get('total', 0))
        except (TypeError, ValueError):
            t = 0
        semana += t
        if d == hoje:
            hoje_n += t
    for r in registros or ():
        try:
            q = int(r[1])
        except (TypeError, ValueError, IndexError):
            continue
        d = dia_do_lote(r, hoje)
        if d is None or not (seg <= d <= sab):
            continue
        semana += q
        if d == hoje:
            hoje_n += q
    return semana, hoje_n


def fim_da_semana(d):
    """O sabado (dia do pagamento) da semana de `d` (domingo: o da semana seguinte)."""
    return segunda_da_semana(d) + timedelta(days=5)


def semanas(pecas_por_dia, cfg):
    """Divide as pecas em semanas de pagamento (seg a sab) e aplica a faixa em
    CADA semana. pecas_por_dia: {date: pecas} ou [(date, pecas)] (o mesmo dia
    pode repetir). -> [{'seg', 'sab', 'pecas', 'ganho'}] em ordem."""
    itens = pecas_por_dia.items() if hasattr(pecas_por_dia, 'items') else pecas_por_dia
    por_sem = {}
    for d, q in itens:
        if d is None:
            continue
        try:
            q = int(q)
        except (TypeError, ValueError):
            continue
        seg = segunda_da_semana(d)
        por_sem[seg] = por_sem.get(seg, 0) + q
    return [{'seg': seg, 'sab': seg + timedelta(days=5), 'pecas': q, 'ganho': ganho(q, cfg)}
            for seg, q in sorted(por_sem.items())]


def ganho_por_semanas(pecas_por_dia, cfg):
    """O pagamento de um periodo: a SOMA do ganho de cada semana (seg a sab),
    cada uma com a sua faixa (2 semanas de 2.400 = 2 x R$ 600, e nao 4.800 na
    faixa de cima)."""
    return round(sum(s['ganho'] for s in semanas(pecas_por_dia, cfg)), 2)


def fim_do_periodo(tipo, inicio, hoje):
    """Ate que dia um periodo aberto em `inicio` conta (o fechamento e a
    projecao usam o mesmo): o SEMANAL vai ate o sabado daquela semana (ou ate
    hoje, se fechar antes); os outros tipos vao ate hoje."""
    if str(tipo or '').lower() == 'semanal':
        # aberto num SABADO (fechou e abriu no dia do pagamento): a semana dele
        # e a seguinte (antes contava so aquele sabado e a semana zerava)
        ref = inicio + timedelta(days=2) if inicio.weekday() == 5 else inicio
        return min(fim_da_semana(ref), max(hoje, inicio))
    return max(hoje, inicio)


def inicio_do_proximo(fim, dias_com_turno=()):
    """O periodo seguinte comeca no dia depois do fim do fechado. Se esse dia e
    domingo (folga) e nao tem turno nele, comeca na segunda. Fechou num SABADO:
    o seguinte comeca no proprio sabado - um turno de sabado finalizado depois
    de fechar entra nele em vez de ficar fora de todos (os ja contados no
    fechado estao em 'contadas' e nao contam de novo)."""
    if fim.weekday() == 5:
        return fim
    d = fim + timedelta(days=1)
    if d.weekday() == 6 and d not in set(dias_com_turno):
        d += timedelta(days=1)
    return d


def config_coerente(base, meio, bonus, meta_meio, meta_bonus):
    """None se as faixas fecham (base <= meio <= bonus e meta do meio menor que a
    de cima), senao o texto do problema (para o aviso dos ajustes)."""
    if not (base <= meio <= bonus):
        if base > bonus:
            return "A BASE NÃO PODE PASSAR DO BÔNUS"
        return "O R$ DO MEIO TEM QUE FICAR ENTRE A BASE E O BÔNUS"
    if not (meta_meio < meta_bonus):
        return "A META DO MEIO TEM QUE SER MENOR QUE A META DE CIMA"
    return None


def meta_diaria(alvo, feitas_semana, feitas_hoje, hoje, pecas_sabado=200):
    """Quanto produzir por dia para chegar a `alvo` pecas na semana.
    -> dict: falta (na semana), por_dia (seg a sex, contando hoje), sabado
    (o que fica para o sabado), dias (dias uteis que sobram contando hoje),
    hoje_meta, hoje_falta, e_sabado, batida."""
    alvo = int(alvo)
    sab_cfg = max(0, int(pecas_sabado))
    wd = hoje.weekday()
    if wd == 6:                                       # domingo: a semana nova comeca amanha
        feitas_semana = feitas_hoje = 0
        wd = -1
    falta = max(0, alvo - int(feitas_semana))
    r = {'alvo': alvo, 'falta': falta, 'batida': falta == 0, 'e_sabado': wd == 5}
    if wd == 5:                                       # sabado: tudo o que falta e hoje
        r.update(dias=0, por_dia=0, sabado=falta, hoje_meta=int(feitas_hoje) + falta, hoje_falta=falta)
        return r
    dias = 5 - max(0, wd) if wd >= 0 else 5
    antes_de_hoje = int(feitas_semana) - int(feitas_hoje)
    resto = max(0, alvo - antes_de_hoje)              # o que falta contando o que ja saiu hoje
    sab = min(sab_cfg, resto)
    por_dia = int(math.ceil((resto - sab) / float(dias))) if dias > 0 else 0
    hoje_meta = por_dia if wd >= 0 else 0
    r.update(dias=dias, por_dia=por_dia, sabado=sab, hoje_meta=hoje_meta,
             hoje_falta=max(0, hoje_meta - int(feitas_hoje)) if wd >= 0 else 0)
    return r


# ── a sequencia de dias (o STREAK) ─────────────────────────────────────
def dia_util_anterior(d):
    """O dia de trabalho antes de `d` (domingo e folga: da segunda volta ao sabado)."""
    d = d - timedelta(days=1)
    if d.weekday() == 6:
        d = d - timedelta(days=1)
    return d


def sequencia(dias):
    """Dias de trabalho seguidos (com turno) terminando no mais recente; o
    domingo sem turno nao quebra (folga). Um domingo COM turno conta junto."""
    if not dias:
        return 0
    ultimo = max(dias)
    n, d = 1, ultimo
    while True:
        ant = d - timedelta(days=1)
        if ant in dias:
            n, d = n + 1, ant
            continue
        if ant.weekday() == 6 and (ant - timedelta(days=1)) in dias:
            n, d = n + 1, ant - timedelta(days=1)      # pulou o domingo de folga
            continue
        return n


def sequencia_vale(ultimo, hoje):
    """A sequencia ainda vale hoje? (o ultimo turno foi hoje ou no ultimo dia de trabalho)"""
    if ultimo is None:
        return False
    return ultimo >= dia_util_anterior(hoje)


# ── o ritmo do dia ─────────────────────────────────────────────────────
def lotes_de_hoje(registros, hoje):
    """[(ts, qtd)] dos lotes de hoje que tem hora (em ordem)."""
    out = []
    for r in registros or ():
        if len(r) < 5 or not r[4]:
            continue
        try:
            ts = float(r[4])
            q = int(r[1])
        except (TypeError, ValueError):
            continue
        if datetime.fromtimestamp(ts).date() != hoje:
            continue
        out.append((ts, q))
    out.sort()
    return out


def ritmo(lotes):
    """Pecas por hora (float) ou None se ainda nao da para medir. Os
    intervalos de pausa (ritmo abaixo de 60% da mediana) ficam de fora."""
    if len(lotes) < MIN_LOTES:
        return None
    trechos = []
    for (t0, _q0), (t1, q1) in zip(lotes, lotes[1:]):
        dt = t1 - t0
        if dt <= 0:
            continue
        trechos.append((dt, q1))
    if not trechos:
        return None
    taxas = sorted(q / dt for dt, q in trechos)
    med = taxas[len(taxas) // 2]
    bons = [(dt, q) for dt, q in trechos if q / dt >= med * 0.6]
    tempo = sum(dt for dt, _q in bons)
    if tempo < MIN_MINUTOS * 60:
        return None
    return sum(q for _dt, q in bons) / tempo * 3600.0


def tempo_txt(horas):
    """1.5 -> '1h30'; 0.25 -> '15 min'."""
    if horas is None or horas <= 0:
        return '0 min'
    m = int(round(horas * 60))
    if m < 60:
        return f"{m} min"
    return f"{m // 60}h{m % 60:02d}"
