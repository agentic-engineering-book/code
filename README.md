# Agentic Engineering from First Principles - Companion Code

59 executable experiments across 30 chapters, built on a tiny provider-neutral
educational kernel (`agentic/`). Every experiment file is printed in full in its
chapter, together with its real output.

## Run

```bash
python -m pip install -e .          # the agentic kernel (Python 3.10+)
python -m pip install -r requirements.txt
# set OPENAI_API_KEY in your environment (never commit it)
python chapters/01/01_llm_call.py
python chapters/03/05_agent_loop.py
python -m pytest
```

Every experiment calls a real model through `agentic.live`. Each makes paid
requests of a fraction of a cent, and its output changes from
run to run, so the book prints one recorded run, kept in the chapter's
`output/` folder. `python tools/record_output.py chapters/01/01_llm_call.py`
records a new one. Set `BOOK_MODEL` to use another model; the tests run these
experiments only when `BOOK_LIVE_TESTS=1`.

`agentic/model.py` keeps two deterministic stand-ins, `ScriptedModel` and
`PolicyModel`, for the offline tests. They do not measure any real model.

## Live-model experiments

`agentic/live.py` connects the same `Agent` loop to a real model through any
OpenAI-compatible Chat Completions endpoint (OpenAI, or a local server such as
Ollama). `live/` repeats six of the book's questions against pinned model
snapshots and records each run in `live/results/` (model, date, token use, and
95% Wilson intervals). These runs make more paid requests and are optional.

```bash
# set OPENAI_API_KEY in your environment (never commit it)
python -m live.ch01_tool_vs_no_tool
```

A recorded run is evidence about one model on one day, not a general property
of the model. Rerunning will give somewhat different numbers.

## Framework implementations

All 59 experiments also have runnable LangChain core / LangGraph companions.
Like the experiments, they call a real model (`OPENAI_API_KEY`, paid
requests). See [the framework guide](framework_examples/README.md) for
installation, pinned versions, and the boundaries of each example.

```bash
python -m pip install -r requirements-frameworks.txt   # Python 3.12+
python -m framework_examples.02_llm_to_agent
python -m framework_examples.run_all             # all 59: many paid requests
```

## Notebooks

`notebooks/` contains both sets of experiments as notebooks. They are generated
from the source files with `python tools/build_notebooks.py`; edit the `.py`
files, then rebuild the notebooks.
