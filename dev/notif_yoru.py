"""Gera as imagens do Yoru para os cards de aviso (res_yoru/, 256x256, fundo
transparente), o Yoru de verdade (KiritoPixel) em cada pose, com o selo HUD
(brilho + anel) atras:
  yoru_<pose>.png        card aberto: da cabeca ate a cintura COM a espada,
                         o corpo sumindo embaixo como um holograma
  yoru_<pose>_rosto.png  card fechado (pequeno): o rosto de perto, num circulo
  guarda   lembrete de lancar     (em guarda, a espada para baixo)
  meta     meta / faixa ao alcance (mirando com a espada, olhar firme)
  vitoria  fechamento / resumo / faixa nova (as duas espadas erguidas, piscando)
  susto    sequencia em risco     (maos na cabeca, boca aberta)
uso: python dev/notif_yoru.py [pasta_previa]"""
import json
import math
import os
import shutil
import sys
import tempfile
os.environ.setdefault('KIVY_LOG_MODE', 'PYTHON')
os.environ['KIVY_NO_ARGS'] = '1'
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
from kivy.config import Config  # noqa: E402
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '300')
from kivy.app import App  # noqa: E402
from kivy.uix.floatlayout import FloatLayout  # noqa: E402
from kivy.uix.stencilview import StencilView  # noqa: E402
from kivy.clock import Clock  # noqa: E402
import kirito as K  # noqa: E402

PS = 4                       # tamanho do desenho (px por ponto da pose)
L = 112                      # lado do quadro do card aberto (px do desenho)
L_ROSTO = 84                 # e o do rosto (card fechado)
N = 256                      # o tamanho final
POSES = {
    'guarda': ('guarda', {}),
    'meta': ('estoca_arma', {}),
    'vitoria': ('guarda2', {'olhos': 'f'}),
    'susto': ('susto', {'olhos': 'g'}),
}
BW, BH = PS * 90, PS * 110
OLHO_Y = 0.62                # onde fica o olho na caixa do desenho (de baixo)
TMP = tempfile.mkdtemp(prefix='notif_yoru_')


class _A(App):
    def build(self):
        r = FloatLayout()
        self.caixas = {}
        for nome, (base, extra) in POSES.items():
            sv = StencilView(size_hint=(None, None), size=(BW, BH), pos=(0, 0))
            r.add_widget(sv)
            k = K.KiritoPixel(ps=PS)
            sv.add_widget(k)
            pose = dict(K.POSE_A[base])
            pose.update(extra)
            k.mostrar(pose)
            lx, ly = k._local_texel(*K.olhos_texel(k._pose)[0])
            k.pos = (int(BW * 0.5 - lx), int(BH * OLHO_Y - ly))
            self.caixas[nome] = sv
        Clock.schedule_once(self.gravar, 1.0)
        return r

    def gravar(self, dt):
        for nome, sv in self.caixas.items():
            sv.export_to_png(os.path.join(TMP, nome + '.png'))
        self.stop()


def enquadrar(caminho, rosto=False):
    """O quadro do card a partir da pose inteira (rosto=True: so o rosto)."""
    from PIL import Image, ImageDraw
    im = Image.open(caminho).convert('RGBA')
    ex, ey = BW * 0.5, BH * (1 - OLHO_Y)          # o olho (de cima para baixo)
    a = im.getchannel('A')
    nada = Image.new('L', (N, N), 0)
    if rosto:
        # o olho um pouco acima do meio e o rosto (que olha para a direita) no centro
        lado = L_ROSTO
        esq, cima = int(round(ex - lado * 0.60)), int(round(ey - lado * 0.54))
    else:
        lado = L
        bb = a.getbbox()
        # o topo: o que estiver mais alto (a espada erguida) ou o cabelo, com folga
        topo = min(ey - 0.30 * lado, bb[1] - 3)
        topo = max(topo, ey - 0.88 * lado)
        # na horizontal: o meio do que aparece nessa faixa, com o rosto dentro
        fb = a.crop((0, int(topo), im.width, int(topo + lado))).getbbox()
        cx = min(max((fb[0] + fb[2]) / 2.0, ex - 0.30 * lado), ex + 0.10 * lado)
        esq, cima = int(round(cx - lado / 2)), int(round(topo))
    q = im.crop((esq, cima, esq + lado, cima + lado)).resize((N, N), Image.NEAREST)
    if rosto:
        # dentro de um circulo, com a borda suave
        grad = Image.new('L', (N, N), 0)
        gp = grad.load()
        for y in range(N):
            for x in range(N):
                d = math.hypot(x - N / 2.0, y - N / 2.0) / (N * 0.47)
                gp[x, y] = int(255 * max(0.0, min(1.0, (1.0 - d) / 0.06)))
    else:
        # embaixo o corpo some (holograma)
        grad = Image.new('L', (1, N))
        for y in range(N):
            t = max(0.0, min(1.0, (y / (N - 1) - 0.72) / 0.28))
            grad.putpixel((0, y), int(255 * (1 - t) ** 1.4))
        grad = grad.resize((N, N))
    q.putalpha(Image.composite(q.getchannel('A'), nada, grad))
    # o selo atras: brilho redondo, anel e os 4 tracinhos do HUD
    selo = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    c, R = N / 2.0, N * 0.46
    px = selo.load()
    for y in range(N):
        for x in range(N):
            d = math.hypot(x - c, y - c) / R
            if d < 1:
                px[x, y] = (0, 229, 255, int(70 * (1 - d) ** 1.6))
    dr = ImageDraw.Draw(selo)
    dr.ellipse((c - R, c - R, c + R, c + R), outline=(0, 229, 255, 110), width=3)
    for ang in (0, 90, 180, 270):
        u, v = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        dr.line((c + u * (R - 9), c + v * (R - 9), c + u * (R + 4), c + v * (R + 4)),
                fill=(0, 229, 255, 200), width=4)
    selo.putalpha(Image.composite(selo.getchannel('A'), nada, grad))
    selo.alpha_composite(q)
    return selo


if __name__ == '__main__':
    _A().run()
    destino = os.path.join(RAIZ, 'res_yoru')
    os.makedirs(destino, exist_ok=True)
    for nome in POSES:
        for rosto, fim in ((False, ''), (True, '_rosto')):
            img = enquadrar(os.path.join(TMP, nome + '.png'), rosto)
            img.save(os.path.join(destino, f'yoru_{nome}{fim}.png'), optimize=True)
            if len(sys.argv) > 1:
                img.save(os.path.join(sys.argv[1], f'yoru_{nome}{fim}.png'))
        print('ok', nome)
    shutil.rmtree(TMP, ignore_errors=True)
