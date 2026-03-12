import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import random
import requests
import cohere
from datetime import date, timedelta
from collections import defaultdict
from dotenv import load_dotenv

# ─────────────────────────────────────────────────
# LOAD API KEYS
# Your .env file should contain:
#   COHERE_API_KEY=your_key_here
#   ELEVENLABS_API_KEY=your_key_here
# ─────────────────────────────────────────────────
load_dotenv()
COHERE_API_KEY    = os.getenv("COHERE_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

co = cohere.ClientV2(COHERE_API_KEY) if COHERE_API_KEY else None


# ─────────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────────
st.set_page_config(page_title="Mooncyc", page_icon="🌙", layout="wide")

# ─────────────────────────────────────────────────
# CUSTOM STYLING
# ─────────────────────────────────────────────────
st.markdown("""
    <style>
    .stApp { background-color: #F3E4F5; color: #2d1f33; }
    [data-testid="stSidebar"] { background-color: #e8d0ec; }
    h1, h2, h3, p, label { color: #2d1f33 !important; }
    [data-testid="stDecoration"] { display: none; }
    [data-testid="stHeader"] { background-color: transparent; display: none; }
    [data-testid="stSlider"] > div > div > div > div {
        background: linear-gradient(to right, #d8bfd8, #b39eb5) !important; }
    [data-testid="stSlider"] [role="slider"] {
        background-color: #d8bfd8 !important; border-color: #d8bfd8 !important; }
    div[role="radiogroup"] label div:first-child { display: none !important; }
    div[role="radiogroup"] label {
        background-color: #e8d0ec !important; border: 1.5px solid #b39eb5 !important;
        border-radius: 20px !important; padding: 8px 22px !important;
        margin-right: 10px !important; cursor: pointer !important;
        color: #2d1f33 !important; font-size: 1rem !important;
        font-weight: 600 !important; min-width: 100px !important;
        text-align: center !important; }
    div[role="radiogroup"] label:has(input:checked) {
        background-color: #b39eb5 !important; border-color: #6b5b7a !important;
        color: #ffffff !important; font-weight: 800 !important;
        box-shadow: 0 0 10px #d8bfd8 !important; }
    span[data-baseweb="tag"] {
        background-color: #b39eb5 !important; border-color: #d8bfd8 !important; }
    span[data-baseweb="tag"] span[class] { color: #ffffff !important; }
    span[data-baseweb="tag"] button { color: #ffffff !important; }
    [data-testid="stFormSubmitButton"] > button {
        background-color: #d8bfd8 !important; color: #4a3f4f !important;
        border: 2px solid #b39eb5 !important; border-radius: 10px !important;
        width: 100% !important; padding: 1.2rem 2rem !important;
        font-size: 1.15rem !important; font-weight: 700 !important;
        margin-top: 20px !important; }
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #b39eb5 !important; color: white !important; }
    div.stButton > button {
        background-color: #b39eb5 !important; color: #ffffff !important;
        border: 1px solid #d8bfd8 !important; border-radius: 8px !important; }
    div.stButton > button:hover {
        background-color: #d8bfd8 !important; color: #4a3f4f !important; }
    /* ── Override ALL Streamlit red/orange accents → dark purple ── */
    :root {
        --primary-color: #6b5b7a !important;
    }
    a { color: #6b5b7a !important; }
    /* Focus rings on inputs, selects, textareas */
    input:focus, textarea:focus, select:focus,
    [data-baseweb="input"]:focus-within,
    [data-baseweb="textarea"]:focus-within,
    [data-baseweb="select"]:focus-within {
        border-color: #6b5b7a !important;
        box-shadow: 0 0 0 2px rgba(107,91,122,0.3) !important;
        outline-color: #6b5b7a !important;
    }
    /* Streamlit's primary interactive color (used for borders, checkboxes, etc.) */
    [data-testid="stForm"] { border-color: #b39eb5 !important; }
    /* Progress bar fill */
    [data-testid="stProgress"] > div > div > div {
        background-color: #b39eb5 !important; }
    /* st.error box */
    [data-testid="stAlert"][kind="error"],
    div[data-testid="stNotification"][data-type="error"] {
        border-left-color: #6b5b7a !important;
        background-color: #e8d0ec !important;
    }
    /* Multiselect and select dropdown hover */
    [data-baseweb="menu"] [aria-selected="true"],
    [data-baseweb="menu"] li:hover {
        background-color: #e8d0ec !important; }
    /* Date input and number input focus */
    [data-baseweb="calendar"] [aria-selected="true"] {
        background-color: #6b5b7a !important; }
    /* Slider thumb and track already handled above, but reinforce */
    [data-testid="stSlider"] [role="slider"]:focus {
        box-shadow: 0 0 0 4px rgba(107,91,122,0.4) !important; }
    </style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────
# STORAGE
# ─────────────────────────────────────────────────
CYCLE_FILE = "cycle_data.json"
TASKS_FILE = "tasks.json"


def load_cycle_data():
    if os.path.exists(CYCLE_FILE):
        with open(CYCLE_FILE, "r") as f:
            data = json.load(f)
        if data.get("last_period"):
            data["last_period"] = date.fromisoformat(data["last_period"])
        for entry in data.get("symptoms_log", []):
            if "date" in entry:
                entry["date"] = date.fromisoformat(entry["date"])
        return data
    return {"last_period": None, "cycle_length": 28, "period_length": 5, "symptoms_log": []}


def save_cycle_data(data):
    data_copy = data.copy()
    if data_copy.get("last_period"):
        data_copy["last_period"] = data_copy["last_period"].isoformat()
    symptoms_copy = []
    for entry in data_copy.get("symptoms_log", []):
        entry_copy = entry.copy()
        if "date" in entry_copy:
            entry_copy["date"] = entry_copy["date"].isoformat()
        symptoms_copy.append(entry_copy)
    data_copy["symptoms_log"] = symptoms_copy
    with open(CYCLE_FILE, "w") as f:
        json.dump(data_copy, f, indent=2)


def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            tasks = json.load(f)
        for task in tasks:
            if task.get("deadline"):
                task["deadline"] = date.fromisoformat(task["deadline"])
        return tasks
    return []


def save_tasks(tasks):
    tasks_copy = []
    for task in tasks:
        t = task.copy()
        if t.get("deadline"):
            t["deadline"] = t["deadline"].isoformat()
        tasks_copy.append(t)
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks_copy, f, indent=2)


# ─────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────
if "cycle_data"          not in st.session_state: st.session_state.cycle_data = load_cycle_data()
if "tasks"               not in st.session_state: st.session_state.tasks = load_tasks()
if "meditation_messages" not in st.session_state: st.session_state.meditation_messages = []
if "current_meditation"  not in st.session_state: st.session_state.current_meditation = None
if "meditation_audio"    not in st.session_state: st.session_state.meditation_audio = None
if "current_meal_plan"   not in st.session_state: st.session_state.current_meal_plan = None
if "current_remedy"      not in st.session_state: st.session_state.current_remedy = None
if "monthly_insights"    not in st.session_state: st.session_state.monthly_insights = None
if "fasting_advice"      not in st.session_state: st.session_state.fasting_advice = None
if "quote_refresh_count" not in st.session_state: st.session_state.quote_refresh_count = 0


# ─────────────────────────────────────────────────
# CYCLE LOGIC
# ─────────────────────────────────────────────────
def get_cycle_phase(cycle_data, target_date=None):
    if not cycle_data["last_period"]:
        return None
    if target_date is None:
        target_date = date.today()
    days_since = (target_date - cycle_data["last_period"]).days
    day_in_cycle = days_since % cycle_data["cycle_length"]
    period_len = cycle_data["period_length"]
    if day_in_cycle < period_len:       return "Menstrual"
    elif day_in_cycle < 14:             return "Follicular"
    elif day_in_cycle < 16:             return "Ovulation"
    else:                               return "Luteal"


def get_phase_energy_level(phase):
    return {"Menstrual": 2, "Follicular": 4, "Ovulation": 5, "Luteal": 3}.get(phase, 3)


def get_phase_description(phase):
    descriptions = {
        "Menstrual": {
            "emoji": "🩸", "summary": "Your body is shedding the uterine lining",
            "hormones": "Both estrogen and progesterone are at their lowest",
            "feeling": "It's completely normal to feel drained, emotional, or want to curl up in bed. Your body is doing intense biological work — be kind to yourself.",
            "tip": "This is your body's natural reset. Honor the need for rest, warmth, and gentle movement."
        },
        "Follicular": {
            "emoji": "🌱", "summary": "Your body is preparing to release an egg",
            "hormones": "Estrogen is rising steadily",
            "feeling": "You might notice your mood lifting, energy returning, and skin glowing. This is your spring phase — new ideas and motivation come naturally.",
            "tip": "Harness this energy! Start new projects, have difficult conversations, tackle your hardest tasks."
        },
        "Ovulation": {
            "emoji": "✨", "summary": "Your body releases an egg — peak fertility",
            "hormones": "Estrogen and testosterone peak together",
            "feeling": "This is your superpower window. You feel confident, social, strong, and clear-headed. Everything feels easier right now.",
            "tip": "Schedule presentations, workouts, social events, and challenging tasks here. You're literally at your best."
        },
        "Luteal": {
            "emoji": "🌙", "summary": "Your body prepares for either pregnancy or menstruation",
            "hormones": "Progesterone rises, then both hormones drop sharply before your period",
            "feeling": "It's completely normal to feel drained, irritable, or foggy — especially in the second half. The hormone crash is real and it's not in your head.",
            "tip": "This is your autumn phase. Focus on finishing what you started, not starting new things. Rest is productive."
        }
    }
    return descriptions.get(phase, descriptions["Follicular"])


def get_exercise_recommendation(phase):
    recommendations = {
        "Menstrual": {"type": "🧘 Gentle yoga, walking, stretching", "why": "Low progesterone and estrogen — your body needs rest and gentle movement."},
        "Follicular": {"type": "🏃 HIIT, running, strength training", "why": "Rising estrogen boosts energy and muscle building capacity."},
        "Ovulation":  {"type": "💪 Peak performance training, heavy lifting", "why": "Testosterone and estrogen peak — your strongest days."},
        "Luteal":     {"type": "🚴 Moderate cardio, pilates, swimming", "why": "Progesterone rises — focus on steady-state endurance."}
    }
    return recommendations.get(phase, recommendations["Follicular"])


# ─────────────────────────────────────────────────
# FEATURE 1: DAILY QUOTE (ZenQuotes API)
# ─────────────────────────────────────────────────
# ZenQuotes is free, no API key needed, and has 100s of quotes.
# It returns a fresh random quote on every call.
# We also keep a large per-phase fallback list so the button
# always produces a different quote even if the API is down.

FALLBACK_QUOTES = {
    "Menstrual": [
        {"content": "Rest when you're weary. Refresh and renew yourself, your body, your mind, your spirit.", "author": "Ralph Marston"},
        {"content": "Almost everything will work again if you unplug it for a few minutes, including you.", "author": "Anne Lamott"},
        {"content": "Self-care is not self-indulgence. Self-care is self-preservation.", "author": "Audre Lorde"},
        {"content": "You don't have to be positive all the time. It's perfectly okay to feel sad, angry, annoyed, or overwhelmed.", "author": "Lori Deschene"},
        {"content": "Be gentle with yourself. You are a child of the universe, no less than the trees and the stars.", "author": "Max Ehrmann"},
        {"content": "Nourishing yourself in a way that helps you blossom in the direction you want to go is attainable.", "author": "Deborah Day"},
        {"content": "Rest and self-care are so important. When you take time to replenish your spirit, it allows you to serve others.", "author": "Eleanor Brown"},
        {"content": "To love oneself is the beginning of a lifelong romance.", "author": "Oscar Wilde"},
    ],
    "Follicular": [
        {"content": "The secret of getting ahead is getting started.", "author": "Mark Twain"},
        {"content": "Each day is a new beginning. The sky is clearing and the sun shines anew.", "author": "Sarah Ban Breathnach"},
        {"content": "With the new day comes new strength and new thoughts.", "author": "Eleanor Roosevelt"},
        {"content": "The beginning is always today.", "author": "Mary Wollstonecraft"},
        {"content": "Every day is a new opportunity to grow.", "author": "Roy T. Bennett"},
        {"content": "Start where you are. Use what you have. Do what you can.", "author": "Arthur Ashe"},
        {"content": "Do something today that your future self will thank you for.", "author": "Sean Patrick Flanery"},
        {"content": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt"},
    ],
    "Ovulation": [
        {"content": "You are braver than you believe, stronger than you seem, and smarter than you think.", "author": "A.A. Milne"},
        {"content": "The most courageous act is still to think for yourself. Aloud.", "author": "Coco Chanel"},
        {"content": "She believed she could, so she did.", "author": "R.S. Grey"},
        {"content": "You have within you right now, everything you need to deal with whatever the world can throw at you.", "author": "Brian Tracy"},
        {"content": "The question isn't who's going to let me; it's who is going to stop me.", "author": "Ayn Rand"},
        {"content": "I am not afraid. I was born to do this.", "author": "Joan of Arc"},
        {"content": "Your potential is limitless. Keep going.", "author": "Roy T. Bennett"},
        {"content": "Confidence is not 'they will like me'. Confidence is 'I'll be fine if they don't'.", "author": "Christina Grimmie"},
    ],
    "Luteal": [
        {"content": "In the middle of difficulty lies opportunity.", "author": "Albert Einstein"},
        {"content": "Patience is not the ability to wait, but the ability to keep a good attitude while waiting.", "author": "Joyce Meyer"},
        {"content": "Wisdom is knowing what to do next, virtue is doing it.", "author": "David Starr Jordan"},
        {"content": "The quieter you become, the more you are able to hear.", "author": "Rumi"},
        {"content": "Almost everything will work again if you unplug it for a few minutes, including you.", "author": "Anne Lamott"},
        {"content": "Within you there is a stillness and a sanctuary to which you can retreat at any time.", "author": "Hermann Hesse"},
        {"content": "Grant me the serenity to accept the things I cannot change.", "author": "Reinhold Niebuhr"},
        {"content": "Nothing is permanent. This too shall pass.", "author": "Persian proverb"},
    ]
}


def get_cycle_quote(phase: str, previous_content: str = "") -> dict:
    # Try ZenQuotes API first — free, no key, returns a fresh random quote every call
    try:
        response = requests.get("https://zenquotes.io/api/random", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # ZenQuotes returns a list with one item: [{"q": "quote", "a": "author"}]
            if data and data[0].get("q") and data[0]["q"] != previous_content:
                return {"content": data[0]["q"], "author": data[0]["a"]}
    except requests.exceptions.RequestException:
        pass

    # Fallback: pick randomly from the curated per-phase list,
    # avoiding the previous quote so it always feels fresh
    options = [q for q in FALLBACK_QUOTES.get(phase, FALLBACK_QUOTES["Follicular"])
               if q["content"] != previous_content]
    if not options:
        options = FALLBACK_QUOTES.get(phase, FALLBACK_QUOTES["Follicular"])
    return random.choice(options)


# ─────────────────────────────────────────────────
# FEATURE 2: AI MEDITATION + ITERATIVE REFINEMENT
# ─────────────────────────────────────────────────
def get_initial_meditation(phase: str, mood: str, symptoms: list, age: int) -> str:
    if not co:
        return "Add COHERE_API_KEY to your .env file to unlock AI meditations."

    symptom_str = ", ".join(symptoms) if symptoms else "no specific symptoms"
    age_context = f"The user is {age} years old." if age else ""

    system_message = """You are a compassionate mindfulness guide who specializes in 
    menstrual cycle wellness. You write personalized, gentle, and grounding meditation 
    scripts. Your scripts are warm, poetic, and practical. Each step is a short paragraph."""

    user_message = f"""Write a personalized meditation script for someone in their {phase} phase.
{age_context}
Current mood: {mood}
Symptoms today: {symptom_str}

The meditation should:
- Start by acknowledging exactly how they feel right now
- Use imagery that matches the energy of the {phase} phase
- Be gentle and compassionate in tone
- End with an empowering affirmation suited to this phase
- Be 5-7 minutes long (mention the duration at the start)

Write the full script, ready to be read or followed."""

    try:
        response = co.chat(
            model="command-r-plus-08-2024",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user",   "content": user_message}
            ]
        )
        return response.message.content[0].text
    except Exception as e:
        return f"Could not connect to Cohere: {str(e)}"


def refine_meditation(messages_history: list, user_feedback: str) -> tuple:
    if not co:
        return "Add COHERE_API_KEY to your .env file.", messages_history

    updated_history = messages_history + [{
        "role": "user",
        "content": f"This meditation didn't quite work for me. Here is what I would like changed: {user_feedback}\n\nCan you rewrite the meditation taking this into account? Keep the same warm, guided format."
    }]

    try:
        response = co.chat(model="command-r-plus-08-2024", messages=updated_history)
        new_meditation = response.message.content[0].text
        updated_history.append({"role": "assistant", "content": new_meditation})
        return new_meditation, updated_history
    except Exception as e:
        return f"Could not connect to Cohere: {str(e)}", messages_history


# ─────────────────────────────────────────────────
# ELEVENLABS TEXT-TO-SPEECH
# ─────────────────────────────────────────────────
# Converts the LLM meditation script to MP3 audio.
# Free tier: 10,000 characters/month at elevenlabs.io
# Voice: "Rachel" — calm, warm, ideal for meditations.
# Voice ID: 21m00Tcm4TlvDq8ikWAM

def text_to_speech(text: str) -> tuple:
    """Returns (audio_bytes_or_None, error_message_or_None)"""
    if not ELEVENLABS_API_KEY:
        return None, "No ElevenLabs API key found. Add ELEVENLABS_API_KEY to your .env file."

    VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
    url      = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers  = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload  = {
        "text": text[:2500],   # trim to stay inside free tier
        "model_id": "eleven_turbo_v2",
        "voice_settings": {"stability": 0.80, "similarity_boost": 0.75, "speed": 0.75}
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.content, None
        else:
            # Show the actual ElevenLabs error so we can debug it
            try:
                body = response.json()
                msg  = body.get("detail", {}).get("message", str(body))
            except Exception:
                msg = f"HTTP {response.status_code}"
            return None, f"ElevenLabs error: {msg}"
    except requests.exceptions.RequestException as e:
        return None, f"Network error contacting ElevenLabs: {str(e)}"


# ─────────────────────────────────────────────────
# FEATURE 3: AI MEAL PLAN
# ─────────────────────────────────────────────────
def get_llm_meal_plan(phase: str, symptoms: list, age: int) -> dict:
    if not co:
        return {"breakfast": "Add COHERE_API_KEY to .env to unlock AI meal plans",
                "lunch": "", "dinner": "", "snacks": "", "why": ""}

    symptom_str = ", ".join(symptoms) if symptoms else "no specific symptoms"
    age_context = f"The user is {age} years old." if age else ""

    system_message = """You are a nutritionist specializing in cycle-syncing nutrition. 
    You create personalized, practical meal plans that support hormonal health at each 
    phase of the menstrual cycle. Your suggestions are realistic, delicious, and evidence-based."""

    user_message = f"""Create a one-day meal plan for someone in their {phase} phase.
{age_context}
Current symptoms: {symptom_str}

Respond ONLY in this exact format with no extra text before or after:
BREAKFAST: [meal with emoji]
LUNCH: [meal with emoji]
DINNER: [meal with emoji]
SNACKS: [snacks with emoji]
WHY: [1-2 sentences on the nutritional logic for this phase, symptoms, and age]"""

    try:
        response = co.chat(
            model="command-r-plus-08-2024",
            messages=[{"role": "system", "content": system_message},
                      {"role": "user",   "content": user_message}]
        )
        raw    = response.message.content[0].text
        result = {"breakfast": "", "lunch": "", "dinner": "", "snacks": "", "why": ""}
        for line in raw.strip().split("\n"):
            if   line.startswith("BREAKFAST:"): result["breakfast"] = line.replace("BREAKFAST:", "").strip()
            elif line.startswith("LUNCH:"):     result["lunch"]     = line.replace("LUNCH:", "").strip()
            elif line.startswith("DINNER:"):    result["dinner"]    = line.replace("DINNER:", "").strip()
            elif line.startswith("SNACKS:"):    result["snacks"]    = line.replace("SNACKS:", "").strip()
            elif line.startswith("WHY:"):       result["why"]       = line.replace("WHY:", "").strip()
        if not result["breakfast"]:
            result["breakfast"] = "Could not parse — try regenerating"
        return result
    except Exception as e:
        return {"breakfast": f"Error: {str(e)}", "lunch": "", "dinner": "", "snacks": "", "why": ""}


# ─────────────────────────────────────────────────
# FEATURE 4: AI NATURAL REMEDIES
# ─────────────────────────────────────────────────
def get_llm_remedies(symptoms: list, phase: str, age: int) -> str:
    if not co:
        return "Add COHERE_API_KEY to your .env file to unlock AI remedies."
    if not symptoms:
        return "No symptoms logged. Track how you are feeling above to get personalized remedies."

    symptom_str = ", ".join(symptoms)
    age_context = f"The user is {age} years old." if age else ""

    system_message = """You are a holistic women's health coach with expertise in natural, 
    evidence-based remedies for menstrual cycle symptoms. You give warm, practical advice 
    grounded in science. Always remind users to consult a healthcare provider for severe symptoms."""

    user_message = f"""The user is in their {phase} phase and is experiencing: {symptom_str}
{age_context}

For each symptom, provide a natural remedy:
**[Symptom name]**
Remedy: [what to do]
How: [specific, actionable instructions]
Why it works: [brief science-backed explanation, 1 sentence]

After all symptoms, add one short closing note about how these remedies interact 
with the {phase} phase specifically. Keep each remedy concise and practical."""

    try:
        response = co.chat(
            model="command-r-plus-08-2024",
            messages=[{"role": "system", "content": system_message},
                      {"role": "user",   "content": user_message}]
        )
        return response.message.content[0].text
    except Exception as e:
        return f"Could not connect to Cohere: {str(e)}"


# ─────────────────────────────────────────────────
# FEATURE 5: INTERMITTENT FASTING ADVISOR
# ─────────────────────────────────────────────────
# No public API exists for cycle-based fasting recommendations,
# so the LLM does the reasoning. It receives the cycle phase,
# cycle day number, age, and current symptoms — then decides:
#   - Is today a good day to fast? (yes/no + reason)
#   - If yes: what is the maximum safe fasting window?
#   - If no: what should the user eat instead?
# This is non-trivial because the LLM makes a data-driven
# medical judgment, not just text formatting.

def get_fasting_advice(phase: str, day_in_cycle: int, symptoms: list, age: int) -> str:
    if not co:
        return "Add COHERE_API_KEY to your .env file to unlock fasting advice."

    symptom_str  = ", ".join(symptoms) if symptoms else "no specific symptoms"
    age_context  = f"The user is {age} years old." if age else ""

    system_message = """You are a women's health nutritionist with expertise in 
    intermittent fasting and menstrual cycle nutrition. You give evidence-based, 
    safety-conscious advice on whether fasting is appropriate at each cycle phase. 
    You are direct and practical. You always prioritize the user's wellbeing and 
    remind them to consult a doctor if they have any health conditions."""

    user_message = f"""Should this person do intermittent fasting today?

Cycle phase: {phase}
Day in cycle: {day_in_cycle}
Current symptoms: {symptom_str}
{age_context}

Please respond in this exact format:
RECOMMENDATION: [Good day to fast / Not recommended today]
MAX HOURS: [e.g. 14 hours, or N/A if not recommended]
REASON: [2-3 sentences explaining why, referencing the specific phase and symptoms]
TIP: [One specific, practical tip for today — either how to do the fast safely, or what to eat instead if not fasting]"""

    try:
        response = co.chat(
            model="command-r-plus-08-2024",
            messages=[{"role": "system", "content": system_message},
                      {"role": "user",   "content": user_message}]
        )
        return response.message.content[0].text
    except Exception as e:
        return f"Could not connect to Cohere: {str(e)}"


def parse_fasting_advice(raw: str) -> dict:
    """Parses the structured LLM fasting response into a dict for display."""
    result = {"recommendation": "", "max_hours": "", "reason": "", "tip": ""}
    for line in raw.strip().split("\n"):
        if   line.startswith("RECOMMENDATION:"): result["recommendation"] = line.replace("RECOMMENDATION:", "").strip()
        elif line.startswith("MAX HOURS:"):       result["max_hours"]      = line.replace("MAX HOURS:", "").strip()
        elif line.startswith("REASON:"):          result["reason"]         = line.replace("REASON:", "").strip()
        elif line.startswith("TIP:"):             result["tip"]            = line.replace("TIP:", "").strip()
    if not result["recommendation"]:
        result["recommendation"] = raw  # show raw text if parsing fails
    return result


# ─────────────────────────────────────────────────
# FEATURE 6: SYMPTOM PATTERN ANALYZER
# ─────────────────────────────────────────────────
def build_symptom_analysis_prompt(symptoms_log: list, cycle_length: int, age: int) -> str:
    if not symptoms_log:
        return ""

    phase_symptoms = defaultdict(list)
    phase_moods    = defaultdict(list)
    phase_energy   = defaultdict(list)

    for entry in symptoms_log:
        p = entry.get("phase", "Unknown")
        if p and p != "Unknown":
            for symptom in entry.get("symptoms", []):
                if symptom != "None":
                    phase_symptoms[p].append(symptom)
            if entry.get("mood"):   phase_moods[p].append(entry["mood"])
            if entry.get("energy"): phase_energy[p].append(entry["energy"])

    phase_symptom_counts = {}
    for p, slist in phase_symptoms.items():
        counts = defaultdict(int)
        for s in slist: counts[s] += 1
        phase_symptom_counts[p] = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]

    avg_energy = {}
    for p, energies in phase_energy.items():
        avg_energy[p] = round(sum(energies) / len(energies), 1) if energies else "N/A"

    age_context = f"The user is {age} years old." if age else ""
    prompt = f"""You are a compassionate women's health coach analyzing a user's menstrual cycle data.
{age_context}
The user has a {cycle_length}-day cycle and has logged {len(symptoms_log)} days of data.

Symptom and mood pattern by cycle phase:
"""
    for p in ["Menstrual", "Follicular", "Ovulation", "Luteal"]:
        top = phase_symptom_counts.get(p, [])
        avg_e = avg_energy.get(p, "N/A")
        moods = phase_moods.get(p, [])
        prompt += f"\n**{p} Phase** (average energy: {avg_e}/5):\n"
        prompt += f"  Symptoms: {', '.join([f'{s} (x{c})' for s,c in top]) if top else 'none logged yet'}\n"
        if moods: prompt += f"  Recent moods: {', '.join(moods[-3:])}\n"

    prompt += """
Based on this data, provide:
1. **Top 3 Pattern Observations** — be concrete, reference the actual data.
2. **Personalized Recommendations for Next Cycle** — 3 specific suggestions, each mentioning which phase.
3. **One Thing to Watch** — one symptom or trend to monitor next cycle, and why.

Warm, supportive tone. Concise. Address the user as "you".
"""
    return prompt


def get_symptom_insights(symptoms_log: list, cycle_length: int, age: int) -> str:
    if not co:
        return "Add COHERE_API_KEY to your .env file to unlock AI cycle analysis."
    if len(symptoms_log) < 5:
        return "Log at least 5 days of symptoms to unlock your personalized cycle insights."

    prompt = build_symptom_analysis_prompt(symptoms_log, cycle_length, age)
    try:
        response = co.chat(
            model="command-r-plus-08-2024",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.message.content[0].text
    except Exception as e:
        return f"Could not connect to Cohere: {str(e)}"


# ─────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────
with st.sidebar:
    st.title("🌙 Mooncyc")
    st.caption("*Your daily cycle buddy*")
    st.divider()

    if co:
        st.success("🤖 AI features: Active")
    else:
        st.warning("🤖 AI: Add COHERE_API_KEY to .env")

    if ELEVENLABS_API_KEY:
        st.success("🔊 Audio: Active")
    else:
        st.warning("🔊 Audio: Add ELEVENLABS_API_KEY to .env")

    st.divider()
    st.subheader("🩸 Your Cycle Setup")

    last_period   = st.date_input("Last period started",
                                   value=st.session_state.cycle_data.get("last_period") or date.today())
    cycle_length  = st.slider("Average cycle length (days)", 21, 35,
                               value=st.session_state.cycle_data.get("cycle_length", 28))
    period_length = st.slider("Period duration (days)", 3, 7,
                               value=st.session_state.cycle_data.get("period_length", 5))

    st.divider()
    st.subheader("👤 About Me")
    # Age is used in all LLM prompts to personalise recommendations
    user_age = st.number_input("My Age", min_value=13, max_value=60, value=25, step=1)

    if st.button("💾 Save My Info"):
        st.session_state.cycle_data["last_period"]  = last_period
        st.session_state.cycle_data["cycle_length"] = cycle_length
        st.session_state.cycle_data["period_length"]= period_length
        save_cycle_data(st.session_state.cycle_data)
        st.success("✨ Saved")


# ═══════════════════════════════════════════════════════════════
# MAIN AREA
# ═══════════════════════════════════════════════════════════════
st.title("🌙 Mooncyc")
st.subheader("*Your daily organizer buddy who gets your cycle*")
st.divider()

phase = get_cycle_phase(st.session_state.cycle_data)

if phase:
    phase_info = get_phase_description(phase)
    days_since   = (date.today() - st.session_state.cycle_data["last_period"]).days
    day_in_cycle = (days_since % cycle_length) + 1

    # ── 1. CURRENT PHASE + QUOTE ──────────────────────────────────
    st.markdown(f"### {phase_info['emoji']} Current Phase: {phase} — Day {day_in_cycle} of {cycle_length}")
    energy = get_phase_energy_level(phase)
    st.progress(energy / 5.0, text=f"Energy: {energy}/5")

    quote_cache_key = f"quote_{phase}_{st.session_state.quote_refresh_count}"
    if st.session_state.get("quote_cache_key") != quote_cache_key:
        previous = st.session_state.get("daily_quote", {}).get("content", "")
        st.session_state.daily_quote     = get_cycle_quote(phase, previous)
        st.session_state.quote_cache_key = quote_cache_key

    quote = st.session_state.daily_quote
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#e8d0ec,#F3E4F5);border-left:4px solid #b39eb5;
                border-radius:12px;padding:20px 24px;margin:16px 0;">
        <p style="color:#6b5b7a;font-size:0.75rem;font-weight:700;letter-spacing:0.12em;
                  text-transform:uppercase;margin:0 0 12px 0;">✨ Quote of the Day</p>
        <p style="font-style:italic;font-size:1.1rem;color:#2d1f33;margin:0 0 10px 0;">
            "{quote['content']}"</p>
        <p style="color:#6b5b7a;font-size:0.9rem;margin:0;">— {quote['author']}</p>
    </div>""", unsafe_allow_html=True)

    if st.button("🔄 New Quote"):
        st.session_state.quote_refresh_count += 1
        st.rerun()

    st.divider()

    # ── 2. HOW ARE YOU FEELING (SYMPTOM TRACKER) ──────────────────
    st.subheader("📝 How Are You Feeling?")
    st.caption("Track symptoms for any day — build your cycle pattern database")

    with st.form("symptom_form"):
        log_date = st.date_input("Which day are you logging?", value=date.today(), max_value=date.today())
        col_a, col_b = st.columns(2)
        with col_a:
            mood = st.select_slider("Mood",
                options=["😭 Terrible","😢 Low","😔 Down","😐 Neutral","🙂 Okay","😊 Good","😄 Great","🌟 Amazing"],
                value="😐 Neutral")
            energy_today = st.slider("Energy level", 1, 5, 3)
        with col_b:
            symptoms = st.multiselect("Symptoms (if any)", options=[
                "Cramps","Bloating","Headache","Irritable","Stressed","Tired","Low Energy",
                "Pissed","Intolerant","Migraine","Fatigue","Irritability","Anxiety","Depression",
                "Breast tenderness","Acne","Back pain","Very self-critical","Sweet cravings",
                "Salty cravings","Increased appetite","Nausea","Insomnia","Brain fog",
                "Hungry","Calm","Energized","Happy","Enthusiastic","Creative","None"])
        notes = st.text_area("Additional notes (optional)",
                             placeholder="Track anything else — sleep quality, stress level, triggers...")
        if st.form_submit_button("🌙 Log This Day's Data"):
            logged_phase = get_cycle_phase(st.session_state.cycle_data, log_date)
            entry = {"date": log_date, "phase": logged_phase, "mood": mood,
                     "energy": energy_today, "symptoms": symptoms, "notes": notes}
            st.session_state.cycle_data["symptoms_log"].append(entry)
            save_cycle_data(st.session_state.cycle_data)
            st.success(f"✨ Logged data for {log_date.strftime('%B %d, %Y')}")

    st.divider()

    # ── 3. WHAT'S HAPPENING / HOW YOU MIGHT FEEL / WISDOM ─────────
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.caption("**What's happening:**")
        st.write(phase_info["summary"])
        st.caption("**Hormones:**")
        st.write(phase_info["hormones"])
    with info_col2:
        st.caption("**How you might feel:**")
        st.info(phase_info["feeling"])
        st.caption("**Mooncyc's wisdom:**")
        st.success(phase_info["tip"])

    st.divider()

    # ── 4. TODAY'S GUIDANCE (exercise / task focus / AI meditation) ─
    st.subheader("✨ Today's Guidance")
    guide_col1, guide_col2, guide_col3 = st.columns(3)

    with guide_col1:
        st.markdown("### 💪 Exercise")
        ex_rec = get_exercise_recommendation(phase)
        st.info(f"**{ex_rec['type']}**\n\n*{ex_rec['why']}*")

    with guide_col2:
        st.markdown("### 📋 Task Focus")
        st.info(f"**{phase_info['tip']}**")

    with guide_col3:
        st.markdown("### 🧘 AI Meditation")

        recent_mood         = "Neutral"
        recent_symptoms_med = []
        if st.session_state.cycle_data.get("symptoms_log"):
            last_entry          = st.session_state.cycle_data["symptoms_log"][-1]
            recent_mood         = last_entry.get("mood", "Neutral")
            recent_symptoms_med = last_entry.get("symptoms", [])

        if st.button("🧘 Generate My Meditation"):
            with st.spinner("Writing your meditation..."):
                first_meditation = get_initial_meditation(
                    phase, recent_mood, recent_symptoms_med, user_age)
                st.session_state.current_meditation = first_meditation
                st.session_state.meditation_audio   = None

                symptom_str = ", ".join(recent_symptoms_med) if recent_symptoms_med else "no specific symptoms"
                st.session_state.meditation_messages = [
                    {"role": "system",    "content": "You are a compassionate mindfulness guide for menstrual cycle wellness."},
                    {"role": "user",      "content": f"Write a meditation for {phase} phase. Age: {user_age}. Mood: {recent_mood}. Symptoms: {symptom_str}."},
                    {"role": "assistant", "content": first_meditation}
                ]

        if st.session_state.current_meditation:
            with st.expander("📖 Read your meditation", expanded=True):
                st.write(st.session_state.current_meditation)

            if st.button("🔊 Listen to My Meditation"):
                with st.spinner("Generating audio — takes ~10 seconds..."):
                    audio_bytes, error = text_to_speech(st.session_state.current_meditation)
                    if audio_bytes:
                        st.session_state.meditation_audio = audio_bytes
                    else:
                        st.error(f"Audio error: {error}")

            if st.session_state.meditation_audio:
                st.audio(st.session_state.meditation_audio, format="audio/mp3")
                st.caption("🎧 Put on headphones for the best experience")

            if not ELEVENLABS_API_KEY:
                st.caption("💡 Add ELEVENLABS_API_KEY to .env to unlock audio")

            st.markdown("**Not what you needed? Tell me:**")
            with st.form("meditation_refine_form", clear_on_submit=True):
                med_feedback = st.text_input(
                    "What would you like to change?",
                    placeholder="e.g. Make it shorter, more energizing, focus on breathing"
                )
                if st.form_submit_button("🔄 Rewrite Meditation"):
                    if med_feedback:
                        with st.spinner("Rewriting for you..."):
                            new_med, updated_history = refine_meditation(
                                st.session_state.meditation_messages, med_feedback)
                            st.session_state.current_meditation  = new_med
                            st.session_state.meditation_messages = updated_history
                            st.session_state.meditation_audio    = None
                        st.rerun()

    st.divider()

    # ── 5. TODAY'S AI MEAL PLAN ───────────────────────────────────
    st.markdown("### 🍽️ Today's AI Meal Plan")
    st.caption(f"Personalized for your {phase} phase and age by Mooncyc AI")

    recent_symptoms_meal = []
    if st.session_state.cycle_data.get("symptoms_log"):
        recent_symptoms_meal = st.session_state.cycle_data["symptoms_log"][-1].get("symptoms", [])

    if st.button("🍽️ Generate My Meal Plan"):
        with st.spinner("Creating your personalized meal plan..."):
            st.session_state.current_meal_plan = get_llm_meal_plan(
                phase, recent_symptoms_meal, user_age)

    if st.session_state.current_meal_plan:
        meal_plan = st.session_state.current_meal_plan
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown("**Breakfast**"); st.write(meal_plan["breakfast"])
        with m2:
            st.markdown("**Lunch**");     st.write(meal_plan["lunch"])
        with m3:
            st.markdown("**Dinner**");    st.write(meal_plan["dinner"])
        with m4:
            st.markdown("**Snacks**");    st.write(meal_plan["snacks"])
        if meal_plan["why"]:
            st.caption(f"💡 *Why these foods?* {meal_plan['why']}")
        if st.button("🔄 Regenerate Meal Plan"):
            st.session_state.current_meal_plan = None
            st.rerun()

    st.divider()

    # ── 6. INTERMITTENT FASTING ───────────────────────────────────
    st.subheader("⏱️ Intermittent Fasting")
    st.caption("AI-powered fasting guidance based on your cycle phase, symptoms, and age")

    recent_symptoms_fast = []
    if st.session_state.cycle_data.get("symptoms_log"):
        recent_symptoms_fast = st.session_state.cycle_data["symptoms_log"][-1].get("symptoms", [])

    if st.button("⏱️ Should I Fast Today?"):
        with st.spinner("Analyzing your cycle for fasting advice..."):
            raw_advice = get_fasting_advice(phase, day_in_cycle, recent_symptoms_fast, user_age)
            st.session_state.fasting_advice = parse_fasting_advice(raw_advice)

    if st.session_state.fasting_advice:
        fa  = st.session_state.fasting_advice
        rec = fa.get("recommendation", "")
        is_good    = "good" in rec.lower() or "yes" in rec.lower()
        box_color  = "#c8e6c9" if is_good else "#ffe0b2"
        text_color = "#1b5e20" if is_good else "#e65100"
        icon       = "✅" if is_good else "⚠️"

        # Use st.container + individual st.write calls so LLM text is NEVER
        # injected into an f-string with unsafe_allow_html — that was the bug.
        st.markdown(f"""
        <div style="background:{box_color};border-radius:12px;padding:20px 24px;margin:12px 0 4px 0;">
            <p style="color:{text_color};font-size:1rem;font-weight:700;margin:0;">
                {icon} {rec}</p>
        </div>""", unsafe_allow_html=True)

        with st.container():
            if fa.get("max_hours") and fa["max_hours"] not in ("N/A", ""):
                st.markdown(f"**⏱️ Max fasting window:** {fa['max_hours']}")
            st.write(fa.get("reason", ""))
            st.caption(f"💡 {fa.get('tip', '')}")

        st.caption("⚠️ *General guidance only — not medical advice. Consult your doctor before fasting.*")

        if st.button("🔄 Refresh Fasting Advice"):
            st.session_state.fasting_advice = None
            st.rerun()

    st.divider()

else:
    st.info("👈 Set your cycle info in the sidebar to get started")
    st.divider()


# ── 7. ADD NEW TASK ───────────────────────────────────────────
st.subheader("⚔️ Add New Task")
with st.form("task_form", clear_on_submit=True):
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        task_name = st.text_input("Task name", placeholder="e.g. Finish presentation")
        category  = st.selectbox("Category", ["Work","Study","Personal","Exercise","Creative"])
    with t_col2:
        deadline = st.date_input("Deadline")
        hours    = st.number_input("Hours needed", min_value=0.5, max_value=20.0, value=2.0, step=0.5)
    st.caption("**Task intensity** — How mentally/emotionally demanding is this?")
    intensity = st.radio("Intensity level",
        options=["Light (easy, routine)","Moderate (some focus)","Demanding (high focus, stressful)"],
        horizontal=True, label_visibility="collapsed")
    if st.form_submit_button("🌙 Add Task"):
        if task_name:
            new_task = {"task": task_name, "category": category, "deadline": deadline,
                        "hours": hours, "intensity": intensity.split(" ")[0], "completed": False}
            st.session_state.tasks.append(new_task)
            save_tasks(st.session_state.tasks)
            st.success(f"✨ {task_name} added")

st.divider()


# ── 2-WEEK SCHEDULE ───────────────────────────────────────────
if st.session_state.tasks:
    active_tasks = [t for t in st.session_state.tasks if not t.get("completed")]
    if active_tasks:
        st.subheader("📅 Your Next 2 Weeks")
        st.caption("Tasks distributed evenly until their deadlines")
        today   = date.today()
        next_14 = [today + timedelta(days=i) for i in range(14)]
        daily_load = {day: [] for day in next_14}
        for task in active_tasks:
            days_until = (task["deadline"] - today).days
            if days_until <= 0:
                if today in daily_load:
                    daily_load[today].append({"task": task["task"], "hours": task["hours"]})
            else:
                days_to_spread = min(days_until, 14)
                hours_per_day  = round(task["hours"] / days_to_spread, 1)
                for i in range(days_to_spread):
                    day = today + timedelta(days=i)
                    if day in daily_load:
                        daily_load[day].append({"task": task["task"], "hours": hours_per_day})

        df_schedule = pd.DataFrame({
            "Date": [d.strftime("%a %d") for d in next_14],
            "Total Hours": [sum(t["hours"] for t in daily_load[d]) for d in next_14]
        })
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_schedule["Date"], y=df_schedule["Total Hours"],
            marker_color="#d8bfd8",
            text=[f"{h:.1f}h" if h > 0 else "" for h in df_schedule["Total Hours"]],
            textposition="outside"))
        fig.add_hline(y=6, line_dash="dash", line_color="#6b5b7a",
                      annotation_text="6h healthy limit", annotation_position="right")
        fig.update_layout(paper_bgcolor="#F3E4F5", plot_bgcolor="#e8d0ec",
            font=dict(color="#2d1f33"),
            yaxis=dict(title="Hours", range=[0, max(df_schedule["Total Hours"].max()+2, 8)]),
            xaxis=dict(title=""), height=400, margin=dict(t=30, b=40))
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("📋 See daily breakdown"):
            for day in next_14:
                if daily_load[day]:
                    st.markdown(f"**{day.strftime('%A, %B %d')}**")
                    for te in daily_load[day]:
                        st.caption(f"• {te['task']} — {te['hours']}h")
        st.divider()


# ── CYCLE SYMPTOM PATTERN CHART ───────────────────────────────
if st.session_state.cycle_data.get("last_period") and st.session_state.cycle_data.get("symptoms_log"):
    st.subheader("🌙 Your Cycle Symptom Patterns")
    st.caption(f"Tracking patterns across your {cycle_length}-day cycle")

    cycle_days    = list(range(1, cycle_length + 1))
    symptom_counts = {day: defaultdict(int) for day in cycle_days}

    for entry in st.session_state.cycle_data["symptoms_log"]:
        entry_date    = entry["date"]
        days_since_lp = (entry_date - st.session_state.cycle_data["last_period"]).days
        dic           = (days_since_lp % cycle_length) + 1
        if 1 <= dic <= cycle_length:
            for symptom in entry.get("symptoms", []):
                if symptom != "None":
                    symptom_counts[dic][symptom] += 1

    all_symptoms = defaultdict(int)
    for day in symptom_counts.values():
        for s, c in day.items(): all_symptoms[s] += c

    top_symptoms      = sorted(all_symptoms.items(), key=lambda x: x[1], reverse=True)[:3]
    top_symptom_names = [s[0] for s in top_symptoms]

    if top_symptom_names:
        chart_data = {s: [] for s in top_symptom_names}
        for day in cycle_days:
            for s in top_symptom_names:
                chart_data[s].append(symptom_counts[day].get(s, 0))

        fig2   = go.Figure()
        colors = ["#d8bfd8", "#b39eb5", "#c8b8c8"]
        for idx, s in enumerate(top_symptom_names):
            fig2.add_trace(go.Scatter(x=cycle_days, y=chart_data[s],
                mode='lines+markers', name=s,
                line=dict(color=colors[idx], width=3), marker=dict(size=6)))
        fig2.update_layout(paper_bgcolor="#F3E4F5", plot_bgcolor="#e8d0ec",
            font=dict(color="#2d1f33"),
            xaxis=dict(title="Day of Cycle", range=[1, cycle_length]),
            yaxis=dict(title="Times Reported"),
            legend=dict(bgcolor="#e8d0ec", bordercolor="#b39eb5", borderwidth=1),
            height=400, margin=dict(t=30, b=40))
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(f"💡 Based on {len(st.session_state.cycle_data['symptoms_log'])} logged days.")
        st.divider()

        # ── AI CYCLE PATTERN ANALYSIS ─────────────────────────
        st.subheader("🧠 AI Cycle Pattern Analysis")
        st.caption("Your AI coach analyzes your full symptom history and gives tailored advice for next cycle")

        log_count = len(st.session_state.cycle_data["symptoms_log"])
        if log_count < 5:
            st.info(f"📊 Log {5 - log_count} more days to unlock AI cycle analysis")
        else:
            if st.button("🔬 Analyze My Cycle Patterns"):
                with st.spinner("Analyzing your cycle data..."):
                    insights = get_symptom_insights(
                        st.session_state.cycle_data["symptoms_log"], cycle_length, user_age)
                    st.session_state.monthly_insights = insights

            if st.session_state.monthly_insights:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#e8d0ec,#F3E4F5);
                            border:1px solid #b39eb5;border-radius:12px;
                            padding:24px;margin:16px 0;">
                    <p style="color:#2d1f33;white-space:pre-wrap;margin:0;line-height:1.7;">
                        {st.session_state.monthly_insights}</p>
                </div>""", unsafe_allow_html=True)
                if st.button("🔄 Re-analyze"):
                    st.session_state.monthly_insights = None
                    st.rerun()

        st.divider()

        # ── AI NATURAL REMEDIES ───────────────────────────────
        st.subheader("🌿 AI Natural Remedies for Your Symptoms")
        st.caption("Personalized remedies for your exact symptoms, phase, and age")

        all_tracked_symptoms = set()
        for entry in st.session_state.cycle_data["symptoms_log"]:
            for s in entry.get("symptoms", []):
                if s != "None": all_tracked_symptoms.add(s)

        if all_tracked_symptoms:
            if st.button("🌿 Generate Remedies for My Symptoms"):
                with st.spinner("Preparing your personalized remedies..."):
                    remedy_text = get_llm_remedies(
                        list(all_tracked_symptoms), phase or "Follicular", user_age)
                    st.session_state.current_remedy = remedy_text

            if st.session_state.current_remedy:
                st.markdown(f"""
                <div style="background:#F3E4F5;border:1px solid #b39eb5;
                            border-radius:12px;padding:24px;margin:16px 0;">
                    <p style="color:#2d1f33;white-space:pre-wrap;margin:0;line-height:1.8;">
                        {st.session_state.current_remedy}</p>
                </div>""", unsafe_allow_html=True)
                if st.button("🔄 Regenerate Remedies"):
                    st.session_state.current_remedy = None
                    st.rerun()
        else:
            st.info("Log some symptoms above to get your personalized AI remedies.")

        st.caption("⚠️ *Complementary approaches only — not medical advice. Consult a healthcare provider for severe symptoms.*")

    else:
        st.info("No symptom data yet. Start logging above to see patterns emerge!")
else:
    st.info("🌱 Start logging symptoms above to build your cycle pattern database")

st.divider()


# ── ALL ACTIVE TASKS ──────────────────────────────────────────
if st.session_state.tasks:
    active_tasks = [t for t in st.session_state.tasks if not t.get("completed")]
    if active_tasks:
        with st.expander(f"📋 All Active Tasks ({len(active_tasks)})", expanded=False):
            sorted_tasks = sorted(active_tasks, key=lambda x: x["deadline"])
            for task in sorted_tasks:
                col_task, col_actions = st.columns([5, 1])
                with col_task:
                    days_left     = (task["deadline"] - date.today()).days
                    urgency_icon  = "🔴" if days_left <= 2 else "🟡" if days_left <= 5 else "🟢"
                    st.write(f"{urgency_icon} **{task['task']}** — {task.get('category','Task')} — "
                             f"Due: {task['deadline']} — {task['hours']}h — {task['intensity']}")
                with col_actions:
                    if st.button("🗑️", key=f"del_{sorted_tasks.index(task)}"):
                        st.session_state.tasks.remove(task)
                        save_tasks(st.session_state.tasks)
                        st.rerun()
