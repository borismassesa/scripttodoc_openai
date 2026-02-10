"""
Step Validator: Validates generated steps for quality and completeness.

Phase 2 Component - Validates steps before returning to user.
Checks action count, title quality, details quality, and provides auto-fix suggestions.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """
    Represents a validation issue found in a step.
    """
    issue_type: str                    # "missing_actions", "poor_title", "insufficient_details", etc.
    severity: str                      # "error", "warning", "info"
    message: str                       # Human-readable description
    field: Optional[str] = None        # Which field has the issue ("title", "details", "actions")
    suggestion: Optional[str] = None   # Auto-fix suggestion


@dataclass
class ValidationResult:
    """
    Result of validating a step.

    Contains validation status, issues found, and quality scores.
    """
    step_index: int
    is_valid: bool                     # True if step passes all checks
    quality_score: float               # 0.0-1.0 overall quality score

    # Issues found
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)

    # Quality metrics
    action_count: int = 0
    title_length: int = 0
    details_length: int = 0
    confidence_score: float = 0.0
    has_duplicates: bool = False

    # Suggestions
    auto_fix_available: bool = False
    suggested_fixes: List[str] = field(default_factory=list)


@dataclass
class ValidationConfig:
    """Configuration for step validation."""

    # Action validation
    min_actions: int = 3                # Minimum actions per step
    max_actions: int = 15               # Maximum actions per step (warn if exceeded)
    warn_duplicate_actions: bool = True # Warn about duplicate actions

    # Title validation
    min_title_length: int = 10          # Minimum title length (characters)
    max_title_length: int = 100         # Maximum title length (characters)
    require_descriptive_title: bool = True  # Title should be descriptive

    # Details validation
    min_details_length: int = 20        # Minimum details length (characters)
    require_details: bool = True        # Details field is required

    # Confidence validation
    min_confidence_threshold: float = 0.2  # Warn if confidence < 0.2 (low confidence)
    low_confidence_threshold: float = 0.4  # Info if confidence < 0.4

    # Quality scoring weights
    weight_actions: float = 0.4         # Weight for action count score
    weight_title: float = 0.2           # Weight for title quality score
    weight_details: float = 0.2         # Weight for details quality score
    weight_confidence: float = 0.2      # Weight for confidence score

    # Auto-fix
    enable_auto_fix_suggestions: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if self.min_actions < 1:
            raise ValueError("min_actions must be >= 1")
        if self.max_actions < self.min_actions:
            raise ValueError("max_actions must be >= min_actions")
        if not 0.0 <= self.min_confidence_threshold <= 1.0:
            raise ValueError("min_confidence_threshold must be between 0.0 and 1.0")

        # Validate weights
        total_weight = (
            self.weight_actions +
            self.weight_title +
            self.weight_details +
            self.weight_confidence
        )
        if not 0.99 <= total_weight <= 1.01:  # Allow small floating point error
            raise ValueError(
                f"Validation weights must sum to 1.0, got {total_weight}"
            )


class StepValidator:
    """
    Validates generated steps for quality and completeness.

    Performs multi-dimensional validation:
    - Action count and quality
    - Title descriptiveness
    - Details completeness
    - Confidence score
    - Duplicate detection
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Initialize step validator.

        Args:
            config: Validation configuration (uses defaults if None)
        """
        self.config = config or ValidationConfig()
        logger.info(
            f"Step Validator initialized: "
            f"min_actions={self.config.min_actions}, "
            f"min_confidence={self.config.min_confidence_threshold}"
        )

    def validate_step(self, step: Dict[str, Any], step_index: int = 0) -> ValidationResult:
        """
        Validate a single step.

        Args:
            step: Step dictionary with title, details, actions, confidence
            step_index: Index of step in document (for reporting)

        Returns:
            ValidationResult with validation status and issues
        """
        result = ValidationResult(
            step_index=step_index,
            is_valid=True,  # Assume valid until proven otherwise
            quality_score=0.0
        )

        # Extract step fields
        title = step.get('title', '')
        details = step.get('details', '')
        actions = step.get('actions', [])
        confidence = step.get('confidence_score', 0.0)

        # Store metrics
        result.action_count = len(actions)
        result.title_length = len(title)
        result.details_length = len(details)
        result.confidence_score = confidence

        # Run validation checks
        self._validate_actions(actions, result)
        self._validate_title(title, result)
        self._validate_details(details, result)
        self._validate_confidence(confidence, result)
        self._check_duplicates(actions, result)

        # Compute quality score
        result.quality_score = self._compute_quality_score(result)

        # Determine if step is valid (no errors)
        result.is_valid = len(result.errors) == 0

        # Generate auto-fix suggestions if enabled
        if self.config.enable_auto_fix_suggestions and not result.is_valid:
            self._generate_auto_fix_suggestions(result)

        logger.debug(
            f"Step {step_index} validation: "
            f"valid={result.is_valid}, "
            f"quality={result.quality_score:.2f}, "
            f"errors={len(result.errors)}, "
            f"warnings={len(result.warnings)}"
        )

        return result

    def validate_steps(self, steps: List[Dict[str, Any]]) -> List[ValidationResult]:
        """
        Validate multiple steps.

        Args:
            steps: List of step dictionaries

        Returns:
            List of ValidationResult (one per step)
        """
        results = []
        for i, step in enumerate(steps):
            result = self.validate_step(step, step_index=i)
            results.append(result)

        logger.info(
            f"Validated {len(steps)} steps: "
            f"{sum(1 for r in results if r.is_valid)} valid, "
            f"{sum(1 for r in results if not r.is_valid)} invalid"
        )

        return results

    def _validate_actions(self, actions: List[str], result: ValidationResult) -> None:
        """Validate action count and quality."""
        action_count = len(actions)

        # Check minimum actions
        if action_count < self.config.min_actions:
            result.errors.append(ValidationIssue(
                issue_type="insufficient_actions",
                severity="error",
                message=f"Step has {action_count} actions, minimum is {self.config.min_actions}",
                field="actions",
                suggestion=f"Add at least {self.config.min_actions - action_count} more action(s)"
            ))

        # Check maximum actions (warning only)
        if action_count > self.config.max_actions:
            result.warnings.append(ValidationIssue(
                issue_type="too_many_actions",
                severity="warning",
                message=f"Step has {action_count} actions, which may be too many (max recommended: {self.config.max_actions})",
                field="actions",
                suggestion="Consider splitting this step into multiple steps"
            ))

        # Check for empty actions
        empty_actions = [i for i, action in enumerate(actions) if not action or not action.strip()]
        if empty_actions:
            result.errors.append(ValidationIssue(
                issue_type="empty_actions",
                severity="error",
                message=f"Step has {len(empty_actions)} empty action(s) at indices: {empty_actions}",
                field="actions",
                suggestion="Remove empty actions or add descriptive text"
            ))

    def _validate_title(self, title: str, result: ValidationResult) -> None:
        """Validate title quality."""
        title_length = len(title)

        # Check if title exists
        if not title or not title.strip():
            result.errors.append(ValidationIssue(
                issue_type="missing_title",
                severity="error",
                message="Step has no title",
                field="title",
                suggestion="Add a descriptive title for this step"
            ))
            return

        # Check minimum length
        if title_length < self.config.min_title_length:
            result.warnings.append(ValidationIssue(
                issue_type="short_title",
                severity="warning",
                message=f"Title is too short ({title_length} chars, minimum {self.config.min_title_length})",
                field="title",
                suggestion="Use a more descriptive title"
            ))

        # Check maximum length
        if title_length > self.config.max_title_length:
            result.warnings.append(ValidationIssue(
                issue_type="long_title",
                severity="warning",
                message=f"Title is too long ({title_length} chars, maximum {self.config.max_title_length})",
                field="title",
                suggestion="Shorten the title or move details to the details field"
            ))

        # Check if title is descriptive (contains action words)
        if self.config.require_descriptive_title:
            if self._is_generic_title(title):
                result.info.append(ValidationIssue(
                    issue_type="generic_title",
                    severity="info",
                    message="Title may not be descriptive enough",
                    field="title",
                    suggestion="Use specific action words (e.g., 'Configure', 'Create', 'Navigate')"
                ))

    def _validate_details(self, details: str, result: ValidationResult) -> None:
        """Validate details quality."""
        details_length = len(details)

        # Check if details exist
        if self.config.require_details:
            if not details or not details.strip():
                result.errors.append(ValidationIssue(
                    issue_type="missing_details",
                    severity="error",
                    message="Step has no details",
                    field="details",
                    suggestion="Add context or additional information about this step"
                ))
                return

        # Check minimum length
        if details_length < self.config.min_details_length:
            result.warnings.append(ValidationIssue(
                issue_type="insufficient_details",
                severity="warning",
                message=f"Details are too short ({details_length} chars, minimum {self.config.min_details_length})",
                field="details",
                suggestion="Add more context or explanation about this step"
            ))

    def _validate_confidence(self, confidence: float, result: ValidationResult) -> None:
        """Validate confidence score."""
        # Check very low confidence (error)
        if confidence < self.config.min_confidence_threshold:
            result.errors.append(ValidationIssue(
                issue_type="very_low_confidence",
                severity="error",
                message=f"Step has very low confidence ({confidence:.2f} < {self.config.min_confidence_threshold:.2f})",
                field="confidence_score",
                suggestion="Review step quality - may need more source information"
            ))
        # Check low confidence (warning)
        elif confidence < self.config.low_confidence_threshold:
            result.warnings.append(ValidationIssue(
                issue_type="low_confidence",
                severity="warning",
                message=f"Step has low confidence ({confidence:.2f} < {self.config.low_confidence_threshold:.2f})",
                field="confidence_score",
                suggestion="Consider adding more context from source material"
            ))

    def _check_duplicates(self, actions: List[str], result: ValidationResult) -> None:
        """Check for duplicate actions."""
        if not self.config.warn_duplicate_actions:
            return

        # Normalize actions for comparison (lowercase, strip whitespace)
        normalized_actions = [action.lower().strip() for action in actions]

        # Find duplicates
        seen = set()
        duplicates = []
        for i, action in enumerate(normalized_actions):
            if action in seen:
                duplicates.append(i)
            else:
                seen.add(action)

        if duplicates:
            result.has_duplicates = True
            result.warnings.append(ValidationIssue(
                issue_type="duplicate_actions",
                severity="warning",
                message=f"Step has {len(duplicates)} duplicate action(s) at indices: {duplicates}",
                field="actions",
                suggestion="Remove or rephrase duplicate actions"
            ))

    def _is_generic_title(self, title: str) -> bool:
        """Check if title is too generic."""
        generic_patterns = [
            r'^step \d+$',           # "Step 1", "Step 2"
            r'^untitled',            # "Untitled"
            r'^new step',            # "New Step"
            r'^todo',                # "TODO"
            r'^instructions?$',      # "Instruction(s)"
        ]

        title_lower = title.lower().strip()
        for pattern in generic_patterns:
            if re.match(pattern, title_lower):
                return True

        return False

    def _compute_quality_score(self, result: ValidationResult) -> float:
        """
        Compute overall quality score (0.0-1.0).

        Based on:
        - Action count (meets minimum)
        - Title quality (length and descriptiveness)
        - Details quality (length and completeness)
        - Confidence score
        """
        # Action score (0.0-1.0)
        if result.action_count >= self.config.min_actions:
            action_score = min(1.0, result.action_count / (self.config.min_actions * 2))
        else:
            action_score = result.action_count / self.config.min_actions

        # Title score (0.0-1.0)
        if result.title_length >= self.config.min_title_length:
            title_score = min(1.0, result.title_length / self.config.max_title_length)
        else:
            title_score = result.title_length / self.config.min_title_length

        # Details score (0.0-1.0)
        if result.details_length >= self.config.min_details_length:
            details_score = min(1.0, result.details_length / (self.config.min_details_length * 3))
        else:
            details_score = result.details_length / self.config.min_details_length if self.config.require_details else 1.0

        # Confidence score (0.0-1.0) - already normalized
        confidence_score = result.confidence_score

        # Weighted combination
        quality_score = (
            action_score * self.config.weight_actions +
            title_score * self.config.weight_title +
            details_score * self.config.weight_details +
            confidence_score * self.config.weight_confidence
        )

        return min(1.0, max(0.0, quality_score))

    def _generate_auto_fix_suggestions(self, result: ValidationResult) -> None:
        """Generate auto-fix suggestions for validation issues."""
        suggestions = []

        # Insufficient actions
        if any(issue.issue_type == "insufficient_actions" for issue in result.errors):
            needed = self.config.min_actions - result.action_count
            suggestions.append(f"Add {needed} more action(s) to meet minimum requirement")

        # Missing title
        if any(issue.issue_type == "missing_title" for issue in result.errors):
            suggestions.append("Generate title from step actions or context")

        # Missing details
        if any(issue.issue_type == "missing_details" for issue in result.errors):
            suggestions.append("Generate details from source transcript or knowledge")

        # Duplicate actions
        if result.has_duplicates:
            suggestions.append("Remove duplicate actions automatically")

        if suggestions:
            result.auto_fix_available = True
            result.suggested_fixes = suggestions

    def get_validation_report(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Get detailed validation report for analysis.

        Args:
            results: Validation results from validate_steps()

        Returns:
            Report dictionary with statistics and issues
        """
        if not results:
            return {
                "total_steps": 0,
                "valid_steps": 0,
                "invalid_steps": 0,
                "statistics": {},
                "issues_by_type": {}
            }

        # Count valid/invalid
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = len(results) - valid_count

        # Aggregate quality scores
        quality_scores = [r.quality_score for r in results]
        avg_quality = sum(quality_scores) / len(quality_scores)

        # Count issues by type
        issues_by_type = {}
        for result in results:
            for issue in result.errors + result.warnings + result.info:
                issue_type = issue.issue_type
                if issue_type not in issues_by_type:
                    issues_by_type[issue_type] = 0
                issues_by_type[issue_type] += 1

        # Compute statistics
        action_counts = [r.action_count for r in results]
        confidence_scores = [r.confidence_score for r in results]

        return {
            "total_steps": len(results),
            "valid_steps": valid_count,
            "invalid_steps": invalid_count,
            "validation_rate": valid_count / len(results) if results else 0.0,
            "statistics": {
                "avg_quality_score": avg_quality,
                "min_quality_score": min(quality_scores),
                "max_quality_score": max(quality_scores),
                "avg_action_count": sum(action_counts) / len(action_counts),
                "avg_confidence": sum(confidence_scores) / len(confidence_scores),
                "high_quality_steps": sum(1 for q in quality_scores if q >= 0.8),
                "medium_quality_steps": sum(1 for q in quality_scores if 0.5 <= q < 0.8),
                "low_quality_steps": sum(1 for q in quality_scores if q < 0.5)
            },
            "issues_by_type": issues_by_type,
            "issues_by_severity": {
                "errors": sum(len(r.errors) for r in results),
                "warnings": sum(len(r.warnings) for r in results),
                "info": sum(len(r.info) for r in results)
            }
        }
