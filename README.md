# 🚀 LMS Portal

A "modern" frontend for LM Studio, featuring integrated internet search and voice input via Whisper.

---

## ✨ Features

- **Internet Search:** Seamlessly search the web from within the portal.
- **Whisper Voice Input:** Use your voice to interact (supported in Chrome and Edge).
- **Easy Model Finetuning:** Just edit `prompt.txt` to customize your model's behavior.

---

## 🛠️ Getting Started

1. **Launch LM Studio** with your preferred model loaded.
2. **Customize** your model by editing or creating a `prompt.txt` file.
3. Add your whisperCPP binary in `bin/whisper/whisper-cli.exe`
4. Add your whisper model in `models/whisper-model.gguf`
5. **Run the Portal:**
   ```sh
   python main.py
   ```
   > Requires Python 3.11.3

---

## 💡 Notes

- For the best experience, use the latest version of Chrome or Edge for voice input.
- Make sure LM Studio is running before starting the portal.

---

## 📬 Feedback & Contributions

Feel free to open issues or submit pull requests to help improve LMS Portal!
