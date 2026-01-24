class ApplicationError(Exception):
    pass


class ClientAlreadyExists(ApplicationError):
    pass


class ClientNotFound(ApplicationError):
    pass
