"""Experiment 3: LangChain structured-output parsing."""
from typing import Literal

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel


class Arguments(BaseModel):
    expression: str


class CalculatorDecision(BaseModel):
    action: Literal["calculator"]
    arguments: Arguments


def run():
    parser = PydanticOutputParser(pydantic_object=CalculatorDecision)
    good = parser.invoke(
        '{"action": "calculator", "arguments": {"expression": "37*42"}}')
    try:
        parser.invoke('{"action": "delete_database", "arguments": {}}')
        rejected = False
    except OutputParserException:
        rejected = True
    return {"parsed": good.model_dump(),
            "delete_database_rejected": rejected}


if __name__ == "__main__":
    print(run())
