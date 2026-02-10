"""
Quick analysis of Week 0 quality improvements.
Verifies that generated steps meet the new quality standards.
"""

import sys
from pathlib import Path
from docx import Document

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.action_validator import ActionValidator, WEAK_VERBS, STRONG_VERBS


def analyze_document(docx_path):
    """Analyze generated document for Week 0 quality metrics."""

    doc = Document(docx_path)
    validator = ActionValidator(min_actions=3, max_actions=6, min_content_words=50)

    print("=" * 80)
    print("WEEK 0 QUALITY ANALYSIS")
    print("=" * 80)
    print(f"\nDocument: {docx_path.name}")
    print()

    # Parse steps from document
    steps = []
    current_step = None
    current_section = None

    for para in doc.paragraphs:
        text = para.text.strip()

        if text.startswith("STEP "):
            # Save previous step
            if current_step:
                steps.append(current_step)

            # Start new step
            title = text.split(":", 1)[1].strip() if ":" in text else ""
            current_step = {
                "title": title,
                "summary": "",
                "details": "",
                "actions": []
            }
            current_section = None

        elif current_step:
            if text.upper().startswith("OVERVIEW:") or text.upper().startswith("SUMMARY:"):
                current_section = "summary"
                content = text.split(":", 1)[1].strip() if ":" in text else ""
                if content:
                    current_step["summary"] = content

            elif text.upper().startswith("CONTENT:") or text.upper().startswith("DETAILS:"):
                current_section = "details"
                content = text.split(":", 1)[1].strip() if ":" in text else ""
                if content:
                    current_step["details"] = content

            elif text.upper().startswith("KEY ACTIONS:") or text.upper().startswith("ACTIONS:"):
                current_section = "actions"

            elif current_section == "actions" and text.startswith("-"):
                action = text.lstrip("- ").strip()
                if action:
                    current_step["actions"].append(action)

            elif current_section == "summary" and text and not text.startswith("-"):
                current_step["summary"] += " " + text

            elif current_section == "details" and text and not text.startswith("-"):
                current_step["details"] += " " + text

    # Save last step
    if current_step:
        steps.append(current_step)

    print(f"Total steps found: {len(steps)}\n")

    # Analyze each step
    total_actions = 0
    total_weak_verbs = []
    total_strong_verbs = []
    total_word_count = 0

    for i, step in enumerate(steps, 1):
        print(f"\n{'=' * 80}")
        print(f"STEP {i}: {step['title']}")
        print(f"{'=' * 80}")

        # Validate step
        validation = validator.validate_step(step)

        # Action count
        action_count = len(step['actions'])
        total_actions += action_count
        print(f"\n✓ Action count: {action_count} {'✅' if 3 <= action_count <= 6 else '❌'}")

        # Check verbs
        weak_verbs = []
        strong_verbs = []

        for action in step['actions']:
            first_word = action.split()[0].lower().strip('.,!?;:()[]{}"\' ') if action.split() else ""

            if first_word in WEAK_VERBS:
                weak_verbs.append(first_word)
                total_weak_verbs.append(first_word)
            elif first_word in STRONG_VERBS:
                strong_verbs.append(first_word)
                total_strong_verbs.append(first_word)

        print(f"✓ Strong verbs: {len(strong_verbs)} {strong_verbs if strong_verbs else ''}")
        print(f"✓ Weak verbs: {len(weak_verbs)} {'❌ ' + str(weak_verbs) if weak_verbs else '✅ None'}")

        # Content length
        content = step.get('details', '') or step.get('summary', '')
        word_count = len(content.split())
        total_word_count += word_count
        print(f"✓ Content words: {word_count} {'✅' if word_count >= 50 else '❌'}")

        # Title check
        first_word_title = step['title'].split()[0].lower() if step['title'].split() else ""
        is_action_title = first_word_title in STRONG_VERBS or first_word_title.endswith('ing')
        print(f"✓ Action-oriented title: {'✅' if is_action_title else '⚠️'}")

        # Validation result
        print(f"\n✓ Overall validation: {'✅ PASSED' if validation.passed else '❌ FAILED'}")

        if validation.issues:
            print(f"  Issues: {', '.join(validation.issues)}")
        if validation.warnings:
            print(f"  Warnings: {', '.join(validation.warnings)}")

        # Show actions
        print(f"\nActions ({action_count}):")
        for j, action in enumerate(step['actions'], 1):
            print(f"  {j}. {action}")

    # Summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"\n✓ Total steps analyzed: {len(steps)}")
    print(f"✓ Average actions per step: {total_actions / len(steps) if steps else 0:.1f}")
    print(f"✓ Total weak verbs found: {len(total_weak_verbs)} {set(total_weak_verbs) if total_weak_verbs else '✅'}")
    print(f"✓ Total strong verbs used: {len(total_strong_verbs)}")
    print(f"✓ Average content words: {total_word_count / len(steps) if steps else 0:.1f}")
    print(f"\n✓ Week 0 Success Criteria:")
    print(f"  • All steps have 3-6 actions: {'✅ YES' if all(3 <= len(s['actions']) <= 6 for s in steps) else '❌ NO'}")
    print(f"  • Zero weak verbs: {'✅ YES' if len(total_weak_verbs) == 0 else '❌ NO (' + str(len(total_weak_verbs)) + ' found)'}")
    print(f"  • All steps >= 50 words: {'✅ YES' if all(len((s.get('details', '') or s.get('summary', '')).split()) >= 50 for s in steps) else '⚠️ SOME'}")
    print()


if __name__ == "__main__":
    docx_path = Path(__file__).parent / "test_output" / "chunk_based_pipeline_test.docx"

    if not docx_path.exists():
        print(f"❌ Document not found: {docx_path}")
        sys.exit(1)

    analyze_document(docx_path)
