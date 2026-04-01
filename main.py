"""
MarketMate WhatsApp Bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- WhatsApp Cloud API (Meta) webhook
- Ollama (offline, local LLM) for AI responses
- Fully multilingual: detects and responds in user's language
- Customer info collection: name, order number, issue description
- Deploy-ready for Render.com
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import httpx
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MarketMate WhatsApp Bot", version="1.0.0")

# ── Config (set these as environment variables) ───────────────────────────────
WHATSAPP_TOKEN      = os.environ.get("WHATSAPP_TOKEN", "")       # Meta permanent token
WHATSAPP_PHONE_ID   = os.environ.get("WHATSAPP_PHONE_ID", "")    # Phone number ID from Meta
VERIFY_TOKEN        = os.environ.get("VERIFY_TOKEN", "marketmate_verify_2025")
OLLAMA_URL          = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL        = os.environ.get("OLLAMA_MODEL", "llama3")

# ── Mock Data ─────────────────────────────────────────────────────────────────
ORDERS = {
    "MM-1042": {"status": "Delivered ✅", "date": "28 March 2025", "total": "₺342.50", "items": ["Tomatoes", "Yogurt", "Chicken Breast"]},
    "MM-1078": {"status": "On the way 🚚", "date": "31 March 2025", "total": "₺187.90", "items": ["Milk", "Cheese", "Pasta", "Rice"]},
    "MM-1091": {"status": "Being prepared 📦", "date": "1 April 2025", "total": "₺512.00", "items": ["Salmon Fillet", "Olive Oil", "Spinach"]},
}

PRODUCTS = {
    "produce":   ["Tomatoes ₺24.90 (20% OFF)", "Fuji Apple ₺34.90", "Banana ₺29.90 (15% OFF)", "Cucumber ₺12.90", "Spinach ₺18.50 (10% OFF)"],
    "dairy":     ["Whole Milk ₺28.90", "Yogurt ₺45.90 (25% OFF)", "White Cheese ₺89.90", "Butter ₺74.90 (10% OFF)"],
    "meat-fish": ["Chicken Breast ₺149.90 (15% OFF)", "Ground Beef ₺189.90", "Salmon Fillet ₺219.90 (20% OFF)"],
    "pantry":    ["Pasta ₺22.90", "Rice ₺89.90 (12% OFF)", "Olive Oil ₺189.90", "Flour ₺54.90 (8% OFF)"],
}

CAMPAIGNS = [
    "🥦 Up to 20% off Produce — Code: TAZE20 (until April 5)",
    "🥛 Dairy Sale — Code: SUT25 (until April 3)",
    "🥩 Weekend Meat Discount — Code: PROTEIN15 (until April 6)",
    "🎁 First Order 10% off — Code: WELCOME10 (no expiry)",
]

SYSTEM_PROMPT = """You are Mate, MarketMate's WhatsApp shopping assistant.
MarketMate delivers groceries in 2-4 hours.

=== CRITICAL LANGUAGE RULE ===
- Detect the language of EVERY user message
- ALWAYS respond in the EXACT same language
- Turkish → Turkish | English → English | Arabic → Arabic | German → German
- Never switch languages unless the user does

=== WHATSAPP FORMATTING ===
- Keep messages SHORT (max 3-4 lines per reply, WhatsApp is mobile)
- Use emojis naturally
- No markdown headers, no bullet lists with dashes — use emojis as bullets
- Bold with *asterisks* if needed

=== CUSTOMER SUPPORT FLOW ===
When user mentions a complaint, problem, missing item, late delivery, or any issue:
1. Ask warmly for their FULL NAME
2. Ask if they have an ORDER NUMBER (MM-XXXX)
   - If yes → look up in orders data, share status
   - If no → ask them to briefly describe the issue
3. Confirm info collected, say a human agent will contact them within 1 hour
4. Be empathetic and warm

=== STORE DATA ===
Products: """ + json.dumps(PRODUCTS, ensure_ascii=False) + """
Orders: """ + json.dumps(ORDERS, ensure_ascii=False) + """
Active campaigns: """ + json.dumps(CAMPAIGNS, ensure_ascii=False) + """

Delivery: Free over ₺200, otherwise ₺29.90. Min. order ₺150. Time: 2-4 hours.
Returns: Full refund within 24h for damaged/spoiled items.
Payment: Credit card, debit card, cash on delivery, digital wallets.

Keep responses short and mobile-friendly!
"""

# ── In-memory conversation store (use Redis in production) ───────────────────
conversations: dict[str, list] = {}

# ── Ollama AI call ────────────────────────────────────────────────────────────
async def ask_ollama(phone: str, user_message: str) -> str:
    if phone not in conversations:
        conversations[phone] = []

    conversations[phone].append({"role": "user", "content": user_message})

    # Keep last 10 messages to avoid context overflow
    history = conversations[phone][-10:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 300},
                },
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["message"]["content"].strip()
    except httpx.ConnectError:
        reply = "⚠️ AI service is temporarily offline. Please try again in a moment."
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        reply = "⚠️ Something went wrong. Please try again."

    conversations[phone].append({"role": "assistant", "content": reply})
    return reply

# ── Send WhatsApp message ─────────────────────────────────────────────────────
async def send_whatsapp_message(to: str, message: str):
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            logger.error(f"WhatsApp send error: {resp.text}")

# ── Webhook verification (GET) ────────────────────────────────────────────────
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    mode      = params.get("hub.mode")
    token     = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("✅ Webhook verified by Meta")
        return PlainTextResponse(challenge)

    raise HTTPException(status_code=403, detail="Verification failed")

# ── Webhook receive (POST) ────────────────────────────────────────────────────
@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()
    logger.info(f"Incoming: {json.dumps(body, indent=2)}")

    try:
        entry   = body["entry"][0]
        changes = entry["changes"][0]
        value   = changes["value"]

        # Ignore status updates
        if "statuses" in value:
            return {"status": "ok"}

        messages = value.get("messages", [])
        if not messages:
            return {"status": "ok"}

        msg      = messages[0]
        phone    = msg["from"]
        msg_type = msg.get("type", "")

        # Only handle text messages
        if msg_type != "text":
            await send_whatsapp_message(phone, "👋 I can only process text messages for now!")
            return {"status": "ok"}

        user_text = msg["text"]["body"].strip()
        logger.info(f"Message from {phone}: {user_text}")

        # Get AI reply
        reply = await ask_ollama(phone, user_text)

        # Send reply
        await send_whatsapp_message(phone, reply)

    except (KeyError, IndexError) as e:
        logger.error(f"Webhook parsing error: {e}")

    return {"status": "ok"}

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "MarketMate WhatsApp Bot is running 🛒"}

@app.get("/health")
def health():
    return {"status": "healthy", "model": OLLAMA_MODEL, "ollama_url": OLLAMA_URL}
