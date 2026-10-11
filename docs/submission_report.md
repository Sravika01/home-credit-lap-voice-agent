# Submission Report — Home Credit LAP AI Voice Agent

> **Status: PROTOTYPE CONFIGURED — PARTIALLY TESTED.** The Retell AI agent is configured and prompt v0.3 has been tested in conversational scenarios. See `../tests/test_results.md` for recorded outcomes. Call IDs, dates, and saved evidence links were not recorded in that report.

## 1. What the agent does

An outbound AI voice agent for existing Home Credit customers. It verifies the customer's identity, presents a Loan Against Property offer of up to ₹75 lakh, collects seven eligibility data points, and ends every call with exactly one outcome:
- a qualified close: the customer is told a senior loan expert will call back shortly with exact rates;
- a loan-transfer referral;
- a callback request;
- a disqualification;
- a polite close.

The agent never transfers a call.

- Prompt: [prompts/home_credit_lap_system_prompt.md](../prompts/home_credit_lap_system_prompt.md)
- Rules and interpretations: [requirements.md](requirements.md)
- Flow and state: [conversation-flow.md](conversation-flow.md)
- Platform setup: [platform-setup.md](platform-setup.md)

## 2. Architecture

```
Customer (web test call) ⇄ Retell AI (STT + TTS + call transcript) ⇄ LLM with system prompt v0.3
                                   │
                                   ├─ tool: end_call (only)
                                   ├─ dynamic variables: 6 custom + built-in current_time/current_calendar (Asia/Kolkata)
                                   └─ post-call extraction: call_outcome, callback time, 7 data points
```

There's no custom backend. All logic is in the system prompt, and Retell handles speech, recordings, and transcripts.

- Platform: Retell AI, single prompt agent (configured)
- LLM / voice / STT: Not recorded in the test report

## 3. The seven eligibility checks

| # | Check | Pass | Fail |
|---|---|---|---|
| 1 | Property type | Residential / commercial | Agricultural / industrial |
| 2 | Ownership | Sole / joint | Not an owner (interpretation I-3) |
| 3 | Original documents | Available | Unavailable; with a lender → transfer referral |
| 4 | Loan amount | ≤ ₹75 lakh | > ₹75 lakh → cap sub-flow |
| 5 | Occupation and income | Salaried / self-employed, bank-credited | Cash income |
| 6 | Property value | Any estimate (no threshold) | — |
| 7 | Tenure | 3–15 years, inclusive | Outside the range |

Ambiguous answers get one clarifying question. Disqualifiers that could have been misheard are repeated back once before the agent acts on them.

## 4. Key prompt-engineering decisions

- **Stateless slot rebuild:** every turn, the model rebuilds a checklist from the full transcript. This handles out-of-order answers, several answers in one sentence, and corrections without external memory.
- **Default question order with skipping:** the agent always asks for the first missing data point, so it never asks again for one already answered.
- **Layered qualification guard:** a hard rule, an explicit all-of qualification gate, and a read-back summary before the qualified close.
- **Inform-and-end instead of transfer:** as the brief requires, the agent tells a qualified customer that a senior loan expert will call back shortly with exact rates, and tells loan-transfer cases that it is referring them to the loan-transfer specialist. Then it ends the call. It never names a day or time, or claims anything was scheduled or received, because no scheduler or CRM exists.
- **Immediate exit on confirmed disqualification:** no remaining questions are asked.
- **No invented facts:** rates are blocked even when the RAG context contains them; there is no approval wording; callbacks are only ever "noted", never "confirmed"; no extra thresholds (such as LTV or minimum value) are made up.
- **Voice-first style:** short turns, one question at a time, amounts spoken in words, grammatical gender fixed to `agent_gender`.
- **Prompt-injection guard:** the RAG content and customer speech are treated as data, not instructions.

## 5. How specific behaviours are handled

| Behaviour | Mechanism |
|---|---|
| Out-of-order answers | Checklist rebuilt from the full transcript every turn; the latest clear answer wins |
| Disqualification | Confirm once if ambiguous → explain the criterion → end, no expert-callback message |
| Transfer referral | Existing property loan / balance transfer / refinance / EMI reduction / originals held by a lender → "I'm referring you to our loan-transfer specialist" → end the call (no transfer; nothing is actually sent) |
| Busy customer | Ask for a time, resolve relative dates from `current_date`, repeat back, "noted" only, end |
| Loan amount cap | Explain ₹75 lakh max → continue within it, or `declined_loan_cap` |
| Premature qualified close | Gate + hard rule + summary confirmation; an early "put me through" is declined politely |

## 6a. Assignment compliance

"In prompt" means the behaviour is written into prompt v0.3. The last column reflects observed test conversations recorded in [tests/test_results.md](../tests/test_results.md). Untested requirements remain marked Not run.

| Assignment requirement | In prompt | Tests | Verified by a call |
|---|---|---|---|
| LAP offer up to ₹75 lakh to existing customers | Step 3 | TC-01 | Pass (observed eligible scenario in TC-01) |
| Verify identity before disclosing the offer | Hard rule 1, Step 1 | TC-03, TC-27 | Not run |
| Busy → ask for preferred callback time, end the call | Busy customer | TC-04, TC-05, PV-02 | Pass (observed in TC-04; TC-05 and PV-02 not run) |
| Existing property loan / transfer / refinance / EMI reduction → loan-transfer specialist referral, end the call | Loan-transfer referral | TC-13, TC-14, TC-15, TC-16 | Pass (observed in TC-13; TC-14–TC-16 not run) |
| Property type: residential / commercial; agricultural, industrial disqualify | Data point 1 | TC-06, TC-19, TC-20, EX-02 | Agricultural disqualified (TC-06 Pass); Industrial test initially failed (EX-02 Fail), retested and verified Pass on live Retell agent |
| Ownership: sole / joint | Data point 2 | TC-01, TC-02 | Pass (sole observed in TC-01, joint observed in TC-02) |
| Original documents required | Data point 3 | TC-07, TC-15 | Partial: TC-07 disqualified correctly, but had repeated closing messages (prompt remediated) |
| Loan amount max ₹75 lakh; explain the cap and offer to continue within it | Data point 4, Loan amount cap | TC-11, TC-12, TC-26 | Partial coverage (cap explanation observed in TC-11; TC-12, TC-26 not run) |
| Salaried / self-employed, bank income; cash disqualifies | Data point 5 | TC-08, TC-02 | Pass (cash disqualification observed in TC-08; self-employed in TC-02) |
| Collect property value; no invented threshold | Data point 6, hard rule 5 | TC-21 | Not run |
| Tenure 3–15 years inclusive; outside the range disqualifies | Data point 7 | TC-09, TC-10 | Partial coverage (20-year disqualification observed in TC-09; TC-10 boundaries not run) |
| Remember out-of-order answers; don't repeat questions | Tracking section, hard rule 8 | TC-02, TC-19, PV-01 | Pass (observed out-of-order capture in TC-02; TC-19, PV-01 not run) |
| End immediately after a confirmed disqualifier | Disqualification | TC-06 to TC-09 | Pass (immediate disqualification observed in TC-06, TC-08, TC-09; TC-07 had goodbye repetition) |
| No qualified close before all 7 pass | Qualification gate, hard rule 6 | TC-18, TC-21 | Not run |
| Qualified → "senior loan expert will call back shortly with exact rates" | Step 6 | TC-01, TC-22 | Observed in TC-01; exact timing is not integrated |
| Never invent rates, approvals, or callback confirmations | Hard rules 2–4 | TC-17, TC-22 | Not run |
| Use configured language and agent gender | Language and voice style | TC-23 | Not run |
| All runtime variables used | Call context + [platform-setup.md](platform-setup.md#runtime-variable-mapping) | PV-02, PV-03 | Not run |

## 6. Testing

- Test plan: [tests/test_cases.md](../tests/test_cases.md): 6 platform validation checks (PV-01 to PV-06), 27 core scenarios (TC-01 to TC-27), and 2 exploratory scenarios (EX-01 DNC, EX-02 industrial property).
- Results: [tests/test_results.md](../tests/test_results.md)
- Method: Retell Test LLM / Test Audio. Observed live results: 9 mapped scenarios (7 Pass, 2 Partial), plus 2 exploratory tests (EX-01 Partial; EX-02 initial Fail, verified retest Pass).
- Observed issues, remediations, and retests:
  1. Repeated goodbye messages after unavailable-documents disqualification (TC-07): Remedied in prompt v0.3 by explicitly enforcing single-turn `end_call` execution and adding few-shot examples.
  2. Industrial property disqualification (EX-02): Initial run on live Retell failed as the agent continued asking subsequent questions (screenshot evidence in [retell_industrial_property_test.png](../evidence/transcripts/retell_industrial_property_test.png)). Remedied by explicitly categorizing industrial property under Disqualifies in prompt v0.3, updating business logic in `file.py`, and adding automated tests. Applied to Retell agent `agent_e86cc8540577ceb0bfaba483bc` (GPT 5.6 Terra, Cimo voice) and retested successfully in Test Audio (screenshot evidence in [retell_industrial_property_pass.png](../evidence/transcripts/retell_industrial_property_pass.png)); call ended immediately upon industrial answer with `end_call`. Retest status: **Pass**.

## 7. Evidence

- Verified Test Audio initial failure screenshot: [retell_industrial_property_test.png](../evidence/transcripts/retell_industrial_property_test.png) documenting the industrial property failure (EX-02 Fail).
- Verified Test Audio retest pass screenshot: [retell_industrial_property_pass.png](../evidence/transcripts/retell_industrial_property_pass.png) documenting the successful live Retell Test Audio retest (EX-02 Pass).
- Saved audio recordings, call IDs, and public export links are not yet recorded in the repository. Do not claim audio or logs are attached when they are not.

## 8. Known limitations and integrations not configured

- Identity check is name confirmation only (I-1). There is no OTP or knowledge-based verification.
- **The senior-expert callback and loan-transfer referral are conversation only.** The agent says them because the assignment requires it, but no callback is scheduled and no referral is sent. There's no CRM, scheduler, Cal.com, or webhook integration. At most, the outcome is recorded inside Retell post-call extraction (planned; unverified for web calls until PV-05). See [requirements.md](requirements.md#conversation-behaviour-vs-system-reality).
- Busy-customer callback times are recorded only in the transcript and post-call extraction.
- No live call transfer is configured. This is by design: the brief requires a callback, and Retell transfers don't work on web calls.
- No phone number, telephony, KYC, or outbound or batch calling. Testing used Retell web calls only.
- No Knowledge Base. `additional_context_from_rag` is a manually set variable.
- Platform behaviours U-1 to U-7 are not all verified. See `../tests/test_results.md`; PV-01 to PV-06 remain Not run in the current report.
- No real customer was called. Testing used fictional data only.
- Eligibility outcomes depend on the LLM following the prompt. There is no deterministic rules engine, so test results reflect the specific model and configuration used.
- Interpretations I-1 to I-11 in [requirements.md](requirements.md) have not been confirmed by the assignment owner.
- The unavailable-documents test produced repeated goodbye messages after the end-call action.

## 9. Security and privacy

- No API keys or secrets are in the repository (`.env` is git-ignored; checked with `scripts/check_project.py`). The Retell API key isn't needed, because everything is done in the dashboard.
- All test identities are fictional. Phone numbers are redacted from logs.
## Final Project Status

**Project:** Home Credit LAP AI Voice Agent  
**Platform:** Retell AI  
**Status:** Prototype configured and partially tested

### Completed
- Configured the agent prompt, dynamic variables, and post-call extraction fields.
- Tested the eligible-customer conversation.
- Tested agricultural property, cash income, excessive tenure, unavailable documents, and joint ownership.
- Tested a loan amount above ₹75 lakh.
- Tested busy-customer callback handling.
- Tested loan-transfer and do-not-call requests.
- Confirmed that the audio test works.

### Known Limitations
- Callback scheduling, specialist referrals, and do-not-call list updates have not been verified through real integrations.
- The missing-documents test showed repeated closing messages that may need improvement.
- Many test cases remain untested. Call IDs, dates, and saved evidence links are not recorded in the current test report.

### Conclusion
The Retell AI prototype demonstrates the main conversation flow and several key eligibility rules. It is not yet a fully integrated production system.
