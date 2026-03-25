from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from math import log
from pathlib import Path

STOPWORDS = {
    "a",
    "about",
    "all",
    "an",
    "and",
    "are",
    "do",
    "does",
    "exact",
    "for",
    "how",
    "in",
    "is",
    "it",
    "local",
    "of",
    "on",
    "say",
    "show",
    "the",
    "their",
    "there",
    "these",
    "this",
    "to",
    "what",
    "with",
}


@dataclass(frozen=True)
class RetrievalChunk:
    source: str
    text: str


@dataclass(frozen=True)
class RetrievalHit:
    source: str
    excerpt: str
    score: float


CORPUS_PATHS = [
    "README.md",
    "docs/architecture.md",
    "docs/implementation-cadence-plan.md",
    "docs/runbook.md",
    "warehouse/glossary.md",
]


def build_corpus(repo_root: Path) -> list[RetrievalChunk]:
    chunks: list[RetrievalChunk] = []
    for relative_path in CORPUS_PATHS:
        path = repo_root / relative_path
        content = path.read_text(encoding="utf-8")
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", content) if part.strip()]
        for paragraph in paragraphs:
            chunks.append(RetrievalChunk(source=relative_path, text=paragraph))
    return chunks


def retrieve(question: str, corpus: list[RetrievalChunk], top_k: int = 3) -> list[RetrievalHit]:
    question_tokens = _tokenize(question)
    if not question_tokens:
        return []
    doc_frequency = Counter()
    corpus_tokens = []
    for chunk in corpus:
        tokens = set(_tokenize(chunk.text))
        corpus_tokens.append(tokens)
        for token in tokens:
            doc_frequency[token] += 1

    hits = []
    total_docs = len(corpus)
    for chunk, tokens in zip(corpus, corpus_tokens):
        overlap = set(question_tokens) & tokens
        if not overlap:
            continue
        score = 0.0
        for token in overlap:
            score += 1 + log((total_docs + 1) / (doc_frequency[token] + 1))
        hits.append(
            RetrievalHit(
                source=chunk.source,
                excerpt=_excerpt(chunk.text),
                score=score,
            )
        )
    hits.sort(key=lambda hit: hit.score, reverse=True)
    return hits[:top_k]


def grounded_answer(question: str, hits: list[RetrievalHit]) -> str:
    if not hits or hits[0].score <= 0:
        return "I do not have enough grounded evidence in the local corpus to answer that safely."
    lead = hits[0].excerpt
    if len(hits) == 1:
        return lead
    return f"{lead} Supporting context: {hits[1].excerpt}"


def _tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9_]+", text.lower())
        if token not in STOPWORDS and len(token) > 1
    ]


def _excerpt(text: str, limit: int = 220) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."
