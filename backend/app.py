import os
import sys
import time
import threading
import webbrowser
from flask import Flask
from . import config, speech, ai, routes

# Initialize Flask with explicit modular paths
app = Flask(__name__, 
            template_folder=config.TEMPLATE_DIR, 
            static_folder=config.STATIC_DIR, 
            static_url_path='')

# Register Blueprint
app.register_blueprint(routes.main_bp)

# Enable CORS natively to support local file access
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    return response

# CLI Runner
def run_cli_mode():
    speech.speak("Hello! I am Jarvis, your assistant.")
    
    # Choose preferred language
    print("\n🌍 Choose your preferred language:")
    for lang, code in config.LANGUAGE_CODES.items():
        print(f" - {lang.capitalize()}: {code}")
    user_lang_code = input("Enter language code (default 'en'): ").strip().lower()
    if user_lang_code not in config.LANGUAGE_CODES.values():
        user_lang_code = "en"

    # Set speech recognition locale code based on selected language
    rec_lang = 'en-US'
    if user_lang_code == 'bn':
        rec_lang = 'bn-BD'
    elif user_lang_code == 'hi':
        rec_lang = 'hi-IN'
    elif user_lang_code == 'es':
        rec_lang = 'es-ES'
    elif user_lang_code == 'fr':
        rec_lang = 'fr-FR'
    elif user_lang_code == 'de':
        rec_lang = 'de-DE'
    elif user_lang_code == 'ja':
        rec_lang = 'ja-JP'
    elif user_lang_code == 'ko':
        rec_lang = 'ko-KR'
    elif user_lang_code == 'ru':
        rec_lang = 'ru-RU'
    elif user_lang_code == 'zh-cn':
        rec_lang = 'zh-CN'

    welcome = ai.translate_output("How can I help you today?", user_lang_code)
    speech.speak(welcome)
    time.sleep(0.5)

    while True:
        print("\n⚙️ Choose input mode:")
        print("1. Speak 🎤")
        print("2. Type ✍️")
        choice = input("Enter choice (1 or 2, default is 1): ").strip()
        
        command = ""
        if choice == '2':
            command = speech.get_typed_command()
        else:
            command = speech.listen(rec_lang)
            
        if command:
            if "exit" in command or "stop" in command or "quit" in command:
                speech.speak(ai.translate_output("Goodbye! Have a nice day.", user_lang_code))
                break
            
            # Translate input before running commands
            translated_command, original_lang = ai.translate_input(command)
            # Process command
            routes.handle_command(translated_command, original_lang)

# Helper to open the browser after a short delay
def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:5000")

# --- Main Entry Point ---
def main():
    # Support command-line flags to bypass interactive prompt
    if '--web' in sys.argv:
        mode = '2'
    elif '--cli' in sys.argv:
        mode = '1'
    else:
        print("🤖 Jarvis Assistant Setup")
        print("1. CLI Mode (Console) 💻")
        print("2. Web Mode (Animated Holographic UI) 🌍")
        mode = input("Select mode (1 or 2, default is 2): ").strip()
    
    if mode == '1':
        config.is_web_mode = False
        run_cli_mode()
    else:
        config.is_web_mode = True
        print("\n🚀 Starting Jarvis Web Server on http://localhost:5000")
        # Automatically open browser window in the background
        threading.Thread(target=open_browser, daemon=True).start()
        app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    main()
