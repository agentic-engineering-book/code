# Framework companions

Each of the 59 primitive experiments has a separate runnable framework version.
LangChain core supplies model, prompt, tool, retrieval, runnable, and callback
interfaces. LangGraph supplies graphs, routing, reducers, checkpointing, stores,
and human approval. These examples call real framework APIs while using
deterministic model and environment fixtures. No API key, network model request,
LangSmith account, or paid service is needed to run them.

## Install and run

Use Python 3.12 or newer for the pinned framework environment (the primitive
examples still support Python 3.10):

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-frameworks.txt
python -m framework_examples.02_llm_to_agent
python -m framework_examples.46_human_approval
python -m framework_examples.run_all
python -m pytest -q
```

Run modules from the repository root. The book prints their code and links each
example to its source. `manifest.json` maps experiment numbers, primitive files,
framework files, behavioral contracts, and limitations. `support.py` contains
the short shared StateGraph builders; read it alongside graph examples.
The `.py` files are the source of truth: the book prints each file and the
output captured by running it, and `tests/test_framework_examples.py` checks each
result against `manifest.json`.

## Scope and limits

### Optional real model calls

Experiments 2 and 22 also accept `--live`. Install `requirements-frameworks-live.txt`,
set `OPENAI_API_KEY` privately in your environment, and set `BOOK_MODEL` to an
available tool-capable model in your provider account. Then run:

```bash
python -m framework_examples.02_llm_to_agent --live
python -m framework_examples.22_react --live
```

The live path uses `ChatOpenAI.bind_tools` and the same LangGraph execution loop.
It makes real paid provider requests; outputs and tool choices may vary. Live
provider calls are not part of the offline test suite. A recursion ceiling and
request timeout bound execution, but are not a monetary budget. See the
[official integration guide](https://docs.langchain.com/oss/python/integrations/chat/openai).

Each example states its boundary in the book and in `manifest.json`. In short:
the MCP example (21) simulates protocol message shapes in process and does not
use the MCP SDK or a transport; the A2A example (37) models the task lifecycle
without an A2A endpoint; the code-execution examples (50, 53) use a child
process with a timeout and an empty environment, which is NOT a sandbox;
computer use (55) uses screen fixtures; multimodal input (56) represents
message blocks without fetching images; and policy selection (57-59) does not
train weights. The framework manages interfaces and orchestration; provider
behavior, security, protocol transport, real environment control, and
validated learning require additional systems.

Working memory and stores use in-memory implementations. They demonstrate APIs,
not restart-safe storage. Fixtures make comparisons reproducible, but are not
empirical measurements of real LLM performance.

## Official references

- [LangChain core](https://reference.langchain.com/python/langchain_core/)
- [LangChain tools](https://docs.langchain.com/oss/python/langchain/tools)
- [LangGraph graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)

Dependency versions are pinned in `requirements-frameworks.txt`; the environment
used for validation is captured in `requirements-frameworks-lock.txt`.
