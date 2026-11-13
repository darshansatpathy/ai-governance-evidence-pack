"""Every rule has a failing case. A test at the end asserts no rule is left untested."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date

import pytest

from govpack import pack as packmod
from govpack import rules

from .conftest import TODAY, Editor

fired: set[str] = set()


def as_documents(e: Editor, control: str) -> None:
    """Turn every evidence item of a mapping into a document, so no running evidence remains."""
    rel, block, start, end = e.mapping_block(control)
    text = e.read(rel)
    block = re.sub(r'kind = "(?:code|test|config)"', 'kind = "doc"', block)
    e.write(rel, text[:start] + block + text[end:])


def one_limitation(e: Editor) -> None:
    text = e.read("systems/support-agent.toml")
    e.write(
        "systems/support-agent.toml",
        re.sub(r"limitations = \[.*?\]\n", 'limitations = ["only one"]\n', text, flags=re.DOTALL),
    )


def findings(edit: Editor, today: date = TODAY) -> list[rules.Finding]:
    return rules.run(edit.load(), today)


def only(fs: list[rules.Finding], rule_id: str) -> list[rules.Finding]:
    return [f for f in fs if f.rule == rule_id]


def test_the_shipped_pack_has_no_findings(real_pack):
    assert rules.run(real_pack, TODAY) == []


def test_findings_are_sorted_most_severe_first(edit: Editor):
    edit.drop_mapping("EUAIA-09")  # critical
    edit.edit_mapping("EUAIA-50", "reviewed = 2026-11-13", "reviewed = 2025-01-01")  # medium
    fs = findings(edit)
    ranks = [rules.severity_rank(f.severity) for f in fs]
    assert ranks == sorted(ranks, reverse=True) and fs[0].severity == "critical"


# (case id, rule, mutation, expected message fragment)
Mutation = Callable[[Editor], None]
CASES: list[tuple[str, str, Mutation, str]] = [
    ("missing-mapping", "GOV001", lambda e: e.drop_mapping("EUAIA-09"), "has no mapping"),
    (
        "mapping-for-unknown-control",
        "GOV001",
        lambda e: e.edit_mapping("EUAIA-09", 'control = "EUAIA-09"', 'control = "EUAIA-99"'),
        "does not exist",
    ),
    (
        "duplicate-mapping",
        "GOV001",
        lambda e: e.write(
            "mappings/eu-ai-act.toml",
            e.read("mappings/eu-ai-act.toml") + e.mapping_block("EUAIA-04")[1],
        ),
        "2 mappings",
    ),
    (
        "unknown-status",
        "GOV002",
        lambda e: e.edit_mapping("EUAIA-04", 'status = "organisational"', 'status = "done"'),
        "unknown status",
    ),
    (
        "implemented-without-running-evidence",
        "GOV002",
        lambda e: as_documents(e, "EUAIA-12"),
        "implemented needs",
    ),
    (
        "partial-without-evidence",
        "GOV002",
        lambda e: e.edit_mapping("EUAIA-04", 'status = "organisational"', 'status = "partial"'),
        "partial needs",
    ),
    (
        "designed-without-evidence",
        "GOV002",
        lambda e: e.edit_mapping("EUAIA-04", 'status = "organisational"', 'status = "designed"'),
        "designed needs",
    ),
    (
        "designed-but-has-running-code",
        "GOV002",
        lambda e: e.edit_mapping("ISO42001-A.10.3", 'kind = "doc"', 'kind = "config"'),
        "understated",
    ),
    (
        "gap-with-evidence",
        "GOV002",
        lambda e: e.edit_mapping("EUAIA-09", 'status = "partial"', 'status = "gap"'),
        "a gap has no evidence",
    ),
    (
        "unknown-evidence-kind",
        "GOV002",
        lambda e: e.edit_mapping("EUAIA-09", 'kind = "doc"', 'kind = "video"'),
        "unknown kind",
    ),
    (
        "missing-owner",
        "GOV003",
        lambda e: e.drop_line("EUAIA-50", "owner"),
        "needs an owner",
    ),
    (
        "missing-next-step",
        "GOV003",
        lambda e: e.drop_line("EUAIA-50", "next_step"),
        "next step",
    ),
    (
        "thin-rationale",
        "GOV003",
        lambda e: e.set_line("EUAIA-50", "rationale", "Nothing here."),
        "rationale",
    ),
    (
        "unregistered-repo",
        "GOV004",
        lambda e: e.edit_mapping(
            "EUAIA-09", 'repo = "ai-platform-reference-architecture"', 'repo = "other-repo"'
        ),
        "not registered",
    ),
    (
        "path-traversal",
        "GOV004",
        lambda e: e.edit_mapping(
            "EUAIA-09", 'path = "docs/risk-register.md"', 'path = "../secrets.md"'
        ),
        "relative file path",
    ),
    (
        "absolute-path",
        "GOV004",
        lambda e: e.edit_mapping(
            "EUAIA-09", 'path = "docs/risk-register.md"', 'path = "/etc/passwd"'
        ),
        "relative file path",
    ),
    (
        "directory-path",
        "GOV004",
        lambda e: e.edit_mapping("EUAIA-09", 'path = "docs/risk-register.md"', 'path = "docs/"'),
        "relative file path",
    ),
    (
        "backslash-path",
        "GOV004",
        lambda e: e.edit_mapping(
            "EUAIA-09", 'path = "docs/risk-register.md"', 'path = "docs\\\\risk.md"'
        ),
        "relative file path",
    ),
    (
        "evidence-not-locked",
        "GOV005",
        lambda e: e.edit_mapping(
            "EUAIA-09", 'path = "docs/risk-register.md"', 'path = "docs/other.md"'
        ),
        "not in evidence.lock.json",
    ),
    (
        "orphan-lock-entry",
        "GOV005",
        lambda e: e.write(
            "evidence.lock.json",
            e.read("evidence.lock.json").replace(
                '"files": {', '"files": {\n    "demo:orphan.md": {"sha256": "00", "size": 1},', 1
            ),
        ),
        "not used by any mapping",
    ),
    (
        "overclaim-in-rationale",
        "GOV006",
        lambda e: e.edit_mapping(
            "EUAIA-09",
            "Risks are identified",
            "The system is fully compliant. Risks are identified",
        ),
        "claims compliance",
    ),
    (
        "overclaim-in-control-summary",
        "GOV006",
        lambda e: e.replace(
            "frameworks/eu-ai-act.toml",
            "Providers run a documented",
            "Certified providers run a documented",
        ),
        "claims compliance",
    ),
    (
        "overclaim-in-system",
        "GOV006",
        lambda e: e.replace(
            "systems/support-agent.toml",
            "It is a reference design",
            "It guarantees compliance. It is a reference design",
        ),
        "claims compliance",
    ),
    (
        "reference-does-not-match",
        "GOV007",
        lambda e: e.replace("frameworks/eu-ai-act.toml", 'ref = "Article 14"', 'ref = "Art. 14"'),
        "does not match",
    ),
    (
        "duplicate-control-id",
        "GOV007",
        lambda e: e.replace("frameworks/eu-ai-act.toml", 'id = "EUAIA-15"', 'id = "EUAIA-14"'),
        "appears 2 times",
    ),
    (
        "bad-applies-to",
        "GOV007",
        lambda e: e.replace(
            "frameworks/eu-ai-act.toml", 'applies_to = "deployer"', 'applies_to = "everyone"'
        ),
        "applies_to",
    ),
    (
        "bad-kind",
        "GOV007",
        lambda e: e.replace("frameworks/eu-ai-act.toml", 'kind = "technical"', 'kind = "magic"'),
        "kind must be",
    ),
    (
        "short-summary",
        "GOV007",
        lambda e: e.replace(
            "frameworks/eu-ai-act.toml",
            'summary = "Providers and deployers take measures to support the AI literacy of the people who operate or use AI systems on their behalf, in proportion to their role and context."',
            'summary = "Short."',
        ),
        "at least 40",
    ),
    (
        "bad-control-id",
        "GOV007",
        lambda e: e.replace("frameworks/eu-ai-act.toml", 'id = "EUAIA-04"', 'id = "euaia_04"'),
        "id must look like",
    ),
    (
        "duplicate-framework-id",
        "GOV007",
        lambda e: e.replace(
            "frameworks/nist-ai-rmf.toml", 'id = "nist-ai-rmf"', 'id = "iso-42001"'
        ),
        "framework id appears 2 times",
    ),
    (
        "stale-mapping",
        "GOV008",
        lambda e: e.edit_mapping("EUAIA-04", "reviewed = 2026-11-13", "reviewed = 2025-01-01"),
        "days ago",
    ),
    (
        "future-review-date",
        "GOV008",
        lambda e: e.edit_mapping("EUAIA-04", "reviewed = 2026-11-13", "reviewed = 2027-01-01"),
        "in the future",
    ),
    (
        "stale-framework-list",
        "GOV008",
        lambda e: e.replace(
            "frameworks/iso-42001.toml", "checked = 2026-11-13", "checked = 2025-01-01"
        ),
        "control list last compared",
    ),
    (
        "organisational-control-marked-partial",
        "GOV009",
        lambda e: e.edit_mapping("EUAIA-17", 'status = "organisational"', 'status = "partial"'),
        "cannot be partial",
    ),
    (
        "technical-control-marked-organisational",
        "GOV009",
        lambda e: e.edit_mapping("EUAIA-12", 'status = "implemented"', 'status = "organisational"'),
        "technical control",
    ),
    (
        "short-shows",
        "GOV010",
        lambda e: e.edit_mapping(
            "EUAIA-09",
            'shows = "A risk register with likelihood, impact, mitigations tied to ADRs and components, early indicators and an owning team."',
            'shows = "A register."',
        ),
        "'shows' sentence",
    ),
    (
        "short-contains",
        "GOV010",
        lambda e: e.edit_mapping(
            "EUAIA-09", 'contains = "Prompt injection causes a harmful action"', 'contains = "R2"'
        ),
        "'contains' phrase",
    ),
    (
        "implemented-without-limits",
        "GOV010",
        lambda e: e.drop_line("EUAIA-12", "limits"),
        "'limits' statement",
    ),
    (
        "duplicate-evidence",
        "GOV010",
        lambda e: e.write(
            "mappings/eu-ai-act.toml",
            e.read("mappings/eu-ai-act.toml").replace(
                '[[mapping.evidence]]\nrepo = "ai-platform-reference-architecture"\npath = "docs/risk-register.md"',
                '[[mapping.evidence]]\nrepo = "ai-platform-reference-architecture"\npath = "docs/risk-register.md"\nkind = "doc"\ncontains = "Prompt injection causes a harmful action"\nshows = "Duplicate entry for the same file in one mapping."\n\n[[mapping.evidence]]\nrepo = "ai-platform-reference-architecture"\npath = "docs/risk-register.md"',
                1,
            ),
        ),
        "listed twice",
    ),
    (
        "system-unknown-repo",
        "GOV011",
        lambda e: e.replace(
            "systems/support-agent.toml", 'repo = "azure-ai-landing-zone"', 'repo = "ghost"'
        ),
        "not registered",
    ),
    (
        "system-unknown-control",
        "GOV011",
        lambda e: e.replace("systems/support-agent.toml", '"EUAIA-12",', '"EUAIA-99",'),
        "does not exist",
    ),
    (
        "system-without-components",
        "GOV011",
        lambda e: e.write(
            "systems/support-agent.toml",
            e.read("systems/support-agent.toml").split("[[components]]")[0],
        ),
        "no components",
    ),
    ("system-with-one-limitation", "GOV011", one_limitation, "at least two limitations"),
]


@pytest.mark.parametrize(
    ("name", "rule_id", "mutate", "fragment"), CASES, ids=[c[0] for c in CASES]
)
def test_rule_fires_on_a_broken_pack(edit: Editor, name, rule_id, mutate, fragment):
    mutate(edit)
    pack, _ = packmod.load(edit.root)
    assert pack is not None
    hits = only(rules.run(pack, TODAY), rule_id)
    assert hits, f"{rule_id} did not fire for {name}"
    assert any(fragment in h.message for h in hits), [h.message for h in hits]
    fired.add(rule_id)


def test_every_rule_is_exercised():
    # Runs after the parametrised cases in file order.
    assert fired == {r.id for r in rules.REGISTRY}


def test_catalog_lists_every_rule_with_a_reason():
    cat = rules.catalog()
    assert [c[0] for c in cat] == [f"GOV{n:03d}" for n in range(1, len(cat) + 1)]
    assert all(c[1] in rules.SEVERITIES and c[2] and len(c[3]) > 20 for c in cat)


def test_review_age_boundary_is_exactly_the_configured_limit(edit: Editor):
    # 180 days before TODAY is acceptable; 181 is not
    edit.edit_mapping("EUAIA-04", "reviewed = 2026-11-13", "reviewed = 2026-05-17")
    assert not only(findings(edit), "GOV008")
    edit.edit_mapping("EUAIA-04", "reviewed = 2026-05-17", "reviewed = 2026-05-16")
    hits = only(findings(edit), "GOV008")
    assert len(hits) == 1 and "181 days" in hits[0].message


def test_the_review_limit_comes_from_pack_settings(edit: Editor):
    edit.write("pack.toml", "review_days = 30\n")
    assert not only(findings(edit, date(2026, 12, 13)), "GOV008")  # exactly 30 days
    late = only(findings(edit, date(2026, 12, 14)), "GOV008")  # 31 days
    assert len(late) >= 41  # every mapping, and the three control lists
