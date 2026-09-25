class URLFetchError(Exception):
    """A stable, safe failure produced while acquiring user-supplied content."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
