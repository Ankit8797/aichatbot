
import streamlit as st
import requests
from datetime import datetime
import google.generativeai as genai

# ---- CONFIG ----
WEATHER_API_KEY = "942055b86cf421ffa91df3591b2d2ee0"
GEMINI_API_KEY = "AIzaSyChB0b-MqY_5hHrrJ3wSqGyLjqNbWIJyf0"
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"

# ---- Gemini API Setup ----
genai.configure(api_key=GEMINI_API_KEY)

# ---- WEATHER FUNCTION ----
def get_weather(city):
    try:
        params = {"q": city + ",IN", "appid": WEATHER_API_KEY, "units": "metric"}
        response = requests.get(WEATHER_API_URL, params=params)
        data = response.json()
        weather = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        return f"🌦️ Weather in {city.title()}: {weather}, Temp: {temp}°C, Humidity: {humidity}%, Wind Speed: {wind_speed} m/s"
    except:
        return "⚠️ Couldn't fetch weather info. Please check the city name."

# ---- GEMINI RESPONSE FUNCTION ----
def generate_ai_response(city, weather_info):
    main_prompt = f"""
    You are a smart and helpful AI travel safety assistant.

    The user is interested in visiting the Indian city: **{city}**.
    The current weather details are: {weather_info}.

    Please provide:
    1. A helpful and practical **safety tip**.
    2. A short **fun fact** about {city}.
    3. One **digital safety or travel advice** (e.g., using local apps or tips for tourists).
    
    Keep it clear, friendly, and informative.
    """
    language_prompt = f"What are the main local languages spoken in {city}, India? Respond in one line."

    try:
        model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-001")

        # Main travel tips
        travel_response = model.generate_content(main_prompt)
        travel_text = travel_response.text

        # Local language only
        lang_response = model.generate_content(language_prompt)
        language = lang_response.text.strip().replace("*", "")

        # Static emergency info
        emergency_info = (
            f"🗣️ Local Language(s): {language}\n"
            f"📞 Emergency Helpline Numbers:\n"
            f"- Police: 112\n"
            f"- Ambulance: 102\n"
            f"- Women’s Helpline: 1090"
        )

        return travel_text, emergency_info

    except Exception as e:
        st.error(f"❌ Gemini API Error: {e}")
        return "⚠️ AI response failed. Please try again later.", ""

# ---- UI CONFIG ----
st.set_page_config(page_title="🌍 Travel Safety Chatbot", layout="centered")

st.markdown("""
    <style>
        .chat-bubble {
            padding: 15px;
            border-radius: 20px;
            margin: 10px 0;
            font-size: 16px;
            line-height: 1.5;
            max-width: 90%;
        }
        .user {
            background-color: #e3f2fd;
            color: #000;
            align-self: flex-end;
        }
        .bot {
            background-color: #1976d2;
            color: #fff;
            align-self: flex-start;
        }
        .timestamp {
            font-size: 12px;
            color: gray;
            margin-top: 4px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🧠 AI Travel Safety Chatbot")
st.markdown("Ask about **any Indian city** to get weather updates, safety tips, local languages, and emergency helplines.")

# ---- SESSION STATE ----
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---- INPUT ----
user_input = st.text_input("💬 Type something...", "")

if user_input:
    user_msg = user_input.strip()
    timestamp = datetime.now().strftime("%I:%M %p")

    st.session_state.chat_history.append(("user", user_msg, timestamp))

    greetings = ["hi", "hello", "hey", "hii", "heyy", "yo", "hola"]
    if user_msg.lower() in greetings:
        response = "👋 Hi! I'm your AI travel safety chatbot. Type the name of any Indian city to get weather, safety tips, local languages, and helpline numbers!"
        st.session_state.chat_history.append(("bot", response, timestamp))
    else:
        weather_info = get_weather(user_msg)
        travel_tips, emergency_details = generate_ai_response(user_msg, weather_info)

        st.session_state.chat_history.append(("bot", weather_info, timestamp))
        if emergency_details:
            st.session_state.chat_history.append(("bot", emergency_details, timestamp))
        st.session_state.chat_history.append(("bot", travel_tips, timestamp))

# ---- DISPLAY CHAT ----
for sender, msg, time in st.session_state.chat_history:
    bubble_class = "user" if sender == "user" else "bot"
    align = "flex-end" if sender == "user" else "flex-start"
    st.markdown(f"""
        <div style='display: flex; flex-direction: column; align-items: {align};'>
            <div class='chat-bubble {bubble_class}'>
                <b>{'🧍 You' if sender == 'user' else '🤖 Bot'} ({time}):</b><br>{msg}
            </div>
        </div>
    """, unsafe_allow_html=True)
