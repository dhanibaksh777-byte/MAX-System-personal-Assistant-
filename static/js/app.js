/**
 * MAX AI Assistant — Frontend Application Logic
 * Handles speech recognition, TTS, API communication, and UI state management.
 */

// ═══════════════════════════════════════════════
// Configuration & State
// ═══════════════════════════════════════════════

const API_BASE = window.location.origin;

const STATE = {
    IDLE: 'idle',
    LISTENING: 'listening',
    PROCESSING: 'processing',
    SPEAKING: 'speaking',
    ERROR: 'error'
};

let currentState = STATE.IDLE;
let currentLanguage = 'en-US';
let languageCode = 'en';
let voiceEnabled = true;
let autoListen = false;
let speechRate = 1.0;
let isListening = false;
let recognition = null;
let synth = window.speechSynthesis;

// ═══════════════════════════════════════════════
// DOM Elements
// ═══════════════════════════════════════════════

const elements = {
    orbContainer: document.getElementById('orbContainer'),
    statusText: document.getElementById('statusText'),
    statusDot: document.getElementById('statusDot'),
    chatMessages: document.getElementById('chatMessages'),
    chatContainer: document.getElementById('chatContainer'),
    userInput: document.getElementById('userInput'),
    btnSend: document.getElementById('btnSend'),
    btnMic: document.getElementById('btnMic'),
    btnClearMemory: document.getElementById('btnClearMemory'),
    btnSettings: document.getElementById('btnSettings'),
    settingsPanel: document.getElementById('settingsPanel'),
    settingsClose: document.getElementById('settingsClose'),
    apiKeyInput: document.getElementById('apiKeyInput'),
    btnSaveKey: document.getElementById('btnSaveKey'),
    keyStatusText: document.getElementById('keyStatusText'),
    modelSelect: document.getElementById('modelSelect'),
    voiceToggle: document.getElementById('voiceToggle'),
    autoListenToggle: document.getElementById('autoListenToggle'),
    speechRateSlider: document.getElementById('speechRate'),
    speechRateValue: document.getElementById('speechRateValue'),
    langButtons: document.querySelectorAll('.lang-btn')
};

// ═══════════════════════════════════════════════
// State Management
// ═══════════════════════════════════════════════

function setState(state) {
    currentState = state;
    
    // Update orb
    elements.orbContainer.className = 'orb-container';
    if (state !== STATE.IDLE) {
        elements.orbContainer.classList.add(state);
    }

    // Update status dot
    elements.statusDot.className = 'status-dot';
    if (state !== STATE.IDLE) {
        elements.statusDot.classList.add(state);
    }

    // Update status text
    const statusTexts = {
        [STATE.IDLE]: 'Ready',
        [STATE.LISTENING]: 'Listening...',
        [STATE.PROCESSING]: 'Thinking...',
        [STATE.SPEAKING]: 'Speaking...',
        [STATE.ERROR]: 'Error'
    };
    elements.statusText.textContent = statusTexts[state] || 'Ready';

    // Update mic button
    elements.btnMic.classList.toggle('active', state === STATE.LISTENING);
}

// ═══════════════════════════════════════════════
// Speech Recognition
// ═══════════════════════════════════════════════

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        console.warn('Speech Recognition not supported');
        showToast('Speech recognition not supported in this browser');
        return null;
    }

    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = true;
    rec.lang = currentLanguage;
    rec.maxAlternatives = 1;

    rec.onstart = () => {
        isListening = true;
        setState(STATE.LISTENING);
    };

    rec.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        // Show interim results in input field
        if (interimTranscript) {
            elements.userInput.value = interimTranscript;
        }

        // Process final result
        if (finalTranscript) {
            elements.userInput.value = finalTranscript;
            sendMessage(finalTranscript);
        }
    };

    rec.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isListening = false;
        
        if (event.error === 'no-speech') {
            setState(STATE.IDLE);
            showToast('No speech detected. Try again.');
        } else if (event.error === 'not-allowed') {
            setState(STATE.ERROR);
            showToast('Microphone access denied. Please allow microphone access.');
        } else if (event.error !== 'aborted') {
            setState(STATE.IDLE);
        }
    };

    rec.onend = () => {
        isListening = false;
        if (currentState === STATE.LISTENING) {
            setState(STATE.IDLE);
        }
    };

    return rec;
}

function startListening() {
    if (isListening) {
        stopListening();
        return;
    }

    // Stop any ongoing speech
    synth.cancel();

    if (!recognition) {
        recognition = initSpeechRecognition();
    }

    if (recognition) {
        recognition.lang = currentLanguage;
        try {
            recognition.start();
        } catch (e) {
            // Already started, ignore
        }
    }
}

function stopListening() {
    if (recognition && isListening) {
        recognition.stop();
        isListening = false;
    }
}

// ═══════════════════════════════════════════════
// Text-to-Speech
// ═══════════════════════════════════════════════

function speak(text) {
    if (!voiceEnabled || !text) return;
    
    // Cancel any ongoing speech
    synth.cancel();
    
    setState(STATE.SPEAKING);

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = currentLanguage;
    utterance.rate = speechRate;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Try to find the best voice for the language
    const voices = synth.getVoices();
    const langPrefix = currentLanguage.split('-')[0];
    
    // Prefer Microsoft voices on Windows
    let bestVoice = voices.find(v => v.lang.startsWith(langPrefix) && v.name.includes('Microsoft'));
    if (!bestVoice) {
        bestVoice = voices.find(v => v.lang.startsWith(langPrefix));
    }
    // If Urdu voice is not installed, fallback to Hindi voice (phonetically identical script representation)
    if (!bestVoice && langPrefix === 'ur') {
        bestVoice = voices.find(v => v.lang.startsWith('hi'));
    }
    if (bestVoice) {
        utterance.voice = bestVoice;
    }

    utterance.onend = () => {
        setState(STATE.IDLE);
        if (autoListen) {
            setTimeout(startListening, 300);
        }
    };

    utterance.onerror = (e) => {
        console.error('TTS error:', e);
        setState(STATE.IDLE);
    };

    synth.speak(utterance);
}

// Preload voices
if (synth) {
    synth.getVoices();
    synth.onvoiceschanged = () => synth.getVoices();
}

// ═══════════════════════════════════════════════
// API Communication
// ═══════════════════════════════════════════════

async function sendMessage(text) {
    if (!text || !text.trim()) return;
    
    const message = text.trim();
    elements.userInput.value = '';
    autoResizeInput();
    
    // Stop listening
    stopListening();
    
    // Add user message to chat
    addMessage('user', message);

    // Show typing indicator
    const typingEl = showTypingIndicator();

    setState(STATE.PROCESSING);

    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                language: languageCode
            })
        });

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator(typingEl);

        if (data.error && typeof data.error === 'string') {
            addMessage('assistant', data.error, [], true);
            setState(STATE.ERROR);
            setTimeout(() => setState(STATE.IDLE), 3000);
            return;
        }

        // Show assistant response
        const actions = data.actions || [];
        addMessage('assistant', data.response, actions, data.error === true);

        // Speak the response
        if (!data.error) {
            speak(data.response);
        } else {
            setState(STATE.IDLE);
        }

    } catch (error) {
        console.error('API Error:', error);
        removeTypingIndicator(typingEl);
        addMessage('assistant', 'Connection error. Make sure the Max server is running.', [], true);
        setState(STATE.ERROR);
        setTimeout(() => setState(STATE.IDLE), 3000);
    }
}

// ═══════════════════════════════════════════════
// Chat UI
// ═══════════════════════════════════════════════

function addMessage(role, content, actions = [], isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const avatar = role === 'assistant' ? 'M' : 'U';
    
    let actionsHtml = '';
    if (actions && actions.length > 0) {
        actionsHtml = actions.map(a => {
            const success = a.result?.success;
            const msg = a.result?.message || a.function;
            return `<div class="action-badge ${success ? '' : 'error'}">
                ${success ? '✓' : '✗'} ${escapeHtml(msg)}
            </div>`;
        }).join('');
    }

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content ${isError ? 'error-content' : ''}">
            <p>${formatMessage(content)}</p>
            ${actionsHtml}
        </div>
    `;

    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant-message typing-message';
    typingDiv.innerHTML = `
        <div class="message-avatar">M</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    elements.chatMessages.appendChild(typingDiv);
    scrollToBottom();
    return typingDiv;
}

function removeTypingIndicator(el) {
    if (el && el.parentNode) {
        el.parentNode.removeChild(el);
    }
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    });
}

function formatMessage(text) {
    if (!text) return '';
    // Convert markdown-like formatting
    let formatted = escapeHtml(text);
    // Bold: **text** or __text__
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/__(.*?)__/g, '<strong>$1</strong>');
    // Inline code: `code`
    formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>');
    // Line breaks
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ═══════════════════════════════════════════════
// Toast Notifications
// ═══════════════════════════════════════════════

let toastTimeout = null;
function showToast(message) {
    let toast = document.querySelector('.toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    
    toast.textContent = message;
    toast.classList.add('show');
    
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ═══════════════════════════════════════════════
// Input Handling
// ═══════════════════════════════════════════════

function autoResizeInput() {
    const input = elements.userInput;
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 80) + 'px';
}

// ═══════════════════════════════════════════════
// Event Listeners
// ═══════════════════════════════════════════════

// Send button
elements.btnSend.addEventListener('click', () => {
    sendMessage(elements.userInput.value);
});

// Mic button
elements.btnMic.addEventListener('click', startListening);

// Input field
elements.userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(elements.userInput.value);
    }
});

elements.userInput.addEventListener('input', autoResizeInput);

// Keyboard shortcuts (when input not focused)
document.addEventListener('keydown', (e) => {
    // Space to toggle mic (only when not typing)
    if (e.code === 'Space' && document.activeElement !== elements.userInput) {
        e.preventDefault();
        startListening();
    }
    
    // Escape to stop everything
    if (e.key === 'Escape') {
        synth.cancel();
        stopListening();
        setState(STATE.IDLE);
    }
    
    // Ctrl+/ to focus input
    if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        elements.userInput.focus();
    }
});

// Language buttons
elements.langButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        elements.langButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentLanguage = btn.dataset.lang;
        languageCode = btn.dataset.code;
        
        const langNames = { 'en': 'English', 'hi': 'Hindi', 'ur': 'Urdu' };
        showToast(`Language: ${langNames[languageCode] || languageCode}`);
    });
});

// Clear memory
elements.btnClearMemory.addEventListener('click', async () => {
    if (confirm('Clear all conversation memory?')) {
        try {
            await fetch(`${API_BASE}/api/memory/clear`, { method: 'POST' });
            // Clear chat UI
            elements.chatMessages.innerHTML = '';
            addMessage('assistant', 'Memory cleared. Starting fresh! How can I help you?');
            showToast('Memory cleared');
        } catch (e) {
            showToast('Failed to clear memory');
        }
    }
});

// Settings panel
elements.btnSettings.addEventListener('click', () => {
    elements.settingsPanel.classList.toggle('open');
    if (elements.settingsPanel.classList.contains('open')) {
        loadSettings();
    }
});

elements.settingsClose.addEventListener('click', () => {
    elements.settingsPanel.classList.remove('open');
});

// Settings API key & model
if (elements.btnSaveKey) {
    elements.btnSaveKey.addEventListener('click', async () => {
        const key = elements.apiKeyInput.value.trim();
        const model = elements.modelSelect.value;
        if (!key && !elements.apiKeyInput.placeholder.includes('...')) {
            showToast('Please enter an API key');
            return;
        }
        try {
            elements.btnSaveKey.textContent = 'Saving...';
            const res = await fetch(`${API_BASE}/api/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: key, model: model })
            });
            const data = await res.json();
            showToast(data.message || 'Settings saved');
            elements.btnSaveKey.textContent = 'Save';
            if (key) {
                elements.apiKeyInput.placeholder = (key.slice(0, 4) + '...' + key.slice(-4));
                elements.apiKeyInput.value = '';
            }
            updateKeyStatus(data.api_configured);
        } catch (e) {
            elements.btnSaveKey.textContent = 'Save';
            showToast('Failed to save settings');
        }
    });
}

if (elements.modelSelect) {
    elements.modelSelect.addEventListener('change', async () => {
        const model = elements.modelSelect.value;
        try {
            await fetch(`${API_BASE}/api/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: model })
            });
            showToast(`Model set: ${model}`);
        } catch (e) {
            showToast('Failed to update model');
        }
    });
}

async function loadSettings() {
    try {
        const res = await fetch(`${API_BASE}/api/settings`);
        const data = await res.json();
        if (data.masked_key && elements.apiKeyInput) {
            elements.apiKeyInput.placeholder = data.masked_key;
        }
        if (data.model && elements.modelSelect) {
            elements.modelSelect.value = data.model;
        }
        updateKeyStatus(data.api_configured);
    } catch (e) {
        console.warn('Could not load settings:', e);
    }
}

function updateKeyStatus(configured) {
    if (!elements.keyStatusText) return;
    if (configured) {
        elements.keyStatusText.textContent = '● AI Engine Active (Groq Llama 3.3)';
        elements.keyStatusText.className = 'key-status active';
    } else {
        elements.keyStatusText.textContent = '⚡ Local Mode (System Commands Ready)';
        elements.keyStatusText.className = 'key-status warning';
    }
}

// Settings controls
elements.voiceToggle.addEventListener('change', (e) => {
    voiceEnabled = e.target.checked;
    showToast(voiceEnabled ? 'Voice enabled' : 'Voice disabled');
});

elements.autoListenToggle.addEventListener('change', (e) => {
    autoListen = e.target.checked;
    showToast(autoListen ? 'Auto-listen ON' : 'Auto-listen OFF');
});

elements.speechRateSlider.addEventListener('input', (e) => {
    speechRate = parseFloat(e.target.value);
    elements.speechRateValue.textContent = speechRate.toFixed(1) + 'x';
});

// ═══════════════════════════════════════════════
// Health Check
// ═══════════════════════════════════════════════

async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/api/health`);
        const data = await res.json();
        updateKeyStatus(data.api_configured);
        
        if (!data.api_configured) {
            // Friendly tip that apps are ready and API key unlocks conversation
            setTimeout(() => {
                showToast('Tip: Apps & commands ready! Add free Groq key in Settings for AI chat.');
            }, 1000);
        }
    } catch (e) {
        setState(STATE.ERROR);
        addMessage('assistant', 'Cannot connect to Max server. Make sure it is running via CMD.', [], true);
    }
}

// ═══════════════════════════════════════════════
// Initialization
// ═══════════════════════════════════════════════

function init() {
    // Initialize speech recognition
    recognition = initSpeechRecognition();
    
    // Check server health & load settings
    setTimeout(() => {
        checkHealth();
        loadSettings();
    }, 400);
    
    // Focus input
    elements.userInput.focus();
    
    console.log('%c MAX AI Assistant %c v1.0 Online ', 
        'background: #00d4ff; color: #060612; font-weight: bold; padding: 4px 8px; border-radius: 4px 0 0 4px;',
        'background: #7b2ff7; color: white; padding: 4px 8px; border-radius: 0 4px 4px 0;'
    );
}

// Start when DOM is ready
document.addEventListener('DOMContentLoaded', init);
// Also run if DOM already loaded
if (document.readyState !== 'loading') {
    init();
}
