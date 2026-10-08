"""Experiment 44 (Chapter 24): idempotency.
Run directly; deterministic by design so the mechanism is inspectable.
"""
seen=set()
def send(key):
 if key in seen:return 'duplicate suppressed'
 seen.add(key); return 'sent'
print(send('abc'),send('abc'))
