#!/usr/bin/env python3
"""
Live AIS System Launcher
Easy startup script for the complete live AIS system with AISStream.io integration
"""

import argparse
import asyncio
import subprocess
import sys
import os
import webbrowser
import time
from datetime import datetime

def print_banner():
    """Print system banner"""
    print("🌊" + "=" * 70 + "🌊")
    print("🚢" + " " * 20 + "LIVE AIS SYSTEM LAUNCHER" + " " * 23 + "🚢")
    print("⚓" + " " * 15 + "Real-Time Marine Vessel Tracking" + " " * 20 + "⚓")
    print("📡" + " " * 15 + "Powered by AISStream.io Integration" + " " * 17 + "📡")
    print("🌊" + "=" * 70 + "🌊")
    print()

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_modules = [
        'websockets',
        'flask',
        'pandas',
        'geopy',
        'faker'
    ]
    
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module} (missing)")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️ Missing dependencies: {', '.join(missing)}")
        print(f"💡 Install with: pip install {' '.join(missing)}")
        print(f"   Or run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def test_aisstream_connection():
    """Test AISStream.io connection"""
    print("\n🧪 Testing AISStream.io connection...")
    
    try:
        # Run quick connection test
        result = subprocess.run([
            sys.executable, 'test_aisstream_integration.py'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ AISStream.io connection test passed!")
            return True
        else:
            print("⚠️ AISStream.io connection test had issues")
            print("💡 Check the detailed test output for more information")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️ Connection test timed out")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def run_live_websocket_server():
    """Run the live WebSocket server"""
    print("\n🚀 Starting Live AIS WebSocket Server...")
    print("📡 This will connect to AISStream.io for live data")
    print("🎭 Simulated data will be used as fallback/supplement")
    print()
    
    try:
        # Run the live WebSocket server
        subprocess.run([sys.executable, 'realtime_live_websocket_server.py'])
    except KeyboardInterrupt:
        print("\n⏹️ Server stopped by user")
    except Exception as e:
        print(f"❌ Error running server: {e}")

def run_test_client():
    """Run the test client"""
    print("\n🖥️ Starting Live AIS WebSocket Client...")
    
    try:
        subprocess.run([sys.executable, 'realtime_live_client.py'])
    except KeyboardInterrupt:
        print("\n⏹️ Client stopped by user")
    except Exception as e:
        print(f"❌ Error running client: {e}")

def open_web_dashboard():
    """Open the web dashboard"""
    print("\n🌐 Opening Live AIS Web Dashboard...")
    
    dashboard_path = os.path.join(os.getcwd(), 'live_dashboard.html')
    
    if os.path.exists(dashboard_path):
        try:
            webbrowser.open(f'file://{dashboard_path}')
            print("✅ Dashboard opened in your default browser")
            print("🔗 If it didn't open automatically, navigate to:")
            print(f"   file://{dashboard_path}")
        except Exception as e:
            print(f"❌ Failed to open dashboard: {e}")
            print(f"💡 Manually open: {dashboard_path}")
    else:
        print(f"❌ Dashboard file not found: {dashboard_path}")

def run_system_demo():
    """Run complete system demonstration"""
    print("\n🎬 RUNNING COMPLETE SYSTEM DEMO")
    print("=" * 50)
    print("This will start:")
    print("1. Live WebSocket server (with AISStream.io)")
    print("2. Web dashboard (in your browser)")
    print("3. You can also run the Python client separately")
    print()
    
    # Open dashboard first
    open_web_dashboard()
    
    # Wait a moment for browser to open
    time.sleep(2)
    
    # Start the server (this will block)
    run_live_websocket_server()

def show_system_info():
    """Show system information and usage"""
    print("📋 LIVE AIS SYSTEM COMPONENTS")
    print("=" * 50)
    print()
    
    print("🔧 Core Components:")
    print("├── realtime_live_websocket_server.py - Main server with AISStream.io")
    print("├── realtime_live_client.py - Python WebSocket client")
    print("├── live_dashboard.html - Interactive web dashboard")
    print("├── integrations/aisstream_client.py - AISStream.io integration")
    print("└── test_aisstream_integration.py - Connection testing")
    print()
    
    print("📡 Data Sources:")
    print("├── 🔴 LIVE: AISStream.io real vessel data")
    print("└── 🎭 SIMULATED: Generated vessel data (fallback)")
    print()
    
    print("🌐 WebSocket Protocol:")
    print("├── URL: ws://localhost:8765")
    print("├── Messages: vessel_updates, fleet_summary, live_status")
    print("└── Real-time updates every 30 seconds")
    print()
    
    print("🎯 Usage Examples:")
    print("├── Full demo: python run_live_ais_system.py --demo")
    print("├── Server only: python run_live_ais_system.py --server")
    print("├── Test connection: python run_live_ais_system.py --test")
    print("└── Check deps: python run_live_ais_system.py --check")
    print()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Live AIS System Launcher with AISStream.io Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_live_ais_system.py --demo          # Run complete demo
  python run_live_ais_system.py --server        # Start server only
  python run_live_ais_system.py --client        # Start client only
  python run_live_ais_system.py --dashboard     # Open dashboard only
  python run_live_ais_system.py --test          # Test AISStream.io connection
  python run_live_ais_system.py --check         # Check dependencies
  python run_live_ais_system.py --info          # Show system information
        """
    )
    
    parser.add_argument('--demo', action='store_true',
                       help='Run complete system demonstration')
    parser.add_argument('--server', action='store_true',
                       help='Start live WebSocket server only')
    parser.add_argument('--client', action='store_true',
                       help='Start Python WebSocket client only')
    parser.add_argument('--dashboard', action='store_true',
                       help='Open web dashboard only')
    parser.add_argument('--test', action='store_true',
                       help='Test AISStream.io connection')
    parser.add_argument('--check', action='store_true',
                       help='Check dependencies')
    parser.add_argument('--info', action='store_true',
                       help='Show system information')
    
    args = parser.parse_args()
    
    # Show banner
    print_banner()
    
    # Handle different modes
    if args.check:
        check_dependencies()
    
    elif args.test:
        if check_dependencies():
            test_aisstream_connection()
    
    elif args.info:
        show_system_info()
    
    elif args.server:
        if check_dependencies():
            run_live_websocket_server()
    
    elif args.client:
        if check_dependencies():
            run_test_client()
    
    elif args.dashboard:
        open_web_dashboard()
    
    elif args.demo:
        if check_dependencies():
            run_system_demo()
    
    else:
        # Default: show info and prompt user
        show_system_info()
        
        print("🚀 QUICK START OPTIONS:")
        print("=" * 30)
        print("1. 🎬 Run complete demo: --demo")
        print("2. 🧪 Test connection: --test")
        print("3. 🔧 Check dependencies: --check")
        print("4. 🌐 Open dashboard: --dashboard")
        print("5. 🖥️ Start server: --server")
        print()
        print("💡 Example: python run_live_ais_system.py --demo")
        print()
        
        # Auto-run demo with CSV data instead of prompting for input
        print("🚀 Auto-starting system demo with CSV data...")
        if check_dependencies():
            run_system_demo()

if __name__ == "__main__":
    main()
