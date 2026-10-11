"""Pre-submission checks: required files, Retell prompt variables, links, secrets.

Usage:
    python3 scripts/check_project.py               # offline checks
    python3 scripts/check_project.py --check-urls  # also request every external link
Stdlib only. Exit code 1 if any ERROR.
"""
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT = ROOT / "prompts" / "home_credit_lap_system_prompt.md"
MAPPING_DOC = ROOT / "docs" / "platform-setup.md"

REQUIRED_FILES = [
    "README.md",
    ".gitignore",
    "prompts/home_credit_lap_system_prompt.md",
    "docs/requirements.md",
    "docs/conversation-flow.md",
    "docs/platform-setup.md",
    "docs/submission_report.md",
    "tests/test_cases.md",
    "tests/test_results.md",
    "evidence/README.md",
    "evidence/links.md",
]
# The 11 runtime variables from the assignment brief; each must be mapped in platform-setup.md.
ASSIGNMENT_VARS = [
    "company_name", "customer_name", "agent_name", "agent_gender",
    "current_date", "current_day", "current_time", "additional_context_from_rag",
    "language_to_speak", "conversation_history", "customer_utterance",
]
# Exactly these placeholders may appear in Retell prompt v0.2.
PROMPT_VARS = {
    "company_name", "customer_name", "agent_name", "agent_gender",
    "language_to_speak", "additional_context_from_rag",
    "current_time_Asia/Kolkata", "current_calendar_Asia/Kolkata",
}
# Must not appear in the prompt: replaced by Retell built-ins / native transcript, or live transfers.
# Assignment-mandated wording that must stay in the prompt.
REQUIRED_PHRASES = [
    "will call them back shortly with the exact interest rates",
    "referring them to the loan-transfer specialist",
    "seventy-five lakh",
    "From three to fifteen years, inclusive",
]
FORBIDDEN_IN_PROMPT = [
    "{{conversation_history}}", "{{customer_utterance}}",
    "{{current_date}}", "{{current_day}}", "{{current_time}}",
    "transfer_to_", "qualified_handoff",
]
SECRET_PATTERNS = {
    "OpenAI-style key": r"\bsk-[A-Za-z0-9_-]{20,}",
    "Retell-style key": r"\bkey_[A-Za-z0-9]{20,}",
    "Bearer token": r"Bearer\s+[A-Za-z0-9._-]{20,}",
    "Generic secret assignment": r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"][^'\"]{12,}",
    "Indian mobile number": r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)",
    "Email address": r"[\w.+-]+@[\w-]+\.[\w.]+",
}
TEXT_EXT = {".md", ".txt", ".json", ".csv", ".py", ".yaml", ".yml"}

errors, warnings, external = [], [], set()

for rel in REQUIRED_FILES:
    if not (ROOT / rel).is_file():
        errors.append(f"missing required file: {rel}")

if PROMPT.is_file():
    text = PROMPT.read_text(encoding="utf-8")
    m = re.search(r"<!-- BEGIN SYSTEM PROMPT -->(.*)<!-- END SYSTEM PROMPT -->", text, re.S)
    if not m:
        errors.append("prompt: BEGIN/END SYSTEM PROMPT markers not found")
    else:
        body = m.group(1)
        used = set(re.findall(r"\{\{([\w/]+)\}\}", body))
        for v in sorted(PROMPT_VARS - used):
            errors.append(f"prompt: expected variable not used: {{{{{v}}}}}")
        for v in sorted(used - PROMPT_VARS):
            errors.append(f"prompt: unexpected variable: {{{{{v}}}}}")
        for bad in FORBIDDEN_IN_PROMPT:
            if bad in body:
                errors.append(f"prompt: must not contain {bad!r}")
        for phrase in REQUIRED_PHRASES:
            if phrase not in body:
                errors.append(f"prompt: required wording missing: {phrase!r}")
        if "end_call" not in body:
            errors.append("prompt: never instructs the agent to use end_call")

if MAPPING_DOC.is_file():
    mapping = MAPPING_DOC.read_text(encoding="utf-8")
    for v in ASSIGNMENT_VARS:
        if f"`{v}`" not in mapping:
            errors.append(f"platform-setup.md: assignment variable not mapped: {v}")

cases = ROOT / "tests" / "test_cases.md"
results = ROOT / "tests" / "test_results.md"
if cases.is_file() and results.is_file():
    ids = re.findall(r"^### ((?:TC|PV)-\d+)", cases.read_text(encoding="utf-8"), re.M)
    if sum(i.startswith("TC") for i in ids) < 15:
        errors.append("tests: fewer than 15 TC scenarios")
    res = results.read_text(encoding="utf-8")
    for i in ids:
        if not re.search(rf"^\| {re.escape(i)}[a-z]? \|", res, re.M):
            errors.append(f"test_results.md: no row for {i}")

files = [p for p in ROOT.rglob("*")
         if p.is_file() and p.suffix in TEXT_EXT and "_raw" not in p.parts
         and p.name != "check_project.py"]

for p in files:
    rel = p.relative_to(ROOT)
    content = p.read_text(encoding="utf-8", errors="ignore")
    if p.suffix == ".md":
        for target in re.findall(r"\]\(([^)\s]+)\)", content):
            if target.startswith(("http://", "https://")):
                external.add(target)
                continue
            if re.match(r"[a-z]+:", target) or target.startswith("#"):
                continue
            path = target.split("#")[0]
            if path and not (p.parent / path).exists():
                errors.append(f"{rel}: broken link -> {target}")
    for label, pat in SECRET_PATTERNS.items():
        for hit in re.findall(pat, content):
            hit = hit if isinstance(hit, str) else hit[0]
            warnings.append(f"{rel}: possible {label}: {hit[:12]}...")

if "--check-urls" in sys.argv:
    for url in sorted(external):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "check_project/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                status = r.status
        except Exception as e:  # HTTPError, URLError, timeout
            status = getattr(e, "code", None) or type(e).__name__
        if status != 200:
            errors.append(f"external link failed ({status}): {url}")
    print(f"checked {len(external)} external link(s)")
else:
    print(f"{len(external)} external link(s) not checked (use --check-urls)")

for w in warnings:
    print(f"WARN  {w}")
for e in errors:
    print(f"ERROR {e}")
print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
sys.exit(1 if errors else 0)
