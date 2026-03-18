# Vercel Serverless Function Handler for Django
# Vercel Python runtime supports WSGI applications natively

import os
import sys

# Add the plane Django app to the path
apps_api_path = os.path.join(os.path.dirname(__file__), '..', 'apps', 'api')
sys.path.insert(0, apps_api_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plane.settings.vercel")

# =============================================================================
# CELERY MOCK - Must be injected BEFORE importing any plane code
# =============================================================================
# Plane's __init__.py imports celery, but celery is not installed on Vercel
# to reduce bundle size. We inject a mock module instead.

class MockCeleryApp:
    """Mock Celery app that does nothing"""
    def __init__(self, *args, **kwargs):
        self.conf = type('conf', (), {
            'beat_schedule': {},
            'beat_scheduler': None,
        })()

    def config_from_object(self, *args, **kwargs):
        pass

    def autodiscover_tasks(self, *args, **kwargs):
        pass

    def task(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

class MockCeleryModule:
    """Mock celery module"""
    Celery = MockCeleryApp

    @staticmethod
    def shared_task(_func=None, **kwargs):
        def decorator(func):
            # Add delay method that runs synchronously
            def delay(*args, **kw):
                try:
                    return func(*args, **kw)
                except Exception:
                    pass  # Background tasks shouldn't crash requests
            func.delay = delay
            func.apply_async = lambda *a, **kw: delay(*a, **kw)
            func.s = lambda *a, **kw: func
            func.si = lambda *a, **kw: func
            return func
        if _func is not None:
            return decorator(_func)
        return decorator

# Inject mock modules before any imports
mock_celery = MockCeleryModule()
sys.modules['celery'] = mock_celery
sys.modules['celery.schedules'] = type(sys)('celery.schedules')
sys.modules['celery.schedules'].crontab = lambda **kwargs: None
sys.modules['celery.signals'] = type(sys)('celery.signals')
sys.modules['celery.signals'].after_setup_logger = type('Signal', (), {'connect': lambda self, f: f})()
sys.modules['celery.signals'].after_setup_task_logger = type('Signal', (), {'connect': lambda self, f: f})()

# =============================================================================
# Import Django WSGI application
# Vercel's Python runtime will detect and use this as a WSGI app
from plane.wsgi import application

# Export as 'app' for Vercel
app = application
