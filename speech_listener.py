import pyaudio
import wave
import threading
import subprocess
import os
import re
import requests
import audioop

WAKE_WORDS = ["hostess", "hey hostess"]
RECORD_SECONDS = 1
SAMPLE_RATE = 16000
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
CHUNK = 1024
MODEL_PATH = "models/whisper-large-v3-f16.gguf"  # Set your model path here
WHISPER_BIN = os.path.abspath("bin/whisper/whisper-cli.exe")

LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

SILENCE_SECONDS = 1  # How long to wait before considering it silence
SILENCE_THRESHOLD = 500  # Adjust this value for your mic/environment

LISTENING = False  # Start as not listening

def transcribe_with_whisper_cpp(wav_path: str) -> str:
    txt_path = wav_path + ".txt"
    # Remove previous transcript if exists
    if os.path.exists(txt_path):
        os.remove(txt_path)
    try:
        result = subprocess.run([
            WHISPER_BIN,
            "-m", MODEL_PATH,
            "-f", wav_path,
            "-l", "en",
            "-otxt",
            "-nt"
        ], capture_output=True, text=True)

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

def process_audio_and_transcribe(frames, callback):
    wav_path = "temp.wav"
    # Overwrite temp.wav if it exists
    if os.path.exists(wav_path):
        os.remove(wav_path)
    try:
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(AUDIO_FORMAT))
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b"".join(frames))
    except Exception as e:
        print(f"[❌ Failed to save audio]: {e}")
        return

    # Transcribe in this thread
    text = transcribe_with_whisper_cpp(wav_path)
    print(f"[🗣 Heard]: {text}")
    if text.strip() and callback:
        callback(text.strip())

def start_listening(callback=None):
    global LISTENING
    LISTENING = True

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
        all_frames = []
        silence_chunks = 0
        max_silence_chunks = int(SAMPLE_RATE / CHUNK * SILENCE_SECONDS)

        while LISTENING:
            data = stream.read(CHUNK, exception_on_overflow=False)
            all_frames.append(data)
            rms = audioop.rms(data, 2)  # 2 bytes per sample

            if rms < SILENCE_THRESHOLD:
                silence_chunks += 1
            else:
                silence_chunks = 0  # Reset on speech

            if silence_chunks > max_silence_chunks:
                # Stop listening after silence
                break

        stream.stop_stream()
        stream.close()
        p.terminate()
        LISTENING = False

        # Process all collected frames as one utterance
        if all_frames:
            process_audio_and_transcribe(all_frames, callback)

    thread = threading.Thread(target=listen_loop, daemon=True)
    thread.start()

def stop_listening(callback=None):
    global LISTENING
    LISTENING = False
    # No need to handle anything here, as silence will trigger callback