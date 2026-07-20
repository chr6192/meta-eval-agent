---
id: task_meeting_gov_data_sources
name: NASA UAP Hearing Data Sources Extraction
category: meeting_analysis
subcategory: Meeting Transcript Extraction
timeout_seconds: 180
input_modality: text-only
external_dependency: none
workspace_files:
- source: assets/T070_pinchbench_meeting_gov_data_sources/meetings/2025-07-30-nasa-holds-first-public-meeting-on-ufos-transcript.md
  dest: transcript.md
labels:
  complexity: L3
  environment: closed
  modality:
    type: text
    channels: []
  capabilities:
  - Tool_Use
  - Planning
  - Logic_Reasoning
  scenario: Office_Productivity/Document
---

## Prompt

I have a transcript file `transcript.md` from NASA's first public meeting on Unidentified Anomalous Phenomena (UAPs/UFOs). Throughout the meeting, speakers referenced various data sources, sensors, databases, and measurement systems relevant to UAP research.

Please read the transcript and extract all referenced data sources and measurement systems into a file called `data_sources.md`. For each source, include:

- **Name/Type** of data source or sensor system
- **Owner/Operator** (agency or organization)
- **Description** (what it measures or provides)
- **Relevance to UAP** (how it was discussed in context of UAP research)
- **Limitations** (any noted limitations or caveats mentioned)
- **Who referenced it** (speaker name)

Organize sources into categories: Government/Military Sensors, Civilian Aviation Systems, Space-Based Assets, Ground-Based Scientific Instruments, Crowdsource/Public Data, and Databases/Archives. Include a summary table at the top listing all sources with their category and owner.

---


## Additional Notes

This task tests the agent's ability to:

- Identify technical systems and data sources mentioned in context (not just listed)
- Extract technical specifications from conversational discussion
- Distinguish between different types of sensors and their capabilities
- Note both capabilities and limitations
- Present technical information in a structured, referenceable format

Speakers often mention data sources in passing or as examples rather than in a structured way. The agent must identify these references across the full transcript.
