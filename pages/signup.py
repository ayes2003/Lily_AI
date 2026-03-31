import streamlit as st
import json
import os
import ollama
from datetime import time
import datetime

# --- 📂 CONSTANTS & PATHS ---
USER_DB = "data/users.json"

if not os.path.exists("data"):
    os.makedirs("data")

def show():
    st.markdown("<h1 style='color: #FF7E7E;'>🛡️ Guardian Setup Wizard</h1>", unsafe_allow_html=True)
    st.write("Welcome to Lily's Configuration. Let's build a personalized AI companion.")

    # Initialize session states
    if 'signup_step' not in st.session_state: 
        st.session_state.signup_step = 1
    if 'temp_habits' not in st.session_state: 
        st.session_state.temp_habits = []
    if 'ai_steps' not in st.session_state:
        st.session_state.ai_steps = []

    # --- STEP 1: EMERGENCY & GUARDIAN PROFILE ---
    if st.session_state.signup_step == 1:
        st.subheader("Step 1: Emergency & Caregiver Profile")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 👵 Senior User")
            u_name = st.text_input("Senior's Full Name", placeholder="e.g. Ayesha Sharafudeen")
            u_age = st.number_input("Age", 50, 120, 70)
        with col2:
            st.markdown("### 🛡️ Guardian (Guide)")
            g_name = st.text_input("Guardian Name", placeholder="Enter your name")
            g_phone = st.text_input("Emergency Contact Number", "+91 ")
        
        st.divider()
        st.markdown("### 🔑 Dashboard Security & Alerts")
        st.write("This password will be required to access daily wellness trends and oversight data.")
        
        # 🚀 DASHBOARD PASSWORD: Required for "Anyone" who is the guardian
        g_password = st.text_input("Set Guardian Access Password", type="password", help="Keep this secure to monitor daily data.")
        
        u_conditions = st.text_area("Medical Conditions (Displayed to Guide during Emergency)")
        
        st.divider()
        st.write("### 🔑 Memory Path Login (For Senior)")
        icon_map = {"Flower": "🌸", "Cat": "🐱", "Sun": "☀️", "Apple": "🍎", "House": "🏠", "Coffee": "☕"}
        selected_label = st.radio("Pick the Senior's Login Icon:", list(icon_map.keys()), horizontal=True)
        secret_icon = icon_map[selected_label]
        
        if st.button("Next: Build Schedule ➡️"):
            if u_name and g_name and g_phone and g_password:
                st.session_state.u_info = {
                    "name": u_name, 
                    "age": u_age, 
                    "guardian_name": g_name,
                    "guardian_phone": g_phone,
                    "guardian_password": g_password, # 🔒 Secure access key
                    "secret_icon": secret_icon,
                    "sos": {"phone": g_phone, "conditions": u_conditions}
                }
                st.session_state.signup_step = 2
                st.rerun()
            else:
                st.error("Please fill in all details, including the Guardian Password.")

    # --- STEP 2: AI-POWERED TASK DECOMPOSITION ---
    elif st.session_state.signup_step == 2:
        st.subheader("Step 2: AI Task Assistant (Step-by-Step)")
        
        with st.form("ai_habit_form", clear_on_submit=False):
            c1, c2 = st.columns([2, 1])
            h_name = c1.text_input("Task Name", placeholder="e.g. Morning Walk")
            h_time = c2.time_input("Scheduled Time", value=time(8, 0))
            
            col_a, col_b = st.columns(2)
            h_priority = col_a.selectbox("⚠️ Risk Level (Priority)", ["Low", "Medium", "High"])
            h_cat = col_b.selectbox("📂 Category", ["Health", "Exercise", "Social", "Hobby"])
            
            h_food = st.radio("🍴 Food Instructions", ["None", "Before Food", "After Food", "Empty Stomach"], horizontal=True)
            h_notes = st.text_area("Additional Context for Lily", placeholder="e.g. Use the walker.")
            
            generate_ai = st.form_submit_button("✨ Lily, Auto-Generate Procedure")

        if generate_ai and h_name:
            with st.spinner("Lily is analyzing safety..."):
                try:
                    prompt = f"""
                    You are Lily, an empathetic AI companion. Your goal is to guide a senior named {st.session_state.u_info['name']} 
                    through the task: '{h_name}'. Safety Context: "{h_notes}". Instructions: {h_food}.
                    Output ONLY 4 to 6 concise, sequential steps starting with action verbs.
                    """
                    response = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
                    raw_steps = response['message']['content'].split('\n')
                    
                    st.session_state.ai_steps = [s.strip().lstrip('0123456789.-* ') for s in raw_steps if len(s.strip()) > 5]
                    
                    st.session_state.last_h_name = h_name
                    st.session_state.last_h_time = h_time
                    st.session_state.last_h_priority = h_priority
                    st.session_state.last_h_cat = h_cat
                    st.session_state.last_h_food = h_food
                    st.session_state.last_h_notes = h_notes
                    st.rerun()
                except Exception:
                    st.error("AI is unavailable. Please enter steps manually.")

        if st.session_state.ai_steps:
            st.markdown("#### 📝 Edit & Confirm AI Steps")
            final_steps = []
            for i, step in enumerate(st.session_state.ai_steps):
                edited = st.text_input(f"Step {i+1}", value=step, key=f"step_edit_{i}")
                final_steps.append(edited)
            
            if st.button("💾 Save Task to AI Memory", type="primary", use_container_width=True):
                st.session_state.temp_habits.append({
                    "label": st.session_state.last_h_name, 
                    "time": st.session_state.last_h_time.strftime("%H:%M"),
                    "priority": st.session_state.last_h_priority,
                    "category": st.session_state.last_h_cat,
                    "instruction": st.session_state.last_h_food,
                    "steps": final_steps,
                    "notes": st.session_state.last_h_notes, 
                    "done": False,
                    "logs": [] 
                })
                st.session_state.ai_steps = [] 
                st.success(f"Task saved!")
                st.rerun()

        if st.session_state.temp_habits:
            st.divider()
            st.markdown("### 📋 Current Schedule Preview")
            for habit in st.session_state.temp_habits:
                st.write(f"✅ **{habit['label']}** at {habit['time']} ({habit['priority']})")

        st.divider()
        col_back, col_save = st.columns(2)
        if col_back.button("⬅️ Back"): 
            st.session_state.signup_step = 1
            st.rerun()
            
        if col_save.button("Finalize & Save AI System 💾", use_container_width=True): 
            if not st.session_state.temp_habits:
                st.error("Please add at least one task first!")
            else:
                user_id = st.session_state.u_info['name'].lower().replace(" ", "_")
                db = {}
                if os.path.exists(USER_DB):
                    with open(USER_DB, "r") as f:
                        try: db = json.load(f)
                        except: db = {}
                
                db[user_id] = {
                    "profile": st.session_state.u_info,
                    "habits": st.session_state.temp_habits,
                    "created_at": str(datetime.date.today()),
                    "wellness_history": {}, 
                    "daily_stats": {},
                    "memories": [] 
                }
                
                with open(USER_DB, "w") as f:
                    json.dump(db, f, indent=4)

                st.success(f"Profile Ready! {st.session_state.u_info['guardian_name']} can now monitor {st.session_state.u_info['name']}.")
                st.balloons()
                st.session_state.signup_step = 1
                st.session_state.temp_habits = []
                st.rerun()