"""
Unit tests for Enhanced Confidence Scoring (Phase 2 Day 8).

Tests confidence enhancement with validation quality scores.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from script_to_doc.source_reference import SourceReferenceManager


class TestEnhanceConfidenceWithValidation:
    """Test confidence enhancement with validation quality scores."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SourceReferenceManager()

    def test_high_quality_boosts_confidence(self):
        """Test that high quality score boosts confidence."""
        original = 0.5
        quality = 0.9  # Very high quality

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        # Should be higher than original (70% * 0.5 + 30% * 0.9) * 1.10
        assert enhanced > original
        assert enhanced > 0.6  # Significant boost

    def test_low_quality_reduces_confidence(self):
        """Test that low quality score reduces confidence."""
        original = 0.6
        quality = 0.2  # Low quality

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        # Should be lower than original (70% * 0.6 + 30% * 0.2) * 0.95
        assert enhanced < original

    def test_medium_quality_moderate_effect(self):
        """Test that medium quality has moderate effect."""
        original = 0.5
        quality = 0.5  # Medium quality

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        # Should be close to original (70% * 0.5 + 30% * 0.5) = 0.5
        assert 0.45 <= enhanced <= 0.55

    def test_perfect_scores_maxed_out(self):
        """Test that perfect scores result in high confidence."""
        original = 0.9
        quality = 1.0  # Perfect quality

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        # Should be very high (70% * 0.9 + 30% * 1.0) * 1.10 = 0.96 * 1.10
        assert enhanced >= 0.95
        assert enhanced <= 1.0  # Clamped at 1.0

    def test_low_scores_not_too_penalized(self):
        """Test that low scores don't get overly penalized."""
        original = 0.3
        quality = 0.2  # Low quality

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        # Should still be positive
        assert enhanced > 0.0
        assert enhanced < original

    def test_weighted_combination(self):
        """Test 70-30 weighting of source vs quality."""
        original = 0.8
        quality = 0.2

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        # Calculate expected: 0.7 * 0.8 + 0.3 * 0.2 = 0.56 + 0.06 = 0.62
        # With low quality penalty: 0.62 * 0.95 = 0.589
        expected = 0.62 * 0.95
        assert abs(enhanced - expected) < 0.05  # Allow small floating point error

    def test_high_quality_multiplier(self):
        """Test that quality >= 0.8 gets 1.10x multiplier."""
        original = 0.5
        quality = 0.85  # High quality (>= 0.8)

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        # Calculate: (0.7 * 0.5 + 0.3 * 0.85) * 1.10 = (0.35 + 0.255) * 1.10 = 0.6655
        expected = (0.7 * original + 0.3 * quality) * 1.10
        assert abs(enhanced - expected) < 0.01

    def test_medium_high_quality_multiplier(self):
        """Test that quality >= 0.6 gets 1.05x multiplier."""
        original = 0.5
        quality = 0.7  # Medium-high quality (>= 0.6)

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        # Calculate: (0.7 * 0.5 + 0.3 * 0.7) * 1.05 = (0.35 + 0.21) * 1.05 = 0.588
        expected = (0.7 * original + 0.3 * quality) * 1.05
        assert abs(enhanced - expected) < 0.01

    def test_clamping_to_one(self):
        """Test that enhanced confidence is clamped to 1.0."""
        original = 0.95
        quality = 0.95

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        assert enhanced <= 1.0

    def test_clamping_to_zero(self):
        """Test that enhanced confidence is clamped to 0.0."""
        original = 0.0
        quality = 0.0

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        assert enhanced >= 0.0


class TestConfidenceQualityIndicator:
    """Test quality indicator labels."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SourceReferenceManager()

    def test_high_quality_indicator(self):
        """Test high quality indicator for confidence >= 0.7."""
        assert self.manager.get_confidence_quality_indicator(0.7) == "high"
        assert self.manager.get_confidence_quality_indicator(0.8) == "high"
        assert self.manager.get_confidence_quality_indicator(0.9) == "high"
        assert self.manager.get_confidence_quality_indicator(1.0) == "high"

    def test_medium_quality_indicator(self):
        """Test medium quality indicator for 0.4 <= confidence < 0.7."""
        assert self.manager.get_confidence_quality_indicator(0.4) == "medium"
        assert self.manager.get_confidence_quality_indicator(0.5) == "medium"
        assert self.manager.get_confidence_quality_indicator(0.6) == "medium"
        assert self.manager.get_confidence_quality_indicator(0.69) == "medium"

    def test_low_quality_indicator(self):
        """Test low quality indicator for confidence < 0.4."""
        assert self.manager.get_confidence_quality_indicator(0.0) == "low"
        assert self.manager.get_confidence_quality_indicator(0.1) == "low"
        assert self.manager.get_confidence_quality_indicator(0.2) == "low"
        assert self.manager.get_confidence_quality_indicator(0.3) == "low"
        assert self.manager.get_confidence_quality_indicator(0.39) == "low"

    def test_boundary_values(self):
        """Test boundary values for quality indicators."""
        # Just below high threshold
        assert self.manager.get_confidence_quality_indicator(0.699) == "medium"
        # At high threshold
        assert self.manager.get_confidence_quality_indicator(0.7) == "high"

        # Just below medium threshold
        assert self.manager.get_confidence_quality_indicator(0.399) == "low"
        # At medium threshold
        assert self.manager.get_confidence_quality_indicator(0.4) == "medium"


class TestEnhancedConfidenceScenarios:
    """Test realistic confidence enhancement scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = SourceReferenceManager()

    def test_good_source_good_quality(self):
        """Test good source + good quality = excellent confidence."""
        original = 0.7  # Good source confidence
        quality = 0.8   # Good quality

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        assert enhanced >= 0.8  # Should be excellent
        assert self.manager.get_confidence_quality_indicator(enhanced) == "high"

    def test_poor_source_excellent_quality(self):
        """Test poor source + excellent quality = decent confidence."""
        original = 0.3  # Poor source confidence
        quality = 0.9   # Excellent quality

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        # Quality can boost it significantly
        assert enhanced > original
        assert enhanced >= 0.4  # Should reach medium at least

    def test_excellent_source_poor_quality(self):
        """Test excellent source + poor quality = reduced confidence."""
        original = 0.9  # Excellent source confidence
        quality = 0.2   # Poor quality

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        # Quality penalty should reduce it
        assert enhanced < original
        # But source confidence should prevent it from dropping too much
        assert enhanced >= 0.5

    def test_average_everything(self):
        """Test average source + average quality = average confidence."""
        original = 0.5  # Average source
        quality = 0.5   # Average quality

        enhanced = self.manager.enhance_confidence_with_validation(original, quality)

        assert 0.45 <= enhanced <= 0.55  # Should remain around average
        assert self.manager.get_confidence_quality_indicator(enhanced) == "medium"


def main():
    """Run Enhanced Confidence tests."""
    import pytest

    print("\n" + "=" * 80)
    print("ENHANCED CONFIDENCE UNIT TESTS (Phase 2 Day 8)")
    print("=" * 80)
    print()

    # Run tests
    exit_code = pytest.main([__file__, "-v", "--tb=short"])

    if exit_code == 0:
        print("\n" + "=" * 80)
        print("✅ ALL ENHANCED CONFIDENCE TESTS PASSED")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ SOME TESTS FAILED")
        print("=" * 80)

    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
