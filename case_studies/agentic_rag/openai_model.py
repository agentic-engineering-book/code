"""A real model for the Chapter 31 agent: an OpenAI model through the API.

It has the same generate(messages) interface as the stand-in, so the agent
loop and every control stay unchanged. Structured outputs make each reply
one JSON decision; the agent still validates it against the contract
(Chapter 2), because a schema constrains shape, not judgement. Requires the
openai package and OPENAI_API_KEY in the environment (never in the code).
"""
import json
import time

from case_studies.agentic_rag.prompts import system

MODEL = 'gpt-5.4-mini-2026-03-17'
TEXT = {'type': ['string', 'null']}
DECISION = {
    'type': 'object', 'additionalProperties': False,
    'required': ['action', 'query', 'doc_id', 'node', 'text', 'citations',
                 'reason'],
    'properties': {
        'action': {'type': 'string',
                   'enum': ['search', 'read', 'explore', 'answer',
                            'decline']},
        'query': TEXT, 'doc_id': TEXT, 'node': TEXT, 'text': TEXT,
        'reason': TEXT,
        'citations': {'type': ['array', 'null'],
                      'items': {'type': 'string'}}}}


REWRITE = """Rewrite the user's follow-up as one short, self-contained
question. Use the earlier conversation only to resolve references such as
"he", "it", "that chapter" or "the second one", replacing each with what it
refers to. Do not answer the question, do not add facts, and do not add the
book's title or words such as "in the book": every question is about the
book already, and extra words harm the search. If the follow-up already
stands on its own, return it exactly as written."""


def standalone_question(history, question, model=MODEL, client=None,
                        instructions=REWRITE):
    """A follow-up rewritten to stand alone, so that search and every check
    see the full question. history: [{'question': ..., 'answer': ...}]."""
    if not history:
        return question, None
    if client is None:
        from openai import OpenAI
        client = OpenAI()
    lines = [f'Q: {turn["question"]}\nA: {turn["answer"]}'
             for turn in history[-4:]]
    response = client.chat.completions.create(
        model=model, messages=[
            {'role': 'system', 'content': instructions},
            {'role': 'user', 'content': 'Earlier conversation:\n'
             + '\n\n'.join(lines) + f'\n\nFollow-up: {question}'}],
        response_format={'type': 'json_schema', 'json_schema': {
            'name': 'rewrite', 'strict': True, 'schema': {
                'type': 'object', 'additionalProperties': False,
                'required': ['question'],
                'properties': {'question': {'type': 'string'}}}}})
    rewritten = json.loads(response.choices[0].message.content)['question']
    usage = {'input_tokens': response.usage.prompt_tokens,
             'output_tokens': response.usage.completion_tokens}
    return rewritten.strip() or question, usage


class OpenAIRagModel:
    def __init__(self, model=MODEL, client=None, graph=False,
                 hybrid=False, system_prompt=None):
        if client is None:
            from openai import OpenAI
            client = OpenAI()
        self.client, self.model = client, model
        self.system = system_prompt or system(graph, hybrid)
        self.replies = []            # the model's own earlier turns
        self.calls = []              # tokens and latency per request

    def conversation(self, messages):
        """Book messages to chat turns: the question, then pairs of reply
        and observation (every decision acted on gets one)."""
        turns = [{'role': 'system', 'content': self.system},
                 {'role': 'user', 'content': messages[0]['content']}]
        observations = [m for m in messages[1:] if m['role'] == 'tool']
        for reply, observation in zip(self.replies, observations):
            content = observation['content']
            if not isinstance(content, str):
                content = json.dumps(content, ensure_ascii=False)
            turns.append({'role': 'assistant', 'content': reply})
            turns.append({'role': 'user', 'content':
                          f'{observation["name"]} result: {content[:4000]}'})
        return turns

    def generate(self, messages):
        start = time.perf_counter()
        response = self.client.chat.completions.create(
            model=self.model, messages=self.conversation(messages),
            response_format={'type': 'json_schema', 'json_schema': {
                'name': 'decision', 'strict': True, 'schema': DECISION}})
        self.calls.append({
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens,
            'seconds': round(time.perf_counter() - start, 3)})
        text = response.choices[0].message.content or ''
        self.replies.append(text)
        try:
            decision = json.loads(text)
        except json.JSONDecodeError:
            return {'action': None, 'raw': text}   # the contract rejects it
        return {k: v for k, v in decision.items() if v is not None}
