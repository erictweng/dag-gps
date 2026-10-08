# DAG GPS delivery workflow

Eric explicitly authorizes direct pushes to `main` for this project. PR creation and manual merge approval are not required for future verified changes.

Workers may build on isolated branches. The parent reviews and runs the relevant unit/evaluation/browser gates before integrating and pushing to `main`. Fetch remote state first, preserve other workers' edits, never force-push, and verify the remote commit after pushing.

This authorization is specific to `erictweng/dag-gps`; it does not apply to quest-coder or Eric's other repositories.

Existing PRs #3–#5 were retargeted to main and merged in order. PR #2 originally merged into m1-canvas; its implementation is now also on main through PR #3.
