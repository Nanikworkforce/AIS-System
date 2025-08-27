#!/usr/bin/env python3
"""
Vessel Dashboard Launcher
Starts the enhanced vessel categorization dashboard system
"""

import asyncio
import subprocess
import sys
import time
import webbrowser
import os
from pathlib import Path

def print_banner():
    print("=" + "="*60 + "=")
    print("  VESSEL CATEGORIZATION DASHBOARD SYSTEM")
    print("="*64)
    print("  Advanced fleet management with categorized vessel data")
    print("  * Real-time vessel tracking")
    print("  * Categorized by vessel type (Tankers, Containers, Bulkers)")
    print("  * Date-based historical queries")
    print("  * Detailed vessel specifications and dry dock history")
    print("="*64)

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import websockets
        return True
    except ImportError:
        print("❌ Missing required dependency: websockets")
        print("   Install with: pip install websockets")
        return False

def start_server():
    """Start the enhanced vessel dashboard server"""
    server_file = Path(__file__).parent / "enhanced_vessel_dashboard_server.py"
    
    if not server_file.exists():
        print(f"❌ Server file not found: {server_file}")
        return None
    
    print("Starting Enhanced Vessel Dashboard Server...")
    print("   Port: 8766")
    print("   Protocol: WebSocket")
    
    # Start the server as a subprocess
    server_process = subprocess.Popen([
        sys.executable, str(server_file)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Give the server time to start
    time.sleep(2)
    
    # Check if server started successfully
    if server_process.poll() is None:
        print("* Enhanced server started successfully")
        return server_process
    else:
        stdout, stderr = server_process.communicate()
        print(f"❌ Server failed to start:")
        print(f"   STDOUT: {stdout}")
        print(f"   STDERR: {stderr}")
        return None

def open_dashboard():
    """Open the vessel dashboard in the default browser"""
    dashboard_file = Path(__file__).parent / "vessel_categorization_dashboard.html"
    
    if not dashboard_file.exists():
        print(f"❌ Dashboard file not found: {dashboard_file}")
        return False
    
    dashboard_url = f"file://{dashboard_file.absolute()}"
    print(f"Opening dashboard: {dashboard_url}")
    
    try:
        webbrowser.open(dashboard_url)
        print("* Dashboard opened in browser")
        return True
    except Exception as e:
        print(f"❌ Failed to open dashboard: {e}")
        print(f"   Manual URL: {dashboard_url}")
        return False

def print_instructions():
    """Print usage instructions"""
    print("\n📋 DASHBOARD FEATURES:")
    print("="*40)
    print("🚢 VESSEL CATEGORIES:")
    print("   • Tankers - Oil and chemical transport vessels")
    print("   • Container Ships - Containerized cargo vessels")
    print("   • Bulk Carriers - Dry bulk cargo vessels")
    print("   • General Cargo - Multi-purpose cargo vessels")
    print()
    print("📊 CATEGORY DETAILS:")
    print("   • Click any category card to expand vessel list")
    print("   • View vessel count, status distribution, and average age")
    print("   • Click individual vessels for detailed information")
    print()
    print("🔧 VESSEL DETAILS:")
    print("   • Technical specifications (length, tonnage, capacity)")
    print("   • Dry dock history and maintenance schedules")
    print("   • Current location and navigation status")
    print("   • Flag country and operator information")
    print()
    print("📅 DATE QUERIES:")
    print("   • Select date range for historical vessel data")
    print("   • Query vessel positions and status over time")
    print("   • Analyze fleet movement patterns")
    print()
    print("🎛️ CONTROLS:")
    print("   • Refresh fleet data in real-time")
    print("   • Filter by vessel type and status")
    print("   • Monitor dry dock schedules and maintenance")

def main():
    """Main launcher function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start the enhanced server
    server_process = start_server()
    if not server_process:
        print("❌ Failed to start server. Exiting.")
        sys.exit(1)
    
    # Wait a moment for server to fully initialize
    time.sleep(3)
    
    # Open the dashboard
    dashboard_opened = open_dashboard()
    
    # Print instructions
    print_instructions()
    
    print(f"\n🎯 QUICK ACCESS:")
    print(f"   Server: ws://localhost:8766")
    print(f"   Dashboard: vessel_categorization_dashboard.html")
    print(f"   Fallback: simple_live_websocket_server.py (port 8765)")
    
    if dashboard_opened:
        print(f"\n✨ Dashboard is now running!")
        print(f"   Press Ctrl+C to stop the server")
        
        try:
            # Keep the script running and monitor the server
            while True:
                if server_process.poll() is not None:
                    print(f"\n⚠️ Server process has stopped")
                    stdout, stderr = server_process.communicate()
                    if stdout:
                        print(f"Server output: {stdout}")
                    if stderr:
                        print(f"Server error: {stderr}")
                    break
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n⏹️ Stopping server...")
            server_process.terminate()
            server_process.wait()
            print(f"🛑 Server stopped")
    
    else:
        print(f"\n⚠️ Dashboard could not be opened automatically")
        print(f"   Please open vessel_categorization_dashboard.html manually")
        server_process.terminate()

if __name__ == "__main__":
    main()
