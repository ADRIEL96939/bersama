"""
Optional language-model client.

Thin wrapper around the Anthropic Messages API. It is only used when
LLM_ENABLED is true. If the SDK is not installed or no key is set, calling
complete() raises a clear error, and the rest of the system falls back to its
offline behavior instead.
"""

from . import config


def is_available() -> bool:
    """True only if the LLM is switched on AND we have what we need to call it."""
    if not config.LLM_ENABLED:
        return False
    if not config.ANTHROPIC_API_KEY:
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def complete(system: str, user: str, max_tokens: int = 700) -> str:
    """Send one prompt to the model and return the text of the reply.

    Raises RuntimeError with a readable message if the LLM is not usable, so
    callers can catch it and fall back cleanly.
    """
    if not config.LLM_ENABLED:
        raise RuntimeError("LLM is disabled. Set BERSAMA_LLM=1 to enable it.")
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError(
            "The 'anthropic' package is not installed. Run: pip install anthropic"
        ) from e

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=config.MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    parts = [block.text for block in message.content if getattr(block, "type", None) == "text"]
    return "\n".join(parts).strip()
