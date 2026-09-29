"""Gera 'Starburst' e 'Stream!' com as vozes Piper (varias variacoes)."""
import os, wave, sys
from piper import PiperVoice
from piper.config import SynthesisConfig

AQUI = os.path.dirname(os.path.dirname(__file__))
VOZES = os.path.join(AQUI, 'vozes')
SAIDA = os.path.join(AQUI, 'voz_piper')
os.makedirs(SAIDA, exist_ok=True)

textos = {
    'starburst': ('Starburst...', 1.18),
    'stream': ('Stream!', 1.0),
    'frase': ('Starburst... Stream!', 1.12),
}
for nome in ('ryan', 'hfc_male', 'joe'):
    v = PiperVoice.load(os.path.join(VOZES, f'en_US-{nome}-medium.onnx'))
    for chave, (txt, ls) in textos.items():
        cfg = SynthesisConfig(length_scale=ls, noise_scale=0.55, noise_w_scale=0.7)
        caminho = os.path.join(SAIDA, f'{nome}_{chave}.wav')
        with wave.open(caminho, 'wb') as wf:
            v.synthesize_wav(txt, wf, syn_config=cfg)
        with wave.open(caminho) as wf:
            print(nome, chave, wf.getframerate(), round(wf.getnframes() / wf.getframerate(), 2), 's')
