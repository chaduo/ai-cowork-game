## Purpose

Defines evidence-based playtesting and a bounded platform-controlled repair loop that can improve a failing Candidate without publishing unsafe work or allowing Agents to self-orchestrate.

## ADDED Requirements

### Requirement: Structured TestReport
TestAgent SHALL return a TestReport covering build, page load, blocking console errors, player movement, enemy loop, item collection, NPC interaction, and a game outcome with evidence for every check.

#### Scenario: Test failure is reported
- **WHEN** one required gameplay check fails
- **THEN** TestReport verdict is FAIL and identifies the failed check, diagnostic message, and evidence

### Requirement: Platform validates test evidence
The platform SHALL verify required checks, evidence references, and deterministic command results before accepting a TestReport verdict.

#### Scenario: Evidence contradicts PASS
- **WHEN** deterministic build or browser results contradict a TestAgent PASS verdict
- **THEN** the platform marks the TestReport invalid and prevents Version publication

### Requirement: Bounded repair and retest
The platform SHALL control the sequence TestAgent FAIL → CodingAgent repair → new Candidate attempt → TestAgent retest and SHALL enforce configured attempt, time, and cost limits.

#### Scenario: Repair succeeds within budget
- **WHEN** CodingAgent repairs a failed Candidate and the next TestReport passes within budget
- **THEN** the platform may publish the new Candidate attempt as a Version

#### Scenario: Repair budget is exhausted
- **WHEN** the next repair would exceed an attempt, time, or cost limit
- **THEN** the run ends with a diagnosable failure and the existing playable Version remains unchanged
