# Data flow

```mermaid
flowchart TD
  Catalog[Published course and lesson] --> Start[Authenticated start or resume]
  Start --> Submit[Submit exercise answer]
  Submit --> Grade[Server validation and grading]
  Grade --> Row[Upsert learner submission]
  Row --> XP[Once-only XP and completion]
  XP --> Activity[Daily activity and achievements]
  Activity --> Dashboard[Progress and leaderboard]
```

```mermaid
flowchart LR
  Personal[Owned personal words] --> Select[Select at most ten]
  Course[Published course words and filters] --> Select
  Select --> Snapshot[(Owned JSON snapshot)]
  Snapshot --> Empty[Empty cannot complete]
  Snapshot --> Complete[Complete nonempty session]
  Complete --> Test[Owned test-words handoff]
```

Flashcard completion does not award XP or implement a test grader. Snapshot content survives source-word deletion.

```mermaid
flowchart LR
  JSON[Versioned draft JSON] --> Contract[Schema and identity checks]
  Contract --> Audit[Offline evidence and grader probes]
  Audit --> Report[JSON and Markdown reports]
  Contract --> Import[Dry-run or explicit draft import]
  Import --> Draft[(Unpublished rows)]
  Draft --> Preview[Local reviewer preview]
  Preview --> Human[Teacher and translator review]
  Human --> SHA[Explicit reviewed SHA acknowledgement]
```

The SHA acknowledges an exact snapshot, not linguistic approval. Production publication is not an automatic startup step.

[Section index](README.md) · [Documentation home](../README.md)
