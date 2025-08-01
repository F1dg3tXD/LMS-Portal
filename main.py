
import sys
import threading
import asyncio
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QLineEdit, QPushButton,
    QVBoxLayout, QWidget
)
from PyQt6.QtCore import QTimer
from speech_listener import start_listening, stop_listening
from utils import search_duckduckgo, load_memory, save_to_memory  # <-- Make sure this is imported
from voice import speak  # <-- Import the speak function
from langchain_core.messages import messages_to_dict

LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

# Global event loop reference
async_loop = asyncio.new_event_loop()

def start_async_loop():
    asyncio.set_event_loop(async_loop)
    async_loop.run_forever()

# Start this once when your app launches
threading.Thread(target=start_async_loop, daemon=True).start()

def run_in_async_loop(coro):
    """Thread-safe way to schedule a coroutine from any thread"""
    asyncio.run_coroutine_threadsafe(coro, async_loop)

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
        
    def sanitize_messages(self, msgs):
        sanitized = []
        for m in msgs:
            if isinstance(m, dict) and "role" in m and "content" in m:
                if isinstance(m["role"], str) and isinstance(m["content"], str):
                    sanitized.append({"role": m["role"], "content": m["content"]})
                else:
                    print(f"[WARN] Skipping message with invalid types: {m}")
            else:
                print(f"[WARN] Skipping invalid message format: {m}")
        return sanitized

    def send_message(self):
        user_msg = self.input_box.text().strip()
        if not user_msg:
            return

        self.add_message("You", user_msg)
        self.input_box.clear()

        if user_msg.lower().startswith("search:"):
            query = user_msg[7:].strip()
            self.add_message("Hostess", "Searching DuckDuckGo...")
            threading.Thread(target=self.perform_search, args=(query,), daemon=True).start()
            return

        try:
            history = load_memory()
            messages = messages_to_dict(history)
        except Exception as e:
            print("[DEBUG] Error loading/converting memory:", e)
            messages = []

        messages = self.sanitize_messages(messages)

        messages = [SYSTEM_PROMPT] + messages + [{"role": "user", "content": user_msg}]

        print("[DEBUG] Final messages payload:")
        for i, msg in enumerate(messages):
            print(f" {i}: role={msg.get('role')} content={repr(msg.get('content'))}")

        payload = {
            "model": "your-model-name-here",
            "messages": messages,
            "temperature": 0.8
        }

        def call_and_display():
            try:
                response = requests.post(LM_STUDIO_API_URL, json=payload)
                data = response.json()
                print("[DEBUG] Raw response:", data)

                if "choices" not in data or not data["choices"]:
                    raise ValueError(f"Unexpected response format from LM Studio: {data}")

                reply = data["choices"][0]["message"]["content"]

                # Check if LLM is requesting a search
                if reply.strip().lower().startswith("search:"):
                    search_query = reply.split("search:", 1)[1].strip()
                    QTimer.singleShot(0, lambda: self.add_message("Hostess", "Searching the web..."))
                    search_result = search_duckduckgo(search_query)

                    followup_payload = {
                        "model": "your-model-name-here",
                        "messages": [
                            SYSTEM_PROMPT,
                            {"role": "user", "content": user_msg},
                            {"role": "assistant", "content": reply},
                            {"role": "system", "content": f"Search result: {search_result}\n\nPlease answer the user's original question using the search result above."}
                        ],
                        "temperature": 0.8
                    }

                    followup_response = requests.post(LM_STUDIO_API_URL, json=followup_payload)
                    followup_data = followup_response.json()
                    print("[DEBUG] Follow-up raw response:", followup_data)

                    if "choices" not in followup_data or not followup_data["choices"]:
                        raise ValueError(f"Unexpected follow-up response format: {followup_data}")

                    followup_reply = followup_data["choices"][0]["message"]["content"]

                    if followup_reply.strip():
                        self.add_message("Hostess", followup_reply)
                        save_to_memory(user_msg, followup_reply)
                        run_in_async_loop(speak(followup_reply, voice="en-GB-SoniaNeural"))
                    else:
                        self.add_message("Hostess", "Sorry, I couldn't find an answer.")
                        run_in_async_loop(speak("Sorry, I couldn't find an answer.", voice="en-GB-SoniaNeural"))
                else:
                    self.add_message("Hostess", reply)
                    save_to_memory(user_msg, reply)
                    run_in_async_loop(speak(reply, voice="en-GB-SoniaNeural"))

            except Exception as e:
                self.add_message("Error", f"Hostess had a meltdown: {str(e)}")
                run_in_async_loop(speak(f"Hostess had a meltdown: {str(e)}", voice="en-GB-SoniaNeural"))

        threading.Thread(target=call_and_display).start()


    def perform_search(self, query):
        # This runs in a separate thread
        result = search_duckduckgo(query)
        # Schedule the UI update on the main thread
        def update_ui():
            self.add_message("🔍 Search Result", result)
        QTimer.singleShot(0, update_ui)

    def handle_voice_command(self, message):
        self.add_message("🎤 Voice", message)
        self.input_box.setText(message)
        self.send_message()

    def toggle_listening(self):
        if self.is_listening:
            stop_listening(callback=self.handle_voice_command)
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