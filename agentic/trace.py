"""Minimal deterministic tracing used in Chapter 23.

Spans carry a trace ID, a span ID, a parent ID, start and end times, a
status, and attributes. IDs are sequential and the clock is injectable, so
every run prints the same trace.
"""
from contextlib import contextmanager


class ManualClock:
    """A clock in milliseconds that moves only when told to."""

    def __init__(self):
        self.now_ms = 0

    def __call__(self):
        return self.now_ms

    def advance(self, ms):
        self.now_ms += ms


class Tracer:
    def __init__(self, trace_id="T-1", clock=None):
        self.trace_id = trace_id
        self.clock = clock or ManualClock()
        self.spans = []
        self._open = []

    @contextmanager
    def span(self, name, **attributes):
        parent = self._open[-1]["span_id"] if self._open else None
        span = {
            "trace_id": self.trace_id,
            "span_id": f"S{len(self.spans) + 1}",
            "parent_id": parent,
            "name": name,
            "start": self.clock(),
            "end": None,
            "status": "ok",
            "attributes": dict(attributes),
        }
        self.spans.append(span)
        self._open.append(span)
        try:
            yield span
        except Exception as error:
            span["status"] = "error"
            span["attributes"]["error"] = type(error).__name__
            raise
        finally:
            span["end"] = self.clock()
            self._open.pop()

    def children(self, span_id):
        return [s for s in self.spans if s["parent_id"] == span_id]
