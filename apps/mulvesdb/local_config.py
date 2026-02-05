"""
本地Milvus测试环境配置工具
用于配置和管理本地部署的Milvus数据库连接
"""

import os
from typing import Dict, Any
from django.conf import settings


class MilvusLocalConfig:
    """本地Milvus环境配置管理器"""
    
    # 默认本地Milvus配置
    DEFAULT_CONFIG = {
        'host': 'localhost',
        'port': 19530,  # Milvus默认端口
        'database': 'default',  # Milvus默认数据库
        'username': '',  # Milvus通常不需要用户名
        'password': '',  # Milvus通常不需要密码
        'ssl_enabled': False,
        'connection_timeout': 30,
        'name': 'Local Milvus Test'
    }
    
    @classmethod
    def get_local_config(cls) -> Dict[str, Any]:
        """获取本地Milvus配置"""
        config = cls.DEFAULT_CONFIG.copy()
        
        # 允许通过环境变量覆盖默认配置
        config.update({
            'host': os.getenv('MILVUS_HOST', config['host']),
            'port': int(os.getenv('MILVUS_PORT', config['port'])),
            'database': os.getenv('MILVUS_DATABASE', config['database']),
            'username': os.getenv('MILVUS_USERNAME', config['username']),
            'password': os.getenv('MILVUS_PASSWORD', config['password']),
            'ssl_enabled': os.getenv('MILVUS_SSL_ENABLED', str(config['ssl_enabled'])).lower() == 'true',
            'connection_timeout': int(os.getenv('MILVUS_TIMEOUT', config['connection_timeout'])),
            'name': os.getenv('MILVUS_CONNECTION_NAME', config['name'])
        })
        
        return config
    
    @classmethod
    def create_test_connection_config(cls) -> Dict[str, Any]:
        """创建用于测试的连接配置数据"""
        local_config = cls.get_local_config()
        return {
            'name': local_config['name'],
            'host': local_config['host'],
            'port': local_config['port'],
            'database': local_config['database'],
            'username': local_config['username'],
            'password': local_config['password'],
            'ssl_enabled': local_config['ssl_enabled'],
            'connection_timeout': local_config['connection_timeout'],
            'is_active': True
        }


class MilvusQueryBuilder:
    """Milvus查询构建器"""
    
    @staticmethod
    def build_collection_info_query() -> str:
        """构建获取集合信息的查询"""
        return """
        SELECT 
            collection_name,
            description,
            auto_id,
            num_shards,
            PRIMARY_KEY_FIELD as primary_key
        FROM information_schema.collections 
        WHERE collection_name IS NOT NULL
        """
    
    @staticmethod
    def build_vector_search_query(collection_name: str, vector_field: str, 
                                query_vector: list, limit: int = 10) -> str:
        """构建向量搜索查询"""
        # 注意：这只是一个示例格式，实际Milvus查询语法可能不同
        vector_str = ','.join(map(str, query_vector))
        return f"""
        SELECT *
        FROM {collection_name}
        WHERE {vector_field} SEARCH ({vector_str})
        LIMIT {limit}
        """
    
    @staticmethod
    def build_insert_query(collection_name: str, data: Dict) -> str:
        """构建插入数据查询"""
        columns = ', '.join(data.keys())
        values = ', '.join([f"'{v}'" if isinstance(v, str) else str(v) for v in data.values()])
        return f"""
        INSERT INTO {collection_name} ({columns})
        VALUES ({values})
        """


# 环境检查工具
class MilvusEnvironmentChecker:
    """Milvus环境检查工具"""
    
    @staticmethod
    def check_docker_services() -> Dict[str, bool]:
        """检查必要的Docker服务是否运行"""
        import subprocess
        
        services = {
            'milvus-standalone': False,
            'milvus-etcd': False,
            'milvus-minio': False
        }
        
        try:
            result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'], 
                                  capture_output=True, text=True)
            running_containers = result.stdout.strip().split('\n')
            
            for service_name in services.keys():
                services[service_name] = any(service_name in container 
                                           for container in running_containers)
                
        except Exception as e:
            print(f"检查Docker服务时出错: {e}")
            
        return services
    
    @staticmethod
    def check_port_availability(host: str = 'localhost', port: int = 19530) -> bool:
        """检查Milvus端口是否可用"""
        import socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception:
            return False


# 使用示例和帮助函数
def get_local_milvus_connection_info() -> str:
    """获取本地Milvus连接信息"""
    config = MilvusLocalConfig.get_local_config()
    checker = MilvusEnvironmentChecker()
    
    info = f"""
本地Milvus测试环境信息:
=====================
连接地址: {config['host']}:{config['port']}
数据库: {config['database']}
用户名: {config['username'] or '(无需认证)'}
密码: {config['password'] or '(无需认证)'}
SSL启用: {config['ssl_enabled']}
超时时间: {config['connection_timeout']}秒

环境检查:
=======
Docker服务状态: {checker.check_docker_services()}
端口可用性: {checker.check_port_availability(config['host'], config['port'])}
    """
    return info.strip()


if __name__ == "__main__":
    print(get_local_milvus_connection_info())