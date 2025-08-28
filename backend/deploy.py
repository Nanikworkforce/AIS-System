#!/usr/bin/env python3
"""
Deployment script for Render with fallback options
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def deploy_with_fallback():
    """Try to deploy with SocketIO, fallback to basic Flask if needed"""
    
    try:
        # Try main deployment with SocketIO
        logger.info("🚀 Attempting deployment with SocketIO...")
        
        from api.app import create_app
        
        # Get configuration
        fleet_size = int(os.environ.get('DEFAULT_FLEET_SIZE', 500))
        port = int(os.environ.get('PORT', 5000))
        
        # Create app
        app, socketio = create_app(fleet_size=fleet_size)
        
        logger.info(f"✅ SocketIO app created successfully")
        logger.info(f"📊 Fleet size: {fleet_size}")
        logger.info(f"🌐 Starting on port: {port}")
        
        # Start with SocketIO
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
        
    except ImportError as e:
        logger.warning(f"⚠️ SocketIO import failed: {e}")
        deploy_basic_flask()
        
    except Exception as e:
        logger.error(f"❌ SocketIO deployment failed: {e}")
        logger.info("🔄 Falling back to basic Flask...")
        deploy_basic_flask()

def deploy_basic_flask():
    """Deploy basic Flask app without SocketIO"""
    try:
        from flask import Flask, jsonify
        from flask_cors import CORS
        
        app = Flask(__name__)
        CORS(app)
        
        @app.route('/')
        def home():
            return jsonify({
                'status': 'running',
                'message': 'AIS System - Basic Mode',
                'note': 'SocketIO features disabled for compatibility'
            })
        
        @app.route('/health')
        def health():
            return jsonify({'status': 'healthy'})
        
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"🌐 Starting basic Flask app on port {port}")
        
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"❌ Basic Flask deployment also failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    deploy_with_fallback()
