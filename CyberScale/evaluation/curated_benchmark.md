# CyberScale Phase 3 — Curated Incident Benchmark

**Date:** 2026-08-05 17:39
**Dataset:** `data/reference/curated_incidents.json`
**Incidents:** 46
**Elapsed:** 0.0s

> This benchmark evaluates classification of **human-curated real-world incidents**,
> as opposed to the synthetic benchmark, which uses parametrically generated scenarios.
> Gaps between the two indicate distribution shift.

**T and O are derived deterministically**, by the same `derive_t_level()` and
`derive_o_level()` that `tools/incident.py` calls. Until 2026-08-05 this file instead
loaded the ML classifiers from `data/models/`, which v4 deprecated and production no
longer calls, and which retain MC dropout at inference: three consecutive runs on
identical data gave T 91.3 / 93.5 / 91.3 % and matrix 89.1 / 91.3 / 89.1 %. The figures
below are now fixed by the data. Run with `--compare-ml` to see the deprecated models
alongside.

**Two limitations of the dataset, stated because they bound what these numbers mean.**

The curated incidents carry no `financial_impact`, `safety_impact` or
`affected_persons_count`, so those three parameters of `derive_o_level()` sit at their
defaults and their escalation paths never fire here. That would bias O *downward* — and
it is not what the errors look like: of the 9 O mismatches, 6 are over-predictions and 3
are under-predictions. Missing fields can account for at most those 3. The dominant error
runs the other way and is not explained by the dataset.

Every T and O error is off by exactly one level; none is off by two or more.

## T-model Results

- **Accuracy:** 93.5%
- **Macro F1:** 0.9458

### Per-level F1

| Level | F1 | Support |
|-------|-----|---------|
| T1 | 1.0000 | 4 |
| T2 | 0.9333 | 16 |
| T3 | 0.9268 | 19 |
| T4 | 0.9231 | 7 |

### Confusion Matrix

| Actual \ Predicted | T1 | T2 | T3 | T4 |
|---|---|---|---|---|
| **T1** | 4 | 0 | 0 | 0 |
| **T2** | 0 | 14 | 2 | 0 |
| **T3** | 0 | 0 | 19 | 0 |
| **T4** | 0 | 0 | 1 | 6 |

## O-model Results

- **Accuracy:** 80.4%
- **Macro F1:** 0.7025

### Per-level F1

| Level | F1 | Support |
|-------|-----|---------|
| O1 | 0.9434 | 25 |
| O2 | 0.5333 | 11 |
| O3 | 0.6667 | 8 |
| O4 | 0.6667 | 2 |

### Confusion Matrix

| Actual \ Predicted | O1 | O2 | O3 | O4 |
|---|---|---|---|---|
| **O1** | 25 | 0 | 0 | 0 |
| **O2** | 3 | 4 | 4 | 0 |
| **O3** | 0 | 0 | 6 | 2 |
| **O4** | 0 | 0 | 0 | 2 |

## End-to-end Matrix Results

- **Accuracy:** 84.8%

### Classification Distribution

| Classification | Count | Pct |
|---------------|-------|-----|
| below_threshold | 4 | 8.7% |
| significant | 26 | 56.5% |
| large_scale | 10 | 21.7% |
| cyber_crisis | 6 | 13.0% |

## Per-incident Results

| ID | Incident | Expected T/O | Predicted T/O | T | O | Matrix |
|----|----------|-------------|--------------|---|---|--------|
| INC-001 | WannaCry ransomware (2017) | T4/O4 | T4/O4 | ok | ok | Cyber crisis |
| INC-002 | NotPetya destructive attack (2017) | T4/O4 | T4/O4 | ok | ok | Cyber crisis |
| INC-003 | SolarWinds Orion supply chain (2020) | T4/O3 | T3/O3 | MISS | ok | Large-scale |
| INC-004 | Irish HSE ransomware (2021) | T3/O2 | T3/O1 | ok | MISS | Significant |
| INC-005 | Colonial Pipeline ransomware (2021) | T3/O1 | T3/O1 | ok | ok | Significant |
| INC-006 | Kaseya VSA supply chain ransomware (2021 | T3/O3 | T3/O3 | ok | ok | Large-scale |
| INC-007 | Belgian MoD Log4Shell exploitation (2021 | T2/O1 | T2/O1 | ok | ok | Significant |
| INC-008 | University of Maastricht ransomware (201 | T2/O1 | T2/O1 | ok | ok | Significant |
| INC-009 | MOVEit Transfer mass exploitation (2023) | T4/O3 | T4/O4 | ok | MISS | Cyber crisis |
| INC-010 | Change Healthcare ransomware (2024) | T3/O2 | T3/O1 | ok | MISS | Significant |
| INC-011 | Norsk Hydro LockerGoga ransomware (2019) | T2/O2 | T3/O2 | MISS | ok | Large-scale |
| INC-012 | German Landkreis Anhalt-Bitterfeld ranso | T3/O2 | T3/O3 | ok | MISS | Large-scale |
| INC-013 | Düsseldorf University Hospital ransomwar | T3/O1 | T3/O1 | ok | ok | Significant |
| INC-014 | Finnish parliament email breach (2020) | T3/O1 | T3/O1 | ok | ok | Significant |
| INC-015 | EMA COVID vaccine data breach (2020) | T3/O3 | T3/O3 | ok | ok | Large-scale |
| INC-016 | Vodafone Portugal DDoS and sabotage (202 | T3/O2 | T3/O1 | ok | MISS | Significant |
| INC-017 | Costa Rica Conti ransomware (2022) | T4/O2 | T4/O3 | ok | MISS | Cyber crisis |
| INC-018 | European Parliament DDoS (2022) | T1/O1 | T1/O1 | ok | ok | Below threshold |
| INC-019 | KNP Logistics Group ransomware (2023) | T4/O1 | T4/O1 | ok | ok | Large-scale |
| INC-020 | Viasat KA-SAT modem wiper (2022) | T3/O3 | T3/O3 | ok | ok | Large-scale |
| INC-021 | JBS Foods ransomware (2021) | T2/O2 | T2/O2 | ok | ok | Significant |
| INC-022 | Montenegro government ransomware (2022) | T3/O2 | T3/O3 | ok | MISS | Large-scale |
| INC-023 | Danish railway Supeo attack (2022) | T2/O1 | T2/O1 | ok | ok | Significant |
| INC-024 | Portuguese TAP Air data breach (2022) | T3/O1 | T3/O1 | ok | ok | Significant |
| INC-025 | SAS DDoS (2023) | T2/O2 | T2/O2 | ok | ok | Significant |
| INC-026 | French hospitals ransomware series (2022 | T3/O1 | T3/O1 | ok | ok | Significant |
| INC-027 | Italian Agenzia delle Entrate LockBit cl | T2/O1 | T2/O1 | ok | ok | Significant |
| INC-028 | Austrian FMTG hotel chain ransomware (20 | T1/O1 | T1/O1 | ok | ok | Below threshold |
| INC-029 | Romanian hospital ransomware wave (2024) | T3/O2 | T3/O3 | ok | MISS | Large-scale |
| INC-030 | Barcelona Hospital Clínic ransomware (20 | T3/O1 | T3/O1 | ok | ok | Significant |
| INC-031 | Polish railway GPS spoofing (2023) | T2/O1 | T2/O1 | ok | ok | Significant |
| INC-032 | Port of Lisbon LockBit ransomware (2023) | T2/O1 | T2/O1 | ok | ok | Significant |
| INC-033 | AnyDesk supply chain breach (2024) | T2/O3 | T3/O3 | MISS | ok | Large-scale |
| INC-034 | Nordex wind turbine ransomware (2022) | T2/O2 | T2/O2 | ok | ok | Significant |
| INC-035 | Medibank data breach (2022) | T3/O1 | T3/O1 | ok | ok | Significant |
| INC-036 | German DIHK Chamber of Commerce attack ( | T3/O1 | T3/O1 | ok | ok | Significant |
| INC-037 | Luxembourg POST telecom breach (2023) | T2/O1 | T2/O1 | ok | ok | Significant |
| INC-038 | European Investment Bank DDoS (2023) | T1/O1 | T1/O1 | ok | ok | Below threshold |
| INC-039 | Europol EPE portal data theft (2024) | T3/O3 | T3/O4 | ok | MISS | Cyber crisis |
| INC-040 | Small Italian water utility ransomware ( | T1/O1 | T1/O1 | ok | ok | Below threshold |
| INC-041 | Synnovis pathology ransomware (2024) | T4/O3 | T4/O3 | ok | ok | Cyber crisis |
| INC-042 | Transport for London breach (2024) | T2/O1 | T2/O1 | ok | ok | Significant |
| INC-043 | Orange Belgium data breach (2025) | T2/O1 | T2/O1 | ok | ok | Significant |
| INC-044 | AZ Monica hospital cyberattack (2026) | T3/O1 | T3/O1 | ok | ok | Significant |
| INC-045 | Port of Vigo ransomware (2026) | T2/O1 | T2/O1 | ok | ok | Significant |
| INC-046 | Deutsche Bahn DDoS (2026) | T2/O1 | T2/O1 | ok | ok | Significant |

## Failure Analysis

### T-model Misclassifications

- **INC-003 SolarWinds Orion supply chain (2020)**: expected T4, got T3 (confidence: deterministic)
- **INC-011 Norsk Hydro LockerGoga ransomware (2019)**: expected T2, got T3 (confidence: deterministic)
- **INC-033 AnyDesk supply chain breach (2024)**: expected T2, got T3 (confidence: deterministic)

### O-model Misclassifications

- **INC-004 Irish HSE ransomware (2021)**: expected O2, got O1 (confidence: deterministic)
- **INC-009 MOVEit Transfer mass exploitation (2023)**: expected O3, got O4 (confidence: deterministic)
- **INC-010 Change Healthcare ransomware (2024)**: expected O2, got O1 (confidence: deterministic)
- **INC-012 German Landkreis Anhalt-Bitterfeld ransomware (2021)**: expected O2, got O3 (confidence: deterministic)
- **INC-016 Vodafone Portugal DDoS and sabotage (2022)**: expected O2, got O1 (confidence: deterministic)
- **INC-017 Costa Rica Conti ransomware (2022)**: expected O2, got O3 (confidence: deterministic)
- **INC-022 Montenegro government ransomware (2022)**: expected O2, got O3 (confidence: deterministic)
- **INC-029 Romanian hospital ransomware wave (2024)**: expected O2, got O3 (confidence: deterministic)
- **INC-039 Europol EPE portal data theft (2024)**: expected O3, got O4 (confidence: deterministic)
