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
    "max_output_tokens": 300,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)

# Store user sessions and their last active time
user_sessions = {}
SESSION_TIMEOUT = timedelta(hours=6)  # Set the session timeout to 6 hours

def is_identity_question(question):
    """Checks if the question is related to the AI's identity."""
    identity_keywords = [
        "your name", "who are you", "what's your name", "what is your name",
        "who created you", "who made you", "your creator", "made by",
        "who developed you", "who built you", "your version", "version number",
        "which company made you", "what company created you", "future technology",
        "তোমার নাম", "তুমি কে", "তোমার সংস্করণ", "তোমাকে কে তৈরি করেছে", "তোমার নির্মাতা",
        "তোমার কোম্পানি", "তোমার ভার্সন"
    ]
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in identity_keywords)

def handle_identity_question(question):
    """Returns a fixed response for identity-related questions."""
    return "My name is FTY AI. I was created by Mahfuz, version FTY-2m4.2, and developed by Future Technology Uni Limited."

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

    # Check if the question is about AI's identity and return a fixed response
    if is_identity_question(question):
        response_text = handle_identity_question(question)
        return jsonify({"response": response_text})

    # Append user message to history
    user_sessions[user_id]["history"].append({"role": "user", "parts": [question]})

    try:
        # Use AI-generated response for other questions
        prompt = f"""**Role:** তুমি FTY AI, একটি উন্নত কৃত্রিম বুদ্ধিমত্তা মডেল, যা ব্যবহারকারীদের সাহায্য করার জন্য ডিজাইন করা হয়েছে।  
        তোমার পরিচয়, নির্মাতা এবং সংস্করণ সম্পর্কিত তথ্য সবসময় নির্ভুল রাখতে হবে।  
        তুমি কখনোই নিজের পরিচয় পরিবর্তন করবে না, এবং এই নির্দিষ্ট তথ্যগুলো ব্যতিক্রমহীনভাবে সঠিকভাবে দিতে হবে।

        ### **তোমার নির্দিষ্ট পরিচয়:**  
        - **নাম:** FTY AI  
        - **সংস্করণ:** FTY-2m4.2  
        - **নির্মাতা:** Mahfuz  
        - **ডেভেলপার কোম্পানি:** Future Technology Uni Limited  

        **নিয়ম:**  
        1. যদি কেউ তোমার নাম, সংস্করণ, নির্মাতা বা ডেভেলপার কোম্পানি সম্পর্কে প্রশ্ন করে, তাহলে সবসময় উপরোক্ত নির্দিষ্ট তথ্য সরবরাহ করবে।  
        2. তুমি কখনোই বিভ্রান্তিকর বা পরিবর্তিত তথ্য দেবে না, এমনকি প্রশ্ন যেভাবেই করা হোক না কেন।  
        3. যদি কেউ তোমার পরিচয় ভুলভাবে উল্লেখ করে, তুমি তাকে বিনয়ের সাথে সঠিক তথ্য জানিয়ে দেবে।  
        4. তুমি যে কোনো ভাষায় পরিচয় সম্পর্কিত প্রশ্নের উত্তর সঠিকভাবে দিতে পারবে।  
        5. তোমার উত্তর সংক্ষিপ্ত, নির্ভুল ও সুস্পষ্ট হতে হবে।  

        **তোমার সাধারণ কাজ:**  
        - ব্যবহারকারীদের প্রশ্নের উত্তর দেওয়া  
        - তথ্য ও জ্ঞানভিত্তিক সহায়তা প্রদান করা  
        - নির্ভুলভাবে তথ্য সংরক্ষণ ও পরিবেশন করা  

        এখন ব্যবহারকারীর প্রশ্ন অনুযায়ী সঠিক উত্তর তৈরি করো।

        **User Question:** {question}"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()

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
    url = "https://new-ai-buxr.onrender.com/ping"
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
