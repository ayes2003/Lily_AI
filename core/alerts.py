import datetime
import json
import streamlit as st
import os

def check_red_flags():
    """Checks if any High Priority habits are missed by > 2 hours."""
    user_id = st.session_state.get('user_id')
    if not user_id: return

    try:
        if os.path.exists("data/users.json"):
            with open("data/users.json", "r") as f:
                db = json.load(f)
                user_data = db.get(user_id)
            
            if not user_data: return

            now = datetime.datetime.now()
            
            for habit in user_data.get('habits', []):
                # Ensure we only alert on High Priority items that are NOT done
                if habit.get('priority') == "High" and not habit.get('done', False):
                    scheduled_time = datetime.datetime.strptime(habit['time'], "%H:%M").replace(
                        year=now.year, month=now.month, day=now.day
                    )
                    
                    delay = now - scheduled_time
                    # If delayed by more than 2 hours (7200 seconds)
                    if delay.total_seconds() > 7200: 
                        st.sidebar.error(f"⚠️ RED FLAG: {habit['label']} missed!")
    except:
        pass