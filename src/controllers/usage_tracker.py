class UsageTracker:
    def __init__(self):
        self._usage: dict[str, float] = {}

    def add_usage(self, run_id: str, amount: float) -> None:
        if run_id in self._usage:
            self._usage[run_id] += amount
        else:
            self._usage[run_id] = amount

    def get_total_usage(self, run_id: str) -> float | None:
        return self._usage.get(run_id)
