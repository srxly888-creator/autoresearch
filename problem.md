# Active Problem

The default task is now API-focused and designed for users who build products on top of hosted LLM APIs.

## Goal

Fix and harden an OpenAI-compatible API helper in:

- `tasks/api_bugfix_assistant/workspace/api_client.py`

The helper should:

1. Build correct chat request payloads.
2. Extract assistant text robustly from common response shapes.
3. Retry only retryable failures.

## Success Metric

- Primary metric: maximize `score`
- Correctness gate: all evaluator tests must pass to reach `status=pass`.
- Speed bonus: after correctness is 100%, faster text extraction gets a higher score.

The evaluator runs deterministic local checks and does not make network calls.

## Mutable Surface Area

You may edit only:

- `tasks/api_bugfix_assistant/workspace/api_client.py`

Treat these as read-only:

- `task.json`
- `run_task.py`
- `tasks/api_bugfix_assistant/evaluate.py`
- `problem.md`

## Constraints

- Keep the existing function names:
  - `build_chat_request(...)`
  - `extract_text_from_response(...)`
  - `should_retry(...)`
- Use only Python standard library.
- Keep behavior predictable and easy to understand.
- Do not hardcode evaluator answers.

## Why This Task Exists

This default task models a common real scenario:

- API-only teams need reliable request/response handling.
- Bugs are usually in payload format, parser edge cases, and retry policy.
- Those bugs are perfect for autonomous fix loops with local, deterministic tests.

To retarget for your project:

1. Rewrite `problem.md`
2. Update `task.json`
3. Point `mutable_paths` to your editable files
4. Replace evaluator command with your own test/benchmark harness
