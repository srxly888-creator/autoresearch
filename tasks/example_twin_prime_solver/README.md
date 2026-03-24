# Example Task: Twin Prime Solver

This task is the default local benchmark for the generic autoresearch flow.

## Files

- `workspace/solver.py` is the only mutable file.
- `evaluate.py` is the fixed evaluator.
- `../../problem.md` explains the goal in repo-level terms.
- `../../task.json` points the generic harness at this task.

## Run The Baseline

```bash
python3 run_task.py --description baseline
```

The harness writes logs and result metadata under:

```bash
artifacts/example_twin_prime_solver/
```
