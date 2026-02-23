import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import random
from datetime import date, timedelta
from collections import defaultdict
import anthropic

# ----------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------
st.set_page_config(
    page_title="Mooncyc",
    page_icon="🌙",
    layout="wide"
)

# ----------------------------------------
# CUSTOM STYLING
# ----------------------------------------
st.markdown("""
    <style>
    .stApp {
        background-color: #6b5b7a;
        color: #f5f0f5;
    }
    [data-testid="stSidebar"] {
        background-color: #524560;
    }
    h1, h2, h3, p, label {
        color: #f5f0f5 !important;
    }
    [data-testid="stDecoration"] { display: none; }
    [data-testid="stHeader"] {
        background-color: transparent;
        display: none;
    }
    [data-testid="stSlider"] > div > div > div > div {
        background: linear-gradient(to right, #d8bfd8, #b39eb5) !important;
    }
    [data-testid="stSlider"] [role="slider"] {
        background-color: #d8bfd8 !important;
        border-color: #d8bfd8 !important;
    }
    div[role="radiogroup"] label div:first-child {
        display: none !important;
    }
    div[role="radiogroup"] label {
        background-color: #524560 !important;
        border: 1.5px solid #d8bfd8 !important;
        border-radius: 20px !important;
        padding: 8px 22px !important;
        margin-right: 10px !important;
        cursor: pointer !important;
        color: #ffffff !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        min-width: 100px !important;
        text-align: center !important;
    }
    div[role="radiogroup"] label:has(input:checked) {
        background-color: #d8bfd8 !important;
        border-color: #ffffff !important;
        color: #4a3f4f !important;
        font-weight: 800 !important;
        box-shadow: 0 0 10px #d8bfd8 !important;
    }
    span[data-baseweb="tag"] {
        background-color: #b39eb5 !important;
        border-color: #d8bfd8 !important;
    }
    span[data-baseweb="tag"] span[class] {
        color: #ffffff !important;
    }
    span[data-baseweb="tag"] button {
        color: #ffffff !important;
    }
    [data-testid="stFormSubmitButton"] > button {
        background-color: #d8bfd8 !important;
        color: #4a3f4f !important;
        border: 2px solid #b39eb5 !important;
        border-radius: 10px !important;
        width: 100% !important;
        padding: 1.2rem 2rem !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        margin-top: 20px !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #b39eb5 !important;
        color: white !important;
    }
    div.stButton > button {
        background-color: #b39eb5 !important;
        color: #ffffff !important;
        border: 1px solid #d8bfd8 !important;
        border-radius: 8px !important;
    }
    div.stButton > button:hover {
        background-color: #d8bfd8 !important;
        color: #4a3f4f !important;
    }
    </style>
""", unsafe_allow_html=True)


# ----------------------------------------
# STORAGE
# ----------------------------------------
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
    return {
        "last_period": None,
        "cycle_length": 28,
        "period_length": 5,
        "symptoms_log": []
    }


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


if "cycle_data" not in st.session_state:
    st.session_state.cycle_data = load_cycle_data()

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()


# ----------------------------------------
# LLM INTEGRATION
# ----------------------------------------

def get_claude_client():
    """
    Initialize Claude API client
    User pastes their API key in the sidebar
    """
    api_key = st.session_state.get("anthropic_api_key")
    if not api_key:
        return None
    try:
        return anthropic.Anthropic(api_key=api_key)
    except:
        return None


def generate_meditation_with_llm(phase, symptoms, energy):
    """
    LLM INTEGRATION POINT 1
    Uses Claude to generate personalized meditation script
    """
    client = get_claude_client()
    if not client:
        return get_meditation_fallback(phase)
    
    try:
        prompt = f"""You are a wellness coach specializing in menstrual health.

Current situation:
- Cycle phase: {phase}
- Symptoms: {', '.join(symptoms) if symptoms else 'None'}
- Energy level: {energy}/5

Create a personalized 5-minute guided meditation script. Format:

**Title:** [Engaging title]
**Duration:** 5 minutes

[Full meditation script with breath cues, visualizations, and affirmations]

Make it gentle, empowering, and specifically tailored to this phase and these symptoms."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "script": message.content[0].text,
            "generated_by": "Claude AI"
        }
    except:
        return get_meditation_fallback(phase)


def generate_meal_plan_with_llm(phase, symptoms):
    """
    LLM INTEGRATION POINT 2
    Uses Claude to generate personalized meal plan
    """
    client = get_claude_client()
    if not client:
        return get_meal_plan_fallback(phase)
    
    try:
        prompt = f"""You are a nutritionist specializing in menstrual cycle nutrition.

Current situation:
- Cycle phase: {phase}
- Current symptoms: {', '.join(symptoms) if symptoms else 'None'}

Create a one-day meal plan optimized for this phase and symptoms.

Format:
🍳 **Breakfast:** [meal with emoji]
🥗 **Lunch:** [meal with emoji]
🍝 **Dinner:** [meal with emoji]
🍎 **Snacks:** [snacks with emoji]

💡 **Why these foods?** [1-2 sentence scientific explanation]

Be specific with meal names, make them appealing, and base recommendations on hormonal science."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = message.content[0].text
        
        # Parse the response
        lines = content.split('\n')
        meal_plan = {
            "breakfast": "Generating...",
            "lunch": "Generating...",
            "dinner": "Generating...",
            "snacks": "Generating...",
            "why": "Generating..."
        }
        
        for line in lines:
            if "Breakfast:" in line:
                meal_plan["breakfast"] = line.split("Breakfast:")[-1].strip()
            elif "Lunch:" in line:
                meal_plan["lunch"] = line.split("Lunch:")[-1].strip()
            elif "Dinner:" in line:
                meal_plan["dinner"] = line.split("Dinner:")[-1].strip()
            elif "Snacks:" in line:
                meal_plan["snacks"] = line.split("Snacks:")[-1].strip()
            elif "Why these foods?" in line:
                meal_plan["why"] = line.split("?")[-1].strip()
        
        meal_plan["generated_by"] = "Claude AI"
        return meal_plan
        
    except Exception as e:
        st.error(f"LLM Error: {str(e)}")
        return get_meal_plan_fallback(phase)


def generate_remedy_with_llm(symptom):
    """
    LLM INTEGRATION POINT 3
    Uses Claude to suggest natural remedies for any symptom
    """
    client = get_claude_client()
    if not client:
        return get_remedy_fallback(symptom)
    
    try:
        prompt = f"""You are a wellness advisor specializing in natural, evidence-based remedies for menstrual cycle symptoms.

Symptom: {symptom}

Provide a natural remedy in this exact format:

**Remedy:** [emoji] [Short remedy name]
**How:** [Specific instructions - what to do, when, how much]
**Why it works:** [Scientific explanation in 1-2 sentences]

Focus on safe, natural approaches. Be specific and actionable."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = message.content[0].text
        
        remedy = {
            "remedy": "Generating...",
            "how": "Generating...",
            "why": "Generating..."
        }
        
        lines = content.split('\n')
        for line in lines:
            if "Remedy:" in line:
                remedy["remedy"] = line.split("Remedy:")[-1].strip()
            elif "How:" in line:
                remedy["how"] = line.split("How:")[-1].strip()
            elif "Why it works:" in line or "Why:" in line:
                remedy["why"] = line.split(":")[-1].strip()
        
        remedy["generated_by"] = "Claude AI"
        return remedy
        
    except:
        return get_remedy_fallback(symptom)


# ----------------------------------------
# FALLBACK FUNCTIONS (when LLM not available)
# ----------------------------------------

def get_meditation_fallback(phase):
    meditations = {
        "Menstrual": {
            "script": """**Rest & Release Meditation**
**Duration:** 5 minutes

Find a comfortable position, lying down or seated with support.

Close your eyes. Take three deep breaths — in through your nose, out through your mouth.

Place your hands on your lower belly. Feel the warmth of your palms.

Say to yourself: *"My body is doing sacred work. I honor this time of release."*

Visualize a warm, golden light filling your belly — soothing, melting away tension.

With each exhale, imagine releasing what no longer serves you.

Rest here for 3-5 minutes. You are exactly where you need to be.""",
            "generated_by": "Pre-written"
        },
        "Follicular": {
            "script": """**Energy & Possibility Meditation**
**Duration:** 5 minutes

Sit upright with your spine tall. Roll your shoulders back.

Take a deep breath in — feel your lungs expand. Exhale fully.

Say to yourself: *"I am rising. I am ready. I am capable."*

Visualize a bright, spring-green light starting at your feet, rising up through your body.

With each breath, feel energy building — like a seed sprouting toward the sun.

Notice any new ideas or intentions that arise. Welcome them.

Take one final deep breath. Open your eyes feeling refreshed.""",
            "generated_by": "Pre-written"
        },
        "Ovulation": {
            "script": """**Confidence & Clarity Meditation**
**Duration:** 3 minutes

Stand tall or sit upright. Feel your strength.

Take three powerful breaths — sharp inhale, full exhale.

Say to yourself: *"I am powerful. I am magnetic. I am clear."*

Visualize a bright white light at the crown of your head — radiating confidence outward.

Feel yourself standing in your full power. You have everything you need.

This is your moment. Use it.

Open your eyes when ready.""",
            "generated_by": "Pre-written"
        },
        "Luteal": {
            "script": """**Grounding & Compassion Meditation**
**Duration:** 7 minutes

Lie down or sit with your back supported. Close your eyes.

Take slow, deep breaths — 4 counts in, 4 counts out.

Say to yourself: *"I am allowed to slow down. I am enough as I am."*

Visualize roots growing from your body into the earth — grounding you, holding you.

With each exhale, release self-criticism. With each inhale, breathe in gentleness.

Place your hand on your heart. Feel your heartbeat.

You are doing your best. That is enough.

Rest here as long as you need.""",
            "generated_by": "Pre-written"
        }
    }
    return meditations.get(phase, meditations["Follicular"])


def get_meal_plan_fallback(phase):
    plans = {
        "Menstrual": {
            "breakfast": "🍳 Scrambled eggs with spinach and avocado",
            "lunch": "🥩 Grilled steak salad with dark leafy greens",
            "dinner": "🐟 Baked salmon with roasted sweet potato",
            "snacks": "🍫 Dark chocolate, dates, handful of almonds",
            "why": "Replenish iron lost during bleeding. Magnesium reduces cramps.",
            "generated_by": "Pre-written"
        },
        "Follicular": {
            "breakfast": "🥣 Greek yogurt with berries and flaxseeds",
            "lunch": "🥗 Grilled chicken quinoa bowl with broccoli",
            "dinner": "🍜 Miso soup with tofu and fermented vegetables",
            "snacks": "🥕 Carrot sticks with hummus, apple slices",
            "why": "Support rising estrogen with fiber and fermented foods.",
            "generated_by": "Pre-written"
        },
        "Ovulation": {
            "breakfast": "🥑 Avocado toast with poached egg and tomato",
            "lunch": "🌯 Whole grain wrap with grilled veggies and chickpeas",
            "dinner": "🍗 Herb-roasted chicken with quinoa and asparagus",
            "snacks": "🍊 Orange slices, bell pepper strips, mixed nuts",
            "why": "Balance peak estrogen. Antioxidants support detoxification.",
            "generated_by": "Pre-written"
        },
        "Luteal": {
            "breakfast": "🥞 Oatmeal with banana, cinnamon, and walnuts",
            "lunch": "🍠 Sweet potato and black bean bowl with brown rice",
            "dinner": "🍝 Whole wheat pasta with lentil bolognese",
            "snacks": "🍌 Banana with almond butter, yogurt with honey",
            "why": "Complex carbs stabilize blood sugar and serotonin.",
            "generated_by": "Pre-written"
        }
    }
    return plans.get(phase, plans["Follicular"])


def get_remedy_fallback(symptom):
    return {
        "remedy": "🌿 General wellness approach",
        "how": "Hydrate well, rest when needed, and consider gentle movement.",
        "why": "Basic self-care supports overall wellbeing during hormonal changes.",
        "generated_by": "Pre-written (symptom not in database)"
    }


# ----------------------------------------
# CORE FUNCTIONS
# ----------------------------------------

def get_cycle_phase(cycle_data, target_date=None):
    if not cycle_data["last_period"]:
        return None
    
    if target_date is None:
        target_date = date.today()
    
    days_since = (target_date - cycle_data["last_period"]).days
    day_in_cycle = days_since % cycle_data["cycle_length"]
    
    period_len = cycle_data["period_length"]
    
    if day_in_cycle < period_len:
        return "Menstrual"
    elif day_in_cycle < 14:
        return "Follicular"
    elif day_in_cycle < 16:
        return "Ovulation"
    else:
        return "Luteal"


def get_phase_energy_level(phase):
    energy_map = {
        "Menstrual": 2,
        "Follicular": 4,
        "Ovulation": 5,
        "Luteal": 3
    }
    return energy_map.get(phase, 3)


def get_phase_description(phase):
    descriptions = {
        "Menstrual": {
            "emoji": "🩸",
            "summary": "Your body is shedding the uterine lining",
            "hormones": "Both estrogen and progesterone are at their lowest",
            "feeling": "It's completely normal to feel drained, emotional, or want to curl up in bed. Your body is doing intense biological work — be kind to yourself.",
            "tip": "This is your body's natural reset. Honor the need for rest, warmth, and gentle movement."
        },
        "Follicular": {
            "emoji": "🌱",
            "summary": "Your body is preparing to release an egg",
            "hormones": "Estrogen is rising steadily",
            "feeling": "You might notice your mood lifting, energy returning, and skin glowing. This is your 'spring' phase — new ideas and motivation come naturally.",
            "tip": "Harness this energy! Start new projects, have difficult conversations, tackle your hardest tasks."
        },
        "Ovulation": {
            "emoji": "✨",
            "summary": "Your body releases an egg — peak fertility",
            "hormones": "Estrogen and testosterone peak together",
            "feeling": "This is your superpower window. You feel confident, social, strong, and clear-headed. Everything feels easier right now.",
            "tip": "Schedule presentations, workouts, social events, and challenging tasks here. You're literally at your best."
        },
        "Luteal": {
            "emoji": "🌙",
            "summary": "Your body prepares for either pregnancy or menstruation",
            "hormones": "Progesterone rises, then both hormones drop sharply before your period",
            "feeling": "It's completely normal to feel drained, irritable, or foggy — especially in the second half. The hormone crash is real and it's not in your head.",
            "tip": "This is your 'autumn' phase. Focus on finishing what you started, not starting new things. Rest is productive."
        }
    }
    return descriptions.get(phase, descriptions["Follicular"])


def get_exercise_recommendation(phase):
    recommendations = {
        "Menstrual": {
            "type": "🧘 Gentle yoga, walking, stretching",
            "why": "Low progesterone and estrogen — your body needs rest and gentle movement."
        },
        "Follicular": {
            "type": "🏃 HIIT, running, strength training",
            "why": "Rising estrogen boosts energy and muscle building capacity."
        },
        "Ovulation": {
            "type": "💪 Peak performance training, heavy lifting",
            "why": "Testosterone and estrogen peak — your strongest days."
        },
        "Luteal": {
            "type": "🚴 Moderate cardio, pilates, swimming",
            "why": "Progesterone rises — focus on steady-state endurance."
        }
    }
    return recommendations.get(phase, recommendations["Follicular"])


# ----------------------------------------
# SIDEBAR
# ----------------------------------------
with st.sidebar:
    
    if "cycle_data" not in st.session_state:
        st.session_state.cycle_data = load_cycle_data()
    
    if "tasks" not in st.session_state:
        st.session_state.tasks = load_tasks()

    st.title("🌙 Mooncyc")
    st.caption("*Your daily organizer buddy who gets your cycle*")
    st.divider()
    
    # LLM API KEY INPUT
    st.subheader("🤖 AI Features (Optional)")
    st.caption("Enable Claude AI for personalized recommendations")
    
    api_key_input = st.text_input(
        "Anthropic API Key",
        type="password",
        help="Get your key from console.anthropic.com",
        value=st.session_state.get("anthropic_api_key", "")
    )
    
    if api_key_input:
        st.session_state["anthropic_api_key"] = api_key_input
        if get_claude_client():
            st.success("✅ AI enabled")
        else:
            st.error("❌ Invalid API key")
    else:
        st.info("💡 App works without API key (uses pre-written content)")
    
    st.divider()
    
    st.subheader("🩸 Your Cycle Setup")
    
    last_period = st.date_input(
        label="Last period started",
        value=st.session_state.cycle_data.get("last_period") or date.today()
    )
    
    cycle_length = st.slider(
        label="Average cycle length (days)",
        min_value=21,
        max_value=35,
        value=st.session_state.cycle_data.get("cycle_length", 28)
    )
    
    period_length = st.slider(
        label="Period duration (days)",
        min_value=3,
        max_value=7,
        value=st.session_state.cycle_data.get("period_length", 5)
    )
    
    if st.button("💾 Save Cycle Info"):
        st.session_state.cycle_data["last_period"] = last_period
        st.session_state.cycle_data["cycle_length"] = cycle_length
        st.session_state.cycle_data["period_length"] = period_length
        save_cycle_data(st.session_state.cycle_data)
        st.success("✨ Saved")


# ----------------------------------------
# MAIN AREA
# ----------------------------------------
st.title("🌙 Mooncyc")
st.subheader("*Your daily organizer buddy who gets your cycle*")
st.divider()

# Get current symptoms for LLM context
current_symptoms = []
if st.session_state.cycle_data.get("symptoms_log"):
    latest_log = sorted(
        st.session_state.cycle_data["symptoms_log"],
        key=lambda x: x["date"],
        reverse=True
    )
    if latest_log:
        current_symptoms = latest_log[0].get("symptoms", [])

# CURRENT PHASE INFO
phase = get_cycle_phase(st.session_state.cycle_data)

if phase:
    phase_info = get_phase_description(phase)
    
    st.markdown(f"### {phase_info['emoji']} Current Phase: {phase}")
    
    energy = get_phase_energy_level(phase)
    st.progress(energy / 5.0, text=f"Energy: {energy}/5")
    
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
    
    # TODAY'S GUIDANCE
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
        st.markdown("### 🧘 Meditation")
        
        if st.button("✨ Generate Personalized Meditation"):
            with st.spinner("Claude is creating your meditation..."):
                meditation = generate_meditation_with_llm(phase, current_symptoms, energy)
                st.session_state["current_meditation"] = meditation
        
        if "current_meditation" in st.session_state:
            meditation = st.session_state["current_meditation"]
            with st.expander(f"**Your Personalized Meditation**"):
                st.write(meditation["script"])
                st.caption(f"*Generated by: {meditation['generated_by']}*")
        else:
            st.caption("Click above to generate a meditation")
    
    st.divider()
    
    # MEAL PLAN
    st.markdown("### 🍽️ Today's Meal Plan")
    
    col_meal_info, col_meal_button = st.columns([3, 1])
    with col_meal_info:
        st.caption(f"Optimized for your {phase} phase")
    with col_meal_button:
        if st.button("🔄 Generate New Plan"):
            with st.spinner("Claude is crafting your meal plan..."):
                meal_plan = generate_meal_plan_with_llm(phase, current_symptoms)
                st.session_state["current_meal_plan"] = meal_plan
    
    # Get or generate meal plan
    if "current_meal_plan" not in st.session_state:
        meal_plan = get_meal_plan_fallback(phase)
        st.session_state["current_meal_plan"] = meal_plan
    else:
        meal_plan = st.session_state["current_meal_plan"]
    
    meal_col1, meal_col2, meal_col3, meal_col4 = st.columns(4)
    
    with meal_col1:
        st.markdown("**Breakfast**")
        st.write(meal_plan["breakfast"])
    
    with meal_col2:
        st.markdown("**Lunch**")
        st.write(meal_plan["lunch"])
    
    with meal_col3:
        st.markdown("**Dinner**")
        st.write(meal_plan["dinner"])
    
    with meal_col4:
        st.markdown("**Snacks**")
        st.write(meal_plan["snacks"])
    
    st.caption(f"💡 *Why these foods?* {meal_plan['why']}")
    st.caption(f"*Source: {meal_plan.get('generated_by', 'Pre-written')}*")
    
    st.divider()

else:
    st.info("👈 Set your cycle info in the sidebar to get started")
    st.divider()

# SYMPTOM TRACKER
st.subheader("📝 How Are You Feeling?")
st.caption("Track symptoms for any day — build your cycle pattern database")

with st.form("symptom_form"):
    log_date = st.date_input(
        "Which day are you logging?",
        value=date.today(),
        max_value=date.today(),
        help="Select today or a past date to build your symptom history"
    )
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        mood = st.select_slider(
            "Mood",
            options=[
                "😭 Terrible", 
                "😢 Low", 
                "😔 Down",
                "😐 Neutral", 
                "🙂 Okay",
                "😊 Good", 
                "😄 Great",
                "🌟 Amazing"
            ],
            value="😐 Neutral"
        )
        
        energy_today = st.slider(
            "Energy level",
            min_value=1,
            max_value=5,
            value=3
        )
    
    with col_b:
        symptoms = st.multiselect(
            "Symptoms (if any)",
            options=[
                "Cramps", "Bloating", "Headache", "Irritable", "Stressed",
                "Tired", "Low Energy", "Pissed", "Intolerant", "Migraine",
                "Fatigue", "Irritability", "Anxiety", "Depression",
                "Breast tenderness", "Acne", "Back pain", "Very self-critical",
                "Sweet cravings", "Salty cravings", "Increased appetite",
                "Nausea", "Insomnia", "Brain fog", "Hungry", "Calm",
                "Energized", "Happy", "Enthusiastic", "Creative", "None"
            ]
        )
    
    notes = st.text_area(
        "Additional notes (optional)",
        placeholder="Track anything else — sleep quality, stress level, specific triggers...",
        help="Mooncyc's AI will learn your patterns over time from these notes"
    )
    
    if st.form_submit_button("🌙 Log This Day's Data"):
        logged_phase = get_cycle_phase(st.session_state.cycle_data, log_date)
        
        entry = {
            "date": log_date,
            "phase": logged_phase,
            "mood": mood,
            "energy": energy_today,
            "symptoms": symptoms,
            "notes": notes
        }
        st.session_state.cycle_data["symptoms_log"].append(entry)
        save_cycle_data(st.session_state.cycle_data)
        st.success(f"✨ Logged data for {log_date.strftime('%B %d, %Y')}")

st.divider()

# ADD TASK
st.subheader("⚔️ Add New Task")

with st.form("task_form", clear_on_submit=True):
    t_col1, t_col2 = st.columns(2)
    
    with t_col1:
        task_name = st.text_input(
            "Task name",
            placeholder="e.g. Finish presentation"
        )
        category = st.selectbox(
            "Category",
            ["Work", "Study", "Personal", "Exercise", "Creative"]
        )
    
    with t_col2:
        deadline = st.date_input("Deadline")
        hours = st.number_input(
            "Hours needed",
            min_value=0.5,
            max_value=20.0,
            value=2.0,
            step=0.5
        )
    
    st.caption("**Task intensity** — How mentally/emotionally demanding is this?")
    intensity = st.radio(
        "Intensity level",
        options=["Light (easy, routine)", "Moderate (some focus)", "Demanding (high focus, stressful)"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if st.form_submit_button("🌙 Add Task"):
        if task_name:
            intensity_clean = intensity.split(" ")[0]
            
            new_task = {
                "task": task_name,
                "category": category,
                "deadline": deadline,
                "hours": hours,
                "intensity": intensity_clean,
                "completed": False
            }
            st.session_state.tasks.append(new_task)
            save_tasks(st.session_state.tasks)
            st.success(f"✨ {task_name} added")

st.divider()

# 2-WEEK SCHEDULE
if st.session_state.tasks:
    active_tasks = [t for t in st.session_state.tasks if not t.get("completed")]
    
    if active_tasks:
        st.subheader("📅 Your Next 2 Weeks")
        st.caption("AI has distributed your tasks evenly until their deadlines")
        
        today = date.today()
        next_14 = [today + timedelta(days=i) for i in range(14)]
        daily_load = {day: [] for day in next_14}
        
        for task in active_tasks:
            days_until = (task["deadline"] - today).days
            
            if days_until <= 0:
                if today in daily_load:
                    daily_load[today].append({
                        "task": task["task"],
                        "hours": task["hours"]
                    })
            else:
                days_to_spread = min(days_until, 14)
                hours_per_day = round(task["hours"] / days_to_spread, 1)
                
                for i in range(days_to_spread):
                    day = today + timedelta(days=i)
                    if day in daily_load:
                        daily_load[day].append({
                            "task": task["task"],
                            "hours": hours_per_day
                        })
        
        df_schedule = pd.DataFrame({
            "Date": [d.strftime("%a %d") for d in next_14],
            "Total Hours": [sum([t["hours"] for t in daily_load[d]]) for d in next_14]
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_schedule["Date"],
            y=df_schedule["Total Hours"],
            marker_color="#d8bfd8",
            text=[f"{h:.1f}h" if h > 0 else "" for h in df_schedule["Total Hours"]],
            textposition="outside"
        ))
        
        fig.add_hline(
            y=6,
            line_dash="dash",
            line_color="#f5f0f5",
            annotation_text="6h healthy limit",
            annotation_position="right"
        )
        
        fig.update_layout(
            paper_bgcolor="#6b5b7a",
            plot_bgcolor="#524560",
            font=dict(color="#f5f0f5"),
            yaxis=dict(title="Hours of work", range=[0, max(df_schedule["Total Hours"].max() + 2, 8)]),
            xaxis=dict(title=""),
            height=400,
            margin=dict(t=30, b=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📋 See daily breakdown"):
            for day in next_14:
                if daily_load[day]:
                    st.markdown(f"**{day.strftime('%A, %B %d')}**")
                    for task_entry in daily_load[day]:
                        st.caption(f"• {task_entry['task']} — {task_entry['hours']}h")
        
        st.divider()

# CYCLE SYMPTOM PATTERN
if st.session_state.cycle_data.get("last_period") and st.session_state.cycle_data.get("symptoms_log"):
    st.subheader("🌙 Your Cycle Symptom Patterns")
    st.caption(f"Tracking patterns across your {cycle_length}-day cycle")
    
    cycle_days = list(range(1, cycle_length + 1))
    symptom_counts = {day: defaultdict(int) for day in cycle_days}
    
    for entry in st.session_state.cycle_data["symptoms_log"]:
        entry_date = entry["date"]
        days_since = (entry_date - st.session_state.cycle_data["last_period"]).days
        day_in_cycle = (days_since % cycle_length) + 1
        
        if 1 <= day_in_cycle <= cycle_length:
            for symptom in entry.get("symptoms", []):
                if symptom != "None":
                    symptom_counts[day_in_cycle][symptom] += 1
    
    all_symptoms = defaultdict(int)
    for day in symptom_counts.values():
        for symptom, count in day.items():
            all_symptoms[symptom] += count
    
    top_symptoms = sorted(all_symptoms.items(), key=lambda x: x[1], reverse=True)[:3]
    top_symptom_names = [s[0] for s in top_symptoms]
    
    if top_symptom_names:
        chart_data = {symptom: [] for symptom in top_symptom_names}
        
        for day in cycle_days:
            for symptom in top_symptom_names:
                chart_data[symptom].append(symptom_counts[day].get(symptom, 0))
        
        fig2 = go.Figure()
        
        colors = ["#d8bfd8", "#b39eb5", "#c8b8c8"]
        
        for idx, symptom in enumerate(top_symptom_names):
            fig2.add_trace(go.Scatter(
                x=cycle_days,
                y=chart_data[symptom],
                mode='lines+markers',
                name=symptom,
                line=dict(color=colors[idx], width=3),
                marker=dict(size=6)
            ))
        
        fig2.update_layout(
            paper_bgcolor="#6b5b7a",
            plot_bgcolor="#524560",
            font=dict(color="#f5f0f5"),
            xaxis=dict(title="Day of Cycle", range=[1, cycle_length]),
            yaxis=dict(title="Times Reported"),
            legend=dict(bgcolor="#524560", bordercolor="#d8bfd8", borderwidth=1),
            height=400,
            margin=dict(t=30, b=40)
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        st.caption(f"💡 **Insights:** Based on {len(st.session_state.cycle_data['symptoms_log'])} logged days. Keep tracking to see clearer patterns!")
        
        st.divider()
        
        # NATURAL REMEDIES WITH LLM
        st.subheader("🌿 Natural Remedies for Your Symptoms")
        st.caption("AI-powered remedy suggestions — automatically updates as you track new symptoms")
        
        # Get all unique symptoms
        all_tracked_symptoms = set()
        for entry in st.session_state.cycle_data["symptoms_log"]:
            for symptom in entry.get("symptoms", []):
                if symptom != "None":
                    all_tracked_symptoms.add(symptom)
        
        for symptom in sorted(all_tracked_symptoms):
            with st.expander(f"💚 {symptom} — Natural Relief"):
                if f"remedy_{symptom}" not in st.session_state:
                    if st.button(f"Generate remedy for {symptom}", key=f"gen_{symptom}"):
                        with st.spinner("Claude is researching remedies..."):
                            remedy = generate_remedy_with_llm(symptom)
                            st.session_state[f"remedy_{symptom}"] = remedy
                
                if f"remedy_{symptom}" in st.session_state:
                    remedy = st.session_state[f"remedy_{symptom}"]
                    st.markdown(f"**{remedy['remedy']}**")
                    st.write(f"**How:** {remedy['how']}")
                    st.info(f"**Why it works:** {remedy['why']}")
                    st.caption(f"*Source: {remedy.get('generated_by', 'Pre-written')}*")
                else:
                    st.caption("Click the button above to generate a personalized remedy")
        
        st.caption("⚠️ *These are complementary approaches, not medical advice. Consult a healthcare provider for severe symptoms.*")
    
    else:
        st.info("No symptom data yet. Start logging above to see patterns emerge!")

else:
    st.info("🌱 Start logging symptoms above to build your cycle pattern database")

st.divider()

# ALL ACTIVE TASKS
if st.session_state.tasks:
    active_tasks = [t for t in st.session_state.tasks if not t.get("completed")]
    
    if active_tasks:
        with st.expander(f"📋 All Active Tasks ({len(active_tasks)})", expanded=False):
            sorted_tasks = sorted(active_tasks, key=lambda x: x["deadline"])
            
            for task in sorted_tasks:
                col_task, col_actions = st.columns([5, 1])
                
                with col_task:
                    days_left = (task["deadline"] - date.today()).days
                    urgency_icon = "🔴" if days_left <= 2 else "🟡" if days_left <= 5 else "🟢"
                    
                    st.write(
                        f"{urgency_icon} **{task['task']}** — "
                        f"{task.get('category', 'Task')} — "
                        f"Due: {task['deadline']} — "
                        f"{task['hours']}h — "
                        f"{task['intensity']}"
                    )
                
                with col_actions:
                    if st.button("🗑️", key=f"del_{sorted_tasks.index(task)}"):
                        st.session_state.tasks.remove(task)
                        save_tasks(st.session_state.tasks)
                        st.rerun()