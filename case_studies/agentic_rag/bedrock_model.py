"""A real model for the Chapter 31 agent: Amazon Nova Lite through Bedrock.

It has the same generate(messages) interface as the book's stand-in models,
so the agent loop and every control stay unchanged. The model answers each
turn with one JSON decision; the agent validates it against the contract
(Chapter 2) and rejects anything else. Requires boto3 and AWS credentials
with Bedrock access; nothing here stores or prints credentials.
"""
import json
import re

from case_studies.agentic_rag.prompts import SYSTEM

MODEL_ID = 'us.amazon.nova-lite-v1:0'
REGION = 'us-east-1'


class BedrockModel:
    def __init__(self, model_id=MODEL_ID, region=REGION, client=None,
                 max_tokens=400):
        if client is None:
            import boto3
            client = boto3.client('bedrock-runtime', region_name=region)
        self.client, self.model_id = client, model_id
        self.max_tokens = max_tokens
        self.replies = []            # the model's own earlier turns
        self.usage = {'inputTokens': 0, 'outputTokens': 0, 'calls': 0}

    def conversation(self, messages):
        """Book messages to Converse turns: the question, then pairs of
        reply and observation (every decision acted on gets one)."""
        question = messages[0]['content']
        turns = [{'role': 'user', 'content': [{'text': question}]}]
        observations = [m for m in messages[1:] if m['role'] == 'tool']
        for reply, observation in zip(self.replies, observations):
            content = observation['content']
            if not isinstance(content, str):
                content = json.dumps(content, ensure_ascii=False)
            text = f'{observation["name"]} result: {content[:3000]}'
            turns.append({'role': 'assistant', 'content': [{'text': reply}]})
            turns.append({'role': 'user', 'content': [{'text': text}]})
        return turns

    def generate(self, messages):
        response = self.client.converse(
            modelId=self.model_id, system=[{'text': SYSTEM}],
            messages=self.conversation(messages),
            inferenceConfig={'maxTokens': self.max_tokens,
                             'temperature': 0})
        for key in ('inputTokens', 'outputTokens'):
            self.usage[key] += response['usage'][key]
        self.usage['calls'] += 1
        text = response['output']['message']['content'][0]['text']
        self.replies.append(text)
        found = re.search(r'\{.*\}', text, re.S)
        try:
            return json.loads(found.group(0))
        except (AttributeError, json.JSONDecodeError):
            # Not a decision: the contract will reject it (Chapter 2).
            return {'action': None, 'raw': text}
