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

/**
 * Mostra um aviso na barra do celular na hora agendada pelo app (lembretes.py),
 * mesmo com o app fechado. O texto vem pronto no Intent (titulo, texto, id).
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

    @Override
    public void onReceive(Context ctx, Intent it) {
        try {
            String titulo = ler(it, "titulo");
            String texto = ler(it, "texto");
            String sid = ler(it, "id");
            int id = 7100;
            try {
                id = Integer.parseInt(sid);
            } catch (Exception e) {
                id = 7100;
            }
            if (titulo == null) {
                titulo = "TraveteFocus";
            }
            if (texto == null) {
                texto = "";
            }
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
            Notification.Builder b;
            if (Build.VERSION.SDK_INT >= 26) {
                b = new Notification.Builder(ctx, CANAL);
            } else {
                b = new Notification.Builder(ctx);
            }
            int icone = ctx.getResources().getIdentifier("notif_icone", "drawable", ctx.getPackageName());
            if (icone == 0) {
                icone = ctx.getApplicationInfo().icon;
            }
            b.setSmallIcon(icone);
            b.setContentTitle(titulo);
            b.setContentText(texto);
            b.setStyle(new Notification.BigTextStyle().bigText(texto));
            b.setAutoCancel(true);
            b.setColor(0xFF00E5FF);
            if (pi != null) {
                b.setContentIntent(pi);
            }
            nm.notify(id, b.build());
        } catch (Exception e) {
            // um aviso nunca pode derrubar nada
        }
    }
}
