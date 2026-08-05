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
| LuxTrust outage, 2025-12-16 | significant | out of scope, Art. 2(6) | trust services stay under IR |
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

## 5. A data error this work found and fixed

Working through Art. 2(6) surfaced a discrepancy in our own data, since **resolved against the Official Journal text**.

`ir_incident_thresholds.json` classed **fourteen** entity types as governed by IR (EU) 2024/2690. Article 1 of that regulation names **eleven**:

> *"This Regulation, with regard to DNS service providers, TLD name registries, cloud computing service providers, data centre service providers, content delivery network providers, managed service providers, managed security service providers, providers of online market places, of online search engines and of social networking services platforms, and trust service providers (the relevant entities)…"*

Articles 5 to 14 cover exactly those eleven (Article 10 covers managed service providers and managed security service providers together). **No article covers IXPs or electronic communications providers.**

The three extras were `ixp_operator`, `public_ecn_provider` and `public_ecs_provider`, and the error mattered twice over. It routed telecom operators and IXPs to IR thresholds that do not apply to them. And under N26 it excluded them from the regime entirely via Art. 2(6) — on the first run of this analysis it did exactly that, silently marking POST and Tango "out of scope" and hiding the largest change in the draft.

Fixed:

| | |
|---|---|
| `ir_incident_thresholds.json` | the three removed, with the Art. 1 citation recorded in `scope_note` |
| `lu_n26.py` | `ir_scope()` now follows Art. 1, not our entity list |
| `curated_lu_incidents.json` | LU-06 (IXP) and LU-21 (POST) re-routed from `ir_thresholds` to `nis2_ml` |

LU-06 predates this work, so the error was pre-existing rather than introduced here.

**A consequence worth noting.** With IR correctly scoped, Luxembourg has no implemented rule for electronic communications providers: the applicable national text is ILR/N23/3, which CyberScale does not implement and which this draft also abrogates. Telecom therefore falls to the general model today and would fall to N26's generic criteria tomorrow.

### Does `contextual_train.csv` need updating?

Checked, because the fix moves those three entity types from tier 1 (IR deterministic) to tier 3 (the ML model) in `entity_incident.py`. The model is now answerable for them where it previously was not.

**No correction is needed.** The 440 rows covering them are labelled consistently with their sector rather than with IR logic:

| Group | rows | Critical | High | Medium | Low |
|---|---:|---:|---:|---:|---:|
| the three moved to ML | 440 | 32.5% | 30.0% | 21.4% | 16.1% |
| all `digital_infrastructure` | 1,289 | 33.9% | 28.2% | 22.7% | 15.1% |
| the eleven that stay IR-routed | 3,678 | 32.6% | 24.6% | 22.4% | 20.4% |
| everything already ML-routed | 27,882 | 23.9% | 25.0% | 25.4% | 25.7% |

They track `digital_infrastructure` closely, which is their actual sector, and all 440 are sectored correctly. Had the generator treated them as IR entities the distribution would look different from the sector baseline; it does not.

**Coverage is thin, though.** Across the 48 entity types that now route to the ML model, the median is 299.5 rows. These three carry 145, 140 and 155 — roughly half, though comfortably above the minimum of 87. Not a blocker, and not a reason to retrain on its own; worth topping up whenever a retrain happens for other reasons, since these three just became load-bearing.

**N26 implies no training change either.** The draft governs *significance* determination, which is a deterministic threshold layer. The contextual model predicts *severity*. The two are separate outputs and N26 does not touch the second.

Two housekeeping notes from the same check, both since resolved. The file existed as byte-identical copies under `data/training/contextual/` and `training/data/contextual/`; the untracked one was removed and `data/training/contextual/README.md` now disambiguates the three schema generations that share similar names. And the file has 32,000 logical rows rather than the 47,470 a line count suggests, because `input_text` contains embedded newlines — worth knowing before sizing it.

> **Correction, 2026-08-05.** The coverage figures above were computed on `contextual_train.csv`, the **v3** corpus. The deployed model was never trained on it: the v3 retrain was reverted in `575c625`, so `data/models/contextual/` is v2-era, and v2 carries **8** entity types against v3's 59, with zero overlap. The three re-routed types therefore have *no* representation in the model now answering for them — not the 145 / 140 / 155 rows counted here. The row-level conclusion still holds of the corpus a retrain would use (v4, which reproduces v3's 59-type vocabulary); it says nothing about what is deployed today. Tracked as `BACKLOG.md` D8, and `contextual_train.csv` has since been removed — v4 is byte-reproducible from published inputs.

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
