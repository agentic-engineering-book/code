"""Experiment 56 (Chapter 29): multimodal.
Run directly; deterministic by design so the mechanism is inspectable.
"""
inputs={'text':'red light','image_label':'stop sign'}; print('decision: stop' if 'stop' in inputs['image_label'] else 'go')
