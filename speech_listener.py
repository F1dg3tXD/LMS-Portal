import pyaudio
import wave
import threading
import subprocess
import os
import re

WAKE_WORDS = ["hostess", "hey hostess"]
RECORD_SECONDS = 4
SAMPLE_RATE = 16000
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
CHUNK = 1024
MODEL_PATH = "models/whisper-large-v3-f16.gguf"  # Set your model path here
WHISPER_BIN = os.path.abspath("bin/whisper/whisper-cli.exe")

LISTENING = True

print(f"[🔍 WHISPER BIN]: {WHISPER_BIN}")
print(f"[🔍 MODEL PATH]: {MODEL_PATH}")
print(f"[📂 File Exists]:", os.path.isfile(WHISPER_BIN), os.path.isfile(MODEL_PATH))

def transcribe_with_whisper_cpp(wav_path: str) -> str:
    txt_path = wav_path.replace(".wav", ".txt")

    try:
        result = subprocess.run([
            WHISPER_BIN,
            "-m", MODEL_PATH,
            "-f", wav_path,
            "-l", "en",
            "-otxt",
            "-nt"
        ], capture_output=True, text=True)

        print("[🔧 Whisper output]:", result.stdout)
        print("[⚠️ Whisper errors]:", result.stderr)

        if result.returncode != 0:
            print("[❌ Whisper CLI failed]")
            return ""

        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                return f.read().strip().lower()
        else:
            print("[⚠️ No transcript file generated]")
            return ""

    except Exception as e:
        print(f"[❌ Whisper subprocess failed]: {e}")
        return ""

def start_listening(callback=None):
    def listen_loop():
        global LISTENING
        p = pyaudio.PyAudio()

        try:
            stream = p.open(format=AUDIO_FORMAT,
                            channels=CHANNELS,
                            rate=SAMPLE_RATE,
                            input=True,
                            frames_per_buffer=CHUNK)
        except Exception as e:
            print(f"[❌ Mic open failed]: {e}")
            return

        print("[🎤 Listening using default microphone...]")

        while LISTENING:
            frames = []
            for _ in range(0, int(SAMPLE_RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

            wav_path = "temp.wav"
            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(AUDIO_FORMAT))
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(b"".join(frames))

            text = transcribe_with_whisper_cpp(wav_path)
            print(f"[🗣 Heard]: {text}")

            if any(word in text for word in WAKE_WORDS):
                command = re.sub(r"^(hey\s+)?hostess[, ]*", "", text)
                print(f"[🤖 Wake word detected]: {command}")
                if command:
                    if callback:
                        callback(command)

    thread = threading.Thread(target=listen_loop, daemon=True)
    thread.start()


def stop_listening():
    global LISTENING
    LISTENING = False
    