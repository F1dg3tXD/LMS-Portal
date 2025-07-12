from flask import Flask, render_template, request, jsonify
import requests
from utils import search_duckduckgo

app = Flask(__name__)

LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"

def load_system_prompt(path="prompt.txt"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return {"role": "system", "content": f.read()}
    except Exception as e:
        print(f"Error loading system prompt: {e}")
        return {"role": "system", "content": "You are a helpful assistant."}

# Replace with your system prompt (can load from file too)
SYSTEM_PROMPT = load_system_prompt()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")

    # Handle internet command: "search:"
    if user_msg.lower().startswith("search:"):
        query = user_msg[7:].strip()
        results = search_duckduckgo(query)
        return jsonify({"response": results})

    # Send to LM Studio
    payload = {
        "model": "your-model-name-here",  # replace or ignore if using default
        "messages": [SYSTEM_PROMPT, {"role": "user", "content": user_msg}],
        "temperature": 0.8
    }

    try:
        response = requests.post(LM_STUDIO_API_URL, json=payload)
        reply = response.json()["choices"][0]["message"]["content"]
        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"response": f"Hostess had a meltdown: {str(e)}"})

def start_flask():
    from waitress import serve  # or use app.run() for dev
    serve(app, host="127.0.0.1", port=5000)
