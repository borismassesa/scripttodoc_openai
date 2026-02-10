# Document Structure & Format

## Visual Document Layout

```
┌─────────────────────────────────────────────────────────┐
│                    TITLE PAGE                            │
│                                                          │
│              [Large Title - 28pt, Blue]                 │
│                                                          │
│         [Subtitle - 16pt, Gray, Italic]                 │
│                                                          │
│              ┌─────────────────────┐                     │
│              │ Generated: [Date]  │                     │
│              │ Version: [Version] │                     │
│              │ Author: [Author]   │                     │
│              │ Tone: [Tone]       │                     │
│              │ Audience: [Aud]    │                     │
│              └─────────────────────┘                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              TABLE OF CONTENTS                          │
│                                                          │
│  [Instructions for auto-generation]                      │
│                                                          │
│  Document Sections:                                      │
│    • Step 1: [Title]                                     │
│    • Step 2: [Title]                                     │
│    • ...                                                 │
│    • Source References                                   │
│    • Document Statistics                                 │
│                                                          │
│  [Note about Word's TOC feature]                        │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              STEP 1: [Step Title]                        │
│  ─────────────────────────────────────────────────────  │
│                                                          │
│  Overview: [Summary text]                                │
│                                                          │
│  [Details paragraph with first-line indent]             │
│  [Proper line spacing for readability]                  │
│                                                          │
│  Key Actions:                                            │
│    • Action item 1                                      │
│    • Action item 2                                      │
│    • Action item 3                                      │
│                                                          │
│  Visual References:                                      │
│    • screenshot_01.png: [Description]                    │
│                                                          │
│  ┌─────────────────────────────────────────┐            │
│  │ Quality Indicator: High (85.0%)         │            │
│  │ Sources: transcript (3), visual (1)     │            │
│  └─────────────────────────────────────────┘            │
│                                                          │
│  ⚠ [Validation warnings if any]                         │
│                                                          │
│  ─────────────────────────────────────────────────────  │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              STEP 2: [Step Title]                        │
│  [Same format as Step 1]                                │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              SOURCE REFERENCES                          │
│                                                          │
│  [Introduction paragraph]                                │
│                                                          │
│  Step 1 Sources                                          │
│  Overall confidence: 85.0% (High) | Total sources: 4    │
│                                                          │
│  Source 1: Transcript (Sentence 5)                        │
│  ┌─────────────────────────────────────┐                │
│  │ "Full transcript excerpt here..."    │                │
│  └─────────────────────────────────────┘                │
│  Confidence: 90.0% (Very High)                           │
│                                                          │
│  Source 2: Visual (screenshot_01.png)                    │
│  ┌─────────────────────────────────────┐                │
│  │ "Screenshot description..."          │                │
│  └─────────────────────────────────────┘                │
│  Confidence: 75.0% (High)                                │
│                                                          │
│  Step 2 Sources                                          │
│  [Same format]                                           │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              DOCUMENT STATISTICS                         │
│                                                          │
│  [Introduction paragraph]                                │
│                                                          │
│  ┌──────────────────────┬──────────────────┐            │
│  │ Total Steps:         │ 8                │            │
│  │ Average Confidence:  │ 82.5% (High)     │            │
│  │ High Confidence:     │ 6 (≥70%)         │            │
│  │ Visual Support:      │ 3                │            │
│  │ Total Sources:       │ 24               │            │
│  │ Processing Time:     │ 2m 15s           │            │
│  └──────────────────────┴──────────────────┘            │
│                                                          │
│  [Summary analysis paragraph]                            │
└─────────────────────────────────────────────────────────┘
```

## Formatting Details

### Step Format
```
Step N: [Title]
─────────────────────────────────────
Overview: [Summary]

[Details paragraph with proper indentation and spacing]

Key Actions:
  • Action 1
  • Action 2
  • Action 3

Quality Indicator: [Level] ([Percentage]) | Sources: [Summary]
─────────────────────────────────────
```

### Source Reference Format
```
Step N Sources
Overall confidence: [%] ([Level]) | Total sources: [Count]

Source 1: [Type] ([Location])
"[Excerpt text]"
Confidence: [%] ([Level])
```

### Statistics Table Format
```
┌──────────────────────┬──────────────────┐
│ Metric Label:        │ Value            │
│ Metric Label:        │ Value (colored)  │
│ ...                  │ ...              │
└──────────────────────┴──────────────────┘
```

## Style Guide

### Headings
- **Heading 1**: 16pt, Bold, Blue (RGB 0, 70, 120)
  - Used for: Steps, Major sections
  - Spacing: 12pt before, 6pt after

- **Heading 2**: 14pt, Bold, Darker Blue (RGB 0, 100, 150)
  - Used for: Subsections (e.g., "Step N Sources")
  - Spacing: 10pt before, 4pt after

### Body Text
- **Default**: Calibri, 11pt
- **Line Spacing**: 1.15 (improved readability)
- **First-line Indent**: 0.25" (for details paragraphs)

### Lists
- **Bullet Lists**: 0.5" left indent
- **Numbered Lists**: For TOC placeholder
- **Spacing**: 3pt after each item

### Colors
- **Primary Blue**: RGB(0, 70, 120) - Headings, important labels
- **Secondary Blue**: RGB(0, 100, 150) - Subheadings
- **Gray**: RGB(100, 100, 100) - Metadata, secondary text
- **Confidence Green**: RGB(0, 150, 0) - High confidence (≥70%)
- **Confidence Yellow**: RGB(200, 150, 0) - Medium confidence (50-69%)
- **Confidence Red**: RGB(200, 0, 0) - Low confidence (<50%)

### Spacing Rules
- **Between sections**: 12pt
- **Between paragraphs**: 6-10pt (context-dependent)
- **Before headings**: 10-12pt
- **After headings**: 4-8pt
- **In lists**: 3pt between items

## Quality Indicators

### Confidence Levels
- **Very High**: ≥85% (Green)
- **High**: 70-84% (Green)
- **Medium**: 50-69% (Yellow/Orange)
- **Low**: 30-49% (Red)
- **Very Low**: <30% (Red)

### Display Format
```
Quality Indicator: [Level] ([Percentage]) | Sources: [Summary]
```

Example:
```
Quality Indicator: High (85.0%) | Sources: transcript (3), visual (1)
```

## Document Properties

- **Title**: Set from document title
- **Author**: "ScriptToDoc" (or from metadata)
- **Comments**: "Generated by ScriptToDoc AI"
- **Default Font**: Calibri, 11pt
- **Page Size**: Standard (8.5" x 11")
- **Margins**: Word defaults (1" all sides)

## Best Practices

1. **Consistent Formatting**: All similar elements use the same style
2. **Visual Hierarchy**: Clear distinction between headings, body, and metadata
3. **Readability**: Proper spacing and line heights
4. **Professional Appearance**: Clean, modern design
5. **TOC-Ready**: Uses proper heading styles for auto-generation
6. **Color Coding**: Meaningful use of color for confidence levels
7. **Structured Data**: Tables for statistics and metadata

