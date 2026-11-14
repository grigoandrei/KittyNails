class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class ValidationError(Exception):
    pass


class StorageError(Exception):
    """A required file could not be stored. Maps to 502."""
