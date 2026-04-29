"""Custom errors for agentrail."""


class AgentrailError(Exception):
    """Base error for application failures."""


class NotGitRepositoryError(AgentrailError):
    """Raised when the current directory is not inside a Git repository."""


class GitCommandError(AgentrailError):
    """Raised when a Git subprocess call fails."""


class ConfigError(AgentrailError):
    """Raised for invalid user configuration."""


class UnsupportedTargetError(AgentrailError):
    """Raised for unsupported continuation targets."""
