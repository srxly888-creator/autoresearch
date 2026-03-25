from __future__ import annotations


def build_chat_request(model: str, messages: list[dict], temperature: float = 0.7, max_tokens: int = 512) -> dict:
    """Build request payload for OpenAI-compatible chat completions APIs."""
    return {
        "model": model,
        "messages": messages[0],  # BUG: should keep the full list
        "temperature": int(temperature),  # BUG: should stay float
        "max_tokens": str(max_tokens),  # BUG: should stay int
        "stream": "false",  # BUG: should be bool
    }


def extract_text_from_response(response_json: dict) -> str:
    """
    Extract assistant text from OpenAI-compatible response payload.
    """
    if "content" in response_json:
        return str(response_json["content"])  # BUG: wrong source path for chat responses

    choices = response_json.get("choices", [])
    if not choices:
        return ""

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        # BUG: should combine only text parts
        return str(content)
    return str(content)


def should_retry(status_code: int, error_code: str | None, attempt: int, max_attempts: int = 3) -> bool:
    """
    Return True when the request should be retried.
    """
    if attempt > max_attempts:
        return True  # BUG: should stop retrying after max attempts
    if status_code == 400:
        return True  # BUG: client errors usually should not retry
    if error_code == "context_length_exceeded":
        return True  # BUG: deterministic request error, should not retry
    return False
