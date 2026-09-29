"""Gritos de espadachim GRAVADOS (29/09/2026, mistura A+C) no lugar das
vozes sintetizadas: 'Hah!', 'Sei!', 'Fun!' nos cortes, 'Seiya!' nos golpes
fortes; falas de anime nos especiais: 'Saa, iku zo!' (comeca a danca / o
WIPE), 'Tou!' (entrada rapida), 'Kurae!', 'Ukete miro! Ougi!' (golpe final
do Bankai)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'cenas.py'), [
    ("""                'golpe_final', 'voz_mugetsu', 'giro', 'fitas', 'trevas',
                'gemido_ha', 'gemido_hun', 'gemido_ya', 'gemido_yaa', 'gemido_to', 'gemido_fun']""",
     """                'golpe_final', 'fala_ougi', 'fala_ikuzo', 'fala_kurae', 'kiai_seiya', 'giro', 'fitas',
                'trevas', 'fusao', 'reiatsu',
                'kiai_ha1', 'kiai_ha2', 'kiai_sei1', 'kiai_sei2', 'kiai_sei3', 'kiai_fun']"""),
    ("""_GEMIDOS = ['gemido_ha', 'gemido_hun', 'gemido_ya', 'gemido_yaa', 'gemido_to', 'gemido_fun']""",
     """_GEMIDOS = ['kiai_ha1', 'kiai_ha2', 'kiai_sei1', 'kiai_sei2', 'kiai_sei3', 'kiai_fun']"""),
    ("""def _gemido():
    \"\"\"Kiai curtinho do Yoru num golpe ('Hah!', 'Hmph!', 'Yah!'...): varia
    e nunca repete o ultimo.\"\"\"
    opcoes = [g for g in _GEMIDOS if g != _ult_gemido[0]]""",
     """def _gemido(forte=False):
    \"\"\"Kiai do Yoru num golpe (gravado: 'Hah!', 'Sei!', 'Fun!'): varia e
    nunca repete o ultimo. forte=True: 'Seiya!' (golpe com as duas).\"\"\"
    if forte:
        _som('kiai_seiya')
        _ult_gemido[0] = 'kiai_seiya'
        return
    opcoes = [g for g in _GEMIDOS if g != _ult_gemido[0]]"""),
    # abertura: "Saa, iku zo!" no close do olho antes do iai
    ("""            ag.depois(0.12, lambda: close_rosto(camada, 'normal', dur=0.72, y_rel=0.8,""",
     """            ag.depois(0.1, lambda: _som('fala_ikuzo'))
            ag.depois(0.12, lambda: close_rosto(camada, 'normal', dur=0.72, y_rel=0.8,"""),
    # TE e FO (as duas espadas): Seiya!
    ("""                if i == i_r - 2:
                    _gemido()
                    kk.empurrar(capa=12, lift=6)""", """                if i == i_r - 2:
                    _gemido(forte=True)
                    kk.empurrar(capa=12, lift=6)"""),
    ("""                if i == i_r - 2:
                    _gemido()
                    kk.empurrar(capa=10, cabelo=8, lift=6)""", """                if i == i_r - 2:
                    _som('fala_kurae')
                    kk.empurrar(capa=10, cabelo=8, lift=6)"""),
    # golpe final do Bankai: "Ukete miro! Ougi!" - o corte cai no "GI!"
    ("""            _som('voz_mugetsu')
            kk.empurrar(capa=4, cabelo=4, lift=3)
            ag.depois(0.85, _golpe_final)             # o corte cai no "TSU" do grito""",
     """            _som('fala_ougi')
            kk.empurrar(capa=4, cabelo=4, lift=3)
            ag.depois(1.2, _golpe_final)              # o corte cai no "GI!" do grito"""),
    # entrada rapida: "Tou!"
    ("""            kk.tocar(K.sequencia(chaves))
            _som('sacar_iai')
            _gemido()
            kk.empurrar(capa=16, cabelo=12)""", """            kk.tocar(K.sequencia(chaves))
            _som('sacar_iai')
            _som('fala_tou')
            kk.empurrar(capa=16, cabelo=12)"""),
    # WIPE: sem o "Starburst Stream" sintetizado
    ("""        _precarregar_sons(['sacar', 'corte', 'corte2', 'titulo', 'pulo', 'teleporte', 'voz_starburst',
                           'voz_stream'] + _GEMIDOS)""",
     """        _precarregar_sons(['sacar', 'corte', 'corte2', 'titulo', 'pulo', 'teleporte', 'fala_ikuzo',
                           'fala_kurae', 'kiai_seiya'] + _GEMIDOS)"""),
    ("""        def _saca():
            _som('voz_starburst')""", """        def _saca():
            _som('fala_ikuzo')"""),
    ("""                elif i == 40:                        # a fala "Sutabasuto..." ja acabou
                    _som('voz_stream')""", """                elif i == 40:                        # a fala "Saa, iku zo!" ja acabou
                    _som('fala_kurae')"""),
])
print('ok')
