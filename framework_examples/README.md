# Framework companions

Each of the 59 experiments in Chapters 1 to 30 has a separate runnable
framework version. LangChain core supplies model, prompt, tool, retrieval,
runnable, and callback interfaces; `langchain-openai` supplies the real chat
model. LangGraph supplies graphs, routing, reducers, checkpointing, stores,
and human approval. Like the primitive experiments, every example calls a
real model, so it needs `OPENAI_API_KEY` and makes a few paid requests.
Outputs vary between runs; the book prints one recorded run of each.

## Install and run

Use Python 3.12 or newer for the pinned framework environment:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-frameworks.txt
python -m pip install -e .
# set OPENAI_API_KEY in your environment (never commit it)
python -m framework_examples.22_react
python -m framework_examples.run_all        # all 59: many paid requests
python -m pytest -q                         # graph tests only
BOOK_LIVE_TESTS=1 python -m pytest -q       # also runs every example
```

Run modules from the repository root. `framework_examples/support.py` provides
`chat()`, a `ChatOpenAI` with a timeout and retries, and the short shared
StateGraph builders; read it alongside the graph examples. Set `BOOK_MODEL` to
use another model. `manifest.json` maps experiment numbers, primitive files,
framework files, concepts, and limitations. The `.py` files are the source of
truth: the book prints each file and the output captured by running it.

## Scope and limits

Each example states its boundary in the book and in `manifest.json`. In short:
the MCP example (21) simulates protocol message shapes in process and does not
use the MCP SDK or a transport; the A2A example (37) models the task lifecycle
in process without an A2A endpoint; the code-execution examples (50, 53) use a
child process with a timeout and an empty environment, which is NOT a sandbox;
computer use (55) grounds actions on a toy screen, not a real display; and
policy selection (57-59) does not train weights. The framework manages
interfaces and orchestration; provider behavior, security, protocol transport,
real environment control, and validated learning require additional systems.

Working memory and stores use in-memory implementations. They demonstrate
APIs, not restart-safe storage. One recorded run of a model is evidence about
that model on that day, not a general measurement.

## Official references

- [LangChain core](https://reference.langchain.com/python/langchain_core/)
- [LangChain tools](https://docs.langchain.com/oss/python/langchain/tools)
- [LangGraph graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)

Dependency versions are pinned in `requirements-frameworks.txt`; the environment
used for validation is captured in `requirements-frameworks-lock.txt`.
