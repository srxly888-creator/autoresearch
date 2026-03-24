# Active Problem

The default task in this fork is a small, fully local benchmark that demonstrates the generic autoresearch loop.

## Goal

Improve the implementation of `count_twin_primes(limit)` in `tasks/example_twin_prime_solver/workspace/solver.py`.

The function must return the exact number of twin-prime pairs `(p, p + 2)` such that both primes are less than or equal to `limit`.

## Success Metric

- Primary metric: maximize `score`
- Current scorer: `score = 1.0 / benchmark_runtime_seconds`
- Correctness is a hard gate. Wrong answers get a failing status and a non-improving score.

The benchmark is intentionally simple:

1. The evaluator runs correctness checks on several limits.
2. If correctness passes, it times the solver on a larger fixed input.
3. Faster correct code gets a better score.

## Mutable Surface Area

You may edit only:

- `tasks/example_twin_prime_solver/workspace/solver.py`

Treat these as read-only:

- `task.json`
- `run_task.py`
- `tasks/example_twin_prime_solver/evaluate.py`
- `problem.md`

## Constraints

- Keep the public function signature: `count_twin_primes(limit: int) -> int`
- Use only the Python standard library
- Do not special-case known benchmark answers
- Prefer simple, readable improvements over clever but fragile tricks

## Why This Task Exists

This task is only a working example of the generic architecture. To retarget the repo at a real project:

1. Rewrite `problem.md`
2. Update `task.json`
3. Point `mutable_paths` at the files the agent may edit
4. Replace the evaluator command with your own reproducible benchmark
