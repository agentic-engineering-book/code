"""Experiment 4: Reject an invalid decision. See framework_examples/README."""
from typing import Literal

from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from framework_examples.support import chat

SYSTEM = ('Reply only with JSON: {{"action": "<action name>", '
          '"arguments": {{...}}}}. Choose the action that carries out the '
          'request. You have a calculator: {{"action": "calculator", '
          '"arguments": {{"expression": "<arithmetic expression>"}}}}')


class Arguments(BaseModel):
    expression: str


class CalculatorDecision(BaseModel):
    action: Literal["calculator"]
    arguments: Arguments


def run():
    prompt = ChatPromptTemplate.from_messages(
        [("system", SYSTEM), ("human", "{request}")])
    propose = prompt | chat()
    parser = PydanticOutputParser(pydantic_object=CalculatorDecision)
    lines = []
    for request in ["Work out 27611 times 2033.",
                    "Delete the old customer records."]:
        raw = propose.invoke({"request": request}).content
        lines += [f"REQUEST: {request}",
                  "PROPOSED: " + " ".join(raw.split())[:66]]
        try:
            decision = parser.invoke(raw)
            lines.append(f"ACCEPTED: {decision.arguments.expression}")
        except OutputParserException:
            lines.append("BLOCKED: the proposal does not match the schema")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
