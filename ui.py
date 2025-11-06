from __future__ import annotations
from typing import Any
from main import run

def _prompt_int(prompt: str, default: int) -> int:
    """Prompt the user for an int with a default."""
    try:
        return int(input(f"{prompt} [{default}]: ") or default)
    except ValueError:
        return default

def interactive() -> None:
    """Run generation and present an interactive quiz to the user."""
    try:
        path = input("File path (enter for input.txt): ").strip() or "input.txt"
        keywords = _prompt_int("Number of keywords", 8)
        questions = _prompt_int("Number of MCQs", 5)
        out = input("Output JSON file [outputs.json]: ").strip() or "outputs.json"

        res = run(path, keywords=keywords, questions=questions, out_path=out)
    except KeyboardInterrupt:
        print("\nCancelled.")
        return
    except Exception as exc:
        print("Error running generation:", exc)
        return

    mcqs = res.get("mcqs") or []
    if not mcqs:
        print("\nNo MCQs generated.")
        return

    print("\nStarting quiz. Answer each question by typing A, B, C or D.\n")
    score = 0
    total = len(mcqs)

    for i, q in enumerate(mcqs, start=1):
        # Validate MCQ shape before use
        question = q.get("question") or "(no question text)"
        options = q.get("options") or {}
        if not isinstance(options, dict) or not options:
            print(f"{i}. {question}\n   (invalid options; skipped)\n")
            continue

        # Normalize option keys and sort A-D
        available_keys = [k.upper() for k in options.keys()]
        keys_ordered = [k for k in ("A", "B", "C", "D") if k in available_keys]
        if not keys_ordered:
            print(f"{i}. {question}\n   (no valid options; skipped)\n")
            continue

        answer_key = (q.get("answer") or "").upper() if q.get("answer") else None

        print(f"{i}. {question}")
        for opt in keys_ordered:
            print(f"   {opt}. {options.get(opt) or options.get(opt.lower()) or ''}")

        # Prompt user for valid option
        user_ans = ""
        while True:
            user_ans = input("Your answer (A-D): ").strip().upper()
            if user_ans in keys_ordered:
                break
            print("Please enter one of the option letters shown (A, B, C, D).")

        if answer_key:
            if user_ans == answer_key:
                print("Correct.\n")
                score += 1
            else:
                print(f"Incorrect. Correct answer: {answer_key}\n")
        else:
            print("No reference answer available for this question.\n")

    print(f"Quiz finished. Score: {score}/{total}")

if __name__ == "__main__":
    interactive()