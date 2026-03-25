from __future__ import annotations

from typing import Any


def peft_sandbox_summary() -> dict[str, Any]:
    return {
        "recommended_for": "LLM engineer and applied gen-AI interview variants",
        "status": "sandbox_ready",
        "experiments": [
            {
                "name": "lora_instruction_tune",
                "method": "LoRA",
                "target_modules": ["q_proj", "v_proj"],
                "rank": 16,
                "alpha": 32,
                "dropout": 0.05,
                "expected_value": (
                    "cheap adaptation for prompt-following and domain tone experiments"
                ),
            },
            {
                "name": "qlora_instruction_tune",
                "method": "QLoRA",
                "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
                "rank": 32,
                "alpha": 64,
                "dropout": 0.05,
                "quantization": "4-bit nf4",
                "expected_value": "memory-efficient adaptation path for stronger local models",
            },
        ],
        "notes": [
            (
                "Sandbox is intentionally configuration-first and not part of the"
                " main product runtime."
            ),
            "Add only if the interview loop actually values fine-tuning depth.",
        ],
    }
