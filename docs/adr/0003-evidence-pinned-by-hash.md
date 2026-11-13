# ADR 0003: Evidence is pinned by hash and by a required phrase

## Status

Accepted

## Context

A link to a file in another repository proves nothing a week later. The file can change, move, or be emptied, and the mapping keeps claiming what the old version showed. Pinning by commit would tie the pack to repositories that change often for unrelated reasons.

## Decision

`evidence.lock.json` records the SHA-256 and size of each evidence file. Each evidence item also names a phrase that must appear in the file. `govpack verify` fails on a changed hash, a missing file, a missing phrase or an unlocked item. `govpack lock` refuses to pin if a file or phrase is missing, so a re-pin cannot paper over a rewrite. Paths and symlinks that leave the checkout are refused.

## Consequences

- Any edit to an evidence file is noticed, including harmless ones. Re-pinning is a deliberate review step with a runbook.
- The phrase check catches a re-pin done without reading.
- Noise is the cost. It is kept low by choosing stable files (decision records, policies, generated registers) rather than source files that change often.
- Hashes are of file bytes, so line-ending conversion would register as drift.
