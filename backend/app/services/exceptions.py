class ApplicationError(Exception):
    pass


class ClientAlreadyExists(ApplicationError):
    pass


class ClientNotFound(ApplicationError):
    pass


class InternalServerError(Exception):
    pass


class ForbiddenError(ApplicationError):
    def __init__(self, detail: str = "Forbidden"):
        self.detail = detail
        super().__init__(detail)
