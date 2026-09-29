"""Recalcular ao editar: a sequencia de dias e a ultima data saem das datas
dos turnos (editar a data ou apagar um turno corrige tudo)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from p import patch
A = os.path.join('C:' + os.sep, 'Users', 'kirit', 'travetefocus', 'app')

patch(os.path.join(A, 'main.py'), [
    ("import shutil\nimport sys\n", "import shutil\nimport sys\nfrom datetime import datetime, timedelta\n"),
    ("""        self.total_geral = total_g
        self.total_xp    = total_x
        self.melhor_dia  = max(por_dia.values(), default=0)
""", """        self.total_geral = total_g
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
            ultima = max(dias)
            seq = 1
            while ultima - timedelta(days=seq) in dias:
                seq += 1
            self.streak      = seq
            self.ultima_data = ultima.strftime("%d/%m/%Y")
        else:
            self.streak      = 0
            self.ultima_data = ""
"""),
])
print('ok')
