from __future__ import annotations
from typing import List, Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_ROUTER_MODEL = os.getenv("HF_ROUTER_MODEL", "Qwen/Qwen2.5-72B-Instruct")

try:
    import openai
except Exception:
    openai = None


def _call_hf_router(prompt: str, max_tokens: int = 300, model: Optional[str] = None) -> str:
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN not set in environment")
    if openai is None:
        raise RuntimeError("openai package not installed; install openai to call HF Router")
    m = model or HF_ROUTER_MODEL
    try:
        client = openai.OpenAI(base_url="https://router.huggingface.co/v1", api_key=HF_TOKEN)
        resp = client.chat.completions.create(
            model=m,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return getattr(resp.choices[0].message, "content", "") .strip()
    except Exception as exc:
        raise RuntimeError(f"HF Router API call failed: {exc}")


def _call_openai(prompt: str, max_tokens: int = 300, model: str = "gpt-3.5-turbo") -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    if openai is None:
        raise RuntimeError("openai package not installed; run: pip install openai")
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return getattr(resp.choices[0].message, "content", "") .strip()
    except Exception as exc:
        raise RuntimeError(f"OpenAI API call failed: {exc}")


def get_summary(text: str, provider: str = "hf") -> str:
    if not text or not text.strip():
        return ""
    prompt = f"Summarize the following text in 2-3 concise sentences:\n\n{text}"
    if provider == "openai":
        logger.info("Generating summary via OpenAI")
        return _call_openai(prompt, max_tokens=300, model="gpt-3.5-turbo")
    logger.info("Generating summary via HF Router: %s", HF_ROUTER_MODEL)
    return _call_hf_router(prompt, max_tokens=300)


def get_keywords(text: str, count: int = 8, provider: str = "openai") -> List[str]:
    if not text or not text.strip():
        return []
    prompt = (
        f"Extract exactly {count} important keywords from the following text. "
        "Return only the keywords separated by commas, nothing else:\n\n" + text
    )
    if provider == "hf":
        logger.info("Generating keywords via HF Router: %s", HF_ROUTER_MODEL)
        out = _call_hf_router(prompt, max_tokens=200)
    else:
        logger.info("Generating keywords via OpenAI")
        out = _call_openai(prompt, max_tokens=200, model="gpt-3.5-turbo")
    items = [k.strip() for k in out.split(",") if k.strip()]
    items = [k.lstrip("0123456789. -•").strip() for k in items]
    return items[:count]


def get_mcqs(text: str, count: int = 5, provider: str = "openai") -> List[Dict[str, Any]]:
    if not text or not text.strip():
        return []
    prompt = (
        f"Create {count} multiple-choice questions based on the following text. "
        "Provide exactly 4 options (A, B, C, D) and an ANSWER line with the correct letter. "
        "Format each question like:\nQ: <question>\nA: <opt A>\nB: <opt B>\nC: <opt C>\nD: <opt D>\nANSWER: <letter>\n\n"
        f"Text:\n{text}"
    )
    if provider == "hf":
        logger.info("Generating MCQs via HF Router: %s", HF_ROUTER_MODEL)
        out = _call_hf_router(prompt, max_tokens=1500)
    else:
        logger.info("Generating MCQs via OpenAI")
        out = _call_openai(prompt, max_tokens=1500, model="gpt-3.5-turbo")
    return _parse_mcq_text(out, count)


def _parse_mcq_text(raw: str, count: int) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    parts = [p.strip() for p in raw.split("\nQ:") if p.strip()]
    for p in parts:
        if p.startswith("Q:"):
            p = p[2:].strip()
        lines = [ln.strip() for ln in p.splitlines() if ln.strip()]
        if not lines:
            continue
        question = lines[0]
        options: Dict[str, str] = {}
        answer_key: Optional[str] = None
        for ln in lines[1:]:
            if len(ln) >= 3 and ln[1] == ":" and ln[0].upper() in "ABCD":
                key = ln[0].upper()
                val = ln[2:].strip()
                options[key] = val
            elif ln.upper().startswith("ANSWER:"):
                ans = ln.split(":", 1)[1].strip().upper()
                if ans and ans[0] in "ABCD":
                    answer_key = ans[0]
        if question and len(options) >= 2:
            items.append({"question": question, "options": options, "answer": answer_key})
        if len(items) >= count:
            break
    return items[:count]
