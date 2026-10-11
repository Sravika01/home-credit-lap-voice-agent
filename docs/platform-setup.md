# Platform Setup — Retell AI

> **Status: PROTOTYPE CONFIGURED — PARTIALLY TESTED.** The Retell AI agent prompt and dynamic variables have been tested across conversational scenarios (see [../tests/test_results.md](../tests/test_results.md)), while platform validation checks (PV-01 to PV-06) and external integrations remain unrun. Docs checked on 2026-10-11. Dashboard labels below are quoted from the linked official pages; if your dashboard looks different, trust the dashboard and update this file.

## Rules for this project

- Test with **web calls only**, through the dashboard's Test Audio panel. No phone number is needed.
- **Don't** buy a phone number, complete KYC, call a real customer, or run a batch/outbound campaign.
- Use only fictional data: the test values in [../tests/test_cases.md](../tests/test_cases.md).
- No transfer tools, Cal.com, CRM, or webhooks are configured. The only tool is **End Call**.

## Costs (verified)

| Item | What the docs say | Source |
|---|---|---|
| Signup credit | "$10 in free credits when you sign up" | [Testing pricing](https://docs.retellai.com/test/testing-pricing) |
| Testing | "There's no separate test tier and no free testing sandbox" | same |
| Text tests (Test LLM) | "roughly $0.001 to $0.05 per message depending on the model" | same |
| Web calls | "roughly $0.07 to $0.31 per minute depending on the model and voice" | same |

The quick-start page calls web testing free, which contradicts the pricing page. This file goes with the pricing page. Budget plan: debug with text tests first and use web calls only for the final evidence runs. 27 voice runs of about 3 minutes each would cost roughly $6–$25, so the $10 credit may not cover every run.

## Steps

### 1. Create the agent
1. Sign up at retellai.com.
2. Open the **Agents** tab → **Create an agent** → **Single prompt** ([quick start](https://docs.retellai.com/get-started/quick-start), [agent types](https://docs.retellai.com/build/choose-agent-type)).
3. Paste the prompt between the markers in [../prompts/home_credit_lap_system_prompt.md](../prompts/home_credit_lap_system_prompt.md) into the prompt box ([basic settings](https://docs.retellai.com/build/single-multi-prompt/configure-basic-settings)).

### 2. Model, voice, language, opening
Source for all of these: [basic settings](https://docs.retellai.com/build/single-multi-prompt/configure-basic-settings).
- **Model dropdown:** pick a model marked **Suggested**, preferably from **Fast and cost-efficient** to save credit.
- **Voice control → Select Voice:** use the **Gender** filter to pick a voice that matches `agent_gender`. Use the **Accent** filter for an Indian accent if one is available.
- **Language dropdown:** set it to match `language_to_speak`. Use `en-IN` for English or `hi-IN` for Hindi ([supported languages](https://docs.retellai.com/build/language-support)).
- **Welcome Message:** choose **AI speaks first**, then **Dynamic message**, so the greeting follows Step 1 of the prompt. Don't use a fixed custom message, because it could mention the offer before identity is verified.

### 3. End Call tool
In the tools section, click **+ Add**, then choose **End Call** ([end call](https://docs.retellai.com/build/single-multi-prompt/end-call)). Name it `end_call`: the API schema gives each tool a `name` ("Must be unique within all tools available to LLM") and uses `name: end_call` in its example ([Create Retell LLM](https://docs.retellai.com/api-references/create-retell-llm)). Retell's end-call page also recommends putting the end conditions in the prompt, which the prompt's "Ending the call" section does. "By default, the agent won't end the call automatically", so without this tool calls won't end. Don't add **Call Transfer**: "Transfer Call works on phone calls only, not web calls" ([transfer call](https://docs.retellai.com/build/single-multi-prompt/transfer-call)), and the assignment requires a callback, not a transfer.

### 4. Default dynamic variables
In the agent editor, open **Security & fallback settings** → **Default Dynamic Variables** ([dynamic variables](https://docs.retellai.com/build/dynamic-variables)) and enter the default test values from [../tests/test_cases.md](../tests/test_cases.md). Set `additional_context_from_rag` too; a short "No additional product information." is enough. Any variable left unset stays as the raw `{{...}}` text in the prompt.

### 5. Post call extraction
Open **Post call extraction** → **Add** ([define fields](https://docs.retellai.com/features/post-call-analysis-create)):

| Name | Type | Description / choices |
|---|---|---|
| `call_outcome` | Selector | Choices: the 13 outcome codes in [requirements.md](requirements.md#call-outcomes). Explain each choice in the description, not in the choice text. |
| `callback_preferred_time` | Text | The callback day and time the customer asked for, with the date if stated. Empty if none. |
| `transfer_reason` | Text | Why the call was a loan-transfer referral. Empty if it wasn't. |
| `property_type`, `ownership`, `original_documents`, `loan_amount`, `occupation_income`, `property_value`, `tenure` | Text | The value the customer stated, or "not collected". |

These fields only *record* what happened. Nothing sends them to a CRM or scheduler.

### 6. Leave secure URLs off
Under **Security & fallback settings**, leave **Opt In Secure URLs** off. By default "the URLs we generate for call recordings and logs do not expire, allowing you to easily share the links"; with secure URLs on, they expire after 24 hours by default ([secure URL](https://docs.retellai.com/accounts/signed-secure-url)).

### 7. Test
1. **Text tests first:** in the **Test LLM** tab, open **Test Inputs** → **Dynamic variables**, set the values for the scenario, then click **Save** ([LLM playground](https://docs.retellai.com/test/llm-playground)). Run the platform checks PV-01 to PV-03, then the scenarios.
2. **Voice evidence:** in the Test panel, select **Test Audio** → **Run Test**. The same Test Inputs apply ([web call testing](https://docs.retellai.com/test/test-web)).
3. Record each run in [../tests/test_results.md](../tests/test_results.md).

### 8. Get the evidence
- **Call History:** open the call to see its recording, transcript, post-call analysis, and logs ([call history](https://docs.retellai.com/features/session-history)).
- **Export:** open **Actions** → **Export**, choose columns (exports "can also include recording and public log URLs"), then download from **Actions → Export records**. Completed export records are kept for one week (same page).
- **Per-call links:** the [Get Call API](https://docs.retellai.com/api-references/get-call) returns `recording_url`, `public_log_url`, and `transcript` for both web and phone calls.
- Recordings are WAV. Data is kept with no automatic deletion by default ([data retention](https://docs.retellai.com/accounts/data-retention)).
- Before listing a link in [../evidence/links.md](../evidence/links.md), open it in a private/incognito window to confirm it loads without a login.

## Runtime variable mapping

| Assignment variable | Retell handling | Verified? |
|---|---|---|
| `company_name` | Custom dynamic variable. Agent prompts are a documented supported field. | Syntax verified |
| `customer_name` | Custom dynamic variable (fictional value) | Syntax verified |
| `agent_name` | Custom dynamic variable | Syntax verified |
| `agent_gender` | Custom dynamic variable. Must match the voice picked with the Gender filter. | Syntax verified; the voice match is a manual step |
| `language_to_speak` | Custom dynamic variable. Must match the agent's language setting (`en-IN` / `hi-IN`). | Syntax verified; "the agent is automatically instructed to respond in the configured language" ([language](https://docs.retellai.com/agent/language)) |
| `additional_context_from_rag` | Custom dynamic variable with a default. No Retell Knowledge Base is linked. | Syntax verified |
| `current_date`, `current_day`, `current_time` | Replaced by the built-in `{{current_time_Asia/Kolkata}}` (sample format: "Thursday, March 28, 2024 at 11:46 PM PDT", which includes day, date, and time) and `{{current_calendar_Asia/Kolkata}}` (14-day calendar). Retell has no built-in `current_date` or `current_day`. | The pattern `current_time_[timezone]` is verified (docs example: `{{current_time_Australia/Sydney}}`). **The docs don't list `Asia/Kolkata`; it's checked in PV-02.** |
| `conversation_history`, `customer_utterance` | Removed from the prompt; the agent works from the call transcript. If set, they would have to be supplied per call, and if left unset they would appear as raw `{{...}}` text. | **Not stated explicitly in the docs.** Retell's [single prompt guide](https://docs.retellai.com/build/single-multi-prompt/write-single-prompt) says agents "can handle common situations such as callers changing their minds or answering questions out of order". Checked in PV-01. |

## Platform behaviour still unverified

These have to be confirmed in the dashboard during testing (see the PV checks in [../tests/test_cases.md](../tests/test_cases.md#platform-validation-checks-run-first)):

| # | Behaviour | Check |
|---|---|---|
| U-1 | The LLM receives the full transcript every turn | PV-01 |
| U-2 | `{{current_time_Asia/Kolkata}}` and `{{current_calendar_Asia/Kolkata}}` resolve to IST | PV-02 |
| U-3 | All custom variables resolve, with no raw braces | PV-03 |
| U-4 | The End Call tool is named `end_call` and the agent actually hangs up | PV-04 |
| U-5 | Web test calls appear in Call History with recording, transcript, and post-call extraction | PV-05 |
| U-6 | Recording and public log URLs open without a login | PV-06 |
| U-7 | The credit balance covers the planned test runs | Check the balance after the text tests |

## Not configured (by design)

- Transferring the call, to a senior loan expert or a loan-transfer specialist
- Scheduling the senior-loan-expert callback that the agent tells the customer about (Cal.com, calendar, or CRM)
- Sending loan-transfer referrals to any specialist or system
- CRM or lead hand-off, and the `call_analyzed` webhook
- Phone numbers, KYC, outbound or batch calling
- Knowledge Base
