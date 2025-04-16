import streamlit as st
import requests
from datetime import datetime
import google.generativeai as genai
import re

# ---- CONFIG ----
WEATHER_API_KEY = ""
GEMINI_API_KEY = ""
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

# ---- Gemini API Setup ----
genai.configure(api_key=GEMINI_API_KEY)

# ---- HELPER FUNCTIONS ----
def is_greeting(message):
    greetings = ["hi", "hello", "hey", "hii", "heyy", "yo", "hola", "namaste", "hey there"]
    return message.lower().strip() in greetings

def is_safety_question(message):
    safety_terms = ["safe", "safety", "danger", "risk", "secure", "is it safe", "should i go", "travel advisory"]
    return any(term in message.lower() for term in safety_terms)

def looks_like_city(message):
    return bool(re.match(r'^[a-zA-Z\s\-]+$', message.strip()))

def get_weather(city):
    try:
        params = {"q": city + ",IN", "appid": WEATHER_API_KEY, "units": "metric"}
        response = requests.get(WEATHER_API_URL, params=params)
        data = response.json()
        if data.get("cod") != 200:
            return None
        weather = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        icon_code = data["weather"][0]["icon"]
        icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
        return {
            "message": f"🌦️ Weather in {city.title()}: {weather}, Temp: {temp}°C, Humidity: {humidity}%, Wind Speed: {wind_speed} m/s",
            "icon": icon_url
        }
    except:
        return None

def generate_ai_response(prompt, context=""):
    try:
        model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-001")
        response = model.generate_content(context + prompt)
        return response.text
    except Exception as e:
        st.error(f"❌ Gemini API Error: {e}")
        return "⚠️ AI response failed. Please try again later."

def send_emergency_message(contacts):
    return f"📩 Emergency message sent to {len(contacts)} contacts!"

# ---- PAGE SETUP ----
st.set_page_config(page_title="🌍 Travel Safety Bot", layout="wide", page_icon="🌍")

# ---- CUSTOM CSS ----
st.markdown("""
    <style>
        .title {
            text-align: center;
            font-size: 2.5rem;
            color: #1976d2;
            margin-bottom: 1rem;
        }
        .chat-input-container {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            width: 50%;
            background-color: white;
            padding: 10px;
            border-radius: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            z-index: 1000;
        }
        .chat-bubble {
            padding: 12px 18px;
            border-radius: 18px;
            margin: 10px 0;
            max-width: 75%;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .user-bubble {
            background-color: #1976d2;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }
        .bot-bubble {
            background-color: white;
            color: #333;
            margin-right: auto;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# ---- SESSION STATE ----
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "emergency_contacts" not in st.session_state:
    st.session_state.emergency_contacts = []

# ---- HEADER ----
st.markdown("<h1 class='title'>🌍 TRAVEL SAFETY BOT</h1>", unsafe_allow_html=True)
st.markdown("Get real-time weather, safety tips, and emergency support for travel in India.")

# ---- CHAT INPUT (MAIN PAGE CENTERED) ----
st.markdown("<div class='chat-input-container'>", unsafe_allow_html=True)
with st.form(key="chat_input_form"):
    user_input = st.text_input(
        "💬 Ask about a city or travel safety...",
        placeholder="e.g., Is it safe to travel to Mumbai?",
        key="chat_input",
        label_visibility="collapsed"
    )
    submit_button = st.form_submit_button("Send", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---- PROCESS CHAT INPUT ----
if submit_button and user_input:
    user_msg = user_input.strip()
    st.session_state.chat_history.append(("user", user_msg))

    if is_greeting(user_msg):
        response = "👋 Hi! I'm your AI travel safety bot. Ask about any Indian city (weather, safety) or ask general travel safety questions!"
        st.session_state.chat_history.append(("bot", response))
    elif is_safety_question(user_msg):
        city_match = re.search(r'\b(?:to|in|at)\s+([A-Za-z\s]+)\b', user_msg, re.IGNORECASE)
        if city_match:
            city = city_match.group(1).strip()
            weather_data = get_weather(city)
            if weather_data:
                weather_html = f"""
                <div style="display: flex; align-items: center;">
                    <img src="{weather_data['icon']}" width="40" height="40">
                    <span>{weather_data['message']}</span>
                </div>
                """
                st.session_state.chat_history.append(("bot", weather_html))
                weather_context = f"Current weather in {city}: {weather_data['message']}\n\n"
            else:
                weather_context = ""
            prompt = f"User asked: '{user_msg}' about {city}. Provide safety advice including: 1. Current risks 2. Safe areas 3. Local scams to avoid"
            safety_response = generate_ai_response(prompt, weather_context)
            emergency_info = f"📞 Emergency Numbers for {city}: Police: 112, Ambulance: 102, Women's Helpline: 1090"
            st.session_state.chat_history.append(("bot", emergency_info))
            st.session_state.chat_history.append(("bot", safety_response))
        else:
            prompt = f"User asked: '{user_msg}'. Provide general safety advice for travelers in India."
            response = generate_ai_response(prompt)
            st.session_state.chat_history.append(("bot", response))
    elif looks_like_city(user_msg):
        weather_data = get_weather(user_msg)
        if weather_data:
            weather_html = f"""
            <div style="display: flex; align-items: center;">
                <img src="{weather_data['icon']}" width="40" height="40">
                <span>{weather_data['message']}</span>
            </div>
            """
            st.session_state.chat_history.append(("bot", weather_html))
            prompt = f"""Provide detailed travel info for {user_msg}, India:
            1. Top 3 safety tips
            2. Must-see places
            3. Local customs
            4. Travel options
            5. Advisories"""
            city_info = generate_ai_response(prompt)
            emergency_info = f"📞 Emergency Numbers for {user_msg}: Police: 112, Ambulance: 102, Women's Helpline: 1090"
            st.session_state.chat_history.append(("bot", emergency_info))
            st.session_state.chat_history.append(("bot", city_info))
        else:
            st.session_state.chat_history.append(("bot", f"⚠️ Couldn't find info for '{user_msg}'. Please enter a valid city."))
    else:
        prompt = f"User asked: '{user_msg}'. Respond as an Indian travel safety assistant."
        response = generate_ai_response(prompt)
        st.session_state.chat_history.append(("bot", response))
    st.rerun()

# ---- CHAT HISTORY TAB ----
tab1, tab2 = st.tabs(["💬 Chat History", "📋 Emergency Contacts"])

with tab1:
    for sender, msg in st.session_state.chat_history:
        bubble_class = "user-bubble" if sender == "user" else "bot-bubble"
        align = "flex-end" if sender == "user" else "flex-start"

        # If the bot's message includes raw HTML (e.g., weather info), don't wrap it
        if sender == "bot" and ("<div" in msg or "<img" in msg):
            st.markdown(f"""
                <div style='display: flex; flex-direction: column; align-items: {align};'>
                    {msg}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style='display: flex; flex-direction: column; align-items: {align};'>
                    <div class='chat-bubble {bubble_class}'>
                        <b>{'🧍 You' if sender == 'user' else '🤖 Bot'}</b><br>{msg}
                    </div>
                </div>
            """, unsafe_allow_html=True)



with tab2:
    st.markdown("### ✉️ Emergency Contacts")
    with st.expander("➕ Add Contact"):
        with st.form("add_contact"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name")
            phone = c2.text_input("Phone")
            if st.form_submit_button("Save"):
                if name and phone:
                    st.session_state.emergency_contacts.append({"name": name, "phone": phone})
                    st.success("Contact saved!")
                    st.rerun()
                else:
                    st.error("Fill both fields.")

    if st.session_state.emergency_contacts:
        for i, contact in enumerate(st.session_state.emergency_contacts):
            cols = st.columns([3, 1, 1])
            cols[0].write(f"**{contact['name']}**: {contact['phone']}")
            if cols[1].button("✉️", key=f"send_{i}"):
                st.success(f"Test sent to {contact['name']}")
            if cols[2].button("❌", key=f"del_{i}"):
                st.session_state.emergency_contacts.pop(i)
                st.rerun()
        if st.button("🚨 Send Alert to All"):
            st.success(send_emergency_message(st.session_state.emergency_contacts))
    else:
        st.info("No contacts saved yet.")

# ---- SIDEBAR ----
with st.sidebar:
    st.subheader("📝 Project Info")
    st.write("**Course:** INT-428")
    st.write("**Team:** Himanshu, Ankit Ojha, Nayasa Vishwas")
    st.markdown("- Real-time weather\n- AI safety insights\n- Emergency tools\n- Gemini-powered")
    st.divider()

