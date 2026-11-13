# Security policy

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub's
[private vulnerability reporting](https://github.com/darshansatpathy/ai-governance-evidence-pack/security/advisories/new)
for this repository. You should get an acknowledgement within three working days.

## Scope

In scope: the `govpack` tool and the integrity of the evidence lock, in particular anything that lets a mapping point outside its repository, hide drift or overstate a status. Out of scope: the accuracy of the legal and standards summaries (report those as issues), and the evidence repositories themselves.

## Operating it safely

- The pack contains no secrets and reads no credentials. Evidence is public repositories checked out by CI.
- Treat evidence repositories as untrusted input: `govpack verify` only reads files, refuses paths and symlinks that leave the checkout, and never executes anything from them.
- The pack is a mapping aid, not legal advice. Do not use it as a statement to a regulator or customer that a system complies.
- Do not add personal data, customer names, internal hostnames or real incident details to mappings or system records.
