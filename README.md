# YakTech OPN Monorepo (Unified v2.0)

A comprehensive Open Negotiation document automation platform with unified routing and execution.

## 🏗️ Architecture

```
┌─────────────────────────────────┐      ┌─────────────┐ 
│            Repi                 │      │  OPN-Agent  │
│ (Router + Orchestrator + API)   │─────▶│ (Generator) │
│           Port 8001             │      │  Port 8000  │
└─────────────────────────────────┘      └─────────────┘
```

## 📦 Services

### Repi (Port 8001) - **Unified Brain**
Combines AI routing and orchestration into a single service.
- **Intelligent Routing:** Classifies query using RAG + Grok LLM
- **Orchestration:** Automatically executes downstream agents
- **File Resolution:** Auto-discovers files based on patterns
- **Agent Registry:** Stores capabilities and endpoints in database

### OPN-Agent (Port 8000) - **Specialized Worker**
Dedicated document factory.
- Generates Open Negotiation Excel group files
- Creates Word/PDF notice documents
- Validates data and provides insights

### UI (Port 3000)
User interface.
- React/Vite based frontend
- Connects to Repi (Port 8001)

## 🚀 Quick Start

### 1. Start Services

```powershell
# Terminal 1 - OPN-Agent (The Worker)
cd OPN-Agent
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Repi (The Brain)
cd repi
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 2. Run Automation

You can now trigger the entire workflow via Repi's unified endpoint:

```bash
curl -X POST http://localhost:8001/process/process \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create document for CEP Wave 6" 
  }'
```

**What happens:**
1. Repi analyzes query -> Routes to "Open Negotiation Agent"
2. Repi finds agent endpoint (http://localhost:8000...) from DB
3. Repi auto-resolves files (Excel, Templates)
4. Repi calls OPN-Agent -> Returns combined result

## 📁 Project Structure

```
yak_tech/
├── OPN-Agent/                 # Document generation service
│   └── ...
│
├── repi/                      # Unified Routing & Orchestration
│   ├── app/
│   │   ├── api/
│   │   │   ├── process.py     # ✅ Unified Endpoint
│   │   │   ├── chat.py        # Routing Logic
│   │   │   └── ingest.py      # Agent Registration
│   │   ├── services/
│   │   │   ├── orchestration_service.py  # ✅ Core Logic
│   │   │   ├── file_resolver.py          # ✅ File Discovery
│   │   │   └── ...
│   └── .env
│
└── scripts/                   # Utility scripts
```

## ⚙️ Adding New Agents (Infinite Scaling)

To add a new agent, simply register it via API with an `endpoint`:

```bash
curl -X POST http://localhost:8001/ingest/agent \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Email Agent",
    "description": "Sends emails to clients",
    "capabilities": ["email_sending"],
    "endpoint": "http://localhost:8003/send-email",
    "payload_mapping": {
      "to": "{client_email}",
      "subject": "Notice for {client_name}"
    }
  }'
```

The system will now automatically route relevant queries to this new agent!
