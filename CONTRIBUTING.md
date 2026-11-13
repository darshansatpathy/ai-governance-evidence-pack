# Contributing

Thanks for taking the time to improve this project.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
make check          # ruff, mypy --strict, pytest with 85% coverage gate
make verify         # policy rules and report freshness (offline)
```

## What a change needs

- Change `frameworks/`, `mappings/`, `systems/` or `repos.toml`, never `reports/`. Run `govpack report` and commit the result; CI fails if they differ.
- A status is conservative. Move a control up only with evidence a reviewer can open; say what is still missing in `limits`. Never move it up because a deadline is near.
- Write control summaries in your own words. Do not paste text from the regulation or the standards.
- When evidence changes in another repository, read the change, then run `govpack lock` to re-pin. Re-pinning is a review, not a refresh.
- No wording that claims compliance, certification or conformity (rule `GOV006`).
- A control the pack cannot address is `organisational` or `gap` with an owner and a next step, never left out.
- A new rule has an ID, a severity, a reason and a failing-case test.
- Decisions that change how statuses or evidence work get an ADR in `docs/adr/`.
- Update `CHANGELOG.md` for anything a user would notice.

## Pull requests

Keep them focused, describe the behaviour change and how you tested it, and make sure
CI is green. Security issues go through private reporting, see [SECURITY.md](SECURITY.md).
