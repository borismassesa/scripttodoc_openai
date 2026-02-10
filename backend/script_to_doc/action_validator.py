"""
Action validation for training steps.
Validates that actions use strong, actionable verbs and meet quality criteria.
"""

import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Weak verbs that are not actionable
WEAK_VERBS = {
    # Learning verbs (not actionable)
    'learn', 'understand', 'know', 'remember', 'recall', 'recognize',
    'comprehend', 'grasp', 'appreciate', 'realize', 'familiarize',

    # Passive verbs (not specific)
    'review', 'read', 'study', 'examine', 'consider', 'explore',
    'look at', 'check out', 'be aware', 'keep in mind', 'note',
    'observe', 'watch', 'see', 'view',

    # Vague verbs (not measurable)
    'ensure', 'make sure', 'try', 'attempt', 'work on', 'deal with',
    'handle', 'manage', 'take care of',
}

# Strong action verbs that are specific and actionable
STRONG_VERBS = {
    # Configuration verbs
    'configure', 'set', 'enable', 'disable', 'update', 'modify',
    'adjust', 'customize', 'change', 'edit', 'setup',

    # Creation verbs
    'create', 'add', 'define', 'initialize', 'generate', 'build',
    'construct', 'establish', 'develop', 'make', 'design',

    # Execution verbs
    'run', 'execute', 'deploy', 'install', 'implement', 'apply',
    'launch', 'start', 'invoke', 'trigger', 'activate',

    # Navigation verbs
    'navigate', 'open', 'access', 'go to', 'select', 'click',
    'choose', 'pick', 'locate', 'find',

    # Verification verbs
    'verify', 'test', 'validate', 'confirm', 'check', 'monitor',
    'inspect', 'examine', 'assess', 'evaluate',

    # Removal verbs
    'remove', 'delete', 'disable', 'clear', 'reset', 'uninstall',
    'deactivate', 'stop', 'terminate', 'kill',

    # Data verbs
    'enter', 'input', 'type', 'specify', 'provide', 'fill',
    'insert', 'paste', 'upload', 'download', 'copy',

    # Organization verbs
    'organize', 'arrange', 'sort', 'group', 'categorize',
    'structure', 'order', 'prioritize',
}

# Verb replacement suggestions
VERB_SUGGESTIONS = {
    'learn': 'Complete the tutorial, then configure',
    'understand': 'Review the documentation, then implement',
    'review': 'Analyze the configuration and update',
    'read': 'Open the file and identify',
    'ensure': 'Verify',
    'make sure': 'Confirm',
    'try': 'Execute',
    'attempt': 'Run',
    'check out': 'Examine',
    'look at': 'Open',
    'be aware': 'Note',
    'keep in mind': 'Remember',
    'familiarize': 'Study the documentation, then configure',
}


@dataclass
class ActionValidationResult:
    """Result of action validation."""
    is_valid: bool
    verb: str
    is_weak: bool
    suggestion: Optional[str] = None
    warning: Optional[str] = None


@dataclass
class StepValidationResult:
    """Result of step validation."""
    passed: bool
    action_count: int
    issues: List[str]
    warnings: List[str]
    weak_verbs_found: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "passed": self.passed,
            "action_count": self.action_count,
            "issues": self.issues,
            "warnings": self.warnings,
            "weak_verbs_found": self.weak_verbs_found
        }


class ActionValidator:
    """Validator for action quality."""

    def __init__(
        self,
        min_actions: int = 3,
        max_actions: int = 6,
        min_content_words: int = 50
    ):
        """
        Initialize action validator.

        Args:
            min_actions: Minimum number of actions per step
            max_actions: Maximum number of actions per step
            min_content_words: Minimum word count for content/details
        """
        self.min_actions = min_actions
        self.max_actions = max_actions
        self.min_content_words = min_content_words

    def validate_action_verb(self, action_text: str) -> ActionValidationResult:
        """
        Validate an action verb.

        Args:
            action_text: Full action text (e.g., "Configure the settings")

        Returns:
            ActionValidationResult with validation status
        """
        # Extract the first word (verb)
        words = action_text.strip().split()
        if not words:
            return ActionValidationResult(
                is_valid=False,
                verb="",
                is_weak=True,
                warning="Empty action text"
            )

        verb = words[0].lower().strip('.,!?;:()[]{}"\'')

        # Check for weak verbs
        if verb in WEAK_VERBS:
            suggestion = VERB_SUGGESTIONS.get(verb, f"Use a specific action verb instead of '{verb}'")
            return ActionValidationResult(
                is_valid=False,
                verb=verb,
                is_weak=True,
                suggestion=suggestion
            )

        # Check for strong verbs
        if verb in STRONG_VERBS:
            return ActionValidationResult(
                is_valid=True,
                verb=verb,
                is_weak=False
            )

        # Unknown verb - allow but warn
        return ActionValidationResult(
            is_valid=True,
            verb=verb,
            is_weak=False,
            warning=f"Consider using a more specific verb than '{verb}'"
        )

    def validate_step(self, step: Dict) -> StepValidationResult:
        """
        Validate a complete step.

        Checks:
        - Action count (3-6)
        - No weak verbs
        - Content length (min 50 words)
        - Title is action-oriented
        - Overview exists and doesn't repeat title

        Args:
            step: Step dictionary with title, summary, details, actions

        Returns:
            StepValidationResult with validation details
        """
        issues = []
        warnings = []
        weak_verbs_found = []

        # Check action count
        actions = step.get('actions', [])
        action_count = len(actions)

        if action_count < self.min_actions:
            issues.append(f"Insufficient actions: {action_count} (minimum {self.min_actions})")
        elif action_count > self.max_actions:
            issues.append(f"Too many actions: {action_count} (maximum {self.max_actions})")

        # Validate each action verb
        for i, action in enumerate(actions, 1):
            result = self.validate_action_verb(action)

            if result.is_weak:
                weak_verbs_found.append(result.verb)
                issues.append(f"Action {i} has weak verb '{result.verb}': {result.suggestion}")
            elif result.warning:
                warnings.append(f"Action {i}: {result.warning}")

        # Check content length
        content = step.get('details', '') or step.get('summary', '')
        word_count = len(content.split()) if content else 0

        if word_count < self.min_content_words:
            issues.append(
                f"Content too thin: {word_count} words (minimum {self.min_content_words})"
            )

        # Check title exists and is action-oriented
        title = step.get('title', '').strip()
        if not title:
            issues.append("Missing title")
        else:
            # Check if title starts with action verb or gerund (verb+ing)
            first_word = title.split()[0].lower() if title.split() else ""
            is_gerund = first_word.endswith('ing')
            is_action_verb = first_word in STRONG_VERBS

            if not (is_gerund or is_action_verb):
                warnings.append(
                    f"Title '{title}' should start with action verb or gerund (e.g., 'Configuring...')"
                )

        # Check overview/summary exists
        summary = step.get('summary', '').strip()
        if not summary:
            warnings.append("Missing overview/summary")
        elif summary.lower() == title.lower():
            warnings.append("Overview should not repeat the title")

        # Determine pass/fail
        passed = len(issues) == 0

        return StepValidationResult(
            passed=passed,
            action_count=action_count,
            issues=issues,
            warnings=warnings,
            weak_verbs_found=weak_verbs_found
        )

    def validate_multiple_steps(
        self,
        steps: List[Dict]
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Validate multiple steps and return valid/invalid splits.

        Args:
            steps: List of step dictionaries

        Returns:
            Tuple of (valid_steps, invalid_steps, summary_stats)
        """
        valid_steps = []
        invalid_steps = []

        total_weak_verbs = set()
        total_issues = []
        total_warnings = []

        for i, step in enumerate(steps, 1):
            result = self.validate_step(step)

            if result.passed:
                valid_steps.append(step)
            else:
                invalid_steps.append({
                    "step_index": i,
                    "step": step,
                    "validation": result
                })
                logger.warning(
                    f"Step {i} validation failed: {', '.join(result.issues)}"
                )

            total_weak_verbs.update(result.weak_verbs_found)
            total_issues.extend(result.issues)
            total_warnings.extend(result.warnings)

        summary = {
            "total_steps": len(steps),
            "valid_steps": len(valid_steps),
            "invalid_steps": len(invalid_steps),
            "unique_weak_verbs": list(total_weak_verbs),
            "total_issues": len(total_issues),
            "total_warnings": len(total_warnings)
        }

        logger.info(
            f"Validation complete: {summary['valid_steps']}/{summary['total_steps']} "
            f"steps passed, {summary['total_issues']} issues, {summary['total_warnings']} warnings"
        )

        return valid_steps, invalid_steps, summary


# Convenience functions

def validate_action(action_text: str) -> Tuple[bool, str]:
    """
    Quick validation of a single action.

    Args:
        action_text: Action text to validate

    Returns:
        Tuple of (is_valid, message)
    """
    validator = ActionValidator()
    result = validator.validate_action_verb(action_text)

    if result.is_weak:
        return False, f"Weak verb '{result.verb}': {result.suggestion}"
    elif result.warning:
        return True, result.warning
    else:
        return True, f"Valid action with verb '{result.verb}'"


def is_weak_verb(verb: str) -> bool:
    """
    Check if a verb is weak.

    Args:
        verb: Verb to check (lowercase)

    Returns:
        True if verb is weak
    """
    return verb.lower() in WEAK_VERBS


def suggest_replacement(verb: str) -> Optional[str]:
    """
    Get suggestion for replacing a weak verb.

    Args:
        verb: Weak verb to replace

    Returns:
        Suggestion string or None
    """
    return VERB_SUGGESTIONS.get(verb.lower())
