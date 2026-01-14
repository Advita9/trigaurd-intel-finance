# triguard-intent-finance

# FinAgent — Safety-Gated Multi-Agent Financial Action System (Prototype)

FinAgent is a safety-critical multi-agent automation prototype that converts natural language commands into deterministic financial workflows and executes them on a controlled dummy banking UI using browser automation. The system enforces **human approval gating (“conscious pause”)** and optional **vision-based screen validation** before irreversible actions.

This project demonstrates how to build LLM-driven action agents for banking workflows while maintaining safety guarantees (no hallucinated actions, strict plan schema, approval gates, verification).

---

## Key Capabilities

- **Intent extraction** from free-form user commands (LLM-based + schema validated)
- **Deterministic planning** constrained to pre-approved workflow templates
- **Execution engine** using Playwright for real browser UI automation
- **Safety Officer** agent independently gates irreversible actions:
  - risk rules
  - forced pause + approval
  - vision validation (confirmation screen authenticity check)
- **Redis-backed memory/state machine** for deterministic execution + crash safety
- **Real-time command dashboard**
  - user command input (text)
  - execution logs
  - pause approvals/rejections
  - screenshots
  - agent narration + browser TTS
- **Supports multiple workflows**
  - Buy digital gold
  - Transfer money
  - Pay electricity bill (supports “fetch due amount” flow)
  - Deposit funds (profile-only action)

---

## Architecture Overview

### Agent Layers

1. **Intent Agent**
   - Extracts structured intent from user command.
   - Outputs a strict schema `{action, amount, entity}`.
   - Example intents:
     - `"Buy 500 rupees gold"` → `{"action":"buy_gold","amount":500,"entity":"digital_gold"}`
     - `"Transfer 1000 to mom"` → `{"action":"transfer_money","amount":1000,"entity":"mom"}`
     - `"Pay my Tata bill"` → `{"action":"pay_bill","amount":null,"entity":"tata"}`

2. **Planner**
   - Generates an execution plan strictly from **approved templates**
   - No hallucinated tools / steps allowed
   - Output is a list of typed steps:
     ```json
     [{"step_id":1,"action":"navigate","page":"index"}, ...]
     ```

3. **Executor**
   - Executes steps sequentially against the dummy bank UI.
   - Uses Playwright selectors (DOM-first)
   - Can pause/resume via Redis state
   - Updates user profile + transaction history after workflow completion

4. **Safety Officer**
   - Independent policy gatekeeper
   - Stops execution on:
     - high-risk steps (requires_pause)
     - amount threshold violations
     - vision mismatch / suspicious confirmation screen
   - Forces conscious pause and writes:
     - `risk_flag`
     - screenshot for dashboard
     - narration/log messages

5. **Vision Engine (Optional / Pluggable)**
   - Screenshot → Vision model → JSON verdict verifying:
     - correct screen type
     - displayed amount matches expected amount
     - entity matches expected payee/asset (when available)

---

## Tech Stack

### Backend
- **FastAPI** (API + orchestration)
- **Pydantic / PydanticAI** (schemas + agent outputs)
- **Redis** (memory + deterministic state, logs, approvals, profile store)
- **Playwright** (UI automation)

### Frontend
- Static HTML dashboard (polling-based)
- Browser **SpeechRecognition (voice-to-text)** and **SpeechSynthesis (TTS narration)**

### Vision Safety Layer
- Gemini Vision (optional), with strict JSON output parsing and retry-safe extraction
- Screenshots stored in Redis in base64

---

## Repository Structure

```
finagent/
│
├── backend/
│ ├── main.py # FastAPI app + StaticFiles mount
│ ├── routes/
│ │ └── api.py # API routes (/intent /plan /execute /approve /reject /state /profile)
│ ├── agents/
│ │ ├── intent_agent.py # Intent extraction agent
│ │ ├── planner_agent.py # Deterministic planner templates
│ │ ├── executor_agent.py # Playwright executor
│ │ └── safety_officer.py # Safety gating + vision verification
│ ├── services/
│ │ ├── redis_memory.py # Redis state + profile/history persistence
│ │ ├── playwright_engine.py # Browser wrapper utilities
│ │ └── vision_engine.py # confirmation screen verifier
│ └── dashboard.html # dashboard UI (optional location)
│
├── dummy_bank/
│ ├── index.html
│ ├── gold.html / gold_confirm.html / gold_success.html
│ ├── transfer.html / transfer_confirm.html / transfer_success.html
│ ├── pay_bill.html / bill_confirm.html / bill_success.html
│ ├── profile.html # state visualization (balance/bills/history)
│ └── assets/style.css
│
├── requirements.txt
└── README.md
```


---

## Dummy Bank Workflows Implemented

### 1) Buy Digital Gold
UI Path:
`index → gold.html → gold_confirm → gold_success`

Plan example:
1. navigate(index)
2. click(invest_button)
3. enter_amount
4. click(proceed_button)
5. pause_for_approval (human gate)
6. confirm_payment (vision verification + execute)

---

### 2) Transfer Money
UI Path:
`index → transfer.html → transfer_confirm → transfer_success`

Plan example:
1. navigate(index)
2. click(transfer_button)
3. select_beneficiary
4. enter_amount
5. click(proceed_button)
6. pause_for_approval
7. confirm_transfer

---

### 3) Pay Electricity Bill
Supports “bill due amount from profile”:
- user can say: **“Pay my Tata bill”** (no amount needed)
- system fetches due from profile store

UI Path:
`index → pay_bill.html → bill_confirm → bill_success`

Plan example:
1. navigate(index)
2. click(pay_bill_button)
3. select_biller
4. fetch_bill_amount (pause_for_approval)
5. enter_amount
6. click(proceed_button)
7. click(submit_bill_button) (requires_pause)

---

### 4) Deposit Funds (Profile action)
No UI automation required:
- intent triggers executor to update profile balance and log transaction

---

## Safety Design

### Conscious Pause (Human-in-the-loop)
Execution halts when:
- step requires_pause=True
- risky threshold triggered (e.g. amount > MAX_SAFE_AMOUNT)
- vision mismatch

Redis state controls:
- `is_paused`
- `risk_flag`
- screenshot capture

### Vision Validation (Optional)
Before irreversible click:
- screenshot is taken
- vision model must return:
  ```json
  {"screen_valid":true,"amount_match":true,"entity_match":true}
  ```
If any mismatch → forced pause.

## API Endpoints

**Base URL:** `http://127.0.0.1:8001`

### Orchestration
- `POST /intent`  
  Request:
  ```json
  {"text":"Transfer 1000 to mom"}
  ```

- POST /plan

- POST /execute

### Safety / Human Gate

- POST /approve

- POST /reject

### Monitoring

- GET /state

    Returns:

    - paused

    - risk

    - logs

    - screenshot

    - narration

    - current_step

### Profile

- GET /profile
    Returns:

    - balance

    - bills due

    - history / transaction list

## Setup Instructions

**1) Create environment**

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2) Start Redis**
```
redis-server
```

**3) Run backend**
```
cd backend
uvicorn main:app --reload --port 8001
```

**4) Access dashboard**
```
Dashboard:
http://127.0.0.1:8001/

Dummy bank UI:
http://127.0.0.1:8001/dummy_bank/index.html

Profile:
http://127.0.0.1:8001/profile
```

## Execution Flow (End-to-end)

1. User enters command in dashboard

2. /intent extracts structured intent and stores it in Redis

3. /plan generates a deterministic workflow plan from templates

4. /execute runs executor:

- executes steps sequentially

- invokes Safety Officer when needed

- pauses on risky steps (Conscious Pause)

5. User approves/rejects in dashboard

6. Workflow completes and profile is updated (balance / bills / history)


## Notes / Limitations

- Prototype system intended for a controlled demo UI (not real banking integrations).

- Vision verification is model-dependent and requires API quota.

- UI selector maps are deterministic; vision fallback is optional and extensible.

## Demo Commands

- Buy gold:
```
Buy 500 rupees gold
```

- Transfer:
```
Transfer 2000 to mom
```

- Pay bill:
```
Pay my Tata bill
Pay 500 Tata bill
```

- Deposit:
```
Deposit 10000 rupees
```

## Roadmap (if extended)

- WebSocket dashboard streaming (instead of polling)

- Stronger planner constraints + formal tool graph validation

- OpenCV-based diffing for low-cost spoof detection

- Persistent profile storage (SQLite) + session replay

- Real speech-to-text via LiveKit / Deepgram
