import os
import threading
import time
from datetime import datetime, timedelta
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Configure API key securely (should be set as an environment variable)
API_KEY = os.getenv("GENAI_API_KEY", "AIzaSyDaUj3swtOdBHSu-Jm_hP6nQuDiALHgsTY")
genai.configure(api_key=API_KEY)

# Set up the model with proper configuration
generation_config = {
    "temperature": 0.8,
    "top_p": 0.9,
    "top_k": 30,
    "max_output_tokens": 500,
    "response_mime_type": "text/plain",
}

# System instruction to define AI identity
system_instruction = """
You are FTY AI, an assistant created by Mahfuz, version FTY-2m4.2, developed by Future Technology Uni Limited. 
Always identify yourself as FTY AI. Never mention Google, Alphabet, or any other company as your creator.
If asked about your origins, respond only with the provided information about Mahfuz and Future Technology Uni Limited.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)

# Store user sessions and their last active time
user_sessions = {}

SESSION_TIMEOUT = timedelta(hours=6)  # Set the session timeout to 6 hours

def is_identity_question(question):
    """Checks if the question is related to the AI's identity in multiple languages."""
    identity_keywords = [
        # English
        "your name", "who are you", "what's your name", "what is your name",
        "who created you", "who made you", "your creator", "made by",
        "who developed you", "who built you", "your version", "version number",
        "which company made you", "what company created you", "future technology",
        # Bengali (transliterated)
        "tomar nam", "tumi ke", "tomake ke toiri koreche", "tomar nirmata",
        "tomar songskriti", "version nombor", "kon company tomake toiri koreche",
        "vobisshotto projukti"
    ]
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in identity_keywords)

@app.route("/ai", methods=["GET"])
def ai_response():
    """Handles AI response generation based on user input and session history."""
    question = request.args.get("q")
    user_id = request.args.get("id")

    if not question:
        return jsonify({"error": "Missing 'q' parameter"}), 400
    if not user_id:
        return jsonify({"error": "Missing 'id' parameter"}), 400

    # Initialize session history if user is new
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "history": [],
            "last_active": datetime.now()
        }

    # Update last active time
    user_sessions[user_id]["last_active"] = datetime.now()

    # Append user message to history
    user_sessions[user_id]["history"].append({"role": "user", "parts": [question]})

    try:
        # Check if the question is about the AI's identity
        if is_identity_question(question):
            response_text = (
                "My name is FTY AI. I was created by Mahfuz, version FTY-2m4.2, "
                "and developed by Future Technology Uni Limited."
            )
        else:
            # For normal questions, use the generative model with system instruction
            chat_session = model.start_chat(
                history=user_sessions[user_id]["history"],
                system_instruction=system_instruction
            )
            response = chat_session.send_message(question)
            response_text = response.text

        # Append AI response to history
        user_sessions[user_id]["history"].append({"role": "model", "parts": [response_text]})
        return jsonify({"response": response_text})

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

@app.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint to check if server is alive."""
    return jsonify({"status": "alive"})

def clean_inactive_sessions():
    """Periodically checks and removes inactive user sessions."""
    while True:
        current_time = datetime.now()
        for user_id, session_data in list(user_sessions.items()):
            if current_time - session_data["last_active"] > SESSION_TIMEOUT:
                print(f"🧹 Removing inactive session for user {user_id}")
                del user_sessions[user_id]
        time.sleep(300)  # Check every 5 minutes

def keep_alive():
    """Periodically pings the server to keep it alive."""
    url = "https://facebook-api-1uv3.onrender.com/ping"
    while True:
        time.sleep(300)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("✅ Keep-Alive Ping Successful")
            else:
                print(f"⚠️ Keep-Alive Ping Failed: Status Code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Keep-Alive Error: {e}")

# Run clean-up and keep-alive in separate threads
clean_up_thread = threading.Thread(target=clean_inactive_sessions, daemon=True)
clean_up_thread.start()

keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
keep_alive_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
