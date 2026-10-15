"""Chapter 31: the agentic RAG system as an AgentCore Runtime agent.

The agent loop, the tools and every control are the first-principles code,
unchanged. AgentCore adds what production needs around it: an isolated,
serverless session per request, identity, logs and traces. The model is
Amazon Nova Lite through Bedrock (see bedrock_model.py).

Invoked with {"prompt": "<question>"}; returns the outcome, trace and usage.
"""
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from case_studies.agentic_rag.agent import run
from case_studies.agentic_rag.bedrock_model import MODEL_ID, BedrockModel

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload):
    model = BedrockModel()          # a fresh conversation per question
    outcome = run(payload['prompt'], model)
    return {'status': outcome['status'], 'answer': outcome.get('answer'),
            'reason': outcome.get('reason'),
            'citations': outcome.get('citations', []),
            'trace': [list(map(str, step)) for step in outcome['trace']],
            'cost_units': outcome['budget'].cost_used,
            'model': MODEL_ID, 'usage': model.usage}


if __name__ == '__main__':
    app.run()
