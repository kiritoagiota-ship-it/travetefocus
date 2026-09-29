pk = r'C:\Users\kirit\travetefocus\app\kirito.py'
k = open(pk, encoding='utf-8').read()
a = """        # (as laminas nao atrasam: o corpo e desenhado uma vez por pose)"""
assert k.count(a) == 1
k = k.replace(a, """        # (as laminas nao atrasam: o corpo e desenhado uma vez por pose)
        if b.get('mugetsu'):
            # forma Mugetsu (ainda num desenho so): menos estados, para os
            # quadros virem prontos do arquivo
            q['hx'] = q['hy'] = 0
            q['fase'] = (int(self._fase * 3) % 3) / 3.0""")
open(pk, 'w', encoding='utf-8', newline='\r\n').write(k)
print('ok')
