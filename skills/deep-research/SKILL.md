---
name: deep-research
description: Conduct enterprise-grade research with multi-source synthesis, citation tracking, and verification. Use when user needs comprehensive analysis requiring 10+ sources, verified claims, or comparison of approaches. Triggers include "deep research", "comprehensive analysis", "research report", "compare X vs Y", or "analyze trends". Do NOT use for simple lookups, debugging, or questions answerable with 1-2 searches.
---

# Deep Research

## Core Purpose

Deliver citation-backed, verified research reports through an 8-phase pipeline (Scope → Plan → Retrieve → Triangulate → Synthesize → Critique → Refine → Package) with source credibility scoring and progressive context management.

---

## Decision Tree (Execute First)

```
Request Analysis
├─ Simple lookup? → STOP: Use WebSearch, not this skill
├─ Debugging? → STOP: Use standard tools, not this skill
└─ Complex analysis needed? → CONTINUE

Mode Selection
├─ Initial exploration? → quick (3 phases, 2-5 min)
├─ Standard research? → standard (6 phases, 5-10 min) [DEFAULT]
├─ Critical decision? → deep (8 phases, 10-20 min)
└─ Comprehensive review? → ultradeep (8+ phases, 20-45 min)
```

---

## Workflow

### 1. Clarify (Rarely Needed)

**DEFAULT: Proceed autonomously.** Only ask if query is incomprehensible or contradictory.

Default assumptions:
- Technical query → technical audience
- Comparison → balanced perspective
- Trend → recent 1-2 years
- Standard mode unless specified

### 2. Plan

Announce plan and execute immediately (no approval needed):
- Selected mode, estimated time, number of sources
- Example: "Starting standard mode research (5-10 min, 15-30 sources)"

### 3. Act (Phase Execution)

**All modes:** Phase 1 (SCOPE), Phase 3 (RETRIEVE), Phase 8 (PACKAGE)
**Standard+:** Phase 2 (PLAN), Phase 4 (TRIANGULATE), Phase 4.5 (OUTLINE REFINEMENT), Phase 5 (SYNTHESIZE)
**Deep+:** Phase 6 (CRITIQUE), Phase 7 (REFINE)

Load phase details from [methodology](./reference/methodology.md) on-demand.

**Parallel Execution (CRITICAL for Speed):**
- Decompose query into 5-10 independent search angles
- Launch ALL searches in a single message (NOT sequential)
- Spawn 3-5 parallel agents via Task tool for deep-dive investigations

```
✅ RIGHT: All searches + agents launched simultaneously in one message
❌ WRONG: WebSearch #1 → wait → WebSearch #2 → wait → ...
```

**Anti-Hallucination Protocol:**
- Every factual claim MUST cite a specific source [N]
- Distinguish FACTS (from sources) from SYNTHESIS (your analysis)
- Use "According to [1]..." for source-grounded statements
- Never fabricate citations — say "No sources found" instead

### 4. Verify (Always Execute)

**Step 1: Citation Verification**
```bash
python scripts/verify_citations.py --report [path]
```
- DOI resolution, title/year matching, flags suspicious entries
- Remove or replace any fabricated sources

**Step 2: Structure & Quality Validation**
```bash
python scripts/validate_report.py --report [path]
```
- 8 automated checks: summary length, required sections, citation format, bibliography completeness, no placeholders, word count, minimum sources, no broken links
- Max 2 fix attempts → if still fails, report to user

### 5. Report

**File Organization:**
Create dedicated folder: `C:/Users/ninni/Documents/[TopicName]_Research_[YYYYMMDD]/`

**Three formats (all saved to same folder):**

| Format | Details |
|--------|---------|
| Markdown | Primary source, full detailed report |
| HTML | McKinsey-style, use [template](./templates/mckinsey_report_template.html), auto-open in browser |
| PDF | Via generating-pdf skill (Task tool), auto-open in viewer |

File naming: `research_report_[YYYYMMDD]_[topic_slug].{md,html,pdf}`

**Report Length by Mode:**
- Quick: 2,000-4,000 words
- Standard: 4,000-8,000 words
- Deep: 8,000-15,000 words
- UltraDeep: 15,000-20,000 words

**Progressive File Assembly:** Generate each section individually via Write/Edit tools (≤2,000 words per call). Each Write/Edit call contains ONE section.

**Section Generation Loop:**
1. Executive Summary (200-400 words) → Write(file, frontmatter + summary)
2. Introduction (400-800 words) → Edit(append)
3. Finding 1-N (600-2,000 words each) → Edit(append) per finding
4. Synthesis & Insights → Edit(append)
5. Limitations & Caveats → Edit(append)
6. Recommendations → Edit(append)
7. Bibliography (ALL citations, no ranges/placeholders) → Edit(append)
8. Methodology Appendix → Edit(append)

Track `citations_used` list throughout. Progress update after each section.

**Output Token Limit (32K tokens ≈ 20,000 words max per execution):**
- Quick/Standard/Deep: Comfortably under limit
- UltraDeep (15,000-20,000 words): At limit, monitor closely

**Auto-Continuation Protocol (for reports >18,000 words):**

When report exceeds 18,000 words in single run:
1. Generate sections 1-10 (stay under 18K words)
2. Save continuation state to `C:/Users/ninni/.claude/research_output/continuation_state_[report_id].json`
3. Spawn continuation agent via Task tool (general-purpose)
4. Continuation agent reads state → generates next batch → spawns next agent if needed
5. Chain continues recursively until complete

**Continuation state includes:**
- `progress`: sections completed, word count, continuation count
- `citations`: used numbers, next number, full bibliography entries
- `research_context`: question, themes, findings summaries, narrative arc
- `quality_metrics`: avg words/finding, citation density, prose ratio, style
- `next_sections`: remaining sections with type and target words

**Continuation agent instructions:**
1. Read state file and existing report (last 3 sections for flow)
2. Continue citation numbering from `state.citations.next_number`
3. Maintain quality metrics (words, density, prose ratio, style)
4. Quality gates per section: word count ±20%, citation density match, ≥80% prose
5. If more sections remain: update state, spawn next agent
6. If final: generate complete bibliography, run validation, cleanup state file

**HTML Generation:**
```bash
cd C:/Users/ninni/.claude/skills/deep-research
python scripts/md_to_html.py [markdown_report_path]
```
Then verify:
```bash
python scripts/verify_html.py --html [html_path] --md [md_path]
```

**Deliver to user:**
1. Executive summary (inline in chat)
2. Organized folder path
3. Confirmation of all three formats
4. Source quality assessment
5. Next steps (if relevant)

---

## Output Contract

**Required sections (use [template](./templates/report_template.md)):**
- Executive Summary (50-250 words)
- Introduction (question, scope, methodology, assumptions)
- Main Analysis (4-8 findings, each with citations)
- Synthesis & Insights (patterns, novel insights, implications)
- Limitations & Caveats (gaps, assumptions, uncertainties)
- Recommendations (immediate actions, next steps, further research)
- Bibliography (COMPLETE — every [N] citation must have a full entry)
- Methodology Appendix

**Bibliography Rules (ZERO TOLERANCE):**
- Include EVERY citation [N] used in report body
- Format: [N] Author/Org (Year). "Title". Publication. URL
- NO placeholders, NO ranges ([3-50]), NO truncation

**Writing Standards:**
- Narrative-driven prose (not bullet lists)
- Precise: "reduced mortality 23% (p<0.01)" not "significantly improved"
- Every claim cited in same sentence: "The market reached $2.4B in 2023 [1]."
- Use bullets only for distinct lists (products, steps), default to paragraphs
- ≥80% prose, ≤20% bullets

**Quality gates:**
- Minimum 10 sources (document if fewer)
- 3+ sources per major claim
- Average credibility score >60/100
- No placeholders (TBD, TODO)

---

## Error Handling

**Stop immediately if:**
- 2 validation failures on same error → report to user
- <5 sources after exhaustive search → report limitation
- User interrupts/changes scope → confirm new direction

**Graceful degradation:**
- 5-10 sources → note in limitations, proceed with extra verification
- Time constraint → package partial results, document gaps

---

## Scripts

**Location:** `./scripts/`

| Script | Purpose |
|--------|---------|
| `research_engine.py` | Orchestration engine |
| `validate_report.py` | Quality validation (8 checks) |
| `verify_citations.py` | Citation verification |
| `verify_html.py` | HTML output verification |
| `md_to_html.py` | Markdown → HTML conversion |
| `citation_manager.py` | Citation tracking |
| `source_evaluator.py` | Credibility scoring (0-100) |

No external dependencies required.

---

## Progressive References (Load On-Demand)

- [Complete Methodology](./reference/methodology.md) — 8-phase details
- [Report Template](./templates/report_template.md) — Output structure

**Context Management:** Load files on-demand for current phase only. Do not preload all content.
