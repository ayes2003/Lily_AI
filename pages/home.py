import streamlit as st
import ui_components as ui
import json
import os
import datetime
import time

from core.eyes import get_snapshot_emotion
from core.fusion import calculate_wellness_fusion
from core.memory import get_recent_memories # 🚀 Added to fetch real memory count

def show():
    ui.inject_custom_css()
    
    if "checkin_complete" not in st.session_state:
        st.session_state.checkin_complete = False

    user_id = st.session_state.get('user_id', 'ayesh')
    user_name = st.session_state.get('user_name', 'User')
    
    # --- LOAD DATABASE ---
    if os.path.exists("data/users.json"):
        with open("data/users.json", "r") as f:
            full_db = json.load(f)
            data = full_db.get(user_id)
    else:
        st.error("User database not found.")
        return

    if not data:
        st.error("User data not found.")
        return

    profile = data.get('profile', {})
    habits = data.get('habits', [])
    history = data.get('wellness_history', {})
    today_str = str(datetime.date.today())

    ui.hero_banner(profile.get('name', 'User'))

    # --- 1. MORNING CHECK-IN SECTION ---
    if not st.session_state.checkin_complete:
        st.markdown('<div class="warm-card" style="text-align:center;">', unsafe_allow_html=True)
        st.markdown("## How are you feeling today? 🌸")
        st.write("Lily wants to check in on you before we start.")
        
        if st.button("✨ Start Check-in", use_container_width=True):
            with st.spinner("Lily is looking at you..."):
                try:
                    emo, _ = get_snapshot_emotion()
                    st.session_state.temp_emo = emo
                    st.session_state.emo_captured = True
                except Exception as e:
                    st.error(f"Camera error: {e}")
        
        if st.session_state.get('emo_captured'):
            st.info(f"Lily thinks you look **{st.session_state.temp_emo.upper()}**.")
            reply = st.text_input("Anything you'd like to tell me?")
            if st.button("Complete Check-in", use_container_width=True):
                if reply:
                    score, label = calculate_wellness_fusion(st.session_state.temp_emo, reply)
                    st.session_state.current_mood = st.session_state.temp_emo
                    st.session_state.wellness_percent = score
                    st.session_state.checkin_complete = True
                    
                    # Save wellness to history immediately
                    full_db[user_id].setdefault('wellness_history', {})[today_str] = score
                    with open("data/users.json", "w") as f:
                        json.dump(full_db, f, indent=4)
                        
                    st.rerun()
                else:
                    st.warning("Please tell Lily a little bit about your mood!")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # --- 2. DYNAMIC METRICS CALCULATION ---
    # A. Days Together
    created_date_str = data.get('created_at', today_str)
    created_date = datetime.datetime.strptime(created_date_str, '%Y-%m-%d').date()
    days_together = (datetime.date.today() - created_date).days + 1
    
    # B. REAL Memory Count (Pulling from ChromaDB/Vector Store)
    try:
        # Fetching all memories stored for this user name
        all_stored_memories = get_recent_memories(user_name, limit=2000)
        mem_count = len(all_stored_memories)
    except:
        mem_count = 0
    
    # C. Dynamic Chat Count (Calculated from current session)
    chat_list = st.session_state.get('messages', [])
    chat_count = len([m for m in chat_list if m['role'] == 'user'])
    
    # Sync Chat Count to JSON for persistence
    current_stored_chats = data.get('daily_stats', {}).get(today_str, {}).get('chats', 0)
    if chat_count > current_stored_chats:
        full_db[user_id].setdefault('daily_stats', {}).setdefault(today_str, {})['chats'] = chat_count
        with open("data/users.json", "w") as f:
            json.dump(full_db, f, indent=4)
    else:
        # If session is fresh but DB has chats, use DB count
        chat_count = max(chat_count, current_stored_chats)
    
    # D. Real Wellness Score
    today_wellness = history.get(today_str, st.session_state.get('wellness_percent', 0))
    wellness_display = f"{today_wellness}%" if today_wellness > 0 else "Pending"
    
    # Display the dynamic KPI row
    ui.kpi_row(days_together, mem_count, chat_count, wellness_display)

    st.divider()

    # --- 3. MOOD & SCHEDULE SPLIT VIEW ---
    col_mood, col_sched = st.columns([1, 1.2])

    with col_mood:
        mood_icons = {"happy": "😊", "sad": "😢", "tired": "😴", "neutral": "😐", "angry": "😠", "fear": "😨"}
        current_mood = st.session_state.get('current_mood', 'neutral')
        emoji = mood_icons.get(current_mood, "🙂")
        
        st.markdown(f"""
            <div class="warm-card" style="text-align:center; height:520px;">
                <h3 style="color:white; margin-bottom:10px;">How are you feeling?</h3>
                <p style="color:#8B949E; font-size:14px;">Lily cares about your mood today \U0001F9E1</p>
                <span class="mood-emoji-large">{emoji}</span>
                <h2 style="color:white; margin-top:10px;">{current_mood.capitalize()}!</h2>
            </div>
        """, unsafe_allow_html=True)

    with col_sched:
        schedule_html = ui.schedule_list(habits)
        clean_html = schedule_html.strip()
        final_output = f'<div class="warm-card" style="height:520px; overflow-y:auto; color:#C9D1D9;">{clean_html}</div>'
        st.markdown(final_output, unsafe_allow_html=True)

    # --- 4. WELLNESS CHART & INSIGHTS ---
    st.markdown('<div class="warm-card">', unsafe_allow_html=True)
    st.markdown("### Wellness This Week 📈")
    last_7_days = [(datetime.date.today() - datetime.timedelta(days=i)) for i in range(6, -1, -1)]
    chart_data = [history.get(str(d), 0) for d in last_7_days]
    ui.wellness_chart(chart_data)
    
    if any(chart_data) and max(chart_data) > 0:
        max_score = max(chart_data)
        best_day_idx = chart_data.index(max_score)
        best_day_name = last_7_days[best_day_idx].strftime("%A")
        insight = f"🌟 <b>Insight:</b> Your best day was {best_day_name}! Lily noticed you were extra cheerful and hitting {max_score}% wellness."
    else:
        insight = "🌟 <b>Insight:</b> Lily is waiting for more data to show your weekly patterns!"

    st.markdown(f"""
        <div class="insight-box">
            {insight}
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)