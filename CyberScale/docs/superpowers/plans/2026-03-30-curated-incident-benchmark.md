# Curated Incident Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a human-curated benchmark dataset of real-world cyber incidents with ground-truth T/O labels, and a benchmark script that measures how Phase 3 models perform on real data vs synthetic data.

**Architecture:** A JSON dataset (`data/reference/curated_incidents.json`) of 40 real incidents mapped to the Blueprint T1-T4/O1-O4 schema with documented rationale. A loader module validates and converts incidents into model inputs. A benchmark script runs both models + matrix, generates a comparison report (curated vs synthetic). The dataset is intentionally small (40 incidents) — quality and rationale matter more than volume.

**Tech Stack:** Python 3.12, pytest, existing TechnicalClassifier/OperationalClassifier, existing matrix module, JSON schema validation.

---

### Task 1: Define the curated incident JSON schema

**Files:**
- Create: `data/reference/curated_incidents_schema.json`

This schema defines what each curated incident looks like. Every incident needs: metadata (id, name, date, source URL), a natural-language description, structured T-model fields, structured O-model fields, ground-truth labels, and human rationale for the labels.

- [ ] **Step 1: Create the JSON schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CyberScale Curated Incident Dataset",
  "type": "object",
  "required": ["version", "incidents"],
  "properties": {
    "version": { "type": "string" },
    "incidents": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "id", "name", "date", "sources", "description",
          "t_fields", "o_fields", "expected_t", "expected_o", "rationale"
        ],
        "properties": {
          "id": { "type": "string", "pattern": "^INC-[0-9]{3}$" },
          "name": { "type": "string" },
          "date": { "type": "string", "format": "date" },
          "sources": {
            "type": "array",
            "items": { "type": "string" },
            "minItems": 1
          },
          "description": { "type": "string", "minLength": 50 },
          "t_fields": {
            "type": "object",
            "required": [
              "service_disruption", "affected_entities",
              "sectors_affected", "cascading", "data_compromise"
            ],
            "properties": {
              "service_disruption": { "enum": ["partial", "significant", "complete", "sustained"] },
              "affected_entities": { "type": "integer", "minimum": 1 },
              "sectors_affected": { "type": "integer", "minimum": 1 },
              "cascading": { "enum": ["none", "limited", "cross_sector", "uncontrolled"] },
              "data_compromise": { "enum": ["none", "operational", "sensitive", "systemic"] }
            }
          },
          "o_fields": {
            "type": "object",
            "required": [
              "sectors_affected", "entity_relevance", "ms_affected",
              "cross_border_pattern", "coordination_needs", "capacity_exceeded"
            ],
            "properties": {
              "sectors_affected": { "type": "string" },
              "entity_relevance": { "enum": ["non_essential", "essential", "high_relevance", "systemic"] },
              "ms_affected": { "type": "integer", "minimum": 1 },
              "cross_border_pattern": { "enum": ["none", "limited", "significant", "systemic"] },
              "coordination_needs": { "enum": ["national", "eu_info", "eu_active", "full_ipcr"] },
              "capacity_exceeded": { "type": "boolean" }
            }
          },
          "expected_t": { "enum": ["T1", "T2", "T3", "T4"] },
          "expected_o": { "enum": ["O1", "O2", "O3", "O4"] },
          "rationale": {
            "type": "object",
            "required": ["t_rationale", "o_rationale"],
            "properties": {
              "t_rationale": { "type": "string", "minLength": 20 },
              "o_rationale": { "type": "string", "minLength": 20 }
            }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add data/reference/curated_incidents_schema.json
git commit -m "feat(v2): add JSON schema for curated incident benchmark dataset"
```

---

### Task 2: Create the curated incident dataset

**Files:**
- Create: `data/reference/curated_incidents.json`

Curate 40 real-world incidents across all 4×4 T/O level combinations. Target distribution: ~3 incidents per T-level (12 total minimum), ~3 per O-level (12 total minimum), with the rest filling gaps in the T×O matrix. Every incident must reference a real event with public sources.

**Key principle:** The description field must be written as a CSIRT analyst would describe the incident — no synthetic templates, no structured-field leakage into the narrative. This is what makes it a real benchmark: the model must handle natural language that doesn't match its training distribution.

- [ ] **Step 1: Create the dataset file with all 40 incidents**

The full file is large, so here is the structure with the first 8 representative incidents (one per T and O level). The implementer must complete all 40 following this exact pattern, sourcing from ENISA Threat Landscape reports, CERT-EU advisories, and public incident disclosures.

```json
{
  "version": "1.0",
  "description": "Human-curated benchmark dataset of real-world cyber incidents mapped to Blueprint T/O levels. Each incident includes public sources and rationale for label assignment.",
  "incidents": [
    {
      "id": "INC-001",
      "name": "WannaCry ransomware (2017)",
      "date": "2017-05-12",
      "sources": [
        "https://www.enisa.europa.eu/publications/info-notes/wannacry-ransomware-outburst",
        "https://www.europol.europa.eu/media-press/newsroom/news/wannacry-ransomware-what-we-know"
      ],
      "description": "Global ransomware campaign exploiting EternalBlue SMB vulnerability spread autonomously across networks worldwide. NHS hospitals in the UK cancelled thousands of appointments and diverted ambulances. Renault halted production at multiple factories in France. Deutsche Bahn passenger information systems failed across Germany. The worm propagated without user interaction, encrypting files and demanding Bitcoin ransom.",
      "t_fields": {
        "service_disruption": "sustained",
        "affected_entities": 150,
        "sectors_affected": 5,
        "cascading": "uncontrolled",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "health, transport, digital infrastructure, manufacturing, public administration",
        "entity_relevance": "systemic",
        "ms_affected": 8,
        "cross_border_pattern": "systemic",
        "coordination_needs": "full_ipcr",
        "capacity_exceeded": true
      },
      "expected_t": "T4",
      "expected_o": "O4",
      "rationale": {
        "t_rationale": "Sustained disruption via self-propagating worm. 150+ entities affected across 5+ sectors with uncontrolled cascading. Operational data encrypted (not exfiltrated). Meets all T4 criteria.",
        "o_rationale": "Systemic entity relevance (NHS, Deutsche Bahn). 8+ EU member states affected. Systemic cross-border pattern. Required full IPCR-level coordination. National CSIRT capacity exceeded in multiple countries."
      }
    },
    {
      "id": "INC-002",
      "name": "NotPetya destructive attack (2017)",
      "date": "2017-06-27",
      "sources": [
        "https://www.enisa.europa.eu/publications/info-notes/notpetya-ransomware-campaign",
        "https://www.wired.com/story/notpetya-cyberattack-ukraine-russia-code-crashed-the-world/"
      ],
      "description": "Destructive wiper malware disguised as ransomware, initially distributed via compromised Ukrainian tax software M.E.Doc. Maersk lost all domain controllers globally and rebuilt 45,000 PCs and 4,000 servers. Merck pharmaceutical operations halted for weeks, costing over $800M. Saint-Gobain, Mondelez, and TNT Express suffered major operational outages. Total estimated damages exceeded $10 billion globally.",
      "t_fields": {
        "service_disruption": "sustained",
        "affected_entities": 150,
        "sectors_affected": 5,
        "cascading": "uncontrolled",
        "data_compromise": "systemic"
      },
      "o_fields": {
        "sectors_affected": "transport, health, manufacturing, digital infrastructure, financial_market",
        "entity_relevance": "systemic",
        "ms_affected": 8,
        "cross_border_pattern": "systemic",
        "coordination_needs": "full_ipcr",
        "capacity_exceeded": true
      },
      "expected_t": "T4",
      "expected_o": "O4",
      "rationale": {
        "t_rationale": "Sustained disruption — Maersk rebuilt entire IT infrastructure over 10 days. 150+ entities across 5+ sectors. Uncontrolled cascading via supply chain. Systemic data compromise (wiper destroyed data irrecoverably).",
        "o_rationale": "Systemic entities (Maersk handles 20% of global shipping). 8+ EU member states. Full IPCR coordination required. National capacity exceeded — multiple EU CERTs coordinated response."
      }
    },
    {
      "id": "INC-003",
      "name": "SolarWinds Orion supply chain compromise (2020)",
      "date": "2020-12-13",
      "sources": [
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2021",
        "https://www.fireeye.com/blog/threat-research/2020/12/evasive-attacker-leverages-solarwinds-supply-chain-compromises-with-sunburst-backdoor.html"
      ],
      "description": "State-sponsored actors compromised SolarWinds build system to insert SUNBURST backdoor into Orion IT monitoring software updates. Approximately 18,000 organisations installed the trojanized update. Confirmed victims included EU government agencies, the European Parliament, and technology companies. The attackers maintained persistent access for months, exfiltrating sensitive communications and documents through encrypted channels.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 150,
        "sectors_affected": 4,
        "cascading": "uncontrolled",
        "data_compromise": "systemic"
      },
      "o_fields": {
        "sectors_affected": "public administration, digital infrastructure, space, defence",
        "entity_relevance": "systemic",
        "ms_affected": 7,
        "cross_border_pattern": "systemic",
        "coordination_needs": "eu_active",
        "capacity_exceeded": false
      },
      "expected_t": "T4",
      "expected_o": "O3",
      "rationale": {
        "t_rationale": "Partial disruption (espionage, not destructive), but 150+ entities via supply chain, 4 sectors, uncontrolled cascading via trusted update channel, systemic data compromise of government communications. Systemic data compromise alone triggers T4.",
        "o_rationale": "Systemic entity relevance. 7 EU member states confirmed. Systemic cross-border. EU-active coordination (ENISA advisory, EU-CyCLONe discussion). Capacity not exceeded — espionage response is slower-burn than ransomware crisis."
      }
    },
    {
      "id": "INC-004",
      "name": "Irish HSE ransomware (2021)",
      "date": "2021-05-14",
      "sources": [
        "https://www.hse.ie/eng/services/publications/conti-cyber-attack-on-the-hse-independent-post-incident-review.pdf",
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2021"
      ],
      "description": "Conti ransomware group encrypted systems across Ireland's Health Service Executive, forcing the shutdown of all IT systems nationwide. Hospitals reverted to paper records for weeks. Cancer treatments, diagnostic imaging, and laboratory services were severely disrupted. Patient data for approximately 100,000 individuals was exfiltrated. Recovery took over four months and cost an estimated EUR 100 million.",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 55,
        "sectors_affected": 1,
        "cascading": "limited",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "health",
        "entity_relevance": "high_relevance",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": true
      },
      "expected_t": "T3",
      "expected_o": "O2",
      "rationale": {
        "t_rationale": "Complete disruption of all HSE IT systems. 55 hospitals/facilities affected. Single sector (health). Limited cascading (contained to HSE network). Sensitive data compromise (patient records exfiltrated). Complete disruption + sensitive data = T3.",
        "o_rationale": "High relevance entity (sole national health provider). Single member state (Ireland). No cross-border pattern. National-only coordination. However, national capacity was exceeded — Irish NCSC required external assistance. Capacity exceeded pushes to O2 despite single-MS scope."
      }
    },
    {
      "id": "INC-005",
      "name": "Colonial Pipeline ransomware (2021)",
      "date": "2021-05-07",
      "sources": [
        "https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-131a",
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2021"
      ],
      "description": "DarkSide ransomware group attacked Colonial Pipeline's business IT systems, leading the company to proactively shut down its operational technology pipeline delivering 45% of US East Coast fuel supply. While the OT systems were not directly compromised, the precautionary shutdown caused fuel shortages and panic buying across the southeastern United States for six days. The company paid a 75 Bitcoin ransom (approximately $4.4 million).",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 1,
        "sectors_affected": 2,
        "cascading": "cross_sector",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "energy, transport",
        "entity_relevance": "systemic",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Complete disruption (pipeline shutdown for 6 days). Single entity but cross-sector cascading (energy → transport fuel supply). Operational data compromised. Complete disruption triggers T3.",
        "o_rationale": "Systemic entity relevance but US-only, not EU. In EU context: single member state, national coordination, no cross-border. Included as non-EU reference point — demonstrates that high technical severity doesn't always mean high EU operational impact."
      }
    },
    {
      "id": "INC-006",
      "name": "Kaseya VSA supply chain ransomware (2021)",
      "date": "2021-07-02",
      "sources": [
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-for-supply-chain-attacks",
        "https://helpdesk.kaseya.com/hc/en-gb/articles/4403440684689"
      ],
      "description": "REvil ransomware group exploited zero-day vulnerabilities in Kaseya VSA remote management software to push ransomware to managed service provider customers. Over 1,500 downstream businesses in multiple countries were encrypted through approximately 60 compromised MSPs. Coop Sweden closed 800 stores after their point-of-sale systems were locked. Schools in New Zealand and companies across Europe were affected. The $70 million ransom demand was the largest ever at the time.",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 55,
        "sectors_affected": 3,
        "cascading": "cross_sector",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "digital infrastructure, manufacturing, food",
        "entity_relevance": "essential",
        "ms_affected": 4,
        "cross_border_pattern": "significant",
        "coordination_needs": "eu_active",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O3",
      "rationale": {
        "t_rationale": "Complete disruption via supply chain — MSP customers fully encrypted. 55+ EU entities across 3 sectors. Cross-sector cascading (IT services → retail → manufacturing). Operational data compromise. T3 via complete disruption + cross-sector cascading.",
        "o_rationale": "Essential entity relevance (MSPs serve essential services). 4 EU member states significantly affected. Significant cross-border pattern. EU-active coordination (ENISA published advisory, EU CERTs coordinated). O3 via eu_active + significant cross-border."
      }
    },
    {
      "id": "INC-007",
      "name": "Belgian Ministry of Defence Log4Shell exploitation (2021)",
      "date": "2021-12-20",
      "sources": [
        "https://www.vrt.be/vrtnws/en/2021/12/20/belgian-ministry-of-defence-confirms-cyber-attack/",
        "https://therecord.media/belgian-defense-ministry-confirms-cyberattack-linked-to-log4j-vulnerability"
      ],
      "description": "Attackers exploited the Log4Shell vulnerability (CVE-2021-44228) to compromise systems at the Belgian Ministry of Defence. The ministry confirmed a cyber attack on its network and shut down parts of its infrastructure for several days as a precautionary measure. Email and other communication systems were disrupted. The Belgian CERT coordinated response nationally.",
      "t_fields": {
        "service_disruption": "significant",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "public administration",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T2",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Significant disruption (partial shutdown, not full outage). Single entity, single sector, no cascading. Operational data compromise assumed. Significant disruption triggers T2.",
        "o_rationale": "Essential entity (defence ministry). Single member state. No cross-border. National coordination only. Capacity not exceeded. Single-MS + national coordination = O1."
      }
    },
    {
      "id": "INC-008",
      "name": "University of Maastricht ransomware (2019)",
      "date": "2019-12-24",
      "sources": [
        "https://www.maastrichtuniversity.nl/file/lobreportpdf",
        "https://www.fox-it.com/en/news-events/press-releases/fox-it-helps-maastricht-university-regain-access/"
      ],
      "description": "Clop ransomware encrypted nearly all Windows systems at Maastricht University during the Christmas holiday period, affecting email, library services, and research data access. The university paid a 30 Bitcoin ransom to restore operations. 267 servers were encrypted. Scientific research data was temporarily inaccessible but not exfiltrated. Recovery took several weeks.",
      "t_fields": {
        "service_disruption": "significant",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "none"
      },
      "o_fields": {
        "sectors_affected": "research",
        "entity_relevance": "non_essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T2",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Significant disruption (systems down for weeks but university continued partial operations). Single entity, single sector, no cascading, no data exfiltration. Significant disruption = T2.",
        "o_rationale": "Non-essential entity (university/research). Single member state. No cross-border. National coordination only. All O1 indicators."
      }
    },
    {
      "id": "INC-009",
      "name": "MOVEit Transfer mass exploitation (2023)",
      "date": "2023-05-31",
      "sources": [
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2023",
        "https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-158a"
      ],
      "description": "Cl0p ransomware group exploited a zero-day SQL injection in Progress Software's MOVEit Transfer file sharing application. Over 2,500 organisations worldwide were affected through data exfiltration, including Shell, British Airways, BBC, and multiple EU government agencies. The group exfiltrated data from managed file transfer instances without deploying ransomware, instead threatening publication. Personal data of over 60 million individuals was compromised.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 150,
        "sectors_affected": 4,
        "cascading": "cross_sector",
        "data_compromise": "systemic"
      },
      "o_fields": {
        "sectors_affected": "digital infrastructure, energy, transport, public administration",
        "entity_relevance": "high_relevance",
        "ms_affected": 6,
        "cross_border_pattern": "significant",
        "coordination_needs": "eu_active",
        "capacity_exceeded": false
      },
      "expected_t": "T4",
      "expected_o": "O3",
      "rationale": {
        "t_rationale": "Partial disruption (data theft, not service outage). But 150+ entities, 4 sectors, cross-sector cascading via shared file transfer platform, systemic data compromise (60M+ individuals). Systemic data compromise alone triggers T4.",
        "o_rationale": "High relevance entities (Shell, BA, government). 6 EU member states. Significant cross-border. EU-active coordination (ENISA + multiple CERTs). Capacity not exceeded. O3 via eu_active + significant cross-border."
      }
    },
    {
      "id": "INC-010",
      "name": "Change Healthcare ransomware (2024)",
      "date": "2024-02-21",
      "sources": [
        "https://www.hhs.gov/hipaa/for-professionals/special-topics/change-healthcare-cybersecurity-incident/index.html",
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2024"
      ],
      "description": "ALPHV/BlackCat ransomware attack on Change Healthcare disrupted healthcare payment processing across the United States, affecting pharmacies, hospitals, and insurance claims. As the largest healthcare payment processor, the outage prevented electronic prescriptions and insurance verification for weeks. UnitedHealth Group paid a $22 million ransom. Protected health information of approximately 100 million patients was compromised. Predominantly US-focused with limited EU downstream impact on pharmaceutical supply chains.",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 55,
        "sectors_affected": 1,
        "cascading": "limited",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "health",
        "entity_relevance": "essential",
        "ms_affected": 2,
        "cross_border_pattern": "limited",
        "coordination_needs": "eu_info",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O2",
      "rationale": {
        "t_rationale": "Complete disruption (payment processing fully down). 55+ downstream entities in EU. Single sector. Limited cascading. Sensitive data (patient health records). Complete disruption + sensitive data = T3.",
        "o_rationale": "Essential entity (healthcare payments). 2 EU member states with downstream pharma supply impact. Limited cross-border. EU info-sharing coordination (ENISA situational awareness). O2 via eu_info + limited cross-border."
      }
    },
    {
      "id": "INC-011",
      "name": "Norsk Hydro LockerGoga ransomware (2019)",
      "date": "2019-03-19",
      "sources": [
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2019",
        "https://www.hydro.com/en/media/news/2019/hydro-subject-to-cyber-attack/"
      ],
      "description": "LockerGoga ransomware encrypted systems across Norwegian aluminium manufacturer Norsk Hydro, forcing the company to switch to manual operations at smelting plants across Europe. Production continued at reduced capacity using pen-and-paper processes. The company refused to pay the ransom and rebuilt IT infrastructure over months. Estimated financial impact was NOK 800 million (approximately EUR 75 million). Operations in Norway, Qatar, and Brazil were affected.",
      "t_fields": {
        "service_disruption": "significant",
        "affected_entities": 8,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "manufacturing",
        "entity_relevance": "essential",
        "ms_affected": 3,
        "cross_border_pattern": "limited",
        "coordination_needs": "eu_info",
        "capacity_exceeded": false
      },
      "expected_t": "T2",
      "expected_o": "O2",
      "rationale": {
        "t_rationale": "Significant disruption (reduced capacity, not full shutdown — manual operations continued). 8 facilities across 1 sector. No cascading. Operational data encrypted. Significant disruption = T2.",
        "o_rationale": "Essential entity (major EU manufacturer). 3 member states (Norway EEA + EU operations). Limited cross-border pattern. EU info-sharing coordination. O2 via eu_info + limited cross-border."
      }
    },
    {
      "id": "INC-012",
      "name": "German Landkreis Anhalt-Bitterfeld ransomware (2021)",
      "date": "2021-07-06",
      "sources": [
        "https://www.bsi.bund.de/EN/Themen/Unternehmen-und-Organisationen/Informationen-und-Empfehlungen/Empfehlungen-nach-Angriffszielen/Kommunalverwaltungen/kommunalverwaltungen_node.html",
        "https://www.dw.com/en/german-district-declares-first-ever-cyber-catastrophe/a-58205857"
      ],
      "description": "A ransomware attack on the German district of Anhalt-Bitterfeld paralysed local government services for months, leading to Germany's first-ever cyber catastrophe declaration. Citizens could not receive social benefits, register vehicles, or access government services. The district's entire IT infrastructure had to be rebuilt. Approximately 200 municipal employees were unable to work. Personal data of residents was exfiltrated and published on the dark web.",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "public administration",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": true
      },
      "expected_t": "T3",
      "expected_o": "O2",
      "rationale": {
        "t_rationale": "Complete disruption (government services fully offline for months). Single entity, single sector, no cascading. Sensitive data compromised (resident personal data published). Complete disruption + sensitive data = T3.",
        "o_rationale": "Essential entity (local government). Single member state. No cross-border. National coordination. But capacity was exceeded (first cyber catastrophe declaration — federal assistance required). Capacity exceeded pushes from O1 to O2."
      }
    },
    {
      "id": "INC-013",
      "name": "Düsseldorf University Hospital ransomware (2020)",
      "date": "2020-09-10",
      "sources": [
        "https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Publications/Securitysituation/IT-Security-Situation-in-Germany-2020.html",
        "https://apnews.com/article/technology-hacking-europe-b8d72d78fa8c86e0567edc53ef3ec2a0"
      ],
      "description": "Ransomware targeting Düsseldorf University Hospital exploited a Citrix VPN vulnerability and encrypted 30 servers, forcing the hospital to deregister from emergency care. An emergency patient was redirected to a hospital 30 kilometres away and subsequently died — the first death potentially linked to a ransomware attack. The hospital required weeks to restore full IT operations. The attack was apparently intended for the university, not the hospital.",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "none"
      },
      "o_fields": {
        "sectors_affected": "health",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Complete disruption (emergency care deregistered). Single entity, single sector, no cascading, no data compromise. Complete disruption alone triggers T3.",
        "o_rationale": "Essential entity (hospital). Single member state. No cross-border. National coordination only. Capacity not exceeded. All O1 indicators despite the severity of the disruption — operational scope remained local."
      }
    },
    {
      "id": "INC-014",
      "name": "Finnish parliament email breach (2020)",
      "date": "2020-12-28",
      "sources": [
        "https://www.eduskunta.fi/EN/tiedotteet/Pages/Cyberattack-against-Parliament-of-Finland.aspx",
        "https://yle.fi/a/3-11709454"
      ],
      "description": "The Finnish parliament (Eduskunta) disclosed that email accounts of multiple members of parliament had been compromised through exploitation of a vulnerability in the email system. The Finnish Security Intelligence Service (SUPO) attributed the attack to a state-sponsored actor. No service disruption occurred but confidential parliamentary communications were accessed. The breach was discovered months after initial compromise.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "public administration",
        "entity_relevance": "high_relevance",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Partial disruption (email only, parliament operations continued). Single entity, single sector, no cascading. But sensitive data compromise (parliamentary communications). Sensitive data triggers T3 regardless of low disruption.",
        "o_rationale": "High relevance entity (national parliament). Single member state. No cross-border. National coordination only. O1 — despite political sensitivity, operational scope is national and contained."
      }
    },
    {
      "id": "INC-015",
      "name": "EMA COVID vaccine data breach (2020)",
      "date": "2020-12-09",
      "sources": [
        "https://www.ema.europa.eu/en/news/cyberattack-european-medicines-agency",
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2021"
      ],
      "description": "Attackers breached the European Medicines Agency and accessed documents related to the BioNTech/Pfizer COVID-19 vaccine authorisation process. Leaked documents were manipulated before publication to undermine public trust in the vaccines. The EMA confirmed the breach did not affect the regulatory timeline. Confidential regulatory correspondence and internal review documents were exfiltrated. The attack occurred during the most politically sensitive phase of vaccine approval.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "health",
        "entity_relevance": "systemic",
        "ms_affected": 8,
        "cross_border_pattern": "significant",
        "coordination_needs": "eu_active",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O3",
      "rationale": {
        "t_rationale": "Partial disruption (EMA operations continued). Single entity, single sector, no cascading. Sensitive data compromise (vaccine regulatory documents exfiltrated and manipulated). Sensitive data = T3.",
        "o_rationale": "Systemic entity (EMA regulates vaccines for all EU). 8+ member states impacted (all awaiting vaccine approval). Significant cross-border (EU-wide regulatory process). EU-active coordination (ENISA + national CERTs). O3 via systemic entity + eu_active coordination."
      }
    },
    {
      "id": "INC-016",
      "name": "Vodafone Portugal DDoS and sabotage (2022)",
      "date": "2022-02-07",
      "sources": [
        "https://www.reuters.com/business/media-telecom/vodafone-portugal-hit-by-hackers-says-no-client-data-breach-2022-02-08/",
        "https://www.cncs.gov.pt/"
      ],
      "description": "A deliberate and malicious cyberattack against Vodafone Portugal disrupted mobile voice, SMS, data, fixed voice, and television services across the country. The attack targeted core network infrastructure causing nationwide service outages affecting approximately 4 million customers including emergency services and businesses. Fire departments and hospitals reported communication difficulties. Service restoration took several days.",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 1,
        "sectors_affected": 2,
        "cascading": "cross_sector",
        "data_compromise": "none"
      },
      "o_fields": {
        "sectors_affected": "digital infrastructure, health",
        "entity_relevance": "systemic",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": true
      },
      "expected_t": "T3",
      "expected_o": "O2",
      "rationale": {
        "t_rationale": "Complete disruption of all telecom services. Single entity but cross-sector cascading (telecom → health emergency services). No data compromise. Complete disruption + cross-sector = T3.",
        "o_rationale": "Systemic entity (major telecom provider). Single member state. No cross-border. National coordination. Capacity exceeded (emergency services disrupted, national crisis response activated). O2 via capacity exceeded."
      }
    },
    {
      "id": "INC-017",
      "name": "Costa Rica Conti ransomware (2022)",
      "date": "2022-04-17",
      "sources": [
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2022",
        "https://therecord.media/costa-rican-president-declares-state-of-national-emergency-after-conti-ransomware-attacks"
      ],
      "description": "Conti ransomware group attacked multiple Costa Rican government agencies, forcing the president to declare a national state of emergency — the first by any country in response to a cyberattack. Tax collection, customs, and social security systems were disrupted for months. Twenty-seven government institutions were affected. While not an EU incident, it serves as a reference for how a multi-agency government attack maps to the Blueprint framework. Limited EU impact through diplomatic channels only.",
      "t_fields": {
        "service_disruption": "sustained",
        "affected_entities": 25,
        "sectors_affected": 2,
        "cascading": "cross_sector",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "public administration, financial_market",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": true
      },
      "expected_t": "T4",
      "expected_o": "O2",
      "rationale": {
        "t_rationale": "Sustained disruption (months of outages). 25+ entities across 2 sectors. Cross-sector cascading (tax → customs → social security). Sensitive data compromised. Sustained disruption triggers T4.",
        "o_rationale": "Essential entity (government agencies). Single member state context (non-EU, but mapped as if EU equivalent). National coordination. Capacity exceeded (national emergency declared). O2 via capacity exceeded despite national scope."
      }
    },
    {
      "id": "INC-018",
      "name": "European Parliament DDoS (2022)",
      "date": "2022-11-23",
      "sources": [
        "https://www.europarl.europa.eu/news/en/press-room/20221123IPR56219/",
        "https://therecord.media/european-parliament-website-hit-by-ddos-attack"
      ],
      "description": "Pro-Russian hacktivist group Killnet launched a DDoS attack against the European Parliament website shortly after MEPs voted to designate Russia as a state sponsor of terrorism. The parliament's public website was intermittently unavailable for several hours. Internal parliamentary systems and legislative processes were not affected. The attack was primarily symbolic and politically motivated.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "none"
      },
      "o_fields": {
        "sectors_affected": "public administration",
        "entity_relevance": "high_relevance",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "eu_info",
        "capacity_exceeded": false
      },
      "expected_t": "T1",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Partial disruption (public website only, hours). Single entity, single sector, no cascading, no data compromise. All T1 indicators.",
        "o_rationale": "High relevance entity (EU Parliament). But: minimal actual operational impact (website only), no cross-border service disruption. EU info shared (CERT-EU notified) but no active coordination needed. The political sensitivity doesn't change the operational classification — O1."
      }
    },
    {
      "id": "INC-019",
      "name": "KNP Logistics Group ransomware (2023)",
      "date": "2023-06-01",
      "sources": [
        "https://www.ncsc.gov.uk/news/knp-logistics-ransomware-attack",
        "https://www.bbc.co.uk/news/technology-66895580"
      ],
      "description": "Akira ransomware attack on KNP Logistics Group, one of the UK's largest privately owned logistics companies. The attack disrupted operations across the group's warehousing and distribution network. The company was unable to recover and entered administration in September 2023, with approximately 730 employees losing their jobs. The attack demonstrated how ransomware can cause permanent business failure rather than temporary disruption.",
      "t_fields": {
        "service_disruption": "sustained",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "limited",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "transport",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T4",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Sustained disruption (company entered administration — permanent failure). Single entity, single sector, limited cascading (downstream logistics customers). Operational data. Sustained disruption triggers T4.",
        "o_rationale": "Essential entity (major logistics). Single member state. No cross-border. National coordination. Capacity not exceeded. O1 — despite catastrophic business outcome, operational scope was local and national."
      }
    },
    {
      "id": "INC-020",
      "name": "Viasat KA-SAT modem wiper (2022)",
      "date": "2022-02-24",
      "sources": [
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2022",
        "https://www.viasat.com/about/newsroom/blog/ka-sat-network-cyber-attack-overview/"
      ],
      "description": "On the day of Russia's invasion of Ukraine, a destructive wiper attack targeted Viasat's KA-SAT satellite network, bricking tens of thousands of broadband modems across Europe. German wind turbines lost remote monitoring (5,800 Enercon turbines). French users lost internet. Ukrainian military communications were disrupted. The attack exploited a misconfigured VPN to access the satellite network management system and pushed a destructive firmware update to consumer modems.",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 55,
        "sectors_affected": 3,
        "cascading": "cross_sector",
        "data_compromise": "none"
      },
      "o_fields": {
        "sectors_affected": "digital infrastructure, energy, defence",
        "entity_relevance": "high_relevance",
        "ms_affected": 5,
        "cross_border_pattern": "significant",
        "coordination_needs": "eu_active",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O3",
      "rationale": {
        "t_rationale": "Complete disruption (modems permanently bricked). 55+ entities across 3 sectors (satellite, energy, defence). Cross-sector cascading (satellite → wind energy → military comms). No data compromise. Complete + cross-sector = T3.",
        "o_rationale": "High relevance entity (satellite infrastructure). 5 EU member states. Significant cross-border. EU-active coordination (joint EU attribution, ENISA + EU-CyCLONe activated). O3 via eu_active + significant cross-border."
      }
    },
    {
      "id": "INC-021",
      "name": "JBS Foods ransomware (2021)",
      "date": "2021-05-30",
      "sources": [
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2021",
        "https://www.fbi.gov/news/press-releases/fbi-statement-on-compromise-of-jbs-foods"
      ],
      "description": "REvil ransomware shut down JBS Foods' meat processing plants worldwide, including EU operations. JBS is the world's largest meat processing company. EU slaughterhouses and processing facilities in multiple countries were temporarily idled. The company paid an $11 million ransom to restore operations. Production resumed within days but the incident highlighted food supply chain vulnerability.",
      "t_fields": {
        "service_disruption": "significant",
        "affected_entities": 12,
        "sectors_affected": 1,
        "cascading": "limited",
        "data_compromise": "none"
      },
      "o_fields": {
        "sectors_affected": "food",
        "entity_relevance": "essential",
        "ms_affected": 3,
        "cross_border_pattern": "limited",
        "coordination_needs": "eu_info",
        "capacity_exceeded": false
      },
      "expected_t": "T2",
      "expected_o": "O2",
      "rationale": {
        "t_rationale": "Significant disruption (EU plants idled for days, not weeks). 12 EU facilities. Single sector (food). Limited cascading. No data compromise. Significant disruption + entities > 10 = T2.",
        "o_rationale": "Essential entity (largest global meat processor). 3 EU member states. Limited cross-border. EU info coordination. O2 via eu_info + limited cross-border."
      }
    },
    {
      "id": "INC-022",
      "name": "Montenegro government ransomware (2022)",
      "date": "2022-08-22",
      "sources": [
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2022",
        "https://therecord.media/montenegro-investigating-ongoing-cyber-attack-on-government-systems"
      ],
      "description": "Cuba ransomware group attacked Montenegro's government IT infrastructure, disabling critical government digital services including tax administration, vehicle registration, and court systems. The National Security Agency (ANB) confirmed 150 workstations at 10 government institutions were compromised. Public services were disrupted for weeks. NATO allies provided cybersecurity assistance teams. Sensitive government data was exfiltrated.",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 10,
        "sectors_affected": 1,
        "cascading": "limited",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "public administration",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "eu_info",
        "capacity_exceeded": true
      },
      "expected_t": "T3",
      "expected_o": "O2",
      "rationale": {
        "t_rationale": "Complete disruption (government services offline for weeks). 10 government institutions. Single sector. Limited cascading. Sensitive data exfiltrated. Complete disruption + sensitive data = T3.",
        "o_rationale": "Essential entity (government agencies). Single member state (NATO applicant, EU candidate). EU info shared. Capacity exceeded (NATO assistance teams deployed). O2 via eu_info + capacity exceeded."
      }
    },
    {
      "id": "INC-023",
      "name": "Danish railway Supeo attack (2022)",
      "date": "2022-11-05",
      "sources": [
        "https://therecord.media/danish-train-operator-dsb-hit-by-cyberattack-on-it-subcontractor",
        "https://www.dr.dk/nyheder/indland/it-angreb-kan-staa-bag-togkaos-i-loerdags"
      ],
      "description": "A ransomware attack on Supeo, a Danish IT subcontractor, forced DSB (Danish State Railways) to halt all train operations for several hours on a Saturday morning. The attack hit Supeo's systems that train drivers use for operational information. Without access to these systems, drivers could not safely operate trains. The incident demonstrated third-party supply chain risk in critical infrastructure operations.",
      "t_fields": {
        "service_disruption": "significant",
        "affected_entities": 2,
        "sectors_affected": 1,
        "cascading": "limited",
        "data_compromise": "none"
      },
      "o_fields": {
        "sectors_affected": "transport",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T2",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Significant disruption (train operations halted for hours, not days). 2 entities (Supeo + DSB). Single sector. Limited cascading (subcontractor → operator). No data compromise. Significant disruption = T2.",
        "o_rationale": "Essential entity (national railway). Single member state. No cross-border. National coordination. Capacity not exceeded. O1."
      }
    },
    {
      "id": "INC-024",
      "name": "Portuguese TAP Air data breach (2022)",
      "date": "2022-08-25",
      "sources": [
        "https://www.cncs.gov.pt/",
        "https://therecord.media/tap-air-portugal-confirms-data-breach-after-ragnar-locker-ransomware-attack"
      ],
      "description": "Ragnar Locker ransomware group attacked TAP Air Portugal and exfiltrated personal data of approximately 1.5 million customers including names, addresses, dates of birth, phone numbers, and passport information. The airline initially claimed no customer data was accessed, but the attackers published the data. Flight operations were not affected as the attack targeted business IT systems only.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "transport",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Partial disruption (business IT only, flights unaffected). Single entity, single sector, no cascading. But sensitive data compromise (1.5M customer records including passports). Sensitive data = T3.",
        "o_rationale": "Essential entity (national airline). Single member state. No cross-border. National coordination. O1 — data breach without operational disruption keeps operational impact local."
      }
    },
    {
      "id": "INC-025",
      "name": "Scandinavian Airlines SAS DDoS (2023)",
      "date": "2023-02-14",
      "sources": [
        "https://therecord.media/scandinavian-airline-sas-ddos-attack-app-hack",
        "https://www.ncsc.gov.uk/news/heightened-threat-of-state-aligned-groups"
      ],
      "description": "Anonymous Sudan hacktivist group launched DDoS attacks against Scandinavian Airlines, disrupting the website and mobile app for several hours. During the attack, a separate vulnerability in the mobile app briefly exposed passenger booking data to other logged-in users. The airline's flight operations were not disrupted. The attack was politically motivated following Quran burning protests in Sweden.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "transport",
        "entity_relevance": "essential",
        "ms_affected": 3,
        "cross_border_pattern": "limited",
        "coordination_needs": "eu_info",
        "capacity_exceeded": false
      },
      "expected_t": "T2",
      "expected_o": "O2",
      "rationale": {
        "t_rationale": "Partial disruption (website/app only, flights operated normally). Single entity, single sector, no cascading. Operational data briefly exposed (booking data). Operational data = T2.",
        "o_rationale": "Essential entity (major airline). 3 member states (Denmark, Sweden, Norway). Limited cross-border. EU info coordination. O2 via eu_info + limited cross-border."
      }
    },
    {
      "id": "INC-026",
      "name": "French hospitals series ransomware (2022-2023)",
      "date": "2022-12-03",
      "sources": [
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2023",
        "https://www.cert.ssi.gouv.fr/"
      ],
      "description": "A series of ransomware attacks targeted French hospitals in late 2022 and early 2023, including Centre Hospitalier de Versailles (André Mignot Hospital) and Centre Hospitalier Universitaire de Rennes. At Versailles, all IT systems were shut down, patients were transferred to other hospitals, and surgical operations were cancelled. Staff reverted to paper records. Each hospital required weeks to months for recovery. ANSSI (French national cyber agency) provided direct support.",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 3,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "health",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Complete disruption (surgeries cancelled, patients transferred). 3 hospitals affected. Single sector, no cascading. Sensitive data (patient records). Complete disruption + sensitive data = T3.",
        "o_rationale": "Essential entities (hospitals). Single member state. No cross-border. National coordination (ANSSI support). Capacity not exceeded (ANSSI handled it). O1."
      }
    },
    {
      "id": "INC-027",
      "name": "Italian Agenzia delle Entrate LockBit claim (2022)",
      "date": "2022-07-25",
      "sources": [
        "https://therecord.media/lockbit-claims-ransomware-attack-on-italian-revenue-agency",
        "https://www.cybersecurity360.it/"
      ],
      "description": "LockBit ransomware group claimed to have attacked Italy's tax agency (Agenzia delle Entrate), threatening to publish 78 GB of data. Investigation revealed the attack actually compromised GSIS, an IT service provider for tax professionals, not the agency directly. Tax filing services experienced minor disruptions. The incident caused public alarm due to the sensitivity of tax data but actual impact was limited to the service provider's systems.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "public administration",
        "entity_relevance": "non_essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T2",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Partial disruption (minor service interruptions). Single entity (service provider, not the agency). Single sector. No cascading. Operational data compromised. Operational data = T2.",
        "o_rationale": "Non-essential entity (IT service provider). Single member state. No cross-border. National coordination. All O1 indicators."
      }
    },
    {
      "id": "INC-028",
      "name": "Austrian FMTG hotel chain ransomware (2019)",
      "date": "2019-11-14",
      "sources": [
        "https://www.bka.gv.at/",
        "https://www.zdnet.com/article/locked-out-ransomware-gang-targets-hotel-chain/"
      ],
      "description": "Ransomware attack on Falkensteiner Michaeler Tourism Group (FMTG), an Austrian hotel chain, disabled reservation and key card systems at properties across multiple European countries. Guests were locked out of rooms and check-in processes reverted to manual operation. The company managed the incident without paying ransom. Operations returned to normal within days. No personal guest data was confirmed exfiltrated.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 5,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "none"
      },
      "o_fields": {
        "sectors_affected": "digital infrastructure",
        "entity_relevance": "non_essential",
        "ms_affected": 3,
        "cross_border_pattern": "limited",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T1",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Partial disruption (reservation/keycard systems, not full outage). 5 properties but single entity. Single sector. No cascading. No data compromise. All T1 indicators.",
        "o_rationale": "Non-essential entity (hotel chain). 3 member states but minimal operational impact. Limited cross-border but national coordination only. O1 — low relevance entity with limited disruption."
      }
    },
    {
      "id": "INC-029",
      "name": "Romanian hospital ransomware wave (2024)",
      "date": "2024-02-12",
      "sources": [
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2024",
        "https://therecord.media/romanian-hospitals-ransomware-attack"
      ],
      "description": "Backmydata ransomware simultaneously hit the Hipocrate IT management platform used by Romanian hospitals, knocking over 100 hospitals offline. Twenty-five hospitals had their databases encrypted. Staff reverted to paper records across the country. The Romanian DNSC (national cyber agency) coordinated the response. Patient care continued but with significant delays. Some hospitals took weeks to restore systems.",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 25,
        "sectors_affected": 1,
        "cascading": "limited",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "health",
        "entity_relevance": "high_relevance",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": true
      },
      "expected_t": "T3",
      "expected_o": "O2",
      "rationale": {
        "t_rationale": "Complete disruption (databases encrypted, paper records). 25 hospitals. Single sector. Limited cascading (shared IT platform). Sensitive data (patient records). Complete disruption + sensitive data = T3.",
        "o_rationale": "High relevance entities (hospitals). Single member state. No cross-border. National coordination. But capacity exceeded (DNSC scaled to handle 100+ hospitals simultaneously). O2 via capacity exceeded."
      }
    },
    {
      "id": "INC-030",
      "name": "Barcelona hospital Clínic ransomware (2023)",
      "date": "2023-03-05",
      "sources": [
        "https://therecord.media/barcelona-hospital-ransomware-attack-cancelled-surgeries",
        "https://www.ccma.cat/324/"
      ],
      "description": "RansomHouse group attacked Hospital Clínic de Barcelona, one of Spain's leading public hospitals. 150 surgeries were cancelled, 3,000 patient appointments postponed, and radiation therapy for oncology patients disrupted. Emergency services continued with reduced capacity. Patient data including medical records was exfiltrated and partially published. Catalonia's cybersecurity agency coordinated the response.",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "health",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Complete disruption (surgeries cancelled, appointments postponed). Single entity, single sector, no cascading. Sensitive data (patient records exfiltrated and published). Complete + sensitive = T3.",
        "o_rationale": "Essential entity (major public hospital). Single member state. No cross-border. National coordination (Catalonia agency). Capacity not exceeded. O1."
      }
    },
    {
      "id": "INC-031",
      "name": "Polish railway GPS spoofing (2023)",
      "date": "2023-08-25",
      "sources": [
        "https://therecord.media/poland-railway-radio-stop-attack",
        "https://www.reuters.com/world/europe/saboteurs-halt-polish-trains-using-radio-system-2023-08-26/"
      ],
      "description": "Attackers exploited the unsecured analog radio-stop system used by Polish railways to send emergency stop commands to over 20 trains. Trains were halted in several regions causing widespread delays. The attack used simple radio equipment to broadcast the emergency stop frequency. No injuries occurred but rail traffic was disrupted for hours. Pro-Russian messaging was interspersed with the commands. The vulnerability had been known for years.",
      "t_fields": {
        "service_disruption": "significant",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "none"
      },
      "o_fields": {
        "sectors_affected": "transport",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T2",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Significant disruption (trains halted for hours across regions). Single entity (PKP railway). Single sector. No cascading. No data compromise. Significant = T2.",
        "o_rationale": "Essential entity (national railway). Single member state. No cross-border. National coordination. Capacity not exceeded. O1."
      }
    },
    {
      "id": "INC-032",
      "name": "Port of Lisbon LockBit ransomware (2023)",
      "date": "2023-01-01",
      "sources": [
        "https://therecord.media/port-of-lisbon-administration-hit-by-lockbit-ransomware",
        "https://www.portodelisboa.pt/"
      ],
      "description": "LockBit ransomware group attacked the Port of Lisbon administration on New Year's Day. The port's website was taken offline and internal systems were disrupted. LockBit demanded $1.5 million and threatened to publish financial reports, audits, contracts, and personal data. Port operations (ship movements, cargo handling) continued normally as operational technology systems were separate from the compromised business IT. The port is one of the busiest in Europe.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "transport",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T2",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Partial disruption (website/business IT only, port operations continued). Single entity, single sector, no cascading. Operational data compromised (financial reports, contracts). Operational data = T2.",
        "o_rationale": "Essential entity (major EU port). Single member state. No cross-border. National coordination. Capacity not exceeded. O1."
      }
    },
    {
      "id": "INC-033",
      "name": "AnyDesk supply chain breach (2024)",
      "date": "2024-02-02",
      "sources": [
        "https://anydesk.com/en/public-statement",
        "https://www.bsi.bund.de/EN/Themen/Unternehmen-und-Organisationen/Cyber-Sicherheitslage/Reaktion/CERT-Bund/Advisories/advisories_node.html"
      ],
      "description": "AnyDesk, a widely used remote desktop software provider, confirmed that attackers compromised their production systems and stole code-signing certificates. The company revoked all web portal passwords and replaced compromised certificates. While no confirmed downstream exploitation was reported, the potential blast radius affected millions of enterprise users globally. BSI Germany issued an advisory. The incident raised supply chain concerns similar to SolarWinds but without confirmed exploitation.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 12,
        "sectors_affected": 2,
        "cascading": "limited",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "digital infrastructure, manufacturing",
        "entity_relevance": "high_relevance",
        "ms_affected": 5,
        "cross_border_pattern": "significant",
        "coordination_needs": "eu_active",
        "capacity_exceeded": false
      },
      "expected_t": "T2",
      "expected_o": "O3",
      "rationale": {
        "t_rationale": "Partial disruption (password resets, certificate replacement). 12+ entities took active remediation. 2 sectors. Limited cascading (potential, not confirmed). Operational data (code signing certs, portal credentials). Entities > 10 + operational data = T2.",
        "o_rationale": "High relevance entity (remote access infrastructure used by enterprises). 5+ EU member states. Significant cross-border (pan-European user base). EU-active coordination (BSI advisory, ENISA monitoring). O3 via eu_active + significant cross-border."
      }
    },
    {
      "id": "INC-034",
      "name": "Nordex wind turbine ransomware (2022)",
      "date": "2022-03-31",
      "sources": [
        "https://www.nordex-online.com/en/2022/04/nordex-se-cyber-security-incident/",
        "https://therecord.media/wind-turbine-giant-nordex-shuts-down-it-systems-after-cyberattack"
      ],
      "description": "Conti ransomware hit Nordex, one of the world's largest wind turbine manufacturers headquartered in Hamburg, Germany. The company shut down IT systems across multiple locations as a precaution. Remote monitoring of installed wind turbines was temporarily disabled. Manufacturing and engineering operations were disrupted. The company operated at reduced IT capacity for weeks while rebuilding systems. No wind turbines were physically affected.",
      "t_fields": {
        "service_disruption": "significant",
        "affected_entities": 1,
        "sectors_affected": 2,
        "cascading": "limited",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "energy, manufacturing",
        "entity_relevance": "essential",
        "ms_affected": 3,
        "cross_border_pattern": "limited",
        "coordination_needs": "eu_info",
        "capacity_exceeded": false
      },
      "expected_t": "T2",
      "expected_o": "O2",
      "rationale": {
        "t_rationale": "Significant disruption (reduced IT capacity for weeks, remote monitoring disabled). Single entity. 2 sectors (energy + manufacturing). Limited cascading. Operational data. Significant disruption = T2.",
        "o_rationale": "Essential entity (major wind manufacturer). 3 EU member states (offices in DE, DK, ES). Limited cross-border. EU info coordination. O2 via eu_info + limited cross-border."
      }
    },
    {
      "id": "INC-035",
      "name": "Medibank data breach (2022)",
      "date": "2022-10-13",
      "sources": [
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2023",
        "https://www.medibank.com.au/health-insurance/info/cyber-event/"
      ],
      "description": "Attackers exfiltrated personal and health data of 9.7 million current and former Medibank customers including names, dates of birth, Medicare numbers, and sensitive health claims data. The data was progressively leaked on the dark web after Medibank refused to pay ransom. The breach was one of the largest healthcare data compromises globally. Primarily Australian but included EU citizens covered by travel insurance. Technical disruption to services was minimal.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "health",
        "entity_relevance": "non_essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Partial disruption (services continued). Single entity, single sector, no cascading. But sensitive data compromise (9.7M health records). Sensitive data = T3 regardless of low disruption.",
        "o_rationale": "Non-essential entity in EU context (Australian company, limited EU exposure). Single MS for GDPR purposes. No cross-border. National coordination. O1."
      }
    },
    {
      "id": "INC-036",
      "name": "German Chamber of Commerce (DIHK) attack (2022)",
      "date": "2022-08-03",
      "sources": [
        "https://www.dihk.de/de/aktuelles-und-presse/aktuelle-informationen/stoerung-it-systeme-77504",
        "https://therecord.media/german-chambers-of-commerce-take-all-it-systems-offline-after-cyberattack"
      ],
      "description": "The Association of German Chambers of Commerce and Industry (DIHK) took all IT systems offline after detecting a cyberattack. The DIHK represents 3.6 million German businesses. Email, phone, and website services were unavailable for days. Individual regional chambers (IHKs) across Germany were also affected as they share infrastructure. Business registration and trade document services were disrupted. Recovery took weeks.",
      "t_fields": {
        "service_disruption": "complete",
        "affected_entities": 12,
        "sectors_affected": 1,
        "cascading": "limited",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "public administration",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Complete disruption (all IT systems offline). 12+ regional chambers affected. Single sector. Limited cascading (shared infra). Operational data. Complete disruption + entities > 10 = T3.",
        "o_rationale": "Essential entity (represents 3.6M businesses). Single member state. No cross-border. National coordination. Capacity not exceeded. O1."
      }
    },
    {
      "id": "INC-037",
      "name": "Luxembourg POST telecom breach (2023)",
      "date": "2023-07-12",
      "sources": [
        "https://www.post.lu/en",
        "https://www.cnpd.public.lu/"
      ],
      "description": "A targeted attack compromised systems at POST Luxembourg, the country's incumbent telecom operator providing services to government, banking, and EU institutions. The breach affected a limited set of business customer accounts. POST notified affected customers and the Luxembourg data protection authority (CNPD). Service operations were not disrupted. The attack was contained quickly due to network segmentation.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "operational"
      },
      "o_fields": {
        "sectors_affected": "digital infrastructure",
        "entity_relevance": "essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T2",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Partial disruption (limited customer accounts, no service outage). Single entity, single sector, no cascading. Operational data compromised. Operational data = T2.",
        "o_rationale": "Essential entity (national telecom/EU institution provider). Single member state. No cross-border. National coordination. Capacity not exceeded. O1."
      }
    },
    {
      "id": "INC-038",
      "name": "European Investment Bank DDoS (2023)",
      "date": "2023-06-19",
      "sources": [
        "https://therecord.media/eib-ddos-attack-killnet-pro-russian-hackers",
        "https://www.eib.org/"
      ],
      "description": "Pro-Russian hacktivist group Killnet launched DDoS attacks against the European Investment Bank, taking its website offline intermittently for several hours. The bank confirmed the attack but stated that internal systems and financial operations were unaffected. The attack coincided with the EU's continued support for Ukraine. CERT-EU coordinated the response.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "none"
      },
      "o_fields": {
        "sectors_affected": "financial_market",
        "entity_relevance": "high_relevance",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "eu_info",
        "capacity_exceeded": false
      },
      "expected_t": "T1",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Partial disruption (website only, hours). Single entity, single sector, no cascading, no data compromise. All T1 indicators.",
        "o_rationale": "High relevance entity (EIB). Single member state impact (website is EU-wide but disruption was trivial). EU info (CERT-EU notified) but no active coordination needed. O1 — trivial DDoS against high-profile target doesn't elevate operational impact."
      }
    },
    {
      "id": "INC-039",
      "name": "Europol data theft from EPE portal (2024)",
      "date": "2024-05-10",
      "sources": [
        "https://therecord.media/europol-data-breach-investigation",
        "https://www.europol.europa.eu/"
      ],
      "description": "A threat actor claimed to have stolen classified data from Europol's Platform for Experts (EPE) portal and offered it for sale. Europol confirmed the EPE incident but stated it was a limited breach of a collaboration platform, not core operational systems. Personnel data of Europol staff may have been accessed. The platform was taken offline for investigation. Core law enforcement databases were not compromised.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "sensitive"
      },
      "o_fields": {
        "sectors_affected": "public administration",
        "entity_relevance": "systemic",
        "ms_affected": 8,
        "cross_border_pattern": "significant",
        "coordination_needs": "eu_active",
        "capacity_exceeded": false
      },
      "expected_t": "T3",
      "expected_o": "O3",
      "rationale": {
        "t_rationale": "Partial disruption (single platform offline). Single entity, single sector, no cascading. But sensitive data compromise (personnel data, classified collaboration content). Sensitive data = T3.",
        "o_rationale": "Systemic entity (Europol is EU-wide law enforcement). 8+ member states use EPE. Significant cross-border (all EU members affected). EU-active coordination (CERT-EU + member state CERTs). O3 via systemic entity + eu_active."
      }
    },
    {
      "id": "INC-040",
      "name": "Small Italian water utility ransomware (2023)",
      "date": "2023-05-10",
      "sources": [
        "https://www.enisa.europa.eu/publications/enisa-threat-landscape-2023",
        "https://therecord.media/italian-water-utility-cyberattack"
      ],
      "description": "A ransomware attack targeted a small Italian municipal water utility's business IT systems. Customer billing and communication systems were disrupted for several days. Water treatment and distribution SCADA systems were on a separate network and were not affected. Water supply continued uninterrupted. The utility serves approximately 50,000 residents. The local municipality coordinated recovery with national CSIRT assistance.",
      "t_fields": {
        "service_disruption": "partial",
        "affected_entities": 1,
        "sectors_affected": 1,
        "cascading": "none",
        "data_compromise": "none"
      },
      "o_fields": {
        "sectors_affected": "drinking_water",
        "entity_relevance": "non_essential",
        "ms_affected": 1,
        "cross_border_pattern": "none",
        "coordination_needs": "national",
        "capacity_exceeded": false
      },
      "expected_t": "T1",
      "expected_o": "O1",
      "rationale": {
        "t_rationale": "Partial disruption (billing only, water supply unaffected). Single entity, single sector, no cascading, no data compromise. All T1 indicators.",
        "o_rationale": "Non-essential entity (small municipal utility). Single member state. No cross-border. National coordination. Capacity not exceeded. All O1 indicators."
      }
    }
  ]
}
```

- [ ] **Step 2: Validate label distribution**

After creating the file, verify the distribution covers the T×O matrix adequately. Count per expected_t and expected_o:

Run:
```bash
python3 -c "
import json
from collections import Counter
data = json.load(open('data/reference/curated_incidents.json'))
t_counts = Counter(i['expected_t'] for i in data['incidents'])
o_counts = Counter(i['expected_o'] for i in data['incidents'])
matrix = Counter((i['expected_t'], i['expected_o']) for i in data['incidents'])
print('T distribution:', dict(sorted(t_counts.items())))
print('O distribution:', dict(sorted(o_counts.items())))
print(f'Total: {len(data[\"incidents\"])} incidents')
print('Matrix coverage:')
for t in ['T1','T2','T3','T4']:
    for o in ['O1','O2','O3','O4']:
        print(f'  {t}/{o}: {matrix.get((t,o), 0)}')
"
```

Expected: At least 3 per T-level, at least 3 per O-level, at least 10 of the 16 T×O cells covered.

- [ ] **Step 3: Commit**

```bash
git add data/reference/curated_incidents.json
git commit -m "feat(v2): add 40 curated real-world incidents for benchmark dataset"
```

---

### Task 3: Build the curated dataset loader

**Files:**
- Create: `evaluation/curated_loader.py`
- Test: `src/tests/test_curated_loader.py`

A module that loads, validates, and converts curated incidents into the format the T-model and O-model expect.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for curated incident dataset loader."""

import json
from pathlib import Path

import pytest

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from evaluation.curated_loader import load_curated_incidents, CuratedIncident


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "curated_sample.json"


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a minimal valid dataset for testing."""
    data = {
        "version": "1.0",
        "incidents": [
            {
                "id": "INC-001",
                "name": "Test incident",
                "date": "2024-01-01",
                "sources": ["https://example.com"],
                "description": "A test ransomware attack on a hospital that disrupted all IT systems for several days",
                "t_fields": {
                    "service_disruption": "complete",
                    "affected_entities": 1,
                    "sectors_affected": 1,
                    "cascading": "none",
                    "data_compromise": "sensitive",
                },
                "o_fields": {
                    "sectors_affected": "health",
                    "entity_relevance": "essential",
                    "ms_affected": 1,
                    "cross_border_pattern": "none",
                    "coordination_needs": "national",
                    "capacity_exceeded": False,
                },
                "expected_t": "T3",
                "expected_o": "O1",
                "rationale": {
                    "t_rationale": "Complete disruption plus sensitive data compromise triggers T3",
                    "o_rationale": "Single member state, national coordination, essential entity = O1",
                },
            }
        ],
    }
    path = tmp_path / "curated_incidents.json"
    path.write_text(json.dumps(data))
    return path


def test_load_returns_list_of_curated_incidents(sample_dataset):
    incidents = load_curated_incidents(sample_dataset)
    assert len(incidents) == 1
    assert isinstance(incidents[0], CuratedIncident)


def test_curated_incident_has_required_fields(sample_dataset):
    incident = load_curated_incidents(sample_dataset)[0]
    assert incident.id == "INC-001"
    assert incident.name == "Test incident"
    assert incident.expected_t == "T3"
    assert incident.expected_o == "O1"


def test_curated_incident_t_fields(sample_dataset):
    incident = load_curated_incidents(sample_dataset)[0]
    assert incident.t_fields["service_disruption"] == "complete"
    assert incident.t_fields["affected_entities"] == 1
    assert incident.t_fields["data_compromise"] == "sensitive"


def test_curated_incident_o_fields(sample_dataset):
    incident = load_curated_incidents(sample_dataset)[0]
    assert incident.o_fields["sectors_affected"] == "health"
    assert incident.o_fields["entity_relevance"] == "essential"
    assert incident.o_fields["capacity_exceeded"] is False


def test_invalid_t_level_raises(tmp_path):
    data = {
        "version": "1.0",
        "incidents": [{
            "id": "INC-001", "name": "Bad", "date": "2024-01-01",
            "sources": ["https://example.com"],
            "description": "A test incident with invalid T level that should fail validation checks",
            "t_fields": {
                "service_disruption": "complete", "affected_entities": 1,
                "sectors_affected": 1, "cascading": "none", "data_compromise": "none",
            },
            "o_fields": {
                "sectors_affected": "health", "entity_relevance": "essential",
                "ms_affected": 1, "cross_border_pattern": "none",
                "coordination_needs": "national", "capacity_exceeded": False,
            },
            "expected_t": "T5",
            "expected_o": "O1",
            "rationale": {"t_rationale": "bad level test rationale here", "o_rationale": "bad level test rationale here"},
        }],
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="T5"):
        load_curated_incidents(path)


def test_empty_incidents_returns_empty_list(tmp_path):
    data = {"version": "1.0", "incidents": []}
    path = tmp_path / "empty.json"
    path.write_text(json.dumps(data))
    assert load_curated_incidents(path) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `poetry run pytest src/tests/test_curated_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'evaluation.curated_loader'`

- [ ] **Step 3: Write the implementation**

```python
"""Loader and validator for curated incident benchmark datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

VALID_T_LEVELS = {"T1", "T2", "T3", "T4"}
VALID_O_LEVELS = {"O1", "O2", "O3", "O4"}
VALID_DISRUPTIONS = {"partial", "significant", "complete", "sustained"}
VALID_CASCADING = {"none", "limited", "cross_sector", "uncontrolled"}
VALID_DATA_COMPROMISE = {"none", "operational", "sensitive", "systemic"}
VALID_ENTITY_RELEVANCE = {"non_essential", "essential", "high_relevance", "systemic"}
VALID_CROSS_BORDER = {"none", "limited", "significant", "systemic"}
VALID_COORDINATION = {"national", "eu_info", "eu_active", "full_ipcr"}


@dataclass
class CuratedIncident:
    """A single curated incident with ground-truth labels."""

    id: str
    name: str
    date: str
    sources: list[str]
    description: str
    t_fields: dict
    o_fields: dict
    expected_t: str
    expected_o: str
    rationale: dict


def load_curated_incidents(path: Path) -> list[CuratedIncident]:
    """Load and validate curated incidents from a JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    incidents = []

    for raw in data["incidents"]:
        _validate_incident(raw)
        incidents.append(CuratedIncident(
            id=raw["id"],
            name=raw["name"],
            date=raw["date"],
            sources=raw["sources"],
            description=raw["description"],
            t_fields=raw["t_fields"],
            o_fields=raw["o_fields"],
            expected_t=raw["expected_t"],
            expected_o=raw["expected_o"],
            rationale=raw["rationale"],
        ))

    return incidents


def _validate_incident(raw: dict) -> None:
    """Validate a single incident dict, raising ValueError on problems."""
    inc_id = raw.get("id", "unknown")

    t = raw["expected_t"]
    if t not in VALID_T_LEVELS:
        raise ValueError(f"{inc_id}: invalid expected_t '{t}', must be one of {VALID_T_LEVELS}")

    o = raw["expected_o"]
    if o not in VALID_O_LEVELS:
        raise ValueError(f"{inc_id}: invalid expected_o '{o}', must be one of {VALID_O_LEVELS}")

    tf = raw["t_fields"]
    if tf["service_disruption"] not in VALID_DISRUPTIONS:
        raise ValueError(f"{inc_id}: invalid service_disruption '{tf['service_disruption']}'")
    if tf["cascading"] not in VALID_CASCADING:
        raise ValueError(f"{inc_id}: invalid cascading '{tf['cascading']}'")
    if tf["data_compromise"] not in VALID_DATA_COMPROMISE:
        raise ValueError(f"{inc_id}: invalid data_compromise '{tf['data_compromise']}'")

    of = raw["o_fields"]
    if of["entity_relevance"] not in VALID_ENTITY_RELEVANCE:
        raise ValueError(f"{inc_id}: invalid entity_relevance '{of['entity_relevance']}'")
    if of["cross_border_pattern"] not in VALID_CROSS_BORDER:
        raise ValueError(f"{inc_id}: invalid cross_border_pattern '{of['cross_border_pattern']}'")
    if of["coordination_needs"] not in VALID_COORDINATION:
        raise ValueError(f"{inc_id}: invalid coordination_needs '{of['coordination_needs']}'")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `poetry run pytest src/tests/test_curated_loader.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add evaluation/curated_loader.py src/tests/test_curated_loader.py
git commit -m "feat(v2): add curated incident loader with validation"
```

---

### Task 4: Build the curated benchmark script

**Files:**
- Create: `evaluation/benchmark_curated.py`

This is the core deliverable: a benchmark that runs both models against the curated dataset and produces a comparison report.

- [ ] **Step 1: Write the benchmark script**

```python
#!/usr/bin/env python3
"""Benchmark CyberScale Phase 3 models against human-curated real-world incidents.

Loads the curated incident dataset, runs T-model and O-model predictions,
computes per-model and end-to-end matrix metrics, and generates a comparison
report highlighting synthetic vs real-world performance gaps.

Usage:
    poetry run python evaluation/benchmark_curated.py \
        --t-model data/models/technical \
        --o-model data/models/operational \
        --dataset data/reference/curated_incidents.json \
        --output evaluation/curated_benchmark.md
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from datetime import datetime
from functools import partial
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "evaluation"))

from curated_loader import load_curated_incidents, CuratedIncident
from cyberscale.models.technical import TechnicalClassifier
from cyberscale.models.operational import OperationalClassifier
from cyberscale.matrix.dual_scale import classify_incident

print = partial(print, flush=True)


def evaluate_t_model(
    t_model: TechnicalClassifier, incidents: list[CuratedIncident],
) -> tuple[list[str], list[str], list[dict]]:
    """Run T-model on curated incidents. Returns (y_true, y_pred, details)."""
    y_true, y_pred, details = [], [], []
    for inc in incidents:
        result = t_model.predict(
            description=inc.description,
            service_disruption=inc.t_fields["service_disruption"],
            affected_entities=inc.t_fields["affected_entities"],
            sectors_affected=inc.t_fields["sectors_affected"],
            cascading=inc.t_fields["cascading"],
            data_compromise=inc.t_fields["data_compromise"],
        )
        y_true.append(inc.expected_t)
        y_pred.append(result.level)
        details.append({
            "id": inc.id,
            "name": inc.name,
            "expected_t": inc.expected_t,
            "predicted_t": result.level,
            "confidence": result.confidence,
            "correct": inc.expected_t == result.level,
        })
    return y_true, y_pred, details


def evaluate_o_model(
    o_model: OperationalClassifier, incidents: list[CuratedIncident],
) -> tuple[list[str], list[str], list[dict]]:
    """Run O-model on curated incidents. Returns (y_true, y_pred, details)."""
    y_true, y_pred, details = [], [], []
    for inc in incidents:
        result = o_model.predict(
            description=inc.description,
            sectors_affected=inc.o_fields["sectors_affected"],
            entity_relevance=inc.o_fields["entity_relevance"],
            ms_affected=inc.o_fields["ms_affected"],
            cross_border_pattern=inc.o_fields["cross_border_pattern"],
            coordination_needs=inc.o_fields["coordination_needs"],
            capacity_exceeded=inc.o_fields["capacity_exceeded"],
        )
        y_true.append(inc.expected_o)
        y_pred.append(result.level)
        details.append({
            "id": inc.id,
            "name": inc.name,
            "expected_o": inc.expected_o,
            "predicted_o": result.level,
            "confidence": result.confidence,
            "correct": inc.expected_o == result.level,
        })
    return y_true, y_pred, details


def compute_metrics(
    y_true: list[str], y_pred: list[str], labels: list[str],
) -> dict:
    """Compute accuracy, per-class F1, macro F1, and confusion matrix."""
    accuracy = sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true) if y_true else 0.0

    per_class_f1 = {}
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        per_class_f1[label] = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

    macro = sum(per_class_f1.values()) / len(per_class_f1) if per_class_f1 else 0.0

    cm = [[0] * len(labels) for _ in labels]
    idx = {l: i for i, l in enumerate(labels)}
    for t, p in zip(y_true, y_pred):
        cm[idx[t]][idx[p]] += 1

    return {
        "accuracy": accuracy,
        "per_class_f1": per_class_f1,
        "macro_f1": macro,
        "confusion_matrix": cm,
    }


def format_confusion_matrix(cm: list[list[int]], labels: list[str]) -> str:
    """Format confusion matrix as markdown table."""
    lines = []
    header = "| Actual \\ Predicted | " + " | ".join(labels) + " |"
    sep = "|" + "---|" * (len(labels) + 1)
    lines.append(header)
    lines.append(sep)
    for i, label in enumerate(labels):
        row = f"| **{label}** | " + " | ".join(str(cm[i][j]) for j in range(len(labels))) + " |"
        lines.append(row)
    return "\n".join(lines)


def generate_report(
    dataset_path: str,
    n_incidents: int,
    t_metrics: dict,
    o_metrics: dict,
    t_details: list[dict],
    o_details: list[dict],
    matrix_accuracy: float,
    matrix_dist: dict[str, int],
    elapsed_seconds: float,
) -> str:
    """Generate the curated benchmark markdown report."""
    t_labels = ["T1", "T2", "T3", "T4"]
    o_labels = ["O1", "O2", "O3", "O4"]

    report = f"""# CyberScale Phase 3 — Curated Incident Benchmark

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Dataset:** `{dataset_path}`
**Incidents:** {n_incidents}
**Elapsed:** {elapsed_seconds:.1f}s

> This benchmark evaluates model performance on **human-curated real-world incidents**,
> as opposed to the synthetic benchmark which uses parametrically generated scenarios.
> Performance gaps between synthetic and curated benchmarks indicate distribution shift.

## T-model Results

- **Accuracy:** {t_metrics['accuracy'] * 100:.1f}%
- **Macro F1:** {t_metrics['macro_f1']:.4f}

### Per-level F1

| Level | F1 | Support |
|-------|-----|---------|
"""
    t_support = Counter(d["expected_t"] for d in t_details)
    for label in t_labels:
        f1 = t_metrics["per_class_f1"].get(label, 0.0)
        report += f"| {label} | {f1:.4f} | {t_support.get(label, 0)} |\n"

    report += f"""
### Confusion Matrix

{format_confusion_matrix(t_metrics['confusion_matrix'], t_labels)}

## O-model Results

- **Accuracy:** {o_metrics['accuracy'] * 100:.1f}%
- **Macro F1:** {o_metrics['macro_f1']:.4f}

### Per-level F1

| Level | F1 | Support |
|-------|-----|---------|
"""
    o_support = Counter(d["expected_o"] for d in o_details)
    for label in o_labels:
        f1 = o_metrics["per_class_f1"].get(label, 0.0)
        report += f"| {label} | {f1:.4f} | {o_support.get(label, 0)} |\n"

    report += f"""
### Confusion Matrix

{format_confusion_matrix(o_metrics['confusion_matrix'], o_labels)}

## End-to-end Matrix Results

- **Accuracy:** {matrix_accuracy * 100:.1f}%

### Classification Distribution

| Classification | Count | Pct |
|---------------|-------|-----|
"""
    total = sum(matrix_dist.values()) or 1
    for cls in ["below_threshold", "significant", "large_scale", "cyber_crisis"]:
        count = matrix_dist.get(cls, 0)
        report += f"| {cls} | {count} | {count / total * 100:.1f}% |\n"

    # Per-incident detail table
    report += """
## Per-incident Results

| ID | Incident | Expected T/O | Predicted T/O | T | O | Matrix |
|----|----------|-------------|--------------|---|---|--------|
"""
    for td, od in zip(t_details, o_details):
        t_ok = "ok" if td["correct"] else "MISS"
        o_ok = "ok" if od["correct"] else "MISS"
        try:
            mat = classify_incident(td["predicted_t"], od["predicted_o"]).label
        except ValueError:
            mat = "error"
        report += (
            f"| {td['id']} | {td['name'][:40]} | "
            f"{td['expected_t']}/{od['expected_o']} | "
            f"{td['predicted_t']}/{od['predicted_o']} | "
            f"{t_ok} | {o_ok} | {mat} |\n"
        )

    # Failure analysis
    t_misses = [d for d in t_details if not d["correct"]]
    o_misses = [d for d in o_details if not d["correct"]]

    if t_misses or o_misses:
        report += "\n## Failure Analysis\n\n"
        if t_misses:
            report += "### T-model Misclassifications\n\n"
            for d in t_misses:
                report += f"- **{d['id']} {d['name']}**: expected {d['expected_t']}, got {d['predicted_t']} (confidence: {d['confidence']})\n"
        if o_misses:
            report += "\n### O-model Misclassifications\n\n"
            for d in o_misses:
                report += f"- **{d['id']} {d['name']}**: expected {d['expected_o']}, got {d['predicted_o']} (confidence: {d['confidence']})\n"

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark Phase 3 models against curated real-world incidents"
    )
    parser.add_argument(
        "--t-model", type=Path, default=Path("data/models/technical"),
    )
    parser.add_argument(
        "--o-model", type=Path, default=Path("data/models/operational"),
    )
    parser.add_argument(
        "--dataset", type=Path, default=Path("data/reference/curated_incidents.json"),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("evaluation/curated_benchmark.md"),
    )
    parser.add_argument(
        "--mc-passes", type=int, default=5,
    )
    args = parser.parse_args()

    start = time.time()

    # 1. Load curated incidents
    print(f"Loading curated incidents from {args.dataset}...")
    incidents = load_curated_incidents(args.dataset)
    print(f"Loaded {len(incidents)} incidents")

    # 2. Load models
    print(f"Loading T-model from {args.t_model}...")
    t_model = TechnicalClassifier(args.t_model, mc_passes=args.mc_passes)
    print(f"Loading O-model from {args.o_model}...")
    o_model = OperationalClassifier(args.o_model, mc_passes=args.mc_passes)

    # 3. Evaluate
    print("Evaluating T-model...")
    t_true, t_pred, t_details = evaluate_t_model(t_model, incidents)
    t_metrics = compute_metrics(t_true, t_pred, ["T1", "T2", "T3", "T4"])
    print(f"  T accuracy: {t_metrics['accuracy'] * 100:.1f}%, macro F1: {t_metrics['macro_f1']:.4f}")

    print("Evaluating O-model...")
    o_true, o_pred, o_details = evaluate_o_model(o_model, incidents)
    o_metrics = compute_metrics(o_true, o_pred, ["O1", "O2", "O3", "O4"])
    print(f"  O accuracy: {o_metrics['accuracy'] * 100:.1f}%, macro F1: {o_metrics['macro_f1']:.4f}")

    # 4. Matrix evaluation
    print("Computing matrix results...")
    n = len(incidents)
    correct = 0
    dist: dict[str, int] = Counter()
    for i in range(n):
        gt = classify_incident(t_true[i], o_true[i])
        pred = classify_incident(t_pred[i], o_pred[i])
        dist[pred.classification] += 1
        if pred.classification == gt.classification:
            correct += 1
    matrix_accuracy = correct / n if n > 0 else 0.0
    print(f"  Matrix accuracy: {matrix_accuracy * 100:.1f}%")

    elapsed = time.time() - start

    # 5. Generate report
    report = generate_report(
        dataset_path=str(args.dataset),
        n_incidents=len(incidents),
        t_metrics=t_metrics,
        o_metrics=o_metrics,
        t_details=t_details,
        o_details=o_details,
        matrix_accuracy=matrix_accuracy,
        matrix_dist=dict(dist),
        elapsed_seconds=elapsed,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"\nReport written to {args.output}")
    print(f"Total time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run a dry-run test (no models needed)**

Verify the script parses arguments and loads the dataset correctly:

Run:
```bash
poetry run python evaluation/benchmark_curated.py --help
```

Expected: Help text showing all arguments

- [ ] **Step 3: Commit**

```bash
git add evaluation/benchmark_curated.py
git commit -m "feat(v2): add curated incident benchmark script"
```

---

### Task 5: Add integration test for the benchmark pipeline

**Files:**
- Create: `src/tests/test_benchmark_curated.py`

Test the end-to-end benchmark pipeline using mocked models (since we can't assume GPU/models are available in CI).

- [ ] **Step 1: Write the integration test**

```python
"""Integration tests for curated benchmark pipeline (mocked models)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "evaluation"))

from evaluation.curated_loader import load_curated_incidents
from cyberscale.matrix.dual_scale import classify_incident


@pytest.fixture
def curated_dataset(tmp_path):
    """Minimal curated dataset with 4 incidents (one per T-level)."""
    data = {
        "version": "1.0",
        "incidents": [
            {
                "id": "INC-001", "name": "Low incident", "date": "2024-01-01",
                "sources": ["https://example.com"],
                "description": "A minor port scan detected at a small research lab with no data compromise or service impact",
                "t_fields": {
                    "service_disruption": "partial", "affected_entities": 1,
                    "sectors_affected": 1, "cascading": "none", "data_compromise": "none",
                },
                "o_fields": {
                    "sectors_affected": "research", "entity_relevance": "non_essential",
                    "ms_affected": 1, "cross_border_pattern": "none",
                    "coordination_needs": "national", "capacity_exceeded": False,
                },
                "expected_t": "T1", "expected_o": "O1",
                "rationale": {"t_rationale": "All minimal fields = T1", "o_rationale": "All minimal fields = O1"},
            },
            {
                "id": "INC-002", "name": "Medium incident", "date": "2024-02-01",
                "sources": ["https://example.com"],
                "description": "A DDoS attack disrupted banking services across two EU member states for several hours",
                "t_fields": {
                    "service_disruption": "significant", "affected_entities": 5,
                    "sectors_affected": 1, "cascading": "none", "data_compromise": "operational",
                },
                "o_fields": {
                    "sectors_affected": "banking", "entity_relevance": "essential",
                    "ms_affected": 2, "cross_border_pattern": "limited",
                    "coordination_needs": "eu_info", "capacity_exceeded": False,
                },
                "expected_t": "T2", "expected_o": "O2",
                "rationale": {"t_rationale": "Significant disruption = T2", "o_rationale": "EU info + limited cross-border = O2"},
            },
            {
                "id": "INC-003", "name": "High incident", "date": "2024-03-01",
                "sources": ["https://example.com"],
                "description": "Ransomware encrypted hospital systems completely, sensitive patient data exfiltrated and published online",
                "t_fields": {
                    "service_disruption": "complete", "affected_entities": 25,
                    "sectors_affected": 2, "cascading": "cross_sector", "data_compromise": "sensitive",
                },
                "o_fields": {
                    "sectors_affected": "health, digital infrastructure",
                    "entity_relevance": "high_relevance", "ms_affected": 4,
                    "cross_border_pattern": "significant",
                    "coordination_needs": "eu_active", "capacity_exceeded": True,
                },
                "expected_t": "T3", "expected_o": "O3",
                "rationale": {"t_rationale": "Complete + sensitive = T3", "o_rationale": "EU active + significant = O3"},
            },
            {
                "id": "INC-004", "name": "Crisis incident", "date": "2024-04-01",
                "sources": ["https://example.com"],
                "description": "Supply chain compromise caused sustained disruption across critical infrastructure in multiple EU member states",
                "t_fields": {
                    "service_disruption": "sustained", "affected_entities": 150,
                    "sectors_affected": 5, "cascading": "uncontrolled", "data_compromise": "systemic",
                },
                "o_fields": {
                    "sectors_affected": "energy, transport, health, digital infrastructure, banking",
                    "entity_relevance": "systemic", "ms_affected": 8,
                    "cross_border_pattern": "systemic",
                    "coordination_needs": "full_ipcr", "capacity_exceeded": True,
                },
                "expected_t": "T4", "expected_o": "O4",
                "rationale": {"t_rationale": "Sustained + systemic = T4", "o_rationale": "Full IPCR + systemic = O4"},
            },
        ],
    }
    path = tmp_path / "curated_incidents.json"
    path.write_text(json.dumps(data))
    return path


def test_loader_produces_correct_count(curated_dataset):
    incidents = load_curated_incidents(curated_dataset)
    assert len(incidents) == 4


def test_matrix_lookup_for_curated_incidents(curated_dataset):
    incidents = load_curated_incidents(curated_dataset)
    expected_classifications = [
        "below_threshold",  # T1/O1
        "significant",      # T2/O2
        "large_scale",      # T3/O3
        "cyber_crisis",     # T4/O4
    ]
    for inc, expected_cls in zip(incidents, expected_classifications):
        result = classify_incident(inc.expected_t, inc.expected_o)
        assert result.classification == expected_cls, (
            f"{inc.id}: expected {expected_cls}, got {result.classification}"
        )


def test_full_dataset_loads_and_validates():
    """Test that the actual curated_incidents.json loads without errors."""
    dataset_path = PROJECT_ROOT / "data" / "reference" / "curated_incidents.json"
    if not dataset_path.exists():
        pytest.skip("curated_incidents.json not yet created")
    incidents = load_curated_incidents(dataset_path)
    assert len(incidents) >= 30, f"Expected at least 30 incidents, got {len(incidents)}"

    # Verify all T/O levels are represented
    t_levels = {inc.expected_t for inc in incidents}
    o_levels = {inc.expected_o for inc in incidents}
    assert t_levels == {"T1", "T2", "T3", "T4"}, f"Missing T levels: {{'T1','T2','T3','T4'} - t_levels}"
    assert o_levels == {"O1", "O2", "O3", "O4"}, f"Missing O levels: {{'O1','O2','O3','O4'} - o_levels}"
```

- [ ] **Step 2: Run tests**

Run: `poetry run pytest src/tests/test_benchmark_curated.py -v`
Expected: All tests PASS (the full dataset test may skip if file doesn't exist yet, or pass if Task 2 is complete)

- [ ] **Step 3: Commit**

```bash
git add src/tests/test_benchmark_curated.py
git commit -m "test(v2): add integration tests for curated benchmark pipeline"
```

---

### Task 6: Publish curated dataset to HuggingFace

**Files:**
- Modify: `training/scripts/publish_hf.py`

Add the curated dataset as a new HuggingFace dataset repository.

- [ ] **Step 1: Read current publish_hf.py to identify the dataset publishing pattern**

Read `training/scripts/publish_hf.py` and find the section that publishes datasets. Look for the `DATASET_REPOS` list or similar structure.

- [ ] **Step 2: Add the curated dataset repo**

Add a new entry to the dataset publishing configuration following the existing pattern. The exact edit depends on the current file structure, but it should map:

- Repo ID: `eromang/cyberscale-curated-incidents`
- Source file: `data/reference/curated_incidents.json`
- Dataset card: auto-generated describing the curated benchmark

The implementer should read the existing `publish_hf.py` and add the new dataset following the same pattern used for the Phase 3 training datasets.

- [ ] **Step 3: Commit**

```bash
git add training/scripts/publish_hf.py
git commit -m "feat(v2): add curated incidents dataset to HuggingFace publishing"
```

---

### Task 7: Run the benchmark and document results

**Files:**
- Output: `evaluation/curated_benchmark.md` (generated)

This task requires trained models on disk. It should be the final task after all code is merged.

- [ ] **Step 1: Run the curated benchmark**

Run:
```bash
poetry run python evaluation/benchmark_curated.py \
    --t-model data/models/technical \
    --o-model data/models/operational \
    --dataset data/reference/curated_incidents.json \
    --output evaluation/curated_benchmark.md \
    --mc-passes 5
```

Expected: Report generated at `evaluation/curated_benchmark.md`

- [ ] **Step 2: Review the results**

Check the report for:
1. T-model accuracy and F1 per level — which levels degrade most on real data?
2. O-model accuracy and F1 per level — same question
3. Matrix end-to-end accuracy — what's the gap vs synthetic (96.2%)?
4. Per-incident failures — do failures cluster around specific incident types?

These results directly inform which v2 enhancements to prioritise next.

- [ ] **Step 3: Commit the benchmark report**

```bash
git add evaluation/curated_benchmark.md
git commit -m "docs(v2): add initial curated benchmark results"
```

- [ ] **Step 4: Publish dataset to HuggingFace**

Run:
```bash
poetry run python training/scripts/publish_hf.py --dataset-only
```

Expected: Curated incidents dataset published to `eromang/cyberscale-curated-incidents`
