"""Experiment 50: LangChain capability-limited tool registry. See framework_examples/README.md."""
from langchain_core.tools import tool


def run():
    @tool
    def read_fixture(name: str) -> str:
        """Read a named in-memory fixture; no filesystem or shell access."""
        return {'example': 'safe fixture'}[name]
    registry = {read_fixture.name: read_fixture}
    return {'shell_available': 'shell' in registry,
            'fixture': registry['read_fixture'].invoke({'name': 'example'})}


if __name__ == "__main__":
    print(run())
