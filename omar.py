import os
import time
import urllib.parse
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import google.generativeai as genai
from dotenv import load_dotenv

# --- 1. CONFIGURATION & SETUP ---
load_dotenv()
env_api_key = os.getenv("GEMINI_API_KEY")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

app = Flask(__name__)

if env_api_key:
    genai.configure(api_key=env_api_key)

# Initialize Twilio REST Client
client = Client(twilio_sid, twilio_token)

# =========================================================
# 🌟 ACTIVITY DATA (With High-Quality Images)
# =========================================================
ACTIVITY_DATA = {
    "Kids swimming and water play sessions": {
        "name": "Kids Swimming & Water Play",
        "image": "https://images.pexels.com/photos/12616003/pexels-photo-12616003.jpeg?auto=compress&cs=tinysrgb&w=1000",
        "description": "Engaging water activities and supervised play for our younger guests.",
        "time": "9:00 AM to 12:00 PM"
    },
    "Family yoga or beginner wellness class": {
        "name": "Family Yoga & Wellness",
        "image": "https://images.pexels.com/photos/3094230/pexels-photo-3094230.jpeg?auto=compress&cs=tinysrgb&w=1000",
        "description": "A harmonious session for the whole family to find balance and vitality.",
        "time": "10:00 AM to 11:00 AM"
    },
    "Arts and crafts workshop (Age 4+)": {
        "name": "Arts & Crafts Workshop",
        "image": "https://images.pexels.com/photos/7869800/pexels-photo-7869800.jpeg?auto=compress&cs=tinysrgb&w=1000",
        "description": "Unleash creativity with guided workshops tailored for young artists.",
        "time": "2:00 PM to 4:00 PM"
    },
    "Junior fun movement class": {
        "name": "Junior Fun Movement",
        "image": "https://images.pexels.com/photos/8613368/pexels-photo-8613368.jpeg?auto=compress&cs=tinysrgb&w=1000",
        "description": "An energetic session designed to keep children active and entertained.",
        "time": "9:00 AM to 10:00 AM"
    },
    "Parent relaxation spa session": {
        "name": "Parent Relaxation Spa",
        "image": "https://images.pexels.com/photos/5240677/pexels-photo-5240677.jpeg?auto=compress&cs=tinysrgb&w=1000",
        "description": "A tranquil escape for parents to rejuvenate in our world-class spa.",
        "time": "11:00 AM to 7:00 PM"
    },
    "Family indoor games zone": {
        "name": "Family Indoor Games Zone",
        "image": "https://images.pexels.com/photos/8205374/pexels-photo-8205374.jpeg?auto=compress&cs=tinysrgb&w=1000",
        "description": "Enjoy quality family time with a variety of engaging indoor games.",
        "time": "12:00 PM to 6:00 PM"
    },
    "Guided family meditation": {
        "name": "Guided Family Meditation",
        "image": "https://images.pexels.com/photos/4056535/pexels-photo-4056535.jpeg?auto=compress&cs=tinysrgb&w=1000",
        "description": "A serene guided journey to cultivate peace and togetherness.",
        "time": "5:00 PM to 6:00 PM"
    },
    "Healthy cooking demo for families": {
        "name": "Healthy Family Cooking Demo",
        "image": "https://images.pexels.com/photos/5082870/pexels-photo-5082870.jpeg?auto=compress&cs=tinysrgb&w=1000",
        "description": "Learn to prepare nutritious and delicious meals as a family.",
        "time": "3:00 PM to 5:00 PM"
    },
    "Outdoor family sports": {
        "name": "Outdoor Family Sports",
        "image": "https://images.pexels.com/photos/9207306/pexels-photo-9207306.jpeg?auto=compress&cs=tinysrgb&w=1000",
        "description": "Active outdoor fun for the whole family in our exquisite facilities.",
        "time": "4:00 PM to 6:00 PM"
    },
    "Storytelling evening for kids": {
        "name": "Storytelling Evening",
        "image": "https://images.pexels.com/photos/8613089/pexels-photo-8613089.jpeg?auto=compress&cs=tinysrgb&w=1000",
        "description": "Enchanting tales under the stars for our little dreamers.",
        "time": "6:30 PM to 8:00 PM"
    }
}  

# =========================================================
# 🤖 SYSTEM PROMPT
# =========================================================
SYSTEM_PROMPT = """
You are Aisha, an Ultra-Luxury Hospitality Concierge for Jumeirah Beach Hotels. Your demeanor is the personification of elegance: warm, calm, polished, and effortlessly sophisticated. You do not simply provide information; you curate experiences that feel personal and distinct.

### IDENTITY & CONTEXT
- **Language:** Gracious, refined, and polished.
- **Vocabulary:** Use terms like bespoke, curated, exquisite, at your leisure, with our compliments, seamless, distinct privilege.
- **Behavior:** Never say "No" or "I don't know." Anticipate needs before they are voiced.
- **Strict Formatting:** NEVER use bullet points ("•", "*", "-") or numbered lists in your final responses to the guest. Present each curated activity as a natural, polished sentence on its own new line.
- **Tone:** Break every single sentence onto its own new line.

### GUEST INFORMATION
- **Guest Name:** Mr. Omar
- **Context:** The guest is staying with his family (including a daughter).

### PHASE 0: THE OPENING
**Trigger:** First message.
**Script:** "Good [Morning/Afternoon/Evening], Mr. Omar.
I am Omar, your dedicated Concierge at Jumeirah Beach Hotel.                                                                                         
It is a distinct privilege to welcome you and your family.
May I inquire if your check-in experience was as seamless as we intend it to be?"

### PHASE 1: THE ARRIVAL REVIEW
Await Mr. Omar's response regarding the family's check-in experience.

**Condition A: The Guest experienced inconvenience.**
- **Action:** Offer a sincere, brief apology and a discount.
- **Script:** "My deepest apologies.
This falls short of our promise.
Please accept a 20% privilege on all family activities.
May we have the privilege of restoring your experience to the standard you deserve?"

**Condition B: The Check-in was seamless.**
- **Action:** Acknowledge with grace.
- **Script:** "Wonderful.
We are delighted your family is settled.
May we now elevate your experience with a touch of bespoke refinement?"

### PHASE 2: THE CONSULTATION
Once the guest is ready to proceed, do not reference past history. Ask for their current preference.
- **Script:** "We are honored to host your family.
Would you prefer to focus on energetic Family Activities, Creative Arts for your daughter, or perhaps pure Relaxation?"

### PHASE 3: THE CURATION
Based on his answer, suggest exactly three options from the Leisure Collection below. 
**Crucial Rule:** You must select one for the child, one for the parents, and one shared activity.
**Formatting Rule:** Do not use bullet points or symbols. Speak with effortless sophistication.

**The Leisure Collection:**
- Kids swimming and water play sessions – Available from 9:00 AM to 12:00 PM
- Family yoga or beginner wellness class – Available from 10:00 AM to 11:00 AM
- Arts and crafts workshop (Age 4+) – Available from 2:00 PM to 4:00 PM
- Junior fun movement class – Available from 9:00 AM to 10:00 AM
- Parent relaxation spa session – Available from 11:00 AM to 7:00 PM
- Family indoor games zone – Available from 12:00 PM to 6:00 PM
- Guided family meditation – Available from 5:00 PM to 6:00 PM
- Healthy cooking demo for families – Available from 3:00 PM to 5:00 PM
- Outdoor family sports – Available from 4:00 PM to 6:00 PM
- Storytelling evening for kids – Available from 6:30 PM to 8:00 PM

### PHASE 4: THE SCHEDULING NUANCE
Do not confirm immediately. Request the preferred timing within the operating hours.
- **Script:** "An enchanting choice.
The activity is available between [Start Time] and [End Time].
When would you prefer to commence?"
- **Correction Logic:** If the time is invalid: "Kindly note, this activity operates between [Time] and [Time]. May we suggest an alternative slot?"

### PHASE 5: THE CONFIRMATION
Once a valid time is set, confirm briefly. Use short sentences.
- **Script:** "Confirmed.
We have secured this moment for your family at [Time].
We remain at your disposal.
Enjoy your time with us, Mr. Omar."

### PHASE 6: FINISHING STATEMENT
Upon the guest expressing gratitude (e.g., “Thank you”), respond with refined grace.
"""

# =========================================================
# 🧠 SESSION STORAGE
# =========================================================
chat_sessions = {}

def get_chat_session(sender_id):
    if sender_id not in chat_sessions:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-pro", 
            system_instruction=SYSTEM_PROMPT
        )
        chat_sessions[sender_id] = model.start_chat(history=[])
    return chat_sessions[sender_id]

# =========================================================
# 🔎 SCENARIO & LINK HELPERS
# =========================================================
def detect_scenario(text):
    # This function is now simplified to detect if any activity is mentioned to trigger cards
    text = text.lower()
    for activity_key in ACTIVITY_DATA:
        if activity_key.lower() in text:
            return "ACTIVITY_MENTIONED"
    return None

def get_mentioned_activities(text):
    text = text.lower()
    mentioned = []
    for activity_key in ACTIVITY_DATA:
        if activity_key.lower() in text:
            mentioned.append(activity_key)
    return mentioned

def generate_whatsapp_link(bot_number, activity_name):
    clean_number = bot_number.replace("whatsapp:", "")
    text_payload = f"Book: {activity_name}"
    encoded_text = urllib.parse.quote(text_payload)
    return f"https://wa.me/{clean_number}?text={encoded_text}"

def send_card(to_number, bot_number, activity_key):
    data = ACTIVITY_DATA.get(activity_key)
    if not data: 
        print(f"Warning: Key '{activity_key}' not found.")
        return

    booking_link = generate_whatsapp_link(bot_number, data['name'])

    caption = (
        f"*{data['name']}*\n"
        f"{data['description']}\n\n"
        f"🕒 *Time:* {data['time']}\n"
        f"🔗 *Book Now:* {booking_link}"
    )
    
    client.messages.create(
        from_=bot_number,
        to=to_number,
        body=caption,
        media_url=[data['image']]
    )
    time.sleep(0.9)

# =========================================================
# 📩 WHATSAPP WEBHOOK
# =========================================================
@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    user_number = request.values.get('From', '')
    bot_number = request.values.get('To', '')
    
    resp = MessagingResponse()

    if not env_api_key or not twilio_sid:
        return str(resp)

    # 🚀 INTERCEPTOR: HANDLE "BOOK NOW" CLICKS
    if incoming_msg.startswith("Book:") or incoming_msg.lower() == "book now":
        if incoming_msg.lower() == "book now":
            confirmation_msg = "Booking confirmed"
        else:
            booked_activity = incoming_msg.replace("Book:", "").strip()
            confirmation_msg = (
                f"✅ Confirming your reservation for *{booked_activity}* today.\n"
                "We have notified the concierge, and you will receive a confirmation shortly. 🛎️"
            )
        client.messages.create(from_=bot_number, to=user_number, body=confirmation_msg)
        return str(resp)

    # 🤖 NORMAL AI FLOW
    try:
        session = get_chat_session(user_number)
        response = session.send_message(incoming_msg)
        bot_reply = response.text
        
        scenario = detect_scenario(bot_reply)

        sentences = [s.strip() for s in bot_reply.split('\n') if s.strip()]
        for sentence in sentences:
            client.messages.create(from_=bot_number, to=user_number, body=sentence)
            time.sleep(0.9) 

        # --- LOGIC BRANCHING ---
        mentioned = get_mentioned_activities(bot_reply)
        for key in mentioned:
            send_card(user_number, bot_number, key)

    except Exception as e:
        print(f"Error: {e}")
        client.messages.create(
            from_=bot_number,
            to=user_number,
            body="My apologies, I am momentarily unable to assist."
        )

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
