from django.apps import AppConfig


class ArrozConfig(AppConfig):
    name = 'arroz'

    def ready(self):
        import arroz.signals
