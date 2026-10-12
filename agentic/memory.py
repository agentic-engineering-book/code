"""A typed memory store with provenance (Chapter 8)."""


class Memory:
    """Records are dicts: {"type", "text", "source"}.

    The store keeps whatever it is given; deciding what deserves to be
    written is the caller's write policy.
    """

    def __init__(self):
        self.records = []

    def write(self, text, kind, source="user"):
        record = {"type": kind, "text": text, "source": source}
        self.records.append(record)
        return record

    def retrieve(self, kind=None, query=None, limit=3):
        """Records of the given type whose text contains the query."""
        matches = [
            record for record in self.records
            if (kind is None or record["type"] == kind)
            and (query is None or query.lower() in record["text"].lower())
        ]
        return matches[:limit]
