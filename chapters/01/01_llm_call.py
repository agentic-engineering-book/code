"""Experiment 1 (Chapter 1): llm call.
Run directly; deterministic by design so the mechanism is inspectable.
"""
def model_generate(prompt): return "37 x 42 is approximately 1,500."
if __name__=='__main__': print(model_generate('37 x 42?'))
