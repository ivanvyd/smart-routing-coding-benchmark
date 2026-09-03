import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "results"
ARMS = ("FIXED_STRONG", "FIXED_CHEAP", "CLIENT_ROUTING")
PRIVATE_FIELDS = {
    "account_id",
    "endpoint_id",
    "invocation_id",
    "request_id",
    "requester",
    "workspace_id",
}


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_public_evidence_has_every_attempt_without_private_fields() -> None:
    for arm in ARMS:
        normalized = _jsonl(EVIDENCE / "normalized" / f"{arm}.jsonl")
        attributed = _jsonl(EVIDENCE / "attributed" / f"{arm}.jsonl")
        assert len(normalized) == 24
        assert len(attributed) == 24
        assert all(PRIVATE_FIELDS.isdisjoint(row) for row in normalized + attributed)


def test_public_text_contains_no_identity_or_workspace_values() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "evidence").rglob("*")
        if path.suffix in {".json", ".jsonl", ".md"}
    )
    assert not re.search(r"[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    assert not re.search(r"https?://[^\s\"]*databricks", text)
    assert not re.search(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        text,
    )
