from __future__ import annotations

import re
import shutil
from datetime import date
from pathlib import Path

import pytest

from govpack import pack as packmod

ROOT = Path(__file__).resolve().parent.parent
TODAY = date(2026, 11, 13)
PACK_FILES = ["frameworks", "mappings", "systems", "repos.toml", "pack.toml", "evidence.lock.json"]


class Editor:
    """Edits a copy of the pack as text, then loads it, so each test changes one thing."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def path(self, rel: str) -> Path:
        return self.root / rel

    def read(self, rel: str) -> str:
        return self.path(rel).read_text(encoding="utf-8")

    def write(self, rel: str, text: str) -> None:
        self.path(rel).write_text(text, encoding="utf-8")

    def replace(self, rel: str, old: str, new: str, count: int = 1) -> None:
        text = self.read(rel)
        assert old in text, f"{old!r} not found in {rel}"
        self.write(rel, text.replace(old, new, count))

    def mapping_block(self, control: str) -> tuple[str, str, int, int]:
        """Return (file, block text, start, end) for the [[mapping]] of a control."""
        for f in sorted(self.root.glob("mappings/*.toml")):
            text = f.read_text(encoding="utf-8")
            for m in re.finditer(r"\[\[mapping\]\]\n(?:(?!\n\[\[mapping\]\]).)*", text, re.DOTALL):
                if f'control = "{control}"' in m.group(0):
                    return str(f.relative_to(self.root)), m.group(0), m.start(), m.end()
        raise AssertionError(f"no mapping for {control}")

    def edit_mapping(self, control: str, old: str, new: str) -> None:
        rel, block, start, end = self.mapping_block(control)
        assert old in block, f"{old!r} not in mapping {control}"
        text = self.read(rel)
        self.write(rel, text[:start] + block.replace(old, new, 1) + text[end:])

    def drop_mapping(self, control: str) -> None:
        rel, _, start, end = self.mapping_block(control)
        text = self.read(rel)
        self.write(rel, text[:start] + text[end:])

    def set_line(self, control: str, field: str, value: str) -> None:
        _, block, _, _ = self.mapping_block(control)
        line = next(ln for ln in block.splitlines() if ln.startswith(f"{field} = "))
        self.edit_mapping(control, line, f'{field} = "{value}"')

    def drop_line(self, control: str, field: str) -> None:
        _, block, _, _ = self.mapping_block(control)
        line = next(ln for ln in block.splitlines() if ln.startswith(f"{field} = "))
        self.edit_mapping(control, line + "\n", "")

    def load(self) -> packmod.Pack:
        pack, problems = packmod.load(self.root)
        assert pack is not None and problems == [], problems
        return pack


@pytest.fixture
def edit(tmp_path: Path) -> Editor:
    for name in PACK_FILES:
        src = ROOT / name
        dst = tmp_path / name
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy(src, dst)
    return Editor(tmp_path)


@pytest.fixture(scope="session")
def real_pack() -> packmod.Pack:
    pack, problems = packmod.load(ROOT)
    assert pack is not None and problems == [], problems
    return pack


MINI_FRAMEWORK = """\
[framework]
id = "demo"
name = "Demo framework"
citation = "Demo 1"
source = "https://example.com/demo"
ref_pattern = 'Section \\d+'
checked = 2026-11-01

[[controls]]
id = "DEMO-1"
ref = "Section 1"
title = "Keep a log"
summary = "The system keeps a log of what it does so that events can be traced afterwards."
applies_to = "provider"
kind = "technical"
"""

MINI_MAPPING = """\
framework = "demo"

[[mapping]]
control = "DEMO-1"
status = "implemented"
reviewed = 2026-11-01
rationale = "The demo repository writes a log line for every event it handles."
limits = "Only the demo repository is covered; retention is not configured here."

[[mapping.evidence]]
repo = "demo-repo"
path = "docs/log.md"
kind = "code"
contains = "writes a log line"
shows = "The demo log module records every handled event with a timestamp."
"""

MINI_SYSTEM = """\
[system]
id = "demo-system"
name = "Demo system"
summary = "A small demonstration system used only by the tests."
intended_purpose = "Demonstrate the pack."
provider_role = "Test author."
deployer_role = "Test author."
risk_note = "Not classified."
oversight = "None."
logging = "A log."
data = "None."
limitations = ["Not real.", "Only a test fixture."]
controls = ["DEMO-1"]

[[components]]
repo = "demo-repo"
role = "The only component."
"""


@pytest.fixture
def mini(tmp_path: Path) -> tuple[Path, Path]:
    """A tiny valid pack and a checkout of its one evidence repository: (pack root, repos dir)."""
    root = tmp_path / "pack"
    (root / "frameworks").mkdir(parents=True)
    (root / "mappings").mkdir()
    (root / "systems").mkdir()
    (root / "frameworks" / "demo.toml").write_text(MINI_FRAMEWORK, encoding="utf-8")
    (root / "mappings" / "demo.toml").write_text(MINI_MAPPING, encoding="utf-8")
    (root / "systems" / "demo.toml").write_text(MINI_SYSTEM, encoding="utf-8")
    (root / "repos.toml").write_text(
        '[[repo]]\nname = "demo-repo"\nurl = "https://example.com/demo-repo"\nrole = "Demo."\n',
        encoding="utf-8",
    )
    repos = tmp_path / "repos"
    (repos / "demo-repo" / "docs").mkdir(parents=True)
    (repos / "demo-repo" / "docs" / "log.md").write_text(
        "# Log\nThe module writes a log line for every event.\n", encoding="utf-8"
    )
    return root, repos
