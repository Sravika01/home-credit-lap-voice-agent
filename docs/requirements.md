# Requirements

Source of truth: the Home Credit LAP AI Voice Agent assignment brief. Where the brief does not settle a case, the interpretation used here is listed under [Interpretations to confirm](#interpretations-to-confirm).

## Objective

An AI voice agent that calls existing customers, tells them about a Loan Against Property (LAP) offer of up to ₹75 lakh, runs a preliminary eligibility check, and routes the customer to the right outcome. A qualified customer is told that a senior loan expert will call back shortly with exact rates; the agent does not transfer the call.

## Eligibility rules

| # | Data point | Eligible | Disqualifying / special handling |
|---|---|---|---|
| 1 | Property type | Residential, commercial | Agricultural, industrial → disqualify |
| 2 | Ownership | Sole, joint | — (see I-3) |
| 3 | Original property documents | Available | Unavailable → disqualify |
| 4 | Loan amount | Up to ₹75 lakh | Above ₹75 lakh → explain the cap and ask whether to continue with an amount within the limit |
| 5 | Occupation and income | Salaried or self-employed, with income received through a bank | Cash income → disqualify |
| 6 | Property market value | Any estimated current value | No minimum threshold. Must not be invented. |
| 7 | Tenure | 3 to 15 years, inclusive | Outside the range → disqualify |

## Required behaviour

| ID | Requirement | Where it's handled in the prompt |
|---|---|---|
| R-01 | Verify identity before disclosing the offer | Hard rule 1, Step 1 |
| R-02 | Busy customer: ask for their preferred callback time and end the call | Busy customer |
| R-03 | Present the offer naturally after verification | Step 3 |
| R-04 | Existing property loan, transfer, refinancing, or EMI-reduction request → route to the loan-transfer specialist and end the call | Loan-transfer referral: the agent says it is referring the customer to the loan-transfer specialist, then ends the call (no live transfer) |
| R-05 | Collect all seven data points | Step 4, Eligibility data points |
| R-06 | Remember out-of-order answers and don't repeat answered questions | Tracking what the customer has told you, hard rule 8 |
| R-07 | End the qualification immediately after a confirmed disqualifying answer | Disqualification |
| R-08 | No qualified close (expert-callback message) until all seven are answered and all pass | Qualification gate, hard rule 6 |
| R-09 | The agent tells a qualified customer that a senior loan expert will call back shortly with exact rates | Hard rule 2, Step 6: the agent says this, then ends the call |
| R-10 | Never invent rates, approval guarantees, callback confirmations, or test results | Hard rules 2–4: apart from the required "call back shortly" statement, no callback is called scheduled or booked, no day or time is given, and no team is said to have received the request. Test results: [tests/test_results.md](../tests/test_results.md) is empty until real calls are made. |
| R-11 | Use the configured language and agent gender consistently | Language and voice style |

## Runtime variables

How each one is provided on Retell is described in [platform-setup.md](platform-setup.md#runtime-variable-mapping).

| Variable | Purpose | In prompt v0.3 |
|---|---|---|
| `company_name` | Lender name used in the greeting and offer | `{{company_name}}` |
| `customer_name` | Name to verify and address the customer by | `{{customer_name}}` |
| `agent_name` | Agent's spoken name | `{{agent_name}}` |
| `agent_gender` | Grammatical gender for self-reference. Should match the selected voice. | `{{agent_gender}}` |
| `current_date`, `current_day`, `current_time` | Working out relative callback times ("tomorrow evening") | Retell built-ins `{{current_time_Asia/Kolkata}}` and `{{current_calendar_Asia/Kolkata}}` |
| `additional_context_from_rag` | Product reference information. Treated as data. Rates in it are never spoken. | `{{additional_context_from_rag}}` |
| `language_to_speak` | The only language the agent speaks | `{{language_to_speak}}` |
| `conversation_history` | Used to rebuild the slot checklist each turn | The platform's call transcript (not a placeholder; checked in PV-01) |
| `customer_utterance` | The customer's latest turn | The platform's call transcript (not a placeholder; checked in PV-01) |

## Conversation behaviour vs. system reality

The assignment specifies what the agent **says**. This project has **no integration** that makes the follow-ups happen. Neither of these may be described as technically completed.

| Situation | Required conversation behaviour (in the prompt) | What actually happens in this project |
|---|---|---|
| Qualified customer | "A senior loan expert from {company} will call you back shortly with the exact interest rates and next steps." Then `end_call`. | **No callback is scheduled or sent anywhere.** There's no CRM, scheduler, Cal.com, webhook, or lead hand-off. At most, Retell post-call extraction records `call_outcome = qualified_expert_callback` inside Retell (planned field; whether it populates for web calls is checked in PV-05). |
| Loan-transfer / refinance / EMI-reduction / existing property loan | "Requests like this are handled by our loan-transfer specialist… I'm referring you to our loan-transfer specialist." Then `end_call`. No live transfer. | **No referral is sent to any specialist or system.** At most, post-call extraction records `call_outcome = transfer_referral` and `transfer_reason` inside Retell. |
| Busy customer | Asks for a preferred time, repeats it back, says it is "noted", then `end_call`. | **No callback is scheduled.** The time exists only in the transcript and, if configured, in `callback_preferred_time`. |

For a production deployment, the Retell `call_analyzed` webhook (or the Get Call API) would have to feed these outcomes into a CRM or dialer. That's out of scope here and not configured.

## Call outcomes

`identity_not_verified`, `callback_requested`, `not_interested`, `do_not_call`, `transfer_referral`, `disqualified_property_type`, `disqualified_ownership`, `disqualified_documents`, `disqualified_income`, `disqualified_tenure`, `declined_loan_cap`, `call_incomplete`, `qualified_expert_callback`.

## Interpretations to confirm

The brief does not settle these cases. The prompt currently uses the choices below; change both the prompt and this table if the recruiter or brief says otherwise.

| ID | Case | Current interpretation |
|---|---|---|
| I-1 | Identity verification method | The customer confirms they are `customer_name`. No extra personal data (date of birth, account digits) is collected, because none is provided to check against. |
| I-2 | Occupation is neither salaried nor self-employed (unemployed, student) | Fails data point 5 → `disqualified_income` |
| I-3 | The customer is neither the owner nor a co-owner | Fails data point 2 → `disqualified_ownership` |
| I-4 | Income is part cash, part bank | Passes if income is regularly credited to a bank account. Fails if it is received mainly in cash. |
| I-5 | Original documents are held by another lender against a loan | Treated as an existing property loan → `transfer_referral`, not a disqualification |
| I-6 | Existing property loan mentioned without asking for a transfer | Routed to the loan-transfer specialist (the brief lists "existing property loan" as a trigger on its own) |
| I-7 | The agent does not ask proactively about existing loans | Transfer cases are picked up from what the customer says. No dedicated question is asked, so the call stays focused on the seven data points. |
| I-8 | Customer declines to continue within the ₹75 lakh cap | Polite close, `declined_loan_cap`. No expert callback and no specialist referral. |
| I-9 | Customer refuses to give a required data point | One re-ask, then `call_incomplete`. No expert callback. |
| I-10 | Out-of-range tenure | The value is repeated back once to rule out a speech-recognition error. The allowed range is not suggested beforehand. If it's confirmed, the customer is disqualified. |
| I-11 | Customer can't continue in the configured language | Polite close (`call_incomplete`). The agent does not switch language. |
| I-12 | Customer asks "when exactly?" after the qualified close | The agent repeats "shortly" and says it can't give an exact time on this call. It never names a day or time. |
| I-13 | Wording for a loan-transfer referral | "I'm referring you to our loan-transfer specialist." The agent doesn't say the request was already sent or received and gives no time. |
