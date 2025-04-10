class BaseEcoleDirecteException(Exception):
    """Base exception for Ecole Directe errors."""


class EcoleDirecteException(BaseEcoleDirecteException):
    """Raised when an undefined error occurs while communicating with the Ecole Directe API."""


class ServiceUnavailableException(BaseEcoleDirecteException):
    """Raised when the service is unavailable."""


class LoginException(BaseEcoleDirecteException):
    """Raised when MFA is required."""


class MFARequiredException(LoginException):
    """Raised when MFA is required."""


class GTKException(LoginException):
    """Raised when cookies is not good."""


class QCMException(LoginException):
    """Raised when QCM stuff is not good."""
