# CyberScale — impact of ILR consultation CP/N26/2

ILR has opened a public consultation on a draft règlement **ILR/N26/X** setting the modalities and criteria for notifying incidents having an *important impact*, under articles 14(1) and 14(3) of the **loi du 5 mai 2026**.

Article 5 of the draft abrogates eleven NIS1-era ILR regulations. **CyberScale implements nine of them.** The entire Luxembourg national threshold layer rests on text this draft replaces.

**Status:** the draft is in consultation and not in force. Nothing here changes CyberScale's default behaviour — `lu.py` still implements the regulations that currently apply. `lu_n26.py` sits alongside it so the impact can be measured now rather than after adoption.

Source: `00_Inbox/PDF/ilr-niss-cp-2026-07-06-notification_incident.pdf` (5 pages, no annexes).

---

## 1. What CyberScale loses

| Abrogated | Subject | In CyberScale |
|---|---|---|
| ILR/N19/1 | fixation des services essentiels | no |
| ILR/N21/1 | fournisseurs de services numériques | **yes** |
| ILR/N21/2 | eau potable | **yes** |
| ILR/N22/1 | transport ferroviaire | **yes** |
| ILR/N22/2 | transport routier | **yes** |
| ILR/N22/3 | énergie — gaz | **yes** |
| ILR/N22/4 | énergie — électricité | **yes** |
| ILR/N22/5 | santé | **yes** |
| ILR/N22/6 | infrastructure numérique | **yes** |
| ILR/N23/1 | transport aérien | **yes** |
| ILR/N23/3 | communications électroniques | no |

`lu_thresholds.json` describes its own source as *"ILR NIS1 transposition (Règlements ILR)"*. That is exactly the body of text being withdrawn. Every `_assess_energy_electricity`, `_assess_transport_rail`, `_assess_health_hospital` and sibling in `lu.py` implements an abrogated regulation, and every `expected_ilr_reference` in `curated_lu_incidents.json` points at one.

## 2. What replaces it

A single generic article. **Art. 2(1) lists twelve criteria; any one triggers notification**, and none of them is sector-specific:

| | Criterion | Threshold |
|---|---|---|
| a | service partially or totally inaccessible | **> 1 hour**, or **> 5%** of that service's users in LU |
| b | unauthorised access, suspected malicious, liable to cause serious disruption | judgement |
| c | impact on authenticity / integrity / confidentiality | **> 50 users** in LU |
| d | exfiltration of trade secrets | any |
| e | cross-border or international impact | any |
| f | physical access to infrastructure compromised | any |
| g | risk to public safety, security or health | any |
| h | considerable damage to a person's health | any |
| i | death of a person | any |
| j | direct financial loss | **≥ EUR 500 000 or ≥ 5% of turnover, whichever is lower** |
| k | prejudice to a legal / natural person | **≥ EUR 50 000 / ≥ EUR 10 000** |
| l | criteria in the annexes | not published |

Plus: scheduled maintenance is excluded (2(2)); duration runs from disruption of *availability, authenticity, integrity or confidentiality* to restoration (2(3)); and sub-threshold incidents aggregate — **twice in six months, same root cause, collectively meeting (j)** (2(4)).

Notification: **24h preliminary** from *detection*, **72h notification** from *awareness*, **final report at one month**. Trust service providers notify at **24h, not 72** (3(5)).

## 3. What actually changes, measured

`lu_n26.py` run against the real Luxembourg incidents documented in the vault:

| Incident | In force | Under N26 | Trigger |
|---|---|---|---|
| POST nationwide outage, 2025-07-23 | significant | significant | 2(1)(a) |
| **Proximus/Tango outage, 2025-08-05** | **not significant** | **significant** | **2(1)(a)** |
| CTIE DDoS on public.lu, 2026-01-20 | not significant | below threshold | — |
| CTIE malware on MDM, 2026-02-26 | undetermined | significant | 2(1)(a) |
| LuxTrust outage, 2025-12-16 | significant | out of scope (2(6)) | — |
| arcus asbl, 2026-07-16 | undetermined | significant | 2(1)(c) |

The Tango row is the one to look at. A four-hour partial mobile degradation caused by **hardware failure, with no malicious element**, is below threshold today and notifiable under N26 — on duration alone. The RETEX recorded `nis2_significant: false`; the new (a) does not care about cause, only that service was partially inaccessible for more than an hour.

CTIE's 41-minute DDoS stays below threshold, which is the right answer under both regimes and a useful confirmation that N26 is not simply "everything notifies".

## 4. Inputs CyberScale does not have

Four criteria need fields absent from the impact taxonomy:

| Criterion | Missing field |
|---|---|
| (d) trade secrets | `trade_secret_exfiltration` |
| (f) physical access | `physical_access_compromised` |
| (j) financial loss | `direct_financial_loss_eur`, `annual_turnover_eur` |
| (k) prejudice | `prejudice_legal_person_eur`, `prejudice_natural_person_eur` |

`lu_n26.py` accepts them as optional and reports them in `not_evaluable` when absent. It never treats a missing input as "did not trigger" — that would turn a gap in our data into a clean negative, which for a notification decision is the wrong direction to be wrong in.

Criterion (l) is permanently not evaluable: the consultation draft carries no annexes, and Art. 2(5) is the route by which sector-specific thresholds could return.

## 5. A finding worth checking before responding

Working through Art. 2(6) surfaced a discrepancy in our own data.

The N26 recital quotes the title of IR (EU) 2024/2690, which names **eleven** entity types. `ir_incident_thresholds.json` classes **fourteen** as IR-governed. The three extras are **`ixp_operator`, `public_ecn_provider`, `public_ecs_provider`**.

This matters twice over. Today it routes telecom operators to IR thresholds. Under N26 it would exclude them from the regime entirely via Art. 2(6) — and on the first run of this analysis it did exactly that, silently marking POST and Tango "out of scope" and hiding the most significant change in the whole draft.

`lu_n26.py` now treats those three as **disputed**: it assesses them and reports the doubt rather than picking a side. Confirming their status against IR (EU) 2024/2690 Art. 3 is a prerequisite for trusting either the current IR routing or the N26 impact above.

## 6. Points a consultation response could raise

Offered as observations from implementing the text, not as positions.

**The (j) threshold binds hardest on the smallest entities.** *"Le montant le plus faible étant retenu"* means an entity with EUR 1 000 000 turnover notifies at EUR 50 000 of direct loss, while a large operator notifies at EUR 500 000. That is presumably deliberate, but it inverts the usual reading of a EUR 500 000 threshold.

**Criteria (j) and (k) ask for figures nobody has at 24 hours.** The preliminary notification is due 24h from *detection*. Direct financial loss, turnover percentage and prejudice valuation are post-incident accounting quantities. In practice these criteria can only be assessed at the one-month final report, by which point notification has already happened or not.

**Art. 2(4) requires state no single-incident assessment holds.** Aggregating two incidents in six months with a shared root cause needs incident history. Any tool assessing one incident at a time — CyberScale included — cannot evaluate it. `assess_recurrence()` is exposed separately for this reason, so the requirement stays visible.

**The annexes are the substance.** Art. 2(1)(l) and 2(5) let ILR reintroduce sector-specific criteria. Without them, consultation respondents are being asked about a regime whose sector dimension is undefined — and the eleven regulations being withdrawn are precisely that dimension.

**(a) and (e) are very wide.** One hour of partial degradation, or any cross-border effect, each suffice alone. For an entity with customers in the Grande Région, (e) is close to always true.

## 7. What was built

| Path | |
|---|---|
| `data/reference/lu_n26_thresholds.json` | the twelve criteria, exclusions, recurrence rule and deadlines as data |
| `src/cyberscale/national/lu_n26.py` | assessor, `assess_recurrence()`, `notification_deadlines()`, `ir_scope()` |
| `src/tests/national/test_lu_n26.py` | 14 tests, including that missing inputs read as unknown and not as negative |

Results carry `in_force: False` and a `regulation` string naming the draft, so an N26 verdict cannot be mistaken for a current-law one.

Nothing is wired into the router. Switching Luxembourg from `lu.py` to `lu_n26.py` should be a deliberate act on the date the regulation enters force, not a side effect of this work.
