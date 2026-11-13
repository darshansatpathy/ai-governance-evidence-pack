"""Command line: check, report, verify, lock, rules."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from govpack import __version__, lock, render, rules
from govpack.pack import Pack, load


def _load(root: Path) -> tuple[Pack | None, list[str]]:
    pack, problems = load(root)
    return pack, problems


def _print_problems(problems: list[str]) -> None:
    for p in problems:
        print(f"error: {p}", file=sys.stderr)


def cmd_check(a: argparse.Namespace) -> int:
    pack, problems = _load(Path(a.root))
    if pack is None or problems:
        _print_problems(problems)
        return 2
    findings = rules.run(pack, date.fromisoformat(a.today))
    if a.format == "markdown":
        print(render.findings_markdown(pack, findings, len(rules.REGISTRY)), end="")
    else:
        for f in findings:
            print(f"{f.severity.upper():8} {f.rule} {f.subject}: {f.message}")
        print(
            f"{len(pack.controls)} controls, {len(pack.mappings)} mappings, "
            f"{len(rules.REGISTRY)} rules: {len(findings)} findings"
        )
    threshold = rules.severity_rank(a.fail_on)
    return 1 if any(rules.severity_rank(f.severity) >= threshold for f in findings) else 0


def cmd_report(a: argparse.Namespace) -> int:
    root = Path(a.root)
    pack, problems = _load(root)
    if pack is None or problems:
        _print_problems(problems)
        return 2
    reports = render.all_reports(pack)
    if a.check:
        stale = [
            rel
            for rel, text in reports.items()
            if not (root / rel).exists() or (root / rel).read_text(encoding="utf-8") != text
        ]
        for rel in stale:
            print(f"stale: {rel}")
        if stale:
            print("run `govpack report` and commit the result")
            return 1
        print(f"{len(reports)} reports are current")
        return 0
    for rel, text in reports.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    print(f"wrote {len(reports)} reports")
    return 0


def cmd_verify(a: argparse.Namespace) -> int:
    pack, problems = _load(Path(a.root))
    if pack is None or problems:
        _print_problems(problems)
        return 2
    drift = lock.check(pack, Path(a.repos))
    for d in drift:
        print(f"{d.kind:14} {d.key}: {d.detail}")
    n = len({e.key for _, e in pack.evidence_items()})
    if drift:
        print(f"{len(drift)} problems in {n} evidence files; see docs/runbooks/evidence-drift.md")
        return 1
    print(f"{n} evidence files match the lock and contain their required text")
    return 0


def cmd_lock(a: argparse.Namespace) -> int:
    root = Path(a.root)
    pack, problems = _load(root)
    # The lock file may be missing or stale while it is being rebuilt; other problems are fatal.
    problems = [p for p in problems if not p.startswith("evidence.lock.json")]
    if pack is None or problems:
        _print_problems(problems)
        return 2
    new, drift = lock.build(pack, Path(a.repos), a.date)
    for d in drift:
        print(f"{d.kind:14} {d.key}: {d.detail}")
    if new is None:
        print("not writing the lock: fix the problems above")
        return 1
    lock.write(new, root / "evidence.lock.json")
    print(f"pinned {len(new.files)} evidence files")
    return 0


def cmd_rules(_: argparse.Namespace) -> int:
    for rid, sev, title, _why in rules.catalog():
        print(f"{rid} {sev:8} {title}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="govpack", description=__doc__)
    p.add_argument("--version", action="version", version=f"govpack {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--root", default=".", help="repository root (default: current directory)")

    check = sub.add_parser("check", help="check the pack against the policy rules (offline)")
    common(check)
    check.add_argument("--fail-on", choices=rules.SEVERITIES, default="high")
    check.add_argument("--format", choices=["text", "markdown"], default="text")
    check.add_argument("--today", default=date.today().isoformat(), help="date for freshness rules")
    check.set_defaults(func=cmd_check)

    rep = sub.add_parser("report", help="write the reports under reports/")
    common(rep)
    rep.add_argument("--check", action="store_true", help="fail if the reports are out of date")
    rep.set_defaults(func=cmd_report)

    ver = sub.add_parser(
        "verify", help="check evidence against checked-out repositories and the lock"
    )
    common(ver)
    ver.add_argument(
        "--repos", required=True, help="directory containing one folder per evidence repository"
    )
    ver.set_defaults(func=cmd_verify)

    lk = sub.add_parser("lock", help="re-pin evidence hashes after a person has re-read the files")
    common(lk)
    lk.add_argument("--repos", required=True)
    lk.add_argument("--date", default=date.today().isoformat(), help="date recorded in the lock")
    lk.set_defaults(func=cmd_lock)

    ru = sub.add_parser("rules", help="list the policy rules")
    ru.set_defaults(func=cmd_rules)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
