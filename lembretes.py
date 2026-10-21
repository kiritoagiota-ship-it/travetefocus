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
ID_TESTE = 7199
RECEBEDOR = 'org.travetefocus.Lembrete'


def _android():
    try:
        from kivy.utils import platform
        return platform == 'android'
    except Exception:
        return False


def _sdk():
    from jnius import autoclass
    return autoclass('android.os.Build$VERSION').SDK_INT


def pedir_permissao():
    """Android 13+: pede a permissao de mostrar avisos (uma vez)."""
    if not _android():
        return
    try:
        if _sdk() < 33:
            return
        from android.permissions import request_permissions, check_permission
        p = 'android.permission.POST_NOTIFICATIONS'
        if not check_permission(p):
            request_permissions([p])
    except Exception as e:
        print(f"[lembretes] permissao: {e}")


def _agendar(nid, titulo, texto, quando_ms, cancelar_so=False):
    """Agenda (ou so cancela) o aviso `nid` no AlarmManager -> o recebedor
    org.travetefocus.Lembrete mostra o aviso na hora, com o app fechado."""
    from jnius import autoclass, cast
    PA = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    Intent = autoclass('android.content.Intent')
    PendingIntent = autoclass('android.app.PendingIntent')
    AlarmManager = autoclass('android.app.AlarmManager')
    sdk = _sdk()
    ctx = PA.mActivity
    am = cast('android.app.AlarmManager', ctx.getSystemService(Context.ALARM_SERVICE))
    flags = PendingIntent.FLAG_UPDATE_CURRENT
    if sdk >= 23:
        flags |= PendingIntent.FLAG_IMMUTABLE
    it = Intent()
    it.setClassName(ctx.getPackageName(), RECEBEDOR)
    it.setAction('org.travetefocus.LEMBRETE_%d' % nid)
    if not cancelar_so:
        # os textos vao num Bundle com putString: o putExtra tem varias versoes
        # e o pyjnius escolhia a errada para texto do Python (chegava como
        # bytes: o aviso aparecia so com "TraveteFocus", sem titulo nem texto)
        Bundle = autoclass('android.os.Bundle')
        b = Bundle()
        b.putString('id', str(nid))
        b.putString('titulo', str(titulo))
        b.putString('texto', str(texto))
        it.putExtras(b)
    pi = PendingIntent.getBroadcast(ctx, nid, it, flags)
    am.cancel(pi)
    if cancelar_so:
        return
    # no horario EXATO (como um despertador) quando o Android deixa: o modo
    # aproximado de antes podia ser atrasado muito pela economia de bateria
    # (Samsung) e o aviso nao chegava na hora
    if _pode_exato(am, sdk):
        am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, int(quando_ms), pi)
    elif sdk >= 23:
        am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, int(quando_ms), pi)
    else:
        am.set(AlarmManager.RTC_WAKEUP, int(quando_ms), pi)


def _pode_exato(am, sdk):
    """O Android deixa agendar no horario exato? (12+ pede permissao: o app
    declara USE_EXACT_ALARM / SCHEDULE_EXACT_ALARM no buildozer.spec)"""
    if sdk < 23:
        return False
    if sdk < 31:
        return True
    try:
        return bool(am.canScheduleExactAlarms())
    except Exception:
        return False


CANAL = 'travete_lembretes'          # o mesmo canal do recebedor (Lembrete.java)


def mostrar_agora(nid, titulo, texto):
    """Mostra um aviso NA HORA, direto do app (sem agendar): prova que o
    celular mostra os avisos do TraveteFocus. Devolve '' ou o erro."""
    if not _android():
        return 'Os avisos só funcionam no celular.'
    try:
        from jnius import autoclass, cast
        PA = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        ctx = PA.mActivity
        sdk = _sdk()
        nm = cast('android.app.NotificationManager', ctx.getSystemService(Context.NOTIFICATION_SERVICE))
        if sdk >= 26:
            NotificationChannel = autoclass('android.app.NotificationChannel')
            NotificationManager = autoclass('android.app.NotificationManager')
            ch = NotificationChannel(CANAL, 'Lembretes', NotificationManager.IMPORTANCE_DEFAULT)
            nm.createNotificationChannel(ch)
            b = autoclass('android.app.Notification$Builder')(ctx, CANAL)
        else:
            b = autoclass('android.app.Notification$Builder')(ctx)
        icone = ctx.getResources().getIdentifier('notif_icone', 'drawable', ctx.getPackageName())
        if not icone:
            icone = ctx.getApplicationInfo().icon
        b.setSmallIcon(icone)
        b.setContentTitle(str(titulo))
        b.setContentText(str(texto))
        b.setAutoCancel(True)
        nm.notify(int(nid), b.build())
        return ''
    except Exception as ex:
        return str(ex)[:160]


def aplicar(planos, ligado=True):
    """Agenda os avisos de `planos` e cancela os outros (ligado=False: cancela tudo)."""
    if not _android():
        return
    try:
        por_id = {p['id']: p for p in (planos if ligado else [])}
        for nid in IDS.values():
            p = por_id.get(nid)
            if p is None:
                _agendar(nid, '', '', 0, cancelar_so=True)
            else:
                _agendar(nid, p['titulo'], p['texto'], p['quando'].timestamp() * 1000)
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


# ── diagnostico (o painel AVISOS do menu) ────────────────────────────────
def estado():
    """O que pode impedir os avisos, conferido no proprio celular:
    {'android', 'permissao', 'ativadas', 'recebedor', 'sdk', 'erro'}
    (None = nao deu para conferir)."""
    e = {'android': _android(), 'permissao': None, 'ativadas': None, 'recebedor': None, 'exato': None,
         'sdk': None, 'erro': ''}
    if not e['android']:
        return e
    try:
        from jnius import autoclass, cast
        PA = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        ctx = PA.mActivity
        sdk = _sdk()
        e['sdk'] = sdk
        if sdk >= 33:
            from android.permissions import check_permission
            e['permissao'] = bool(check_permission('android.permission.POST_NOTIFICATIONS'))
        else:
            e['permissao'] = True
        nm = cast('android.app.NotificationManager', ctx.getSystemService(Context.NOTIFICATION_SERVICE))
        if sdk >= 24:
            e['ativadas'] = bool(nm.areNotificationsEnabled())
        try:
            ComponentName = autoclass('android.content.ComponentName')
            ctx.getPackageManager().getReceiverInfo(ComponentName(ctx.getPackageName(), RECEBEDOR), 0)
            e['recebedor'] = True
        except Exception:
            e['recebedor'] = False
        try:
            am = cast('android.app.AlarmManager', ctx.getSystemService(Context.ALARM_SERVICE))
            e['exato'] = _pode_exato(am, sdk)
        except Exception:
            e['exato'] = None
    except Exception as ex:
        e['erro'] = str(ex)[:120]
    return e


ID_TESTE_DIRETO = 7198


def testar(seg=5):
    """O teste em duas partes: (1) um aviso DIRETO agora (o celular mostra os
    avisos do app?) e (2) um AGENDADO daqui a `seg` s pelo mesmo caminho dos
    lembretes (AlarmManager -> recebedor). Devolve (erro_direto, erro_agendado)."""
    if not _android():
        return ('Os avisos só funcionam no celular.',) * 2
    e1 = mostrar_agora(ID_TESTE_DIRETO, "TraveteFocus: teste 1 de 2",
                       "Aviso direto: se você está lendo isto, o celular mostra os avisos do app.")
    try:
        import time
        _agendar(ID_TESTE, "⚔ TraveteFocus: teste 2 de 2",
                 "Aviso agendado: é assim que os lembretes vão chegar na hora certa.",
                 (time.time() + seg) * 1000)
        e2 = ''
    except Exception as ex:
        e2 = str(ex)[:160]
    return e1, e2


def apareceu(nid=ID_TESTE):
    """O aviso `nid` esta na barra agora? (None = nao deu para conferir)"""
    if not _android():
        return None
    try:
        from jnius import autoclass, cast
        PA = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        if _sdk() < 23:
            return None
        nm = cast('android.app.NotificationManager',
                  PA.mActivity.getSystemService(Context.NOTIFICATION_SERVICE))
        return any(int(sb.getId()) == nid for sb in nm.getActiveNotifications())
    except Exception as ex:
        print(f"[lembretes] apareceu: {ex}")
        return None


def abrir_config():
    """Abre a tela do Android com as notificacoes do app (para liberar)."""
    if not _android():
        return
    try:
        from jnius import autoclass
        PA = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        Settings = autoclass('android.provider.Settings')
        Uri = autoclass('android.net.Uri')
        ctx = PA.mActivity
        pkg = ctx.getPackageName()
        pm = ctx.getPackageManager()
        tentativas = []
        if _sdk() >= 26:
            it = Intent('android.settings.APP_NOTIFICATION_SETTINGS')
            it.putExtra('android.provider.extra.APP_PACKAGE', pkg)
            it.putExtra('app_package', pkg)                       # (Androids mais antigos/Samsung)
            it.putExtra('app_uid', ctx.getApplicationInfo().uid)
            tentativas.append(it)
        # a tela de informacoes do app existe em todo Android (Notificacoes e Bateria)
        tentativas.append(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse('package:' + pkg)))
        for it in tentativas:
            it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            try:
                if it.resolveActivity(pm) is None:
                    continue
                ctx.startActivity(it)
                return
            except Exception as ex:
                print(f"[lembretes] abrir config (tentando a proxima): {ex}")
    except Exception as ex:
        print(f"[lembretes] abrir config: {ex}")


_DIAS = ('seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom')


def proximos(app, agora=None):
    """[(quando 'qua 16:00', titulo)] dos avisos agendados com os dados de agora."""
    agora = agora or datetime.now()
    try:
        planos = planejar(agora, app.memorias, app.registros, app.config_ganhos)
    except Exception as ex:
        print(f"[lembretes] proximos: {ex}")
        return []
    out = []
    for p in sorted(planos, key=lambda q: q['quando']):
        q = p['quando']
        dia = 'hoje' if q.date() == agora.date() else (
            'amanhã' if (q.date() - agora.date()).days == 1 else _DIAS[q.weekday()])
        out.append((f"{dia} {q.strftime('%H:%M')}", p['titulo']))
    return out
