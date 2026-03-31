import pyttsx3
import speech_recognition as sr
import re
import streamlit as st
import threading
import os

# Only import pythoncom if on Windows to prevent crashes on Mac/Linux
if os.name == 'nt':
    import pythoncom

# --- LILY'S VOICE (Output) ---
def speak(text):
    """
    Cleans AI text and speaks it using a warm, senior-friendly voice.
    Uses threading and COM initialization for stability in Streamlit.
    """
    def run_speech():
        try:
            # 🚀 Windows Fix: Initialize COM for the background thread
            if os.name == 'nt':
                pythoncom.CoInitialize()
            
            engine = pyttsx3.init()
            
            # 1. CLEAN THE TEXT
            # Remove Markdown stars, hashtags, etc.
            clean_text = re.sub(r'[\*\#\-\>]', '', text)
            # Add pauses for readability
            clean_text = clean_text.replace('\n', ', ')
            clean_text = " ".join(clean_text.split())

            # 2. CONFIGURE VOICE
            voices = engine.getProperty('voices')
            # Select Female Voice (usually Index 1)
            if len(voices) > 1:
                engine.setProperty('voice', voices[1].id)
            else:
                engine.setProperty('voice', voices[0].id)
                
            # Senior-friendly settings: Slow (145) and loud (1.0)
            engine.setProperty('rate', 145) 
            engine.setProperty('volume', 1.0) 
            
            # 3. SPEAK
            engine.say(clean_text)
            engine.runAndWait()
            
            # Clean up engine properly
            del engine
            
        except Exception as e:
            print(f"Speech Error: {e}")

    # Start speech in a background thread so the UI remains responsive
    threading.Thread(target=run_speech, daemon=True).start()

# --- LILY'S EARS (Input) ---
def listen():
    """Listens for user speech and returns text."""
    r = sr.Recognizer()
    
    # Senior-friendly sensitivity
    r.dynamic_energy_threshold = True
    r.pause_threshold = 1.0  
    
    try:
        with sr.Microphone() as source:
            # Quick ambient adjustment
            r.adjust_for_ambient_noise(source, duration=0.8)
            
            # Allow longer phrase time for seniors (12 seconds)
            audio = r.listen(source, timeout=5, phrase_time_limit=12)
            
            query = r.recognize_google(audio) 
            return query
            
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return "I heard something, but I couldn't understand it."
    except Exception as e:
        print(f"Lily Listening Error: {e}")
        return None