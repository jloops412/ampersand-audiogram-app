class EngineError(RuntimeError):
    """Base class for expected, user-actionable engine failures."""


class DependencyUnavailable(EngineError):
    """A required controlled native tool is unavailable."""


class InvalidMedia(EngineError):
    """The supplied local source is not supported audio media."""


class OutputValidationError(EngineError):
    """A rendered artifact failed a release-safety validation."""
