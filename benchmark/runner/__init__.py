"""Benchmark runner.

For each (arm, task) pair, the runner:
  1. Creates an isolated git worktree from the same base commit.
  2. Applies the task prompt to that worktree.
  3. Invokes Claude Code via `ucode claude` with the prompt on the command line.
  4. Captures stdout, stderr, exit code, git diff, start/end timestamps.
  5. Runs the deterministic evaluator.
  6. Destroys the worktree.

The deterministic evaluator, rather than an LLM judge, determines pass or fail.
"""

from .env import capture_env
from .runner import Runner, RunResult

__all__ = ["RunResult", "Runner", "capture_env"]
