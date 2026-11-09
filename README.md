# ✨ Dukaan Dost AI (దుకాన్ దోస్త్ AI)
### Intelligent 3D Voice Assistant & Real-Time Operating System for Indian Kirana Stores
> **Built for the Gnani AI Internship Challenge**  
> *Multilingual Voice AI for Bharat — Telugu • English • Hindi*

---

## 🌟 Executive Overview

**Dukaan Dost AI** is a premium, futuristic full-stack AI voice assistant and retail operating system designed specifically for India's 12 million+ local kirana store owners. 

Instead of dealing with complicated accounting menus or static forms, a shopkeeper can simply **speak naturally** in **Telugu**, **English**, or **Hindi** to:
- Inquire about today's sales and revenue: *“ఈరోజు మొత్తం ఎంత అమ్మకాలు జరిగాయి?”* / *“What is today's revenue?”*
- Check real-time stock balances: *“బియ్యం ఎంత ఉంది?”* / *“How much rice is left?”*
- Add products and inventory by voice: *“10 కేజీల బియ్యం చేర్చు”* / *“Add 10 packets of rice”*
- Record customer sales on the fly: *“2 కేజీల పంచదార అమ్మాను”* / *“Sell 2 soap”*
- Ingest distributor invoices and stock data from **PDFs, Excel spreadsheets, CSVs, receipt photos, or voice dictation** with a strict confirmation/review step before modifying SQLite records.
- Track business analytics with real-time gross profit calculations, weekly sales velocity charts, and low-stock reorder warnings.

---

## 🚀 Key Features

### 1. Cinematic 3D Kirana Landing Page (`/`)
- **WebGL Three.js Indian Kirana Store Scene**: Features a 3D Kirana shop structure with traditional striped awning, wooden grocery shelves, counter desk, floating burlap rice bags (*సోనా మసూరి బియ్యం*), soap bars, dairy pouches, biscuit packets, spice jars, and floating holographic stock cards (*"Today's Sales: ₹12,450"*, *"Rice: 25 kg remaining"*).
- **Interactive Cursor Dynamics**: Scene responds smoothly to mouse tilt, perspective hover, and cursor-following parallax motion.
- **Hero Voice Trigger**: Direct *"Start Talking"* and *"Explore Dashboard"* entry points.

### 2. Speaking AI Assistant with Real Gnani AI Integration
- **Gnani Prisma STT (Speech-to-Text)**: Audio captured via browser Web Audio API in 16kHz PCM WAV format and transcribed with model `prisma-v3.0` (`https://api.vachana.ai/stt/v3`).
- **Audio file input**: Upload audio on the assistant page. Files in formats supported by FFmpeg (for example WAV, MP3, M4A/AAC, FLAC, OGG/Opus, and WebM) are converted to 16kHz mono PCM WAV before transcription. `imageio-ffmpeg` supplies the converter binary as a Python dependency.
- **Gnani Timbre TTS (Text-to-Speech)**: High-fidelity natural voice synthesis using model `timbre-v2.5` (`https://api.vachana.ai/api/v1/tts/inference`), with Kaveri voice profile.
- **Multilingual Spoken Greeting**: Welcomes the user naturally upon page launch:
  - *Telugu*: “నమస్కారం! నేను మీ దుకాన్ దోస్త్ AI. మీ షాప్ అమ్మకాలు, స్టాక్, ఆదాయం గురించి అడగండి. మీకు ఎలా సహాయం చేయాలి?”
  - *English*: “Hello! I’m Dukaan Dost AI. Ask me about today’s sales, revenue, inventory, or anything about your shop.”
  - *Hindi*: “नमस्ते! मैं हूँ दुकान दोस्त AI। आज की बिक्री, स्टॉक और कमाई के बारे में मुझसे पूछें। मैं आपकी क्या मदद करूँ?”
- **Visualizer & Orb States**: Pulsing interactive AI Orb reflecting real-time states: `Idle`, `Listening`, `Thinking`, and `Speaking` with active animated soundwave bars.
- **Audio Controls**: Replay greeting, mute/unmute audio toggle, language switcher, and browser SpeechSynthesis fallback for instant testing.

### 3. Real SQLite Database & Accurate Calculations
- **Never Hardcoded**: All sales figures, unit quantities, and transactions are queried directly from the SQLite database.
- **Revenue vs. Profit Distinction**: Accurately differentiates Gross Sales Revenue (`SUM(quantity * unit_price)`) from Gross Profit (`SUM(quantity * (unit_price - cost_price))`).
- **Asia/Kolkata Timezone Awareness**: Summarizes daily sales based on local store time.

### 4. Six Dedicated Pages & Navigation
1. **Home (`/`)**: Cinematic 3D Kirana experience, speaking AI assistant, feature highlights, and interactive voice chips.
2. **Dashboard (`/dashboard`)**: Business command center with live KPI tiles, 7-day revenue trend chart, category mix doughnut chart, recent transactions, best-sellers leaderboard, and low-stock alerts.
3. **Inventory (`/inventory`)**: Live catalogue with search, category filtering, stock health badges (Healthy, Low Stock, Out of Stock), Add/Edit product modals, and quick restock actions.
4. **Sales (`/sales`)**: Full transaction audit trail, quick date range filters (Today, Yesterday, 7 Days, 30 Days, All Time), custom date pickers, and instant sale recorder.
5. **AI Voice Assistant (`/assistant`)**: Dedicated full-screen voice companion with giant central 3D AI Orb, real-time audio soundwave visualizer, conversation history log, microphone controls, and audio file upload.
6. **Upload Center (`/upload`)**: Drag-and-drop document ingestion center for supplier PDFs, Excel `.xlsx`/`.xls`, CSVs, receipt photos, and audio dictation with editable data preview grid and confirmation workflow.

---

## 🛠️ Tech Stack & Architecture

- **Backend**: Python 3.11, Flask 3.0, SQLite3
- **Voice AI Engines**: Gnani AI Prisma STT (`https://api.vachana.ai/stt/v3`), Gnani AI Timbre TTS (`https://api.vachana.ai/api/v1/tts/inference`)
- **Document & Data Parsing**: `openpyxl` (Excel), `pypdf` (PDF), `csv` (CSV), `Pillow` (Images)
- **3D & Visuals**: Three.js WebGL, Chart.js, HTML5 Canvas, Web Audio API (PCM WAV recorder)
- **Styling**: Cyber-Kirana dark theme (Midnight Navy `#070913`, Violet/Purple `#8b5cf6`, Mint Green `#10b981`, Saffron Gold `#f59e0b`)

---

## 🔑 Configuring Gnani AI API Keys

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and paste your Gnani AI API credentials:
   ```env
   # Unified key or specific service keys
   GNANI_API_KEY=your_gnani_api_key_here
   GNANI_STT_API_KEY=your_gnani_stt_key_here
   GNANI_TTS_API_KEY=your_gnani_tts_key_here

   DEFAULT_LANGUAGE=te-IN
   PRISMA_MODEL=prisma-v3.0
   TIMBRE_MODEL=timbre-v2.5
   TIMBRE_VOICE=Kaveri
   ```

> **Security Note**: All Gnani API calls are executed strictly within the secure Python backend. API keys are never exposed in browser JavaScript or client headers.

---

## 💻 How to Run the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Flask Web Application
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

### 3. Run Automated Tests
```bash
python -m pytest
```
*All 14 unit and integration tests will execute, verifying health checks, multilingual NLP, database math, CSV ingestion, and CRUD lifecycles.*

---

## 📦 Project Structure

```
dukaan_dost_ai/
├── agent/
│   ├── intent_detector.py      # Multilingual NLP (Telugu, English, Hindi, Transliteration)
│   ├── orchestrator.py         # Business workflow, confirmation gating, speech dispatch
│   └── validation.py           # Stock and mutation guards
├── database/
│   ├── db.py                   # SQLite connection, migration, and analytics query engine
│   └── schema.sql              # Database schema (products, sales, stock_movements, expenses)
├── gnani/
│   ├── prisma.py               # Gnani Prisma v3.0 REST STT integration
│   └── timbre.py               # Gnani Timbre v2.5 REST TTS integration
├── modules/
│   ├── data_ingestion.py       # PDF, Excel, CSV, Image & Audio parser with confirmation
│   ├── inventory.py            # Catalogue CRUD & stock mutations
│   ├── restocking.py           # Low-stock detection logic
│   └── sales.py                # Sales summaries and transaction history
├── static/
│   ├── css/
│   │   └── style.css           # Futuristic cyber-kirana design system & glassmorphism
│   └── js/
│       ├── cursor.js           # 3D perspective card tilt & magnetic cursor follower
│       ├── dashboard.js        # Chart.js analytics & live telemetry updater
│       ├── three-scene.js      # Three.js 3D Kirana shop, floating items & AI core
│       └── voice-assistant.js  # Audio recorder, STT/TTS engine & soundwave visualizer
├── templates/
│   ├── base.html               # Shared futuristic navigation & ambient lighting
│   ├── landing.html            # Page 1: 3D Kirana landing page & speaking AI assistant
│   ├── dashboard.html          # Page 2: Business command dashboard & charts
│   ├── inventory.html          # Page 3: Product catalogue & stock health
│   ├── sales.html              # Page 4: Sales history & transaction logs
│   ├── assistant.html          # Page 5: Full-screen AI voice companion
│   └── upload.html             # Page 6: Universal multi-format invoice & data uploader
├── tests/
│   ├── test_app.py             # Core routes & command tests
│   ├── test_advanced_features.py # Multilingual, analytics, CSV & CRUD test suite
│   └── test_smoke.py           # Smoke test
├── app.py                      # Flask application factory & route dispatch
├── config.py                   # Environment configuration
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment configuration
└── README.md                   # Complete documentation
```

---

## 🏆 Gnani AI Challenge Highlights

- **Native Telugu & Indic NLP**: Seamlessly understands natural shopkeeper speech (*“ఈరోజు ఎంత సేల్ అయింది?”*, *“10 కేజీల బియ్యం చేర్చు”*, *“సబ్బులు ఎన్ని ఉన్నాయి?”*).
- **Zero Hallucination Guarantee**: Every figure is computed directly from actual SQLite tables.
- **Safety First**: Destructive or inventory-altering operations require confirmation before modifying store data.
- **Product Launch Grade UI**: A visual experience built with 3D WebGL, perspective tilts, and smooth animations that stands out.
