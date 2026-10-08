"""Experiment 45 (Chapter 24): checkpoint resume.
Run directly; deterministic by design so the mechanism is inspectable.
"""
import json,tempfile,os
p=tempfile.mktemp(); json.dump({'step':2},open(p,'w')); print(json.load(open(p))); os.remove(p)
