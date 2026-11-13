# Periodic review

## Purpose

Keep mappings and control lists current. Rule `GOV008` fails when a mapping has not been reviewed, or a control list has not been compared with its source, within the configured interval (180 days by default).

## Triggers

- The scheduled workflow reports `GOV008`.
- A framework publishes a new version, or a regulator changes dates (see [regulatory status](../regulatory-status.md)).
- A system in the system record changes purpose, model, data or deployment.

## First checks

- Which mappings and frameworks does `govpack check --fail-on low` name?
- Have the evidence repositories changed meaningfully since the last review (`govpack verify`)?

## Steps

1. For each framework named: compare the control list with the current source. Add, remove or reword controls; update `checked` in the framework file and the `note` if dates changed.
2. For each mapping named: open each evidence file, confirm it still shows what `shows` says, and re-read `limits` and `next_step`. Move the status only on evidence, in either direction.
3. Close out `next_step` items that were done: attach the new evidence and raise the status, or record why not.
4. Set `reviewed` to the review date for every mapping you actually reviewed. Do not bulk-update dates.
5. Run `govpack lock` if evidence changed, then `govpack check --fail-on low` and `govpack report`.

## Verification

- `govpack check --fail-on low` reports no findings.
- The gap register has an owner and a next step for every row, and the owners agree.

## Escalation

If a mapping cannot be reviewed because nobody owns the evidence, record that as the next step and change the status to reflect what can be shown.
