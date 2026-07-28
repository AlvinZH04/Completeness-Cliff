"""Project configuration: paths, model registry with card-recommended sampling params.

Sampling parameters are sourced from the official HF model cards (see
docs/experiments/model_generation_params.md). If you change values here,
update that doc too.
"""

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = PROJECT_ROOT / "logs"

THINK_OPEN = "<think>"
THINK_CLOSE = "</think>"


@dataclass
class SamplingConfig:
    temperature: float
    top_p: float
    top_k: int
    min_p: float = 0.0
    presence_penalty: float = 0.0


@dataclass
class ModelConfig:
    key: str
    hf_id: str
    # 'thinking'  : reasoning-only model; chat template auto-appends the think-open
    #               marker (Qwen *-Thinking-2507) or model emits it (R1-style).
    # 'instruct'  : non-thinking model, no think tags.
    # 'hybrid'    : one set of weights, thinking toggled per `thinking_switch`.
    style: str
    sampling: SamplingConfig
    # sampling for non-thinking mode (hybrid models only)
    sampling_nothink: SamplingConfig | None = None
    max_model_len: int = 131072
    # default generation budget; complex math (AIME) may need 81920 per model card
    default_max_new_tokens: int = 32768
    # whether apply_chat_template(add_generation_prompt=True) already ends with
    # the think-open marker — verified empirically by scripts/check_templates.py
    template_appends_think: bool = False
    # per-model reasoning-channel markers (Qwen defaults; Gemma 4 differs)
    think_open: str = "<think>\n"
    think_close: str = "</think>"
    # exact string appended to force-close the think channel in injection prompts
    think_close_render: str = "\n</think>\n\n"
    # how hybrid models toggle thinking: 'kwarg' (enable_thinking template kwarg)
    # or 'system_token' (prepend a system message containing thinking_system_token)
    thinking_switch: str | None = None
    thinking_system_token: str = "<|think|>"
    # Gemma 4 channel markers are special tokens vLLM strips by default; grading
    # needs them visible in the generated text
    skip_special_tokens: bool = True


MODELS: dict[str, ModelConfig] = {}


def _register(cfg: ModelConfig) -> None:
    MODELS[cfg.key] = cfg


_register(ModelConfig(
    key="qwen3-4b-thinking",
    hf_id="Qwen/Qwen3-4B-Thinking-2507",
    style="thinking",
    # model card: Temperature=0.6, TopP=0.95, TopK=20, MinP=0
    sampling=SamplingConfig(temperature=0.6, top_p=0.95, top_k=20, min_p=0.0),
    default_max_new_tokens=32768,
    template_appends_think=True,
))

_register(ModelConfig(
    key="qwen3-4b-instruct",
    hf_id="Qwen/Qwen3-4B-Instruct-2507",
    style="instruct",
    # model card: Temperature=0.7, TopP=0.8, TopK=20, MinP=0
    sampling=SamplingConfig(temperature=0.7, top_p=0.8, top_k=20, min_p=0.0),
    default_max_new_tokens=16384,
))

_register(ModelConfig(
    key="qwen3.5-4b",
    hf_id="Qwen/Qwen3.5-4B",
    style="hybrid",
    thinking_switch="kwarg",
    # thinking mode, general tasks
    sampling=SamplingConfig(temperature=1.0, top_p=0.95, top_k=20, min_p=0.0,
                            presence_penalty=1.5),
    # non-thinking mode, reasoning tasks
    sampling_nothink=SamplingConfig(temperature=1.0, top_p=1.0, top_k=40, min_p=0.0,
                                    presence_penalty=2.0),
    default_max_new_tokens=32768,
))

# Gemma 4: thinking toggled by <|think|> in a system turn; generation format is
# '<|channel>thought\n{reasoning}<channel|>{answer}' (verified empirically
# 2026-07-18 on E2B-it). Channel markers are special tokens -> skip_special_tokens
# must be False so grading can split channels.
_register(ModelConfig(
    key="gemma-4-e2b",
    hf_id="google/gemma-4-E2B-it",
    style="hybrid",
    # model card: temperature=1.0, top_p=0.95, top_k=64 for all use cases
    sampling=SamplingConfig(temperature=1.0, top_p=0.95, top_k=64, min_p=0.0),
    sampling_nothink=SamplingConfig(temperature=1.0, top_p=0.95, top_k=64, min_p=0.0),
    max_model_len=131072,
    default_max_new_tokens=32768,
    think_open="<|channel>thought\n",
    think_close="<channel|>",
    think_close_render="<channel|>",
    thinking_switch="system_token",
    skip_special_tokens=False,
))

_register(ModelConfig(
    key="r1-qwen3-8b",
    hf_id="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
    style="thinking",
    sampling=SamplingConfig(temperature=0.6, top_p=0.95, top_k=-1, min_p=0.0),
    default_max_new_tokens=32768,
))


# Answer-format instructions appended to questions, per task kind.
MATH_INSTRUCTION = "Please reason step by step, and put your final answer within \\boxed{}."
RG_INSTRUCTION = "When you are done, write your final answer within <answer></answer> tags."

# generation budget when the think block is force-closed (final answer only)
ANSWER_ONLY_MAX_TOKENS = 4096

# truncation-rate threshold above which a cell is flagged in summaries
TRUNCATION_GATE = 0.02
