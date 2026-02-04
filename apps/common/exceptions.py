class MelonMindException(Exception):
    """MelonMind 基础异常类"""
    def __init__(self, message: str, error_code: str = ""):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AgentFlowException(MelonMindException):
    """Agent 流程相关异常"""
    pass


class KnowledgeBaseException(MelonMindException):
    """知识库相关异常"""
    pass


class ValidationError(MelonMindException):
    """数据验证异常"""
    pass


class ExternalServiceException(MelonMindException):
    """外部服务调用异常"""
    def __init__(self, service_name: str, message: str, error_code: str = ""):
        self.service_name = service_name
        super().__init__(f"{service_name}: {message}", error_code)


class ConfigurationException(MelonMindException):
    """配置相关异常"""
    pass


class AuthenticationException(MelonMindException):
    """认证相关异常"""
    pass


class AuthorizationException(MelonMindException):
    """授权相关异常"""
    pass