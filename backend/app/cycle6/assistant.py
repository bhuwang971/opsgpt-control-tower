from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.control_tower import repo_root
from app.cycle6.retrieval import build_corpus, grounded_answer, retrieve
from app.cycle6.sql_guard import execute_guarded_sql, question_to_sql, sql_summary


@dataclass(frozen=True)
class AssistantResponse:
    mode: str
    answer: str
    citations: list[dict[str, Any]]
    sql: dict[str, Any] | None


def answer_question(question: str) -> AssistantResponse:
    sql_candidate = question_to_sql(question)
    if sql_candidate:
        result = execute_guarded_sql(question=question, statement=sql_candidate)
        return AssistantResponse(
            mode="sql",
            answer=sql_summary(result),
            citations=[
                {
                    "source": "analytics allowlist",
                    "excerpt": (
                        "Query executed against an allowlisted analytics mart "
                        "with LIMIT enforcement."
                    ),
                }
            ],
            sql={
                "statement": result.statement,
                "columns": result.columns,
                "rows": result.rows,
                "audit_id": result.audit_id,
            },
        )

    corpus = build_corpus(repo_root())
    hits = retrieve(question, corpus)
    return AssistantResponse(
        mode="retrieval",
        answer=grounded_answer(question, hits),
        citations=[{"source": hit.source, "excerpt": hit.excerpt} for hit in hits],
        sql=None,
    )
