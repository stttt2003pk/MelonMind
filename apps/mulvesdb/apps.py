from django.apps import AppConfig


class MulvesdbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mulvesdb'
    verbose_name = 'Mulves数据库'

    def ready(self):
        """应用启动时执行的初始化操作"""
        # 导入信号处理器
        try:
            import apps.mulvesdb.signals  # noqa
        except ImportError:
            pass