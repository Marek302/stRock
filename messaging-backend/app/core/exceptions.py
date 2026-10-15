class NotFoundError(Exception):
    """Resource not found (mapped to HTTP 404)."""
    pass


class ForbiddenError(Exception):
    """User not allowed to access resource (mapped to HTTP 403)."""
    pass


class ConflictError(Exception):
    """Uniqueness violation (mapped to HTTP 409)."""
    pass
