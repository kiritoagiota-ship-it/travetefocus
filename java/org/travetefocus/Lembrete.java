package org.travetefocus;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.widget.RemoteViews;

/**
 * Mostra um aviso na barra do celular na hora agendada pelo app (lembretes.py),
 * mesmo com o app fechado, ou na hora (faixa alcancada). O texto vem pronto no
 * Intent. No Android 7+ o aviso e o CARD HUD do app (res_layout/notif_hud*.xml):
 * o Yoru numa pose, o titulo, a fala dele, o texto, a barra de progresso e os
 * numeros da semana. Se o card falhar por qualquer motivo, sai o aviso simples.
 * Tocar no aviso abre o TraveteFocus.
 */
public class Lembrete extends BroadcastReceiver {
    private static final String CANAL = "travete_lembretes";

    /** Le um texto do aviso em qualquer formato que tenha chegado (texto,
     *  CharSequence ou bytes em UTF-8). */
    private static String ler(Intent it, String chave) {
        try {
            Bundle b = it.getExtras();
            if (b == null) {
                return null;
            }
            Object o = b.get(chave);
            if (o == null) {
                return null;
            }
            if (o instanceof byte[]) {
                return new String((byte[]) o, "UTF-8");
            }
            return o.toString();
        } catch (Exception e) {
            return null;
        }
    }

    private static int numero(String s, int padrao) {
        try {
            return Integer.parseInt(s.trim());
        } catch (Exception e) {
            return padrao;
        }
    }

    private static int recurso(Context ctx, String nome, String tipo) {
        return ctx.getResources().getIdentifier(nome, tipo, ctx.getPackageName());
    }

    /** Preenche o card (pequeno ou grande). So mexe nas pecas que o layout tem. */
    private static RemoteViews card(Context ctx, String layout, boolean grande, String titulo, String texto,
                                    String fala, String pose, int prog, int max, String rotulo, String semana) {
        int lay = recurso(ctx, layout, "layout");
        if (lay == 0) {
            return null;
        }
        RemoteViews v = new RemoteViews(ctx.getPackageName(), lay);
        v.setTextViewText(recurso(ctx, "tf_titulo", "id"), titulo);
        v.setTextViewText(recurso(ctx, "tf_texto", "id"), texto);
        int img = recurso(ctx, "yoru_" + (pose == null ? "guarda" : pose), "drawable");
        if (img == 0) {
            img = recurso(ctx, "yoru_guarda", "drawable");
        }
        int idYoru = recurso(ctx, "tf_yoru", "id");
        if (img != 0) {
            v.setImageViewResource(idYoru, img);
        } else {
            v.setViewVisibility(idYoru, View.GONE);
        }
        int idBarra = recurso(ctx, "tf_barra", "id");
        if (max > 0) {
            v.setProgressBar(idBarra, max, Math.max(0, Math.min(prog, max)), false);
        } else {
            v.setViewVisibility(idBarra, View.GONE);
        }
        if (grande) {
            int idFala = recurso(ctx, "tf_fala", "id");
            if (fala != null && fala.length() > 0) {
                v.setTextViewText(idFala, fala);
            } else {
                v.setViewVisibility(idFala, View.GONE);
            }
            int idRot = recurso(ctx, "tf_rotulo", "id");
            int idSem = recurso(ctx, "tf_semana", "id");
            v.setTextViewText(idRot, rotulo == null ? "" : rotulo);
            v.setTextViewText(idSem, semana == null ? "" : semana);
        }
        return v;
    }

    @Override
    public void onReceive(Context ctx, Intent it) {
        try {
            String titulo = ler(it, "titulo");
            String texto = ler(it, "texto");
            int id = numero(ler(it, "id"), 7100);
            if (titulo == null) {
                titulo = "TraveteFocus";
            }
            if (texto == null) {
                texto = "";
            }
            String fala = ler(it, "fala");
            String pose = ler(it, "pose");
            String rotulo = ler(it, "rotulo");
            String semana = ler(it, "semana");
            int prog = numero(ler(it, "prog"), 0);
            int max = numero(ler(it, "prog_max"), 0);

            NotificationManager nm = (NotificationManager) ctx.getSystemService(Context.NOTIFICATION_SERVICE);
            if (nm == null) {
                return;
            }
            if (Build.VERSION.SDK_INT >= 26) {
                NotificationChannel ch = new NotificationChannel(CANAL, "Lembretes",
                        NotificationManager.IMPORTANCE_DEFAULT);
                ch.setDescription("Lembrete de lancar, metas e resumo da semana");
                nm.createNotificationChannel(ch);
            }
            PendingIntent pi = null;
            Intent abrir = ctx.getPackageManager().getLaunchIntentForPackage(ctx.getPackageName());
            if (abrir != null) {
                int flags = PendingIntent.FLAG_UPDATE_CURRENT;
                if (Build.VERSION.SDK_INT >= 23) {
                    flags = flags | PendingIntent.FLAG_IMMUTABLE;
                }
                pi = PendingIntent.getActivity(ctx, id, abrir, flags);
            }
            int icone = recurso(ctx, "notif_icone", "drawable");
            if (icone == 0) {
                icone = ctx.getApplicationInfo().icon;
            }

            Notification aviso = null;
            // 1) o card HUD (Android 7+)
            if (Build.VERSION.SDK_INT >= 24) {
                try {
                    RemoteViews pequeno = card(ctx, "notif_hud", false, titulo, texto, fala, pose, prog, max,
                            rotulo, semana);
                    RemoteViews grande = card(ctx, "notif_hud_grande", true, titulo, texto, fala, pose, prog, max,
                            rotulo, semana);
                    if (pequeno != null && grande != null) {
                        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                                ? new Notification.Builder(ctx, CANAL) : new Notification.Builder(ctx);
                        b.setSmallIcon(icone);
                        b.setContentTitle(titulo);
                        b.setContentText(texto);
                        b.setStyle(new Notification.DecoratedCustomViewStyle());
                        b.setCustomContentView(pequeno);
                        b.setCustomBigContentView(grande);
                        b.setAutoCancel(true);
                        b.setColor(0xFF00E5FF);
                        if (pi != null) {
                            b.setContentIntent(pi);
                        }
                        aviso = b.build();
                    }
                } catch (Exception e) {
                    aviso = null;
                }
            }
            // 2) o aviso simples (se o card nao deu)
            if (aviso == null) {
                Notification.Builder b = Build.VERSION.SDK_INT >= 26
                        ? new Notification.Builder(ctx, CANAL) : new Notification.Builder(ctx);
                b.setSmallIcon(icone);
                b.setContentTitle(titulo);
                b.setContentText(texto);
                String longo = (fala != null && fala.length() > 0) ? fala + "\n" + texto : texto;
                b.setStyle(new Notification.BigTextStyle().bigText(longo));
                b.setAutoCancel(true);
                b.setColor(0xFF00E5FF);
                if (max > 0 && Build.VERSION.SDK_INT >= 21) {
                    b.setProgress(max, Math.max(0, Math.min(prog, max)), false);
                }
                if (pi != null) {
                    b.setContentIntent(pi);
                }
                aviso = b.build();
            }
            nm.notify(id, aviso);
        } catch (Exception e) {
            // um aviso nunca pode derrubar nada
        }
    }
}
