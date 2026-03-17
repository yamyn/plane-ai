# Vercel Serverless Function Handler for Django
# Vercel Python runtime supports WSGI applications natively

import os
import sys

# Add the plane Django app to the path
apps_api_path = os.path.join(os.path.dirname(__file__), '..', 'apps', 'api')
sys.path.insert(0, apps_api_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "plane.settings.vercel")

# Import Django WSGI application
# Vercel's Python runtime will detect and use this as a WSGI app
from plane.wsgi import application

# Export as 'app' for Vercel
app = application
