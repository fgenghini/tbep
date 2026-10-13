# Agent Development Workflow

These instructions apply to every new task in this repository.

## Worktrees and pull requests

1. Fetch the latest `origin/main` and create a dedicated Git worktree from it
   before changing any files. Each task must have its own worktree so multiple
   agents can work on the repository concurrently. Use the platform's managed
   worktree tools when available; reuse a worktree already isolated for the
   current task. Do not develop in the shared `main` checkout.
2. Give the worktree a descriptive branch with the `codex/` prefix, such as
   `codex/add-user-settings` or `codex/fix-webhook-timeout`. Worktrees still need
   branches for pushing changes and opening pull requests; a branch alone is
   not sufficient isolation.
3. Keep all task changes in that worktree. Do not modify another agent's
   worktree, branch, or uncommitted changes.
4. Run the relevant checks before handing the work off. For this project, the
   standard checks are:

   ```sh
   uv run --locked ruff check .
   uv run --locked ruff format --check .
   uv run --locked mypy src
   uv run --locked pytest
   uv run --locked python scripts/smoke_commands.py
   uv run --locked python scripts/smoke_worker.py
   ```

   Install dependencies with `uv sync --locked` and `npm ci` first. CI also
   scans for secrets and audits both Python and npm dependencies.
5. Commit the completed work, push its branch, and create a pull request
   targeting `main` for every completed task.
6. When the task changes or clarifies the system design or product
   requirements, update the relevant ARCH and PRD documents in the same PR.
7. In the PR description, summarize the change, list the checks run, and
   call out any known limitations or follow-up work.
8. Agents may merge the PR once all CI checks pass for its latest commit.
   Wait for every check to finish successfully, including Quality, Worker
   runtime, Secret scanning, Python dependencies, and npm dependencies.
   Missing, pending, skipped, cancelled, or failing checks do not count as
   passing. Resolve review requests and conflicts and honor repository
   protection rules. Do not bypass required checks or use administrator
   overrides. After pushing any fix or updating the branch, wait for CI again.
9. Once the PR is confirmed merged, remove the task's worktree using the
   platform's managed cleanup tools when available, and delete its merged
   branch when safe. Never remove another agent's worktree or discard
   uncommitted work.
10. Update the shared local `main` checkout from `origin/main` with a
    fast-forward-only update. Preserve unrelated files and changes. If the
    checkout is busy, dirty in a way that prevents updating, or cannot
    fast-forward, report the blocker instead of resetting or overwriting it.

If worktree creation, pushing, PR creation, CI, merging, cleanup, or updating
`main` is blocked by missing credentials, permissions, tooling, or failed
checks, finish the unaffected work and report the exact blocker. Keep the
worktree until the PR is merged so its work remains recoverable.
