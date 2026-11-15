"""Regressão do fechamento com turnos tardios. Rode: python dev/teste_ganhos.py."""
import sys
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from telas.ganhos import TelaGanhos, _num


class Ganhos(unittest.TestCase):
    def setUp(self):
        with patch.object(TelaGanhos, 'on_kv_post'):
            self.tela = TelaGanhos()
        self.semana = dict(tipo='semanal', data_inicio='14/11/2026')
        self.fechado = dict(tipo='semanal', data_inicio='09/11/2026', data_fim='14/11/2026',
                            contadas=['ts:1'], total_pecas=2950, total_ganho=796.50,
                            valor_base=0.25, valor_meio=0.27, valor_bonus=0.30,
                            meta_meio=2500, meta=3000)
        self.app = SimpleNamespace(
            config_ganhos={'tipo_periodo': 'semanal', 'valor_bonus': 0.35}, registros=[],
            periodos_ganhos=[self.fechado, self.semana], memorias=[
                dict(data='13/11/2026 17:00', total=2950, ts=1),
                dict(data='13/11/2026 18:00', total=100, ts=2),
                dict(data='16/11/2026 10:00', total=200, ts=3),
            ])
        app = patch('telas.ganhos.App.get_running_app', return_value=self.app)
        relogio = patch('telas.ganhos.datetime', wraps=datetime)
        app.start()
        relogio.start().now.return_value = datetime(2026, 11, 16, 18)
        self.addCleanup(app.stop)
        self.addCleanup(relogio.stop)

    def test_turno_atrasado_recalcula_faixa_e_desconta_fechamento(self):
        turnos, pecas, semanas, _, _ = self.tela._conta_periodo(self.semana)
        self.assertEqual([t['ts'] for t in turnos], [2, 3])
        self.assertEqual(pecas, 300)
        self.assertEqual([s['ganho'] for s in semanas], [118.50, 50.00])
        self.assertEqual(self.fechado['total_ganho'], 796.50)

    def test_lote_atrasado_entra_na_projecao_e_impede_fechar(self):
        self.app.memorias.pop(1)
        self.app.registros.append(['Camisa', '100', 300, '13/11/2026'])
        _, pecas, semanas, _, soltas = self.tela._conta_periodo(self.semana)
        self.assertEqual((pecas, soltas, semanas[0]['ganho']), (300, 100, 118.50))
        _, pecas, semanas, _, soltas = self.tela._conta_periodo(self.semana, com_lotes=False)
        self.assertEqual((pecas, soltas, semanas[0]['ganho']), (200, 100, 50.00))

    def test_segundo_acerto_conta_so_a_diferenca_nova(self):
        self.app.periodos_ganhos.insert(1, dict(
            data_inicio='14/11/2026', data_fim='14/11/2026', contadas=['ts:2'],
            semanas=[dict(seg='2026-11-09', pecas=100, ganho=118.50,
                          faixas=dict(valor_base=0.25, valor_meio=0.27, valor_bonus=0.30,
                                      meta_meio=2500, meta_bonus=3000))]))
        self.app.memorias.append(dict(data='12/11/2026 17:00', total=50, ts=4))
        turnos, pecas, semanas, _, _ = self.tela._conta_periodo(self.semana)
        self.assertEqual([t['ts'] for t in turnos], [3, 4])
        self.assertEqual(pecas, 250)
        self.assertEqual([s['ganho'] for s in semanas], [15.00, 50.00])

    def test_fechamento_antigo_sem_lista_de_turnos_nao_recobra(self):
        self.fechado.pop('contadas')
        turnos, pecas, semanas, _, _ = self.tela._conta_periodo(self.semana)
        self.assertEqual([t['ts'] for t in turnos], [3])
        self.assertEqual((pecas, semanas[0]['ganho']), (200, 50.00))

    def test_periodo_antigo_de_varias_semanas_com_turnos_identificados(self):
        self.fechado.update(data_inicio='02/11/2026', total_pecas=3050, total_ganho=821.50,
                            contadas=['ts:1', 'ts:4'])
        self.app.memorias.append(dict(data='04/11/2026 17:00', total=100, ts=4))
        turnos, pecas, semanas, _, _ = self.tela._conta_periodo(self.semana)
        self.assertEqual([t['ts'] for t in turnos], [2, 3])
        self.assertEqual(pecas, 300)
        self.assertEqual([s['ganho'] for s in semanas], [118.50, 50.00])

    def test_ajustes_rejeitam_valores_nao_finitos_e_meta_fracionaria(self):
        self.assertIsNone(_num('inf'))
        self.assertIsNone(_num('NaN', inteiro=True))
        self.assertIsNone(_num('10,5', inteiro=True))
        self.assertEqual(_num('0,30'), 0.30)

    def test_confirmacao_reabre_se_lote_entrou_enquanto_estava_aberta(self):
        turnos, pecas, semanas, fim, _ = self.tela._conta_periodo(self.semana, com_lotes=False)
        self.app.registros.append(['Camisa', '100', 300, '13/11/2026'])
        with patch.object(self.tela, 'fechar_periodo') as confirmar:
            self.tela._fechar_de_vez(self.semana, ('ts:2', 'ts:3'), pecas, 168.50, semanas, fim)
        confirmar.assert_called_once()
        self.assertNotIn('data_fim', self.semana)


if __name__ == '__main__':
    unittest.main()
