import streamlit as st
from groq import Groq
import io
import os
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
from core.memory import save_memory, summarize_session, get_recent_memories
from core.voice import speak
import datetime
import ui_components as ui
import json

# 🚀 INITIALIZE GROQ CLIENT
# Replace with your actual API Key from console.groq.com
# Change it to exactly this:
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def check_pending_tasks(user_id):
    if not os.path.exists("data/users.json"):
        return None
    try:
        with open("data/users.json", "r") as f:
            db = json.load(f)
            user_data = db.get(user_id, {})
            habits = user_data.get('habits', [])
            pending = [h['task'] for h in habits if ("med" in h['task'].lower() or "pill" in h['task'].lower()) and not h.get('done', False)]
            if pending:
                return f"Also, Lily's gentle note: I noticed you haven't checked off '{pending[0]}' in your Daily Guide yet. Please don't forget! 🌸"
    except Exception:
        pass
    return None

def show():
    ui.inject_custom_css()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "welcome_done" not in st.session_state:
        st.session_state.welcome_done = False
    
    user_id = st.session_state.get('user_id', 'ayesh')
    user_name = st.session_state.get('user_name', 'User')
    checkin_mood = st.session_state.get('current_mood', 'neutral')

    past_mems = get_recent_memories(user_name, limit=5)
    memory_context = ""
    if past_mems:
        memory_texts = [m['content'] for m in past_mems if isinstance(m, dict)]
        memory_context = "Lily's past records of you: " + " | ".join(memory_texts)

    st.markdown(f"### 🤖 Chatting with Lily")
    chat_container = st.container(height=550) 
    
    input_col, mic_col = st.columns([5, 1])
    with input_col:
        text_input = st.chat_input("Type a message to Lily...", key="chat_text_input")
    with mic_col:
        audio_bytes = audio_recorder(text="", icon_size="2x", neutral_color="#8B949E", recording_color="#FF4B4B", key="mic_recorder")

    # --- 5. AUTOMATIC WELCOME LOGIC (GROQ POWERED) ---
    if not st.session_state.welcome_done and len(st.session_state.messages) == 0:
        task_reminder = check_pending_tasks(user_id)
        welcome_text = f"Hello {user_name}! I remember you looked {checkin_mood} earlier. How are you feeling now?"
        
        try:
            reminder_instruction = f"Remind them gently about: {task_reminder}" if task_reminder else ""
            welcome_prompt = (
                f"You are Lily, a warm AI companion. {memory_context}. Greet {user_name} warmly. "
                f"Mention they looked {checkin_mood} earlier. {reminder_instruction}. Keep it very brief."
            )
            # 🚀 GROQ CALL
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": welcome_prompt}],
                model="llama-3.3-70b-versatile",
            )
            welcome_text = chat_completion.choices[0].message.content
        except:
            pass 

        st.session_state.messages.append({"role": "assistant", "content": welcome_text})
        st.session_state.welcome_done = True
        with chat_container:
            with st.chat_message("assistant"):
                st.markdown(welcome_text)
        speak(welcome_text)
        st.rerun()

    # --- 6. RENDER HISTORY ---
    with chat_container:
        for m in st.session_state.messages:
            if m["content"].strip():
                with st.chat_message(m["role"]): 
                    st.markdown(m["content"])

    # --- 7. INPUT & AI PROCESSING ---
    final_input = text_input
    if audio_bytes and not text_input:
        st.toast("🎤 Lily is listening...")
        r = sr.Recognizer()
        try:
            with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
                audio_data = r.record(source)
                final_input = r.recognize_google(audio_data)
        except:
            st.error("I missed that. Try again?")

    if final_input:
        st.session_state.messages.append({"role": "user", "content": final_input})
        lily_prompt = f"You are Lily, a warm AI companion. {memory_context}. Morning Mood: {checkin_mood}."

        with chat_container:
            with st.chat_message("user"): 
                st.markdown(final_input)
            
            with st.chat_message("assistant"):
                with st.spinner("Lily is thinking..."):
                    try:
                        # 🚀 GROQ CALL
                        chat_completion = client.chat.completions.create(
                            messages=[{"role": "system", "content": lily_prompt}] + st.session_state.messages,
                            model="llama-3.3-70b-versatile",
                        )
                        lily_text = chat_completion.choices[0].message.content
                        st.markdown(lily_text)
                        st.session_state.messages.append({"role": "assistant", "content": lily_text})
                        speak(lily_text)
                        st.rerun()
                    except Exception:
                        st.error("Lily is having a quiet moment. Check your internet connection.")

    # --- 8. THE SIDEBAR "CLEAN EXIT" ---
    with st.sidebar:
        st.divider()
        if st.button("♻️ Start Fresh Chat", width='stretch'):
            if len(st.session_state.messages) > 2:
                st.toast("Lily is remembering this chat...")
                summary = summarize_session(st.session_state.messages, user_name)
                if summary:
                    save_memory(user_name, summary, checkin_mood, entry_type="personal", tags=["#AutoSummary"])
            st.session_state.messages = []
            st.session_state.welcome_done = False
            st.rerun()