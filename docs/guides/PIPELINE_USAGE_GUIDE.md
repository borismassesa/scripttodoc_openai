# ScriptToDoc Pipeline - Complete Usage Guide

**How to process your own transcripts with Phase 1 & Phase 2 features**

---

## Quick Start (5 Minutes)

### 1. Prepare Your Transcript

Create a transcript file (plain text or .txt format):

```text
[00:15] Instructor: Welcome everyone. Today we'll learn how to create an Azure Resource Group.

[00:45] Instructor: First, log in to the Azure Portal at portal.azure.com.

[01:10] Instructor: Click on "Resource groups" in the left navigation menu.

[01:30] Instructor: Then click the "+ Create" button at the top.

[02:00] Participant: Do we need to select a subscription first?

[02:15] Instructor: Great question! Yes, you'll see a dropdown for "Subscription". Select your subscription.

[02:45] Instructor: Next, enter a name for your resource group. Use something descriptive like "my-app-resources".

[03:20] Instructor: Choose a region. I recommend selecting a region close to your users.

[04:00] Instructor: Finally, click "Review + Create" and then "Create".
```

Save this as `my_transcript.txt`

---

### 2. Run the Pipeline (Interactive Python)

```bash
cd backend
source venv/bin/activate
python
```

Then in Python:

```python
from script_to_doc.pipeline import ScriptToDocPipeline, PipelineConfig
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure pipeline with ALL Phase 1 & Phase 2 features enabled
config = PipelineConfig(
    # Azure credentials
    azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_openai_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),

    # Azure services
    use_openai=True,                 # Required for step generation

    # ===== PHASE 1 FEATURES (Intelligent Parsing + Segmentation) =====
    use_intelligent_parsing=True,    # Extract timestamps, speakers, questions
    use_topic_segmentation=True,     # Segment by topics (not arbitrary chunks)

    # ===== PHASE 2 FEATURES (Quality Gates) =====
    use_qa_filtering=True,           # Filter Q&A sections
    use_topic_ranking=True,          # Rank topics by importance
    use_step_validation=True,        # Validate step quality

    # Thresholds (tune as needed)
    qa_density_threshold=0.50,       # 50% questions = Q&A section
    importance_threshold=0.15,       # Min importance to keep topic
    min_confidence_threshold=0.1,    # Min confidence for validation

    # Document settings
    min_steps=3,
    target_steps=5,
    max_steps=10,
    document_title="How to Create an Azure Resource Group"
)

# Initialize pipeline
print("Initializing pipeline...")
pipeline = ScriptToDocPipeline(config)

# Load your transcript
with open("my_transcript.txt", 'r') as f:
    transcript_text = f.read()

print(f"Loaded transcript: {len(transcript_text)} characters")

# Process transcript
print("Processing... (this may take 20-30 seconds)")
result = pipeline.process(
    transcript_text=transcript_text,
    output_path="output/my_tutorial.md"
)

# Display results
print("\n" + "="*80)
print("RESULTS")
print("="*80)
print(f"✅ Success: {result.success}")
print(f"📄 Document: {result.document_path}")
print(f"⏱️  Time: {result.processing_time:.2f}s")
print(f"📊 Steps: {len(result.steps)}")

# Show step details
for i, step in enumerate(result.steps, 1):
    print(f"\n{i}. {step['title']}")
    print(f"   • Actions: {len(step['actions'])}")
    print(f"   • Confidence: {step['confidence_score']:.2f} ({step['quality_indicator']})")
    print(f"   • Quality: {step.get('quality_score', 'N/A'):.2f}")

    # Show first 2 actions
    for j, action in enumerate(step['actions'][:2], 1):
        print(f"      {j}. {action['action']}")

    if len(step['actions']) > 2:
        print(f"      ... and {len(step['actions']) - 2} more actions")

print(f"\n✅ Tutorial saved to: {result.document_path}")
```

**Expected output:**
```
Initializing pipeline...
Loaded transcript: 850 characters
Processing... (this may take 20-30 seconds)

================================================================================
RESULTS
================================================================================
✅ Success: True
📄 Document: output/my_tutorial.md
⏱️  Time: 23.4s
📊 Steps: 3

1. Accessing Azure Resource Groups
   • Actions: 4
   • Confidence: 0.62 (medium)
   • Quality: 0.78
      1. Open your web browser and navigate to https://portal.azure.com
      2. Sign in with your Azure account credentials
      ... and 2 more actions

2. Creating a New Resource Group
   • Actions: 6
   • Confidence: 0.71 (high)
   • Quality: 0.84
      1. Click on "Resource groups" in the left navigation menu
      2. Click the "+ Create" button at the top of the page
      ... and 4 more actions

3. Configuring Resource Group Settings
   • Actions: 5
   • Confidence: 0.58 (medium)
   • Quality: 0.72
      1. Select your Azure subscription from the "Subscription" dropdown
      2. Enter a descriptive name for your resource group (e.g., "my-app-resources")
      ... and 3 more actions

✅ Tutorial saved to: output/my_tutorial.md
```

---

## Configuration Options

### Feature Flags

```python
# Phase 1 Features
use_intelligent_parsing = True      # Extract metadata from transcript
use_topic_segmentation = True       # Segment by topics (recommended)

# Phase 2 Features
use_qa_filtering = True             # Remove Q&A sections
use_topic_ranking = True            # Prioritize important topics
use_step_validation = True          # Validate step quality

# Azure Services
use_azure_di = False                # Set True for PDF/image OCR
use_openai = True                   # Required for generation
```

### Threshold Tuning

**Q&A Filter Threshold:**
```python
qa_density_threshold = 0.50     # 50% questions = Q&A section

# Adjust based on your needs:
# - 0.30: More strict (filters sections with 30%+ questions)
# - 0.50: Balanced (default)
# - 0.70: More lenient (only filters obvious Q&A)
```

**Topic Ranking Threshold:**
```python
importance_threshold = 0.15     # Min importance to keep

# Adjust based on your needs:
# - 0.10: Keep more topics (lenient)
# - 0.15: Balanced (default)
# - 0.25: Keep fewer topics (strict)
```

**Confidence Threshold:**
```python
min_confidence_threshold = 0.1  # Min confidence for validation

# Adjust based on your needs:
# - 0.1: More lenient (default)
# - 0.2: Balanced
# - 0.3: Stricter validation
```

---

## Common Use Cases

### Case 1: Tutorial from Meeting Recording

**Scenario:** You recorded a training session and want to create a tutorial.

**Configuration:**
```python
config = PipelineConfig(
    # Enable all features
    use_intelligent_parsing=True,
    use_topic_segmentation=True,
    use_qa_filtering=True,
    use_topic_ranking=True,
    use_step_validation=True,

    # Stricter Q&A filtering (meetings have lots of Q&A)
    qa_density_threshold=0.40,

    # Normal importance threshold
    importance_threshold=0.15,

    # Generate 5-8 steps
    target_steps=6,
    max_steps=10,

    document_title="Team Training: Azure Deployment"
)
```

---

### Case 2: Documentation from Demo Video

**Scenario:** You have a product demo video transcript and want clean documentation.

**Configuration:**
```python
config = PipelineConfig(
    # Enable all features
    use_intelligent_parsing=True,
    use_topic_segmentation=True,
    use_qa_filtering=True,
    use_topic_ranking=True,
    use_step_validation=True,

    # Lenient Q&A filtering (demos have fewer questions)
    qa_density_threshold=0.60,

    # Higher importance threshold (focus on main content)
    importance_threshold=0.20,

    # More detailed steps
    target_steps=8,
    max_steps=15,

    document_title="Product Demo: Key Features"
)
```

---

### Case 3: Quick Notes from Conversation

**Scenario:** Informal conversation, just want basic structure.

**Configuration:**
```python
config = PipelineConfig(
    # Phase 1 only (faster, simpler)
    use_intelligent_parsing=True,
    use_topic_segmentation=True,

    # Disable Phase 2 for speed
    use_qa_filtering=False,
    use_topic_ranking=False,
    use_step_validation=False,

    # Fewer steps
    target_steps=3,
    max_steps=6,

    document_title="Meeting Notes"
)
```

---

## Command Line Usage

### Option 1: Create a Script

Create `process_transcript.py`:

```python
#!/usr/bin/env python3
"""Process a transcript file and generate a tutorial."""

import argparse
from pathlib import Path
from script_to_doc.pipeline import ScriptToDocPipeline, PipelineConfig
import os
from dotenv import load_dotenv

def main():
    parser = argparse.ArgumentParser(description='Process transcript to tutorial')
    parser.add_argument('input', help='Input transcript file')
    parser.add_argument('output', help='Output markdown file')
    parser.add_argument('--title', help='Document title', default='Tutorial')
    parser.add_argument('--phase2', action='store_true', help='Enable Phase 2 features')

    args = parser.parse_args()

    # Load environment
    load_dotenv()

    # Configure pipeline
    config = PipelineConfig(
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        use_openai=True,

        # Phase 1
        use_intelligent_parsing=True,
        use_topic_segmentation=True,

        # Phase 2 (optional)
        use_qa_filtering=args.phase2,
        use_topic_ranking=args.phase2,
        use_step_validation=args.phase2,

        document_title=args.title
    )

    # Process
    pipeline = ScriptToDocPipeline(config)

    with open(args.input, 'r') as f:
        transcript = f.read()

    print(f"Processing {args.input}...")
    result = pipeline.process(transcript, args.output)

    if result.success:
        print(f"✅ Success! Saved to {args.output}")
        print(f"   Steps: {len(result.steps)}")
        print(f"   Time: {result.processing_time:.2f}s")
    else:
        print(f"❌ Failed: {result.error}")

if __name__ == "__main__":
    main()
```

Make it executable:
```bash
chmod +x process_transcript.py
```

Run it:
```bash
# With Phase 1 only
./process_transcript.py my_transcript.txt output.md --title "My Tutorial"

# With Phase 1 + Phase 2
./process_transcript.py my_transcript.txt output.md --title "My Tutorial" --phase2
```

---

## Troubleshooting

### Issue: "No steps generated"

**Cause:** Transcript might be too short or lacks procedural content.

**Solution:**
```python
# Lower thresholds
config = PipelineConfig(
    importance_threshold=0.10,      # Keep more content
    min_confidence_threshold=0.05,  # Accept lower confidence
    min_steps=2,                    # Reduce minimum
)
```

---

### Issue: "All segments filtered"

**Cause:** Thresholds too aggressive for your transcript type.

**Solution:**
```python
# More lenient thresholds
config = PipelineConfig(
    qa_density_threshold=0.70,      # Less Q&A filtering
    importance_threshold=0.10,      # Keep more topics
)
```

---

### Issue: "Too many Q&A-style steps"

**Cause:** Q&A filter threshold too lenient.

**Solution:**
```python
# Stricter Q&A filtering
config = PipelineConfig(
    qa_density_threshold=0.30,      # Filter more aggressively
)
```

---

## Best Practices

1. **Start with defaults:** Use default thresholds first, then tune based on results

2. **Review output:** Check the generated document and adjust thresholds incrementally

3. **Use Phase 2 for:** Training recordings, demos, presentations
   **Skip Phase 2 for:** Quick notes, informal conversations

4. **Transcript quality matters:** Better transcripts (with timestamps, speakers) = better output

5. **Iterate:** Process → Review → Adjust thresholds → Process again

---

## Example Transcript Formats

**Format 1: Timestamped with speakers** (Best)
```
[00:15] Instructor: First, open the Azure Portal.
[00:45] Instructor: Click on Resource Groups.
[01:10] Participant: Where is that located?
[01:25] Instructor: It's in the left navigation menu.
```

**Format 2: Simple timestamps** (Good)
```
[00:15] First, open the Azure Portal.
[00:45] Click on Resource Groups in the left menu.
[01:30] Enter a name for your resource group.
```

**Format 3: Plain text** (Acceptable)
```
First, open the Azure Portal at portal.azure.com.
Click on Resource Groups in the left navigation menu.
Then click the Create button at the top.
Enter a descriptive name for your resource group.
```

---

## Output Example

The pipeline generates a markdown tutorial like this:

```markdown
# How to Create an Azure Resource Group

Generated with ScriptToDoc AI Pipeline

## Step 1: Accessing Azure Portal

**Confidence:** High (0.72)

1. Open your web browser
2. Navigate to https://portal.azure.com
3. Sign in with your Azure credentials
4. Wait for the portal dashboard to load

**Details:**
The Azure Portal is the web-based interface for managing all your Azure resources...

---

## Step 2: Creating Resource Group

**Confidence:** High (0.68)

1. Click "Resource groups" in the left navigation
2. Click "+ Create" button
3. Select your subscription
4. Enter resource group name
5. Choose a region

**Details:**
Resource groups are containers that hold related Azure resources...

---

[Additional steps...]
```

---

## Next Steps

- ✅ Process your first transcript
- ✅ Review and tune thresholds
- ✅ Integrate into your workflow
- ✅ Deploy to production (see DEPLOYMENT_CHECKLIST.md)

---

**Questions?** Check the test files for more examples:
- `test_phase2_e2e.py` - Full pipeline example
- `test_phase2_integration.py` - Configuration examples
- `PHASE2_COMPLETE.md` - Detailed documentation
