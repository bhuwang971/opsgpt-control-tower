# PEFT Sandbox

## Purpose

This sandbox exists for interview loops that care about LLM adaptation depth.
It is intentionally separate from the main product runtime.

## Included Paths

- LoRA instruction-tune recipe
- QLoRA instruction-tune recipe

## Why It Is Separate

- The main OpsGPT story is governed analytics, RAG safety, experimentation, and evaluation
- PEFT is valuable for LLM engineer roles, but not required for the core control-tower narrative

## Recommended Follow-Up

- Add a small Hugging Face trainer script
- Track train/eval loss, token-level accuracy, and cost/runtime notes
- Compare full fine-tune vs LoRA vs QLoRA trade-offs in a model card
