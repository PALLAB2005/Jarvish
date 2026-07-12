import os
import sys

# Reconfigure console encoding for emojis on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: frontend is located at parent directory level relative to backend
TEMPLATE_DIR = os.path.abspath(os.path.join(BASE_DIR, '../frontend'))
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '../frontend'))

# Helper to load API key from .env file
def load_api_key():
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    
                    if ":" in line:
                        k, v = line.split(":", 1)
                    elif "=" in line:
                        k, v = line.split("=", 1)
                    else:
                        continue
                    
                    k = k.strip().upper().replace("_", " ").replace("-", " ")
                    if k in ["API KEY", "APIKEY", "DEEPSEEK API KEY", "OPENROUTER API KEY"]:
                        val = v.strip().rstrip(';').strip().strip('"').strip("'").strip()
                        return val
        except Exception as e:
            print(f"Error reading .env file: {e}")
    return None

# Load Deepseek / OpenRouter API key
DEEPSEEK_API_KEY = load_api_key()
if not DEEPSEEK_API_KEY:
    DEEPSEEK_API_KEY = "sk-or-v1-351...c0b"  # Default fallback placeholder

# Supported Language Codes for Google Translate
LANGUAGE_CODES = {
    "english": "en",
    "bengali": "bn",
    "hindi": "hi",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "japanese": "ja",
    "korean": "ko",
    "russian": "ru",
    "chinese": "zh-cn"
}

# Global states
is_web_mode = False
web_response_buffer = []
