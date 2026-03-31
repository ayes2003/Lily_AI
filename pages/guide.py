import streamlit as st
import json
import datetime
import ollama
import time
import os
import random
from core.memory import save_memory

def load_user_data():
    """Fetch the logged-in user's data from our local JSON DB."""
    user_id = st.session_state.get('user_id')
    if not user_id: return None
    try:
        if os.path.exists("data/users.json"):
            with open("data/users.json", "r") as f:
                db = json.load(f)
                return db.get(user_id)
    except Exception:
        return None
    return None

def show():
    user_data = load_user_data()
    
    if not user_data:
        st.warning("⚠️ No active profile found. Please tap your Secret Friend to log in.")
        return

    # --- 1. DATA & CONTEXT INITIALIZATION ---
    today = str(datetime.date.today())
    profile = user_data.get('profile', {})
    name = profile.get('name', 'User')
    g_name = profile.get('guardian_name', 'Guardian')
    user_id = st.session_state.get('user_id')
    
    checkin_mood = st.session_state.get('current_mood', 'neutral').lower()
    checkin_score = st.session_state.get('wellness_percent', 75)

    if 'current_habits' not in st.session_state or st.session_state.get('last_cleared_date') != today:
        st.session_state.current_habits = user_data.get('habits', [])
        st.session_state.last_cleared_date = today

    # --- 2. ADAPTIVE HEADER ---
    st.markdown(f"""
        <div style="background:#1C2128; padding:30px; border-radius:30px; border:1px solid #30363D; margin-bottom:20px;">
            <h1 style="color: #FF7E7E; margin-bottom:0;">☀️ Daily Guide, {name}!</h1>
            <p style="color: #8B949E; font-size:16px; margin-top:10px;">
                Lily remembers you felt <b>{checkin_mood.upper()}</b> during our check-in. Let's make the best of it!
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- 3. ADD NEW TASK (WITH UPDATED AI PROMPT) ---
    st.markdown("#### ➕ Add a New Task to Lily's List")
    with st.container():
        st.markdown('<div style="background:#0D1117; padding:20px; border-radius:20px; border:1px solid #30363D; margin-bottom:25px;">', unsafe_allow_html=True)
        
        c1, c2 = st.columns([2, 1])
        h_name = c1.text_input("Task Name", placeholder="e.g. Morning Walk")
        
        # Time Dropdown
        time_options = [f"{h:02d}:{m}" for h in range(24) for m in ["00", "30"]]
        h_time = c2.selectbox("Scheduled Time", options=time_options, index=16) # Default 08:00
        
        c3, c4 = st.columns(2)
        h_priority = c3.selectbox("Risk Level (Priority)", ["Low", "Normal", "High"])
        h_food = c4.selectbox("Safety (Food Instructions)", ["None", "Before Food", "After Food", "Empty Stomach"])
        
        h_notes = st.text_area("Additional Context for Lily", placeholder="e.g. take pills from top shelf in your cupboard")
        
        if st.button("Add Custom Task 💾", use_container_width=True):
            if h_name:
                with st.spinner("Lily is writing your instructions..."):
                    try:
                        # --- YOUR SPECIFIC AI PROMPT ---
                        prompt = f"""
                        You are Lily, an empathetic AI companion. Your goal is to guide a senior named {name} 
                        through the task: '{h_name}'.

                        The Guardian ({g_name}) has provided this specific context: 
                        "{h_notes}". 

                        Safety Instructions: {h_food}.

                        STRICT RULES FOR OUTPUT:
                        1. DIRECT ADDRESS: Speak directly to {name} using "You" and "Your".
                        2. NO CAREGIVER TALK: Never use words like "Assist," "Help," "Provide," or "Support." 
                        3. ACTION VERBS: Start each step with a clear command (e.g., "Wear," "Drink," "Check," "Eat").
                        4. CONCISION: Provide only 4 to 6 high-quality, sequential steps. Do not repeat ideas.
                        5. NO WRAPPING TEXT: Do not include "Here are the steps" or "I hope this helps." Output ONLY the steps.
                        6. COGNITIVE LOAD: Keep each step under 10 words. 

                        Example of Good Tone:
                        "Wear your walking shoes." 
                        "Grab your water bottle from the kitchen."

                        Step-by-step procedure:
                        """
                        
                        client = ollama.Client(host='http://localhost:11434')
                        res = client.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
                        raw_steps = res['message']['content'].strip().split('\n')
                        # Sanitize steps to remove numbering or bullets if the AI includes them
                        lily_steps = [s.lstrip('0123456789. -').strip() for s in raw_steps if s.strip()]
                    except:
                        lily_steps = ["Start the task.", "Follow Lily's notes.", "Mark it as done!"]

                new_task = {
                    "label": h_name, 
                    "time": h_time, 
                    "priority": h_priority, 
                    "instruction": h_notes if h_notes else "Take your time and stay safe.",
                    "done": False,
                    "steps": lily_steps
                }
                st.session_state.current_habits.append(new_task)
                
                # Update JSON
                if os.path.exists("data/users.json"):
                    with open("data/users.json", "r") as f:
                        full_db = json.load(f)
                    full_db[user_id]['habits'] = st.session_state.current_habits
                    with open("data/users.json", "w") as f:
                        json.dump(full_db, f, indent=4)
                
                st.success(f"Added {h_name}!")
                time.sleep(1)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. CATEGORIZED TABS ---
    tab_h, tab_c, tab_t = st.tabs(["🏥 My Schedule", "🍳 Cooking", "💻 Tech Help"])

    with tab_h:
        st.subheader("Your Daily Goals")
        
        # --- 🚀 AUTOMATED MOOD SUGGESTIONS ---
        mood_library = {
            "sad": [
                {"label": "🖼️ Browse your memory vault", "note": "Let's look at some happy moments you've saved.", "steps": ["Go to the 'Our Memories' page.", "Click on the '😊 Great' filter.", "Read three memories that make you smile."]},
                {"label": "📞 Call a dear friend", "note": "Sharing a few words can make the world feel brighter.", "steps": ["Find your phone.", "Pick a friend from your contacts.", "Say hello and chat for 5 minutes."]}
            ],
            "tired": [
                {"label": "💧 Hydration check", "note": "Drink a full glass of water to refresh your mind.", "steps": ["Go to the kitchen.", "Pour a fresh glass of water.", "Drink it all while sitting down."]}
            ],
            "happy": [
                {"label": "📝 Record a happy memory", "note": "You feel great! Let's save this feeling in your diary.", "steps": ["Go to 'Our Memories'.", "Type why you are happy right now.", "Press Save to keep the memory forever."]}
            ],
            "neutral": [
                {"label": "🎨 Do a quick doodle", "note": "A little creativity is great for the brain.", "steps": ["Find a piece of paper.", "Draw something simple like a flower.", "Smile at your creation!"]}
            ]
        }

        if checkin_mood in mood_library:
            random.seed(int(datetime.date.today().strftime('%Y%m%d')))
            suggestion = random.choice(mood_library[checkin_mood])
            
            if not any(suggestion['label'] in h['label'] for h in st.session_state.current_habits):
                st.session_state.current_habits.insert(0, {
                    "label": f"Lily suggests: {suggestion['label']}", 
                    "time": "Today", 
                    "priority": "High", 
                    "instruction": suggestion['note'], 
                    "steps": suggestion['steps'],
                    "done": False
                })

        habits = st.session_state.current_habits
        completed_count = 0 
        
        if not habits:
            st.write("No tasks scheduled for today.")
        else:
            for i, h in enumerate(habits):
                b_color = "#FF7E7E" if h.get('priority') == "High" else "#30363D"
                
                st.markdown(f"""<div style="border-left: 5px solid {b_color}; padding:15px; margin-bottom:10px; background: #0D1117; border-radius: 0 15px 15px 0;">""", unsafe_allow_html=True)
                
                is_checked = st.checkbox(
                    f"**{h['label']}** at {h['time']}", 
                    value=h.get('done', False), 
                    key=f"hab_check_{i}"
                )
                
                if is_checked != h.get('done'):
                    h['done'] = is_checked
                    if is_checked: st.toast(f"Excellent work, {name}!")
                    st.rerun()

                if is_checked:
                    completed_count += 1

                with st.expander("📝 View Procedure Steps"):
                    st.info(f"💡 Lily's Note: {h.get('instruction', 'Let\'s take it slow.')}")
                    steps = h.get('steps', ["Start the task.", "Take your time.", "Mark it as done!"])
                    for j, step in enumerate(steps):
                        st.markdown(f"{j+1}. {step}")
                
                st.markdown("</div>", unsafe_allow_html=True)

        if habits:
            total_tasks = len(habits)
            progress_pct = completed_count / total_tasks
            st.write(f"**Overall Progress: {int(progress_pct*100)}%**")
            st.progress(progress_pct)

    with tab_c:
        st.subheader("🍳 Lily's Smart Kitchen")
        if checkin_score < 60:
            st.info(f"Since your wellness score is {checkin_score}%, Lily recommends easy, low-effort meals today.")

        cook_mode = st.radio("How can Lily help you cook?", ["Find a Recipe", "I have Ingredients"], horizontal=True)

        if cook_mode == "Find a Recipe":
            dish = st.text_input("Which dish would you like to make?")
            if st.button("Get Recipe ✨", use_container_width=True) and dish:
                with st.spinner(f"Lily is finding a simple way to make {dish}..."):
                    res = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': f"Simple senior-friendly recipe for {dish}."}])
                    st.markdown(f"<div style='background:#1A1B26; padding:20px; border-radius:15px;'>{res['message']['content']}</div>", unsafe_allow_html=True)

    with tab_t:
        st.subheader("Lily's Tech Support")
        tech_q = st.text_input("What tech help do you need?")
        if tech_q:
            with st.spinner("Lily is writing simple steps..."):
                res = ollama.chat(model='llama3.2', messages=[
                    {'role': 'system', 'content': 'You are Lily, a tech assistant for seniors. Short steps.'},
                    {'role': 'user', 'content': tech_q}
                ])
                st.write(res['message']['content'])