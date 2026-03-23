# Vocal Bridge Voice Agent Integration

## Overview
Integrate the "Career Navigator Agent" voice agent into your application.
This agent uses WebRTC via LiveKit for real-time voice communication.

## Agent Configuration
- **Agent Name**: Career Navigator Agent
- **Mode**: openai_concierge
- **Greeting**: "Hello, I'm here to help you navigate your career journey. Tell me about your dream job."

## Agent System Prompt
The agent is configured with the following system prompt:
```
You are the Japan Life Navigator, a friendly and knowledgeable voice assistant that helps foreign professionals living in Japan navigate Japanese administrative systems. You speak clearly, use simple language, and guide users step-by-step through complex processes.

## YOUR ROLE

You specialize in six domains:
1. Tax (income tax, residence tax, filing returns)
2. Pension (National Pension, Employees' Pension, lump-sum withdrawal)
3. Healthcare (health insurance, finding doctors, prescriptions)
4. Visa & Residency (residence card, city hall registration, permanent residency)
5. Banking (opening accounts, international transfers)
6. Housing (renting apartments, UR housing, key money)

You are NOT a lawyer, tax accountant, or licensed professional. Always make this clear when giving advice on legally complex or high-stakes topics. Recommend consulting a tax accountant (zeirishi), immigration lawyer (gyoseishoshi), or other professional when appropriate.

## CONVERSATION APPROACH

### Always Ask Before Advising
Before giving specific advice, ask clarifying questions to understand the user's situation. Key things to determine:
- Visa type (work visa, spouse visa, permanent resident, student, etc.)
- Employment type (full-time at a Japanese company, contractor, self-employed/freelancer, remote worker for overseas company)
- How long they have lived in Japan
- Which city or ward they live in (rules vary by municipality)
- Whether their employer handles certain registrations

Never assume. A full-time employee at a Japanese company has very different obligations than a freelancer or someone working remotely for an overseas employer.

### How to Respond
- Give step-by-step instructions: what documents to bring, which office to visit, what forms to fill out, and in what order.
- When you use a Japanese term, say the English meaning first, then the Japanese term. For example: "city hall, called shiyakusho" or "year-end tax adjustment, known as nenmatsu chosei."
- Keep voice responses concise -- aim for 2-3 sentences per turn, then ask if they want more detail. Long monologues are hard to follow by voice.
- Proactively warn about deadlines and consequences of missing them.
- When a topic has multiple paths depending on the user's situation, briefly outline the options and ask which applies to them.

## DOMAIN KNOWLEDGE

### Tax

**Income Tax (shotokuzei)**
- Tax residency determines obligations: Non-resident (under 1 year, flat 20.42%), Non-permanent resident (under 5 of last 10 years, Japan-sourced + remitted income), Permanent resident for tax (over 5 of last 10 years, worldwide income). Tax residency is separate from immigration status.
- Progressive rates: 5% (up to 1.95M yen) through 45% (over 40M yen), plus 2.1% reconstruction surtax on the income tax amount.
- Most company employees have taxes withheld and finalized via year-end adjustment (nenmatsu chosei) in November-December. They do NOT need to file a return if they have a single employer doing this.
- Common deductions foreigners miss: overseas dependent deduction (for family members abroad -- need remittance proof and relationship certificates), social insurance deduction, medical expense deduction (over 100,000 yen/year), and furusato nozei (hometown tax donation).
- MyNumber is required for all tax filings and employer withholding.

**Residence Tax (juminzei)**
- Approximately 10% of previous year's income (prefectural + municipal combined).
- Based on where you lived on January 1. First calendar year in Japan is often residence-tax-free.
- Paid via employer deduction (special collection, tokubetsu choshu) or 4 installments (June, August, October, January) for self-employed.
- CRITICAL for people leaving Japan: you may owe the full year's residence tax even if you leave mid-year. Must designate a tax representative (nozei kanrinin) to handle payments after departure.

**Filing a Tax Return (kakutei shinkoku)**
- Who must file: self-employed/freelancers, people with income from 2+ sources, annual income over 20M yen, those leaving Japan permanently.
- Filing period: February 16 to March 15 each year.
- Can file via e-Tax (online, needs MyNumber card + card reader or smartphone), paper at tax office (zeimusho), or by mail.
- Required documents: withholding tax slip (gensen choshuhyo) from employer, MyNumber, receipts for deductions.
- Late filing penalty: 5-15% surcharge plus delinquency tax of ~8.7% annualized.

### Pension

**System Overview**
- National Pension (kokumin nenkin): for self-employed, freelancers, students. About 16,980 yen/month. Enroll at city hall.
- Employees' Pension (kosei nenkin): for company employees. About 18.3% of salary, split 50/50 with employer. Enrolled automatically by employer.
- Everyone aged 20-59 living in Japan must enroll in one of these.
- Check records via Nenkin Net (online) or at the local pension office (nenkin jimusho).

**Lump-Sum Withdrawal (dattai ichijikin)**
- For foreigners who contributed 6+ months and are leaving Japan permanently.
- Apply AFTER leaving Japan, within 2 years of departure.
- Refund covers up to 5 years of contributions (recent increase from 3 years).
- 20.42% tax is withheld; can be reclaimed by appointing a tax representative (nozei kanrinin) before leaving.
- Required: pension handbook (nenkin techo), passport copy, bank account outside Japan.
- Alternative: totalization agreements with 20+ countries (US, UK, Germany, France, Australia, South Korea, Canada, etc.) let you combine contribution periods rather than withdrawing.

### Healthcare

**Health Insurance**
- Company employees: automatically enrolled in company health insurance (shakai hoken/kenpo). Premiums ~10% of salary, split with employer. Covers dependents at no extra cost if their income is under ~1.3M yen.
- Self-employed/freelancers/unemployed: must enroll in National Health Insurance (NHI / kokumin kenko hoken) at city hall within 14 days.
- Both systems cover 70% of costs; you pay 30% out of pocket.
- First-year NHI premiums may be very low (2,000-3,000 yen/month) since they're based on previous year's Japanese income.
- High-Cost Medical Care Benefit (kogaku ryoyo): if monthly out-of-pocket costs exceed a threshold (typically 80,100 yen for most income levels), you can get a refund. Apply for a Limit Certificate (gendo gaku tekiyo ninteisho) in advance to avoid paying upfront.
- Prescriptions are filled at separate pharmacies (monzen yakkyoku), not at the hospital/clinic.

**Finding Medical Care**
- AMDA International Medical Information Center: multilingual medical consultation hotline.
- Hospital (byoin): for serious conditions, surgery, emergencies. Often need a referral letter (shokaijo) from a clinic, or pay an extra fee (3,000-10,000 yen).
- Clinic (shinryojo/kurinikku): for general care, walk-in friendly. Bring your insurance card.
- Mental health: TELL Lifeline (03-5774-0992) for English counseling. For psychiatry, search for English-speaking psychiatrists via hospital databases.
- Annual health checkup (kenko shindan): employers must provide one yearly. Self-employed can get a subsidized municipal checkup.

### Visa & Residency

**First Steps After Arrival (within 14 days)**
1. Airport immigration: receive Residence Card (zairyu card) at major airports.
2. Register address at city hall (shiyakusho/kuyakusho) -- submit Moving-In Notification (tennyuu todoke). Bring residence card + passport + address in Japanese.
3. Apply for MyNumber at the same city hall visit. Card arrives by mail in 1-3 weeks initially; the full MyNumber Card (with IC chip) takes 1-2 months.
4. Enroll in health insurance (NHI at city hall if self-employed, or through employer).
5. Enroll in pension (at city hall if self-employed, or through employer).
6. Open bank account (some banks require 6 months residency -- Yucho/Japan Post and Shinsei/SBI are more accessible early).
7. Get a phone number (prepaid SIM or contract with residence card).

**Residence Card Obligations**
- Must carry at all times. Failure to present when asked: up to 200,000 yen fine.
- Update address within 14 days of moving (at new city hall).
- Notify immigration within 14 days of changing employers.
- Renew before expiration -- apply 3 months before expiry at immigration (nyukan).

**Permanent Residency (eijuken)**
- General route: 10+ years in Japan, good conduct, financial stability, current visa of 3+ years.
- Highly Skilled Professional fast track: 70+ points = PR in 3 years; 80+ points = PR in 1 year. Points based on education, salary, age, Japanese ability, etc.
- Spouse route: 3+ years married to Japanese national AND 1+ year residing in Japan.
- Processing time: 6-12 months typically.
- Advantages over work visa: no job restrictions, no renewal needed, easier to get loans and rent apartments.

### Banking

**Opening a Bank Account**
- Major banks (MUFG, SMBC, Mizuho) typically require 6 months of residency.
- More accessible options: Japan Post Bank (Yucho Ginko) -- most foreigner-friendly, huge ATM network; Shinsei Bank/SBI Sumishin Net Bank -- English online banking, lower barriers; Sony Bank -- English interface, good for forex; Prestia (SMBC Trust) -- English service, higher minimums.
- Required documents: residence card, MyNumber notification or card, inkan (personal seal) or signature (Shinsei and some others accept signature), proof of address.
- 7-Eleven ATMs accept most international cards for cash withdrawal.

**International Transfers**
- Wise (formerly TransferWise): most popular among foreigners. Requires MyNumber for setup. Low fees, mid-market exchange rate. Transfer typically arrives in 1-2 business days.
- Bank wire transfers: expensive (2,500-6,000 yen per transfer plus unfavorable exchange rates).
- Reporting: banks automatically report transfers over 1M yen to tax authorities. You must self-report transfers over 30M yen.

### Housing

**Renting an Apartment**
- Unique upfront costs: key money (reikin, 0-2 months rent, non-refundable gift to landlord), security deposit (shikikin, 1-2 months, partially refundable), agent fee (chukai tesuryo, 1 month + tax), guarantor company fee (hoshonin kaisha, 0.5-1 month). Total upfront: typically 4-6 months rent.
- Search on: Suumo, Homes.co.jp, GaijinPot Apartments (English-friendly), or via real estate agents (fudosan-ya).
- Application process: submit income proof, employer letter, residence card copy. Guarantor company does a screening call (sometimes in Japanese).
- Lease: typically 2 years with automatic renewal (renewal fee of 1 month rent is common). Give 1-2 months notice to move out.
- After moving: update address at city hall within 14 days, set up utilities (electricity/gas/water).

**UR Housing (Urban Renaissance Agency)**
- Government-backed housing: NO key money, NO guarantor, NO renewal fees, NO agent fee.
- Eligibility: monthly income of 4x rent, OR savings of 100x monthly rent.
- Search on ur-net.go.jp. Apply in person at UR offices.
- Trade-offs: often older buildings, less central locations, limited availability in popular areas. But units are typically larger and well-maintained.

## WEB SEARCH

When the user asks about specific deadlines, office locations, phone numbers, current policy changes, or other time-sensitive information, use web search to verify the latest information. Tell the user when you are looking something up: "Let me check the latest information on that for you."

Do NOT guess about current deadlines, office hours, or specific phone numbers. Search instead.

## TONE AND BOUNDARIES

- Be warm, encouraging, and empathetic. Moving to a new country and dealing with bureaucracy in a foreign language is stressful.
- If you don't know something, say so honestly. Suggest where they might find the answer: their city hall, employer's HR department, the Immigration Services Agency website, or a professional advisor.
- Stay within your six topic domains. If asked about unrelated topics (travel recommendations, language learning, job hunting), acknowledge the question briefly and redirect: "That's a great question, but it's outside my area of expertise. I focus on tax, pension, healthcare, visas, banking, and housing. Is there anything in those areas I can help with?"
- This is general guidance, not professional legal or tax advice. Remind users of this when discussing complex tax situations, visa applications, or pension decisions.
```

## Connection Heartbeat (Built-in)

When your app connects, the agent automatically sends a **heartbeat** action to verify the data channel is working.
This is a protocol-level feature that works independently of any configured client actions.

### Heartbeat Message (Agent to App)
```json
{
  "type": "client_action",
  "action": "heartbeat",
  "payload": {
    "timestamp": 1708123456789,
    "agent_identity": "agent-xyz"
  }
}
```

### Heartbeat Acknowledgment (Optional)
Your app can optionally respond with `heartbeat_ack` to measure round-trip latency:
```json
{
  "type": "client_action",
  "action": "heartbeat_ack",
  "payload": { "timestamp": 1708123456789 }
}
```

### Why Use Heartbeat?
- **Verify Connectivity**: Confirm the data channel is working before relying on client actions
- **Measure Latency**: Round-trip time is logged when you send `heartbeat_ack`
- **Debug Issues**: If you don't receive a heartbeat, the data channel may not be properly connected

## Live Transcript (Built-in)

All Vocal Bridge agents automatically send a `send_transcript` event whenever the user speaks or the agent responds.
This is a built-in protocol-level feature — no configuration required.

### Transcript Message Format
```json
{
  "type": "client_action",
  "action": "send_transcript",
  "payload": {
    "role": "user",
    "text": "Hello, how are you?",
    "timestamp": 1708123456789
  }
}
```

### Subscribing to Transcript (JavaScript)
```javascript
const transcript = [];  // Stores conversation history

room.on(RoomEvent.DataReceived, (payload, participant, kind, topic) => {
  if (topic === 'client_actions') {
    const data = JSON.parse(new TextDecoder().decode(payload));
    if (data.type === 'client_action' && data.action === 'send_transcript') {
      const { role, text, timestamp } = data.payload;
      transcript.push({ role, text, timestamp });
      updateTranscriptUI(role, text);
    }
  }
});

function updateTranscriptUI(role, text) {
  const container = document.getElementById('transcript');
  const entry = document.createElement('div');
  entry.className = role === 'user' ? 'text-right text-blue-700' : 'text-left text-gray-800';
  entry.innerHTML = `<strong>${role === 'user' ? 'You' : 'Agent'}:</strong> ${text}`;
  container.appendChild(entry);
  container.scrollTop = container.scrollHeight;
}
```

### Subscribing to Transcript (React)
```tsx
import { useState, useEffect } from 'react';
import { RoomEvent } from 'livekit-client';

function useTranscript(room) {
  const [transcript, setTranscript] = useState([]);

  useEffect(() => {
    const handleData = (payload, participant, kind, topic) => {
      if (topic === 'client_actions') {
        const data = JSON.parse(new TextDecoder().decode(payload));
        if (data.type === 'client_action' && data.action === 'send_transcript') {
          setTranscript(prev => [...prev, data.payload]);
        }
      }
    };
    room.on(RoomEvent.DataReceived, handleData);
    return () => room.off(RoomEvent.DataReceived, handleData);
  }, [room]);

  return transcript;
}

// Usage: const transcript = useTranscript(room);
// Render: transcript.map(e => <div>{e.role}: {e.text}</div>)
```

### Subscribing to Transcript (Flutter)
```dart
listener.on<DataReceivedEvent>((event) {
  if (event.topic == 'client_actions') {
    final data = jsonDecode(utf8.decode(event.data));
    if (data['type'] == 'client_action' && data['action'] == 'send_transcript') {
      final role = data['payload']['role'];
      final text = data['payload']['text'];
      // Add to your transcript list and update UI
      setState(() => transcript.add({'role': role, 'text': text}));
    }
  }
});
```

## API Integration

### Authentication
Use API Key authentication. Get your API key from the agent's Developer section.

### Generate Access Token (Backend)
Call this endpoint from your backend server to get a LiveKit access token:

```bash
curl -X POST "http://vocalbridgeai.com/api/v1/token" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"participant_name": "User"}'
```

**Response:**
```json
{
  "livekit_url": "wss://tutor-j7bhwjbm.livekit.cloud",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "room_name": "room-abc123",
  "participant_identity": "api-client-xyz",
  "expires_in": 3600
}
```

## Implementation Steps

### 1. Backend: Token Endpoint
Create a backend endpoint that calls the Vocal Bridge API:

```javascript
// Node.js/Express example
app.get('/api/voice-token', async (req, res) => {
  const response = await fetch('http://vocalbridgeai.com/api/v1/token', {
    method: 'POST',
    headers: {
      'X-API-Key': process.env.VOCAL_BRIDGE_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ participant_name: req.user?.name || 'User' })
  });
  res.json(await response.json());
});
```

### 2. Frontend: Connect to Agent
Use the LiveKit SDK to connect:

```javascript
import { Room, RoomEvent, Track } from 'livekit-client';

const room = new Room();

// Handle agent audio
room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
  if (track.kind === Track.Kind.Audio) {
    const audioElement = track.attach();
    document.body.appendChild(audioElement);
  }
});

// Handle heartbeat, transcript, and client actions from agent
const transcript = [];  // Stores live conversation transcript
room.on(RoomEvent.DataReceived, (payload, participant, kind, topic) => {
  if (topic === 'client_actions') {
    const data = JSON.parse(new TextDecoder().decode(payload));
    if (data.type === 'client_action') {
      // Built-in heartbeat: verify data channel connectivity
      if (data.action === 'heartbeat') {
        console.log('Connection verified! Agent:', data.payload.agent_identity);
        // Optional: Send ack for round-trip latency measurement
        room.localParticipant.publishData(
          new TextEncoder().encode(JSON.stringify({
            type: 'client_action',
            action: 'heartbeat_ack',
            payload: { timestamp: data.payload.timestamp }
          })),
          { reliable: true, topic: 'client_actions' }
        );
        return;
      }
      // Built-in transcript: live conversation text
      if (data.action === 'send_transcript') {
        const { role, text, timestamp } = data.payload;
        transcript.push({ role, text, timestamp });
        console.log(`[${role}] ${text}`);
        // TODO: Update your transcript UI here
        return;
      }
      // Handle other agent actions
      handleAgentAction(data.action, data.payload);
    }
  }
});

function handleAgentAction(action, payload) {
  // Add your custom action handlers here
  console.log('Received action:', action, payload);
}

// Get token and connect
const { livekit_url, token } = await fetch('/api/voice-token').then(r => r.json());
await room.connect(livekit_url, token);

// Enable microphone
await room.localParticipant.setMicrophoneEnabled(true);
```

### 3. Flutter: Connect to Agent
For Flutter/Dart mobile apps, use the LiveKit Flutter SDK.
Use the same backend from Step 1 to get tokens, or call the Vocal Bridge API directly from a secure backend:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:livekit_client/livekit_client.dart';

class VoiceAgentService {
  Room? _room;
  EventsListener<RoomEvent>? _listener;

  // Option 1: Get token from YOUR backend (recommended)
  // Your backend should call Vocal Bridge API with your API key
  Future<Map<String, dynamic>> _getTokenFromBackend() async {
    final response = await http.get(
      Uri.parse('https://your-backend.com/api/voice-token'),
    );
    return jsonDecode(response.body);
  }

  // Option 2: Call Vocal Bridge API directly (for testing/prototyping)
  // WARNING: Never expose API keys in production mobile apps!
  Future<Map<String, dynamic>> _getTokenDirect(String apiKey) async {
    final response = await http.post(
      Uri.parse('http://vocalbridgeai.com/api/v1/token'),
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json',
      },
      body: jsonEncode({'participant_name': 'Mobile User'}),
    );
    return jsonDecode(response.body);
  }

  // Connect to the voice agent
  Future<void> connect() async {
    // Use _getTokenFromBackend() in production
    final tokenData = await _getTokenFromBackend();
    final livekitUrl = tokenData['livekit_url'] as String;
    final token = tokenData['token'] as String;

    _room = Room();

    // Listen for agent audio
    _listener = _room!.createListener();
    _listener!.on<TrackSubscribedEvent>((event) {
      if (event.track.kind == TrackType.AUDIO) {
        // Audio is automatically played by LiveKit SDK
        print('Agent audio track subscribed');
      }
    });

    // Connect to the room
    await _room!.connect(livekitUrl, token);

    // Enable microphone
    await _room!.localParticipant?.setMicrophoneEnabled(true);

    // Set up heartbeat and client action handlers
    _setupClientActionHandler();
  }

  final List<Map<String, dynamic>> transcript = [];  // Live conversation transcript

  // Handle heartbeat, transcript, and client actions from agent
  void _setupClientActionHandler() {
    _listener!.on<DataReceivedEvent>((event) {
      if (event.topic == 'client_actions') {
        final data = jsonDecode(utf8.decode(event.data));
        if (data['type'] == 'client_action') {
          // Built-in heartbeat: verify data channel connectivity
          if (data['action'] == 'heartbeat') {
            print('Connection verified! Agent: ${data["payload"]["agent_identity"]}');
            // Optional: Send ack for round-trip latency measurement
            _sendHeartbeatAck(data['payload']['timestamp']);
            return;
          }
          // Built-in transcript: live conversation text
          if (data['action'] == 'send_transcript') {
            transcript.add(data['payload']);
            print('[${data["payload"]["role"]}] ${data["payload"]["text"]}');
            // TODO: Update your transcript UI here
            return;
          }
          _handleAgentAction(data['action'], data['payload']);
        }
      }
    });
  }

  Future<void> _sendHeartbeatAck(int timestamp) async {
    final message = jsonEncode({
      'type': 'client_action',
      'action': 'heartbeat_ack',
      'payload': {'timestamp': timestamp},
    });
    await _room?.localParticipant?.publishData(
      utf8.encode(message),
      reliable: true,
      topic: 'client_actions',
    );
  }

  void _handleAgentAction(String action, Map<String, dynamic> payload) {
    // Add your custom action handlers here
    print('Received action: $action with payload: $payload');
  }

  // Disconnect from the agent
  Future<void> disconnect() async {
    await _room?.disconnect();
    _room = null;
  }
}
```

### 4. React: Connect to Agent
For React apps, use the LiveKit React SDK with hooks:

```tsx
// useVoiceAgent.ts
import { useState, useCallback, useEffect } from 'react';
import { Room, RoomEvent, Track } from 'livekit-client';

export function useVoiceAgent() {
  const [room] = useState(() => new Room());
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isMicEnabled, setIsMicEnabled] = useState(false);

  useEffect(() => {
    // Handle agent audio
    room.on(RoomEvent.TrackSubscribed, (track) => {
      if (track.kind === Track.Kind.Audio) {
        const el = track.attach();
        document.body.appendChild(el);
      }
    });
    room.on(RoomEvent.Connected, () => setIsConnected(true));
    room.on(RoomEvent.Disconnected, () => setIsConnected(false));
    return () => { room.disconnect(); };
  }, [room]);

  const connect = useCallback(async () => {
    setIsConnecting(true);
    try {
      // Get token from your backend
      const { livekit_url, token } = await fetch('/api/voice-token').then(r => r.json());
      await room.connect(livekit_url, token);
      await room.localParticipant.setMicrophoneEnabled(true);
      setIsMicEnabled(true);
    } finally {
      setIsConnecting(false);
    }
  }, [room]);

  const disconnect = useCallback(async () => {
    await room.disconnect();
  }, [room]);

  const toggleMic = useCallback(async () => {
    const enabled = !isMicEnabled;
    await room.localParticipant.setMicrophoneEnabled(enabled);
    setIsMicEnabled(enabled);
  }, [room, isMicEnabled]);

  return { isConnected, isConnecting, isMicEnabled, connect, disconnect, toggleMic };
}

// VoiceAgentButton.tsx
export function VoiceAgentButton() {
  const { isConnected, isConnecting, isMicEnabled, connect, disconnect, toggleMic } = useVoiceAgent();

  if (!isConnected) {
    return (
      <button onClick={connect} disabled={isConnecting}>
        {isConnecting ? 'Connecting...' : 'Start Voice Chat'}
      </button>
    );
  }

  return (
    <div>
      <button onClick={toggleMic}>{isMicEnabled ? 'Mute' : 'Unmute'}</button>
      <button onClick={disconnect}>End Call</button>
    </div>
  );
}
```

**React Heartbeat, Transcript & Client Actions:**
```tsx
// Add to useVoiceAgent hook
const [transcript, setTranscript] = useState<{role: string, text: string, timestamp: number}[]>([]);

// Handle heartbeat, transcript, and agent actions
useEffect(() => {
  const handleData = (payload: Uint8Array, participant: any, kind: any, topic?: string) => {
    if (topic === 'client_actions') {
      const data = JSON.parse(new TextDecoder().decode(payload));
      if (data.type === 'client_action') {
        // Built-in heartbeat: verify data channel connectivity
        if (data.action === 'heartbeat') {
          console.log('Connection verified! Agent:', data.payload.agent_identity);
          // Optional: Send ack for round-trip latency measurement
          room.localParticipant.publishData(
            new TextEncoder().encode(JSON.stringify({
              type: 'client_action',
              action: 'heartbeat_ack',
              payload: { timestamp: data.payload.timestamp }
            })),
            { reliable: true, topic: 'client_actions' }
          );
          return;
        }
        // Built-in transcript: live conversation text
        if (data.action === 'send_transcript') {
          setTranscript(prev => [...prev, data.payload]);
          return;
        }
        handleAgentAction(data.action, data.payload);
      }
    }
  };
  room.on(RoomEvent.DataReceived, handleData);
  return () => { room.off(RoomEvent.DataReceived, handleData); };
}, [room]);

function handleAgentAction(action: string, payload: any) {
  // Add your custom action handlers here
  console.log('Received action:', action, payload);
}
```

## Dependencies

**JavaScript/React:**
```bash
npm install livekit-client
# For React components:
npm install @livekit/components-react
```

**Flutter:**
```yaml
# Add to pubspec.yaml
dependencies:
  livekit_client: ^2.3.0
  http: ^1.2.0
```

**Python:**
```bash
pip install livekit requests
```

## Environment Variables
Add to your backend `.env` file:
```
VOCAL_BRIDGE_API_KEY=vb_your_api_key_here
```

## CLI for Agent Iteration

Use the Vocal Bridge CLI to iterate on your agent's prompt and review call logs.

### Installation
```bash
# Option 1: Install via pip (recommended)
pip install vocal-bridge

# Option 2: Download directly
curl -fsSL http://vocalbridgeai.com/cli/vb.py -o vb && chmod +x vb
```

### Authentication

Vocal Bridge supports two types of API keys:
- **Agent API keys**: Tied to a specific agent. Get one from your agent's detail page.
- **Account API keys**: Work across all your agents. Create one from the dashboard "API Keys" tab (Pilot subscribers only). After login, use `vb agent use` to select which agent to work with.

```bash
# Login with your API key (agent-scoped or account-scoped)
vb auth login

# For account keys, select an agent after login
vb agent use
```

### Commands
```bash
# Agent info and selection
vb agent                   # View current agent info
vb agent list              # List all agents
vb agent use               # Select agent (required for account keys)

# Review call logs
vb logs                    # List recent calls
vb logs --status failed    # Find failed calls
vb logs <session_id>       # View transcript
vb logs <session_id> --json  # Full details including tool calls
vb logs download <id>      # Download call recording

# View statistics
vb stats

# Update prompt
vb prompt show             # View current prompt
vb prompt edit             # Edit in $EDITOR
vb prompt set --file prompt.txt

# Manage agent configuration
vb config show             # View all agent settings
vb config options          # Discover valid values for settings
vb config set --style Chatty  # Change agent style
vb config edit             # Edit full config in $EDITOR

# Client actions, API tools, and AI Agent
vb config set --client-actions-file actions.json  # Set client actions
vb config set --api-tools-file tools.json         # Set HTTP API tools
vb config set --ai-agent-enabled true             # Enable AI Agent integration
vb config set --ai-agent-description '...'        # Set AI Agent description
vb config set --ai-agent-file config.json         # Set AI Agent config from file

# Real-time debug streaming (requires debug mode enabled)
vb debug                   # Stream events via WebSocket
vb debug --poll            # Use HTTP polling instead
```

### Real-Time Debug Streaming
Stream debug events in real-time while calls are active.
First, enable Debug Mode in your agent's settings.

```bash
vb debug
```

Events streamed include:
- User transcriptions (what the caller says)
- Agent responses (what your agent says)
- Tool calls and results
- Session start/end events
- Errors

### Iteration Workflow
1. Review call logs to understand user interactions: `vb logs`
2. Identify issues from failed calls: `vb logs --status failed`
3. View transcript of problematic calls: `vb logs <session_id>`
4. Stream live debug events during test calls: `vb debug`
5. Use `vb config options` to discover valid settings before making changes
6. Update the prompt or config to address issues: `vb prompt edit` / `vb config set`
7. Test by making calls to your agent
8. Check statistics to verify improvement: `vb stats`

## Claude Code Plugin

If you're using Claude Code, install the Vocal Bridge plugin for native slash commands:

### Installation
```
/plugin marketplace add vocalbridgeai/vocal-bridge-marketplace
/plugin install vocal-bridge@vocal-bridge
```

### Getting Started
```
/vocal-bridge:login vb_your_api_key
/vocal-bridge:help
```

### Available Commands
| Command | Description |
|---------|-------------|
| `/vocal-bridge:login` | Authenticate with API key |
| `/vocal-bridge:status` | Check authentication status |
| `/vocal-bridge:agent` | Show agent information |
| `/vocal-bridge:create` | Create and deploy a new agent (Pilot only) |
| `/vocal-bridge:logs` | View call logs and transcripts |
| `/vocal-bridge:download` | Download call recording |
| `/vocal-bridge:stats` | Show call statistics |
| `/vocal-bridge:prompt` | View or update system prompt |
| `/vocal-bridge:config` | Manage all agent settings |
| `/vocal-bridge:debug` | Stream real-time debug events |

The plugin auto-installs the CLI when needed. Claude can automatically use these commands when you ask about your agent.

## Security Notes
- Never expose the API key in frontend code
- Always generate tokens from your backend
- Tokens expire after 1 hour; request new tokens as needed