import sys
import threading
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QLineEdit, QPushButton,
    QVBoxLayout, QWidget
)

from speech_listener import start_listening, stop_listening

LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

def load_system_prompt(path="prompt.txt"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {"role": "system", "content": f.read()}
    except Exception:
        return {"role": "system", "content": "You are a helpful assistant."}

SYSTEM_PROMPT = load_system_prompt()

class HostessApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hostess AI")
        self.setGeometry(100, 100, 700, 550)

        self.is_listening = False

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)

        self.input_box = QLineEdit()
        self.input_box.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        self.listen_button = QPushButton("🎤 Start Listening")
        self.listen_button.clicked.connect(self.toggle_listening)

        layout = QVBoxLayout()
        layout.addWidget(self.chat_display)
        layout.addWidget(self.input_box)
        layout.addWidget(self.send_button)
        layout.addWidget(self.listen_button)

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

    def toggle_listening(self):
        if self.is_listening:
            stop_listening()
            self.listen_button.setText("🎤 Start Listening")
            self.is_listening = False
        else:
            threading.Thread(target=start_listening, args=(self.handle_voice_command,), daemon=True).start()
            self.listen_button.setText("🛑 Stop Listening")
            self.is_listening = True

def run_app():
    app = QApplication(sys.argv)
    window = HostessApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_app()
