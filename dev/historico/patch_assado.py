"""Quadros prontos: o PC desenha uma vez as poses que as cenas usam e grava
em yoru_quadros.bin (vai no APK); o celular so abre. Tambem grava o que as
cenas pedem quando YORU_GRAVA aponta para um arquivo."""
pk = r'C:\Users\kirit\travetefocus\app\kirito.py'
k = open(pk, encoding='utf-8').read()


def troca(a, b):
    global k
    assert k.count(a) == 1, (a[:70], k.count(a))
    k = k.replace(a, b)


troca('''def _bytes(p):''', '''# ═══════════════════════════════════════════════════════════════════
#  QUADROS PRONTOS (assados no PC; o arquivo vai no APK)
#  Formato: b'YQ01' + tamanho do cabecalho (4 bytes) + cabecalho (json em
#  zlib) + as imagens, cada uma em zlib (1 byte por texel = cor da paleta).
#  Se o desenho mudou depois de assar (a pose de prova sai diferente), o
#  arquivo e ignorado e tudo e desenhado na hora, como antes.
# ═══════════════════════════════════════════════════════════════════
import os as _os
import json as _json
import zlib as _zlib
import hashlib as _hashlib

_ASSADO = {}               # repr((camada, chave)) -> (inicio, tamanho, recorte, extra)
_ASSADO_CAIXAS = {}        # repr(chave da pose) -> caixa
_ASSADO_DADOS = [None]
_ASSADO_OK = [None]        # None = ainda nao conferido
_ASSADO_PROVA = [None]
_GRAVA = _os.environ.get('YORU_GRAVA')
_GRAVADOS = {}


def _pose_prova():
    return dict(POSE_A['guarda'], capa=0.0, cabelo=0.0, lift=0.0, fase=0.0)


def _digital(dados):
    return _hashlib.md5(dados).hexdigest()[:16]


def carregar_assado(caminho=None):
    """Le o indice do arquivo de quadros prontos (as imagens so quando
    forem pedidas)."""
    try:
        caminho = caminho or _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'yoru_quadros.bin')
        if not _os.path.exists(caminho):
            return False
        with open(caminho, 'rb') as f:
            dados = f.read()
        if dados[:4] != b'YQ01':
            return False
        n = int.from_bytes(dados[4:8], 'little')
        cab = _json.loads(_zlib.decompress(dados[8:8 + n]).decode('utf-8'))
        if cab.get('paleta') != ''.join(sorted(_PALETA)) or cab.get('R') != R:
            print('[kirito] quadros prontos de outra versao: ignorados')
            return False
        base = 8 + n
        for ch, (ini, tam, rec, extra) in cab['itens'].items():
            _ASSADO[ch] = (base + ini, tam, tuple(rec), extra)
        for ch, cx in cab.get('caixas', {}).items():
            _ASSADO_CAIXAS[ch] = tuple(cx)
        _ASSADO_PROVA[0] = cab.get('prova')
        _ASSADO_DADOS[0] = dados
        print(f"[kirito] quadros prontos: {len(_ASSADO)} imagens, {len(_ASSADO_CAIXAS)} caixas")
        return True
    except Exception as e:
        print(f"[kirito] quadros prontos: {e}")
        return False


def _assado_valido():
    """Confere uma vez se o desenho de hoje e o mesmo de quando assou."""
    if _ASSADO_OK[0] is None:
        try:
            q = _pose_prova()
            dados, rec = _rasteriza(montar(q, camada='corpo'))
            _ASSADO_OK[0] = bool(_ASSADO) and _digital(dados) == _ASSADO_PROVA[0]
            if not _ASSADO_OK[0] and _ASSADO:
                print('[kirito] quadros prontos desatualizados: ignorados')
        except Exception as e:
            print(f"[kirito] prova: {e}")
            _ASSADO_OK[0] = False
    return _ASSADO_OK[0]


def _do_assado(qual, chave):
    """(bytes RGBA, recorte, extra) da imagem pronta, ou None."""
    if not _ASSADO:
        return None
    item = _ASSADO.get(repr((qual, chave)))
    if item is None or not _assado_valido():
        return None
    ini, tam, rec, extra = item
    idx = _zlib.decompress(_ASSADO_DADOS[0][ini:ini + tam])
    buf = bytearray(len(idx) * 4)
    buf[0::4] = idx.translate(_TAB[0])
    buf[1::4] = idx.translate(_TAB[1])
    buf[2::4] = idx.translate(_TAB[2])
    buf[3::4] = idx.translate(_TAB[3])
    return bytes(buf), rec, extra


def _grava(qual, chave, q):
    """Anota o pedido (so no PC, quando assando)."""
    if _GRAVA:
        _GRAVADOS.setdefault(repr((qual, chave)), (qual, q))


def salvar_gravados():
    if not _GRAVA:
        return
    try:
        velho = {}
        if _os.path.exists(_GRAVA):
            with open(_GRAVA, encoding='utf-8') as f:
                velho = _json.load(f)
        for ch, (qual, q) in _GRAVADOS.items():
            velho[ch] = [qual, {kk: (list(v) if isinstance(v, tuple) else v) for kk, v in q.items()}]
        with open(_GRAVA, 'w', encoding='utf-8') as f:
            _json.dump(velho, f)
        print(f"[kirito] gravados {len(_GRAVADOS)} pedidos (total {len(velho)})")
    except Exception as e:
        print(f"[kirito] gravar: {e}")


def _bytes(p):''')
# camadas: olha o arquivo antes de desenhar
troca('''    k = (qual, chave)
    item = _CAM.get(k)
    if item is not None:
        _CAM.move_to_end(k)
        return item
    item = _rasteriza(montar(q, camada=qual))''', '''    k = (qual, chave)
    item = _CAM.get(k)
    if item is not None:
        _CAM.move_to_end(k)
        return item
    _grava(qual, chave, q)
    pronto = _do_assado(qual, chave)
    item = (pronto[0], pronto[1]) if pronto else _rasteriza(montar(q, camada=qual))''')
# pose inteira (forma Mugetsu): tambem pode vir pronta (com o contorno do fogo)
troca('''def _gerar_imagem(p):
    ch = _chave(p)
    item = _CACHE.get(ch)
    if item is not None:
        _CACHE.move_to_end(ch)
        return ch, item
    px = montar(p)''', '''def _gerar_imagem(p):
    ch = _chave(p)
    item = _CACHE.get(ch)
    if item is not None:
        _CACHE.move_to_end(ch)
        return ch, item
    _grava('inteiro', ch, p)
    pronto = _do_assado('inteiro', ch)
    if pronto:
        dados, rec, extra = pronto
        item = (dados, tuple(extra['caixa']), [tuple(b) for b in extra['bordas']] if extra.get('bordas') else None,
                rec)
        _CACHE[ch] = item
        while len(_CACHE) > _CACHE_MAX:
            _CACHE.popitem(last=False)
        return ch, item
    px = montar(p)''')
troca('''    cx = _CAIXAS.get(ch)
    if cx is None:
        px = montar(p, rapido=True)''', '''    cx = _CAIXAS.get(ch)
    if cx is None and _ASSADO_CAIXAS and _assado_valido():
        cx = _ASSADO_CAIXAS.get(repr(ch))
    if cx is None:
        _grava('caixa', ch, p)
        px = montar(p, rapido=True)''')
k += '''

carregar_assado()
'''
open(pk, 'w', encoding='utf-8', newline='\r\n').write(k)
print('ok')
