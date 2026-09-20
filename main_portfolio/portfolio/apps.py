from django.apps import AppConfig

class PortfolioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'portfolio'
    verbose_name = "Portfolio Management"

    def ready(self):
        import portfolio.signals  # noqa
        try:
            from .keep_alive import start_keep_alive
            start_keep_alive()
        except Exception as e:
            print(f"[Keep-Alive Setup Notice]: {e}")

