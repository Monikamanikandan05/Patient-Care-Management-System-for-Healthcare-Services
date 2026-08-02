# 🏥 IPCMS — Integrated Patient Care Management System

A full-stack cardiac-care web application built with **Streamlit**, **SQLAlchemy (MySQL)**, and an **AI chatbot** powered by Groq + LangChain + ChromaDB.

---

## 📁 Project Structure

```
Patient_Care_Systems/
├── app.py                  # Streamlit entry point
├── seed_data.py            # Creates tables + seeds default data
├── requirements.txt        # Python dependencies
├── run.sh                  # One-command launcher (Linux/Mac/Git-Bash)
├── .env                    # ← YOUR secrets (never commit!)
├── .env.example            # Safe template for sharing
├── .gitignore
├── README.md
│
├── core/                   # DB connection & security
│   ├── config.py           # Reads .env, builds DATABASE_URL
│   ├── database.py         # SQLAlchemy engine + session factory
│   └── security.py         # SHA-256 password hashing
│
├── models/
│   └── models.py           # ORM table definitions
│
├── services/               # Business logic (no UI code)
│   ├── auth_service.py
│   ├── appointment_service.py
│   ├── doctor_service.py
│   ├── health_service.py
│   └── analytics_service.py
│
├── views/                  # Streamlit UI pages
│   ├── auth_view.py
│   ├── patient_dashboard.py
│   ├── doctor_portal.py
│   ├── admin_portal.py
│   ├── appointments_view.py
│   ├── doctors_view.py
│   ├── chatbot_view.py
│   └── components.py
│
├── ai/                     # LLM / RAG chatbot
│   ├── smartcare_agent.py
│   ├── llm.py
│   ├── knowledge_base.py
│   ├── embeddings.py
│   └── vectorstore.py
│
├── assets/
│   └── styles.css
│
└── patient_care/           # Python virtual environment (never commit)
```

---

## ⚙️ Setup

### 1. Prerequisites
- Python 3.10+
- MySQL 8.x running locally

### 2. Create virtual environment
```bash
python -m venv patient_care
# Windows
patient_care\Scripts\activate
# Linux / macOS
source patient_care/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your MySQL password and Groq API key
```

### 5. Seed the database
```bash
python seed_data.py
```

### 6. Run the app
```bash
# Windows
patient_care\Scripts\python.exe -m streamlit run app.py

# Linux / macOS / Git-Bash
bash run.sh
```

The app will open at **http://localhost:8501**

---

## 🔑 Default Credentials (after seeding)

| Role    | Email                    | Password    |
|---------|--------------------------|-------------|
| Admin   | admin@smartcare.com      | admin123    |
| Doctor  | doctor@smartcare.com     | doctor123   |
| Patient | patient@smartcare.com    | patient123  |

> ⚠️ Change these immediately in a production environment.

---

## 🤖 AI Chatbot

The AI assistant uses [Groq](https://console.groq.com) (free tier available).  
Set your `GROQ_API_KEY` in `.env` to enable full functionality.  
Without a key, the chatbot runs in **offline simulation mode**.

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| ORM | SQLAlchemy |
| Database | MySQL 8 |
| AI / LLM | Groq (Mixtral-8x7B) |
| RAG | LangChain + ChromaDB |
| Auth | SHA-256 password hashing |
