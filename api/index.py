import os
import sys
import json
import requests
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_PATH = os.path.join(BASE_DIR, "public", "index.html")
if not os.path.exists(HTML_PATH):
    HTML_PATH = os.path.join(BASE_DIR, "html.html")
if not os.path.exists(HTML_PATH):
    HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

# LLM Providers Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
IS_VERCEL = bool(os.environ.get("VERCEL"))

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@app.route("/status", methods=["GET", "OPTIONS"])
@app.route("/api/status", methods=["GET", "OPTIONS"])
def status():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    if GROQ_API_KEY:
        engine = "Groq Cloud (Llama 3.3)"
        model_name = "llama-3.3-70b-versatile"
    elif OPENAI_API_KEY:
        engine = "OpenAI Cloud (gpt-4o-mini)"
        model_name = "gpt-4o-mini"
    elif GEMINI_API_KEY:
        engine = "Google Gemini (gemini-1.5-flash)"
        model_name = "gemini-1.5-flash"
    elif not IS_VERCEL:
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=0.5)
            if r.status_code == 200:
                engine = "Ollama Local (qwen2.5:0.5b)"
                model_name = "qwen2.5:0.5b"
            else:
                engine = "Karan Core Engine"
                model_name = "karan-smart-core"
        except Exception:
            engine = "Karan Cloud Engine"
            model_name = "karan-v1-cloud"
    else:
        engine = "Karan Cloud Engine (Vercel)"
        model_name = "karan-cloud-native"

    return jsonify({
        "status": "online",
        "assistant": "Karan",
        "engine": engine,
        "model": model_name,
        "platform": "Vercel Serverless" if IS_VERCEL else "Local / Cloud",
        "gmail_connected": False
    })

def handle_actions(normalized):
    """Executes predefined smart actions for instant, reliable responses."""
    # Greetings & Salutations (including 'hii', 'hello', 'hey', 'namaste')
    if any(k in normalized for k in ["namaste", "pranam", "how are you", "kaise ho", "hello", "hi", "hii", "heyy", "hey", "namaskar", "karan", "good morning", "good evening", "good afternoon"]):
        return {
            "reply": "Namaste Captain! I am Karan, your personal AI assistant. All systems are operational. How may I assist you today?"
        }

    elif any(k in normalized for k in ["who are you", "what is your name", "identify yourself", "tell me about yourself"]):
        return {
            "reply": "I am Karan, an intelligent AI voice assistant inspired by modern Indian tactical interfaces. I can help you with web browsing, weather forecasts, live cricket scores, email tasks, and answering questions."
        }

    elif any(k in normalized for k in ["open youtube", "youtube", "yt", "play youtube", "launch youtube"]):
        return {
            "reply": "Opening YouTube for you now, Captain.",
            "url": "https://www.youtube.com"
        }

    elif any(k in normalized for k in ["cricket", "match", "score", "scores", "ipl", "cricbuzz"]):
        return {
            "reply": "Opening live cricket scores for you, Captain.",
            "url": "https://www.cricbuzz.com"
        }

    elif any(k in normalized for k in ["weather", "mausam", "forecast", "temperature"]):
        return {
            "reply": "Checking the latest weather forecast for you, Captain.",
            "url": "https://www.google.com/search?q=weather+today"
        }

    elif any(k in normalized for k in ["open google", "google", "search google"]):
        return {
            "reply": "Opening Google search for you, Captain.",
            "url": "https://www.google.com"
        }

    elif any(k in normalized for k in ["open gmail", "gmail", "inbox"]):
        return {
            "reply": "Opening your Gmail inbox now, Captain.",
            "url": "https://mail.google.com"
        }

    elif any(k in normalized for k in ["compose", "write an email", "send email", "new email", "draft email"]):
        return {
            "reply": "Opening Gmail composer for you, Captain.",
            "url": "https://mail.google.com/mail/?view=cm&fs=1"
        }

    elif any(k in normalized for k in ["check email", "check my email", "check emails", "unread email", "unread emails", "my emails"]):
        return {
            "reply": "Captain, on the cloud deployment, Gmail requires your Google account login. Click below to open your Gmail inbox directly.",
            "url": "https://mail.google.com",
            "auth_required": False
        }

    return None

def ask_llm(prompt):
    """Queries available LLMs (Groq, OpenAI, Gemini, Ollama, or fallback engine)."""
    # 1. Try Groq (Ultra-fast, free tier)
    if GROQ_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are Karan, a helpful, polite Indian AI assistant. Answer in concise, respectful English with an Indian conversational tone ('Captain')."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[Groq Error] {e}")

    # 2. Try OpenAI
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are Karan, a helpful, polite Indian AI assistant. Answer in concise, respectful English with an Indian conversational tone ('Captain')."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"[OpenAI Error] {e}")

    # 3. Try Local Ollama if not running on Vercel
    if not IS_VERCEL:
        try:
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:0.5b",
                    "prompt": f"You are Karan, a helpful, polite AI assistant. Answer briefly in English to: {prompt}",
                    "stream": False,
                    "options": {"num_predict": 75}
                },
                timeout=2.0
            )
            if r.status_code == 200:
                return r.json().get("response", "").strip()
        except Exception:
            pass

    # 4. Built-in Smart Fallback Knowledge Engine
    p_lower = prompt.lower()
    if "time" in p_lower:
        from datetime import datetime
        return f"Captain, the current server time is {datetime.utcnow().strftime('%H:%M:%S UTC')}."
    elif "date" in p_lower or "day" in p_lower:
        from datetime import datetime
        return f"Captain, today's date is {datetime.utcnow().strftime('%A, %d %B %Y')}."
    elif "joke" in p_lower:
        return "Why do programmers prefer dark mode, Captain? Because light attracts bugs!"
    elif "quote" in p_lower or "motivation" in p_lower:
        return "Arise, awake, and stop not till the goal is reached. - Swami Vivekananda"
    elif "india" in p_lower:
        return "India is the world's largest democracy, celebrated for its rich cultural heritage, technological innovation, and vibrant diversity."

    return (
        f"Namaste Captain! I received your query: '{prompt}'. "
        "All cloud systems are operational. To enable deep generative intelligence on Vercel, "
        "you can add a free GROQ_API_KEY or OPENAI_API_KEY in your Vercel Project Environment Variables."
    )

# Universal Chat Route (handles /karan, /friday, /api/karan, and POST to /)
@app.route("/", methods=["GET", "POST", "OPTIONS"])
@app.route("/karan", methods=["GET", "POST", "OPTIONS"])
@app.route("/friday", methods=["GET", "POST", "OPTIONS"])
@app.route("/api", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/karan", methods=["GET", "POST", "OPTIONS"])
@app.route("/api/friday", methods=["GET", "POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    # Serve HTML page on GET requests to root
    if request.method == "GET" and (request.path == "/" or request.path == "/api"):
        if os.path.exists(HTML_PATH):
            return send_file(HTML_PATH)
        return "<h3>Karan AI Assistant Online</h3>", 200

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"reply": "I am listening Captain, please ask me a question or give a command."})

    action = handle_actions(message.lower())
    if action:
        return jsonify(action)

    answer = ask_llm(message)
    return jsonify({"reply": answer})

@app.route("/auth/gmail", methods=["GET"])
@app.route("/api/auth/gmail", methods=["GET"])
def auth_gmail():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Gmail Access</title></head>
    <body style="background:#080c1a;color:#fcf6ea;font-family:sans-serif;text-align:center;padding:50px;">
        <h2 style="color:#ff9933;">Gmail Integration</h2>
        <p style="color:#9cb1c9;font-size:16px;">To access your Gmail securely from the cloud, opening your Gmail inbox directly:</p>
        <p style="margin-top:25px;">
            <a href="https://mail.google.com" target="_blank" style="display:inline-block;padding:12px 24px;background:#ff9933;color:#080c1a;font-weight:bold;text-decoration:none;border-radius:8px;">Open Gmail Inbox &rarr;</a>
        </p>
    </body>
    </html>
    """, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
