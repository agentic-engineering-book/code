"""Experiment 36 (Chapter 20): Blackboard."""
import threading

AUTHORITY = {"catalog_v4": 3, "catalog_v3": 2, "carrier_api": 2,
             "calculator": 2, "cached_page": 1}
REQUIRED = ["unit_price", "quantity", "shipping"]


class Blackboard:
    """Shared task state: claims with provenance, a version, and a lock."""

    def __init__(self):
        self.claims = {}
        self.version = 0
        self.tasks = {"calculate_total": "open"}
        self._lock = threading.Lock()

    def publish(self, key, value, source, expected_version=None):
        """Compare-and-swap: the version check and the write are atomic."""
        with self._lock:
            if expected_version not in (None, self.version):
                return f"rejected: stale (read v{expected_version}, " \
                       f"board is v{self.version})"
            claim = {"value": value, "source": source}
            self.claims.setdefault(key, []).append(claim)
            self.version += 1
            return f"ok (v{self.version})"

    def current(self, key):
        """Resolve conflicting claims by source authority, not by timing."""
        claims = self.claims.get(key)
        if not claims:
            return None
        return max(claims, key=lambda c: AUTHORITY[c["source"]])["value"]

    def claim_task(self, task, agent):
        with self._lock:
            if self.tasks[task] != "open":
                return False
            self.tasks[task] = f"claimed by {agent}"
            return True


def calculate_total(board):
    """Return (version read, total), or None while inputs are missing."""
    facts = {key: board.current(key) for key in REQUIRED}
    if None in facts.values():
        return None
    total = facts["unit_price"] * facts["quantity"] + facts["shipping"]
    return board.version, total


board = Blackboard()
board.publish("unit_price", 80, "catalog_v3")
board.publish("quantity", 3, "catalog_v3")
print(f"ready after pricing: {calculate_total(board) is not None}")
board.publish("shipping", 15, "carrier_api")
print(f"ready after shipping: {calculate_total(board)}")

last_write_wins = {"unit_price": 80}
last_write_wins["unit_price"] = 90  # a cached page overwrites the catalog
board.publish("unit_price", 90, "cached_page")
print(f"last write wins: unit_price={last_write_wins['unit_price']}")
for claim in board.claims["unit_price"]:
    print(f"  claim kept: {claim}")
print(f"resolved by authority: unit_price={board.current('unit_price')}")

print(f"A claims calculate_total: {board.claim_task('calculate_total', 'A')}")
print(f"B claims calculate_total: {board.claim_task('calculate_total', 'B')}")

snapshot, total = calculate_total(board)
board.publish("unit_price", 90, "catalog_v4")  # correction lands mid-task
print(f"commit total={total}: "
      f"{board.publish('total', total, 'calculator', snapshot)}")
snapshot, total = calculate_total(board)
print(f"recompute total={total}: "
      f"{board.publish('total', total, 'calculator', snapshot)}")
