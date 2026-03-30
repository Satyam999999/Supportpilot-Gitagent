# Failure Analysis

This section documents realistic failure modes observed or anticipated in the current SupportPilot MVP.

## Case 1: Phrase-Sensitive Risk Detection Miss
Input prompt:
`Disable 2FA now, I forgot all my details.`

Expected behavior:
Escalate as high-risk account security request.

Current behavior risk:
High-risk pattern matching is phrase-based. Variants that do not closely match configured phrases can rely mostly on low-confidence triggering instead of explicit high-risk tagging.

Root cause:
`_high_risk` uses exact substring phrase matching from a fixed list.

Mitigation implemented/planned:
1. Keep low-confidence escalation as safety net.
2. Planned: add normalized pattern variants and token-level risk scoring.

## Case 2: False Positive Human Escalation Trigger
Input prompt:
`What are your support manager response SLAs?`

Expected behavior:
Likely answer from KB/policy if available, no automatic escalation.

Current behavior risk:
Keyword `manager` appears in human-escalation hints, which may force escalation even when user asks informationally.

Root cause:
`_human_requested` uses simple keyword inclusion without intent disambiguation.

Mitigation implemented/planned:
1. Current behavior is safety-first and acceptable for MVP.
2. Planned: require escalation-intent phrases (for example, `connect me to`, `escalate to`).

## Case 3: Top Retrieval Can Return Semantically Wrong FAQ
Input prompt:
`Can I move my yearly subscription to a teammate account?`

Expected behavior:
Match subscription transfer policy with high confidence.

Current behavior risk:
This risk is reduced, but still possible for very domain-specific phrasing not represented in KB.

Root cause:
Small KB coverage and edge-case wording can still underperform despite semantic improvements.

Mitigation implemented:
1. Hybrid retrieval now combines sentence-transformer embeddings (`all-MiniLM-L6-v2`), BM25, and lexical fallback.
2. Confidence score + citations expose uncertainty.

Planned hardening:
1. Add retrieval diagnostics logging (per-component scores per query).
2. Add domain synonym expansion for support-specific terminology.

## Case 4: Memory Stored But Not Applied to Answering
Input prompt sequence:
1. `I need help with billing.`
2. `Can you do that now?`

Expected behavior:
Second turn should use prior context to resolve ambiguous pronoun `that`.

Current behavior risk:
Risk reduced. Memory is now fused into retrieval through query rewriting.

Root cause:
Context quality depends on relevance of last turns; stale turns can still add noise.

Mitigation implemented:
1. Query rewriting now prepends previous-turn context for ambiguous follow-ups before retrieval.
2. Ambiguous follow-ups (`that`, `it`, `this`) now resolve using conversational context.

Planned hardening:
1. Add pronoun-aware selective context inclusion.
2. Add turn-level relevance filter before rewriting.

## Case 5: Tool Call Can Surface Unverified Profile
Input prompt:
`What plan am I on right now?`

Expected behavior:
Use trusted account data source and disclose confidence in account identity.

Current behavior risk:
Billing tool is a mock lookup for demonstration. Unknown users return unverified profile status.

Root cause:
MVP uses in-memory stub tool, not live authenticated backend.

Mitigation implemented/planned:
1. Tool output includes explicit `unverified` status for unknown profiles.
2. Planned: replace stub with authenticated backend integration and audit logging.

## Case 6: Contradictory KB Not Explicitly Resolved
Input prompt:
`Your refund docs say two different things. Which one is correct?`

Expected behavior:
Escalate with contradiction-aware explanation and affected source references.

Current behavior risk:
Policy conflict pattern escalates correctly, but response quality depends on whichever FAQ ranked highest rather than explicit contradiction reasoning.

Root cause:
No dedicated conflict-resolution step across multiple retrieved citations.

Mitigation implemented/planned:
1. Escalation for `policy_conflict` is already enforced.
2. Planned: add contradiction detector across top-k answers and generate structured conflict report.

## Why Include Failures
1. Demonstrates production mindset and transparent risk handling.
2. Shows roadmap grounded in observed behavior, not generic claims.
3. Improves trust in the project evaluation narrative.
