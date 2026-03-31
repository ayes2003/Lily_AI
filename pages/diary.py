import streamlit as st
import ui_components as ui
import json
import os
import datetime
import ollama
from core.memory import get_recent_memories, save_memory, search_memories

def generate_hashtags(text):
    """Uses Llama 3.2 to generate 3 relevant hashtags for the diary entry."""
    try:
        prompt = f"Analyze this diary entry and provide exactly 3 hashtags starting with #. Entry: {text}"
        res = ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': prompt}])
        tags = [tag.strip() for tag in res['message']['content'].split() if tag.startswith("#")]
        return tags[:3]
    except:
        return ["#Life", "#Memory", "#Lily"]

def show():
    # Load Theme
    ui.inject_custom_css()
    
    user_name = st.session_state.get('user_name', 'ayesh')
    user_id = st.session_state.get('user_id', 'ayesh')
    
    # --- 0. FETCH ACTUAL DATABASE STATE ---
    # This ensures our KPIs are dynamic and not static placeholders
    USER_DB = "data/users.json"
    user_data = {}
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            db = json.load(f)
            user_data = db.get(user_id, {})

    # --- 1. DYNAMIC HEADER ---
    st.markdown("""
        <div class="hero-banner">
            <h1 style="color: white !important; margin-bottom:0;">Our Private Diary 📖</h1>
            <p style="color: white !important; opacity:0.9; font-size:16px; margin-top:10px;">
                Every conversation Lily has with you is gently saved here — shared memories, 
                feelings, and moments. Always private, always yours.
            </p>
            <div style="background:rgba(0,0,0,0.2); color:white; padding:8px 15px; border-radius:10px; font-size:13px; display:inline-block; border:1px solid rgba(255,255,255,0.3); margin-top:15px;">
                🔒 Stored locally in ChromaDB — No cloud uploads
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- 2. NEW ENTRY SECTION ---
    with st.expander("✍️ Record a New Memory for Today", expanded=False):
        entry_text = st.text_area("What's on your mind, Ayesha?", placeholder="Lily is listening...")
        if st.button("Save to Diary 💾", use_container_width=True):
            if entry_text:
                with st.spinner("Lily is adding hashtags..."):
                    tags = generate_hashtags(entry_text)
                    current_emo = st.session_state.get('current_mood', 'neutral')
                    save_memory(user_name, entry_text, current_emo, entry_type="personal", tags=tags)
                    st.success("Saved to your private vault!")
                    st.rerun()

    # --- 3. SEARCH & FILTERS ---
    st.markdown('<div class="warm-card">', unsafe_allow_html=True)
    search_query = st.text_input("🔍 Search memories...", placeholder="Type to search past chats...")
    
    st.markdown("### Filter by Mood")
    m_cols = st.columns(6)
    mood_map = {
        "🗓️ All": None, 
        "😊 Great": "happy", 
        "🙂 Good": "neutral", 
        "😐 Okay": "neutral", 
        "😔 Low": "sad", 
        "😭 Sad": "sad"
    }
    
    for i, (label, value) in enumerate(mood_map.items()):
        if m_cols[i].button(label, use_container_width=True, key=f"mood_btn_{i}"):
            st.session_state.diary_filter = value
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. DATA RETRIEVAL ---
    if search_query:
        all_memories = search_memories(user_name, search_query)
    else:
        all_memories = get_recent_memories(user_name, limit=50, mood_filter=st.session_state.get('diary_filter'))

    # --- 5. DYNAMIC KPI DASHBOARD ---
    # We calculate these in real-time now
    total_results = len(all_memories)
    
    # Get total count of every memory Lily ever saved
    global_memories = get_recent_memories(user_name, limit=1000)
    grand_total = len(global_memories)
    
    # Count how many check-ins are in the wellness history
    checkin_count = len(user_data.get('wellness_history', {}))

    c1, c2, c3 = st.columns(3)
    
    metrics = [
        ("📝", total_results, "Results Found"),
        ("\U0001F9E1", grand_total, "Total Memories"), 
        ("🔔", checkin_count, "AI Check-ins")
    ]
    
    for i, (icon, val, lab) in enumerate(metrics):
        with [c1, c2, c3][i]:
            st.markdown(f"""
                <div class="stat-card">
                    <span style="font-size:22px;">{icon}</span><br>
                    <span class="stat-number">{val}</span>
                    <span class="stat-label">{lab}</span>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # --- 6. DYNAMIC MEMORY FEED ---
    if not all_memories:
        st.info("No matching memories found. Try a different filter or search!")
    else:
        for i, data in enumerate(all_memories):
            if i == 0 and not search_query:
                st.markdown(f"""
                    <div class="warm-card" style="border-left: 5px solid #FF7E7E;">
                        <span style="float:right; font-size:12px; color:#8B949E;">{data.get('status', 'Synced')}</span>
                        <h4 style="color:#FF7E7E; margin-top:0;">📅 {data.get('date')}</h4>
                        <p style="color:#C9D1D9; font-size:16px; line-height:1.6;">{data.get('content')}</p>
                        <div style="margin-top:15px;">
                            {" ".join([f'<span style="color:#FF7E7E; font-size:12px; margin-right:10px;">{t}</span>' for t in (data.get('tags') or ["#memory"])])}
                        </div>
                        <div class="insight-box" style="margin-top:20px;">
                            <span style="color:#D1FAE5; font-weight:bold;">\U0001F4AC LILY'S REFLECTION</span><br>
                            <span style="font-style:italic;">"I've saved this moment for us. It's important to remember how you felt about this."</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="warm-card">
                        <span style="color:#8B949E; font-size:12px;">{data.get('date')}</span>
                        <p style="color:#C9D1D9; margin:10px 0;">{data.get('content')}</p>
                        <span style="color:#FF7E7E; font-size:12px;">{" ".join(data.get('tags') or ["#memory"])}</span>
                    </div>
                """, unsafe_allow_html=True)