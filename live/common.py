"""Shared helpers for the live-model experiments.

Every experiment runs repeated trials against a pinned model snapshot and
saves a results file with the model, date, settings, token use, and a 95%
Wilson interval for each rate. Live results vary between runs and models;
the files record one run, not a general property of the model.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from math import sqrt
from pathlib import Path
import argparse
import json
import re

MODEL = "gpt-5.4-mini-2026-03-17"
SMALL_MODEL = "gpt-5.4-nano-2026-03-17"
RESULTS = Path(__file__).with_name("results")


def wilson(successes, n, z=1.96):
    """95% Wilson score interval for a proportion."""
    if n == 0:
        return [0.0, 0.0]
    p = successes / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0.0, centre - half), 3), round(min(1.0, centre + half), 3)]


def rate(name, outcomes):
    """Summarise a list of booleans as count, rate and interval."""
    k, n = sum(bool(o) for o in outcomes), len(outcomes)
    return {"metric": name, "successes": k, "n": n,
            "rate": round(k / n, 3) if n else 0.0, "ci95": wilson(k, n)}


def parallel(function, items, workers=8):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(function, items))


def numbers_in(text):
    """Integers and decimals in a model answer, ignoring thousands commas."""
    cleaned = re.sub(r"(?<=\d),(?=\d{3})", "", text or "")
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", cleaned)]


def contains_number(text, expected, tolerance=1e-6):
    return any(abs(x - expected) <= tolerance for x in numbers_in(text))


def usage(models):
    calls = [call for model in models for call in model.calls]
    return {"requests": len(calls),
            "input_tokens": sum(c["input_tokens"] for c in calls),
            "output_tokens": sum(c["output_tokens"] for c in calls),
            "mean_seconds": round(sum(c["seconds"] for c in calls)
                                  / max(1, len(calls)), 2)}


def save(name, chapter, question, models, metrics, trials, usage_summary,
         notes=""):
    import openai
    RESULTS.mkdir(exist_ok=True)
    record = {"experiment": name, "chapter": chapter, "question": question,
              "models": models,
              "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
              "openai_sdk": openai.__version__,
              "settings": "provider defaults (no temperature or seed set)",
              "metrics": metrics, "usage": usage_summary, "notes": notes,
              "trials": trials}
    path = RESULTS / f"{name}.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    for metric in metrics:
        low, high = metric["ci95"]
        print(f"{metric['metric']:<44} {metric['successes']:>3}/"
              f"{metric['n']:<3} {metric['rate']:.2f}  [{low:.2f}, {high:.2f}]")
    print("saved", path)
    return record


def arguments(default_model=MODEL):
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=default_model)
    return parser.parse_args()
