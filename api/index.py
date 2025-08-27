"""
Vercel serverless function for AIS Flask API
This file serves as the entry point for Vercel deployment
"""

import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.insert(0, backend_path)

# Import the Flask app
from api.app import AISFlaskApp

# Create the Flask app instance
flask_app_instance = AISFlaskApp(fleet_size=500)  # Smaller fleet for serverless
app = flask_app_instance.app

# Vercel serverless function handler
def handler(request):
    """Handle Vercel requests"""
    return app(request.environ, lambda status, headers: None)

# For local testing
if __name__ == "__main__":
    app.run(debug=True, port=5000)
