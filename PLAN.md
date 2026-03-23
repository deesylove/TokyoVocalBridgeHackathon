# Jizo - Voice Agent for Foreign Professionals in Japan

Named after Jizo Bosatsu (地蔵菩薩), the Buddhist guardian who watches over travelers and those facing difficult journeys.

## Context
Foreign professionals in Japan struggle with navigating tax, pension, healthcare, visa, banking, and housing systems. Jizo is a voice agent built on Vocal Bridge that guides users step-by-step through these processes in simple English, personalizing advice based on their visa type, employment, and situation.

## Project Structure
```
tokyo_vocal_bridge_hackathon/
├── .env                          # VOCAL_BRIDGE_API_KEY=vb_...
├── prompt.txt                    # System prompt (core agent behavior)
├── model_settings.json           # Voice, STT, temperature config
├── VocalBridgeInstructions.md    # Integration docs (WebRTC/LiveKit API)
├── knowledge/                    # Reference docs & step-by-step guides
│   ├── tax/                      # Income tax, residence tax, filing returns
│   ├── pension/                  # Pension system, lump-sum withdrawal
│   ├── healthcare/               # Health insurance, finding doctors
│   ├── visa/                     # First steps, residence card, PR path
│   ├── banking/                  # Bank accounts, international transfers
│   └── housing/                  # Renting, UR housing
└── venv/                         # Python 3.13 venv (vocal-bridge 0.14.0)
```

## Agent Configuration
- **Name**: Jizo
- **Style**: Chatty (openai_concierge)
- **Deploy**: Web only
- **STT**: nova-3
- **TTS Voice**: nova
- **Temperature**: 0.7
- **Web Search**: Enabled
- **Background AI**: Enabled
- **Debug Mode**: Enabled

## Knowledge Base Strategy
The `knowledge/` folder serves two purposes:
1. **Source of truth for the prompt** -- Key facts and step-by-step procedures are distilled from these guides into the system prompt. When we update a guide, we update the corresponding prompt section.
2. **Iteration reference** -- During testing, when the agent gets something wrong or misses a step, we update the relevant guide first, then reflect the fix in the prompt.

Each guide follows a consistent format: Overview, Who Needs This, Step-by-Step Process, Common Pitfalls, Key Deadlines, Useful Phrases.

## Completed Steps

### Step 1: Sign Up & Authenticate
- [x] Signed up at vocalbridgeai.com
- [x] Got API key (starts with `vb_`)
- [x] Authenticated via `vb auth login`

### Step 2: Knowledge Base
- [x] Created 13 step-by-step guides across 6 domains
- [x] Tax: income tax, residence tax, tax return filing
- [x] Pension: system overview, lump-sum withdrawal
- [x] Healthcare: health insurance, finding doctors
- [x] Visa: first steps arrival, residence card, path to PR
- [x] Banking: opening accounts, international transfers
- [x] Housing: renting in Japan, UR housing

### Step 3: System Prompt
- [x] Created `prompt.txt` distilled from knowledge base
- [x] Covers all 6 domains with key facts and decision trees
- [x] Includes conversation approach, tone guidelines, web search instructions

### Step 4: Model Settings
- [x] Created `model_settings.json` (nova-3 STT, nova voice, 0.7 temp)

### Step 5: Agent Deployed
- [x] Agent created and deployed on Vocal Bridge
- [x] WebRTC/LiveKit integration docs received (`VocalBridgeInstructions.md`)
- [ ] Update live agent name to "Jizo" and sync latest prompt

## Next: Frontend Integration

The agent is live and accessible via the Vocal Bridge API. Integration docs are in `VocalBridgeInstructions.md`.

### Architecture
```
Browser/App  <--WebRTC/LiveKit-->  Vocal Bridge  <-->  Jizo Agent
     |                                                       |
     |-- POST /api/v1/token (get access token)               |
     |-- Connect to LiveKit room                             |
     |-- Microphone audio streamed to agent                  |
     |-- Agent audio streamed back                           |
     |-- Transcript events via data channel                  |
```

### Key API Endpoints
- `POST /api/v1/token` -- Generate LiveKit access token (call from backend)
- Token response includes `livekit_url`, `token`, `room_name`

### Built-in Features (no config needed)
- **Heartbeat** -- Agent sends heartbeat to verify data channel connectivity
- **Live Transcript** -- `send_transcript` events with role, text, timestamp
- **Debug Events** -- Real-time streaming via `vb debug` or WebSocket

### Frontend Options
1. **Simple HTML/JS** -- Vanilla JavaScript with livekit-client SDK
2. **React** -- Hooks-based integration with @livekit/components-react
3. **Flutter** -- Mobile app with livekit_client package

### Dependencies
```bash
npm install livekit-client              # Core SDK
npm install @livekit/components-react   # React components (optional)
```

## Iteration Workflow
```bash
source venv/bin/activate

# Monitor live calls
vb debug                          # Stream real-time events

# Update prompt
vb prompt edit                    # Edit in $EDITOR
vb prompt set -f prompt.txt       # Set from file

# Review calls
vb logs                           # List recent calls
vb logs show <session_id>         # View transcript
vb logs download <session_id>     # Download recording
vb stats                          # Aggregate metrics

# Change settings
vb config set --model-settings-file model_settings.json
vb config show                    # Verify
```

## Key Decisions
- **Jizo** name -- Buddhist guardian of travelers, approachable and meaningful
- **Chatty style** -- Warm, conversational tone for stressed newcomers
- **Web only** deployment -- Free tier, good for hackathon demo
- **No external APIs** for MVP -- Built-in web search handles real-time info
- **Professional disclaimer** baked into prompt -- Not a substitute for legal/tax advice
