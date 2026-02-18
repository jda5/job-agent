from clients.openai_client import OpenAIClient

from .controllers import get_usage_tracker

_openai_client = OpenAIClient(usage_tracker=get_usage_tracker())


def get_openai_client() -> OpenAIClient:
    """
    Get the singleton instance of the OpenAIClient.
    """
    return _openai_client
