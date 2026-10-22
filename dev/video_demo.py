"""Poe o SOM do app no video gravado pela cena CENA=video (filme_cenas.py):
cada som que o app tocou (filme.json 'sons', quadro a 60/s) entra na hora
certa; mistura em mono, com um limitador suave, e junta ao video (AAC).

uso (Git Bash, em app/):
  S=../ferramentas/saida_testes/video
  VIDEO=$S/so_imagem.mp4 CENA=video CADA=2 TOUR_PY=dev/filme_cenas.py \\
      bash dev/tour.sh 1080 2090 $S 2.8125
  python dev/video_demo.py $S/filme.json $S/so_imagem.mp4 SAIDA.mp4 [largura]
(largura opcional: 720 reduz o video, ex.: para mandar no WhatsApp)"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.environ.setdefault('KIVY_LOG_MODE', 'PYTHON')
os.environ['KIVY_NO_ARGS'] = '1'
import imageio_ffmpeg  # noqa: E402

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
TAXA = 44100


def _wav_do_som(nome):
    """O arquivo do som `nome`: a gravacao (sons/) ou o sintetizado pelo som.py."""
    import som
    caminho = som._gravacao(nome)
    if caminho:
        return caminho
    if nome in som._RECEITAS:
        return som._gerar(nome)
    return None


def _ler(caminho):
    """Qualquer WAV -> mono float32 a 44.100 Hz (o ffmpeg converte)."""
    bruto = subprocess.run([FFMPEG, '-loglevel', 'error', '-i', caminho, '-f', 'f32le', '-ac', '1',
                            '-ar', str(TAXA), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(bruto, dtype=np.float32)


def main():
    log_json, video, saida = sys.argv[1], sys.argv[2], sys.argv[3]
    largura = int(sys.argv[4]) if len(sys.argv) > 4 else None
    L = json.load(open(log_json, encoding='utf-8'))
    q0 = L['video']['q0']
    n_quadros = int(subprocess.run(
        [FFMPEG, '-i', video, '-map', '0:v:0', '-c', 'copy', '-f', 'null', '-'],
        capture_output=True, text=True).stderr.split('frame=')[-1].split()[0])
    dur = n_quadros / float(L['video']['fps'])
    mix = np.zeros(int(dur * TAXA) + TAXA, dtype=np.float32)
    cache = {}
    faltam = set()
    for q, nome in L['sons']:
        if q < q0:
            continue
        if nome not in cache:
            try:
                c = _wav_do_som(nome)
                cache[nome] = _ler(c) if c else None
            except Exception as e:
                print('som', nome, e)
                cache[nome] = None
        a = cache[nome]
        if a is None:
            faltam.add(nome)
            continue
        i = int((q - q0) / 60.0 * TAXA)
        n = min(len(a), len(mix) - i)
        if n > 0:
            mix[i:i + n] += a[:n] * 0.8
    if faltam:
        print('sem arquivo:', sorted(faltam))
    mix = np.tanh(mix * 1.1) * 0.89                    # limitador suave (nada estoura)
    caminho_wav = saida + '.som.wav'
    with wave.open(caminho_wav, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    cmd = [FFMPEG, '-y', '-loglevel', 'error', '-i', video, '-i', caminho_wav]
    if largura:
        cmd += ['-vf', f'scale={largura}:-2:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '20',
                '-pix_fmt', 'yuv420p']
    else:
        cmd += ['-c:v', 'copy']
    cmd += ['-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', saida]
    subprocess.run(cmd, check=True)
    os.remove(caminho_wav)
    print(saida, f'{os.path.getsize(saida) / 1e6:.1f} MB', f'{dur:.1f} s')


main()
