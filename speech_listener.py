import whisper
import pyaudio
import wave
import io
import numpy as np
import threading
import re
import requests
import tempfile
from whisper.audio import load_audio


# Constants
WAKE_WORDS = ["hostess", "hey hostess"]
RECORD_SECONDS = 5
MODEL = whisper.load_model("base")
# Replace with your actual chat endpoint
# This should point to your Flask server or LM Studio API
CHAT_ENDPOINT = "http://localhost:5000/chat"

def transcribe_audio():
    p = pyaudio.PyAudio()
    DEVICE_INDEX = 4  # <-- Replace with your desired device index
    device_info = p.get_device_info_by_index(mic_index)
    print(f"[🔍 Opening mic index {mic_index}] {device_info['name']}")
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    frames_per_buffer=1024,
                    input_device_index=DEVICE_INDEX)

    print("[Listening for 'Hostess' or 'Hey Hostess'...]")

    while True:
        frames = []
        for _ in range(0, int(16000 / 1024 * RECORD_SECONDS)):
            data = stream.read(1024)
            frames.append(data)

        audio = b"".join(frames)

        # Write to a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
            tmpfile_path = tmpfile.name
        try:
            with wave.open(tmpfile_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)
                wf.writeframes(audio)
            result = MODEL.transcribe(tmpfile_path)
        finally:
            import os
            if os.path.exists(tmpfile_path):
                os.remove(tmpfile_path)

        text = result["text"].lower().strip()
        print(f"[Heard]: {text}")

        if any(word in text for word in WAKE_WORDS):
            command = re.sub(r"^(hey\s+)?hostess[, ]*", "", text)
            print(f"[Command Detected]: {command}")
            if command:
                send_to_chat(command)

def send_to_chat(text):
    try:
        print(f"[Sending to Hostess]: {text}")
        response = requests.post(CHAT_ENDPOINT, json={"message": text})
        print(f"[Response]: {response.json().get('response')}")
    except Exception as e:
        print(f"[Error]: {e}")

def start_listening(callback=None, mic_index=0):
    def listen_loop():
        p = pyaudio.PyAudio()

        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get('maxInputChannels') > 0:
                print(f"[🎙 Device {i}]: {info['name']}")

        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        input_device_index=mic_index,
                        frames_per_buffer=1024)

        print("[🎤 Listening for 'Hostess' or 'Hey Hostess'...]")

        while True:
            frames = []
            for _ in range(0, int(16000 / 1024 * RECORD_SECONDS)):
                data = stream.read(1024)
                frames.append(data)

            # Convert raw audio bytes to a NumPy array
            raw_audio = b"".join(frames)
            audio_np = np.frombuffer(raw_audio, np.int16).astype(np.float32) / 32768.0

            try:
                result = MODEL.transcribe(audio_np)
                text = result["text"].lower().strip()
                print(f"[🗣 Heard]: {text}")

                if any(word in text for word in WAKE_WORDS):
                    command = re.sub(r"^(hey\s+)?hostess[, ]*", "", text)
                    print(f"[🤖 Triggered Command]: {command}")
                    if command and callback:
                        callback(command)
            except Exception as e:
                print(f"[❌ Whisper Error]: {e}")

    thread = threading.Thread(target=listen_loop)
    thread.daemon = True
    thread.start()

def get_input_devices():
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info.get('maxInputChannels') > 0:
            devices.append((i, info['name']))
    return devices

def list_input_devices():
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            print(f"Index {i}: {info['name']}")
    p.terminate()

list_input_devices()
