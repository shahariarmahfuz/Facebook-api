import os
import threading
import time
from datetime import datetime, timedelta
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai
from google.generativeai import types

app = Flask(__name__)

# Configure API key securely (should be set as environment variable)
API_KEY = os.getenv("GENAI_API_KEY", "AIzaSyDaUj3swtOdBHSu-Jm_hP6nQuDiALHgsTY")
genai.configure(api_key=API_KEY)

# Set up model with initial training data
INITIAL_HISTORY = [
    {
        "role": "user",
        "parts": ["Who are you?"]
    },
    {
        "role": "model", 
        "parts": ["I am Echo, created by Shahariar Mahfuz from Evolving Intelligence. I'm an AI assistant specialized in natural conversation."]
    }
]

generation_config = {
    "temperature": 0.8,
    "top_p": 0.9,
    "top_k": 30,
    "max_output_tokens": 600,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)

user_sessions = {}
SESSION_TIMEOUT = timedelta(hours=72)

def is_identity_question(question):
    """Enhanced identity detection with more keywords"""
    identity_keywords = [
        "your name", "who are you", "what's your name", "what is your name",
        "who created you", "who made you", "your creator", "made by",
        "who developed you", "who built you", "your version", "version number",
        "which company made you", "what company created you", "future technology",
        "who designed you", "are you human", "are you ai", "what are you",
        "tell me about yourself"
    ]
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in identity_keywords)

@app.route("/ai", methods=["GET"])
def ai_response():
    question = request.args.get("q")
    user_id = request.args.get("id")

    if not question:
        return jsonify({"error": "Missing 'q' parameter"}), 400
    if not user_id:
        return jsonify({"error": "Missing 'id' parameter"}), 400

    # Initialize session with predefined history
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "history": INITIAL_HISTORY.copy(),
            "last_active": datetime.now()
        }

    user_sessions[user_id]["last_active"] = datetime.now()
    user_sessions[user_id]["history"].append({"role": "user", "parts": [question]})

    try:
        if is_identity_question(question):
            # Enhanced identity responses
            if any(k in question.lower() for k in ["your name", "who are you"]):
                response_text = "My name is Echo, a conversational AI developed by Evolving Intelligence."
            elif "creator" in question.lower() or "made you" in question.lower():
                response_text = "I was created by Shahariar Mahfuz, lead AI engineer at Evolving Intelligence."
            elif "company" in question.lower():
                response_text = "I'm developed and maintained by Evolving Intelligence, an AI research company."
            else:
                response_text = "I'm Echo, an AI assistant created by Shahariar Mahfuz at Evolving Intelligence (version Echo-2m4.2)."
        else:
            chat_session = model.start_chat(history=user_sessions[user_id]["history"])
            response = chat_session.send_message(question)
            response_text = response.text

        user_sessions[user_id]["history"].append({"role": "model", "parts": [response_text]})
        return jsonify({"response": response_text})

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

# RapidAPI তথ্য
RAPIDAPI_HOST = "facebook-reel-and-video-downloader.p.rapidapi.com"
RAPIDAPI_KEY = "d4cc664bddmshad58db8819652d6p19e7adjsn6bcd66d66ef4"

def fetch_video_links(fb_url):
    """RapidAPI থেকে ভিডিও লিংক বের করা (শুধুমাত্র পাওয়া লিংকগুলো রিটার্ন করা)"""
    url = f"https://{RAPIDAPI_HOST}/app/main.php?url={fb_url}"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        links = data.get("links", {})
        
        result = {}
        # HD লিংক চেক করা
        if "Download High Quality" in links:
            result["hd_url"] = links["Download High Quality"]
        
        # SD লিংক চেক করা
        if "Download Low Quality" in links:
            result["sd_url"] = links["Download Low Quality"]
        
        return result if result else None
    return None

@app.route("/fb", methods=["GET"])
def get_video_links():
    """ফেসবুক ভিডিওর পাওয়া লিংকগুলো রিটার্ন করা"""
    fb_url = request.args.get("link")
    if not fb_url:
        return jsonify({"error": "লিংক প্রদান করুন"}), 400

    video_links = fetch_video_links(fb_url)
    
    if video_links:
        return jsonify({
            "status": "success",
            "links": video_links
        })
    else:
        return jsonify({"error": "কোন ভিডিও লিংক পাওয়া যায়নি"}), 404

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "alive", "timestamp": datetime.now().isoformat()})

def clean_inactive_sessions():
    while True:
        current_time = datetime.now()
        for user_id in list(user_sessions.keys()):
            if current_time - user_sessions[user_id]["last_active"] > SESSION_TIMEOUT:
                del user_sessions[user_id]
        time.sleep(300)

def keep_alive():
    # Update this URL to your actual deployment URL
    DEPLOYMENT_URL = "https://facebook-api-1uv3.onrender.com/ping"  
    while True:
        time.sleep(300)
        try:
            requests.get(DEPLOYMENT_URL)
            print("Keep-alive ping successful")
        except Exception as e:
            print(f"Keep-alive error: {str(e)}")

if __name__ == "__main__":
    threading.Thread(target=clean_inactive_sessions, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
