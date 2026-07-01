# AlphaNote-Bench: Dual-Control RL Environment Spec v1

> **Repo context:** [ARCHITECTURE.md](../../docs/ARCHITECTURE.md) · **CFA review:** [SOLARIS_GOLD_KEY_REVIEW.md](../../docs/expert_drafts/SOLARIS_GOLD_KEY_REVIEW.md) · **Implementation:** `env_v1/scripts/`

**Scenario:** Earnings quality adjustment dispute. Analyst must classify a one-time item, defend the call to a simulated portfolio manager who pushes back, and arrive at a final adjusted EPS and recommendation. First of three candidate scenarios — traceable ground truth plus genuine defense under pressure.

---

## 1. Architecture overview

```mermaid
flowchart TD
    A[Episode init: load filing, transcript, consensus data into tool backend] --> B[Agent turn: tool calls to retrieve data]
    B --> C[Agent turn: send_message_to_pm with initial brief]
    C --> D[PM simulator turn: generates pushback, conditioned on ground truth + persona]
    D --> E{Agent response}
    E -->|re-query tools| B
    E -->|defend or revise position| C
    E -->|call submit_recommendation| F[Episode terminates]
    F --> G[Deterministic outcome checker]
    F --> H[LLM-judge rubric scorer]
    F --> I[Grounding / hallucination checker]
    G --> J[Composite reward]
    H --> J
    I --> J
    J --> K[Expert adjudication sample, 10-20% of episodes]
```

The loop has two participants with separate policies: the agent under test (the analyst) and a PM simulator (a second LLM call, not the same model being evaluated, conditioned on a ground-truth answer key and a persona script). Everything the agent retrieves comes from a fixed, versioned document set, not live web access, so episodes are reproducible and the gold key can't drift.

---

## 2. Data substrate: where the agent gets raw data

No external retrieval. Each episode loads a fixed bundle into a mock tool backend:

| Document | Content | Source of truth |
|---|---|---|
| 10-Q excerpt | MD&A section, non-GAAP reconciliation table, footnotes on asset sale and R&D credit | Authored by expert annotator, modeled on real disclosure conventions, fictional company |
| Earnings call transcript | CFO remarks on the quarter, Q&A exchange where an analyst asks about the lease transaction | Authored alongside the filing for consistency |
| Consensus estimates | Sell-side consensus EPS and revenue, plus a one-line note on what major banks' models include or exclude | Authored, represents realistic dispersion |
| Prior-year footnotes | FY2024 and FY2023 10-K excerpts showing two prior R&D credit true-ups | Authored, this is what creates the contested judgment call |

The agent never sees these documents directly. It calls tools, and the tool backend returns the relevant excerpt. This is deliberate: it lets the verifier check whether the agent's claims trace to something it actually retrieved, versus something it asserted without grounding.

---

## 3. Action space

| Tool | Signature | Behavior |
|---|---|---|
| `get_filing` | `get_filing(doc_type, period)` | Returns the matching excerpt (10-Q, prior 10-K footnotes) for the period requested. Wrong period or doc_type returns a "not found" message, which itself is loggable as a navigation error. |
| `get_transcript` | `get_transcript(period)` | Returns the earnings call transcript excerpt for that period. |
| `get_consensus` | `get_consensus(metric, period)` | Returns sell-side consensus value and a brief methodology note. |
| `calculator` | `calculator(expression)` | Deterministic arithmetic, no model involved. Prevents the agent from getting credit for arithmetic the verifier can't independently check. |
| `send_message_to_pm` | `send_message_to_pm(text)` | Sends the agent's reasoning to the PM simulator and triggers a PM turn in response. This is the dual-control channel. |
| `submit_recommendation` | `submit_recommendation(adjusted_eps, classification, rationale)` | Terminal action. Ends the episode and hands the full trace to the verifier. |

Turn budget: 8 total exchanges (agent tool calls plus PM exchanges combined) before forced termination, scored as a partial-credit timeout if `submit_recommendation` was never called.

---

## 4. The worked example

**Company:** Solaris Components Inc. (fictional, semiconductor packaging, mid-cap)

**Setup:** Q2 reported EPS is $1.42 against sell-side consensus of $1.28, a $0.14 beat. The beat decomposes into two items:

1. **Sale-leaseback gain on a fab facility, $0.18/share.** Disclosed in the 10-Q as a one-time gain on disposal, non-operating, no stated recurrence. This is the clean item.
2. **R&D tax credit true-up, $0.04/share.** Disclosed in a footnote. Cross-referencing the FY2024 and FY2023 10-Ks (which the agent must think to retrieve) shows Solaris took similar, smaller true-ups in two of the last three years. This is the contested item: defensible to treat as one-time given each instance differs in size and trigger, equally defensible to treat as a quasi-recurring pattern worth flagging.

**Gold key:**
- Sale-leaseback gain: must be excluded from adjusted EPS. Binary, strict grading.
- R&D credit: no single correct binary. Gold standard is that the analyst identifies the prior-year pattern (meaning they actually pulled the FY2024/FY2023 footnotes, not just the current 10-Q), discloses it explicitly, and reaches a defensible conclusion either way. Grading here is on disclosure and reasoning quality, not on which side they land.
- Correct adjusted EPS, if the agent excludes both items: $1.20. If the agent defensibly includes the R&D credit as recurring: $1.24. Both are scoreable as correct on the outcome axis provided the reasoning meets the rubric; only a result that fails to exclude the sale-leaseback gain, or that includes it without acknowledgment, is wrong outright.

**PM simulator script (branching):**

| PM turn | Trigger | Content |
|---|---|---|
| Opening pushback | Always fires after agent's initial brief | "Sell-side already backs out the lease gain, that's not new information. Did you treat the R&D credit the same way they did?" |
| Follow-up A | Agent excludes the R&D credit without mentioning prior-year pattern | "Didn't they take a similar credit last year too? Doesn't that make it operating in substance?" |
| Follow-up B | Agent addresses the pattern and gives reasoning | PM concedes or asks one clarifying question on magnitude, then accepts |
| Follow-up C | Agent repeats prior answer without engaging the new point | Flagged as an engagement failure regardless of the final numeric answer, this is the process check that catches a model gaming the outcome axis without doing the reasoning |

---

## 5. Verifier logic

Four components, weighted into a composite reward:

| Component | Weight | What it checks | Method |
|---|---|---|---|
| **Outcome correctness** | 0.45 | Sale-leaseback correctly excluded (binary). R&D credit treatment defensible and disclosed (graded, not binary). | Deterministic check on the binary half, LLM-judge against expert rubric on the judgment half |
| **Grounding quality** | 0.25 | Every factual claim in the agent's messages traces to something an actual tool call returned, including the prior-year footnote retrieval | Automated cross-reference of agent claims against tool call logs |
| **Defense quality** | 0.20 | Did the agent engage with each PM follow-up on its merits, versus deflecting or repeating itself | LLM-judge against expert-authored rubric, calibrated against Follow-up C trigger above |
| **Hallucination penalty** | 0.10 (subtracted) | Any invented fact not present in retrieved documents, e.g. citing a magnitude or date that wasn't in any tool output | Automated detector, hard penalty, mirrors the RxScribe HallRate treatment |

Composite: `Reward = 0.45·Outcome + 0.25·Grounding + 0.20·Defense - 0.10·Hallucination`

All four sub-scores are reported alongside the composite, not just the final number. This mirrors the RxScribe RBS precedent and is the detail that signals methodological seriousness to a lab evaluator, since it shows you're not just collapsing everything into one opaque scalar.

---

## 6. End-to-end workflow, init to reward

1. Episode initialized: filing, transcript, consensus, and prior-year footnotes loaded into the tool backend, gold key withheld from the agent.
2. Agent receives task brief: report and beat figures, instruction to determine adjusted EPS and brief the PM.
3. Agent operates in a tool-call loop, retrieving whatever it chooses to retrieve. Critically, nothing forces it to pull the prior-year footnotes. Whether it does so unprompted is itself a signal.
4. Agent calls `send_message_to_pm` with its initial brief and recommendation.
5. PM simulator turn fires per the branching script, conditioned on what the agent actually said.
6. Agent responds, possibly re-querying tools (e.g., realizing mid-conversation it needs to check prior filings).
7. Loop continues until `submit_recommendation` is called or the 8-turn budget is exhausted.
8. Full trace (tool calls, PM exchanges, final submission) passed to the verifier pipeline.
9. Four sub-scores computed, composite reward generated.
10. 10-20% of episodes sampled for human expert adjudication, where a CFA-credentialed reviewer checks the LLM-judge's scoring on Outcome (judgment half) and Defense quality against their own read. This is the calibration loop that catches the LLM-judge drifting or being gameable, same function as the pharmacist recalibration protocol in RxScribe.

---

## 7. Open questions, deferred for now

- **Which model plays the PM.** A cheaper model risks predictable, gameable pushback patterns. A frontier model raises cost per episode meaningfully at scale.
- **Turn budget tuning.** 8 is a starting guess, not derived from pilot data.
- **Contamination protection.** The gold key and full PM script must never appear in any public-facing version of AlphaNote-Bench, only the task brief and tool backend should be shared if this gets a public benchmark counterpart later.
- **How many of these get built before a lab conversation.** This document specs one scenario in full. The earlier recommendation was one robust environment over many shallow ones, worth revisiting once this one is pressure-tested.
