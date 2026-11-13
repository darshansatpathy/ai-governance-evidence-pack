from __future__ import annotations

import hashlib
import os
from pathlib import Path

from govpack import lock
from govpack import pack as packmod


def load_mini(root: Path) -> packmod.Pack:
    pack, _ = packmod.load(root)
    assert pack is not None
    return pack


def built(mini: tuple[Path, Path]) -> packmod.Pack:
    root, repos = mini
    pack = load_mini(root)
    new, drift = lock.build(pack, repos, "2026-11-01")
    assert drift == [] and new is not None
    lock.write(new, root / "evidence.lock.json")
    return load_mini(root)


def test_sha256_matches_hashlib(mini):
    _, repos = mini
    target = repos / "demo-repo" / "docs" / "log.md"
    assert lock.sha256_of(target) == hashlib.sha256(target.read_bytes()).hexdigest()


def test_build_write_and_check_roundtrip(mini):
    root, repos = mini
    pack = built(mini)
    assert list(pack.lock.files) == ["demo-repo:docs/log.md"]
    assert pack.lock.generated == "2026-11-01"
    assert lock.check(pack, repos) == []
    # the file is stable text with a trailing newline
    text = (root / "evidence.lock.json").read_text()
    assert text.endswith("}\n") and '"schema": 1' in text


def test_check_reports_a_changed_file(mini):
    _, repos = mini
    pack = built(mini)
    f = repos / "demo-repo" / "docs" / "log.md"
    f.write_text(f.read_text() + "one more line\n")
    drift = lock.check(pack, repos)
    assert [d.kind for d in drift] == ["changed"]


def test_check_reports_a_missing_phrase_even_if_hash_matches_nothing(mini):
    _, repos = mini
    pack = built(mini)
    (repos / "demo-repo" / "docs" / "log.md").write_text("# Log\nThe module is silent.\n")
    kinds = sorted(d.kind for d in lock.check(pack, repos))
    assert kinds == ["changed", "phrase-missing"]


def test_check_reports_a_missing_file_and_missing_repo(mini):
    _, repos = mini
    pack = built(mini)
    (repos / "demo-repo" / "docs" / "log.md").unlink()
    assert [d.kind for d in lock.check(pack, repos)] == ["missing-file"]
    assert [d.kind for d in lock.check(pack, repos / "elsewhere")] == ["missing-repo"]


def test_check_reports_unlocked_evidence(mini):
    root, repos = mini
    pack = load_mini(root)  # no lock written
    assert [d.kind for d in lock.check(pack, repos)] == ["not-locked"]


def test_paths_cannot_escape_the_repository(mini):
    root, repos = mini
    (repos / "secret.txt").write_text("outside the repo, contains: writes a log line\n")
    text = (root / "mappings" / "demo.toml").read_text().replace("docs/log.md", "../secret.txt")
    (root / "mappings" / "demo.toml").write_text(text)
    pack = load_mini(root)
    assert [d.kind for d in lock.check(pack, repos)] == ["missing-file"]
    new, drift = lock.build(pack, repos, "x")
    assert new is None and drift[0].kind == "missing-file"


def test_a_symlink_out_of_the_repository_is_refused(mini):
    root, repos = mini
    outside = repos / "outside.md"
    outside.write_text("The module writes a log line.\n")
    link = repos / "demo-repo" / "docs" / "link.md"
    os.symlink(outside, link)
    text = (root / "mappings" / "demo.toml").read_text().replace("docs/log.md", "docs/link.md")
    (root / "mappings" / "demo.toml").write_text(text)
    pack = load_mini(root)
    new, drift = lock.build(pack, repos, "x")
    assert new is None and drift[0].kind == "missing-file"


def test_build_refuses_when_the_phrase_is_missing(mini):
    root, repos = mini
    (repos / "demo-repo" / "docs" / "log.md").write_text("nothing relevant\n")
    new, drift = lock.build(load_mini(root), repos, "x")
    assert new is None and drift[0].kind == "phrase-missing"


def test_missing_repo_is_reported_once(mini):
    root, repos = mini
    text = (root / "mappings" / "demo.toml").read_text()
    extra = text.split("[[mapping.evidence]]")[1]
    (root / "mappings" / "demo.toml").write_text(
        text + "\n[[mapping.evidence]]" + extra.replace("docs/log.md", "docs/two.md")
    )
    pack = load_mini(root)
    drift = lock.check(pack, repos / "elsewhere")
    assert [d.kind for d in drift] == ["missing-repo"]
