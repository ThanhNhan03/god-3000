import os
import re
from typing import Optional
from openai import AsyncOpenAI

# ─── API Keys ────────────────────────────────────────────────────────────────
# ShopAIKey proxy (OpenAI-compatible)
SHOPAI_KEY_1 = ""
SHOPAI_KEY_2 = ""
SHOPAI_BASE_URL = "https://api.shopaikey.com/v1"
SHOPAI_MODEL = "gpt-4o"

# Build list of clients
def _make_client(api_key: str) -> AsyncOpenAI:
    return AsyncOpenAI(api_key=api_key, base_url=SHOPAI_BASE_URL)

CLIENTS = []
if SHOPAI_KEY_1: CLIENTS.append(_make_client(SHOPAI_KEY_1))
if SHOPAI_KEY_2: CLIENTS.append(_make_client(SHOPAI_KEY_2))

def set_api_key(key: str):
    global CLIENTS
    if key:
        CLIENTS = [_make_client(key)]

async def test_api_key(key: str) -> bool:
    try:
        client = _make_client(key)
        await client.chat.completions.create(
            model=SHOPAI_MODEL,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
        )
        return True
    except Exception:
        return False

# ─── Fake Anthropic-style response wrapper ────────────────────────────────────
class _Content:
    def __init__(self, text: str):
        self.text = text

class _Response:
    def __init__(self, text: str):
        self.content = [_Content(text)]

# ─── Non-streaming generate ───────────────────────────────────────────────────
async def generate_response(prompt: str, system_prompt: str = "") -> _Response:
    """Call the LLM and return a response. Falls back through all clients."""
    errors = []
    for client in CLIENTS:
        try:
            resp = await client.chat.completions.create(
                model=SHOPAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=4096,
            )
            return _Response(resp.choices[0].message.content or "")
        except Exception as e:
            errors.append(str(e))
            continue

    error_msg = "; ".join(errors)
    return _Response(
        f"**Fallback Plan generated (LLM Error):** {error_msg}\n\n- Migrate all identified modules sequentially."
    )

# ─── Streaming generate ───────────────────────────────────────────────────────
async def stream_response(prompt: str, system_prompt: str = ""):
    """
    Async-generator that streams text chunks from the LLM.
    Falls back through all configured clients.
    Yields error message if every client fails.
    """
    errors = []
    for client in CLIENTS:
        try:
            stream = await client.chat.completions.create(
                model=SHOPAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=4096,
                stream=True,
            )
            # Must use `async for` because the streaming response is an async iterator
            async for chunk in stream:
                # Guard: final [DONE] chunk often has choices=[] — skip it
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
            return  # success – stop trying other clients
        except Exception as e:
            errors.append(str(e))
            continue

    # All clients failed – yield a structured error so caller can detect it
    error_msg = "; ".join(errors)
    yield f"[STREAM_ERROR]: {error_msg}"

# ─── Helper: robust JSON extractor ───────────────────────────────────────────
def extract_json_from_text(text: str) -> Optional[dict]:
    """
    Try to extract a JSON object from a mixed text/code response.

    Priority:
      1. ```json … ``` fenced block
      2. First outermost { … } braces (last resort)

    Returns parsed dict or None on failure.
    """
    # 1. Fenced code block
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        try:
            return _try_parse(m.group(1))
        except Exception:
            pass

    # 2. Raw braces fallback
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return _try_parse(text[start:end + 1])
        except Exception:
            pass

    return None

def _try_parse(s: str) -> dict:
    """Strip BOM / leading whitespace then parse."""
    s = s.strip().lstrip("\ufeff")
    return __import__("json").loads(s)
