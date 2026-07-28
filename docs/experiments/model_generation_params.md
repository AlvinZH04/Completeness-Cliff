# Recommended Generation Parameters (from official HF model cards)

Verified against the HuggingFace model cards on 2026-07-16. `src/config.py` mirrors these values — if you change one, change both.

## Qwen/Qwen3.5-4B (hybrid; also applies to Qwen3.5-9B, Qwen3.5-35B-A3B)

Thinking mode is **on by default** (`<think>\n...\n</think>` before the response). Disable via `chat_template_kwargs={"enable_thinking": False}`.

| Mode | temperature | top_p | top_k | min_p | presence_penalty |
|------|------------|-------|-------|-------|------------------|
| Thinking, general | 1.0 | 0.95 | 20 | 0.0 | 1.5 |
| Thinking, precise coding | 0.6 | 0.95 | 20 | 0.0 | 0.0 |
| Non-thinking, general | 0.7 | 0.8 | 20 | 0.0 | 1.5 |
| Non-thinking, reasoning | 1.0 | 1.0 | 40 | 0.0 | 2.0 |

- Output length: 32,768 general; **81,920 for complex math** problems.
- Context: 262,144 native. vLLM: `--reasoning-parser qwen3` when serving (we use offline API + raw prompts instead).
- **We use:** Thinking-general for thinking mode; Non-thinking-reasoning for non-thinking mode (math tasks).

## Qwen/Qwen3-4B-Thinking-2507

Thinking **only** — chat template automatically appends `<think>\n`; output contains only `</think>` (no opening tag). Do **not** pass `enable_thinking`.

| temperature | top_p | top_k | min_p | presence_penalty |
|------------|-------|-------|-------|------------------|
| 0.6 | 0.95 | 20 | 0.0 | 0–2 (we use 1.0) |

- Output length: 32,768 standard; **81,920 for complex math/coding**. Context: 262,144 native.

## Qwen/Qwen3-4B-Instruct-2507

Non-thinking **only**.

| temperature | top_p | top_k | min_p | presence_penalty |
|------------|-------|-------|-------|------------------|
| 0.7 | 0.8 | 20 | 0.0 | 0–2 (we use 1.0) |

- Output length: 16,384 recommended. Context: 262,144 native.

## deepseek-ai/DeepSeek-R1-0528-Qwen3-8B

| temperature | top_p |
|------------|-------|
| 0.6 | 0.95 |

- Max generation for benchmarks: 64K tokens. System prompt supported. No need to force `<think>\n` at output start for 0528 (unlike older R1 distills) — but its chat template still emits the think pattern; verify with `scripts/check_templates.py` before use.

## google/gemma-4-E2B-it (later phase — non-Qwen generalization check)

Hybrid reasoning: thinking enabled by `<|think|>` token at the start of the system prompt; reasoning emitted as `<|channel>thought\n...<channel|>` before the answer (NOT Qwen-style `<think>` tags — injection code needs a per-model marker adapter).

| temperature | top_p | top_k |
|------------|-------|-------|
| 1.0 | 0.95 | 64 |

- One sampling config for all use cases per card. Context 128K. 2.3B effective params (5.1B with embeddings, Per-Layer Embeddings). Cached locally; E4B/E4B-it also cached for scale-up.

## Notes

- **Never use greedy decoding** with thinking models (model cards warn of repetition/degradation; and pass@k needs sample diversity anyway).
- vLLM `SamplingParams` supports temperature/top_p/top_k/min_p/presence_penalty directly (vllm 0.17.0 ✓).
- **Always check truncation rate** after generation (`finish_reason == "length"`); target < 2% per cell, otherwise raise `max_new_tokens` (32,768 → 81,920) and rerun.
