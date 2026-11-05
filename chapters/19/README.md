# Chapter 19: Debate and voting

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model (about thirty-five requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `34_voting.py` - Experiment 34: Voting. Real model voters answer from the source each reads; independent versus correlated sources, nine voters, and a tie. `python chapters/19/34_voting.py`
- `35_debate_judge.py` - Experiment 35: Judge and debate. A real model judge versus a calculator-grounded judge on bare claims, one-sided worked answers and two-sided worked answers, in both orders. `python chapters/19/35_debate_judge.py`

Kernel modules used: `agentic/tools.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [34: LangGraph parallel voters with an explicit vote policy](../../framework_examples/34_voting.py) - `python -m framework_examples.34_voting`
- [35: LangGraph debaters and a tool-grounded judge](../../framework_examples/35_debate_judge.py) - `python -m framework_examples.35_debate_judge`
