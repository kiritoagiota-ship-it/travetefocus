"""
infinito.py — TraveteFocus
InfinitoLoader: cometa de luz percorrendo um simbolo de infinito (lemniscata),
com trilho fantasma, cauda que afina, bloom, faiscas e halo radial.

Substitui o ReatorArcShader na tela de loading mantendo a mesma interface:
  - build_progress (0..1): "energia" do loader (Animation(build_progress=...))
  - core_color [r,g,b]: ciano padrao = cor ciclando (ciano/roxo/verde-agua);
    qualquer outra cor (erro vermelho, hack roxo, sucesso verde) = cor fixa.

Sem shader GLSL (so instrucoes de canvas) e sem PIL/numpy: roda igual no
Android (GLES2) e no PC. Nenhuma excecao escapa do loop do Clock.
"""
import math
import random

from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle, Mesh, InstructionGroup
from kivy.graphics.texture import Texture
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.core.text import Label as CoreLabel
from kivy.metrics import dp, sp
from kivy.clock import Clock

_CIANO_PADRAO = (0.0, 0.89, 1.0)

# Ciclo de cores da referencia (violeta -> ciano -> verde-agua -> ciano)
_CICLO = [
    (0.55, 0.30, 1.00),
    (0.00, 0.85, 1.00),
    (0.10, 1.00, 0.80),
    (0.00, 0.85, 1.00),
]
_CICLO_SEG = 5.2          # duas voltas do cometa por ciclo completo de cor
_VOLTA_SEG = 2.6          # uma volta no infinito com energia maxima

_N_CURVA   = 240          # pontos do infinito
_N_CAUDA   = 44           # amostras da cauda (mesh continua)
_N_FAISCAS = 26

_TEX_RADIAL = None


def _gerar_bytes_radial(n=64):
    buf = bytearray(n * n * 4)
    c = (n - 1) / 2.0
    i = 0
    for y in range(n):
        for x in range(n):
            r = math.hypot(x - c, y - c) / c
            a = max(0.0, 1.0 - r)
            a = a * a * (3 - 2 * a)          # smoothstep: borda bem suave
            buf[i] = buf[i + 1] = buf[i + 2] = 255
            buf[i + 3] = int(255 * a)
            i += 4
    return bytes(buf)


def textura_radial():
    """Textura branca com alpha radial (tingida por Color). Gerada uma vez."""
    global _TEX_RADIAL
    if _TEX_RADIAL is None:
        dados = _gerar_bytes_radial()
        tex = Texture.create(size=(64, 64), colorfmt='rgba')
        tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
        # No Android o contexto GL e recriado ao voltar do segundo plano
        tex.add_reload_observer(
            lambda t: t.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte'))
        _TEX_RADIAL = tex
    return _TEX_RADIAL


_TEX_CAUDA = {}


def textura_cauda(expo):
    """Gradiente para a mesh da cauda: u = ao longo (1 na cabeca -> 0 no fim,
    com curva `expo`), v = atravessado (bordas suaves). Branco, tingido por Color."""
    tex = _TEX_CAUDA.get(expo)
    if tex is None:
        nu, nv = 64, 16
        buf = bytearray(nu * nv * 4)
        i = 0
        for y in range(nv):
            v = y / (nv - 1.0)
            borda = max(0.0, 1.0 - abs(2 * v - 1) ** 2)
            for x in range(nu):
                u = x / (nu - 1.0)
                a = (1.0 - u) ** expo * borda
                buf[i] = buf[i + 1] = buf[i + 2] = 255
                buf[i + 3] = int(255 * a)
                i += 4
        dados = bytes(buf)
        tex = Texture.create(size=(nu, nv), colorfmt='rgba')
        tex.wrap = 'clamp_to_edge'
        tex.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte')
        tex.add_reload_observer(
            lambda t: t.blit_buffer(dados, colorfmt='rgba', bufferfmt='ubyte'))
        _TEX_CAUDA[expo] = tex
    return tex


def _curva_unitaria(n):
    """Lemniscata de Bernoulli com a=1 (largura 2, altura ~0.707)."""
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n
        s = math.sin(t)
        d = 1 + s * s
        pts.append((math.cos(t) / d, s * math.cos(t) / d))
    return pts


_CURVA = _curva_unitaria(_N_CURVA)


def _lerp(a, b, t):
    return a + (b - a) * t


def _lerp3(c1, c2, t):
    return (_lerp(c1[0], c2[0], t), _lerp(c1[1], c2[1], t), _lerp(c1[2], c2[2], t))


class InfinitoLoader(Widget):
    build_progress = NumericProperty(0.0)
    core_color     = ListProperty(list(_CIANO_PADRAO))
    texto          = StringProperty("")
    velocidade     = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ev       = None
        self._t        = 0.0          # tempo total
        self._fase     = 0.0          # posicao da cabeca na curva (0..1)
        self._energia  = 0.0          # build_progress suavizado
        self._cor      = list(_CIANO_PADRAO)
        self._faiscas  = []           # [x, y, vx, vy, vida, vida_max, tam]
        self._acum_faisca = 0.0
        self._pontos   = []           # curva escalada (coords de tela)
        self._escala   = 1.0
        self._txt_ult  = None
        self._txt_acum = 0.0
        self._txt_dots = 0
        self._sug      = None         # sendo sugado (golpe final do Kirito)
        self._sug_u    = 0.0
        self.pontos_atuais = []       # curva como esta sendo desenhada agora
        self._montar_canvas()
        self.bind(pos=self._recalcular, x=self._recalcular, y=self._recalcular,
                  size=self._recalcular)

    # ── construcao (uma vez) ────────────────────────────────────────────
    def _montar_canvas(self):
        with self.canvas:
            self._c_halo = Color(0, 0.9, 1, 0.0)
            self._halo   = Rectangle()
            self._c_trilho_b = Color(0, 0.9, 1, 0.0)
            self._trilho_b   = Line(width=dp(5), close=True)
            self._c_trilho   = Color(0.6, 0.7, 0.9, 0.0)
            self._trilho     = Line(width=dp(1.6), close=True)

            idx = list(range(2 * _N_CAUDA))
            # camada larga e fraca (bloom), cauda colorida e nucleo branco curto
            self._c_bloom = Color(0, 0.9, 1, 0)
            self._m_bloom = Mesh(mode='triangle_strip', indices=idx, vertices=[0] * (8 * _N_CAUDA))
            self._c_cauda = Color(0, 0.9, 1, 0)
            self._m_cauda = Mesh(mode='triangle_strip', indices=idx, vertices=[0] * (8 * _N_CAUDA))
            self._c_miolo = Color(1, 1, 1, 0)
            self._m_miolo = Mesh(mode='triangle_strip', indices=idx, vertices=[0] * (8 * _N_CAUDA))

            self._faisca_grp = InstructionGroup()
            self._faisca_ins = []
            for _ in range(_N_FAISCAS):
                c = Color(1, 1, 1, 0)
                e = Ellipse(size=(0, 0))
                self._faisca_grp.add(c)
                self._faisca_grp.add(e)
                self._faisca_ins.append((c, e))
            self._faisca_ins_livres = list(range(_N_FAISCAS))
        self.canvas.add(self._faisca_grp)
        with self.canvas:
            self._c_glow  = Color(0, 0.9, 1, 0)
            self._glow    = Rectangle()
            self._c_nucleo = Color(1, 1, 1, 0)
            self._nucleo   = Ellipse()
            self._c_txt = Color(0.75, 0.85, 1, 0)
            self._txt   = Rectangle()

    def on_parent(self, inst, parent):
        try:
            if parent is not None:
                try:
                    tex = textura_radial()
                    self._halo.texture = tex
                    self._glow.texture = tex
                    self._m_bloom.texture = textura_cauda(1.3)
                    self._m_cauda.texture = textura_cauda(1.5)
                    self._m_miolo.texture = textura_cauda(4.0)
                except Exception as e:
                    print(f"[infinito] textura radial indisponivel: {e}")
                if self._ev is None:
                    self._ev = Clock.schedule_interval(self._tick, 1 / 60.)
            elif self._ev is not None:
                self._ev.cancel()
                self._ev = None
        except Exception as e:
            print(f"[infinito] on_parent: {e}")

    def _recalcular(self, *_):
        try:
            w, h = self.width, self.height
            if w <= 1 or h <= 1:
                self._pontos = []
                return
            reserva_txt = dp(26) if self.texto else 0
            h_util = max(1.0, h - reserva_txt)
            # largura da curva = 2a ; altura = 0.707a
            a = max(1.0, min(w * 0.42, h_util * 0.60 / 0.707))
            self._escala = a
            cx = self.x + w / 2.0      # (center_x tem cache: pode estar velho)
            cy = self.y + reserva_txt + h_util / 2.0
            self._cx, self._cy = cx, cy
            self._pontos = [(cx + px * a, cy + py * a) for px, py in _CURVA]
            flat = [v for p in self._pontos for v in p]
            self._trilho.points   = flat
            self._trilho_b.points = flat
            self._trilho.width    = max(1.0, a * 0.012)
            self._trilho_b.width  = max(1.5, a * 0.05)
            r = a * 1.45
            self._halo.pos  = (cx - r, cy - r)
            self._halo.size = (2 * r, 2 * r)
            self._txt_ult = None
        except Exception as e:
            print(f"[infinito] recalcular: {e}")

    # ── cor ─────────────────────────────────────────────────────────────
    def _cor_alvo(self):
        cc = list(self.core_color[:3]) if len(self.core_color) >= 3 else list(_CIANO_PADRAO)
        dist = sum(abs(a - b) for a, b in zip(cc, _CIANO_PADRAO))
        if dist < 0.2:
            f = (self._t % _CICLO_SEG) / _CICLO_SEG * len(_CICLO)
            i = int(f) % len(_CICLO)
            k = f - int(f)
            k = 0.5 - 0.5 * math.cos(math.pi * k)          # easing suave
            return _lerp3(_CICLO[i], _CICLO[(i + 1) % len(_CICLO)], k), False
        return tuple(cc), True

    # ── loop ────────────────────────────────────────────────────────────
    def _tick(self, dt):
        try:
            self._frame(min(dt, 1 / 20.))
        except Exception as e:
            print(f"[infinito] frame ignorado: {e}")

    def _frame(self, dt):
        self._t += dt
        if not self._pontos:
            self._recalcular()
            if not self._pontos:
                return

        alvo_e = max(0.0, min(1.0, float(self.build_progress)))
        self._energia += (alvo_e - self._energia) * (1 - math.exp(-dt * 6))
        e = self._energia

        alvo_cor, fixa = self._cor_alvo()
        k = 1 - math.exp(-dt * (10 if fixa else 30))
        self._cor = [_lerp(self._cor[i], alvo_cor[i], k) for i in range(3)]
        r, g, b = self._cor
        erro = fixa and r > 0.8 and g < 0.3          # vermelho: glitch

        # velocidade: devagar com pouca energia, periodo de 2,6s em energia 1
        vel = (0.35 + 0.65 * e) * self.velocidade / _VOLTA_SEG
        self._fase = (self._fase + dt * vel) % 1.0

        pts = self._pontos
        n = len(pts)
        a = self._escala
        respiro = 0.5 + 0.5 * math.sin(self._t * 2.4)
        some = 1.0                                     # 0 = ja foi todo sugado
        if self._sug is not None:
            pts, some, e = self._deformar(dt, e)
            vel_extra = 1 + 5.0 * self._sug_u
            self._fase = (self._fase + dt * vel * (vel_extra - 1)) % 1.0
        self.pontos_atuais = pts

        # halo radial atras de tudo
        self._c_halo.rgba = (r, g, b, (0.10 + 0.14 * min(1.0, e)) * (0.75 + 0.25 * respiro) * some)
        # trilho fantasma
        self._c_trilho.rgba   = (0.55 + 0.3 * r, 0.6 + 0.3 * g, 0.75 + 0.25 * b, (0.05 + 0.06 * e) * some)
        self._c_trilho_b.rgba = (r, g, b, (0.012 + 0.022 * e) * some)

        # cauda: fracao da curva atras da cabeca
        comp = (0.10 + 0.32 * e)
        cabeca_f = self._fase * n
        total_seg = _N_CAUDA - 1
        passo = comp * n / total_seg

        def ponto(fidx):
            fidx %= n
            i0 = int(fidx)
            t = fidx - i0
            p0 = pts[i0]
            p1 = pts[(i0 + 1) % n]
            return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)

        jit = (random.uniform(-1, 1) * a * 0.03) if erro and random.random() < 0.35 else 0.0
        amostras = [ponto(cabeca_f - j * passo) for j in range(total_seg + 1)]
        if jit:
            amostras = [(x + jit, y) for x, y in amostras]

        larg_max = max(1.5, a * (0.034 + 0.030 * e))
        self._strip(self._m_cauda, amostras, larg_max * 2.0, 1.1)
        self._strip(self._m_bloom, amostras, larg_max * 6.5, 0.8)
        self._strip(self._m_miolo, amostras, larg_max * 0.9, 1.4)
        self._c_cauda.rgba = (r, g, b, min(1.0, 0.45 + 0.55 * e) * some)
        self._c_bloom.rgba = (r, g, b, min(1.0, 0.18 + 0.14 * e) * some)
        self._c_miolo.rgba = (_lerp(r, 1, 0.8), _lerp(g, 1, 0.8), _lerp(b, 1, 0.8), min(1.0, 0.5 + 0.5 * e) * some)

        hx, hy = amostras[0]
        tam_glow = a * (0.30 + 0.35 * e) * (0.9 + 0.1 * respiro)
        self._glow.pos  = (hx - tam_glow / 2, hy - tam_glow / 2)
        self._glow.size = (tam_glow, tam_glow)
        self._c_glow.rgba = (_lerp(r, 1, 0.25), _lerp(g, 1, 0.25), _lerp(b, 1, 0.25), min(1.0, 0.55 + 0.35 * e) * some)
        tam_n = max(3.0, larg_max * 1.35)
        self._nucleo.pos  = (hx - tam_n / 2, hy - tam_n / 2)
        self._nucleo.size = (tam_n, tam_n)
        self._c_nucleo.rgba = (1, 1, 1, min(1.0, 0.55 + 0.45 * e) * some)

        self._atualizar_faiscas(dt, hx, hy, amostras, min(1.0, e), (r, g, b), a)
        self._atualizar_texto(dt, (r, g, b), min(1.0, e))
        if self._sug_u > 0:
            self._c_txt.a *= max(0.0, 1 - 2 * self._sug_u)

    # ── sugado pela espada ──────────────────────────────────────────────
    def sugar(self, alvo, dur=2.4, on_fim=None):
        """O infinito e sugado ate alvo() (ponta da espada): a curva gira em
        espiral e encolhe ate o ponto, o cometa acelera e brilha mais, e no
        fim nao sobra nada. alvo(): (x, y) nas mesmas coords deste widget."""
        self._sug = {'t': 0.0, 'dur': max(0.1, dur), 'alvo': alvo, 'fim': on_fim}
        self._sug_u = 0.0

    def restaurar(self):
        """Volta ao normal (se a cena for interrompida no meio)."""
        self._sug = None
        self._sug_u = 0.0
        try:
            flat = [v for p in self._pontos for v in p]
            self._trilho.points = flat
            self._trilho_b.points = flat
        except Exception:
            pass

    def _deformar(self, dt, e):
        s = self._sug
        s['t'] += dt
        u = min(1.0, s['t'] / s['dur'])
        self._sug_u = u
        try:
            ax, ay = s['alvo']()
        except Exception:
            ax, ay = self._cx, self._cy
        base = self._pontos
        # pontos mais longe do alvo sao puxados depois (a curva "escorre")
        dists = [math.hypot(x - ax, y - ay) for x, y in base]
        dmax = max(dists) or 1.0
        pts = []
        for (x, y), d in zip(base, dists):
            f = (u * 1.45 - 0.45 * d / dmax)
            f = max(0.0, min(1.0, f))
            f = f * f * (3 - 2 * f)
            ang = f * 2.6                              # espiral em volta da ponta
            vx, vy = x - ax, y - ay
            c, sn = math.cos(ang), math.sin(ang)
            k = 1.0 - f
            pts.append((ax + (vx * c - vy * sn) * k, ay + (vx * sn + vy * c) * k))
        flat = [v for p in pts for v in p]
        self._trilho.points = flat
        self._trilho_b.points = flat
        # halo encolhe e vai para o alvo
        r = self._escala * 1.45 * (1 - u) + 1
        hx = self._cx + (ax - self._cx) * u
        hy = self._cy + (ay - self._cy) * u
        self._halo.pos, self._halo.size = (hx - r, hy - r), (2 * r, 2 * r)
        self._c_txt.a = self._c_txt.a * (1 - u)
        some = 1.0 - max(0.0, (u - 0.82) / 0.18)
        if u >= 1:
            fim, s['fim'] = s['fim'], None
            self._sug = None
            self.opacity = 0
            if fim:
                try:
                    fim()
                except Exception as ex:
                    print(f"[infinito] fim do sugar: {ex}")
        return pts, some, e + 0.9 * u

    @staticmethod
    def _strip(mesh, amostras, largura, expo_larg):
        """Triangle strip afinando da cabeca (u=0) ao fim (u=1)."""
        n = len(amostras)
        vs = []
        for i in range(n):
            x, y = amostras[i]
            xa, ya = amostras[max(0, i - 1)]
            xb, yb = amostras[min(n - 1, i + 1)]
            tx, ty = xa - xb, ya - yb
            ln = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / ln, tx / ln
            u = i / (n - 1.0)
            meia = max(0.5, largura * 0.5 * (1 - u) ** expo_larg)
            vs.extend((x + nx * meia, y + ny * meia, u, 0.0,
                       x - nx * meia, y - ny * meia, u, 1.0))
        mesh.vertices = vs

    def _atualizar_faiscas(self, dt, hx, hy, amostras, e, cor, a):
        # emissao proporcional a energia
        self._acum_faisca += dt * (8 + 34 * e)
        dx = amostras[0][0] - amostras[2][0]
        dy = amostras[0][1] - amostras[2][1]
        while self._acum_faisca >= 1 and self._faisca_ins_livres:
            self._acum_faisca -= 1
            idx = self._faisca_ins_livres.pop()
            ang = random.uniform(0, 2 * math.pi)
            v = a * random.uniform(0.05, 0.22)
            vida = random.uniform(0.35, 0.8)
            self._faiscas.append([
                hx, hy,
                math.cos(ang) * v - dx * 2.0, math.sin(ang) * v - dy * 2.0,
                vida, vida, random.uniform(dp(1.2), dp(2.6)), idx])
        self._acum_faisca = min(self._acum_faisca, 3)

        vivas = []
        for f in self._faiscas:
            f[4] -= dt
            c, el = self._faisca_ins[f[7]]
            if f[4] <= 0:
                c.a = 0
                el.size = (0, 0)
                self._faisca_ins_livres.append(f[7])
                continue
            f[0] += f[2] * dt
            f[1] += f[3] * dt
            f[2] *= 0.94
            f[3] *= 0.94
            k = f[4] / f[5]
            t = f[6] * (0.4 + 0.6 * k)
            el.pos = (f[0] - t / 2, f[1] - t / 2)
            el.size = (t, t)
            c.rgba = (_lerp(cor[0], 1, k * 0.7), _lerp(cor[1], 1, k * 0.7), _lerp(cor[2], 1, k * 0.7), k * (0.5 + 0.5 * e))
            vivas.append(f)
        self._faiscas = vivas

    def _atualizar_texto(self, dt, cor, e):
        if not self.texto:
            self._c_txt.a = 0
            return
        self._txt_acum += dt
        if self._txt_acum >= 0.4:
            self._txt_acum = 0
            self._txt_dots = (self._txt_dots + 1) % 4
        conteudo = self.texto + "." * self._txt_dots
        if conteudo != self._txt_ult:
            self._txt_ult = conteudo
            try:
                lbl = CoreLabel(text=self.texto + "...", font_name="orbitron.ttf",
                                font_size=sp(10))
                lbl.refresh()
                largura_fixa = lbl.texture.size[0]
                lbl = CoreLabel(text=conteudo, font_name="orbitron.ttf", font_size=sp(10))
                lbl.refresh()
                tex = lbl.texture
                self._txt.texture = tex
                self._txt.size = tex.size
                self._txt.pos = (self.x + self.width / 2.0 - largura_fixa / 2.0, self.y + dp(4))
            except Exception as ex:
                print(f"[infinito] texto: {ex}")
                self.texto = ""
                return
        self._c_txt.rgba = (_lerp(cor[0], 1, 0.6), _lerp(cor[1], 1, 0.6), _lerp(cor[2], 1, 0.6),
                            0.35 + 0.3 * e)

    def on_texto(self, *_):
        if hasattr(self, '_trilho'):      # kwargs chegam antes do canvas existir
            self._recalcular()


def cor_do_ciclo(cor, t):
    """Mesma regra do infinito: ciano padrao cicla; outra cor fica fixa."""
    cc = list(cor[:3])
    if sum(abs(a - b) for a, b in zip(cc, _CIANO_PADRAO)) < 0.2 or \
            sum(abs(a - b) for a, b in zip(cc, (0.0, 0.5, 1.0))) < 0.2:
        f = (t % _CICLO_SEG) / _CICLO_SEG * len(_CICLO)
        i = int(f) % len(_CICLO)
        k = f - int(f)
        k = 0.5 - 0.5 * math.cos(math.pi * k)
        return _lerp3(_CICLO[i], _CICLO[(i + 1) % len(_CICLO)], k)
    return tuple(cc)


# ═══════════════════════════════════════════════════════════════════
#  BARRA COM COMETA (substitui a barra segmentada da loading)
# ═══════════════════════════════════════════════════════════════════
class BarraCometa(Widget):
    """Fio de luz: trilho apagado + trecho preenchido com brilho + cometa na
    ponta + porcentagem. Mesma interface da BarraNeon (progresso 0..100,
    cor_linha); em ciano a cor cicla junto com o infinito."""
    progresso = NumericProperty(0)
    cor_linha = ListProperty([0, 0.9, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._t = 0.0
        self._cor = [0.0, 0.9, 1.0]
        self._pct_ult = None
        self._ev = None
        with self.canvas:
            self._c_trilho = Color(0.6, 0.8, 1, 0.12)
            self._trilho = Line(points=[0, 0, 0, 0], width=dp(1))
            self._c_glow = Color(0, 0.9, 1, 0.22)
            self._glow = Line(points=[0, 0, 0, 0], width=dp(4), cap='round')
            self._c_fio = Color(0, 0.9, 1, 0.95)
            self._fio = Line(points=[0, 0, 0, 0], width=dp(1.3), cap='round')
            self._c_cabeca = Color(0, 0.9, 1, 0.9)
            self._cabeca = Rectangle(size=(0, 0))
            self._c_nucleo = Color(1, 1, 1, 0.95)
            self._nucleo = Ellipse(size=(0, 0))
            self._c_pct = Color(0.8, 0.95, 1, 0.75)
            self._pct = Rectangle(size=(0, 0))

    def on_parent(self, inst, parent):
        try:
            if parent is not None:
                try:
                    self._cabeca.texture = textura_radial()
                except Exception as e:
                    print(f"[barra] textura: {e}")
                if self._ev is None:
                    self._ev = Clock.schedule_interval(self._tick, 1 / 60.)
            elif self._ev is not None:
                self._ev.cancel()
                self._ev = None
        except Exception as e:
            print(f"[barra] on_parent: {e}")

    def _tick(self, dt):
        try:
            self._t += dt
            alvo = cor_do_ciclo(self.cor_linha, self._t)
            k = 1 - math.exp(-dt * 10)
            self._cor = [_lerp(self._cor[i], alvo[i], k) for i in range(3)]
            r, g, b = self._cor
            pct = max(0.0, min(100.0, float(self.progresso)))
            larg_pct = dp(40)
            x0, y = self.x, self.y + self.height / 2.0
            x1 = self.right - larg_pct
            if x1 - x0 < 4:
                return
            xp = x0 + (x1 - x0) * pct / 100.0
            self._trilho.points = [x0, y, x1, y]
            self._fio.points = [x0, y, max(x0 + 0.5, xp), y]
            self._glow.points = self._fio.points
            self._c_fio.rgba = (r, g, b, 0.95)
            self._c_glow.rgba = (r, g, b, 0.22 + 0.06 * math.sin(self._t * 6))
            self._c_trilho.rgba = (0.6 + 0.4 * r, 0.6 + 0.4 * g, 0.6 + 0.4 * b, 0.12)
            vivo = pct > 0.5
            tam = dp(22) * (1.0 + 0.12 * math.sin(self._t * 9))
            self._cabeca.pos = (xp - tam / 2.0, y - tam / 2.0)
            self._cabeca.size = (tam, tam) if vivo else (0, 0)
            self._c_cabeca.rgba = (r, g, b, 0.85)
            n = dp(4)
            self._nucleo.pos = (xp - n / 2.0, y - n / 2.0)
            self._nucleo.size = (n, n) if vivo else (0, 0)
            p = int(round(pct))
            if p != self._pct_ult:
                self._pct_ult = p
                lbl = CoreLabel(text=f"{p}%", font_name="orbitron.ttf", font_size=sp(9))
                lbl.refresh()
                self._pct.texture = lbl.texture
                self._pct.size = lbl.texture.size
            tw, th = self._pct.size
            self._pct.pos = (self.right - tw, y - th / 2.0)
            self._c_pct.rgba = (0.6 + 0.4 * r, 0.6 + 0.4 * g, 0.6 + 0.4 * b, 0.8)
        except Exception as e:
            print(f"[barra] frame ignorado: {e}")


# ═══════════════════════════════════════════════════════════════════
#  PAINEL HOLOGRAFICO (terminal da loading sem a caixa pesada)
# ═══════════════════════════════════════════════════════════════════
from kivy.uix.boxlayout import BoxLayout  # noqa: E402


class PainelHolografico(BoxLayout):
    """Colchetes de canto finos, acento lateral e uma scanline sutil que
    desce devagar; a cor acompanha o ciclo do infinito."""
    cor = ListProperty([0, 0.9, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._t = 0.0
        self._ev = None
        with self.canvas.before:
            self._c_fundo = Color(0.02, 0.06, 0.12, 0.18)
            self._fundo = Rectangle()
            self._c_linhas = Color(0, 0.9, 1, 0.55)
            self._cantos = [Line(points=[0, 0, 0, 0], width=dp(1.1)) for _ in range(4)]
            self._c_acento = Color(0, 0.9, 1, 0.35)
            self._acento = Line(points=[0, 0, 0, 0], width=dp(1.4))
            self._c_scan = Color(0, 0.9, 1, 0.08)
            self._scan = Rectangle(size=(0, 0))

    def on_parent(self, inst, parent):
        if parent is not None:
            if self._ev is None:
                self._ev = Clock.schedule_interval(self._tick, 1 / 30.)
        elif self._ev is not None:
            self._ev.cancel()
            self._ev = None

    def _tick(self, dt):
        try:
            self._t += dt
            r, g, b = cor_do_ciclo(self.cor, self._t)
            x, y, w, h = self.x, self.y, self.width, self.height
            self._fundo.pos, self._fundo.size = (x, y), (w, h)
            c = min(dp(16), w * 0.2, h * 0.3)
            self._cantos[0].points = [x, y + h - c, x, y + h, x + c, y + h]
            self._cantos[1].points = [x + w - c, y + h, x + w, y + h, x + w, y + h - c]
            self._cantos[2].points = [x, y + c, x, y, x + c, y]
            self._cantos[3].points = [x + w - c, y, x + w, y, x + w, y + c]
            self._acento.points = [x + dp(5), y + h * 0.2, x + dp(5), y + h * 0.8]
            self._c_linhas.rgba = (r, g, b, 0.55)
            self._c_acento.rgba = (r, g, b, 0.30 + 0.15 * math.sin(self._t * 2))
            sy = y + h - ((self._t * dp(26)) % (h + dp(20)))
            self._scan.pos, self._scan.size = (x, sy), (w, dp(2))
            self._c_scan.rgba = (r, g, b, 0.10)
        except Exception as e:
            print(f"[painel] frame ignorado: {e}")
