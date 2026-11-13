# Method

How a control becomes a mapping, and what each status commits you to.

## The chain

```text
framework  ->  control  ->  mapping  ->  evidence item  ->  file in a repository  ->  pinned hash
(who wrote     (a short     (status,      (what it shows,     (checked out when        (changes are
 the rules)     paraphrase   limits,       the phrase that      verified)                reviewed, not
                of one        owner,        must appear)                                absorbed)
                requirement)  next step)
```

- A **framework** file under `frameworks/` records the source, how references are written, and the date the
  list of controls was last compared with that source.
- A **control** is one requirement, summarised in original words. It says who it applies to
  (`provider`, `deployer` or `both`) and what kind of thing it is (`technical`, `organisational` or `mixed`).
- A **mapping** under `mappings/` gives each control exactly one status and the reasoning.
- **Evidence** is a file in a registered repository, with a sentence on what it shows and a phrase that must
  still be in it. The file is pinned by SHA-256 in `evidence.lock.json`.

## Statuses

| Status | What it commits you to saying | Needs |
|---|---|---|
| `implemented` | A working technical control exists in code, tests or configuration. | At least one code, test or config item; stated `limits` |
| `partial` | Some of what the control asks for exists. | At least one item; stated `limits`; owner and next step |
| `designed` | A design or decision is written down; nothing runs. | At least one document; owner and next step |
| `organisational` | Needs people, policy or a legal decision. Supporting evidence may be listed. | Owner and next step |
| `gap` | Applicable, and nothing here addresses it. | Owner and next step; no evidence |

Two guards keep statuses honest. A control whose kind is `organisational` can never be `implemented` or
`partial`, because code cannot show that people were trained or a policy was approved. A `designed`
control with running code or tests is flagged as understated, so a status can be too modest as well as too
generous.

`implemented` never means "the requirement is met". It means a technical control of the described kind
exists in the reference code and is tested there, and `limits` says what that does not cover. Whether a
system meets a legal requirement depends on its purpose, its context and a judgement this pack does not make.

## Evidence

An evidence item is only as good as the sentence beside it. Each one has:

- `shows`: what a reviewer will find in the file, in at least one full sentence.
- `contains`: text that must be present. If someone empties the file, renames the thing it describes or
  rewrites it, verification fails even if a person re-pins the hash without reading.
- `kind`: `code`, `test`, `config` or `doc`. Only the first three count as something running.

The pin is deliberately strict. Any change to a pinned file makes `govpack verify` fail. A person reads the
change, decides whether the mapping is still true, edits the mapping if not, and re-pins. See
[the drift runbook](runbooks/evidence-drift.md).

## What the pack does not do

- It does not decide whether a system is high-risk, which obligations apply, or whether it complies.
- It does not read the evidence for meaning. It checks that the file exists, is unchanged and still
  contains the phrase; whether the file supports the claim is a human judgement made at review.
- It does not cover obligations outside the three frameworks (for example data protection law, sector rules
  or the general-purpose AI model chapter).
- Control summaries are paraphrases written for this pack. Cite the regulation or the standard itself, not
  these summaries.

## Adding to the pack

1. New control: add it to the framework file, then give it a mapping. The rules refuse a control without one.
2. New evidence: add the repository to `repos.toml` if it is new, add the item with `shows` and
   `contains`, check out the repository beside the others and run `govpack lock --repos <dir>`.
3. New framework: add `frameworks/<id>.toml` and `mappings/<id>.toml`. Reports pick it up without changes.
4. Run `govpack check --fail-on low` and `govpack report`, and commit the generated reports.
