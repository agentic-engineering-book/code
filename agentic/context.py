def select_context(items, budget=3): return list(items)[:budget]
def compress(text, max_chars=160): return text if len(text)<=max_chars else text[:max_chars-3]+'...'
