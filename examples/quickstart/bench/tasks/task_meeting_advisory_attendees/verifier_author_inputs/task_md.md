---
id: task_meeting_advisory_attendees
name: NTIA Advisory Board Attendee List
category: Office Productivity
subcategory: Meeting
timeout_seconds: 300
input_modality: text-only
external_dependency: none
workspace_files:
- source: assets/T060_pinchbench_meeting_advisory_attendees/meetings/2012-05-30-meeting-transcript-ntia-csmac.md
  dest: meeting-transcript.md
labels:
  scenario: Office_Productivity/Meeting
  capabilities:
  - Tool_Use
  - Planning
  - Logic_Reasoning
  modality:
    type: text
    channels: []
  complexity: L3
  environment: closed
---

## Prompt

I have a transcript of a government advisory committee meeting in `meeting-transcript.md`. This is a meeting of the Commerce Spectrum Management Advisory Committee (CSMAC) held on May 30, 2012.

Please analyze the transcript and create a structured attendee list in a file called `attendees.md`. For each attendee, include:

- **Full name** (with title if mentioned, e.g., Dr., Esq.)
- **Role at the meeting** (Chair, Member, Also Present, Public Participant)
- **Organization and title** (as stated in the transcript)
- **Attendance mode** (In-person or Phone/Remote)
- **Speaking role** (whether they made substantive remarks, asked questions, or only identified themselves)

Organize the list into sections: Committee Leadership, Committee Members (In-Person), Committee Members (Remote), Non-Member Officials, and Public Participants. Include a summary count of total attendees at the end.

---


## Additional Notes

This task tests the agent's ability to:

- Extract structured information from an unstructured meeting transcript
- Distinguish between different attendance categories and roles
- Cross-reference information from multiple sections of the document (header lists vs. dialogue)
- Handle the asterisk notation convention for remote attendees
- Identify a public participant (Mr. Snider) who speaks near the end but is not in the formal member lists
