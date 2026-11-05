"""Run all 59 examples. Each calls a real model: paid requests."""
import importlib
import json
from pathlib import Path


def main():
    cases = json.loads(Path(__file__).with_name('manifest.json').read_text())
    for case in cases:
        print(f"== {case['experiment']:02} {case['name']}")
        result = importlib.import_module(case['module']).run()
        print(result)


if __name__ == '__main__':
    main()
