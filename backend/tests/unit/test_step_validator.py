"""
Unit tests for Step Validator (Phase 2).

Tests step validation rules and quality scoring.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.step_validator import StepValidator, ValidationConfig, ValidationResult, ValidationIssue


class TestValidationConfig:
    """Test ValidationConfig validation and defaults."""

    def test_default_config(self):
        """Test default configuration is valid."""
        config = ValidationConfig()
        assert config.min_actions == 3
        assert config.max_actions == 15
        assert config.min_title_length == 10
        assert config.min_details_length == 20
        assert config.min_confidence_threshold == 0.2
        assert config.enable_auto_fix_suggestions is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = ValidationConfig(
            min_actions=5,
            max_actions=20,
            min_confidence_threshold=0.3
        )
        assert config.min_actions == 5
        assert config.max_actions == 20
        assert config.min_confidence_threshold == 0.3

    def test_invalid_min_actions(self):
        """Test that invalid min_actions raises error."""
        try:
            ValidationConfig(min_actions=0)
            assert False, "Should raise ValueError for min_actions < 1"
        except ValueError as e:
            assert "min_actions" in str(e)

    def test_invalid_max_actions(self):
        """Test that max_actions < min_actions raises error."""
        try:
            ValidationConfig(min_actions=10, max_actions=5)
            assert False, "Should raise ValueError for max_actions < min_actions"
        except ValueError as e:
            assert "max_actions" in str(e)

    def test_invalid_weights(self):
        """Test that weights not summing to 1.0 raise error."""
        try:
            ValidationConfig(
                weight_actions=0.5,
                weight_title=0.3,
                weight_details=0.3,
                weight_confidence=0.2  # Sum = 1.3
            )
            assert False, "Should raise ValueError for weights not summing to 1.0"
        except ValueError as e:
            assert "must sum to 1.0" in str(e)


class TestStepValidator:
    """Test StepValidator initialization."""

    def test_initialization(self):
        """Test validator initialization with default config."""
        validator = StepValidator()
        assert validator.config.min_actions == 3
        assert validator.config.min_confidence_threshold == 0.2

    def test_initialization_with_custom_config(self):
        """Test validator initialization with custom config."""
        config = ValidationConfig(min_actions=5)
        validator = StepValidator(config)
        assert validator.config.min_actions == 5


class TestActionValidation:
    """Test action validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = StepValidator()

    def test_valid_action_count(self):
        """Test step with valid action count passes."""
        step = {
            'title': 'Configure Azure Settings',
            'details': 'This step configures the Azure settings for the resource group.',
            'actions': [
                'Navigate to Azure portal',
                'Click on Settings',
                'Configure the settings'
            ],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.is_valid is True
        assert result.action_count == 3
        assert len(result.errors) == 0

    def test_insufficient_actions(self):
        """Test step with too few actions fails."""
        step = {
            'title': 'Configure Settings',
            'details': 'Configure the settings',
            'actions': [
                'Click on Settings'
            ],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.is_valid is False
        assert result.action_count == 1
        assert len(result.errors) > 0
        assert any(issue.issue_type == "insufficient_actions" for issue in result.errors)

    def test_too_many_actions_warning(self):
        """Test step with too many actions gets warning."""
        step = {
            'title': 'Complex Configuration Process',
            'details': 'This is a very detailed configuration process.',
            'actions': [f'Action {i}' for i in range(20)],  # 20 actions
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.action_count == 20
        assert any(issue.issue_type == "too_many_actions" for issue in result.warnings)

    def test_empty_actions(self):
        """Test step with empty actions fails."""
        step = {
            'title': 'Configure Settings',
            'details': 'Configure the settings',
            'actions': [
                'Action 1',
                '',  # Empty action
                'Action 3',
                '   '  # Whitespace only
            ],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.is_valid is False
        assert any(issue.issue_type == "empty_actions" for issue in result.errors)


class TestTitleValidation:
    """Test title validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = StepValidator()

    def test_valid_title(self):
        """Test step with valid title passes."""
        step = {
            'title': 'Configure Azure Resource Group Settings',
            'details': 'This step configures the Azure resource group settings.',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.is_valid is True
        assert result.title_length > 0

    def test_missing_title(self):
        """Test step with missing title fails."""
        step = {
            'title': '',
            'details': 'This step does something',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.is_valid is False
        assert any(issue.issue_type == "missing_title" for issue in result.errors)

    def test_short_title_warning(self):
        """Test step with short title gets warning."""
        step = {
            'title': 'Config',  # Only 6 chars
            'details': 'This step configures settings',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.title_length < 10
        assert any(issue.issue_type == "short_title" for issue in result.warnings)

    def test_long_title_warning(self):
        """Test step with long title gets warning."""
        step = {
            'title': 'A' * 150,  # 150 chars (too long)
            'details': 'This step does something',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.title_length > 100
        assert any(issue.issue_type == "long_title" for issue in result.warnings)

    def test_generic_title_info(self):
        """Test step with generic title gets info."""
        step = {
            'title': 'Step 1',
            'details': 'This step does something important',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert any(issue.issue_type == "generic_title" for issue in result.info)


class TestDetailsValidation:
    """Test details validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = StepValidator()

    def test_valid_details(self):
        """Test step with valid details passes."""
        step = {
            'title': 'Configure Settings',
            'details': 'This step configures the Azure resource group settings for the deployment.',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.is_valid is True
        assert result.details_length >= 20

    def test_missing_details(self):
        """Test step with missing details fails."""
        step = {
            'title': 'Configure Settings',
            'details': '',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.is_valid is False
        assert any(issue.issue_type == "missing_details" for issue in result.errors)

    def test_insufficient_details_warning(self):
        """Test step with insufficient details gets warning."""
        step = {
            'title': 'Configure Settings',
            'details': 'Short details',  # Only 13 chars
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.details_length < 20
        assert any(issue.issue_type == "insufficient_details" for issue in result.warnings)


class TestConfidenceValidation:
    """Test confidence validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = StepValidator()

    def test_high_confidence(self):
        """Test step with high confidence passes without warnings."""
        step = {
            'title': 'Configure Azure Settings',
            'details': 'This step configures the settings',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.confidence_score == 0.8
        assert not any(issue.field == "confidence_score" for issue in result.errors)
        assert not any(issue.field == "confidence_score" for issue in result.warnings)

    def test_very_low_confidence_error(self):
        """Test step with very low confidence gets error."""
        step = {
            'title': 'Configure Settings',
            'details': 'This step configures the settings',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.1  # Very low
        }

        result = self.validator.validate_step(step)
        assert result.is_valid is False
        assert any(issue.issue_type == "very_low_confidence" for issue in result.errors)

    def test_low_confidence_warning(self):
        """Test step with low confidence gets warning."""
        step = {
            'title': 'Configure Settings',
            'details': 'This step configures the settings',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.3  # Low but not very low
        }

        result = self.validator.validate_step(step)
        assert any(issue.issue_type == "low_confidence" for issue in result.warnings)


class TestDuplicateDetection:
    """Test duplicate action detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = StepValidator()

    def test_no_duplicates(self):
        """Test step without duplicates passes."""
        step = {
            'title': 'Configure Settings',
            'details': 'This step configures the settings',
            'actions': [
                'Navigate to portal',
                'Click on Settings',
                'Configure options'
            ],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.has_duplicates is False

    def test_duplicate_actions_warning(self):
        """Test step with duplicate actions gets warning."""
        step = {
            'title': 'Configure Settings',
            'details': 'This step configures the settings',
            'actions': [
                'Navigate to portal',
                'Click on Settings',
                'Navigate to portal'  # Duplicate
            ],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.has_duplicates is True
        assert any(issue.issue_type == "duplicate_actions" for issue in result.warnings)

    def test_duplicate_detection_case_insensitive(self):
        """Test duplicate detection is case-insensitive."""
        step = {
            'title': 'Configure Settings',
            'details': 'This step configures the settings',
            'actions': [
                'Navigate to Portal',
                'Click on Settings',
                'navigate to portal'  # Same as first (different case)
            ],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.has_duplicates is True


class TestQualityScore:
    """Test quality score computation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = StepValidator()

    def test_high_quality_step(self):
        """Test high quality step gets high score."""
        step = {
            'title': 'Configure Azure Resource Group Settings and Deployment Options',
            'details': 'This step guides you through configuring the Azure resource group settings including deployment options and networking.',
            'actions': [
                'Navigate to Azure portal',
                'Click on Resource Groups',
                'Select your resource group',
                'Click on Settings',
                'Configure deployment options'
            ],
            'confidence_score': 0.9
        }

        result = self.validator.validate_step(step)
        assert result.quality_score > 0.7  # High quality

    def test_low_quality_step(self):
        """Test low quality step gets low score."""
        step = {
            'title': 'Config',  # Short
            'details': 'Short',  # Too short
            'actions': ['Action'],  # Too few
            'confidence_score': 0.1  # Very low
        }

        result = self.validator.validate_step(step)
        assert result.quality_score < 0.35  # Low quality

    def test_medium_quality_step(self):
        """Test medium quality step gets medium score."""
        step = {
            'title': 'Configure Settings',
            'details': 'This step configures the settings',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.5
        }

        result = self.validator.validate_step(step)
        assert 0.3 <= result.quality_score <= 0.7  # Medium quality


class TestValidateMultipleSteps:
    """Test validating multiple steps."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = StepValidator()

    def test_validate_multiple_steps(self):
        """Test validating multiple steps."""
        steps = [
            {
                'title': 'Step 1: Configure Settings',
                'details': 'This step configures the settings',
                'actions': ['Action 1', 'Action 2', 'Action 3'],
                'confidence_score': 0.8
            },
            {
                'title': 'Step 2: Deploy Application',
                'details': 'This step deploys the application',
                'actions': ['Action 1', 'Action 2', 'Action 3'],
                'confidence_score': 0.7
            },
            {
                'title': 'Bad',  # Short title
                'details': '',  # Missing details
                'actions': ['Only one action'],  # Too few
                'confidence_score': 0.1  # Very low
            }
        ]

        results = self.validator.validate_steps(steps)

        assert len(results) == 3
        assert results[0].is_valid is True
        assert results[1].is_valid is True
        assert results[2].is_valid is False  # Third step has errors

    def test_validate_empty_list(self):
        """Test validating empty step list."""
        results = self.validator.validate_steps([])
        assert len(results) == 0


class TestAutoFixSuggestions:
    """Test auto-fix suggestion generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = StepValidator()

    def test_auto_fix_insufficient_actions(self):
        """Test auto-fix suggests adding more actions."""
        step = {
            'title': 'Configure Settings',
            'details': 'This step configures the settings',
            'actions': ['Only one action'],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.auto_fix_available is True
        assert any('Add' in suggestion and 'action' in suggestion for suggestion in result.suggested_fixes)

    def test_auto_fix_missing_title(self):
        """Test auto-fix suggests generating title."""
        step = {
            'title': '',
            'details': 'This step does something',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.auto_fix_available is True
        assert any('title' in suggestion for suggestion in result.suggested_fixes)

    def test_auto_fix_duplicates(self):
        """Test auto-fix for step with duplicates and errors."""
        step = {
            'title': '',  # Missing title (error)
            'details': 'This step configures the settings',
            'actions': [
                'Action 1',
                'Action 2',
                'Action 1'  # Duplicate (warning)
            ],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.is_valid is False  # Has error
        assert result.auto_fix_available is True
        # Should have suggestions for both title and duplicates
        assert any('title' in suggestion.lower() for suggestion in result.suggested_fixes)

    def test_no_auto_fix_for_valid_step(self):
        """Test no auto-fix suggestions for valid step."""
        step = {
            'title': 'Configure Azure Settings',
            'details': 'This step configures the Azure settings',
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.8
        }

        result = self.validator.validate_step(step)
        assert result.auto_fix_available is False
        assert len(result.suggested_fixes) == 0


class TestValidationReport:
    """Test validation report generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = StepValidator()

    def test_validation_report(self):
        """Test validation report generation."""
        steps = [
            {
                'title': 'Valid Step 1',
                'details': 'This step is valid and has good quality',
                'actions': ['Action 1', 'Action 2', 'Action 3'],
                'confidence_score': 0.8
            },
            {
                'title': 'Valid Step 2',
                'details': 'This step is also valid',
                'actions': ['Action 1', 'Action 2', 'Action 3'],
                'confidence_score': 0.7
            },
            {
                'title': 'Bad',
                'details': '',
                'actions': ['One'],
                'confidence_score': 0.1
            }
        ]

        results = self.validator.validate_steps(steps)
        report = self.validator.get_validation_report(results)

        assert report['total_steps'] == 3
        assert report['valid_steps'] == 2
        assert report['invalid_steps'] == 1
        assert report['validation_rate'] == 2/3
        assert 'statistics' in report
        assert 'issues_by_type' in report
        assert 'issues_by_severity' in report

    def test_validation_report_empty(self):
        """Test validation report with empty results."""
        report = self.validator.get_validation_report([])

        assert report['total_steps'] == 0
        assert report['valid_steps'] == 0
        assert report['invalid_steps'] == 0


class TestValidationConfigOptions:
    """Test validation config options."""

    def test_disable_auto_fix(self):
        """Test disabling auto-fix suggestions."""
        config = ValidationConfig(enable_auto_fix_suggestions=False)
        validator = StepValidator(config)

        step = {
            'title': '',  # Missing title
            'details': 'This step does something',
            'actions': ['Only one'],  # Too few actions
            'confidence_score': 0.8
        }

        result = validator.validate_step(step)
        assert result.is_valid is False
        assert result.auto_fix_available is False
        assert len(result.suggested_fixes) == 0

    def test_custom_thresholds(self):
        """Test custom validation thresholds."""
        config = ValidationConfig(
            min_actions=5,  # Higher minimum
            min_confidence_threshold=0.5  # Higher minimum
        )
        validator = StepValidator(config)

        step = {
            'title': 'Configure Settings',
            'details': 'This step configures the settings',
            'actions': ['A1', 'A2', 'A3'],  # Only 3 actions (< 5)
            'confidence_score': 0.4  # Low confidence (< 0.5)
        }

        result = validator.validate_step(step)
        assert result.is_valid is False
        assert any(issue.issue_type == "insufficient_actions" for issue in result.errors)
        assert any(issue.issue_type == "very_low_confidence" for issue in result.errors)

    def test_optional_details(self):
        """Test making details optional."""
        config = ValidationConfig(require_details=False)
        validator = StepValidator(config)

        step = {
            'title': 'Configure Settings',
            'details': '',  # Empty details
            'actions': ['Action 1', 'Action 2', 'Action 3'],
            'confidence_score': 0.8
        }

        result = validator.validate_step(step)
        # Should not have missing_details error when details are optional
        assert not any(issue.issue_type == "missing_details" for issue in result.errors)


def main():
    """Run Step Validator tests."""
    import pytest

    print("\n" + "=" * 80)
    print("STEP VALIDATOR UNIT TESTS (Phase 2)")
    print("=" * 80)
    print()

    # Run tests
    exit_code = pytest.main([__file__, "-v", "--tb=short"])

    if exit_code == 0:
        print("\n" + "=" * 80)
        print("✅ ALL STEP VALIDATOR TESTS PASSED")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ SOME TESTS FAILED")
        print("=" * 80)

    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
