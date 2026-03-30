# SupportPilot Agent

Grounded support answers with confidence scoring, citation transparency, and escalation triage for uncertain or risky requests.

## Quick Links (Update Before Submission)

- GitHub Repository URL: <https://github.com/Satyam999999/Supportpilot-Gitagent.git>

Submission references:

- Stateful correctness audit: [reports/audits/STATEFUL_CORRECTNESS_AUDIT.md](reports/audits/STATEFUL_CORRECTNESS_AUDIT.md)
- Red-team audit: [reports/audits/RED_TEAM_SECURITY_AUDIT.md](reports/audits/RED_TEAM_SECURITY_AUDIT.md)

## What This Agent Does

SupportPilot automates repetitive support workflows while keeping reliability explicit.

- Resolves common support questions from a grounded FAQ KB.
- Uses hybrid retrieval to reduce single-method blind spots.
- Returns confidence and citations instead of opaque answers.
- Escalates ambiguous, high-risk, or policy-conflict queries with reason codes.
- Preserves recent conversational context for follow-up questions.

## Architecture

![Architecture](./architecture-diagram.svg)

Core flow:

1. Classify incoming query intent.
2. Rewrite query when follow-up ambiguity is detected.
3. Retrieve evidence with hybrid retrieval.
4. Score confidence from retrieval and evidence quality.
5. Either answer with citations or escalate with structured rationale.

## Repository Structure

- Core runtime: [src/support_agent.py](src/support_agent.py)
- Evaluation harness: [src/evaluate.py](src/evaluate.py)
- Demo UI: [src/demo_app.py](src/demo_app.py)
- GitAgent structure validator: [src/validate_gitagent_structure.py](src/validate_gitagent_structure.py)
- Knowledge base: [data/faq_kb.md](data/faq_kb.md)
- Compliance manifest: [agent.yaml](agent.yaml)
- Architecture notes: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Failure summary: [docs/FAILURE_ANALYSIS.md](docs/FAILURE_ANALYSIS.md)
- Test scripts: [tests](tests)
- Audit reports: [reports/audits](reports/audits)
- Submission report: [reports/submission](reports/submission)

## Setup and Installation

Prerequisites:

- Python 3.10+
- pip
- Optional HF token for faster model pulls

Install:

```bash
git clone <https://github.com/Satyam999999/Supportpilot-Gitagent.git>
cd GITAGENT
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional environment file:

```bash
HF_TOKEN=your_hf_token_optional
PYTHONUNBUFFERED=1
```

## Run the Project

CLI agent:

```bash
python src/support_agent.py
```

Demo app:

```bash
streamlit run src/demo_app.py
```

Evaluation benchmark:

```bash
python src/evaluate.py
```

Structure validation:

```bash
python src/validate_gitagent_structure.py
```

## Evaluation Snapshot

Source: [evaluation_results.json](evaluation_results.json)

- total_prompts: 25
- grounded_rate: 1.0
- escalation_accuracy: 0.92
- median_latency_ms: 38.56

## GitAgent Manifest Compliance

Source: [agent.yaml](agent.yaml)

| Field | Value |
|---|---|
| spec_version | 0.1.0 |
| name | supportpilot-agent |
| version | 0.1.0 |
| skills | support-resolution, escalation-triage |
| tools | [] declared |
| runtime.max_turns | 20 |
| runtime.timeout | 120 |

Note:
- Runtime includes an internal billing helper path while manifest tools are currently empty. This is tracked in known limitations.

## Tool Reference

### fetch_user_subscription (runtime helper)

Input:
- user_id: string

Output:
- plan: string
- status: string

Example outputs:
- {"plan": "Pro", "status": "active"}
- {"plan": "Unknown", "status": "unverified"}

Behavior:
- No external network call in current MVP.
- Uses in-memory lookup and returns explicit unverified status for unknown users.

## Bugs Found and Fixed During Development

This section replaces the placeholder and summarizes what was found and improved.

Fixed or improved:

1. Added hybrid retrieval fallback strategy to reduce retrieval misses on wording variance.
2. Added confidence plus citation output so weak grounding is visible to users.
3. Added escalation reason codes for risky and policy-conflict paths.
4. Added query rewriting for ambiguous follow-up turns.
5. Added comprehensive benchmark and validator flow for repeatable checks.

Known unresolved or partially unresolved (tracked in reports):

1. Manifest-runtime tool declaration drift.
2. Short-horizon memory limitations for long sessions.
3. Need stronger tool-output and KB sanitization.
4. Heuristic intent classification can still be prompt-steered.
5. Registry trust hardening not fully enforced.

Details:

- [reports/audits/STATEFUL_CORRECTNESS_AUDIT.md](reports/audits/STATEFUL_CORRECTNESS_AUDIT.md)
- [reports/audits/RED_TEAM_SECURITY_AUDIT.md](reports/audits/RED_TEAM_SECURITY_AUDIT.md)

## Known Limitations

1. Manifest declares no tools while one internal helper is used in billing logic.
2. Memory is list-based and short horizon, so very long sessions may degrade context quality.
3. Sanitization and schema validation need hardening for production-grade security.
4. Intent classification is heuristic and benefits from stronger disambiguation.
5. Provenance and signing controls for registry trust are not fully implemented.



## License

MIT
