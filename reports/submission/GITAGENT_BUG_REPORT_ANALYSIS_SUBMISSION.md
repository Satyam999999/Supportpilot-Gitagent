# GitAgent Bug Report & Analysis
**Agent:** SupportPilot Agent  
**Tester:** Satyam Ghosh  
**Date:** 30 March 2026  
**Total Issues Found:** 12  
**Critical:** 4 | **High:** 5 | **Medium:** 3 | **Low:** 0

## Executive Summary
SupportPilot performs well for baseline FAQ resolution and risk-aware escalation, but deep testing reveals contract drift, state-isolation gaps, and weak trust-boundary controls. The most critical issue is cross-session memory bleed in shared-instance deployments, which creates a direct privacy and data isolation risk. The second critical class is untrusted data handling: tool output and KB content can alter responses without robust sanitization and integrity checks.

## Bug Index
| # | Bug Title | Layer | Severity | Status |
|---|---|---|---|---|
| B-001 | Runtime invokes undeclared tool when billing intent is detected | Schema | High | Open |
| B-002 | Manifest lacks machine-actionable error taxonomy and retry semantics | Schema | Medium | Open |
| B-003 | Capability contract lacks version/lifecycle metadata causing upgrade ambiguity | Schema | Medium | Open |
| B-004 | Session memory truncates context without summarization after window overflow | Memory | High | Open |
| B-005 | Shared agent instance allows cross-session context bleed | Memory | Critical | Open |
| B-006 | Repeated identical requests mutate memory and trigger duplicate tool calls | Memory | High | Open |
| B-007 | Tool output injection propagates attacker-controlled content to user response | Security | Critical | Open |
| B-008 | Poisoned knowledge base content changes behavior for all users | Security | Critical | Open |
| B-009 | Query keyword smuggling manipulates category and tool-path routing | Security | High | Open |
| B-010 | Missing trace correlation and structured failure envelope on runtime errors | Observability | High | Open |
| B-011 | Output schema stability is weak for nullable fields across scenarios | Observability | Medium | Open |
| B-012 | Registry trust assumptions lack integrity verification for tampered metadata | Ecosystem | Critical | Open |

## Detailed Bug Reports

### B-001: Runtime invokes undeclared tool when billing intent is detected
**Layer:** Schema / Memory / Security / Observability  
**Severity:** High  
**Likelihood:** Common  
**Who encounters this:** Integrators relying on manifest contracts.

**Description:**
Billing-path responses include tool output even though the manifest declares no tools. This creates declaration-runtime mismatch and weakens interop guarantees.

**Steps to Reproduce:**
1. Inspect manifest and verify tools are empty.
2. Send a safe billing query.
3. Observe tool-derived data in response payload.

**Expected Behavior:**
Only declared tools should execute.

**Actual Behavior:**
Undeclared tool path executes at runtime.

**Why Most Testers Miss This:**
Most tests verify answer quality but not manifest/runtime parity.

### B-002: Manifest lacks machine-actionable error taxonomy and retry semantics
**Layer:** Schema / Memory / Security / Observability  
**Severity:** Medium  
**Likelihood:** Common  
**Who encounters this:** Orchestrator and platform teams.

**Description:**
Failure outcomes are not encoded with stable error classes and retry safety signals. This blocks deterministic automation and increases duplicate side-effect risk.

**Steps to Reproduce:**
1. Trigger a tool or retrieval failure.
2. Inspect error payload shape.
3. Attempt to map retry policy programmatically.

**Expected Behavior:**
Structured error codes with retry class metadata.

**Actual Behavior:**
Ambiguous failure representation.

**Why Most Testers Miss This:**
Single-process test loops do not simulate orchestrated retries.

### B-003: Capability contract lacks version/lifecycle metadata causing upgrade ambiguity
**Layer:** Schema / Memory / Security / Observability  
**Severity:** Medium  
**Likelihood:** Rare  
**Who encounters this:** Teams rolling out new versions in production.

**Description:**
Capabilities are named but not versioned with deprecation windows. This increases breakage risk during upgrades.

**Steps to Reproduce:**
1. Integrate agent in a workflow with fixed assumptions.
2. Upgrade capability behavior without lifecycle metadata.
3. Observe downstream incompatibility.

**Expected Behavior:**
Versioned capabilities with deprecation/removal markers.

**Actual Behavior:**
No machine-readable compatibility lifecycle.

**Why Most Testers Miss This:**
Release-cycle regressions are not visible in one-time evaluations.

### B-004: Session memory truncates context without summarization after window overflow
**Layer:** Schema / Memory / Security / Observability  
**Severity:** High  
**Likelihood:** Common  
**Who encounters this:** Users with long issue threads.

**Description:**
Context eviction is hard truncation only. Early constraints disappear and reduce answer reliability.

**Steps to Reproduce:**
1. Run 15+ conversation turns.
2. Ask ambiguous follow-up.
3. Verify early context no longer affects reasoning.

**Expected Behavior:**
Older turns summarized before eviction.

**Actual Behavior:**
Older turns are dropped.

**Why Most Testers Miss This:**
Short scripts rarely exceed memory limits.

### B-005: Shared agent instance allows cross-session context bleed
**Layer:** Schema / Memory / Security / Observability  
**Severity:** Critical  
**Likelihood:** Common  
**Who encounters this:** Multi-user deployments with shared instance caching.

**Description:**
Shared mutable memory allows one session’s context to influence another. This is a tenant isolation failure.

**Steps to Reproduce:**
1. Start session A and add context-rich turns.
2. Reuse same agent instance for session B.
3. Trigger ambiguous rewrite in session B.

**Expected Behavior:**
Strict per-session/per-user state isolation.

**Actual Behavior:**
Session B can inherit A-derived context.

**Why Most Testers Miss This:**
Single-user local demos hide tenancy issues.

### B-006: Repeated identical requests mutate memory and trigger duplicate tool calls
**Layer:** Schema / Memory / Security / Observability  
**Severity:** High  
**Likelihood:** Common  
**Who encounters this:** Users behind flaky networks and retrying orchestrators.

**Description:**
Identical calls are not idempotent. Retries can duplicate state mutation and tool invocation.

**Steps to Reproduce:**
1. Send a billing request once.
2. Replay same request with same inputs.
3. Observe duplicate state/tool-path behavior.

**Expected Behavior:**
Deterministic idempotent handling for duplicates.

**Actual Behavior:**
Full re-execution occurs on replay.

**Why Most Testers Miss This:**
Manual QA often avoids duplicate replay tests.

### B-007: Tool output injection propagates attacker-controlled content to user response
**Layer:** Schema / Memory / Security / Observability  
**Severity:** Critical  
**Likelihood:** Common  
**Who encounters this:** Users when external tools are compromised.

**Description:**
Tool output is reflected into user response without strict trust handling. Compromised tools can inject phishing or policy-subverting text.

**Steps to Reproduce:**
1. Mock tool output with malicious payload.
2. Execute billing path.
3. Confirm payload appears in final answer.

**Expected Behavior:**
Tool output treated as untrusted and sanitized.

**Actual Behavior:**
Payload propagates into response.

**Why Most Testers Miss This:**
Positive-path tests use only well-formed tool responses.

### B-008: Poisoned knowledge base content changes behavior for all users
**Layer:** Schema / Memory / Security / Observability  
**Severity:** Critical  
**Likelihood:** Rare  
**Who encounters this:** All users querying poisoned KB topics.

**Description:**
KB entries are trusted as authoritative. Poisoned content can inject false instructions and capability claims at scale.

**Steps to Reproduce:**
1. Add adversarial KB entry.
2. Query related topic from multiple sessions.
3. Observe poisoned answer propagation.

**Expected Behavior:**
KB entries should pass integrity and policy checks before serving.

**Actual Behavior:**
Poisoned entries are retrieved and returned.

**Why Most Testers Miss This:**
Benchmark corpora are clean and non-adversarial.

### B-009: Query keyword smuggling manipulates category and tool-path routing
**Layer:** Schema / Memory / Security / Observability  
**Severity:** High  
**Likelihood:** Common  
**Who encounters this:** Any user crafting mixed-intent strings.

**Description:**
Simple keyword routing allows intent steering by token stuffing. This can force unintended behavior paths.

**Steps to Reproduce:**
1. Send baseline account query.
2. Add billing keywords in same request.
3. Observe route/category flip.

**Expected Behavior:**
Intent model should resist keyword stuffing and mixed-intent manipulation.

**Actual Behavior:**
Token presence alone can change route.

**Why Most Testers Miss This:**
Most prompts are clean, not adversarial.

### B-010: Missing trace correlation and structured failure envelope on runtime errors
**Layer:** Schema / Memory / Security / Observability  
**Severity:** High  
**Likelihood:** Common  
**Who encounters this:** Incident responders and SRE teams.

**Description:**
Errors do not consistently emit trace correlation fields or execution-stage metadata. This slows diagnosis and safe remediation during incidents.

**Steps to Reproduce:**
1. Trigger a runtime failure.
2. Inspect logs/output for trace id and stage context.
3. Attempt distributed root-cause analysis.

**Expected Behavior:**
Every response/failure includes trace id and stage metadata.

**Actual Behavior:**
Tracing context is incomplete or absent.

**Why Most Testers Miss This:**
Local single-process tests do not require trace stitching.

### B-011: Output schema stability is weak for nullable fields across scenarios
**Layer:** Schema / Memory / Security / Observability  
**Severity:** Medium  
**Likelihood:** Common  
**Who encounters this:** Typed clients and downstream automation services.

**Description:**
Field presence and nullability vary by path without strict contract enforcement. This increases parser fragility.

**Steps to Reproduce:**
1. Send normal, risky, and unknown prompts.
2. Compare output field shapes and nullability.
3. Validate against strict typed parser.

**Expected Behavior:**
Stable output schema with explicit required/optional semantics.

**Actual Behavior:**
Path-dependent shape variation.

**Why Most Testers Miss This:**
Manual inspection tolerates variability.

### B-012: Registry trust assumptions lack integrity verification for tampered metadata
**Layer:** Schema / Memory / Security / Observability  
**Severity:** Critical  
**Likelihood:** Edge Case  
**Who encounters this:** Deployments consuming manifests from compromised paths.

**Description:**
Registry-provided metadata is not cryptographically verified. Tampered contracts can be accepted silently.

**Steps to Reproduce:**
1. Simulate tampered manifest in distribution path.
2. Load modified artifact.
3. Confirm acceptance without trust-failure signal.

**Expected Behavior:**
Load should fail on signature/checksum mismatch.

**Actual Behavior:**
Trust is assumed by default.

**Why Most Testers Miss This:**
Most validation focuses on schema shape, not supply-chain threats.

## Patterns & Systemic Issues
1. Contract drift: manifest declarations and runtime behavior diverge in critical paths.
2. Trust-boundary weakness: tool, KB, and registry inputs are not treated as adversarial by default.
3. Distributed-systems readiness gap: idempotency, isolation, and traceability are not first-class controls.

## Conclusion
This submission demonstrates reproducible, multi-layer reliability and security risk across schema, memory, trust-boundary, and observability controls.

Key outcome:
1. The findings are not cosmetic defects; they represent systemic failure modes under realistic production conditions.
2. The highest-risk defects (cross-session bleed, untrusted input propagation, and registry trust assumptions) have multi-tenant blast radius.
3. The test evidence indicates that happy-path benchmark quality can coexist with critical operational risk.

Overall assessment:
1. Risk posture under tested conditions is critical.
2. The defect profile is evidence-backed and suitable for escalation to framework-level interoperability and safety discussion.

## Positive Findings
1. High-risk prompts are frequently escalated instead of answered directly.
2. Citation-based grounding is present and operational.
3. Confidence outputs provide useful operator signal.
4. Testing depth includes state and security scenarios beyond happy path.
5. Response shape already contains useful fields for future hardening.
