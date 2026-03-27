# Continuation Agent Instructions

## Purpose

This agent continues generating a research report that exceeded the 18,000-word limit in the main session. It reads the saved state and generates the next batch of sections.

## Instructions for the continuation agent

1. **Read state file**: Load `~/.claude/research_output/continuation_state_[report_id].json`
2. **Read existing report**: Read the last 3 sections of the existing report file for flow continuity
3. **Continue citation numbering**: Start from `state.citations.next_number`
4. **Maintain quality metrics**: Match the style from `state.quality_metrics`:
   - Words per finding: stay within ±20%
   - Citation density: match existing pattern
   - Prose ratio: maintain ≥80% prose, ≤20% bullets
5. **Generate next sections**: Write each section from `state.next_sections` list, one at a time
6. **Quality gates per section**:
   - Word count within ±20% of target
   - Citation density matches existing pattern
   - At least 80% prose
7. **If more sections remain after this batch**: Update state file, spawn next continuation agent
8. **If this is the final batch**:
   - Generate complete bibliography (ALL citations, no ranges, no placeholders)
   - Run validation: `python scripts/validate_report.py --report [path]`
   - Run citation verification: `python scripts/verify_citations.py --report [path]`
   - Delete state file

## State file structure

```json
{
  "progress": {
    "sections_completed": [],
    "word_count": 0,
    "continuation_count": 0
  },
  "citations": {
    "used_numbers": [],
    "next_number": 1,
    "bibliography_entries": {}
  },
  "research_context": {
    "question": "",
    "themes": [],
    "findings_summaries": [],
    "narrative_arc": ""
  },
  "quality_metrics": {
    "avg_words_per_finding": 0,
    "citation_density": 0,
    "prose_ratio": 0,
    "style": ""
  },
  "next_sections": [
    {"type": "finding", "title": "", "target_words": 0}
  ],
  "report_path": ""
}
```

## Critical rules

- Never fabricate citations — say "No sources found" instead
- Every factual claim must cite a specific source [N]
- Do not restart numbering — continue from `state.citations.next_number`
- Append to existing report file using Edit tool (never overwrite)
