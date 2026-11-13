# Evidence drift

## Purpose

Respond when `govpack verify` fails: an evidence file changed, moved, lost its justifying text, or a repository could not be fetched.

## Triggers

- The scheduled or manual `Verify evidence` workflow fails.
- Someone runs `govpack verify --repos <dir>` locally and it reports a problem.

## First checks

- Read the kind of each problem: `changed`, `missing-file`, `phrase-missing`, `missing-repo`, `not-locked`.
- `missing-repo` on every line usually means a clone failed, not drift: check the workflow log and the repository URL in `repos.toml`.
- Find the commit in the evidence repository that touched the file (`git log -p -- <path>`).

## Steps

1. **`changed`**: read the diff. If the file still shows what the mapping says it shows, re-pin. If it shows less or something different, change the mapping (status, `limits`, `shows`) first, then re-pin.
2. **`phrase-missing`**: the file no longer contains the text that justified using it. Find where the content went. Update the `contains` phrase only if the same fact is now worded differently; if the fact is gone, remove the evidence item and revisit the status.
3. **`missing-file`**: the file moved or was deleted. Find the new path or choose other evidence. Do not point at a path you have not opened.
4. **`not-locked`**: a mapping was added without pinning. Run `govpack lock`.
5. Re-pin with the repositories checked out side by side: `govpack lock --repos <dir> --date <today>`. The command refuses if a file or phrase is missing.
6. Run `govpack check --fail-on low`, then `govpack report`, and commit the mapping, lock and reports together with a message naming the evidence commit you reviewed.

## Verification

- `govpack verify --repos <dir>` exits 0.
- `govpack report --check` exits 0.
- The pull request description states what changed in the evidence and why the status stands.

## Escalation

If the change weakens a control that appears in the system record, tell the system owner the same day. If evidence has been deleted without explanation, ask the repository owner before changing the mapping.
