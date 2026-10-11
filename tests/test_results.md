# Test Results

> **Status: PARTIALLY TESTED.** The results below reflect observed Retell test conversations. Dates, call IDs, and evidence links were not recorded here; add them only when available.

## Test run details

| Field | Value |
|---|---|
| Platform | Retell AI (agent configured) |
| Agent ID / version | Not recorded |
| Prompt version | v0.3 |
| LLM / voice / STT used | Not recorded |
| Test method | Retell Test LLM / Test Audio; exact method per scenario not recorded |
| Tester | Project owner |
| Date(s) | Not recorded |

## Results

Status values: `Not run` · `Pass` · `Fail` · `Partial` (passed with issues — describe them in the notes).

| Test | Date | Call ID | Evidence | Observed outcome | Status | Notes |
|---|---|---|---|---|---|---|
| PV-01 | | | | | Not run | |
| PV-02 | | | | | Not run | |
| PV-03 | | | | | Not run | |
| PV-04 | | | | | Not run | |
| PV-05 | | | | | Not run | |
| PV-06 | | | | | Not run | |
| TC-01 | Not recorded | Not recorded | Not saved / not recorded | Eligible customer completed all checks and received the senior-expert callback message. | Pass | Eligible customer completed all checks and received the senior-expert callback message. |
| TC-02 | Not recorded | Not recorded | Not saved / not recorded | Joint ownership was remembered and the agent continued the eligibility flow. | Pass | Joint ownership was remembered and the agent continued the eligibility flow. |
| TC-03 | | | | | Not run | |
| TC-04 | Not recorded | Not recorded | Not saved / not recorded | Busy customer requested a callback; preferred time was captured conversationally. No scheduling integration. | Pass | Busy customer requested a callback; preferred time was captured conversationally. No scheduling integration. |
| TC-05 | | | | | Not run | |
| TC-06 | Not recorded | Not recorded | Not saved / not recorded | Agricultural property was disqualified immediately. | Pass | Agricultural property was disqualified immediately. |
| TC-07 | Not recorded | Not recorded | Not saved / not recorded | Unavailable original documents triggered disqualification, but repeated goodbye messages followed end_call. | Partial | Unavailable original documents triggered disqualification, but repeated goodbye messages followed end_call. |
| TC-08 | Not recorded | Not recorded | Not saved / not recorded | Cash income triggered disqualification. | Pass | Cash income triggered disqualification. |
| TC-09 | Not recorded | Not recorded | Not saved / not recorded | The agent remembered the 20-year tenure and disqualified it as outside the allowed range. | Pass | The agent remembered the 20-year tenure and disqualified it as outside the allowed range. |
| TC-10a | | | | | Not run | |
| TC-10b | | | | | Not run | |
| TC-10c | | | | | Not run | |
| TC-11 | Not recorded | Not recorded | Not saved / not recorded | An above-cap request triggered the ₹75 lakh cap explanation. Other-product and human-connection requests were not fulfilled through a real referral; this was not a full scripted TC-11 run. | Partial | An above-cap request triggered the ₹75 lakh cap explanation. Other-product and human-connection requests were not fulfilled through a real referral; this was not a full scripted TC-11 run. |
| TC-12 | | | | | Not run | |
| TC-13 | Not recorded | Not recorded | Not saved / not recorded | Existing-loan transfer request received the specialist-referral wording and the call ended. No actual referral integration. | Pass | Existing-loan transfer request received the specialist-referral wording and the call ended. No actual referral integration. |
| TC-14 | | | | | Not run | |
| TC-15 | | | | | Not run | |
| TC-16 | | | | | Not run | |
| TC-17 | | | | | Not run | |
| TC-18 | | | | | Not run | |
| TC-19 | | | | | Not run | |
| TC-20 | | | | | Not run | |
| TC-21 | | | | | Not run | |
| TC-22 | | | | | Not run | |
| TC-23 | | | | | Not run | |
| TC-24 | | | | | Not run | |
| TC-25 | | | | | Not run | |
| TC-26 | | | | | Not run | |
| TC-27 | | | | | Not run | |

| EX-01 (exploratory DNC) | Not recorded | Not recorded | Not saved / not recorded | Agent acknowledged the request, but no actual do-not-call suppression integration exists. | Partial | Conversational acknowledgement only; suppression-list integration not implemented. |
| EX-02 (initial run) | 2026-10-11 | Not recorded | [retell_industrial_property_test.png](../evidence/transcripts/retell_industrial_property_test.png) | Customer stated "Industrial" property; agent continued asking eligibility questions (ownership, documents, loan amount) instead of disqualifying immediately. | Fail | Initial run on live Retell agent failed to disqualify industrial property. |
| EX-02 (retest) | 2026-10-11 | agent_e86cc8540577ceb0bfaba483bc | [retell_industrial_property_pass.png](../evidence/transcripts/retell_industrial_property_pass.png) | Customer answered "Industrial." Agent explained that LAP is available only for residential/commercial and industrial properties are ineligible, thanked customer, said goodbye, and called `end_call` in the same turn without asking further eligibility questions. | Pass | Verified live on Retell AI Test Audio (Model: GPT 5.6 Terra, Voice: Cimo, Agent ID: agent_e86cc8540577ceb0bfaba483bc). |

## Summary

- **Mapped test cases run:** 9
- **Pass:** 7 (TC-01, TC-02, TC-04, TC-06, TC-08, TC-09, TC-13)
- **Fail:** 0
- **Partial:** 2 (TC-07, TC-11)
- **Additional exploratory tests:** 2 scenarios (3 observed runs):
  - `EX-01` (do-not-call; Partial)
  - `EX-02 (initial run)` (industrial property; Fail — evidence: [retell_industrial_property_test.png](../evidence/transcripts/retell_industrial_property_test.png))
  - `EX-02 (retest)` (industrial property; Pass — evidence: [retell_industrial_property_pass.png](../evidence/transcripts/retell_industrial_property_pass.png))
- **Total observed live Retell test runs:** 12 runs across 11 scenarios (8 Pass, 3 Partial, 1 Fail)
- **Not run:** Remaining test cases, including PV-01–PV-06, unless separately tested and documented.

Counts reflect the observed scenarios mapped above, not a claim that every scripted test case was executed.

## Distinction: Live Retell Tests vs. Automated Python Tests

| Layer | Test Type | Coverage | Status & Evidence |
|---|---|---|---|
| **Live Retell AI Platform** | Interactive conversational testing (Test Audio & Test LLM) | 11 scenarios (TC-01, TC-02, TC-04, TC-06, TC-07, TC-08, TC-09, TC-11, TC-13, EX-01, EX-02) | 8 Pass, 3 Partial, 1 Fail (initial EX-02). Verified with screenshots: [retell_industrial_property_test.png](../evidence/transcripts/retell_industrial_property_test.png) (failure) and [retell_industrial_property_pass.png](../evidence/transcripts/retell_industrial_property_pass.png) (successful retest). |
| **Local Automated Suite** | Python unit tests (`tests/test_business_rules.py`, `tests/test_app.py`) | 38 automated unit tests (27 business rule & prompt static checks + 11 Flask web demo HTTP/validation checks) | 38 / 38 Pass (100% passing). Executed locally via `python3 -m unittest discover tests -v`. |

## Failures, Remediations, and Retests

- **Repeated goodbye (TC-07):** Disqualification was correct, but the agent continued with extra goodbye responses after `end_call`. System prompt updated with explicit instructions to deliver closing statement, goodbye, and execute `end_call` in the same turn without generating further turns or repeated goodbyes. Added explicit Disqualification and Busy customer examples to `# Examples` in `prompts/home_credit_lap_system_prompt.md`.
- **Industrial property failure & verified retest (EX-02):**
  - *Initial Failure:* Customer answered "Industrial", and agent continued asking subsequent eligibility questions (ownership, documents, amount) instead of immediate disqualification (captured in `evidence/transcripts/retell_industrial_property_test.png`).
  - *Remediation:* System prompt updated locally to explicitly classify industrial property under Disqualifies (alongside agricultural), enforce same-turn `end_call`, and add a dedicated few-shot example. Business logic in `file.py` and 27 unit tests updated.
  - *Verified Retest:* The prompt update was applied to Retell agent `agent_e86cc8540577ceb0bfaba483bc` (GPT 5.6 Terra, Cimo voice). In Test Audio, customer answered "Industrial", agent immediately stated industrial properties are ineligible, and invoked `end_call` with no further questions (captured in `evidence/transcripts/retell_industrial_property_pass.png`). Retest status: **Pass**.
- **Do-not-call (EX-01):** The agent acknowledged the request, but no suppression-list integration is implemented. Do not claim the customer was actually removed from a calling list.
- **Other integrations:** Callback scheduling and specialist referral are conversational only; no real scheduling or referral integration is implemented.
- **Evidence documentation:** Transcript screenshots for EX-02 failure and successful retest are saved in `evidence/transcripts/`. Audio recordings and public export URLs remain unexported. Do not invent unverified evidence.
