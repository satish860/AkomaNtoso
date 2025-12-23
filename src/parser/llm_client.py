"""Claude API client configuration for Azure OpenAI."""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_client() -> Anthropic:
    """Get configured Anthropic client for Azure.

    Uses Azure OpenAI endpoint with Anthropic models.

    Environment variables:
        ANTHROPIC_ENDPOINT: Azure endpoint URL
        ANTHROPIC_API_KEY: Azure API key

    Returns:
        Configured Anthropic client
    """
    endpoint = os.getenv("ANTHROPIC_ENDPOINT")
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    if not endpoint:
        raise ValueError("ANTHROPIC_ENDPOINT environment variable not set")

    return Anthropic(
        base_url=endpoint,
        api_key=api_key,
    )


def get_model() -> str:
    """Get the deployment/model name to use.

    Returns:
        Deployment name from environment or default
    """
    return os.getenv("ANTHROPIC_DEPLOYMENT", "claude-sonnet-4-5")


def hello_world() -> str:
    """Test the API connection with a simple request.

    Returns:
        Response from Claude
    """
    client = get_client()
    model = get_model()

    response = client.messages.create(
        model=model,
        max_tokens=100,
        messages=[{"role": "user", "content": "Say hello in one sentence."}]
    )

    return response.content[0].text
