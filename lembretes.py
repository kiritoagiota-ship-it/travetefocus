"""
lembretes.py — TraveteFocus
Avisos na barra do celular, com o app fechado (escolha do usuario):

  lancar      seg a sab, 7h (a hora de chegar no trabalho): bom dia, se ainda
              nao saiu nenhum lote no dia
  sequencia   seg a sex 17h / sabado 11h30: o dia de hoje ainda nao foi
              finalizado (FINALIZAR DIA) e ha uma sequencia (2+ dias) - o dia so conta na
              sequencia com o FINALIZAR DIA. Com lotes lancados: "finaliza
              e vira N+1 dias"; sem nenhum lote: "a sequencia esta em risco".
              Avisa quando o dia bate o recorde de dias seguidos.
  meta        seg a sex, 16h: se a meta do dia ainda nao foi batida, quanto falta
  fechamento  seg a sex 20h / sabado 13h: o dia (pecas, XP) e a faixa da semana
  faixa       sabado, 8h: se a proxima faixa da semana (2.500 / 3.000) cabe no
              sabado, quanto falta e quanto a mais rende
  resumo      sabado, 14h (dia do pagamento): pecas da semana e quanto vai receber
  faixa_nova  na hora (o app avisa ao gravar): a semana passou de uma faixa

Cada aviso e um CARD (Lembrete.java + res_layout/): o Yoru numa pose, o titulo,
a fala dele (uma por dia, sorteada), o texto, a barra de progresso com o
rotulo e os numeros da semana.

planejar() e so conta (testada no PC: dev/teste_lembretes.py). aplicar()
agenda no Android: AlarmManager -> org.travetefocus.Lembrete (java/), que mostra
o aviso com o que vai pronto. Tudo e refeito a cada vez que o app grava os
dados (o lote novo cancela o lembrete de hoje, a meta batida cancela o aviso
da meta...). Fora do Android nao faz nada. Nunca levanta excecao.
"""
import random
from datetime import datetime, timedelta

import metas

HORA_LANCAR = (7, 0)
HORA_SEQ = (17, 0)
HORA_SEQ_SAB = (11, 30)
HORA_META = (16, 0)
HORA_FECHAMENTO = (20, 0)
HORA_FECHAMENTO_SAB = (13, 0)
HORA_FAIXA = (8, 0)
HORA_RESUMO = (14, 0)
IDS = {'lancar': 7101, 'meta': 7102, 'faixa': 7103, 'resumo': 7104, 'sequencia': 7105, 'fechamento': 7106}
ID_FAIXA_NOVA = 7107

# o que o Yoru fala em cada aviso (uma por dia, sorteada)
FALAS = {
    'lancar': ("Bom dia! A espada está afiada. E a agulha?", "Chegou? Então bora, a meta não se bate sozinha.",
               "Primeiro lote do dia: o resto vem junto.", "Um lote de cada vez, como um golpe de cada vez.",
               "Café tomado? Hoje é dia de subir de nível."),
    'risco': ("Não deixa a sequência cair agora!", "Um lote e o dia finalizado já salvam a sequência.",
              "Eu seguro a linha, você lança o lote.", "Dias seguidos valem mais que um dia gigante."),
    'seq_fim': ("Não deixa o dia de hoje de fora!", "Um toque em FINALIZAR DIA e hoje entra para a conta.",
                "Dias seguidos valem mais que um dia gigante.", "O trabalho está feito. Só falta guardar."),
    'meta': ("Falta pouco. Último esforço!", "Respira e vai: a meta está logo ali.",
             "Cada peça agora conta em dobro na cabeça.", "Mais um pouco e a meta cai."),
    'fechamento': ("Bom trabalho hoje. Descansa a espada.", "Mais um dia no placar.",
                   "Amanhã a gente continua de onde parou.", "Isso é constância de verdade."),
    'faixa': ("Dá para fechar a faixa no sábado!", "O sábado decide o preço da semana.",
              "Meio período, faixa inteira."),
    'resumo': ("Semana fechada. Hora de colher!", "Pagamento chegando: missão cumprida.",
               "Que semana! Eu vi tudo daqui."),
    'faixa_nova': ("Subiu de faixa! Cada peça vale mais agora.", "Faixa nova desbloqueada!",
                   "Isso! A semana inteira ficou mais cara."),
}
POSES = {'lancar': 'guarda', 'risco': 'susto', 'seq_fim': 'meta', 'meta': 'meta', 'fechamento': 'vitoria',
         'faixa': 'meta', 'resumo': 'vitoria', 'faixa_nova': 'vitoria'}


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


def _fala(tipo, dia):
    """A fala do Yoru para o aviso `tipo` no dia (a mesma o dia todo)."""
    lista = FALAS.get(tipo) or ("",)
    return random.Random(f"{dia.isoformat()}-{tipo}").choice(lista)


def _xp_hoje(memorias, registros, hoje):
    xp = 0
    for m in memorias or ():
        if metas._dia_de(m.get('data', '')) == hoje:
            try:
                xp += int(m.get('xp', 0))
            except (TypeError, ValueError):
                pass
    for r in registros or ():
        try:
            d = metas._dia_de(r[3]) if len(r) > 3 and r[3] else hoje
            if d == hoje:
                xp += int(r[2])
        except (TypeError, ValueError, IndexError):
            pass
    return xp


def _dias_com_turno(memorias):
    dias = set()
    for m in memorias or ():
        d = metas._dia_de(m.get('data', ''))
        if d is not None:
            dias.add(d)
    return dias


def _melhor_seq(dias):
    """A maior sequencia de dias seguidos (com a regra do app: o domingo de
    folga nao quebra)."""
    melhor = n = 0
    ant = None
    for d in sorted(dias):
        if ant is not None and ((d - ant).days == 1 or
                                ((d - ant).days == 2 and (ant + timedelta(days=1)).weekday() == 6)):
            n += 1
        else:
            n = 1
        melhor = max(melhor, n)
        ant = d
    return melhor


def _card(tipo, dia, prog=0, prog_max=0, rotulo='', semana=''):
    return {'pose': POSES.get(tipo, 'guarda'), 'fala': _fala(tipo, dia), 'prog': int(max(0, prog)),
            'prog_max': int(max(0, prog_max)), 'rotulo': rotulo, 'semana': semana}


def planejar(agora, memorias, registros, cfg):
    """[{'id', 'tipo', 'quando' (datetime), 'titulo', 'texto', + o card: 'pose',
    'fala', 'prog', 'prog_max', 'rotulo', 'semana'}] - os avisos que valem a
    partir de `agora`, com os numeros de agora."""
    cfg = metas.completar_cfg(cfg)
    hoje = agora.date()
    sem, hj = metas.pecas_da_semana(memorias or [], registros or [], hoje)
    ganho_sem = metas.ganho(sem, cfg)
    linha_semana = f"Semana: {_br(sem)} peças · R$ {_br(ganho_sem, 2)}"
    planos = []

    # a meta da semana: a proxima faixa (ou a ultima, se ja passou de todas)
    prox = metas.proxima_faixa(sem, cfg)
    alvo = prox['inicio'] if prox else int(cfg['meta_bonus'])
    md_hoje = metas.meta_diaria(alvo, sem, hj, hoje, cfg['pecas_sabado'])

    # 1) lembrete de lancar: hoje (se ainda nao lancou e ainda nao passou da
    #    hora) ou no proximo dia de trabalho
    dia = hoje
    if hoje.weekday() == 6 or hj > 0 or agora >= _as(hoje, HORA_LANCAR):
        dia = _dia_util(hoje + timedelta(days=1))
    meta_l = md_hoje['hoje_meta'] if dia == hoje else 0
    p = {'id': IDS['lancar'], 'tipo': 'lancar', 'quando': _as(dia, HORA_LANCAR),
         'titulo': "⚔ Bom dia! Bora começar",
         'texto': "Chegou no trabalho? O Yoru já está de guarda. Assim que sair o primeiro lote, "
                  "lança no TraveteFocus!"}
    p.update(_card('lancar', dia, 0, meta_l, f"Meta de hoje: 0 / {_br(meta_l)}" if meta_l else '', linha_semana))
    planos.append(p)

    # 2) sequencia (seg a sex 17h, sabado 11h30): o dia so entra na sequencia
    #    com o turno FINALIZADO - avisa se hoje ainda nao tem turno salvo
    dias = _dias_com_turno(memorias)
    hora_s = HORA_SEQ_SAB if hoje.weekday() == 5 else HORA_SEQ
    if hoje.weekday() <= 5 and dias and hoje not in dias and agora < _as(hoje, hora_s):
        seq = metas.sequencia(dias) if metas.sequencia_vale(max(dias), hoje) else 0
        if seq >= 2:
            melhor = _melhor_seq(dias)
            novo = seq + 1
            bate = novo > melhor
            rot = f"Sequência: {seq} → {novo} dias"
            fim = f"Recorde: {melhor} dias"
            if hj > 0:
                p = {'id': IDS['sequencia'], 'tipo': 'seq_fim', 'quando': _as(hoje, hora_s),
                     'titulo': f"🔥 Finaliza o dia: {novo} dias seguidos",
                     'texto': f"Você já lançou {_br(hj)} peças hoje, mas hoje só entra na sequência "
                              f"quando você toca em FINALIZAR DIA. Finaliza e ela vai de {seq} para {novo} dias"
                              + (", o seu novo recorde!" if bate else ".")}
                p.update(_card('seq_fim', hoje, seq, max(melhor, novo), rot, fim))
            else:
                p = {'id': IDS['sequencia'], 'tipo': 'risco', 'quando': _as(hoje, hora_s),
                     'titulo': f"🔥 Sequência de {seq} dias em risco",
                     'texto': f"Ainda não saiu nenhum lote hoje. Lança e toca em FINALIZAR DIA para não "
                              f"perder os {seq} dias seguidos."
                              + (f" Fechando hoje, bate o recorde: {novo} dias!" if bate else "")}
                p.update(_card('risco', hoje, seq, max(melhor, novo), rot, fim))
            planos.append(p)

    # 3) meta do dia (seg a sex), as 16h de hoje, se ainda falta
    if hoje.weekday() <= 4 and agora < _as(hoje, HORA_META):
        md = md_hoje
        if md['hoje_meta'] > 0 and md['hoje_falta'] > 0:
            p = {'id': IDS['meta'], 'tipo': 'meta', 'quando': _as(hoje, HORA_META),
                 'titulo': "🎯 Meta de hoje",
                 'texto': f"Faltam {_br(md['hoje_falta'])} peças para a meta de hoje "
                          f"({_br(md['hoje_meta'])}). Já saíram {_br(hj)}."}
            p.update(_card('meta', hoje, hj, md['hoje_meta'],
                           f"Hoje: {_br(hj)} / {_br(md['hoje_meta'])}", linha_semana))
            planos.append(p)

    # 4) fechamento do dia (seg a sex 20h, sabado 13h), se ja saiu algo hoje
    hora_f = HORA_FECHAMENTO_SAB if hoje.weekday() == 5 else HORA_FECHAMENTO
    if hoje.weekday() <= 5 and hj > 0 and agora < _as(hoje, hora_f):
        xp = _xp_hoje(memorias, registros, hoje)
        if prox:
            falta_txt = f"faltam {_br(prox['falta'])} para R$ {_br(prox['valor'], 2)}"
        else:
            falta_txt = "já está na faixa máxima"
        # so fala em finalizar se ainda tem lote de hoje fora de um turno salvo
        pendente = any((metas._dia_de(r[3]) if len(r) > 3 and r[3] else hoje) == hoje
                       for r in registros or () if len(r) > 1)
        fim_txt = "Não esquece de tocar em FINALIZAR DIA." if pendente else "Dia finalizado. Bom descanso!"
        p = {'id': IDS['fechamento'], 'tipo': 'fechamento', 'quando': _as(hoje, hora_f),
             'titulo': "📊 Fechamento do dia",
             'texto': f"Hoje: {_br(hj)} peças · +{_br(xp)} XP. Na semana, {falta_txt}. " + fim_txt}
        p.update(_card('fechamento', hoje, sem, alvo, f"Semana: {_br(sem)} / {_br(alvo)}",
                       f"R$ {_br(ganho_sem, 2)}"))
        planos.append(p)

    # 5) faixa: no sabado desta semana, as 8h, se a proxima faixa cabe no sabado
    sabado = hoje + timedelta(days=(5 - hoje.weekday()) % 7) if hoje.weekday() != 6 else None
    if sabado is not None and prox and agora < _as(sabado, HORA_FAIXA):
        if 0 < prox['falta'] <= int(cfg['pecas_sabado']) * 1.5:
            p = {'id': IDS['faixa'], 'tipo': 'faixa', 'quando': _as(sabado, HORA_FAIXA),
                 'titulo': f"⭐ Faixa de R$ {_br(prox['valor'], 2)} ao alcance",
                 'texto': f"Faltam {_br(prox['falta'])} peças para todas as peças da semana "
                          f"valerem R$ {_br(prox['valor'], 2)} (+R$ {_br(prox['a_mais'], 2)})."}
            p.update(_card('faixa', sabado, sem, prox['inicio'], f"Semana: {_br(sem)} / {_br(prox['inicio'])}",
                           f"R$ {_br(ganho_sem, 2)}"))
            planos.append(p)

    # 6) resumo da semana: sabado, 14h
    if sabado is not None and agora < _as(sabado, HORA_RESUMO) and sem > 0:
        _i, _ini, valor, _n = metas.faixa_de(sem, cfg)
        topo = int(cfg['meta_bonus'])
        p = {'id': IDS['resumo'], 'tipo': 'resumo', 'quando': _as(sabado, HORA_RESUMO),
             'titulo': "💰 Resumo da semana",
             'texto': f"{_br(sem)} peças na semana · R$ {_br(ganho_sem, 2)} "
                      f"(cada peça a R$ {_br(valor, 2)}). Bom pagamento!"}
        p.update(_card('resumo', sabado, min(sem, topo), topo, f"{_br(sem)} peças · R$ {_br(valor, 2)} cada",
                       f"R$ {_br(ganho_sem, 2)}"))
        planos.append(p)
    return planos


def aviso_faixa_nova(antes, depois, cfg, hoje=None):
    """O aviso de FAIXA NOVA quando as pecas da semana passam de `antes` para
    `depois` cruzando o inicio de uma faixa (ou None)."""
    cfg = metas.completar_cfg(cfg)
    i0 = metas.faixa_de(antes, cfg)[0]
    i1, ini, valor, _n = metas.faixa_de(depois, cfg)
    if i1 <= i0:
        return None
    hoje = hoje or datetime.now().date()
    prox = metas.proxima_faixa(depois, cfg)
    p = {'id': ID_FAIXA_NOVA, 'tipo': 'faixa_nova', 'quando': None,
         'titulo': f"⭐ Faixa nova: R$ {_br(valor, 2)}",
         'texto': f"A semana passou de {_br(ini)} peças: todas as peças da semana valem "
                  f"R$ {_br(valor, 2)} agora!"}
    if prox:
        p.update(_card('faixa_nova', hoje, depois, prox['inicio'], f"Próxima: {_br(prox['inicio'])} peças",
                       f"Semana: {_br(depois)} · R$ {_br(metas.ganho(depois, cfg), 2)}"))
    else:
        p.update(_card('faixa_nova', hoje, 1, 1, "Faixa máxima!",
                       f"Semana: {_br(depois)} · R$ {_br(metas.ganho(depois, cfg), 2)}"))
    return p


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


CAMPOS_CARD = ('pose', 'fala', 'prog', 'prog_max', 'rotulo', 'semana')


def _intent(ctx, nid, titulo, texto, card=None):
    """O Intent para o recebedor, com o texto e o card do aviso `nid`."""
    from jnius import autoclass
    Intent = autoclass('android.content.Intent')
    it = Intent()
    it.setClassName(ctx.getPackageName(), RECEBEDOR)
    it.setAction('org.travetefocus.LEMBRETE_%d' % nid)
    if titulo is not None:
        # os textos vao num Bundle com putString: o putExtra tem varias versoes
        # e o pyjnius escolhia a errada para texto do Python (chegava como
        # bytes: o aviso aparecia so com "TraveteFocus", sem titulo nem texto)
        Bundle = autoclass('android.os.Bundle')
        b = Bundle()
        b.putString('id', str(nid))
        b.putString('titulo', str(titulo))
        b.putString('texto', str(texto))
        for k in CAMPOS_CARD:
            v = (card or {}).get(k)
            if v is not None and v != '':
                b.putString(k, str(v))                 # os numeros tambem vao como texto
        it.putExtras(b)
    return it


def _agendar(nid, titulo, texto, quando_ms, cancelar_so=False, card=None):
    """Agenda (ou so cancela) o aviso `nid` no AlarmManager -> o recebedor
    org.travetefocus.Lembrete mostra o aviso na hora, com o app fechado.
    `card`: o plano (pose, fala, prog...) para o card HUD."""
    from jnius import autoclass, cast
    PA = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    PendingIntent = autoclass('android.app.PendingIntent')
    AlarmManager = autoclass('android.app.AlarmManager')
    sdk = _sdk()
    ctx = PA.mActivity
    am = cast('android.app.AlarmManager', ctx.getSystemService(Context.ALARM_SERVICE))
    flags = PendingIntent.FLAG_UPDATE_CURRENT
    if sdk >= 23:
        flags |= PendingIntent.FLAG_IMMUTABLE
    it = _intent(ctx, nid, None if cancelar_so else titulo, texto, card)
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
                _agendar(nid, p['titulo'], p['texto'], p['quando'].timestamp() * 1000, card=p)
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


def avisar_agora(plano):
    """Mostra o card `plano` NA HORA pelo recebedor (o mesmo card dos
    agendados): o aviso de FAIXA NOVA. Devolve '' ou o erro."""
    if not _android() or not plano:
        return 'Os avisos só funcionam no celular.'
    try:
        from jnius import autoclass
        ctx = autoclass('org.kivy.android.PythonActivity').mActivity
        ctx.sendBroadcast(_intent(ctx, int(plano['id']), plano['titulo'], plano['texto'], plano))
        return ''
    except Exception as ex:
        print(f"[lembretes] avisar agora: {ex}")
        return str(ex)[:160]


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
                 (time.time() + seg) * 1000,
                 card={'pose': 'guarda', 'fala': "Se chegou, está tudo certo. Pode confiar nos avisos!",
                       'prog': 2, 'prog_max': 2, 'rotulo': "Teste: 2 / 2", 'semana': "Card do TraveteFocus"})
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
