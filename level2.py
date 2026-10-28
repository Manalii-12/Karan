from openai import OpenAI
import speech_recognition as sr
import pyttsx3
import webbrowser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle, os, json, threading, time, base64, sys
from email.mime.text import MIMEText

# Ensure utf-8 output encoding on Windows console
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

# === PATH SETUP ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_JSON = os.path.join(BASE_DIR, 'credentials.json')
if not os.path.exists(CREDENTIALS_JSON) and os.path.exists(os.path.join(BASE_DIR, 'credentials.json.json')):
    CREDENTIALS_JSON = os.path.join(BASE_DIR, 'credentials.json.json')
TOKEN_PICKLE = os.path.join(BASE_DIR, 'token_gmail.pickle')

# === OPENAI & LOCAL LLM SETUP ===
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
client = None
if OPENAI_API_KEY and OPENAI_API_KEY != "YOUR_OPENAI_API_KEY":
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        print(f"[OpenAI] init notice: {e}")
recognizer = sr.Recognizer()

# === GMAIL SETUP ===
SCOPES_GMAIL = ['https://www.googleapis.com/auth/gmail.modify']
last_email_id = None
gmail_thread_active = False

# === PRESAVED CONTACTS ===
CONTACTS = {
    "boss": "riya123@gmail.com",
    "rohan": "rohan.work@gmail.com",
    "priya": "priya.mehta@outlook.com",
    "manali": "manali@example.com"
}

# === GMAIL AUTH ===
def gmail_service(interactive=False):
    creds = None
    try:
        if os.path.exists(TOKEN_PICKLE):
            try:
                with open(TOKEN_PICKLE, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"[Gmail] Error reading {TOKEN_PICKLE}: {e}")
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    with open(TOKEN_PICKLE, 'wb') as token:
                        pickle.dump(creds, token)
                except Exception as e:
                    print(f"[Gmail] Token refresh notice: {e}")
                    creds = None

            if not creds or not creds.valid:
                if interactive and os.path.exists(CREDENTIALS_JSON):
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_JSON, SCOPES_GMAIL)
                        creds = flow.run_local_server(port=0)
                        with open(TOKEN_PICKLE, 'wb') as token:
                            pickle.dump(creds, token)
                    except Exception as e:
                        print(f"[Gmail] Auth flow error: {e}")
                        return None
                else:
                    if not os.path.exists(CREDENTIALS_JSON):
                        print(f"[Gmail] Credentials file not found at {CREDENTIALS_JSON}.")
                    else:
                        print("[Gmail] Interactive login required to refresh expired token. Gmail offline for now.")
                    return None
        return build('gmail', 'v1', credentials=creds)
    except Exception as e:
        print(f"[Gmail] Initialization notice: {e}")
        return None


gmail_service_instance = gmail_service(interactive=False)

# === INDIAN TTS SETUP (Microsoft Ravi - English India) ===
def get_indian_voice():
    try:
        import win32com.client
        cat = win32com.client.Dispatch('SAPI.SpObjectTokenCategory')
        cat.SetId(r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech_OneCore\Voices', False)
        for t in cat.EnumerateTokens():
            desc = t.GetDescription().lower()
            if 'ravi' in desc or 'india' in desc or 'en-in' in desc:
                spk = win32com.client.Dispatch('SAPI.SpVoice')
                spk.Voice = t
                spk.Rate = 1
                return spk
    except Exception as e:
        print(f"[Voice] Indian voice init notice: {e}")
    return None

indian_speaker = get_indian_voice()

def speak(text):
    global indian_speaker
    clean = text.replace("✅", "").replace("⚠️", "").replace("🤖", "").replace("💬", "").replace("✉️", "")
    if indian_speaker is not None:
        try:
            indian_speaker.Speak(clean)
            return
        except Exception as e:
            print(f"[Voice] SAPI error: {e}")
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.say(clean)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[Voice] Speech output error: {e}")


def speak_async(text):
    """Speaks text in a background thread so actions and web requests are not delayed."""
    threading.Thread(target=speak, args=(text,), daemon=True).start()


def get_best_ollama_model():
    try:
        import ollama
        models = [m.model for m in ollama.list().models]
        # Prefer fast lightweight models on CPU if downloaded
        for candidate in ['qwen2.5:0.5b', 'qwen2.5:1.5b', 'phi3:mini', 'gemma3:latest']:
            if any(candidate in m for m in models):
                return candidate
        if models:
            return models[0]
        return 'gemma3:latest'
    except Exception:
        return 'gemma3:latest'


def ask_gpt(prompt):
    system_instruction = (
        "You are Karan, a smart, polite, and respectful personal AI assistant. "
        "You speak fluent English with a warm and courteous Indian tone (e.g. 'Namaste Captain!'). "
        "Always respond in clear English. Keep your answers direct, helpful, and concise (1-2 sentences max). "
        "Proudly identify yourself as Karan."
    )

    if client is not None:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=70
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[OpenAI] notice: {e}. Falling back to Ollama...")

    try:
        import ollama
        active_model = get_best_ollama_model()
        res = ollama.chat(
            model=active_model,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            options={
                "num_predict": 50,
                "num_thread": 4,
                "temperature": 0.6,
                "top_p": 0.9
            }
        )
        return res['message']['content'].strip()
    except Exception as e:
        print(f"[Ollama] error: {e}")
        return "I am Karan, your AI assistant. I'm standing by to help."


# === GMAIL SEND ===
def send_email(to_email, subject, body):
    try:
        if not ("@" in to_email and "." in to_email):
            speak("The email address looks invalid.")
            print(f"⚠️ Invalid email: {to_email}")
            return

        message = MIMEText(body)
        message["to"] = to_email
        message["subject"] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        service = gmail_service_instance
        if not service:
            speak("Gmail service is not connected. Please check your credentials.")
            print("⚠️ Gmail service is not connected.")
            return
        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()

        speak(f"Email sent successfully to {to_email}.")
        print(f"✅ Email sent successfully to {to_email}")
    except Exception as e:
        import traceback
        print("⚠️ Error sending email:", e)
        traceback.print_exc()
        speak("Sorry, I couldn’t send the email.")


# === COMPOSE EMAIL ===
def compose_email():
    try:
        speak("What’s the subject of your email?")
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            subject_audio = recognizer.listen(source)
        subject = recognizer.recognize_google(subject_audio)
        speak(f"Got it. The subject is {subject}. Now, what should I write about?")

        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            body_audio = recognizer.listen(source)
        topic = recognizer.recognize_google(body_audio)

        speak("Let me draft your email.")
        body = ask_gpt(
            f"Write a professional email about: {topic}. "
            "End with 'Best regards, Manali Patkar'."
        )

        speak("Here’s your draft.")
        print("\n✉️ Draft Email:\n", body)
        speak(body)

        speak("Should I send this email?")
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            confirm_audio = recognizer.listen(source)
        confirm = recognizer.recognize_google(confirm_audio).lower()

        if "yes" in confirm or "send" in confirm:
            speak("Who should I send it to? Please say the name of the person or contact.")
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                name_audio = recognizer.listen(source)
            name_spoken = recognizer.recognize_google(name_audio).lower().strip()
            print(f"🎧 Heard name: {name_spoken}")

            if name_spoken in CONTACTS:
                to_email = CONTACTS[name_spoken]
                speak(f"Found contact {name_spoken}. Sending to {to_email}.")
            else:
                speak("Sorry, I couldn’t find that contact. Please type the email manually.")
                to_email = input("📩 Type recipient email address: ").strip()

            send_email(to_email, subject, body)
        else:
            speak("Okay, I’ll save it as a draft for now.")

    except Exception as e:
        import traceback
        print("⚠️ Compose error:", e)
        traceback.print_exc()
        speak("Sorry, something went wrong while composing your email.")


# === GMAIL MONITOR (with read feature) ===
def check_new_email():
    global last_email_id
    try:
        service = gmail_service_instance
        if not service:
            return
        results = service.users().messages().list(
            userId="me", labelIds=["INBOX"], q="is:unread"
        ).execute()
        messages = results.get("messages", [])
        if messages:
            new_message = messages[0]
            msg_id = new_message["id"]
            if msg_id != last_email_id:
                last_email_id = msg_id
                speak("Hey Manali, you have a new email!")
                message = service.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()
                headers = message["payload"]["headers"]
                from_ = [i["value"] for i in headers if i["name"] == "From"][0]
                subject = [i["value"] for i in headers if i["name"] == "Subject"][0]
                speak(f"From: {from_}. Subject: {subject}.")
                print(f"📧 From: {from_}\nSubject: {subject}")

                speak("Would you like me to read it?")
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source)
                    try:
                        audio = recognizer.listen(source, phrase_time_limit=4)
                        answer = recognizer.recognize_google(audio).lower()
                    except:
                        answer = "no"

                if "yes" in answer or "read" in answer:
                    # Extract and summarize body text
                    body_data = ""
                    parts = message["payload"].get("parts", [])
                    for part in parts:
                        if part["mimeType"] == "text/plain":
                            body_data = base64.urlsafe_b64decode(
                                part["body"]["data"]
                            ).decode("utf-8")
                            break
                    if body_data:
                        summary = ask_gpt(f"Summarize this email briefly:\n{body_data}")
                        speak("Here’s a short summary of the email.")
                        speak(summary)
                        print("\n📜 Summary:", summary)
                    else:
                        speak("Sorry, I couldn’t read the email content.")
                else:
                    speak("Okay, not reading it.")
    except Exception as e:
        print("⚠️ Gmail check error:", e)


def start_gmail_thread():
    global gmail_thread_active
    gmail_thread_active = True

    def gmail_loop():
        while gmail_thread_active:
            check_new_email()
            time.sleep(60)

    thread = threading.Thread(target=gmail_loop, daemon=True)
    thread.start()


# === GMAIL CHECK UNREAD EMAILS ===
def get_unread_emails(limit=5):
    """Checks and returns unread emails from Gmail."""
    global gmail_service_instance
    service = gmail_service_instance
    if not service:
        return (
            "Captain, Gmail is not connected because the Google OAuth token has expired. "
            "Please click the 'Connect Gmail' button or visit http://localhost:5000/auth/gmail to sign in."
        )
    try:
        results = service.users().messages().list(
            userId="me", labelIds=["INBOX"], q="is:unread", maxResults=limit
        ).execute()
        messages = results.get("messages", [])
        if not messages:
            return "Captain, your inbox is completely clear. You have no unread emails."

        email_list = []
        for idx, m in enumerate(messages, 1):
            msg = service.users().messages().get(
                userId="me", id=m["id"], format="metadata", metadataHeaders=["From", "Subject"]
            ).execute()
            headers = msg.get("payload", {}).get("headers", [])
            sender = "Unknown"
            subject = "(No Subject)"
            for h in headers:
                if h["name"].lower() == "from":
                    sender = h["value"]
                elif h["name"].lower() == "subject":
                    subject = h["value"]
            if "<" in sender:
                sender = sender.split("<")[0].strip().replace('"', '')
            email_list.append(f"{idx}. From {sender}: '{subject}'")

        count = len(messages)
        return f"Captain, you have {count} unread email{'s' if count > 1 else ''}:\n" + "\n".join(email_list)
    except Exception as e:
        print(f"[Gmail] Error checking emails: {e}")
        return f"Captain, I encountered an error checking your emails: {e}. Please re-authenticate at http://localhost:5000/auth/gmail."


# === ACTION HANDLER ===
def handle_actions(normalized):
    if any(k in normalized for k in ["namaste", "how are you", "kaise ho", "pranam"]):
        reply = "Namaste Captain! I am doing very well. How may I assist you today?"
        speak_async(reply)
        return {"reply": reply}

    elif any(k in normalized for k in ["cricket", "match", "score", "scores", "ipl", "cricbuzz"]):
        reply = "Opening live cricket scores for you, Captain."
        url = "https://www.cricbuzz.com"
        speak_async(reply)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return {"reply": reply, "url": url}

    elif any(k in normalized for k in ["weather", "mausam", "forecast", "temperature"]):
        reply = "Checking the weather forecast for you, Captain."
        url = "https://www.google.com/search?q=weather+today"
        speak_async(reply)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return {"reply": reply, "url": url}

    elif any(k in normalized for k in ["open youtube", "youtube", "yt", "play youtube", "launch youtube"]):
        reply = "Opening YouTube for you now, Captain."
        url = "https://www.youtube.com"
        speak_async(reply)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return {"reply": reply, "url": url}

    elif any(k in normalized for k in ["open google", "google", "search google", "launch google"]):
        reply = "Opening Google search for you, Captain."
        url = "https://www.google.com"
        speak_async(reply)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return {"reply": reply, "url": url}

    elif any(k in normalized for k in [
        "check email", "check my email", "check emails", "unread email", "unread emails",
        "any email", "any emails", "read email", "read emails", "my email", "my emails",
        "check mail", "check mails", "get emails", "show emails", "emails"
    ]):
        reply = get_unread_emails()
        speak_async("Checking your emails now, Captain.")
        if gmail_service_instance is None:
            return {"reply": reply, "url": "/auth/gmail", "auth_required": True}
        return {"reply": reply, "url": "https://mail.google.com", "auth_required": False}

    elif any(k in normalized for k in ["open gmail", "launch gmail", "gmail", "inbox"]):
        reply = "Opening your Gmail inbox now, Captain."
        url = "https://mail.google.com"
        speak_async(reply)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return {"reply": reply, "url": url}

    elif any(k in normalized for k in ["compose", "write an email", "send email", "new email", "draft email"]):
        url = "https://mail.google.com/mail/?view=cm&fs=1"
        reply = "Opening Gmail composer for you, Captain."
        speak_async(reply)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return {"reply": reply, "url": url}

    return None


# === MAIN LOOP ===
def main():
    global gmail_thread_active
    speak("Namaste Captain, Karan assistant ready. Say 'Hey Karan' to activate.")

    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("🎤 Say 'Hey Karan' to activate...")
                try:
                    audio = recognizer.listen(source, phrase_time_limit=5, timeout=5)
                    wake_text = recognizer.recognize_google(audio)
                except (sr.WaitTimeoutError, sr.UnknownValueError, OverflowError):
                    continue

            wake_lower = wake_text.lower()
            if any(kw in wake_lower for kw in ["hey karan", "hi karan", "hello karan", "karan", "hey karna", "karna", "namaste karan"]):
                speak("Namaste captain, Karan online and listening.")
                start_gmail_thread()
                ACTIVE_TIMEOUT = 600  # 10 minutes
                active_start_time = time.time()

                while True:
                    if time.time() - active_start_time > ACTIVE_TIMEOUT:
                        speak("Going back to sleep. Say 'Hey Karan' to wake me again.")
                        break

                    with sr.Microphone() as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        try:
                            audio = recognizer.listen(source, phrase_time_limit=5, timeout=5)
                            command = recognizer.recognize_google(audio)
                            active_start_time = time.time()
                        except (sr.WaitTimeoutError, sr.UnknownValueError, OverflowError):
                            continue

                    normalized = command.lower()

                    if handle_actions(normalized):
                        continue

                    if any(phrase in normalized for phrase in ["over and out", "exit", "shutdown", "alvida", "goodbye"]):
                        speak("Goodbye, Captain. Have a wonderful time ahead.")
                        gmail_thread_active = False
                        exit(0)

                    print("🤖 Thinking...")
                    answer = ask_gpt(command)
                    print(f"💬 Karan: {answer}")
                    speak(answer)

        except Exception as e:
            print("⚠️ Error in activation:", e)


if __name__ == "__main__":
    main()
