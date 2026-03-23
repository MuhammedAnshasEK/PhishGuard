# 🛡️ PhishGuard — AI-Powered Phishing Detection System

> A full-stack phishing detection web app that uses Machine Learning to analyze suspicious URLs and emails in real time.

---

## 🔍 What It Does

PhishGuard helps users identify phishing threats by scanning suspicious URLs and email content. It provides an instant risk score, a detailed feature breakdown, and AI-powered support — all through a clean, modern web interface.

---

## ✨ Features

- **🔗 URL & Email Scanner** — Paste any suspicious URL or email text and get an instant phishing risk score (0–100)
- **🧠 ML-Powered Detection** — Ensemble model using Logistic Regression, LinearSVC, and Random Forest with TF-IDF features
- **📊 Live Threat Dashboard** — Real-time statistics on scans, threats blocked, and detection distribution
- **🤖 AI Support Chatbot** — Powered by Groq (LLaMA 3.3 70B) for phishing guidance and safe next steps
- **📰 Live Threat News** — Latest cybersecurity news pulled from The Hacker News RSS feed
- **📧 Contact Form** — Sends support messages via Gmail SMTP asynchronously
- **🌙 Dark / Light Mode** — Theme preference saved across sessions
- **⚡ Rate Limiting** — API endpoints protected against abuse

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript (Vanilla) |
| Backend | Python, FastAPI, Uvicorn |
| ML Model | scikit-learn (VotingClassifier) |
| Database | PostgreSQL + SQLAlchemy |
| AI Chatbot | Groq API (LLaMA 3.3 70B) |
| Email | aiosmtplib + Gmail SMTP |
| Rate Limiting | SlowAPI |

---

## 📁 Project Structure

```
PHISHGUARD/
├── index.html              # Landing page (dashboard, news, contact)
├── checker.html            # Threat scanner page
├── chatbot.html            # Full-page AI chat
├── css/                    # Stylesheets
├── js/
│   ├── main.js             # Core frontend logic
│   └── chat-widget.js      # Floating chat bubble (all pages)
├── images/                 # UI images
├── start.ps1               # One-command startup script (Windows)
└── ml_backend/
    ├── main.py             # FastAPI app + all API endpoints
    ├── model_loader.py     # ML model loader
    ├── train_model.py      # Model training script
    ├── model.pkl           # Trained ML model
    ├── .env                # Environment variables (not committed)
    ├── requirements.txt    # Python dependencies
    └── database/
        └── db.py           # PostgreSQL models + queries
```

---

## 🚀 Local Setup Guide

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Git

---

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/PhishGuard.git
cd PhishGuard
```

---

### 2. Set Up Python Virtual Environment

```bash
cd ml_backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

---

### 3. Set Up PostgreSQL Database

Open `psql` and run:

```sql
CREATE USER phishguard_user WITH PASSWORD 'phishguard_pass_123';
CREATE DATABASE phishguard_db OWNER phishguard_user;
GRANT ALL PRIVILEGES ON DATABASE phishguard_db TO phishguard_user;
```

---

### 4. Create `.env` File

Inside `ml_backend/`, create a `.env` file:

```env
DATABASE_URL=postgresql://phishguard_user:phishguard_pass_123@localhost:5432/phishguard_db
GROQ_API_KEY=your_groq_api_key_here
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_gmail@gmail.com
SMTP_PASS=your_gmail_app_password
SUPPORT_TO_EMAIL=your_gmail@gmail.com
SUPPORT_FROM_NAME=PhishGuard Support
```

> 💡 Get a free Groq API key at [console.groq.com](https://console.groq.com)
> 💡 Get a Gmail App Password at [myaccount.google.com](https://myaccount.google.com) → Security → App Passwords

---

### 5. Start the App (Windows)

From the `PHISHGUARD` root folder:

```powershell
.\start.ps1
```

This starts both:
- **Backend** → `http://127.0.0.1:8000`
- **Frontend** → `http://127.0.0.1:5500`

---

### 5. Start the App (Mac/Linux)

Run both in separate terminals:

```bash
# Terminal 1 — Backend
cd ml_backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd ..
python -m http.server 5500
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/scan` | Scan a URL or email for phishing |
| GET | `/api/dashboard` | Get threat statistics |
| POST | `/api/contact` | Send a support message |
| POST | `/api/chat` | Chat with AI assistant |

### Example: Scan a URL

```bash
curl -X POST http://127.0.0.1:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "http://suspicious-login.tk/verify"}'
```

**Response:**
```json
{
  "label": "phishing",
  "score": 87.3,
  "is_phishing": true,
  "breakdown": [
    { "label": "Suspicious TLD", "value": ".tk", "risk": true },
    { "label": "Phishing keywords found", "value": "verify, login", "risk": true }
  ]
}
```

---

## 🧠 ML Model Details

The model uses a **VotingClassifier** ensemble combining:
- Logistic Regression
- LinearSVC (Calibrated)
- Random Forest

Features are extracted using:
- **TF-IDF** on URL/email text
- **Custom hand-crafted features** — IP in URL, suspicious TLDs, phishing keywords, URL length, special characters, HTTPS presence, and more

---

## ⚙️ Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `GROQ_API_KEY` | Groq API key for LLaMA chatbot |
| `SMTP_HOST` | SMTP server (default: smtp.gmail.com) |
| `SMTP_PORT` | SMTP port (default: 587) |
| `SMTP_USER` | Gmail address for sending emails |
| `SMTP_PASS` | Gmail App Password |
| `SUPPORT_TO_EMAIL` | Email to receive contact form messages |
| `SUPPORT_FROM_NAME` | Display name for support emails |

---

## 📸 Pages

| Page | URL | Description |
|---|---|---|
| Home | `/index.html` | Dashboard, news, FAQ, contact |
| Threat Scanner | `/checker.html` | URL & email scanning |
| AI Chat | `/chatbot.html` | Full-page AI support chat |
| API Docs | `http://127.0.0.1:8000/docs` | Interactive Swagger UI |

---

## 📄 License

This project was built as part of a 6th semester IBM project at Yenepoya University.

---

## 🙋 Support

For issues or questions, contact: **phishguardsupport@gmail.com**
