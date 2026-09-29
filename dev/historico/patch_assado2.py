pk = r'C:\Users\kirit\travetefocus\app\kirito.py'
k = open(pk, encoding='utf-8').read()


def troca(a, b):
    global k
    assert k.count(a) == 1, (a[:70], k.count(a))
    k = k.replace(a, b)


troca('''                while time.time() - t0 < 0.010:
                    if not fila:
                        return False
                    _bytes(fila.pop(0))''', '''                while time.time() - t0 < 0.010:
                    if not fila:
                        return False
                    p = fila.pop(0)
                    if p.get('mugetsu'):
                        _bytes(p)
                    else:                        # o corpo (a parte cara) fica pronto
                        q = dict(p, luz=0.0, brilho=None)
                        imagem_camada(q, 'corpo', chave_camadas(q)[0])''')
troca('''

carregar_assado()
''', '''

carregar_assado()
if _GRAVA:
    import atexit
    atexit.register(salvar_gravados)
''')
open(pk, 'w', encoding='utf-8', newline='\r\n').write(k)
b = r'C:\Users\kirit\travetefocus\app\buildozer.spec'
s = open(b, encoding='utf-8').read()
a = 'source.include_exts = py,kv,ttf,json,wav,mp3,ogg,png,jpg,csv'
assert s.count(a) == 1
s = s.replace(a, a + ',bin')
open(b, 'w', encoding='utf-8', newline='').write(s)
print('ok')
