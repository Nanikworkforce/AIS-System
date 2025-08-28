"""
WSGI entrypoint for running the Flask app with Gunicorn on Render.
"""

import os
from .app import create_app

# Get fleet size from environment variable  
fleet_size = int(os.environ.get('DEFAULT_FLEET_SIZE', 500))

# Create app with SocketIO support
app, socketio = create_app(fleet_size=fleet_size)

# For Gunicorn deployment with SocketIO
application = socketio


