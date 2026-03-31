import streamlit as st
import numpy as np
import os
import json
import ui_components as ui 
from pages import guide, home, chat, diary, signup 
from core.memory import summarize_session, save_memory

# 1. PAGE CONFIG
st.set_page_config(page_title="Lily AI", layout="centered", initial_sidebar_state="collapsed")

# 2. INITIALIZATION & GLOBAL DATABASE LOAD
db = {}
if os.path.exists("data/users.json"):
    try:
        with open("data/users.json", "r") as f:
            db = json.load(f)
    except Exception:
        db = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "🏠 Home"
if "user_role" not in st.session_state:
    st.session_state.user_role = "senior"

ui.inject_custom_css()

# --- 🎯 MODERN BLACK SIDEBAR CSS & UI OVERRIDES ---
st.markdown("""
    <style>
        /* 1. HIDE SIDEBAR TOTALLY ON LOGIN */
        [data-testid="collapsedControl"] { display: none !important; }
        
        /* 2. Global Large Text for Readability */
        .big-font { font-size: 22px !important; line-height: 1.6; color: #E0E0E0; }
        .title-font { font-size: 32px !important; font-weight: bold; color: #FF7E7E; }

        /* 3. Sidebar Background (Deep Black) */
        [data-testid="stSidebar"] {
            background-color: #000000 !important;
            border-right: 1px solid #1E1E1E;
        }
        [data-testid="stSidebarNav"] {display: none;}

        .hero-card {
            background: linear-gradient(145deg, #1e1e1e, #121212);
            padding: 20px;
            border-radius: 20px;
            margin-bottom: 25px;
            border: 1px solid #333;
            text-align: center;
        }

        .stRadio > div { gap: 12px; padding: 0px 10px; }
        
        /* Clean Button Fix: Hide radio dot */
        .stRadio div[role="radiogroup"] label > div:first-child { display: none !important; }
        
        .stRadio label {
            background-color: #1A1A1A !important;
            color: #E0E0E0 !important;
            border-radius: 15px !important;
            padding: 12px 20px !important;
            border: 1px solid #333 !important;
            transition: all 0.3s ease;
            width: 100%;
            font-size: 16px;
            display: flex;
            justify-content: center !important;
            align-items: center;
        }

        .stRadio div[role="radiogroup"] input:checked + div {
            background-color: #FF4B4B !important;
            color: white !important;
            font-weight: bold;
            border: none !important;
            transform: scale(1.02);
            border-radius: 15px !important;
            display: flex;
            justify-content: center;
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# 3. AUTHENTICATION LOGIC
if not st.session_state.logged_in:
    # Force sidebar hidden via CSS when not logged in
    st.markdown("<style>[data-testid='stSidebar'] { display: none; }</style>", unsafe_allow_html=True)

    st.markdown("<h1 class='title-font' style='text-align: center;'>🌸 Lily is waiting for you.</h1>", unsafe_allow_html=True)
    
    # --- 💡 COMBINED INSTRUCTIONS (Font Size 13) ---
    st.markdown("""
        <div style="background-color: #121212; border-left: 4px solid #FF7E7E; padding: 15px; border-radius: 12px; margin-bottom: 25px;">
            <p style="margin:0; color: #FF7E7E; font-size: 13px; font-weight: bold; margin-bottom: 5px;">👋 How to enter:</p>
            <p style="margin:0; color: #BBB; font-size: 13px; line-height: 1.5;">
                <b>Seniors:</b> Login using your favorite <b>Icon Password</b> below.<br>
                <b>Guardians:</b> Use the <b>Setup</b> tab to create an account, or use your <b>Admin Password</b> in the login tab to check user status.
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab_log, tab_sign = st.tabs(["🔒 Senior Login", "📝 Guardian Setup"])
    
    with tab_log:
        st.session_state.in_signup_mode = False
        if not db:
            st.markdown("<p style='color: #BBB; font-size: 13px;'>No profiles found. Please use 'Guardian Setup' to get started.</p>", unsafe_allow_html=True)
        else:
            user_options = {db[uid]["profile"]["name"]: uid for uid in db.keys()}
            selected_name = st.selectbox("Select Profile", options=list(user_options.keys()), label_visibility="collapsed")
            
            u_id = user_options[selected_name]
            user_data = db[u_id]
            correct_icon = user_data["profile"].get("secret_icon", "🌸")
            
            st.markdown(f"<h2 style='text-align: center; color: white;'>Hello, {selected_name}!</h2>", unsafe_allow_html=True)
            
            icons = ["🐱", "🍎", "☀️", "🌸", "🏠", "☕"]
            cols = st.columns(3)
            for i, icon in enumerate(icons):
                if cols[i % 3].button(icon, width='stretch', key=f"login_icon_{i}"):
                    if icon == correct_icon:
                        st.session_state.user_id = u_id
                        st.session_state.user_name = selected_name
                        st.session_state.user_role = "senior"
                        # 🚀 REQUIRE SCAN FOR SENIOR
                        st.session_state.checkin_complete = False 
                        st.session_state.logged_in = True
                        st.rerun() 
                    else:
                        st.toast(f"Try another friend!", icon="❌")

            guardian_name = user_data["profile"].get("guardian_name", "Guardian")
            stored_password = user_data["profile"].get("guardian_password")

            st.markdown("---")
            with st.expander(f"🔐 Guardian Admin Entry"):
                st.markdown(f"<p style='color: #BBB; font-size: 13px;'>Enter password for <b>{selected_name}</b> dashboard.</p>", unsafe_allow_html=True)
                admin_pwd = st.text_input("Guardian Password", type="password", key="admin_pwd_input")
                if st.button("Unlock Oversight Dashboard 🛡️", width='stretch'):
                    if admin_pwd == stored_password:
                        st.session_state.user_id = u_id
                        st.session_state.user_name = guardian_name
                        st.session_state.user_role = "guardian"
                        # 🚀 BYPASS SCAN FOR GUARDIAN
                        st.session_state.checkin_complete = True 
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Incorrect Password.")

    with tab_sign:
        st.session_state.in_signup_mode = True
        signup.show() 
    
    st.stop()

# --- 4. POST-LOGIN NAVIGATION ---
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 10px 0px 20px 0px;">
            <h2 style="color: #FF4B4B; margin:0;">❤️ LilyAI</h2>
            <p style="color: #888; font-size: 0.8rem;">Your caring companion</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="hero-card">
            <p style="color: #FF4B4B; margin:0; font-weight: bold; font-size: 1rem;">🟢 Lily is active</p>
            <p style="color: #AAA; font-size: 0.85rem; margin-top: 5px;">"Hello {st.session_state.get('user_name', 'User')}, I am ready to help."</p>
        </div>
    """, unsafe_allow_html=True)

    nav_options = ["🏠 Home", "💬 Talk to Lily", "📖 Our Memories", "☀️ Daily Guide"]
    
    try: current_idx = nav_options.index(st.session_state.nav_page)
    except: current_idx = 0

    new_page = st.radio("Menu", nav_options, index=current_idx, label_visibility="collapsed")

    if st.session_state.nav_page == "💬 Talk to Lily" and new_page != "💬 Talk to Lily":
        active_id = st.session_state.get('user_id')
        if active_id and len(st.session_state.get('messages', [])) > 2:
            st.toast("Lily is remembering...")
            real_u_name = db[active_id]["profile"]["name"] if active_id in db else "User"
            mood = st.session_state.get('current_mood', 'neutral')
            summary = summarize_session(st.session_state.messages, real_u_name)
            if summary:
                save_memory(real_u_name, summary, mood, entry_type="personal", tags=["#AutoSaved"])
            st.session_state.messages = []
            st.session_state.welcome_done = False
            
    st.session_state.nav_page = new_page
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Logout 🚪", width='stretch'):
        # 🚀 THE HARD RESET
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_role = "senior"
        st.session_state.checkin_complete = False # Forces re-scan on next login
        st.session_state.messages = []
        st.rerun()

# --- 5. ROUTER ---
if st.session_state.nav_page == "🏠 Home": home.show()
elif st.session_state.nav_page == "💬 Talk to Lily": chat.show()
elif st.session_state.nav_page == "📖 Our Memories": diary.show()
elif st.session_state.nav_page == "☀️ Daily Guide": guide.show()