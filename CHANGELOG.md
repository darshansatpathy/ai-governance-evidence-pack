# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-13

### Added
- Control library for the EU AI Act (13 articles), NIST AI RMF 1.0 (14 subcategories) and ISO/IEC 42001 Annex A (14 controls), summarised in original wording.
- Mappings of all 41 controls to evidence in nine repositories, with conservative statuses, stated limits, owners and next steps.
- Hash-pinned evidence (`evidence.lock.json`) and `govpack verify`, which also checks that each file still contains the text that justifies its use.
- Eleven policy rules (GOV001 to GOV011) over the pack, including a rule against claiming compliance.
- Generated coverage, gap register, evidence index, crosswalk and AI system record.
- Five ADRs, three runbooks, a regulatory status note and a method note.

[0.1.0]: https://github.com/darshansatpathy/ai-governance-evidence-pack/releases/tag/v0.1.0
