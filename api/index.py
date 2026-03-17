# Vercel Serverless Function Handler for Django
# Using mangum adapter for ASGI compatibility

import os
import sys

# Add the plane Django app to the path
# Since we're in /api/index.py, we need to go up one level then into apps/api
apps_api_path = os.path.join(os.path.dirname(__file__), '..', 'apps', 'api')
sys.path.insert(0, apps_api_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plane.settings.vercel")

# Import Django and initialize
import django
django.setup()

from mangum import Mangum
from django.core.asgi import get_asgi_application

# Get Django ASGI application
django_app = get_asgi_application()

# Wrap with Mangum for AWS Lambda/Vercel compatibility
handler = Mangum(django_app, lifespan="off")
