# autoresearch

This fork keeps the original GPU training workflow in `program-train.md`, but the default mode is now a generic automatic research / problem-solving loop.

## Setup

To set up a new run, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar25`). The branch `autoresearch/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current master.
3. **Read the active task definition**:
   - `README.md` — repository context.
   - `problem.md` — the current task, constraints, and success criteria.
   - `task.json` — mutable paths, evaluation command, score direction, timeout, artifact location.
   - `run_task.py` — the generic evaluation harness.
4. **Read the task-specific files**:
   - Files listed in `mutable_paths` are the only files you may edit by default.
   - Read the evaluator entrypoint from `task.json` so you understand how scoring works.
5. **Confirm the baseline**: Run `python3 run_task.py --description baseline` before making changes.
6. **Confirm and go**: Once the baseline works, begin the experiment loop.

## Experimentation

Each experiment follows a generic cycle:

1. Propose one concrete hypothesis.
2. Modify only the files listed in `mutable_paths`, unless the human explicitly broadens scope.
3. Commit the change.
4. Run `python3 run_task.py --description "<short hypothesis>"`.
5. Read the printed summary and the logs under `artifacts/.../runs/<run_id>/`.
6. If the task score improved in the configured direction, keep the commit.
7. If it regressed or failed, revert to the previous good commit.
8. Record lessons learned in an untracked note under the artifact directory if helpful.

The task may be about code generation, bug fixing, benchmark optimization, search strategy design, or any other problem that has:

- a clear success metric
- a reproducible evaluator
- a small, explicit mutable surface area

## Rules

**What you CAN do:**
- Edit the files listed in `mutable_paths`.
- Read any read-only task context needed to understand the benchmark.
- Use the evaluator output, logs, and git history to steer the next hypothesis.

**What you CANNOT do by default:**
- Edit the evaluator or `run_task.py`.
- Add dependencies.
- Change the scoring contract in `task.json`.

If the human explicitly asks to expand the search space, you may revise those constraints together.

## Output format

`python3 run_task.py` prints a summary like this:

```
---
task:             example_twin_prime_solver
run_id:           20260325-120000-abc123
score:            0.812345
score_direction:  maximize
status:           pass
duration_seconds: 1.231
best_score_before:0.790000
comparison:       improved
summary:          all tests passed; benchmark runtime 1.231s
artifact_dir:     artifacts/example_twin_prime_solver/runs/20260325-120000-abc123
```

The evaluator must write a JSON result payload to the path given in `AUTORESEARCH_OUTPUT_JSON`. The minimum payload is:

```json
{
  "score": 0.812345,
  "status": "pass",
  "summary": "all tests passed; benchmark runtime 1.231s"
}
```

## Logging

`run_task.py` automatically appends a row to `artifacts/<task>/results.tsv` with:

```
run_id	branch	commit	score	status	duration_seconds	description	summary
```

The artifact directory also stores:

- `stdout.log`
- `stderr.log`
- `result.json`
- `metadata.json`

## The experiment loop

LOOP FOREVER:

1. Inspect the current branch and best known score.
2. Read `problem.md` again before large directional changes.
3. Make one focused change.
4. Commit.
5. Run the evaluator.
6. Keep or discard based on the configured score direction.
7. Repeat until the human stops you.

Use `program-train.md` when the active task is the original single-GPU `train.py` optimization workflow instead of a generic benchmark-driven task.
