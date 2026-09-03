"""Deterministic evaluators.

The benchmark explicitly does NOT use an LLM judge for anything that can be
checked deterministically. The evaluator's job is to run the verifier command
the task declares (pytest, mypy, ruff, a SQL assertion, a structured-output
check) and report pass/fail with as much evidence as possible.
"""
