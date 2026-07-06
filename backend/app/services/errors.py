class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "invalid_state_transition"


class ConfigurationError(AppError):
    status_code = 503
    code = "configuration_error"


class SafetyBlockError(AppError):
    status_code = 200
    code = "safety_blocked"
