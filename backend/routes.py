import json
import queue
import threading
import datetime
import subprocess
import webbrowser
import wikipedia
import pywhatkit
from flask import Blueprint, render_template, request, Response, jsonify
from . import config, speech, ai

main_bp = Blueprint('main', __name__)

# Handle user commands
def handle_command(command, original_lang='en', speak_fn=None, action_fn=None):
    def speak_msg(text):
        if speak_fn:
            speak_fn(text)
        else:
            speech.speak(text)
            
    def trigger_action(action_type, value):
        if action_fn:
            action_fn(action_type, value)

    command = command.lower()

    if command.startswith("open "):
        target = command.replace("open ", "", 1).strip()
        
        COMMON_APPS = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "paint": "mspaint.exe",
            "mspaint": "mspaint.exe",
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "task manager": "taskmgr.exe",
            "taskmgr": "taskmgr.exe",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe"
        }
        
        COMMON_WEBSITES = {
            "youtube": "https://youtube.com",
            "gmail": "https://mail.google.com",
            "google": "https://google.com",
            "facebook": "https://facebook.com",
            "github": "https://github.com",
            "wikipedia": "https://wikipedia.org",
            "yahoo": "https://yahoo.com",
            "amazon": "https://amazon.com"
        }
        
        if target in COMMON_WEBSITES:
            url = COMMON_WEBSITES[target]
            webbrowser.open(url)
            trigger_action("open_url", url)
            speak_msg(ai.translate_output(f"Opening {target.capitalize()}", original_lang))
        elif target in COMMON_APPS:
            try:
                subprocess.Popen(COMMON_APPS[target], shell=True)
                speak_msg(ai.translate_output(f"Opening {target.capitalize()}", original_lang))
            except Exception as e:
                print(f"Error opening application {target}: {e}")
                speak_msg(ai.translate_output(f"Sorry, I could not open {target}.", original_lang))
        elif any(target.endswith(tld) for tld in [".com", ".org", ".net", ".edu", ".in", ".gov", ".co"]) or target.startswith("http"):
            url = target if target.startswith("http") else f"https://{target}"
            webbrowser.open(url)
            trigger_action("open_url", url)
            speak_msg(ai.translate_output(f"Opening {target}", original_lang))
        else:
            try:
                subprocess.Popen(target, shell=True)
                speak_msg(ai.translate_output(f"Opening {target}", original_lang))
            except Exception:
                url = f"https://www.google.com/search?q={target}"
                trigger_action("open_url", url)
                speak_msg(ai.translate_output(f"I couldn't open {target} locally. Searching the web...", original_lang))
                webbrowser.open(url)

    elif "weather" in command:
        city = "Delhi"
        if "in" in command:
            parts = command.split("in")
            if len(parts) > 1:
                city = parts[-1].strip()
        weather = ai.get_weather(city)
        speak_msg(ai.translate_output(weather, original_lang))

    elif "time" in command:
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak_msg(ai.translate_output(f"The time is {now}", original_lang))

    elif "date" in command:
        today = datetime.datetime.now().strftime("%A, %d %B %Y")
        speak_msg(ai.translate_output(f"Today's date is {today}", original_lang))

    elif "google search" in command:
        query = command.replace("google search", "").strip()
        if query:
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
            trigger_action("open_url", url)
            speak_msg(ai.translate_output(f"Here are the Google search results for {query}", original_lang))
        else:
            speak_msg(ai.translate_output("Please tell me what to search on Google.", original_lang))

    elif "bing search" in command:
        query = command.replace("bing search", "").strip()
        if query:
            url = f"https://www.bing.com/search?q={query}"
            webbrowser.open(url)
            trigger_action("open_url", url)
            speak_msg(ai.translate_output(f"Here are the Bing search results for {query}", original_lang))
        else:
            speak_msg(ai.translate_output("Please tell me what to search on Bing.", original_lang))

    elif "play song" in command:
        song = command.replace("play song", "").strip()
        if song:
            speak_msg(ai.translate_output(f"Playing {song} on YouTube", original_lang))
            pywhatkit.playonyt(song)
        else:
            speak_msg(ai.translate_output("Which song would you like me to play?", original_lang))

    elif "wikipedia" in command:
        try:
            topic = command.replace("wikipedia", "").strip()
            if topic:
                result = wikipedia.summary(topic, sentences=2)
                speak_msg(ai.translate_output("According to Wikipedia", original_lang))
                speak_msg(ai.translate_output(result, original_lang))
            else:
                speak_msg(ai.translate_output("Please specify what topic you want to read about on Wikipedia.", original_lang))
        except Exception as e:
            print(f"Wikipedia Error: {e}")
            speak_msg(ai.translate_output("Sorry, I couldn't find anything on Wikipedia.", original_lang))

    else:
        # AI assistant fallback
        translated_input, detected_lang = ai.translate_input(command)
        ai_response = ai.ask_deepseek(translated_input)
        translated_response = ai.translate_output(ai_response, detected_lang)
        speak_msg(translated_response)


@main_bp.route('/')
def web_home():
    return render_template('index.html')


@main_bp.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    command_text = data.get('command', '')
    lang_code = data.get('lang', 'en')
    
    if not command_text:
        return jsonify({"status": "error", "message": "No command provided"}), 400
        
    responses = []
    actions = []
    
    def speak_callback(text):
        responses.append(text)
        
    def action_callback(action_type, value):
        actions.append({"type": action_type, "value": value})
        
    # Translate first
    translated_cmd, original_lang = ai.translate_input(command_text)
    if lang_code:
        original_lang = lang_code
        
    try:
        handle_command(translated_cmd, original_lang, speak_fn=speak_callback, action_fn=action_callback)
    except Exception as e:
        print(f"Error handling command: {e}")
        return jsonify({"status": "error", "message": "An error occurred while executing the command."}), 500
        
    return jsonify({
        "status": "success",
        "responses": responses,
        "actions": actions
    })

