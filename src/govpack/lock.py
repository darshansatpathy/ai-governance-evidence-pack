"""Pin evidence files by hash and check them against checked-out repositories."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from govpack.pack import Lock, LockEntry, Pack


@dataclass(frozen=True)
class Drift:
    key: str
    kind: str  # missing-repo | missing-file | changed | phrase-missing | not-locked
    detail: str


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve(repos: Path, repo: str, rel: str) -> Path | None:
    base = (repos / repo).resolve()
    target = (base / rel).resolve()
    if not target.is_relative_to(base):
        return None
    return target


def check(pack: Pack, repos: Path) -> list[Drift]:
    """Compare every evidence item with the checked-out repositories and the lock."""
    out: list[Drift] = []
    done: set[str] = set()
    for _, e in pack.evidence_items():
        target = _resolve(repos, e.repo, e.path)
        if not (repos / e.repo).is_dir():
            if e.repo not in done:
                out.append(Drift(e.repo, "missing-repo", f"{repos / e.repo} is not a directory"))
                done.add(e.repo)
            continue
        if target is None or not target.is_file():
            out.append(Drift(e.key, "missing-file", "file does not exist in the checkout"))
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        if e.contains not in text:
            out.append(Drift(e.key, "phrase-missing", f"expected text not found: {e.contains!r}"))
        locked = pack.lock.files.get(e.key)
        if locked is None:
            out.append(Drift(e.key, "not-locked", "no entry in evidence.lock.json"))
        elif locked.sha256 != sha256_of(target):
            out.append(Drift(e.key, "changed", "content differs from the pinned hash"))
    return out


def build(pack: Pack, repos: Path, generated: str) -> tuple[Lock | None, list[Drift]]:
    """Hash every evidence file. Refuses when a file or a required phrase is missing."""
    problems: list[Drift] = []
    files: dict[str, LockEntry] = {}
    for _, e in pack.evidence_items():
        target = _resolve(repos, e.repo, e.path)
        if target is None or not target.is_file():
            problems.append(Drift(e.key, "missing-file", "file does not exist in the checkout"))
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        if e.contains not in text:
            problems.append(
                Drift(e.key, "phrase-missing", f"expected text not found: {e.contains!r}")
            )
            continue
        files[e.key] = LockEntry(sha256=sha256_of(target), size=target.stat().st_size)
    if problems:
        return None, problems
    return Lock(generated=generated, files=dict(sorted(files.items()))), []


def write(lock: Lock, path: Path) -> None:
    body = {
        "schema": 1,
        "generated": lock.generated,
        "files": {k: {"sha256": v.sha256, "size": v.size} for k, v in sorted(lock.files.items())},
    }
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
