"""Record a run of the deployed AgentCore agent on the Chapter 31 questions.

Invokes the agent runtime once per question (a new session each time),
scores the outcomes with the same evaluation as the other two versions, and
saves everything with the date, model, region and SDK version to
case_studies/agentic_rag/results/agentcore_run.json, which the book prints.

Usage (from the repository root, with AWS credentials configured):
  python -m case_studies.agentic_rag.agentcore.record --arn <runtime ARN>
"""
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
import argparse
import json
import uuid

import boto3

from case_studies.agentic_rag.bedrock_model import MODEL_ID, REGION
from case_studies.agentic_rag.evaluate import score
from case_studies.agentic_rag.questions import QUESTIONS

RESULTS = Path(__file__).resolve().parents[1] / 'results'


def invoke(client, arn, question):
    response = client.invoke_agent_runtime(
        agentRuntimeArn=arn, runtimeSessionId=str(uuid.uuid4()),
        payload=json.dumps({'prompt': question}).encode(),
        qualifier='DEFAULT')
    body = response['response']
    body = body.read() if hasattr(body, 'read') else b''.join(body)
    return json.loads(body.decode('utf-8'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arn', required=True)
    arn = parser.parse_args().arn
    client = boto3.client('bedrock-agentcore', region_name=REGION)
    rows = []
    for case in QUESTIONS:
        outcome = invoke(client, arn, case['question'])
        correct, unsafe, cited = score(case, outcome)
        rows.append({'id': case['id'], 'type': case['type'],
                     'question': case['question'], 'correct': correct,
                     'unsafe': unsafe, 'outcome': outcome})
        mark = 'UNSAFE' if unsafe else ('ok' if correct else 'wrong')
        print(f'{case["id"]} {case["type"]:12s} {mark:6s} '
              f'{outcome["status"]}')
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    record = {'recorded_at': now, 'model': MODEL_ID, 'region': REGION,
              'bedrock_agentcore_sdk': version('bedrock-agentcore'),
              'boto3': version('boto3'),
              'correct': sum(r['correct'] for r in rows),
              'unsafe': sum(r['unsafe'] for r in rows), 'questions': rows}
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / 'agentcore_run.json'
    text = json.dumps(record, indent=1, ensure_ascii=False)
    path.write_text(text + '\n', encoding='utf-8')
    print(f'correct {record["correct"]}/{len(rows)}, '
          f'unsafe {record["unsafe"]}; saved {path.name}')


if __name__ == '__main__':
    main()
