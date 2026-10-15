"""
Max Assistant - Core AI Engine
Handles LLM integration with Groq API, function calling, and response generation.
"""
import requests
import json
import re
from datetime import datetime
from config import GROQ_API_KEY, GROQ_API_URL, MODEL_NAME, SYSTEM_PROMPT, CONTEXT_WINDOW
from memory_manager import MemoryManager
from system_controller import SystemController


class AssistantCore:
    """Core AI engine with LLM integration and function calling."""

    def __init__(self):
        self.memory = MemoryManager()
        self.system = SystemController()
        self.tools = self._define_tools()

    def _define_tools(self):
        """Define available function calling tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "open_application",
                    "description": "Open a desktop application on the user's Windows computer. Use this for apps like Notepad, Calculator, Spotify, WhatsApp, VS Code, Chrome, File Explorer, Settings, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {
                                "type": "string",
                                "description": "Name of the application to open (e.g., 'notepad', 'calculator', 'spotify', 'vs code', 'whatsapp', 'chrome', 'file explorer')"
                            }
                        },
                        "required": ["app_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "open_website",
                    "description": "Open a website URL in the default web browser. Use this for websites like YouTube, Google, Gmail, WhatsApp Web, Facebook, Instagram, GitHub, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to open (e.g., 'https://youtube.com', 'https://github.com')"
                            },
                            "site_name": {
                                "type": "string",
                                "description": "Friendly name of the website (e.g., 'YouTube', 'GitHub')"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search for information on the internet using Google. Use when user asks to search for something or look something up online.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to look up"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "play_on_youtube",
                    "description": "Search and play a video, song, or music on YouTube. Use when user asks to play something, listen to music, or watch a video.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What to search/play on YouTube (e.g., 'Arijit Singh songs', 'Python tutorial', 'lofi beats')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "system_command",
                    "description": "Execute a system-level command. Use for shutdown, restart, lock screen, sleep, screenshot, volume control.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["shutdown", "restart", "lock", "sleep", "screenshot", "volume_up", "volume_down", "mute"],
                                "description": "The system action to perform"
                            }
                        },
                        "required": ["action"]
                    }
                }
            }
        ]

    def _get_system_prompt(self):
        """Get the system prompt with current timestamp."""
        return SYSTEM_PROMPT.format(
            current_time=datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        )

    def _execute_function(self, func_name: str, args: dict) -> dict:
        """Execute a function call and return the result."""
        try:
            if func_name == "open_application":
                return self.system.open_application(args.get("app_name", ""))
            elif func_name == "open_website":
                return self.system.open_website(
                    args.get("url", ""),
                    args.get("site_name", "")
                )
            elif func_name == "search_web":
                return self.system.search_web(args.get("query", ""))
            elif func_name == "play_on_youtube":
                return self.system.play_on_youtube(args.get("query", ""))
            elif func_name == "system_command":
                return self.system.system_command(args.get("action", ""))
            else:
                return {"success": False, "message": f"Unknown function: {func_name}"}
        except Exception as e:
            return {"success": False, "message": f"Error executing {func_name}: {str(e)}"}

    def reload_config(self):
        """Reload configuration from .env file."""
        import importlib
        import config
        importlib.reload(config)
        return bool(config.GROQ_API_KEY and config.GROQ_API_KEY != "your_groq_api_key_here")

    def _detect_language(self, text: str, default_lang: str = "en") -> str:
        """Detect language (en, hi, ur) from message content or script."""
        text_lower = text.lower()
        # Arabic/Urdu unicode script range: \u0600-\u06FF
        if any('\u0600' <= char <= '\u06ff' for char in text):
            return "ur"
        # Devanagari/Hindi unicode script range: \u0900-\u097F
        if any('\u0900' <= char <= '\u097f' for char in text):
            return "hi"
        # Common Roman Urdu / Hinglish words
        roman_indic_markers = ['kholo', 'chalao', 'karo', 'kaun', 'mera', 'meri', 'kya', 
                                'haal', 'kaise', 'kaisey', 'batao', 'suno', 'aawaz', 'awaaz', 
                                'badhao', 'kam karo', 'band karo', 'namaste', 'salam']
        for marker in roman_indic_markers:
            if marker in text_lower:
                return "ur" if default_lang == "ur" else "hi"
        return default_lang

    def _fast_path(self, user_message: str, lang: str):
        """
        Zero-delay (<5ms) rule-based intent matching for apps, web, media,
        system volume, screen lock, and core Jarvis conversational commands.
        Eliminates network lag and hallucination for direct laptop tasks.
        """
        msg = user_message.strip()
        msg_lower = msg.lower()

        # ─── 1. Identity & Greetings ───
        if any(q in msg_lower for q in ['tum kaun ho', 'aap kaun ho', 'aap kaun hain', 'who are you', 'what is your name', 'tumhara naam kya hai', 'aapka naam', 'تم کون ہو', 'तुम कौन हो']):
            if lang == "ur":
                reply = "میں میکس ہوں، آپ کا پرسنل اے آئی اسسٹنٹ! میں آپ کے لیپ ٹاپ کی ایپس اوپن کر سکتا ہوں، گانے چلا سکتا ہوں اور سسٹم کنٹرول کر سکتا ہوں۔ فرمائیے، میں آپ کی کیا مدد کروں؟"
            elif lang == "hi":
                reply = "मैं मैक्स हूँ, आपका पर्सनल एआई असिस्टेंट! मैं आपके सिस्टम ऐप्स खोल सकता हूँ, यूट्यूब और गाने चला सकता हूँ और बातें कर सकता हूँ। बताइए, क्या मदद करूँ?"
            else:
                reply = "I am Max, your personal AI assistant. I can launch apps, play music, search the web, manage system controls, and converse in English, Hindi, and Urdu."
            return {'response': reply, 'actions': [], 'error': False, 'fast_path': True}

        if any(q in msg_lower for q in ['kaisey ho', 'kaise ho', 'kya haal hai', 'how are you', 'how are you doing', 'حال کیسا ہے', 'کیسے ہو', 'कैसे हो']):
            if lang == "ur":
                reply = "الحمدللہ، میں بالکل مستعد اور تیار ہوں! آپ بتائیں، کیا حکم ہے؟"
            elif lang == "hi":
                reply = "मैं बिल्कुल ठीक और तैयार हूँ! आप बताइए, आज क्या करना है?"
            else:
                reply = "All systems operational and ready for your command, Sir! How can I help you today?"
            return {'response': reply, 'actions': [], 'error': False, 'fast_path': True}

        if any(msg_lower == g for g in ['hi', 'hello', 'hey', 'salam', 'assalam o alaikum', 'assalamu alaikum', 'namaste', 'مرحبا', 'ہیلو', 'سلام']):
            if lang == "ur":
                reply = "وعلیکم السلام! میکس حاضر ہے۔ بتائیے کیا کام کروں؟"
            elif lang == "hi":
                reply = "नमस्ते! मैक्स तैयार है। बताइए आज क्या सेवा करूँ?"
            else:
                reply = "Hello! Max online and at your service. What would you like to do?"
            return {'response': reply, 'actions': [], 'error': False, 'fast_path': True}

        # ─── 2. System Volume & Hardware Commands ───
        if any(v in msg_lower for v in ['volume up', 'increase volume', 'aawaz badhao', 'awaaz badhao', 'aawaz tez karo', 'آواز بڑھاؤ', 'आवाज़ बढ़ाओ']):
            action_res = self.system.system_command('volume_up')
            reply = "Volume increased." if lang == "en" else "Aawaz badha di gayi hai."
            return {'response': reply, 'actions': [{'function': 'system_command', 'args': {'action': 'volume_up'}, 'result': action_res}], 'error': False, 'fast_path': True}

        if any(v in msg_lower for v in ['volume down', 'decrease volume', 'aawaz kam karo', 'awaaz kam karo', 'aawaz dheemi karo', 'آواز کم کرو', 'आवाज़ कम करो']):
            action_res = self.system.system_command('volume_down')
            reply = "Volume decreased." if lang == "en" else "Aawaz kam kar di gayi hai."
            return {'response': reply, 'actions': [{'function': 'system_command', 'args': {'action': 'volume_down'}, 'result': action_res}], 'error': False, 'fast_path': True}

        if any(v in msg_lower for v in ['mute', 'silent', 'aawaz band karo', 'chup ho jao', 'میوٹ کرو', 'म्यूट करो']):
            action_res = self.system.system_command('mute')
            reply = "Audio muted." if lang == "en" else "Aawaz mute kar di gayi hai."
            return {'response': reply, 'actions': [{'function': 'system_command', 'args': {'action': 'mute'}, 'result': action_res}], 'error': False, 'fast_path': True}

        if any(s in msg_lower for s in ['lock screen', 'lock pc', 'screen lock karo', 'lock my laptop', 'اسکرین لاک کرو', 'स्क्रीन लॉक करो']):
            action_res = self.system.system_command('lock')
            reply = "Locking system." if lang == "en" else "System lock kar raha hoon."
            return {'response': reply, 'actions': [{'function': 'system_command', 'args': {'action': 'lock'}, 'result': action_res}], 'error': False, 'fast_path': True}

        if any(s in msg_lower for s in ['screenshot', 'take screenshot', 'screenshot lo', 'screen shot', 'اسکرین شاٹ', 'स्क्रीनशॉट लो']):
            action_res = self.system.system_command('screenshot')
            reply = "Opening Snipping Tool for screenshot." if lang == "en" else "Screenshot tool open kar raha hoon."
            return {'response': reply, 'actions': [{'function': 'system_command', 'args': {'action': 'screenshot'}, 'result': action_res}], 'error': False, 'fast_path': True}

        # ─── 3. Play Music / YouTube Search ───
        yt_patterns = [
            r'play\s+(.*?)\s+on\s+youtube',
            r'play\s+(.*)',
            r'youtube\s+par\s+(.*?)\s+chalao',
            r'youtube\s+pe\s+(.*?)\s+chalao',
            r'youtube\s+par\s+(.*?)\s+bajao',
            r'youtube\s+pe\s+(.*?)\s+bajao',
            r'(.*?)\s+gaana\s+bajao',
            r'(.*?)\s+gaana\s+chalao',
            r'(.*?)\s+song\s+play\s+karo',
            r'یوٹیوب\s+پر\s+(.*?)\s+چلاؤ',
            r'यूट्यूब\s+पर\s+(.*?)\s+चलाओ'
        ]
        for pattern in yt_patterns:
            m = re.search(pattern, msg_lower)
            if m:
                query = m.group(1).strip()
                # Exclude trivial matches like just "youtube"
                if query and query not in ['youtube', 'on youtube', 'kholo']:
                    action_res = self.system.play_on_youtube(query)
                    if lang == "ur":
                        reply = f"یوٹیوب پر '{query}' چلا رہا ہوں، جناب!"
                    elif lang == "hi":
                        reply = f"यूट्यूब पर '{query}' चला रहा हूँ, सर!"
                    else:
                        reply = f"Playing '{query}' on YouTube right away, Sir!"
                    return {'response': reply, 'actions': [{'function': 'play_on_youtube', 'args': {'query': query}, 'result': action_res}], 'error': False, 'fast_path': True}

        # ─── 4. Web Search ───
        search_patterns = [
            r'search\s+(?:google\s+for|for)\s+(.*)',
            r'google\s+(.*)',
            r'google\s+par\s+search\s+karo\s+(.*)',
            r'google\s+pe\s+search\s+karo\s+(.*)',
            r'(.*?)\s+search\s+karo',
            r'گوگل\s+پر\s+سرچ\s+کرو\s+(.*)',
            r'गूगल\s+पर\s+सर्च\s+करो\s+(.*)'
        ]
        for pattern in search_patterns:
            m = re.search(pattern, msg_lower)
            if m:
                query = m.group(1).strip()
                if query and query not in ['google', 'search', 'karo']:
                    action_res = self.system.search_web(query)
                    if lang == "ur":
                        reply = f"گوگل پر '{query}' تلاش کر رہا ہوں۔"
                    elif lang == "hi":
                        reply = f"गूगल पर '{query}' सर्च कर रहा हूँ।"
                    else:
                        reply = f"Searching Google for: '{query}'"
                    return {'response': reply, 'actions': [{'function': 'search_web', 'args': {'query': query}, 'result': action_res}], 'error': False, 'fast_path': True}

        # ─── 5. App & Website Opening ───
        # Check direct keywords
        target_app = None

        # Check English commands: "open X", "launch X"
        open_match = re.search(r'^(?:open|launch|start)\s+([a-zA-Z0-9\s]+)$', msg_lower)
        if open_match:
            target_app = open_match.group(1).strip()

        # Check Hindi/Urdu commands: "X kholo", "X open karo", "X chalao", "X کھولو", "X खोलो"
        indic_match = re.search(r'^([a-zA-Z0-9\s]+?)\s+(?:kholo|open karo|chalao|khol do|کھولو|اوپن کرو|खोलो)$', msg_lower)
        if indic_match:
            target_app = indic_match.group(1).strip()

        # Specific well-known app single words (e.g. "youtube", "whatsapp", "spotify", "notepad", "calculator")
        common_apps = ['youtube', 'whatsapp', 'spotify', 'notepad', 'calculator', 'chrome', 'edge', 
                       'word', 'excel', 'powerpoint', 'vs code', 'vscode', 'telegram', 'discord', 
                       'camera', 'paint', 'settings', 'file explorer']
        if msg_lower in common_apps:
            target_app = msg_lower

        if target_app:
            # Special case: Spotify
            if 'spotify' in target_app or 'music' in target_app or 'gaana' in target_app:
                action_res = self.system.open_application('spotify')
                reply = "Opening Spotify, Sir!" if lang == "en" else "Spotify khol raha hoon!"
                return {'response': reply, 'actions': [{'function': 'open_application', 'args': {'app_name': 'spotify'}, 'result': action_res}], 'error': False, 'fast_path': True}

            # Special case: WhatsApp
            if 'whatsapp' in target_app or 'whatsap' in target_app:
                action_res = self.system.open_application('whatsapp')
                reply = "Opening WhatsApp, Sir!" if lang == "en" else "WhatsApp khol raha hoon!"
                return {'response': reply, 'actions': [{'function': 'open_application', 'args': {'app_name': 'whatsapp'}, 'result': action_res}], 'error': False, 'fast_path': True}

            # Special case: YouTube
            if 'youtube' in target_app or 'yt' in target_app:
                action_res = self.system.open_website('https://www.youtube.com', 'YouTube')
                reply = "Opening YouTube, Sir!" if lang == "en" else "YouTube khol raha hoon!"
                return {'response': reply, 'actions': [{'function': 'open_website', 'args': {'url': 'https://www.youtube.com'}, 'result': action_res}], 'error': False, 'fast_path': True}

            # Generic app open
            action_res = self.system.open_application(target_app)
            if action_res.get('success'):
                if lang == "ur":
                    reply = f"{target_app.title()} کھول رہا ہوں، سر!"
                elif lang == "hi":
                    reply = f"{target_app.title()} खोल रहा हूँ, सर!"
                else:
                    reply = f"Opening {target_app.title()} right away, Sir!"
                return {'response': reply, 'actions': [{'function': 'open_application', 'args': {'app_name': target_app}, 'result': action_res}], 'error': False, 'fast_path': True}

        # No fast-path match
        return None

    def process_message(self, user_message: str, language: str = "en") -> dict:
        """
        Process a user message with a zero-delay fast-path for system tasks,
        and fall back to Groq Llama LLM for general conversation.
        """
        if not user_message or not user_message.strip():
            return {'response': 'Please say or type something.', 'actions': [], 'error': True}

        # Detect effective language
        effective_lang = self._detect_language(user_message, language)

        # ─── FAST PATH: ZERO-DELAY INSTANT EXECUTION (<5ms) ───
        fast_result = self._fast_path(user_message, effective_lang)
        if fast_result is not None:
            # Save to conversation memory
            self.memory.add_message('user', user_message)
            self.memory.add_message('assistant', fast_result['response'])
            return fast_result

        # Reload Groq API Key dynamically if updated
        import config
        api_key = config.GROQ_API_KEY

        # ─── CONVERSATIONAL AI VIA GROQ LLM ───
        if not api_key or api_key == "your_groq_api_key_here":
            # Friendly fallback if user hasn't set their free Groq key yet
            self.memory.add_message('user', user_message)
            if effective_lang == "ur":
                fallback = ("میں سسٹم کنٹرول، ایپس اوپننگ، گانے اور یوٹیوب فوری چلا سکتا ہوں! "
                            "مکمل تفصیلی گفتگو کے لیے برائے مہربانی سیٹنگز میں جا کر اپنی مفت Groq API کی داخل کریں۔")
            elif effective_lang == "hi":
                fallback = ("मैं सिस्टम कमांड्स, ऐप्स, गाने और यूट्यूब तुरंत खोल सकता हूँ! "
                            "फुल चैट करने के लिए कृपया सेटिंग्स में जाकर अपनी फ्री Groq API Key दर्ज करें।")
            else:
                fallback = ("Max is ready! I can instantly open apps (YouTube, WhatsApp, Spotify), control volume, and search. "
                            "To enable full conversational AI, please enter your free Groq API key in the top Settings panel.")
            
            self.memory.add_message('assistant', fallback)
            return {'response': fallback, 'actions': [], 'error': False}

        # Add user message to memory
        self.memory.add_message('user', user_message)

        # Build conversation context
        history = self.memory.get_recent_messages(limit=CONTEXT_WINDOW)
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            *history
        ]

        # Headers for Groq API
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # First API call - may include tool calls
        payload = {
            "model": config.MODEL_NAME,
            "messages": messages,
            "tools": self.tools,
            "tool_choice": "auto",
            "temperature": 0.7,
            "max_tokens": 1024
        }

        try:
            response = requests.post(
                GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            result = response.json()

        except requests.exceptions.Timeout:
            return {
                'response': 'Response timed out. Please try again.',
                'actions': [],
                'error': True
            }
        except requests.exceptions.ConnectionError:
            return {
                'response': 'Network error. Please check your internet connection.',
                'actions': [],
                'error': True
            }
        except requests.exceptions.HTTPError as e:
            error_msg = f"API error: {e.response.status_code}"
            if e.response.status_code == 401:
                error_msg = "Invalid API key. Please check your Groq API key in .env file."
            elif e.response.status_code == 429:
                error_msg = "Rate limit hit. Please wait a moment and try again."
            return {
                'response': error_msg,
                'actions': [],
                'error': True
            }

        # Process the response
        choice = result.get('choices', [{}])[0]
        message = choice.get('message', {})
        actions_taken = []

        # Check if LLM wants to call functions
        if message.get('tool_calls'):
            # Execute each tool call
            tool_results = []
            for tool_call in message['tool_calls']:
                func_name = tool_call['function']['name']
                try:
                    args = json.loads(tool_call['function']['arguments'])
                except json.JSONDecodeError:
                    args = {}

                result_data = self._execute_function(func_name, args)
                tool_results.append(result_data)
                actions_taken.append({
                    'function': func_name,
                    'args': args,
                    'result': result_data
                })

            # Build follow-up messages with tool results
            messages.append(message)
            for i, tool_call in enumerate(message['tool_calls']):
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call['id'],
                    "content": json.dumps(tool_results[i])
                })

            # Second API call - get natural language response after tool execution
            followup_payload = {
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 512
            }

            try:
                followup_response = requests.post(
                    GROQ_API_URL,
                    headers=headers,
                    json=followup_payload,
                    timeout=15
                )
                followup_response.raise_for_status()
                followup_result = followup_response.json()
                final_response = followup_result['choices'][0]['message']['content']
            except Exception:
                # If follow-up fails, construct response from tool results
                successes = [a['result']['message'] for a in actions_taken if a['result'].get('success')]
                final_response = "Done! " + ", ".join(successes) if successes else "Action completed."
        else:
            final_response = message.get('content', 'Sorry, I couldn\'t process that.')

        # Save assistant response to memory
        self.memory.add_message('assistant', final_response)

        return {
            'response': final_response,
            'actions': actions_taken,
            'error': False
        }

    def clear_memory(self):
        """Clear conversation memory."""
        self.memory.clear()
        return {'message': 'Memory cleared successfully.'}

    def get_memory_info(self):
        """Get memory statistics."""
        return {
            'summary': self.memory.get_summary(),
            'message_count': len(self.memory.messages)
        }
