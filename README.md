# 📱 MarketMate WhatsApp Bot

> A production-ready AI-powered WhatsApp customer support bot built with **FastAPI**, **WhatsApp Cloud API (Meta)**, and **Ollama (offline LLM)**. Fully multilingual — detects and responds in the customer's language automatically.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![WhatsApp](https://img.shields.io/badge/WhatsApp_Cloud_API-Meta-25D366?style=flat-square&logo=whatsapp&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-LLaMA3-black?style=flat-square)
![Render](https://img.shields.io/badge/Deploy-Render.com-46E3B7?style=flat-square)

---

## ✨ Features

- 📱 **WhatsApp integration** — Real customers message your WhatsApp Business number
- 🌍 **Fully multilingual** — Detects and responds in Turkish, English, German, Arabic, and more
- 🧠 **Offline AI (Ollama)** — LLaMA3 runs locally, no API costs, full data privacy
- 👤 **Customer info collection** — AI collects name, order number, and issue description
- 📦 **Order tracking** — Query MM-XXXX order status via chat
- 🏷️ **Product & campaign info** — Full catalog and active discounts
- 💬 **Conversation memory** — Context-aware replies per phone number
- 🚀 **Render.com ready** — One-click deploy with `render.yaml`

---

## 🏗 Architecture

```
Customer WhatsApp
        │
        ▼
Meta WhatsApp Cloud API
        │  POST /webhook
        ▼
FastAPI (Render.com)
        │
        ├─ Parse message
        ├─ Build conversation history
        │
        ▼
Ollama (LLaMA3) ◄── local or remote
        │
        ▼
AI response → send back via WhatsApp API
```

---

## 🚀 Setup Guide

### 1. Meta Developer Setup

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create an App → **Business** type
3. Add **WhatsApp** product
4. Get your:
   - `WHATSAPP_TOKEN` (permanent token)
   - `WHATSAPP_PHONE_ID` (phone number ID)
5. Set webhook URL to: `https://your-app.onrender.com/webhook`
6. Set verify token to: `marketmate_verify_2025`
7. Subscribe to: `messages`

### 2. Install Ollama locally (for development)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull LLaMA3
ollama pull llama3

# Start Ollama
ollama serve
```

### 3. Clone & run locally

```bash
git clone https://github.com/yourusername/marketmate-whatsapp.git
cd marketmate-whatsapp

pip install -r requirements.txt
cp .env.example .env
# Fill in your tokens in .env

uvicorn main:app --reload --port 8000
```

### 4. Test locally with ngrok

```bash
# Install ngrok: https://ngrok.com
ngrok http 8000
# Copy the https URL → paste as webhook in Meta dashboard
```

### 5. Deploy to Render.com

1. Push to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your repo
4. Add environment variables in Render dashboard:
   - `WHATSAPP_TOKEN`
   - `WHATSAPP_PHONE_ID`
5. Deploy — your webhook URL will be `https://your-app.onrender.com/webhook`

---

## 📁 Project Structure

```
marketmate-whatsapp/
├── main.py            # FastAPI app, webhook handler, Ollama client
├── requirements.txt   # Dependencies
├── render.yaml        # Render.com deploy config
├── .env.example       # Environment variables template
└── README.md
```

---

## 🌍 Multilingual Demo

| Customer writes | Bot responds in |
|---|---|
| "Siparişim nerede?" | 🇹🇷 Turkish |
| "Where is my order?" | 🇬🇧 English |
| "Wo ist meine Bestellung?" | 🇩🇪 German |
| "أين طلبي؟" | 🇸🇦 Arabic |

---

## 🛠 Tech Stack

| Component | Technology |
|---|---|
| Webhook server | Python, FastAPI |
| WhatsApp API | Meta WhatsApp Cloud API v19 |
| AI Model | LLaMA3 via Ollama (offline) |
| Deployment | Render.com |
| HTTP client | httpx (async) |

---

## 🔧 Customization for Your Business

Replace mock data in `main.py` with your real data source:

```python
# Connect to your database
ORDERS   = your_db.get_orders()
PRODUCTS = your_db.get_products()
CAMPAIGNS = your_db.get_campaigns()
```

For enterprise use, replace in-memory `conversations` dict with Redis:

```python
import redis
r = redis.Redis(host='localhost', port=6379)
```

---

## 📄 License

MIT

---

Built by [Murat Yesilyurt] — available for WhatsApp bot & AI integration projects on [Upwork](https://www.upwork.com/freelancers/~01e45f433b6bc60914).
