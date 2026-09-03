# Databricks notebook source
# MAGIC %md
# MAGIC # Transparent model-routing benchmark
# MAGIC
# MAGIC This notebook renders the same commit-scoped analysis as `src-analyze`.
# MAGIC The treatment is a disclosed client router, not Databricks Smart Routing.

# COMMAND ----------

import json
import subprocess
import sys
from pathlib import Path

root = Path("/Workspace/Users/<you>/smart-routing-coding-benchmark")
results = root / "results"


def show(value: object) -> None:
    renderer = globals().get("display")
    if callable(renderer):
        renderer(value)
    else:
        print(value)

# COMMAND ----------

completed = subprocess.run(
    [
        sys.executable,
        "-m",
        "benchmark.analysis.cli",
        "--results-dir",
        str(results),
        "--manifest",
        str(root / "benchmark" / "manifest.yaml"),
        "--exclusions",
        str(root / "benchmark" / "exclusions.yaml"),
    ],
    cwd=root,
    check=False,
    capture_output=True,
    text=True,
)
print(completed.stdout)
if completed.returncode:
    raise RuntimeError(completed.stderr)

# COMMAND ----------

summary = json.loads((results / "tables" / "summary.json").read_text())
show(summary["metrics"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Exclusions and routing diagnostics
# MAGIC
# MAGIC Exclusions apply only to the base commit named in
# MAGIC `benchmark/exclusions.yaml`. The raw attempted runs remain available.

# COMMAND ----------

show(summary["excluded_tasks"])
show(summary["router_error_cases"])
