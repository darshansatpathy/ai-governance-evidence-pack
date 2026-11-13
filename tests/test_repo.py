"""The repository must agree with itself: claims, links, workflows and generated files."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
import yaml

import govpack
from govpack import cli, render, rules

from .conftest import ROOT, TODAY

MD = [
    ROOT / "README.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "SECURITY.md",
    ROOT / "CHANGELOG.md",
    *(ROOT / "docs").rglob("*.md"),
]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_reports_are_current(capsys):
    assert cli.main(["report", "--check", "--root", str(ROOT)]) == 0
    assert "6 reports are current" in capsys.readouterr().out


def test_the_pack_passes_every_rule(capsys):
    code = cli.main(
        ["check", "--root", str(ROOT), "--today", TODAY.isoformat(), "--fail-on", "low"]
    )
    assert code == 0
    assert capsys.readouterr().out.strip() in README.replace("$ govpack check\n", "")


def test_version_matches_pyproject():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert project["version"] == govpack.__version__


def test_markdown_links_resolve():
    broken = []
    for f in MD:
        for m in re.finditer(r"\]\(([^)#\s][^)]*)\)", f.read_text()):
            target = m.group(1)
            if target.startswith("http"):
                continue
            if not (f.parent / target.split("#")[0]).resolve().exists():
                broken.append(f"{f.relative_to(ROOT)}: {target}")
    assert broken == []


def test_readme_table_matches_the_pack(real_pack):
    statuses = ("implemented", "partial", "designed", "organisational", "gap")
    for f in real_pack.frameworks:
        counts = [
            sum(1 for c in real_pack.controls_of(f.id) if real_pack.mapping(c.id).status == s)
            for s in statuses
        ]  # type: ignore[union-attr]
        row = (
            f"| {f.name} | {len(real_pack.controls_of(f.id))} | "
            + " | ".join(map(str, counts))
            + " |"
        )
        assert row in README, row
    total = [sum(1 for m in real_pack.mappings if m.status == s) for s in statuses]
    assert "| **All** | **41** | " + " | ".join(f"**{n}**" for n in total) + " |" in README
    assert "Only 6 of 41 controls are `implemented`" in README
    assert total[0] == 6 and total[4] == 1 and total[3] == 10


def test_readme_numbers_match_the_pack(real_pack):
    assert f"{len(real_pack.lock.files)} evidence files" in README
    assert f"**{len(real_pack.controls)}**" in README
    assert "nine repositories" in README and len(real_pack.repos) == 9
    assert "eleven rules" in README and len(rules.REGISTRY) == 11
    assert "50 evidence files match the lock" in README and len(real_pack.lock.files) == 50
    for r in real_pack.repos:
        assert f"/{r.name})" in README, r.name


def test_readme_rule_table_matches_the_registry():
    rows = re.findall(r"^\| `(GOV\d{3})` \| (\w+) \| (.+) \|$", README, re.MULTILINE)
    assert [(i, s, t) for i, s, t, _ in rules.catalog()] == rows


def test_every_command_is_documented():
    for cmd in ("check", "report", "verify", "lock", "rules"):
        assert f"govpack {cmd}" in README, cmd


def test_every_registered_repository_is_used_as_evidence(real_pack):
    used = {e.repo for _, e in real_pack.evidence_items()}
    assert used == {r.name for r in real_pack.repos}


def test_every_framework_has_a_report_section_and_source(real_pack):
    text = render.coverage(real_pack)
    for f in real_pack.frameworks:
        assert f"## {f.name}" in text and f.source.startswith("https://")


def test_adrs_are_numbered_complete_and_linked():
    adrs = sorted((ROOT / "docs" / "adr").glob("*.md"))
    assert [p.name[:4] for p in adrs] == [f"{i:04d}" for i in range(1, len(adrs) + 1)]
    for p in adrs:
        text = p.read_text()
        for heading in ("## Status", "## Context", "## Decision", "## Consequences"):
            assert heading in text, f"{p.name} lacks {heading}"
        assert p.name in README


@pytest.mark.parametrize(
    "path", sorted((ROOT / "docs" / "runbooks").glob("*.md")), ids=lambda p: p.stem
)
def test_runbooks_are_complete_and_linked(path):
    text = path.read_text()
    for h in (
        "## Purpose",
        "## Triggers",
        "## First checks",
        "## Steps",
        "## Verification",
        "## Escalation",
    ):
        assert h in text, f"{path.name} lacks {h}"
    assert path.name in README


def test_regulatory_note_names_the_amending_regulation():
    text = (ROOT / "docs" / "regulatory-status.md").read_text()
    for needle in ("2026/1744", "2 December 2027", "2 August 2028", "Article 50", "2026-11-13"):
        assert needle in text, needle


def test_the_known_gap_is_recorded_and_explained(real_pack):
    m = real_pack.mapping("EUAIA-50")
    assert m is not None and m.status == "gap" and m.evidence == ()
    assert "EUAIA-50" in (ROOT / "docs" / "regulatory-status.md").read_text()


def test_workflows_exist_and_parse():
    for name in ("ci.yml", "codeql.yml", "verify-evidence.yml"):
        doc = yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text())
        assert doc["jobs"], name


def test_ci_runs_the_pack_gates():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    for cmd in ("govpack check", "govpack report --check", "--cov-fail-under=85", "mypy"):
        assert cmd in ci, cmd


def test_verification_workflow_reads_the_registry_and_runs_verify():
    text = (ROOT / ".github" / "workflows" / "verify-evidence.yml").read_text()
    assert "repos.toml" in text and "govpack verify --repos" in text
    assert "govpack check --fail-on low" in text
    assert "schedule:" in text and "workflow_dispatch" in text
    assert "permissions:\n  contents: read" in text
    assert "secrets." not in text


def test_registry_urls_are_public_https():
    data = tomllib.loads((ROOT / "repos.toml").read_text())
    for r in data["repo"]:
        assert r["url"] == f"https://github.com/darshansatpathy/{r['name']}"


SECRET_PATTERNS = [
    r"ghp_[A-Za-z0-9]{20,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"sk-ant-[A-Za-z0-9-]{20,}",
]
SKIP_DIRS = {".git", ".venv", "__pycache__", ".ruff_cache", ".mypy_cache", ".pytest_cache"}


def test_no_secrets_in_the_repository():
    hits = []
    for f in ROOT.rglob("*"):
        if not f.is_file() or SKIP_DIRS & set(f.relative_to(ROOT).parts) or f == Path(__file__):
            continue
        try:
            text = f.read_text()
        except UnicodeDecodeError:
            continue
        hits += [f"{f.relative_to(ROOT)}: {p}" for p in SECRET_PATTERNS if re.search(p, text)]
    assert hits == []


def test_data_files_contain_no_compliance_claims():
    # GOV006 covers the pack data; this covers the prose that introduces it.
    for f in [README, *(ROOT / "docs").rglob("*.md")]:
        text = f.read_text() if isinstance(f, Path) else f
        for m in re.finditer(
            r"\b(we are compliant|is certified|fully compliant|guarantees compliance)\b", text, re.I
        ):
            pytest.fail(f"{f}: {m.group(0)}")
