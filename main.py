import sys
import threading
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QLineEdit, QPushButton,
    QVBoxLayout, QWidget, QLabel, QComboBox
)
from PyQt6.QtCore import Qt

from speech_listener import get_input_devices, start_listening

LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

def load_system_prompt(path="prompt.txt"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {"role": "system", "content": f.read()}
    except Exception as e:
        print(f"Error loading system prompt: {e}")
        return {"role": "system", "content": "You are a helpful assistant."}

SYSTEM_PROMPT = load_system_prompt()

class HostessApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hostess AI")
        self.setGeometry(100, 100, 700, 550)

        # --- Chat Display ---
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)

        self.input_box = QLineEdit()
        self.input_box.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        # --- Microphone Selector ---
        self.device_label = QLabel("🎤 Microphone:")
        self.device_dropdown = QComboBox()
        self.devices = get_input_devices()
        for idx, name in self.devices:
            self.device_dropdown.addItem(name, userData=idx)

        self.listen_button = QPushButton("Start Listening")
        self.listen_button.clicked.connect(self.start_listening_thread)

        # --- Layout ---
        layout = QVBoxLayout()
        layout.addWidget(self.device_label)
        layout.addWidget(self.device_dropdown)
        layout.addWidget(self.listen_button)
        layout.addWidget(self.chat_display)
        layout.addWidget(self.input_box)
        layout.addWidget(self.send_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def add_message(self, sender, message):
        self.chat_display.append(f"<b>{sender}:</b> {message}")

    def send_message(self):
        user_msg = self.input_box.text().strip()
        if not user_msg:
            return

        self.add_message("You", user_msg)
        self.input_box.clear()

        payload = {
            "model": "your-model-name-here",
            "messages": [SYSTEM_PROMPT, {"role": "user", "content": user_msg}],
            "temperature": 0.8
        }

        def call_and_display():
            try:
                response = requests.post(LM_STUDIO_API_URL, json=payload)
                reply = response.json()["choices"][0]["message"]["content"]
                self.add_message("Hostess", reply)
            except Exception as e:
                self.add_message("Error", f"Hostess had a meltdown: {str(e)}")

        threading.Thread(target=call_and_display).start()

    def handle_voice_command(self, message):
        self.add_message("🎤 Voice", message)
        self.input_box.setText(message)
        self.send_message()

    def start_listening_thread(self):
        mic_index = self.device_dropdown.currentData()
        print(f"[🔊 Using mic index: {mic_index}]")

        def threaded_listen():
            start_listening(callback=self.handle_voice_command, mic_index=mic_index)

        threading.Thread(target=threaded_listen, daemon=True).start()
        self.listen_button.setEnabled(False)
        self.listen_button.setText("🎤 Listening...")

def run_app():
    app = QApplication(sys.argv)
    window = HostessApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()
