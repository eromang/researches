# CyberScale — MISP Integration Design

Exploration document for using MISP as a storage and information sharing engine for CyberScale. CIRCL develops and maintains MISP; CyberScale operates in the Luxembourg cybersecurity ecosystem where CIRCL is one of the national CSIRTs (alongside GOVCERT.LU) and a key actor in threat intelligence sharing. This is a natural integration path.

**Status:** Design exploration. Not yet implemented.

---

## Integration Axes

### 1. MISP → CyberScale (Input Feeds)

Threat intelligence from MISP enriches CyberScale assessments at multiple pipeline stages.

| MISP source | CyberScale input | Pipeline stage | Value |
|---|---|---|---|
| CVE events | Vulnerability description + CVSS data | Phase 1 (scorer) | Alternative to NVD; includes CIRCL enrichments |
| Threat actor galaxies | `threat_actor_type` | HCPN crisis qualification | Map galaxy clusters to `state_actor` / `terrorist_group` / `hybrid_operation` |
| Sightings on CVEs | Exploit availability signal | Phase 1 (severity boost) | Real-world exploitation evidence → higher severity |
| Warning lists | `suspected_malicious` enrichment | Phase 2 (entity incident) | Known bad infrastructure matching → automatic flag |
| Sector targeting tags | Contextual enrichment | Phase 2 (contextual model) | Which sectors are currently under active campaigns |
| Cross-border event correlation | `ms_affected` list | Phase 2 + Phase 3 | Multi-national MISP instances reveal cross-MS impact |
| Threat probability indicators | `threat_probability` | HCPN threat qualification | Derive High/Imminent from active IOCs, sightings, campaign intelligence |

**Highest-value input:** HCPN threat probability from MISP threat intelligence. Currently a bare analyst judgment input — MISP sightings, active campaigns, and correlated events provide evidence-based probability assessment.

### 2. CyberScale → MISP (Output Events)

CyberScale assessment results stored as MISP events for sharing via CSIRT Network (Art. 15), EU-CyCLONe, and sectoral authorities.

| CyberScale output | MISP event type | Sharing use case |
|---|---|---|
| Phase 1 severity score | Attribute on CVE event (`cyberscale-band` taxonomy) | Share enriched CVE assessments with constituency |
| Phase 2 entity assessment | Incident event with significance result object | NIS2 Art. 23 early warning sharing to CSIRT |
| Phase 2 IR threshold result | Structured attributes: `triggered_criteria`, `applicable_articles` | Quantitative threshold evidence for notification |
| Phase 2 LU/BE national result | Structured attributes: `ilr_reference` / `ccb_reference`, `competent_authority` | National-specific assessment for sectoral authority |
| Phase 3a national classification | Blueprint matrix result object (`t_level`, `o_level`, `classification`) | CSIRT Network sharing (Art. 15) |
| Phase 3b EU classification | EU-CyCLONe coordination event | Cross-MS situational awareness |
| HCPN crisis qualification | Crisis qualification event: `qualification_level`, `cooperation_mode`, criteria | PGGCCN activation coordination (CERC/CC) |
| Early warning recommendation | Event with `recommended`, `deadline`, `required_content` | Automated early warning trigger |
| Authority feedback | Feedback object: original classification + override + rationale | Rule calibration sharing between CSIRTs |

**Highest-value output:** Assessment results as MISP events for Art. 15 CSIRT Network sharing — structured, machine-readable incident classifications that other MS can correlate with their own data.

### 3. MISP as Storage Backend

Replace current JSON file storage with MISP events for queryable, versionable, shareable data.

| Current storage | MISP replacement | Benefit |
|---|---|---|
| `data/reference/curated_incidents.json` | MISP events with `cyberscale-validation` tag | Queryable, versionable, shareable |
| `data/reference/real_incident_validation.json` | MISP events with RETEX tag + CyberScale classification objects | Link RETEX to IOCs, threat actors, related events |
| Authority feedback store (`feedback.py`) | MISP event annotations (propose/accept workflow) | Multi-authority feedback with attribution and audit trail |
| Incident assessment history (future) | MISP event timeline (proposals, updates) | Built-in versioning for temporal tracking |

---

## Custom MISP Artifacts

### Taxonomies

| Taxonomy | Predicates | Purpose |
|---|---|---|
| `cyberscale:phase` | `phase-1`, `phase-2`, `phase-3a`, `phase-3b`, `hcpn-crisis` | Tag events by pipeline stage |
| `cyberscale:classification` | `below-threshold`, `significant`, `large-scale`, `cyber-crisis` | Blueprint matrix result |
| `cyberscale:cooperation-mode` | `permanent`, `alerte-cerc`, `crise` | HCPN/PGGCCN activation level |
| `cyberscale:significance-model` | `ir-thresholds`, `national-lu`, `national-be`, `nis2-ml` | Which assessment tier was used |
| `nis2:significance` | `significant`, `not-significant`, `undetermined` | NIS2 Art. 23 significance determination |
| `nis2:notification-stage` | `early-warning`, `notification`, `intermediate`, `final` | Notification lifecycle stage |

Existing MISP taxonomies to reuse:
- `tlp` — Traffic Light Protocol for sharing scope
- `admiralty-scale` — Source reliability for threat probability assessment
- `cssa` — CSSA threat assessment for HCPN probability mapping
- `eu-marketop-and-target` — EU market operator classification

### MISP Objects

#### `cyberscale-entity-assessment`

Represents a Phase 2 entity-level incident assessment.

| Attribute | Type | Description |
|---|---|---|
| `sector` | text | NIS2 sector (energy, transport, health, etc.) |
| `entity-type` | text | NIS2 entity type (electricity_undertaking, etc.) |
| `ms-established` | text | Member state where entity is established |
| `service-impact` | text | none / partial / degraded / unavailable / sustained |
| `data-impact` | text | none / accessed / exfiltrated / compromised / systemic |
| `safety-impact` | text | none / health_risk / health_damage / death |
| `financial-impact` | text | none / minor / significant / severe |
| `affected-persons-count` | counter | Number of persons affected |
| `impact-duration-hours` | float | Duration of impact |
| `significance-model` | text | ir_thresholds / national_lu / national_be / nis2_ml |
| `significant-incident` | boolean | Whether incident is significant |
| `triggered-criteria` | text | List of triggered threshold criteria |
| `competent-authority` | text | ILR / CCB / CSSF / etc. |
| `early-warning-recommended` | boolean | Whether early warning should be sent |
| `early-warning-deadline` | text | 24h (NIS2) / 4h (DORA) |

#### `cyberscale-authority-classification`

Represents a Phase 3 authority-level incident classification.

| Attribute | Type | Description |
|---|---|---|
| `t-level` | text | T1 / T2 / T3 / T4 |
| `o-level` | text | O1 / O2 / O3 / O4 |
| `classification` | text | below_threshold / significant / large_scale / cyber_crisis |
| `blueprint-provision` | text | 7(a) / 7(b) / 7(c) / 7(d) |
| `entity-count` | counter | Number of entities in aggregation |
| `sectors-affected` | counter | Number of sectors involved |
| `ms-affected` | counter | Number of member states involved |
| `cross-border` | boolean | Cross-border impact detected |
| `cascading-level` | text | none / limited / cross_sector / uncontrolled |

#### `cyberscale-crisis-qualification`

Represents an HCPN national crisis qualification result.

| Attribute | Type | Description |
|---|---|---|
| `qualification-level` | text | national_major_incident / large_scale_cybersecurity_incident / none |
| `cooperation-mode` | text | crise / alerte_cerc / permanent |
| `event-type` | text | incident / threat |
| `criterion-1-status` | text | met / not_met |
| `criterion-2-status` | text | met / not_met / undetermined / bypassed |
| `criterion-3-status` | text | met / not_met / undetermined |
| `fast-tracked` | boolean | Whether fast-track provision was applied |
| `recommend-consultation` | boolean | Whether consultation with plan actors is recommended |
| `consultation-reasons` | text | Specific undetermined criteria requiring consultation |
| `prejudice-actual` | boolean | Whether prejudice is actual (Crise) or potential (Alerte/CERC) |
| `threat-probability` | text | low / moderate / high / imminent (threats only) |

---

## Integration Architecture

```
MISP instance (CIRCL / GOVCERT.LU)
  │
  ├── Input feed → CyberScale
  │   ├── CVE events → Phase 1 scoring
  │   ├── Threat actor galaxies → HCPN threat_actor_type
  │   ├── Sightings → exploit availability signal
  │   ├── Warning lists → suspected_malicious enrichment
  │   └── Cross-border correlation → ms_affected
  │
  ├── Output feed ← CyberScale
  │   ├── Entity assessments ← Phase 2
  │   ├── National classifications ← Phase 3a
  │   ├── EU classifications ← Phase 3b
  │   └── Crisis qualifications ← HCPN
  │
  └── Sharing (MISP sync protocol)
      ├── CSIRT Network (Art. 15) ← Phase 3 classifications
      ├── EU-CyCLONe ← Phase 3b + HCPN large-scale events
      ├── Sectoral authorities ← National threshold results
      └── Other MS MISP instances ← Cross-border incident data
```

### PyMISP Integration Points

```python
from pymisp import PyMISP, MISPEvent, MISPObject

# Output: Store entity assessment as MISP event
def publish_entity_assessment(misp: PyMISP, assessment: dict) -> MISPEvent:
    event = MISPEvent()
    event.info = f"CyberScale entity assessment: {assessment['sector']} / {assessment['entity_type']}"
    event.add_tag(f"cyberscale:phase=\"phase-2\"")
    event.add_tag(f"cyberscale:significance-model=\"{assessment['significance']['model']}\"")
    event.add_tag(f"tlp:amber")

    obj = MISPObject("cyberscale-entity-assessment")
    obj.add_attribute("sector", assessment["sector"])
    obj.add_attribute("significant-incident", assessment["significance"]["significant_incident"])
    # ... populate all attributes
    event.add_object(obj)

    return misp.add_event(event)

# Input: Derive threat probability from MISP sightings
def derive_threat_probability(misp: PyMISP, threat_event_id: int) -> str:
    event = misp.get_event(threat_event_id)
    sightings = misp.sightings(event)

    active_sightings = [s for s in sightings if s["type"] == "0"]  # true positive
    recent = [s for s in active_sightings if is_recent(s, days=7)]

    if len(recent) > 10:
        return "imminent"
    elif len(recent) > 3:
        return "high"
    elif len(active_sightings) > 0:
        return "moderate"
    return "low"
```

---

## Implementation Phases

### Phase A: Output Events (easiest, immediate value)

Store CyberScale assessment results as MISP events. No changes to CyberScale classification logic — purely additive.

1. Define MISP object templates (JSON)
2. Create `cyberscale/integrations/misp_publisher.py`
3. Optional MCP tool: `publish_to_misp` (takes assessment result, creates MISP event)
4. TLP marking based on assessment sensitivity

**Prerequisite:** PyMISP library, MISP instance access (API key).

### Phase B: Input Feeds (highest value for HCPN)

Enrich CyberScale inputs from MISP threat intelligence.

1. `cyberscale/integrations/misp_enrichment.py`
2. Threat actor galaxy → `threat_actor_type` mapping
3. Sightings → `threat_probability` derivation
4. Warning lists → `suspected_malicious` enrichment
5. Optional: CVE sightings → Phase 1 severity boost

**Prerequisite:** MISP instance with populated threat intelligence (galaxies, sightings, warning lists).

### Phase C: Storage Backend (replaces JSON files)

Migrate curated incidents and validation data to MISP events.

1. Migration script: JSON → MISP events
2. Benchmark/validation scripts query MISP instead of reading JSON
3. Authority feedback as MISP proposals/annotations

**Prerequisite:** Phases A and B complete; stable MISP object templates.

---

## Mapping to CSIRT Network Sharing (NIS2 Art. 15)

NIS2 Article 15 requires CSIRTs to share information on incidents, threats, and vulnerabilities within the CSIRT Network. MISP is the de facto tool for this sharing.

| Art. 15 requirement | CyberScale + MISP implementation |
|---|---|
| Incident information sharing | Phase 3 classification events with TLP marking |
| Cross-border impact notification | Events tagged with affected MS, auto-synced to relevant national MISP instances |
| Threat intelligence sharing | HCPN threat qualification events correlated with MISP threat actor galaxies |
| Vulnerability information | Phase 1 CVE enrichment events with severity bands |
| Anonymised sharing | MISP distribution levels: organisation → community → connected → all |

---

## Mapping to EU-CyCLONe Coordination

For large-scale cybersecurity incidents (HCPN `large_scale_cybersecurity_incident` or Phase 3b `large_scale` / `cyber_crisis`):

| EU-CyCLONe need | CyberScale + MISP implementation |
|---|---|
| Situational awareness | Phase 3b EU classification event with aggregated national data |
| Impact assessment | HCPN crisis qualification event with criteria details |
| Coordination needs | CyCLONe Officer inputs stored as MISP event annotations |
| MS capacity status | `capacity_exceeded` attribute on crisis qualification object |
| Political sensitivity | Officer input attribute (restricted distribution) |

---

## Open Questions

1. **MISP instance scope:** Dedicated CyberScale MISP instance, or integrate into existing CIRCL/GOVCERT.LU instance?
2. **Object template governance:** Who maintains the CyberScale MISP objects? Submit to MISP default templates or keep as custom?
3. **Real-time vs batch:** Push assessments to MISP immediately (real-time), or batch publish (e.g., daily summary)?
4. **Authentication for MCP tools:** How does the MCP server authenticate to MISP? API key in environment variable?
5. **Bidirectional sync:** If an authority modifies a CyberScale event in MISP (e.g., overrides classification), should CyberScale ingest that as feedback?
6. **TLP defaults:** What TLP level for automated assessments? TLP:AMBER for entity assessments, TLP:RED for crisis qualifications?
