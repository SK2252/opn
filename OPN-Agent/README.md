# 🚀 AI Open Negotiation Automation System v2.0

Production-ready multi-agent document processing system with Semantic Kernel integration for Open Negotiation documents.

## ✨ Features

- **Multi-Agent Architecture**: Specialized agents for validation, generation, and orchestration
- **Async Processing**: Full async/await support with parallel execution
- **AI Integration**: Semantic Kernel plugin with natural language processing
- **Error Recovery**: Automatic retry with exponential backoff
- **Comprehensive Logging**: Structured logging with configurable levels

## 📁 Project Structure

```
AI_open_negotiation/
├── agents/
│   ├── base_agent.py          # Abstract base class for all agents
│   ├── validation_agent.py    # Pre-processing validation
│   ├── generation_agents.py   # Document generators (Group, Notice, Merge)
│   └── orchestrator_agent.py  # Main pipeline orchestrator
├── models/
│   ├── task_models.py         # DocumentTask, TaskStatus, DocumentType
│   └── result_models.py       # ValidationResult, GenerationStats
├── plugins/
│   └── document_plugin.py     # Semantic Kernel plugin
├── orchestrators/
│   └── ai_orchestrator.py     # AI-powered orchestrator
├── utils/
│   ├── logger.py              # Enhanced logging
│   ├── file_utils.py          # File operations
│   └── formatters.py          # Data formatters
└── skills/
    ├── document_skill.py      # Legacy document skill
    └── email_skill.py         # Email automation
```

## 🔧 Installation

```bash
# Clone or navigate to project
cd "e:\Upgrade AI_Agent Project"

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env
# Edit .env with your OPENAI_API_KEY
```

## 🚀 Quick Start

### Start the Server

```bash
# Using uvicorn directly
uvicorn main:app --reload --port 8000

# Or using the main script
python main.py server
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/run-workflow` | POST | Legacy workflow (backward compatible) |
| `/run-advanced-workflow` | POST | New multi-agent processing |
| `/validate` | POST | Validate input data |
| `/analyze` | POST | Analyze data with insights |
| `/health` | GET | Health check |

### Example API Call

```bash
curl -X POST http://localhost:8000/run-advanced-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_001",
    "excel_path": "CEP W6 OPNNEG TEMPLATE.xlsx",
    "template_docx": "OpenNeg_CEP_Template.docx",
    "output_folder": "output",
    "use_ai": true
  }'
```

## 💻 Programmatic Usage

### Basic Usage

```python
import asyncio
from AI_open_negotiation.agents.orchestrator_agent import OrchestratorAgent

async def main():
    orchestrator = OrchestratorAgent({
        'max_retries': 3,
        'enable_parallel_processing': True
    })
    
    result = await orchestrator.process_document_request({
        'excel_path': 'data.xlsx',
        'template_docx': 'template.docx',
        'merged_output_folder': 'output/merged'
    })
    
    print(f"Status: {result['status']}")
    print(f"Output: {result['output_folder']}")

asyncio.run(main())
```

### AI-Powered Usage

```python
import asyncio
from AI_open_negotiation.orchestrators.ai_orchestrator import AIDocumentOrchestrator

async def main():
    orchestrator = AIDocumentOrchestrator(api_key="sk-...")
    
    result = await orchestrator.process_with_ai_guidance(
        excel_path="data.xlsx",
        template_docx="template.docx",
        output_folder="output",
        user_instructions="Focus on compliance"
    )
    
    print(result['insights'])

asyncio.run(main())
```

### Interactive Mode

```bash
python main.py interactive
```

## 🔌 Agent Architecture

```
OrchestratorAgent (Master Controller)
├── ValidationAgent (Pre-processing)
│   ├── File existence check
│   ├── Column validation
│   └── Data quality checks
├── GenerationAgents (Parallel Processing)
│   ├── GroupGenerationAgent → Excel files
│   └── NoticeGenerationAgent → Word/PDF files
└── MergeAgent (Post-processing)
    └── Combines all outputs
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key for AI features |
| `AI_MODEL_ID` | gpt-4o-mini | AI model to use |
| `LOG_LEVEL` | INFO | Logging level |
| `MAX_RETRIES` | 3 | Maximum retry attempts |
| `ENABLE_PARALLEL_PROCESSING` | true | Enable parallel execution |

## 📊 Output Structure

```
output/
├── groups/
│   └── {NPI}/
│       └── {InsurancePlan}/
│           └── {OpenNegGroup}.xlsx
├── notices/
│   └── {NPI}/
│       └── {InsurancePlan}/
│           ├── {OpenNegNotice}.docx
│           └── {OpenNegNotice}.pdf
└── merged/
    └── {NPI}/
        └── {InsurancePlan}/
            └── (all files combined)
```

## 🔄 Migration from v1.0

The `/run-workflow` endpoint maintains full backward compatibility:

```python
# Old code continues to work
response = await client.post("/run-workflow", json={
    "request_id": "req_001",
    "agents": ["document_creation"],
    "document_config": {...}
})
```

For new features, use `/run-advanced-workflow`:

```python
# New advanced features
response = await client.post("/run-advanced-workflow", json={
    "request_id": "req_001",
    "excel_path": "data.xlsx",
    "template_docx": "template.docx",
    "output_folder": "output",
    "use_ai": True
})
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=AI_open_negotiation
```

## 📝 License

Proprietary - All rights reserved.

## 📋 Document Processing Workflow

The system follows a structured workflow to generate Open Negotiation documents:

1.  **Input**: Place your source Excel file and Word template in the `AI_open_negotiation/Data/Input` folder.
    *   Example Input: `CEP W6 OPNNEG TEMPLATE.xlsx`
2.  **Processing**: Run the workflow via API (legacy or advanced).
    *   The system parses the input filename (e.g., "CEP W6") to determine the output location.
3.  **Auto-Generation**:
    *   **Group Files**: Excel files grouped by Provider/Insurance are generated.
    *   **Notice Files**: Word/PDF notices are generated from the template.
    *   **Merge**: All files are combined into a final folder.
4.  **Output**: Results are saved in `AI_open_negotiation/Data/Output/{InputName_Prefix}`.
    *   Example Output: `AI_open_negotiation/Data/Output/CEP W6` containing:
        *   `CEP W6 OPN GROUP/`
        *   `CEP W6 OPN NOTICE/`
        *   `CEP W6 OPN GROUP & NOTICE/`
