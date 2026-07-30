## Expected Behavior

The agent should:

1. Read and parse the full transcript
2. Identify all data sources, sensors, databases, and measurement systems mentioned
3. Capture both the capabilities and limitations discussed for each
4. Organize comprehensively

Key data sources referenced:

**Government/Military:**
- AARO database (800+ cases, DOD/IC classified holdings)
- DOD sensors (F-35 cameras, MQ-9 EO sensors — "not scientific sensors")
- Intelligence community sensors ("very close to scientific sensors, calibrated, high precision")
- Purpose-built AARO sensors for UAP detection

**Civilian Aviation:**
- FAA short-range radars (40-60 mile range, up to 24,000 ft)
- FAA long-range radars / ARSR-4 and CRSR systems (200-250 nm range, up to 100,000 ft)
- ADS-B (Automatic Dependent Surveillance-Broadcast) cooperative system
- FAA TRACON terminal systems
- ERAM (En Route Automation Modernization) / STARS systems
- FAA Domestic Events Network (reporting system)

**Space-Based:**
- NASA earth science/sensing satellites
- NOAA satellites
- James Webb Space Telescope (mentioned as calibration example)
- Hubble Space Telescope (mentioned as calibration example)
- International Space Station imaging (sprites observation example)

**Ground-Based Scientific:**
- Large-scale radio telescopes (FRB detection analogy)
- Astronomical observatories (time-domain survey telescopes)
- NOAA ground sensors
- National Weather Service balloon tracking systems

**Crowdsource/Public:**
- Smartphone sensor data (GPS, location, speed, accelerometer)
- Eyewitness reports (noted as insufficient alone)
- iPhone imagery (noted as "generally not helpful" unless close range)
- Proposed NASA crowdsourcing platform

**Databases/Archives:**
- NASA open data portal (data.nasa.gov)
- Data.gov open data resources
- FAA processed radar data archives (retained for months)
- National Weather Service balloon launch records (92 stations, twice daily)

---

## Grading Criteria

- [ ] Output file `data_sources.md` is created
- [ ] AARO database referenced with case count details
- [ ] FAA radar systems described (short-range and long-range differentiated)
- [ ] ADS-B system mentioned
- [ ] NASA satellites / earth sensing assets referenced
- [ ] Smartphone / citizen science data sources included
- [ ] NASA open data portal (data.nasa.gov) mentioned
- [ ] Limitations noted for at least 3 data sources
- [ ] Sources organized into categories
- [ ] Summary table or overview included

---

## LLM Judge Rubric

### Criterion 1: Source Identification Completeness (Weight: 30%)

**Score 1.0**: At least 15 distinct data sources/systems identified across all categories. Covers military sensors, FAA systems, space assets, scientific instruments, and public/citizen data. No major sources missed.
**Score 0.75**: 10-14 sources across most categories.
**Score 0.5**: 6-9 sources with some categories underrepresented.
**Score 0.25**: Fewer than 6 sources.
**Score 0.0**: No sources identified.

### Criterion 2: Technical Accuracy (Weight: 25%)

**Score 1.0**: Descriptions are technically accurate including specific details (e.g., FAA short-range radar 40-60 mile range, ADS-B coverage to 1,500 ft AGL, MQ-9 EO sensor). Limitations correctly described.
**Score 0.75**: Mostly accurate with minor technical errors.
**Score 0.5**: Some accuracy but significant technical details missing.
**Score 0.25**: Vague or inaccurate descriptions.
**Score 0.0**: No technical details.

### Criterion 3: Limitation Analysis (Weight: 25%)

**Score 1.0**: Limitations clearly noted for key systems. Includes: DOD sensors not designed for science, FAA filtering removes small targets, radar line-of-sight constraints, iPhone photos generally unhelpful, eyewitness reports alone insufficient.
**Score 0.75**: Limitations noted for most systems.
**Score 0.5**: Some limitations noted but incomplete.
**Score 0.25**: Few limitations mentioned.
**Score 0.0**: No limitations discussed.

### Criterion 4: Organization and Presentation (Weight: 20%)

**Score 1.0**: Clear categorization, summary table at top, consistent formatting for each entry, easy to reference and compare sources.
**Score 0.75**: Good organization with minor issues.
**Score 0.5**: Organized but inconsistent formatting.
**Score 0.25**: Poorly organized.
**Score 0.0**: No organization.

---
