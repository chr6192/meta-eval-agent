## Expected Behavior

The agent should:

1. Read and parse the meeting transcript
2. Identify all named individuals from the "Members Present" lists, "Also Present" section, and dialogue
3. Determine attendance mode from the asterisk notation (phone) and roll call
4. Categorize each person's role and level of participation
5. Produce a well-structured markdown document

Key expected attendees:

- Dr. Brian Fontes (Chair, NENA) — In-person
- Larry Strickling (Asst. Secretary of Commerce) — In-person, Also Present
- Karl Nebbia (Associate Administrator, Office of Spectrum Management) — In-person, Also Present
- Tom Power (White House OSTP) — In-person, Also Present
- Bruce M. Washington (Designated Federal Officer) — In-person, Also Present
- Dale Hatfield (University of Colorado) — Remote (phone)
- Molly Feldman (Verizon Wireless) — Remote (phone)
- Doug McGinnis (Exelon) — Remote (phone)
- Dan Stancil (NC State) — Remote (phone)
- Rick Reaser (Raytheon) — Remote (phone)
- David Donovan — Remote (phone)
- Mr. Snider — Public participant (spoke during public comment)
- Total committee members: approximately 19-20
- Total attendees including officials and public: approximately 23-24

---

## Grading Criteria

- [ ] File `attendees.md` is created
- [ ] Brian Fontes correctly identified as Chair with NENA affiliation
- [ ] At least 15 committee members identified by name
- [ ] Remote/phone attendees correctly identified (Hatfield, Feldman, McGinnis, Stancil, Reaser, Donovan)
- [ ] Non-member officials listed (Strickling, Nebbia, Power, Washington)
- [ ] Organizations/affiliations included for most attendees
- [ ] Attendance mode (in-person vs phone) correctly noted
- [ ] Mr. Snider identified as public participant
- [ ] Summary count of attendees included

---

## LLM Judge Rubric

### Criterion 1: Completeness of Attendee Identification (Weight: 35%)

**Score 1.0**: All committee members, officials, and public participants are identified with correct names and roles. No one is missed.
**Score 0.75**: Most attendees identified (18+) with only minor omissions.
**Score 0.5**: Majority identified but several attendees missing.
**Score 0.25**: Only the most prominent speakers identified.
**Score 0.0**: Fewer than half of attendees identified.

### Criterion 2: Accuracy of Details (Weight: 30%)

**Score 1.0**: All organizations, titles, and attendance modes are correct. Remote vs in-person status matches the transcript's asterisk notation and roll call.
**Score 0.75**: Most details correct with one or two minor errors.
**Score 0.5**: Several errors in organizations or attendance mode.
**Score 0.25**: Many inaccuracies in affiliations or roles.
**Score 0.0**: Details are largely incorrect or fabricated.

### Criterion 3: Organization and Structure (Weight: 20%)

**Score 1.0**: Clear sections separating leadership, in-person members, remote members, officials, and public. Easy to scan and reference.
**Score 0.75**: Well-organized with minor structural issues.
**Score 0.5**: Some organization but sections are unclear or inconsistent.
**Score 0.25**: Poorly organized, hard to navigate.
**Score 0.0**: No meaningful structure.

### Criterion 4: Speaking Role Assessment (Weight: 15%)

**Score 1.0**: Accurately distinguishes between active participants (asked questions, made remarks) and those who only identified themselves during roll call.
**Score 0.75**: Most speaking roles correctly noted.
**Score 0.5**: Some attempt at noting participation level but incomplete.
**Score 0.25**: Minimal effort to distinguish participation levels.
**Score 0.0**: No assessment of speaking roles.

---
