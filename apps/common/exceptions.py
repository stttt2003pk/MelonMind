class MelonMindException(Exception):
    """MelonMind base exception class"""
    def __init__(self, message: str, error_code: str = ""):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AgentFlowException(MelonMindException):
    """Agent flow related exception"""
    pass


class KnowledgeBaseException(MelonMindException):
    """Knowledge base related exception"""
    pass


class ValidationError(MelonMindException):
    """Data validation exception"""
    pass


class ExternalServiceException(MelonMindException):
    """External service call exception"""
    def __init__(self, service_name: str, message: str, error_code: str = ""):
        self.service_name = service_name
        super().__init__(f"{service_name}: {message}", error_code)


class ConfigurationException(MelonMindException):
    """Configuration related exception"""
    pass


class AuthenticationException(MelonMindException):
    """Authentication related exception"""
    pass


class AuthorizationException(MelonMindException):
    """Authorization related exception"""
    pass