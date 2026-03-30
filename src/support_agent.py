from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import List

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
HIGH_RISK_PATTERNS = {
    "another customer",
    "disable 2fa immediately",
    "recover my account",
    "lost access to my email and phone",
    "legal confirmation",
    "compliance liability",
    "ignore policy",
}
POLICY_CONFLICT_PATTERNS = {
    "two different things",
    "outside the stated policy",
    "approve it now",
}
HUMAN_ESCALATION_HINTS = {
    "manager",
    "human",
    "live agent",
    "escalate",
    "urgent",
}
AMBIGUOUS_FOLLOWUP_TOKENS = {
    "that",
    "it",
    "this",
    "those",
    "them",
    "now",
}


@dataclass
class KBEntry:
    question: str
    answer: str


def tokenize(text: str) -> List[str]:
    return TOKEN_PATTERN.findall(text.lower())


def contains_any_phrase(text: str, phrases: set[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def cosine_similarity(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0

    intersection = set(a.keys()) & set(b.keys())
    numerator = sum(a[token] * b[token] for token in intersection)
    denominator = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    if denominator == 0:
        return 0.0
    return numerator / denominator


def minmax_scale(values: List[float]) -> List[float]:
    if not values:
        return []
    v_min = min(values)
    v_max = max(values)
    if math.isclose(v_min, v_max):
        return [0.0 for _ in values]
    return [(v - v_min) / (v_max - v_min) for v in values]


def fetch_user_subscription(user_id: str) -> dict:
    demo_subscriptions = {
        "demo-user": {"plan": "Pro", "status": "active"},
        "trial-user": {"plan": "Free", "status": "trial"},
    }
    return demo_subscriptions.get(user_id, {"plan": "Unknown", "status": "unverified"})


def load_kb(path: Path) -> List[KBEntry]:
    text = path.read_text(encoding="utf-8")
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    entries: List[KBEntry] = []

    for block in blocks:
        lines = block.splitlines()
        q_line = next((line for line in lines if line.startswith("Q:")), "")
        a_line = next((line for line in lines if line.startswith("A:")), "")
        if q_line and a_line:
            entries.append(KBEntry(question=q_line[2:].strip(), answer=a_line[2:].strip()))

    if not entries:
        raise ValueError("No valid Q/A entries found in KB file")

    return entries


class SupportPilotAgent:
    def __init__(self, kb_path: Path, threshold: float = 0.65) -> None:
        self.threshold = threshold
        self.entries = load_kb(kb_path)
        self._entry_vectors = [Counter(tokenize(f"{entry.question} {entry.answer}")) for entry in self.entries]
        self._entry_tokens = [tokenize(f"{entry.question} {entry.answer}") for entry in self.entries]
        self._bm25 = BM25Okapi(self._entry_tokens) if BM25Okapi is not None else None
        self._semantic_texts = [f"{entry.question} {entry.answer}" for entry in self.entries]
        self._embedder = None
        self._semantic_embeddings = None
        if SentenceTransformer is not None:
            try:
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
                self._semantic_embeddings = self._embedder.encode(
                    self._semantic_texts,
                    normalize_embeddings=True,
                    convert_to_numpy=True,
                )
            except Exception:
                self._embedder = None
                self._semantic_embeddings = None
        self.memory: List[str] = []

    def _classify(self, query: str) -> str:
        q = query.lower()
        if any(k in q for k in ["payment", "invoice", "refund", "billing", "plan"]):
            return "billing"
        if any(k in q for k in ["password", "2fa", "security", "otp", "login"]):
            return "account"
        if any(k in q for k in ["api", "error", "bug", "dashboard", "rate limit"]):
            return "technical"
        if any(k in q for k in ["policy", "terms", "legal", "compliance"]):
            return "policy"
        return "other"

    def _high_risk(self, query: str) -> bool:
        q = query.lower()
        return contains_any_phrase(q, HIGH_RISK_PATTERNS)

    def _policy_conflict(self, query: str) -> bool:
        q = query.lower()
        return contains_any_phrase(q, POLICY_CONFLICT_PATTERNS)

    def _human_requested(self, query: str) -> bool:
        q = query.lower()
        return any(k in q for k in HUMAN_ESCALATION_HINTS)

    def _build_query(self, current_query: str) -> str:
        if not self.memory:
            return current_query
        current_tokens = set(tokenize(current_query))
        if not any(token in current_tokens for token in AMBIGUOUS_FOLLOWUP_TOKENS):
            return current_query
        last_turn = self.memory[-1]
        return f"{last_turn} {current_query}"

    def _semantic_scores(self, query: str) -> List[float] | None:
        if self._embedder is None or self._semantic_embeddings is None:
            return None
        query_embedding = self._embedder.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )[0]
        return [float(query_embedding.dot(doc_embedding)) for doc_embedding in self._semantic_embeddings]

    def _bm25_scores(self, query: str) -> List[float] | None:
        if self._bm25 is None:
            return None
        return [float(score) for score in self._bm25.get_scores(tokenize(query))]

    def _retrieve(self, query: str, top_k: int = 3) -> List[tuple[int, float]]:
        q_vec = Counter(tokenize(query))
        lexical_scores = [cosine_similarity(q_vec, vec) for vec in self._entry_vectors]
        semantic_scores = self._semantic_scores(query)
        bm25_scores = self._bm25_scores(query)

        score_components = {
            "semantic": minmax_scale(semantic_scores) if semantic_scores is not None else None,
            "bm25": minmax_scale(bm25_scores) if bm25_scores is not None else None,
            "lexical": minmax_scale(lexical_scores),
        }
        default_weights = {"semantic": 0.45, "bm25": 0.35, "lexical": 0.20}
        active_components = [name for name, values in score_components.items() if values is not None]

        weight_total = sum(default_weights[name] for name in active_components)
        scored = []
        for idx in range(len(self.entries)):
            hybrid_score = 0.0
            for name in active_components:
                hybrid_score += (default_weights[name] / weight_total) * score_components[name][idx]
            scored.append((idx, round(hybrid_score, 4)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def _confidence(self, retrieval_scores: List[float], citations: int, risk_penalty: bool) -> float:
        if retrieval_scores:
            best_retrieval = retrieval_scores[0]
            avg_retrieval = sum(retrieval_scores) / len(retrieval_scores)
        else:
            best_retrieval = 0.0
            avg_retrieval = 0.0

        retrieval_component = ((best_retrieval * 0.6) + (avg_retrieval * 0.4)) * 0.50

        citation_component = min(citations / 3, 1.0) * 0.20
        policy_component = (0.0 if risk_penalty else 1.0) * 0.30

        return round(retrieval_component + citation_component + policy_component, 3)

    def _escalation_reasons(self, query: str, confidence: float, citations: int) -> List[str]:
        reasons: List[str] = []
        if confidence < self.threshold:
            reasons.append("low_confidence")
        if citations == 0:
            reasons.append("no_grounded_context")
        if self._high_risk(query):
            reasons.append("high_risk_request")
        if self._policy_conflict(query):
            reasons.append("policy_conflict")
        if self._human_requested(query):
            reasons.append("human_requested")
        return reasons

    def _confidence_reason(self, retrieval_scores: List[float], risk_penalty: bool) -> str:
        if not retrieval_scores:
            retrieval_note = "no grounded retrieval"
        elif retrieval_scores[0] >= 0.75:
            retrieval_note = "strong retrieval match"
        elif retrieval_scores[0] >= 0.45:
            retrieval_note = "moderate retrieval match"
        else:
            retrieval_note = "weak retrieval match"

        risk_note = "risk flags detected" if risk_penalty else "no policy-risk flags"
        return f"{retrieval_note}; {risk_note}"

    def ask(self, query: str, user_id: str = "demo-user") -> dict:
        category = self._classify(query)
        rewritten_query = self._build_query(query)
        top = self._retrieve(rewritten_query, top_k=3)

        citations = []
        retrieval_scores = []
        for idx, score in top:
            if score > 0:
                entry = self.entries[idx]
                citations.append(entry.question)
                retrieval_scores.append(score)

        risk_penalty = self._high_risk(query) or self._policy_conflict(query)
        confidence = self._confidence(retrieval_scores, len(citations), risk_penalty)
        confidence_reason = self._confidence_reason(retrieval_scores, risk_penalty)

        escalation_reasons = self._escalation_reasons(query, confidence, len(citations))
        escalate = len(escalation_reasons) > 0

        if citations:
            best_idx = top[0][0]
            answer = self.entries[best_idx].answer
        else:
            answer = "I do not have enough grounded information to answer reliably."

        if self._high_risk(query) or self._policy_conflict(query):
            answer = "I cannot safely complete this request. I am escalating it to a human specialist."

        tool_data = None
        if category == "billing" and not escalate:
            tool_data = fetch_user_subscription(user_id)
            answer = (
                f"{answer} Your current plan is {tool_data['plan']} "
                f"with account status {tool_data['status']}."
            )

        escalation_summary = None
        if escalate:
            escalation_summary = (
                f"Issue category: {category}. "
                f"Reason(s): {', '.join(escalation_reasons)}. "
                f"User query: {query}"
            )

        self.memory.append(query)
        if len(self.memory) > 10:
            self.memory = self.memory[-10:]

        return {
            "answer": answer,
            "confidence": confidence,
            "confidence_reason": confidence_reason,
            "citations": citations,
            "category": category,
            "escalate": escalate,
            "escalation_summary": escalation_summary,
            "escalation_reasons": escalation_reasons,
            "rewritten_query": rewritten_query,
            "tool_data": tool_data,
        }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    agent = SupportPilotAgent(kb_path=project_root / "data" / "faq_kb.md")

    print("SupportPilot is ready. Type 'exit' to quit.")
    while True:
        query = input("\nUser> ").strip()
        if query.lower() == "exit":
            break
        result = agent.ask(query)
        print(f"Answer: {result['answer']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Confidence Reason: {result['confidence_reason']}")
        print(f"Category: {result['category']}")
        print(f"Escalate: {result['escalate']}")
        print(f"Rewritten Query: {result['rewritten_query']}")
        if result["citations"]:
            print("Citations:")
            for c in result["citations"]:
                print(f"- {c}")
        if result["tool_data"]:
            print(f"Tool Data: {result['tool_data']}")
        if result["escalation_summary"]:
            print(f"Escalation Summary: {result['escalation_summary']}")


if __name__ == "__main__":
    main()
