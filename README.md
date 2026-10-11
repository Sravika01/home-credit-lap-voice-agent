# Home Credit — AI Voice Agent for Loan Against Property (LAP) Qualification

A voice agent, configured with a prompt, that calls existing customers, presents a LAP offer of up to ₹75 lakh, runs a seven-point preliminary eligibility check, and ends each call with one outcome: a senior-loan-expert callback message, a loan-transfer referral, a busy-customer callback request, a disqualification, or a polite close. It never transfers calls. Built for Retell AI.

## Status

| Item | Status |
|---|---|
| System prompt | v0.3 for Retell AI (remediated for single-turn exit & industrial disqualification) |
| Voice platform | Retell AI single prompt agent prototype (no custom telephony backend) |
| Web eligibility demo | Standalone Flask web prototype (`app.py`, `Procfile`, `requirements.txt`) |
| Platform validation checks (PV-01 to PV-06) | Not run |
| Test calls | Partially tested: 9 mapped (7 Pass, 2 Partial); 2 exploratory (1 Partial, 1 initial Fail verified Pass on retest) |
| Automated tests | 38 automated tests passing locally (`tests/test_business_rules.py`, `tests/test_app.py`) |
| Evidence | Transcript screenshots saved in `evidence/transcripts/` (`retell_industrial_property_test.png` failure, `retell_industrial_property_pass.png` pass) |

## Project structure

```
prompts/home_credit_lap_system_prompt.md   Final system prompt (paste between the markers)
docs/requirements.md                       Eligibility rules, runtime variables, outcomes, interpretations
docs/conversation-flow.md                  Flow diagram, state model, transfer vs. callback
docs/platform-setup.md                     Retell setup steps, variable mapping, unverified behaviour
docs/submission_report.md                  Submission report
tests/test_cases.md                        6 platform checks + 27 scenarios + 2 exploratory scenarios
tests/test_results.md                      Actual results (7 pass, 2 partial mapped; 1 partial, 1 pass retest exploratory)
tests/test_business_rules.py               27 automated business rule and prompt static integrity tests
tests/test_app.py                          11 automated HTTP and validation tests for the Flask demo
app.py                                     Standalone Flask demo for testing LAP eligibility rules in a browser
file.py                                    Python business rules and qualification evaluator engine
requirements.txt                           Python dependencies for web demo deployment (Flask, gunicorn)
Procfile                                   WSGI process entrypoint for cloud hosting
evidence/                                  Recordings, transcripts, call logs, links
scripts/check_project.py                   Pre-submission checks
```

## System Architecture: Voice Agent vs. Web Demo

This repository contains two distinct, uncoupled components:

1. **Retell AI Voice Agent (Primary Prototype):**
   - The voice agent runs entirely within the Retell AI managed platform.
   - Retell handles telephony, speech-to-text (STT), text-to-speech (TTS), LLM prompt execution, recordings, and transcripts.
   - Logic is governed by the system prompt in `prompts/home_credit_lap_system_prompt.md`.
   - There is no direct integration between the Retell voice agent and any external CRM, calendar, or web backend.

2. **Flask Eligibility Demo (`app.py` - Auxiliary Browser Prototype):**
   - A lightweight web application providing an interactive 7-field form to evaluate preliminary LAP criteria in a browser.
   - Built to demonstrate and test the deterministic business rules independently of voice telephony.
   - Not connected to Retell AI or Home Credit core banking systems.

## How it works (Voice Flow)

1. **Verify** that the person on the line is `customer_name` before mentioning the offer.
2. **Check availability.** If the customer is busy, the agent takes a preferred callback time and ends the call.
3. **Present the offer** (up to ₹75 lakh).
4. **Collect the seven data points**: property type, ownership, original documents, loan amount, occupation and income mode, property value, tenure. Answers given out of order are captured, and nothing is asked twice.
5. **Exit early** on a confirmed disqualifier, a loan-transfer trigger, or a refusal to continue within the ₹75 lakh cap.
6. **Summarise, confirm, and close.** Once all seven data points pass, the agent says a senior loan expert will call back shortly with the exact rates, then ends the call. There is no live transfer, and nothing is actually scheduled: no callback integration exists.

See [docs/conversation-flow.md](docs/conversation-flow.md) for details.

## Retell AI Setup

Step-by-step Retell instructions, with links to the official docs, are in **[docs/platform-setup.md](docs/platform-setup.md)**. In short:

1. Create a Retell **Single prompt** agent and paste in the prompt between the markers in [prompts/home_credit_lap_system_prompt.md](prompts/home_credit_lap_system_prompt.md).
2. Set the model, a voice whose gender matches `agent_gender`, and a language that matches `language_to_speak`.
3. Add the **End Call** tool only. Don't add transfer tools.
4. Set default dynamic variables (fictional) and the post-call extraction fields.
5. Run the platform checks PV-01 to PV-06, then the scenarios in [tests/test_cases.md](tests/test_cases.md): text tests first, then web calls for evidence.
6. Record the real results in [tests/test_results.md](tests/test_results.md) and save the exported evidence in [evidence/](evidence/README.md).

Never buy a phone number, call real customers, or run an outbound campaign for this assignment.

## Flask Web Demo & Deployment

### Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python3 app.py
```

Open `http://localhost:5000` in your browser. The app also supports running via Gunicorn:
```bash
gunicorn app:app
```

### Cloud Deployment (Render / Railway)

The Flask app is prepared for 1-click cloud hosting via `requirements.txt` and `Procfile`.

#### Deploying on Render (Free Tier)
1. Push your repository to GitHub: `https://github.com/Sravika01/home-credit-lap-voice-agent`.
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New + > Web Service**.
3. Connect your GitHub repository `Sravika01/home-credit-lap-voice-agent`.
4. Configure service settings:
   - **Name:** `home-credit-lap-demo` (or desired name)
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Click **Create Web Service**. Render will build and deploy the app, providing a public URL (e.g. `https://home-credit-lap-demo.onrender.com`).

#### Deploying on Railway
1. Go to [Railway Dashboard](https://railway.app/) and select **New Project > Deploy from GitHub repo**.
2. Select `Sravika01/home-credit-lap-voice-agent`.
3. Railway automatically detects `requirements.txt` and `Procfile` and deploys the service.
4. Go to **Settings > Domains** to generate a public domain URL.

## Automated Testing & Verification

Run the entire automated test suite (38 tests) and project static checker:

```bash
# Run all automated tests (business rules + Flask web app)
python3 -m unittest discover tests -v

# Run the business rules evaluator self-test
python3 file.py

# Run offline project integrity and secret checks
python3 scripts/check_project.py

# Optional: request and verify all external documentation URLs
python3 scripts/check_project.py --check-urls
```

The checker verifies that:
- all required documentation and prompt files exist;
- the prompt uses exactly the expected Retell variables;
- forbidden placeholders and live transfer tools are absent from the prompt;
- local markdown links resolve;
- no API keys, private tokens, phone numbers, or email addresses are exposed.

## Security

- Keep API keys in `.env` (git-ignored) or in the platform dashboard. Never commit secrets to the repository.
- Use fictional customer data only. Redact phone numbers and personal details from logs before adding them to `evidence/`.

