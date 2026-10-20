"""telas/calculadora.py — TelaCalculadora

Calculadora com contas exatas (Decimal: 0,1 + 0,2 = 0,3), formato
brasileiro (1.234.567,89), visor que encolhe o numero para caber numa
linha, conta pequena em cima (enquanto digita mostra o resultado parcial),
historico das ultimas contas (toque reusa o resultado) e protecao na
digitacao (nao deixa '++', dois pontos no mesmo numero etc.).
Teclas: 0-9 . + - * / % () DEL C = (o DEL segurando apaga rapido).
"""
import re
from decimal import Decimal, ROUND_HALF_UP, localcontext

from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.text import Label as CoreLabel

import som
import tatil
from efeitos import tremer_tela

_OPS = '+-*/'
_MAX_DIGITOS = 15             # por numero digitado
_CASAS = Decimal('1e-8')      # resultado arredondado em ate 8 casas


class _ContaInvalida(Exception):
    pass


class _Leitor:
    """Le a conta (0-9 . + - * / % ( )) e calcula com Decimal.
    Porcentagem como nas calculadoras de celular: 200 + 10% = 220,
    200 x 10% = 20, 10% = 0,1."""

    def __init__(self, s):
        self.s, self.i = s, 0

    def ver(self):
        return self.s[self.i] if self.i < len(self.s) else ''

    def calcular(self):
        with localcontext() as ctx:
            ctx.prec = 40
            v = self._soma()
            if self.i != len(self.s):
                raise _ContaInvalida()
            return v

    def _soma(self):
        v, _, _ = self._produto()
        while self.ver() and self.ver() in '+-':
            op = self.ver()
            self.i += 1
            t, so_pct, bruto = self._produto()
            if so_pct:                      # a + b% = a + a*b/100
                t = v * bruto / 100
            v = v + t if op == '+' else v - t
        return v

    def _produto(self):
        v, pct, bruto = self._fator()
        sozinho = True
        while self.ver() and self.ver() in '*/':
            op = self.ver()
            self.i += 1
            f, _, _ = self._fator()
            sozinho = False
            if op == '*':
                v = v * f
            else:
                if f == 0:
                    raise ZeroDivisionError()
                v = v / f
        return v, pct and sozinho, bruto

    def _fator(self):
        c = self.ver()
        if c == '-':
            self.i += 1
            v, p, b = self._fator()
            return -v, p, -b
        if c == '(':
            self.i += 1
            v = self._soma()
            if self.ver() == ')':
                self.i += 1
        else:
            ini = self.i
            while self.ver() and (self.ver().isdigit() or self.ver() == '.'):
                self.i += 1
            txt = self.s[ini:self.i]
            if not txt or txt == '.':
                raise _ContaInvalida()
            v = Decimal(txt)
        if self.ver() == '%':
            self.i += 1
            return v / 100, True, v
        return v, False, v


def _milhar(inteiro):
    """'1234567' -> '1.234.567'"""
    neg = inteiro.startswith('-')
    d = inteiro.lstrip('-')
    grupos = []
    while len(d) > 3:
        grupos.insert(0, d[-3:])
        d = d[:-3]
    grupos.insert(0, d)
    return ('-' if neg else '') + '.'.join(grupos)


def fmt_resultado(v, cientifico=False):
    """Decimal -> texto brasileiro: 1.219.326.311.126.352.690 / 0,3 / 3,33333333.
    Numeros enormes (ou pequenininhos) em notacao cientifica: 1,219326 E20."""
    if v == 0:
        return '0'
    a = abs(v)
    if cientifico or a >= Decimal('1e18') or a < Decimal('1e-8'):
        m, e = '{:.6E}'.format(v).split('E')
        m = m.rstrip('0').rstrip('.').replace('.', ',')
        return f'{m} E{int(e)}'.replace('-', '−')
    q = v.quantize(_CASAS, rounding=ROUND_HALF_UP)
    s = format(q, 'f')
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    inteiro, _, frac = s.partition('.')
    if inteiro in ('-0', '') and not frac:
        return '0'
    return (_milhar(inteiro) + (',' + frac if frac else '')).replace('-', '−')


def _plano(v):
    """Decimal -> conta para continuar calculando ('1234.5', '-3')."""
    q = v.quantize(_CASAS, rounding=ROUND_HALF_UP) if abs(v) < Decimal('1e18') else v
    s = format(q.normalize(), 'f')
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return s or '0'


def fmt_conta(expr):
    """'1234.5*-3+10%' -> '1.234,5 × −3 + 10%' (como aparece no visor)."""
    out = []
    i = 0
    while i < len(expr):
        c = expr[i]
        if c.isdigit() or c == '.':
            j = i
            while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                j += 1
            num = expr[i:j]
            inteiro, ponto, frac = num.partition('.')
            out.append(_milhar(inteiro or '0') + (',' + frac if ponto else ''))
            i = j
            continue
        if c in _OPS:
            anterior = expr[i - 1] if i else ''
            if c == '-' and (not anterior or anterior in _OPS + '('):
                out.append('−')                     # sinal de negativo
            else:
                out.append({'+': ' + ', '-': ' − ', '*': ' × ', '/': ' ÷ '}[c])
        else:
            out.append(c)
        i += 1
    return ''.join(out)


class TelaCalculadora(Screen):
    _historico = []           # [(conta formatada, resultado formatado, valor)] - ultimas contas
    MAX_HIST = 6

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.expr = ''
        self.mostrando_resultado = False
        self._resultado_txt = ''
        self._ev_del = None
        Clock.schedule_once(lambda dt: self._mostrar_historico(), 0)

    # ── teclas ────────────────────────────────────────────────────────
    def apertar(self, tecla):
        """Entrada unica de todas as teclas (vem do KV)."""
        try:
            if tecla.isdigit():
                ok = self._digito(tecla)
            elif tecla == '.':
                ok = self._ponto()
            elif tecla in _OPS:
                ok = self._operador(tecla)
            elif tecla == '%':
                ok = self._porcento()
            elif tecla == '()':
                ok = self._parenteses()
            elif tecla == 'DEL':
                ok = self._apagar()
            elif tecla == 'C':
                self.limpar()
                return
            elif tecla == '=':
                self.calcular()
                return
            else:
                return
            if not ok:
                self._recusar()
            self._atualizar()
        except Exception as e:
            print(f"[calculadora] {tecla}: {e}")

    def _numero_atual(self):
        return re.search(r'[\d.]*$', self.expr).group(0)

    def _novo_se_resultado(self):
        if self.mostrando_resultado:
            self.mostrando_resultado = False
            self.expr = ''

    def _digito(self, d):
        self._novo_se_resultado()
        if self.expr.endswith((')', '%')):
            self.expr += '*'
        num = self._numero_atual()
        if len(num.replace('.', '')) >= _MAX_DIGITOS:
            return False
        if num == '0':                              # sem zero na frente: 05 -> 5
            self.expr = self.expr[:-1]
        self.expr += d
        return True

    def _ponto(self):
        self._novo_se_resultado()
        if self.expr.endswith((')', '%')):
            self.expr += '*'
        num = self._numero_atual()
        if '.' in num:
            return False
        if not num:
            self.expr += '0'
        self.expr += '.'
        return True

    def _operador(self, op):
        self.mostrando_resultado = False            # continua a partir do resultado
        e = self.expr
        if e.endswith('.'):
            e = e[:-1]
        if not e or e.endswith('('):
            if op == '-':
                self.expr = e + '-'
                return True
            self.expr = e
            return False
        if e[-1] in _OPS:
            if op == '-' and e[-1] in '*/':          # 5 × −3
                self.expr = e + '-'
                return True
            e = e.rstrip(_OPS)                       # troca o sinal que estava
            if not e:
                self.expr = '-' if op == '-' else ''
                return op == '-'
        self.expr = e + op
        return True

    def _porcento(self):
        self.mostrando_resultado = False
        if not self.expr or self.expr[-1] not in '0123456789)':
            return False
        self.expr += '%'
        return True

    def _parenteses(self):
        self.mostrando_resultado = False
        e = self.expr
        abertos = e.count('(') - e.count(')')
        ult = e[-1:]
        if abertos > 0 and ult and (ult.isdigit() or ult in ')%'):
            self.expr = e + ')'
            return True
        if ult == '.':
            e = e[:-1]
            ult = e[-1:]
        if ult and (ult.isdigit() or ult in ')%'):
            e += '*'                                 # 2(3+1) = 2 × (3+1)
        self.expr = e + '('
        return True

    def _apagar(self):
        if not self.expr:
            return False
        self.mostrando_resultado = False
        self.expr = self.expr[:-1]
        return True

    # segurar o DEL apaga um atras do outro
    def del_segurar(self):
        self.apertar('DEL')
        self.del_soltar()
        self._ev_del = Clock.schedule_once(self._del_repetir, 0.42)

    def _del_repetir(self, dt):
        self._ev_del = None
        if not self.expr or self.manager is None or self.manager.current != self.name:
            return
        tatil.tecla()
        self.apertar('DEL')
        self._ev_del = Clock.schedule_once(self._del_repetir, 0.06)

    def del_soltar(self):
        if self._ev_del is not None:
            self._ev_del.cancel()
            self._ev_del = None

    def on_enter(self, *_):
        try:
            from animacoes_ui import entrada_tela
            entrada_tela(self.ids.calc_hist_area.parent)
        except Exception as e:
            print(f"[calc] entrada: {e}")

    def on_leave(self, *_):
        self.del_soltar()

    def limpar(self):
        lbl = self.ids.calc_display
        self.expr = ''
        self.mostrando_resultado = False
        Animation.cancel_all(lbl, 'color')
        (Animation(color=(1, 0.1, 0.2, 1), duration=0.06, transition='out_quad') +
         Animation(color=(1, 1, 1, 1), duration=0.25, transition='out_quad')).start(lbl)
        self._atualizar()

    # ── conta ─────────────────────────────────────────────────────────
    @staticmethod
    def _fechada(expr):
        """A conta pronta para calcular: sem sinal sobrando no fim e com os
        parenteses fechados."""
        e = expr
        while e and e[-1] in _OPS + '(.':
            e = e[:-1]
        return e + ')' * max(0, e.count('(') - e.count(')'))

    def _valor(self, expr):
        e = self._fechada(expr)
        if not e:
            raise _ContaInvalida()
        return e, _Leitor(e).calcular()

    def calcular(self):
        lbl = self.ids.calc_display
        if not self.expr or self.mostrando_resultado:
            self._recusar()
            return
        try:
            e, v = self._valor(self.expr)
        except ZeroDivisionError:
            self._erro("NÃO DÁ PARA DIVIDIR POR ZERO")
            return
        except Exception:
            self._erro("CONTA INCOMPLETA")
            return
        if not re.search(r'[+*/%(]|\d-|\)-', e):    # so um numero: nada a calcular
            self._recusar()
            return
        conta = fmt_conta(e)
        txt = fmt_resultado(v)
        self._historico.append((conta, txt, _plano(v)))
        del self._historico[:-self.MAX_HIST]
        self.expr = _plano(v)
        self.mostrando_resultado = True
        self._resultado_txt = txt
        self._atualizar(conta_feita=conta + ' =')
        self._mostrar_historico()
        try:
            som.tocar_calc_resultado()
        except Exception:
            pass
        tatil.confirmar()
        tremer_tela(5)
        Animation.cancel_all(lbl, 'color')
        (Animation(color=(0, 1, 0.8, 1), duration=0.06, transition='out_expo') +
         Animation(color=(0, 0.9, 1, 1), duration=0.08, transition='out_expo') +
         Animation(color=(1, 1, 1, 1), duration=0.28, transition='in_out_expo')).start(lbl)

    def usar_historico(self, i):
        try:
            conta, txt, plano = self._historico[i]
        except IndexError:
            return
        tatil.tecla()
        self.expr = plano
        self.mostrando_resultado = True
        self._resultado_txt = txt
        self._atualizar(conta_feita=conta + ' =')

    # ── visor ─────────────────────────────────────────────────────────
    def _atualizar(self, conta_feita=None):
        lbl, sub = self.ids.calc_display, self.ids.calc_conta
        larg = max(dp(40), lbl.width - dp(4))
        if self.mostrando_resultado:
            txt = self._resultado_txt
            if not self._caber(lbl, txt, larg):        # nem pequeno cabe: cientifico
                try:
                    txt = fmt_resultado(Decimal(self.expr), cientifico=True)
                except Exception:
                    pass
                self._caber(lbl, txt, larg)
            lbl.text = txt
            if conta_feita is not None:
                sub.text = conta_feita
                sub.color = (0.45, 0.62, 0.70, 1)
        else:
            txt = fmt_conta(self.expr)
            if not self._caber(lbl, txt, larg):        # mostra o fim do que digita
                while len(txt) > 1 and not self._caber(lbl, '…' + txt, larg):
                    txt = txt[1:]
                txt = '…' + txt
            lbl.text = txt
            # previa do resultado enquanto digita
            sub.text = ''
            if re.search(r'[+*/%]|\d-|\)-', self.expr):
                try:
                    _, v = self._valor(self.expr)
                    sub.text = '= ' + fmt_resultado(v)
                    sub.color = (0.35, 0.55, 0.62, 1)
                except Exception:
                    pass
        self._caber(sub, sub.text, max(dp(40), sub.width - dp(4)), maximo=16, minimo=10)

    @staticmethod
    def _caber(lbl, texto, largura, maximo=44, minimo=18):
        """Poe no label a maior fonte (ate `maximo` sp) em que o texto cabe
        numa linha. Devolve False se nem com `minimo` sp couber."""
        if not texto:
            lbl.font_size = sp(maximo)
            return True
        cl = CoreLabel(text=texto, font_name=lbl.font_name, font_size=sp(maximo))
        cl.refresh()
        w = cl.texture.size[0] if cl.texture else 0
        fs = sp(maximo)
        if w > largura:
            fs = max(sp(minimo), sp(maximo) * largura / float(w))
        lbl.font_size = fs
        return w * fs / sp(maximo) <= largura + 0.5

    def _mostrar_historico(self):
        try:
            caixa = self.ids.calc_historico
            area = self.ids.calc_hist_area
        except Exception:
            return
        caixa.clear_widgets()
        cabem = int(area.height // dp(34))                         # sem invadir o titulo
        ultimas = self._historico[-max(0, min(self.MAX_HIST, cabem)):] if cabem > 0 else []
        base = len(self._historico) - len(ultimas)
        for k, (conta, txt, _) in enumerate(ultimas):
            idx = base + k
            b = Button(text=f"[color=#5a7f8c]{conta} =[/color]   [color=#00e5ff]{txt}[/color]",
                       markup=True, font_name='rajdhani.ttf', font_size='17sp',
                       background_normal='', background_color=(0, 0, 0, 0),
                       halign='right', valign='middle', shorten=True, shorten_from='left',
                       size_hint_y=None, height=dp(34))
            b.bind(size=lambda w, s: setattr(w, 'text_size', (s[0] - dp(8), s[1])))
            b.bind(on_press=lambda w, i=idx: self.usar_historico(i))
            caixa.add_widget(b)

    def _recusar(self):
        """Tecla que nao cabe ali (ex.: '++'): nada muda, so um tremidinho."""
        try:
            lbl = self.ids.calc_display
            Animation.cancel_all(lbl, 'color')
            (Animation(color=(1, 0.55, 0, 1), duration=0.05) +
             Animation(color=(1, 1, 1, 1), duration=0.18)).start(lbl)
        except Exception:
            pass

    def _erro(self, msg):
        lbl, sub = self.ids.calc_display, self.ids.calc_conta
        sub.text = msg
        sub.color = (1, 0.3, 0.35, 1)
        self._caber(sub, msg, max(dp(40), sub.width - dp(4)), maximo=16, minimo=10)
        try:
            som.tocar_erro()
        except Exception:
            pass
        tatil.erro()
        tremer_tela(18)
        Animation.cancel_all(lbl, 'color')
        (Animation(color=(1, 0.15, 0.2, 1), duration=0.07) +
         Animation(color=(1, 1, 1, 1), duration=0.45)).start(lbl)
