# Test Cases

Expected behaviour only. Record what actually happens in [test_results.md](test_results.md). Platform setup is in [../docs/platform-setup.md](../docs/platform-setup.md).

**Default test configuration** (fictional values; never use a real customer's details). Enter these in Retell under **Test Inputs → Dynamic variables**, or as the agent's default dynamic variables.

| Variable | Value |
|---|---|
| `company_name` | Home Credit |
| `customer_name` | Test Customer Ananya |
| `agent_name` | Riya |
| `agent_gender` | female (with a female voice) |
| `language_to_speak` | English (agent language `en-IN`) |
| `additional_context_from_rag` | No additional product information. (unless the case says otherwise) |

`current_time_Asia/Kolkata` and `current_calendar_Asia/Kolkata` are built into Retell and are not set by hand.

**Method:** text tests in **Test LLM** first, then the final evidence runs as **Test Audio** web calls. No phone numbers, real customers, or outbound campaigns.

**Every call should end with:** a goodbye, then `end_call`. No transfers. Apart from the required "call you back shortly" (qualified) and "I'm referring you" (loan transfer) statements, the agent never says a callback or referral is scheduled, booked, confirmed, sent, or received, and never names a day or time for an expert or specialist call.

---

## Platform validation checks (run first)

These check Retell behaviour that the docs don't state explicitly. If any of them fails, fix the setup before running TC-01 onwards.

### PV-01 — Conversation memory comes from the native transcript
- **Method:** Test LLM. Turn 1: confirm identity. Turn 2: "I have time." Turn 3 (after the offer): "It's a residential flat in my name." Then answer whatever is asked next.
- **Expected:** the agent doesn't ask again for property type or ownership in any later turn. This shows the model sees earlier turns without `conversation_history` / `customer_utterance` variables.
- **Verifies:** U-1

### PV-02 — India time variables resolve
- **Method:** Test LLM. After verification, say: "I'm busy, call me tomorrow evening."
- **Expected:** the agent repeats back tomorrow's correct day and date in IST. Its replies contain no literal `{{current_time_Asia/Kolkata}}` text and no wrong timezone (for example a US date).
- **Verifies:** U-2

### PV-03 — Custom variables resolve
- **Method:** Test LLM, default values.
- **Expected:** the greeting uses "Riya", "Home Credit", and "Test Customer Ananya". No `{{` text is spoken anywhere.
- **Verifies:** U-3

### PV-04 — End Call works
- **Method:** Test Audio web call. Say "Not interested, thanks."
- **Expected:** the agent says goodbye and the call actually disconnects. The Call History entry shows the call ended by the agent.
- **Verifies:** U-4

### PV-05 — Web call artifacts exist
- **Method:** after PV-04, open the call in Call History.
- **Expected:** recording, transcript, and post-call extraction (including `call_outcome`) are all present.
- **Verifies:** U-5

### PV-06 — Links can be shared
- **Method:** export the PV-04 call, including the recording and public log URLs. Open both in a private/incognito window.
- **Expected:** both load without a login. If they don't, write down the actual limitation in [../evidence/links.md](../evidence/links.md).
- **Verifies:** U-6

---

## Conversation scenarios

### TC-01 — Happy path, answers in order
- **Customer:** confirms identity → has time → interested → residential flat → sole owner → originals available → ₹40 lakh → salaried, salary credited to bank → value ₹1.2 crore → tenure 10 years → confirms the summary.
- **Expected:**
  - offer given only after verification; each data point asked once; summary of all 7;
  - says they meet the *preliminary* criteria (no "approved" wording);
  - says a senior loan expert will **call back shortly with the exact interest rates** and next steps;
  - names no day or time and doesn't say "scheduled", "booked", or "the expert has your details";
  - goodbye → `end_call`. **No transfer.**
- **Expected outcome:** `qualified_expert_callback` · **Covers:** R-01, R-03, R-05, R-08, R-09

### TC-02 — Out-of-order answers in one sentence
- **Customer (right after the offer):** "I have a commercial shop, jointly owned with my brother. I'm self-employed and need about 50 lakh for 12 years."
- **Expected:** captures property type, ownership, occupation, loan amount, and tenure. Asks only for the missing ones: income mode (bank or cash), original documents, property value. Doesn't ask again for anything already given.
- **Expected outcome:** `qualified_expert_callback` (if the remaining answers pass) · **Covers:** R-06

### TC-03 — Someone else answers
- **Customer:** "This is her husband. She's not home."
- **Expected:** no mention of the loan offer; asks when the customer can be reached; says only that it's "noted"; ends.
- **Expected outcome:** `identity_not_verified` · **Covers:** R-01

### TC-04 — Busy at the start, relative time
- **Customer:** confirms identity, then "I'm driving, call me tomorrow evening."
- **Expected:**
  - asks for or confirms a time;
  - repeats it back with the correct IST day and date;
  - says the time is "noted", never "confirmed" or "scheduled", and doesn't promise anyone will call at that time;
  - ends the call; no offer details pushed.
- **Expected outcome:** `callback_requested` · **Covers:** R-02, R-10

### TC-05 — Busy mid-qualification
- **Customer:** answers 3 data points, then "Sorry, I have to go, call me Saturday at 11."
- **Expected:** stops the questions; repeats back Saturday's correct date (from the calendar) and 11 am; "noted" wording only; ends.
- **Expected outcome:** `callback_requested` · **Covers:** R-02

### TC-06 — Agricultural property
- **Customer:** "It's agricultural land in my village."
- **Expected:** may confirm once; then explains politely that agricultural property doesn't meet this offer's criteria; asks **no** further data points; no mention of an expert call.
- **Expected outcome:** `disqualified_property_type` · **Covers:** R-07

### TC-07 — Original documents lost
- **Customer:** "The originals were lost in a flood; I only have photocopies."
- **Expected:** immediate polite disqualification; no further questions; no mention of an expert call.
- **Expected outcome:** `disqualified_documents` · **Covers:** R-07

### TC-08 — Cash income
- **Customer:** "I run a small shop, all my income is in cash."
- **Expected:** may confirm once; disqualifies on income mode; ends.
- **Expected outcome:** `disqualified_income` · **Covers:** R-07

### TC-09 — Tenure out of range
- **Customer:** all other data points pass, then "20 years."
- **Expected:** repeats it back once ("twenty years?"); customer confirms → disqualifies; no mention of an expert call.
- **Expected outcome:** `disqualified_tenure` · **Covers:** R-07, R-08

### TC-10 — Tenure boundaries
- **Variants:**
  - **TC-10a:** "3 years" (lower boundary, passes).
  - **TC-10b:** "15 years" (upper boundary, passes).
  - **TC-10c:** "36 months" (month-to-year conversion, 36 months = 3 years, passes).
- **Expected:** all three pass; the flow continues to the expert-callback close.
- **Expected outcome:** `qualified_expert_callback` for each variant · **Covers:** rule 7

### TC-11 — Above the cap, accepts a lower amount
- **Customer:** "I need 1 crore." → "OK, 75 lakh then."
- **Expected:** explains the ₹75 lakh maximum; asks whether to continue within it; records ₹75 lakh; doesn't ask for the amount again; continues to the remaining data points.
- **Expected outcome:** `qualified_expert_callback` (if the rest pass) · **Covers:** rule 4

### TC-12 — Above the cap, declines
- **Customer:** "I need 90 lakh." → "No, 75 isn't enough for me."
- **Expected:** explains the cap once; accepts the refusal; no expert call or specialist referral mentioned; polite close.
- **Expected outcome:** `declined_loan_cap` · **Covers:** rule 4

### TC-13 — Balance transfer mid-flow
- **Customer:** after 2 data points: "Actually I already have a home loan on this flat with another bank, can you take it over?"
- **Expected:**
  - stops qualification;
  - explains that the loan-transfer specialist handles this and says it is **referring** the customer to the loan-transfer specialist;
  - doesn't say the request was already sent or received, and gives no callback time;
  - **no transfer**; goodbye → `end_call`.
- **Expected outcome:** `transfer_referral` · **Covers:** R-04

### TC-14 — EMI-reduction request at the offer stage
- **Customer:** "I don't need a new loan, I want my current property loan EMI reduced." Then: "So when will they call me?"
- **Expected:** EMI reduction on an existing property loan is a transfer trigger; referral wording as in TC-13; no eligibility questions; when asked "when", says it can't give an exact time on this call; ends.
- **Expected outcome:** `transfer_referral` · **Covers:** R-04, R-10

### TC-15 — Original documents held by another bank
- **Customer:** "The originals are with SBI because of my existing loan."
- **Expected:** treated as an existing property loan → referral wording, not a documents disqualification; ends.
- **Expected outcome:** `transfer_referral` · **Covers:** R-04, I-5

### TC-16 — Unrelated existing loan
- **Customer:** "I have a car loan, does that matter?"
- **Expected:** not a transfer trigger; the agent doesn't judge eligibility on it or invent a rule; continues the flow.
- **Expected outcome:** depends on the remaining answers · **Covers:** R-04 (negative case)

### TC-17 — Asks for the interest rate
- **Setup:** `additional_context_from_rag` = "Sample (fictional) note: LAP interest rates start at 9.5% per annum."
- **Customer:** "What's the interest rate?" / "Just give me a rough number."
- **Expected:** no rate, range, or EMI given (even though the reference text has one); says a senior loan expert shares exact rates; returns to the next missing data point.
- **Expected outcome:** continues normally · **Covers:** R-09, R-10

### TC-18 — Early expert request
- **Customer:** after 4 data points: "Just put me through to the expert now."
- **Expected:** politely says a few more details are needed; asks for the next missing data point; no qualified close until all 7 pass; no transfer.
- **Expected outcome:** `qualified_expert_callback` only after all 7 · **Covers:** R-08

### TC-19 — Correction of an earlier answer
- **Customer:** says "residential", then later "Sorry, it's actually a commercial shop."
- **Expected:** updates property type to commercial (still passes); doesn't ask again for the other captured data points.
- **Expected outcome:** continues normally · **Covers:** R-06

### TC-20 — Ambiguous property type
- **Customer:** "It's a plot."
- **Expected:** asks whether it's residential, commercial, industrial, or agricultural; doesn't disqualify or pass until the customer clarifies (residential/commercial passes; agricultural/industrial disqualifies).
- **Expected outcome:** depends on the clarified answer · **Covers:** rule 1

### TC-21 — Refuses to give the property value
- **Customer:** "I don't want to tell you the value." (twice)
- **Expected:** explains once why it's needed; on the second refusal ends politely; **no** qualified close; no minimum value invented.
- **Expected outcome:** `call_incomplete` · **Covers:** R-08, rule 6

### TC-22 — Approval guarantee and timing
- **Customer:** "Will I definitely get the loan?" … (after qualifying) "When exactly will the expert call?"
- **Expected:** explains it's a preliminary check only; no guarantee. When asked "when exactly", repeats that the expert will call back **shortly** and says it can't give an exact time; names no day or time.
- **Expected outcome:** `qualified_expert_callback` if all 7 pass · **Covers:** R-10

### TC-23 — Hindi, male agent
- **Config:** `language_to_speak` = Hindi, `agent_gender` = male, agent language `hi-IN`, a male voice (Gender filter), `agent_name` = Rahul.
- **Expected:** whole call in Hindi; male self-reference throughout ("bol raha hoon"); amounts spoken in words.
- **Expected outcome:** any · **Covers:** R-11

### TC-24 — Not interested
- **Customer:** "Not interested, thanks."
- **Expected:** polite close; no pressure or repeated pitch.
- **Expected outcome:** `not_interested`

### TC-25 — Customer tries to read out sensitive numbers
- **Customer:** "Let me give you my Aadhaar number, it's…"
- **Expected:** stops them politely; says it isn't needed; continues.
- **Expected outcome:** continues normally · **Covers:** hard rule 7

### TC-26 — Repeated amount above the cap
- **Customer:** "I need 1 crore." → (after the cap is explained) "Then 80 lakh." → (cap restated) "85 lakh."
- **Expected:** explains the cap, restates it once, then treats the third above-cap amount as not continuing within the limit; polite close; no expert call mentioned.
- **Expected outcome:** `declined_loan_cap` · **Covers:** rule 4

### TC-27 — Identity stays unclear
- **Customer:** "Who's asking?" → (agent asks again) "Just tell me what it's about."
- **Expected:** doesn't mention the loan offer; after the second unclear answer, thanks them and ends.
- **Expected outcome:** `identity_not_verified` · **Covers:** R-01

---

## Exploratory test scenarios

### EX-01 — Do-not-call request
- **Customer:** "Please add me to your do-not-call list and never call again."
- **Expected:**
  - Agent politely acknowledges and notes the request;
  - Closes politely and invokes `end_call`;
  - Conversational acknowledgement only (no live dialer/CRM suppression list integration).
- **Expected outcome:** `do_not_call` · **Covers:** Hard rules, call outcomes

### EX-02 — Industrial property disqualification test
- **Customer:** After greeting and offer presentation, answers "Industrial" to property type.
- **Expected:**
  - Agent immediately explains industrial property does not meet eligibility criteria;
  - Closes politely and invokes `end_call` without asking further eligibility questions.
- **Expected outcome:** `disqualified_property_type` · **Covers:** Data point 1, immediate disqualification
