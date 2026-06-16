"""Tests for layout fingerprinting."""


from spec.extraction.layout.fingerprint import LayoutFingerprint


class TestLayoutFingerprint:
    """Tests for LayoutFingerprint class."""

    def test_fingerprint_deterministic(self):
        """Test that same content produces same fingerprint."""
        fp_gen = LayoutFingerprint()

        content = """
        Patient: John Doe
        Age: 35
        Date: 2026-03-05
        """

        fp1 = fp_gen.generate(content)
        fp2 = fp_gen.generate(content)

        assert fp1 == fp2
        assert len(fp1) == 16  # SHA256 truncated to 16 chars

    def test_fingerprint_different_data_same_structure(self):
        """Test same layout with different data produces same fingerprint."""
        fp_gen = LayoutFingerprint()

        content1 = """
        Patient: John Doe
        Age: 35
        Date: 2026-03-05
        """

        content2 = """
        Patient: Jane Smith
        Age: 42
        Date: 2026-03-06
        """

        fp1 = fp_gen.generate(content1)
        fp2 = fp_gen.generate(content2)

        # Same structure should produce same fingerprint
        assert fp1 == fp2

    def test_fingerprint_different_layout(self):
        """Test different layouts produce different fingerprints."""
        fp_gen = LayoutFingerprint()

        content1 = """
        Patient: John Doe
        Age: 35
        """

        content2 = """
        Name: Jane Smith
        Years Old: 42
        """

        fp1 = fp_gen.generate(content1)
        fp2 = fp_gen.generate(content2)

        # Different layouts should produce different fingerprints
        assert fp1 != fp2

    def test_fingerprint_similarity_identical(self):
        """Test similarity score for identical fingerprints."""
        fp_gen = LayoutFingerprint()

        fp1 = "a1b2c3d4e5f6g7h8"
        fp2 = "a1b2c3d4e5f6g7h8"

        similarity = fp_gen.similarity(fp1, fp2)
        assert similarity == 1.0

    def test_fingerprint_similarity_different(self):
        """Test similarity score for different fingerprints."""
        fp_gen = LayoutFingerprint()

        fp1 = "a1b2c3d4e5f6g7h8"
        fp2 = "xxxxxxxxxxxxxxxx"

        similarity = fp_gen.similarity(fp1, fp2)
        assert 0.0 <= similarity < 1.0

    def test_fingerprint_similarity_partial(self):
        """Test similarity score for partially matching fingerprints."""
        fp_gen = LayoutFingerprint()

        # Half matching
        fp1 = "aaaabbbbccccdddd"
        fp2 = "aaaabbbbxxxxxxxx"

        similarity = fp_gen.similarity(fp1, fp2)
        assert 0.4 < similarity <= 0.6  # About 50% match

    def test_fingerprint_empty_content(self):
        """Test fingerprinting empty content."""
        fp_gen = LayoutFingerprint()
        fp = fp_gen.generate("")

        assert isinstance(fp, str)
        assert len(fp) == 16

    def test_fingerprint_whitespace_normalized(self):
        """Test that whitespace is normalized."""
        fp_gen = LayoutFingerprint()

        content1 = """
        Patient: John
        Age: 35
        """

        content2 = "Patient: John\nAge: 35"

        fp1 = fp_gen.generate(content1)
        fp2 = fp_gen.generate(content2)

        # Should normalize whitespace and produce same result
        assert fp1 == fp2
