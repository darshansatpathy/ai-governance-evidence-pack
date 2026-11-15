# AI governance evidence pack

[![CI](https://github.com/darshansatpathy/ai-governance-evidence-pack/actions/workflows/ci.yml/badge.svg)](https://github.com/darshansatpathy/ai-governance-evidence-pack/actions/workflows/ci.yml)
[![Verify evidence](https://github.com/darshansatpathy/ai-governance-evidence-pack/actions/workflows/verify-evidence.yml/badge.svg)](https://github.com/darshansatpathy/ai-governance-evidence-pack/actions/workflows/verify-evidence.yml)
[![CodeQL](https://github.com/darshansatpathy/ai-governance-evidence-pack/actions/workflows/codeql.yml/badge.svg)](https://github.com/darshansatpathy/ai-governance-evidence-pack/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Governance reports usually say what a team intends. This one says what a reviewer can open. It takes **41
controls** from the EU AI Act, the NIST AI RMF and ISO/IEC 42001, maps each to evidence in nine real
repositories, pins every evidence file by hash, and checks weekly that the files still say what the mapping
claims. Where nothing exists, it says so, with an owner and a next step.

> A mapping aid for engineers, architects and auditors. It is not legal advice, not a conformity assessment,
> and not a statement that any system complies with anything. A rule in the build rejects wording that says
> otherwise.

## Where the reference systems stand

| Framework | Controls | implemented | partial | designed | organisational | gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| EU AI Act | 13 | 2 | 6 | 0 | 4 | 1 |
| ISO/IEC 42001:2023 | 14 | 2 | 6 | 1 | 5 | 0 |
| NIST AI RMF 1.0 | 14 | 2 | 10 | 1 | 1 | 0 |
| **All** | **41** | **6** | **22** | **2** | **10** | **1** |

Only 6 of 41 controls are `implemented`, and each of those says what it still does not cover. The honest
reading of the rest:

- **Technical controls for the agent boundary are strong:** human approval of writes, tamper-evident logs,
  budgets, an evaluation gate, an attack corpus in CI, private keyless infrastructure, personal-data masking.
- **Almost everything else needs people.** Ten controls (AI literacy, quality management, impact
  assessment, incident communication, a policy) cannot be shown by a repository at all.
- **One plain gap:** nothing here tells an end user they are talking to an AI system (EU AI Act Article 50),
  which already applies. See [regulatory status](docs/regulatory-status.md).
- Full lists: [coverage](reports/coverage.md), [gap register](reports/gap-register.md).

## What is in it

| | |
|---|---|
| [`frameworks/`](frameworks) | Control lists: reference, short title, who it applies to, a summary in original words, and the date it was last compared with its source |
| [`mappings/`](mappings) | One mapping per control: status, rationale, limits, owner, next step, review date and evidence |
| [`repos.toml`](repos.toml) | The nine repositories that hold evidence |
| [`evidence.lock.json`](evidence.lock.json) | SHA-256 of each of the 50 evidence files |
| [`systems/`](systems) | An AI system record for the reference customer-support agent |
| [`reports/`](reports) | Generated: [coverage](reports/coverage.md), [gap register](reports/gap-register.md), [evidence index](reports/evidence-index.md), [crosswalk](reports/crosswalk.md), [system record](reports/system-record.md), [policy rules](reports/policy-rules.md) |
| [`src/govpack/`](src/govpack) | The `govpack` tool (standard library only) |

The evidence comes from these repositories:
[`claude-agent-reference`](https://github.com/darshansatpathy/claude-agent-reference),
[`agent-guardrails-gateway`](https://github.com/darshansatpathy/agent-guardrails-gateway),
[`human-in-the-loop-inbox`](https://github.com/darshansatpathy/human-in-the-loop-inbox),
[`agent-eval-harness`](https://github.com/darshansatpathy/agent-eval-harness),
[`agent-tracing-otel`](https://github.com/darshansatpathy/agent-tracing-otel),
[`governed-data-agents`](https://github.com/darshansatpathy/governed-data-agents),
[`databricks-medallion-lakehouse`](https://github.com/darshansatpathy/databricks-medallion-lakehouse),
[`azure-ai-landing-zone`](https://github.com/darshansatpathy/azure-ai-landing-zone) and
[`ai-platform-reference-architecture`](https://github.com/darshansatpathy/ai-platform-reference-architecture).

## A mapping

```toml
[[mapping]]
control = "EUAIA-14"            # Article 14, human oversight
status = "implemented"
reviewed = 2026-11-13
rationale = "Writes need approval by default across the agent harness and the gateway; the approval service binds an approval to the exact arguments, ..."
limits = "A rubber-stamp approver defeats the control. Nothing here addresses automation bias, training or competence of overseers (Article 14(4)), ..."

[[mapping.evidence]]
repo = "claude-agent-reference"
path = "evals/scenarios/08-injection-in-document-cannot-refund.json"
kind = "test"
contains = "injection-in-document-cannot-refund"
shows = "A scripted model obeys hostile text in a document and asks for a refund; the scenario asserts that no refund happens."
```

An `implemented` mapping needs running evidence (code, test or configuration) and a stated limit. A control
that is about people can never be `implemented`. The reasoning is in the [method note](docs/method.md).

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

govpack check                       # run the policy rules over the pack (offline)
govpack report                      # regenerate reports/
govpack report --check              # fail if the committed reports are out of date
govpack verify --repos ../evidence  # check evidence files against the lock and their required text
govpack lock --repos ../evidence    # re-pin after a person has read the changes
govpack rules                       # list the policy rules
make check                          # ruff, mypy --strict, pytest with an 85% coverage gate
```

`govpack verify` expects a directory with one folder per repository in [`repos.toml`](repos.toml). The
[weekly workflow](.github/workflows/verify-evidence.yml) clones them and runs it. A run looks like this:

```text
$ govpack check
41 controls, 41 mappings, 11 rules: 0 findings
$ govpack verify --repos ../evidence
50 evidence files match the lock and contain their required text
$ govpack report
wrote 6 reports
```

## Policy rules

`govpack check` runs eleven rules over the pack. Each has a failing-case test, and a test asserts none is left
untested. The full table is in [reports/policy-rules.md](reports/policy-rules.md).

| Rule | Severity | Requirement |
|---|---|---|
| `GOV001` | critical | Every control has exactly one mapping, and every mapping names a control |
| `GOV002` | high | A status is backed by the evidence it requires |
| `GOV003` | high | Anything short of implemented has an owner, a stated limit and a next step |
| `GOV004` | critical | Evidence points at a registered repository and a safe relative path |
| `GOV005` | high | Every evidence file is pinned by hash in the lock file, and the lock has nothing extra |
| `GOV006` | high | Wording does not claim compliance or certification |
| `GOV007` | medium | Control IDs are unique, references match the framework, and enumerations are valid |
| `GOV008` | medium | Each mapping was reviewed recently |
| `GOV009` | high | A purely organisational control is never marked implemented by repository evidence |
| `GOV010` | medium | Evidence says what it shows and names the text that proves it |
| `GOV011` | high | Systems refer only to registered repositories and existing controls |

## Design decisions

1. [Controls and mappings are data](docs/adr/0001-controls-and-mappings-are-data.md)
2. [Statuses are conservative](docs/adr/0002-conservative-statuses.md)
3. [Evidence is pinned by hash and a required phrase](docs/adr/0003-evidence-pinned-by-hash.md)
4. [Rules run offline; verification runs on a schedule](docs/adr/0004-offline-rules-online-verification.md)
5. [A mapping aid, with wording guarded by a rule](docs/adr/0005-mapping-aid-not-legal-advice.md)

Also: [method](docs/method.md), [regulatory status](docs/regulatory-status.md), and runbooks for
[evidence drift](docs/runbooks/evidence-drift.md), [periodic review](docs/runbooks/periodic-review.md) and
[adding a framework or system](docs/runbooks/adding-a-framework.md).

## What has and has not been verified

**Verified by the test suite and CI**

- Every policy rule fires on a broken copy of the pack, and the shipped pack passes all of them.
- Every evidence file existed, matched its pinned hash and contained its required phrase when the lock was
  written (`govpack verify` against fresh checkouts of the nine repositories).
- The lock rejects paths and symlinks that leave a checkout, and refuses to pin a file that lacks its phrase.
- Reports are regenerated in CI and fail the build if stale; counts in this README are asserted against them.
- Code is linted, formatted, type-checked in strict mode and tested on Python 3.11 to 3.13 with an 85%
  coverage gate; the wheel is built and run from a clean environment; CodeQL and `pip-audit` run.

**Not verified, and not claimed**

- **Whether the evidence supports the claim is a human judgement.** The tool checks that a file exists, is
  unchanged and still contains a phrase. The `shows` sentences and statuses were written by the author with
  AI assistance and have not had independent review; nothing checks that a sentence is right.
- **The evidence repositories are reference implementations.** None runs in production. The Spark SQL in the
  lakehouse repository, for instance, has not been run on Databricks.
- **No system is classified.** Whether any system is high-risk under the AI Act, which obligations apply to
  whom, and whether any requirement is met are legal judgements this pack does not make.
- **The control lists are partial and paraphrased.** 13 of the AI Act's articles, 14 NIST subcategories and
  14 of ISO 42001's 38 Annex A controls. Summaries are not the legal or standard text, and ISO control titles
  are descriptive, not the standard's wording. Cite the sources.
- **Dates and legislative status come from secondary summaries** and the author's reading; check
  EUR-Lex. See [regulatory status](docs/regulatory-status.md).
- **The weekly verification workflow has not run yet** at the time of writing; the first run is the
  first test of cloning the repositories in CI.
- Written and tested by an AI assistant (Claude) working with the repository owner; the design has not had an independent review.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). Do not add personal data, customer
names or real incident details to mappings or system records.

## Licence

MIT. See [LICENSE](LICENSE).
