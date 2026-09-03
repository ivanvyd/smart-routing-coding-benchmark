import csv
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _rows(task_id: str, query: str) -> list[tuple[str, int]]:
    sql_dir = (
        ROOT
        / "tasks"
        / ("easy" if task_id.startswith("easy") else "medium")
        / task_id
        / "repo"
        / "sql"
    )
    connection = sqlite3.connect(":memory:")
    connection.executescript((sql_dir / "schema.sql").read_text(encoding="utf-8"))
    connection.executescript((sql_dir / "seed.sql").read_text(encoding="utf-8"))
    return list(connection.execute(query))


def _expected(task_id: str) -> list[tuple[str, int]]:
    tier = "easy" if task_id.startswith("easy") else "medium"
    path = ROOT / "tasks" / tier / task_id / "repo" / "sql" / "expected.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return [(row[0], int(row[1])) for row in list(csv.reader(handle))[1:]]


def test_easy_004_fixture_has_a_valid_solution() -> None:
    task_dir = ROOT / "tasks" / "easy" / "easy-004"
    task = yaml.safe_load((task_dir / "task.yaml").read_text(encoding="utf-8"))
    assert "expected[1:]" in task["verifier"]
    solution = """
        SELECT substr(event_ts, 1, 10), COUNT(DISTINCT user_id)
        FROM events
        WHERE kind IN ('page_view', 'click')
        GROUP BY substr(event_ts, 1, 10)
        ORDER BY 1
    """
    assert _rows("easy-004", solution) == _expected("easy-004")


def test_medium_007_fixture_exposes_the_declared_fanout() -> None:
    task_dir = ROOT / "tasks" / "medium" / "medium-007" / "repo" / "sql"
    broken = (task_dir / "weekly_active.sql").read_text(encoding="utf-8")
    solution = """
        SELECT strftime('%Y-%W', event_ts), COUNT(DISTINCT account_id)
        FROM events
        WHERE kind IN ('login', 'click')
        GROUP BY strftime('%Y-%W', event_ts)
        ORDER BY 1
    """
    assert _rows("medium-007", broken) != _expected("medium-007")
    assert _rows("medium-007", solution) == _expected("medium-007")


def test_hard_005_fixture_has_a_valid_solution(tmp_path: Path) -> None:
    repo = ROOT / "tasks" / "hard" / "hard-005" / "repo"
    candidate = tmp_path / "repo"
    shutil.copytree(repo, candidate)
    before = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/"],
        cwd=candidate,
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert before.returncode != 0

    fetcher = candidate / "src" / "fetcher.py"
    source = fetcher.read_text(encoding="utf-8")
    fetcher.write_text(
        source.replace("urlopen(url)", "urlopen(url, timeout=timeout)"),
        encoding="utf-8",
    )
    after = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/"],
        cwd=candidate,
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert after.returncode == 0, after.stdout + after.stderr
