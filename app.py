import os
import threading
import time
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Configure API key
API_KEY = os.getenv("GENAI_API_KEY", "AIzaSyDaUj3swtOdBHSu-Jm_hP6nQuDiALHgsTY")
genai.configure(api_key=API_KEY)

# জেনারিক মডেল সেটআপ
model = genai.GenerativeModel('gemini-pro')

# ইউজার সেশন ম্যানেজমেন্ট (সরল ভার্সন)
user_sessions = {}

@app.route("/ask", methods=["GET"])
def ask_ai():
    user_id = request.args.get("id")
    question = request.args.get("q")

    if not user_id or not question:
        return jsonify({"error": "Missing parameters"}), 400

    # সেশন ম্যানেজমেন্ট
    if user_id not in user_sessions:
        user_sessions[user_id] = {"history": []}

    # আইডেন্টিটি প্রম্পট (কোন ভাষা জোরাজুরি নেই)
    identity = "You are Habib AI, created by Mahfuz at Habib Corporation Ltd on March 23, 2025. Respond naturally like a standard AI assistant."

    try:
        # জেনারিক রেসপন্স জেনারেট
        response = model.generate_content(f"{identity}\n\nUser: {question}")
        
        return jsonify({
            "response": response.text,
            "meta": {
                "ai": "Habib AI",
                "created": "2025-03-23",
                "developer": "Habib Corporation Ltd"
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "active"})

def keep_alive():
    while True:
        time.sleep(300)
        try: requests.get("https://your-app-url/ping")
        except: pass

threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
