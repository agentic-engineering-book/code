"""Every first-principles experiment runs and exits cleanly.

Experiments with stand-in models must also be deterministic. Experiments that
call a real model (they import agentic.live) make paid requests and vary
between runs, so they run only when BOOK_LIVE_TESTS=1, and each must have a
recorded run in its chapter's output folder for the book to print.
"""
from pathlib import Path
import os
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = sorted(ROOT.glob('chapters/*/*.py'))


def is_live(script):
    return 'agentic.live' in script.read_text(encoding='utf-8')


def run(script):
    env = {**os.environ, 'PYTHONPATH': str(ROOT), 'PYTHONIOENCODING': 'utf-8'}
    return subprocess.run([sys.executable, str(script)], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=120)


def test_all_59_experiments_present():
    assert len(SCRIPTS) == 59


@pytest.mark.parametrize('script', SCRIPTS, ids=lambda p: p.stem)
def test_experiment_runs(script):
    if is_live(script):
        assert (script.parent / 'output' / f'{script.stem}.txt').exists(), \
            'record a run with tools/record_output.py'
        if os.environ.get('BOOK_LIVE_TESTS') != '1':
            pytest.skip('calls a real model; set BOOK_LIVE_TESTS=1')
        result = run(script)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip(), 'experiment should print its result'
        return
    first, second = run(script), run(script)
    assert first.returncode == 0, first.stderr
    assert first.stdout.strip(), 'experiment should print its result'
    assert first.stdout == second.stdout
