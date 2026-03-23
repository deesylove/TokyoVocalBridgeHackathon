# Japan Life Navigator - Vocal Bridge Voice Agent

## Context
Foreign professionals in Japan struggle with navigating tax, pension, healthcare, visa, banking, and housing systems. We're building a voice agent using Vocal Bridge that guides users step-by-step through these processes in simple English, personalizing advice based on their visa type, employment, and situation.

## Project Structure
```
tokyo_vocal_bridge_hackathon/
├── .env                    # VOCAL_BRIDGE_API_KEY=vb_...
├── prompt.txt              # System prompt (core agent behavior)
├── model_settings.json     # Voice, STT, temperature config
├── knowledge/              # Reference docs & step-by-step guides
│   ├── tax/
│   │   ├── income-tax-guide.md
│   │   ├── residence-tax-guide.md
│   │   └── tax-return-filing.md
│   ├── pension/
│   │   ├── pension-system-overview.md
│   │   └── lump-sum-withdrawal.md
│   ├── healthcare/
│   │   ├── health-insurance-guide.md
│   │   └── finding-doctors.md
│   ├── visa/
│   │   ├── first-steps-arrival.md
│   │   ├── residence-card-guide.md
│   │   └── path-to-permanent-residency.md
│   ├── banking/
│   │   ├── opening-bank-account.md
│   │   └── international-transfers.md
│   └── housing/
│       ├── renting-in-japan.md
│       └── ur-housing-guide.md
├── venv/                   # Python 3.13 venv (vocal-bridge 0.14.0 installed)
```

No API tools, MCP servers, or client actions needed for MVP -- built-in web search covers real-time lookups.

## Knowledge Base Strategy
The `knowledge/` folder serves two purposes:
1. **Source of truth for the prompt** -- We distill key facts and step-by-step procedures from these guides into the system prompt. When we update a guide, we update the corresponding prompt section.
2. **Iteration reference** -- During testing, when the agent gets something wrong or misses a step, we update the relevant guide first, then reflect the fix in the prompt.

Each guide follows a consistent format:
- **Overview**: What this is and why it matters
- **Who needs this**: Which visa/employment types this applies to
- **Step-by-step process**: Numbered steps with required documents, which office to visit, forms to fill
- **Common pitfalls**: Mistakes foreigners commonly make
- **Key deadlines**: Dates and consequences of missing them
- **Useful phrases**: Japanese terms with pronunciation and meaning

## Step 1: Sign Up & Authenticate
1. Sign up at vocalbridgeai.com and get API key (starts with `vb_`)
2. Add to `.env`: `VOCAL_BRIDGE_API_KEY=vb_...`
3. Run: `source venv/bin/activate && vb auth login`

## Step 2: Create Knowledge Base (`knowledge/`)
Write step-by-step guides for each of the 6 domains. These are our source material -- we'll distill them into the prompt. Priority order:
1. `visa/first-steps-arrival.md` -- Most common starting point for users
2. `tax/income-tax-guide.md` & `tax/tax-return-filing.md` -- Highest complexity
3. `healthcare/health-insurance-guide.md` -- Essential early need
4. `pension/pension-system-overview.md` -- Often confusing
5. `banking/opening-bank-account.md` -- Early practical need
6. `housing/renting-in-japan.md` -- Common pain point
7. Remaining guides as time allows

## Step 3: Create `prompt.txt`
Distill the knowledge base guides into a structured system prompt with these sections:
- **Identity**: "Japan Life Navigator" -- friendly guide for foreign professionals in Japan
- **Conversation approach**: Always ask clarifying questions first (visa type, employment type, city, how long in Japan), personalize advice, use simple language, give step-by-step instructions, warn about deadlines, recommend professionals for complex cases
- **Domain knowledge** (6 areas):
  - **Tax**: Income tax vs residence tax, year-end adjustment vs final return, MyNumber, common deductions for foreigners, e-Tax
  - **Pension**: National Pension vs Employees' Pension, lump-sum withdrawal, totalization agreements
  - **Healthcare**: NHI vs company insurance (shakai hoken), finding English-speaking doctors, prescriptions
  - **Visa/Residency**: Residence card, city hall registration, status changes, path to PR
  - **Banking**: 6-month residency requirement, foreigner-friendly banks, Wise transfers, MyNumber
  - **Housing**: Key money, deposit, guarantor companies, UR housing, foreigner-friendly agencies
- **Web search guidance**: Use for current deadlines, office locations, policy changes; tell user when looking things up
- **Tone**: Warm, empathetic, honest about unknowns; redirect off-topic questions

## Step 4: Create `model_settings.json`
```json
{
  "stt_model": "nova-3",
  "tts_voice": "nova",
  "temperature": 0.7
}
```
- **nova-3**: Best STT accuracy for Japanese term recognition
- **nova voice**: Warm, approachable -- right for a supportive guide
- **0.7 temperature**: Natural conversation while keeping facts accurate

## Step 5: Create & Deploy Agent
```bash
vb agent create \
  --name "Japan Life Navigator" \
  --style Chatty \
  --prompt-file prompt.txt \
  --greeting "Hi! I'm Japan Life Navigator, your guide to navigating life in Japan. I can help with taxes, pension, healthcare, visas, banking, and housing. To give you the best advice, it helps to know a bit about your situation -- like your visa type and whether you work for a Japanese company. What can I help you with today?" \
  --deploy-targets web \
  --background-enabled true \
  --web-search-enabled true \
  --debug-mode true \
  --model-settings-file model_settings.json
```

## Step 6: Verify
```bash
vb config show        # Confirm all settings
vb agent              # Check deployment status
```

## Step 7: Test & Iterate
Run `vb debug` in one terminal, open the web agent in another. Test scenarios:
1. "I just arrived in Japan on a work visa. What do I need to do first?"
2. "I'm a freelancer. Do I need to file a tax return?"
3. "How do I sign up for health insurance?"
4. "I want to open a bank account but I've only been here two weeks"
5. "My visa expires in two months. What are my options?"
6. "I'm looking for an apartment. What is key money?"

Watch debug output for: STT accuracy, missing clarifying questions, overly long responses, web search trigger behavior.

**Iterate fast with**: `vb prompt edit` or `vb prompt set -f prompt.txt`
**Swap voices with**: `vb config set --model-settings-file model_settings.json`

## Key Decisions
- **Chatty style** for warm, conversational tone
- **Web only** deployment (free tier, good for hackathon)
- **No external APIs** for MVP -- web search handles real-time info needs
- **Debug mode on** for development iteration
- **Professional disclaimer** baked into prompt -- not a substitute for legal/tax advice
