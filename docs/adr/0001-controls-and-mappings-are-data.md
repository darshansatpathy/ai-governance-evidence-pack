# ADR 0001: The control library and the mappings are data, not prose

## Status

Accepted

## Context

Governance mappings usually live in spreadsheets or slide decks. They drift from the code, cannot be reviewed line by line, and cannot be checked by a machine. A reviewer asking "what backs this claim?" gets a link that may no longer say what it said.

## Decision

Frameworks, mappings, repositories and systems are TOML files. A loader reports every problem in one pass. Rules (`GOV001` to `GOV011`) run over the data, and the reports are generated from it. Reports are committed and CI fails if they are stale.

## Consequences

- A change to a claim is a pull request with a diff.
- Every control must be accounted for; omission is a finding, not a silent choice.
- The format is plain enough to be edited by someone who does not write Python, at the cost of a stricter loader than a spreadsheet needs.
- Rich prose lives in `docs/`, not in the data.
