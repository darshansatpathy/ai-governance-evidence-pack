# Regulatory status

Where the three frameworks stood when the control lists were last compared with their sources
(**2026-11-13**). Check the sources before relying on this note; dates and wording in legislation move.

## EU AI Act

Regulation (EU) 2024/1689 entered into force on 1 August 2024. It was amended by the **Digital Omnibus on AI,
Regulation (EU) 2026/1744**, published in the Official Journal on 24 July 2026 and in force from
27 July 2026. As reported by several law-firm and research summaries of the amending regulation:

| Provision | Position |
|---|---|
| Prohibited practices (Article 5) and AI literacy (Article 4) | Applying since 2 February 2025. Article 4 was reworded: a duty to take measures to support AI literacy rather than to ensure a level. |
| General-purpose AI model obligations | Applying since 2 August 2025. Not covered by this pack. |
| Transparency obligations (Article 50) | Applying from 2 August 2026, with a later transition (to 2 December 2026) for marking synthetic content by generative systems already on the market. |
| High-risk systems listed in Annex III | Deferred to 2 December 2027. |
| High-risk systems that are safety components of products in Annex I | Deferred to 2 August 2028. |

Consequences for this pack:

- The mappings for Articles 9 to 15, 17, 26, 72 and 73 describe obligations that apply to **high-risk**
  systems, and from the deferred dates. Whether a given system is high-risk is a legal classification the
  pack does not make; the system record says "not classified".
- **Article 50 already applies.** A customer-facing chat built from these components would need to tell people
  they are talking to an AI system. The mapping is a recorded `gap` (EUAIA-50).
- The Article 4 control (EUAIA-04) was written against the reworded duty.

Primary source: the consolidated text on EUR-Lex (<https://eur-lex.europa.eu/eli/reg/2024/1689/oj>). The
dates above come from secondary summaries and should be checked against the Official Journal text.

## NIST AI RMF

NIST AI 100-1 (AI RMF 1.0, January 2023) is voluntary and organises risk management into Govern, Map,
Measure and Manage. NIST describes the Playbook as neither a checklist nor a set of steps to follow in full,
and has indicated that the framework is being revised. The pack uses 14 subcategories that bear on the
reference systems; it makes no claim to cover the whole Core.

## ISO/IEC 42001

ISO/IEC 42001:2023 is a certifiable AI management system standard. Annex A is a reference set of controls from
which an organisation selects through a Statement of Applicability, so a control listed here is not
automatically required. The pack uses 14 of the 38 Annex A controls, with short descriptive titles that are
not the standard's wording. Buy and read the standard before citing a control number in an audit.

## Keeping this current

`govpack check` fails (rule `GOV008`) when a framework's control list has not been compared with its source for
more than the configured number of days (180 by default). See [the review runbook](runbooks/periodic-review.md).
