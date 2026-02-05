from django.apps import AppConfig


class PdfloaderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.pdfloader'
    verbose_name = 'PDF加载器'

    def ready(self):
        """应用启动时执行的初始化操作"""
        import apps.pdfloader.signals  # noqa