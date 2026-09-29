"""Reacoes do Yoru mais expressivas: emotes (!!, ?, nota, gota) ~60% maiores
e legiveis no celular, entrando num pop com estica-e-encolhe; pulinhos com
preparacao (encolhe), impulso (estica) e pouso (amortece); "Yatta!"
gravado quando ele comemora a vitoria."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'cenas.py'), [
    ("""        u = max(2.0, round(te * 2.2))         # grande o bastante para ler no celular
        h = len(self.mapa)
        w = len(self.mapa[0])
        if self.tipo == 'gota':               # do lado da testa, na frente do rosto
            return olho[0] + frente * te * 12 - w * u / 2.0, olho[1] + te * 3, u
        if self.tipo == 'brilho':             # em cima do olho
            u = max(1.0, round(te * 1.2))
            return olho[0] - w * u / 2.0, olho[1] - h * u / 2.0 + te, u
        if self.tipo == 'rubor':              # na bochecha, embaixo do olho
            u = max(1.0, round(te))
            return olho[0] - frente * te * 2 - w * u / 2.0, olho[1] - te * 7, u
        # !!, ?, nota: acima da cabeca, um pouco para tras
        return olho[0] - frente * te * 10 - w * u / 2.0, olho[1] + te * 30, u""",
     """        u = max(3.0, round(te * 3.4))         # grande o bastante para ler no celular
        h = len(self.mapa)
        w = len(self.mapa[0])
        if self.tipo == 'gota':               # do lado da testa, na frente do rosto
            return olho[0] + frente * te * 13 - w * u / 2.0, olho[1] + te * 2, u
        if self.tipo == 'brilho':             # em cima do olho
            u = max(1.0, round(te * 1.6))
            return olho[0] - w * u / 2.0, olho[1] - h * u / 2.0 + te, u
        if self.tipo == 'rubor':              # na bochecha, embaixo do olho
            u = max(1.0, round(te * 1.3))
            return olho[0] - frente * te * 2 - w * u / 2.0, olho[1] - te * 8, u
        # !!, ?, nota: acima da cabeca, um pouco para tras
        return olho[0] - frente * te * 11 - w * u / 2.0, olho[1] + te * 31, u"""),
    ("""            x, y, u = self._pontos()
            s = 1.0
            if t < 0.1:
                s = 0.4 + 0.8 * t / 0.1                  # entra num pulinho
            elif t < 0.16:
                s = 1.2 - 0.2 * (t - 0.1) / 0.06""", """            x, y, u = self._pontos()
            s = 1.0
            if t < 0.07:
                s = 0.3 + 1.0 * t / 0.07                 # pop: estoura maior...
            elif t < 0.13:
                s = 1.3 - 0.42 * (t - 0.07) / 0.06       # ... encolhe passando do ponto ...
            elif t < 0.19:
                s = 0.88 + 0.12 * (t - 0.13) / 0.06      # ... e assenta"""),
    ("""    def __init__(self, k, tipo, dur=0.9, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k, self.tipo, self.dur = k, tipo, dur
        self.mapa = _EMOTE_MAPAS[tipo]
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, _EMOTE_CORES)
        self._ev = Clock.schedule_interval(self._tick, 1 / 30.)""", """    def __init__(self, k, tipo, dur=0.9, **kwargs):
        kwargs.setdefault('size_hint', (None, None))
        kwargs.setdefault('size', (0, 0))
        super().__init__(**kwargs)
        self.k, self.tipo, self.dur = k, tipo, dur
        self.mapa = _EMOTE_MAPAS[tipo]
        self.t = 0.0
        self._lote = K.LotePixels(self.canvas, _EMOTE_CORES)
        self._ev = Clock.schedule_interval(self._tick, 1 / 60.)"""),
    # pulinhos com preparacao, impulso e pouso
    ("""    def _um():
        if cont[0] >= n or k.parent is None:
            k.mostrar(pose)
            fim()
            return
        cont[0] += 1
        k.mostrar(no_ar)
        k.empurrar(lift=4, cabelo=3)
        _mover(k, base, base, dur, altura=altura, fantasmas=0,
               on_fim=lambda: (k.mostrar(pose), Clock.schedule_once(lambda dt: _um(), 0.05)))
    _um()""", """    def _pousa():
        k.mostrar(_com(pose, estica=-1))           # amortece o pouso
        Clock.schedule_once(lambda dt: (k.mostrar(pose), Clock.schedule_once(lambda dt2: _um(), 0.04)), 0.07)

    def _sobe():
        k.mostrar(K.esticado(pose))                  # impulso: o corpo todo estica
        k.empurrar(lift=4, cabelo=3)
        Clock.schedule_once(lambda dt: k.mostrar(no_ar), 0.05)
        _mover(k, base, base, dur, altura=altura, fantasmas=0, on_fim=_pousa)

    def _um():
        if cont[0] >= n or k.parent is None:
            k.mostrar(pose)
            fim()
            return
        cont[0] += 1
        k.mostrar(_com(pose, estica=-1))             # prepara: encolhe
        Clock.schedule_once(lambda dt: _sobe(), 0.07)
    _um()"""),
    # vitoria: "Yatta!"
    ("""            feliz = _com(P['vitoria'], olhos='e')
            emote(s.cam, k, '!!', 0.45)""", """            feliz = _com(P['vitoria'], olhos='e')
            _som('fala_yatta')
            emote(s.cam, k, '!!', 0.45)"""),
])
print('ok')
