#!/usr/bin/env python3
"""
Quick WebSocket Connection Test
Tests if the WebSocket server is working and dashboard can connect
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket_connection():
    """Test WebSocket connection to the server"""
    print("🧪 Testing WebSocket Connection")
    print("=" * 40)
    
    try:
        print("🔗 Connecting to ws://localhost:8765...")
        
        # Connect to WebSocket server
        websocket = await websockets.connect('ws://localhost:8765')
        print("✅ WebSocket connection successful!")
        
        # Send a test message
        test_message = {
            'type': 'get_fleet_summary'
        }
        await websocket.send(json.dumps(test_message))
        print("📤 Sent test message")
        
        # Wait for response
        response = await asyncio.wait_for(websocket.recv(), timeout=10)
        data = json.loads(response)
        
        print("📥 Received response:")
        print(f"   Message type: {data.get('type', 'unknown')}")
        
        if data.get('type') == 'connection_established':
            print("🎉 Server responded with connection established!")
            live_enabled = data.get('live_data_enabled', False)
            print(f"   Live data: {'✅ Enabled' if live_enabled else '❌ Disabled'}")
            
            if 'fleet_summary' in data:
                summary = data['fleet_summary']
                print(f"   Total vessels: {summary.get('total_vessels', 0)}")
                print(f"   Live vessels: {summary.get('live_vessels', 0)}")
                print(f"   Simulated vessels: {summary.get('simulated_vessels', 0)}")
        
        # Close connection
        await websocket.close()
        print("🔌 Connection closed")
        
        return True
        
    except asyncio.TimeoutError:
        print("⏰ Connection timed out")
        return False
    except ConnectionRefusedError:
        print("❌ Connection refused - server may not be running")
        print("💡 Start server with: python realtime_live_websocket_server.py")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    """Main test function"""
    print("🌊 WEBSOCKET CONNECTION TEST")
    print("=" * 50)
    print("This test verifies the WebSocket server is running")
    print("and can accept connections from the dashboard.")
    print("=" * 50)
    print()
    
    result = asyncio.run(test_websocket_connection())
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 SUCCESS! WebSocket server is working correctly!")
        print("✅ Dashboard should now be able to connect")
        print("🌐 Open live_dashboard.html in your browser")
    else:
        print("❌ FAILED! WebSocket server connection issues")
        print("🔧 Check if server is running on port 8765")
    
    return result

if __name__ == "__main__":
    main()
