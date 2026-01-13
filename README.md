# YakTech OPN Monorepo

A comprehensive Open Negotiation document automation platform consisting of three integrated services.

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│    Repi     │────▶│ Orchestrator │────▶│  OPN-Agent  │
│  (Router)   │     │ (Middleware) │     │ (Generator) │
│  Port 8001  │     │  Port 8002   │     │  Port 8000  │
└─────────────┘     └──────────────┘     └─────────────┘
```

## 📦 Services

### Repi (Port 8001)
AI-powered routing agent using RAG for intelligent query classification.
- Routes queries to appropriate agents/subagents
- Extracts client name, wave number from natural language
- Uses Grok API for LLM capabilities

### Orchestrator (Port 8002)
Middleware service coordinating Repi and OPN-Agent.
- Single API endpoint for end-to-end workflows
- Smart file resolution based on client/wave parameters
- Agent registry configuration

### OPN-Agent (Port 8000)
Multi-agent document generation system.
- Generates Open Negotiation Excel group files
- Creates Word/PDF notice documents
- Validates data and provides insights

## 🚀 Quick Start

### 1. Start All Services

```powershell
# Terminal 1 - OPN-Agent
cd OPN-Agent
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH="D:\opn\yak_tech\OPN-Agent"
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 - Repi
cd repi
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001

# Terminal 3 - Orchestrator
cd orchestrator
.\venv\Scripts\Activate.ps1
uvicorn main:app --host 0.0.0.0 --port 8002
```

### 2. Test the Workflow

```bash
# Via Orchestrator (recommended)
curl -X POST http://localhost:8002/process \
  -H "Content-Type: application/json" \
  -d '{"query": "Create document for client CEP wave 6", "session_id": "test"}'

# Direct OPN-Agent call
curl -X POST http://localhost:8000/run-advanced-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "test",
    "excel_path": "path/to/input.xlsx",
    "template_docx": "path/to/template.docx",
    "output_folder": "path/to/output",
    "use_ai": false
  }'
```

## 📁 Project Structure

```
yak_tech/
├── OPN-Agent/                 # Document generation service
│   ├── AI_open_negotiation/   # Core agent logic
│   │   ├── agents/            # Document agents
│   │   ├── models/            # Result models
│   │   ├── plugins/           # SK plugins
│   │   └── Data/              # Input/Output folders
│   └── main.py                # FastAPI app
│
├── repi/                      # Routing service
│   ├── app/
│   │   ├── main.py            # FastAPI app
│   │   ├── rag/               # RAG components
│   │   └── config.py          # Configuration
│   └── .env                   # Environment variables
│
├── orchestrator/              # Middleware service
│   ├── main.py                # FastAPI app
│   ├── orchestrator.py        # Core logic
│   ├── file_resolver.py       # Smart file resolution
│   └── agent_registry.json    # Agent configuration
│
└── scripts/                   # Utility scripts
    ├── register_*.py          # Agent registration
    └── test_scripts/          # Test files
```

## ⚙️ Configuration

### Environment Variables

**Repi (.env)**
```
GROK_API_KEY=your_grok_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

**Orchestrator (.env)**
```
REPI_URL=http://localhost:8001
OPN_AGENT_URL=http://localhost:8000
ORCHESTRATOR_PORT=8002
```

### Agent Registry (orchestrator/agent_registry.json)
Configure agent endpoints, file patterns, and payload mappings.

## 📄 Generated Documents

For a typical CEP Wave 6 request, the system generates:
- 4 Group Excel files (per insurance plan)
- 4 Notice Word documents
- 4 Notice PDF files

Output location: `OPN-Agent/AI_open_negotiation/Data/Output/{client}_W{wave}/`

## 🛠️ Development

### Install Dependencies

```bash
# OPN-Agent
cd OPN-Agent && pip install -r requirements.txt

# Repi
cd repi && pip install -r requirements.txt

# Orchestrator
cd orchestrator && pip install -r requirements.txt
```

### Run Tests

```bash
cd scripts/test_scripts
python test_complete_workflow.py
python test_opn_direct.py
```

## 📝 License

Proprietary - YakTech Industries
