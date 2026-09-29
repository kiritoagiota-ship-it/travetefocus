import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app', 'sons', 'CREDITOS.txt')
patch(A, [("""Vozes do Yoru (voz_starburst, voz_stream, voz_mugetsu, voz_ha, voz_seiya, voz_teya)
------------------------------------------------------------------------------------""",
"""Vozes do Yoru (voz_starburst, voz_stream, voz_mugetsu, voz_ha, voz_seiya, voz_teya
e os gemidinhos dos golpes: gemido_ha, gemido_hun, gemido_ya, gemido_yaa,
gemido_to, gemido_fun)
------------------------------------------------------------------------------------""")])
print('ok')
