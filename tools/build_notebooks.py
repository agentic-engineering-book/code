"""Rebuild both notebooks from the experiment files so they cannot drift.

Run from the repository root: python tools/build_notebooks.py
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SETUP = '''from pathlib import Path
import sys

# Start Jupyter in the repository root or in notebooks/.
repo = Path.cwd()
if not (repo / "agentic").exists():
    repo = repo.parent
assert (repo / "agentic").exists(), "Start Jupyter in the code repository"
sys.path.insert(0, str(repo))'''


def cell(kind, text):
    data = {'cell_type': kind, 'metadata': {}, 'source': text.splitlines(keepends=True)}
    if kind == 'code':
        data.update(execution_count=None, outputs=[])
    return data


def notebook(cells):
    return {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python',
            'name': 'python3'}, 'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 5}


def main():
    manifest = json.loads((ROOT / 'framework_examples/manifest.json').read_text(encoding='utf-8'))
    primitive = [cell('markdown', '# Agentic Engineering from First Principles: 59 experiments\n\n'
                      'Each code cell is the exact content of one file in `chapters/`. The experiments are '
                      'deterministic and use only the standard library and the `agentic` kernel.'),
                 cell('code', SETUP)]
    framework = [cell('markdown', '# Framework companions: all 59 experiments\n\n'
                      'Install `requirements-frameworks.txt` first (Python 3.12+). No API key is needed. '
                      'Read each boundary before interpreting a result.'),
                 cell('code', SETUP)]
    for case in manifest:
        n, title = case['experiment'], case['title']
        source = (ROOT / case['file']).read_text(encoding='utf-8')
        source = re.sub(r'^"""(?:.|\n)*?"""\n', '', source, count=1).strip('\n')
        primitive.append(cell('markdown', f'## Experiment {n} (Chapter {case["chapter"]}): {title}\n\n'
                              f'Source: `{case["file"]}`'))
        if '__file__' in source:
            # Notebooks have no __file__; point it at the experiment file.
            source = f'__file__ = str(repo / "{case["file"]}")\n\n' + source
        primitive.append(cell('code', source))
        framework.append(cell('markdown', f'## Experiment {n}: {title}\n\n{case["concept"]}.\n\n'
                              f'Source: `{case["framework_file"]}`. Boundary: {case["limitation"]}'))
        framework.append(cell('code', f'import importlib\n'
                              f'importlib.import_module("{case["module"]}").run()'))
    for name, cells in [('Agentic_Engineering_59_Experiments.ipynb', primitive),
                        ('Agentic_Engineering_Framework_Examples.ipynb', framework)]:
        path = ROOT / 'notebooks' / name
        path.write_text(json.dumps(notebook(cells), indent=1, ensure_ascii=False) + '\n',
                        encoding='utf-8', newline='\n')
        print('wrote', path.relative_to(ROOT))


if __name__ == '__main__':
    main()
