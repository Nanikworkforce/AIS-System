#!/usr/bin/env python3
"""
Test script to verify the vessel dashboard WebSocket connection
"""

import asyncio
import websockets
import json
import sys

async def test_connection():
    """Test WebSocket connection to the vessel dashboard server"""
    uri = "ws://localhost:8766"
    
    try:
        print("Connecting to vessel dashboard server...")
        print(f"URI: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("* Connected successfully!")
            
            # Test fleet statistics request
            request = {"type": "get_fleet_statistics"}
            await websocket.send(json.dumps(request))
            print("* Sent fleet statistics request")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"* Received response: {data['type']}")
            
            if data['type'] == 'fleet_statistics':
                stats = data['data']
                print(f"* Total vessels: {stats['total_vessels']}")
                print(f"* Vessel types: {list(stats['vessel_types'].keys())}")
                
            # Test vessel by type request
            request = {"type": "get_vessels_by_type", "vessel_type": "tanker"}
            await websocket.send(json.dumps(request))
            print("* Sent tanker vessels request")
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"* Received response: {data['type']}")
            
            if data['type'] == 'vessels_by_type':
                vessels = data['data']
                print(f"* Found {len(vessels)} tanker vessels")
                if vessels:
                    print(f"* Example vessel: {vessels[0]['vessel_name']}")
            
            print("* All tests passed!")
            return True
            
    except ConnectionRefusedError:
        print("* Connection refused - server may not be running")
        print("  Start server with: python enhanced_vessel_dashboard_server.py")
        return False
        
    except Exception as e:
        print(f"* Error: {e}")
        return False

async def main():
    print("VESSEL DASHBOARD CONNECTION TEST")
    print("=" * 40)
    
    success = await test_connection()
    
    if success:
        print("\n* Test completed successfully!")
        print("* The vessel dashboard server is working correctly")
    else:
        print("\n* Test failed!")
        print("* Please check that the server is running")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
