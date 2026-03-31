import streamlit as st
import json
import os
import datetime
import pandas as pd
import plotly.express as px

def load_all_user_data():
    user_id = st.session_state.get('user_id', 'ayesh')
    if os.path.exists("data/users.json"):
        with open("data/users.json", "r") as f:
            return json.load(f).get(user_id)
    return None

def show():
    data = load_all_user_data()
    if not data:
        st.error("No data available.")
        return

    profile = data.get('profile', {})
    history = data.get('wellness_history', {})
    habits = data.get('habits', [])
    memories = data.get('memories', []) # This is where Lily saves chat insights

    st.title(f"📊 {profile.get('guardian_name', 'Guardian')}'s Control Center")
    st.divider()

    # --- 1. ROUTINE TRACKING (What she did vs. missed) ---
    st.subheader("✅ Daily Routine Tracker")
    col_stat, col_list = st.columns([1, 2])
    
    done_tasks = [h for h in habits if h.get('done')]
    pending_tasks = [h for h in habits if not h.get('done')]
    
    with col_stat:
        st.metric("Tasks Completed", f"{len(done_tasks)} / {len(habits)}")
        if pending_tasks:
            st.warning(f"Pending: {pending_tasks[0]['label']}")

    with col_list:
        for h in habits:
            status = "🟢 Completed" if h.get('done') else "🔴 Pending"
            # Show the exact time she finished it from the logs
            time_log = h.get('logs', ['--'])[0] if h.get('done') else "Not yet"
            st.write(f"**{h['label']}**: {status} (Log: {time_log})")

    st.divider()

    # --- 2. CHAT INSIGHTS (New things shared with Lily) ---
    st.subheader("💡 New Insights from Lily's Chats")
    st.caption("Lily extracts key life events and memories mentioned during conversations.")
    
    if not memories:
        st.info("No new memories or life events shared today.")
    else:
        # Display the last 3 things Ayesha told Lily
        for mem in reversed(memories[-3:]):
            st.markdown(f"""
                <div style="background:#1C2128; padding:15px; border-radius:15px; border-left:5px solid #FF7E7E; margin-bottom:10px;">
                    <span style="color:#8B949E; font-size:12px;">{mem.get('timestamp', 'Recent')}</span><br>
                    <b style="color:#C9D1D9;">{mem.get('content')}</b>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # --- 3. THE ANALYTICS CHART ---
    st.subheader("📈 Emotional Stability Trend")
    today = datetime.date.today()
    dates = [(today - datetime.timedelta(days=i)) for i in range(6, -1, -1)]
    scores = [history.get(str(d), 0) for d in dates]
    df = pd.DataFrame({"Date": dates, "Score": scores})
    
    fig = px.area(df, x="Date", y="Score", title="Weekly Wellness Score")
    fig.update_traces(line_color='#FF7E7E', fillcolor='rgba(255, 126, 126, 0.2)')
    st.plotly_chart(fig, use_container_width=True)

    # --- 4. THE "MASKING" LOG ---
    if st.session_state.get('checkin_label') == "Discordant (Masked Sadness)":
        st.error("🚨 **AI Alert:** Ayesha showed signs of 'Masked Sadness' today. She looked sad during check-in but reported feeling 'Fine' in text.")