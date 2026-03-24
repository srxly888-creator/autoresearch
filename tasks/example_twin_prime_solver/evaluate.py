#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import math
import os
from pathlib import Path
import time
import traceback


ROOT = Path(__file__).resolve().parent
SOLVER_PATH = ROOT / "workspace" / "solver.py"
OUTPUT_JSON = Path(os.environ.get("AUTORESEARCH_OUTPUT_JSON", ROOT / "result.json"))

CORRECTNESS_LIMITS = [10, 100, 1_000, 10_000]
BENCHMARK_LIMIT = 150_000
BENCHMARK_REPEATS = 2


def load_solver():
    spec = importlib.util.spec_from_file_location("twin_prime_solver", SOLVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import solver from {SOLVER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "count_twin_primes"):
        raise AttributeError("solver.py must define count_twin_primes(limit)")
    return module


def reference_count_twin_primes(limit: int) -> int:
    if limit < 3:
        return 0
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for factor in range(2, math.isqrt(limit) + 1):
        if sieve[factor]:
            start = factor * factor
            count = ((limit - start) // factor) + 1
            sieve[start : limit + 1 : factor] = b"\x00" * count

    twin_count = 0
    previous_prime = None
    for candidate in range(2, limit + 1):
        if not sieve[candidate]:
            continue
        if previous_prime is not None and candidate - previous_prime == 2:
            twin_count += 1
        previous_prime = candidate
    return twin_count


def write_result(payload: dict[str, object]) -> None:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def fail(summary: str, *, status: str = "fail", score: float = 0.0, metrics: dict[str, object] | None = None) -> int:
    write_result(
        {
            "score": score,
            "status": status,
            "summary": summary,
            "metrics": metrics or {},
        }
    )
    return 1


def main() -> int:
    try:
        solver = load_solver()
        function = solver.count_twin_primes

        correctness_metrics: dict[str, int] = {}
        for limit in CORRECTNESS_LIMITS:
            expected = reference_count_twin_primes(limit)
            actual = function(limit)
            correctness_metrics[f"limit_{limit}"] = actual
            if actual != expected:
                return fail(
                    f"incorrect result for limit={limit}: expected {expected}, got {actual}",
                    metrics=correctness_metrics,
                )

        expected_benchmark = reference_count_twin_primes(BENCHMARK_LIMIT)
        timings = []
        for _ in range(BENCHMARK_REPEATS):
            start = time.perf_counter()
            actual = function(BENCHMARK_LIMIT)
            elapsed = time.perf_counter() - start
            if actual != expected_benchmark:
                return fail(
                    f"incorrect benchmark result for limit={BENCHMARK_LIMIT}: expected {expected_benchmark}, got {actual}",
                    metrics=correctness_metrics,
                )
            timings.append(elapsed)

        benchmark_runtime = min(timings)
        score = 1.0 / benchmark_runtime if benchmark_runtime > 0 else 0.0
        payload = {
            "score": score,
            "status": "pass",
            "summary": f"all tests passed; benchmark runtime {benchmark_runtime:.6f}s",
            "metrics": {
                **correctness_metrics,
                "benchmark_limit": BENCHMARK_LIMIT,
                "benchmark_runtime_seconds": benchmark_runtime,
                "benchmark_expected": expected_benchmark,
            },
        }
        write_result(payload)
        return 0
    except Exception:
        return fail(
            "evaluator crashed: " + traceback.format_exc().splitlines()[-1],
            status="crash",
        )


if __name__ == "__main__":
    raise SystemExit(main())
