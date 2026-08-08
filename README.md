# 🚀 Kinetic Campus — AI-Powered Python Flask Web Application

> **100% Python Flask Implementation** — An intelligent campus event management, interactive archive, and GPU AI platform built for Presidency University, Bengaluru.

---

## 📁 Project Structure

```
kinetic-campus-flask/
├── app.py                  ← Main Python Flask server (REST API & routes)
├── ai_engine.py            ← PyTorch GPU/CPU AI Engine (NVIDIA RTX CUDA)
├── seed_events.py          ← Database sample events seeder
├── requirements.txt        ← Python dependencies (Flask, PyTorch, Transformers, MySQL)
├── setup.sql               ← MySQL database schema script
├── static/
│   ├── ai_features.js      ← AI Chatbot & frontend AI engine
│   └── uploads/            ← Uploaded event banner images
└── templates/              ← HTML5 & Jinja2 Templates
    ├── index.html          ← Home page
    ├── register.html       ← Login & Register page
    ├── dashboard.html      ← Student Dashboard page
    ├── explore.html        ← Browse Events, Voice Search & AI Recommendations
    ├── create_event.html   ← Create Event Form & AI Writer
    ├── event_details.html  ← RSVP Form & Leaflet Campus Map
    ├── my_events.html      ← Student Registered Events
    ├── admin_dashboard.html← Live Admin Analytics & GPU Telemetry Dashboard
    └── success.html        ← Registration Success page
```

---

## 🛠️ Technology Stack (100% Python)

| Layer | Technology |
|---|---|
| **Backend Framework** | Python 3.12 + Flask 3.0 |
| **Artificial Intelligence** | PyTorch (CUDA 12.1) + Sentence-Transformers (`all-MiniLM-L6-v2`) |
| **Data Analytics** | NumPy + Chart.js |
| **Database** | MySQL Server via `mysql-connector-python` |
| **Frontend** | HTML5, Tailwind CSS, JavaScript (ES6+), Leaflet.js Maps |
| **Audio Processing** | Web Speech API (AI Voice Search) |

---

## ⚙️ Setup & Run Instructions

### 1. Install Dependencies
```bash
py -3.12 -m pip install -r requirements.txt
```

### 2. Set up MySQL Database
Import `setup.sql` into MySQL Workbench or run:
```bash
mysql -u root -p < setup.sql
```

### 3. Seed Sample Events (Optional)
```bash
py -3.12 seed_events.py
```

### 4. Start the Application
```bash
py -3.12 app.py
```
Open 👉 **http://localhost:5000** in your browser.

---

## ✨ Core Features

- 🐍 **100% Python Flask REST Architecture** — Session handling, secure password hashing, and MySQL integration.
- 🟢 **GPU-Accelerated AI Engine (`ai_engine.py`)** — Automatic CUDA detection for NVIDIA GPUs (RTX series) with CPU fallback.
- 🔍 **Semantic Search** — 384-dimensional PyTorch vector embeddings to understand search queries by context instead of plain text matching.
- 🎤 **AI Voice Search** — Real-time speech recognition for event filtering.
- 🗺️ **Campus Maps** — Interactive Leaflet.js map centered on Presidency University, Yelahanka, Bengaluru with venue pins.
- 🤖 **KineticAI Chatbot** — Assistant for event discovery and seat availability checks.
- 📊 **Admin Analytics Dashboard** — Live telemetry for GPU VRAM, CPU load, trending scores, department breakdown, and CSV report exporter.
