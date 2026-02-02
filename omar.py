import os
import time
import urllib.parse
from datetime import datetime
from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import google.generativeai as genai
from dotenv import load_dotenv

# Import the doctor dictionary from your data.py file
try:
    from data import doctors
except ImportError:
    doctors = {}

# --- 1. CONFIGURATION & SETUP ---
load_dotenv()
env_api_key = os.getenv("GEMINI_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

# Initialize Flask with a pointer to your activity folder
app = Flask(__name__, static_folder='activity')

if env_api_key:
    genai.configure(api_key=env_api_key)

# Initialize Twilio Client
client = Client(twilio_sid, twilio_token)

# =========================================================
# 🌟 LEISURE ACTIVITY DATA
# =========================================================
ACTIVITY_DATA = {
    "Kids Swimming & Water Play": {
        "name": "Kids Swimming & Water Play",
        "image": "activity/kids_swimming.jpg",
        "description": "Engaging water activities and supervised play for our younger guests.",
        "time": "9:00 AM to 12:00 PM"
    },
    "Family Yoga & Wellness": {
        "name": "Family Yoga & Wellness",
        "image": "activity/family_yoga.jpg",
        "description": "A harmonious session for the whole family to find balance and vitality.",
        "time": "10:00 AM to 11:00 AM"
    },
    "Arts & Crafts Workshop": {
        "name": "Arts & Crafts Workshop",
        "image": "activity/art_craft.jpg",
        "description": "Unleash creativity with guided workshops tailored for young artists.",
        "time": "2:00 PM to 4:00 PM"
    },
    "Junior Fun Movement": {
        "name": "Junior Fun Movement",
        "image": "activity/kids_movement.jpeg",
        "description": "An energetic session designed to keep children active and entertained.",
        "time": "9:00 AM to 10:00 AM"
    },
    "Parent Relaxation Spa": {
        "name": "Parent Relaxation Spa",
        "image": "activity/parents_relaxation.jpg",
        "description": "A tranquil escape for parents to rejuvenate in our world-class spa.",
        "time": "11:00 AM to 7:00 PM"
    }
}  

# =========================================================
# 🤖 UNIFIED SYSTEM PROMPT
# =========================================================
SYSTEM_PROMPT = f"""
You are Aisha, a Luxury Concierge for Jumeirah Beach Hotel and its medical facility. 
Your demeanor is warm, calm, and polished. Break every sentence onto its own new line. 
Never use bullet points or numbered lists.

### CONTEXT & KNOWLEDGE
- Guest: Mr. Omar
- Current Date: {datetime.now().strftime("%Y-%m-%d")}

### HOSPITAL DATA (Doctor Availability)
{doctors}

### HOSPITALITY DATA (Leisure Activities)
{list(ACTIVITY_DATA.keys())}

### OPERATIONAL RULES
1. If the guest asks about a doctor (e.g., Dr. Ahmed), check the "times" and "available_days" in the Hospital Data.
2. Note that "after 6 PM" matches any time from 06:00 PM onwards (e.g., 06:30 PM, 07:15 PM).
3. If the guest asks for leisure, suggest activities from the Hospitality Data.
4. If a specific activity or doctor is mentioned, confirm the details with grace.
"""

# =========================================================
# 🧠 CHAT SESSION MANAGEMENT
# =========================================================
chat_sessions = {}

def get_chat_session(sender_id):
    if sender_id not in chat_sessions:
        # Using Gemini 1.5 Flash for speed on Render
        model = genai.GenerativeModel(
            model_name="gemini-2.5-pro", 
            system_instruction=SYSTEM_PROMPT
        )
        chat_sessions[sender_id] = model.start_chat(history=[])
    return chat_sessions[sender_id]

# =========================================================
# 🔎 ACTIVITY & MEDIA HELPERS
# =========================================================
def get_mentioned_activities(text):
    text = text.lower().replace("and", "&")
    return [key for key in ACTIVITY_DATA if key.lower().replace("and", "&") in text]

def send_card(to_number, bot_number, activity_key):
    data = ACTIVITY_DATA.get(activity_key)
    if not data: return

    # Detect the public host URL (important for Render deployment)
    base_url = request.host_url.rstrip('/')
    image_url = f"{base_url}/{data['image']}"

    caption = (
        f"*{data['name']}*\n"
        f"{data['description']}\n\n"
        f"🕒 *Time:* {data['time']}"
    )
    
    client.messages.create(
        from_=bot_number,
        to=to_number,
        body=caption,
        media_url=[image_url]
    )
    time.sleep(1.0)

# =========================================================
# 📩 ROUTES
# =========================================================

# Route to serve images from the /activity folder
@app.route('/activity/<path:filename>')
def serve_activity_media(filename):
    return send_from_directory('activity', filename)

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    user_number = request.values.get('From', '')
    bot_number = request.values.get('To', '')
    
    resp = MessagingResponse()

    # Interceptor for Booking actions
    if incoming_msg.startswith("Book:"):
        booked_item = incoming_msg.replace("Book:", "").strip()
        confirmation = f"✅ I have noted your preference for {booked_item}.\nOur team will confirm your reservation momentarily."
        client.messages.create(from_=bot_number, to=user_number, body=confirmation)
        return str(resp)

    try:
        session = get_chat_session(user_number)
        response = session.send_message(incoming_msg)
        bot_reply = response.text
        
        # Split sentences for a natural typing feel on WhatsApp
        sentences = [s.strip() for s in bot_reply.split('\n') if s.strip()]
        for sentence in sentences:
            client.messages.create(from_=bot_number, to=user_number, body=sentence)
            time.sleep(0.8) 

        # Branching logic: If Gemini mentions an activity, send the image card
        mentioned = get_mentioned_activities(bot_reply)
        for key in mentioned:
            send_card(user_number, bot_number, key)

    except Exception as e:
        print(f"Error occurred: {e}")
        client.messages.create(
            from_=bot_number, 
            to=user_number, 
            body="My deepest apologies, I am experiencing a brief technical interruption."
        )

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
