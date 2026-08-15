# Agent Development Workflow

These instructions apply to every new task in this repository.

## Branches and pull requests

1. Start from the latest `main` branch and create a dedicated branch before
   changing any files. Do not develop directly on `main`.
2. Use a descriptive branch name with the `codex/` prefix, such as
   `codex/add-user-settings` or `codex/fix-webhook-timeout`.
3. Keep all task changes isolated to that branch. Do not mix unrelated cleanup
   or feature work into the task.
4. Run the relevant checks before handing the work off. For this project, the
   standard checks are:

   ```sh
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src
   uv run pytest
   ```

5. Commit the completed work with a clear message, push the branch, and open a
   pull request targeting `main`.
6. When the completed task changes or clarifies the system design or product
   requirements, update the relevant ARCH and PRD documents in the same branch.
7. In the pull request description, summarize the change, list the checks that
   were run, and call out any known limitations or follow-up work.
8. Do not merge the pull request unless the task explicitly asks you to do so.

If a branch cannot be pushed or a pull request cannot be opened because of
missing credentials, permissions, or tooling, finish the local work and report
the exact blocker clearly instead of silently skipping the handoff.
