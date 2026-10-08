# Agentic Engineering from First Principles - Companion Code

59 executable experiments across 30 chapters, built on a tiny provider-neutral educational kernel.

## Run
```bash
python chapters/01/01_llm_call.py
python chapters/01/02_llm_to_agent.py
pytest -q
```

The deterministic examples isolate mechanisms from model variance. Replace `ScriptedModel` with a provider adapter for live-model experiments.
