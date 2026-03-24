from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from model_loader import load_model
from database.db import init_db, save_scan, get_dashboard_stats
from slowapi import Limiter
from slowapi.util import get_remote_address
from dotenv import load_dotenv
import re
import os
import httpx
import time
import uuid
import logging
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi.responses import RedirectResponse

# ── Setup logging ──────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Load environment variables ─────────────────────────────────────────
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SUPPORT_TO_EMAIL = os.getenv("SUPPORT_TO_EMAIL", SMTP_USER)
SUPPORT_FROM_NAME = os.getenv("SUPPORT_FROM_NAME", "PhishGuard Support")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHAT_SYSTEM_PROMPT = os.getenv("CHAT_SYSTEM_PROMPT", "You are PhishGuard AI Support. Give short, practical phishing-safety guidance. If uncertain, say so and recommend contacting human support.")

# ── Create FastAPI app ─────────────────────────────────────────────────
app = FastAPI()

# ── Rate limiter setup ─────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# ── CORS middleware ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "https://musical-torrone-407580.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Root route ─────────────────────────────────────────────────────────  
@app.get("/")
def root():
    return RedirectResponse(url="http://127.0.0.1:5500")

# ── Pydantic models ────────────────────────────────────────────────────
class ScanRequest(BaseModel):
    url: str = ""
    email: str = ""

class ContactRequest(BaseModel):
    name: str
    email: str
    message: str

class ChatRequest(BaseModel):
    message: str
    sessionId: str = ""

# ── Feature extraction function ────────────────────────────────────────
def extract_features(url: str, email: str) -> list:
    """Extract features for UI breakdown - MUST match TextFeatureExtractor logic"""
    features = []
    text = f"{url} {email}".lower()
    
    # 1. IP in URL check
    if re.search(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', text):
        features.append({"label": "IP address in URL", "value": "Highly suspicious", "risk": True})
    else:
        features.append({"label": "Uses domain name", "value": "Normal", "risk": False})
    
    # 2. Suspicious TLD check
    suspicious_tlds = ['.tk', '.ml', '.gq', '.xyz', '.top', '.cf', '.ga']
    found_tld = next((t for t in suspicious_tlds if t in text), None)
    if found_tld:
        features.append({"label": "Suspicious TLD", "value": found_tld, "risk": True})
    else:
        features.append({"label": "Domain extension", "value": "Normal", "risk": False})
    
    # 3. Excessive subdomains
    domain_match = re.search(r'https?://([^/]+)', text)
    if domain_match:
        subdomain_count = domain_match.group(1).count('.')
        if subdomain_count > 3:
            features.append({"label": "Excessive subdomains", "value": domain_match.group(1), "risk": True})
        else:
            features.append({"label": "Subdomain count", "value": "Normal", "risk": False})
    
    # 4. HTTP vs HTTPS
    if url.startswith("http://"):
        features.append({"label": "No HTTPS", "value": "Insecure connection", "risk": True})
    elif url.startswith("https://"):
        features.append({"label": "HTTPS present", "value": "Secure connection", "risk": False})
    else:
        features.append({"label": "Connection type", "value": "Unknown", "risk": False})
    
    # 5. URL length
    if url and len(url) > 75:
        features.append({"label": "URL is very long", "value": f"{len(url)} characters", "risk": True})
    elif url:
        features.append({"label": "URL length", "value": f"{len(url)} characters", "risk": False})
    
    # 6. Special characters
    special_count = url.count('-') + url.count('@') * 2 + url.count('%')
    if special_count > 4:
        features.append({"label": "Excessive special characters", "value": f"{special_count} found", "risk": True})
    else:
        features.append({"label": "Special characters", "value": "Normal", "risk": False})
    
    # 7. Phishing keywords
    phishing_keywords = ['verify', 'suspend', 'urgent', 'login', 'account', 'click', 'free',
                        'winner', 'update', 'confirm', 'banking', 'alert', 'limited',
                        'password', 'secure', 'reset', 'compromised', 'immediately',
                        'expires', 'locked', 'blocked', 'claim', 'prize', 'congratulations',
                        'selected', 'reward', 'gift', 'lucky', 'won', 'inheritance',
                        'beneficiary', 'transfer', 'nigeria', 'prince']
    found_keywords = [k for k in phishing_keywords if k in text]
    if found_keywords:
        features.append({"label": "Phishing keywords found", "value": ", ".join(found_keywords[:3]), "risk": True})
    else:
        features.append({"label": "Phishing keywords", "value": "None detected", "risk": False})
    
    # 8. Legitimate keywords
    legit_keywords = ['meeting', 'attached', 'report', 'schedule', 'team',
                     'project', 'review', 'invoice', 'delivered', 'receipt',
                     'newsletter', 'agenda', 'reminder', 'feedback']
    found_legit = [k for k in legit_keywords if k in text]
    if found_legit:
        features.append({"label": "Legitimate keywords", "value": ", ".join(found_legit[:2]), "risk": False})
    else:
        features.append({"label": "Legitimate keywords", "value": "None found", "risk": True})
    
    # 9. Suspicious character mimics
    if re.search(r'\b(l0gin|paypa1|g00gle|amaz0n|rn[il]cr0soft)\b', text):
        features.append({"label": "Suspicious character substitution", "value": "Detected", "risk": True})
    else:
        features.append({"label": "Character substitution", "value": "None detected", "risk": False})
    
    # 10. Exclamation marks (spam indicator)
    exclamation_count = text.count('!')
    if exclamation_count > 3:
        features.append({"label": "Excessive exclamation marks", "value": f"{exclamation_count} found", "risk": True})
    else:
        features.append({"label": "Exclamation marks", "value": "Normal", "risk": False})
    
    return features

# ── Chat session management ────────────────────────────────────────────
chat_sessions = {}
MAX_SESSION_TURNS = 6
SESSION_TIMEOUT = 30 * 60  # 30 minutes

def cleanup_expired_sessions():
    """Remove sessions inactive for more than 30 minutes"""
    current_time = time.time()
    expired = [sid for sid, (hist, timestamp) in chat_sessions.items() 
               if current_time - timestamp > SESSION_TIMEOUT]
    for sid in expired:
        del chat_sessions[sid]
    return len(expired)

# ── Async email function ───────────────────────────────────────────────
async def send_email_async(name: str, email: str, message: str):
    """Send email asynchronously without blocking"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[PhishGuard Support] New message from {name}"
        msg["From"] = f"{SUPPORT_FROM_NAME} <{SMTP_USER}>"
        msg["To"] = SUPPORT_TO_EMAIL
        msg["Reply-To"] = email
        
        text = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        html = f"<h2>Support message</h2><p><strong>Name:</strong> {name}</p><p><strong>Email:</strong> {email}</p><p><strong>Message:</strong></p><pre>{message}</pre>"
        
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        
        async with aiosmtplib.SMTP(hostname=SMTP_HOST, port=SMTP_PORT) as smtp:
            await smtp.login(SMTP_USER, SMTP_PASS)
            await smtp.send_message(msg)
        
        logger.info(f"Email sent from {email}")
    except Exception as e:
        logger.error(f"Email send failed: {e}")

# ── Load model and init database ───────────────────────────────────────
model = load_model()
init_db()

# ── API ENDPOINTS ──────────────────────────────────────────────────────

@app.post("/api/scan")
@limiter.limit("30/hour")
def scan(request: Request, scan_request: ScanRequest):
    """Scan URL or email for phishing threats"""
    try:
        text = f"{scan_request.url} {scan_request.email}".strip()
        prediction = model.predict([text])[0]
        score = model.predict_proba([text])[0][1]
        label = "phishing" if prediction == 1 else "legitimate"
        is_phishing = bool(prediction == 1)
        final_score = round(float(score) * 100, 1)

        if scan_request.url and scan_request.email:
            scan_type = "Both"
            target = scan_request.url
        elif scan_request.url:
            scan_type = "URL"
            target = scan_request.url
        else:
            scan_type = "Email"
            target = scan_request.email[:60]

        save_scan(scan_type, target, final_score, label, is_phishing)
        breakdown = extract_features(scan_request.url, scan_request.email)

        return {
            "label": label,
            "score": final_score,
            "is_phishing": is_phishing,
            "breakdown": breakdown
        }
    except Exception as e:
        logger.error(f"Scan error: {e}")
        return {"label": "error", "score": 0, "is_phishing": False, "breakdown": []}

@app.get("/api/dashboard")
@limiter.limit("60/hour")
def dashboard(request: Request):
    """Get dashboard statistics"""
    try:
        stats = get_dashboard_stats()
        return stats
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return {}

@app.post("/api/contact")
@limiter.limit("10/hour")
async def contact(request: Request, contact_data: ContactRequest, background_tasks: BackgroundTasks):
    """Send contact form message via email (async, non-blocking)"""
    try:
        name = contact_data.name.strip()
        email = contact_data.email.strip().lower()
        message = contact_data.message.strip()

        if not name or not email or not message:
            return {"ok": False, "error": "All fields required."}

        # Send email in background (non-blocking)
        background_tasks.add_task(send_email_async, name, email, message)
        
        return {"ok": True, "message": "Message received. We'll respond soon."}
    except Exception as e:
        logger.error(f"Contact form error: {e}")
        return {"ok": False, "error": "Could not process message. Please try again."}

@app.post("/api/chat")
@limiter.limit("20/hour")
async def chat(request: Request, chat_data: ChatRequest):
    """Chat with PhishGuard AI Support (server-side sessions)"""
    try:
        cleanup_expired_sessions()
        
        if not GROQ_API_KEY:
            logger.error("GROQ_API_KEY not configured")
            return {"ok": False, "error": "Chat service not available."}

        # Generate secure server-side session ID if none provided
        session_id = chat_data.sessionId[:80] if chat_data.sessionId else str(uuid.uuid4())
        message = chat_data.message.strip()[:800]

        if not message:
            return {"ok": False, "error": "Message required."}

        # Get or create session
        if session_id in chat_sessions:
            history, _ = chat_sessions[session_id]
        else:
            history = []
        
        messages = history + [{"role": "user", "content": message}]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {GROQ_API_KEY}"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "temperature": 0.2,
                    "messages": [
                        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                        *messages
                    ]
                },
                timeout=30.0
            )
            data = response.json()

        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        if not reply:
            logger.warning("Empty response from Groq API")
            return {"ok": False, "error": "Empty response received."}

        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": reply}
        ]
        if len(history) > MAX_SESSION_TURNS * 2:
            history = history[-(MAX_SESSION_TURNS * 2):]
        
        # Store with current timestamp
        chat_sessions[session_id] = (history, time.time())

        return {
            "ok": True, 
            "reply": reply,
            "sessionId": session_id
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"ok": False, "error": "Assistant unavailable."}
