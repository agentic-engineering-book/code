"""Every first-principles experiment runs, exits cleanly, and is deterministic."""
from pathlib import Path
import os
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = sorted(ROOT.glob('chapters/*/*.py'))


def run(script):
    env = {**os.environ, 'PYTHONPATH': str(ROOT), 'PYTHONIOENCODING': 'utf-8'}
    return subprocess.run([sys.executable, str(script)], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=60)


def test_all_59_experiments_present():
    assert len(SCRIPTS) == 59


@pytest.mark.parametrize('script', SCRIPTS, ids=lambda p: p.stem)
def test_experiment_runs_deterministically(script):
    first, second = run(script), run(script)
    assert first.returncode == 0, first.stderr
    assert first.stdout.strip(), 'experiment should print its result'
    assert first.stdout == second.stdout
