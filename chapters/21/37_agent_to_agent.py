"""Experiment 37 (Chapter 21): Agent-to-agent communication."""
import json

from agentic.live import OpenAIModel

FACTS = ("Facts: company A's product costs 80 US dollars; company B's costs "
         "95 US dollars.")
V1 = ("You are a research agent. " + FACTS + ' Reply with JSON only: '
      '{"price": <the lower price as an integer>, "currency": "USD"}.')
V2 = ("You are a research agent. " + FACTS +  # the schema line was dropped
      " Reply with your comparison as JSON only.")
AGENT_CARD = {
    "name": "researcher",
    "version": "1.0.0",
    "capabilities": {"streaming": False, "pushNotifications": False},
    "skills": [{"id": "company-research", "name": "Company research",
                "description": "Compare two companies on price.",
                "tags": ["research"]}],
}


class RemoteAgent:
    """An in-process A2A-style server (no network, no real auth) whose
    work is done by a real model."""

    def __init__(self, card, allowed_callers, instructions):
        self.card = card
        self.allowed_callers = allowed_callers
        self.instructions = instructions
        self.tasks = {}
        self.task_for_message = {}

    def send_message(self, caller, message):
        known = self.task_for_message.get(message["messageId"])
        if known:  # a retry of a message already received
            return self.tasks[known]
        task_id = f"task-{len(self.tasks) + 1}"  # the server assigns IDs
        task = {"id": task_id, "states": ["submitted"], "artifacts": []}
        self.tasks[task_id] = task
        self.task_for_message[message["messageId"]] = task_id
        if caller not in self.allowed_callers:
            task["states"].append("rejected")
            return task
        task["states"].append("working")
        model = OpenAIModel(system=self.instructions,
                            response_format={"type": "json_object"})
        text = message["parts"][0]["text"]
        reply = model.generate([{"role": "user", "content": text}])
        part = {"kind": "data", "data": json.loads(reply["answer"])}
        task["artifacts"].append(
            {"artifactId": "art-1", "name": "comparison", "parts": [part]})
        task["states"].append("completed")
        return task


def valid_comparison(artifact):
    data = artifact["parts"][0]["data"]
    has_price = isinstance(data.get("price"), int)
    return has_price and data.get("currency") == "USD"


remote = RemoteAgent(AGENT_CARD, {"coordinator"}, V1)
skills = [skill["id"] for skill in remote.card["skills"]]
print("skills discovered:", skills)

message = {"messageId": "msg-1", "role": "user",
           "parts": [{"kind": "text", "text": "Compare A and B on price"}]}
task = remote.send_message("coordinator", message)
print(task["id"], "states:", " -> ".join(task["states"]))

retry = remote.send_message("coordinator", message)
print("retry of msg-1 ->", retry["id"], "| tasks stored:", len(remote.tasks))

other = {**message, "messageId": "msg-2"}
denied = remote.send_message("intruder", other)
print("intruder ->", denied["id"], denied["states"][-1])

print("valid artifact:", valid_comparison(task["artifacts"][0]))

drifted = RemoteAgent(AGENT_CARD, {"coordinator"}, V2)
task = drifted.send_message("coordinator", message)
print("drifted agent:", task["states"][-1], "| valid artifact:",
      valid_comparison(task["artifacts"][0]))
print("  drifted keys:", list(task["artifacts"][0]["parts"][0]["data"]))
