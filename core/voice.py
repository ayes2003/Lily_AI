import pyttsx3
import speech_recognition as sr
import re
import threading
import os

# Windows COM fix
if os.name == 'nt':
    import pythoncom

# --- GLOBAL STATE ---
_is_speaking = False
_stop_signal = False
_speech_lock = threading.Lock()


# --- CLEAN TEXT ---
def clean_text_for_speech(text):
    text = re.sub(r'[\*\#\-\>]', '', text)
    text = text.replace('\n', ', ')
    text = " ".join(text.split())
    return text


# --- STOP SPEECH ---
def stop_speaking():
    global _stop_signal
    _stop_signal = True


# --- SPEAK FUNCTION ---
def speak(text):
    global _is_speaking, _stop_signal

    # Prevent overlapping speech
    if _is_speaking:
        return

    def run_speech():
        global _is_speaking, _stop_signal

        try:
            with _speech_lock:
                _is_speaking = True
                _stop_signal = False

                # Windows fix
                if os.name == 'nt':
                    pythoncom.CoInitialize()

                engine = pyttsx3.init()

                # Clean text
                clean_text = clean_text_for_speech(text)

                # Configure voice
                voices = engine.getProperty('voices')
                if len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)
                else:
                    engine.setProperty('voice', voices[0].id)

                engine.setProperty('rate', 145)
                engine.setProperty('volume', 1.0)

                # --- INTERRUPT SUPPORT ---
                def on_word(name, location, length):
                    if _stop_signal:
                        engine.stop()

                engine.connect('started-word', on_word)

                # Speak
                engine.say(clean_text)
                engine.runAndWait()

                engine.stop()
                del engine

                if os.name == 'nt':
                    pythoncom.CoUninitialize()

        except Exception as e:
            print(f"Speech Error: {e}")

        finally:
            _is_speaking = False
            _stop_signal = False

    thread = threading.Thread(target=run_speech, daemon=True)
    thread.start()


# --- LISTEN FUNCTION ---
def listen():
    r = sr.Recognizer()

    r.dynamic_energy_threshold = True
    r.pause_threshold = 1.2

    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.8)

            audio = r.listen(source, timeout=5, phrase_time_limit=12)

            query = r.recognize_google(audio)
            return query

    except sr.WaitTimeoutError:
        return None

    except sr.UnknownValueError:
        return "I heard something, but I couldn't quite catch that. Could you repeat it?"

    except Exception as e:
        print(f"Lily Listening Error: {e}")
        return None