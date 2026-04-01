# CyberScale v5 — Multi-Entity Aggregation Benchmark (Fully Deterministic)

**Date:** 2026-04-01 11:56
**Scenarios:** 50
**Pipeline:** aggregation → derive_t_level → derive_o_level → matrix (zero ML)
**Elapsed:** 0.0s

## Results

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Aggregation T-level | 100% | 100.0% | PASS |
| Aggregation O-level | 100% | 100.0% | PASS |
| Matrix end-to-end | 100% | 100.0% | PASS |

## Per-scenario Results

| ID | Scenario | Entities | Expected T/O | Predicted T/O | Matrix | Pass |
|----|----------|----------|-------------|--------------|--------|------|
| ME-001 | WannaCry-style ransomware across EU | 5 | T3/O4 | T3/O4 | cyber_crisis | ok |
| ME-002 | NotPetya-style supply chain wiper a | 6 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-003 | SolarWinds-style supply chain espio | 5 | T3/O4 | T3/O4 | cyber_crisis | ok |
| ME-004 | MOVEit-style file transfer zero-day | 4 | T3/O4 | T3/O4 | cyber_crisis | ok |
| ME-005 | Colonial Pipeline-style energy rans | 3 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-006 | Log4Shell-style zero-day in cloud i | 6 | T2/O4 | T2/O4 | large_scale | ok |
| ME-007 | Kaseya-style MSP ransomware cascade | 4 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-008 | EU water treatment SCADA compromise | 2 | T3/O4 | T3/O4 | cyber_crisis | ok |
| ME-009 | Cross-border railway signalling sus | 3 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-010 | EU DNS infrastructure DDoS campaign | 3 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-011 | Power grid cascading failure from c | 4 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-012 | Banking sector credential stuffing  | 2 | T2/O3 | T2/O3 | large_scale | ok |
| ME-013 | CDN provider compromise with data l | 3 | T3/O4 | T3/O4 | cyber_crisis | ok |
| ME-014 | Airport IT system ransomware | 2 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-015 | Trust service provider key compromi | 3 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-016 | Pharmaceutical IP theft campaign | 3 | T2/O3 | T2/O3 | large_scale | ok |
| ME-017 | Satellite ground station jamming | 2 | T2/O4 | T2/O4 | large_scale | ok |
| ME-018 | Regional government sustained ranso | 2 | T4/O3 | T4/O3 | cyber_crisis | ok |
| ME-019 | Wastewater SCADA intrusion | 2 | T2/O1 | T2/O1 | significant | ok |
| ME-020 | Small ISP BGP hijack pair | 2 | T2/O2 | T2/O2 | significant | ok |
| ME-021 | Port logistics ransomware | 3 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-022 | Financial market data feed manipula | 2 | T2/O3 | T2/O3 | large_scale | ok |
| ME-023 | Medical device firmware backdoor | 3 | T2/O4 | T2/O4 | large_scale | ok |
| ME-024 | Postal service minor data access | 2 | T2/O2 | T2/O2 | significant | ok |
| ME-025 | Multi-country search engine defacem | 2 | T2/O4 | T2/O4 | large_scale | ok |
| ME-026 | Chemical plant OT network breach | 2 | T2/O2 | T2/O2 | significant | ok |
| ME-027 | Waste management system minor breac | 2 | T2/O2 | T2/O2 | significant | ok |
| ME-028 | Food supply chain minor disruption | 2 | T1/O2 | T1/O2 | significant | ok |
| ME-029 | Data centre minor cooling system in | 2 | T1/O2 | T1/O2 | significant | ok |
| ME-030 | Motor vehicle manufacturer pair phi | 2 | T2/O2 | T2/O2 | significant | ok |
| ME-031 | Social network and marketplace mino | 2 | T2/O2 | T2/O2 | significant | ok |
| ME-032 | Cross-border electricity and gas di | 3 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-033 | Managed security provider supply ch | 4 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-034 | Nordic banking trojan campaign | 2 | T3/O4 | T3/O4 | cyber_crisis | ok |
| ME-035 | EU cloud region sustained outage | 5 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-036 | Iberian electricity grid cyber intr | 2 | T4/O3 | T4/O3 | cyber_crisis | ok |
| ME-037 | Multi-sector espionage via MSP comp | 4 | T3/O3 | T3/O3 | large_scale | ok |
| ME-038 | Drinking water contamination scare  | 2 | T2/O3 | T2/O3 | large_scale | ok |
| ME-039 | Government email system minor compr | 2 | T2/O2 | T2/O2 | significant | ok |
| ME-040 | Automotive supply chain ransomware | 3 | T3/O3 | T3/O3 | large_scale | ok |
| ME-041 | Hospital ransomware with fatality | 2 | T4/O2 | T4/O2 | large_scale | ok |
| ME-042 | Pan-EU telecom backbone sustained a | 6 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-043 | Financial market trading halt attac | 3 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-044 | Central EU gas pipeline OT compromi | 4 | T3/O4 | T3/O4 | cyber_crisis | ok |
| ME-045 | Research institution minor reconnai | 3 | T2/O3 | T2/O3 | large_scale | ok |
| ME-046 | Minor regional government website d | 2 | T1/O2 | T1/O2 | significant | ok |
| ME-047 | Multi-entity shipping and port cybe | 4 | T4/O4 | T4/O4 | cyber_crisis | ok |
| ME-048 | Non-NIS2 entities minor incident | 2 | T2/O2 | T2/O2 | significant | ok |
| ME-049 | Small electricity provider pair out | 2 | T2/O3 | T2/O3 | large_scale | ok |
| ME-050 | Pan-EU election infrastructure atta | 8 | T4/O4 | T4/O4 | cyber_crisis | ok |
