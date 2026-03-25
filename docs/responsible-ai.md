# Responsible AI Notes

## Scope

This project implements local-first responsible AI controls that are practical for a portfolio system:
- time-based split discipline
- model cards
- dataset datasheet summary
- SQL audit logging
- retrieval grounding and refusal behavior
- red-team style RAG evaluation cases
- operational segment fairness slices

## NIST AI RMF Alignment

- Govern: model/reporting docs, review checklist, audit trail
- Map: risk areas documented for leakage, hallucination, unsafe SQL, and rollout decisions
- Measure: ML metrics, RAG eval metrics, experiment guardrails, OPE estimates
- Manage: refusal behavior, SQL allowlists, staged rollout recommendations, human review placeholders

## Current Limits

- Fairness slices use carrier segments, not protected-class fairness attributes
- No formal privacy review or PII handling assessment has been completed
- No SHAP/LIME-style explainability package is wired yet
- Human approval gates exist conceptually but are not enforced by workflow runtime
