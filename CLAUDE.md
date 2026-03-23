# Tokyo Vocal Bridge Hackathon

## Overview
Vocal Bridge competition — pair programming via Telegram + Claude Code.

## Repo
https://github.com/deesylove/TokyoVocalBridgeHackathon

## Stack
- **Vocal Bridge** — hosted voice agent platform (WebRTC via LiveKit)
- **LiveKit SDK** — `livekit-client` for browser, `@livekit/components-react` for React
- **Next.js or FastAPI** — backend to proxy token requests (keeps API key server-side)
- **React** — frontend with voice widget + transcript UI

## Vocal Bridge Architecture
Token flow: Backend calls `POST vocalbridgeai.com/api/v1/token` with `X-API-Key` header → gets `{livekit_url, token, room_name}` → client connects via LiveKit SDK → mic enabled → user talks to agent.

### Agent Extension Points
1. **MCP Tools** — agent calls external MCP server URL for tools (Zapier or custom)
2. **Custom HTTP API Tools** — agent calls REST endpoints you define (with auth)
3. **Client Actions** — bidirectional data channel via LiveKit (agent↔app events)
4. **AI Agent Integration** — delegate questions to your own AI via `query_agent`/`agent_response` on data channel
5. **Post-Processing** — after-call automation (summarize, CRM update, email)
6. **Live Transcript** — built-in `send_transcript` events on data channel (automatic)

### CLI
`pip install vocal-bridge` → `vb auth login`, `vb agent create`, `vb prompt set`, `vb config set`, `vb call`, `vb debug`

## Branch Strategy
- Main branch: `main`
- Feature branches: `feat/<name>`

## Dev Workflow
- Telegram group chat for pair programming (2 users)
- Test before commit
- Keep it simple — hackathon pace
