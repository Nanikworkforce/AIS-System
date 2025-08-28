#!/usr/bin/env python3
"""
Smart deployment script that auto-detects available dependencies
Falls back gracefully when complex dependencies fail
"""

import os
import sys
import importlib
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependency(module_name):
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def deploy_full_features():
    """Deploy with full SocketIO features"""
    try:
        logger.info("🚀 Attempting full-featured deployment...")
        
        from api.app import create_app
        
        fleet_size = int(os.environ.get('DEFAULT_FLEET_SIZE', 500))
        port = int(os.environ.get('PORT', 5000))
        
        app, socketio = create_app(fleet_size=fleet_size)
        
        logger.info("✅ Full features available - starting with SocketIO")
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"❌ Full deployment failed: {e}")
        raise

def deploy_basic_flask():
    """Deploy basic Flask app"""
    logger.info("🔄 Starting basic Flask deployment...")
    
    from flask import Flask, jsonify
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/')
    def home():
        return jsonify({
            'status': 'running',
            'message': 'AIS System - Basic Mode',
            'mode': 'compatibility',
            'features': 'limited'
        })
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"✅ Basic Flask app starting on port {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

def main():
    """Smart deployment main function"""
    logger.info("🧠 Smart deployment starting...")
    logger.info(f"🐍 Python version: {sys.version}")
    logger.info(f"📁 Working directory: {os.getcwd()}")
    
    # Check available dependencies
    dependencies = {
        'flask': check_dependency('flask'),
        'flask_cors': check_dependency('flask_cors'),
        'flask_socketio': check_dependency('flask_socketio'),
        'socketio': check_dependency('socketio'),
        'eventlet': check_dependency('eventlet'),
        'gevent': check_dependency('gevent')
    }
    
    logger.info("📦 Dependency check:")
    for dep, available in dependencies.items():
        status = "✅" if available else "❌"
        logger.info(f"  {status} {dep}")
    
    # Decision logic
    if dependencies['flask_socketio'] and dependencies['socketio']:
        try:
            deploy_full_features()
        except Exception as e:
            logger.warning(f"⚠️ Full deployment failed, falling back: {e}")
            if dependencies['flask'] and dependencies['flask_cors']:
                deploy_basic_flask()
            else:
                logger.error("❌ Even basic Flask is not available")
                sys.exit(1)
    elif dependencies['flask'] and dependencies['flask_cors']:
        logger.info("📉 SocketIO not available, using basic Flask")
        deploy_basic_flask()
    else:
        logger.error("❌ Required dependencies not available")
        sys.exit(1)

if __name__ == '__main__':
    main()
