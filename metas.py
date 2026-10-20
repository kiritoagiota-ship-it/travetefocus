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


def pecas_da_semana(memorias, registros, hoje):
    """(pecas na semana, pecas de hoje): turnos finalizados + lotes ainda nao
    finalizados (os lotes sem dia sao de hoje)."""
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
        d = _dia_de(r[3]) if len(r) > 3 and r[3] else hoje
        if d is None or not (seg <= d <= sab):
            continue
        semana += q
        if d == hoje:
            hoje_n += q
    return semana, hoje_n


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
