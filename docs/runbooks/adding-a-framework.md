# Adding a framework or a system

## Purpose

Extend the pack without weakening it.

## Triggers

- A new standard or regulation becomes relevant.
- A new AI system needs a record.

## First checks

- Is there a stable public source and a way to reference individual requirements?
- For a system: which repositories make it up, and are they in `repos.toml`?

## Steps

1. Framework: create `frameworks/<id>.toml` with `[framework]` metadata (`ref_pattern` is a regular expression for references) and `[[controls]]`. Write summaries in your own words.
2. Create `mappings/<id>.toml` with one `[[mapping]]` per control. Start from `gap` or `organisational` and move up only on evidence.
3. System: create `systems/<id>.toml` with components, limitations (at least two) and the controls that apply.
4. Add new repositories to `repos.toml`, check them out beside the others, and run `govpack lock --repos <dir>`.
5. Run `govpack check --fail-on low` and `govpack report`.

## Verification

- Rules pass with no findings.
- A new test covers any new rule, with a failing case.

## Escalation

Ask whether the framework's licence permits summarising its requirements. Do not paste text from standards that are sold.
