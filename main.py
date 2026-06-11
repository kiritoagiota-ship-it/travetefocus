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
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.properties import NumericProperty, ListProperty, StringProperty
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
        pass

class RootWidget(FloatLayout):
    pass

class Gerenciador(ScreenManager):
    pass

# ═══════════════════════════════════════════════════════════
#  CONFIGURAÇÃO DE JANELA
# ═══════════════════════════════════════════════════════════

def _configurar_janela():
    if platform not in ('android', 'ios'):
        Window.size = (420, 780)
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_ganhos = {
            "valor_base":   0.25,
            "valor_bonus":  0.30,
            "meta_bonus":   3000,
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

    def on_stop(self):
        self.salvar_dados()
        som.limpar()

    def mudar_tela(self, destino):
        transicao_tela(self, destino)

    def recalcular_totais(self):
        total_g = 0; total_x = 0; melhor = 0
        for m in self.memorias:
            total_g += int(m.get('total', 0))
            total_x += int(m.get('xp',    0))
            if m.get('total', 0) > melhor:
                melhor = m['total']
        for r in self.registros:
            total_x += int(r[2]) if len(r) > 2 else 0
        self.total_geral = total_g
        self.total_xp    = total_x
        self.melhor_dia  = melhor

    def salvar_dados(self):
        snapshot = {
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
        }
        data_dir = self.user_data_dir
        threading.Thread(
            target=self._salvar_bg, args=(snapshot, data_dir), daemon=True
        ).start()

    def _salvar_bg(self, dados, data_dir):
        try:
            tmp  = os.path.join(data_dir, "dados.json.tmp")
            dest = os.path.join(data_dir, "dados.json")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
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
                if arquivo != "dados.json":
                    print(f"[DADOS] Recuperado de {arquivo}")
                self.memorias        = d.get("memorias",        [])
                self.registros       = d.get("registros",       [])
                self.meta_geral      = d.get("meta_geral",    10000)
                self.streak          = d.get("streak",            0)
                self.ultima_data     = d.get("ultima_data",      "")
                self.periodos_ganhos = d.get("periodos_ganhos",  [])
                self.config_ganhos.update(d.get("config_ganhos", {}))
                self.recalcular_totais()
                return
            except Exception as e:
                print(f"[DADOS] {arquivo} corrompido: {e} — tentando backup...")


if __name__ == "__main__":
    TraveteApp().run()
