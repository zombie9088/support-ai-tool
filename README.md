# SupportAI — Customer Support AI Ticket Tool

AI-powered support ticket categorization and response suggestion system using a 6-agent agentic pipeline.

---

## Features

- **6-Agent Pipeline**: Specialized agents for preprocessing, classification, priority scoring, emotion analysis, response drafting, and quality checking
- **PII Masking**: Automatic detection and anonymization of sensitive customer data
- **Smart Classification**: Category assignment with confidence scores and alternatives
- **Priority Triage**: P1-P4 priority levels with SLA targets and escalation flags
- **Churn Detection**: Sentiment analysis, frustration scoring, and churn risk identification
- **Dual-Tone Responses**: Formal and friendly draft responses tailored to each ticket
- **Quality Scoring**: Automated quality assessment with redraft loop for subthreshold responses
- **Batch Processing**: Process hundreds of tickets at once with progress tracking
- **Analytics Dashboard**: Real-time metrics, charts, and efficiency calculations
- **Export Options**: JSON, CSV export and simulated ticketing system push

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Streamlit UI (app.py)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   run_pipeline()                          │   │
│  │                                                            │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │   │
│  │  │ Agent 1 │→ │ Agent 2 │→ │ Agent 3 │→ │ Agent 4 │      │   │
│  │  │Preprocess│ │Classify │ │Priority │ │ Emotion │      │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │   │
│  │       ↓              ↓              ↓              ↓       │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │   │
│  │  │ PII     │  │Category │  │ P1-P4   │  │Sentiment│      │   │
│  │  │ Cleaning│  │ +Conf   │  │ +SLA    │  │ +Churn  │      │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │   │
│  │                                                            │   │
│  │  ┌─────────┐  ┌─────────┐                                 │   │
│  │  │ Agent 5 │→ │ Agent 6 │                                 │   │
│  │  │ Drafter │  │ Quality │                                 │   │
│  │  └─────────┘  └─────────┘                                 │   │
│  │       ↓              ↓                                     │   │
│  │  ┌─────────┐  ┌─────────┐                                 │   │
│  │  │Formal + │  │ Scores  │                                 │   │
│  │  │Friendly │  │ +Redraft│                                 │   │
│  │  └─────────┘  └─────────┘                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Pipeline

| Agent | Function | Input | Output |
|-------|----------|-------|--------|
| **Agent 1: Preprocessor** | PII masking, text cleaning | Raw ticket text | Cleaned text, key issue, tone, urgency keywords |
| **Agent 2: Classifier** | Category classification | Preprocessed text | Category, subcategory, confidence score |
| **Agent 3: Priority** | Priority assignment | Preprocessed + classified | P1-P4, SLA hours, escalation flag |
| **Agent 4: Emotion** | Sentiment & churn analysis | All previous outputs | Sentiment, frustration, churn risk, VIP status |
| **Agent 5: Drafter** | Response generation | All previous outputs | Formal draft, friendly draft |
| **Agent 6: Quality Checker** | Quality scoring | All outputs + drafts | Scores, flags, approved draft, redraft loop |

---

## Setup

### Prerequisites

- Python 3.12.8 or compatible
- Access to an OpenAI-compatible API endpoint

### Installation

1. **Clone or create the project directory:**

```bash
cd support-ai-tool
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
api_endpoint=https://your-api-endpoint.com/v1
api_key=your-api-key-here
model="genailab-maas-gpt-35-turbo"
```

4. **Generate synthetic data (optional, auto-generates on first run):**

```bash
python utils/synthetic_data.py
```

---

## Running the Application

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`.

---

## Usage

### Single Ticket Mode

1. Paste a support ticket into the text area
2. (Optional) Fill in ticket ID, customer ID, and channel
3. Click "🚀 Analyze Ticket"
4. View results:
   - Category and confidence
   - Priority level with SLA target
   - Churn risk meter
   - Emotion analysis
   - Formal and friendly response drafts
   - Quality scores
5. Expand "🔍 View Agent Reasoning Trace" to see detailed outputs

### Batch Upload Mode

1. Upload a CSV file with columns: `ticket_id`, `subject`, `body`
2. Or click "📊 Use Synthetic Data" to process 100 pre-generated tickets
3. Click "⚡ Process All Tickets"
4. View results table, sentiment heatmap, and churn risk leaderboard

### Analytics Dashboard

1. Process tickets in Single or Batch mode first
2. Navigate to Analytics Dashboard
3. View:
   - KPI cards (tickets processed, avg confidence, time saved)
   - Category distribution (donut chart)
   - Priority breakdown (bar chart)
   - Churn risk distribution (pie chart)
   - Success metrics panel

---

## Project Structure

```
support-ai-tool/
├── .env                          # API credentials (fill this in)
├── .env.example                  # Template with placeholder values
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── app.py                        # Main Streamlit entry point
├── data/
│   └── synthetic_tickets.csv     # Pre-generated synthetic data (100 tickets)
├── agents/
│   ├── __init__.py
│   ├── preprocessor.py           # Agent 1 — PII masking, text cleaning
│   ├── classifier.py             # Agent 2 — Category + confidence
│   ├── priority.py               # Agent 3 — P1–P4 + SLA + escalation
│   ├── emotion.py                # Agent 4 — Sentiment + churn + VIP
│   ├── drafter.py                # Agent 5 — Formal + friendly drafts
│   └── quality_checker.py        # Agent 6 — Scoring + redraft loop
├── utils/
│   ├── __init__.py
│   ├── synthetic_data.py         # Synthetic ticket generator
│   ├── exporter.py               # JSON/CSV export + ticketing push
│   └── metrics.py                # Metrics tracking
└── components/
    ├── __init__.py
    ├── single_ticket_view.py     # Single ticket results display
    ├── batch_view.py             # Batch results table + heatmap
    └── analytics_view.py         # Analytics dashboard
```

---

## Synthetic Data

The `utils/synthetic_data.py` module generates 100 realistic support tickets with:

- **Balanced categories**: Billing (15), Technical (20), Account (15), Shipping (10), Refund (10), Feature Request (15), Security (10), General Inquiry (5)
- **Varied tones**: Angry, frustrated, neutral, polite, urgent
- **Churn signals**: 20% of tickets contain cancellation/competitor mentions
- **VIP markers**: 10% of tickets indicate enterprise/premium customers

Each ticket includes:
- `ticket_id`, `customer_id`, `channel`
- `category`, `subcategory`
- `priority_hint`, `churn_risk_hint`
- `subject`, `body` (3-6 sentences, realistic first-person language)
- `created_at`

---

## API Integration

The application uses an OpenAI-compatible API client:

```python
import httpx
from openai import OpenAI

client = httpx.Client(verify=False)
llm = OpenAI(
    base_url=os.getenv("api_endpoint"),
    api_key=os.getenv("api_key"),
    http_client=client
)
```

All LLM calls use:
```python
llm.chat.completions.create(
    model=os.getenv("model"),
    messages=[...]
)
```

---

## Export Options

### JSON Export
Download full pipeline results as formatted JSON.

### CSV Export
Download batch results as CSV with flattened fields.

### Simulated Ticketing Push
Simulates pushing to Zendesk/Freshdesk/ServiceNow with:
- Generated ticket number (e.g., `ZD-45678`)
- Priority mapping
- Assignment to AI-Triage-Queue

---

## Quality Features

- **Error Handling**: All agents wrapped in try/except, never crash the app
- **JSON Parsing**: Strips markdown fences before parsing
- **Redraft Loop**: Max 2 attempts if quality score < 70
- **Session State**: Results persist across UI interactions
- **Progress Indicators**: Live status updates for each agent
- **Confidence Threshold**: Configurable slider (50-100%) to flag low-confidence tickets

---

## Demo Flow (Hackathon Presentation)

1. Open app → sidebar shows model info from `.env`
2. Click "Load Demo Ticket" → high churn-risk billing ticket loads
3. Click "Analyze Ticket" → progress bar shows 6 agents running
4. Results appear: red P1 badge, 87% churn risk meter, formal + friendly drafts
5. Expand agent trace → judges see full reasoning
6. Switch to Batch Upload → load synthetic_tickets.csv → process all → heatmap appears
7. Switch to Analytics → KPI cards show time saved metric
8. Click "Export JSON" → download full payload
9. Click "Simulate Ticketing Push" → `ZD-XXXXX` ticket number appears

---

## Troubleshooting

### "Model not configured" error
Ensure `.env` file exists with valid `api_endpoint`, `api_key`, and `model`.

### "SSL verification failed"
The app uses `httpx.Client(verify=False)` for internal endpoints. For production, use valid SSL certificates.

### "No synthetic data found"
Run `python utils/synthetic_data.py` or click "Generate New Synthetic Data" in the sidebar.

### Low confidence scores
Tickets with confidence < 60% are flagged for human review. This is expected for ambiguous tickets.

---

## License

MIT License

---

## Support

For issues or questions, please open an issue in the project repository.
