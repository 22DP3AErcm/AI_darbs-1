from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

from ai_services import get_summary, get_keywords, get_mcqs

def run(file: str, keywords: int = 8, questions: int = 5, out_path: str | None = None) -> Dict[str, Any]:
    p = Path(file)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {file}")
    text = p.read_text(encoding="utf-8")
    warnings: list[str] = []

    try:
        summary = get_summary(text)
    except Exception as exc:
        summary = ""
        warnings.append(str(exc))

    try:
        kw = get_keywords(text, count=keywords)
    except Exception as exc:
        kw = []
        warnings.append(str(exc))

    try:
        mcqs = get_mcqs(text, count=questions)
    except Exception as exc:
        mcqs = []
        warnings.append(str(exc))

    result: Dict[str, Any] = {
        "summary": summary,
        "keywords": kw,
        "mcqs": mcqs,
        "warnings": warnings,
    }
    if out_path:
        Path(out_path).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result

def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize, extract keywords and generate MCQs from a text file.")
    parser.add_argument("--file", default="input.txt", help="Path to input text file")
    parser.add_argument("--keywords", type=int, default=8, help="Number of keywords to extract")
    parser.add_argument("--questions", type=int, default=5, help="Number of MCQs to generate")
    parser.add_argument("--out", default="outputs.json", help="JSON output file path")
    args = parser.parse_args()

    res = run(args.file, keywords=args.keywords, questions=args.questions, out_path=args.out)

    print("\n=== SUMMARY ===\n")
    print(res["summary"])
    print("\n=== KEYWORDS ===\n")
    print(", ".join(res["keywords"]))
    print("\n=== MCQS ===\n")
    for i, q in enumerate(res["mcqs"], start=1):
        print(f"{i}. {q.get('question')}")
        for opt_key in sorted(q.get("options", {}).keys()):
            print(f"   {opt_key}. {q['options'][opt_key]}")
        if q.get("answer"):
            print(f"   Answer: {q.get('answer')}")
        print()
    if res["warnings"]:
        print("\nWarnings:")
        for w in res["warnings"]:
            print(" -", w)

if __name__ == "__main__":
    main()