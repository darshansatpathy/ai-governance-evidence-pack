"""The data model and the loader for the control library, mappings, repositories and systems.

Everything is plain TOML. The loader reports every problem it finds in one pass, with the file
and location, instead of stopping at the first.
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

STATUSES = ("implemented", "partial", "designed", "organisational", "gap")
APPLIES_TO = ("provider", "deployer", "both")
CONTROL_KINDS = ("technical", "organisational", "mixed")
EVIDENCE_KINDS = ("code", "test", "config", "doc")
# Kinds of evidence that show something running, as opposed to something written down.
OPERATING_KINDS = ("code", "test", "config")


@dataclass(frozen=True)
class Framework:
    id: str
    name: str
    citation: str
    source: str
    ref_pattern: str
    checked: date
    note: str


@dataclass(frozen=True)
class Control:
    id: str
    framework: str
    ref: str
    title: str
    summary: str
    applies_to: str
    kind: str


@dataclass(frozen=True)
class Evidence:
    repo: str
    path: str
    kind: str
    contains: str
    shows: str

    @property
    def key(self) -> str:
        return f"{self.repo}:{self.path}"


@dataclass(frozen=True)
class Mapping:
    control: str
    status: str
    rationale: str
    limits: str
    owner: str
    next_step: str
    reviewed: date
    evidence: tuple[Evidence, ...]
    source_file: str = ""


@dataclass(frozen=True)
class Repo:
    name: str
    url: str
    role: str


@dataclass(frozen=True)
class Component:
    repo: str
    role: str


@dataclass(frozen=True)
class System:
    id: str
    name: str
    summary: str
    intended_purpose: str
    provider_role: str
    deployer_role: str
    risk_note: str
    oversight: str
    logging: str
    data: str
    components: tuple[Component, ...]
    limitations: tuple[str, ...]
    controls: tuple[str, ...]


@dataclass(frozen=True)
class LockEntry:
    sha256: str
    size: int


@dataclass(frozen=True)
class Lock:
    generated: str
    files: dict[str, LockEntry] = field(default_factory=dict)


@dataclass(frozen=True)
class Pack:
    frameworks: tuple[Framework, ...]
    controls: tuple[Control, ...]
    mappings: tuple[Mapping, ...]
    repos: tuple[Repo, ...]
    systems: tuple[System, ...]
    lock: Lock
    review_days: int

    def control(self, cid: str) -> Control | None:
        return next((c for c in self.controls if c.id == cid), None)

    def framework(self, fid: str) -> Framework | None:
        return next((f for f in self.frameworks if f.id == fid), None)

    def mapping(self, cid: str) -> Mapping | None:
        return next((m for m in self.mappings if m.control == cid), None)

    def repo(self, name: str) -> Repo | None:
        return next((r for r in self.repos if r.name == name), None)

    def controls_of(self, fid: str) -> list[Control]:
        return [c for c in self.controls if c.framework == fid]

    def evidence_items(self) -> list[tuple[Mapping, Evidence]]:
        return [(m, e) for m in self.mappings for e in m.evidence]


class _Reader:
    """Typed access to a TOML mapping that records problems with their location."""

    def __init__(self, data: Any, where: str, problems: list[str]) -> None:
        self.data: dict[str, Any] = data if isinstance(data, dict) else {}
        self.where = where
        self.problems = problems
        if not isinstance(data, dict):
            problems.append(f"{where}: expected a table")

    def _p(self, key: str, msg: str) -> None:
        self.problems.append(f"{self.where}: '{key}' {msg}")

    def req(self, key: str) -> str:
        v = self.data.get(key)
        if v is None:
            self._p(key, "is required")
            return ""
        if not isinstance(v, str):
            self._p(key, "must be a string")
            return ""
        return v

    def opt(self, key: str, default: str = "") -> str:
        v = self.data.get(key, default)
        if not isinstance(v, str):
            self._p(key, "must be a string")
            return default
        return v

    def day(self, key: str) -> date:
        v = self.data.get(key)
        if isinstance(v, date):
            return v
        self._p(key, "must be a date such as 2026-11-13")
        return date(1970, 1, 1)

    def strs(self, key: str) -> tuple[str, ...]:
        v = self.data.get(key, [])
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            self._p(key, "must be a list of strings")
            return ()
        return tuple(v)

    def rows(self, key: str) -> list[Any]:
        v = self.data.get(key, [])
        if not isinstance(v, list):
            self._p(key, "must be an array of tables")
            return []
        return v

    def unknown(self, allowed: set[str]) -> None:
        for k in sorted(set(self.data) - allowed):
            self._p(k, "is not a known field")


def _read(path: Path, problems: list[str]) -> dict[str, Any]:
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        problems.append(f"{path.name}: {exc}")
        return {}


def _framework(path: Path, problems: list[str]) -> tuple[Framework | None, list[Control]]:
    data = _read(path, problems)
    where = path.name
    top = _Reader(data, where, problems)
    top.unknown({"framework", "controls"})
    fr = _Reader(data.get("framework"), f"{where}[framework]", problems)
    fr.unknown({"id", "name", "citation", "source", "ref_pattern", "checked", "note"})
    fid = fr.req("id")
    framework = Framework(
        id=fid,
        name=fr.req("name"),
        citation=fr.req("citation"),
        source=fr.req("source"),
        ref_pattern=fr.req("ref_pattern"),
        checked=fr.day("checked"),
        note=fr.opt("note"),
    )
    controls = []
    for i, raw in enumerate(top.rows("controls")):
        r = _Reader(raw, f"{where}[controls][{i}]", problems)
        r.unknown({"id", "ref", "title", "summary", "applies_to", "kind"})
        controls.append(
            Control(
                id=r.req("id"),
                framework=fid,
                ref=r.req("ref"),
                title=r.req("title"),
                summary=r.req("summary"),
                applies_to=r.req("applies_to"),
                kind=r.req("kind"),
            )
        )
    return framework, controls


def _mappings(path: Path, problems: list[str]) -> list[Mapping]:
    data = _read(path, problems)
    where = path.name
    top = _Reader(data, where, problems)
    top.unknown({"framework", "mapping"})
    out = []
    for i, raw in enumerate(top.rows("mapping")):
        r = _Reader(raw, f"{where}[mapping][{i}]", problems)
        r.unknown(
            {
                "control",
                "status",
                "rationale",
                "limits",
                "owner",
                "next_step",
                "reviewed",
                "evidence",
            }
        )
        evidence = []
        for j, eraw in enumerate(r.rows("evidence")):
            e = _Reader(eraw, f"{where}[mapping][{i}].evidence[{j}]", problems)
            e.unknown({"repo", "path", "kind", "contains", "shows"})
            evidence.append(
                Evidence(
                    repo=e.req("repo"),
                    path=e.req("path"),
                    kind=e.req("kind"),
                    contains=e.req("contains"),
                    shows=e.req("shows"),
                )
            )
        out.append(
            Mapping(
                control=r.req("control"),
                status=r.req("status"),
                rationale=r.req("rationale"),
                limits=r.opt("limits"),
                owner=r.opt("owner"),
                next_step=r.opt("next_step"),
                reviewed=r.day("reviewed"),
                evidence=tuple(evidence),
                source_file=where,
            )
        )
    return out


def _repos(path: Path, problems: list[str]) -> list[Repo]:
    data = _read(path, problems)
    top = _Reader(data, path.name, problems)
    top.unknown({"repo"})
    out = []
    for i, raw in enumerate(top.rows("repo")):
        r = _Reader(raw, f"{path.name}[repo][{i}]", problems)
        r.unknown({"name", "url", "role"})
        out.append(Repo(name=r.req("name"), url=r.req("url"), role=r.req("role")))
    return out


def _systems(folder: Path, problems: list[str]) -> list[System]:
    out = []
    for path in sorted(folder.glob("*.toml")):
        data = _read(path, problems)
        r = _Reader(data.get("system"), f"{path.name}[system]", problems)
        top = _Reader(data, path.name, problems)
        top.unknown({"system", "components"})
        r.unknown(
            {
                "id", "name", "summary", "intended_purpose", "provider_role", "deployer_role",
                "risk_note", "oversight", "logging", "data", "limitations", "controls",
            }
        )  # fmt: skip
        comps = []
        for i, raw in enumerate(top.rows("components")):
            c = _Reader(raw, f"{path.name}[components][{i}]", problems)
            c.unknown({"repo", "role"})
            comps.append(Component(repo=c.req("repo"), role=c.req("role")))
        out.append(
            System(
                id=r.req("id"),
                name=r.req("name"),
                summary=r.req("summary"),
                intended_purpose=r.req("intended_purpose"),
                provider_role=r.req("provider_role"),
                deployer_role=r.req("deployer_role"),
                risk_note=r.req("risk_note"),
                oversight=r.req("oversight"),
                logging=r.req("logging"),
                data=r.req("data"),
                components=tuple(comps),
                limitations=r.strs("limitations"),
                controls=r.strs("controls"),
            )
        )
    return out


def read_lock(path: Path, problems: list[str] | None = None) -> Lock:
    problems = problems if problems is not None else []
    if not path.exists():
        problems.append(f"{path.name}: missing; run `govpack lock`")
        return Lock(generated="")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        files = {
            str(k): LockEntry(sha256=str(v["sha256"]), size=int(v["size"]))
            for k, v in raw["files"].items()
        }
        return Lock(generated=str(raw["generated"]), files=files)
    except (ValueError, KeyError, TypeError) as exc:
        problems.append(f"{path.name}: not a valid lock file ({exc!r})")
        return Lock(generated="")


def load(root: Path) -> tuple[Pack | None, list[str]]:
    """Load the pack under ``root``; returns the pack (None if it cannot be built) and problems."""
    problems: list[str] = []
    frameworks: list[Framework] = []
    controls: list[Control] = []
    for path in sorted((root / "frameworks").glob("*.toml")):
        fw, cs = _framework(path, problems)
        if fw:
            frameworks.append(fw)
        controls.extend(cs)
    mappings: list[Mapping] = []
    for path in sorted((root / "mappings").glob("*.toml")):
        mappings.extend(_mappings(path, problems))
    repos = _repos(root / "repos.toml", problems) if (root / "repos.toml").exists() else []
    if not (root / "repos.toml").exists():
        problems.append("repos.toml: missing")
    systems = _systems(root / "systems", problems)
    settings = _read(root / "pack.toml", problems) if (root / "pack.toml").exists() else {}
    review_days = settings.get("review_days", 180)
    if not isinstance(review_days, int) or review_days < 1:
        problems.append("pack.toml: 'review_days' must be a positive integer")
        review_days = 180
    lock = read_lock(root / "evidence.lock.json", problems)
    if not frameworks:
        return None, [*problems, "no frameworks found under frameworks/"]
    return (
        Pack(
            frameworks=tuple(frameworks),
            controls=tuple(controls),
            mappings=tuple(mappings),
            repos=tuple(repos),
            systems=tuple(systems),
            lock=lock,
            review_days=review_days,
        ),
        problems,
    )
