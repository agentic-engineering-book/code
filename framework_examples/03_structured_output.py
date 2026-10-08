"""Experiment 3: LangChain structured-output parsing. See framework_examples/README.md."""
from pydantic import BaseModel
from langchain_core.output_parsers import PydanticOutputParser


def run():
    class Action(BaseModel):
        tool: str
        arguments: dict
    parser = PydanticOutputParser(pydantic_object=Action)
    return parser.invoke('{"tool":"calculator","arguments":{"expression":"6*7"}}').model_dump()


if __name__ == "__main__":
    print(run())
