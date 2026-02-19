# 🌙 Mooncyc

**AI-powered app to sync your productivity with your menstrual cycle**

## What is this?

I made this for my AI Prototyping class. The idea is simple: your energy and mood change throughout your cycle, so why don't productivity apps care about that?

Mooncyc tracks your cycle and helps you plan tasks on days when you'll actually have the energy to do them. Plus, it suggests workouts, meals, and natural remedies based on what phase you're in.

## What it does

- Tracks which phase of your cycle you're in (menstrual, follicular, ovulation, luteal)
- Spreads out your tasks across the next 2 weeks based on energy levels
- Suggests exercises, meals, and meditations for each phase
- Lets you log symptoms and shows patterns over time
- **NEW:** Uses Claude AI to generate personalized recommendations

## The AI part (the cool part)

The app works fine without AI, but if you add an Anthropic API key, it can:

1. **Generate custom meditations** based on how you're feeling that day
2. **Create meal plans** that match your symptoms + cycle phase
3. **Suggest natural remedies** for any symptom you track

I used the Anthropic API to make these features. The app sends your current phase and symptoms to Claude, and Claude sends back personalized advice.

## How to run it

```bash
# 1. Clone this repo
git clone https://github.com/YOUR-USERNAME/mooncyc-prototype.git
cd mooncyc-prototype

# 2. Create environment
micromamba create -n mooncyc python=3.11
micromamba activate mooncyc

# 3. Install stuff
pip install -r requirements.txt

# 4. Run it
streamlit run app.py
```

Then open the link it gives you (usually `http://localhost:8501`)

## Files in here

- `app.py` - The main code
- `requirements.txt` - List of Python packages needed
- `cycle_data.json` - Saves your cycle data (created when you use the app)
- `tasks.json` - Saves your tasks (created when you use the app)

## Widgets I used (for the assignment)

These are Streamlit widgets we didn't cover in class:

- `st.date_input` - For picking dates (cycle tracking)
- `st.select_slider` - The emoji mood slider
- `st.multiselect` - Picking multiple symptoms
- `st.progress` - Energy bar visualization
- `st.expander` - Collapsible sections for meditations/remedies
- `st.text_input(type="password")` - For the API key
- Plotly charts - Interactive graphs

## What I learned

- How to connect a Streamlit app to an LLM API (Claude)
- How to make the app work even without the API (fallback functions)
- How to store data in JSON files so it persists
- How to calculate cycle phases from dates
- Prompt engineering - getting Claude to format responses consistently

## Limitations / What could be better

- Right now it's just me using it (no user accounts)
- The AI responses aren't perfect - sometimes the formatting gets messy
- No actual ML model predicting symptoms (it just shows patterns)
- Can't export tasks to Google Calendar
- The meal plans are nice but not actual recipes

## If I had more time

- Add actual pattern prediction with ML
- Make it work on mobile
- Add a "share your remedies" feature
- Connect to calendar apps
- Make the AI remember what worked for you in past cycles

---

Made for MIBA Prototyping with AI class, February 2025
