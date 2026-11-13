from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import govpack
from govpack import cli

from .conftest import ROOT, Editor

TODAY = "2026-11-13"


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = cli.main(list(argv))
    out = capsys.readouterr()
    return code, out.out, out.err


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert govpack.__version__ in capsys.readouterr().out


def test_check_passes_on_the_shipped_pack(capsys):
    code, out, _ = run(capsys, "check", "--root", str(ROOT), "--today", TODAY, "--fail-on", "low")
    assert code == 0
    assert "41 controls, 41 mappings, 11 rules: 0 findings" in out


def test_check_markdown_format(capsys):
    code, out, _ = run(
        capsys, "check", "--root", str(ROOT), "--today", TODAY, "--format", "markdown"
    )
    assert code == 0 and out.startswith("# govpack check")


def test_check_fails_on_findings_at_or_above_the_threshold(capsys, edit: Editor):
    edit.drop_mapping("EUAIA-09")
    code, out, _ = run(capsys, "check", "--root", str(edit.root), "--today", TODAY)
    assert code == 1 and "CRITICAL" in out and "GOV001" in out
    code, out, _ = run(
        capsys, "check", "--root", str(edit.root), "--today", TODAY, "--format", "markdown"
    )
    assert code == 1 and "| critical | GOV001 |" in out


def test_check_threshold_ignores_lower_severities(capsys, edit: Editor):
    edit.edit_mapping("EUAIA-04", "reviewed = 2026-11-13", "reviewed = 2025-01-01")  # medium
    assert run(capsys, "check", "--root", str(edit.root), "--today", TODAY)[0] == 0
    assert (
        run(capsys, "check", "--root", str(edit.root), "--today", TODAY, "--fail-on", "medium")[0]
        == 1
    )


def test_check_exits_2_when_the_pack_cannot_load(capsys, tmp_path: Path):
    code, _, err = run(capsys, "check", "--root", str(tmp_path))
    assert code == 2 and "error:" in err


def test_report_writes_then_checks(capsys, tmp_path: Path, edit: Editor):
    code, out, _ = run(capsys, "report", "--root", str(edit.root))
    assert code == 0 and "wrote 6 reports" in out
    assert run(capsys, "report", "--root", str(edit.root), "--check")[0] == 0
    (edit.root / "reports" / "coverage.md").write_text("changed\n")
    code, out, _ = run(capsys, "report", "--root", str(edit.root), "--check")
    assert code == 1 and "stale: reports/coverage.md" in out


def test_report_check_flags_missing_reports(capsys, edit: Editor):
    code, out, _ = run(capsys, "report", "--root", str(edit.root), "--check")
    assert code == 1 and out.count("stale:") == 6


def test_report_exits_2_on_a_broken_pack(capsys, tmp_path: Path):
    assert run(capsys, "report", "--root", str(tmp_path))[0] == 2


def test_verify_and_lock_on_a_mini_pack(capsys, mini):
    root, repos = mini
    # no lock yet: verify reports it, lock creates it
    code, out, err = run(capsys, "verify", "--root", str(root), "--repos", str(repos))
    assert code == 2 and "evidence.lock.json" in err  # missing lock is a load problem
    code, out, _ = run(
        capsys, "lock", "--root", str(root), "--repos", str(repos), "--date", "2026-11-01"
    )
    assert code == 0 and "pinned 1 evidence files" in out
    assert json.loads((root / "evidence.lock.json").read_text())["generated"] == "2026-11-01"
    code, out, _ = run(capsys, "verify", "--root", str(root), "--repos", str(repos))
    assert code == 0 and "match the lock" in out
    f = repos / "demo-repo" / "docs" / "log.md"
    f.write_text(f.read_text() + "edited\n")
    code, out, _ = run(capsys, "verify", "--root", str(root), "--repos", str(repos))
    assert code == 1 and "changed" in out and "evidence-drift.md" in out


def test_lock_refuses_to_pin_a_missing_phrase(capsys, mini):
    root, repos = mini
    (repos / "demo-repo" / "docs" / "log.md").write_text("nothing\n")
    code, out, _ = run(capsys, "lock", "--root", str(root), "--repos", str(repos))
    assert code == 1 and "phrase-missing" in out and "not writing the lock" in out
    assert not (root / "evidence.lock.json").exists()


def test_lock_exits_2_on_a_broken_pack(capsys, tmp_path: Path):
    assert run(capsys, "lock", "--root", str(tmp_path), "--repos", str(tmp_path))[0] == 2


def test_verify_exits_2_on_a_broken_pack(capsys, tmp_path: Path):
    assert run(capsys, "verify", "--root", str(tmp_path), "--repos", str(tmp_path))[0] == 2


def test_rules_lists_every_rule(capsys):
    code, out, _ = run(capsys, "rules")
    assert code == 0 and out.count("GOV0") == 11


def test_cli_runs_as_a_module():
    import subprocess
    import sys

    out = subprocess.run(
        [sys.executable, "-m", "govpack.cli", "--version"],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )
    assert govpack.__version__ in out.stdout


def test_copy_of_pack_is_independent(edit: Editor):
    assert edit.root != ROOT and (edit.root / "frameworks").is_dir()
    shutil.rmtree(edit.root / "frameworks")
    assert (ROOT / "frameworks").is_dir()
