import asyncio
import requests
from googletrans import Translator
from . import config

# Initialize translator module
translator = Translator()

# Translate input to English & detect original language
def translate_input(text):
    if not text:
        return "", "en"
    
    async def do_translate():
        local_translator = Translator()
        detected = await local_translator.detect(text)
        src_lang = detected.lang if detected else "en"
        translated = await local_translator.translate(text, src=src_lang, dest='en')
        return translated.text, src_lang
        
    try:
        return asyncio.run(do_translate())
    except Exception as e:
        print(f"Translation Error (Input): {e}")
        return text, 'en'

# Translate back to original language
def translate_output(text, lang):
    if lang == 'en' or not text:
        return text
        
    async def do_translate_back():
        local_translator = Translator()
        translated = await local_translator.translate(text, dest=lang)
        return translated.text
        
    try:
        return asyncio.run(do_translate_back())
    except Exception as e:
        print(f"Translation Error (Output): {e}")
        return text

# Ask Deepseek or OpenRouter depending on API key type
def ask_deepseek(question):
    # Detect placeholder key
    if not config.DEEPSEEK_API_KEY or "..." in config.DEEPSEEK_API_KEY:
        print("Warning: API key is a placeholder or not provided.")
        return "I'm running in local mode because my API key is not configured. Please set a valid API key in the script to enable my AI brain."
    
    # Check if the key is for OpenRouter
    if config.DEEPSEEK_API_KEY.startswith("sk-or-"):
        url = "https://openrouter.ai/api/v1/chat/completions"
        model = "google/gemini-2.5-flash"
        headers = {
            "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "Jarvis Assistant"
        }
        data = {
            "model": model,
            "max_tokens": 1024,
            "messages": [
                {"role": "system", "content": "You are Jarvis, a personal AI assistant created and developed by PALLAB BAG. You were NOT made by Google, OpenAI, or any other company. If anyone asks who made you, who created you, or who developed you, always say 'I was created by PALLAB BAG'. Keep responses concise and clear."},
                {"role": "user", "content": question}
            ]
        }
    else:
        # Direct Deepseek
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "max_tokens": 1024,
            "messages": [
                {"role": "system", "content": "You are Jarvis, a personal AI assistant created and developed by PALLAB BAG. You were NOT made by Google, OpenAI, or any other company. If anyone asks who made you, who created you, or who developed you, always say 'I was created by PALLAB BAG'. Keep responses concise and clear."},
                {"role": "user", "content": question}
            ]
        }
        
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            return f"Received an unexpected response format from the AI API: {result}"
    except Exception as e:
        print(f"LLM API Error: {e}")
        return "Sorry, I couldn't reach my AI brain. Please check your internet connection and API key configuration."

# Get weather info
def get_weather(city="Delhi"):
    try:
        url = f"https://wttr.in/{city}?format=3"
        response = requests.get(url, timeout=10)
        return response.text.strip()
    except Exception as e:
        print(f"Weather Fetch Error: {e}")
        return "Sorry, I can't fetch the weather now."
