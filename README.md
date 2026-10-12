# Agentic Engineering from First Principles - Companion Code

59 executable experiments across 30 chapters, built on a tiny provider-neutral
educational kernel (`agentic/`). Every experiment file is printed in full in its
chapter, together with its real output.

## Run

```bash
python -m pip install -e .          # the agentic kernel (Python 3.10+)
python -m pip install -r requirements.txt
python chapters/01/01_llm_call.py
python chapters/03/05_agent_loop.py
python -m pytest
```

The experiments are deterministic. `ScriptedModel` replays fixed responses and
`PolicyModel` decides from the messages it receives; both stand in for a real
model so the mechanism, not model variance, is what you observe. They do not
measure any real model. To use one, give the loop an object with the same
`generate(messages)` method.

## Framework implementations

All 59 experiments also have runnable LangChain core / LangGraph companions.
See [the framework guide](framework_examples/README.md) for installation,
pinned versions, and the boundaries of the local fixtures.

```bash
python -m pip install -r requirements-frameworks.txt   # Python 3.12+
python -m framework_examples.02_llm_to_agent
python -m framework_examples.run_all
```

## Notebooks

`notebooks/` contains both sets of experiments as notebooks. They are generated
from the source files with `python tools/build_notebooks.py`; edit the `.py`
files, then rebuild the notebooks.
