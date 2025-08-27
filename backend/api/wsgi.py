"""
WSGI entrypoint for running the Flask app with Gunicorn on Render.
"""

from .app import create_app

# Expose the Flask app as `app` for Gunicorn
app = create_app()


