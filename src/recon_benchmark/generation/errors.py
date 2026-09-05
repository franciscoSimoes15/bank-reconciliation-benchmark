"""Erros explícitos da geração experimental."""

class PerturbationNoOpError(RuntimeError):
    """Signal that a requested experimental change did not alter the observed record."""
    pass
