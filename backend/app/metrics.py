"""Business metrics - what the app does, next to the instrumentator's generic HTTP metrics."""
from prometheus_client import Counter, Gauge

ITEMS_REPORTED = Counter(
    "foundit_items_reported_total",
    "Lost/found reports created",
    ["type"],
)
ITEMS_RESOLVED = Counter(
    "foundit_items_resolved_total",
    "Items marked as returned to their owner",
)
ITEMS_OPEN = Gauge(
    "foundit_items_open",
    "Items still open (OPEN or CLAIMED), refreshed after every change",
    ["type"],
)
