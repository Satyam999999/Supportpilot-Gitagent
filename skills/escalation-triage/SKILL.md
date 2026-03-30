---
name: escalation-triage
description: Escalate ambiguous, risky, or low-confidence support requests.
license: MIT
metadata:
  author: satyamghosh
  version: "1.0.0"
  category: support
---

# Skill: Escalation Triage

## Purpose
Escalate cases that are risky, ambiguous, or low-confidence.

## Triggers
1. Confidence below threshold.
2. Account security or identity risk.
3. Contradictory or missing policy context.
4. Explicit user request for human escalation.

## Outputs
- escalate: true
- escalation_summary

## Escalation Summary Format
- user_issue
- detected_category
- attempted_resolution
- reason_for_escalation
- suggested_next_action
