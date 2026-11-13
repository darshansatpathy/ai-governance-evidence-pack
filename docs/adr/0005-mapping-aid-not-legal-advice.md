# ADR 0005: The pack is a mapping aid, with wording guarded by a rule

## Status

Accepted

## Context

Pages that say a system "complies" with the AI Act or "is ISO 42001 compliant" are common and risky. Compliance is a legal and audit judgement that depends on the system's purpose, context and the organisation running it. Reference repositories belong to no deployed system.

## Decision

The pack records which controls have checked evidence and where the gaps are. Rule `GOV006` rejects wording that claims compliance, conformity or certification in controls, mappings and system records. Control summaries are paraphrases, not quotations, and every report opens with a notice saying so. The system record says "not classified" for risk.

## Consequences

- The pack is useful to engineers, architects and auditors as a starting point and cannot be mistaken for an attestation.
- A reader who wants a compliance statement must get one from the right people.
- The wording rule is a blunt regular expression; a determined author can evade it. It protects against accidents, not bad faith.
