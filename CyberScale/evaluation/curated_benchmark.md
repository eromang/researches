# CyberScale Phase 3 — Curated Incident Benchmark

**Date:** 2026-03-30 20:23
**Dataset:** `data/reference/curated_incidents.json`
**Incidents:** 40
**Elapsed:** 6.7s

> This benchmark evaluates model performance on **human-curated real-world incidents**,
> as opposed to the synthetic benchmark which uses parametrically generated scenarios.
> Performance gaps between synthetic and curated benchmarks indicate distribution shift.

## T-model Results

- **Accuracy:** 85.0%
- **Macro F1:** 0.6678

### Per-level F1

| Level | F1 | Support |
|-------|-----|---------|
| T1 | 0.0000 | 4 |
| T2 | 0.8148 | 12 |
| T3 | 0.9474 | 18 |
| T4 | 0.9091 | 6 |

### Confusion Matrix

| Actual \ Predicted | T1 | T2 | T3 | T4 |
|---|---|---|---|---|
| **T1** | 0 | 4 | 0 | 0 |
| **T2** | 0 | 11 | 1 | 0 |
| **T3** | 0 | 0 | 18 | 0 |
| **T4** | 0 | 0 | 1 | 5 |

## O-model Results

- **Accuracy:** 40.0%
- **Macro F1:** 0.4949

### Per-level F1

| Level | F1 | Support |
|-------|-----|---------|
| O1 | 0.0952 | 20 |
| O2 | 0.3784 | 11 |
| O3 | 0.7059 | 7 |
| O4 | 0.8000 | 2 |

### Confusion Matrix

| Actual \ Predicted | O1 | O2 | O3 | O4 |
|---|---|---|---|---|
| **O1** | 1 | 19 | 0 | 0 |
| **O2** | 0 | 7 | 4 | 0 |
| **O3** | 0 | 0 | 6 | 1 |
| **O4** | 0 | 0 | 0 | 2 |

## End-to-end Matrix Results

- **Accuracy:** 67.5%

### Classification Distribution

| Classification | Count | Pct |
|---------------|-------|-----|
| below_threshold | 0 | 0.0% |
| significant | 16 | 40.0% |
| large_scale | 20 | 50.0% |
| cyber_crisis | 4 | 10.0% |

## Per-incident Results

| ID | Incident | Expected T/O | Predicted T/O | T | O | Matrix |
|----|----------|-------------|--------------|---|---|--------|
| INC-001 | WannaCry ransomware (2017) | T4/O4 | T4/O4 | ok | ok | Cyber crisis |
| INC-002 | NotPetya destructive attack (2017) | T4/O4 | T4/O4 | ok | ok | Cyber crisis |
| INC-003 | SolarWinds Orion supply chain (2020) | T4/O3 | T3/O3 | MISS | ok | Large-scale |
| INC-004 | Irish HSE ransomware (2021) | T3/O2 | T3/O2 | ok | ok | Large-scale |
| INC-005 | Colonial Pipeline ransomware (2021) | T3/O1 | T3/O1 | ok | ok | Significant |
| INC-006 | Kaseya VSA supply chain ransomware (2021 | T3/O3 | T3/O3 | ok | ok | Large-scale |
| INC-007 | Belgian MoD Log4Shell exploitation (2021 | T2/O1 | T2/O2 | ok | MISS | Significant |
| INC-008 | University of Maastricht ransomware (201 | T2/O1 | T2/O2 | ok | MISS | Significant |
| INC-009 | MOVEit Transfer mass exploitation (2023) | T4/O3 | T4/O4 | ok | MISS | Cyber crisis |
| INC-010 | Change Healthcare ransomware (2024) | T3/O2 | T3/O2 | ok | ok | Large-scale |
| INC-011 | Norsk Hydro LockerGoga ransomware (2019) | T2/O2 | T2/O2 | ok | ok | Significant |
| INC-012 | German Landkreis Anhalt-Bitterfeld ranso | T3/O2 | T3/O3 | ok | MISS | Large-scale |
| INC-013 | Düsseldorf University Hospital ransomwar | T3/O1 | T3/O2 | ok | MISS | Large-scale |
| INC-014 | Finnish parliament email breach (2020) | T3/O1 | T3/O2 | ok | MISS | Large-scale |
| INC-015 | EMA COVID vaccine data breach (2020) | T3/O3 | T3/O3 | ok | ok | Large-scale |
| INC-016 | Vodafone Portugal DDoS and sabotage (202 | T3/O2 | T3/O2 | ok | ok | Large-scale |
| INC-017 | Costa Rica Conti ransomware (2022) | T4/O2 | T4/O3 | ok | MISS | Cyber crisis |
| INC-018 | European Parliament DDoS (2022) | T1/O1 | T2/O2 | MISS | MISS | Significant |
| INC-019 | KNP Logistics Group ransomware (2023) | T4/O1 | T4/O2 | ok | MISS | Large-scale |
| INC-020 | Viasat KA-SAT modem wiper (2022) | T3/O3 | T3/O3 | ok | ok | Large-scale |
| INC-021 | JBS Foods ransomware (2021) | T2/O2 | T2/O2 | ok | ok | Significant |
| INC-022 | Montenegro government ransomware (2022) | T3/O2 | T3/O3 | ok | MISS | Large-scale |
| INC-023 | Danish railway Supeo attack (2022) | T2/O1 | T2/O2 | ok | MISS | Significant |
| INC-024 | Portuguese TAP Air data breach (2022) | T3/O1 | T3/O2 | ok | MISS | Large-scale |
| INC-025 | SAS DDoS (2023) | T2/O2 | T2/O2 | ok | ok | Significant |
| INC-026 | French hospitals ransomware series (2022 | T3/O1 | T3/O2 | ok | MISS | Large-scale |
| INC-027 | Italian Agenzia delle Entrate LockBit cl | T2/O1 | T2/O2 | ok | MISS | Significant |
| INC-028 | Austrian FMTG hotel chain ransomware (20 | T1/O1 | T2/O2 | MISS | MISS | Significant |
| INC-029 | Romanian hospital ransomware wave (2024) | T3/O2 | T3/O3 | ok | MISS | Large-scale |
| INC-030 | Barcelona Hospital Clínic ransomware (20 | T3/O1 | T3/O2 | ok | MISS | Large-scale |
| INC-031 | Polish railway GPS spoofing (2023) | T2/O1 | T2/O2 | ok | MISS | Significant |
| INC-032 | Port of Lisbon LockBit ransomware (2023) | T2/O1 | T2/O2 | ok | MISS | Significant |
| INC-033 | AnyDesk supply chain breach (2024) | T2/O3 | T3/O3 | MISS | ok | Large-scale |
| INC-034 | Nordex wind turbine ransomware (2022) | T2/O2 | T2/O2 | ok | ok | Significant |
| INC-035 | Medibank data breach (2022) | T3/O1 | T3/O2 | ok | MISS | Large-scale |
| INC-036 | German DIHK Chamber of Commerce attack ( | T3/O1 | T3/O2 | ok | MISS | Large-scale |
| INC-037 | Luxembourg POST telecom breach (2023) | T2/O1 | T2/O2 | ok | MISS | Significant |
| INC-038 | European Investment Bank DDoS (2023) | T1/O1 | T2/O2 | MISS | MISS | Significant |
| INC-039 | Europol EPE portal data theft (2024) | T3/O3 | T3/O3 | ok | ok | Large-scale |
| INC-040 | Small Italian water utility ransomware ( | T1/O1 | T2/O2 | MISS | MISS | Significant |

## Failure Analysis

### T-model Misclassifications

- **INC-003 SolarWinds Orion supply chain (2020)**: expected T4, got T3 (confidence: medium)
- **INC-018 European Parliament DDoS (2022)**: expected T1, got T2 (confidence: medium)
- **INC-028 Austrian FMTG hotel chain ransomware (2019)**: expected T1, got T2 (confidence: medium)
- **INC-033 AnyDesk supply chain breach (2024)**: expected T2, got T3 (confidence: medium)
- **INC-038 European Investment Bank DDoS (2023)**: expected T1, got T2 (confidence: medium)
- **INC-040 Small Italian water utility ransomware (2023)**: expected T1, got T2 (confidence: medium)

### O-model Misclassifications

- **INC-007 Belgian MoD Log4Shell exploitation (2021)**: expected O1, got O2 (confidence: medium)
- **INC-008 University of Maastricht ransomware (2019)**: expected O1, got O2 (confidence: medium)
- **INC-009 MOVEit Transfer mass exploitation (2023)**: expected O3, got O4 (confidence: medium)
- **INC-012 German Landkreis Anhalt-Bitterfeld ransomware (2021)**: expected O2, got O3 (confidence: medium)
- **INC-013 Düsseldorf University Hospital ransomware (2020)**: expected O1, got O2 (confidence: medium)
- **INC-014 Finnish parliament email breach (2020)**: expected O1, got O2 (confidence: medium)
- **INC-017 Costa Rica Conti ransomware (2022)**: expected O2, got O3 (confidence: medium)
- **INC-018 European Parliament DDoS (2022)**: expected O1, got O2 (confidence: medium)
- **INC-019 KNP Logistics Group ransomware (2023)**: expected O1, got O2 (confidence: medium)
- **INC-022 Montenegro government ransomware (2022)**: expected O2, got O3 (confidence: medium)
- **INC-023 Danish railway Supeo attack (2022)**: expected O1, got O2 (confidence: medium)
- **INC-024 Portuguese TAP Air data breach (2022)**: expected O1, got O2 (confidence: high)
- **INC-026 French hospitals ransomware series (2022-2023)**: expected O1, got O2 (confidence: medium)
- **INC-027 Italian Agenzia delle Entrate LockBit claim (2022)**: expected O1, got O2 (confidence: medium)
- **INC-028 Austrian FMTG hotel chain ransomware (2019)**: expected O1, got O2 (confidence: medium)
- **INC-029 Romanian hospital ransomware wave (2024)**: expected O2, got O3 (confidence: medium)
- **INC-030 Barcelona Hospital Clínic ransomware (2023)**: expected O1, got O2 (confidence: high)
- **INC-031 Polish railway GPS spoofing (2023)**: expected O1, got O2 (confidence: medium)
- **INC-032 Port of Lisbon LockBit ransomware (2023)**: expected O1, got O2 (confidence: high)
- **INC-035 Medibank data breach (2022)**: expected O1, got O2 (confidence: medium)
- **INC-036 German DIHK Chamber of Commerce attack (2022)**: expected O1, got O2 (confidence: medium)
- **INC-037 Luxembourg POST telecom breach (2023)**: expected O1, got O2 (confidence: medium)
- **INC-038 European Investment Bank DDoS (2023)**: expected O1, got O2 (confidence: medium)
- **INC-040 Small Italian water utility ransomware (2023)**: expected O1, got O2 (confidence: medium)
