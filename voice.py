import os
import subprocess
import torch
import collections
from TTS.utils.radam import RAdam

# Add both RAdam and collections.defaultdict to safe globals
torch.serialization.add_safe_globals([RAdam, collections.defaultdict])

from TTS.api import TTS
from PyQt6.QtCore import QTimer, QCoreApplication
import sounddevice as sd
import numpy as np

COQUI_MODEL = "tts_models/en/ek1/tacotron2"  # Example: British English female

tts = TTS(COQUI_MODEL)

def speak(text):
    """
    Synthesize and play speech from text using Coqui TTS with a British English female voice.
    This function is safe to call from any thread.
    """
    def do_speak():
        # Synthesize speech to numpy array
        wav = tts.tts(text=text, speaker=tts.speakers[0] if hasattr(tts, "speakers") else None)
        # Play audio using sounddevice
        sd.play(wav, tts.synthesizer.output_sample_rate)
        sd.wait()
    # Ensure TTS runs on the main thread
    app = QCoreApplication.instance()
    if app and hasattr(QTimer, "singleShot"):
        QTimer.singleShot(0, do_speak)
    else:
        do_speak()