from __future__ import annotations

import json
from pathlib import Path

from govpack import pack as packmod

from .conftest import ROOT, Editor


def test_the_real_pack_loads_without_problems(real_pack):
    assert len(real_pack.frameworks) == 3
    assert len(real_pack.controls) == 41
    assert len(real_pack.mappings) == 41
    assert len(real_pack.repos) == 9
    assert len(real_pack.systems) == 1
    assert real_pack.review_days == 180


def test_lookups(real_pack):
    assert real_pack.control("EUAIA-14").title == "Human oversight"
    assert real_pack.control("nope") is None
    assert real_pack.framework("iso-42001").name.startswith("ISO")
    assert real_pack.mapping("EUAIA-50").status == "gap"
    assert real_pack.repo("agent-eval-harness") is not None
    assert len(real_pack.controls_of("eu-ai-act")) == 13


def test_evidence_items_pair_mappings_with_evidence(real_pack):
    items = real_pack.evidence_items()
    assert items and all(e in m.evidence for m, e in items)
    assert {e.key for _, e in items} == set(real_pack.lock.files)


def test_loader_reports_every_problem_together(edit: Editor):
    edit.replace("frameworks/eu-ai-act.toml", 'title = "Human oversight"\n', "")
    edit.replace("frameworks/eu-ai-act.toml", 'kind = "technical"', "kind = 7", count=1)
    edit.replace(
        "mappings/nist-ai-rmf.toml",
        'status = "implemented"',
        'status = "implemented"\nsurprise = 1',
    )
    pack, problems = packmod.load(edit.root)
    assert pack is not None
    joined = "\n".join(problems)
    assert "'title' is required" in joined
    assert "'kind' must be a string" in joined
    assert "'surprise' is not a known field" in joined
    assert len(problems) >= 3


def test_loader_reports_bad_dates_and_lists(edit: Editor):
    edit.replace("mappings/eu-ai-act.toml", "reviewed = 2026-11-13", 'reviewed = "yesterday"')
    edit.replace("systems/support-agent.toml", "limitations = [", "limitations = 5\nignored = [")
    _, problems = packmod.load(edit.root)
    joined = "\n".join(problems)
    assert "'reviewed' must be a date" in joined
    assert "'limitations' must be a list of strings" in joined
    assert "'ignored' is not a known field" in joined or "'ignored'" in joined


def test_loader_reports_non_table_values(edit: Editor):
    edit.write("mappings/eu-ai-act.toml", 'framework = "eu-ai-act"\nmapping = [1, 2]\n')
    _, problems = packmod.load(edit.root)
    assert any("expected a table" in p for p in problems)


def test_loader_reports_broken_toml(edit: Editor):
    edit.write("mappings/eu-ai-act.toml", "this is = = not toml")
    _, problems = packmod.load(edit.root)
    assert any(p.startswith("eu-ai-act.toml") for p in problems)


def test_loader_reports_missing_repos_file_and_bad_settings(edit: Editor):
    edit.path("repos.toml").unlink()
    edit.write("pack.toml", "review_days = 0\n")
    _, problems = packmod.load(edit.root)
    assert "repos.toml: missing" in problems
    assert any("review_days" in p for p in problems)


def test_loader_without_frameworks(tmp_path: Path):
    pack, problems = packmod.load(tmp_path)
    assert pack is None
    assert any("no frameworks" in p for p in problems)


def test_lock_problems(tmp_path: Path):
    problems: list[str] = []
    assert packmod.read_lock(tmp_path / "nope.json", problems).files == {}
    assert "missing" in problems[0]
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert packmod.read_lock(bad, problems).files == {}
    assert "not a valid lock file" in problems[1]
    wrong = tmp_path / "wrong.json"
    wrong.write_text(
        json.dumps({"generated": "x", "files": {"a": {"sha256": "b"}}}), encoding="utf-8"
    )
    assert packmod.read_lock(wrong, problems).files == {}
    assert len(problems) == 3
    assert packmod.read_lock(ROOT / "evidence.lock.json").generated == "2026-11-13"


def test_reader_default_problem_list_is_optional(tmp_path: Path):
    good = tmp_path / "ok.json"
    good.write_text(json.dumps({"generated": "d", "files": {}}), encoding="utf-8")
    assert packmod.read_lock(good).generated == "d"
