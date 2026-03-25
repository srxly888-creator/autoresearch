from __future__ import annotations


def build_chat_request(model: str, messages: list[dict], temperature: float = 0.7, max_tokens: int = 512) -> dict:
    """Build request payload for OpenAI-compatible chat completions APIs."""
    return {
        "model": model,
        "messages": messages,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "stream": False,
    }


def extract_text_from_response(response_json: dict) -> str:
    """
    Extract assistant text from OpenAI-compatible response payload.
    """
    if "output_text" in response_json:
        return str(response_json["output_text"])

    choices = response_json.get("choices", [])
    if not choices:
        return ""

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(str(part.get("text", "")))
        return "\n".join(part for part in text_parts if part)
    return str(content)


def should_retry(status_code: int, error_code: str | None, attempt: int, max_attempts: int = 3) -> bool:
    """
    Return True when the request should be retried.
    """
    if attempt >= max_attempts:
        return False
    if error_code == "context_length_exceeded":
        return False
    if status_code in {429, 500, 502, 503, 504}:
        return True
    return False
