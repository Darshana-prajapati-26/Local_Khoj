from django.apps import AppConfig


class StoresConfig(AppConfig):
    name = 'stores'
    verbose_name = 'Store'

    def ready(self):
        import stores.signals  # noqa: F401 — registers signals
