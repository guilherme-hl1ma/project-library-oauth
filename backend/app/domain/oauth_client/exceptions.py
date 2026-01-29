class DomainError(Exception):
    pass


class InvalidRedirectURI(DomainError):
    pass


class GrantTypeNotAllowed(DomainError):
    pass
