# 🌙 Mooncyc

**AI-powered app to sync your productivity with your menstrual cycle**

## What is this?

A Prototype that connects woman with their body and makes them more aware of how the menstrual cycle can affect their daily file.
The idea is simple: your energy and mood change throughout your cycle, so why don't productivity apps care about that?

Mooncyc tracks your cycle and helps you plan tasks on days when you'll actually have the energy to do them.
It will tell how you are expected to feel depending on the phase of your cycle, it will help you to get to know your body. 
It suggests workouts, meals, and natural remedies based on what phase you're in.

## What it does

- Tracks which phase of your cycle you're in (menstrual, follicular, ovulation, luteal)
- Spreads out your tasks across the next 2 weeks based on energy levels
- Suggests exercises, meals, and meditations for each phase
- Lets you log symptoms and shows patterns over time
- Uses Claude AI to generate personalized recommendations:
  
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

## Widgets used

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

## Limitations

- Right now it's just me using it (no user accounts)
- The AI responses aren't perfect, you should not consider this a doctor substitute
- Can't export tasks from and to Google Calendar
- The meal plans are nice but not actual recipes

## If I had more time

- Add actual pattern prediction with ML
- Make it work on mobile
- Add a "share your remedies" feature
- Connect to calendar apps
- Make the AI remember what worked for you in past cycles

---

---

# 🌙 Mooncyc v2

**AI-powered app to sync your productivity, wellness, and nutrition with your menstrual cycle**

## What changed in v2?

This second version goes much deeper than v1. Instead of rule-based suggestions, everything is now powered by a real LLM pipeline using **Cohere** (`command-r-plus-08-2024`). The app personalizes recommendations based on your cycle phase, logged symptoms, and age.

### AI-powered features (Cohere)

1. **AI Meditation** — generates a personalized script based on your phase, mood, and symptoms. You can refine it by giving feedback and it rewrites it keeping the full conversation history (multi-turn LLM pipeline)
2. **Audio Meditation** — converts the script to speech using ElevenLabs TTS
3. **AI Meal Plan** — structured output parsed by Python into a 4-column breakfast/lunch/dinner/snacks display
4. **Intermittent Fasting Advisor** — the LLM reasons about whether fasting is safe today based on your cycle day, symptoms, and age
5. **AI Natural Remedies** — generates remedies for your exact combination of tracked symptoms
6. **Cycle Pattern Analyzer** — pre-processes all your logged symptom history in Python, then sends a structured summary to the LLM for personalized insights

## How to run v2 locally
```bash
streamlit run app_v2.py
```

Add a `.env` file with:
```
COHERE_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
```

## API keys needed

| Key | Where to get it | Required? |
|-----|----------------|-----------|
| `COHERE_API_KEY` | cohere.com → free trial | Yes, for all AI features |
| `ELEVENLABS_API_KEY` | elevenlabs.io → free tier | No, only for audio meditation |

## What I learned in v2

- How to build a multi-turn LLM pipeline (conversation history for iterative refinement)
- How to prompt an LLM for structured output and parse it with Python
- How to pre-process data in Python before sending it to an LLM
- How to integrate TTS audio into a Streamlit app
- That API model names go deprecated — always check you're using a current one