"""Tests for custom exceptions."""


from spec.core.exceptions import (
    ExtractionFailed,
    GenieException,
    InvalidConfig,
    LayoutNotRecognized,
    LLMProviderError,
    StorageError,
)


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""

    def test_genie_exception_base(self):
        """Test base GenieException."""
        exc = GenieException("Test error")
        assert str(exc) == "Test error"
        assert isinstance(exc, Exception)

    def test_layout_not_recognized(self):
        """Test LayoutNotRecognized exception."""
        exc = LayoutNotRecognized("Layout not in library")
        assert isinstance(exc, GenieException)

    def test_extraction_failed(self):
        """Test ExtractionFailed exception."""
        exc = ExtractionFailed("Extraction process failed")
        assert isinstance(exc, GenieException)

    def test_llm_provider_error(self):
        """Test LLMProviderError exception."""
        exc = LLMProviderError("API error")
        assert isinstance(exc, GenieException)

    def test_invalid_config(self):
        """Test InvalidConfig exception."""
        exc = InvalidConfig("Bad configuration")
        assert isinstance(exc, GenieException)

    def test_storage_error(self):
        """Test StorageError exception."""
        exc = StorageError("Storage operation failed")
        assert isinstance(exc, GenieException)

    def test_all_exceptions_inherit_from_base(self):
        """Test all custom exceptions inherit from GenieException."""
        exceptions = [
            LayoutNotRecognized,
            ExtractionFailed,
            LLMProviderError,
            InvalidConfig,
            StorageError,
        ]

        for exc_class in exceptions:
            exc = exc_class("test")
            assert isinstance(exc, GenieException)
