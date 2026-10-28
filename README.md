# 🇮🇳 Karan AI Assistant

> **Karan** is an intelligent tactical AI assistant built with an authentic Indian visual aesthetic (Ashoka Chakra / Mandala core, Kesari gold palette) and Indian conversational tone.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Manalii-12/Karan)

---

## 🚀 Features

- **Holographic Indian UI**: 24-ray rotating Ashoka Chakra mandala core with Kesari Gold (`#ff9933`) and Ashoka Navy (`#080c1a`) theme.
- **Voice Interaction**:
  - **Voice Input**: Web Speech Recognition in Indian English (`en-IN`).
  - **Voice Output**: Speech synthesis with native Indian pronunciation (`Microsoft Ravi` / `en-IN`).
- **Tactical Actions**:
  - ▶ Open YouTube
  - 🏏 Live Cricket Scores
  - ⛅ Weather Forecasts
  - 🔍 Google Search
  - ✉ Gmail Inbox & Email Composer
- **Multi-LLM Cloud Intelligence**:
  - Works with **Groq** (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) for ultra-fast, free inference.
  - Works with **OpenAI** (`gpt-4o-mini`).
  - Works with **Local Ollama** (`qwen2.5:0.5b`) for offline local use.
  - Intelligent built-in rule and knowledge engine fallback.

---

## 🌐 Deploy to Vercel (1-Click)

1. Import this repository in [Vercel](https://vercel.com/new).
2. Set Project Name to something like `karan-voice-assistant` (or your choice).
3. (Optional) Add your environment variables:
   - `GROQ_API_KEY` (Free from [console.groq.com](https://console.groq.com)) OR
   - `OPENAI_API_KEY`
4. Click **Deploy**!

Your assistant will be live at:
`https://karan-voice-assistant.vercel.app` (or your chosen Vercel domain).

---

## 💻 Local Development

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   python server.py
   ```
3. Open `http://localhost:5000` in your browser.
