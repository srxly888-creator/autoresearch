#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import time
import traceback


ROOT = Path(__file__).resolve().parent
WORKSPACE_PATH = ROOT / "workspace" / "api_client.py"
OUTPUT_JSON = Path(os.environ.get("AUTORESEARCH_OUTPUT_JSON", ROOT / "result.json"))
BENCHMARK_REPEATS = 10000


def load_module():
    spec = importlib.util.spec_from_file_location("api_bugfix_client", WORKSPACE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load workspace module from {WORKSPACE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_result(payload: dict[str, object]) -> None:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run_case(name: str, fn):
    try:
        fn()
        return True, f"{name}: pass"
    except AssertionError as exc:
        return False, f"{name}: fail ({exc})"
    except Exception as exc:
        return False, f"{name}: crash ({exc})"


def main() -> int:
    try:
        module = load_module()
        cases = []

        def case_build_payload_messages():
            payload = module.build_chat_request(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": "hello"}],
                temperature=0.25,
                max_tokens=128,
            )
            assert isinstance(payload.get("messages"), list), "messages should be a list"

        cases.append(("build_payload_messages", case_build_payload_messages))

        def case_build_payload_types():
            payload = module.build_chat_request(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": "hello"}],
                temperature=0.25,
                max_tokens=128,
            )
            assert isinstance(payload.get("temperature"), float), "temperature should be float"
            assert isinstance(payload.get("max_tokens"), int), "max_tokens should be int"
            assert isinstance(payload.get("stream"), bool), "stream should be bool"

        cases.append(("build_payload_types", case_build_payload_types))

        def case_extract_string_content():
            response = {
                "choices": [
                    {
                        "message": {
                            "content": "ok"
                        }
                    }
                ]
            }
            assert module.extract_text_from_response(response) == "ok", "should extract content string"

        cases.append(("extract_string_content", case_extract_string_content))

        def case_extract_array_content():
            response = {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": "hello"},
                                {"type": "image_url", "image_url": {"url": "https://example.com/x.png"}},
                                {"type": "text", "text": "world"},
                            ]
                        }
                    }
                ]
            }
            assert module.extract_text_from_response(response) == "hello\nworld", "should merge text blocks only"

        cases.append(("extract_array_content", case_extract_array_content))

        def case_extract_output_text_fallback():
            response = {"output_text": "fallback text"}
            assert module.extract_text_from_response(response) == "fallback text", "should support output_text"

        cases.append(("extract_output_text_fallback", case_extract_output_text_fallback))

        def case_retry_429():
            assert module.should_retry(429, None, attempt=1, max_attempts=3) is True, "429 should retry"

        cases.append(("retry_429", case_retry_429))

        def case_retry_500():
            assert module.should_retry(500, None, attempt=1, max_attempts=3) is True, "5xx should retry"

        cases.append(("retry_500", case_retry_500))

        def case_no_retry_400():
            assert module.should_retry(400, None, attempt=1, max_attempts=3) is False, "400 should not retry"

        cases.append(("no_retry_400", case_no_retry_400))

        def case_no_retry_context_len():
            assert (
                module.should_retry(400, "context_length_exceeded", attempt=1, max_attempts=3) is False
            ), "context length should not retry"

        cases.append(("no_retry_context_len", case_no_retry_context_len))

        def case_no_retry_after_max():
            assert module.should_retry(429, None, attempt=3, max_attempts=3) is False, "attempt=max should stop"

        cases.append(("no_retry_after_max", case_no_retry_after_max))

        details = []
        passed = 0
        for name, fn in cases:
            ok, msg = run_case(name, fn)
            details.append(msg)
            if ok:
                passed += 1

        total = len(cases)
        pass_ratio = passed / total if total else 0.0

        benchmark_input = {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"type": "text", "text": "a"},
                            {"type": "text", "text": "b"},
                            {"type": "text", "text": "c"},
                        ]
                    }
                }
            ]
        }
        t0 = time.perf_counter()
        for _ in range(BENCHMARK_REPEATS):
            module.extract_text_from_response(benchmark_input)
        elapsed = time.perf_counter() - t0

        # Correctness dominates. Speed only matters after correctness reaches 100%.
        if pass_ratio < 1.0:
            score = pass_ratio * 100.0
            status = "fail"
            summary = f"{passed}/{total} tests passed; fix correctness first"
        else:
            speed_bonus = 1.0 / max(elapsed, 1e-9)
            score = 100.0 + speed_bonus
            status = "pass"
            summary = f"all tests passed; extraction benchmark {elapsed:.6f}s for {BENCHMARK_REPEATS} runs"

        write_result(
            {
                "score": score,
                "status": status,
                "summary": summary,
                "metrics": {
                    "tests_passed": passed,
                    "tests_total": total,
                    "pass_ratio": pass_ratio,
                    "benchmark_seconds": elapsed,
                    "benchmark_repeats": BENCHMARK_REPEATS,
                    "details": details,
                },
            }
        )
        return 0 if status == "pass" else 1
    except Exception:
        write_result(
            {
                "score": 0.0,
                "status": "crash",
                "summary": "evaluator crashed: " + traceback.format_exc().splitlines()[-1],
                "metrics": {},
            }
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
