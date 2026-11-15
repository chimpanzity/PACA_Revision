"""
rps_client.py - OpenRouter call for PACA-RPS. Same client (api_client.make_client), request
shape, retry schedule and usage extraction as the MP harness, with two differences:

  1. It NEVER substitutes a choice. Outcomes: "model" (parsed real choice), "parse_fail",
     "truncation", "api_fail". The session runner aborts on anything but "model".
  2. Any finish_reason == "length" escalates the budget (x2, up to the ceiling), even if the
     truncated text happens to parse; a truncated reply is never accepted as a choice.

Every attempt is recorded (attempts list) and the full response object can be dumped to a raw
JSONL by the caller. The API key never passes through here except inside the client object.
"""
import json, os, sys, time
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_client import make_client, _extract_usage   # noqa: E402,F401  (same client as MP)
from rps_prompts import parse_choice, last_line_choice  # noqa: E402

RPS_CLIENT_VERSION = "rps-client-v1"


@dataclass
class RPSResult:
    status: str                    # model | parse_fail | truncation | api_fail
    choice: str                    # "" unless status == model
    response_text: str = ""
    last_line_choice: str = ""
    latency_ms: int = 0
    retries_used: int = 0          # network retries on the final budget level
    n_attempts: int = 0            # all HTTP attempts, including escalations
    error_message: str = ""
    served_model: str = ""
    generation_id: str = ""
    provider: str = ""
    finish_reason: str = ""
    native_finish_reason: str = ""
    system_fingerprint: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    max_tokens_used: int = 0
    truncated: bool = False
    attempts: list = field(default_factory=list)
    raw: list = field(default_factory=list)       # model_dump() of every response received


def call_rps(client, model, system_prompt, user_prompt, temperature, max_tokens=20000,
             max_tokens_ceiling=80000, top_p=None, max_retries=3) -> RPSResult:
    start = time.time()
    cur = max_tokens
    attempts, raw = [], []
    last_err = ""
    while True:
        for attempt in range(max_retries):
            kw = {"model": model, "max_tokens": cur,
                  "messages": [{"role": "system", "content": system_prompt},
                               {"role": "user", "content": user_prompt}]}
            if temperature is not None:
                kw["temperature"] = temperature
            if top_p is not None:
                kw["top_p"] = top_p
            t0 = time.time()
            try:
                r = client.chat.completions.create(**kw)
                if not getattr(r, "choices", None):
                    raise RuntimeError(f"response without choices; error={getattr(r, 'error', None)}")
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"[:4000]
                attempts.append(dict(max_tokens=cur, attempt=attempt, error=last_err,
                                     latency_ms=int((time.time() - t0) * 1000)))
                if attempt < max_retries - 1:
                    time.sleep(2 ** (attempt + 1)); continue
                return RPSResult("api_fail", "", latency_ms=int((time.time() - start) * 1000),
                                 retries_used=attempt, n_attempts=len(attempts), error_message=last_err,
                                 max_tokens_used=cur, attempts=attempts, raw=raw)
            try: raw.append(r.model_dump())
            except Exception: raw.append({"dump_error": True})
            ch = r.choices[0]
            text = (ch.message.content or "") if ch.message is not None else ""
            fin = getattr(ch, "finish_reason", "") or ""
            pt, ct, rt, tt = _extract_usage(r)
            res = RPSResult("", "", response_text=text, last_line_choice=last_line_choice(text),
                            latency_ms=int((time.time() - start) * 1000), retries_used=attempt,
                            served_model=getattr(r, "model", "") or "", generation_id=getattr(r, "id", "") or "",
                            provider=getattr(r, "provider", "") or "", finish_reason=fin,
                            native_finish_reason=str(getattr(ch, "native_finish_reason", "") or ""),
                            system_fingerprint=str(getattr(r, "system_fingerprint", "") or ""),
                            prompt_tokens=pt, completion_tokens=ct, reasoning_tokens=rt, total_tokens=tt,
                            max_tokens_used=cur, truncated=(fin == "length"), raw=raw)
            attempts.append(dict(max_tokens=cur, attempt=attempt, finish_reason=fin, completion_tokens=ct,
                                 latency_ms=int((time.time() - t0) * 1000), provider=res.provider))
            res.attempts, res.n_attempts = attempts, len(attempts)
            if fin == "length":
                if cur < max_tokens_ceiling:
                    cur = min(cur * 2, max_tokens_ceiling)
                    break                       # escalate: same trial, bigger budget
                res.status, res.error_message = "truncation", f"finish_reason=length at max_tokens={cur}"
                return res
            choice = parse_choice(text)
            if choice is None:
                res.status, res.error_message = "parse_fail", f"no ROCK/PAPER/SCISSORS found (finish_reason={fin})"
                return res
            res.status, res.choice = "model", choice
            return res


def dumps_raw(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)
