import whisper
import pyaudio
import numpy as np
import threading
import re
import requests
from faster_whisper import WhisperModel

WAKE_WORDS = ["hostess", "hey hostess"]
RECORD_SECONDS = 4
model_size = "medium"  # try "small" or "medium" if needed
MODEL = WhisperModel("medium", compute_type="int8", device="cpu")  # try "float32" for accuracy
CHAT_ENDPOINT = "http://localhost:5000/chat"

# This flag is controlled from outside to stop listening
LISTENING = True

def send_to_chat(text):
    try:
        response = requests.post(CHAT_ENDPOINT, json={"message": text})
        print(f"[🤖 Hostess replied]: {response.json().get('response')}")
    except Exception as e:
        print(f"[Error]: {e}")

def transcribe_audio_chunk(audio_np):
    segments, _ = MODEL.transcribe(audio_np, language="en")
    return " ".join(segment.text for segment in segments).strip().lower()

def debug_audio_level(frames):
    audio = b''.join(frames)
    audio_np = np.frombuffer(audio, np.int16)
    rms = np.sqrt(np.mean(audio_np ** 2))
    print(f"[🎚️ RMS Volume]: {rms:.2f}")

def detect_wake_word(text):
    return any(word in text.lower() for word in WAKE_WORDS)

def start_listening(callback=None):
    def listen_loop():
        global LISTENING
        p = pyaudio.PyAudio()

        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                input_device_index=None,  # ✅ default mic
                frames_per_buffer=1024
            )
        except Exception as e:
            print(f"[❌ Mic open failed]: {e}")
            return

        print("[🎤 Listening using default microphone...]")

        while LISTENING:
            frames = []
            for _ in range(0, int(44100 / 1024 * RECORD_SECONDS)):
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    frames.append(data)
                except Exception as e:
                    print(f"[Mic Read Error]: {e}")
                    return

            debug_audio_level(frames)

            audio = b''.join(frames)
            audio_np = np.frombuffer(audio, np.int16).astype(np.float32) / 32768.0

            try:
                text = transcribe_audio_chunk(audio_np)
                print(f"[🗣 Heard]: {text}")

                if detect_wake_word(text):
                    command = re.sub(r"^(hey\s+)?hostess[, ]*", "", text)
                    print(f"[🤖 Wake word detected]: {command}")
                    if command:
                        if callback:
                            callback(command)
                        else:
                            send_to_chat(command)
            except Exception as e:
                print(f"[Whisper error]: {e}")

    thread = threading.Thread(target=listen_loop, daemon=True)
    thread.start()

def stop_listening():
    global LISTENING
    LISTENING = False
