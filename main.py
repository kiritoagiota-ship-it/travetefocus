"""
main.py — TraveteFocus v6.0 AINCRAD EDITION
Arquivo principal: apenas configuração, App e imports.
Toda a lógica de telas está em telas/*.py
"""
import json
import os
import threading
import shutil
import sys
from datetime import datetime, timedelta
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.properties import NumericProperty, ListProperty, StringProperty, BooleanProperty
from kivy.metrics import dp
from kivy.utils import platform
from kivy.resources import resource_add_path, resource_find

import som
from efeitos import *
from helpers import transicao_tela

from telas.loading     import TelaLoading
from telas.registro    import TelaRegistro
from telas.memorias    import TelaMemorias
from telas.progresso   import TelaProgresso
from telas.ganhos      import TelaGanhos
from telas.calculadora import TelaCalculadora

# ── Tela de menu (sem lógica, só navegação) ───────────────
class MenuPrincipal(Screen):
    def on_enter(self):
        # botoes entram em cascata, de cima para baixo
        try:
            from animacoes_ui import entrada_cascata
            botoes = [w for w in self.walk(restrict=True) if isinstance(w, BotaoAngular)]
            botoes.sort(key=lambda w: -w.to_window(*w.center)[1])
            entrada_cascata(botoes, atraso=0.07, dy=dp(28))
        except Exception as e:
            print(f"[menu] cascata: {e}")
        # vida enquanto o menu esta aberto: um reflexo passa pelo titulo e
        # pontos de luz correm pelas linhas (instalados uma vez so)
        try:
            from animacoes_ui import brilho_texto, luz_na_linha
            brilho_texto(self.ids.titulo_menu, periodo=6.5, atraso=1.2)
            luz_na_linha(self.ids.linha_menu_1, (0, 0.9, 1), periodo=5.0, atraso=0.6)
            luz_na_linha(self.ids.linha_menu_2, (0.6, 0.25, 1), periodo=5.0, atraso=2.2)
            luz_na_linha(self.ids.linha_menu_3, (0, 0.9, 1), periodo=5.0, atraso=3.8)
        except Exception as e:
            print(f"[menu] vida: {e}")

LARGURA_COLUNA = 560     # dp: largura maxima do app em janela larga (PC/tablet)


class RootWidget(FloatLayout):
    """Celular: o app ocupa a tela toda. Janela larga: o app fica numa coluna
    central e um fundo animado (grade + particulas) preenche as laterais."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._fundo_largo = None
        self.bind(size=self._ajustar_fundo)

    def _ajustar_fundo(self, *_):
        try:
            largo = self.width > dp(LARGURA_COLUNA + 80)
            if largo and self._fundo_largo is None:
                fundo = FloatLayout(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
                fundo.add_widget(GridHolografico(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0}))
                fundo.add_widget(FundoAnimado(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0}))
                self.add_widget(fundo, index=len(self.children))   # atras de tudo
                self._fundo_largo = fundo
            elif not largo and self._fundo_largo is not None:
                self.remove_widget(self._fundo_largo)
                self._fundo_largo = None
        except Exception as e:
            print(f"[root] fundo largo: {e}")


class Gerenciador(ScreenManager):
    def __init__(self, **kwargs):
        # a troca acontece escondida sob o corte de espada (golpe_tela);
        # um slide por baixo apareceria quando o veu clareia
        kwargs.setdefault('transition', NoTransition())
        super().__init__(**kwargs)

# ═══════════════════════════════════════════════════════════
#  CONFIGURAÇÃO DE JANELA
# ═══════════════════════════════════════════════════════════

def _configurar_janela():
    if platform not in ('android', 'ios'):
        Window.size = (420, 780)
        try:
            Window.minimum_width  = 320
            Window.minimum_height = 520
        except Exception:
            pass
        try:
            Window.left = 100
            Window.top  = 50
        except Exception:
            pass

_configurar_janela()

# ═══════════════════════════════════════════════════════════
#  APP
# ═══════════════════════════════════════════════════════════

class TraveteApp(App):
    total_geral     = NumericProperty(0)
    meta_geral      = NumericProperty(10000)
    total_xp        = NumericProperty(0)
    streak          = NumericProperty(0)
    melhor_dia      = NumericProperty(0)
    ultima_data     = StringProperty("")
    registros       = ListProperty([])
    memorias        = ListProperty([])
    periodos_ganhos = ListProperty([])
    versao          = StringProperty("dev")
    vibracao        = BooleanProperty(True)     # resposta tatil (tatil.py)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:                                   # escrito pelo build do GitHub
            import json
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'versao.json'),
                      encoding='utf-8') as f:
                self.versao = str(json.load(f).get('versao', 'dev'))
        except Exception:
            pass
        self.config_ganhos = {
            "valor_base":   0.25,
            "valor_meio":   0.27,          # faixa do meio (configs antigas ganham este padrao)
            "valor_bonus":  0.30,
            "meta_meio":    2500,
            "meta_bonus":   3000,
            "pecas_sabado": 200,           # meta do sabado (meio periodo)
            "tipo_periodo": "semanal"
        }

    def build(self):
        Window.softinput_mode = 'below_target'
        if platform == 'android':
            resource_add_path(os.path.dirname(os.path.abspath(__file__)))
        som.inicializar()
        self.carregar_dados()
        kv = resource_find("interface.kv") or "interface.kv"
        return Builder.load_file(kv)

    def on_start(self):
        # botao VOLTAR do Android (ESC no PC): antes jogava o app para o fundo
        # na hora, ate com um popup aberto ou no meio de uma tela
        Window.bind(on_keyboard=self._tecla_voltar)

    def _tecla_voltar(self, window, key, *args):
        if key != 27:
            return False
        try:
            return self._voltar()
        except Exception as e:
            print(f"[voltar] {e}")
            return True

    def _voltar(self):
        """VOLTAR faz o que o Android costuma fazer, em ordem: fecha o
        teclado do app; fecha o popup de cima; volta para o menu; no menu (ou
        na abertura) o Android minimiza o app, como sempre."""
        from kivy.uix.popup import Popup
        for w in list(Window.children):
            if w.__class__.__name__ in ('TecladoLetras', 'TecladoNumeros'):
                fechar = getattr(w, '_fechar', None)
                if fechar:
                    fechar()
                    return True
        for w in list(Window.children):              # o primeiro e o de cima
            if isinstance(w, Popup):
                if w.auto_dismiss:                   # (no meio de um golpe nao fecha)
                    w.dismiss()
                return True
        sm = self.root.ids.sm
        if sm.current not in ('menu', 'loading'):
            self.mudar_tela('menu')
            return True
        return False                                  # menu/abertura: o Android minimiza

    def on_pause(self):
        # No Android o app pode ser morto em segundo plano sem passar pelo
        # on_stop: grava ja, de forma sincrona
        self.salvar_dados(sincrono=True)
        return True

    def on_stop(self):
        # sincrono: numa thread daemon o processo encerra antes de gravar
        self.salvar_dados(sincrono=True)
        som.limpar()

    def mudar_tela(self, destino):
        transicao_tela(self, destino)

    def alternar_vibracao(self):
        """Botao do menu: liga/desliga a resposta tatil (fica salvo)."""
        self.vibracao = not self.vibracao
        self.salvar_dados()
        if self.vibracao:
            import tatil
            tatil.confirmar()

    def trocar_senha(self):
        """Botao do menu: abre a janela de trocar a senha."""
        from helpers import popup_trocar_senha
        popup_trocar_senha()

    def recalcular_totais(self):
        total_g = 0; total_x = 0
        por_dia = {}                       # dois turnos no mesmo dia somam
        for m in self.memorias:
            try:
                t = int(m.get('total', 0))
            except (TypeError, ValueError):
                t = 0
            total_g += t
            try:
                total_x += int(m.get('xp', 0))
            except (TypeError, ValueError):
                pass
            dia = str(m.get('data', '')).strip().split(' ')[0]
            por_dia[dia] = por_dia.get(dia, 0) + t
        for r in self.registros:
            try:
                total_x += int(r[2]) if len(r) > 2 else 0
            except (TypeError, ValueError):
                pass
        self.total_geral = total_g
        self.total_xp    = total_x
        self.melhor_dia  = max(por_dia.values(), default=0)
        # sequencia: dias seguidos com turno, terminando no dia mais recente
        dias = set()
        for dia in por_dia:
            try:
                dias.add(datetime.strptime(dia, "%d/%m/%Y").date())
            except ValueError:
                pass
        if dias:
            import metas
            ultima = max(dias)
            self.streak      = metas.sequencia(dias)      # o domingo de folga nao quebra
            self.ultima_data = ultima.strftime("%d/%m/%Y")
        else:
            self.streak      = 0
            self.ultima_data = ""

    def salvar_dados(self, sincrono=False):
        # copia de verdade (nao so a lista): a gravacao roda em outra thread e
        # nao pode ler um turno no meio de uma alteracao
        snapshot = json.loads(json.dumps({
            "memorias":        list(self.memorias),
            "total_geral":     self.total_geral,
            "meta_geral":      self.meta_geral,
            "total_xp":        self.total_xp,
            "registros":       list(self.registros),
            "streak":          self.streak,
            "melhor_dia":      self.melhor_dia,
            "ultima_data":     self.ultima_data,
            "periodos_ganhos": list(self.periodos_ganhos),
            "config_ganhos":   dict(self.config_ganhos),
            "config_app":      {"vibracao": bool(self.vibracao)},
        }, ensure_ascii=False))
        data_dir = self.user_data_dir
        if sincrono:
            self._salvar_bg(snapshot, data_dir)
            return
        threading.Thread(
            target=self._salvar_bg, args=(snapshot, data_dir), daemon=True
        ).start()

    _lock_salvar = threading.Lock()

    def _salvar_bg(self, dados, data_dir):
        # Serializa gravacoes: duas threads escrevendo o mesmo .tmp ao mesmo
        # tempo podiam gerar um dados.json corrompido
        with self._lock_salvar:
            self._salvar_bg_impl(dados, data_dir)

    def _salvar_bg_impl(self, dados, data_dir):
        try:
            tmp  = os.path.join(data_dir, "dados.json.tmp")
            dest = os.path.join(data_dir, "dados.json")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())          # no disco de verdade antes de trocar (celular desligando)
            os.replace(tmp, dest)
            # Backup rotativo — mantém últimas 3 versões
            for i in range(2, 0, -1):
                bsrc = os.path.join(data_dir, f"dados.backup{i}.json")
                bdst = os.path.join(data_dir, f"dados.backup{i+1}.json")
                if os.path.exists(bsrc):
                    shutil.copy2(bsrc, bdst)
            if os.path.exists(dest):
                shutil.copy2(dest, os.path.join(data_dir, "dados.backup1.json"))
        except Exception as e:
            print(f"[ERRO] _salvar_bg: {e}")

    @staticmethod
    def _int(v):
        try:
            return int(float(str(v).replace(',', '.')))
        except (TypeError, ValueError):
            return 0

    def _normalizar_memorias(self, lista):
        """Turnos salvos por versoes antigas podem ter numero como texto ('120')
        ou faltar campo: as telas comparam e somam numeros. Aqui so se acerta o
        TIPO (nada e apagado; campos desconhecidos ficam)."""
        out = []
        for m in lista if isinstance(lista, list) else []:
            if not isinstance(m, dict):
                continue
            m = dict(m)
            m['data'] = str(m.get('data', '') or '')
            m['total'] = self._int(m.get('total', 0))
            m['xp'] = self._int(m.get('xp', 0))
            if not isinstance(m.get('itens'), list):
                m['itens'] = []
            out.append(m)
        return out

    def _normalizar_registros(self, lista):
        out = []
        for r in lista if isinstance(lista, list) else []:
            if not isinstance(r, (list, tuple)) or len(r) < 2:
                continue
            r = list(r)
            r[1] = str(self._int(r[1]))
            if len(r) < 3:
                r.append(0)
            r[2] = self._int(r[2])
            out.append(r)
        return out

    def carregar_dados(self):
        """Carrega dados com fallback para backups se arquivo principal estiver corrompido."""
        d = self.user_data_dir
        candidatos = [
            os.path.join(d, "dados.json"),
            os.path.join(d, "dados.backup1.json"),
            os.path.join(d, "dados.backup2.json"),
            os.path.join(d, "dados.backup3.json"),
        ]
        for arquivo in candidatos:
            if not os.path.exists(arquivo):
                continue
            try:
                with open(arquivo, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if os.path.basename(arquivo) != "dados.json":
                    print(f"[DADOS] Recuperado de {arquivo}")
                # a conferencia dos tipos NUNCA pode fazer um arquivo bom parecer
                # estragado: se ela falhar, ficam os dados como vieram
                try:
                    self.memorias = self._normalizar_memorias(d.get("memorias", []))
                except Exception as e:
                    print(f"[DADOS] conferir turnos: {e}")
                    self.memorias = d.get("memorias", [])
                try:
                    self.registros = self._normalizar_registros(d.get("registros", []))
                except Exception as e:
                    print(f"[DADOS] conferir lotes: {e}")
                    self.registros = d.get("registros", [])
                self.meta_geral      = d.get("meta_geral",    10000)
                self.streak          = d.get("streak",            0)
                self.ultima_data     = d.get("ultima_data",      "")
                self.periodos_ganhos = d.get("periodos_ganhos",  [])
                self.config_ganhos.update(d.get("config_ganhos", {}))
                self.vibracao        = bool(d.get("config_app", {}).get("vibracao", True))
                self.recalcular_totais()
                return
            except Exception as e:
                print(f"[DADOS] {arquivo} corrompido: {e} — tentando backup...")
                # guarda o arquivo estragado antes que a proxima gravacao passe
                # por cima dele (da para tentar recuperar a mao depois)
                try:
                    guarda = arquivo + ".corrompido"
                    if not os.path.exists(guarda):
                        shutil.copy2(arquivo, guarda)
                except Exception as e2:
                    print(f"[DADOS] nao guardei a copia: {e2}")


if __name__ == "__main__":
    TraveteApp().run()