from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO_ROOT / "docs" / "development" / "c08-opengame-spike"


def test_committed_stream_fixtures_are_valid_sanitized_ndjson() -> None:
    fixtures = sorted(EVIDENCE_DIR.glob("*-run.stream.json"))
    assert fixtures

    forbidden = (
        "yanjiusheng",
        "D:\\\\",
        "/Users/",
        '"uuid"',
        '"session_id"',
        '"thinking"',
        "OPENAI_API_KEY",
    )
    secret_pattern = re.compile(r"sk-[A-Za-z0-9_-]{12,}")

    for fixture in fixtures:
        lines = [line for line in fixture.read_text().splitlines() if line.strip()]
        assert lines, f"{fixture.name} must not be empty"
        for line in lines:
            json.loads(line)
        contents = "\n".join(lines)
        for value in forbidden:
            assert value not in contents, f"{fixture.name} contains {value}"
        assert secret_pattern.search(contents) is None


def test_c08_report_records_every_operation_conclusion() -> None:
    report = (EVIDENCE_DIR / "README.md").read_text().lower()

    for operation in (
        "create",
        "modify",
        "cancel",
        "timeout",
        "invalid output",
        "unsupported",
    ):
        assert operation in report


def test_portable_capture_script_has_no_developer_paths_or_secret_interpolation() -> None:
    script = (EVIDENCE_DIR / "capture-fixture.sh").read_text()

    assert "vendor/opengame/dist/cli.js" in script
    assert "yanjiusheng" not in script
    assert "D:/" not in script
    assert "D:\\" not in script
    assert "powershell" not in script.lower()
    assert "OPENAI_API_KEY='" not in script
    assert 'if [[ "$SCENARIO" == "failure" ]]; then\n  (\n    cd "$WORKSPACE"' in script


def test_c08_setup_builds_the_pinned_source_checkout() -> None:
    report = (EVIDENCE_DIR / "README.md").read_text()
    script = (EVIDENCE_DIR / "capture-fixture.sh").read_text()

    assert "npm ci" in report
    assert "npm run build" in report
    assert "npm ci" in script
    assert "npm run build" in script


def test_create_claim_has_committed_reviewable_provenance() -> None:
    provenance = json.loads((EVIDENCE_DIR / "create-run.provenance.json").read_text())

    assert provenance["opengame_commit"] == "c54307efe1dab927e7fc52dbb92af6b3df1d1c66"
    assert provenance["operation"] == "create"
    assert provenance["command"][0:2] == ["node", "vendor/opengame/dist/cli.js"]
    assert provenance["exit_code"] == 0
    assert provenance["terminal_event"]["type"] == "result"
    assert provenance["terminal_event"]["is_error"] is False
    assert provenance["artifact_checks"]["preview_entry"] == "index.html"
    assert provenance["artifact_checks"]["preview_entry_exists"] is True
    assert "index.html" in provenance["artifact_checks"]["output_tree"]
