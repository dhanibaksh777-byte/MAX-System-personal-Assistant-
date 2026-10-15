"""
Max Assistant - Flask API Server
Provides REST API endpoints for the frontend.
"""
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from assistant_core import AssistantCore
import os

# Initialize Flask app
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static')
)
CORS(app)

# Initialize assistant
assistant = AssistantCore()


@app.route('/')
def index():
    """Serve the main UI."""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Process a chat message."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400

    user_message = data['message'].strip()
    language = data.get('language', 'en')

    if not user_message:
        return jsonify({'error': 'Empty message'}), 400

    # Process the message
    result = assistant.process_message(user_message, language)
    return jsonify(result)


@app.route('/api/memory/clear', methods=['POST'])
def clear_memory():
    """Clear conversation memory."""
    result = assistant.clear_memory()
    return jsonify(result)


@app.route('/api/memory/info', methods=['GET'])
def memory_info():
    """Get memory information."""
    result = assistant.get_memory_info()
    return jsonify(result)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    import config
    has_key = bool(config.GROQ_API_KEY and config.GROQ_API_KEY != "your_groq_api_key_here")
    return jsonify({
        'status': 'online',
        'assistant': 'Max',
        'api_configured': has_key,
        'model': config.MODEL_NAME
    })


@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    """Get or update application settings."""
    import config
    env_path = os.path.join(os.path.dirname(__file__), '.env')

    if request.method == 'GET':
        has_key = bool(config.GROQ_API_KEY and config.GROQ_API_KEY != "your_groq_api_key_here")
        # Mask the key for security: gsk_...1234
        masked = ""
        if has_key:
            k = config.GROQ_API_KEY
            masked = (k[:4] + "..." + k[-4:]) if len(k) > 8 else "***"
        return jsonify({
            'api_configured': has_key,
            'masked_key': masked,
            'model': config.MODEL_NAME
        })

    data = request.get_json() or {}
    new_key = data.get('api_key', '').strip()
    new_model = data.get('model', '').strip()

    # Read current .env
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

    # Update values
    updated_lines = []
    key_found = False
    model_found = False

    for line in lines:
        if line.strip().startswith('GROQ_API_KEY='):
            if new_key:
                updated_lines.append(f'GROQ_API_KEY={new_key}\n')
            else:
                updated_lines.append(line)
            key_found = True
        elif line.strip().startswith('MODEL_NAME='):
            if new_model:
                updated_lines.append(f'MODEL_NAME={new_model}\n')
            else:
                updated_lines.append(line)
            model_found = True
        else:
            updated_lines.append(line)

    if not key_found and new_key:
        updated_lines.append(f'GROQ_API_KEY={new_key}\n')
    if not model_found and new_model:
        updated_lines.append(f'MODEL_NAME={new_model}\n')

    # Save to .env
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)

    # Reload in assistant
    assistant.reload_config()

    return jsonify({
        'success': True,
        'message': 'Settings saved successfully!',
        'api_configured': bool(config.GROQ_API_KEY and config.GROQ_API_KEY != "your_groq_api_key_here")
    })


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory(app.static_folder, filename)
