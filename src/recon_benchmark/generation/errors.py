"""Explicit errors in experimental generation."""

class PerturbationNoOpError(RuntimeError):
    """Signal that a requested experimental change did not alter the observed record."""
    pass
