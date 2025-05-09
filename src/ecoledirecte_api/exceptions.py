from typing import Any


class BaseEcoleDirecteException(Exception):
    """Base exception for Ecole Directe errors."""

    def __init__(
        self,
        path: str,
        params: dict | None = None,
        payload: Any | None = None,
        status: str | None = None,
        message: str | None = None,
    ) -> None:
        """
        Constructor

        :param path: the path of the API endpoint
        :param params: the parameters of the API endpoint
        :param payload: the payload of the API endpoint
        :param message: the message of the exception
        """
        self.message = f"Error occurred while calling [{path}] with params [{params}] and payload [{payload}] - [{status}]{message}"


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
