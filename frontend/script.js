// DOM Elements
const jarvisCoreBtn = document.getElementById('jarvisCoreBtn');
const hologramContainer = document.getElementById('hologramContainer');
const stateLabel = document.getElementById('stateLabel');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const langSelect = document.getElementById('langSelect');
const consoleLog = document.getElementById('consoleLog');
const cmdInput = document.getElementById('cmdInput');
const sendBtn = document.getElementById('sendBtn');
const micBtn = document.getElementById('micBtn');

// States: 'idle', 'listening', 'thinking', 'speaking'
let currentState = 'idle';
let speechRecognition = null;
let isListeningInstance = false;

// Initialize Speech Synthesis
const synth = window.speechSynthesis;

// Initialize Speech Recognition
const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognitionAPI) {
    speechRecognition = new SpeechRecognitionAPI();
    speechRecognition.continuous = false;
    speechRecognition.interimResults = false;

    speechRecognition.onstart = () => {
        isListeningInstance = true;
        setJarvisState('listening');
        micBtn.classList.add('active');
    };

    speechRecognition.onend = () => {
        isListeningInstance = false;
        micBtn.classList.remove('active');
        if (currentState === 'listening') {
            setJarvisState('idle');
        }
    };

    speechRecognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        appendLog(text, 'user');
        processCommand(text);
    };

    speechRecognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error !== 'no-speech') {
            appendLog(`Speech recognition failed: ${event.error}`, 'system');
        }
        setJarvisState('idle');
    };
} else {
    console.warn('Speech Recognition not supported in this browser.');
    micBtn.style.display = 'none';
    appendLog('System Note: Voice input is not supported in this browser. Please use keyboard input.', 'system');
}

// Set Jarvis State (Handles Colors, Animations, Status Panels)
function setJarvisState(state) {
    currentState = state;
    hologramContainer.className = `hologram-container ${state}`;

    // Labels and Indicator colors
    switch (state) {
        case 'listening':
            stateLabel.innerText = 'LISTENING...';
            statusText.innerText = 'LISTENING';
            statusDot.style.backgroundColor = 'var(--state-listening-color)';
            statusDot.style.boxShadow = '0 0 10px var(--state-listening-color)';
            break;
        case 'thinking':
            stateLabel.innerText = 'THINKING...';
            statusText.innerText = 'THINKING';
            statusDot.style.backgroundColor = 'var(--state-thinking-color)';
            statusDot.style.boxShadow = '0 0 10px var(--state-thinking-color)';
            break;
        case 'speaking':
            stateLabel.innerText = 'SPEAKING...';
            statusText.innerText = 'TRANSMITTING';
            statusDot.style.backgroundColor = 'var(--state-speaking-color)';
            statusDot.style.boxShadow = '0 0 10px var(--state-speaking-color)';
            break;
        case 'idle':
        default:
            stateLabel.innerText = 'SYSTEM IDLE';
            statusText.innerText = 'ONLINE';
            statusDot.style.backgroundColor = 'var(--state-idle-color)';
            statusDot.style.boxShadow = '0 0 10px var(--state-idle-color)';
            break;
    }
}

// Speak Text using Browser Speech Synthesis
function speakText(text) {
    // Cancel current speech if any
    synth.cancel();

    if (!text) {
        setJarvisState('idle');
        return;
    }

    const utterance = new SpeechSynthesisUtterance(text);

    // Map selected language to Voice URI / language code
    const selectedLang = langSelect.value;
    utterance.lang = selectedLang;

    // Attempt to find a suitable local voice matching language
    const voices = synth.getVoices();
    let voiceMatch = voices.find(v => v.lang.startsWith(selectedLang));
    if (voiceMatch) {
        utterance.voice = voiceMatch;
    }

    utterance.onstart = () => {
        setJarvisState('speaking');
    };

    utterance.onend = () => {
        setJarvisState('idle');
    };

    utterance.onerror = (e) => {
        console.error('Speech synthesis error:', e);
        setJarvisState('idle');
    };

    // Speak the utterance
    synth.speak(utterance);
}

// Append text to terminal log
function appendLog(text, sender) {
    const bubble = document.createElement('div');
    bubble.className = `log-bubble ${sender}`;
    bubble.innerText = text;
    consoleLog.appendChild(bubble);
    consoleLog.scrollTop = consoleLog.scrollHeight;
}

// Send query to python backend via standard HTTP POST /chat
function processCommand(commandText) {
    if (!commandText.trim()) return;

    setJarvisState('thinking');

    const url = window.location.protocol === 'file:' ? 'https://jarvis-web-assistent.netlify.app/' : '/chat';

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            command: commandText,
            lang: langSelect.value
        })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Check if there are any voice responses
                if (data.responses && data.responses.length > 0) {
                    // Combine responses into a single string for TTS and logs
                    const fullResponse = data.responses.join(' ');
                    appendLog(fullResponse, 'jarvis');
                    speakText(fullResponse);
                } else {
                    setJarvisState('idle');
                }

                // Check if there are any browser actions to run
                if (data.actions && data.actions.length > 0) {
                    data.actions.forEach(act => {
                        if (act.type === 'open_url' && act.value) {
                            window.open(act.value, '_blank');
                        }
                    });
                }
            } else {
                const errorMsg = data.message || "An unknown error occurred.";
                appendLog(`Error: ${errorMsg}`, 'system');
                speakText(errorMsg);
                setJarvisState('idle');
            }
        })
        .catch(err => {
            console.error('Fetch error:', err);
            appendLog('Error: Connection to system backend failed.', 'system');
            speakText('Connection to system backend failed.');
            setJarvisState('idle');
        });
}

// Trigger Listening Session
function toggleVoiceRecognition() {
    if (!speechRecognition) return;
    if (isListeningInstance) {
        speechRecognition.stop();
    } else {
        // Configure speech recognition locale based on select
        const code = langSelect.value;
        let locale = 'en-US';
        if (code === 'bn') locale = 'bn-BD';
        else if (code === 'hi') locale = 'hi-IN';
        else if (code === 'es') locale = 'es-ES';
        else if (code === 'fr') locale = 'fr-FR';
        else if (code === 'de') locale = 'de-DE';
        else if (code === 'ja') locale = 'ja-JP';
        else if (code === 'ko') locale = 'ko-KR';
        else if (code === 'ru') locale = 'ru-RU';
        else if (code === 'zh-CN') locale = 'zh-CN';

        speechRecognition.lang = locale;
        speechRecognition.start();
    }
}

// Event Listeners
jarvisCoreBtn.addEventListener('click', toggleVoiceRecognition);
micBtn.addEventListener('click', toggleVoiceRecognition);

sendBtn.addEventListener('click', () => {
    const cmd = cmdInput.value;
    if (cmd.trim()) {
        appendLog(cmd, 'user');
        cmdInput.value = '';
        processCommand(cmd);
    }
});

cmdInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendBtn.click();
    }
});

// Preload voices (Chrome requires this event listener)
if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = () => { };
}
