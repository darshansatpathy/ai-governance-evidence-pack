"""Policy rules over the pack. Each rule has an ID, a severity and a failing-case test.

The rules check that the pack is internally honest: every control is accounted for, statuses are
backed by the right kind of evidence, gaps have an owner and a next step, evidence is pinned, and
the wording does not claim more than a mapping can show.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date, timedelta

from govpack.pack import (
    APPLIES_TO,
    CONTROL_KINDS,
    EVIDENCE_KINDS,
    OPERATING_KINDS,
    STATUSES,
    Pack,
)

SEVERITIES = ("low", "medium", "high", "critical")


def severity_rank(s: str) -> int:
    return SEVERITIES.index(s)


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    subject: str
    message: str


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    title: str
    why: str
    check: Callable[[Pack, date], Iterator[tuple[str, str]]]


REGISTRY: list[Rule] = []


def rule(
    rule_id: str, severity: str, title: str, why: str
) -> Callable[[Callable[[Pack, date], Iterator[tuple[str, str]]]], Callable[..., object]]:
    def wrap(fn: Callable[[Pack, date], Iterator[tuple[str, str]]]) -> Callable[..., object]:
        REGISTRY.append(Rule(rule_id, severity, title, why, fn))
        return fn

    return wrap


# Words that turn "this evidence supports a control" into "this system satisfies the law".
OVERCLAIM = re.compile(
    r"\b(fully compliant|is compliant|are compliant|compliant with|certified|certification achieved"
    r"|guarantees? compliance|ensures? compliance|meets all|satisfies the (?:act|regulation|standard))\b",
    re.IGNORECASE,
)
ID_FORMAT = re.compile(r"[A-Z0-9]+(?:-[A-Z0-9]+)*-[A-Za-z0-9.]+")
ABSOLUTE_PATH = re.compile(r"^(?:/|[A-Za-z]:|\\|~)")


@rule(
    "GOV001",
    "critical",
    "Every control has exactly one mapping, and every mapping names a control",
    "A control without a mapping is an unexamined gap; a mapping without a control is noise.",
)
def _complete(p: Pack, today: date) -> Iterator[tuple[str, str]]:
    seen: dict[str, int] = {}
    for m in p.mappings:
        seen[m.control] = seen.get(m.control, 0) + 1
        if p.control(m.control) is None:
            yield m.control, "mapping refers to a control that does not exist"
    for c in p.controls:
        n = seen.get(c.id, 0)
        if n == 0:
            yield c.id, "control has no mapping; a gap must be recorded as one"
        elif n > 1:
            yield c.id, f"control has {n} mappings; keep exactly one"


@rule(
    "GOV002",
    "high",
    "A status is backed by the evidence it requires",
    "Implemented needs running code, tests or configuration; partial needs some evidence; designed needs a document.",
)
def _status_evidence(p: Pack, today: date) -> Iterator[tuple[str, str]]:
    for m in p.mappings:
        if m.status not in STATUSES:
            yield m.control, f"unknown status {m.status!r}; use one of {', '.join(STATUSES)}"
            continue
        operating = [e for e in m.evidence if e.kind in OPERATING_KINDS]
        if m.status == "implemented" and not operating:
            yield m.control, "implemented needs at least one code, test or config evidence item"
        if m.status == "partial" and not m.evidence:
            yield m.control, "partial needs at least one evidence item"
        if m.status == "designed" and not m.evidence:
            yield m.control, "designed needs at least one document as evidence"
        if m.status == "designed" and operating:
            yield (
                m.control,
                "designed with running code or tests is understated; use partial or implemented",
            )
        if m.status == "gap" and m.evidence:
            yield m.control, "a gap has no evidence; if something exists, it is not a gap"
        for e in m.evidence:
            if e.kind not in EVIDENCE_KINDS:
                yield m.control, f"evidence {e.key} has unknown kind {e.kind!r}"


@rule(
    "GOV003",
    "high",
    "Anything short of implemented has an owner, a stated limit and a next step",
    "A gap nobody owns stays a gap; a limit left unsaid becomes a false assurance.",
)
def _gaps_owned(p: Pack, today: date) -> Iterator[tuple[str, str]]:
    for m in p.mappings:
        if m.status == "implemented":
            continue
        if len(m.owner.strip()) < 3:
            yield m.control, "needs an owner (a role, not a person's name)"
        if len(m.next_step.strip()) < 20:
            yield m.control, "needs a next step of at least 20 characters"
        if len(m.rationale.strip()) < 40:
            yield m.control, "needs a rationale of at least 40 characters"


@rule(
    "GOV004",
    "critical",
    "Evidence points at a registered repository and a safe relative path",
    "A path outside the evidence repository, or an unregistered repository, cannot be verified.",
)
def _evidence_paths(p: Pack, today: date) -> Iterator[tuple[str, str]]:
    for m, e in p.evidence_items():
        if p.repo(e.repo) is None:
            yield m.control, f"evidence repository {e.repo!r} is not registered in repos.toml"
        if (
            ABSOLUTE_PATH.match(e.path)
            or ".." in e.path.split("/")
            or "\\" in e.path
            or not e.path
            or e.path.endswith("/")
        ):
            yield (
                m.control,
                f"evidence path {e.path!r} must be a relative file path inside the repository",
            )


@rule(
    "GOV005",
    "high",
    "Every evidence file is pinned by hash in the lock file, and the lock has nothing extra",
    "Evidence that can change without anyone noticing is a claim, not evidence.",
)
def _lock_covers(p: Pack, today: date) -> Iterator[tuple[str, str]]:
    keys = {e.key for _, e in p.evidence_items()}
    for k in sorted(keys - set(p.lock.files)):
        yield k, "evidence file is not in evidence.lock.json; run `govpack lock`"
    for k in sorted(set(p.lock.files) - keys):
        yield k, "lock entry is not used by any mapping; run `govpack lock`"


@rule(
    "GOV006",
    "high",
    "Wording does not claim compliance or certification",
    "A mapping shows that evidence exists; whether a system complies is a legal and audit judgement.",
)
def _no_overclaim(p: Pack, today: date) -> Iterator[tuple[str, str]]:
    for c in p.controls:
        for field_name, text in (("title", c.title), ("summary", c.summary)):
            hit = OVERCLAIM.search(text)
            if hit:
                yield c.id, f"control {field_name} claims compliance: {hit.group(0)!r}"
    for m in p.mappings:
        for field_name, text in (
            ("rationale", m.rationale),
            ("limits", m.limits),
            ("next_step", m.next_step),
            *((f"evidence {e.key} shows", e.shows) for e in m.evidence),
        ):
            hit = OVERCLAIM.search(text)
            if hit:
                yield m.control, f"{field_name} claims compliance: {hit.group(0)!r}"
    for s in p.systems:
        for field_name, text in (("summary", s.summary), ("risk_note", s.risk_note)):
            hit = OVERCLAIM.search(text)
            if hit:
                yield s.id, f"system {field_name} claims compliance: {hit.group(0)!r}"


@rule(
    "GOV007",
    "medium",
    "Control IDs are unique, references match the framework, and enumerations are valid",
    "Stable identifiers and valid values keep reports and cross-references trustworthy.",
)
def _control_shape(p: Pack, today: date) -> Iterator[tuple[str, str]]:
    ids: dict[str, int] = {}
    for c in p.controls:
        ids[c.id] = ids.get(c.id, 0) + 1
        fw = p.framework(c.framework)
        if fw and not re.fullmatch(fw.ref_pattern, c.ref):
            yield c.id, f"reference {c.ref!r} does not match {fw.ref_pattern!r} for {fw.name}"
        if c.applies_to not in APPLIES_TO:
            yield c.id, f"applies_to must be one of {', '.join(APPLIES_TO)}"
        if c.kind not in CONTROL_KINDS:
            yield c.id, f"kind must be one of {', '.join(CONTROL_KINDS)}"
        if len(c.summary.strip()) < 40:
            yield c.id, "summary must be at least 40 characters"
        if not ID_FORMAT.fullmatch(c.id):
            yield c.id, "id must look like PREFIX-REF, for example EUAIA-14 or NIST-GV-1.4"
    for cid, n in sorted(ids.items()):
        if n > 1:
            yield cid, f"control id appears {n} times"
    fids: dict[str, int] = {}
    for f in p.frameworks:
        fids[f.id] = fids.get(f.id, 0) + 1
    for fid, n in sorted(fids.items()):
        if n > 1:
            yield fid, f"framework id appears {n} times"


@rule(
    "GOV008",
    "medium",
    "Each mapping was reviewed recently",
    "Repositories change; a mapping nobody has looked at for months is a guess about the present.",
)
def _fresh(p: Pack, today: date) -> Iterator[tuple[str, str]]:
    limit = timedelta(days=p.review_days)
    for m in p.mappings:
        age = today - m.reviewed
        if age > limit:
            yield (
                m.control,
                f"last reviewed {m.reviewed}, {age.days} days ago; limit is {p.review_days}",
            )
        if m.reviewed > today:
            yield m.control, f"review date {m.reviewed} is in the future"
    for f in p.frameworks:
        if today - f.checked > timedelta(days=p.review_days):
            yield (
                f.id,
                f"control list last compared with the source on {f.checked}; limit is {p.review_days} days",
            )


@rule(
    "GOV009",
    "high",
    "A purely organisational control is never marked implemented by repository evidence",
    "Training, policy approval and legal decisions are not things code can demonstrate.",
)
def _org_not_implemented(p: Pack, today: date) -> Iterator[tuple[str, str]]:
    for m in p.mappings:
        c = p.control(m.control)
        if c and c.kind == "organisational" and m.status in ("implemented", "partial"):
            yield (
                m.control,
                f"{c.kind} control cannot be {m.status}; use 'organisational' with supporting evidence",
            )
        if m.status == "organisational" and c and c.kind == "technical":
            yield m.control, "a technical control should be implemented, partial, designed or a gap"


@rule(
    "GOV010",
    "medium",
    "Evidence says what it shows and names the text that proves it",
    "A bare file link tells a reviewer nothing; a checked phrase catches a file that was emptied or rewritten.",
)
def _evidence_quality(p: Pack, today: date) -> Iterator[tuple[str, str]]:
    for m, e in p.evidence_items():
        if len(e.shows.strip()) < 30:
            yield m.control, f"evidence {e.key} needs a 'shows' sentence of at least 30 characters"
        if len(e.contains.strip()) < 6:
            yield m.control, f"evidence {e.key} needs a 'contains' phrase of at least 6 characters"
    for m in p.mappings:
        if m.status in ("implemented", "partial") and len(m.limits.strip()) < 30:
            yield m.control, f"{m.status} needs a 'limits' statement of at least 30 characters"
        seen: set[str] = set()
        for e in m.evidence:
            if e.key in seen:
                yield m.control, f"evidence {e.key} is listed twice"
            seen.add(e.key)


@rule(
    "GOV011",
    "high",
    "Systems refer only to registered repositories and existing controls",
    "A system record that cites something that does not exist undermines the rest of the pack.",
)
def _systems(p: Pack, today: date) -> Iterator[tuple[str, str]]:
    for s in p.systems:
        if not s.components:
            yield s.id, "system lists no components"
        for c in s.components:
            if p.repo(c.repo) is None:
                yield s.id, f"component repository {c.repo!r} is not registered"
        for cid in s.controls:
            if p.control(cid) is None:
                yield s.id, f"control {cid!r} does not exist"
        if len(s.limitations) < 2:
            yield s.id, "a system record lists at least two limitations"


def run(pack: Pack, today: date) -> list[Finding]:
    findings = []
    for r in REGISTRY:
        for subject, message in r.check(pack, today):
            findings.append(Finding(r.id, r.severity, subject, message))
    findings.sort(key=lambda f: (-severity_rank(f.severity), f.rule, f.subject, f.message))
    return findings


def catalog() -> list[tuple[str, str, str, str]]:
    return sorted((r.id, r.severity, r.title, r.why) for r in REGISTRY)
