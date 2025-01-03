"""Custom exceptions for CodeFactory."""

class CodeFactoryError(Exception):
    """Base exception for all CodeFactory errors."""
    pass

class CodeGenerationError(CodeFactoryError):
    """Raised when code generation fails."""
    pass

class GitOperationError(CodeFactoryError):
    """Raised when a Git operation fails."""
    pass

class ValidationError(CodeFactoryError):
    """Raised when input validation fails."""
    pass

class DatabaseError(CodeFactoryError):
    """Raised when a database operation fails."""
    pass
