# ADR 0004: Rules run offline; verification runs against checkouts on a schedule

## Status

Accepted

## Context

Pull requests to this repository should not depend on nine other repositories being reachable, and should not fail because an unrelated repository changed. But drift must still be noticed.

## Decision

`govpack check` and `govpack report --check` need only this repository and run on every pull request. `govpack verify` needs the evidence repositories checked out and runs weekly, on manual dispatch, and when mappings or the lock change. Review freshness (`GOV008`, medium severity) is enforced only by the scheduled run, so an aged pack does not block unrelated changes.

## Consequences

- Pull requests are fast and deterministic.
- Drift is found within a week rather than at the next audit.
- A failing scheduled run is the signal to follow the drift runbook; nothing is auto-fixed.
- The scheduled run clones default branches, so it reflects what is published, not what is local.
