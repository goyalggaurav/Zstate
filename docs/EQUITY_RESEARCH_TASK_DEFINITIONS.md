# Equity Research Benchmark — Full Task Definitions (185 Tasks)

**Version:** 0.1  
**Total tasks:** 185  
**Companion:** [Task Catalog Overview](./EQUITY_RESEARCH_BENCHMARK_TASK_CATALOG.md) | [Framework](./ZSTATE_EQUITY_RESEARCH_BENCHMARK_FRAMEWORK.md)

Each task includes: **ID, name, layer, phase, description, inputs, outputs, tools, dependencies, pass criteria, fail conditions, difficulty (L1–L3), reward layers, sector applicability.**

**Naming note:** Compliance tasks use prefix `CPL-` (not `COMP-`, which is reserved for trading comps).

---

## Task Index Summary

| Prefix | Layer | Count | IDs |
|--------|-------|-------|-----|
| D- | Data acquisition | 24 | D-001 – D-024 |
| FS- | Financial statements | 24 | FS-001 – FS-024 |
| M3- | 3-statement model | 20 | M3-001 – M3-020 |
| DCF- | DCF valuation | 17 | DCF-001 – DCF-017 |
| COMP- | Trading comps | 12 | COMP-001 – COMP-012 |
| LBO- | LBO model | 10 | LBO-001 – LBO-010 |
| SOTP- | Sum-of-the-parts | 9 | SOTP-001 – SOTP-009 |
| DDM- | Dividend discount | 7 | DDM-001 – DDM-007 |
| MA- | M&A accretion/dilution | 4 | MA-001 – MA-004 |
| VAL- | Valuation synthesis | 6 | VAL-001 – VAL-006 |
| IND- | Industry analysis | 9 | IND-001 – IND-009 |
| EARN- | Earnings workflow | 12 | EARN-001 – EARN-012 |
| TH- | Investment thesis | 10 | TH-001 – TH-010 |
| RISK- | Risk & special situations | 10 | RISK-001 – RISK-010 |
| CPL- | Compliance | 10 | CPL-001 – CPL-010 |
| OUT- | Output assembly | 1 | OUT-001 |
| **Total** | | **185** | |

---

# Layer 0 — Data Acquisition (24 tasks)

### D-001: Map Ticker to CIK
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Resolve public ticker symbol to SEC Central Index Key and legal entity name. |
| **Inputs** | Ticker (e.g., GOOGL) |
| **Outputs** | `{ cik, entity_name, exchange, ticker }` |
| **Tools** | SEC EDGAR lookup, `Search_Filing` |
| **Dependencies** | None |
| **Pass** | CIK matches SEC EDGAR master |
| **Fail** | Wrong entity (e.g., GOOG vs GOOGL class confusion without disclosure) |
| **Difficulty** | L1 |
| **Reward** | L1 |
| **Sectors** | All |

### D-002: Fetch Latest 10-K for Fiscal Year
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Download and index the authoritative 10-K for a specified fiscal year, preferring latest amendment. |
| **Inputs** | Ticker, fiscal year (e.g., FY2024) |
| **Outputs** | Raw filing, `doc_id`, filing date, checksum |
| **Tools** | EDGAR fetcher, `PDF_Parser` |
| **Dependencies** | D-001 |
| **Pass** | Correct FY; 10-K/A supersedes original if amended |
| **Fail** | Wrong year; pre-amendment version used |
| **Difficulty** | L1 |
| **Reward** | L1 |
| **Sectors** | All |

### D-003: Fetch Trailing Eight 10-Q Filings
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Retrieve eight most recent quarterly filings for trend and guidance-drift analysis. |
| **Inputs** | Ticker |
| **Outputs** | Indexed list of 8 `doc_id`s with fiscal quarters |
| **Tools** | EDGAR fetcher |
| **Dependencies** | D-001, D-005 |
| **Pass** | No missing quarters in window |
| **Fail** | Gap quarter; wrong fiscal calendar |
| **Difficulty** | L1 |
| **Reward** | L1 |
| **Sectors** | All |

### D-004: Detect Filing Amendments
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Identify 10-K/A, 10-Q/A and mark superseded documents. |
| **Inputs** | CIK, document list |
| **Outputs** | Amendment graph: `{ original_doc_id, superseded_by }` |
| **Tools** | EDGAR metadata |
| **Dependencies** | D-002, D-003 |
| **Pass** | Latest amendment flagged as canonical |
| **Fail** | Original used when amendment exists |
| **Difficulty** | L2 |
| **Reward** | L1, L3 |
| **Sectors** | All |

### D-005: Parse Fiscal Calendar
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Determine fiscal year-end month (Dec, Jun, Sep, etc.) from 10-K cover page. |
| **Inputs** | 10-K |
| **Outputs** | `{ fy_end_month, period_convention }` |
| **Tools** | `PDF_Parser` |
| **Dependencies** | D-002 |
| **Pass** | FY end matches SEC header |
| **Fail** | Calendar assumption causes quarter mis-map |
| **Difficulty** | L1 |
| **Reward** | L1 |
| **Sectors** | All |

### D-006: Extract Income Statement (3–5 Years)
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Extract multi-year IS: revenue through net income, EPS if reported. |
| **Inputs** | 10-K series |
| **Outputs** | Structured IS JSON with periods and units |
| **Tools** | `PDF_Parser`, `Python_Interpreter` |
| **Dependencies** | D-002, D-009 |
| **Pass** | Line items match filing; units correct |
| **Fail** | Wrong period; thousands vs millions error |
| **Difficulty** | L2 |
| **Reward** | L1 |
| **Sectors** | All |

### D-007: Extract Balance Sheet (2–5 Years)
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Extract assets, liabilities, equity with current/non-current split. |
| **Inputs** | 10-K, latest 10-Q |
| **Outputs** | Structured BS JSON |
| **Tools** | `PDF_Parser` |
| **Dependencies** | D-002, D-003, D-009 |
| **Pass** | A = L + E on extracted numbers |
| **Fail** | Missing lease lines; misclassified current debt |
| **Difficulty** | L2 |
| **Reward** | L1 |
| **Sectors** | All |

### D-008: Extract Cash Flow Statement (3–5 Years)
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Extract OCF, investing, financing sections including CapEx, buybacks, dividends. |
| **Inputs** | 10-K series |
| **Outputs** | Structured CF JSON |
| **Tools** | `PDF_Parser` |
| **Dependencies** | D-002, D-009 |
| **Pass** | CapEx and SBC in CF reconcile to footnotes ±materiality |
| **Fail** | Sign inversion on CapEx or buybacks |
| **Difficulty** | L2 |
| **Reward** | L1 (sign = critical) |
| **Sectors** | All |

### D-009: Identify Unit Convention
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Detect whether tables are in thousands, millions, or billions. |
| **Inputs** | Any filing financial table |
| **Outputs** | `{ unit_multiplier, unit_label }` |
| **Tools** | `PDF_Parser` |
| **Dependencies** | None |
| **Pass** | Multiplier matches table header |
| **Fail** | 1000× magnitude error downstream |
| **Difficulty** | L1 |
| **Reward** | L1 |
| **Sectors** | All |

### D-010: Distinguish GAAP vs Non-GAAP Labels
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Parse IR earnings deck/release and map non-GAAP metrics to GAAP equivalents. |
| **Inputs** | IR PDF, 10-Q |
| **Outputs** | Label mapping table |
| **Tools** | `PDF_Parser`, `Search_Filing` |
| **Dependencies** | D-013 |
| **Pass** | No conflation of adjusted vs GAAP in storage |
| **Fail** | Stores "Adjusted EPS" as GAAP EPS |
| **Difficulty** | L2 |
| **Reward** | L1, L2 |
| **Sectors** | All |

### D-011: Pull Earnings Transcript
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Ingest earnings call transcript for specified fiscal quarter (API primary, IR fallback). |
| **Inputs** | Ticker, fiscal quarter |
| **Outputs** | Transcript text, `doc_id`, event date, speaker index |
| **Tools** | Transcript API, manual IR importer |
| **Dependencies** | D-001, D-005 |
| **Pass** | Correct quarter and call date |
| **Fail** | Wrong quarter; wrong company |
| **Difficulty** | L1 |
| **Reward** | L1, L3 |
| **Sectors** | All |

### D-012: Align Transcript Quarter to 10-Q
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Link transcript fiscal period to corresponding 10-Q `doc_id`. |
| **Inputs** | Transcript metadata, 10-Q list |
| **Outputs** | `{ transcript_doc_id, ten_q_doc_id, fiscal_period }` |
| **Tools** | Corpus registry |
| **Dependencies** | D-003, D-011 |
| **Pass** | Same fiscal period on both |
| **Fail** | Off-by-one quarter |
| **Difficulty** | L2 |
| **Reward** | L1 |
| **Sectors** | All |

### D-013: Fetch Investor Presentation
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Download IR earnings presentation matching earnings date. |
| **Inputs** | Ticker, earnings date |
| **Outputs** | Deck PDF, `doc_id` |
| **Tools** | IR fetcher, `PDF_Parser` |
| **Dependencies** | D-011 |
| **Pass** | Deck date matches earnings |
| **Fail** | Wrong event deck |
| **Difficulty** | L1 |
| **Reward** | L1 |
| **Sectors** | All |

### D-014: Extract Supplemental KPI Table
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Extract KPIs from IR supplemental (subs, units, ARPU, etc.). |
| **Inputs** | IR deck/Excel, 10-Q |
| **Outputs** | KPI time series JSON |
| **Tools** | `PDF_Parser`, `Python_Interpreter` |
| **Dependencies** | D-013, D-003 |
| **Pass** | KPIs cross-check to 10-Q where disclosed |
| **Fail** | Invented KPI not in source |
| **Difficulty** | L2 |
| **Reward** | L1, L3 |
| **Sectors** | Tech, Media, Consumer (KPI-heavy) |

### D-015: Build Peer Universe
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P0 |
| **Description** | Select 5–8 comparable companies with written GICS/segment rationale. |
| **Inputs** | Target ticker, sector |
| **Outputs** | Peer list + rationale memo |
| **Tools** | `Search_Filing`, `Vector_Search` |
| **Dependencies** | D-001 |
| **Pass** | Peers same industry; rationale cites business model |
| **Fail** | Cross-sector peer without justification |
| **Difficulty** | L2 |
| **Reward** | L2 |
| **Sectors** | All |

### D-016: Pull Peer 10-K Filings
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Ingest latest 10-K for each peer in universe. |
| **Inputs** | Peer list |
| **Outputs** | Peer filing bundle |
| **Tools** | EDGAR fetcher |
| **Dependencies** | D-015, D-002 |
| **Pass** | All peers have current FY filing |
| **Fail** | Missing peer data |
| **Difficulty** | L1 |
| **Reward** | L1 |
| **Sectors** | All |

### D-017: Load FX Average Rates
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Build weighted-average FX table for currencies disclosed in geographic segments. |
| **Inputs** | 10-K FX note, FRED rates |
| **Outputs** | `{ pair, period, avg_rate, rate_type }` table |
| **Tools** | Corpus FX API, `Python_Interpreter` |
| **Dependencies** | D-002 |
| **Pass** | Uses weighted avg when footnote specifies; flags spot misuse |
| **Fail** | Spot rate used for organic growth calc |
| **Difficulty** | L2 |
| **Reward** | L1 |
| **Sectors** | Tech, Consumer, Media (international) |

### D-018: Load Shares Outstanding
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Extract basic and diluted share count by period. |
| **Inputs** | 10-K, 10-Q, EPS footnote |
| **Outputs** | Share count series |
| **Tools** | `PDF_Parser` |
| **Dependencies** | D-002, D-003 |
| **Pass** | Diluted used for EPS; period-end for market cap noted |
| **Fail** | Wrong share class; wrong period |
| **Difficulty** | L2 |
| **Reward** | L1 |
| **Sectors** | All |

### D-019: Load Net Debt Components
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Compute net debt: ST debt + LT debt + leases − cash & equivalents. |
| **Inputs** | BS, debt footnote |
| **Outputs** | `{ net_debt, components[] }` |
| **Tools** | `PDF_Parser`, `Python_Interpreter` |
| **Dependencies** | D-007 |
| **Pass** | Matches footnote reconciliation |
| **Fail** | Omits ST debt or lease liabilities |
| **Difficulty** | L2 |
| **Reward** | L1 |
| **Sectors** | All |

### D-020: Flag Restatement / Accounting Change
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Scan footnotes for restatements, accounting policy changes, prior period adjustments. |
| **Inputs** | 10-K notes |
| **Outputs** | Change log with impacted line items |
| **Tools** | `Search_Filing`, `PDF_Parser` |
| **Dependencies** | D-002 |
| **Pass** | All material changes logged |
| **Fail** | Misses Note 1 policy change |
| **Difficulty** | L2 |
| **Reward** | L2, L3 |
| **Sectors** | All |

### D-021: Ingest 8-K Material Event
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Fetch and summarize 8-K filings in date window (M&A, impairment, leadership). |
| **Inputs** | Ticker, date range |
| **Outputs** | Event summary list |
| **Tools** | EDGAR fetcher, `PDF_Parser` |
| **Dependencies** | D-001 |
| **Pass** | Material events captured with date and item code |
| **Fail** | Misses EX-99.1 earnings 8-K |
| **Difficulty** | L2 |
| **Reward** | L1, L2 |
| **Sectors** | All |

### D-022: Cross-Check 8-K Press Release vs 10-Q
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Compare EX-99.1 earnings release numbers to subsequently filed 10-Q. |
| **Inputs** | 8-K exhibit, 10-Q |
| **Outputs** | Discrepancy report |
| **Tools** | `PDF_Parser`, `Python_Interpreter` |
| **Dependencies** | D-021, D-003 |
| **Pass** | Material diffs explained (reclassification, subsequent events) |
| **Fail** | Ignores pre-release vs filed gap |
| **Difficulty** | L3 |
| **Reward** | L1, L2 |
| **Sectors** | All |

### D-023: Version Corpus Snapshot
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Lock all documents for benchmark run with root checksum manifest. |
| **Inputs** | Full document set |
| **Outputs** | `corpus_v1` manifest |
| **Tools** | Corpus service |
| **Dependencies** | D-002 through D-022 |
| **Pass** | Immutable manifest; all doc checksums |
| **Fail** | Drift between eval runs |
| **Difficulty** | L1 |
| **Reward** | L3 |
| **Sectors** | All |

### D-024: Cite Every Extracted Number
| Field | Detail |
|-------|--------|
| **Layer / Phase** | 0 — Data / P1 |
| **Description** | Attach `{ doc_id, page, snippet, table_id }` to every extracted data point. |
| **Inputs** | Any extraction task output |
| **Outputs** | Citation-enriched data package |
| **Tools** | Corpus citation API |
| **Dependencies** | Parallel to D-006–D-019 |
| **Pass** | 100% citation coverage |
| **Fail** | Any number without auditable path |
| **Difficulty** | L2 |
| **Reward** | L3 (critical) |
| **Sectors** | All |

---

# Layer 1 — Financial Statement Intelligence (24 tasks)

### FS-001: Identify Non-GAAP Reconciliations
| Field | Detail |
|-------|--------|
| **Description** | Locate all non-GAAP metrics and reconciliation tables in earnings release and 10-Q. |
| **Inputs** | IR release, 10-Q |
| **Outputs** | List of non-GAAP metrics + reconciliation refs |
| **Dependencies** | D-010, D-003 |
| **Pass** | All adjusted metrics mapped to GAAP |
| **Fail** | Uses adjusted without reconciliation |
| **Difficulty** | L2 | **Reward** | L2 |

### FS-002: Rebuild GAAP → Adjusted EBITDA Bridge
| Field | Detail |
|-------|--------|
| **Description** | Construct full bridge from GAAP net income to company-reported adjusted EBITDA. |
| **Inputs** | Reconciliation tables |
| **Outputs** | Line-by-line bridge with citations |
| **Dependencies** | FS-001 |
| **Pass** | Bridge sums correctly |
| **Fail** | Omits stock comp or restructuring add-back |
| **Difficulty** | L2 | **Reward** | L1, L2 |

### FS-003: Separate Recurring vs One-Time Operating Items
| Field | Detail |
|-------|--------|
| **Description** | Classify operating income components as recurring or one-time. |
| **Inputs** | IS, footnotes, 8-K |
| **Outputs** | Core operating income vs adjustments |
| **Dependencies** | FS-002, D-020 |
| **Pass** | One-times identified with footnote source |
| **Fail** | Treats asset sale gain as recurring |
| **Difficulty** | L2 | **Reward** | L2 |

### FS-004: Footnote Reconciliation — Segment vs Consolidated
| Field | Detail |
|-------|--------|
| **Description** | Reconcile segment revenue/OP to consolidated; resolve eliminations and reclassifications in footnotes. |
| **Inputs** | Segment table, accounting policy note |
| **Outputs** | Reconciliation table + discrepancy flag |
| **Dependencies** | D-006, D-024 |
| **Pass** | Segments tie to consolidated ± disclosed eliminations |
| **Fail** | Misses footnote-only reclassification (**MVD archetype**) |
| **Difficulty** | L3 | **Reward** | L1, L2 |

### FS-005: Footnote Reconciliation — Inventory Costing Change
| Field | Detail |
|-------|--------|
| **Description** | Quantify impact of inventory accounting change on COGS and margins. |
| **Inputs** | Note 1/2, IS |
| **Outputs** | Impact quantification by period |
| **Dependencies** | D-020, D-006 |
| **Pass** | Impact matches footnote disclosure |
| **Fail** | Ignores retrospective application |
| **Difficulty** | L3 | **Reward** | L1, L2 |

### FS-006: Extract Stock-Based Compensation
| Field | Detail |
|-------|--------|
| **Description** | Pull SBC from footnote and CF statement; note cash tax benefit if any. |
| **Inputs** | 10-K notes, CF |
| **Outputs** | SBC by year; cash vs non-cash |
| **Dependencies** | D-006, D-008 |
| **Pass** | Matches footnote total |
| **Fail** | Confuses SBC with other equity comp |
| **Difficulty** | L2 | **Reward** | L1 | **Sectors** | Tech |

### FS-007: Allocate SBC to Segments
| Field | Detail |
|-------|--------|
| **Description** | Allocate enterprise SBC to segments when not directly reported. |
| **Inputs** | SBC total, segment headcount/revenue proxy, footnotes |
| **Outputs** | Segment SBC allocation with method |
| **Dependencies** | FS-006 |
| **Pass** | Method disclosed; sums to total |
| **Fail** | Arbitrary split without rationale |
| **Difficulty** | L3 | **Reward** | L2 | **Sectors** | Tech |

### FS-008: Identify Capitalized Software / R&D
| Field | Detail |
|-------|--------|
| **Description** | Quantify capitalized development costs and amortization from footnotes. |
| **Inputs** | Intangible assets note, R&D footnote |
| **Outputs** | Capitalized vs expensed split |
| **Dependencies** | D-008, footnotes |
| **Pass** | Ties to CF and BS intangible roll-forward |
| **Fail** | Misses cloud software capitalization |
| **Difficulty** | L3 | **Reward** | L2 | **Sectors** | Tech (GOOGL, MSFT) |

### FS-009: Content Amortization vs Cash Content Spend
| Field | Detail |
|-------|--------|
| **Description** | Compare content amortization (P&L/CF) to cash content investments on balance sheet. |
| **Inputs** | NFLX/DIS content footnote, CF |
| **Outputs** | Amort vs cash spend bridge |
| **Dependencies** | D-008, content asset note |
| **Pass** | Distinguishes amort from cash spend |
| **Fail** | Uses amort as proxy for cash investment |
| **Difficulty** | L3 | **Reward** | L2 | **Sectors** | Media |

### FS-010: Reconcile Franchise vs Company-Operated Revenue
| Field | Detail |
|-------|--------|
| **Description** | Separate franchise royalties from company-operated store revenue and margins. |
| **Inputs** | Segment/franchise disclosure |
| **Outputs** | Split revenue and OP metrics |
| **Dependencies** | D-006, franchise note |
| **Pass** | Matches 10-K franchise disclosure |
| **Fail** | Blends unlike margin profiles |
| **Difficulty** | L2 | **Reward** | L2 | **Sectors** | Consumer (MCD, SBUX) |

### FS-011: Lease-Adjusted Metrics
| Field | Detail |
|-------|--------|
| **Description** | Compute EBITDAR or adjust for ASC 842 lease accounting when comparing peers. |
| **Inputs** | Lease footnote, IS |
| **Outputs** | Lease-adjusted EBITDA metrics |
| **Dependencies** | D-007, lease note |
| **Pass** | Lease liability/op lease cost handled per ASC 842 |
| **Fail** | Double-counts rent |
| **Difficulty** | L3 | **Reward** | L2 | **Sectors** | Retail, restaurants |

### FS-012: Organic Constant-Currency Revenue Growth
| Field | Detail |
|-------|--------|
| **Description** | Calculate organic CC revenue growth by geography using weighted-average FX. |
| **Inputs** | Geographic revenue, FX table (D-017) |
| **Outputs** | Organic CC growth by region and consolidated |
| **Dependencies** | D-017, segment footnote |
| **Pass** | Uses weighted avg; separates M&A if disclosed |
| **Fail** | Spot rate; ignores acquisition impact (**MVD archetype**) |
| **Difficulty** | L3 | **Reward** | L1, L2 |

### FS-013: Price vs Volume vs Mix Decomposition
| Field | Detail |
|-------|--------|
| **Description** | Decompose revenue growth into price, volume, mix when company discloses. |
| **Inputs** | MD&A, IR deck, 10-Q |
| **Outputs** | P/V/M table |
| **Dependencies** | D-006, D-013 |
| **Pass** | Components sum to total growth |
| **Fail** | Invents decomposition not disclosed |
| **Difficulty** | L2 | **Reward** | L2 | **Sectors** | Consumer |

### FS-014: Goodwill Impairment Triggers
| Field | Detail |
|-------|--------|
| **Description** | Identify goodwill/intangible impairment indicators and recorded charges. |
| **Inputs** | Goodwill footnote, 8-K |
| **Outputs** | Impairment history + trigger assessment |
| **Dependencies** | D-007, D-021 |
| **Pass** | Impairments tied to segment reporting |
| **Fail** | Misses WBD-style legacy goodwill risk |
| **Difficulty** | L2 | **Reward** | L2 | **Sectors** | Media |

### FS-015: Debt Maturity Schedule
| Field | Detail |
|-------|--------|
| **Description** | Extract contractual debt maturity ladder from footnote. |
| **Inputs** | Debt note |
| **Outputs** | Maturity schedule by year |
| **Dependencies** | D-007 |
| **Pass** | Matches total debt on BS |
| **Fail** | Omits revolving credit availability |
| **Difficulty** | L2 | **Reward** | L1, L2 |

### FS-016: Off-Balance-Sheet Commitments
| Field | Detail |
|-------|--------|
| **Description** | Quantify operating lease commitments, purchase obligations, guarantees. |
| **Inputs** | Commitments & contingencies note |
| **Outputs** | Commitment summary table |
| **Dependencies** | D-002 |
| **Pass** | All material commitments captured |
| **Fail** | Ignores purchase obligations |
| **Difficulty** | L2 | **Reward** | L2, L3 |

### FS-017: Related-Party Transactions
| Field | Detail |
|-------|--------|
| **Description** | Identify related-party transactions from proxy and footnotes. |
| **Inputs** | DEF 14A, footnotes |
| **Outputs** | RPT list with amounts |
| **Dependencies** | D-002 |
| **Pass** | Material RPTs disclosed |
| **Fail** | Misses proxy-only disclosure |
| **Difficulty** | L2 | **Reward** | L3 |

### FS-018: Verify Cash Flow Sign Conventions
| Field | Detail |
|-------|--------|
| **Description** | Confirm CapEx, buybacks, dividends, debt issuance shown with correct sign in CF and models. |
| **Inputs** | CF statement, model CF |
| **Outputs** | Sign validation report |
| **Dependencies** | D-008 |
| **Pass** | CapEx negative in FCF calc; buybacks negative in financing |
| **Fail** | Sign inversion inflates FCF (**critical**) |
| **Difficulty** | L2 | **Reward** | L1 (critical veto) |

### FS-019: Reconcile Net Income → OCF → FCF
| Field | Detail |
|-------|--------|
| **Description** | Build and verify indirect method bridge from NI to OCF to unlevered FCF. |
| **Inputs** | IS, CF, WC changes |
| **Outputs** | Integrated bridge |
| **Dependencies** | D-006, D-008, FS-018 |
| **Pass** | Bridge ties within ±0.01% |
| **Fail** | WC change wrong sign |
| **Difficulty** | L3 | **Reward** | L1 |

### FS-020: Auditor Opinion & Going Concern
| Field | Detail |
|-------|--------|
| **Description** | Flag changes in auditor, qualified opinion, going concern paragraph. |
| **Inputs** | 10-K audit report |
| **Outputs** | Audit risk flags |
| **Dependencies** | D-002 |
| **Pass** | Correct opinion type extracted |
| **Fail** | Misses going concern |
| **Difficulty** | L1 | **Reward** | L3 |

### FS-021: MD&A Narrative vs Quantitative Trend
| Field | Detail |
|-------|--------|
| **Description** | Compare management MD&A claims to reported numbers (guidance drift precursor). |
| **Inputs** | MD&A, IS/CF trends |
| **Outputs** | Narrative vs data alignment report |
| **Dependencies** | D-006, D-008 |
| **Pass** | Flags contradictions |
| **Fail** | Accepts narrative without verification |
| **Difficulty** | L2 | **Reward** | L2 |

### FS-022: Change in Accounting Principle
| Field | Detail |
|-------|--------|
| **Description** | Identify and summarize new accounting standards adopted (Note 1). |
| **Inputs** | Note 1 |
| **Outputs** | Policy change memo |
| **Dependencies** | D-020 |
| **Pass** | Effective date and impact stated |
| **Fail** | Misses retrospective restatement |
| **Difficulty** | L2 | **Reward** | L2 |

### FS-023: Segment OP vs Consolidated OP Reconciliation
| Field | Detail |
|-------|--------|
| **Description** | Reconcile sum of segment operating profit to consolidated OP including unallocated corporate. |
| **Inputs** | Segment note |
| **Outputs** | Reconciliation with corporate overhead |
| **Dependencies** | FS-004 |
| **Pass** | Corporate overhead identified |
| **Fail** | Double-counts eliminations |
| **Difficulty** | L3 | **Reward** | L1, L2 | **Sectors** | Conglomerates |

### FS-024: Calculate NOPAT for ROIC
| Field | Detail |
|-------|--------|
| **Description** | Compute NOPAT and invested capital for ROIC analysis. |
| **Inputs** | Normalized EBIT, tax rate, BS |
| **Outputs** | `{ nopat, invested_capital, roic }` |
| **Dependencies** | FS-003, D-007 |
| **Pass** | Tax rate normalized; IC excludes excess cash per policy |
| **Fail** | Uses headline tax rate with one-time benefit |
| **Difficulty** | L3 | **Reward** | L1, L2 |

---

# Layer 2A — Three-Statement Model (20 tasks)

### M3-001: Build 5-Year Historical Income Statement
| **Description** | Populate historical IS from extracted filings. | **Dependencies** | D-006, FS-003 | **Pass** | Matches filings cited | **Fail** | Mixed annual/quarterly | **Difficulty** | L2 |

### M3-002: Build 5-Year Historical BS and CF
| **Description** | Populate historical balance sheet and cash flow. | **Dependencies** | D-007, D-008 | **Pass** | A=L+E; CF ties | **Fail** | Broken links | **Difficulty** | L2 |

### M3-003: Identify Revenue Drivers by Segment
| **Description** | Map revenue to segment, geographic, or unit×price drivers. | **Dependencies** | M3-001, segment note | **Pass** | Driver map cited | **Fail** | Single growth rate with no segment detail | **Difficulty** | L2 |

### M3-004: Forecast Revenue 5 Years (Segment-Level)
| **Description** | Project revenue by segment/geography with stated assumptions. | **Dependencies** | M3-003, FS-012 | **Pass** | Segments sum to total | **Fail** | Top-down only with no segment build | **Difficulty** | L3 |

### M3-005: Forecast Gross Margin (Commodity Sensitivity)
| **Description** | Model gross margin with input cost drivers where relevant. | **Dependencies** | M3-004 | **Pass** | Sensitivity to commodity shown | **Fail** | Flat margin without rationale | **Difficulty** | L3 | **Sectors** | PEP, KO, MDLZ |

### M3-006: Forecast OpEx with Operating Leverage
| **Description** | Project R&D, S&M, G&A as % revenue or absolute with leverage thesis. | **Dependencies** | M3-004 | **Pass** | OpEx ties to historical ratios bounded | **Fail** | OpEx declines forever without limit | **Difficulty** | L3 |

### M3-007: Build D&A from PP&E Roll-Forward
| **Description** | Link CapEx and D&A through PP&E schedule. | **Dependencies** | M3-002, M3-008 | **Pass** | PP&E roll ties | **Fail** | D&A disconnected from assets | **Difficulty** | L3 |

### M3-008: Build CapEx Schedule (Maintenance + Growth)
| **Description** | Split CapEx into maintenance and growth; align with mgmt guidance. | **Dependencies** | M3-004, D-008 | **Pass** | CapEx/Revenue ratio bounded vs history | **Fail** | Ignores AI/cloud capex guidance (tech) | **Difficulty** | L3 |

### M3-009: Build NWC Schedule (DSO, DIO, DPO)
| **Description** | Forecast working capital from turnover ratios. | **Dependencies** | M3-002 | **Pass** | ΔNWC feeds CF correctly | **Fail** | NWC change wrong sign in FCF | **Difficulty** | L3 |

### M3-010: PP&E Roll-Forward Link
| **Description** | Verify Beginning + CapEx − D&A = Ending PP&E each year. | **Dependencies** | M3-007, M3-008 | **Pass** | Roll-forward exact | **Fail** | Broken link | **Difficulty** | L2 |

### M3-011: Debt Schedule with Interest Expense
| **Description** | Model debt balances, interest at effective rate, mandatory amortization. | **Dependencies** | FS-015, D-019 | **Pass** | Interest ties to footnote rate ±10bps | **Fail** | Interest on wrong base | **Difficulty** | L3 |

### M3-012: Model SBC and Share Count Dilution
| **Description** | Forecast SBC and diluted share count path. | **Dependencies** | FS-006, D-018 | **Pass** | Dilution matches repurchase offset | **Fail** | Flat shares ignoring SBC | **Difficulty** | L3 | **Sectors** | Tech |

### M3-013: Model Share Repurchase Program
| **Description** | Apply authorization-based buyback to equity and share count. | **Dependencies** | M3-012, CF | **Pass** | Buybacks tie to CF financing | **Fail** | Buybacks exceed authorization without flag | **Difficulty** | L2 |

### M3-014: Model Dividend Payout Schedule
| **Description** | Project DPS and total dividends from payout policy. | **Dependencies** | M3-015, CF | **Pass** | Dividends ≤ FCF or flagged | **Fail** | Unsustainable payout ignored | **Difficulty** | L2 | **Sectors** | PEP, KO, MCD |

### M3-015: Complete Projected Cash Flow (Indirect Method)
| **Description** | Build full projected CF from NI through OCF, ICF, FCF. | **Dependencies** | M3-001–M3-014 | **Pass** | Ending cash = BS cash | **Fail** | CF not linked to BS | **Difficulty** | L3 |

### M3-016: Verify A = L + E All Periods
| **Description** | Balance sheet identity check every historical and forecast year. | **Dependencies** | M3-015 | **Pass** | Zero balance sheet error all periods | **Fail** | Any period fails (**critical**) | **Difficulty** | L2 |

### M3-017: Calculate Unlevered Free Cash Flow
| **Description** | Derive UFCF = EBIT(1−t) + D&A − CapEx − ΔNWC from model. | **Dependencies** | M3-015, M3-016 | **Pass** | UFCF matches manual Python verify ±0.01% | **Fail** | Uses net income shortcut | **Difficulty** | L3 |

### M3-018: Scenario — Recession Case (−10% Revenue)
| **Description** | Downside IS/CF with recession assumptions. | **Dependencies** | M3-004–M3-017 | **Pass** | Scenario documented and still balances | **Fail** | Breaks balance sheet | **Difficulty** | L3 |

### M3-019: Scenario — Margin Expansion Upside
| **Description** | Upside case with explicit margin drivers. | **Dependencies** | M3-004–M3-017 | **Pass** | Bounded vs peer margins | **Fail** | Unrealistic margin target | **Difficulty** | L3 |

### M3-020: Export Model Assumptions with Citations
| **Description** | Produce assumption log: every input linked to source. | **Dependencies** | M3-001–M3-019 | **Pass** | 100% material assumptions cited | **Fail** | Uncited key driver | **Difficulty** | L2 | **Reward** | L3 |

---

# Layer 2B — DCF Model (17 tasks)

### DCF-001: Calculate CAPM Cost of Equity
| **Description** | Ke = Rf + β × ERP. | **Inputs** | FRED Rf, beta, ERP assumption | **Dependencies** | D-018, market data | **Pass** | Formula correct; inputs cited | **Fail** | Hardcoded Ke | **Difficulty** | L2 |

### DCF-002: Justify Beta Selection
| **Description** | Document 2-yr vs 5-yr regression choice vs peer beta. | **Dependencies** | DCF-001 | **Pass** | Written rationale | **Fail** | Beta without source | **Difficulty** | L2 | **Reward** | L2 |

### DCF-003: Calculate Pre-Tax Cost of Debt
| **Description** | Kd from interest expense / average debt or footnote yield. | **Dependencies** | FS-015, M3-011 | **Pass** | Matches footnote ±25bps | **Fail** | Uses coupon on wrong debt balance | **Difficulty** | L2 |

### DCF-004: Compute WACC
| **Description** | Weight Ke and Kd by market values; tax-adjust Kd. | **Dependencies** | DCF-001, DCF-003, D-019 | **Pass** | WACC within peer range | **Fail** | Book value weights used | **Difficulty** | L3 |

### DCF-005: Project UFCF 5–10 Years
| **Description** | Pull UFCF from 3-statement model. | **Dependencies** | M3-017 | **Pass** | Matches M3-017 exactly | **Fail** | Skips model; guesses FCF | **Difficulty** | L3 |

### DCF-006: Select Terminal Value Method
| **Description** | Choose Gordon growth vs exit multiple with written rationale. | **Dependencies** | DCF-005 | **Pass** | Method matches business maturity | **Fail** | Gordon on high-growth tech without bounds | **Difficulty** | L2 | **Reward** | L2 |

### DCF-007: Bound Terminal Growth Rate
| **Description** | Terminal g ≤ long-term GDP/industry growth with justification. | **Dependencies** | DCF-006, IND-002 | **Pass** | g bounded and cited | **Fail** | g > GDP without moat case (**mandate fail**) | **Difficulty** | L3 |

### DCF-008: Compute Gordon Terminal Value
| **Description** | TV = UFCF(n+1) / (WACC − g). | **Dependencies** | DCF-005, DCF-007 | **Pass** | TV calculation verified in Python | **Fail** | g ≥ WACC | **Difficulty** | L3 |

### DCF-009: Compute Exit Multiple Terminal Value
| **Description** | TV = Exit EBITDA × peer median multiple. | **Dependencies** | COMP-006, M3-004 | **Pass** | Multiple from comp set | **Fail** | Arbitrary multiple | **Difficulty** | L3 |

### DCF-010: Discount UFCF and TV to Present Value
| **Description** | PV of explicit period + PV of TV. | **Dependencies** | DCF-005, DCF-008 or DCF-009 | **Pass** | Mid-year convention documented | **Fail** | TV > 80% without sensitivity flag | **Difficulty** | L3 |

### DCF-011: Bridge EV to Equity Value
| **Description** | Equity = EV − net debt + non-operating assets. | **Dependencies** | DCF-010, D-019 | **Pass** | Net debt matches D-019 | **Fail** | Omits minority interest | **Difficulty** | L2 |

### DCF-012: Compute Implied Share Price
| **Description** | Equity value ÷ diluted shares. | **Dependencies** | DCF-011, D-018 | **Pass** | Uses diluted shares | **Fail** | Basic shares for dilutive co | **Difficulty** | L2 |

### DCF-013: WACC × Terminal g Sensitivity Table
| **Description** | 5×5 grid of implied prices. | **Dependencies** | DCF-004, DCF-007, DCF-012 | **Pass** | Grid mathematically consistent | **Fail** | Single point estimate only | **Difficulty** | L2 |

### DCF-014: Exit Multiple Sensitivity
| **Description** | Sensitivity of price to exit EV/EBITDA ±2 turns. | **Dependencies** | DCF-009 | **Pass** | Range presented | **Fail** | No sensitivity | **Difficulty** | L2 |

### DCF-015: Compare DCF to Current Market Price
| **Description** | Compute upside/downside %. | **Dependencies** | DCF-012, market price | **Pass** | % calc correct | **Fail** | Stale price without date | **Difficulty** | L1 |

### DCF-016: Document All DCF Assumptions
| **Description** | Audit trail for WACC, g, margins, CapEx. | **Dependencies** | DCF-001–015 | **Pass** | All assumptions cited | **Fail** | Missing source | **Difficulty** | L2 | **Reward** | L3 |

### DCF-017: Flag Unverified DCF Inputs
| **Description** | Mark missing data; do not interpolate. | **Dependencies** | DCF-016 | **Pass** | Gaps flagged as unverified | **Fail** | Hallucinated input (**critical L3**) | **Difficulty** | L2 |

---

# Layer 2C — Trading Comps (12 tasks)

### COMP-001: Select 5–8 Peers with Rationale
| **Dependencies** | D-015 | **Pass** | Sector-appropriate list | **Fail** | Absurd peer (e.g., NVDA for KO) | **Difficulty** | L2 |

### COMP-002: Pull LTM Revenue, EBITDA, EPS for Peers
| **Dependencies** | D-016, D-006 | **Pass** | Same LTM period all peers | **Fail** | Mixed fiscal periods | **Difficulty** | L2 |

### COMP-003: Normalize Peer EBITDA
| **Dependencies** | COMP-002, FS-003 | **Pass** | One-times added back with citation | **Fail** | Raw GAAP only | **Difficulty** | L3 |

### COMP-004: Calculate Peer Enterprise Values
| **Dependencies** | COMP-002, market data, D-019 | **Pass** | EV = MC + net debt | **Fail** | Equity value used as EV | **Difficulty** | L2 |

### COMP-005: Compute Peer Multiples
| **Description** | EV/EBITDA, EV/Revenue, P/E, P/FCF. | **Dependencies** | COMP-003, COMP-004 | **Pass** | Median and mean calculated | **Fail** | Division by zero unhandled | **Difficulty** | L2 |

### COMP-006: Summarize Multiple Statistics
| **Description** | Mean, median, 25th/75th percentile. | **Dependencies** | COMP-005 | **Pass** | Stats correct | **Fail** | Outlier not flagged | **Difficulty** | L2 |

### COMP-007: Apply Median EV/EBITDA to Target NTM EBITDA
| **Dependencies** | COMP-006, M3-004 | **Pass** | Implied EV reasonable | **Fail** | NTM EBITDA not from model | **Difficulty** | L3 |

### COMP-008: Apply Median P/E to Target NTM EPS
| **Dependencies** | COMP-006, M3-001 | **Pass** | Implied price calculated | **Fail** | Uses GAAP EPS with one-time | **Difficulty** | L3 |

### COMP-009: Explain Premium/Discount vs Peers
| **Dependencies** | COMP-007, COMP-008 | **Pass** | 3+ factor rationale | **Fail** | "Deserves premium" without evidence | **Difficulty** | L2 | **Reward** | L2 |

### COMP-010: Sector-Specific Multiple (EV/Sub, EV/Sub)
| **Dependencies** | COMP-005, D-014 | **Pass** | Sector metric correctly computed | **Fail** | Wrong denominator | **Difficulty** | L3 | **Sectors** | NFLX, SPOT, DIS |

### COMP-011: Flag Inappropriate Comp
| **Description** | Identify and reject wrong-sector peer inclusion. | **Dependencies** | COMP-001 | **Pass** | Flags bad comp | **Fail** | Accepts all peers uncritically | **Difficulty** | L2 | **Reward** | L2 |

### COMP-012: Refresh Comps Post-Earnings
| **Dependencies** | COMP-001–011, EARN-008 | **Pass** | Updated LTM/NTM | **Fail** | Stale peer data | **Difficulty** | L2 |

---

# Layer 2D — LBO Model (10 tasks)

### LBO-001: Set Entry EV/Multiple
| **Dependencies** | COMP-006 or market | **Pass** | Entry rationale documented | **Fail** | Arbitrary entry | **Difficulty** | L2 |

### LBO-002: Build Sources & Uses
| **Dependencies** | LBO-001 | **Pass** | S&U balance | **Fail** | S≠U | **Difficulty** | L2 |

### LBO-003: Layer Debt Tranches
| **Description** | Senior + sub at market rates; 60–70% leverage. | **Dependencies** | LBO-002 | **Pass** | Leverage stated | **Fail** | 90% leverage on cyclical without flag | **Difficulty** | L3 |

### LBO-004: Project 5-Year FCF Under PE Ownership
| **Dependencies** | M3-017, LBO-003 | **Pass** | FCF from model not reinvented | **Fail** | Ignores capex maintenance | **Difficulty** | L3 |

### LBO-005: Model Debt Paydown from FCF
| **Dependencies** | LBO-004 | **Pass** | Debt schedule ties | **Fail** | Interest not cash swept | **Difficulty** | L3 |

### LBO-006: Set Exit EV/EBITDA Year 5
| **Dependencies** | COMP-006 | **Pass** | Exit multiple bounded | **Fail** | Exit > entry without growth case | **Difficulty** | L2 |

### LBO-007: Calculate IRR and MOIC
| **Dependencies** | LBO-005, LBO-006 | **Pass** | IRR verified in Python | **Fail** | Manual IRR error | **Difficulty** | L3 |

### LBO-008: Entry vs Exit Multiple Sensitivity
| **Dependencies** | LBO-007 | **Pass** | IRR grid produced | **Fail** | Single scenario | **Difficulty** | L2 |

### LBO-009: Assess LBO Feasibility
| **Description** | FCF stability, capex intensity, cyclicality assessment. | **Dependencies** | LBO-007, M3-017 | **Pass** | Feasibility memo with constraints | **Fail** | Declares LBO on negative FCF name | **Difficulty** | L2 | **Sectors** | PEP, MCD, CMCSA |

### LBO-010: Compare LBO Implied Price to DCF
| **Dependencies** | LBO-007, DCF-012 | **Pass** | Triangulation comment | **Fail** | Ignores 50% dispersion | **Difficulty** | L2 |

---

# Layer 2E — Sum-of-the-Parts (9 tasks)

### SOTP-001: Map Segments to Valuation Buckets
| **Dependencies** | segment note | **Pass** | All reportable segments mapped | **Fail** | Missing segment | **Difficulty** | L2 | **Sectors** | GOOGL, AMZN, DIS, CMCSA |

### SOTP-002: Assign Peer Set per Segment
| **Dependencies** | SOTP-001, D-015 | **Pass** | Distinct peers per segment | **Fail** | Same comp set for cloud and retail | **Difficulty** | L3 |

### SOTP-003: Value Segment A (EV/EBITDA)
| **Dependencies** | SOTP-002, segment financials | **Pass** | Segment EBITDA normalized | **Fail** | Unallocated costs ignored | **Difficulty** | L3 |

### SOTP-004: Value Segment B (Different Multiple)
| **Dependencies** | SOTP-002 | **Pass** | Multiple appropriate to segment growth | **Fail** | Single multiple all segments | **Difficulty** | L3 |

### SOTP-005: Apply Holdco Discount
| **Dependencies** | SOTP-003, SOTP-004 | **Pass** | Discount 0–25% with rationale | **Fail** | No discount on unrelated segments | **Difficulty** | L2 | **Reward** | L2 |

### SOTP-006: Allocate Corporate Overhead
| **Dependencies** | FS-023 | **Pass** | Overhead removed from segments | **Fail** | Double-counted | **Difficulty** | L3 |

### SOTP-007: Sum to EV → Equity → Per Share
| **Dependencies** | SOTP-003–006, D-019 | **Pass** | Arithmetic correct | **Fail** | Net debt omitted | **Difficulty** | L2 |

### SOTP-008: Compare SOTP to Consolidated DCF
| **Dependencies** | SOTP-007, DCF-012 | **Pass** | Explains premium/discount | **Fail** | Ignores divergence | **Difficulty** | L2 |

### SOTP-009: Flag Hidden / Unlisted Value
| **Description** | Identify undisclosed subsidiaries (Waymo, etc.). | **Dependencies** | SOTP-001 | **Pass** | Flags unmodeled value | **Fail** | Assigns value without disclosure | **Difficulty** | L2 | **Reward** | L3 |

---

# Layer 2F — Dividend Discount Model (7 tasks)

### DDM-001: Extract 10-Year Dividend History
| **Dependencies** | CF, dividend footnote | **Pass** | DPS series correct | **Fail** | Special dividend not flagged | **Difficulty** | L1 | **Sectors** | PEP, KO, MCD |

### DDM-002: Compute Payout vs FCF and EPS Coverage
| **Dependencies** | DDM-001, M3-014, M3-017 | **Pass** | Coverage ratios calculated | **Fail** | Uses EPS only ignoring FCF | **Difficulty** | L2 |

### DDM-003: Project Dividend Growth 5 Years
| **Dependencies** | DDM-001, M3-014 | **Pass** | Growth bounded vs history | **Fail** | 15% DPS growth forever | **Difficulty** | L2 |

### DDM-004: Calculate Cost of Equity (CAPM)
| **Dependencies** | DCF-001 | **Pass** | Same Ke methodology as DCF | **Fail** | Different Ke unexplained | **Difficulty** | L2 |

### DDM-005: Run Gordon or Multi-Stage DDM
| **Dependencies** | DDM-003, DDM-004 | **Pass** | Intrinsic value calculated | **Fail** | g ≥ Ke | **Difficulty** | L3 |

### DDM-006: Dividend Sustainability Stress Test
| **Description** | Model −20% FCF scenario; can dividend be maintained? | **Dependencies** | DDM-002, M3-018 | **Pass** | Stress outcome stated | **Fail** | Ignores payout risk (**mandate**) | **Difficulty** | L3 |

### DDM-007: Compare Yield to Peer Income Names
| **Dependencies** | DDM-001, COMP-001 | **Pass** | Relative yield table | **Fail** | Wrong peer set | **Difficulty** | L2 |

---

# Layer 2G — M&A Accretion/Dilution (4 tasks)

### MA-001: Model Pro Forma Combined IS
| **Dependencies** | M3-001, target IS | **Pass** | Combination mechanics correct | **Fail** | Double-counts revenue | **Difficulty** | L3 | **Sectors** | Media M&A |

### MA-002: Synergy Assumptions with Timing
| **Dependencies** | MA-001 | **Pass** | Synergies phased | **Fail** | Day-1 full synergies | **Difficulty** | L3 |

### MA-003: Compute EPS Accretion/Dilution
| **Dependencies** | MA-001, MA-002 | **Pass** | Accretion % in Y1 and Y2 | **Fail** | Wrong share count | **Difficulty** | L3 |

### MA-004: Deal Sources & Uses / Financing
| **Dependencies** | MA-003 | **Pass** | S&U balances | **Fail** | Unfunded purchase price | **Difficulty** | L3 |

---

# Layer 3 — Valuation Synthesis (6 tasks)

### VAL-001: Build Football Field Chart
| **Description** | Combine DCF, comps, SOTP, LBO ranges on one chart. | **Dependencies** | ≥2 of DCF-012, COMP-007, SOTP-007, LBO-007 | **Pass** | All methods shown with ranges | **Fail** | Single method only | **Difficulty** | L2 |

### VAL-002: Assign Methodology Weights
| **Description** | Weight each method for blended target. | **Dependencies** | VAL-001 | **Pass** | Weights sum to 100%; rationale | **Fail** | Equal weights without thought | **Difficulty** | L2 | **Reward** | L2 |

### VAL-003: Set 12-Month Price Target with Range
| **Dependencies** | VAL-002 | **Pass** | Bull/base/bear stated | **Fail** | Point target only | **Difficulty** | L2 |

### VAL-004: Compute Upside/Downside to Current
| **Dependencies** | VAL-003, market price | **Pass** | Return calc with date | **Fail** | Wrong denominator | **Difficulty** | L1 |

### VAL-005: Reconcile Wide Valuation Dispersion
| **Description** | Explain if methods diverge >30%. | **Dependencies** | VAL-001 | **Pass** | Identifies driver of spread | **Fail** | Ignores dispersion | **Difficulty** | L2 | **Reward** | L2 |

### VAL-006: Update Target Post-Model Refresh
| **Dependencies** | VAL-003, EARN-008 | **Pass** | Revision tied to model change | **Fail** | PT unchanged despite 10% EPS change | **Difficulty** | L2 |

---

# Layer 4 — Industry Analysis (9 tasks)

### IND-001: Porter's Five Forces Analysis
| **Outputs** | Forces memo with evidence | **Difficulty** | L2 | **Reward** | L2 |

### IND-002: TAM/SAM/SOM Sizing
| **Inputs** | IR decks, industry reports (bounded) | **Pass** | Ranges not point estimates | **Difficulty** | L2 |

### IND-003: Market Share Trends
| **Dependencies** | D-016, D-006 | **Pass** | Share calc methodology stated | **Difficulty** | L2 |

### IND-004: Pricing Power Analysis
| **Dependencies** | FS-013, margin trends | **Pass** | Links margins to pricing | **Difficulty** | L2 | **Sectors** | Consumer |

### IND-005: Regulatory Overlay
| **Pass** | Identifies sector-specific regulation | **Difficulty** | L2 | **Sectors** | Tech antitrust, media content regs |

### IND-006: Disruption Risk Matrix
| **Pass** | AI/streaming/DTC threats assessed | **Difficulty** | L2 | **Sectors** | Tech, Media |

### IND-007: Commodity / Input Cost Sensitivity
| **Dependencies** | FRED commodities, M3-005 | **Pass** | Quantified sensitivity | **Difficulty** | L3 | **Sectors** | PEP, KO, MDLZ |

### IND-008: Capital Intensity / ROIC vs Peers
| **Dependencies** | FS-024, COMP-001 | **Pass** | ROIC comparison table | **Difficulty** | L3 |

### IND-009: Industry Cycle Positioning
| **Pass** | Early/mid/late cycle call with evidence | **Difficulty** | L2 | **Reward** | L2 |

---

# Layer 5 — Earnings Workflow (12 tasks)

### EARN-001: Pre-Earnings Preview Note
| **Timing** | T−5 to T−1 | **Outputs** | Expected KPIs, key debates | **Difficulty** | L2 |

### EARN-002: Extract Consensus Expectations
| **Pass** | Source cited or flagged unavailable | **Fail** | Fabricated consensus | **Difficulty** | L2 | **Reward** | L3 |

### EARN-003: Identify Key KPIs to Watch
| **Examples** | NFLX subs, AMZN AWS growth, MCD comps | **Difficulty** | L2 |

### EARN-004: Real-Time Earnings Recap
| **Timing** | T+0 | **Outputs** | Headline beats/misses | **Difficulty** | L2 |

### EARN-005: Compare Actual vs Preview
| **Dependencies** | EARN-001, EARN-004 | **Pass** | Variance explained | **Difficulty** | L2 |

### EARN-006: Extract Guidance Raise/Lower/Maintain
| **Dependencies** | D-011 | **Pass** | Direction correct with quote | **Difficulty** | L2 |

### EARN-007: Guidance Drift — Call vs Subsequent 10-Qs
| **Description** | Cross-reference qualitative Q2 guidance to Q3/Q4 actuals. | **Dependencies** | D-011, D-003, D-012 | **Pass** | Drift quantified with citations (**MVD**) | **Fail** | Confuses guidance with actuals | **Difficulty** | L3 |

### EARN-008: Update Model for New Quarter Actuals
| **Dependencies** | M3-001–017, EARN-004 | **Pass** | Model refreshed; still balances | **Difficulty** | L3 |

### EARN-009: Revise Price Target Post-Earnings
| **Dependencies** | VAL-003, EARN-008 | **Pass** | PT change linked to model delta | **Difficulty** | L2 |

### EARN-010: Identify Estimate Revision Catalyst
| **Outputs** | Catalyst list for next quarter | **Difficulty** | L2 |

### EARN-011: Management Tone Change Assessment
| **Inputs** | Current vs prior transcript | **Pass** | Specific quote comparisons | **Difficulty** | L2 | **Reward** | L2 |

### EARN-012: Press Release Non-GAAP vs 10-Q GAAP
| **Dependencies** | D-022, FS-001 | **Pass** | Differences reconciled | **Difficulty** | L2 |

---

# Layer 6 — Investment Thesis (10 tasks)

### TH-001: State Variant Perception vs Consensus
| **Reward** | L2 | **Difficulty** | L3 |

### TH-002: Bull Case — Three Pillars
| **Pass** | Each pillar evidence-based | **Difficulty** | L2 |

### TH-003: Bear Case — Three Pillars
| **Pass** | Risks not generic boilerplate | **Difficulty** | L2 |

### TH-004: Base Case Probability Weight
| **Pass** | Weights sum to 100% | **Difficulty** | L2 |

### TH-005: Three Near-Term Catalysts with Dates
| **Pass** | Dated catalysts | **Fail** | Vague "potential growth" | **Difficulty** | L2 |

### TH-006: Moat Assessment
| **Pass** | Uses framework (network, scale, brand, switching) | **Difficulty** | L2 | **Reward** | L2 |

### TH-007: Management Quality Assessment
| **Inputs** | Proxy, guidance track record (EARN-007) | **Difficulty** | L2 |

### TH-008: Capital Allocation Scorecard
| **Pass** | Buyback, M&A, dividend, reinvestment scored | **Difficulty** | L2 |

### TH-009: Buy / Hold / Sell Recommendation
| **Dependencies** | VAL-003, RISK-001, CPL-001–010 | **Pass** | Rec aligns with valuation + risk | **Difficulty** | L3 |

### TH-010: Two-Sentence PM Summary
| **Pass** | Concise, accurate, compliant | **Difficulty** | L2 |

---

# Layer 7 — Risk & Special Situations (10 tasks)

### RISK-001: Top 5 Company-Specific Risks
| **Dependencies** | FS-016, IND-006 | **Difficulty** | L2 |

### RISK-002: Liquidity / Solvency Analysis
| **Outputs** | Current ratio, net debt/EBITDA | **Dependencies** | D-019, D-007 | **Difficulty** | L2 |

### RISK-003: Customer Concentration
| **Inputs** | 10-K risk factors / footnote | **Difficulty** | L2 |

### RISK-004: Legal Contingencies Quantification
| **Dependencies** | contingencies note | **Difficulty** | L3 |

### RISK-005: China / Geopolitical Exposure
| **Inputs** | Geographic revenue | **Difficulty** | L2 | **Sectors** | AAPL, PEP |

### RISK-006: Refinancing Wall Chart
| **Dependencies** | FS-015 | **Difficulty** | L2 |

### RISK-007: Downside Case Price (−30% Scenario)
| **Dependencies** | M3-018, VAL-003 | **Difficulty** | L3 |

### RISK-008: ESG Mandate Exclusion Flag
| **Difficulty** | L2 | **Reward** | L3 | **Phase** | 2 optional |

### RISK-009: Activist Situation (13D)
| **Dependencies** | D-021 | **Difficulty** | L3 |

### RISK-010: Spin-Off / Restructuring Tracking
| **Dependencies** | D-021, 8-K | **Difficulty** | L3 | **Sectors** | WBD, DIS |

---

# Layer 8 — Compliance (10 tasks)

*Prefix `CPL-` (compliance) — distinct from trading comps `COMP-`.*

### CPL-001: Separate Fact from Opinion
| **Pass** | Labels on thesis vs data | **Fail** | Opinion stated as fact | **Reward** | L3 | **FINRA**

### CPL-002: No Guaranteed Return Language
| **Fail examples** | "Will reach $200" | **Reward** | L3 veto |

### CPL-003: Risk of Loss Disclosure Present
| **Pass** | Standard disclosure block | **FINRA**

### CPL-004: Price Target Disclaimer
| **Pass** | PT labeled as estimate | **FINRA**

### CPL-005: Long-Only Mandate — No Short Language
| **Fail** | "Short this stock" | **Mandate** | long_only_equity |

### CPL-006: Conservative Income — Dividend Risk Disclosed
| **Dependencies** | DDM-006 | **Mandate** | conservative_income |

### CPL-007: No Speculative Language Without Bounds
| **Dependencies** | DCF-007, DCF-013 | **Mandate** | no_speculative_language |

### CPL-008: Cite All Material Data Points
| **Dependencies** | D-024 | **Reward** | L3 |

### CPL-009: Flag Unverified Data Explicitly
| **Dependencies** | DCF-017 | **Fail** | Silent interpolation | **Reward** | L3 |

### CPL-010: Past Performance Disclaimer if Cited
| **Pass** | Disclaimer when citing returns | **FINRA**

---

# Layer 9 — Output Assembly (1 task)

### OUT-001: Assemble Full Initiation Report
| Field | Detail |
|-------|--------|
| **Description** | Compile all sections into structured initiation report: business overview, industry, financials, model summary, valuation football field, thesis, risks, recommendation, disclosures. |
| **Inputs** | Outputs from D, FS, M3, DCF, COMP, IND, TH, RISK, CPL tasks |
| **Outputs** | `investment_memo_v1` structured document |
| **Dependencies** | TH-009, VAL-001, RISK-001, CPL-001–010 |
| **Tools** | `Compliance_Linter`, document assembler |
| **Pass** | All required sections present; passes compliance lint; citations complete |
| **Fail** | Missing section; FINRA violation; no recommendation |
| **Difficulty** | L3 |
| **Reward** | L1, L2, L3 |
| **Type** | Type C — full coverage benchmark |

---

## Appendix A — Task Count Verification

| Prefix | Count |
|--------|-------|
| D- | 24 |
| FS- | 24 |
| M3- | 20 |
| DCF- | 17 |
| COMP- | 12 |
| LBO- | 10 |
| SOTP- | 9 |
| DDM- | 7 |
| MA- | 4 |
| VAL- | 6 |
| IND- | 9 |
| EARN- | 12 |
| TH- | 10 |
| RISK- | 10 |
| CPL- | 10 |
| OUT- | 1 |
| **Total** | **185** |

---

## Appendix B — Eval Unit Packaging (185 → Benchmark Releases)

| Release | Tasks included | Count |
|---------|----------------|-------|
| v0.1 MVD | FS-004, EARN-007, FS-012 bundles × 15 cos | 45 |
| v0.2 | M3-001–M3-020 per sector sample | +45 |
| v0.3 | DCF-001–017 + COMP-001–012 bundles | +45 |
| v0.4 | LBO, SOTP, DDM, MA subsets | +30 |
| v0.5 | OUT-001 full initiation chains | +20 |
| **Total catalog** | | **185** |

---

*All 185 tasks defined. Compliance prefix standardized to `CPL-`. Trading comps remain `COMP-`.*
