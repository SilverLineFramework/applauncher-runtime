"""
*TL;DR
Runtime exceptions
"""

class RuntimeException(Exception):
    """Base class for runtime exceptions."""

    def __init__(self, description, data):
        self.desc = description
        self.data = data

class MissingField(RuntimeException):
    """Required field is missing."""

    def __init__(self, data):
        super().__init__("missing field", data)
