#!/usr/bin/env python3
"""
Alternative server startup script for deployment
Handles SocketIO compatibility issues
"""

import os
import sys
from api.app import AISFlaskApp

def main():
    """Start the server with proper configuration"""
    try:
        # Get configuration from environment
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        fleet_size = int(os.environ.get('DEFAULT_FLEET_SIZE', 500))
        
        print(f"🚢 Starting AIS System Server...")
        print(f"📊 Fleet Size: {fleet_size}")
        print(f"🌐 Host: {host}:{port}")
        
        # Create app with compatible settings
        app = AISFlaskApp(fleet_size=fleet_size)
        
        # Use the more compatible threading mode
        app.socketio.run(
            app.app,
            host=host,
            port=port,
            debug=False,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        # Fallback to basic Flask without SocketIO
        print("🔄 Falling back to basic Flask app...")
        from flask import Flask
        fallback_app = Flask(__name__)
        
        @fallback_app.route('/')
        def home():
            return "AIS System - Basic Mode (SocketIO disabled)"
        
        fallback_app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    main()
