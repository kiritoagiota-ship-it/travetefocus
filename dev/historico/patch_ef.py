import os
AQUI = os.path.dirname(__file__)
R = r'C:\Users\kirit\travetefocus\app'


def troca(p, a, b, n=1):
    caminho = os.path.join(R, p)
    c = open(caminho, encoding='utf-8').read()
    assert c.count(a) == n, (p, a[:80], c.count(a))
    open(caminho, 'w', encoding='utf-8').write(c.replace(a, b))


# ── F: cenas de comemoracao ──
com = open(os.path.join(AQUI, 'comemora.txt'), encoding='utf-8').read()
troca('cenas.py', 'def kirito_wipe(widgets, on_fim=None, grafico=None, area_lista=None):',
      com + 'def kirito_wipe(widgets, on_fim=None, grafico=None, area_lista=None):')
troca('telas/progresso.py', '''        def _level_up_fanfare(dt):
            try: som.tocar_level_up()
            except Exception: pass''', '''        def _level_up_fanfare(dt):
            try: som.tocar_level_up()
            except Exception: pass
            # o Yoru comemora do lado do nivel
            try:
                from cenas import kirito_nivel
                kirito_nivel(self.ids.lbl_level_num)
            except Exception as e:
                print(f"[progresso] yoru: {e}")''')
troca('telas/ganhos.py', '''        caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        _abrir_popup(caixa, pop)''', '''        caixa.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        _abrir_popup(caixa, pop)
        if n_bonus > 0:                          # bateu a meta: o Yoru comemora
            def _yoru(dt):
                try:
                    from cenas import kirito_meta
                    kirito_meta(caixa)
                except Exception as e:
                    print(f"[ganhos] yoru: {e}")
            Clock.schedule_once(_yoru, 0.45)''', n=1)

# ── E: sons proprios ──
troca('cenas.py', """                'teleporte', 'golpe_final', 'voz_ha', 'voz_seiya', 'voz_teya', 'voz_mugetsu']""",
      """                'teleporte', 'golpe_final', 'voz_ha', 'voz_seiya', 'voz_teya', 'voz_mugetsu',
                'giro', 'fitas', 'cristal', 'vidro', 'fogo', 'trevas']""")
troca('cenas.py', """                        _som('corte2' if q == 3 else 'corte')
                        if q == 3:
                            _som('voz_seiya')""", """                        _som('giro')
                        _som('corte2' if q == 3 else 'corte')
                        if q == 3:
                            _som('voz_seiya')""")
troca('cenas.py', """            estado['casulo'] = _Crisalida(kk, camada, faiscas, on_estouro=_estoura_casulo)
            ag.depois(1.9, _estoura_casulo)               # seguranca, se a crisalida falhar
            _som('carga')""", """            estado['casulo'] = _Crisalida(kk, camada, faiscas, on_estouro=_estoura_casulo)
            ag.depois(1.9, _estoura_casulo)               # seguranca, se a crisalida falhar
            _som('fitas')""")
troca('cenas.py', """            _brilho_tela(camada, 0.45, 0.25, (0.85, 0.75, 1.0))
            _som('absorve')""", """            _brilho_tela(camada, 0.45, 0.25, (0.85, 0.75, 1.0))
            _som('absorve')
            _som('vidro')
            ag.depois(0.3, lambda: _som('fogo'))""")
troca('cenas.py', """            tv.crescer(ax, ay + alt * 0.3, dur=0.75)
            _som('reiatsu')""", """            tv.crescer(ax, ay + alt * 0.3, dur=0.75)
            _som('trevas')
            ag.depois(0.5, lambda: _som('fogo'))""")
# a crisalida trinca: som do cristal quando as rachaduras comecam
troca('cenas.py', """            # rachaduras de luz
            if t >= self.T_CRISTAL:""", """            # rachaduras de luz
            if t >= self.T_CRISTAL and not getattr(self, '_trincou', False):
                self._trincou = True
                _som('cristal')
            if t >= self.T_CRISTAL:""")
# estocada: vidro rachando
troca('cenas.py', """            _quadro_impacto(s.cam, k, (s.cx, s.cy))
            _som('golpe_final')""", """            _quadro_impacto(s.cam, k, (s.cx, s.cy))
            _som('golpe_final')
            _som('vidro')""")
# pergaminho: papel voando
troca('cenas.py', """                    rolo.soltar((W + s.te * 20, H + s.te * 10), 0.5)
                    _som('pulo')""", """                    rolo.soltar((W + s.te * 20, H + s.te * 10), 0.5)
                    _som('papel')""")
troca('cenas.py', """        _precarregar_sons(['materializa', 'teleporte', 'corte', 'corte2', 'pulo', 'koiguchi', 'sacar_iai',
                           'desliza', 'embainhar', 'golpe_final', 'habilidade', 'voz_teya', 'voz_seiya'])""",
      """        _precarregar_sons(['materializa', 'teleporte', 'corte', 'corte2', 'pulo', 'koiguchi', 'sacar_iai',
                           'desliza', 'embainhar', 'golpe_final', 'habilidade', 'voz_teya', 'voz_seiya',
                           'vidro', 'papel', 'giro', 'moedas', 'pouso'])""")
print('ok')
