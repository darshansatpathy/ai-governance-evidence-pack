# ADR 0002: Statuses are conservative and checked against the kind of control

## Status

Accepted

## Context

A coverage report that shows mostly green is persuasive and, for a set of reference repositories, wrong. Code can show that a technical control exists; it cannot show that people were trained or that a policy was approved. Equally, a control that is merely documented should not be reported as running.

## Decision

Five statuses (`implemented`, `partial`, `designed`, `organisational`, `gap`), each with required evidence and required explanation (`GOV002`, `GOV003`, `GOV010`). A purely organisational control can never be `implemented` or `partial` (`GOV009`). A `designed` control that has running evidence is flagged as understated. `implemented` carries a mandatory `limits` statement.

## Consequences

- The shipped pack reports 6 of 41 controls as implemented and 1 as a plain gap. That is the point.
- Authors cannot raise a status without writing down what is still missing.
- Some reviewers will find the bar high. The alternative is a report nobody can rely on.
