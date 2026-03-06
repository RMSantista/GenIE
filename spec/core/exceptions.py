"""Custom exception hierarchy for GENIE framework."""


class GenieException(Exception):
    """Base exception for all GENIE-related errors.

    This is the root of the custom exception hierarchy.
    """

    pass


class LayoutNotRecognized(GenieException):
    """Raised when a document layout is not recognized in the search library.

    This typically triggers a fallback to LLM extraction.
    """

    pass


class ExtractionFailed(GenieException):
    """Raised when extraction process fails.

    This can occur at any stage of the extraction pipeline.
    """

    pass


class LLMProviderError(GenieException):
    """Raised when an LLM provider encounters an error.

    This includes API errors, timeouts, invalid responses, etc.
    """

    pass


class InvalidConfig(GenieException):
    """Raised when a configuration is invalid or missing required fields."""

    pass


class StorageError(GenieException):
    """Raised when search library storage operations fail.

    This includes file I/O errors, data corruption, etc.
    """

    pass
