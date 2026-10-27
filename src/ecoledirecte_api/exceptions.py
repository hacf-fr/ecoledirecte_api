from typing import Any


class BaseEcoleDirecteException(Exception):
    """Base exception for Ecole Directe errors."""

    def __init__(
        self,
        path: str | None = None,
        params: dict[str, Any] | None = None,
        payload: Any | None = None,
        status: int | str | None = None,
        message: object | None = None,
    ) -> None:
        """
        Constructor

        :param path: the path of the API endpoint
        :param params: the parameters of the API endpoint
        :param payload: the payload of the API endpoint
        :param status: the HTTP status code
        :param message: the message of the exception
        """
        if path is None:
            self.message = str(message) if message is not None else "Ecole Directe error."
        else:
            self.message = (
                f"Error occurred while calling [{path}] with params [{params}] "
                f"and payload [{payload}]"
            )
            if status is not None:
                self.message += f" - status [{status}]"
            if message is not None:
                self.message += f": {message}"

        super().__init__(self.message)


class EcoleDirecteException(BaseEcoleDirecteException):
    """Raised when an undefined error occurs while communicating with the Ecole Directe API."""


class ServiceUnavailableException(BaseEcoleDirecteException):
    """Raised when the service is unavailable."""


class LoginException(BaseEcoleDirecteException):
    """Raised when MFA is required."""


class NotAuthenticatedException(LoginException):
    """Raised when user is not authenticated."""


class MFARequiredException(LoginException):
    """Raised when MFA is required."""


class GTKException(LoginException):
    """Raised when cookies is not good."""


class QCMException(LoginException):
    """Raised when QCM stuff is not good."""
