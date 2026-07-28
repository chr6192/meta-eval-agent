# Legal Analysis: Software Services Agreement

**Contract No.:** SSA-2024-09172
**Effective Date:** September 15, 2024
**Parties:** Pinnacle Digital Solutions, Inc. ("Provider") and GreenLeaf Enterprises, LLC ("Client")

---

## 1. Key Dates and Deadlines

| Date(s) | Event / Milestone |
|---|---|
| **September 15, 2024** | Effective Date; Agreement executed by both Parties |
| **September 15, 2024** | Commencement of Requirements Gathering Phase |
| **September 30, 2024** | First payment installment due ($360,000 — upon execution) |
| **November 30, 2024** | End of Requirements Gathering Phase |
| **December 1, 2024** | Start of Design and Architecture Phase |
| **January 31, 2025** | End of Design and Architecture Phase |
| **February 1, 2025** | Start of Development Phase 1 (Core Modules) |
| **February 15, 2025** | Second payment installment due ($360,000 — upon Design & Architecture completion) |
| **May 31, 2025** | End of Development Phase 1 |
| **June 1, 2025** | Start of Development Phase 2 (Integration & Testing) |
| **June 15, 2025** | Third payment installment due ($600,000 — upon Dev Phase 1 completion) |
| **August 31, 2025** | End of Development Phase 2 |
| **September 1, 2025** | Start of User Acceptance Testing (UAT) |
| **September 15, 2025** | Fourth payment installment due ($480,000 — upon Dev Phase 2 completion) |
| **October 15, 2025** | End of UAT period |
| **November 1, 2025** | Production Deployment date; Fifth payment installment due ($360,000 — upon successful UAT) |
| **November 1, 2025** | Start of Post-Launch Support Period |
| **April 30, 2026** | End of Post-Launch Support Period |
| **May 15, 2026** | Final payment installment due ($240,000 — upon conclusion of Post-Launch Support) |

**Additional Deadline Notes:**
- **30-day milestone grace period:** If Provider misses any milestone by more than 30 calendar days, Client may demand a remediation plan within 10 business days or terminate for cause (§2.3).
- **30-day invoice payment window:** All invoices are payable within 30 days of receipt (§3.2).
- **48-hour breach notification:** Provider must notify Client of any data breach within 48 hours of discovery (§6.2).
- **60-day termination for convenience:** Either party may terminate with 60 days' written notice (§9.1).
- **30-day cure period for termination for cause:** The breaching party has 30 days to cure after written notice (§9.2).
- **5-year confidentiality survival:** Confidentiality obligations survive for 5 years after termination (§5.3).
- **12-month warranty period:** Custom Work Product must conform to specifications for 12 months after final acceptance (§7.1).
- **12-month non-solicitation period:** Neither party may solicit the other's employees for 12 months after termination (§11.6).
- **90-day force majeure limit:** Delays due to force majeure are excused for up to 90 days (§11.1).

---

## 2. Party Obligations

### Provider (Pinnacle Digital Solutions, Inc.)

| Obligation | Section |
|---|---|
| Design, develop, and deploy a custom ERP platform (inventory, orders, financial reporting, CRM) | §1.1 |
| Adhere to the specifications, milestones, and deliverables in Exhibit A (Statement of Work) | §1.2 |
| Assign a dedicated project manager as primary point of contact | §1.3 |
| Meet all milestone deadlines (with 30-day grace period) | §2.2–§2.3 |
| Implement safeguards compliant with CCPA, GDPR (where applicable), and SOC 2 Type II standards | §6.1 |
| Notify Client of data breaches within 48 hours | §6.2 |
| Conduct annual third-party security audits; share results with Client upon request | §6.3 |
| Perform Services in a professional and workmanlike manner consistent with industry standards | §7.1(i) |
| Ensure Custom Work Product materially conforms to Exhibit A specifications for 12 months post-acceptance | §7.1(ii) |
| Warrant that Custom Work Product does not infringe third-party IP rights | §7.1(iii) |
| Grant Client perpetual, non-exclusive, royalty-free license to Provider Tools incorporated into deliverables | §4.2 |
| Indemnify Client for claims arising from Provider's breach of warranties, IP infringement by deliverables, or Provider's gross negligence/willful misconduct | §8.3 |
| Hold Client's Confidential Information in strict confidence and use only for performance purposes | §5.2 |
| Deliver all completed and in-progress work product upon termination | §9.3(ii) |
| Return or destroy Client's Confidential Information within 30 days upon termination | §9.3(iii) |
| Refrain from soliciting Client's employees during the engagement and for 12 months after | §11.6 |

### Client (GreenLeaf Enterprises, LLC)

| Obligation | Section |
|---|---|
| Pay total fixed fee of $2,400,000 per the installment schedule | §3.1 |
| Pay invoices within 30 days of receipt | §3.2 |
| Provide reasonable access to systems, personnel, and information for Provider to perform Services | §7.2 |
| Warrant authority to enter into the Agreement | §7.2 |
| Obtain Client's full payment before IP ownership transfers to Client (§4.1) | §4.1 |
| Not reverse-engineer, decompile, or disassemble Provider Tools without written consent | §4.3 |
| Hold Provider's Confidential Information in strict confidence | §5.2 |
| Indemnify Provider for third-party claims arising from Client's violation of the Agreement or applicable law | §8.4 |
| Return or destroy Provider's Confidential Information within 30 days upon termination | §9.3(iii) |
| Refrain from soliciting Provider's employees during the engagement and for 12 months after | §11.6 |
| Permit one annual Client-conducted security audit of Provider's systems with 30 days' notice | §6.3 |

---

## 3. Risks and Concerns

### Risks for Provider (Pinnacle Digital Solutions, Inc.)

| # | Risk / Concern | Detail | Severity |
|---|---|---|---|
| 1 | **Fixed-fee structure with no scope-change mechanism** | The $2.4M is a fixed fee with no explicit change-order process or cost escalation provisions. Scope creep or Client-requested additions are not addressed, creating financial exposure. | 🔴 High |
| 2 | **IP ownership conditional on full payment** | Custom Work Product ownership transfers only "upon full payment of all fees owed." If Client disputes or withholds final payments, Provider may face IP disputes while still performing. Conversely, Client may leverage non-payment as a negotiation tactic. | 🟡 Medium |
| 3 | **10% retainage on every milestone** | Client may withhold up to 10% of each payment as retainage, creating ongoing cash-flow pressure. Combined with the 30-day invoice payment window, this reduces effective cash flow significantly. | 🟡 Medium |
| 4 | **Strict milestone penalties** | Missing a milestone by 30+ days gives Client the right to terminate for cause (§2.3, §9.2). No reciprocal penalty exists if Client delays deliverables or approvals. | 🔴 High |
| 5 | **Broad force majeure exclusion** | Force majeure (§11.1) does not explicitly cover supply-chain issues, key-person unavailability, or subcontractor failures — all common risks in software development. | 🟡 Medium |
| 6 | **No payment delay cure period for Provider** | Late payments accrue interest at 1.5%/month, but Provider has no termination right specifically for non-payment (only general termination for cause under §9.2 after 30-day cure). | 🟡 Medium |
| 7 | **Texas arbitration and governing law** | Arbitration is mandated in Austin, Texas — a significant geographic and cost disadvantage for the California-based Client, but neutral/favorable for the Texas-based Provider. | — |
| 8 | **Liability cap at total contract fees** | Provider's aggregate liability is capped at $2.4M (total fees), which is reasonable, but the carve-outs for IP, confidentiality, and data protection mean unlimited liability for those areas. | 🟡 Medium |

### Risks for Client (GreenLeaf Enterprises, LLC)

| # | Risk / Concern | Detail | Severity |
|---|---|---|---|
| 1 | **Termination for convenience — no penalty protection** | Either party may terminate with 60 days' notice (§9.1). If Provider terminates early, Client has no guaranteed penalty or refund, and may have sunk costs without deliverables. | 🔴 High |
| 2 | **IP ownership contingent on full payment** | If Client encounters cash flow issues and cannot make final payments, Provider retains ownership of all Custom Work Product. This could leave Client with an unusable system. | 🔴 High |
| 3 | **Liability cap limits Client recovery** | Client's aggregate damages are capped at total fees paid/payable ($2.4M), excluding IP, confidentiality, and data protection breaches. For a critical ERP system, consequential damages (e.g., business interruption) are excluded — potentially far exceeding $2.4M. | 🔴 High |
| 4 | **No explicit SLA or uptime guarantee** | The warranty (§7.1) covers "material conformance" for 12 months, but there is no service-level agreement defining performance standards, uptime requirements, or response times. | 🟡 Medium |
| 5 | **Limited security audit rights** | Client can conduct only one audit per calendar year with 30 days' notice (§6.3). This is a relatively low frequency for a critical system handling sensitive data. | 🟡 Medium |
| 6 | **Texas forum for dispute resolution** | Arbitration and governing law are in Texas, a home-court advantage for Provider and an additional cost/convenience burden for the California-based Client. | 🟡 Medium |
| 7 | **Exhibit A not included** | The Statement of Work (Exhibit A) referenced in §1.2 and §7.1 is critical for defining scope, specifications, and acceptance criteria but is not present in the extracted document. Its absence is a significant gap. | 🔴 High |
| 8 | **No data ownership/return clause** | The contract addresses confidentiality but does not explicitly address ownership of Client data processed by Provider or data return/deletion upon termination — a gap for CCPA/GDPR compliance. | 🟡 Medium |
| 9 | **Post-launch support scope undefined** | The "Post-Launch Support Period" (Nov 2025–Apr 2026) is mentioned in milestones but lacks defined scope, response times, or deliverables. What level of support is guaranteed? | 🟡 Medium |

### General Concerns for Both Parties

| Concern | Detail |
|---|---|
| **Missing Exhibit A (Statement of Work)** | The contract extensively references Exhibit A for detailed specifications, milestones, and deliverables (§1.2, §7.1). Its absence makes key obligations indeterminate. |
| **No insurance requirements** | Neither party is required to maintain any specific insurance coverage (e.g., professional liability, cyber liability, general liability). |
| **Non-solicitation is one-sided in effect** | While stated as mutual (§11.6), Provider (a services firm with employees directly involved) is more likely to be the target of solicitation by Client, making this provision more impactful on Provider. |
| **No explicit warranty period for Provider Tools** | While Custom Work Product has a 12-month warranty, the perpetual license to Provider Tools has no quality assurance or update/maintenance commitment. |
| **Force majeure 90-day limit lacks remedy** | If force majeure exceeds 90 days, the contract does not specify what happens — automatic termination? renegotiation? This gap could lead to disputes. |

---

## 4. Financial Summary

### Total Contract Value

| Item | Amount |
|---|---|
| **Total Fixed Fee** | **$2,400,000** |

### Payment Schedule

| Installment | Amount | Trigger / Condition | Due Date | Cumulative % |
|---|---|---|---|---|
| 1 | $360,000 | Upon execution of Agreement | September 30, 2024 | 15.0% |
| 2 | $360,000 | Completion of Design & Architecture Phase | February 15, 2025 | 30.0% |
| 3 | $600,000 | Completion of Development Phase 1 | June 15, 2025 | 55.0% |
| 4 | $480,000 | Completion of Development Phase 2 | September 15, 2025 | 75.0% |
| 5 | $360,000 | Successful completion of UAT | November 1, 2025 | 90.0% |
| 6 | $240,000 | Conclusion of Post-Launch Support | May 15, 2026 | 100.0% |

### Financial Conditions

| Condition | Detail |
|---|---|
| **Invoice Payment Terms** | Payable within 30 days of receipt (§3.2) |
| **Late Payment Interest** | 1.5% per month (18% annually), or the maximum rate permitted by law, whichever is less (§3.2) |
| **Retainage** | Client may withhold up to 10% of each milestone payment; released upon final acceptance of the complete deliverable set (§3.3) |
| **Termination Payment** | Upon termination, Client pays for all Services "satisfactorily performed" through the termination date (§9.3(i)) |
| **IP Ownership Trigger** | Custom Work Product ownership transfers only upon full payment of all fees (§4.1) |

### Financial Risk Assessment

- **Provider perspective:** The front-loaded payments (30% by Feb 2025) provide reasonable cash flow in the early stages, but the 10% retainage could reduce effective payments to 90% per milestone ($2,160,000 effectively received before final release of retainage). The final 10% ($240,000) is not due until May 2026 — approximately 8 months after deployment, creating a receivables risk.
- **Client perspective:** Client does not pay the full 90% until November 2025 (after UAT), which provides leverage. However, 75% of the total ($1.8M) is committed before production deployment. The retainage mechanism provides some protection, but 10% per milestone is relatively modest. The late payment interest rate of 1.5%/month (18% APR) is on the higher end.
- **Net effective payment to Provider:** Due to 10% retainage, Provider effectively receives $2,160,000 during milestones, with $240,000 in retainage released at final acceptance plus the final $240,000 milestone payment due May 2026.

---

*This analysis is provided for informational purposes only and does not constitute legal advice. Parties should consult qualified legal counsel before relying on this analysis for decision-making.*
