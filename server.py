import os
import sys
import pickle
from flask import Flask, request, jsonify, send_file

# Reconfigure console output to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import level2
from level2 import ask_gpt, handle_actions, client, get_best_ollama_model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "html.html")

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/", methods=["GET"])
def index():
    if os.path.exists(HTML_PATH):
        return send_file(HTML_PATH)
    return "<h3>Karan Assistant Server Online</h3><p>html.html not found.</p>", 200

@app.route("/status", methods=["GET"])
def status():
    if client is not None:
        engine = "OpenAI (gpt-4o-mini)"
        model_name = "gpt-4o-mini"
    else:
        active = get_best_ollama_model()
        engine = f"Ollama Local ({active})"
        model_name = active
    return jsonify({
        "status": "online",
        "assistant": "Karan",
        "engine": engine,
        "model": model_name,
        "gmail_connected": level2.gmail_service_instance is not None
    })

@app.route("/auth/gmail", methods=["GET"])
def auth_gmail():
    """Runs the Google OAuth flow to grant Gmail access and generate fresh token."""
    if not os.path.exists(level2.CREDENTIALS_JSON):
        return f"<h3>Gmail credentials file not found at {level2.CREDENTIALS_JSON}</h3>", 400
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        flow = InstalledAppFlow.from_client_secrets_file(
            level2.CREDENTIALS_JSON, level2.SCOPES_GMAIL
        )
        creds = flow.run_local_server(port=0)
        with open(level2.TOKEN_PICKLE, 'wb') as token:
            pickle.dump(creds, token)
        level2.gmail_service_instance = build('gmail', 'v1', credentials=creds)
        print("[Gmail] Re-authentication successful! Gmail service instance is now active.")
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Gmail Connected</title></head>
        <body style="background:#080c1a;color:#fcf6ea;font-family:sans-serif;text-align:center;padding:60px;">
            <h1 style="color:#00e676;">&#9989; Gmail Connected Successfully!</h1>
            <p style="font-size:18px;color:#9cb1c9;margin-top:10px;">Karan can now check, read, and compose your emails.</p>
            <p style="margin-top:30px;">
                <a href="/" style="display:inline-block;padding:12px 28px;background:#ff9933;color:#080c1a;font-weight:bold;text-decoration:none;border-radius:8px;box-shadow:0 0 15px rgba(255,153,51,0.5);">
                    Return to Karan Dashboard &rarr;
                </a>
            </p>
            <script>setTimeout(() => { window.location.href = '/'; }, 3500);</script>
        </body>
        </html>
        """
    except Exception as e:
        print(f"[Gmail Auth Error] {e}")
        return f"<body style='background:#080c1a;color:#ff3366;font-family:sans-serif;padding:40px;'><h2>Authentication Failed:</h2><p>{e}</p><a href='/' style='color:#ff9933;'>Return to Home</a></body>", 500

@app.route("/friday", methods=["POST", "OPTIONS"])
@app.route("/karan", methods=["POST", "OPTIONS"])
def handle_chat_message():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()
    print(f"[Karan Server] message received: {user_message}")

    if not user_message:
        return jsonify({"reply": "I am listening Captain, please enter a command or question."})

    # First check smart actions (e.g. open youtube, open google, check emails, weather, cricket)
    try:
        action_res = handle_actions(user_message.lower())
        if action_res is not None:
            return jsonify(action_res)
    except Exception as e:
        print(f"[Actions Error] {e}")

    # Otherwise query the fast LLM
    answer = ask_gpt(user_message)
    return jsonify({"reply": answer})

if __name__ == "__main__":
    print("[Server] Starting Karan assistant server on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
