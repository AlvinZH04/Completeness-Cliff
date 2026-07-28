"""vLLM engine wrapper and chat-template prompt building.

All experiment code builds *raw string prompts* (chat template rendered here,
injected thinking appended as plain text) and generates with the offline
vLLM ``LLM`` API. This gives exact control over what sits inside <think>.
"""

from dataclasses import dataclass

from .config import ModelConfig


def render_base_prompt(tokenizer, model_cfg: ModelConfig, user_text: str,
                       enable_thinking: bool = True) -> str:
    """Render the chat template up to (and including) the assistant header."""
    messages = [{"role": "user", "content": user_text}]
    kwargs = dict(tokenize=False, add_generation_prompt=True)
    if model_cfg.style == "hybrid":
        if model_cfg.thinking_switch == "system_token":
            if enable_thinking:
                messages = [{"role": "system",
                             "content": model_cfg.thinking_system_token}] + messages
        else:
            kwargs["enable_thinking"] = enable_thinking
    return tokenizer.apply_chat_template(messages, **kwargs)


def ensure_think_open(prompt: str, model_cfg: ModelConfig) -> str:
    """Make the prompt end inside an open think block."""
    if prompt.rstrip().endswith(model_cfg.think_open.strip()):
        return prompt
    return prompt + model_cfg.think_open


def build_injection_prompt(tokenizer, model_cfg: ModelConfig, user_text: str,
                           trace_text: str, close_think: bool,
                           thinking_mode: bool = True) -> str:
    """Base prompt + injected (wrong) reasoning.

    thinking models / hybrid-thinking: trace goes inside the think channel; if
    ``close_think``, append the close marker so the model can only answer.
    instruct models / hybrid-nothink: trace is prefilled as the beginning of the
    assistant's visible response (``close_think`` handled by the caller via a
    transition appended to trace_text; here it is ignored).
    """
    is_thinking = model_cfg.style == "thinking" or (
        model_cfg.style == "hybrid" and thinking_mode)
    base = render_base_prompt(tokenizer, model_cfg, user_text,
                              enable_thinking=is_thinking)
    if is_thinking:
        # never allow a stray close marker inside the injected trace
        clean = trace_text.split(model_cfg.think_close)[0].rstrip()
        prompt = ensure_think_open(base, model_cfg) + clean
        if close_think:
            prompt += model_cfg.think_close_render
        return prompt
    return base + trace_text


@dataclass
class GenSample:
    text: str
    n_tokens: int
    finish_reason: str  # "stop" | "length" | ...


class Engine:
    def __init__(self, model_cfg: ModelConfig, max_model_len: int | None = None,
                 gpu_memory_utilization: float = 0.9, seed: int = 0,
                 enforce_eager: bool = False, attention_backend: str | None = None):
        from vllm import LLM
        self.cfg = model_cfg
        kwargs = {}
        if attention_backend:
            kwargs["attention_backend"] = attention_backend
        self.llm = LLM(
            model=model_cfg.hf_id,
            max_model_len=max_model_len or model_cfg.max_model_len,
            gpu_memory_utilization=gpu_memory_utilization,
            seed=seed,
            enforce_eager=enforce_eager,
            **kwargs,
        )
        self.tokenizer = self.llm.get_tokenizer()

    def generate(self, prompts: list[str], n: int, max_new_tokens: int,
                 sampling=None, seed: int | None = None,
                 stop: list[str] | None = None) -> list[list[GenSample]]:
        """Generate n samples per prompt. Returns one list of GenSample per prompt.

        `stop`: optional stop strings. Used for forced-answer cells, where the model
        should halt once the answer expression closes instead of rambling into the
        token cap (see findings.md C6).
        """
        from vllm import SamplingParams
        s = sampling or self.cfg.sampling
        params = SamplingParams(
            n=n,
            temperature=s.temperature,
            top_p=s.top_p,
            top_k=s.top_k,
            min_p=s.min_p,
            presence_penalty=s.presence_penalty,
            max_tokens=max_new_tokens,
            seed=seed,
            skip_special_tokens=self.cfg.skip_special_tokens,
            stop=stop,
            include_stop_str_in_output=True,
        )
        outs = self.llm.generate(prompts, params)
        results = []
        for out in outs:
            results.append([
                GenSample(text=o.text, n_tokens=len(o.token_ids),
                          finish_reason=str(o.finish_reason))
                for o in out.outputs
            ])
        return results
