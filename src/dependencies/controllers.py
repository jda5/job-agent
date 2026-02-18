from controllers.usage_tracker import UsageTracker

_usage_tracker = UsageTracker()


def get_usage_tracker() -> UsageTracker:
    """
    Get the singleton instance of the UsageTracker.
    """
    return _usage_tracker
