# Expert credentials — naming policy

**Version:** 1.0  
**Last updated:** July 2026

---

## Team (current)

| Role | Name | Credential |
|------|------|------------|
| **Finance lead reviewer** | Gaurav Goyal | CFA Level III candidate |
| **Associate** | Gaurav Goyal | CFA Level III candidate |

Charterholder co-signer: **not yet named**. Until then, external materials use **expert-reviewed**, not **CFA-approved**.

---

## When to use which label

| Context | Use | Do not use |
|---------|-----|------------|
| **External** (README, lab deck, leaderboard) | Expert-reviewed · Finance expert (CFA L3 candidate) | CFA-approved · CFA sign-off · Credentialed CFA |
| **Internal** (backlog owner column) | Finance expert | CFA (implies charter) |
| **Review doc headers** | Expert Review | CFA Review (unless charterholder is reviewer) |
| **JSON `review_status`** | `expert_reviewed` | `cfa_approved` (legacy values may remain until migrated) |
| **Workflow diagram nodes** | Finance expert | CFA Expert |
| **Future — after charter + co-signer** | CFA-reviewed (name charterholder) | — |

---

## Why not "CFA L3" everywhere?

- **CFA L3 candidate** belongs on **credential lines** (who reviewed), not as a replacement for every workflow label.
- Backlog **Owner: Finance expert** stays readable; credential lives in this file and review doc sign-off blocks.
- **Level III candidate ≠ charterholder.** Using "CFA" alone in publish gates overstates authority.

---

## Publish gate (honest version)

A task or episode may move to `published` when:

1. Finance expert (named above) completes checklist in `docs/expert_drafts/`.
2. External copy says **expert-reviewed**, with credential footnote if needed.
3. Optional later: charterholder co-review recorded in sign-off table.

---

## Migrating legacy "CFA approved" copy

Historical docs (Jul 2026) used "CFA approved" before this policy. Treat as **expert-reviewed by Gaurav Goyal (CFA L3 candidate)** unless a charterholder co-sign is added retroactively.
