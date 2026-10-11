# Home Credit — AI Voice Agent for Loan Against Property (LAP) Qualification

A voice agent, configured with a prompt, that calls existing customers, presents a LAP offer of up to ₹75 lakh, runs a seven-point preliminary eligibility check, and ends each call with one outcome: a senior-loan-expert callback message, a loan-transfer referral, a busy-customer callback request, a disqualification, or a polite close. It never transfers calls. Built for Retell AI.

## Status

| Item | Status |
|---|---|
| System prompt | v0.3 for Retell AI (remediated for single-turn exit & industrial disqualification) |
| Voice platform | Retell AI single prompt agent prototype |
| Platform validation checks (PV-01 to PV-06) | Not run |
| Test calls | Partially tested: 9 mapped (7 Pass, 2 Partial); 2 exploratory (1 Partial, 1 initial Fail verified Pass on retest) |
| Automated business rule tests | 27 automated tests passing locally (`tests/test_business_rules.py`) |
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
evidence/                                  Recordings, transcripts, call logs, links
scripts/check_project.py                   Pre-submission checks
```

There's no custom backend or web app. The voice platform provides telephony, speech-to-text, text-to-speech, recordings, and transcripts.

## How it works

1. **Verify** that the person on the line is `customer_name` before mentioning the offer.
2. **Check availability.** If the customer is busy, the agent takes a preferred callback time and ends the call.
3. **Present the offer** (up to ₹75 lakh).
4. **Collect the seven data points**: property type, ownership, original documents, loan amount, occupation and income mode, property value, tenure. Answers given out of order are captured, and nothing is asked twice.
5. **Exit early** on a confirmed disqualifier, a loan-transfer trigger, or a refusal to continue within the ₹75 lakh cap.
6. **Summarise, confirm, and close.** Once all seven data points pass, the agent says a senior loan expert will call back shortly with the exact rates, then ends the call. There is no live transfer, and nothing is actually scheduled: no callback integration exists.

See [docs/conversation-flow.md](docs/conversation-flow.md) for details.

## Setup

Step-by-step Retell instructions, with links to the official docs, are in **[docs/platform-setup.md](docs/platform-setup.md)**. In short:

1. Create a Retell **Single prompt** agent and paste in the prompt between the markers in [prompts/home_credit_lap_system_prompt.md](prompts/home_credit_lap_system_prompt.md).
2. Set the model, a voice whose gender matches `agent_gender`, and a language that matches `language_to_speak`.
3. Add the **End Call** tool only. Don't add transfer tools.
4. Set default dynamic variables (fictional) and the post-call extraction fields.
5. Run the platform checks PV-01 to PV-06, then the scenarios in [tests/test_cases.md](tests/test_cases.md): text tests first, then web calls for evidence.
6. Record the real results in [tests/test_results.md](tests/test_results.md) and save the exported evidence in [evidence/](evidence/README.md).

Never buy a phone number, call real customers, or run an outbound campaign for this assignment.

### Check before submitting
```
python3 scripts/check_project.py              # offline checks
python3 scripts/check_project.py --check-urls # also checks that every external link responds
```
The script checks that:
- the required files exist;
- the prompt uses exactly the expected Retell variables;
- removed placeholders and transfer tools are gone from the prompt;
- local markdown links resolve.

It also scans for keys, phone numbers, and email addresses.

## Security

- Keep API keys in `.env` (git-ignored) or in the platform dashboard. Never put them in this repo.
- Use fictional customer data only. Redact phone numbers from logs before adding them to `evidence/`.
