"""
lembretes.py — TraveteFocus
Avisos na barra do celular, com o app fechado (escolha do usuario):

  lancar   seg a sab, 11h: se ainda nao saiu nenhum lote no dia, o Yoru lembra
  meta     seg a sex, 16h: se a meta do dia ainda nao foi batida, quanto falta
  faixa    sabado, 8h: se a proxima faixa da semana (2.500 / 3.000) cabe no
           sabado, quanto falta e quanto a mais rende
  resumo   sabado, 14h (dia do pagamento): pecas da semana e quanto vai receber

planejar() e so conta (testada no PC: dev/teste_lembretes.py). aplicar()
agenda no Android: AlarmManager -> org.travetefocus.Lembrete (java/), que mostra
o aviso com o texto que vai pronto. Tudo e refeito a cada vez que o app grava
os dados (o lote novo cancela o lembrete de hoje, a meta batida cancela o aviso
da meta...). Fora do Android nao faz nada. Nunca levanta excecao.
"""
from datetime import datetime, timedelta

import metas

HORA_LANCAR = (11, 0)
HORA_META = (16, 0)
HORA_FAIXA = (8, 0)
HORA_RESUMO = (14, 0)
IDS = {'lancar': 7101, 'meta': 7102, 'faixa': 7103, 'resumo': 7104}


def _as(dia, hm):
    return datetime(dia.year, dia.month, dia.day, hm[0], hm[1])


def _dia_util(d):
    """O proprio dia ou o proximo que nao e domingo."""
    while d.weekday() == 6:
        d += timedelta(days=1)
    return d


def _br(v, casas=0):
    s = f"{float(v):,.{casas}f}"
    return s.replace(',', '#').replace('.', ',').replace('#', '.')


def planejar(agora, memorias, registros, cfg):
    """[{'id', 'tipo', 'quando' (datetime), 'titulo', 'texto'}] - os avisos que
    valem a partir de `agora`, com os numeros de agora."""
    cfg = metas.completar_cfg(cfg)
    hoje = agora.date()
    sem, hj = metas.pecas_da_semana(memorias or [], registros or [], hoje)
    planos = []

    # 1) lembrete de lancar: hoje (se ainda nao lancou e ainda nao passou da
    #    hora) ou no proximo dia de trabalho
    dia = hoje
    if hoje.weekday() == 6 or hj > 0 or agora >= _as(hoje, HORA_LANCAR):
        dia = _dia_util(hoje + timedelta(days=1))
    planos.append({'id': IDS['lancar'], 'tipo': 'lancar', 'quando': _as(dia, HORA_LANCAR),
                   'titulo': "⚔ Hora de lançar",
                   'texto': "O Yoru está esperando os lotes de hoje. Abre o TraveteFocus e lança o primeiro!"})

    # a meta da semana: a proxima faixa (ou a ultima, se ja passou de todas)
    prox = metas.proxima_faixa(sem, cfg)
    alvo = prox['inicio'] if prox else int(cfg['meta_bonus'])

    # 2) meta do dia (seg a sex), as 16h de hoje, se ainda falta
    if hoje.weekday() <= 4 and agora < _as(hoje, HORA_META):
        md = metas.meta_diaria(alvo, sem, hj, hoje, cfg['pecas_sabado'])
        if md['hoje_meta'] > 0 and md['hoje_falta'] > 0:
            planos.append({'id': IDS['meta'], 'tipo': 'meta', 'quando': _as(hoje, HORA_META),
                           'titulo': "🎯 Meta de hoje",
                           'texto': f"Faltam {_br(md['hoje_falta'])} peças para a meta de hoje "
                                    f"({_br(md['hoje_meta'])}). Já saíram {_br(hj)}."})

    # 3) faixa: no sabado desta semana, as 8h, se a proxima faixa cabe no sabado
    sabado = hoje + timedelta(days=(5 - hoje.weekday()) % 7) if hoje.weekday() != 6 else None
    if sabado is not None and prox and agora < _as(sabado, HORA_FAIXA):
        if 0 < prox['falta'] <= int(cfg['pecas_sabado']) * 1.5:
            planos.append({'id': IDS['faixa'], 'tipo': 'faixa', 'quando': _as(sabado, HORA_FAIXA),
                           'titulo': f"⭐ Faixa de R$ {_br(prox['valor'], 2)} ao alcance",
                           'texto': f"Faltam {_br(prox['falta'])} peças para todas as peças da semana "
                                    f"valerem R$ {_br(prox['valor'], 2)} (+R$ {_br(prox['a_mais'], 2)})."})

    # 4) resumo da semana: sabado, 14h
    if sabado is not None and agora < _as(sabado, HORA_RESUMO) and sem > 0:
        _i, _ini, valor, _n = metas.faixa_de(sem, cfg)
        planos.append({'id': IDS['resumo'], 'tipo': 'resumo', 'quando': _as(sabado, HORA_RESUMO),
                       'titulo': "💰 Resumo da semana",
                       'texto': f"{_br(sem)} peças na semana · R$ {_br(metas.ganho(sem, cfg), 2)} "
                                f"(cada peça a R$ {_br(valor, 2)}). Bom pagamento!"})
    return planos


# ── Android ──────────────────────────────────────────────────────────────
def _android():
    try:
        from kivy.utils import platform
        return platform == 'android'
    except Exception:
        return False


def pedir_permissao():
    """Android 13+: pede a permissao de mostrar avisos (uma vez)."""
    if not _android():
        return
    try:
        from jnius import autoclass
        sdk = autoclass('android.os.Build$VERSION').SDK_INT
        if sdk < 33:
            return
        from android.permissions import request_permissions, check_permission
        p = 'android.permission.POST_NOTIFICATIONS'
        if not check_permission(p):
            request_permissions([p])
    except Exception as e:
        print(f"[lembretes] permissao: {e}")


def aplicar(planos, ligado=True):
    """Agenda os avisos de `planos` e cancela os outros (ligado=False: cancela tudo)."""
    if not _android():
        return
    try:
        from jnius import autoclass, cast
        PA = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        Intent = autoclass('android.content.Intent')
        PendingIntent = autoclass('android.app.PendingIntent')
        AlarmManager = autoclass('android.app.AlarmManager')
        sdk = autoclass('android.os.Build$VERSION').SDK_INT
        ctx = PA.mActivity
        am = cast('android.app.AlarmManager', ctx.getSystemService(Context.ALARM_SERVICE))
        flags = PendingIntent.FLAG_UPDATE_CURRENT
        if sdk >= 23:
            flags |= PendingIntent.FLAG_IMMUTABLE
        por_id = {p['id']: p for p in (planos if ligado else [])}
        for nid in IDS.values():
            it = Intent()
            it.setClassName(ctx.getPackageName(), 'org.travetefocus.Lembrete')
            it.setAction('org.travetefocus.LEMBRETE_%d' % nid)
            p = por_id.get(nid)
            if p is not None:
                it.putExtra('id', str(nid))
                it.putExtra('titulo', str(p['titulo']))
                it.putExtra('texto', str(p['texto']))
            pi = PendingIntent.getBroadcast(ctx, nid, it, flags)
            am.cancel(pi)
            if p is None:
                continue
            quando = int(p['quando'].timestamp() * 1000)
            if sdk >= 23:
                am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, quando, pi)
            else:
                am.set(AlarmManager.RTC_WAKEUP, quando, pi)
    except Exception as e:
        print(f"[lembretes] agendar: {e}")


def replanejar(app):
    """Refaz os avisos com os dados de agora (chamado ao gravar e ao sair)."""
    if not _android():
        return
    try:
        ligado = bool(getattr(app, 'lembretes', True))
        planos = planejar(datetime.now(), app.memorias, app.registros, app.config_ganhos) if ligado else []
        aplicar(planos, ligado)
    except Exception as e:
        print(f"[lembretes] {e}")
