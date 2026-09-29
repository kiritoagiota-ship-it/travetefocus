"""Gera os efeitos finais (44,1 kHz mono) em tf_repo/sons/ a partir das
amostras CC0. Cada efeito: transiente cedo (sincroniza com o quadro do
golpe), graves de corpo, agudos domados para alto-falante de celular."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import audio as A

SAIDA = r'C:\Users\kirit\travetefocus\app\sons'
L = A.ler

def alinhar(a, t_pico, em):
    """desloca `a` para o pico cair em `em` segundos (corta ou atrasa)."""
    d = t_pico - em
    return (A.seg(a, d), 0.0) if d > 0 else (a, -d)

def final(nome, a, rms_alvo, lp=11000, hp=60, cauda=0.08, fade_ini=0.002):
    a = A.aparar(a, lim=0.002, antes=0.003, depois=0.05)
    if hp: a = A.hp(a, hp)
    if lp: a = A.lp(a, lp)
    a = A.fade(a, fade_ini, cauda)
    a = A.normalizar(a, -1.0)
    g = A.db(rms_alvo - A.rms_db(a))
    if g > 1.0:                       # sobe o volume com saturacao suave em vez de estourar
        a = A.saturar(A.ganho(a, g), 1.0)
        a = A.normalizar(a, -1.0)
    else:
        a = A.ganho(a, g)
    A.escrever(os.path.join(SAIDA, nome + '.wav'), a)
    print(f"{nome:14s} {A.dur(a):.2f}s pico@{A.pico_t(a):.3f} rms={A.rms_db(a):.1f}dB")

def thump(f0=90, f1=45, d=0.14, vol=0.8):
    return A.seno(f0, f1, d, vol, queda=5.0, atk=0.002)

# ── corte (Elucidator): ar + "shing" metalico + peso ─────────────────
metal, tm = alinhar(L('sword.7'), 0.33, 0.05)     # o "shiing" (com anel) entra em ~0,05 s
ar = L('swish-7')
corte = A.mix((ar, 0.0, 0.9), (metal, tm, 0.85), (thump(), 0.045, 0.5))
final('corte', A.seg(corte, 0, 0.7), -15, cauda=0.2)

# ── corte2 (Dark Repulser): mais agudo e cristalino ──────────────────
metal2 = A.reamostrar(L('sword.6'), 1.10)
ar2 = L('swish-9')
cristal = A.fade(A.reamostrar(L('metal-ringing'), 1.35), 0.0, 0.2)
corte2 = A.mix((ar2, 0.0, 0.8), (metal2, 0.02, 0.85), (cristal, 0.03, 0.22))
final('corte2', A.seg(corte2, 0, 0.62), -15)

# ── sacar (Dark Repulser das costas): "shiing" longo ──────────────────
final('sacar', L('sword-unsheathe3'), -16, cauda=0.12)

# ── sacar_iai (Elucidator da cintura): saque rapido + ar ─────────────
iai = A.mix((L('sword-unsheathe2'), 0.0, 1.0), (L('swish-3'), 0.03, 0.5))
final('sacar_iai', iai, -15, cauda=0.1)

# ── koiguchi: polegar solta a guarda (clique seco, discreto) ─────────
koi = A.reamostrar(A.seg(L('metalLatch'), 0, 0.16), 0.92)
final('koiguchi', koi, -24, cauda=0.05)

# ── desliza: a lamina entrando na bainha (sem o clique) ──────────────
desl = A.envelope(A.seg(L('drawKnife1'), 0.02, 0.40), [(0, 0.3), (0.12, 1.0), (0.3, 0.8), (0.38, 0.0)])
final('desliza', A.lp(desl, 7000), -24, cauda=0.06, fade_ini=0.04)

# ── embainhar: o "clack" final da guarda batendo na bainha ───────────
clique1 = A.seg(L('metalLatch'), 0, 0.2)
clique2 = A.seg(L('metalClick'), 0.24, 0.40)            # 2o clique do arquivo
emb = A.mix((clique1, 0.0, 1.0), (clique2, 0.004, 0.6), (thump(120, 60, 0.08), 0.0, 0.35))
final('embainhar', emb, -17, cauda=0.06)

# ── carga: tensao subindo ate o golpe final (0,85 s) ─────────────────
sobe = A.seg(L('sword.9'), 0.30, 0.84)
hum = A.seno(90, 180, 0.85, 0.5, queda=-1.2, atk=0.3)
hum = [v * (1 - 0.35 * (0.5 + 0.5 * math.sin(2 * math.pi * 16 * i / A.TAXA))) for i, v in enumerate(hum)]
carga = A.mix((hum, 0.0, 0.5), (A.fade(sobe, 0.15, 0.0), 0.30, 0.9))
carga = A.envelope(carga, [(0, 0.0), (0.2, 0.6), (0.8, 1.0), (0.85, 0.0)])
final('carga', carga, -19, cauda=0.03, fade_ini=0.1)

# ── golpe_final: o corte que atravessa a frase ───────────────────────
peso = A.reamostrar(L('swing'), 0.78)
brilho, t0 = alinhar(L('sword.10'), 0.42, 0.06)
boom = A.seno(75, 38, 0.45, 0.9, queda=4.0, atk=0.003)
gf = A.mix((peso, 0.0, 1.0), (brilho, t0, 0.9), (boom, 0.05, 0.55))
final('golpe_final', A.seg(gf, 0, 1.0), -14, cauda=0.3)

# ── titulo: a frase explode (choque de laminas + boom + ressonancia) ─
c1, t1 = alinhar(L('sword_clash.2'), 0.03, 0.01)
c2, t2 = alinhar(L('sword_clash.4'), 0.05, 0.045)
anel = A.fade(A.reamostrar(L('metal-ringing'), 0.85), 0.0, 0.35)
boom2 = A.seno(62, 34, 0.9, 1.0, queda=3.5, atk=0.002)
ruido = A.fade(A.lp(A.ruido_rosa(int(0.5 * A.TAXA)), 900), 0.0, 0.45)
tit = A.mix((c1, t1, 1.0), (c2, t2, 0.7), (boom2, 0.0, 0.7), (ruido, 0.0, 0.8), (anel, 0.06, 0.25))
final('titulo', A.seg(tit, 0, 1.3), -13, cauda=0.5)

# ── movimento: pulo, pouso, agarrar, susto ───────────────────────────
final('pulo', A.mix((L('cloth-heavy'), 0.0, 1.0), (L('swish-3'), 0.02, 0.35)), -21)
pouso = A.mix((A.seg(L('footstep08'), 0.0), 0.0, 1.0), (L('cloth4'), 0.0, 0.35), (thump(80, 40, 0.12), 0.005, 0.5))
final('pouso', pouso, -18)
agarra = A.mix((L('handleSmallLeather'), 0.0, 1.0), (A.seg(L('cloth2'), 0.05), 0.0, 0.45))
final('agarra', agarra, -22)
final('susto', A.mix((L('cloth4'), 0.0, 1.0), (L('swish-2'), 0.0, 0.4)), -21)

# ── teleporte (cristal de SAO): swell magico + brilho subindo ────────
brilho_t = A.lp(A.fade(A.reamostrar(L('metal-ringing'), 1.2), 0.25, 0.2), 6000)
tele = A.mix((L('magic1'), 0.0, 0.8), (brilho_t, 0.05, 0.35), (A.reamostrar(L('swish-9'), 0.8), 0.0, 0.4))
final('teleporte', A.seg(tele, 0, 0.95), -19, cauda=0.3)

# ── transicao de tela: corte leve ────────────────────────────────────
tr = A.mix((L('swish-3'), 0.0, 1.0), (A.seg(L('sword.3'), 0.18), 0.0, 0.35))
final('transicao', A.seg(tr, 0, 0.45), -20, cauda=0.15)

# ══ golpe final estilo Bleach ═══════════════════════════════════════
# fusao: as laminas se tocam e viram uma (choque + cristal subindo + corpo)
toque, tt = alinhar(L('sword_clash.5'), 0.14, 0.02)
cristal_f = A.fade(A.reamostrar(L('metal-ringing'), 1.25), 0.08, 0.3)
fus = A.mix((toque, tt, 0.9), (cristal_f, 0.05, 0.45), (A.fade(L('magic1'), 0.05, 0.3), 0.0, 0.35),
            (thump(90, 45, 0.18), 0.01, 0.45))
final('fusao', A.seg(fus, 0, 1.2), -15, cauda=0.35)

# reiatsu: o infinito sendo sugado para a espada (2,4 s subindo)
n = int(2.4 * A.TAXA)
vento = A.ruido_rosa(n, seed=3)
k0 = 0.0
filt = []
for i, v in enumerate(vento):                 # passa-baixa que abre (sucao ganhando forca)
    u = i / n
    fc = 250 + 3200 * u * u
    a = 1 - math.exp(-2 * math.pi * fc / A.TAXA)
    k0 += a * (v - k0)
    filt.append(k0 * (0.25 + 0.75 * u))
hum = A.seno(55, 118, 2.4, 0.6, queda=-0.9, atk=0.6)
magia = A.fade(A.seg(L('spell'), 0.3, 2.7), 0.4, 0.3)
sobe2 = A.seg(L('sword.9'), 0.45, 0.84)
rei = A.mix((filt, 0.0, 1.1), (hum, 0.0, 0.45), (magia, 0.0, 0.5), (A.fade(sobe2, 0.2, 0.0), 2.0, 0.6))
rei = A.envelope(rei, [(0, 0.0), (0.35, 0.55), (1.8, 0.85), (2.35, 1.0), (2.4, 0.0)])
final('reiatsu', rei, -18, cauda=0.03, fade_ini=0.2)

# absorve: o infinito some dentro da lamina (baque grave + anel pesado + brilho)
anel_p, ta = alinhar(A.reamostrar(L('sword_clash.2'), 0.75), 0.04, 0.02)
brilho_a = A.fade(A.reamostrar(L('metal-ringing'), 1.4), 0.1, 0.35)
boom3 = A.seno(55, 28, 1.1, 1.0, queda=3.0, atk=0.002)
estouro = A.fade(A.lp(A.ruido_rosa(int(0.6 * A.TAXA), seed=5), 1200), 0.0, 0.5)
absv = A.mix((boom3, 0.0, 0.8), (estouro, 0.0, 0.7), (anel_p, ta, 0.8), (brilho_a, 0.08, 0.35))
final('absorve', A.seg(absv, 0, 1.5), -13, cauda=0.6)

# getsuga: a onda de energia do ultimo golpe
rasgo = A.reamostrar(L('swish-9'), 0.55)
peso2 = A.reamostrar(L('swing'), 0.6)
brilho_g, tg = alinhar(L('sword.10'), 0.42, 0.07)
rasgando = A.fade(A.hp(A.lp(A.ruido_rosa(int(0.9 * A.TAXA), seed=9), 5000), 400), 0.02, 0.6)
boom4 = A.seno(70, 32, 0.8, 1.0, queda=3.5, atk=0.003)
gs = A.mix((rasgo, 0.0, 1.0), (peso2, 0.0, 0.8), (brilho_g, tg, 0.85), (rasgando, 0.03, 0.55),
           (boom4, 0.05, 0.7))
final('getsuga', A.seg(gs, 0, 1.4), -13, cauda=0.5)

# separa: a espada evoluida volta a ser duas (saque cristalino)
sep = A.mix((A.reamostrar(L('sword-unsheathe'), 1.05), 0.0, 1.0),
            (A.fade(A.reamostrar(L('metal-ringing'), 1.5), 0.02, 0.25), 0.03, 0.3))
final('separa', sep, -17, cauda=0.2)

# materializa: o teleporte ao contrario (brilho subindo que termina seco)
tele_inv = list(reversed(A.ler_saida('teleporte')))
final('materializa', A.seg(tele_inv, max(0.0, A.dur(tele_inv) - 0.5)), -20, cauda=0.02, fade_ini=0.08)

# ══ "STARBURST STREAM": voz (sintetizada no Windows e tratada) ═══════
PASTA_VOZ = r'C:\Users\kirit\travetefocus\ferramentas\voz\saida'


def voz(arq):
    a = A.ler_arquivo(os.path.join(PASTA_VOZ, arq))
    a = A.aparar(a, lim=0.01, antes=0.005, depois=0.06)
    a = A.reamostrar(a, 0.84)                     # mais grave (tom e timbre)
    a = A.hp(a, 100)
    a = A.lp(a, 7000)
    dobra = A.reamostrar(a, 1.01)                 # dobra levemente desafinada: voz mais cheia
    a = A.mix((a, 0.0, 1.0), (dobra, 0.012, 0.35))
    # eco curto de "ativacao de habilidade"
    return A.mix((a, 0.0, 1.0), (A.lp(a, 3000), 0.11, 0.26), (A.lp(a, 2200), 0.22, 0.13),
                 (A.lp(a, 1500), 0.34, 0.06))


final('voz_starburst', voz('starburst_m.wav'), -15, cauda=0.3, lp=None, hp=None)
final('voz_stream', voz('stream_m.wav'), -14, cauda=0.3, lp=None, hp=None)

# habilidade: brilho de cristal subindo (o nome do golpe aparece)
sobe_c = list(reversed(A.fade(A.reamostrar(L('metal-ringing'), 1.3), 0.0, 0.3)))
toque_c = A.fade(A.reamostrar(L('metal-ringing'), 1.6), 0.0, 0.35)
hab = A.mix((A.fade(sobe_c, 0.1, 0.0), 0.0, 0.45), (toque_c, A.dur(sobe_c) - 0.02, 0.5),
            (A.reamostrar(L('swish-3'), 1.3), A.dur(sobe_c) - 0.06, 0.3))
final('habilidade', hab, -19, cauda=0.3)
