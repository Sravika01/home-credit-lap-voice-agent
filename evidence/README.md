# Evidence

Real call evidence only. Includes verified test conversation screenshots and exported platform artifacts.

| Folder / file | Contents |
|---|---|
| `recordings/` | WAV recordings downloaded from Retell Call History |
| `transcripts/` | Transcripts and test conversation screenshots exported from the platform (`retell_industrial_property_test.png` failure, `retell_industrial_property_pass.png` pass) |
| `call_logs/` | Retell Call History CSV export (**Actions → Export**), including the recording and public log URLs |
| [links.md](links.md) | Shareable platform links, with their access level |
| `_raw/` | Unredacted downloads. **Git-ignored. Never submit.** |

## Naming

`<TC-XX or PV-XX>_<YYYY-MM-DD>_<call-id>.<ext>`, for example `TC-06_2026-10-12_abc123.wav`. The call ID must match the one in [../tests/test_results.md](../tests/test_results.md).

## Before adding a file

- Use only fictional customer details and Retell web test calls (no phone numbers).
- Remove phone numbers, email addresses, API keys, and agent/webhook secrets from logs. Keep the call ID.
- Download into `_raw/` first, then copy a redacted version here.
- If a recording can't be shared publicly, say so in [links.md](links.md), state the actual limitation, and include the exported transcript and call log instead.
