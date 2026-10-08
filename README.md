# Agentic Engineering from First Principles - Companion Code

59 executable experiments across 30 chapters, built on a tiny provider-neutral educational kernel.

## Run
```bash
python chapters/01/01_llm_call.py
python chapters/01/02_llm_to_agent.py
pytest -q
```

The deterministic examples isolate mechanisms from model variance. Replace `ScriptedModel` with a provider adapter for live-model experiments.

## Framework implementations

All 59 experiments also have runnable LangChain core / LangGraph companions.
See [the framework guide](framework_examples/README.md) for installation,
examples, exact dependency versions, and the boundaries of the local fixtures.
The original first-principles implementations remain unchanged.

```bash
python -m pip install -r requirements-frameworks.txt
python -m framework_examples.02_llm_to_agent
python -m framework_examples.run_all
python -m pytest -q
```

[Open the framework notebook](notebooks/Agentic_Engineering_Framework_Examples.ipynb).
