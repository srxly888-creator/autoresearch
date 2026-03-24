#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid


RESULTS_HEADER = [
    "run_id",
    "branch",
    "commit",
    "score",
    "status",
    "duration_seconds",
    "description",
    "summary",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a generic autoresearch task evaluator")
    parser.add_argument("--config", default="task.json", help="Path to the task config JSON")
    parser.add_argument("--description", default="manual run", help="Short description for the run log")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sanitize_field(value: object) -> str:
    return str(value).replace("\t", " ").replace("\n", " ").strip()


def git_value(repo_root: Path, args: list[str], default: str) -> str:
    try:
        output = subprocess.check_output(
            ["git", *args],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return default
    return output or default


def resolve_command(command: list[str]) -> list[str]:
    resolved = []
    for token in command:
        if token == "__PYTHON__":
            resolved.append(sys.executable)
        else:
            resolved.append(token)
    return resolved


def append_results(results_path: Path, row: dict[str, object]) -> None:
    results_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not results_path.exists()
    with results_path.open("a", encoding="utf-8") as handle:
        if write_header:
            handle.write("\t".join(RESULTS_HEADER) + "\n")
        handle.write(
            "\t".join(sanitize_field(row.get(column, "")) for column in RESULTS_HEADER) + "\n"
        )


def load_previous_scores(results_path: Path) -> list[float]:
    if not results_path.exists():
        return []
    scores: list[float] = []
    with results_path.open("r", encoding="utf-8") as handle:
        next(handle, None)
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5:
                continue
            status = parts[4]
            if status != "pass":
                continue
            try:
                scores.append(float(parts[3]))
            except ValueError:
                continue
    return scores


def compare_score(previous_scores: list[float], score: float, direction: str, status: str) -> tuple[str, str]:
    if status != "pass":
        return "n/a", "not comparable"
    if not previous_scores:
        return "n/a", "first run"

    best_before = max(previous_scores) if direction == "maximize" else min(previous_scores)
    if direction == "maximize":
        if score > best_before:
            return f"{best_before:.6f}", "improved"
        if score == best_before:
            return f"{best_before:.6f}", "tied best"
        return f"{best_before:.6f}", "regressed"

    if score < best_before:
        return f"{best_before:.6f}", "improved"
    if score == best_before:
        return f"{best_before:.6f}", "tied best"
    return f"{best_before:.6f}", "regressed"


def normalize_result(raw: dict[str, object], returncode: int) -> dict[str, object]:
    status = str(raw.get("status", "pass" if returncode == 0 else "crash"))
    summary = str(raw.get("summary", ""))

    try:
        score = float(raw.get("score", 0.0))
    except (TypeError, ValueError):
        score = 0.0

    metrics = raw.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}

    return {
        "score": score,
        "status": status,
        "summary": summary,
        "metrics": metrics,
    }


def print_summary(task_name: str, run_id: str, score: float, direction: str, status: str, duration: float,
                  best_before: str, comparison: str, summary: str, artifact_dir: Path) -> None:
    print("---")
    print(f"task:             {task_name}")
    print(f"run_id:           {run_id}")
    print(f"score:            {score:.6f}")
    print(f"score_direction:  {direction}")
    print(f"status:           {status}")
    print(f"duration_seconds: {duration:.3f}")
    print(f"best_score_before:{best_before}")
    print(f"comparison:       {comparison}")
    print(f"summary:          {summary}")
    print(f"artifact_dir:     {artifact_dir}")


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    repo_root = config_path.parent
    config = load_json(config_path)

    task_name = str(config["name"])
    direction = str(config["evaluate"].get("score_direction", "maximize"))
    command = resolve_command(list(config["evaluate"]["command"]))
    timeout_seconds = int(config["evaluate"].get("timeout_seconds", 30))
    artifacts_dir = (repo_root / config["artifacts_dir"]).resolve()
    results_path = artifacts_dir / "results.tsv"
    previous_scores = load_previous_scores(results_path)

    run_stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{run_stamp}-{uuid.uuid4().hex[:6]}"
    run_dir = artifacts_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    output_json = run_dir / "result.json"
    stdout_log = run_dir / "stdout.log"
    stderr_log = run_dir / "stderr.log"
    metadata_json = run_dir / "metadata.json"

    env = os.environ.copy()
    env["AUTORESEARCH_OUTPUT_JSON"] = str(output_json)
    env["AUTORESEARCH_ARTIFACT_DIR"] = str(run_dir)
    env["AUTORESEARCH_TASK_NAME"] = task_name

    started = time.perf_counter()
    returncode = 1
    stdout_text = ""
    stderr_text = ""
    raw_result: dict[str, object] | None = None

    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        returncode = completed.returncode
        stdout_text = completed.stdout
        stderr_text = completed.stderr
    except subprocess.TimeoutExpired as exc:
        stdout_text = exc.stdout or ""
        stderr_text = (exc.stderr or "") + f"\nTimed out after {timeout_seconds}s."
        raw_result = {
            "score": 0.0,
            "status": "crash",
            "summary": f"evaluation timed out after {timeout_seconds}s",
        }
    except FileNotFoundError as exc:
        stderr_text = str(exc)
        raw_result = {
            "score": 0.0,
            "status": "crash",
            "summary": f"failed to launch evaluator: {exc}",
        }

    duration_seconds = time.perf_counter() - started
    stdout_log.write_text(stdout_text, encoding="utf-8")
    stderr_log.write_text(stderr_text, encoding="utf-8")

    if raw_result is None:
        if output_json.exists():
            try:
                raw_result = load_json(output_json)
            except json.JSONDecodeError as exc:
                raw_result = {
                    "score": 0.0,
                    "status": "crash",
                    "summary": f"invalid result JSON: {exc}",
                }
        else:
            raw_result = {
                "score": 0.0,
                "status": "crash",
                "summary": "evaluator did not write AUTORESEARCH_OUTPUT_JSON",
            }

    result = normalize_result(raw_result, returncode)
    best_before, comparison = compare_score(previous_scores, float(result["score"]), direction, str(result["status"]))

    branch = git_value(repo_root, ["branch", "--show-current"], "detached")
    commit = git_value(repo_root, ["rev-parse", "--short", "HEAD"], "nogit")

    metadata = {
        "task_name": task_name,
        "config_path": str(config_path),
        "command": command,
        "timeout_seconds": timeout_seconds,
        "run_id": run_id,
        "branch": branch,
        "commit": commit,
        "returncode": returncode,
        "duration_seconds": duration_seconds,
        "description": args.description,
        "result": result,
    }
    metadata_json.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    output_json.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    append_results(
        results_path,
        {
            "run_id": run_id,
            "branch": branch,
            "commit": commit,
            "score": f"{float(result['score']):.6f}",
            "status": result["status"],
            "duration_seconds": f"{duration_seconds:.3f}",
            "description": args.description,
            "summary": result["summary"],
        },
    )

    print_summary(
        task_name=task_name,
        run_id=run_id,
        score=float(result["score"]),
        direction=direction,
        status=str(result["status"]),
        duration=duration_seconds,
        best_before=best_before,
        comparison=comparison,
        summary=str(result["summary"]),
        artifact_dir=run_dir,
    )

    return 0 if str(result["status"]) == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
