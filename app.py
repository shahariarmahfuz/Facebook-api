import os
import threading
import time
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Configure API key
API_KEY = os.getenv("GENAI_API_KEY", "AIzaSyDaUj3swtOdBHSu-Jm_hP6nQuDiALHgsTY")
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-2.0-flash')

# কোম্পানি ও AI সম্পর্কিত ডিটেলস
COMPANY_PROFILE = {
    "name": "Habib Corporation Ltd",
    "foundation": "2025",
    "specialization": "Advanced AI Development",
    "current_focus": "Generative AI Innovations",
    "vision": "Democratizing AI for everyone",
    "version": "2.6"
}

AI_IDENTITY = f"""
You are Habib AI (Version {COMPANY_PROFILE['version']}), developed by {COMPANY_PROFILE['name']}. 
Our company specializes in:
- Building OpenAI-like AI systems
- Developing cutting-edge generative models
- Researching AGI (Artificial General Intelligence)
- Creating ethical AI solutions

Current Focus: {COMPANY_PROFILE['current_focus']}
Company Vision: {COMPANY_PROFILE['vision']}
"""

@app.route("/ask", methods=["GET"])
def ask_ai():
    user_id = request.args.get("id")
    question = request.args.get("q")

    if not user_id or not question:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        prompt = f"{AI_IDENTITY}\n\nUser Query: {question}"
        response = model.generate_content(prompt)
        return jsonify({"response": response.text})

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
