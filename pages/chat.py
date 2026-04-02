import streamlit as st
from groq import Groq  # Switched from ollama
import io
import os
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
from core.memory import save_memory, summarize_session, get_recent_memories
from core.voice import speak
import ui_components as ui
import json

# --- CHECK PENDING TASKS ---
def check_pending_tasks(user_id):
    if not os.path.exists("data/users.json"):
        return None
    try:
        with open("data/users.json", "r") as f:
            db = json.load(f)
            user_data = db.get(user_id, {})
            habits = user_data.get('habits', [])
            pending = [
                h['task'] for h in habits
                if ("med" in h['task'].lower() or "pill" in h['task'].lower())
                and not h.get('done', False)
            ]
            if pending:
                return f"Also, Lily's gentle note: I noticed you haven't checked off '{pending[0]}' in your Daily Guide yet. Please don't forget! 🌸"
    except:
        pass
    return None

def show():
    ui.inject_custom_css()

    # --- SESSION STATE ---
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "welcome_done" not in st.session_state:
        st.session_state.welcome_done = False

    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False

    if "last_processed_input" not in st.session_state:
        st.session_state.last_processed_input = None

    user_id = st.session_state.get('user_id', 'ayesh')
    user_name = st.session_state.get('user_name', 'User')
    checkin_mood = st.session_state.get('current_mood', 'neutral')

    # --- GROQ CLIENT INITIALIZATION ---
    # Ensure you have "GROQ_API_KEY" in your environment variables or st.secrets
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    # --- MEMORY CONTEXT ---
    past_mems = get_recent_memories(user_name, limit=5)
    memory_context = ""
    if past_mems:
        memory_texts = [m['content'] for m in past_mems if isinstance(m, dict)]
        memory_context = "Lily's past records of you: " + " | ".join(memory_texts)

    st.markdown("### 🤖 Chatting with Lily")

    chat_container = st.container(height=550)

    # --- RENDER CHAT HISTORY ---
    with chat_container:
        for m in st.session_state.messages:
            if m["content"].strip():
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

    # --- INPUT AREA ---
    input_col, mic_col = st.columns([5, 1])

    with input_col:
        text_input = st.chat_input("Type a message to Lily...", key="lily_chat_input")

    with mic_col:
        audio_bytes = audio_recorder(
            text="",
            icon_size="2x",
            neutral_color="#8B949E",
            recording_color="#FF4B4B",
            key="mic_recorder"
        )

    # --- WELCOME MESSAGE ---
    if not st.session_state.welcome_done and len(st.session_state.messages) == 0:
        task_reminder = check_pending_tasks(user_id)
        welcome_text = f"Hello {user_name}! I remember you looked {checkin_mood} earlier. How are you feeling now?"

        try:
            reminder_instruction = f"Remind them gently about: {task_reminder}" if task_reminder else ""
            welcome_prompt = (
                f"You are Lily, a warm companion. {memory_context}. "
                f"Greet {user_name} warmly. Mention they looked {checkin_mood} earlier. "
                f"{reminder_instruction}. Keep it brief."
            )

            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{'role': 'system', 'content': welcome_prompt}]
            )

            if res.choices[0].message.content:
                welcome_text = res.choices[0].message.content

        except Exception as e:
            print(f"Groq Error: {e}")

        st.session_state.messages.append({"role": "assistant", "content": welcome_text})
        st.session_state.welcome_done = True
        speak(welcome_text)
        st.rerun()

    # --- INPUT PROCESSING ---
    final_input = None

    if text_input:
        final_input = text_input.strip().lower()

    elif audio_bytes and not st.session_state.is_processing:
        r = sr.Recognizer()
        try:
            with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
                audio_data = r.record(source)
                final_input = r.recognize_google(audio_data).strip().lower()
        except:
            st.error("I missed that. Try again?")

    # --- MAIN CHAT LOGIC ---
    if (
        final_input
        and not st.session_state.is_processing
        and final_input != st.session_state.last_processed_input
    ):
        st.session_state.is_processing = True
        st.session_state.last_processed_input = final_input

        # Add user message
        st.session_state.messages.append({"role": "user", "content": final_input})

        with chat_container:
            with st.chat_message("user"):
                st.markdown(final_input)

            with st.chat_message("assistant"):
                with st.spinner("Lily is thinking..."):
                    try:
                        lily_system_prompt = (
                            f"You are Lily, a warm AI companion. "
                            f"{memory_context}. Morning Mood: {checkin_mood}."
                        )

                        res = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {'role': 'system', 'content': lily_system_prompt}
                            ] + st.session_state.messages
                        )

                        reply = res.choices[0].message.content

                        st.markdown(reply)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": reply
                        })

                        speak(reply)

                    except Exception as e:
                        st.error("Lily is resting. Check Groq connection.")
                        print(f"Groq Error: {e}")

        # --- RESET STATE ---
        st.session_state.is_processing = False
        st.rerun()

    # --- SIDEBAR ---
    with st.sidebar:
        st.divider()

        if st.button("♻️ Start Fresh Chat", use_container_width=True):
            if len(st.session_state.messages) > 2:
                summary = summarize_session(st.session_state.messages, user_name)
                if summary:
                    save_memory(
                        user_name,
                        summary,
                        checkin_mood,
                        entry_type="personal",
                        tags=["#AutoSummary"]
                    )

            st.session_state.messages = []
            st.session_state.welcome_done = False
            st.session_state.is_processing = False
            st.session_state.last_processed_input = None

            st.rerun()