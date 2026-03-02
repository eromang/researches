---
title: CVE Fixation Analysis — Phase 2
generated: 2026-03-02 18:56 UTC
document_type: analysis-index
tags:
  - llm-benchmark/phase-2
  - llm-benchmark/cve-analysis
---

# CVE Fixation Analysis — Phase 2

> Generated: 2026-03-02 18:56 UTC

## 1. CVE Mention Rates

| Model | Records | With CVEs | Rate | Mean CVE/record | Mean when present |
|-------|---------|-----------|------|-----------------|-------------------|
| deepseek-r1 | 2107 | 767 | 36.4% | 0.638 | 1.754 |
| qwen3 | 2109 | 1192 | 56.5% | 0.898 | 1.589 |
| llama31 | 2112 | 734 | 34.8% | 0.386 | 1.112 |
| gemma3n | 2112 | 40 | 1.9% | 0.030 | 1.600 |
| qwen3-nothink | 2112 | 534 | 25.3% | 0.486 | 1.921 |
| phi4 | 2112 | 58 | 2.8% | 0.028 | 1.017 |
| mistral | 2112 | 230 | 10.9% | 0.167 | 1.535 |

## 2. CVE Frequency Distribution (Top 10 per model)

### deepseek-r1

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2021-4034 | 560 | 73.0% | real |
| 2 | CVE-2021-44228 | 148 | 19.3% | real |
| 3 | CVE-2021-3493 | 68 | 8.9% | real |
| 4 | CVE-2021-3156 | 33 | 4.3% | real |
| 5 | CVE-2021-4033 | 21 | 2.7% | unverified |
| 6 | CVE-2020-1472 | 16 | 2.1% | unverified |
| 7 | CVE-2021-4032 | 15 | 2.0% | unverified |
| 8 | CVE-2021-3151 | 10 | 1.3% | hallucinated |
| 9 | CVE-2021-3448 | 9 | 1.2% | unverified |
| 10 | CVE-2021-44201 | 8 | 1.0% | unverified |

### qwen3

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2023-1234 | 286 | 24.0% | unverified |
| 2 | CVE-2023-22891 | 258 | 21.6% | unverified |
| 3 | CVE-2021-44228 | 185 | 15.5% | real |
| 4 | CVE-2023-22892 | 122 | 10.2% | unverified |
| 5 | CVE-2023-22893 | 107 | 9.0% | unverified |
| 6 | CVE-2021-40444 | 65 | 5.5% | real |
| 7 | CVE-2023-5678 | 46 | 3.9% | unverified |
| 8 | CVE-2022-5678 | 41 | 3.4% | unverified |
| 9 | CVE-2022-3456 | 33 | 2.8% | unverified |
| 10 | CVE-2021-34507 | 29 | 2.4% | unverified |

### llama31

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2021-44228 | 357 | 48.6% | real |
| 2 | CVE-2020-1472 | 79 | 10.8% | unverified |
| 3 | CVE-2019-0604 | 48 | 6.5% | unverified |
| 4 | CVE-2021-40444 | 40 | 5.4% | real |
| 5 | CVE-2021-31440 | 16 | 2.2% | unverified |
| 6 | CVE-2020-0601 | 12 | 1.6% | unverified |
| 7 | CVE-2019-11510 | 10 | 1.4% | unverified |
| 8 | CVE-2020-14779 | 10 | 1.4% | unverified |
| 9 | CVE-2019-11599 | 10 | 1.4% | unverified |
| 10 | CVE-2019-2725 | 9 | 1.2% | real |

### gemma3n

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2017-0144 | 10 | 25.0% | unverified |
| 2 | CVE-2023-23397 | 8 | 20.0% | unverified |
| 3 | CVE-2023-0666 | 5 | 12.5% | unverified |
| 4 | CVE-2023-0669 | 3 | 7.5% | unverified |
| 5 | CVE-2023-0123 | 3 | 7.5% | unverified |
| 6 | CVE-2023-23398 | 3 | 7.5% | unverified |
| 7 | CVE-2023-0124 | 2 | 5.0% | unverified |
| 8 | CVE-2023-0667 | 2 | 5.0% | unverified |
| 9 | CVE-2021-23233 | 2 | 5.0% | unverified |
| 10 | CVE-2020-14724 | 2 | 5.0% | unverified |

### qwen3-nothink

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2023-22892 | 121 | 22.7% | unverified |
| 2 | CVE-2023-22891 | 120 | 22.5% | unverified |
| 3 | CVE-2023-22893 | 64 | 12.0% | unverified |
| 4 | CVE-2021-44228 | 60 | 11.2% | real |
| 5 | CVE-2021-40444 | 57 | 10.7% | real |
| 6 | CVE-2023-1234 | 42 | 7.9% | unverified |
| 7 | CVE-2021-34527 | 40 | 7.5% | unverified |
| 8 | CVE-2023-22894 | 36 | 6.7% | unverified |
| 9 | CVE-2021-34523 | 30 | 5.6% | unverified |
| 10 | CVE-2023-5678 | 20 | 3.7% | unverified |

### phi4

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2021-44228 | 35 | 60.3% | real |
| 2 | CVE-2020-10135 | 4 | 6.9% | unverified |
| 3 | CVE-2020-1472 | 3 | 5.2% | unverified |
| 4 | CVE-2020-1234 | 2 | 3.4% | unverified |
| 5 | CVE-2020-15999 | 2 | 3.4% | unverified |
| 6 | CVE-2021-34523 | 1 | 1.7% | unverified |
| 7 | CVE-2022-22963 | 1 | 1.7% | unverified |
| 8 | CVE-2022-30190 | 1 | 1.7% | unverified |
| 9 | CVE-2022-21824 | 1 | 1.7% | unverified |
| 10 | CVE-2021-28658 | 1 | 1.7% | unverified |

### mistral

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2019-19781 | 66 | 28.7% | unverified |
| 2 | CVE-2021-30551 | 32 | 13.9% | unverified |
| 3 | CVE-2017-11882 | 21 | 9.1% | unverified |
| 4 | CVE-2017-0144 | 15 | 6.5% | unverified |
| 5 | CVE-2022-30668 | 15 | 6.5% | unverified |
| 6 | CVE-2021-40444 | 14 | 6.1% | real |
| 7 | CVE-2017-0199 | 12 | 5.2% | unverified |
| 8 | CVE-2017-5638 | 12 | 5.2% | unverified |
| 9 | CVE-2019-12411 | 9 | 3.9% | unverified |
| 10 | CVE-2017-7494 | 8 | 3.5% | unverified |

## 3. PwnKit Fixation Check

### Phase 1 Baseline

- CVE-containing records: 24
- PwnKit (CVE-2021-4034) mentions: 18
- Concentration: 75%

### Phase 2 Results

**deepseek-r1:**
- CVE-containing records: 767
- PwnKit mentions: 560 (73.0%)
- Phase 1 → 2 change: -2.0pp (decrease)

**qwen3:**
- CVE-containing records: 1192
- PwnKit mentions: 0 (0.0%)

**llama31:**
- CVE-containing records: 734
- PwnKit mentions: 1 (0.1%)

**gemma3n:**
- CVE-containing records: 40
- PwnKit mentions: 0 (0.0%)

**qwen3-nothink:**
- CVE-containing records: 534
- PwnKit mentions: 0 (0.0%)

**phi4:**
- CVE-containing records: 58
- PwnKit mentions: 0 (0.0%)

**mistral:**
- CVE-containing records: 230
- PwnKit mentions: 1 (0.4%)

## 4. CVE Diversity Index

| Model | CVE records | Unique CVEs | Shannon H | Max H | Normalised H | Top CVE | Top % | Fixated? |
|-------|-------------|-------------|-----------|-------|-------------|---------|-------|----------|
| deepseek-r1 | 767 | 274 | 4.789 | 8.098 | 0.591 | CVE-2021-4034 | 73.0% | YES |
| qwen3 | 1192 | 336 | 5.624 | 8.392 | 0.670 | CVE-2023-1234 | 24.0% | no |
| llama31 | 734 | 137 | 4.144 | 7.098 | 0.584 | CVE-2021-44228 | 48.6% | YES |
| gemma3n | 40 | 29 | 4.420 | 4.858 | 0.910 | CVE-2017-0144 | 25.0% | no |
| qwen3-nothink | 534 | 228 | 5.781 | 7.833 | 0.738 | CVE-2023-22892 | 22.7% | no |
| phi4 | 58 | 18 | 2.556 | 4.170 | 0.613 | CVE-2021-44228 | 60.3% | YES |
| mistral | 230 | 94 | 5.263 | 6.555 | 0.803 | CVE-2019-19781 | 28.7% | no |

> Fixation threshold: >40% of CVE-containing records cite a single CVE.

## 5. Sector Appropriateness

**57 CVE(s) appear across 5+ sectors** (potential contextual inappropriateness):

| CVE | Sector count | Sectors |
|-----|-------------|---------|
| CVE-2021-4034 | 21 | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Trade, Transport, Water |
| CVE-2021-44228 | 21 | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Trade, Transport, Water |
| CVE-2023-1234 | 21 | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Trade, Transport, Water |
| CVE-2023-22891 | 21 | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Trade, Transport, Water |
| CVE-2023-22892 | 20 | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Trade, Transport, Water |
| CVE-2020-1472 | 19 | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Sanctions, Semiconductors, Space, Telecom, Trade, Transport, Water |
| CVE-2021-40444 | 19 | Aerospace, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Trade, Transport, Water |
| CVE-2023-22893 | 19 | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Research, Sanctions, Semiconductors, Space, Telecom, Trade, Transport |
| CVE-2023-5678 | 18 | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Manufacturing, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Telecom, Trade, Transport |
| CVE-2019-19781 | 18 | Aerospace, Aviation, Cloud, Defense, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Research, Semiconductors, Space, Telecom, Trade, Transport, Water |
| CVE-2023-22894 | 16 | Aviation, Cloud, Defense, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Sanctions, Semiconductors, Space, Telecom, Trade, Water |
| CVE-2022-5678 | 16 | Aerospace, Aviation, Defense, Elections, Energy, Finance, Manufacturing, Parliament, Ports, Rail, Research, Semiconductors, Space, Telecom, Trade, Transport |
| CVE-2021-3493 | 15 | Aerospace, Aviation, Defense, Elections, Energy, Finance, Health, Manufacturing, Parliament, Ports, Sanctions, Semiconductors, Telecom, Transport, Water |
| CVE-2019-0604 | 14 | Aerospace, Defense, Elections, Energy, Finance, Government, Health, Ports, Sanctions, Semiconductors, Telecom, Trade, Transport, Water |
| CVE-2022-3456 | 12 | Aerospace, Aviation, Defense, Elections, Energy, Finance, Government, Ports, Space, Telecom, Trade, Transport |
| CVE-2022-22944 | 12 | Aerospace, Cloud, Energy, Health, Manufacturing, Rail, Semiconductors, Space, Telecom, Trade, Transport, Water |
| CVE-2023-1235 | 11 | Aviation, Defense, Elections, Energy, Finance, Parliament, Research, Space, Telecom, Trade, Transport |
| CVE-2023-22895 | 11 | Aerospace, Energy, Finance, Health, Ports, Sanctions, Semiconductors, Telecom, Trade, Transport, Water |
| CVE-2017-0144 | 11 | Aerospace, Aviation, Defense, Energy, Finance, Government, Health, Sanctions, Semiconductors, Transport, Water |
| CVE-2023-2281 | 11 | Aviation, Cloud, Defense, Energy, Finance, Health, Research, Telecom, Trade, Transport, Water |
| CVE-2021-30551 | 11 | Cloud, Defense, Energy, Finance, Government, Health, Ports, Rail, Telecom, Trade, Transport |
| CVE-2021-4032 | 10 | Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Sanctions, Semiconductors, Telecom |
| CVE-2021-3156 | 10 | Aerospace, Aviation, Energy, Health, Sanctions, Semiconductors, Telecom, Trade, Transport, Water |
| CVE-2022-3401 | 10 | Aerospace, Defense, Energy, Finance, Health, Parliament, Ports, Sanctions, Telecom, Transport |
| CVE-2021-34523 | 9 | Aerospace, Defense, Energy, Finance, Health, Space, Telecom, Transport, Water |
| CVE-2023-4446 | 9 | Aerospace, Defense, Energy, Finance, Government, Health, Manufacturing, Telecom, Trade |
| CVE-2021-4033 | 8 | Finance, Government, Health, Parliament, Semiconductors, Telecom, Transport, Water |
| CVE-2021-34527 | 8 | Defense, Energy, Government, Health, Manufacturing, Rail, Telecom, Water |
| CVE-2023-2289 | 8 | Aerospace, Aviation, Energy, Finance, Health, Manufacturing, Semiconductors, Telecom |
| CVE-2023-2282 | 8 | Aviation, Cloud, Defense, Energy, Finance, Telecom, Trade, Transport |
| CVE-2020-0601 | 7 | Defense, Energy, Government, Health, Sanctions, Semiconductors, Telecom |
| CVE-2022-5645 | 7 | Aviation, Defense, Elections, Ports, Rail, Space, Telecom |
| CVE-2023-2280 | 7 | Aviation, Defense, Energy, Health, Research, Telecom, Water |
| CVE-2019-11510 | 7 | Cloud, Energy, Finance, Government, Sanctions, Space, Telecom |
| CVE-2017-11882 | 7 | Aerospace, Defense, Energy, Finance, Health, Semiconductors, Transport |
| CVE-2017-0199 | 6 | Aerospace, Energy, Finance, Health, Manufacturing, Water |
| CVE-2023-22896 | 6 | Aerospace, Finance, Government, Telecom, Trade, Transport |
| CVE-2023-22511 | 6 | Defense, Energy, Health, Rail, Space, Water |
| CVE-2023-28255 | 6 | Aviation, Defense, Energy, Government, Research, Transport |
| CVE-2023-3222 | 6 | Aerospace, Energy, Finance, Health, Manufacturing, Telecom |
| CVE-2022-4104 | 6 | Aviation, Energy, Finance, Rail, Space, Telecom |
| CVE-2022-1234 | 6 | Elections, Finance, Government, Parliament, Research, Telecom |
| CVE-2023-22899 | 6 | Aerospace, Cloud, Defense, Finance, Ports, Telecom |
| CVE-2019-2725 | 6 | Aerospace, Energy, Finance, Rail, Space, Transport |
| CVE-2020-14779 | 6 | Cloud, Defense, Health, Ports, Semiconductors, Telecom |
| CVE-2017-5638 | 6 | Finance, Government, Ports, Research, Transport, Water |
| CVE-2021-3151 | 5 | Aviation, Elections, Telecom, Transport, Water |
| CVE-2021-44201 | 5 | Defense, Energy, Government, Health, Transport |
| CVE-2021-26855 | 5 | Energy, Finance, Health, Telecom, Water |
| CVE-2023-2251 | 5 | Cloud, Energy, Ports, Transport, Water |
| CVE-2023-3865 | 5 | Energy, Finance, Health, Trade, Transport |
| CVE-2023-32220 | 5 | Energy, Finance, Research, Telecom, Transport |
| CVE-2023-32228 | 5 | Defense, Energy, Finance, Sanctions, Trade |
| CVE-2017-0145 | 5 | Energy, Government, Health, Transport, Water |
| CVE-2023-29427 | 5 | Aviation, Energy, Government, Semiconductors, Telecom |
| CVE-2023-4681 | 5 | Defense, Energy, Finance, Government, Health |
| CVE-2023-4445 | 5 | Aerospace, Energy, Manufacturing, Telecom, Trade |

## 6. CVE Hallucination Check

### deepseek-r1

- **Real** (5): CVE-2020-1337, CVE-2021-3156, CVE-2021-3493, CVE-2021-4034, CVE-2021-44228
- **Hallucinated** (3): CVE-2021-3151, CVE-2021-34930, CVE-2021-34938
- **Unverified** (266): CVE-1234-5678, CVE-2014-0226, CVE-2015-3450, CVE-2017-0001, CVE-2017-0141, CVE-2017-0143, CVE-2017-0199, CVE-2017-1000353, CVE-2017-17113, CVE-2017-5634, CVE-2017-5636, CVE-2018-10508, CVE-2018-10523, CVE-2018-10539, CVE-2018-10565, CVE-2018-10587, CVE-2018-1059, CVE-2018-10595, CVE-2018-10596, CVE-2018-11110, CVE-2018-11795, CVE-2018-14972, CVE-2018-19999, CVE-2018-20045, CVE-2019-0604, CVE-2019-0809, CVE-2019-0884, CVE-2019-0886, CVE-2019-1249, CVE-2019-12492, CVE-2019-12952, CVE-2019-15107, CVE-2019-19059, CVE-2020-0601, CVE-2020-0798, CVE-2020-0932, CVE-2020-10588, CVE-2020-1262, CVE-2020-12970, CVE-2020-1336, CVE-2020-13379, CVE-2020-1338, CVE-2020-1390, CVE-2020-1391, CVE-2020-1395, CVE-2020-13996, CVE-2020-1472, CVE-2020-1476, CVE-2020-1507, CVE-2020-15177, CVE-2020-16011, CVE-2020-1952, CVE-2020-1957, CVE-2020-3551, CVE-2020-35676, CVE-2020-5902, CVE-2021-1184, CVE-2021-1190, CVE-2021-11909, CVE-2021-1199, CVE-2021-1205, CVE-2021-1357, CVE-2021-1397, CVE-2021-1605, CVE-2021-1673, CVE-2021-1912, CVE-2021-19125, CVE-2021-1936, CVE-2021-20066, CVE-2021-20089, CVE-2021-20739, CVE-2021-20777, CVE-2021-20778, CVE-2021-21998, CVE-2021-22208, CVE-2021-22957, CVE-2021-22959, CVE-2021-26855, CVE-2021-26896, CVE-2021-27078, CVE-2021-30498, CVE-2021-30730, CVE-2021-30794, CVE-2021-30795, CVE-2021-30809, CVE-2021-30860, CVE-2021-30866, CVE-2021-3150, CVE-2021-31503, CVE-2021-31505, CVE-2021-31507, CVE-2021-31519, CVE-2021-31536, CVE-2021-3155, CVE-2021-3159, CVE-2021-31590, CVE-2021-31591, CVE-2021-32173, CVE-2021-32482, CVE-2021-3281, CVE-2021-32993, CVE-2021-32994, CVE-2021-32995, CVE-2021-32996, CVE-2021-32997, CVE-2021-32998, CVE-2021-32999, CVE-2021-33107, CVE-2021-33109, CVE-2021-33110, CVE-2021-33111, CVE-2021-3312, CVE-2021-33128, CVE-2021-3313, CVE-2021-33171, CVE-2021-33179, CVE-2021-33181, CVE-2021-33182, CVE-2021-33183, CVE-2021-33184, CVE-2021-33185, CVE-2021-33193, CVE-2021-33194, CVE-2021-3448, CVE-2021-34489, CVE-2021-34507, CVE-2021-34547, CVE-2021-3490, CVE-2021-34900, CVE-2021-34903, CVE-2021-34906, CVE-2021-34907, CVE-2021-34908, CVE-2021-34909, CVE-2021-3491, CVE-2021-34915, CVE-2021-34916, CVE-2021-3492, CVE-2021-34931, CVE-2021-34932, CVE-2021-34933, CVE-2021-34934, CVE-2021-34936, CVE-2021-34937, CVE-2021-34939, CVE-2021-34942, CVE-2021-34943, CVE-2021-35946, CVE-2021-35947, CVE-2021-3608, CVE-2021-36198, CVE-2021-36199, CVE-2021-36398, CVE-2021-37376, CVE-2021-38648, CVE-2021-38658, CVE-2021-4031, CVE-2021-4032, CVE-2021-40327, CVE-2021-4033, CVE-2021-40344, CVE-2021-40348, CVE-2021-4035, CVE-2021-4036, CVE-2021-405150, CVE-2021-41579, CVE-2021-41777, CVE-2021-42006, CVE-2021-42007, CVE-2021-4404, CVE-2021-44042, CVE-2021-44048, CVE-2021-44049, CVE-2021-44201, CVE-2021-44204, CVE-2021-44530, CVE-2021-44532, CVE-2021-44562, CVE-2021-44846, CVE-2021-44858, CVE-2021-44892, CVE-2021-44896, CVE-2021-45072, CVE-2022-11034, CVE-2022-22269, CVE-2022-22980, CVE-2022-22981, CVE-2022-22983, CVE-2022-22989, CVE-2022-23906, CVE-2022-26071, CVE-2022-26130, CVE-2022-26132, CVE-2022-26134, CVE-2022-26644, CVE-2022-26806, CVE-2022-26809, CVE-2022-26855, CVE-2022-26856, CVE-2023-1234, CVE-2023-12345, CVE-2023-12346, CVE-2023-20105, CVE-2023-20109, CVE-2023-20110, CVE-2023-20152, CVE-2023-20170, CVE-2023-20172, CVE-2023-20175, CVE-2023-20180, CVE-2023-20184, CVE-2023-2019, CVE-2023-20190, CVE-2023-20191, CVE-2023-20192, CVE-2023-20193, CVE-2023-20199, CVE-2023-20628, CVE-2023-2251, CVE-2023-22811, CVE-2023-23146, CVE-2023-23339, CVE-2023-23376, CVE-2023-23377, CVE-2023-23378, CVE-2023-23397, CVE-2023-24015, CVE-2023-24016, CVE-2023-24019, CVE-2023-24020, CVE-2023-24032, CVE-2023-24041, CVE-2023-24096, CVE-2023-240985, CVE-2023-24223, CVE-2023-2780, CVE-2023-2820, CVE-2023-2823, CVE-2023-28240, CVE-2023-2825, CVE-2023-2910, CVE-2023-2920, CVE-2023-29720, CVE-2023-2980, CVE-2023-32565, CVE-2023-3601, CVE-2023-3602, CVE-2023-45678, CVE-2023-45690, CVE-2023-46898, CVE-2023-47456, CVE-2023-48078, CVE-2023-48221, CVE-2023-48222, CVE-2023-48398, CVE-2023-4840, CVE-2023-48826, CVE-2023-48827, CVE-2023-67890, CVE-2024-1020, CVE-2024-10924, CVE-2024-10960, CVE-2024-20251, CVE-2024-20252, CVE-2024-67890, CVE-2024-78901

### qwen3

- **Real** (3): CVE-2021-40444, CVE-2021-44228, CVE-2022-22947
- **Hallucinated** (0): none
- **Unverified** (333): CVE-2017-0144, CVE-2017-0145, CVE-2018-0235, CVE-2020-0601, CVE-2020-0796, CVE-2020-1472, CVE-2020-15525, CVE-2020-1941, CVE-2020-1945, CVE-2020-1946, CVE-2020-25644, CVE-2020-2966, CVE-2020-3581, CVE-2020-3589, CVE-2021-21194, CVE-2021-26855, CVE-2021-26875, CVE-2021-32173, CVE-2021-3447, CVE-2021-3449, CVE-2021-34501, CVE-2021-34502, CVE-2021-34504, CVE-2021-34506, CVE-2021-34507, CVE-2021-34508, CVE-2021-34509, CVE-2021-34523, CVE-2021-34527, CVE-2021-34529, CVE-2021-40445, CVE-2021-4104, CVE-2021-41379, CVE-2021-4510, CVE-2021-4567, CVE-2022-1234, CVE-2022-1345, CVE-2022-21624, CVE-2022-2163, CVE-2022-2165, CVE-2022-21651, CVE-2022-21652, CVE-2022-21654, CVE-2022-21807, CVE-2022-21856, CVE-2022-21861, CVE-2022-21867, CVE-2022-22944, CVE-2022-22946, CVE-2022-24210, CVE-2022-24382, CVE-2022-2499, CVE-2022-2935, CVE-2022-29884, CVE-2022-3086, CVE-2022-30861, CVE-2022-30865, CVE-2022-30866, CVE-2022-30867, CVE-2022-3401, CVE-2022-3456, CVE-2022-37959, CVE-2022-3797, CVE-2022-4104, CVE-2022-4133, CVE-2022-4143, CVE-2022-4147, CVE-2022-4174, CVE-2022-5432, CVE-2022-5645, CVE-2022-5678, CVE-2023-1200, CVE-2023-1234, CVE-2023-1235, CVE-2023-1842, CVE-2023-1845, CVE-2023-1983, CVE-2023-1984, CVE-2023-1989, CVE-2023-2134, CVE-2023-21422, CVE-2023-21423, CVE-2023-21600, CVE-2023-21601, CVE-2023-21602, CVE-2023-21603, CVE-2023-2161, CVE-2023-21612, CVE-2023-2162, CVE-2023-21624, CVE-2023-21629, CVE-2023-21636, CVE-2023-2164, CVE-2023-21657, CVE-2023-21658, CVE-2023-21696, CVE-2023-22419, CVE-2023-22476, CVE-2023-22477, CVE-2023-22478, CVE-2023-2251, CVE-2023-22510, CVE-2023-22511, CVE-2023-22513, CVE-2023-22514, CVE-2023-22515, CVE-2023-22516, CVE-2023-22518, CVE-2023-2280, CVE-2023-22802, CVE-2023-2281, CVE-2023-22812, CVE-2023-22816, CVE-2023-22817, CVE-2023-22818, CVE-2023-2282, CVE-2023-22821, CVE-2023-22822, CVE-2023-22824, CVE-2023-22825, CVE-2023-22826, CVE-2023-22828, CVE-2023-22829, CVE-2023-22844, CVE-2023-22845, CVE-2023-22846, CVE-2023-22853, CVE-2023-22855, CVE-2023-22859, CVE-2023-2288, CVE-2023-2289, CVE-2023-22890, CVE-2023-22891, CVE-2023-22892, CVE-2023-22893, CVE-2023-22894, CVE-2023-22895, CVE-2023-22896, CVE-2023-22899, CVE-2023-2290, CVE-2023-22913, CVE-2023-22914, CVE-2023-2296, CVE-2023-22960, CVE-2023-22961, CVE-2023-22966, CVE-2023-23125, CVE-2023-24102, CVE-2023-24106, CVE-2023-24112, CVE-2023-24114, CVE-2023-24115, CVE-2023-24128, CVE-2023-24129, CVE-2023-24155, CVE-2023-24156, CVE-2023-24191, CVE-2023-24213, CVE-2023-24254, CVE-2023-24290, CVE-2023-24291, CVE-2023-24391, CVE-2023-24392, CVE-2023-24412, CVE-2023-24421, CVE-2023-24422, CVE-2023-24423, CVE-2023-24428, CVE-2023-24429, CVE-2023-24445, CVE-2023-24542, CVE-2023-24721, CVE-2023-24784, CVE-2023-24812, CVE-2023-24814, CVE-2023-24816, CVE-2023-24818, CVE-2023-24821, CVE-2023-24822, CVE-2023-24823, CVE-2023-24827, CVE-2023-24852, CVE-2023-24882, CVE-2023-24892, CVE-2023-24893, CVE-2023-24895, CVE-2023-24915, CVE-2023-24938, CVE-2023-24964, CVE-2023-24965, CVE-2023-25141, CVE-2023-25152, CVE-2023-25444, CVE-2023-25445, CVE-2023-25535, CVE-2023-25536, CVE-2023-25822, CVE-2023-25823, CVE-2023-26115, CVE-2023-27555, CVE-2023-27957, CVE-2023-2825, CVE-2023-28252, CVE-2023-28255, CVE-2023-28256, CVE-2023-28258, CVE-2023-28259, CVE-2023-2902, CVE-2023-29230, CVE-2023-29231, CVE-2023-29232, CVE-2023-29237, CVE-2023-29263, CVE-2023-2931, CVE-2023-29315, CVE-2023-29341, CVE-2023-29347, CVE-2023-2935, CVE-2023-29350, CVE-2023-29352, CVE-2023-29372, CVE-2023-29376, CVE-2023-29377, CVE-2023-29382, CVE-2023-29384, CVE-2023-29389, CVE-2023-29394, CVE-2023-2942, CVE-2023-29420, CVE-2023-29421, CVE-2023-29422, CVE-2023-29423, CVE-2023-29425, CVE-2023-29426, CVE-2023-29427, CVE-2023-2943, CVE-2023-29444, CVE-2023-29453, CVE-2023-29464, CVE-2023-29465, CVE-2023-29466, CVE-2023-29467, CVE-2023-2950, CVE-2023-29500, CVE-2023-2951, CVE-2023-2955, CVE-2023-29553, CVE-2023-29712, CVE-2023-29939, CVE-2023-29948, CVE-2023-30194, CVE-2023-3021, CVE-2023-30215, CVE-2023-30216, CVE-2023-3022, CVE-2023-30226, CVE-2023-30272, CVE-2023-30648, CVE-2023-3065, CVE-2023-3066, CVE-2023-30690, CVE-2023-3116, CVE-2023-31222, CVE-2023-31223, CVE-2023-3124, CVE-2023-3126, CVE-2023-31262, CVE-2023-31263, CVE-2023-31275, CVE-2023-31283, CVE-2023-31864, CVE-2023-32216, CVE-2023-32217, CVE-2023-3222, CVE-2023-32220, CVE-2023-32221, CVE-2023-32222, CVE-2023-32224, CVE-2023-32225, CVE-2023-32227, CVE-2023-32228, CVE-2023-32928, CVE-2023-33194, CVE-2023-3423, CVE-2023-34257, CVE-2023-34258, CVE-2023-34276, CVE-2023-34303, CVE-2023-38281, CVE-2023-38282, CVE-2023-3829, CVE-2023-3856, CVE-2023-38568, CVE-2023-38569, CVE-2023-38607, CVE-2023-3861, CVE-2023-38614, CVE-2023-3862, CVE-2023-38625, CVE-2023-3864, CVE-2023-38645, CVE-2023-38647, CVE-2023-3865, CVE-2023-38655, CVE-2023-38658, CVE-2023-39337, CVE-2023-4111, CVE-2023-41112, CVE-2023-4112, CVE-2023-4250, CVE-2023-4290, CVE-2023-43922, CVE-2023-4445, CVE-2023-44450, CVE-2023-44453, CVE-2023-44454, CVE-2023-44458, CVE-2023-4446, CVE-2023-4567, CVE-2023-4681, CVE-2023-46812, CVE-2023-46813, CVE-2023-46814, CVE-2023-46815, CVE-2023-46816, CVE-2023-46818, CVE-2023-4720, CVE-2023-4724, CVE-2023-4752, CVE-2023-4863, CVE-2023-5678, CVE-2024-1234, CVE-2024-21887

### llama31

- **Real** (5): CVE-2019-2725, CVE-2021-3156, CVE-2021-4034, CVE-2021-40444, CVE-2021-44228
- **Hallucinated** (0): none
- **Unverified** (132): CVE-2014-0160, CVE-2017-1000253, CVE-2017-10145, CVE-2017-11882, CVE-2018-0171, CVE-2018-10562, CVE-2018-13153, CVE-2018-13379, CVE-2018-3615, CVE-2018-4878, CVE-2018-7600, CVE-2018-8453, CVE-2019-0547, CVE-2019-0604, CVE-2019-10946, CVE-2019-10947, CVE-2019-11001, CVE-2019-11008, CVE-2019-11009, CVE-2019-11510, CVE-2019-11539, CVE-2019-11596, CVE-2019-11598, CVE-2019-11599, CVE-2019-11708, CVE-2019-11791, CVE-2019-1181, CVE-2019-11815, CVE-2019-11826, CVE-2019-11881, CVE-2019-11899, CVE-2019-1204, CVE-2019-13239, CVE-2019-14451, CVE-2019-1458, CVE-2019-16759, CVE-2019-19728, CVE-2019-19781, CVE-2019-2629, CVE-2019-3396, CVE-2019-3398, CVE-2019-5076, CVE-2019-5736, CVE-2019-6440, CVE-2019-6445, CVE-2019-6446, CVE-2019-8330, CVE-2019-9468, CVE-2020-0017, CVE-2020-0074, CVE-2020-0601, CVE-2020-0608, CVE-2020-0609, CVE-2020-0796, CVE-2020-0942, CVE-2020-10135, CVE-2020-10189, CVE-2020-11774, CVE-2020-11934, CVE-2020-1234, CVE-2020-12805, CVE-2020-12812, CVE-2020-12856, CVE-2020-1472, CVE-2020-14720, CVE-2020-14744, CVE-2020-14746, CVE-2020-14775, CVE-2020-14776, CVE-2020-14777, CVE-2020-14778, CVE-2020-14779, CVE-2020-15078, CVE-2020-15505, CVE-2020-1553, CVE-2020-1555, CVE-2020-15586, CVE-2020-15706, CVE-2020-1576, CVE-2020-15782, CVE-2020-25506, CVE-2020-2555, CVE-2020-2556, CVE-2020-25592, CVE-2020-25594, CVE-2020-25595, CVE-2020-2652, CVE-2020-2656, CVE-2020-2659, CVE-2020-3113, CVE-2020-3566, CVE-2020-4006, CVE-2020-4009, CVE-2020-5907, CVE-2021-0001, CVE-2021-1234, CVE-2021-1609, CVE-2021-1647, CVE-2021-21449, CVE-2021-21900, CVE-2021-22989, CVE-2021-26691, CVE-2021-30148, CVE-2021-30154, CVE-2021-3019, CVE-2021-3064, CVE-2021-31440, CVE-2021-31955, CVE-2021-33154, CVE-2021-33197, CVE-2021-33899, CVE-2021-34700, CVE-2021-34755, CVE-2021-3492, CVE-2021-36222, CVE-2021-3711, CVE-2021-39157, CVE-2021-40539, CVE-2021-42252, CVE-2021-43890, CVE-2021-4405, CVE-2022-0001, CVE-2022-0541, CVE-2022-1234, CVE-2022-1474, CVE-2022-20624, CVE-2022-20966, CVE-2022-27255, CVE-2022-29162, CVE-2022-32500, CVE-2022-35760, CVE-2023-1234

### gemma3n

- **Real** (1): CVE-2021-44228
- **Hallucinated** (0): none
- **Unverified** (28): CVE-2014-4562, CVE-2017-0144, CVE-2017-0145, CVE-2017-10010, CVE-2017-11882, CVE-2019-0708, CVE-2019-11090, CVE-2020-0609, CVE-2020-14724, CVE-2021-23233, CVE-2022-44864, CVE-2023-0123, CVE-2023-0124, CVE-2023-0129, CVE-2023-0666, CVE-2023-0667, CVE-2023-0669, CVE-2023-1234, CVE-2023-22997, CVE-2023-22998, CVE-2023-23397, CVE-2023-23398, CVE-2023-23517, CVE-2023-23528, CVE-2023-23529, CVE-2023-32221, CVE-2023-4567, CVE-2024-5678

### qwen3-nothink

- **Real** (2): CVE-2021-40444, CVE-2021-44228
- **Hallucinated** (0): none
- **Unverified** (226): CVE-2017-0144, CVE-2020-3581, CVE-2020-3584, CVE-2021-23094, CVE-2021-23095, CVE-2021-26855, CVE-2021-3450, CVE-2021-34507, CVE-2021-34508, CVE-2021-34509, CVE-2021-3451, CVE-2021-34523, CVE-2021-34526, CVE-2021-34527, CVE-2021-34528, CVE-2021-34529, CVE-2021-34530, CVE-2021-40445, CVE-2021-4104, CVE-2021-41379, CVE-2021-44229, CVE-2021-44744, CVE-2021-44832, CVE-2021-44872, CVE-2021-44875, CVE-2021-45046, CVE-2022-2161, CVE-2022-2164, CVE-2022-21642, CVE-2022-21650, CVE-2022-21657, CVE-2022-21858, CVE-2022-21898, CVE-2022-22940, CVE-2022-22944, CVE-2022-22946, CVE-2022-24137, CVE-2022-24736, CVE-2022-24866, CVE-2022-24867, CVE-2022-24868, CVE-2022-34567, CVE-2022-39329, CVE-2022-5645, CVE-2022-5678, CVE-2023-1234, CVE-2023-12345, CVE-2023-1814, CVE-2023-1815, CVE-2023-1845, CVE-2023-1846, CVE-2023-1912, CVE-2023-1913, CVE-2023-1982, CVE-2023-1983, CVE-2023-1984, CVE-2023-21180, CVE-2023-21181, CVE-2023-21182, CVE-2023-2122, CVE-2023-2164, CVE-2023-2168, CVE-2023-2169, CVE-2023-22470, CVE-2023-22478, CVE-2023-22513, CVE-2023-22517, CVE-2023-22746, CVE-2023-2280, CVE-2023-22808, CVE-2023-22809, CVE-2023-2281, CVE-2023-22810, CVE-2023-22811, CVE-2023-2282, CVE-2023-22821, CVE-2023-22822, CVE-2023-22823, CVE-2023-22826, CVE-2023-22828, CVE-2023-22829, CVE-2023-22843, CVE-2023-22845, CVE-2023-22846, CVE-2023-2285, CVE-2023-22855, CVE-2023-2287, CVE-2023-22872, CVE-2023-2288, CVE-2023-2289, CVE-2023-22891, CVE-2023-22892, CVE-2023-22893, CVE-2023-22894, CVE-2023-22895, CVE-2023-22896, CVE-2023-22897, CVE-2023-22898, CVE-2023-2290, CVE-2023-22912, CVE-2023-22925, CVE-2023-22947, CVE-2023-24193, CVE-2023-24194, CVE-2023-24314, CVE-2023-24456, CVE-2023-24457, CVE-2023-24723, CVE-2023-24886, CVE-2023-24906, CVE-2023-24907, CVE-2023-25815, CVE-2023-25816, CVE-2023-25817, CVE-2023-27555, CVE-2023-2825, CVE-2023-28254, CVE-2023-28255, CVE-2023-29157, CVE-2023-29163, CVE-2023-29276, CVE-2023-2928, CVE-2023-2935, CVE-2023-29358, CVE-2023-2937, CVE-2023-29380, CVE-2023-29381, CVE-2023-29411, CVE-2023-29412, CVE-2023-2942, CVE-2023-29423, CVE-2023-29424, CVE-2023-29425, CVE-2023-2943, CVE-2023-29451, CVE-2023-29452, CVE-2023-29455, CVE-2023-29456, CVE-2023-29461, CVE-2023-29464, CVE-2023-29465, CVE-2023-2949, CVE-2023-29494, CVE-2023-29501, CVE-2023-29503, CVE-2023-29510, CVE-2023-29515, CVE-2023-29528, CVE-2023-29529, CVE-2023-29775, CVE-2023-29776, CVE-2023-2978, CVE-2023-2980, CVE-2023-2987, CVE-2023-29931, CVE-2023-30203, CVE-2023-30204, CVE-2023-3021, CVE-2023-3022, CVE-2023-30225, CVE-2023-30226, CVE-2023-3023, CVE-2023-30272, CVE-2023-30273, CVE-2023-3038, CVE-2023-30451, CVE-2023-30452, CVE-2023-30847, CVE-2023-30848, CVE-2023-3120, CVE-2023-3121, CVE-2023-3122, CVE-2023-3126, CVE-2023-31264, CVE-2023-31293, CVE-2023-31294, CVE-2023-31398, CVE-2023-31399, CVE-2023-3215, CVE-2023-3216, CVE-2023-3217, CVE-2023-3222, CVE-2023-32222, CVE-2023-32223, CVE-2023-32225, CVE-2023-3384, CVE-2023-3402, CVE-2023-34449, CVE-2023-3856, CVE-2023-3864, CVE-2023-38640, CVE-2023-38652, CVE-2023-38653, CVE-2023-3984, CVE-2023-4106, CVE-2023-4107, CVE-2023-41112, CVE-2023-41203, CVE-2023-4261, CVE-2023-4262, CVE-2023-42896, CVE-2023-4443, CVE-2023-4445, CVE-2023-44451, CVE-2023-44455, CVE-2023-44456, CVE-2023-4446, CVE-2023-4447, CVE-2023-4567, CVE-2023-45678, CVE-2023-4590, CVE-2023-4681, CVE-2023-46815, CVE-2023-4682, CVE-2023-4721, CVE-2023-4722, CVE-2023-4723, CVE-2023-5678, CVE-2023-9012, CVE-2024-0123, CVE-2024-1234, CVE-2024-21245, CVE-2024-23862, CVE-2024-25262, CVE-2024-28564, CVE-2024-29553

### phi4

- **Real** (2): CVE-2021-40444, CVE-2021-44228
- **Hallucinated** (0): none
- **Unverified** (16): CVE-2019-15126, CVE-2019-19781, CVE-2020-10135, CVE-2020-1234, CVE-2020-1472, CVE-2020-15999, CVE-2020-3946, CVE-2021-2019, CVE-2021-28658, CVE-2021-34523, CVE-2021-41379, CVE-2021-45046, CVE-2022-21824, CVE-2022-22963, CVE-2022-26134, CVE-2022-30190

### mistral

- **Real** (3): CVE-2020-0688, CVE-2021-4034, CVE-2021-40444
- **Hallucinated** (0): none
- **Unverified** (91): CVE-2014-6271, CVE-2015-1635, CVE-2017-0144, CVE-2017-0145, CVE-2017-0199, CVE-2017-10271, CVE-2017-11292, CVE-2017-11882, CVE-2017-15893, CVE-2017-17215, CVE-2017-5638, CVE-2017-5689, CVE-2017-5753, CVE-2017-7494, CVE-2017-8759, CVE-2018-10008, CVE-2018-1000801, CVE-2018-13379, CVE-2018-13699, CVE-2019-0604, CVE-2019-10559, CVE-2019-11510, CVE-2019-12305, CVE-2019-12337, CVE-2019-12338, CVE-2019-12339, CVE-2019-12345, CVE-2019-123456, CVE-2019-12358, CVE-2019-12411, CVE-2019-12687, CVE-2019-13257, CVE-2019-13278, CVE-2019-13476, CVE-2019-1350, CVE-2019-13501, CVE-2019-13773, CVE-2019-13876, CVE-2019-13877, CVE-2019-1624, CVE-2019-19781, CVE-2019-6340, CVE-2019-8641, CVE-2020-12812, CVE-2020-1350, CVE-2020-13504, CVE-2020-13507, CVE-2020-1472, CVE-2020-16898, CVE-2020-3583, CVE-2020-3607, CVE-2020-3618, CVE-2020-3620, CVE-2020-36589, CVE-2020-36680, CVE-2020-5902, CVE-2020-8179, CVE-2020-8554, CVE-2020-9458, CVE-2021-1609, CVE-2021-20037, CVE-2021-26751, CVE-2021-26756, CVE-2021-26855, CVE-2021-27004, CVE-2021-27005, CVE-2021-27019, CVE-2021-30551, CVE-2021-30556, CVE-2021-30559, CVE-2021-3066, CVE-2021-30668, CVE-2021-3069, CVE-2021-30695, CVE-2021-3574, CVE-2021-3575, CVE-2021-3576, CVE-2021-3578, CVE-2021-3589, CVE-2021-36780, CVE-2021-36795, CVE-2021-36934, CVE-2021-37869, CVE-2021-39763, CVE-2021-40506, CVE-2022-1317, CVE-2022-1319, CVE-2022-30166, CVE-2022-3065, CVE-2022-30668, CVE-2023-1975

## 7. Condition Effects on CVE Citation

| Model | Actor | Level | Records | With CVEs | Rate |
|-------|-------|-------|---------|-----------|------|
| deepseek-r1 | China | Confirmed | 192 | 63 | 32.8% |
| deepseek-r1 | China | Suspected | 191 | 71 | 37.2% |
| deepseek-r1 | DPRK | Confirmed | 191 | 80 | 41.9% |
| deepseek-r1 | DPRK | Suspected | 192 | 67 | 34.9% |
| deepseek-r1 | Iran | Confirmed | 192 | 69 | 35.9% |
| deepseek-r1 | Iran | Suspected | 191 | 73 | 38.2% |
| deepseek-r1 | Neutral | Neutral | 192 | 81 | 42.2% |
| deepseek-r1 | Russia | Confirmed | 192 | 68 | 35.4% |
| deepseek-r1 | Russia | Suspected | 190 | 71 | 37.4% |
| deepseek-r1 | US | Confirmed | 192 | 56 | 29.2% |
| deepseek-r1 | US | Suspected | 192 | 68 | 35.4% |
| qwen3 | China | Confirmed | 192 | 98 | 51.0% |
| qwen3 | China | Suspected | 191 | 120 | 62.8% |
| qwen3 | DPRK | Confirmed | 192 | 116 | 60.4% |
| qwen3 | DPRK | Suspected | 192 | 110 | 57.3% |
| qwen3 | Iran | Confirmed | 192 | 96 | 50.0% |
| qwen3 | Iran | Suspected | 192 | 112 | 58.3% |
| qwen3 | Neutral | Neutral | 192 | 120 | 62.5% |
| qwen3 | Russia | Confirmed | 191 | 90 | 47.1% |
| qwen3 | Russia | Suspected | 191 | 111 | 58.1% |
| qwen3 | US | Confirmed | 192 | 106 | 55.2% |
| qwen3 | US | Suspected | 192 | 113 | 58.9% |
| llama31 | China | Confirmed | 192 | 66 | 34.4% |
| llama31 | China | Suspected | 192 | 73 | 38.0% |
| llama31 | DPRK | Confirmed | 192 | 55 | 28.6% |
| llama31 | DPRK | Suspected | 192 | 75 | 39.1% |
| llama31 | Iran | Confirmed | 192 | 70 | 36.5% |
| llama31 | Iran | Suspected | 192 | 61 | 31.8% |
| llama31 | Neutral | Neutral | 192 | 60 | 31.2% |
| llama31 | Russia | Confirmed | 192 | 74 | 38.5% |
| llama31 | Russia | Suspected | 192 | 81 | 42.2% |
| llama31 | US | Confirmed | 192 | 58 | 30.2% |
| llama31 | US | Suspected | 192 | 61 | 31.8% |
| gemma3n | China | Confirmed | 192 | 4 | 2.1% |
| gemma3n | China | Suspected | 192 | 4 | 2.1% |
| gemma3n | DPRK | Confirmed | 192 | 6 | 3.1% |
| gemma3n | DPRK | Suspected | 192 | 3 | 1.6% |
| gemma3n | Iran | Confirmed | 192 | 3 | 1.6% |
| gemma3n | Iran | Suspected | 192 | 4 | 2.1% |
| gemma3n | Neutral | Neutral | 192 | 8 | 4.2% |
| gemma3n | Russia | Confirmed | 192 | 4 | 2.1% |
| gemma3n | Russia | Suspected | 192 | 1 | 0.5% |
| gemma3n | US | Confirmed | 192 | 3 | 1.6% |
| gemma3n | US | Suspected | 192 | 0 | 0.0% |
| qwen3-nothink | China | Confirmed | 192 | 38 | 19.8% |
| qwen3-nothink | China | Suspected | 192 | 56 | 29.2% |
| qwen3-nothink | DPRK | Confirmed | 192 | 39 | 20.3% |
| qwen3-nothink | DPRK | Suspected | 192 | 48 | 25.0% |
| qwen3-nothink | Iran | Confirmed | 192 | 40 | 20.8% |
| qwen3-nothink | Iran | Suspected | 192 | 60 | 31.2% |
| qwen3-nothink | Neutral | Neutral | 192 | 44 | 22.9% |
| qwen3-nothink | Russia | Confirmed | 192 | 45 | 23.4% |
| qwen3-nothink | Russia | Suspected | 192 | 67 | 34.9% |
| qwen3-nothink | US | Confirmed | 192 | 38 | 19.8% |
| qwen3-nothink | US | Suspected | 192 | 59 | 30.7% |
| phi4 | China | Confirmed | 192 | 7 | 3.6% |
| phi4 | China | Suspected | 192 | 4 | 2.1% |
| phi4 | DPRK | Confirmed | 192 | 6 | 3.1% |
| phi4 | DPRK | Suspected | 192 | 5 | 2.6% |
| phi4 | Iran | Confirmed | 192 | 4 | 2.1% |
| phi4 | Iran | Suspected | 192 | 3 | 1.6% |
| phi4 | Neutral | Neutral | 192 | 5 | 2.6% |
| phi4 | Russia | Confirmed | 192 | 6 | 3.1% |
| phi4 | Russia | Suspected | 192 | 6 | 3.1% |
| phi4 | US | Confirmed | 192 | 7 | 3.6% |
| phi4 | US | Suspected | 192 | 5 | 2.6% |
| mistral | China | Confirmed | 192 | 23 | 12.0% |
| mistral | China | Suspected | 192 | 16 | 8.3% |
| mistral | DPRK | Confirmed | 192 | 17 | 8.8% |
| mistral | DPRK | Suspected | 192 | 23 | 12.0% |
| mistral | Iran | Confirmed | 192 | 20 | 10.4% |
| mistral | Iran | Suspected | 192 | 18 | 9.4% |
| mistral | Neutral | Neutral | 192 | 31 | 16.2% |
| mistral | Russia | Confirmed | 192 | 24 | 12.5% |
| mistral | Russia | Suspected | 192 | 21 | 10.9% |
| mistral | US | Confirmed | 192 | 12 | 6.2% |
| mistral | US | Suspected | 192 | 25 | 13.0% |

## 8. Temperature Effects on CVE Citation

| Model | Temperature | Records | With CVEs | Rate | Mean CVEs (present) |
|-------|-------------|---------|-----------|------|---------------------|
| deepseek-r1 | 0.0 | 1054 | 408 | 38.7% | 1.804 |
| deepseek-r1 | 0.7 | 1053 | 359 | 34.1% | 1.696 |
| qwen3 | 0.0 | 1053 | 594 | 56.4% | 1.598 |
| qwen3 | 0.7 | 1056 | 598 | 56.6% | 1.580 |
| llama31 | 0.0 | 1056 | 384 | 36.4% | 1.089 |
| llama31 | 0.7 | 1056 | 350 | 33.1% | 1.137 |
| gemma3n | 0.0 | 1056 | 20 | 1.9% | 1.400 |
| gemma3n | 0.7 | 1056 | 20 | 1.9% | 1.800 |
| qwen3-nothink | 0.0 | 1056 | 236 | 22.4% | 2.000 |
| qwen3-nothink | 0.7 | 1056 | 298 | 28.2% | 1.859 |
| phi4 | 0.0 | 1056 | 22 | 2.1% | 1.000 |
| phi4 | 0.7 | 1056 | 36 | 3.4% | 1.028 |
| mistral | 0.0 | 1056 | 104 | 9.8% | 1.538 |
| mistral | 0.7 | 1056 | 126 | 11.9% | 1.532 |

## Summary

**Fixation detected** in: deepseek-r1, llama31, phi4

### deepseek-r1 Phase 1 → Phase 2 Evolution

- Phase 1: 24 CVE records, PwnKit at 75%, Shannon H ≈ low (dominated by single CVE)
- Phase 2: 767 CVE records, top CVE (CVE-2021-4034) at 73.0%, Shannon H = 4.789
- **Fixation persists** — CVE-2021-4034 exceeds 40% threshold
