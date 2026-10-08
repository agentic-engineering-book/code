"""Run all 59 local examples; no provider credentials are required."""
import importlib
import json
from pathlib import Path


def main():
    cases = json.loads(Path(__file__).with_name('manifest.json').read_text())
    for case in cases:
        result = importlib.import_module(case['module']).run()
        print(f"{case['experiment']:02} {case['name']}: {result}")


if __name__ == '__main__':
    main()
