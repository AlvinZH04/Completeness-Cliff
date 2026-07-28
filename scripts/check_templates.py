"""Verify chat-template think-tag behavior for every registered model (CPU-only).

Asserts that src/config.py's `template_appends_think` flags match reality and
prints the rendered prompt tails + example injection prompts.

    python scripts/check_templates.py [model_key ...]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import MODELS
from src.generation import build_injection_prompt, render_base_prompt


def check(key: str) -> None:
    from transformers import AutoTokenizer
    cfg = MODELS[key]
    tok = AutoTokenizer.from_pretrained(cfg.hf_id)
    print(f"\n=== {key} ({cfg.hf_id}, style={cfg.style}) ===")

    open_marker = cfg.think_open.strip()
    modes = [True] if cfg.style != "hybrid" else [True, False]
    for thinking in modes:
        base = render_base_prompt(tok, cfg, "What is 2+2?", enable_thinking=thinking)
        ends_think = base.rstrip().endswith(open_marker)
        print(f"thinking={thinking}: base tail = {base[-60:]!r} "
              f"(ends with {open_marker!r}: {ends_think})")
        if cfg.style == "thinking":
            assert ends_think == cfg.template_appends_think, (
                f"{key}: template_appends_think={cfg.template_appends_think} "
                f"but rendered prompt ends_think={ends_think}")
        if cfg.thinking_switch == "system_token":
            assert (cfg.thinking_system_token in base) == thinking, (
                f"{key}: system thinking token presence mismatch")

        inj_open = build_injection_prompt(tok, cfg, "What is 2+2?",
                                          "WRONG TRACE HERE", close_think=False,
                                          thinking_mode=thinking)
        inj_closed = build_injection_prompt(tok, cfg, "What is 2+2?",
                                            "WRONG TRACE HERE", close_think=True,
                                            thinking_mode=thinking)
        print(f"  open   tail: {inj_open[-80:]!r}")
        print(f"  closed tail: {inj_closed[-80:]!r}")
        if cfg.style == "thinking" or (cfg.style == "hybrid" and thinking):
            assert inj_open.count(open_marker) == 1, "duplicated think-open marker!"
            assert inj_closed.rstrip().endswith(cfg.think_close), (
                f"closed prompt must end with {cfg.think_close!r}")
    print("OK")


if __name__ == "__main__":
    keys = sys.argv[1:] or list(MODELS)
    for key in keys:
        check(key)
    print("\nall template checks passed")
