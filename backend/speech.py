import pyttsx3
import speech_recognition as sr
from . import config

# Initialize TTS and speech recognition modules
try:
    engine = pyttsx3.init()
except Exception as e:
    print(f"Warning: Could not initialize local text-to-speech engine: {e}")
    engine = None

recognizer = sr.Recognizer()

# Speak function
def speak(text):
    print("Jarvis:", text)
    if config.is_web_mode:
        config.web_response_buffer.append(text)
    else:
        if engine:
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"Speech Engine Error: {e}")

# Listen to user's voice
def listen(lang='en-US'):
    with sr.Microphone() as source:
        print("🎤 Listening...")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            print("Recognizing...")
            command = recognizer.recognize_google(audio, language=lang)
            print("You said:", command)
            return command
        except sr.WaitTimeoutError:
            print("Listening timed out (no speech detected).")
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that. Could you please repeat?")
        except Exception as e:
            print(f"Speech Recognition Error: {e}")
            speak("Sorry, there was an issue with the speech service.")
    return ""

# Get a typed command from input
def get_typed_command():
    try:
        command = input("✍️ Type your command: ")
        return command.strip()
    except KeyboardInterrupt:
        return "exit"
